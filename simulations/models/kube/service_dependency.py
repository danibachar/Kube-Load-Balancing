class ServiceDependency:
    def __init__(self, job_type, req_size):
        self.job_type = job_type
        self.req_size = req_size

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)
