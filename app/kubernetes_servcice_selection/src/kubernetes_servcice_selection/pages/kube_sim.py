from collections import Counter
from textwrap import dedent

import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, State, Output
import dash_pivottable

from ..app import app
from ..utils import get_df, load_balancing_options, app_options

# import dash
# import dash_core_components as dcc
# import dash_html_components as html
from collections import defaultdict
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import numpy as np
import math, random

def get_layout(**kwargs):
    print("########")
    return html.Div(
        [
            dcc.Markdown(
                dedent(
                    """
                    # Kubernetes Sevice Selection
                    """
                )
            ),
            dcc.Dropdown(
                id="app-option",
                options=[{
                    'label': i,
                    'value': i
                } for i in app_options],
                value=app_options[0]
            ),
            dcc.Loading(
                id = "loading-icon",
                type="circle",
                children=[html.Div(dcc.Graph(id="map"))]
            ),

            # dcc.Graph(id="map", animate=True),
            dcc.Dropdown(
                id="balance-option",
                options=[{
                    'label': i,
                    'value': i
                } for i in load_balancing_options + ["Combined"]] ,
                value="Combined"
            ),
            dcc.Loading(
                id = "loading-icon",
                type="circle",
                children=[html.Div(dcc.Graph(id="latency_vs_price"))]
            ),
            # pivot_table(),
            # dash_pivottable.PivotTable(
            #                 data=pivot_table(),#flat_p,
            #                 cols=["load_balance"],
            #                 rows=["cost_mix"],
            #                 vals=["gb_price"]
            #             ),
            # html.Div(id="pivot_table"),
            dcc.Loading(
                id = "loading-icon",
                type="circle",
                children=[html.Div(id="pivot_table"), ]#id="pivot_table"html.Div([pivot_table()])
                #
            ),
        ]
    )

@app.callback(
    Output("map", "figure"),
    [
        Input("app-option", "value"),
    ],
    [],  # States
)
def map_callback(app_option):
    def map_zones(zone_full_name):
        components = zone_full_name.split("-")
        cloud_provider, region = components[0], components[1:].join("-")
        return cloud_provider, region
    df = get_df(app_name=app_option)
    cps = df["cloud_provider"].unique()
    clusters = df["cluster_name"].unique()
    types = df["job_type"].unique()
    lats = []
    lons = []
    sizes = []
    colors = []
    tags = []
    # Clusters
    location_cache = []
    for c in clusters:
        query = df["cluster_name"] == c
        _df = df[query]
        lat = list(_df["lat"].unique())[0]
        lon = list(_df["lon"].unique())[0]
        key =  "{}_{}".format(lat, lon)
        if key in location_cache:
            lat = lat + 1
            lon = lon + 1
            df[query].loc["lat"] = lat
            df[query].loc["lon"] = lon
        else:
            location_cache.append(key)
        lats.append(lat)
        lons.append(lon)
        colors.append(list(_df["cloud_provider"].unique())[0])
        tags.append(list(_df["cluster_name"].unique())[0])
        sizes.append(30)

    # Services
    def svc_divertion(df):
        pos = [0,0.1,-0.1,0.2,-0.2,0.3,-0.3,0.5,-0.5,0.6,-0.6,0.7,-0.7] # ,0.8,-0.8,0.9,-0.9, 2, -2, 2.3, -2.3

        lat = list(group_df["lat"].unique())[0]
        lat = lat + random.choice(pos)
        lon = list(group_df["lon"].unique())[0]
        lon = lon + random.choice(pos)

        return lat, lon
    for group in df.groupby(["cluster_name", "job_type"]):
        group_name = group[0]
        # print(group_name)
        group_df = group[1]
        lat, lon = svc_divertion(group_df)
        lats.append(lat)
        lons.append(lon)
        colors.append(list(group_df["job_type"].unique())[0])
        tags.append(group_name[0])
        sizes.append(5)

    # print("lats={},lons={},colors={},tags={},sizes={}".format(len(lats),len(lons),len(colors),len(tags),len(sizes)))
    mapin = pd.DataFrame(data={"lat":lats,"lon":lons, "color":colors, "tag":tags, "size":sizes})
    fig = px.scatter_mapbox(
        mapin,
        lat='lat',
        lon='lon',
        color='color',#"cloud_provider", # 'color', # 'cloud_provider'
        zoom=0,
        size='size',#[30 for _ in range(len(df["lon"].index))],
        center=dict(lat=0, lon=180),
        hover_data=['tag',], # "source_zone_id","target_zone_id"
        mapbox_style="carto-positron"
    )
    return fig

@app.callback(
    Output("latency_vs_price", "figure"),
    [
        Input("balance-option", "value"),
        Input("app-option", "value"),
    ],
    [],  # States
)
def callback(balance_option, app_option):
    df = get_df(app_name=app_option, balance_name=balance_option)

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
    fig = px.line(agg_df, x='gb_price', y='latency', color='load_balance', hover_data=[points])
    fig.update_traces(mode="markers+lines")
    fig.update_xaxes(title_text = "Price pe GB in $")
    fig.update_yaxes(title_text = "Latency in ms")
    return fig

@app.callback(
    Output("pivot_table", component_property='children'),
    [
        # Input("balance-option", "value"),
        Input("app-option", "value"),
    ],
    [],  # States
)
def pivot_table(app_option):
    df = get_df()# app_name=app_option
    print("pivot_table - app_option",app_option)
    p = pd.pivot_table(
        df,
        index=["load_balance","cost_mix", "job_type","cluster_name", "app"], #[]"cost_mix", "job_type","arrival_time"
        values=["latency","gb_price", "load", "cost_in_usd", "size_in_gb"], #vals,#"latency","gb_price", "duration"
        # columns=special_cols,/
        aggfunc={
                "cost_in_usd": sum,
                "size_in_gb": sum,
                "load": sum,
                "latency": np.mean,
                "gb_price": np.mean,
                # np.median,
                # _90th,
                # np.sum
                # "95th": lambda y: np.quantile(y, 0.95)
                },
    )
    # print(p)
    p = p.reset_index()
    vals = list(p.values.tolist())
    cols = list(p.columns)
    flat_p = vals
    flat_p.insert(0,cols)

    # return flat_p

    pivot = dash_pivottable.PivotTable(
                    data=flat_p,
                    cols=["load_balance"],
                    rows=["cost_mix"],
                    vals=["gb_price"]
                )
    return [html.Div([pivot])]
