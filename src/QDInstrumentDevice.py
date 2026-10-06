from src.MeasurementDevice import MeasurementDevice, DeviceCard
from src.QDInstrumentAPI import QDInstrumentAPI, BridgeConfig, BridgeChannel, CalibrationMode, DriveMode
from threading import RLock, Thread
from ExtraClasses import MeasurementDeviceType as mdType
import DefaultSettings as ds
import numpy as np
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5.QtCore import QTimer
from src.GuiThread import GuiThread


class QDInstrumentDevice(MeasurementDevice):
    Device = None

    KEYS = ["temperature", "field"]
    UNITS = ["K", "Oe"]
    DEFAULT_PLOT_KEYS = [False, False]

    def __init__(self, data=None, settings=None):
        super().__init__({"name": "QDInstrument"})
        self.api = QDInstrumentAPI()
        self.lock = RLock()
        self.type = mdType.NONE

        self.info = None
        self.keys = QDInstrumentDevice.KEYS
        self.units = QDInstrumentDevice.UNITS
        self.logging_keys = ["temp", "field"]
        self.default_plot_keys = QDInstrumentDevice.DEFAULT_PLOT_KEYS
        self.calibration_mapping = {}

        self.key_to_function = {"temperature": self.get_temperature,
                                "field": self.get_field}

    # gets raw readings from device and applies calibration if necessary
    def get_readings(self):
        readings = {}
        for key in self.key_to_function:
            readings[key] = self.key_to_function[key]()
        self.last_reading = readings
        return readings

    # configures physical device
    def set_bridge_config(self, bridge_channel: int, current_limit: float, power_limit: float, voltage_limit: float,
                          calibration_mode: int = -1, drive_mode: int = -1):
        self.lock.acquire()
        config = BridgeConfig(current_limit=current_limit,
                              power_limit=power_limit,
                              voltage_limit=voltage_limit,
                              calibration_mode=calibration_mode,
                              drive_mode=drive_mode)
        try:
            self.api.set_bridge_config(bridge_channel, config)
        except EOFError:
            print("couldn't configure device")
        self.lock.release()

    def get_bridge_config(self, bridge_channel: int):
        if not self.connected:
            return None

        self.lock.acquire()
        try:
            config = self.api.get_bridge_config(bridge_channel)
        except EOFError:
            print("couldn't get bridge config")
        self.lock.release()
        return config

    # establishes connection to the physical device
    def connect(self):
        print("try connecting")
        self.lock.acquire()
        if self.connected:
            print("already connected")
            self.lock.release()
            return

        try:
            self.api.connect()
            self.connected = True
            print("connection successful")
        except:
            self.connected = False
            print("connection to mpv not possible")
            self.lock.release()
            return

        self.type = self.api.get_type()
        self.lock.release()

    def get_temperature(self):
        if not self.connected:
            return np.nan

        self.lock.acquire()
        value = np.nan
        try:
            value = self.api.get_temperature()
        except EOFError:
            print("couldn't read mpv temperature")
        self.lock.release()
        return value

    def get_field(self):
        if not self.connected:
            return np.nan

        self.lock.acquire()
        value = np.nan
        try:
            value = self.api.get_field()
        except EOFError:
            print("couldn't read mpv field")
        self.lock.release()
        return value

    def get_channel_readings(self, bridge_channel: int):
        readings = {"current": np.nan, "resistance": np.nan}
        if not self.connected:
            return readings

        self.lock.acquire()
        try:
            measurement = self.api.get_bridge_readings(bridge_channel)
            if measurement is not None:
                readings["current"] = measurement.current
                readings["resistance"] = measurement.resistance
        except EOFError:
            print("couldn't read bridge channel")
        self.lock.release()
        return readings

    # handles shutting down the properties in this wrapper
    def shutdown(self):
        self.api.disconnect()

    def set_field(self, set_point: float, ramp_rate: float):
        self.lock.acquire()
        try:
            self.api.set_field(set_point, ramp_rate)
        except EOFError:
            print("couldn't set field")
        self.lock.release()

    def set_temperature(self, set_point: float, ramp_rate: float):
        self.lock.acquire()
        try:
            self.api.set_temperature(set_point, ramp_rate)
        except EOFError:
            print("couldn't set temperature")
        self.lock.release()

    @staticmethod
    def get_device():
        if QDInstrumentDevice.Device is None:
            QDInstrumentDevice.Device = QDInstrumentDevice()
        return QDInstrumentDevice.Device

    @staticmethod
    def get_card(gui_setup, data=None):
        print("getting card")
        return QDInstrumentCard(gui_setup, data if data is not None else {})


