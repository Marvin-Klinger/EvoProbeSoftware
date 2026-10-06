from enum import IntEnum
from dataclasses import dataclass
from ExtraClasses import MeasurementDeviceType as mdType


class BridgeChannel(IntEnum):
    CHANNEL_1 = 1
    CHANNEL_2 = 2
    CHANNEL_3 = 3
    CHANNEL_4 = 4


class CalibrationMode(IntEnum):
    NONE = -1
    STANDARD = 0
    FAST = 1
    HI_RES = 2


class DriveMode(IntEnum):
    NONE = -1
    AC = 0
    DC = 1


@dataclass
class BridgeMeasurement:
    current: float
    resistance: float
    # current_error: int = 0
    # resistance_error: int = 0


@dataclass
class BridgeConfig:
    current_limit: float
    power_limit: float
    voltage_limit: float
    calibration_mode: CalibrationMode | int = CalibrationMode.NONE
    drive_mode: DriveMode | int = DriveMode.NONE


class QDInstrumentAPI:

    def __init__(self):
        pass

    def get_type(self) -> mdType.PPMS6000 | mdType.DYNACOOL | mdType.NONE:
        pass

    def get_temperature(self) -> float:
        pass

    def get_field(self) -> float:
        pass

    def get_bridge_readings(self, bridge_channel: BridgeChannel | int) -> BridgeMeasurement:
        pass

    # if necessary
    def set_temperature(self, set_point: float, rate: float):
        pass

    # if necessary
    def set_field(self, set_point: float, rate: float):
        pass

    def set_bridge_config(self, bridge_channel: BridgeChannel | int, config: BridgeConfig):
        pass

    def get_bridge_config(self, bridge_channel: BridgeChannel | int) -> BridgeConfig:
        pass

    # either handle error here and return True|False or raise error if connection fails
    # alternatively expose a connected attribute in class
    def connect(self, *args) -> bool:
        pass

    # if necessary
    def disconnect(self):
        pass

    # if necessary
    def is_connected(self) -> bool:
        pass

