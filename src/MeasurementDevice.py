
class MeasurementDevice:

    def __init__(self):
        self.last_values = {}
        self.info = None
        self.calibration = None
        self.keys = []
        self.logging_keys = []
        self.plotting_keys = []

    # gets raw readings from device and applies calibration if necessary
    def get_readings(self):
        return {}

    # converts readings to data usable by DataHub
    def get_logging_readings(self):
        readings = self.get_readings()
        logging_readings = {}
        for i in range(len(self.keys)):
            logging_readings[self.logging_keys[i]] = readings[self.keys[i]]
        return logging_readings

    # return if data is ready to be read
    def is_ready(self):
        return True

    # configures physical device
    def configure(self, settings):
        pass

    # establishes connection to the physical device
    def connect(self):
        pass

