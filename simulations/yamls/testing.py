import json, sys, argparse, yaml, os
import pandas as pd
def load_ymal(file_name):
    file_name = os.path.abspath(file_name)
    with open(file_name, 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            return None

pricing_ymal = {}

for file_name in ["pricing/aws.yml", "pricing/gcp.yml"]:
    yml = load_ymal(file_name)
    pricing_ymal[yml["name"]] = yml
ymals = {
    "app": load_ymal("application_ymals/bookinfo_api_istio.yml"),
    "latency": load_ymal("latency/full_matrix.yml"),
    "pricing": pricing_ymal
}

pd.io.json.json_normalize(ymals["latency"], 'reviews', 'doc')
