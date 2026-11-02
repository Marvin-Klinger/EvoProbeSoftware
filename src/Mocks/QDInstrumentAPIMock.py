from enum import IntEnum
from dataclasses import dataclass
import random

from src.ExtraClasses import MeasurementDeviceType as mdType
from src.Devices.QDInstrumentAPI import BridgeChannel, CalibrationMode, DriveMode, BridgeMeasurement, BridgeConfig


class QDInstrumentAPIMock:

    def __init__(self):
        self.type = mdType.PPMS6000
        self.temp = 30.
        self.field = 50.
        self.measurement = BridgeMeasurement(10, 100)
        self.config = BridgeConfig(1, 2, 3, CalibrationMode.FAST, DriveMode.AC)
        self.connected = False

    def get_type(self) -> mdType.PPMS6000 | mdType.DYNACOOL | mdType.NONE:
        return self.type

    def get_temperature(self) -> float:
        return self.temp

    def get_field(self) -> float:
        return self.field

    def get_bridge_readings(self, bridge_channel: BridgeChannel | int) -> BridgeMeasurement:
        return self.measurement

    # if necessary
    def set_temperature(self, set_point: float, rate: float):
        self.temp = set_point
        print("setting temp to", set_point)

    # if necessary
    def set_field(self, set_point: float, rate: float):
        self.field = set_point
        print("setting field to", set_point)

    def set_bridge_config(self, bridge_channel: BridgeChannel | int, config: BridgeConfig):
        self.config = config
        print("setting bridge config to", config)

    def get_bridge_config(self, bridge_channel: BridgeChannel | int) -> BridgeConfig:
        return self.config

    # either handle error here and return True|False or raise error if connection fails
    # alternatively expose a connected attribute in class
    def connect(self, *args) -> bool:
        self.connected = True
        print("connecting to QDInstrumentMock")
        return True

    # if necessary
    def disconnect(self):
        self.connected = False
        print("disconnecting from QDInstrumentMock")

    # if necessary
    def is_connected(self) -> bool:
        return self.connected

