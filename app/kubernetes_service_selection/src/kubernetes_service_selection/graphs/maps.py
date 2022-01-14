import pandas as pd
import numpy as np
import random

import plotly.graph_objs as go
import plotly.express as px
import networkx as nx


from ..utils import get_df, center_geolocation, random_color

def _map_zones(zone_full_name):
    components = zone_full_name.split("-")
    cloud_provider, region = components[0], components[1:].join("-")
    return cloud_provider, region

def clusters_map(app_option):
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

    center_point = center_geolocation(list(zip(lats, lons)))
    mapin = pd.DataFrame(data={"lat":lats,"lon":lons, "color":colors, "tag":tags, "size":sizes})
    fig = px.scatter_mapbox(
        mapin,
        lat='lat',
        lon='lon',
        color='color',#"cloud_provider", # 'color', # 'cloud_provider'
        zoom=0.5,
        size='size',#[30 for _ in range(len(df["lon"].index))],
        center=dict(lat=center_point[0], lon=center_point[1]),
        hover_data=['tag',], # "source_zone_id","target_zone_id"
        mapbox_style="carto-positron"
    )
    return fig


def services_map(app_option, balance_option):
    df = get_df(app_name=app_option, balance_name=balance_option)

    groups = [ "source_zone_id","target_zone_id", "job_type","source_job_type"]
    group_df = df.groupby(groups)
    edges = group_df.agg({  "load":sum,
                            "latency":np.mean,
                            "gb_price":np.mean,
                            "capacity":np.mean, }).reset_index()
    #
    edges["source"] = edges["source_zone_id"] + "__"+  edges["source_job_type"]
    edges["target"] = edges["target_zone_id"] + "__"+  edges["job_type"]

    G = nx.from_pandas_edgelist(edges, edge_attr=None, create_using=nx.DiGraph())
    # sources = [node for node in G.nodes() if G.in_degree(node) == 0]
    # for src in sources:
    #     name = "CLIENT__{}".format(src)
    #     G.add_node(name)
    #     print(name)
    #     G.add_edge(*(name,src))

    nodeColor = 'Blue'
    nodeSize = 15
    lineWidth = 1
    lineColor = 'black'##000000'

    # Make list of nodes for plotly
    node_x = []
    node_y = []
    node_names = []
    index = 0
    color_map = {"CLIENT": random_color()}
    node_colors = []
    for job_type in df["job_type"].unique():
        color_map[job_type] = random_color()

            # Services
    def svc_divertion(df):
        pos = [0,0.1,-0.1,0.2,-0.2,0.3,-0.3,0.5,-0.5,0.6,-0.6,0.7,-0.7] # ,0.8,-0.8,0.9,-0.9, 2, -2, 2.3, -2.3

        lat = list(df["lat"].unique())[0]
        lat = lat + random.choice(pos)
        lon = list(df["lon"].unique())[0]
        lon = lon + random.choice(pos)

        return lat, lon
        # for group in df.groupby(["cluster_name", "job_type"]):
        #     group_name = group[0]
        #     # print(group_name)
        #     group_df = group[1]
        #     lat, lon = svc_divertion(group_df)
        #     lats.append(lat)
        #     lons.append(lon)
        #     colors.append(list(group_df["job_type"].unique())[0])
        #     tags.append(group_name[0])
        #     sizes.append(5)
    cache = {}
    for node in G.nodes():
        target_zone_id, job_type = node.split("__")[0], node.split("__")[1]
        # print("target_zone_id",target_zone_id)
        if target_zone_id == "CLIENT" and job_type == "CLIENT":
            if node not in cache:
                cache[node] = svc_divertion(df)
            lat, lon = cache[node]
        else:
            query = (df["job_type"] == job_type) & (df["target_zone_id"] == target_zone_id)
            _df = df[query]
            # print(_df["lat"].unique())
            # print(_df["lon"].unique())

            if node not in cache:
                cache[node] = svc_divertion(_df)
            lat, lon = cache[node]
            # lat, lon = svc_divertion(_df)
            # print("lat",lat)
            # print("lon",lon)

        node_names.append(node)
        node_x.append(lon)
        node_y.append(lat)
        node_colors.append(color_map[job_type])
    # Make a list of edges for plotly, including line segments that result in arrowheads
    lats = []
    lons = []
    line_width = []
    edge_colors = []
    w_cache = {}
    for edge in G.edges():
        source = edge[0]
        target = edge[1]
        if source not in w_cache:
            w_cache[source] = random_color()
        # if target not in w_cache[source]:
        #     w_cache[source][target] = random_color()
        edge_colors.append(w_cache[source])
        load_q = (edges["source"] == source) & (edges["target"] == target)
        load = list(edges[load_q]["load"].unique())[0]
        x1, y1 = cache[source]
        x2, y2 = cache[target]
        # Append line corresponding to the edge
        lats.append(x1)
        lats.append(x2)
        lats.append(None) # Prevents a line being drawn from end of this edge to start of next edge
        lons.append(y1)
        lons.append(y2)
        lons.append(None)
        # edge_x, edge_y = addEdge([x1, y1], [x2, y2], edge_x, edge_y, .8, 'end', .04, 30, nodeSize)

        # edge_x.append([x1,x2,None])
        # edge_y.append([y1,y2,None])
        # print("edge_x",edge_x)
        # print("edge_y",edge_y)
        # start = pos[edge[0]]
        # end = pos[edge[1]]
        # edge_x, edge_y = addEdge(start, end, edge_x, edge_y, .8, 'end', .04, 30, nodeSize)


    edge_trace = go.Scattergeo(
        lon=lons, lat=lats,
        line=dict(width=lineWidth, color=lineColor),
        hoverinfo='none', mode='lines')


    node_trace = go.Scattergeo(
        lon=node_x, lat=node_y,
        mode='markers',
        text=node_names,
        marker=dict(showscale=False, color = node_colors, size=nodeSize))


    # pr = list(filter(lambda xy: xy[0] != None and xy[1] != None, zip(edge_x, edge_y)))
    # print(pr)
    fig = go.Figure(data=[node_trace, edge_trace],# edge_trace
                 layout=go.Layout(
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20,l=5,r=5,t=40),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    # annotations=[
                    #     dict(
                    #         ax=(edge[0][0] + edge[1][0]) / 2,
                    #         ay=(edge[0][1] + edge[1][1]) / 2, axref='x', ayref='y',
                    #         x=(edge[1][0] * 3 + edge[0][0]) / 4,
                    #         y=(edge[1][1] * 3 + edge[0][1]) / 4, xref='x', yref='y',
                    #         showarrow=True,
                    #         arrowhead=3,
                    #         arrowsize=4,
                    #         arrowwidth=1,
                    #         opacity=1
                        # ) for edge in pr]
                    ))
    #
    # # Note: if you don't use fixed ratio axes, the arrows won't be symmetrical
    # fig.update_layout(yaxis = dict(scaleanchor = "x", scaleratio = 1), plot_bgcolor='rgb(255,255,255)')

    return fig
