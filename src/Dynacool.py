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
from MPVWrapper import BridgeChannel, CalibrationMode, DriveMode, MPVWrapper

from src.GuiThread import GuiThread


class Dynacool:
    LOGGING_KEYS = ["current", "resistance"]

    Devices = {}

    def __init__(self):
        self.mpv = MPVWrapper.get_device()
        self.connected = False

    # gets raw readings from device and applies calibration if necessary
    def get_readings(self, channel: BridgeChannel):
        return self.mpv.get_channel_reading(channel)

    # converts readings to data usable by DataHub
    def get_logging_readings(self, channel: BridgeChannel):
        readings = self.get_readings(channel)
        logging_readings = []
        for key in self.LOGGING_KEYS:
            logging_readings.append(readings[key])
        return logging_readings

    # configures physical device
    def configure(self, bridge_channel: int, channel_on: bool,
                  current_limit: float, power_limit: float, voltage_limit: float):
        self.mpv.configure(bridge_channel, channel_on, current_limit, power_limit, voltage_limit)

    # establishes connection to the physical device
    def connect(self):
        self.mpv.connect()
        self.connected = self.mpv.connected

    # connects to the devices asynchronously to not freeze the GUI
    def connect_async(self):
        t = Thread(target=self.connect, daemon=True)
        t.start()

    # starts routines necessary for measuring data
    def start_reading(self):
        pass

    # stops routines necessary for measuring data
    def stop_reading(self):
        pass

    @staticmethod
    def get_device(id: int):
        if id not in Dynacool.Devices:
            Dynacool.Devices[id] = Dynacool()

        return Dynacool.Devices[id]

    @staticmethod
    def get_card(gui_setup, data=None):
        print("getting card")
        return DynacoolCard(gui_setup, data if data is not None else {})


class DynacoolCard(DeviceCard):
    NAME = "Dynacool"
    TYPE = mdType.DYNACOOL

    def __init__(self, gui_setup, data):
        super().__init__(gui_setup, data)

        self.channel_settings = {}
        for ch in BridgeChannel:
            ch_data = data.get("channel_settings", {}).get(str(ch), {})
            settings = {"current_limit": ch_data.get("current_limit", 10),
                        "power_limit": ch_data.get("power_limit", 100),
                        "voltage_limit": ch_data.get("voltage_limit", 5)}
            self.channel_settings[ch] = settings

        self.channel_forms = {}

        # references for live editing
        self.connection_status = None
        self.reconnect_btn = None
        self.tabs = None
        self.dynacool = None

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

            self.channel_forms[ch] = channel_form

        def tab_changed(x):
            pass

        self.tabs.currentChanged.connect(tab_changed)

        def connect_dynacool():
            self.dynacool = Dynacool()
            self.dynacool.connect()

        def update_display():
            if not self.dynacool.connected:
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

            # TODO: apply read settings (there doesnt seem to be a way for now)
            for form in self.channel_forms:
                pass

            def update_readings():
                while True:
                    readings = self.dynacool.get_readings()
                    for ch, form in self.channel_forms.items():
                        formatted = "[" + ", ".join([f"{k[:3]}: {v:.2f}" for k, v in readings[ch].items()]) + "]"
                        try:
                            form["readings"].setText(formatted)
                        except RuntimeError:
                            return
                    time.sleep(1)

            t = Thread(daemon=True, target=update_readings)
            t.start()

        t = GuiThread(target=connect_dynacool)
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

            self.gui_setup.update_slots()
            self.gui_setup.save_setup_settings()
            # dlg.close()

            if self.dynacool is not None and self.dynacool.connected:
                for ch in BridgeChannel:
                    settings = self.channel_settings[ch]
                    self.dynacool.configure(ch, True, settings["current_limit"],
                                            settings["voltage_limit"], settings["power_limit"])

        apply_btn.clicked.connect(apply_changes)

        dlg.exec()


