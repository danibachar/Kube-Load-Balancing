from ploter import plot
import json, os
import numpy as np

dir = "runs"
# subdir = "all_reset_state"
# subdir = "with_reset"
subdir = "single_cluster_4"

rr_prefix = "round_robin"
swrr_prefix = "smooth_weighted_round_robin"

def plot_avg(costs, times, loads):
    avg_costs = np.array(costs).mean(axis=0)
    total_cost = sum(avg_costs)
    cost_title = "total cost = {}".format(total_cost)
    load_title = "total cost = {}".format(total_cost)
    plot(
        costs = avg_costs,
        times = np.array(times).mean(axis=0),
        loads = np.array(loads).mean(axis=0),
        cost_title = cost_title
    )

for test_kind in [rr_prefix, swrr_prefix]:
    full_dir = "/".join([dir, subdir])
    costs = []
    loads = []
    times = []
    for (dirpath, dirnames, filenames) in os.walk(full_dir):
        for filename in filenames:
            if test_kind not in filename:
                continue
            full_file_path = os.path.join(dirpath, filename)
            with open(full_file_path) as json_file:
                data = json.load(json_file)
                costs.append(data["costs"])
                times.append(data["times"])
                loads.append(data["loads"])
    plot_avg(costs = costs, times = times, loads = loads)