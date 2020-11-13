import time, random, math, json, threading
from datetime import datetime
from collections import Counter
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

class Cluster:
    """Representing a Kubernetes Cluster"""

    def __init__(self, id, zone, latency_map):
        self.id = id
        self.zone = zone
        self.latency_map = latency_map
        self.services = {}
        self.mesh = {}

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

    def _service(self, job_type):
        return self.services.get(job_type, None)

    def add_service(self, service):
        if self._service(service.job_type) != None:
            logging.error("trying to add service with job type that already exists")
            return
        service.add_to_cluster(self) # settings cluster <-> service connection
        self.services[service.job_type] = service

    def join_cluster(self, cluster):
        logging.debug("join_cluster - {}".format(cluster))
        self.mesh[cluster.id] = cluster

    def remove_cluster(self, clsuter):
        logging.debug("remove_cluster - {}".format(cluster))
        self.mesh[cluster.id] = None

    def supported_job_types(self):
        return set(self.services.keys())

    def available_zones(self):
        services = set(self.services.values())
        return set(map(lambda service: service.zone, services))

    def available_capacity(job_type):
        services = self._service(job_type)
        if service is None:
            return -1 # incating no support at all
        return service.residual_capacity

    def consume(self, job):
        job.arriavl_time = datetime.now()
        logging.info("cluster:{} consume - {}".format(self.id,job))
        self._service(job.type).consume(job)

    def wait_for_jobs_to_finish(self):
        logging.info("cluster:{} wait_for_jobs_to_finish:{}".format(self.id,len(self.services)))
        for s in self.services.values():
            s.wait_for_jobs_to_finish()

    def sum_traffic_sent(self):
        traffic_sum = {}
        for service in self.services.values():
            for cluster_name, traffic_map in service.total_traffic_sent.items():
                if cluster_name not in traffic_sum:
                    traffic_sum[cluster_name] = {}
                res = Counter(traffic_sum[cluster_name])
                s = Counter(traffic_map)
                traffic_sum[cluster_name] = dict(res+s)

        return traffic_sum


class Service:
    """Representing a Kubernetes Service"""

    def __init__(self, id, dependencies, job_type, capacity, dest_func):
        self.id = id
        self.job_type = job_type
        self.capacity = capacity # RPS
        self.dest_func = dest_func
        self.consumed_jobs = []
        self.dependencies = dependencies
        self.total_traffic_sent = {} # cluster to amount map
        self.load = 0
        self.cluster = None
        self.reduce_capacity_jobs = []

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

    @property
    def residual_capacity(self):
        return self.capacity - self.load

    def add_to_cluster(self, cluster):
        logging.debug("service add_to_cluster - {}".format(cluster))
        self.cluster = cluster

    def consume(self, job):
        logging.debug("service consume - {}".format(job))
        self.consumed_jobs.append(job)
        # 1) Reduce capacity by job.load for job.duration time
        self._reduce_capacity(job.load, job.duration)
        # 2) propogate requests to dependencies
        self._send(job)

    def wait_for_jobs_to_finish(self):
        logging.info("service:{} wait_for_jobs_to_finish:{}".format(self.full_name,len(self.reduce_capacity_jobs)))
        for j in self.reduce_capacity_jobs:
            j.join()

    def _reduce_capacity(self, load, duration):
        logging.info("service:{} _reduce_capacity - load={}, duration={}".format(self.full_name,load,duration))
        def time_load(load, duration):
            logging.debug("service:{}\ntime_load:begin, current load = {}, load to add = {}".format(self.full_name, self.load, load))
            self.load += load
            time.sleep(duration)
            self.load -= load
            logging.debug("service:{}\ntime_load:end, current load = {}, load to add = {}".format(self.full_name, self.load, load))
        thread = threading.Thread(target = time_load, args = (load, duration))
        self.reduce_capacity_jobs.append(thread)
        thread.start()

    def _send(self, job):
        # Needs to propogate the job for each dependency
        # For simplecity we take the same duration
        for dependency in self.dependencies:
            target_cluster = self._choose_target_cluster(dependency)
            if target_cluster.id not in self.total_traffic_sent:
                self.total_traffic_sent[target_cluster.id] = {}
            if dependency.job_type not in self.total_traffic_sent[target_cluster.id]:
                self.total_traffic_sent[target_cluster.id][dependency.job_type] = 0
            self.total_traffic_sent[target_cluster.id][dependency.job_type]+=1

            new_job = Job(self.cluster.id, job.duration, job.load, dependency.job_type)
            logging.info("service:{}\n_send\njob{}\nto:{}".format(self.full_name,new_job,target_cluster))
            target_cluster.consume(new_job)

    def _choose_target_cluster(self, dependency):
        # Prefer local cluster if job is supported
        if dependency.job_type in self.cluster.supported_job_types():
            logging.info("service:{}\n_choose_target_cluster:{}\nfor dependency:{}\nLOCAL".format(self.full_name,self.cluster,dependency))
            return self.cluster
        # Choose from mesh according to dest function
        mesh = list(self.cluster.mesh.values())
        possible_clusters = list(filter(lambda c: dependency.job_type in c.supported_job_types(), mesh))
        cluster = self.dest_func(possible_clusters, self.cluster.id)
        logging.info("service:{}\n_choose_target_cluster:{}\nfor dependency:{}\nDEST_FUNC".format(self.full_name,cluster,dependency))
        return cluster

class ServiceDependency:
    def __init__(self, job_type, req_size):
        self.job_type = job_type
        self.req_size = req_size

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

class Job:
    """Representing a Job in the system"""

    def __init__(self, source_cluster, duration, load, type):
        self.source_cluster = source_cluster
        self.duration = duration
        self.load = load
        # self.available_destinations = available_destinations
        self.type = type
        self.arriavl_time = None

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)
