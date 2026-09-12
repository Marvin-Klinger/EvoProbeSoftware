import os
import sys

from src.DataHub import DataHub
from src.GuiMain import GuiMain
import src.FileHandler as FileHandler
from src.ExtraClasses import MeasurementDeviceType as mdType
from LakeshoreDevice import LakeshoreDevice, Model372
from LakeshoreChannel import LakeshoreChannel
from MPVWrapper import MPVWrapper
from PPMS6000Channel import PPMS6000Channel
from DynacoolChannel import DynacoolChannel

from PyQt5 import QtWidgets as qtw
import threading


class Controller:

    def __init__(self):
        self.devices = []
        self.datahub = None

        app = qtw.QApplication(sys.argv)
        self.main_window = GuiMain(self)
        app.exec_()

    # instantiates measurement_devices from data in setup.json
    def instantiate_devices(self):
        devices = []
        setup_json = FileHandler.get_setup_json()
        slots = setup_json.get("slots", [])
        settings = {d["id"]: d for d in setup_json.get("devices", [])}
        for i, slot in enumerate(slots):
            if slot is None:
                continue

            print(slot)
            match slot.get("type", None):
                case mdType.LAKESHORE:
                    devices.append(LakeshoreChannel(slot, settings.get(slot["id"], None)))
                case mdType.DYNACOOL:
                    devices.append(DynacoolChannel(slot))
                case mdType.PPMS6000:
                    devices.append(PPMS6000Channel(slot))
                case _:
                    pass
        self.devices = devices
        print("Devices:", self.devices)

        for device in self.devices:
            device.connect_async()

        for device in self.devices:
            t = threading.Thread(target=device.start_reading, daemon=True)
            t.start()

    # starts the data reading and logging process and selected sequence
    def start_sequence(self, save_path):
        self.datahub = DataHub(self.devices, save_path, self)
        self.datahub.start_logging()

