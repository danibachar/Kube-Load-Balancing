import collections, logging, time
import pandas as pd

class Cluster:
    """Representing a Kubernetes Cluster"""

    def __init__(self, zone):
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

    @property
    def id(self):
        return self.zone.name

    def service(self, job_type):
        return self.services.get(job_type, None)

    def add_service(self, service):
        if self.service(service.job_type) != None:
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

    def available_capacity(self, job_type, at_tik):
        service = self.service(job_type)
        if service is None:
            return -1 # incating no support at all
        return service.residual_capacity(at_tik)

    def update_weight_for(self, job_type, to_zone, weight):
        if job_type not in self.weights:
            self.weights[job_type] = {}

        self.weights[job_type][to_zone] = weight

    def clear_pending_jobs(self, tok):
        for service in self.services:
            service.clear_pending_jobs(tok)

    def prepare_for_weight_update(self):
        for service in self.services.values():
            service.update_df()

    def consume(self, job ,at_tik):
        # st = time.time()
        job.arrival_time = at_tik

        # logging.debug("cluster:{} consume - {}".format(self.id,job))
        service = self.service(job.type)
        if not service:
            logging.error("cluster:{}\ncannot consume:{} - not supported service".format(self.id,job))
            return
        service.consume(job)
        # print("cluster = {}\nconsumed job {}\nat tik  = {}\nwith ttl = {}".format(self.id, job.type, at_tik, job.ttl))
        # print("cluster consume job took", time.time()-st)
