import collections, logging

class Cluster:
    """Representing a Kubernetes Cluster"""

    def __init__(self, zone):
        self.zone = zone
        self.services = collections.OrderedDict()
        self.mesh = collections.OrderedDict()
        self.weights = {}
        self._is_available = True

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

    @property
    def supported_job_types(self):
        return set(self.services.keys())
    
    @property
    def is_available(self):
        return self._is_available

    def service(self, job_type):
        if not self._is_available:
            return None
        return self.services.get(job_type, None)

    def add_service(self, service):
        if self.service(service.job_type) != None:
            logging.error("trying to add service with job type that already exists")
            return
        service.add_to_cluster(self) # settings cluster <-> service connection
        self.services[service.job_type] = service

    def join_cluster(self, cluster):
        logging.debug("join_cluster - {}".format(cluster))
        if self.id == cluster.id:
            return
        if self.mesh.get(cluster.id, None) is not None:
            return
        self.mesh[cluster.id] = cluster
        cluster.join_cluster(self)

    def remove_cluster(self, cluster):
        logging.debug("remove_cluster - {}".format(cluster))
        self.mesh[cluster.id] = None

    def available_capacity(self, job_type, at_tik):
        if not self._is_available:
            return 0
        service = self.service(job_type)
        if service is None:
            return -1 # incating no support at all
        return service.residual_capacity(at_tik)

    def reset_state(self):
        self.weights = {}
        self._is_available = True
        for service in self.services.values():
            service.reset_state()

    def build_services_df(self):
        for service in self.services.values():
            service.build_df()

    def consume(self, job ,at_tik):
        if not self._is_available:
            logging.error("cluster:{}\ncannot consume:{} - cluster is not available".format(self.id, job))
            raise Exception("Trying to consume for non active cluster")
        job.arrival_time = at_tik
        logging.debug("cluster:{} consume - {}".format(self.id,job))
        srv = self.service(job.type)
        if not srv:
            logging.error("cluster:{}\ncannot consume:{} - not supported service".format(self.id, job))
            return
        srv.consume(job)
