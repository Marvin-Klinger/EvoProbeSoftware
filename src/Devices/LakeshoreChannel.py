import time
from datetime import datetime
import numpy as np
import pandas as pd
from lakeshore import Model372, Model372InputSetupSettings

from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5.QtCore import Qt

from src.Devices.LakeshoreDevice import LakeshoreDevice
from src.Devices.MeasurementDevice import MeasurementDevice
from src.ExtraClasses import DeviceInfo
import src.DefaultSettings as ds
from src.Gui.GuiHelper import range_text_converter


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

    # returns the widget used for settings in GuiActive and its name
    def get_settings_tab(self):
        ch = 0 if self.input_channel.value == 'A' else self.input_channel.value
        channel_holder = qtw.QWidget()
        form_layout = qtw.QFormLayout()
        channel_holder.setLayout(form_layout)

        excitation_frequency = qtw.QComboBox()
        for item in Model372.InputFrequency:
            excitation_frequency.addItem(range_text_converter(item.name), item)

        form_layout.addRow("Excitation Frequency ", excitation_frequency)
        if ch != 0:  # is not Control Channel
            excitation_mode = qtw.QComboBox()
            excitation_mode.addItem("voltage", Model372.SensorExcitationMode.VOLTAGE)
            excitation_mode.addItem("current", Model372.SensorExcitationMode.CURRENT)
            form_layout.addRow("Excitation Mode ", excitation_mode)

        excitation_range = qtw.QComboBox()
        for x in (Model372.MeasurementInputVoltageRange if ch != 0 else Model372.ControlInputCurrentRange):
            excitation_range.addItem(range_text_converter(x.name), x)
        form_layout.addRow("Excitation Range ", excitation_range)

        auto_range = qtw.QCheckBox()
        auto_range.setStyleSheet("QCheckBox::indicator { width:20px; height: 20px;}")
        form_layout.addRow("Auto Range ", auto_range)

        if ch != 0:
            resistance_range = qtw.QComboBox()
            for x in Model372.MeasurementInputResistance:
                resistance_range.addItem(range_text_converter(x.name), x)
            resistance_range.setCurrentIndex(9)  # MeasurementInputResistance.RANGE_63_POINT_2_KIL_OHMS
            form_layout.addRow("Resistance Range ", resistance_range)

            def on_excitation_mode_changed(value=0, _excitation_range=None):
                if _excitation_range is None:
                    return

                _excitation_range.clear()
                if value == Model372.SensorExcitationMode.CURRENT:
                    for x in Model372.MeasurementInputCurrentRange:
                        _excitation_range.addItem(range_text_converter(x.name), x)
                    _excitation_range.setCurrentIndex(16)  # MeasurementInputCurrentRange.RANGE_100_MICRO_AMPS
                else:  # voltage TODO: sensible default value
                    for x in Model372.MeasurementInputVoltageRange:
                        _excitation_range.addItem(range_text_converter(x.name), x)
                    _excitation_range.setCurrentIndex(0)

            excitation_mode.currentIndexChanged.connect(
                lambda x, y=excitation_range: on_excitation_mode_changed(x, y))

        use_filter = qtw.QCheckBox()
        use_filter.setStyleSheet("QCheckBox::indicator { width:20px; height: 20px;}")
        use_filter.setChecked(True)
        form_layout.addRow("use filter ", use_filter)

        settle_time = qtw.QSpinBox()
        settle_time.setRange(1, 200)
        settle_time.setValue(5)
        settle_time.setSuffix("s")
        settle_time.setButtonSymbols(qtw.QAbstractSpinBox.ButtonSymbols.NoButtons)
        form_layout.addRow("settle time (1-200s) ", settle_time)

        window = qtw.QSpinBox()
        window.setRange(1, 80)
        window.setValue(10)
        window.setSuffix("%")
        window.setButtonSymbols(qtw.QAbstractSpinBox.ButtonSymbols.NoButtons)
        form_layout.addRow("window (1-80%) ", window)

        def use_filter_changed(is_checked, _settle_time, _window):
            _settle_time.setEnabled(is_checked)
            _window.setEnabled(is_checked)

        use_filter.stateChanged.connect(lambda a, b=settle_time, c=window: use_filter_changed(a, b, c))

        def apply_changes():
            if self.lakeshore is not None and self.lakeshore.connected:
                self.lakeshore.set_excitation_frequency(Model372.InputChannel.CONTROL, excitation_frequency.currentData())
                if ch == 0:
                    settings = Model372InputSetupSettings(mode=Model372.SensorExcitationMode.CURRENT,
                                                          excitation_range=excitation_range.currentData(),
                                                          auto_range=Model372.AutoRangeMode(
                                                              auto_range.isChecked()),
                                                          current_source_shunted=False,
                                                          units=Model372.InputSensorUnits.OHMS)
                else:
                    settings = Model372InputSetupSettings(mode=excitation_mode.currentData(),
                                                          excitation_range=excitation_range.currentData(),
                                                          auto_range=Model372.AutoRangeMode(
                                                              auto_range.isChecked()),
                                                          current_source_shunted=False,
                                                          units=Model372.InputSensorUnits.OHMS,
                                                          resistance_range=resistance_range.currentData())
                self.lakeshore.configure(self.input_channel, settings)

                self.lakeshore.set_filter(input_channel=self.input_channel,
                                          state=use_filter.isChecked(),
                                          settle_time=settle_time.value(),
                                          window=window.value())

        # Bottom Buttons
        btn_holder = qtw.QWidget()
        btn_holder.setLayout(qtw.QHBoxLayout())
        btn_holder.setContentsMargins(0, 10, 0, 0)
        form_layout.addRow(btn_holder)
        btn_holder.layout().addStretch()
        apply_btn = qtw.QPushButton("Apply")
        btn_holder.layout().addWidget(apply_btn)
        apply_btn.clicked.connect(apply_changes)

        return channel_holder, f"LS_Ch{self.input_channel.value}"
