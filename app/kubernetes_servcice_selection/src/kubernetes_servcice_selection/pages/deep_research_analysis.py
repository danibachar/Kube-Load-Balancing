import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, State, Output

from textwrap import dedent
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import plotly.figure_factory as ff
from ipywidgets import interactive, HBox, VBox, widgets, interact
import math

from ..utils import get_df, get_balancing_options, get_app_options, random_color
from ..app import app
from ..graphs.cdfs import cdf_by_weights_comparison
from ..graphs.price_vs_latency import price_vs_latency, app_latecy_to_price_graph

beta_unicode = "&#946;"

def get_layout(**kwargs):
    return html.Div(
        [
            dcc.Markdown(
                dedent(
                    """
                    # Research Analysis
                    """
                )
            ),
            dcc.Dropdown(
                id="app-option",
                options=[{
                    'label': i,
                    'value': i
                } for i in get_app_options()],
                value=get_app_options()[0]
            ),
            dcc.Dropdown(
                id="balance-option",
                options=[{
                    'label': i,
                    'value': i
                } for i in get_balancing_options()] ,
                value="Combined"
            ),
            dcc.Loading(
                id = "loading-icon",
                type="circle",
                children=[
                    html.Div(
                        children=[dcc.Graph(id="latency_vs_price")],
                        style={'margin': 'auto'},
                    ),
                ]
            ),
            dcc.Loading(
                id = "loading-icon",
                type="circle",
                children=[html.Div(dcc.Graph(id="price_cdf_koss_weights")),]
            ),
            dcc.Loading(
                id = "loading-icon",
                type="circle",
                children=[html.Div(dcc.Graph(id="price_cdf_algo_comparison")),]
            ),
            dcc.Loading(
                id = "loading-icon",
                type="circle",
                children=[html.Div(dcc.Graph(id="latency_cdf_koss_weights")),]
            ),
            dcc.Loading(
                id = "loading-icon",
                type="circle",
                children=[html.Div(dcc.Graph(id="latency_cdf_algo_comparison")),]
            ),
            # dcc.Loading(
            #     id = "loading-icon",
            #     type="circle",
            #     children=[html.Div(dcc.Graph(id="latecy-to-price-graph"))]
            # ),
        ]
    )

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
    df = _prepare_df_with_query(df)
    return price_vs_latency(df)

@app.callback(
    Output('latecy-to-price-graph', 'figure'),
    [
        Input("app-option", "value"),
    ])
def latecy_to_price_graph(app_option):
    return app_latecy_to_price_graph(app_option)

@app.callback(
    Output("price_cdf_koss_weights", "figure"),
    [
        Input("app-option", "value"),
    ],
    [],  # States
)
def price_cdf_koss_weights(app_option):
    df = get_df(app_name=app_option)
    koss_df = _prepare_algo_df(df, "KOSS")
    fig = cdf_by_weights_comparison(
        [koss_df], [""],
        "Price CDF by {} value".format(beta_unicode),
        "GB Price ($)", "P[X<x]", "gb_price"
    )
    return _update_clear_layout_with(fig)

@app.callback(
    Output("price_cdf_algo_comparison", "figure"),
    [
        Input("app-option", "value"),
    ],
    [],  # States
)
def cdf_price(app_option):
    df = get_df(app_name=app_option)

    col = "gb_price"
    dfs = _prepare_cdf_algo_comparison_dfs(df, col)

    fig = cdf_by_weights_comparison(
        dfs=dfs,
        name_prefixes=["koss","koss", "rr", ],
        fig_title="Price KOSS vs RR max/min {} values".format(beta_unicode),
        xaxis_title="GB Price ($)",
        yaxis_title="P[X<x]",
        col=col,
        skip_on_mean=False
    )
    return _update_clear_layout_with(fig)

@app.callback(
    Output("latency_cdf_koss_weights", "figure"),
    [
        Input("app-option", "value"),
    ],
    [],  # States
)
def latency_cdf_koss_weights(app_option):
    df = get_df(app_name=app_option)

    koss_df = _prepare_algo_df(df, "KOSS")
    fig = cdf_by_weights_comparison(
        dfs=[koss_df],
        name_prefixes=[""],
        fig_title="Latency CDF by {} value".format(beta_unicode),
        xaxis_title="Latency (ms)",
        yaxis_title="P[X<x]",
        col="latency"
    )
    return _update_clear_layout_with(fig)

@app.callback(
    Output("latency_cdf_algo_comparison", "figure"),
    [
        Input("app-option", "value"),
    ],
    [],  # States
)
def cdf_latency(app_option):
    df = get_df(app_name=app_option)

    col = "latency"
    dfs = _prepare_cdf_algo_comparison_dfs(df, col)

    fig = cdf_by_weights_comparison(
        dfs=dfs,
        name_prefixes=["koss","koss", "rr",],
        fig_title="Latency KOSS vs RR max/min {} values".format(beta_unicode),
        xaxis_title="Latency (ms)",
        yaxis_title="P[X<x]",
        col=col,
        skip_on_mean=False
    )

    return _update_clear_layout_with(fig)

def _prepare_cdf_algo_comparison_dfs(df, col):
    cost_mix_col = "cost_mix"

    koss_df = _prepare_algo_df(df, "KOSS")
    best_group, worst_group = _best_worst_cost_mix_val(koss_df, col)
    best_koss_df = koss_df[koss_df[cost_mix_col] == best_group]
    worst_koss_df = koss_df[koss_df[cost_mix_col] == worst_group]

    wrr_df = _prepare_algo_df(df, "RR")
    best_group, worst_group = _best_worst_cost_mix_val(wrr_df, col)
    best_wrr_df = wrr_df[wrr_df[cost_mix_col] == best_group]
    worst_wrr_df = wrr_df[wrr_df[cost_mix_col] == worst_group]
    if col == "gb_price":
        return [best_koss_df, worst_koss_df, best_wrr_df, ]
    return [worst_koss_df, best_koss_df, best_wrr_df, ]

def _best_worst_cost_mix_val(df, col):
    best_group = None
    best_val = math.inf
    worst_group = None
    worst_val = -math.inf

    for name, _df in df.groupby(["cost_mix"]):
        mean = _df[col].mean()
        if mean < best_val:
            best_val = mean
            best_group = name
        if mean > worst_val:
            worst_val = mean
            worst_group = name
    return best_group, worst_group

def _prepare_algo_df(df, algo):
    return _prepare_df_with_query(df, df["load_balance"] == algo)

def _prepare_df_with_query(df, query=None):
    if query is not None:
        df = df[query]
    else:
        df = df
    # Temp filtering 1/0
    df = df[df["cost_mix"] != "beta=1.0"]
    df = df[df["cost_mix"] != "beta=0.0"]
    return df.replace(regex=r'^beta=', value='{}='.format(beta_unicode))

def _update_clear_layout_with(fig, height=600):
    fig.update_layout(
        height=height, showlegend=True,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig
