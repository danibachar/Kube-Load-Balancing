import uuid

class Job:
    """Representing a Job in the system"""

    def __init__(
        self,
        source_zone,
        target_zone,
        processing_duration,
        load,
        type,
        data_size_in_kb=0,
        latency=0,
        work_latency=0,
        source_job=None,
    ):
        self.id = uuid.uuid4()

        self.source_zone = source_zone
        self.target_zone = target_zone

        self.processing_duration = processing_duration
        self.load = load
        self.type = type
        self.data_size_in_kb = data_size_in_kb

        self.latency = latency
        self.work_latency = work_latency

        self.source_job = source_job

        self.arrival_time = None
        self.propogated_jobs = []

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

    def __repr__(self):
        if self.source_zone:
            return "{} -> {} = {}".format(self.source_zone.__repr__(), self.target_zone.__repr__(), self.load)
        return "-> {} = {}".format(self.target_zone.__repr__(), self.load)

    @property
    def duration(self):
        max_dependency_duration = max([pj.duration for pj in self.propogated_jobs] + [0])
        return max_dependency_duration + self.processing_duration + self.latency

    @property
    def ttl(self):
        return self.arrival_time + self.duration - self.latency
