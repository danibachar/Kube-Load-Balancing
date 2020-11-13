from models.consts import bookinfo_application_location_graph
from models.topology import CloudProvider, Region, Zone
from models.kubernetes import Cluster, Service, ServiceDependency

def generate_application(destination_func):

    # First zones!
    locations = bookinfo_application_location_graph["locations"]
    pricing = bookinfo_application_location_graph["pricing"]
    zones = _generate_zones(locations, pricing)
    # Second Service!
    services_config = bookinfo_application_location_graph["services_config"]
    clusters_info = bookinfo_application_location_graph["clusters"]
    clusters = _generate_clusters(clusters_info, zones, services_config, destination_func)
    _create_full_cluster_mesh(clusters)
    return clusters, "product_page"

def _create_full_cluster_mesh(clusters):
    for idx in range(0, len(clusters)):
        cluster = clusters[idx]
        for c in clusters:
            if c.id == cluster.id:
                continue
            cluster.join_cluster(c)

def _generate_clusters(clusters_inf, zones, services_config, destination_func):
    def zone_by_name(zones, name):
        return list(filter(lambda z: z.name == name, zones))
    clusters = []
    for idx, (full_zone_name, cluster) in enumerate(clusters_inf.items()):
        zone = zone_by_name(zones, full_zone_name)[0]
        cluster_services = cluster["services"]
        latency_map = cluster["latency"]
        c = _generate_cluster(full_zone_name, cluster_services, zone, latency_map, services_config, destination_func)
        clusters.append(c)
    return clusters

def _generate_cluster(id, cluster_services, zone, latency_map, services_config, destination_func):
    cluster = Cluster(id, zone, latency_map)
    services = _generate_services(cluster_services, zone, services_config, destination_func)
    for service in services:
        cluster.add_service(service)
    return cluster

def _generate_services(cluster_services, zone, services_config, destination_func):
    services = []
    for cs in cluster_services:
        service = _generate_service(cs[0], cs[1], services_config, destination_func)
        services.append(service)
    return services

def _generate_service(service_name, service_capacity, services_config, destination_func):
    s_config = services_config[service_name]
    dependencies = []
    for dep_srv_name in s_config["dependencies"]:
        req_size = services_config[dep_srv_name]["incoming_req_size"]
        dep = ServiceDependency(dep_srv_name, req_size)
        dependencies.append(dep)

    service = Service(service_name, dependencies, service_name, service_capacity, destination_func)
    return service

def _generate_zones(locations, pricing):
    zones = []
    for location in locations:
        zone_parts = location.split("-")
        zone = _generate_zone(zone_parts, pricing)
        zones.append(zone)
    return zones

def _generate_zone(zone_parts, pricing):
    if len(zone_parts) != 3:
        print("Zone must be complete - ", zone_parts)
        return None

    cp = CloudProvider(zone_parts[0])
    region = Region("-".join(zone_parts[1:3]))
    zone = Zone("1", region, cp, pricing)
    return zone
