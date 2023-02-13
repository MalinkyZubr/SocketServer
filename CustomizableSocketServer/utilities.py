import json
import pickle
from typing import Callable


def pickle_file(data: object, path: str):
    data = data.pickle.dumps(data)
    with open(path, "wb") as f:
        f.write(data)

def unpickle_file(path: str):
    with open(path, "rb") as f:
        data = f.read()
        return pickle.loads(data)

def create_client_config(commands: dict[str:Callable], standard_rules:list[Callable]):
    pickle_file(commands, r".\commands.pickle")
    pickle_file(standard_rules, r".\standard_rules.pickle")
    template = {
        "commands":r".\commands.pickle",
        "standard_rules":r".\standard_rules.pickle",
        "executor":False,
        "background":False,
        "allowed_file_types":[],
        "server_ip":"127.0.0.1",
        "port":8000,
        "buffer_size":4096,
        "log_dir":"."
        }
    template = json.dumps(template.encode())
    with open(r".\config.json", 'w') as f:
        f.write(template)

    print("Config files generated at config.json, commands.pickle, and standard_rules.pickle")

def load_config_file(path: str):
    with open(path, 'r') as f:
        return json.loads(f.read())

def extract_config_pickles(commands_path: str, standard_path: str):
    commands, standard_rules = unpickle_file(commands_path), unpickle_file(standard_path)
    return commands, standard_rules
    

