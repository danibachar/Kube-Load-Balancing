import yaml, os

def load_ymal(file_name):
    file_name = os.path.abspath(file_name)
    with open(file_name, 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            return None