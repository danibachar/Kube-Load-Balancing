
def construct_service_to_service_key(source_service, source_cluster, target_service, target_cluster):
    return "{}.{}-{}.{}".format(
        source_service,
        source_cluster,
        target_service,
        target_cluster
    )

def reconstruct_service_cluster_from_key(key):
    source, target = key.split("-")
    source_service, source_cluster = source.split(".")
    target_service, target_cluster = target.split(".")
    return source_service, source_cluster, target_service, target_cluster
