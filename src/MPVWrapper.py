import traceback

import MultiPyVu as mpv
import numpy as np

import threading

from src.MeasurementDevice import MeasurementDevice


class MPVWrapper(MeasurementDevice):

    def __init__(self):
        super().__init__()

        self.server = mpv.Server()
        self.client = mpv.Client()
        self.lock = threading.Lock()

        self.last_values = {}
        self.info = None
        self.calibration = None
        self.keys = ["temperature", "field"]
        self.logging_keys = ["temp", "field"]
        self.plotting_keys = ["temp", "field"]

        self.key_to_function = {"temperature": self.get_temperature,
                                "field": self.get_field}

        self.connect()

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
        self.server.open()
        self.client.open()

    def get_temperature(self):
        self.lock.acquire(blocking=True)
        value = np.nan
        try:
            value = self.client.get_temperature()[0]
        except Exception:
            print(traceback.format_exc())
        self.lock.release()
        return value

    def get_field(self):
        self.lock.acquire(blocking=True)
        value = np.nan
        try:
            value = self.client.get_field()[0]
        except Exception:
            print(traceback.format_exc())
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

