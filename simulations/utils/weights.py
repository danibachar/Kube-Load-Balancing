from scipy.optimize import linprog
import numpy as np
import math, time
from pulp import *
from utils.cost import simple_max_addative_weight, simple_min_addative_weight

failure_count=0

def _weights_for_rr(clusters):
        res = {} # Map of maps, cluster.id <-> weights map
        for cluster in clusters:
            weights_map = {}
            mesh = list(cluster.mesh.values())
            cluster_targets_types = list(set([dependency.job_type for service in cluster.services.values() for dependency in service.dependencies]))
            for target in cluster_targets_types:
                if target not in weights_map:
                    weights_map[target] = {}
                # Handling Local cluster support
                if target in cluster.supported_job_types:
                    weights_map[target][cluster] = 1
                    continue
                possible_clusters = list(filter(lambda c: target in c.supported_job_types, mesh))
                weight_per_cluster = 1/len(possible_clusters) # Round - Robin
                for idx, dest_cluster in enumerate(possible_clusters):
                    weights_map[target][dest_cluster] = weight_per_cluster

            res[cluster.id] = weights_map

        return res

def _weights_for_swrr(clusters, cost_function_weights):
    res = {} # Map of maps, cluster.id <-> weights map
    for cluster in clusters:
        weights_map = {}
        mesh = list(cluster.mesh.values())
        cluster_targets_types = list(set([dependency.job_type for service in cluster.services.values() for dependency in service.dependencies]))
        for target in cluster_targets_types:
            if target not in weights_map:
                weights_map[target] = {}
            # Handling Local cluster support
            if target in cluster.supported_job_types:
                weights_map[target][cluster] = 1
                continue

            possible_clusters = list(filter(lambda c: target in c.supported_job_types, mesh))

            prices = []
            latencies = []
            for c in possible_clusters:
                prices.append(cluster.zone.price_per_gb(c.zone))
                latencies.append(cluster.zone.latency_per_request(c.zone))
            max_price = max(prices)
            max_latency = max(latencies)
            clusters_cost = [simple_max_addative_weight(
                price=p,
                max_price=max_price,
                price_weight=cost_function_weights[0],
                latency=l,
                max_latency=max_latency,
                latency_weight=cost_function_weights[1]
            ) for p,l in zip(prices, latencies)]
            # max_price = max(prices)
            # max_latency = max(latencies)
            # clusters_cost = [simple_max_addative_weight(
            #     price=p,
            #     max_price=max_price,
            #     price_weight=cost_function_weights[0],
            #     latency=l,
            #     max_latency=max_latency,
            #     latency_weight=cost_function_weights[1]
            # ) for p,l in zip(prices, latencies)]
            max_cost = max(clusters_cost)
            x_count = sum([max_cost/cost for cost in clusters_cost])
            x_value = 1/x_count

            for idx, dest_cluster in enumerate(possible_clusters):
                weight = max_cost/clusters_cost[idx] * x_value
                weights_map[target][dest_cluster] = weight

        res[cluster.id] = weights_map

    return res

############################################################
def _services(clusters, target_type):
    source_services = []
    destination_services = []
    for cluster in clusters:
        if not cluster.is_available:
            continue
        for service in cluster.services.values():
            if not service.is_available:
                continue
        
            if target_type in [d.job_type for d in service.dependencies]:
                source_services.append(service)
            if target_type == service.job_type:
                destination_services.append(service)
    return source_services, destination_services

def _lp_params(source_services, destination_services, cost_function_weights, at_tik):
    x = []
    for src in source_services:
        x.append([])
        # my_propogated_request_count = math.floor(src.jobs_consumed_per_time_slot(at_tik))
        for dest in destination_services:
            name = src.full_name+"-"+dest.full_name
            var = pulp.LpVariable(name, lowBound = 0, upBound = src.capacity, cat='Continuous') # Continuous # Integer
            x[-1].append(var)

    capacities = []
    for dest in destination_services:
        capacities.append(dest.capacity)

    demands = []
    for src in source_services:
        my_propogated_request_count = math.floor(src.jobs_consumed_per_time_slot(at_tik))
        demands.append(my_propogated_request_count)

    costs = []
    price_costs = []
    latency_costs = []
    for src in source_services:
        prices = []
        latencies = []
        for dest in destination_services:
            prices.append(src.cluster.zone.price_per_gb(dest.cluster.zone))
            latencies.append(src.cluster.zone.latency_per_request(dest.cluster.zone))
        max_price = max(prices)
        max_latency = max(latencies)
        try:
            dests_cost = [simple_max_addative_weight(
                price=p,
                max_price=max_price,
                price_weight=cost_function_weights[0],
                latency=l,
                max_latency=max_latency,
                latency_weight=cost_function_weights[1]
            ) for p,l in zip(prices, latencies)]
        except Exception as e:
            print("e", e)
            print("prices", prices)
            print("latencies", latencies)
            print("src", src.full_name)
            print("destination_services", destination_services)
            dests_cost = [1/len(prices)] * len(prices)


        # min_price = min(prices)
        # min_latency = min(latencies)
        # dests_cost = [simple_min_addative_weight(
        #     price=p,
        #     min_price=min_price,
        #     price_weight=cost_function_weights[0],
        #     latency=l,
        #     min_latency=min_latency,
        #     latency_weight=cost_function_weights[1]
        # ) for p,l in zip(prices, latencies)]

        price_costs.append(np.asarray(prices) / max_price)
        latency_costs.append(np.asarray(latencies) / max_latency)

        costs.append(dests_cost)

    return x, costs, demands, capacities, price_costs, latency_costs

