import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import lfilter
import math
from collections import defaultdict

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.cost import simple_max_addative_weight

def _90th(x):
    return np.quantile(x, 0.9)

def _map_preps(clusters):
    data = {}
    for cluster in clusters:
        cp_id = cluster.zone.cloud_provider.id
        if cp_id not in data:
            data[cp_id] = defaultdict(list)
        data[cp_id]["lons"].append(cluster.zone.location["lon"])
        data[cp_id]["lats"].append(cluster.zone.location["lat"])
        data[cp_id]["name"].append(cluster.zone.name)

    return data

def _plot_service_loads(df, title=""):
    # Plot smoothing params
    n = 20  # the larger n is, the smoother curve will be
    b = [1.0 / n] * n
    a = 1

    markers = ["h","v","o"]
    linestyles = ["-","--",":"]
    alphas = [0.3,0.6, 1]

    # Ploting!
    for cost_mix_group in df.groupby(["cost_mix"]):
        cost_mix_name = cost_mix_group[0]
        cost_mix_df = cost_mix_group[1]

        # Preparing plots layout
        plots_count = 0
        for groups in cost_mix_df.groupby(["job_type", "target_zone_id"]):
            plots_count+=1
        fig, axs  = plt.subplots(math.ceil(plots_count/3), 3)

        for groups in cost_mix_df.groupby(["job_type", "target_zone_id"]):
            table_name = groups[0]
            g_df = groups[1]

            plots_count-=1
            w = 1
            for group in g_df.groupby("load_balance"):
                name = group[0]
                _g_df = group[1]
                y = lfilter(b, a, _g_df["load"].to_list())
                x = _g_df["arrival_time"].to_list()
                axs[int(plots_count/3), plots_count%3].plot(x, y, label = name, linewidth=1, linestyle=linestyles[w-1])
                axs[int(plots_count/3), plots_count%3].set_xlabel("time")
                axs[int(plots_count/3), plots_count%3].set_ylabel("load")
                w+=1

            axs[int(plots_count/3), plots_count%3].set_title(table_name)

        fig.suptitle(cost_mix_name)
        plt.legend()
        plt.subplots_adjust(hspace=0.5)
        plt.show()

def _plot_service(df, title=""):
    # df[values_cols] = df[values_cols].apply(pd.to_numeric)
    n = 20  # the larger n is, the smoother curve will be
    b = [1.0 / n] * n
    a = 1
    # .aggregate({"load": lambda l: lfilter(b, a,l)})
    # agg_df = df.groupby(["job_type", "target_zone_id", "load_balance"]).reset_index()
    fig = px.line(df, x='arrival_time', y='load', color='load_balance', facet_col='target_zone_id', facet_row='job_type',)
    fig.update_traces(mode="markers+lines")
    fig.update_xaxes(title_text = "Price pe GB in $")
    fig.update_yaxes(title_text = "Latency in ms")
    fig.show()
    return

def _plot_pivot(app_df, app_name):

    values_cols = ["duration", "latency", "gb_price", ] #"load"
    index_cols = ["load_balance", ] # "job_type","cost_mix"
    special_cols = ["cost_mix"]

    app_df = app_df[values_cols + index_cols + special_cols] #
    app_df[values_cols] = app_df[values_cols].apply(pd.to_numeric)
    for value in values_cols:
        vals = [value]
        _df = app_df[index_cols + vals + special_cols]
        print(_df)
        p = pd.pivot_table(
            _df,
            index=index_cols, #[]"cost_mix", "job_type"
            values=vals,#"latency","gb_price", "duration"
            columns=special_cols,
            aggfunc=[
                    np.mean,
                    # np.median,
                    # _90th,
                    # np.sum
                    # "95th": lambda y: np.quantile(y, 0.95)
                    ],
        )
        ax = p.T.plot(kind="bar", legend=True, title=app_name + "_" + value, grid=True)

        plt.xticks(fontsize='xx-small', rotation=30)#rotation='horizontal')

        plt.show()

