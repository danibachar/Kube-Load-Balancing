import pandas as pd
import numpy as np
import uuid, logging, time
from models.kube import Job

class Service:
    """Representing a Kubernetes Service"""

    def __init__(self,
        job_type,
        dependencies,
        capacity,
        expected_outbound_req_size_kb,
        dest_func
    ):
        self.id = uuid.uuid4()

        self.job_type = job_type
        self.capacity = capacity / 10 # RPS
        self.cluster = None
        self.dependencies = dependencies

        self.expected_outbound_req_size_kb = expected_outbound_req_size_kb

        self.dest_func = dest_func

        self.loads_cache = {}

        self.data_frames_to_add = []
        self._df_columns = [
            "job_id", # str
            "job_type", # str
            "load", # float
            "arrival_time", # float
            "ttl", # float
            "duration",
            "zone_dependent_latency",
            "work_latency",
            "consumed", # bool
            "cost_in_usd", # float
            "size_in_gb", # float
            "source_zone_id",# str
            "target_zone_id",# str
            "source_job_id", # str
            "propogated_job_ids" # [str]
        ]
        self.job_data_frame = pd.DataFrame(
            self.data_frames_to_add,
            columns = self._df_columns
        )

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

    def __hash__(self):
        return self.job_type

    @property
    def zone(self):
        return self.cluster.zone

    @property
    def full_name(self):
        return "-".join([self.job_type, self.zone.full_name])

    def _supported_clusters_for(self, job_type):
        mesh = self.cluster.mesh.values()
        return list(filter(lambda c: job_type in c.supported_job_types(), mesh))

    def _fetch_all_similar_jobs(self):
        supported_clusters = self._supported_clusters_for(self.job_type)
        service_supporting_my_job_type = [cluster.service(self.job_type) for cluster in supported_clusters]
        jobs_avg = [s.jobs_consumed_per_time_slot for s in service_supporting_my_job_type]
        return jobs_avg

    @property
    def jobs_consumed_per_time_slot(self):
        mean_job_count = self.job_data_frame.groupby("arrival_time").size().mean()
        if mean_job_count == 0 or np.isnan(mean_job_count):
            return self.capacity
        return mean_job_count

    @property
    def jobs_consumed_per_time_slot_across_mesh(self):
        mesh_jobs = self._fetch_all_similar_jobs()
        mesh_jobs.append(self.jobs_consumed_per_time_slot)
        sum = np.sum(mesh_jobs)
        return sum

    def residual_capacity(self, at_tik):
        load = self.load(at_tik)
        return self.capacity - load

    def load(self, at_tik):
        # cached_load = self.loads_cache.get(at_tik,None)
        # if cached_load:
        #     print("hit")
        #     return cached_load
        selector = (self.job_data_frame["ttl"] > at_tik)
        jobs_not_done = self.job_data_frame.loc[selector]

        load = jobs_not_done["load"].sum()
        # self.loads_cache[at_tik]=load
        return load

    def add_to_cluster(self, cluster):
        logging.debug("service add_to_cluster - {}".format(cluster))
        self.cluster = cluster

    def clear_pending_jobs(self, tok):
        selector = self.job_data_frame["ttl"] <= tok
        self.job_data_frame.loc[selector, "consumed"] = True

    def consume(self, job):
        if job.type != self.job_type:
            raise
        logging.debug("service consume - {}".format(job))
        # If service is loaded we need to increase latency, according to the load
        current_load = self.load(job.arrival_time)
        if current_load >= self.capacity:
            print("@@@@@@@@@@@@@@@@@@@@")
            print("job duration penalty")
            print("@@@@@@@@@@@@@@@@@@@@")
            job._duration = job._duration*(current_load/current_cpacity)
        self._propogate(job)
        self._collect(job)

    def update_df(self):
        if len(self.data_frames_to_add) == 0:
            print("no df to add", self.full_name)
            print(self.zone.cost_func)
            return
        self.job_data_frame = pd.DataFrame(
            self.data_frames_to_add,
            columns = self._df_columns
        )

    def _calc_job_traffic_cost_and_size(self, job):
        # A job's total data is:
        # - The data we will send to the propogated jobs
        # +
        # - The data we will return to the client that sent the job
        # We don't pay for ingress, only egress
        one_million = 1_000_000
        size_in_gb = self.expected_outbound_req_size_kb/one_million
        cost_in_usd = 0

        cost_in_usd += size_in_gb * self.zone.price_per_gb(job.source_zone)

        for pj in job.propogated_jobs:
            s_gb = pj.data_size_in_kb/one_million
            size_in_gb += s_gb
            cost_in_usd += s_gb * self.zone.price_per_gb(pj.target_zone)
        return cost_in_usd, size_in_gb

    def _collect(self, job):
        source_job_id = None
        source_zone = job.source_zone
        if source_zone:
            source_job_id = source_zone.id
        source_zone_name = None
        if source_zone:
            source_zone_name = job.source_zone.full_name
        cost_in_usd, size_in_gb = self._calc_job_traffic_cost_and_size(job)

        self.data_frames_to_add.append([
            job.id,
            job.type,
            job.load,
            job.arrival_time,
            job.ttl,
            job.duration,
            job.zone_dependent_latency,
            job.work_latency,
            False,
            cost_in_usd,
            size_in_gb,
            source_zone_name,
            job.target_zone.full_name,
            source_job_id,
            [j.id for j in job.propogated_jobs]
        ])

    def _propogate(self, job):
        propogated_jobs = []
        for dependency in self.dependencies:
            target_cluster = self._choose_target_cluster(dependency)
            job_latency = self.zone.latency_per_request(target_cluster.zone)/1000

            new_job = Job(
                source_zone=self.zone,
                target_zone=target_cluster.zone,
                duration=job.duration,
                load=job.load,
                type=dependency.job_type,
                data_size_in_kb=dependency.req_size,
                zone_dependent_latency=job_latency,
                source_job=job,
            )
            propogated_jobs.append(new_job)

            target_cluster.consume(new_job, job.arrival_time+job_latency)

        job.propogated_jobs+=propogated_jobs

    def _choose_target_cluster(self, dependency):
        # Prefer local cluster if job is supported
        if dependency.job_type in self.cluster.supported_job_types():
            logging.info("service:{}\n_choose_target_cluster:{}\nfor dependency:{}\nLOCAL".format(self.full_name,self.cluster,dependency))
            return self.cluster

        # Choose from mesh according to dest function
        possible_clusters = self._supported_clusters_for(dependency.job_type)
        clusters_weights = list(map(lambda c: self.cluster.weights[dependency.job_type][c.zone], possible_clusters))
        key = self.full_name + "->" + dependency.job_type
        cluster = self.dest_func(possible_clusters, clusters_weights, key)
        logging.info("service:{}\n_choose_target_cluster:{}\nfor dependency:{}\nDEST_FUNC".format(self.full_name,cluster,dependency))
        return cluster
