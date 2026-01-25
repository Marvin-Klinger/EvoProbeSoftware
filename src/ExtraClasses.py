from enum import Enum


# stores metadata for device used for header
class DeviceInfo:

    def __init__(self, name, version):
        self.name = name
        self.version = version


class MeasurementDeviceType(Enum):
    LAKESHORE = 0
    MPV = 1

