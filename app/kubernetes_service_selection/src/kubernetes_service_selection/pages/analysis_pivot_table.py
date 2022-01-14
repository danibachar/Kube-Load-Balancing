from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, State, Output

from textwrap import dedent
import pandas as pd
import numpy as np
import dash_pivottable

from ..utils import get_df, get_app_options
from ..app import app

def get_layout(**kwargs):
    print("pivot table")
    return html.Div(
        [
            dcc.Markdown(
                dedent(
                    """
                    # Analysis Pivot Table
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
            dcc.Loading(
                id = "loading-icon",
                type="circle",
                children=[html.Div(id="pivot-table"), ]
            ),
        ]
    )
@app.callback(
    Output('pivot-table', component_property='children'),
    [
        Input("app-option", "value"),
    ])
def pivot_table(app_option):
    df = get_df(app_option)

    p = pd.pivot_table(
        df,
        index=["load_balance","cost_mix", "job_type","cluster_name",],
        values=["latency","gb_price",],
        aggfunc={
                "latency": np.mean,
                "gb_price": np.mean,
                },
    )
    p = p.reset_index()
    vals = list(p.values.tolist())
    cols = list(p.columns)
    flat_p = vals
    flat_p.insert(0,cols)
    pivot = dash_pivottable.PivotTable(
                    data=flat_p,
                    cols=["load_balance"],
                    rows=["cost_mix"],
                    vals=["gb_price"]
                )
    return [html.Div([pivot])]
