import collections, logging, time
import pandas as pd

class Cluster:
    """Representing a Kubernetes Cluster"""

    def __init__(self, zone):
        self.zone = zone
        self.services = collections.OrderedDict()
        self.mesh = collections.OrderedDict()
        self.weights = {}

    def __repr__(self):
        return self.zone.__repr__()

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
        
    def reset_state(self):
        for service in self.services.values():
            service.reset_state()

    def consume(self, job ,at_tik):
        job.arrival_time = at_tik
        logging.debug("cluster:{} consume - {}".format(self.id,job))
        srv = self.service(job.type)
        if not srv:
            logging.error("cluster:{}\ncannot consume:{} - not supported service".format(self.id, job))
            return
        srv.consume(job)
