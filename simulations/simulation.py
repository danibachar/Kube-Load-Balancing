import time, random, math, json, threading, logging

from datetime import datetime
from numpy import random
import matplotlib.pyplot as plt

from models.kubernetes import Job
from generators.application_generator import generate_application
from load_balancing.round_robin import round_robin, smooth_weighted_round_robin, reset_state
from utils.cost import simple_addative_weight
from utils.distributions import heavy_tail_jobs_distribution

from ploter import plot

from multiprocessing.pool import ThreadPool

now = datetime.now()
log_file_name = 'logs/simulation.{}.log'.format(now)
logging.basicConfig(filename=log_file_name, level=logging.INFO)

jobs_duration = [1, 0.25, 0.5, 2]
def load(cluster, jobs_count, front_end):
    jobs_count = int(jobs_count)
    pool = ThreadPool(processes=jobs_count)
    duration = random.choice(jobs_duration)
    single_job = Job(None, 0.1, 1, front_end)
    # print("running job:{}\non cluster:{}\n".format(single_job, cluster.id))
    results = []
    for job in range(0, jobs_count):
        # async_result = cluster.consume(single_job)
        async_result = pool.apply_async(cluster.consume, (single_job,))
        results.append(async_result)
        # did_succeed = did_succeed and cluster.consume(single_job)
    pool.close()
    pool.join()
    did_succeed = True
    for r in results:
        # did_succeed = did_succeed and r.get()
        did_succeed = did_succeed and r
    return did_succeed

# Summing the payment for traffic and the latency panelty
def traffic_cost(clusters):
    cost = 0
    min_price = min([cluster.zone.pricing["cross-zone"] for cluster in clusters])
    min_latency = min([min(cluster.zone.latency.values()) for cluster in clusters])

    # min_price = clusters[0].zone.pricing["cross-zone"]
    # min_latency = min(clusters[0].zone.latency.values())

    for cluster in clusters:
        clusters_traffic_map = cluster.sum_traffic_sent()
        # logging.critical(clusters_traffic_map)
        for other_cluster_zone, traffic_map in clusters_traffic_map.items():
            if cluster.zone == other_cluster_zone: # same zone, price and latency =0
                continue
            # print(traffic_map)
            price = cluster.zone.price_per_request(other_cluster_zone)
            latency = cluster.zone.latency_per_request(other_cluster_zone)
            sum_requests = sum(traffic_map.values()) # Note - change in future to take req size into account
            # print("latency:{}\nprice:{}\nsum:{}".format(latency, price, sum_requests))
            cost += sum_requests * simple_addative_weight(price, min_price, latency, min_latency)
            # break
    return cost

def simulate(clusters, load_per_cluster, front_end):
    pool = ThreadPool(processes=len(clusters))
    results = []
    for cluster in clusters:
        # load(cluster, load_per_cluster, front_end)
        # break
        async_result = pool.apply_async(load, (cluster, load_per_cluster, front_end))
        results.append((async_result, cluster.id))

    pool.close()
    pool.join()

    # for task, cluster_id in results:
    #     res = async_result.get()
        # print("cluster:{}\nresult:{}".format(cluster_id, res))

    # Cleanup
    for cluster in clusters:
        cluster.thread_clenup()

    return traffic_cost(clusters)

def run(dest_func, cost_func, did_reset_state, jobs_loads):
    costs = []
    times = []
    loads = []
    clusters, front_end = generate_application(dest_func, cost_func)
    for idx, job_load in enumerate(jobs_loads):
        for cluster in clusters:
            cluster.reset_traffic_sent()
        cost = simulate(clusters, job_load, front_end)
        costs.append(cost)
        loads.append(job_load)
        times.append(idx)

    # Dump results
    prefix = "reset" if did_reset_state else "no_reset"
    with open('runs/{}.{}.{}.txt'.format(dest_func.__name__, prefix, datetime.now()), 'w') as outfile:
        data = {
            "costs": costs,
            "loads": loads,
            "times": times,
        }
        json.dump(data, outfile)
###########################################################################

def selection_func(sign):
    if sign == 1:
        return smooth_weighted_round_robin
    return round_robin

possible_funcs = [1]
states = [True]
tests = 1
jobs_loads = heavy_tail_jobs_distribution("pareto", 100, 45)
for func_sign in possible_funcs:
    for should_reset_state in states:
        for test in range(0,tests):
            dest_func = selection_func(func_sign)
            if should_reset_state:
                reset_state()
            run(dest_func, simple_addative_weight, should_reset_state, jobs_loads)
