import time
from datetime import datetime
import numpy as np
import pandas as pd
from lakeshore import Model372, Model372InputSetupSettings

from src.Devices.LakeshoreDevice import LakeshoreDevice
from src.Devices.MeasurementDevice import MeasurementDevice
from src.ExtraClasses import DeviceInfo


class LakeshoreChannel(MeasurementDevice):

    SCANNER_SETTLE_TIME = 3
    READER_INTERVAL = 0.1
    LOG_INTERVAL = 1
    KEYS = ["kelvin", "resistance", "power", "quadrature"]
    UNITS = ["K", "Ω", "W", "iΩ"]
    CALIBRATION_MAPPING = {"resistance": "kelvin"}
    DEFAULT_PLOT_KEYS = [True, True, False, False]

    def __init__(self, data, settings=None):
        super().__init__(data, settings)

        self.input_channel = Model372.InputChannel(data["channel"])
        self.lakeshore = LakeshoreDevice.get_device(data["id"])
        if settings is not None:
            self.lakeshore.baud_rate = settings.get("baud_rate")
            self.lakeshore.ip_address = settings.get("ip")
            self.use_usb = settings.get("use_usb", False)
            self.use_ip = settings.get("use_ip", False)
        self.lakeshore.add_channel(self.input_channel)

        key_bool_map = [self.calibration is not None, True, True, self.input_channel != Model372.InputChannel.CONTROL]
        self.keys = [key for key, use in zip(LakeshoreChannel.KEYS, key_bool_map) if use]
        self.units = [unit for unit, use in zip(LakeshoreChannel.UNITS, key_bool_map) if use]
        self.logging_keys = [f"{key[:3]}_{self.input_channel.value}" for key in self.keys]
        self.default_plot_keys = [state for state, use in zip(LakeshoreChannel.DEFAULT_PLOT_KEYS, key_bool_map) if use]
        self.calibration_mapping = LakeshoreChannel.CALIBRATION_MAPPING
        self.name += f"_Ch{self.input_channel.value}"
        self.info = DeviceInfo(name=f"Channel {self.input_channel.value}", version=0)

        self.interval = LakeshoreChannel.READER_INTERVAL
        self.is_scanning = False
        self.last_reading = {key: np.nan for key in self.keys}

    # returns readings of {kelvin, resistance, power, quadrature(optional)} as dictionary
    def get_readings(self):
        if self.ready_to_read():
            self.last_reading = self.lakeshore.get_readings(self.input_channel)
            return self.last_reading
        else:
            return {key: np.nan for key in self.keys}

    # configures channels setup settings in lakeshore device
    def configure(self, settings: Model372InputSetupSettings):
        self.lakeshore.configure(self.input_channel.value, settings)

    # establishes connection to the physical device
    def connect(self):
        self.lakeshore.connect(self.use_usb, self.use_ip)
        self.connected = self.lakeshore.connected

    def start_reading(self):
        self.lakeshore.start_scanner_cycle()
        self.is_scanning = self.input_channel != Model372.InputChannel.CONTROL and self.lakeshore.is_cycling
        print(self.input_channel, self.is_scanning)

    def stop_reading(self):
        self.lakeshore.stop_scanner_cycle()
        self.is_scanning = False

    @staticmethod
    def _run(device):
        buffer = pd.DataFrame(columns=["timestamp", "timedelta"]+device.logging_keys)
        last_log_timestamp = time.monotonic()
        is_scanner = False
        while device.is_logging:
            if device.is_scanning:
                if device.ready_to_read() and device.lakeshore.filter_is_ready:
                    is_scanner = True
                    readings = device.get_logging_readings()
                    time_data = [datetime.now(), time.monotonic() - device.start_time]
                    buffer.loc[len(buffer)] = time_data + readings
                elif is_scanner:
                    is_scanner = False
                    device.log_readings(list(buffer.mean()))
                    buffer = buffer.iloc[0:0]
            else:
                if device.ready_to_read():
                    readings = device.get_logging_readings()
                    time_data = [datetime.now(), time.monotonic() - device.start_time]
                    buffer.loc[len(buffer)] = time_data + readings

                if time.monotonic() - last_log_timestamp >= LakeshoreChannel.LOG_INTERVAL:
                    last_log_timestamp = time.monotonic()
                    device.log_readings(list(buffer.mean()))
                    buffer = buffer.iloc[0:0]

            time.sleep(device.interval)

    def ready_to_read(self):
        return (self.lakeshore.connected and
                (self.input_channel == Model372.InputChannel.CONTROL or
                 self.lakeshore.is_ready and
                 self.lakeshore.current_channel == self.input_channel))
