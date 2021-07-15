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

def _prepare_matrix_and_constraints_datasources(services, cost_function_weights):
    # Matrix
    x = []
    # Constraints
    costs = []
    price_costs = []
    latency_costs = []
    demands = []
    capacities = []
    for src_service_idx, src_service in enumerate(services):
        my_propogated_request_count = math.floor(src_service.jobs_consumed_per_time_slot)
        my_depended_job_types = [d.job_type for d in src_service.dependencies]
        capacities.append(src_service.capacity)
        demands.append(my_propogated_request_count)
        # Costs ingrediants
        prices = []
        latencies = []
        # Variable will get 0 - propogated request count if depended, else 0 as it is not relevant
        # Note that we build a very sparse matrix
        x.append([])
        for dst_service_idx, dst_service in enumerate(services):
            name = src_service.full_name+"_"+dst_service.full_name
            upBound = 0
            if dst_service.job_type in my_depended_job_types:
                upBound = my_propogated_request_count
            var = pulp.LpVariable(name, lowBound = 0, upBound = upBound, cat='Continuous')
            x[src_service_idx].append(var)
            # Costs calculation
            prices.append(src_service.cluster.zone.price_per_gb(dst_service.cluster.zone))
            latencies.append(src_service.cluster.zone.latency_per_request(dst_service.cluster.zone))
        price_costs.append(np.asarray(prices) / max(prices))
        latency_costs.append(np.asarray(latencies) / max(latencies))
        # min_price = min(prices)
        # min_latency = min(latencies)
        # clusters_cost = [simple_min_addative_weight(
        #     price=p,
        #     min_price=min_price,
        #     price_weight=cost_function_weights[0],
        #     latency=l,
        #     min_latency=min_latency,
        #     latency_weight=cost_function_weights[1]
        # ) for p,l in zip(prices, latencies)]
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
        costs.append(clusters_cost)

    return x, costs, demands, capacities, price_costs, latency_costs

def _prepare_lp_problem(services, x, costs, demands, capacities, price_costs, latency_costs, cost_function_weights):
    service_count = len(services)
    # Define Optimization Problem - Minimizing Cost
    prob = LpProblem("Service Selection Problem", LpMinimize)
    # Objective
    prob += lpSum(x[src_srv_idx][dst_srv_idx] * costs[src_srv_idx][dst_srv_idx] for src_srv_idx in range(service_count) for dst_srv_idx in range(service_count))
    # prob += lpSum(x[src_srv_idx][dst_srv_idx]*cost_function_weights[0]*price_costs[src_srv_idx][dst_srv_idx] + x[src_srv_idx][dst_srv_idx]*cost_function_weights[1]*latency_costs[src_srv_idx][dst_srv_idx] for src_srv_idx in range(service_count) for dst_srv_idx in range(service_count))

    # Constriants:
    for src_srv_idx in range(service_count):
        src_srv = services[src_srv_idx]
        for dependency in src_srv.dependencies:
            dest_srvs_idx = []
            for i,s in enumerate(services):
                if dependency.job_type == s.job_type:
                    dest_srvs_idx.append(i)
            # (1) All Request demand must be deplited - i.e all requests must be sent and cannot be dropped
            prob += lpSum([x[src_srv_idx][dst_srv_idx] for dst_srv_idx in dest_srvs_idx]) == demands[src_srv_idx]
    for dst_srv_idx in range(service_count):
        dst_srv = services[dst_srv_idx]
        src_srvs_idx = []
        for i,s in enumerate(services):
            if dst_srv.job_type in [d.job_type for d in s.dependencies]:
                src_srvs_idx.append(i)
        # (2) Capacity - service cannot handle more than its capacity
        prob += lpSum([x[src_srv_idx][dst_srv_idx] for src_srv_idx in range(service_count)]) <= max(demands[src_srv_idx],capacities[dst_srv_idx])
        # (3) # Liveness
        # for dst_srv_idx in dest_srvs_idx:
        #     prob += lpSum([x[src_srv_idx][dst_srv_idx]]) >= 1

    prob.writeLP("ServiceSelection.lp")
    return prob

