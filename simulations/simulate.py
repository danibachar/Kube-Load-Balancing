import json, sys, argparse, yaml, os, logging, time
from datetime import datetime
import numpy as np
import pandas as pd

from models.kube import Job

from generators.application_df_generator import generate_application
from load_balancing.round_robin import round_robin, smooth_weighted_round_robin, reset_state

from utils.cost import simple_min_addative_weight, simple_max_addative_weight
from utils.distributions import heavy_tail_jobs_distribution
from utils.weights import weights_for
from utils.plots import plot_avg, full_plot, bar_plot

now = datetime.now()
log_file_name = 'logs/simulation.{}.log'.format(now)
logging.basicConfig(filename=log_file_name, level=logging.INFO)

def update_clusters_weights(clusters, weighting_technique, at_tik):
    reset_state()
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
    jobs_loads = heavy_tail_jobs_distribution("pareto", 100, 5)
    costs_map = {}
    data_frames = {}
    for name, val in funcs.items():
        clusters, front_end = generate_application(ymals, val["func"], simple_min_addative_weight)
        update_clusters_weights(clusters, val["weight_calc"], 0)
        traffic_cost, avg_latency, loads, times = run(clusters, jobs_loads, front_end, val["weight_calc"], val["func"])
        costs_map[name] = (traffic_cost, avg_latency, loads, times)
        data_frames[name] = { s.full_name: s.job_data_frame for cluster in clusters for s in cluster.services.values() }
        reset_state()
    return costs_map, data_frames

def load_ymal(file_name):
    file_name = os.path.abspath(file_name)
    with open(file_name, 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            return None

if __name__ == '__main__':
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
    dfs = {}
    for i in range(10):
        st = time.time()
        _, _dfs = main(ymals)
        dfs[i] = _dfs
        print("iteration = {}".format(time.time()-st))
    print("total run time = {}".format(time.time()-total_start_time))

    total_traffic_cost_in_usd = []
    bars_names = []
    total_traffic_sent_in_gb = []
    total_jobs_handled = []
    avg_latencies = []
    job_durations = []
    for iter, df_type_map in dfs.items():
        bars_names.append([])
        total_traffic_cost_in_usd.append([])
        total_traffic_sent_in_gb.append([])
        total_jobs_handled.append([])
        avg_latencies.append([])
        job_durations.append([])
        for type, t_dfs in df_type_map.items():
            bars_names[-1].append(type)
            concated_df = pd.concat(t_dfs.values())
            total_traffic_cost_in_usd[-1].append(concated_df["cost_in_usd"].sum())
            total_traffic_sent_in_gb[-1].append(concated_df["size_in_gb"].sum())
            avg_latencies[-1].append(concated_df["zone_dependent_latency"].mean())
            job_durations[-1].append(concated_df["duration"].mean())
            total_jobs_handled[-1].append(len(concated_df.index))

    total_traffic_cost_in_usd = np.mean(total_traffic_cost_in_usd, axis=0)
    total_traffic_sent_in_gb = np.mean(total_traffic_sent_in_gb, axis=0)
    total_jobs_handled = np.mean(total_jobs_handled, axis=0)
    avg_latencies = np.mean(avg_latencies, axis=0)
    job_durations = np.mean(job_durations, axis=0)

    title = "Traffic Analysis\n"
    bar_titles = []
    bar_improvments = []

    scatter_titles = []
    scatter_improvments = []

    line_titles = []
    line_values = []
    line_improvments = []

    job_duration_titles = []
    job_duration_improvments = []

    max_price_per_gb = max(np.array(total_traffic_sent_in_gb)/np.array(total_traffic_cost_in_usd))
    max_latency = max(avg_latencies)
    for i in range(len(total_traffic_sent_in_gb)):
        # Traffic titles - Bars
        egress = total_traffic_sent_in_gb[i]
        cost = total_traffic_cost_in_usd[i]
        jobs = total_jobs_handled[i]
        lat = avg_latencies[i]
        job_dur = job_durations[i]

        job_duration_titles.append('%.3f' % job_dur + "ms")
        if i > 0:
            percent_improvment = ((job_durations[i-1]-job_durations[i]) / job_durations[i-1]) * 100
            pt = ('%.3f' % percent_improvment)
            job_duration_improvments.append("{} %\nimprovment".format(pt))
        else:
            job_duration_improvments.append("")

        line_values.append(simple_max_addative_weight(
            price = (cost/egress),
            max_price = max_price_per_gb,
            latency = lat,
            max_latency = max_latency
        ))
        line_titles.append("Cost = "+'%.3f' % line_values[-1])
        if i > 0:
            percent_improvment = ((line_values[i-1]-line_values[i]) / line_values[i-1]) * 100
            pt = ('%.3f' % percent_improvment)
            line_improvments.append("{} %\nimprovment".format(pt))
        else:
            line_improvments.append("")

        if i == 0:
            title += "Egress = {}GB, Jobs Count = #{}".format("%.3f"%egress, int(jobs))

        bar_title = "Payment = {}$\nGB Price = {}$".format("%.3f"%cost,"%.3f"%(cost/egress))
        if i > 0:
            percent_improvment = ((total_traffic_cost_in_usd[i-1]-total_traffic_cost_in_usd[i]) / total_traffic_cost_in_usd[i-1]) * 100
            pt = ('%.3f' % percent_improvment)
            bar_improvments.append("{} %\nimprovment".format(pt))
        else:
            bar_improvments.append("")
        bar_titles.append(bar_title)
        # Latency titles - Scatter
        l_title = "Latency {}ms".format('%.3f' %lat)
        if i > 0:
            percent_improvment = ((avg_latencies[i-1]-avg_latencies[i]) / avg_latencies[i-1]) * 100
            pt = ('%.3f' % percent_improvment)
            scatter_improvments.append("{} %\nimprovment".format(pt))
        else:
            scatter_improvments.append("")
        scatter_titles.append(l_title)

    bar_plot(
        x_values=bars_names[0],

        bars_values=total_traffic_cost_in_usd,
        bar_titles=bar_titles,
        bar_improvments=bar_improvments,

        scatter_values=avg_latencies,
        scatter_titles=scatter_titles,
        scatter_improvments=scatter_improvments,

        line_values=line_values,
        line_titles=line_titles,
        line_improvments=line_improvments,

        job_duration_values=job_durations,
        job_duration_titles=job_duration_titles,
        job_duration_improvments=job_duration_improvments,

        title=title
    )
