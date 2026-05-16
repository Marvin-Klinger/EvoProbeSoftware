import os
import sys

from src.DataHub import DataHub
from src.GuiMain import GuiMain
import src.FileHandler as FileHandler
from src.ExtraClasses import MeasurementDeviceType as mdType
from LakeshoreDevice import LakeshoreDevice, Model372
from LakeshoreChannel import LakeshoreChannel
from MPVWrapper import MPVWrapper

from PyQt5 import QtWidgets as qtw


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
        slots = FileHandler.get_setup_json().get("slots", [])
        for slot in slots:
            if slot is None:
                continue

            print(slot)
            match slot.get("type", None):
                case mdType.LAKESHORE:
                    lhc = LakeshoreChannel(slot)
                    devices.append(lhc)
                case mdType.MPV:
                    mpv = MPVWrapper(slot)
                    devices.append(mpv)
                case _:
                    pass
        self.devices = devices
        print("Devices:", self.devices)

        for device in self.devices:
            device.connect_async()

        for device in self.devices:
            device.start_reading()

    # starts the data reading and logging process and selected sequence
    def start_sequence(self, save_path):
        self.datahub = DataHub(self.devices, save_path, self)
        self.datahub.start_logging()

