import pandas as pd
import numpy as np
import plotly.graph_objs as go
import random

def cdf_by_weights_comparison(
    dfs,
    name_prefixes,
    fig_title,
    xaxis_title,
    yaxis_title,
    col,
    skip_on_mean=True
):
    markers = ['circle', 'square', 'diamond', 'triangle-up', 'triangle-down', 'pentagon', 'hexagon', 'octagon', 'star', 'hexagram', 'star-square',]
    data = []
    cost_mix_col = "cost_mix"
    if len(name_prefixes) != len(dfs):
        name_prefixes = ["" for _ in dfs]

    count = 0
    for prefix, df in zip(name_prefixes,dfs):
        means = []
        for group in df.groupby([cost_mix_col]):
            cost_mix_name = group[0]
            _df = group[1][col]
            mean = _df.mean()
            name = prefix+"-"+cost_mix_name
            if skip_on_mean:
                if mean in means:
                    continue
                if col == "gb_price": # make sure we monotonic up
                    if len(means) > 0 and means[-1] < mean:
                        continue
                if col == "latency": # make sure we monotonic down
                    if len(means) > 0 and means[-1] > mean:
                        continue
            elif prefix == "rr":
                print("hit")
                name = "rr"
            means.append(mean)

            data.append(
                _get_cdf_scatter(
                    col, group[1], name, marker=markers[count]
                )
            )
            count+=1

    fig = go.Figure(data=data,
                    layout=go.Layout(font=dict(size=18, ),title=fig_title, autosize=False,width=600))

    fig.update_xaxes(title_text=xaxis_title, rangemode="tozero")
    fig.update_yaxes(title_text=yaxis_title, rangemode="tozero")
    return fig

def _get_cdf_scatter(col_name, df, name, marker='circle'):
    hist, bin_edges = np.histogram(
        df[col_name],
        bins=df[col_name].nunique(),
        density=True
    )
    cdf = np.cumsum(hist * np.diff(bin_edges))
    return go.Scatter(
                x=bin_edges,
                y=cdf,
                name=name,
                mode="lines+markers",
                line_width=2,
                marker_symbol=marker,
                marker_line_width=1,
                marker_size=6,
                showlegend=True,
            )
