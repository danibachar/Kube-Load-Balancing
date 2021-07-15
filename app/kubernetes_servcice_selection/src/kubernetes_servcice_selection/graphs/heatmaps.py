import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from ..utils import get_price_heat_map_df, get_latency_heat_map_df
import plotly.figure_factory as ff

def app_pricing_heat_map(app_option):
    # df = pd.read_csv("~/Documents/IDC/Kube-Load-Balancing/app/kubernetes_servcice_selection/dataframes/heatmaps/price_{}.csv".format(app_option), index_col=False)
    df = get_price_heat_map_df(app_option)
    return _heat_map(df)

def app_latency_heat_map(app_option):
    # df = pd.read_csv("~/Documents/IDC/Kube-Load-Balancing/app/kubernetes_servcice_selection/dataframes/heatmaps/latency_{}.csv".format(app_option), index_col=False)
    df = get_latency_heat_map_df(app_option)
    return _heat_map(df)

def _heat_map(df):
    x = df.columns.values.tolist()
    y = df.columns.values.tolist()
    data = df.values.tolist()

    fig = ff.create_annotated_heatmap(data, x=x, y=y, colorscale='Greys')
    return fig