class QDInstrumentCard(DeviceCard):
    NAME = "QDInstrument"
    TYPE = mdType.QDInstrument

    def __init__(self, gui_setup, data):
        super().__init__(gui_setup, data)
        self.channel_forms = {}

        # references for live editing
        self.connection_status = None
        self.reconnect_btn = None
        self.tabs = None
        self.qd_instrument = None
        self.reading_timer = None

    def get_device_data(self):
        return {"id": self.id, "type": self.type, "name": self.name}

    def get_slot_data(self, extra=None):
        data = {"id": self.id, "type": self.type, "name": self.name}
        if extra is not None:
            data["channel"] = extra.currentData().value
        return data

    def get_extra(self, slot, selection=None):
        index = selection if selection is not None else 0
        extra = qtw.QComboBox()
        for i in range(1, 5):
            extra.addItem(f"Channel {i}", BridgeChannel(i))
        extra.setCurrentIndex(index)

        def on_change():
            self.gui_setup.slot_selections[slot]["extra"] = extra.currentIndex()
            self.gui_setup.save_setup_settings()

        extra.activated.connect(on_change)
        return extra

    def open_edit_window(self):
        dlg = qtw.QDialog(self)
        dlg.setWindowTitle("edit")
        dlg.setFont(ds.FONT)
        layout = qtw.QVBoxLayout()
        dlg.setLayout(layout)

        # Settings
        form_holder = qtw.QWidget()
        form_holder.setFont(ds.FONT)
        form_layout = qtw.QFormLayout()
        form_holder.setLayout(form_layout)
        layout.addWidget(form_holder)
        name = qtw.QLineEdit()
        name.setText(self.name)
        form_layout.addRow("Name ", name)

        form_layout.addRow(qtw.QLabel(""))

        connection_holder = qtw.QWidget()
        connection_holder.setLayout(qtw.QHBoxLayout())
        form_layout.addRow(connection_holder)
        connection_status = qtw.QLabel("● connecting...")
        connection_holder.layout().addWidget(connection_status)
        connection_status.setStyleSheet("color: orange")
        connection_status.setFont(ds.FONT)
        reconnect_btn = qtw.QPushButton("↻")
        reconnect_btn.setContentsMargins(0, 0, 0, 0)
        reconnect_btn.setFixedSize(25, 25)
        reconnect_btn.hide()
        connection_holder.layout().addWidget(reconnect_btn)
        connection_holder.layout().addStretch()
        self.connection_status = connection_status
        self.reconnect_btn = reconnect_btn

        # Channel Settings
        tabs = qtw.QTabWidget()
        layout.addWidget(tabs)
        tabs.hide()
        self.tabs = tabs

        self.channel_forms = {}
        for ch in BridgeChannel:
            channel_holder = qtw.QWidget()
            form_layout = qtw.QFormLayout()
            channel_holder.setLayout(form_layout)
            tabs.addTab(channel_holder, f"Ch_{ch}")
            channel_form = {"channel": ch}

            readings = qtw.QLabel("[...]")
            readings.setContentsMargins(0, 0, 0, 10)
            form_layout.addRow(readings)
            channel_form["readings"] = readings

            current_limit = qtw.QLineEdit()
            current_limit.setValidator(qtg.QDoubleValidator())
            current_limit.setText("0")
            form_layout.addRow("Current Limit ", current_limit)
            channel_form["current_limit"] = current_limit

            power_limit = qtw.QLineEdit()
            power_limit.setValidator(qtg.QDoubleValidator())
            power_limit.setText("0")
            form_layout.addRow("Power Limit ", power_limit)
            channel_form["power_limit"] = power_limit

            voltage_limit = qtw.QLineEdit()
            voltage_limit.setValidator(qtg.QDoubleValidator())
            voltage_limit.setText("0")
            form_layout.addRow("Voltage Limit ", voltage_limit)
            channel_form["voltage_limit"] = voltage_limit

            calibration_mode = qtw.QComboBox()
            calibration_mode.addItem("Standard", CalibrationMode.STANDARD)
            calibration_mode.addItem("Fast", CalibrationMode.FAST)
            calibration_mode.addItem("Hi-Res", CalibrationMode.HI_RES)
            form_layout.addRow("Calibration Mode ", calibration_mode)
            channel_form["calibration_mode"] = calibration_mode
            channel_form["calibration_mode_label"] = form_layout.labelForField(calibration_mode)
            channel_form["calibration_mode_label"].hide()
            calibration_mode.hide()

            drive_mode = qtw.QComboBox()
            drive_mode.addItem("AC", DriveMode.AC)
            drive_mode.addItem("DC", DriveMode.DC)
            form_layout.addRow("Drive Mode ", drive_mode)
            channel_form["drive_mode"] = drive_mode
            channel_form["drive_mode_label"] = form_layout.labelForField(drive_mode)
            channel_form["drive_mode_label"].hide()
            drive_mode.hide()

            self.channel_forms[ch] = channel_form

        def connect():
            self.qd_instrument = QDInstrumentDevice.get_device()
            self.qd_instrument.connect()

        def update_display():
            if not self.qd_instrument.connected:
                self.connection_status.setText("● Not Connected")
                self.connection_status.setStyleSheet("color: red")
                self.connection_status.setFont(ds.FONT)
                self.reconnect_btn.show()
                return

            self.connection_status.setText("● Connected")
            self.connection_status.setStyleSheet("color: green")
            self.connection_status.setFont(ds.FONT)
            self.tabs.show()
            # self.reconnect_btn.show()

            for ch, form in self.channel_forms.items():
                config = self.qd_instrument.get_bridge_config(ch)
                if not config:
                    continue
                form["current_limit"].setText(str(config.current_limit))
                form["power_limit"].setText(str(config.power_limit))
                form["voltage_limit"].setText(str(config.voltage_limit))
                print(self.qd_instrument.type)
                if self.qd_instrument.type == mdType.PPMS6000:
                    form["calibration_mode"].setCurrentIndex(config.calibration_mode)
                    form["calibration_mode_label"].show()
                    form["calibration_mode"].show()
                    form["drive_mode"].setCurrentIndex(config.drive_mode)
                    form["drive_mode_label"].show()
                    form["drive_mode"].show()
                else:
                    form["calibration_mode_label"].hide()
                    form["calibration_mode"].hide()
                    form["drive_mode_label"].hide()
                    form["drive_mode"].hide()

            def update_readings():
                for ch, form in self.channel_forms.items():
                    readings = self.qd_instrument.get_channel_readings(ch)
                    formatted = "[" + ", ".join([f"{k[:3]}: {v:.2f}" for k, v in readings.items()]) + "]"
                    try:
                        form["readings"].setText(formatted)
                    except RuntimeError:
                        print("runtime err in edit window")
                        self.reading_timer.stop()
                        return

            self.reading_timer = QTimer()
            self.reading_timer.timeout.connect(update_readings)
            self.reading_timer.start(1000)

        t = GuiThread(target=connect)
        t.start()
        t.finished.connect(update_display)

        def reconnect():
            self.connection_status.setText("● connecting...")
            self.connection_status.setStyleSheet("color: orange")
            self.connection_status.setFont(ds.FONT)
            self.reconnect_btn.hide()
            t = GuiThread(target=connect)
            t.start()
            t.finished.connect(update_display)

        self.reconnect_btn.clicked.connect(reconnect)

        btn_holder = qtw.QWidget()
        btn_holder.setLayout(qtw.QHBoxLayout())
        btn_holder.setContentsMargins(0, 10, 0, 0)
        layout.addWidget(btn_holder)
        btn_holder.layout().addStretch()
        apply_btn = qtw.QPushButton("Apply")
        btn_holder.layout().addWidget(apply_btn)

        def apply_changes():
            self.name = name.text()
            self.gui_elements["name"].setText(self.name)
            for ch, form in self.channel_forms.items():
                self.qd_instrument.set_bridge_config(
                    ch,
                    float(form["current_limit"].text()),
                    float(form["voltage_limit"].text()),
                    float(form["power_limit"].text()),
                    form["calibration_mode"].currentData(),
                    form["drive_mode"].currentData()
                )

            self.gui_setup.update_slots()
            self.gui_setup.save_setup_settings()
            dlg.close()

        apply_btn.clicked.connect(apply_changes)

        dlg.exec()
        self.reading_timer.stop()
