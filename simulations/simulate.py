import json, sys, argparse, yaml, os, logging, time
from datetime import datetime
import numpy as np
import pandas as pd

from models.kube import Job

from generators.application_df_generator import generate_application
from load_balancing.round_robin import round_robin, smooth_weighted_round_robin, reset_state

from utils.cost import simple_addative_weight
from utils.distributions import heavy_tail_jobs_distribution
from utils.weights import weights_for
from utils.plots import plot_avg, full_plot, bar_plot

now = datetime.now()
log_file_name = 'logs/simulation.{}.log'.format(now)
logging.basicConfig(filename=log_file_name, level=logging.INFO)


def update_clusters_weights(clusters, weighting_technique, at_tik):
    weights = weights_for(weighting_technique, clusters, at_tik)
    # print("weights {}".format(weights))
    for cluster in clusters:
        cluster.weights = weights[cluster.id]

def run(clusters, jobs_loads, front_end, updating_weights_technique, model):
    jobs = []
    traffic_cost = []
    avg_latency = []
    times = []
    loads = []
    for tik, load in enumerate(jobs_loads):
        load = int(load)
        start_time = time.time()
        for i in range(0, load):
            for cluster in clusters:
                job = Job(None, cluster.zone, 0.25, 1, front_end)
                cluster.consume(job, tik)

        times.append(tik)
        loads.append(load)

        if tik % 10 == 0:
            for cluster in clusters:
                cluster.prepare_for_weight_update()
            update_clusters_weights(clusters, updating_weights_technique, tik)
        # print("full iteration {} took = {}".format(tik, time.time()-start_time))
    return traffic_cost, avg_latency, loads, times

def main(ymals):
    funcs = {
        "rr": {"func": round_robin, "weight_calc": "smooth_weighted_round_robin"},
        "wrr": {"func": smooth_weighted_round_robin, "weight_calc": "smooth_weighted_round_robin"},
        "wbp": {"func": smooth_weighted_round_robin, "weight_calc": "model_2"},
    }
    # funcs = [smooth_weighted_round_robin]
    jobs_loads = heavy_tail_jobs_distribution("pareto", 100, 5)
    costs_map = {}
    data_frames = {}
    for name, val in funcs.items():
        print(val)
        clusters, front_end = generate_application(ymals, val["func"], simple_addative_weight)
        update_clusters_weights(clusters, val["weight_calc"], 0)
        traffic_cost, avg_latency, loads, times = run(clusters, jobs_loads, front_end, val["weight_calc"], val["func"])
        print("loads", sum(loads))
        costs_map[name] = (traffic_cost, avg_latency, loads, times)
        data_frames[name] = { s.full_name: s.job_data_frame for cluster in clusters for s in cluster.services.values() }
    return costs_map, data_frames

def load_ymal(file_name):
    file_name = os.path.abspath(file_name)
    with open(file_name, 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            return None

parser = argparse.ArgumentParser(description='Run Kuberentes simulation')
parser.add_argument(
    '--app_yml',
    type=str,
    default="yamls/application_ymals/bookinfo_api_istio.yml",
    help='The location (relative or full) of the desired app ymal file'
)
parser.add_argument(
    '--pricing_ymls',
    type=list,
    default=[
        "yamls/pricing/aws.yml",
        "yamls/pricing/gcp.yml",
        ],
    help='The pricing maps you wish us to ue, for traffic cost calculation'
)
parser.add_argument(
    '--latency_matrix_ymal',
    type=str,
    default="yamls/latency/full_matrix.yml",
    help='The pricing maps you wish us to ue, for traffic cost calculation'
)

args = parser.parse_args()
pricing_ymal = {}

for file_name in args.pricing_ymls:
    yml = load_ymal(file_name)
    pricing_ymal[yml["name"]] = yml
ymals = {
    "app": load_ymal(args.app_yml),
    "latency": load_ymal(args.latency_matrix_ymal),
    "pricing": pricing_ymal
}

total_start_time = time.time()
costs = {}
dfs = {}
for i in range(1):
    st = time.time()
    _costs, _dfs = main(ymals)
    dfs[i] = _dfs
    for key, val in _costs.items():
        if key not in costs:
            costs[key] = [val]
        else:
            costs[key].append(val)
    print("iteration = {}".format(time.time()-st))
print("total run time = {}".format(time.time()-total_start_time))

total_traffic_cost_in_usd = []
bars_names = []
total_traffic_sent_in_gb = []
total_jobs_handled = []
for iter, df_type_map in dfs.items():
    bars_names.append([])
    total_traffic_cost_in_usd.append([])
    total_traffic_sent_in_gb.append([])
    total_jobs_handled.append([])
    for type, t_dfs in df_type_map.items():
        bars_names[-1].append(type)
        concated_df = pd.concat(t_dfs.values())
        total_traffic_cost_in_usd[-1].append(concated_df["cost_in_usd"].sum())
        total_traffic_sent_in_gb[-1].append(concated_df["size_in_gb"].sum())
        total_jobs_handled[-1].append(len(concated_df.index))


# items = costs.items()
# bars_values = [sum(val[0]) for _,v in items for val in v]
# bars_names = [key for key, _ in items]
print("total_traffic_cost_in_usd before mean = ", total_traffic_cost_in_usd)
total_traffic_cost_in_usd = np.mean(total_traffic_cost_in_usd, axis=0)
print("total_traffic_cost_in_usd after mean = ", total_traffic_cost_in_usd)

print("total_traffic_sent_in_gb before mean", total_traffic_sent_in_gb)
total_traffic_sent_in_gb = np.mean(total_traffic_sent_in_gb, axis=0)
print("total_traffic_sent_in_gb after mean", total_traffic_sent_in_gb)

print("total_jobs_handled before mean", total_jobs_handled)
total_jobs_handled = np.mean(total_jobs_handled, axis=0)
print("total_jobs_handled after mean", total_jobs_handled)

print("bars_names = ", bars_names[0])

traffic_titles = []
for i in range(len(total_traffic_sent_in_gb)):
    egress = total_traffic_sent_in_gb[i]
    cost = total_traffic_cost_in_usd[i]
    jobs = total_jobs_handled[i]
    title = "Cost = {}$\nEgress = {}GB\nGB Price = {}$\nJobs Count = #{}".format("%.3f"%cost,"%.3f"%egress, "%.3f"%(cost/egress),int(jobs))
    if i > 0:
        percent_improvment = ((total_traffic_cost_in_usd[i-1]-total_traffic_cost_in_usd[i]) / total_traffic_cost_in_usd[i-1]) * 100
        pt = ('%.3f' % percent_improvment)
        title += "\n\n{} %\nimprovment".format(pt)
    traffic_titles.append(title)

bar_plot(
    total_traffic_cost_in_usd,
    bars_names[0],
    traffic_titles,
    "traffic analysis"
)

# for key, val in costs.items():
#     sum_costs = [sum(v[0]) for v in val]
#     # print("model = {}, avg cost = {}, val = {}".format(key, np.mean(sum_costs), val))
#
#     traffic_cost = np.mean([v[0] for v in val], axis=0)
#     avg_latencies = np.mean([v[1] for v in val], axis=0)
#     loads = np.mean([v[2] for v in val], axis=0)
#     times = np.mean([v[3] for v in val], axis=0)
#
#     full_plot(traffic_cost, avg_latencies, loads, times, key)
