from enum import Enum
from threading import Thread
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5.QtCore import Qt

import DefaultSettings as ds
from ExtraClasses import MeasurementDeviceType as mdType
from ExtraClasses import DeviceInfo
from src.MeasurementDevice import MeasurementDevice


class PPMS6000Channel(MeasurementDevice):

    def __init__(self, data):
        super().__init__(data)
        self.bridge_channel = data["channel"]

        self.last_values = {}
        self.info = DeviceInfo(name=f"{data.get('name', 'PPMS')} Ch_{self.bridge_channel}", version=0)
        self.calibration = None
        self.keys = ["current", "resistance"]
        self.logging_keys = [f"{key[:3]}_{self.bridge_channel}" for key in self.keys]
        self.plotting_keys = [f"{key[:3]}_{self.bridge_channel}" for key in self.keys]
        self.connected = False

    # gets raw readings from device and applies calibration if necessary
    def get_readings(self):
        return {key: 0 for key in self.keys}

    # configures physical device
    def configure(self, settings):
        pass

    # establishes connection to the physical device
    def connect(self):
        pass

    # connects to the devices asynchronously to not freeze the GUI
    def connect_async(self):
        t = Thread(target=self.connect, daemon=True)
        t.start()

    # starts routines necessary for measuring data
    def start_reading(self):
        pass

    # stops routines necessary for measuring data
    def stop_reading(self):
        pass
