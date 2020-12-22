from scipy.optimize import linprog
import numpy as np
import math, time
from pulp import *

def _weights_for_model_1(clusters):
    res = {} # Map of maps, cluster.id <-> weights map
    for cluster in clusters:
        weights_map = {}
        mesh = list(cluster.mesh.values())

        for service in cluster.services.values():
            expected_jobs_to_be_sent = len(service.consumed_jobs)

            for dependency in service.dependencies:
                if dependency.job_type in cluster.supported_job_types():
                    continue

                possible_clusters = list(filter(lambda c: dependency.job_type in c.supported_job_types(), mesh))
                loads = [1 for _ in range(0,expected_jobs_to_be_sent)] # 1 load per job
                weights = _weights_for_model_1_helper(cluster, possible_clusters, loads, dependency.job_type)
                for idx in range(0,len(possible_clusters)):
                    dest_cluster = possible_clusters[idx]
                    weight = weights[idx]
                    weights_map[dependency.job_type][dest_cluster.zone] = weight

    return res

def _weights_for_swrr(clusters):
    def normalize(weight, weight_sum, num_of_options):
        percent = (1 - weight / weight_sum) /  max(1, num_of_options - 1)
        return percent

    res = {} # Map of maps, cluster.id <-> weights map
    for idx in range(0, len(clusters)):

        weights_map = {}
        cluster = clusters[idx]
        mesh = list(cluster.mesh.values())

        for service in cluster.services.values():
            for dependency in service.dependencies:
                if dependency.job_type in cluster.supported_job_types():
                    continue

                possible_clusters = list(filter(lambda c: dependency.job_type in c.supported_job_types(), mesh))
                clusters_costs = list(map(lambda c: cluster.zone.cost_according_to(c.zone), possible_clusters))
                cost_sum = sum(clusters_costs)
                num_of_options = len(clusters_costs)
                for idx, dest_cluster in enumerate(possible_clusters):
                    cost = cluster.zone.cost_according_to(dest_cluster.zone)
                    weight = normalize(cost, cost_sum, num_of_options)
                    if dependency.job_type not in weights_map:
                        weights_map[dependency.job_type] = {}
                    weights_map[dependency.job_type][dest_cluster.zone] = weight

        res[cluster.id] = weights_map

    return res

def create_data_model(source_cluster, possible_clusters, expected_jobs_count, job_type, at_tik):
    """Create the data for the example."""
    job_loads = [1 for _ in range(expected_jobs_count)]
    jobs_names = ["j"+str(j) for j in range(len(job_loads))]

    clusters_name = [c.id for c in possible_clusters]
    clusters_cost = [source_cluster.zone.cost_according_to(c.zone) for c in possible_clusters]
    clusters_cap = [c.available_capacity(job_type, at_tik) for c in possible_clusters]

    return {
        "job_loads": job_loads,
        "jobs_names": jobs_names,
        "clusters_name": clusters_name,
        "clusters_cost": clusters_cost,
        "clusters_cap": clusters_cap,
    }

