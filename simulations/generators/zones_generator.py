from models.consts import base_topology_map
from models.topology import CloudProvider, Region, Zone
from utils.distributions import normal_choice

def generate_zones(clusters_count=3):
    zones = _zones(clusters_count)
    return zones

def _zones(clusters_count):
    # Normal distribution for choosing the clusters locations
    all_zones = _build_zones()
    zones = []
    for i in range(0, clusters_count):
        zones.append(normal_choice(all_zones))
    return zones

def _build_zones():
    zones = []
    for cp_name, cp in base_topology_map.items():
        cp_model = CloudProvider(cp_name)
        pricing = cp["pricing"]
        regions_map = cp["regions"]
        for global_region_name, global_region in regions_map.items():
            for region_name, region in global_region.items():
                for sub_region_name, sub_region in region.items():
                    # Zones we can choose uniformally from within the options
                    zone_id = np.random.choice(sub_region["zones"], 1)
                    region = Region(_construct_region_id(global_region_name,region_name,sub_region_name))
                    zones.append(Zone(zone_id, region, cp_model, pricing))
    return zones

# DNS like convention
def _construct_region_id(global_region_name, region_name, sub_region_name):
    return "-".join([global_region_name,region_name,sub_region_name])
