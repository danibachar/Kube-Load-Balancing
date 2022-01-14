import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from ..utils import get_load_df
import plotly.figure_factory as ff

markers = ['circle', 'square', 'diamond', 'triangle-up', 'triangle-down', 'pentagon', 'hexagon', 'octagon', 'star', 'hexagram', 'star-square',]

def total_load_global(app_option, balance_option):
    df = get_load_df(app_option)
    
    df = df[df["cost_mix"] == "beta=0.5"]

    print("df", df)

    df = df[df.source == "CLIENT"] # We want only the load on the system itself
    if balance_option != "Combined":
        df = df[df.load_balance == balance_option]

    # TODO avg 5 min

    df["smooth_load"] = df["load"].ewm(com=0.5,min_periods=5).mean()
    df["rolling_load"] = df["load"].rolling(5).mean()
    df["agg_load"] = df["load"].gropby(["", ""]).agg({  "load":sum,})
    new_df = df.stack().reset_index().groupby(["target", ]).mean().unstack("Type").reset_index()
    
    return px.line(new_df, x="time", y="load", color="target")
    return px.line(df, x="time", y="load", color="target")

def app_load_graph(app_option, balance_option=None):
    df = get_load_df(app_option)
    df = df[df["cost_mix"] == "beta=0.5"]

    if balance_option != "Combined":
        df = df[df.load_balance == balance_option]

    return px.line(df, x="time", y="load", color="name")