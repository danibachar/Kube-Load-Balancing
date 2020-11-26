
import json, sys
from datetime import datetime
import numpy as np

from models.kubernetes import Job
from generators.application_generator import generate_application
from load_balancing.round_robin import round_robin, smooth_weighted_round_robin, reset_state
from utils.cost import simple_addative_weight
from utils.distributions import heavy_tail_jobs_distribution

from ploter import plot

def init_capacitiy_matrix(cluster):
    mat = {}
    for idx, service in cluster.services.items():
        mat[service.job_type] = service.capacity
    return mat

def init_residual_capacitiy_matrix(cluster):
    mat = {}
    for idx, service in cluster.services.items():
        mat[service.job_type] = service.residual_capacity
    return mat

def init_load_matrix(cluster):
    mat = {}
    for idx, service in cluster.services.items():
        mat[service.job_type] = service.load
    return mat

def init_cost_matrix(cluster):
    mat = {}
    for service in cluster.services.values():
        mat[service.job_type] = {}

        for dependency in service.dependencies:
            mat[service.job_type][dependency.job_type] = {}

            # Local weight is zero
            # if dependency.job_type in service.cluster.supported_job_types():
                # mat[service.job_type][dependency.job_type][service.cluster.id] = sys.maxsize

            # Remote weights
            for cluster_in_mesh in cluster.mesh.values():
                if dependency.job_type in cluster_in_mesh.supported_job_types():
                    # print("from:{}\nto:{}\nbecause:{}->{}\nw:{}\nnw:{}\nsum:{}\ncount:{}".format(
                    #     cluster.id,
                    #     cluster_in_mesh.id,
                    #     service.job_type,
                    #     dependency.job_type,
                    #     weight, n_weight, weight_sum, num_of_options
                    # ))
                    cost = service.zone.cost_according_to(cluster_in_mesh.zone)
                    mat[service.job_type][dependency.job_type][cluster_in_mesh.id] = cost

    return mat

def init_weights_matrix(cluster):
    mat = {}
    for job_type, zones_weights_map in cluster.weights.items():
        if job_type not in mat:
            mat[job_type] = {}
        for zone, weight in zones_weights_map.items():
            mat[job_type][zone.name] = weight
    return mat

def _sim_matrix(clusters):
    sim_matrix = {}
    for cluster in clusters:
        sim_matrix[cluster.id] = {
            # "cluster": cluster,
            "cost": init_cost_matrix(cluster),
            "load": init_load_matrix(cluster),
            "residual_capacity": init_residual_capacitiy_matrix(cluster),
            "capacity": init_capacitiy_matrix(cluster),
            "weights": init_weights_matrix(cluster)
        }

    # print(sim_matrix)
    with open('matrices/sim_mat.{}.json'.format(datetime.now()), 'w') as outfile:
        json.dump(sim_matrix, outfile)
    return sim_matrix

def jobs_to_arraive_in_next_tik(tik, jobs_loads):
    if len(jobs_loads) <= tik:
        return None
    return jobs_loads[tik+1]

# Some jobs depend on others
def calc_total_job_juration(job, cluster):
    duration = job.duration
    service = cluster._service(job.type)
    # max_duration = job.duration
    for dependency in service.dependencies:
        duration += job.duration

    return duration

def simulate_job_sending(job, cluster, tik):
    service = cluster._service(job.type)
    job.arriavl_time = tik
    service.consumed_jobs.add(job)
    service.load += job.load

    for dependency in service.dependencies:
        new_job = Job(service.cluster, job.duration, job.load, dependency.job_type, job)
        target_cluster = service._choose_target_cluster(dependency)

        if target_cluster.zone not in service.total_traffic_sent:
            service.total_traffic_sent[target_cluster.zone] = {}
        if dependency.job_type not in service.total_traffic_sent[target_cluster.zone]:
            service.total_traffic_sent[target_cluster.zone][dependency.job_type] = 0

        service.total_traffic_sent[target_cluster.zone][dependency.job_type]+=1

        job_latency = cluster.zone.latency_per_request(target_cluster.zone)/1000
        simulate_job_sending(new_job, target_cluster, tik+job_latency)

