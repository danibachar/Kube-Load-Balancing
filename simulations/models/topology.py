import logging, requests, xmltodict, random
from ratelimit import limits, sleep_and_retry

cache = {}

# Free API is limited to one request per second, which is ok
ONE_SEC = 1
MAX_CALLS_PER_SEC = 1
@sleep_and_retry
@limits(calls=MAX_CALLS_PER_SEC, period=ONE_SEC)
def _remote_gmt_offset_by(url):
    res = requests.get(url)
    result = xmltodict.parse(res.content)
    offset = result.get("result", {}).get("gmtOffset", "-1")
    return int(offset) / 60 # minutes

def gmt_offset_by(lon, lat, counter=0): 
    url = "http://api.timezonedb.com/v2.1/get-time-zone?key=F82EPEI8QYD1&by=position&lat={}&lng={}".format(lat, lon)
    cached_offset = cache.get(url, None)
    if cached_offset is not None:
        return cached_offset
    offset = _remote_gmt_offset_by(url)
    cache[url] = offset
    return offset

class Zone:
    """Representing a Topology"""

    def __init__(self, id, region, cloud_provider, latency, pricing):
        self.id = id
        self.region = region
        self.cloud_provider = cloud_provider
        self.latency = _generate_latency_map_for_zone(latency, self)
        self.pricing = pricing

        logging.debug("latency: {} -> {}".format(self.name, self.latency))
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

    @property
    def location(self):
        return self.region.location

    def price_per_gb(self, other_zone):
        if other_zone is None:
            return 0.15
            
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
        logging.debug("checking latency from:{} <-> to:{}".format(self.name, other_zone.name))
        if other_zone.name not in self.latency:
            raise
        latency = self.latency.get(other_zone.name, 0) / 1000
        # Randomize some diviation in the latency
        return latency # + latency * random.uniform(-0.1, 0.1)

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

    def __init__(self, id, location):
        self.id = id
        self.location = location
        self.gmt_offset = gmt_offset_by(location["lon"], location["lat"])

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self,other):
        return self.id == other.id and self.location == other.location

def _generate_latency_map_for_zone(latencies, zone):
    my_index = _latency_index_for(latencies, zone)
    if my_index == -1:
        raise
    if my_index >= len(latencies):
        raise
    _map = {}
    latencies_from_me_to_others = latencies[my_index][zone.name]
    for other_zone_idx in range(len(latencies_from_me_to_others)):
        other_zone_map = latencies[other_zone_idx]
        zone_name = list(other_zone_map.keys())

        if len(zone_name) > 1:
            raise

        _map[zone_name[0]] = latencies_from_me_to_others[other_zone_idx]

    return _map

def _latency_index_for(latency_matrix, zone):
    for idx, latency_map in enumerate(latency_matrix):
        if zone.name in latency_map:
            return idx
    return -1

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
    # if any(ext in source_region.id for ext in ["ap-southeast-2", "australia", "sydney"]):
    #     return "OCEANIA"
    # return "MOST"
    if any(ext in source_region.id for ext in ["us", "america", "canada"]):
        return "US"
    if "eu" in source_region.id:
        return "EU"
    if any(ext in source_region.id for ext in ["ap-northeast", "asia-northeast"]):
        return "AP"
    if any(ext in source_region.id for ext in ["ap", "asia"]):
        return "AP"
    if any(ext in source_region.id for ext in ["ap-southeast-2", "australia", "sydney"]):
        return "OCEANIA"
    if any(ext in source_region.id for ext in ["ap", "asia"]):
        return "AP"
    if any(ext in source_region.id for ext in ["sa",]):
        return "SA"
    if any(ext in source_region.id for ext in ["af"]):
        return "AF"
    raise

def _world_wide_from_to_keys(source_region, target_region):
    def _cross_regions_key(source_region):
        if any(ext in source_region.id for ext in ["ap-southeast-2", "australia", "sydney"]):
            return "OCEANIA"
        return "MOST"
    if any(ext in source_region.id for ext in ["us", "america", "canada"]):
        return "US", _cross_regions_key(target_region)
    if "eu" in source_region.id:
        return "EU", _cross_regions_key(target_region)
    if any(ext in source_region.id for ext in ["ap-northeast", "asia-northeast"]):
        return "AP-NORTHEAST", _cross_regions_key(target_region)
    if any(ext in source_region.id for ext in ["ap", "asia"]):
        return "AP-SOUTH", _cross_regions_key(target_region)
    if any(ext in source_region.id for ext in ["ap-southeast-2", "australia", "sydney"]):
        return "OCEANIA", "MOST"
    if any(ext in source_region.id for ext in ["ap", "asia"]):
        return "AP-EAST", _cross_regions_key(target_region)
    if any(ext in source_region.id for ext in ["sa",]):
        return "SA", _cross_regions_key(target_region)
    if any(ext in source_region.id for ext in ["af"]):
        return "AF", _cross_regions_key(target_region)
    raise
