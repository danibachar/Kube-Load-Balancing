import logging

class Zone:
    """Representing a Topology"""

    def __init__(self, id, region, cloud_provider, pricing, latency, cost_func):
        self.id = id
        self.region = region
        self.cloud_provider = cloud_provider
        self.pricing = pricing
        self.latency = latency
        self.cost_func = cost_func

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

    def __repr__(self):
        return self.full_name

    def __hash__(self):
        h = hash((self.region, self.cloud_provider))
        return h

    def __eq__(self, other):
        return self.region == other.region and self.cloud_provider == other.cloud_provider

    @property
    def name(self):
        return "-".join([self.cloud_provider.id, self.region.id,])

    @property
    def full_name(self):
        return "-".join([self.name, self.id])

    def weight_according_to(self, other_zone):

        min_price = self.pricing["cross-zone"]
        min_latency = min(self.latency.values())
        price = self.price_per_request(other_zone)
        latency = self.latency_per_request(other_zone)

        return self.cost_func(price, latency, min_price, min_latency)

    def price_per_request(self, other_zone):
        logging.debug("checking price from:{} <-> to:{}".format(self.name, other_zone.name))
        logging.debug("pricing:{}".format(self.pricing))
        is_same_cloud_provider = self.cloud_provider == other_zone.cloud_provider
        is_same_region = self.region == other_zone.region
        if is_same_cloud_provider:
            if is_same_region:
                return self.pricing["cross-zone"]
            return self.pricing["cross-region"]
        return self.pricing["internet"]

    def latency_per_request(self, other_zone):
        logging.debug("checking latency from:{} <-> to:{}".format(self.name, other_zone.name))
        logging.debug("latency:{}".format(self.latency))
        return self.latency.get(other_zone.name, None)

class CloudProvider:
    """Representing a Cloud Provider"""

    def __init__(self, id):
        self.id = id

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self,other):
        return self.id == other.id


class Region:
    """Representing a Cloud Provider's Region"""

    def __init__(self, id):
        self.id = id

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self,other):
        return self.id == other.id