def _plot_heavy_tail_dist():
    # plot density function
    m = 27_000
    a = 10
    # s = heavy_tail_jobs_distribution("pareto", 1000, m)
    s = (np.random.pareto(a, size = 500) + 1) * m
    count, bins, _ = plt.hist(s, 100, density=True)
    fit = a*m**a / bins**(a+1)
    plt.plot(bins, max(count)*fit/max(fit), linewidth=2, color='r')
    plt.xlabel('RPS')
    plt.ylabel('Pr(RPS=x)')
    plt.show()

def _plotly_plot(df):
    values_cols = ["duration", "latency", "gb_price", ] #"load"
    index_cols = ["load_balance", ] # "job_type","cost_mix"
    special_cols = ["cost_mix"]
    cols_of_interest = values_cols + index_cols + special_cols + ['app']
    df = df[cols_of_interest] #
    df[values_cols] = df[values_cols].apply(pd.to_numeric)

    x_name = "gb_price"
    y_name = "latency"
    lines_name = "load_balance"
    points = "cost_mix"
    agg_df = df.groupby([lines_name,points,"app"]).aggregate({x_name: np.mean, y_name: np.mean}).reset_index()
    fig = px.line(agg_df, x='gb_price', y='latency', color='load_balance', facet_col='app', hover_data=[points],facet_col_wrap=4)
    fig.update_traces(mode="markers+lines")
    fig.update_xaxes(title_text = "Price pe GB in $")
    fig.update_yaxes(title_text = "Latency in ms")
    fig.show()

def plot_maps(clusters_to_app_map):
    def col_map(c):
        if c % 4 > 0:
            return c%4 + math.floor(c/4)
        return 4
    fig = make_subplots(rows=2, cols=4, specs=[
        [{"type": "mapbox", },{"type": "mapbox", },{"type": "mapbox", },{"type": "mapbox", }],
        [{"type": "mapbox", },{"type": "mapbox", },{"type": "mapbox", },{"type": "mapbox", }]
    ])
    count = 0
    for app, clusters in clusters_to_app_map.items():
        cp_to_clusters_map = _map_preps(clusters)
        count+=1
        for cp_name, data in cp_to_clusters_map.items():
            row = min(1, math.ceil(count/4))
            col = col_map(count)
            fig.add_trace(
                go.Scattermapbox(#Scattergeo # Scattermapbox
                    mode = "markers",
                    lon = data["lons"],
                    lat = data["lats"],
                    text = data["name"],
                    name = cp_name,
                    marker = {'size': 10},
                    subplot = 'mapbox{}'.format(count)
                ),
                row=row, col=col
            )
            lon, lat = sum(data["lons"])/len(data["lons"]), sum(data["lats"])/len(data["lats"])
            p = {
                'mapbox{}'.format(count): {
                    'center': {'lon': lon, 'lat': lat},
                    'style': "stamen-terrain",
                    'zoom': 0
                    },
            }
            fig.update_layout(**p)

    fig.show()

def plot_df(df):
    df["gb_price"] = df["cost_in_usd"] / df["size_in_gb"]
    _plotly_plot(df)

    for app_group in df.groupby("app"):

        app_name = app_group[0]
        app_df = app_group[1]
        # Bck
        app_df.to_csv("run_csv/{}.csv".format(app_name))
        # Filter Front end
        app_df = app_df[app_df["job_type"] != "product_page"]
        app_df = app_df[app_df["job_type"] != "image_server"]
        app_df = app_df[app_df["job_type"] != "api_server"]
        app_df = app_df[app_df["job_type"] != "cdn"]
        app_df = app_df[app_df["job_type"] != "chat"]
        app_df = app_df[app_df["job_type"] != "game"]
        # _plot_pivot(app_df, app_name)
        # _plot_service(app_df,app_name)
        # _plot_service_loads(app_df, app_name)
