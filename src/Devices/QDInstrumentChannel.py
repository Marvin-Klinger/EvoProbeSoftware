import src.DefaultSettings as ds
from src.ExtraClasses import MeasurementDeviceType as mdType, DeviceInfo
from src.Devices.MeasurementDevice import MeasurementDevice
from src.Devices.QDInstrumentAPI import BridgeChannel, BridgeConfig
from src.Devices.QDInstrumentDevice import QDInstrumentDevice


class QDInstrumentChannel(MeasurementDevice):

    KEYS = ["current", "resistance", "temperature"]
    UNITS = ["A", "Ω", "K"]
    CALIBRATION_MAPPING = {"resistance": "temperature"}
    DEFAULT_PLOT_KEYS = [True, False, True]

    def __init__(self, data, settings=None):
        super().__init__(data, settings)
        self.bridge_channel = BridgeChannel(data["channel"])
        self.qd_instrument = QDInstrumentDevice.get_device()

        self.last_values = {}
        self.info = DeviceInfo(name=f"Bridge {self.bridge_channel}", version=0)
        key_bool_map = [True, True, self.calibration is not None]
        self.keys = [key for key, use in zip(QDInstrumentChannel.KEYS, key_bool_map) if use]
        self.units = [unit for unit, use in zip(QDInstrumentChannel.UNITS, key_bool_map) if use]
        self.logging_keys = [f"{key[:3]}_{self.bridge_channel}" for key in self.keys]
        self.default_plot_keys = [state for state, use in zip(QDInstrumentChannel.DEFAULT_PLOT_KEYS, key_bool_map) if use]
        self.calibration_mapping = QDInstrumentChannel.CALIBRATION_MAPPING

    # gets raw readings from device
    def get_readings(self):
        return self.qd_instrument.get_channel_readings(self.bridge_channel)

    # configures physical device
    def configure(self, settings: BridgeConfig):
        self.qd_instrument.set_bridge_config(self.bridge_channel, settings)

    # establishes connection to the physical device
    def connect(self):
        self.qd_instrument.connect()
        self.connected = self.qd_instrument.connected

    # starts routines necessary for measuring data
    def start_reading(self):
        pass

    # stops routines necessary for measuring data
    def stop_reading(self):
        pass
