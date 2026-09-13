from enum import Enum, IntEnum
import numpy as np


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


# creates calibration functions from given parameters
class CalibrationFactory:
    REQUIRED_PARAMETERS = ["min_resistance", "max_resistance", "rescale_0", "rescale_1",
                           "func_params", "min_temperature", "max_temperature"]

    @staticmethod
    def create_function(parameters: dict):
        if parameters is None or any((key not in CalibrationFactory.REQUIRED_PARAMETERS for key in parameters)):
            return None

        def func(resistance):
            if resistance < parameters["min_resistance"] or resistance > parameters["max_resistance"]:
                return np.nan
            x = parameters["rescale_0"] - np.log(resistance - parameters["rescale_1"])
            total = 0
            for i in range(len(parameters["func_params"])):
                total += parameters["func_params"][i] * x ** i
            t = np.exp(total)
            if t < parameters["min_temperature"] or t > parameters["max_temperature"]:
                return np.nan
            return t

        return func
