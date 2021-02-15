from collections import Counter
from textwrap import dedent

import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, State, Output
import dash_pivottable

from ..app import app
from ..utils import get_df, load_balancing_options, app_options, cached_latest_app_secetion

# import dash
# import dash_core_components as dcc
# import dash_html_components as html
from collections import defaultdict
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import numpy as np

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
                value=cached_latest_app_secetion
            ),
            dcc.Graph(id="map"),
            dcc.Dropdown(
                id="balance-option",
                options=[{
                    'label': i,
                    'value': i
                } for i in load_balancing_options + ["Combined"]] ,
                value="Combined"
            ),
            dcc.Graph(id="latency_vs_price"),
            pivot_table(),

            # dcc.Graph(id="total_cost"),

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

    df = get_df(app_name=app_option)
    fig = px.scatter_mapbox(
        df,
        lat='lat',
        lon='lon',
        color='cloud_provider',
        zoom=0,
        # size=[30 for _ in range(len(df["lon"].index))],
        center=dict(lat=0, lon=180),
        hover_data=['cloud_provider',], # "source_zone_id","target_zone_id"
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

def pivot_table():
    df = get_df()

    p = pd.pivot_table(
        df,
        index=["load_balance","cost_mix", "job_type", "arrival_time","cluster_name"], #[]"cost_mix", "job_type"
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
    p = p.reset_index()
    vals = list(p.values.tolist())
    cols = list(p.columns)
    flat_p = vals
    flat_p.insert(0,cols)
    return  dash_pivottable.PivotTable(
                    data=flat_p,
                    cols=["load_balance"],
                    rows=["cost_mix"],
                    vals=["gb_price"]
                )
