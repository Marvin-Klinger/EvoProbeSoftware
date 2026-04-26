from enum import Enum, IntEnum


# stores metadata for device used for header
class DeviceInfo:

    def __init__(self, name, version):
        self.name = name
        self.version = version


class MeasurementDeviceType(IntEnum):
    DUMMY = 0
    LAKESHORE = 1
    MPV = 2

