import random
import time

from MeasurementDevice import MeasurementDevice, DeviceCard
from threading import Thread
from ExtraClasses import MeasurementDeviceType as mdType
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
import MultiPyVu as mpv
import DefaultSettings as ds
from enum import IntEnum

from src.GuiThread import GuiThread


class PPMS6000(MeasurementDevice):
    LOGGING_KEYS = ["current", "resistance"]

    def __init__(self, data=None):
        if data is None:
            data = {}
        super().__init__(data)
        pass

    # gets raw readings from device and applies calibration if necessary
    def get_readings(self):
        # TODO: proper implementation
        return {BridgeChannel(i): {"current": random.uniform(0.1, 10),
                                   "resistance": random.uniform(0.1, 20)} for i in range(1, 5)}

    # converts readings to data usable by DataHub
    def get_logging_readings(self):
        readings = self.get_readings()
        logging_readings = []
        for key in self.keys:
            logging_readings.append(readings[key])
        return logging_readings

    # configures physical device
    def configure(self, settings):
        pass

    # establishes connection to the physical device
    def connect(self):
        # TODO: proper implementation
        time.sleep(1)
        self.connected = True

    # starts routines necessary for measuring data
    def start_reading(self):
        pass

    # stops routines necessary for measuring data
    def stop_reading(self):
        pass

    @staticmethod
    def get_card(gui_setup, data=None):
        print("getting card")
        return PPMS6000Card(gui_setup, data if data is not None else {})


class PPMS6000Card(DeviceCard):
    NAME = "PPMS6000"
    TYPE = mdType.PPMS6000

    def __init__(self, gui_setup, data):
        super().__init__(gui_setup, data)

        self.channel_settings = {}
        for ch in BridgeChannel:
            ch_data = data.get("channel_settings", {}).get(str(ch), {})
            settings = {"current_limit": ch_data.get("current_limit", 10),
                        "power_limit": ch_data.get("power_limit", 100),
                        "voltage_limit": ch_data.get("voltage_limit", 5),
                        "calibration_mode": ch_data.get("calibration_mode", 0),
                        "drive_mode": ch_data.get("drive_mode", 0)}
            self.channel_settings[ch] = settings

        self.channel_forms = {}

        # references for live editing
        self.connection_status = None
        self.reconnect_btn = None
        self.tabs = None
        self.ppms = None

    def get_device_data(self):
        return {"id": self.id, "type": self.type, "name": self.name,
                "channel_settings": self.channel_settings}

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
            settings = self.channel_settings[ch]

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
            current_limit.setText(str(settings["current_limit"]))
            form_layout.addRow("Current Limit ", current_limit)
            channel_form["current_limit"] = current_limit

            power_limit = qtw.QLineEdit()
            power_limit.setValidator(qtg.QDoubleValidator())
            power_limit.setText(str(settings["power_limit"]))
            form_layout.addRow("Power Limit ", power_limit)
            channel_form["power_limit"] = power_limit

            voltage_limit = qtw.QLineEdit()
            voltage_limit.setValidator(qtg.QDoubleValidator())
            voltage_limit.setText(str(settings["voltage_limit"]))
            form_layout.addRow("Voltage Limit ", voltage_limit)
            channel_form["voltage_limit"] = voltage_limit

            calibration_mode = qtw.QComboBox()
            calibration_mode.addItem("Standard", CalibrationMode.STANDARD)
            calibration_mode.addItem("Fast", CalibrationMode.FAST)
            calibration_mode.addItem("Hi-Res", CalibrationMode.HI_RES)
            calibration_mode.setCurrentIndex(settings["calibration_mode"])
            form_layout.addRow("Calibration Mode ", calibration_mode)
            channel_form["calibration_mode"] = calibration_mode

            drive_mode = qtw.QComboBox()
            drive_mode.addItem("AC", DriveMode.AC)
            drive_mode.addItem("DC", DriveMode.DC)
            drive_mode.setCurrentIndex(settings["drive_mode"])
            form_layout.addRow("Drive Mode ", drive_mode)
            channel_form["drive_mode"] = drive_mode

            self.channel_forms[ch] = channel_form

        def tab_changed(x):
            pass

        self.tabs.currentChanged.connect(tab_changed)

        def connect_ppms():
            self.ppms = PPMS6000()
            self.ppms.connect()

        def update_display():
            if not self.ppms.connected:
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

            # TODO: apply read settings
            for form in self.channel_forms:
                pass

            def update_readings():
                while True:
                    readings = self.ppms.get_readings()
                    for ch, form in self.channel_forms.items():
                        formatted = "[" + ", ".join([f"{k[:3]}: {v:.2f}" for k, v in readings[ch].items()]) + "]"
                        try:
                            form["readings"].setText(formatted)
                        except RuntimeError:
                            return
                    time.sleep(1)

            t = Thread(daemon=True, target=update_readings)
            t.start()

        t = GuiThread(target=connect_ppms)
        t.start()
        t.finished.connect(update_display)

        def reconnect():
            self.connection_status.setText("● connecting...")
            self.connection_status.setStyleSheet("color: orange")
            self.connection_status.setFont(ds.FONT)
            self.reconnect_btn.hide()
            t = Thread(daemon=True, target=update_display)
            t.start()

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
                settings = self.channel_settings[ch]
                settings["current_limit"] = form["current_limit"].text()
                settings["voltage_limit"] = form["voltage_limit"].text()
                settings["power_limit"] = form["power_limit"].text()
                settings["calibration_mode"] = form["calibration_mode"].currentData()
                settings["drive_mode"] = form["drive_mode"].currentData()

            self.gui_setup.update_slots()
            self.gui_setup.save_setup_settings()
            dlg.close()

        apply_btn.clicked.connect(apply_changes)

        dlg.exec()


class CalibrationMode(IntEnum):
    STANDARD = 0
    FAST = 1
    HI_RES = 2


class DriveMode(IntEnum):
    AC = 0
    DC = 1


class BridgeChannel(IntEnum):
    CHANNEL_1 = 1
    CHANNEL_2 = 2
    CHANNEL_3 = 3
    CHANNEL_4 = 4
