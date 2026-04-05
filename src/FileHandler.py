import json
import os

SETUP_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "persistent", "setup.json"))
USER_DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "persistent", "user_data.json"))
PUCK_DIR_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "persistent", "pucks"))
ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


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


def get_user_data_json():
    data = get_json(SETUP_PATH)
    if len(data):
        return data
    else:
        return {"save_path": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "out.csv"))}


def save_user_data_json(data):
    save_json(SETUP_PATH, data)


def get_pucks():
    files = [file for file in os.listdir(PUCK_DIR_PATH) if file.endswith(".json")]
    pucks = [get_json(os.path.join(PUCK_DIR_PATH, file)) for file in files]
    return pucks


def setup_folder_structure():
    if not os.path.exists(os.path.join(ROOT_PATH, "persistent")):
        os.mkdir(os.path.join(ROOT_PATH, "persistent"))
    if not os.path.exists(os.path.join(ROOT_PATH, "persistent", "pucks")):
        os.mkdir(os.path.join(ROOT_PATH, "persistent", "pucks"))
    if not os.path.exists(os.path.join(ROOT_PATH, "persistent", "rods")):
        os.mkdir(os.path.join(ROOT_PATH, "persistent", "rods"))
    if not os.path.exists(os.path.join(ROOT_PATH, "data")):
        os.mkdir(os.path.join(ROOT_PATH, "data"))
