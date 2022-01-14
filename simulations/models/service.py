import pandas as pd
import numpy as np
import uuid, logging, time
from models import Job

class Service:
    """Representing a Kubernetes Service"""

    def __init__(self,
        job_type,
        dependencies,
        capacity,
        expected_outbound_req_size_kb
    ):
        self.id = uuid.uuid4()

        self.job_type = job_type
        self.capacity = capacity # RPS
        self.cluster = None
        self.dependencies = dependencies
        self._is_available = True

        self.expected_outbound_req_size_kb = expected_outbound_req_size_kb

        self._df_columns = [
            # "job_id", # str
            "job_type", # str
            "load", # float
            "capacity", # float
            "arrival_time", # float
            "ttl", # float
            "duration", # float
            "latency",
            # "work_latency", # float
            # "consumed", # bool
            "cost_in_usd", # float
            "size_in_gb", # float
            "source_zone_id",# str
            "target_zone_id",# str
            # "source_job_id", # str
            "source_job_type", # str
            "lat", # float
            "lon", # float
            "cloud_provider",
            "cluster_name",
            "drop_rate",
            # "propogated_job_ids" # [str]
        ]

        self.reset_state()

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

    def __repr__(self):
        return self.full_name

    def __hash__(self):
        return self.job_type

    def _calc_job_traffic_cost_and_size(self, job):
        # A job's total data is:
        # - The data we will send to the propogated jobs
        # +
        # - The data we will return to the client that sent the job
        # We don't pay for ingress, only egress

        one_million = 1_000_000
        size_in_gb = job.load*(self.expected_outbound_req_size_kb/one_million)
        cost_in_usd = 0

        cost_in_usd += size_in_gb * self.zone.price_per_gb(job.source_zone)

        for pj in job.propogated_jobs:
            s_gb = pj.data_size_in_kb/one_million*pj.load
            size_in_gb += s_gb
            cost_in_usd += s_gb * self.zone.price_per_gb(pj.target_zone)
        return cost_in_usd, size_in_gb

    def _collect(self, job, load, drop_rate):
        source_job_id = ""
        source_zone = job.source_zone
        if source_zone:
            source_job_id = source_zone.id

        source_zone_name = "CLIENT"
        if source_zone:
            source_zone_name = job.source_zone.full_name

        source_job_type = "CLIENT"
        if job.source_job:
            source_job_type = job.source_job.type
        
        # ttl = 0
        # duration = 0
        # if is_dropped == 0:
        ttl = job.ttl(load, self.capacity)
        duration = job.duration(load, self.capacity)
        
        # print("{} collecting:\nat: {}\njob: {}\nduration: {}\nttl: {}\ndrop_rate: {}".format(self.full_name, job.arrival_time, job.type, duration, ttl, drop_rate))

        cost_in_usd, size_in_gb = self._calc_job_traffic_cost_and_size(job)
        self.data_frames_to_add.append([
            # job.id,
            job.type,
            job.load,
            self.capacity,
            job.arrival_time,
            ttl,
            duration,
            job.latency,
            # job.work_latency,
            # False,
            cost_in_usd,
            size_in_gb,
            source_zone_name,
            job.target_zone.full_name,
            # source_job_id,
            source_job_type,
            job.target_zone.location["lat"],
            job.target_zone.location["lon"],
            self.cluster.zone.cloud_provider.id,
            self.cluster.id,
            drop_rate,
            # [j.id for j in job.propogated_jobs]
        ])
        if None in self.data_frames_to_add[-1]:
            print(job)
            print(self.data_frames_to_add[-1])
            raise Exception("Service")


    def _propogate_by_weight(self, job):
        # Distribute the job's load, which indicates the amount of requests among the clusters
        # Calculate actual load, based on the job load (i.e max load) according to the time-of-day
        
        _propogated_jobs = []
        for dependency in self.dependencies:
            # Hack - make model work by cluster and not service!
            weights = self.cluster.weights
            if dependency.job_type in weights:
                weights = weights[dependency.job_type][self.cluster.id]

            if self.id in weights:
                clusters_weights_map = weights[self.id][dependency.job_type]
            else:
                clusters_weights_map = weights[self.cluster.id][dependency.job_type]

            weights_sum = sum(clusters_weights_map.values())
            if abs(weights_sum-1) > 0.001: # More than 1% diviation should raise error
                print("self",self.full_name)
                print("dependency",dependency)
                print("weights_sum",weights_sum)
                print("clusters_weights_map",clusters_weights_map)
                print("cluster.weights",self.cluster.weights)
                raise Exception("weights_sum not good")
            for dest_cluster, weight in clusters_weights_map.items():
                if weight == 0:
                    continue
                job_latency = self.zone.latency_per_request(dest_cluster.zone)
                new_job = Job(
                    source_zone=self.zone,
                    target_zone=dest_cluster.zone,
                    # processing_duration=job.processing_duration,
                    load=job.load * weight,
                    type=dependency.job_type,
                    data_size_in_kb=dependency.req_size,
                    latency=job_latency,
                    source_job=job,
                )
                _propogated_jobs.append(new_job)
                dest_cluster.consume(new_job, job.arrival_time+job_latency)
        job.propogated_jobs = _propogated_jobs

    @property
    def zone(self):
        return self.cluster.zone

    @property
    def full_name(self):
        return "-".join([self.job_type, self.zone.full_name])

    def jobs_consumed_per_time_slot(self, at_tik):
        mod = 86_340

        if len(self.job_data_frame.index) == 0:
            # print("no df yet")
            return self.capacity - 10
        # if at_tik <= mod:
        #     return self.capacity - 10
        # load = self.load(at_tik)
        
        # return load
        # print("jobs_consumed_per_time_slot at_tik: ", at_tik)
        # load_df = self.job_data_frame[self.job_data_frame["arrival_time"] <= 1_439_000]
        load_df = self.job_data_frame
        begin = (at_tik % mod)
        end = begin - 60#+ 60 # One minute
        if end < 0:
            return self.capacity - 10
        selector = load_df["arrival_time"].between(begin, end)
        df = load_df[selector]["load"]
        
        mean_load = df.mean()
        # print("mean load = ", load)
        load = df.ewm(span=60, adjust=False).mean().mean()
        
        # print("Window: {}".format(df))
        print("between {} -> {}:\nmean_load: {}\newm_load: {}".format(begin, end, mean_load, load))

        if load == 0 or np.isnan(load):
            # print("###########")
            # print("{}: 0 or nan ".format(self.job_type))
            # print("###########")
            return self.capacity - 10
        # else:
            # print("###########")
            # print("{}: mean load {}".format(self.job_type, load))
            # print("###########")
        # print("{} jobs_consumed_per_time_slot {} = {}".format(self.full_name, at_tik, load))
        return load
        sum_load_df = self.job_data_frame.groupby("arrival_time")["load"].agg("sum")
        mean_job_count = sum_load_df.mean()

        if mean_job_count == 0 or np.isnan(mean_job_count):
            print("0 or nan")
            return self.capacity - 10
        return mean_job_count
    
    @property
    def is_available(self):
        return self._is_available

    def residual_capacity(self, at_tik):
        if not self._is_available:
            raise Exception("Trying to get residual_capacity")
        load = self.load(at_tik)
        return self.capacity - load

    def load(self, at_tik):
        if not self._is_available:
            raise Exception("Trying to get load")
        selector = (self.job_data_frame["ttl"] > at_tik)
        print("load at: {}\ndf selector: {}".format(at_tik, selector))
        jobs_not_done = self.job_data_frame.loc[selector]
        print("jobs_not_done", jobs_not_done)
        load = jobs_not_done["load"].sum()
        return load

    def add_to_cluster(self, cluster):
        logging.debug("service add_to_cluster - {}".format(cluster))
        self.cluster = cluster

    def consume(self, job):

        if not self._is_available:
            logging.error("service:{}\ncannot consume:{} - service is not available".format(self.job_type, job))
            raise Exception("Trying to consume for non active service")
        
        if job.type != self.job_type:
            raise Exception("Job type mismatch {} ? {}".format(job.type, self.job_type))

        load = self.load(job.arrival_time)
        # if job.should_drop(load, self.capacity):
        #     # print("Droping job {} because of load cap ratio {}".format(job.type, load/self.capacity))
        #     self._collect(job, load, is_dropped=1) # Collecting mean nothing as we will filter out dropped jobs
        #     return
        
        drop_percentage = job.drop_percent(load, self.capacity)
        
        if drop_percentage > 0:
            # load_before = job.load
            job.load = job.load * (1 - drop_percentage) 
            # load_after = job.load
            print("Droping {} precent of job {} because of load cap ratio {}\nat {}\nload = {}\ncap = {}".format(drop_percentage, job.type, load/self.capacity, job.arrival_time, load, self.capacity))
            # print("load before = {}\nload after = {}".format(load_before, load_after))

        # logging.debug("service={}\nconsumes={} jobs\nat={}".format(self.full_name, job.load, job.arrival_time))
        # 1) Propogate to dependencies
        # Don't worry, if your app is DAG shaped, recursion will not happen!
        # We propogate before collecting data, so panelties will not apply on propogated requests if not needed
        self._propogate_by_weight(job)
        # 2) Apply penalty if needed - add queues support
        # self._penilize_if_overload(job)
        # 3) Collect data

        print("## Before:\nconsume job {} \nat {} \nwith additional load = {}\nwhile load on service {} \nis: {} \nand cap is: {}\nload after collection is: {}".format(job.type, job.arrival_time, job.load, self.full_name, load, self.capacity, self.load(job.arrival_time)))
        print("##########")
        print(self._df_columns)
        print(self.data_frames_to_add)
        print("##########")
        
        self._collect(job, load, drop_percentage)

        print("$$ After:\nconsume job {} \nat {} \nwith additional load = {}\nwhile load on service {} \nis: {} \nand cap is: {}\nload after collection is: {}".format(job.type, job.arrival_time, job.load, self.full_name, load, self.capacity, self.load(job.arrival_time)))
        print("$$$$$$$$$$$$")
        print(self._df_columns)
        print(self.data_frames_to_add)
        print("$$$$$$$$$$$$")
        

    def reset_state(self):
        self.data_frames_count = 0
        self.data_frames_to_add = []
        self._is_available = True
        self.job_data_frame = pd.DataFrame(
            [],
            columns = self._df_columns
        )
        
        # M
        self.job_type_list = np.array([])
        self.load_list = np.array([])
        self.capacity_list = np.array([])
        self.arrival_time_list = np.array([])
        self.ttl_list = np.array([])
        self.duration_list = np.array([])
        self.latency_list = np.array([])
        self.cost_in_usd_list = np.array([])
        self.size_in_gb_list = np.array([])
        self.source_zone_id_list = np.array([])
        self.target_zone_id_list = np.array([])
        self.lat_list = np.array([])
        self.lon_list = np.array([])
        self.cloud_provider_list = np.array([])
        self.cluster_name_list = np.array([])
        self.drop_rate_list = np.array([])
        

    def build_df(self):
        self.job_data_frame = pd.DataFrame(
            {
                "job_type": self.job_type_list,
                "load": self.load_list,
                "capacity": self.capacity_list,
                "arrival_time": self.arrival_time_list,
                "ttl": self.ttl_list,
                "duration": self.duration_list,
                "latency": self.latency_list,
                "cost_in_usd": self.cost_in_usd_list,
                "size_in_gb": self.size_in_gb_list,
                "source_zone_id": self.source_zone_id_list,
                "target_zone_id": self.target_zone_id_list,
                "lat": self.lat_list,
                "lon": self.lon_list,
                "cloud_provider": self.cloud_provider_list,
                "cluster_name": self.cluster_name_list,
                "drop_rate": self.drop_rate_list,
            }
        )
        # self.job_data_frame = pd.DataFrame(
        #     self.data_frames_to_add,
        #     columns = self._df_columns
        # )
