from utils.helpers import load_ymal

def _build_simulation_ymals(simulation_ymals_config):
    pricing_ymal_list = simulation_ymals_config["pricing"]
    app_ymal_list = simulation_ymals_config["apps"]
    latency_ymal = simulation_ymals_config["latency"]
    datacenters_yml = simulation_ymals_config["datacenters_locations"]

    pricing_ymal = {}
    for file_name in pricing_ymal_list:
        yml = load_ymal(file_name)
        pricing_ymal[yml["name"]] = yml

    app_ymal = {}
    for file_name in app_ymal_list:
        yml = load_ymal(file_name)
        app_ymal[file_name] = yml

    ymals = {
        "apps": app_ymal,
        "latency": load_ymal(latency_ymal),
        "pricing": pricing_ymal,
        "datacenters_locations": load_ymal(datacenters_yml)
    }
    return ymals

def build_config(config_file_name):

    main_config_ymal = load_ymal(config_file_name)

    simulation_ymals_config = main_config_ymal["simulation_ymals"]

    config = main_config_ymal["base_config"]
    config["simulation_ymals"] = _build_simulation_ymals(simulation_ymals_config)

    return config
