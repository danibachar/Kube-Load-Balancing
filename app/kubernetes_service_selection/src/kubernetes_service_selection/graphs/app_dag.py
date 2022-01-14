from dash import dcc, html

import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout
import plotly.graph_objs as go
import pandas as pd
# from colour import Color
from datetime import datetime
from textwrap import dedent as d
import json
import numpy as np

from ..utils import get_df, random_color, get_dag_df

def simple_app_dag(app_option):
    # df = pd.read_csv("~/Documents/IDC/Kube-Load-Balancing/app/kubernetes_servcice_selection/dataframes/app_dag/{}.csv".format(app_option))
    df = get_dag_df(app_option)
    G = nx.from_pandas_edgelist(df,edge_attr=None, create_using=nx.DiGraph())
    # Add client node + edges to each 0 degree in Service
    sources = [node for node in G.nodes() if G.in_degree(node) == 0]

    pathes = {}
    for src in sources:
        pathes = {**pathes, **nx.shortest_path_length(G,src)}
    pos = graphviz_layout(G,prog='dot')
    for name, p in pos.items():
        depth_len = pathes[name] * 150
        pos[name] = (p[0]+150, p[1]+depth_len)
    lineWidth = 1
    lineColor = '#000000'
    # Make list of nodes for plotly
    node_x = []
    node_y = []
    node_names = []
    node_colors = [random_color() for node in G.nodes()]
    node_sizes = [ 100 for node in G.nodes()]
    for node in G.nodes():
        x, y = pos[node]
        node_names.append(node)
        node_x.append(x)
        node_y.append(y)
    # Make a list of edges for plotly, including line segments that result in arrowheads
    edge_x = []
    edge_y = []
    for edge in G.edges():
        start = pos[edge[0]]
        end = pos[edge[1]]
        # Append line corresponding to the edge
        edge_x.append(start[0])
        edge_x.append(end[0])
        edge_x.append(None) # Prevents a line being drawn from end of this edge to start of next edge
        edge_y.append(start[1])
        edge_y.append(end[1])
        edge_y.append(None)

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=lineWidth, color=lineColor),
        hoverinfo='none', mode='lines',
    )
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text', hoverinfo='text',
        text=node_names,
        marker=dict(showscale=False, color = node_colors, size=node_sizes),
    )

    fig = go.Figure(data=[edge_trace, node_trace],
                 layout=go.Layout(
                    width=500,
                    height=1000,
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20,l=5,r=5,t=40),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    annotations=[
                        dict(
                            ax=(pos[edge[0]][0] + pos[edge[1]][0]) / 2,
                            ay=(pos[edge[0]][1] + pos[edge[1]][1]) / 2, axref='x', ayref='y',
                            x=(pos[edge[1]][0] * 3 + pos[edge[0]][0]) / 4,
                            y=(pos[edge[1]][1] * 3 + pos[edge[0]][1]) / 4, xref='x', yref='y',
                            showarrow=True,
                            arrowhead=3,
                            arrowsize=4,
                            arrowwidth=1,
                            opacity=1
                        ) for edge in G.edges]
                    ))

    # Note: if you don't use fixed ratio axes, the arrows won't be symmetrical
    fig.update_layout(yaxis = dict(scaleanchor = "x", scaleratio = 1), plot_bgcolor='rgb(255,255,255)')
    return fig
