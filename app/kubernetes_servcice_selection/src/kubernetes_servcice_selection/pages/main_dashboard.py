from collections import Counter
from textwrap import dedent

import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, State, Output

import math, random

from ..app import app
from ..utils import get_balancing_options, get_app_options, get_df
from ..graphs.app_dag import simple_app_dag
from ..graphs.heatmaps import app_pricing_heat_map, app_latency_heat_map
from ..graphs.maps import clusters_map, services_map
from ..graphs.capacity import service_capacity_table

# Colors
bgcolor = "#f3f3f1"  # mapbox light map land color
bar_bgcolor = "#b0bec5"  # material blue-gray 200
bar_unselected_color = "#78909c"  # material blue-gray 400
bar_color = "#546e7a"  # material blue-gray 600
bar_selected_color = "#37474f"  # material blue-gray 800
bar_unselected_opacity = 0.8


# Figure template
row_heights = [150, 500, 300]
template = {"layout": {"paper_bgcolor": bgcolor, "plot_bgcolor": bgcolor}}


def blank_fig():
    """
    Build blank figure with the requested height
    """
    return {
        "data": [],
        "layout": {
            "template": template,
            "xaxis": {"visible": False},
            "yaxis": {"visible": False},
        },
    }

def get_layout(**kwargs):
    return html.Div(
        [
            dcc.Markdown(
                dedent(
                    """
                    # App Dashboard
                    """
                )
            ),
            html.Div(
                children=[
                    html.H4(
                        [ "Select an app",],
                        className="app-selection-title",
                    ),
                    dcc.Dropdown(
                        id="app-option",
                        options=[{
                            'label': i,
                            'value': i
                        } for i in get_app_options()],
                        value=get_app_options()[0]
                    ),
                ]
            ),
            html.Div(
                children=[
                    html.Div(
                        children=[
                            html.H4(
                                ["App Dependency Graph",],
                                className="price-heatmap-title",
                            ),
                            dcc.Graph(
                                id="app-dag",
                                figure=blank_fig(),
                                # config={"displayModeBar": False},
                            )
                        ],
                        style={'width': '49%', 'height': '100%', 'display': 'inline', 'text-align': 'center'},
                    ),
                    html.Div(
                        children=[
                            html.Div(
                                children=[
                                dcc.Loading(
                                    id = "loading-icon",
                                    type="circle",
                                    children=[
                                    html.Div(
                                        children=[
                                            html.Div(
                                                "Cost Saving:  ",
                                                style={'color': 'black', 'margin-right': 30,'fontSize': 36, 'text-align': 'justify'},
                                            ),
                                            html.Div(
                                                id="price-calc",
                                                style={'color': 'black', 'fontSize': 36, 'text-align': 'justify'},
                                            ),
                                        ],
                                        style={'flex-direction': 'row', 'display' : 'flex'},
                                    ),
                                ]),
                                dcc.Loading(
                                    id = "loading-icon",
                                    type="circle",
                                    children=[
                                    html.Div(
                                        children=[
                                            html.Div(
                                                "Latency reduction:  ",
                                                style={'color': 'black', 'fontSize': 36, 'text-align': 'justify'},
                                            ),
                                            html.Div(
                                                id="latency-calc",
                                                style={'color': 'black', 'fontSize': 36, 'text-align': 'justify'},
                                            ),
                                        ],
                                        style={'flex-direction': 'row', 'display' : 'flex'},
                                    ),
                                ]),

                                ],
                            ),
                        ],
                        style={'width': '100%', 'height': '100%','display': 'inline', 'text-align': 'center'},
                    ),
                ]
            ),
            html.Div(
                children=[
                    html.H4(
                        ["Clusters Locations",],
                        className="clusters-location-title",
                    ),
                    dcc.Loading(
                        id = "loading-icon",
                        type="circle",
                        children=[
                            dcc.Graph(
                                id="clusters-map",
                                figure=blank_fig(),
                                # config={"displayModeBar": False},
                            ),
                    ]),
                ],
                className="twelve columns pretty_container",
            ),
            # Heat Maps
            html.Div(
                children=[
                    html.Div(
                        children=[
                            html.H4(
                                ["Latency in ms",],
                                className="latency-heatmap-title",
                            ),
                            dcc.Graph(
                                id="latency-heatmap",
                                figure=blank_fig(),
                                # config={"displayModeBar": False},
                            )
                        ],
                        style={'width': '49%', 'display': 'inline-block'},
                    ),
                    html.Div(
                        children=[
                            html.H4(
                                ["Price per GB outbound in USD($)",],
                                className="price-heatmap-title",
                            ),
                            dcc.Graph(
                                id="price-heatmap",
                                figure=blank_fig(),
                                # config={"displayModeBar": False},
                            )
                        ],
                        style={'width': '49%', 'display': 'inline-block'},
                    ),

                ]
            ),
            # Capacity
            html.Div(
                children=[
                    html.H4(
                        [ "Service capacity per cluster (RPS)",],
                        className="app-balance-selection-title",
                    ),
                    dcc.Loading(
                        id = "loading-icon",
                        type="circle",
                        children=[
                            dcc.Graph(
                                id="capacity-table",
                                figure=blank_fig(),
                                # config={"displayModeBar": False},
                            ),
                    ]),
                ]
            ),
            html.Div(
                children=[
                    html.H4(
                        [ "Select balancing option",],
                        className="app-balance-selection-title",
                    ),
                    dcc.Dropdown(
                        id="balance-option",
                        options=[{
                            'label': i,
                            'value': i
                        } for i in get_balancing_options()] ,
                        value="Combined"
                    ),
                ]
            ),
            html.Div(
                className="services-map",
                children=[
                    html.H4(
                        ["Services Map",],
                        className="service-map-title",
                    ),
                    dcc.Loading(
                        id = "loading-icon",
                        type="circle",
                        children=[
                            dcc.Graph(
                                id="service-map",
                                figure=blank_fig(),
                                # config={"displayModeBar": False},
                            ),
                    ]),
                ],
            ),
        ]
    )

