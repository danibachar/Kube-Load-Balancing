import pandas as pd
import numpy as np
import plotly.graph_objs as go
import plotly.express as px

def percentile(n):
    def percentile_(x):
        return np.percentile(x, n)
    percentile_.__name__ = 'percentile_%s' % n
    return percentile_


def price_vs_latency(df):
        values_cols = ["latency", "gb_price", ] #"load"
        index_cols = ["load_balance", ] # "job_type","cost_mix"
        special_cols = ["cost_mix"]
        cols_of_interest = values_cols + index_cols + special_cols + [ "job_type"] #
        df = df[cols_of_interest] #
        df[values_cols] = df[values_cols].apply(pd.to_numeric)

        x_name = "gb_price"
        y_name = "latency"
        lines_name = "load_balance"
        points = "cost_mix"
        aggregation = ["mean", "max", "min", percentile(75), percentile(25)]
        # [np.mean, min, max]


        group_df = df.groupby([lines_name, points, ])

        agg_df = group_df \
            .aggregate({x_name: aggregation, y_name: aggregation }) \
            .reset_index()
            # .drop_duplicates(subset = [x_name, y_name]) # To avoid problematic labeling (when x and y have the same value for different cost_mix)
        x_name_mean = x_name+"_mean"
        y_name_mean = y_name+"_mean"
        new_cols = []

        for col in agg_df.columns.values:
            if len(col[1]) > 0:
                new_cols.append('_'.join(col))
            else:
                new_cols.append(col[0])
        agg_df.columns = new_cols

        # agg_df = agg_df.drop_duplicates(subset = [lines_name, x_name_mean, y_name_mean]) # To avoid problematic labeling (when x and y have the same value for different cost_mix)
        agg_df = _clear_non_monotonic_cost_mix(agg_df) \
            .drop_duplicates(subset = [lines_name, x_name_mean, y_name_mean])

        x = np.array(agg_df[x_name_mean].tolist())
        max_x = np.max(x)
        min_x = np.min(x)
        x_ratio = min_x/max_x

        y = np.array(agg_df[y_name_mean].tolist())
        max_y = np.max(y)
        min_y = np.min(y)
        y_ratio = min_y/max_y
        if y_ratio > x_ratio:
            max_y = 1/x_ratio * min_y
        else:
            max_x = 1/y_ratio * min_x

        fig = px.scatter(
            agg_df,
            x=x_name_mean,
            y=y_name_mean,
            color=lines_name,
            text=points,
        )
        fig.update_traces(
            mode="markers+lines+text",
            textposition='top right',
            textfont_size=10,
        )

        x_title = "Mean price per GB ($)"
        y_title = "Mean latency (ms)"

        fig.update_xaxes(title_text = x_title, range=[min_x, max_x])
        fig.update_yaxes(title_text = y_title,range=[min_y, max_y])
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            width=600, height=600,
        )
        return fig

def app_latecy_to_price_graph(app_option=None):
    df_lat = pd.read_csv("~/Documents/Kube-Load-Balancing/app/kubernetes_service_selection/dataframes/heatmaps/latency_{}.csv".format(app_option), index_col=False)
    df_price = pd.read_csv("~/Documents/Kube-Load-Balancing/app/kubernetes_service_selection/dataframes/heatmaps/price_{}.csv".format(app_option), index_col=False)

    # DataSource validations
    zone_names_price = list(df_price.columns.values.tolist())
    zone_names_latency = list(df_lat.columns.values.tolist())
    if zone_names_price != zone_names_latency:
        raise Exception("zone_names_price{} != zone_names_latency{}".format(zone_names_price, zone_names_latency))
    zone_names = zone_names_price

    price_matrix = np.array(df_price.values.tolist())
    latency_matrix = np.array(df_lat.values.tolist())

    zones_count = len(zone_names)
    total_figure_height = 450 * zones_count

    specs = [[{"secondary_y": True}] for _ in range(zones_count)]
    titles = ["source="+name for name in zone_names]
    fig = make_subplots(rows=zones_count, cols=1, specs=specs, subplot_titles=titles)
    fig.update_layout(height=total_figure_height, showlegend=False)

    for zone_idx, zone_name in enumerate(zone_names):
        zone_to_others_prices = price_matrix[zone_idx]
        zone_to_others_latencies = latency_matrix[zone_idx]

        norm_prices = zone_to_others_prices / max(zone_to_others_prices) * 0.5
        norm_latencies = zone_to_others_latencies / max(zone_to_others_latencies) * 0.5

        # TODO decide on axis and sort by, lets say price - from low to high
        # 0 = price, 1 = latency
        norm_zipped_sorted = list(
            sorted(
                zip(norm_prices, norm_latencies, zone_names),
                key = lambda x: x[0]
            )
        )
        norm_prices_sorted =  list(map(lambda x: x[0], norm_zipped_sorted))
        norm_latencies_sorted = list(map(lambda x: x[1], norm_zipped_sorted))
        zone_names_sorted = list(map(lambda x: x[2], norm_zipped_sorted))
        fig.add_trace(
            go.Scatter(x=zone_names_sorted,
                       y=norm_prices_sorted,
                       mode='lines+markers+text',
                       name='price',
                       marker_color='rgba(0, 0, 255, 1)'),
            secondary_y=False,
            row=1+zone_idx,
            col=1)
        fig.add_trace(
            go.Scatter(x=zone_names_sorted,
                       y=norm_latencies_sorted,
                       mode='lines+markers+text',
                       name='latency',
                       marker_color='rgba(255, 0, 0, 1)' ),
            secondary_y=True,
            row=1+zone_idx,
            col=1)
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
    return fig

def _data_from(df):
    return go.Scatter(
                x=bin_edges,
                y=cdf,
                name=name,
                mode="lines+markers",
                showlegend=True,
            )

def _clear_non_monotonic_cost_mix(df):
    dfs = []
    for lb_name, lb_df in df.groupby(["load_balance"]):
        price_means = []
        latency_means = []

        for cost_name, cost_df in lb_df.groupby(["cost_mix"]):

            price_mean = cost_df["gb_price_mean"].mean()
            if len(price_means) > 0 and price_means[-1] < price_mean: # mon up
                continue
            latency_mean = cost_df["latency_mean"].mean()
            if len(latency_means) > 0 and latency_means[-1] > latency_mean: # mon down
                continue
            price_means.append(price_mean)
            latency_means.append(latency_mean)
            dfs.append(cost_df)

    return pd.concat(dfs)
