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
        expected_outbound_req_size_kb,
        expected_tiks=1000
    ):
        self.id = uuid.uuid4()

        self.job_type = job_type
        self.capacity = capacity # RPS
        self.cluster = None
        self.dependencies = dependencies

        self.expected_outbound_req_size_kb = expected_outbound_req_size_kb

        self.expected_tiks = expected_tiks

        self._df_columns = [
            "job_id", # str
            "job_type", # str
            "load", # float
            "capacity", # float
            "arrival_time", # float
            "ttl", # float
            "duration", # float
            "latency",
            "work_latency", # float
            "consumed", # bool
            "cost_in_usd", # float
            "size_in_gb", # float
            "source_zone_id",# str
            "target_zone_id",# str
            "source_job_id", # str
            "lat", # float
            "lon", # float
            "cloud_provider",
            "cluster_name",
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

    def _collect(self, job):
        source_job_id = ""
        source_zone = job.source_zone
        if source_zone:
            source_job_id = source_zone.id
        source_zone_name = ""
        if source_zone:
            source_zone_name = job.source_zone.full_name
        cost_in_usd, size_in_gb = self._calc_job_traffic_cost_and_size(job)
        # print("Post processing {}:".format(job.type))
        # print("Cost in USD = ", cost_in_usd)
        # print("Size in GB = ", size_in_gb)
        # self._propogated_jobs(job)
        self.data_frames_to_add.append([
            job.id,
            job.type,
            job.load,
            self.capacity,
            job.arrival_time,
            job.ttl,
            job.duration,
            job.latency,
            job.work_latency,
            False,
            cost_in_usd,
            size_in_gb,
            source_zone_name,
            job.target_zone.full_name,
            source_job_id,
            job.target_zone.location["lat"],
            job.target_zone.location["lon"],
            self.cluster.zone.cloud_provider.id,
            self.cluster.id,
            # [j.id for j in job.propogated_jobs]
        ])
        if None in self.data_frames_to_add[-1]:
            print(job)
            print(self.data_frames_to_add[-1])
            raise

        # self.job_data_frame.loc[len(self.job_data_frame.index)] = self.data_frames_to_add[-1]
        # self.job_data_frame.loc[self.data_frames_count] = self.data_frames_to_add[-1]

        self.job_data_frame.at[self.data_frames_count] = self.data_frames_to_add[-1]
        # self.job_data_frame.at[len(self.job_data_frame.index)] = self.data_frames_to_add[-1]

        self.data_frames_count += 1


    def _propogate_by_weight(self, job):
        # Dsitribute the job load, which indicates the amount of requests among the clusters
        _propogated_jobs = []
        for dependency in self.dependencies:
            # Hack - make model work by cluster and not service!
            if self.id in self.cluster.weights:
                clusters_weights_map = self.cluster.weights[self.id][dependency.job_type]
            else:
                clusters_weights_map = self.cluster.weights[dependency.job_type]
            weights_sum = sum(clusters_weights_map.values())
            if abs(weights_sum-1) > 0.001: # More than 1% diviation should raise error
                print("self",self.full_name)
                print("dependency",dependency)
                print("weights_sum",weights_sum)
                print("clusters_weights_map",clusters_weights_map)
                raise
            for dest_cluster, weight in clusters_weights_map.items():
                if weight == 0:
                    continue
                # print("{} weights = {}".format(dest_cluster.id, weight))
                job_latency = self.zone.latency_per_request(dest_cluster.zone)
                new_job = Job(
                    source_zone=self.zone,
                    target_zone=dest_cluster.zone,
                    processing_duration=job.processing_duration,
                    load=job.load * weight,
                    type=dependency.job_type,
                    data_size_in_kb=dependency.req_size,
                    latency=job_latency,
                    source_job=job,
                )
                _propogated_jobs.append(new_job)
                # print("sending {} {}% portion of requests from {}, for job {}".format(job.target_zone.full_name, weight*100, self.zone.name, new_job.type))
                dest_cluster.consume(new_job, job.arrival_time+job_latency)
        job.propogated_jobs = _propogated_jobs
        # print("dependenceis dists = {}".format(job.propogated_jobs))

    @property
    def zone(self):
        return self.cluster.zone

    @property
    def full_name(self):
        return "-".join([self.job_type, self.zone.full_name])

    @property
    def jobs_consumed_per_time_slot(self):
        if len(self.job_data_frame.index) == 0:
            return self.capacity
        sum_load_df = self.job_data_frame.groupby("arrival_time")["load"].agg("sum")
        mean_job_count = sum_load_df.mean()
        if mean_job_count == 0 or np.isnan(mean_job_count):
            return self.capacity
        return mean_job_count

    def residual_capacity(self, at_tik):
        load = self.load(at_tik)
        return self.capacity - load

    def load(self, at_tik):
        selector = (self.job_data_frame["ttl"] > at_tik)
        jobs_not_done = self.job_data_frame.loc[selector]
        load = jobs_not_done["load"].sum()
        return load

    def add_to_cluster(self, cluster):
        logging.debug("service add_to_cluster - {}".format(cluster))
        self.cluster = cluster

    def consume(self, job):
        if job.type != self.job_type:
            raise
        logging.debug("service={}\nconsumes={} jobs\nat={}".format(self.full_name, job.load, job.arrival_time))
        # 1) Propogate to dependencies
        # Don't worry, if your app is DAG shaped, recursion will not happen!
        # We propogate before collecting data, so panelties will not apply on propogated requests if not needed
        self._propogate_by_weight(job)

        # 2) Apply penalty if needed
        # If service is loaded we need to increase latency, according to the load
        # st1 = time.time()
        load = self.load(job.arrival_time)
        res_cap = self.capacity - load
        if res_cap <= 0:
            # print("@@@@@@@@@@@@@@@@@@@@")
            # print(self.test_name)
            # print("service={}\ncap={}\nload={}\nnew imposed load={}".format(self.full_name, self.capacity, load, job.load))
            # print("processing_duration before penalty = {}\nprocessing_duration after penalty = {}".format(job.processing_duration, job.processing_duration * ((load+job.load) / self.capacity)))
            # print("@@@@@@@@@@@@@@@@@@@@")
            job.processing_duration = job.processing_duration * ( ((load+job.load) / self.capacity)**2 )

        # 3) Collect data
        self._collect(job)

    def reset_state(self):
        self.data_frames_count = 0
        self.data_frames_to_add = []
        cols_count = len(self._df_columns)
        self.job_data_frame = pd.DataFrame(
            [],#[[None for _ in range(cols_count)] for _ in range(self.expected_tiks)],
            columns = self._df_columns
        )