@app.callback(
    Output("clusters-map", "figure"),
    [
        Input("app-option", "value"),
    ])
def clusters_map_callback(app_option):
    return clusters_map(app_option)

@app.callback(
    Output('app-dag', 'figure'),
    [
        Input("balance-option", "value"),
        Input("app-option", "value"),
    ])
def simple_app_dag_callback(balance_option, app_option):
    return simple_app_dag(app_option)

@app.callback(
    Output('service-map', 'figure'),
    [
        Input("balance-option", "value"),
        Input("app-option", "value"),
    ])
def services_map_callback(balance_option, app_option):
    return services_map(app_option, balance_option)

@app.callback(
    Output('price-heatmap', 'figure'),
    [
        Input("app-option", "value"),
    ])
def app_pricing_heat_map_callback(app_option):
    return app_pricing_heat_map(app_option)

@app.callback(
    Output('latency-heatmap', 'figure'),
    [
        Input("app-option", "value"),
    ])
def lapp_latency_heat_map_callback(app_option):
    return app_latency_heat_map(app_option)

@app.callback(
    Output('capacity-table', 'figure'),
    [
        Input("app-option", "value"),
    ])
def service_capacity_table_callback(app_option):
    return service_capacity_table(app_option)

@app.callback(
    Output('latency-calc', component_property='children'),
    [
        Input("app-option", "value"),
    ])
def latency_saving_calc(app_option):
    return min_max_by("latency", app_option)

@app.callback(
    Output('price-calc', component_property='children'),
    [
        Input("app-option", "value"),
    ])
def cost_saving_calc(app_option):
    return min_max_by("gb_price", app_option)

def min_max_by(col, app_option):
    df = get_df(app_name=app_option)

    max_vals = []
    min_vals = []

    for b_group in df.groupby(["load_balance"]):
        max_val = -math.inf
        min_val = math.inf

        for cm_group in b_group[1].groupby(["cost_mix"]):
            mean_val = cm_group[1][col].mean()
            max_val = max(max_val, mean_val)
            min_val = min(min_val, mean_val)

        max_vals.append(max_val)
        min_vals.append(min_val)

    return "  %{:.2f}".format((1 - min(min_vals)/max(max_vals)) * 100)
