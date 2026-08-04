import traceback

import MultiPyVu as mpv
import numpy as np
from enum import IntEnum

import threading

from lakeshore import Model372

from src.ExtraClasses import DeviceInfo
from src.MeasurementDevice import MeasurementDevice, DeviceCard
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5.QtCore import Qt
from ExtraClasses import MeasurementDeviceType as mdType
import DefaultSettings as ds


class MPVWrapper:
    device = None

    def __init__(self):
        self.server = None
        self.client = None
        self.lock = threading.Lock()

        self.last_values = {}
        self.info = DeviceInfo(name="MPV", version=0)
        self.calibration = None
        self.keys = ["temperature", "field"]
        self.logging_keys = ["temp", "field"]
        self.plotting_keys = ["temp", "field"]
        self.connected = False

        self.key_to_function = {"temperature": self.get_temperature,
                                "field": self.get_field}

    # gets raw readings from device and applies calibration if necessary
    def get_readings(self):
        readings = {}
        for key in self.key_to_function:
            readings[key] = self.key_to_function[key]()
        self.last_values = readings
        return readings

    # converts readings to data usable by DataHub
    def get_logging_readings(self):
        readings = self.get_readings()
        logging_readings = []
        for key in self.keys:
            logging_readings.append(readings[key])
        return logging_readings

    # configures physical device
    def configure(self, settings):
        pass

    # establishes connection to the physical device
    def connect(self):
        print("try connecting")
        self.lock.acquire(blocking=True)
        try:
            self.server = mpv.Server()
            self.client = mpv.Client()
            self.server.open()
            self.client.open()
        except:
            self.connected = False
            print("connection to mpv not possible")
            self.lock.release()
            return
        self.connected = True
        self.lock.release()

    def get_temperature(self):
        if not self.connected:
            return np.nan

        self.lock.acquire(blocking=True)
        value = np.nan
        try:
            value = self.client.get_temperature()[0]
        except Exception:
            # print(traceback.format_exc())
            print("couldn't read mpv temperature")
        self.lock.release()
        return value

    def get_field(self):
        if not self.connected:
            return np.nan

        self.lock.acquire(blocking=True)
        value = np.nan
        try:
            value = self.client.get_field()[0]
        except Exception:
            # print(traceback.format_exc())
            print("couldn't read mpv field")
        self.lock.release()
        return value

    def get_channel_reading(self, bridge_channel: int):
        value = {"current": np.nan, "resistance": np.nan}
        if not self.connected:
            return value

        self.lock.acquire(blocking=True)
        try:
            value["current"] = self.client.resistivity.get_current(bridge_channel)
            value["resistance"] = self.client.resistivity.get_resistance(bridge_channel)
        except:
            print("couldn't read bridge channel")
        self.lock.release()
        return value

    # handles shutting down the properties in this wrapper
    def shutdown(self):
        self.client.close_client()
        self.server.close()

    def set_ramp_rate(self, ramp_rate):
        self.lock.acquire()
        try:
            self.client.set_field(0, ramp_rate, mpv.Client.field.approach_mode.linear)
        except Exception:
            print("couldn't set ramprate")
            print(traceback.format_exc())
        self.lock.release()

    @staticmethod
    def get_device():
        if MPVWrapper.device is None:
            MPVWrapper.device = MPVWrapper()
        return MPVWrapper.device


class CalibrationMode(IntEnum):
    STANDARD = 0
    FAST = 1
    HI_RES = 2


class DriveMode(IntEnum):
    AC = 0
    DC = 1


class BridgeChannel(IntEnum):
    CHANNEL_1 = 1
    CHANNEL_2 = 2
    CHANNEL_3 = 3
    CHANNEL_4 = 4
