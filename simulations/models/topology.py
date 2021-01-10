import logging

class Zone:
    """Representing a Topology"""

    def __init__(self, id, region, cloud_provider, latency, pricing):
        self.id = id
        self.region = region
        self.cloud_provider = cloud_provider
        self.latency = _generate_latency_map_for_zone(latency, self)
        self.pricing = pricing

        logging.debug("latency: {} -> {}".format(self.full_name, self.latency))
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
            return 0.15
        # return  self.pricing[self.full_name][other_zone.full_name]

        logging.debug("checking price from:{} <-> to:{}".format(self.name, other_zone.name))

        is_same_zone = self == other_zone
        if is_same_zone:
            return self.pricing["zones"]["from"]["all"]

        is_same_region = self.region == other_zone.region
        is_same_cloud_provider = self.cloud_provider == other_zone.cloud_provider
        if is_same_region and is_same_cloud_provider:
            key = _region_key(self.region)
            return self.pricing["regions"]["from"][key]

        # If we have sepecial key for cross-region within same cp
        if is_same_cloud_provider and "cross-regions" in self.pricing:
            key = _cross_regions_key(self.region)
            return self.pricing["cross-regions"]["from"][key]

        # Traffic goes world wide
        f, t = _world_wide_from_to_keys(self.region, other_zone.region)
        return self.pricing["worldwide"]["from"][f]["to"][t]["10TB"]

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


def _generate_pricing_map_for_zone(pricing, zone):
    cloud_provider_map = pricing[zone.cloud_provider.id]
    # print(cloud_provider_map)

    return {
        "aws-us-east-1": {
            "aws-us-east-1": 0.01,
            "aws-sa-east-1": 0.09,
            "gcp-us-west-1": 0.09,
            "gcp-eu-west-1": 0.09,
            "gcp-asia-east-1": 0.09,
        },
        "aws-sa-east-1": {
            "aws-us-east-1": 0.138,
            "aws-sa-east-1": 0.01,
            "gcp-us-west-1": 0.15,
            "gcp-eu-west-1": 0.15,
            "gcp-asia-east-1": 0.15,
        },
        "gcp-us-west-1": {
            "aws-us-east-1": 0.12,
            "aws-sa-east-1": 0.12,
            "gcp-us-west-1": 0.0,
            "gcp-eu-west-1": 0.08,
            "gcp-asia-east-1": 0.08,
        },
        "gcp-eu-west-1": {
            "aws-us-east-1": 0.12,
            "aws-sa-east-1": 0.12,
            "gcp-us-west-1": 0.02,
            "gcp-eu-west-1": 0.0,
            "gcp-asia-east-1": 0.02,
        },
        "gcp-asia-east-1": {
            "aws-us-east-1": 0.12,
            "aws-sa-east-1": 0.12,
            "gcp-us-west-1": 0.08,
            "gcp-eu-west-1": 0.08,
            "gcp-asia-east-1": 0.0,
        },
    }
def _region_key(source_region):
    if any(ext in source_region.id for ext in ["us", "america", "canada"]):
        return "US"
    if any(ext in source_region.id for ext in ["eu"]):
        return "EU"
    if any(ext in source_region.id for ext in ["ap", "asia"]):
        return "AP"
    if any(ext in source_region.id for ext in ["sa",]):
        return "SA"
    if any(ext in source_region.id for ext in ["af"]):
        return "AF"
    raise

def _cross_regions_key(source_region):
    if any(ext in source_region.id for ext in ["ap-southeast-1", "australia", "sydney"]):
        return "OCEANIA"
    return "MOST"

def _world_wide_from_to_keys(source_region, target_region):

    if any(ext in source_region.id for ext in ["us", "america", "canada"]):
        return "US", _cross_regions_key(target_region)
    if "eu" in source_region.id:
        return "EU", _cross_regions_key(target_region)
    if any(ext in source_region.id for ext in ["ap-northeast", "asia-northeast"]):
        return "AP-NORTHEAST", _cross_regions_key(target_region)
    if any(ext in source_region.id for ext in ["ap", "asia"]):
        return "AP-SOUTH", _cross_regions_key(target_region)
    if any(ext in source_region.id for ext in ["ap-southeast-1", "australia", "sydney"]):
        return "OCEANIA", "MOST"
    if any(ext in source_region.id for ext in ["ap", "asia"]):
        return "AP-EAST", _cross_regions_key(target_region)
    if any(ext in source_region.id for ext in ["sa",]):
        return "SA", _cross_regions_key(target_region)
    if any(ext in source_region.id for ext in ["af"]):
        return "AF", _cross_regions_key(target_region)
    raise
