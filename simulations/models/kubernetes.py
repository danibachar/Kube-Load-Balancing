import time, random, math, json, threading, logging, collections, uuid
from datetime import datetime
from collections import Counter
from multiprocessing.pool import ThreadPool

class Cluster:
    """Representing a Kubernetes Cluster"""

    def __init__(self, id, zone):
        self.id = id
        self.zone = zone
        self.services = {}
        self.mesh = collections.OrderedDict()
        self.weights = {}

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

    def __hash__(self):
        h = hash((self.id, self.zone))
        return h

    def __eq__(self, other):
        return self.id == other.id and self.zone == other.zone

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

    def available_capacity(self, job_type, at_tik):
        service = self._service(job_type)
        if service is None:
            return -1 # incating no support at all
        return service.residual_capacity

    def update_weight_for(self, job_type, to_zone, weight):
        if job_type not in self.weights:
            self.weights[job_type] = {}

        self.weights[job_type][to_zone] = weight

    def consume(self, job):
        job.arrival_time = datetime.now()
        logging.debug("cluster:{} consume - {}".format(self.id,job))
        service = self._service(job.type)
        if not service:
            logging.error("cluster:{}\ncannot consume:{} - not supported service".format(self.id,job))
            return False
        return service.consume(job)

    def thread_clenup(self):
        logging.info("cluster:{} thread_clenup:{}".format(self.id,len(self.services)))
        for s in self.services.values():
            s.thread_clenup()

    def sum_traffic_sent(self):
        traffic_sum = {}
        for service in self.services.values():
            for zone, traffic_map in service.total_traffic_sent.items():
                if zone not in traffic_sum:
                    traffic_sum[zone] = {}
                res = Counter(traffic_sum[zone])
                s = Counter(traffic_map)
                traffic_sum[zone] = dict(res+s)

        return traffic_sum

    def reset_traffic_sent(self):
        for service in self.services.values():
            service.reset_traffic_sent()

class Service:
    """Representing a Kubernetes Service"""

    def __init__(self, id, dependencies, job_type, capacity, dest_func):
        self.id = id
        self.job_type = job_type
        self.capacity = capacity # RPS
        self.THREAD_POOL = None
        # self.THREAD_POOL = ThreadPool(processes=capacity)
        self.dest_func = dest_func
        self.consumed_jobs = set()
        self.dependencies = dependencies
        self.total_traffic_sent = {} # cluster to amount map
        self.load = 0
        self.cluster = None
        self.reduce_capacity_jobs = []
        self.jobs_consumed_per_time_slot = [[0]]

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

    def reset_traffic_sent(self):
        self.jobs_consumed_per_time_slot.append([0])
        self.total_traffic_sent = {}

    def consume(self, job):
        logging.debug("service consume - {}".format(job))
        self.jobs_consumed_per_time_slot[-1]+=1
        self.consumed_jobs.add(job)
        return self._send(job)

    def thread_clenup(self):
        logging.info("service:{} wait_for_jobs_to_finish:{}".format(self.full_name,len(self.reduce_capacity_jobs)))
        if self.THREAD_POOL != None:
            self.THREAD_POOL.close()

    def _send(self, job):
        self.load += job.load
        # Needs to propogate the job for each dependency
        futures = []
        for dependency in self.dependencies:
            target_cluster = self._choose_target_cluster(dependency)
            if target_cluster.zone not in self.total_traffic_sent:
                self.total_traffic_sent[target_cluster.zone] = {}
            if dependency.job_type not in self.total_traffic_sent[target_cluster.zone]:
                self.total_traffic_sent[target_cluster.zone][dependency.job_type] = 0

            self.total_traffic_sent[target_cluster.zone][dependency.job_type]+=1

            new_job = Job(self.cluster, job.duration, job.load, dependency.job_type)
            logging.info("service:{}\n_send\njob{}\nto:{}".format(self.full_name,new_job,target_cluster))
            # async_result = self.THREAD_POOL.apply_async(target_cluster.consume, (new_job,)) # tuple of args for foo
            async_result = target_cluster.consume(new_job)
            futures.append(async_result)


        # time.sleep(job.duration) # Wait for me
        did_succeed = True
        for f in futures:
            # did_succeed = did_succeed and f.get()
            did_succeed = did_succeed and f
        self.load -= job.load
        logging.info("service:{}\ndone".format(self.full_name))
        return did_succeed

    def _choose_target_cluster(self, dependency):
        # Prefer local cluster if job is supported
        if dependency.job_type in self.cluster.supported_job_types():
            logging.info("service:{}\n_choose_target_cluster:{}\nfor dependency:{}\nLOCAL".format(self.full_name,self.cluster,dependency))
            return self.cluster

        # Choose from mesh according to dest function
        mesh = list(self.cluster.mesh.values())
        possible_clusters = list(filter(lambda c: dependency.job_type in c.supported_job_types(), mesh))
        clusters_weights = list(map(lambda c: self.cluster.weights[dependency.job_type][c.zone], possible_clusters))
        key = self.full_name + "->" + dependency.job_type
        cluster = self.dest_func(possible_clusters, clusters_weights, key)
        # print("choose:{}\nfor:{}\nfrom possible:{}\nby:{}".format(cluster.id, dependency.job_type, [pc.id for pc in possible_clusters], self.full_name))
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

    def __init__(self, source_cluster, duration, load, type, source_job=None,job_latency=0):
        self.id = uuid.uuid4()
        self.source_cluster = source_cluster
        self.target_cluster = None

        self.duration = duration
        self.load = load

        self.type = type
        self.arrival_time = None
        self.source_job = source_job
        self.propogated_jobs = []
        self.job_latency = job_latency

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id
