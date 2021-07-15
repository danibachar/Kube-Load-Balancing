import pandas as pd
import plotly.graph_objects as go
import dash_table

def service_capacity_table(app_option):
    df = pd.read_csv("~/Documents/IDC/Kube-Load-Balancing/app/kubernetes_servcice_selection/dataframes/capacity/capacity_{}.csv".format(app_option), index_col=False)
    cells_values = [list(df[col]) for col in df.columns]
    header_values = [col.replace("-", " ") for col in df.columns]
    fig = go.Figure(data=[go.Table(
        header=dict(values=header_values,
                    fill_color='darkgray',
                    font=dict(color='white', size=12),
                    align='left'),
        cells=dict(values=cells_values,
                   fill_color='gray',
                   font=dict(color='white', size=12),
                   align='left',),
        )
    ])
    return fig
