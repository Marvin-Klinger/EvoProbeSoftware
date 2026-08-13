from enum import Enum
from threading import Thread
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5.QtCore import Qt

import DefaultSettings as ds
from ExtraClasses import MeasurementDeviceType as mdType
from src.MeasurementDevice import MeasurementDevice
from Dynacool import Dynacool


class DynacoolChannel(MeasurementDevice):
    LOGGING_KEYS = ["current", "resistance"]

    def __init__(self, data):
        super().__init__(data)
        self.bridge_channel = data["channel"]
        self.dynacool = Dynacool.get_device(data.get("id", 0))

        self.last_values = {}
        self.info = None
        self.calibration = None
        self.keys = ["current", "resistance"]
        self.logging_keys = [f"{key[:3]}_{self.bridge_channel}" for key in self.keys]
        self.plotting_keys = [f"{key[:3]}_{self.bridge_channel}" for key in self.keys]
        self.connected = False

    # gets raw readings from device and applies calibration if necessary
    def get_readings(self):
        return self.dynacool.get_readings(self.bridge_channel)

    # establishes connection to the physical device
    def connect(self):
        self.dynacool.connect()
        self.connected = self.dynacool.connected

    # starts routines necessary for measuring data
    def start_reading(self):
        pass

    # stops routines necessary for measuring data
    def stop_reading(self):
        pass
