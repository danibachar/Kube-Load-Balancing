
class Zone:
    """Representing a Topology"""

    def __init__(self, id, region, cloud_provider, pricing):
        self.id = id
        self.region = region
        self.cloud_provider = cloud_provider
        self.pricing = pricing

    @property
    def name(self):
        return "-".join([self.cloud_provider.id, self.region.id,])

    @property
    def full_name(self):
        return "-".join([self.name, self.id])

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

class CloudProvider:
    """Representing a Cloud Provider"""

    def __init__(self, id):
        self.id = id

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

class Region:
    """Representing a Cloud Provider's Region"""

    def __init__(self, id):
        self.id = id

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)