def _build_problem(source_services, destination_services, x, costs, demands, capacities, price_costs, latency_costs, cost_function_weights):
    # Define Optimization Problem - Minimizing Cost
    prob = LpProblem("Service Selection Problem", LpMinimize)
    src_count = len(source_services)
    dest_count = len(destination_services)
    # Objective
    prob += lpSum(x[src_idx][dst_idx] * costs[src_idx][dst_idx] for src_idx in range(src_count) for dst_idx in range(dest_count))
    # prob += lpSum(x[src_idx][dst_idx]*cost_function_weights[0]*price_costs[src_idx][dst_idx] + x[src_idx][dst_idx]*cost_function_weights[1]*latency_costs[src_idx][dst_idx] for src_idx in range(src_count) for dst_idx in range(dest_count))
    # Constriants:
    # (1) All Request demand must be deplited - i.e all requests must be sent and cannot be dropped
    for src_idx in range(src_count):
        prob += lpSum([x[src_idx][dst_idx] for dst_idx in range(dest_count)]) == demands[src_idx]
    # (2) Capacity - service cannot handle more than its capacity
    for dst_idx in range(dest_count):
        prob += lpSum([x[src_idx][dst_idx] for src_idx in range(src_count)]) <= capacities[dst_idx]
        # (3) # Liveness
    # for dst_srv_idx in dest_srvs_idx:
    #     prob += lpSum([x[src_srv_idx][dst_srv_idx]]) >= 1

    prob.writeLP("ServiceSelection.lp")
    return prob

def _weights_distribution(x, source_services, destination_services):
    res = {}
    src_count = len(source_services)
    dest_count = len(destination_services)

    for src_svc_idx, src_svc in enumerate(source_services):
        if src_svc.cluster.id not in res:
            res[src_svc.cluster.id] = {}
        if src_svc.id not in res[src_svc.cluster.id]:
            res[src_svc.cluster.id][src_svc.id] = {}
        dists = [x[src_svc_idx][dst_svc_idx].value() for dst_svc_idx in range(dest_count)]
        estimated_total_requests = sum(dists)
        if estimated_total_requests == 0:
            # raise Exception("estimated_total_requests were zero, pading with 1")
            print("estimated_total_requests were zero, pading with 1")
            estimated_total_requests = 1
        for dst_svc_idx in range(dest_count):
            dst_svc = destination_services[dst_svc_idx]
            if dst_svc.job_type not in res[src_svc.cluster.id][src_svc.id]:
                res[src_svc.cluster.id][src_svc.id][dst_svc.job_type] = {}
            if dst_svc.cluster in res[src_svc.cluster.id][src_svc.id][dst_svc.job_type]:
                print(res[src_svc.cluster.id][dst_svc.job_type])
                print(src_svc.cluster.id)
                print(dst_svc.job_type)
                print(dst_svc.cluster)
                raise Exception("grrr")
            res[src_svc.cluster.id][src_svc.id][dst_svc.job_type][dst_svc.cluster] = x[src_svc_idx][dst_svc_idx].value() / estimated_total_requests

    return res

from timeit import default_timer as timer

def _costly_weights(clusters, at_tik, cost_function_weights):
    global failure_count
    res = {} # Map of maps, cluster.id <-> weights map
    target_types = list(sorted(set([dependency.job_type for cluster in clusters for service in cluster.services.values() for dependency in service.dependencies])))
    # Optimize per target type
    for target_type in target_types:
        sources, destinations = _services(clusters, target_type)

        if len(destinations) == 0:
            print("target_type", target_type)
            print("sources", sources)
            print("destinations", destinations)
            continue
        x, costs, demands, capacities, price_costs, latency_costs = _lp_params(sources, destinations, cost_function_weights, at_tik)

        sum_demands = sum(demands)
        sum_capacities = sum(capacities)
        if sum_demands > sum_capacities:
            ratio = sum_demands / sum_capacities
            # Normalize 
            print("{} normalize demands {} to capacities {}".format(target_type, sum_demands, sum_capacities))
            demands = np.array(demands) * (1 / ratio)
        prob = _build_problem(sources, destinations, x, costs, demands, capacities, price_costs, latency_costs, cost_function_weights)
        s = timer()
        prob.solve(PULP_CBC_CMD(msg=0))
        e = timer()
        # print("solving took {} seconds".format(e-s))
        # print("res after update = {}".format(res))
        if prob.status == -1:
            failure_count+=1
            print("###########################")
            print("could not solve {}, at tik = {}".format(target_type, at_tik))
            print("demands = {}\nfrom = {}".format(demands, sources))
            print("capacities = {}\nof = {}".format(capacities, destinations))
            print("###########################")
        
        try:
            w = _weights_distribution(x, sources, destinations)
        except Exception as e:
            print("Error", e)
            print("x: ", x)
            print("costs: ", costs)
            print("demands: ", demands)
            print("capacities: ", capacities)
            print("price_costs: ", price_costs)
            print("latency_costs: ", latency_costs)
        # print("w for {} = {}".format(target_type, w))
        # res = {**res, **w}
        res[target_type] = w
        
    # print(res)
    return res



def weights_for(technique, clusters, at_tik, cost_function_weights):
    if technique == "round_robin":
        return _weights_for_rr(clusters)
    if technique == "smooth_weighted_round_robin":
        return _weights_for_swrr(clusters, cost_function_weights)
    if technique == "model":
        # weights = _weights_costly_bin_packing2(clusters, at_tik, cost_function_weights)
        weights = _costly_weights(clusters, at_tik, cost_function_weights)
        return weights