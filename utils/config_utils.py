import json

def read_config(config_file):
    with open(config_file) as cf:
        configs = json.load(cf)

    return configs
