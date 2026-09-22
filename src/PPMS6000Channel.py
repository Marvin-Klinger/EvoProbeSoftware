from enum import Enum
from threading import Thread
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5.QtCore import Qt

import DefaultSettings as ds
from ExtraClasses import MeasurementDeviceType as mdType
from ExtraClasses import DeviceInfo
from src.MPVWrapper import MPVWrapper
from src.MeasurementDevice import MeasurementDevice


class PPMS6000Channel(MeasurementDevice):

    KEYS = ["current", "resistance"]
    CALIBRATION_MAPPING = {"resistance": "temperature"}

    def __init__(self, data, settings=None):
        super().__init__(data, settings)
        self.bridge_channel = data["channel"]
        self.mpv_wrapper = MPVWrapper.get_device()

        self.last_values = {}
        self.info = DeviceInfo(name=f"{data.get('name', 'PPMS')} Ch_{self.bridge_channel}", version=0)
        self.keys = PPMS6000Channel.KEYS + (["temperature"] if self.calibration is not None else [])
        self.logging_keys = [f"{key[:3]}_{self.bridge_channel}" for key in self.keys]
        self.plotting_keys = [f"{key[:3]}_{self.bridge_channel}" for key in self.keys]
        self.calibration_mapping = PPMS6000Channel.CALIBRATION_MAPPING

    # gets raw readings from device and applies calibration if necessary
    def get_readings(self):
        readings = self.mpv_wrapper.get_channel_reading(self.bridge_channel)
        return {"current": readings.current_uA,
                "resistance": readings.resistance_ohm}

    # configures physical device
    def configure(self, settings):
        pass

    # establishes connection to the physical device
    def connect(self):
        self.mpv_wrapper.connect()
        self.connected = self.mpv_wrapper.connected

    # starts routines necessary for measuring data
    def start_reading(self):
        pass

    # stops routines necessary for measuring data
    def stop_reading(self):
        pass
