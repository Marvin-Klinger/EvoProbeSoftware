import random

from lakeshore import Model372, Model372InputSetupSettings


class Model372Mock(Model372):

    KELVIN = 2
    RESISTANCE = 20
    POWER = 75
    QUADRATURE = 3
    SCANNER = 1

    def __init__(self, baud_rate, **kwargs):
        try:
            super().__init__(baud_rate, **kwargs)
        except:
            print("DEBUG MODE IS ACTIVE")

    def get_all_input_readings(self, input_channel):
        Model372Mock.KELVIN += (random.randint(0, 2) - 1) * 0.1
        Model372Mock.RESISTANCE += random.randint(0, 8) - 4
        Model372Mock.POWER += random.randint(0, 4) - 2
        Model372Mock.QUADRATURE += random.randint(0, 2) - 1
        return {"kelvin": max(0, Model372Mock.KELVIN),
                "resistance": max(0, Model372Mock.RESISTANCE),
                "power": max(0, Model372Mock.POWER),
                "quadrature": max(0, Model372Mock.QUADRATURE)}

    def configure_input(self, input_channel, settings):
        print("configuring input")
        print(f"channel {input_channel},\n{vars(settings)}")
        pass

    def get_input_setup_parameters(self, input_channel):
        return Model372InputSetupSettings(1, 2, 1, True, 1, 3)

    def set_filter(self, input_channel, state, settle_time, window):
        print("setting filter")
        pass

    def get_filter(self, input_channel):
        return {}

    def set_scanner_status(self, input_channel, status):
        print("settings scanner")
        Model372Mock.SCANNER = input_channel
        pass

    def get_scanner_status(self):
        return {"input_channel": Model372Mock.SCANNER,
                "status": True}
