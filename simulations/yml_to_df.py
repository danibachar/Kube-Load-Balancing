import argparse

import pandas as pd

from config_builder import build_config
from utils.helpers import load_ymal

def app_dep_graph(yml):
    nodes = []
    source = []
    target = []
    print(yml)
    for svc_name, service in yml["services"].items():
        print(service)
        nodes.append(svc_name)
        for dep in service["dependencies"].values():
            source.append(svc_name)
            target.append(dep["name"])

    edges = pd.DataFrame({'source': source,
                          'target': target, })
    return edges

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run Kuberentes simulation')
    parser.add_argument(
        '--config_file_name',
        type=str,
        default="yamls/configurations/simple_run.yml",
        help='A configuration file that describe the test'
    )

    args = parser.parse_args()
    config_file_name = args.config_file_name
    config = build_config(config_file_name)
    apps = config["simulation_ymals"]["apps"]
    for app_file in apps:
        app_name = app_file.split("/")[-1].split(".")[0]
        yml = load_ymal(app_file)
        graph = app_dep_graph(yml)
        graph.to_csv("{}.csv".format(app_name))
