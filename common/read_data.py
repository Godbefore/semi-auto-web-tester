import yaml

def read_yaml(yaml_path):
    with open(yaml_path, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
        return config