def _prepare_weights_map(services, x):
    res = {}
    for src_svc_idx, src_svc in enumerate(services):
        if src_svc.cluster.id not in res:
            res[src_svc.cluster.id] = {}
        if src_svc.id not in res[src_svc.cluster.id]:
            res[src_svc.cluster.id][src_svc.id] = {}

        for dependency in src_svc.dependencies:
            dest_srvs_idx = []
            for i,s in enumerate(services):
                if dependency.job_type == s.job_type:
                    dest_srvs_idx.append(i)
            dists = [x[src_svc_idx][dst_svc_idx].value() for dst_svc_idx in dest_srvs_idx]
            estimated_total_requests = sum(dists)
            if estimated_total_requests == 0:
                print("estimated_total_requests were zero, pading with 1")
                estimated_total_requests = 1
            for dst_svc_idx in dest_srvs_idx:
                dst_svc = services[dst_svc_idx]
                if dst_svc.job_type not in res[src_svc.cluster.id][src_svc.id]:
                    res[src_svc.cluster.id][src_svc.id][dst_svc.job_type] = {}
                if dst_svc.cluster in res[src_svc.cluster.id][src_svc.id][dst_svc.job_type]:
                    # print(res[src_svc.cluster.id][dst_svc.job_type])
                    # print(src_svc.cluster.id)
                    # print(dst_svc.job_type)
                    # print(dst_svc.cluster)
                    raise
                res[src_svc.cluster.id][src_svc.id][dst_svc.job_type][dst_svc.cluster] = x[src_svc_idx][dst_svc_idx].value() / estimated_total_requests

    return res

def _weights_costly_bin_packing2(clusters, at_tik, cost_function_weights):
    global failure_count

    services = [service for cluster in clusters for service in cluster.services.values()]
    x, costs, demands, capacities, price_costs, latency_costs = _prepare_matrix_and_constraints_datasources(services, cost_function_weights)
    # prob = _prepare_lp_problem(services, x, costs, demands, capacities)
    prob = _prepare_lp_problem(services, x, costs, demands, capacities, price_costs, latency_costs, cost_function_weights)
    prob.solve(PULP_CBC_CMD(msg=0))
    res = _prepare_weights_map(services, x)
    if prob.status == -1:
        failure_count+=1
        print("###########################")
        print("could not solve {}, at tik = {}".format(failure_count, at_tik))
        print("demands = {}".format(demands))
        print("###########################")

    return res

############################################################
def _services(clusters, target_type):
    source_services = []
    destination_services = []
    for cluster in clusters:
        for service in cluster.services.values():
            if target_type in [d.job_type for d in service.dependencies]:
                source_services.append(service)
            if target_type == service.job_type:
                destination_services.append(service)
    return source_services, destination_services

def _lp_params(source_services, destination_services, cost_function_weights):
    x = []
    for src in source_services:
        x.append([])
        my_propogated_request_count = math.floor(src.jobs_consumed_per_time_slot)
        for dest in destination_services:
            name = src.full_name+"-"+dest.full_name
            var = pulp.LpVariable(name, lowBound = 0, upBound = my_propogated_request_count, cat='Continuous') # Continuous # Integer
            x[-1].append(var)

    capacities = []
    for dest in destination_services:
        capacities.append(dest.capacity)

    demands = []
    for src in source_services:
        my_propogated_request_count = math.floor(src.jobs_consumed_per_time_slot)
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
        # dests_cost = [simple_max_addative_weight(
        #     price=p,
        #     max_price=max_price,
        #     price_weight=cost_function_weights[0],
        #     latency=l,
        #     max_latency=max_latency,
        #     latency_weight=cost_function_weights[1]
        # ) for p,l in zip(prices, latencies)]

        min_price = min(prices)
        min_latency = min(latencies)
        dests_cost = [simple_min_addative_weight(
            price=p,
            min_price=min_price,
            price_weight=cost_function_weights[0],
            latency=l,
            min_latency=min_latency,
            latency_weight=cost_function_weights[1]
        ) for p,l in zip(prices, latencies)]

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
            print("estimated_total_requests were zero, pading with 1")
            estimated_total_requests = 1
        for dst_svc_idx in range(dest_count):
            dst_svc = destination_services[dst_svc_idx]
            if dst_svc.job_type not in res[src_svc.cluster.id][src_svc.id]:
                res[src_svc.cluster.id][src_svc.id][dst_svc.job_type] = {}
            if dst_svc.cluster in res[src_svc.cluster.id][src_svc.id][dst_svc.job_type]:
                # print(res[src_svc.cluster.id][dst_svc.job_type])
                # print(src_svc.cluster.id)
                # print(dst_svc.job_type)
                # print(dst_svc.cluster)
                raise
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
        x, costs, demands, capacities, price_costs, latency_costs = _lp_params(sources, destinations, cost_function_weights)
        prob = _build_problem(sources, destinations, x, costs, demands, capacities, price_costs, latency_costs, cost_function_weights)
        s = timer()
        prob.solve(PULP_CBC_CMD(msg=0))
        e = timer()
        print("solving took {} seconds".format(e-s))
        w = _weights_distribution(x, sources, destinations)
        # print("w for {} = {}".format(target_type, w))
        # res = {**res, **w}
        res[target_type] = w
        # print("res after update = {}".format(res))
        if prob.status == -1:
            failure_count+=1
            print("###########################")
            print("could not solve {}, at tik = {}".format(target_type, at_tik))
            print("demands = {}".format(demands))
            print("capacities = {}".format(capacities))
            print("###########################")
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
