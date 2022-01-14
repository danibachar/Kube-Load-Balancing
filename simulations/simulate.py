import argparse, logging, time, multiprocessing
from timeit import default_timer as timer
import pandas as pd
import numpy as np

from models import Job

from utils.distributions import heavy_tail_jobs_distribution
from utils.weights import weights_for
from utils.csv_builders import capacity_csv_builder, heatmaps_csv_builder, app_dag_csv_builder, time_of_day_load_csv_builder, drops_csv_builder, main_csv_builder
from utils.chaos_generator import load_by_time_of_day_from, random_chaos_into

from application_generator import generate_application
from config_builder import build_config

def update_clusters_weights(clusters, weighting_technique, at_tik, cost_function_weights):
    # ss = time.time()
    for cluster in clusters:
        cluster.build_services_df()
    weights = weights_for(weighting_technique, clusters, at_tik, cost_function_weights)

    if weights == None:
        print("weights update error")
        return
    for cluster in clusters:
        cluster.weights = weights
    # print("update clusters took ", time.time()-ss)

def run(
    clusters,
    jobs_loads,
    front_ends,
    updating_weights_technique,
    avg_job_duration,
    weights_update_interval,
    cost_function_weights
):
    # print("run:\n- interval = {}\n- cost_mix = {}\n- weights = {}".format(weights_update_interval, cost_function_weights, updating_weights_technique))
    # Each simulation is of a 24hrs timeframe
    # assert(len(jobs_loads) == 2880)
    for tik_in_min, load in enumerate(jobs_loads): # Each tik indicates a minute
        # s = time.time()
        # Generate chaos BEFORE updating weights
        # Inject some chaos, like cluster un-availability, pods drops (i.e capacity affected)
        # tik_in_min = tik_in_min % 1439
        if tik_in_min % weights_update_interval == 0: 
            # print("updateing weights with interval {} at tik {}".format(weights_update_interval, tik))
            # Time of day in minutes
            update_clusters_weights(clusters, updating_weights_technique, tik_in_min*60, cost_function_weights)
        start = tik_in_min*60
        end = start + 60
        for tik_in_seconds in range(start, end):
            for cluster in clusters:
                # Update load by time of day
                load_by_time_of_day = load_by_time_of_day_from(load, tik_in_min, cluster.zone.region.gmt_offset)
                # print("sending {} on cluster {}".format(load_by_time_of_day, cluster.id))
                for front_end in front_ends:
                    # job = Job(None, cluster.zone, avg_job_duration, load_by_time_of_day, type=front_end)
                    job = Job(None, cluster.zone, load_by_time_of_day, type=front_end)
                    cluster.consume(job, tik_in_seconds)

        continue

        if tik < 1440:
            # tik = tik * 1000
            if tik == 0:
                update_clusters_weights(clusters, updating_weights_technique, tik, cost_function_weights)
            for cluster in clusters:
                # Update load by time of day
                load_by_time_of_day = load_by_time_of_day_from(load, tik, cluster.zone.region.gmt_offset)
                # print("load {} at {} for {}".format(load_by_time_of_day, tik, cluster.id))
                # print("sending {} on cluster {}".format(load_by_time_of_day, cluster.id))
                for front_end in front_ends:
                    # job = Job(None, cluster.zone, avg_job_duration, load_by_time_of_day, type=front_end)
                    job = Job(None, cluster.zone, load_by_time_of_day, type=front_end)
                    cluster.consume(job, tik)
        else:
            if tik == 1440:
                print("#######################")
                print("switchinng to next day")
                print("#######################")
            # tik = tik * 1000
            # random_chaos_into(clusters=clusters)
            if tik % weights_update_interval == 0: 
                # print("updateing weights with interval {} at tik {}".format(weights_update_interval, tik))
                update_clusters_weights(clusters, updating_weights_technique, tik, cost_function_weights)
                
            for cluster in clusters:
                # Update load by time of day
                load_by_time_of_day = load_by_time_of_day_from(load, tik, cluster.zone.region.gmt_offset)
                # print("load {} at {} for {}".format(load_by_time_of_day, tik, cluster.id))
                # print("sending {} on cluster {}".format(load_by_time_of_day, cluster.id))
                for front_end in front_ends:
                    # job = Job(None, cluster.zone, avg_job_duration, load_by_time_of_day, type=front_end)
                    job = Job(None, cluster.zone, load_by_time_of_day, type=front_end)
                    cluster.consume(job, tik)
        # print("running single tik took ", time.time() - s)
        

