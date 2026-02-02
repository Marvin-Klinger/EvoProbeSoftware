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
        lh_channels = []
        for slot in slots:
            data = slot.get("data", None)
            if not data:
                continue
            match data.get("device", None):
                case mdType.LAKESHORE.value:
                    lh_channels.append(data["channel"])
                case mdType.MPV.value:
                    mpv = MPVWrapper()
                    devices.append(mpv)
                case _:
                    pass
        if len(lh_channels) > 0:
            input_channels = [Model372.InputChannel(ch) for ch in lh_channels]
            device = LakeshoreDevice(input_channels)
            for ch in input_channels:
                channel = LakeshoreChannel(device, ch, None)
                devices.append(channel)
        self.devices = devices
        print(self.devices)

    # starts the data reading and logging process and selected sequence
    def start_sequence(self):
        save_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "out.csv"))
        self.datahub = DataHub(self.devices, save_path, self)
        self.datahub.start_logging()

