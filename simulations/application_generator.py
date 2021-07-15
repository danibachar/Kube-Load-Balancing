import models
from models import CloudProvider, Region, Zone, Cluster, Service, ServiceDependency

def generate_application(app_map, latency_map, pricing_map, datacenters_map, app_name):
    clusters = _gen_clusters(app_map, latency_map, pricing_map, datacenters_map)
    for cluster in clusters:
        cluster.app_name = app_name

    _create_full_cluster_mesh(clusters)

    front_ends = _get_front_end_name(app_map)

    return clusters, front_ends

def _get_front_end_name(app):
    services = app["services"]
    fronts = []
    for service in services.values():
        if service.get("label",None) == "front-end":
            fronts.append(service["name"])
    return fronts

def _gen_clusters(app, latency, pricing, datacenters_map):
    services_config = app["services"]
    topology = app["app-topology"]
    clusters = []
    for zone_name, zone_cluster_details in topology.items():
        cluster = _gen_cluster(
            zone_name,
            zone_cluster_details,
            latency,
            pricing,
            datacenters_map,
            services_config
        )
        clusters.append(cluster)
    return clusters

def _gen_cluster(zone_name, zone_cluster_details, latency, pricing, datacenters_map, services_config):

    zone = _gen_zone(zone_name, latency, pricing, datacenters_map)
    cluster = Cluster(zone)

    available_services = zone_cluster_details["services"]

    for service in available_services.values():
        service_name = service["name"]
        service_capacity = service["rps_capacity"]
        svc = _gen_service(services_config[service_name], service_capacity)
        cluster.add_service(svc)

    return cluster

def _gen_zone(zone_name, latency, pricing, datacenters_map):
    supported_cloud_providers = set({"aws", "gcp"})

    zone_parts = zone_name.split("-")

    if len(zone_parts) < 2:
        print("Zone must be complete - ", zone_parts)
        return None

    cp_name = zone_parts[0]
    if cp_name not in supported_cloud_providers:
        print("Unsupported cloud provider - ", cp_name)
        return None
    cp = CloudProvider(cp_name)
    region_name = "-".join(zone_parts[1:len(zone_parts)])
    region_location = datacenters_map[cp_name + "-" + region_name]["location"]
    region = Region(region_name, region_location)
    zone = Zone("1", region, cp, latency, pricing[cp_name])

    return zone

def _gen_service(service_config, capacity):
    dependencies = []
    for dep in service_config["dependencies"].values():
        name = dep["name"]
        his_in = dep["req_size"]
        dep = ServiceDependency(name, his_in)
        dependencies.append(dep)

    my_out = service_config["expected-outbound-req-size-kb"]
    service_name = service_config["name"]
    service = Service(
        job_type=service_name,
        dependencies=dependencies,
        capacity=capacity,
        expected_outbound_req_size_kb=my_out
    )
    return service

def _create_full_cluster_mesh(clusters):
    for idx in range(0, len(clusters)):
        cluster = clusters[idx]
        for c in clusters:
            if c.id == cluster.id:
                continue
            cluster.join_cluster(c)