def _solve_cluster_bin_packing(job_loads, jobs_names, clusters_name, clusters_cost, clusters_cap):
        prob = LpProblem("Service Selection Problem", LpMinimize)
        jobs_count = len(jobs_names)
        clusters_count = len(clusters_name)
        x = []
        for cluster_idx in range(clusters_count):
            x.append([])
            for job_idx in range(jobs_count):
                name = jobs_names[job_idx]+"_"+clusters_name[cluster_idx]
                var = pulp.LpVariable(name, lowBound = 0, upBound = 1, cat='Continuous')
                x[cluster_idx].append(var)
        prob += lpSum(x[cluster_idx][job_idx] * clusters_cost[cluster_idx] for job_idx in range(jobs_count) for cluster_idx in range(clusters_count))
        # A job must be assigned to one clsuter only
        for job_idx in range(jobs_count):
            prob += lpSum([x[cluster_idx][job_idx] for cluster_idx in range(clusters_count)]) == 1

        # A cluster cannot handle more of its cap
        for cluster_idx in range(clusters_count):
            prob += lpSum([x[cluster_idx][job_idx] * job_loads[job_idx] for job_idx in range(jobs_count)]) <= clusters_cap[cluster_idx]

        # Each culster must get some at least 10% of load - avoid herd behaviour and server starvation
        # TODO - inject the epsilon
        epsilon = 0.1
        _percent_of_load = sum(job_loads)*epsilon

        for cluster_idx in range(clusters_count):
            prob += lpSum([x[cluster_idx][job_idx] * job_loads[job_idx] for job_idx in range(jobs_count)]) >= _percent_of_load

        prob.writeLP("ServiceSelection.lp")
        prob.solve(PULP_CBC_CMD(msg=0))
        # print(prob.status)
        if prob.status == -1:
            print("###########################")
            print("could not solve")
            print("###########################")
            print("clusters_cap",clusters_cap)
            print("###########################")
            print("clusters_cost",clusters_cost)
            print("###########################")
            print("job_loads",job_loads)
            print("###########################")

            # print(x)
        total_cost = 0
        cluster_load_dist = []
        for cluster_idx in range(clusters_count):
            cluster_load_dist.append(0)
            for job_idx in range(jobs_count):
                is_job_assigned_to_cluster = x[cluster_idx][job_idx].value()
                cluster_load_dist[cluster_idx]+=is_job_assigned_to_cluster
                total_cost += is_job_assigned_to_cluster * clusters_cost[cluster_idx]
        # print("cluster_load_dist = ",cluster_load_dist)
        # print("total cost = ", total_cost)
        if jobs_count == 0:
            jobs_count = 1
        return [dist/jobs_count for dist in cluster_load_dist]

def _weights_costly_bin_packing(clusters, at_tik):
    res = {} # Map of maps, cluster.id <-> weights map
    for cluster in clusters:
        weights_map = {}
        mesh = list(cluster.mesh.values())

        for service in cluster.services.values():
            # TODO - we need to share the amount of jobs to be sent by this service accross all clusters.
            # In this way we will have a better understanding about the part in the total load that this service takes place in
            expected_jobs_to_be_sent = math.ceil(np.median(service.jobs_consumed_per_time_slot))

            for dependency in service.dependencies:
                if dependency.job_type in cluster.supported_job_types():
                    continue
                # Filter only supported clusters
                possible_clusters = list(filter(lambda c: dependency.job_type in c.supported_job_types(), mesh))
                data = create_data_model(
                    source_cluster=cluster,
                    possible_clusters=possible_clusters,
                    expected_jobs_count=expected_jobs_to_be_sent,
                    job_type=dependency.job_type,
                    at_tik=at_tik
                )

                weights = _solve_cluster_bin_packing(
                    job_loads=data["job_loads"],
                    jobs_names=data["jobs_names"],
                    clusters_name=data["clusters_name"],
                    clusters_cost=data["clusters_cost"],
                    clusters_cap=data["clusters_cap"],
                )
                # loads = [1 for _ in range(0, expected_jobs_to_be_sent)] # 1 load per job
                # weights = _weights_for_model_1_helper(cluster, possible_clusters, loads, dependency.job_type)
                for idx, dest_cluster in enumerate(possible_clusters):
                    if dependency.job_type not in weights_map:
                        weights_map[dependency.job_type] = {}
                    weights_map[dependency.job_type][dest_cluster.zone] = weights[idx]
        res[cluster.id] = weights_map

    return res

############################################################

def weights_for(technique, clusters, at_tik=0):
    if technique == "round_robin":
        return {}
    if technique == "smooth_weighted_round_robin":
        return _weights_for_swrr(clusters)
    if technique == "model_1":
        return _weights_for_model_1(clusters)
    if technique == "model_2":
        # start_time = time.time()
        weights = _weights_costly_bin_packing(clusters, at_tik)
        # print("calculating weights took = ", (time.time() - start_time))
        return weights
