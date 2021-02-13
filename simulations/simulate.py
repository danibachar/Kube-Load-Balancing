import sys, argparse, logging, time, json
from datetime import datetime
import numpy as np
import pandas as pd

import jsonpickle

from models import Job

from utils.distributions import heavy_tail_jobs_distribution
from utils.weights import weights_for

from application_generator import generate_application
from dataframe_ploters import plot_df, plot_maps
from config_builder import build_config

now = datetime.now()
# log_file_name = 'logs/simulation.{}.log'.format(now)
# logging.basicConfig(filename=log_file_name, level=logging.INFO)

def update_clusters_weights(clusters, weighting_technique, at_tik, cost_function_weights):
    s = datetime.now()
    weights = weights_for(weighting_technique, clusters, at_tik, cost_function_weights)
    e = datetime.now()

    if weights == None:
        print("weights update error")
        return
    for cluster in clusters:
        cluster.weights = weights[cluster.id]

    json_object = jsonpickle.encode(weights)
    with open('weights/weights_{}_{}.json'.format(weighting_technique, at_tik), 'w') as outfile:
        json.dump(json_object, sort_keys=True, indent = 4,fp=outfile)
    #
    # print("##########################################")
    # print("weighting_technique {}\nweights {}\ncalculation took {}ms".format(weighting_technique, json_object, e-s))
    # print("##########################################")

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
        # print("###########################")
        # print("single run tik = {} took = {}".format(tik, time.time()-start_time))
        # print("###########################")

def run_app(config, clusters, front_ends):
    funcs = config["funcs"]
    tiks_count = config["tiks_count"]
    rps = config["rps"]
    distribution_name = config["distribution"]

    price_weights = config["cost_function"]["price_weight"]
    latency_weights = config["cost_function"]["latency_weight"]

    jobs_loads = heavy_tail_jobs_distribution(distribution_name, tiks_count, rps)

    dfs = []
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
            df["cost_mix"] = "p={}|l={}".format(pw, lw)
            # print("####################################################")
            print("df after running {}\nwith {}\nis = {}".format(name, "p={}|l={}".format(pw, lw), len(df.index)))
            # print("####################################################")
            dfs.append(df)

    return pd.concat(dfs)

def main(config):
    ymals = config["simulation_ymals"]
    latency_ymal = ymals["latency"]
    prcing_ymal = ymals["pricing"]
    app_ymals = ymals["apps"]
    datacenters_yml = ymals["datacenters_locations"]
    number_of_rounds = config["rounds"]

    dfs = []

    total_start_time = time.time()
    clusters_to_app_map = {}
    for key, app_ymal in app_ymals.items():
        app_name = key.split("/")[-1].split(".")[0]
        print("Building app - ", app_name)
        clusters, front_ends = generate_application(app_ymal, latency_ymal, prcing_ymal, datacenters_yml, app_name)
        clusters_to_app_map[app_name] = clusters
        for i in range(number_of_rounds):
            st = time.time()
            df = run_app(config, clusters, front_ends)
            df["testing_round"] = i
            df["app"] = app_name
            dfs.append(df)

            print("single round took = {}".format(time.time()-st))
    print("running main  {} times took  = {}".format(number_of_rounds, time.time()-total_start_time))

    return pd.concat(dfs), clusters_to_app_map

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

    df, clusters_to_app_map = main(config)

    plot_maps(clusters_to_app_map)
    df.to_csv("run_csv/{}.csv".format("main"))
    # plot_df(df) .
