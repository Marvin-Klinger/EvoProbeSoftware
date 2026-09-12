import random
import time

from lakeshore import Model372, Model372InputSetupSettings


class Model372Mock(Model372):

    KELVIN = [x*4 for x in range(1, 6)]
    RESISTANCE = [x*10 for x in range(1, 6)]
    POWER = [x*.5 for x in range(1, 6)]
    QUADRATURE = [x*2 for x in range(1, 6)]
    SCANNER = 1

    def __init__(self, baud_rate, **kwargs):
        try:
            super().__init__(baud_rate, **kwargs)
        except:
            time.sleep(.5)
            print("DEBUG MODE IS ACTIVE")

    def get_all_input_readings(self, input_channel):
        if input_channel == "A":
            input_channel = 0
        Model372Mock.KELVIN[input_channel] += random.randint(0, 4) - 2
        Model372Mock.RESISTANCE[input_channel] += random.randint(0, 8) - 4
        Model372Mock.POWER[input_channel] += random.randint(0, 1) - 0.5
        Model372Mock.QUADRATURE[input_channel] += random.randint(0, 2) - 1
        return {"kelvin": max(0.01, Model372Mock.KELVIN[input_channel]),
                "resistance": max(0.01, Model372Mock.RESISTANCE[input_channel]),
                "power": max(0.01, Model372Mock.POWER[input_channel]),
                "quadrature": max(0.01, Model372Mock.QUADRATURE[input_channel])}

    def configure_input(self, input_channel, settings):
        print("configuring input")
        print(f"channel {input_channel},\n{vars(settings)}")
        pass

    def get_input_setup_parameters(self, input_channel):
        return Model372InputSetupSettings(Model372.SensorExcitationMode.CURRENT,
                                          Model372.MeasurementInputCurrentRange.RANGE_3_POINT_16_MICRO_AMPS if input_channel != "A"
                                          else Model372.ControlInputCurrentRange.RANGE_10_NANO_AMPS,
                                          Model372.AutoRangeMode.CURRENT,
                                          True,
                                          Model372.InputSensorUnits.OHMS,
                                          Model372.MeasurementInputResistance.RANGE_2_MEGA_OHMS)

    def set_filter(self, input_channel, state, settle_time, window):
        print("setting filter: ", input_channel, state, settle_time, window)
        pass

    def get_filter(self, input_channel):
        if input_channel == "A":
            return {"state": False, "settle_time": 10, "window": 10}
        else:
            return {"state": True, "settle_time": 16, "window": 8}

    def set_excitation_frequency(self, input_channel, frequency):
        print("setting frequency of ", input_channel, " to ", frequency)

    def get_excitation_frequency(self, input_channel):
        return Model372.InputFrequency.FREQUENCY_13_POINT_7_HZ if input_channel == 0 \
            else Model372.InputFrequency.FREQUENCY_9_POINT_8_HZ

    def set_scanner_status(self, input_channel, status):
        print("settings scanner to ", input_channel)
        Model372Mock.SCANNER = input_channel
        pass

    def get_scanner_status(self):
        return {"input_channel": Model372Mock.SCANNER,
                "status": True}
