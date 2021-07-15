import sys, argparse, logging, time, json, random, multiprocessing
from timeit import default_timer as timer
from datetime import datetime
import numpy as np
import pandas as pd

from models import Job

from utils.distributions import heavy_tail_jobs_distribution
from utils.weights import weights_for
from utils.helpers import capacity_csv_builder, heatmaps_csv_builder, app_dag_csv_builder

from application_generator import generate_application
from dataframe_ploters import plot_df, plot_maps
from config_builder import build_config

def update_clusters_weights(clusters, weighting_technique, at_tik, cost_function_weights):
    s = timer()
    for cluster in clusters:
        cluster.build_services_df()
    weights = weights_for(weighting_technique, clusters, at_tik, cost_function_weights)
    e = timer()

    if weights == None:
        print("weights update error")
        return
    for cluster in clusters:
        cluster.weights = weights

def run(
    clusters,
    jobs_loads,
    front_ends,
    updating_weights_technique,
    avg_job_duration,
    weightes_update_interval,
    cost_function_weights
):
    for tik, load in enumerate(jobs_loads):
        start_time = time.time()
        if tik % weightes_update_interval == 0:
            update_clusters_weights(clusters, updating_weights_technique, tik, cost_function_weights)
        for cluster in clusters:
            for front_end in front_ends:
                job = Job(None, cluster.zone, avg_job_duration, load, front_end)
                cluster.consume(job, tik*1000)

def run_app(config, clusters, front_ends):
    funcs = config["funcs"]
    tiks_count = config["tiks_count"]
    rpses = config["rps"]
    distribution_name = config["distribution"]

    price_weights = config["cost_function"]["price_weight"]
    latency_weights = config["cost_function"]["latency_weight"]

    dfs = []
    for rps in rpses:
        jobs_loads = heavy_tail_jobs_distribution(distribution_name, tiks_count, rps)
        for pw, lw in zip(price_weights, latency_weights):
            for name, val in funcs.items():
                for cluster in clusters:
                    cluster.reset_state()
                run(
                    clusters=clusters,
                    jobs_loads=jobs_loads,
                    front_ends=front_ends,
                    updating_weights_technique=val["weight_calc"],
                    avg_job_duration=100,
                    weightes_update_interval=10,
                    cost_function_weights=[pw, lw]
                )
                df = pd.concat([s.job_data_frame for cluster in clusters for s in cluster.services.values() ])
                df["load_balance"] = name
                df["cost_mix"] = "beta={}".format(pw)
                dfs.append(df)


    return pd.concat(dfs)

def run_app_multi_processing(args):
    round = args[0]
    config = args[1]
    clusters = args[2]
    front_ends = args[3]
    st = time.time()
    df = run_app(config, clusters, front_ends)
    df["testing_round"] = round
    print("single round {} took = {}".format(round, time.time()-st))
    return df

def main(config):
    ymals = config["simulation_ymals"]
    latency_ymal = ymals["latency"]
    prcing_ymal = ymals["pricing"]
    app_ymals = ymals["apps"]
    datacenters_yml = ymals["datacenters_locations"]
    number_of_rounds = config["rounds"]

    app_name_to_dfs = {}
    clusters_to_app_map = {}
    total_start_time = time.time()
    for key, app_ymal in app_ymals.items():
        app_name = key.split("/")[-1].split(".")[0]
        print("Building app - ", app_name)
        clusters, front_ends = generate_application(app_ymal, latency_ymal, prcing_ymal, datacenters_yml, app_name)

        p = multiprocessing.Pool(multiprocessing.cpu_count())
        args = []

        for i in range(number_of_rounds):
            clusters, front_ends = generate_application(app_ymal, latency_ymal, prcing_ymal, datacenters_yml, app_name)
            args.append([i, config, clusters, front_ends])

        dfs = p.map(run_app_multi_processing, args)
        clusters_to_app_map[app_name] = clusters
        app_name_to_dfs[app_name] = pd.concat(dfs)

    print("running main  {} times took  = {}".format(number_of_rounds, time.time()-total_start_time))
    return app_name_to_dfs, clusters_to_app_map



def _preps_df(df):
    price_col = "gb_price"
    latency_col = "latency"
    group_cols = [
        "job_type",
        "cloud_provider",
        "cluster_name",
        "lat",
        "lon",
        "source_zone_id",
        "target_zone_id",
        "load_balance",
        "cost_mix",
        "source_job_type",
    ]
    groups = df.groupby(group_cols)
    dfs = []
    for names, group_df in groups:
        group_df[price_col] = group_df["cost_in_usd"] / group_df["size_in_gb"]
        data = list(names) + [group_df[price_col].mean(), group_df[latency_col].mean()]
        data = [[val] for val in data]
        cols = group_cols + [price_col, latency_col]
        dfs.append(pd.DataFrame(np.array(data).T, columns=cols))

    return pd.concat(dfs)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Run Kuberentes simulation')
    parser.add_argument(
        '--config_file_name',
        type=str,
        default="yamls/configurations/simple_run.yml",
        help='A configuration file that describe the test'
    )

    args = parser.parse_args()
    config_file_name = args.config_file_name
    config = build_config(config_file_name)

    app_name_to_df_map, clusters_to_app_map = main(config)
    for app_name, clusters in clusters_to_app_map.items():
        heatmaps_csv_builder(clusters, app_name)
        capacity_csv_builder(clusters, app_name)
        app_dag_csv_builder(clusters, app_name)

    for app_name, df in app_name_to_df_map.items():
        df = _preps_df(df)
        df.to_csv("run_csv/main/{}.csv".format(app_name))
