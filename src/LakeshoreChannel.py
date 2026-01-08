import time

import numpy as np
from lakeshore import Model372, Model372InputSetupSettings

from src.LakeshoreDevice import LakeshoreDevice
from src.MeasurementDevice import MeasurementDevice


class LakeshoreChannel(MeasurementDevice):

    SCANNER_SETTLE_TIME = 3

    def __init__(self, lakeshore: LakeshoreDevice, input_channel: Model372.InputChannel, calibration):
        super().__init__()

        self.lakeshore = lakeshore
        self.input_channel = input_channel
        self.calibration = calibration
        # TODO: is quadrature needed?
        self.keys = ["kelvin", "resistance", "power"]
        self.logging_keys = [f"{key[:2]}_{self.input_channel.name}" for key in self.keys]

        self.last_reading = {"kelvin": np.nan, "resistance": np.nan, "power": np.nan}

    # returns readings of {kelvin, resistance, power, quadrature(optional)} as dictionary
    # TODO: add calibration
    def get_readings(self):
        if (self.input_channel == Model372.InputChannel.CONTROL
                or self.lakeshore.is_ready and self.lakeshore.current_channel == self.input_channel):
            self.last_reading = self.lakeshore.get_readings(self.input_channel)
            return self.last_reading
        else:
            return {key: np.nan for key in self.keys}

    # returns readings mapped to logging_keys
    def get_logging_readings(self):
        readings = self.get_readings()
        logging_readings = {}
        for i, key in enumerate(self.keys):
            logging_readings[self.logging_keys[i]] = readings[key]
        return logging_readings

    # configures channels setup settings in lakeshore device
    def configure_setup_settings(self, settings: Model372InputSetupSettings):
        self.lakeshore.configure(self.input_channel.value, settings)


if __name__ == "__main__":
    device = LakeshoreDevice([Model372.InputChannel.CONTROL, Model372.InputChannel.ONE, Model372.InputChannel.TEN])
    channel = LakeshoreChannel(device, Model372.InputChannel.ONE, None)
    print(device.current_channel)
    print(device.is_ready)
    time.sleep(2)
    print(device.is_ready)
    print(channel.get_readings())
    print(channel.get_logging_readings())
