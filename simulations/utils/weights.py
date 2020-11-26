
def _weights_for_swrr(job_type, current_zone, mesh):
    def normalize(weight, weight_sum, num_of_options):
        percent = (1 - weight / weight_sum) /  max(1, num_of_options - 1)
        return percent

    possible_clusters = list(filter(lambda c: job_type in c.supported_job_types(), mesh.values()))
    clusters_costs = list(map(lambda c: cost_for(current_zone, c.zone), possible_clusters))

    cost_sum = sum(clusters_costs)
    num_of_options = len(clusters_costs)

    normalized_weights = [normalize(w, cost_sum, num_of_options) for w in clusters_costs]
    return normalized_weights, possible_clusters

############################################################

def weights_for(technique, job_type, current_zone, mesh):
    if technique == "round_robin":
        return 1
    if technique == "smooth_weighted_round_robin":
        return _weights_for_swrr(job_type, current_zone, mesh)
    if technique == "model_1":
        return 0
