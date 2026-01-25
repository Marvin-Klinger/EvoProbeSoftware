from enum import Enum


class MeasurementDevice:

    def __init__(self):
        self.last_values = {}
        self.info = None
        self.calibration = None
        self.keys = []
        self.logging_keys = []
        self.plotting_keys = []
        self.connected = False

    # gets raw readings from device and applies calibration if necessary
    def get_readings(self):
        return {}

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
        pass

