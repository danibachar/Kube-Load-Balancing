import sys, argparse, logging, time
from datetime import datetime

from models import Job

from utils.distributions import heavy_tail_jobs_distribution
from utils.weights import weights_for

from application_generator import generate_application
from dataframe_ploters import plot_dfs
from config_builder import build_config

now = datetime.now()
# log_file_name = 'logs/simulation.{}.log'.format(now)
# logging.basicConfig(filename=log_file_name, level=logging.INFO)

def update_clusters_weights(clusters, weighting_technique, at_tik, cost_function_weights=[0.5,0.5]):
    for cluster in clusters:
        cluster.prepare_for_weight_update(at_tik)

    weights = weights_for(weighting_technique, clusters, at_tik, cost_function_weights)
    if weights == None:
        return
    # print("##########################################")
    # print("weighting_technique {}\nweights {}".format(weighting_technique, weights))
    # print("##########################################")
    for cluster in clusters:
        cluster.weights = weights[cluster.id]

def run(
    clusters,
    jobs_loads,
    front_end,
    updating_weights_technique,
    avg_job_duration=100,
    weightes_update_interval=10,
    cost_function_weights=[0.5,0.5]):
    for tik, load in enumerate(jobs_loads):
        start_time = time.time()
        if tik % weightes_update_interval == 0:
            update_clusters_weights(clusters, updating_weights_technique, tik, cost_function_weights)
        for cluster in clusters:
            job = Job(None, cluster.zone, avg_job_duration, load, front_end)
            cluster.consume(job, tik*1000)
        # print("###########################")
        # print("single run tik = {} took = {}".format(tik, time.time()-start_time))
        # print("###########################")

def run_app(config, clusters, front_end, cost_function_weights):
    funcs = config["funcs"]
    tiks_count = config["tiks_count"]
    rps = config["rps"]
    distribution_name = config["distribution"]

    jobs_loads = heavy_tail_jobs_distribution(distribution_name, tiks_count, rps)

    data_frames = {}
    for name, val in funcs.items():
        for cluster in clusters:
            cluster.reset_state()
            cluster.func_name = name
        run(
            clusters=clusters,
            jobs_loads=jobs_loads,
            front_end=front_end,
            updating_weights_technique=val["weight_calc"],
            avg_job_duration=100,
            weightes_update_interval=10,
            cost_function_weights=cost_function_weights
        )
        data_frames[name] = { s.full_name: s.job_data_frame for cluster in clusters for s in cluster.services.values() }

    return data_frames

def main(config):
    ymals = config["simulation_ymals"]
    latency_ymal = ymals["latency"]
    prcing_ymal = ymals["pricing"]
    app_ymals = ymals["apps"]

    number_of_rounds = config["rounds"]

    price_weights = config["cost_function"]["price_weight"]
    latency_weights = config["cost_function"]["latency_weight"]


    dfs = {}
    for key, app_ymal in app_ymals.items():
        app_name = key.split("/")[-1]
        print("Building app - ", app_name)

        clusters, front_end = generate_application(app_ymal, latency_ymal, prcing_ymal, app_name)

        # __dfs = {}
        total_start_time = time.time()
        # for pw, lw in zip(price_weights, latency_weights):
        _dfs = {}
        for i in range(number_of_rounds):
            st = time.time()
            _dfs[i] = run_app(config, clusters, front_end, cost_function_weights=[0.5,0.5])
            print("main iteration took = {}".format(time.time()-st))
            # __dfs["{}_{}".format(pw,lw)] = _dfs
        print("running main  {} times took  = {}".format(number_of_rounds, time.time()-total_start_time))
        dfs[app_name] = _dfs
    return dfs

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

    dfs = main(config)
    plot_dfs(dfs)
