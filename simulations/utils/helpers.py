import yaml, os
import pandas as pd
import numpy as np
def load_ymal(file_name):
    file_name = os.path.abspath(file_name)
    with open(file_name, 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            return None

def heatmaps_csv_builder(clusters, app_name):
    prices = {}
    latencies = {}
    for cluster_src in clusters:
        prices[cluster_src.zone.name] = []
        latencies[cluster_src.zone.name] = []
        for cluster_dest in clusters:
            price = cluster_src.zone.price_per_gb(cluster_dest.zone)
            prices[cluster_src.zone.name].append(price)

            latency = cluster_src.zone.latency_per_request(cluster_dest.zone)
            latencies[cluster_src.zone.name].append(latency)

    pd.DataFrame(prices).to_csv("run_csv/heatmaps/price_{}.csv".format(app_name), index=False)
    pd.DataFrame(latencies).to_csv("run_csv/heatmaps/latency_{}.csv".format(app_name), index=False)

def capacity_csv_builder(clusters, app_name):
    job_types = list(set([job_type for cluster in clusters for job_type, serivce in cluster.services.items()]))
    capacity = {"Service / Cluster" : job_types }
    for cluster in clusters:
        capacity[cluster.zone.name] = []
        for job in job_types:
            service = cluster.service(job)
            if service != None:
                capacity[cluster.zone.name].append("{} K".format(service.capacity/1000))
            else:
                capacity[cluster.zone.name].append("")

    pd.DataFrame(capacity).to_csv("run_csv/capacity/capacity_{}.csv".format(app_name), index=False)

def app_dag_csv_builder(clusters, app_name):
    print(1)
    job_types = list(set([job_type for cluster in clusters for job_type, serivce in cluster.services.items()]))
    job_types_handeled = []
    cols = ["source", "target"]
    data = []
    for cluster in clusters:
        for job in job_types:
            if job in job_types_handeled:
                continue
            service = cluster.service(job)
            if service is None:
                continue
            job_types_handeled.append(job)
            for dep in service.dependencies:
                data.append([job, dep.job_type])
    print("data", data)
    pd.DataFrame(columns=cols, data=data).to_csv("run_csv/app_dag/capacity_{}.csv".format(app_name), index=False)
