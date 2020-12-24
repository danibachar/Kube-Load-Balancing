import logging

class Zone:
    """Representing a Topology"""

    def __init__(self, id, region, cloud_provider, latency, pricing, cost_func):
        self.id = id
        self.region = region
        self.cloud_provider = cloud_provider
        self.pricing = pricing
        self.cost_func = cost_func
        self.latency = _generate_latency_map_for_zone(latency, self)

        logging.debug("latency:{}".format(self.latency))
        logging.debug("pricing:{}".format(self.pricing))

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

    def price_per_gb(self, other_zone):
        if other_zone is None:
            return 0.09

        logging.debug("checking price from:{} <-> to:{}".format(self.name, other_zone.name))

        is_same_cloud_provider = self.cloud_provider == other_zone.cloud_provider
        is_same_region = self.region == other_zone.region
        # if self == other_zone:
        #     return 0
        if is_same_cloud_provider:
            if is_same_region:
                return 0.01
            return 0.02

        return 0.09

    def latency_per_request(self, other_zone):
        logging.debug("checking latency from:{} <-> to:{}".format(self.full_name, other_zone.full_name))
        if other_zone.full_name not in self.latency:
            raise
        latency = self.latency.get(other_zone.full_name, 0)
        return latency

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

def _generate_latency_map_for_zone(latencies, zone):
    my_index = _latency_index_for(latencies, zone)
    if my_index == -1:
        raise
    if my_index >= len(latencies):
        raise
    _map = {}
    latencies_from_me_to_others = latencies[my_index][zone.full_name]
    for other_zone_idx in range(len(latencies_from_me_to_others)):
        other_zone_map = latencies[other_zone_idx]
        zone_name = list(other_zone_map.keys())

        if len(zone_name) > 1:
            raise

        _map[zone_name[0]] = latencies_from_me_to_others[other_zone_idx]

    return _map

def _latency_index_for(latency_matrix, zone):
    for idx, latency_map in enumerate(latency_matrix):
        if zone.full_name in latency_map:
            return idx
    return -1