def run_app(config, clusters, front_ends):
    funcs = config["funcs"]
    tiks_count = config["tiks_count"]
    rpses = config["rps"]
    weights_update_intervals = config["weights_update_intervals"]
    distribution_name = config["distribution"]

    price_weights = config["cost_function"]["price_weight"]
    latency_weights = config["cost_function"]["latency_weight"]

    dfs = []
    for rps in rpses:
        # TODO - add some randomness into the distribution, i.e calls not arrived equally for all FE.
        # Simulate different time of day loads accordsing to articles
        jobs_loads = heavy_tail_jobs_distribution(distribution_name, tiks_count, rps)
        jobs_loads = np.concatenate([jobs_loads, jobs_loads])
        for weights_update_interval in weights_update_intervals:
            for pw, lw in zip(price_weights, latency_weights):
                for name, val in funcs.items():
                        for cluster in clusters:
                            cluster.reset_state()
                        s = time.time()
                        run(
                            clusters=clusters,
                            jobs_loads=jobs_loads,
                            front_ends=front_ends,
                            updating_weights_technique=val["weight_calc"],
                            avg_job_duration=100,
                            weights_update_interval=weights_update_interval,
                            cost_function_weights=[pw, lw]
                        )
                        print("just run took ", time.time() - s)
                        for cluster in clusters:
                            cluster.build_services_df()
                        df = pd.concat([s.job_data_frame for cluster in clusters for s in cluster.services.values()])
                        df["load_balance"] = name
                        df["cost_mix"] = "beta={}".format(pw)
                        df["weights_update_interval"] = weights_update_interval
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

    s = time.time()
    for key, app_ymal in app_ymals.items():
        app_name = key.split("/")[-1].split(".")[0]
        print("Building app - ", app_name)

        p = multiprocessing.Pool(multiprocessing.cpu_count())
        args = []

        for i in range(number_of_rounds):
            clusters, front_ends = generate_application(app_ymal, latency_ymal, prcing_ymal, datacenters_yml, app_name)
            args.append([i, config, clusters, front_ends])

        dfs = p.map(run_app_multi_processing, args)
        df = pd.concat(dfs)
        dump_test_results(app_name, clusters, df)

    print("running main  {} times took  = {}".format(number_of_rounds, time.time()-s))

def dump_test_results(app_name, clusters, df):
    print("Dumping results for ", app_name)

    heatmaps_csv_builder(clusters, app_name)
    capacity_csv_builder(clusters, app_name)
    app_dag_csv_builder(clusters, app_name)

    time_of_day_load_csv_builder(df, app_name)

    # drops_csv_builder(df, app_name)
    # df.to_csv("../app/kubernetes_service_selection/dataframes/full/{}.csv".format(app_name))
    # drop_selector = df["is_dropped"] == 1
    # no_drop_selector = df["is_dropped"] == 0

    # main_csv_builder(df[drop_selector], app_name+"_just_drops")
    # main_csv_builder(df[no_drop_selector], app_name+"_no_drops")

    main_csv_builder(df, app_name)
    df = df[df["arrival_time"] > 1_439 * 60]

    # drop_selector = df["is_dropped"] == 1
    # no_drop_selector = df["is_dropped"] == 0

    # main_csv_builder(df[drop_selector], app_name+"_filtered_at_just_drops")
    # main_csv_builder(df[no_drop_selector], app_name+"_filtered_at_no_drops")
    main_csv_builder(df, app_name+"_arrival_time")

    


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
    main(config)