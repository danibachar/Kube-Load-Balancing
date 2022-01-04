import pandas as pd
import numpy as np

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

    pd.DataFrame(prices).to_csv("../app/kubernetes_service_selection/dataframes/heatmaps/price_{}.csv".format(app_name), index=False)
    pd.DataFrame(latencies).to_csv("../app/kubernetes_service_selection/dataframes/heatmaps/latency_{}.csv".format(app_name), index=False)

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

    pd.DataFrame(capacity).to_csv("../app/kubernetes_service_selection/dataframes/capacity/capacity_{}.csv".format(app_name), index=False)

def app_dag_csv_builder(clusters, app_name):
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
    pd.DataFrame(columns=cols, data=data).to_csv("../app/kubernetes_service_selection/dataframes/app_dag/{}.csv".format(app_name), index=False)

def time_of_day_load_csv_builder(df, app_name):
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
        "arrival_time",
    ]
    lines = []
    groups = df.groupby(group_cols)
    for _, group_df in groups:
        line = [
            group_df["source_zone_id"].to_numpy()[0] + "->" + group_df["target_zone_id"].to_numpy()[0], 
            group_df["source_zone_id"].to_numpy()[0], 
            group_df["target_zone_id"].to_numpy()[0],

            group_df["arrival_time"].to_numpy()[0], 

            group_df["load"].to_numpy().mean(),
            
            group_df["load_balance"].to_numpy()[0],
            group_df["cost_mix"].to_numpy()[0],
        ]
        lines.append(line)
        
    d = pd.DataFrame(np.array(lines), columns=["name", "source", "target", "time", "load", "load_balance", "cost_mix",])
    d.to_csv("../app/kubernetes_service_selection/dataframes/load/{}.csv".format(app_name), index=False)
    
def update_rate_to_converge_csv_builder(df, app_name):
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

    pd.concat(dfs).to_csv("../app/kubernetes_service_selection/dataframes/main/{}.csv".format(app_name))

def main_csv_builder(df, app_name):
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
        "weights_update_interval",

    ]
    groups = df.groupby(group_cols)
    dfs = []
    for names, group_df in groups:
        group_df[price_col] = group_df["cost_in_usd"] / group_df["size_in_gb"]
        data = list(names) + [group_df[price_col].mean(), group_df[latency_col].mean()]
        data = [[val] for val in data]
        cols = group_cols + [price_col, latency_col]
        dfs.append(pd.DataFrame(np.array(data).T, columns=cols))

    pd.concat(dfs).to_csv("../app/kubernetes_service_selection/dataframes/main/{}.csv".format(app_name))
    