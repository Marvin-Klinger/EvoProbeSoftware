from enum import Enum, IntEnum


# stores metadata for device used for header
class DeviceInfo:

    def __init__(self, name, version):
        self.name = name
        self.version = version


class MeasurementDeviceType(IntEnum):
    DUMMY = 0
    LAKESHORE = 1
    PPMS6000 = 2
    DYNACOOL = 3
    MPV = 4


# allows to loop through different colors
class ColorFactory:
    COLORS_RGB = [(57, 106, 177),   # blue
                  (218, 124, 48),   # orange
                  (62, 150, 81),    # green
                  (204, 37, 41),    # red
                  (255, 222, 33),   # yellow
                  (83, 81, 84),     # grey
                  (107, 76, 154),   # purple
                  (146, 36, 40),    # brown
                  (148, 139, 61),   # camo
                  (114, 147, 203),  # light blue
                  (132, 186, 91),   # light green
                  (255, 141, 161),  # pink
                  (204, 194, 16),   # sand
                  ]

    @staticmethod
    def make_colorgenerator():
        while True:
            for c in ColorFactory.COLORS_RGB:
                yield c