def end_job_if_needed(job, cluster, tik):
    service = cluster._service(job.type)
    if service:
        if job in service.consumed_jobs:
            job_ttl = job.arriavl_time + calc_total_job_juration(job, cluster)
            # print("found matching job:{}\ntik:{}\nttl:{}".format(job.type, tik, job_ttl))
            if tik >= job_ttl:
                # print("job:{} has left the building\nafter:{}".format(job.id, tik-job_ttl))
                service.load -= job.load
                service.consumed_jobs.remove(job)
                return True
    return False

def simulate_job_ending_if_needed(job, cluster, tik):
    did_leave = end_job_if_needed(job, cluster, tik)

    all_clusters = list(cluster.mesh.values())+[cluster]

    jobs_to_check_removal = []

    for c in all_clusters:
        for service in c.services.values():
            for consumed_job in service.consumed_jobs:
                if consumed_job.source_job and consumed_job.source_job.id == job.id:
                    jobs_to_check_removal.append((consumed_job,c))

    # start = datetime.now()
    for job_to_check in jobs_to_check_removal:
        # start = datetime.now()
        simulate_job_ending_if_needed(job_to_check[0], job_to_check[1], tik)
        # print("recursion took:{}\nfor:{}\nlen:{}".format(datetime.now()-start, tik, len(jobs_to_check_removal)))
    return did_leave

def clean_obsolete_jobs(jobs, clusters, tik):
    removed_indeces = []
    for idx, job in enumerate(jobs):
        for cluster in clusters:
            did_leave = simulate_job_ending_if_needed(job, cluster, tik)
            if did_leave:
                removed_indeces.append(idx)
    remaining_jobs = [i for j, i in enumerate(jobs) if j not in removed_indeces]
    return remaining_jobs

def traffic_cost(clusters):
    cost = 0
    min_price = min([cluster.zone.pricing["cross-zone"] for cluster in clusters])
    min_latency = min([min(cluster.zone.latency.values()) for cluster in clusters])

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
            cost += sum_requests * simple_addative_weight(price, latency, min_price, min_latency)
            # break
    return cost

def plot_avg(costs, times, loads, title_prefix=""):
    if len(costs) == 0:
        return
    total_cost = sum(costs)
    cost_title = "total cost = {}".format(total_cost)
    plot(
        costs = costs,
        times = times,
        loads = loads,
        cost_title = title_prefix + " " + cost_title
    )

def run(clusters, jobs_loads, front_end):
    jobs = []
    costs = []
    times = []
    loads = []
    for tik, load in enumerate(jobs_loads):
        load = int(load)
        single_job = Job(None, 0.25, 1, front_end)
        jobs.append(single_job)

        for i in range(0, load):
            for cluster in clusters:
                simulate_job_sending(single_job, cluster, tik)

        times.append(tik)
        loads.append(load)
        costs.append(traffic_cost(clusters))

        # Clean jobs at the end of each tik

        total_jobs_before_clean = sum([len(s.consumed_jobs) for c in clusters for s in c.services.values()])
        print("total_jobs_before_clean",total_jobs_before_clean)

        start = datetime.now()

        jobs = clean_obsolete_jobs(jobs, clusters, tik)

        total_jobs_after_clean = sum([len(s.consumed_jobs) for c in clusters for s in c.services.values()])
        time = datetime.now() - start

        print("clean tik:{}\ntook:{}\ntotal jobs in the system:{}\n".format(tik, time, total_jobs_after_clean))

        if tik % 5 == 0:
            _sim_matrix(clusters)

        for cluster in clusters:
            cluster.reset_traffic_sent()

    tiks_more = len(jobs_loads)
    while len(jobs) > 0:
        jobs = clean_obsolete_jobs(jobs, clusters, tiks_more)
        tiks_more+=1
    print("took {} more tiks for all jobs to leave the system".format(tiks_more - len(jobs_loads)))
    _sim_matrix(clusters)
    plot_avg(costs, times, loads)

jobs_loads = heavy_tail_jobs_distribution("pareto", 25, 5)
for f in [round_robin, smooth_weighted_round_robin]:
    clusters, front_end = generate_application(f, simple_addative_weight)
    run(clusters, jobs_loads, front_end)
