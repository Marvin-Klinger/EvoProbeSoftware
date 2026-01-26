import json
import os

SETUP_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "persistent", "setup.json"))


def get_json(path):
    if not os.path.exists(path):
        return {}

    with open(path, "r") as file:
        try:
            s = "".join(file.readlines())
            return json.loads(s)
        except:
            return {}


def save_json(path, data):
    directory = os.path.abspath(os.path.join(path, ".."))
    if not os.path.exists(path):
        os.mkdir(directory)

    with open(path, "w") as file:
        s = json.dumps(data, indent=4)
        file.write(s)


def get_setup_json():
    data = get_json(SETUP_PATH)
    if "devices" in data:
        return data
    else:
        return {"devices": []}


def save_setup_json(data):
    save_json(SETUP_PATH, data)
