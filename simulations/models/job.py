import uuid, random

class Job:
    """Representing a Job in the system"""

    def __init__(
        self,
        source_zone,
        target_zone,
        # processing_duration,
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

        # self.processing_duration = processing_duration
        self.load = load
        self.type = type
        self.data_size_in_kb = data_size_in_kb

        self.latency = latency
        self.work_latency = work_latency

        self.source_job = source_job

        self.arrival_time = None
        self.propogated_jobs = []
        self._duration = 0


    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

    def __repr__(self):
        if self.source_zone:
            return "{} -> {} = {}".format(self.source_zone.__repr__(), self.target_zone.__repr__(), self.load)
        return "-> {} = {}".format(self.target_zone.__repr__(), self.load)

    def processing_duration(self, load, cap):
        ratio = load / cap
        if ratio <= 0.2:
            return 0.18
        if ratio <= 1.0:
            return 0.35
        if ratio <= 1.2:
            return 3.8
        if ratio <= 1.6:
            return 1.4
        # 99% drop will help reducing the duration
        return 0.8

    def drop_percent(self, load, cap):
        ratio = load / cap
        if ratio <= 1.0:
            return 0
        # print("type: ", self.type)
        # print("load to cap ratio: ", ratio)
        # print("cap ", cap)
        if ratio <= 1.2:
            return 0.05
        if ratio <= 1.5:
            return 0.50
        if ratio <= 1.6:
            return 0.60
        if ratio <= 1.7:
            return 0.80
        
        # If the load is so big, drop with 0.99 prob
        return 0.99
    
    def duration(self, load, cap):
        if self._duration > 0:
            return self._duration
        max_dependency_duration = max([pj._duration for pj in self.propogated_jobs] + [0])
        self._duration = max_dependency_duration + self.processing_duration(load, cap) + self.latency
        return self._duration

    def ttl(self, load, cap):
        return self.arrival_time + self.duration(load, cap) #- self.latency
