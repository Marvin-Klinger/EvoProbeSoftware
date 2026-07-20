import time

import numpy as np
from lakeshore import Model372
from Model372Mock import Model372Mock, Model372InputSetupSettings
from MeasurementDevice import DeviceCard
from ExtraClasses import MeasurementDeviceType as mdType
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5.QtCore import Qt
import DefaultSettings as ds
from GuiHelper import range_text_converter

from collections import deque
from threading import Thread, Lock
from itertools import chain


class LakeshoreDevice:
    IP_ADDRESS = "192.168.0.12"
    BAUD_RATE = 57600
    DEBUG_MODE = True

    Devices = {}

    def __init__(self, scanner_interval=5, baud_rate=BAUD_RATE, ip_address=IP_ADDRESS):

        self.lakeshore: Model372 = None
        self.input_channels = []
        self.scanner_queue = deque()
        self.scanner_interval = scanner_interval
        self.baud_rate = baud_rate
        self.ip_address = ip_address
        self.current_channel = None
        self.is_ready = False
        self.is_cycling = False
        self.cycle_is_alive = False
        self.connected = False
        self.lock = Lock()

        self.info = None

    def add_channel(self, channel: Model372.InputChannel):
        self.input_channels.append(channel)
        if channel != Model372.InputChannel.CONTROL:
            self.scanner_queue.append(channel)

    # starts changing scanner position every scanner_interval
    def start_scanner_cycle(self):
        self.lock.acquire()
        if self.is_cycling:
            self.lock.release()
            return

        if len(self.scanner_queue) < 1:
            print("scanner cycling not necessary")
            self.lock.release()
            return

        self.is_cycling = True
        if self.cycle_is_alive:
            self.lock.release()
            return
        self.lock.release()

        def cycle():
            self.lock.acquire()
            self.cycle_is_alive = True
            while self.is_cycling:
                self.lock.release()
                self.set_next_scanner_position()
                time.sleep(self.scanner_interval)
                self.lock.acquire()
            self.cycle_is_alive = False
            self.lock.release()

        t = Thread(target=cycle, daemon=True)
        print("starting scanner cycle")
        print(self.scanner_queue)
        t.start()

    # stops the scanner cycling
    def stop_scanner_cycle(self):
        self.lock.acquire()
        self.is_cycling = False
        self.lock.release()

    # gets raw readings from device and applies calibration if necessary
    def get_readings(self, input_channel: Model372.InputChannel):
        return self.lakeshore.get_all_input_readings(input_channel.value)

    # sets scanner to next channel in scanner_queue
    def set_next_scanner_position(self):
        if len(self.scanner_queue) and self.connected:
            channel = self.scanner_queue.popleft()
            if self.current_channel == channel:
                self.scanner_queue.append(channel)
                return

            self.lakeshore.set_scanner_status(channel.value, False)
            self.current_channel = channel
            self.scanner_queue.append(channel)

            self.is_ready = False

            def wait_for_ready():
                # TODO: find actual settle time
                time.sleep(1)
                self.is_ready = True

            t = Thread(target=wait_for_ready, daemon=True)
            t.start()

    # configures physical device
    def configure(self, input_channel: Model372.InputChannel, settings: Model372InputSetupSettings):
        self.lakeshore.configure_input(input_channel.value, settings)

    # establishes connection to the physical device
    def connect(self, use_usb=False, use_ip=False):
        print("connecting to lakeshore ...")
        self.lock.acquire(blocking=True)
        if self.lakeshore is not None:
            print("already connected")
            self.lock.release()
            return

        if LakeshoreDevice.DEBUG_MODE:
            self.lakeshore = Model372Mock(baud_rate=None)
            self.connected = True
            print("connection successful")
            self.lock.release()
            return

        if use_usb == use_ip:
            use_usb = True
            use_ip = False

        if use_usb:
            try:
                self.lakeshore = Model372(baud_rate=self.baud_rate)
            except:
                print("couldn't connect to lakeshore using usb\n"
                      "trying again ...")
                try:
                    self.lakeshore = Model372(baud_rate=self.baud_rate)
                except:
                    print("still couldn't connect to lakeshore using usb\n"
                          "aborting process")
                    self.connected = False
                    self.lock.release()
                    return
        elif use_ip:
            try:
                self.lakeshore = Model372(baud_rate=None, ip_address=self.ip_address)
            except:
                print("couldn't connect to lakeshore using ethernet\n"
                      "trying again ...")
                try:
                    self.lakeshore = Model372(baud_rate=None, ip_address=self.ip_address)
                except:
                    print("still couldn't connect to lakeshore using ethernet\n"
                          "aborting process")
                    self.connected = False
                    self.lock.release()
                    return
        self.connected = True
        print("connection successful")
        self.lock.release()

    @staticmethod
    def get_card(gui_setup, data=None):
        print("getting card")
        return LakeshoreCard(gui_setup, data if data is not None else {})

    @staticmethod
    def get_device(id: int):
        if id not in LakeshoreDevice.Devices:
            LakeshoreDevice.Devices[id] = LakeshoreDevice()

        return LakeshoreDevice.Devices[id]


class LakeshoreCard(DeviceCard):
    NAME = "Lakeshore"
    TYPE = mdType.LAKESHORE

    def __init__(self, gui_setup, data):
        super().__init__(gui_setup, data)

        # self.channel = Model372.InputChannel(data.get("channel", "A"))
        self.use_usb = data.get("use_usb", True)
        self.baud_rate = data.get("baud_rate", 57600)
        self.use_ip = data.get("use_ip", False)
        self.ip = data.get("ip", "192.168.0.12")

        self.channel_forms = []

        if self.use_usb == self.use_ip:
            self.use_usb = True
            self.use_ip = False

        # references for live editing
        self.connection_status = None
        self.reconnect_btn = None
        self.tabs = None

    def get_device_data(self, extra=None):
        data = {"id": self.id, "type": self.type, "name": self.name,
                "use_usb": self.use_usb, "baud_rate": self.baud_rate,
                "use_ip": self.use_ip, "ip": self.ip}
        return data

    def get_slot_data(self, extra=None):
        data = {"id": self.id, "type": self.type, "name": self.name}
        if extra is not None:
            data["channel"] = extra.currentData().value
        return data

    def get_extra(self, slot, selection=None):
        index = selection if selection is not None else 0
        extra = qtw.QComboBox()
        extra.addItem("Channel A", Model372.InputChannel.CONTROL)
        for i in range(1, 5):
            extra.addItem(f"Channel {i}", Model372.InputChannel(i))
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

        connection_mode_holder = qtw.QWidget()
        connection_mode_holder.setLayout(qtw.QHBoxLayout())
        layout.addWidget(connection_mode_holder)

        usb_holder = qtw.QWidget()
        usb_holder.setLayout(qtw.QVBoxLayout())
        connection_mode_holder.layout().addWidget(usb_holder)
        use_usb = qtw.QCheckBox("use usb")
        use_usb.setChecked(self.use_usb)
        usb_holder.layout().addWidget(use_usb)
        baud_rate = qtw.QLineEdit()
        baud_rate.setValidator(qtg.QIntValidator())
        baud_rate.setText(str(self.baud_rate))
        baud_rate.setEnabled(self.use_usb)
        usb_holder.layout().addWidget(baud_rate)

        ip_holder = qtw.QWidget()
        ip_holder.setLayout(qtw.QVBoxLayout())
        connection_mode_holder.layout().addWidget(ip_holder)
        use_ip = qtw.QCheckBox("use ip")
        use_ip.setChecked(self.use_ip)
        ip_holder.layout().addWidget(use_ip)
        ip_address = qtw.QLineEdit()
        ip_address.setInputMask("000.000.0.00;_")
        ip_address.setText(self.ip)
        ip_address.setEnabled(self.use_ip)
        ip_holder.layout().addWidget(ip_address)

        def connection_mode_change(usb_toggled = False, ip_toggled = False):
            if usb_toggled:
                baud_rate.setEnabled(use_usb.isChecked())
                ip_address.setDisabled(use_usb.isChecked())
                use_ip.setChecked(not use_usb.isChecked())
            elif ip_toggled:
                baud_rate.setDisabled(use_ip.isChecked())
                use_usb.setChecked(not use_ip.isChecked())
                ip_address.setEnabled(use_ip.isChecked())

        use_usb.stateChanged.connect(lambda: connection_mode_change(usb_toggled=True))
        use_ip.stateChanged.connect(lambda: connection_mode_change(ip_toggled=True))

        connection_mode_holder.layout().addStretch()
        form_layout.addRow(connection_mode_holder)

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

        for ch in range(5):
            channel_holder = qtw.QWidget()
            form_layout = qtw.QFormLayout()
            channel_holder.setLayout(form_layout)
            tabs.addTab(channel_holder, f"Ch_{'A' if ch == 0 else ch}")
            channel_form = {"channel": "A" if ch == 0 else ch}

            if ch != 0:  # is not Control Channel
                excitation_mode = qtw.QComboBox()
                excitation_mode.addItem("current", Model372.SensorExcitationMode.CURRENT)
                excitation_mode.addItem("voltage", Model372.SensorExcitationMode.VOLTAGE)
                form_layout.addRow("Excitation Mode:", excitation_mode)
                channel_form["excitation_mode"] = excitation_mode

            excitation_range = qtw.QComboBox()
            for x in Model372.MeasurementInputCurrentRange:
                excitation_range.addItem(range_text_converter(x.name), x)
            form_layout.addRow("Excitation Range:", excitation_range)
            channel_form["excitation_range"] = excitation_range

            auto_range = qtw.QCheckBox()
            auto_range.setStyleSheet("QCheckBox::indicator { width:20px; height: 20px;}")
            form_layout.addRow("Auto Range:", auto_range)
            channel_form["auto_range"] = auto_range

            if ch != 0:
                resistance_range = qtw.QComboBox()
                for x in Model372.MeasurementInputResistance:
                    resistance_range.addItem(range_text_converter(x.name), x)
                resistance_range.setCurrentIndex(9)  # MeasurementInputResistance.RANGE_63_POINT_2_KIL_OHMS
                form_layout.addRow("Resistance Range:", resistance_range)
                channel_form["resistance_range"] = resistance_range

                def on_excitation_mode_changed(value=0, _excitation_range=None):
                    if _excitation_range is None:
                        return

                    _excitation_range.clear()
                    if value == 0:
                        for x in Model372.MeasurementInputCurrentRange:
                            _excitation_range.addItem(range_text_converter(x.name), x)
                        _excitation_range.setCurrentIndex(16)  # MeasurementInputCurrentRange.RANGE_100_MICRO_AMPS
                    else:  # voltage TODO: sensible default value
                        for x in Model372.MeasurementInputVoltageRange:
                            _excitation_range.addItem(range_text_converter(x.name), x)
                        _excitation_range.setCurrentIndex(0)

                excitation_mode.currentIndexChanged.connect(lambda x, y=excitation_range: on_excitation_mode_changed(x, y))

            use_filter = qtw.QCheckBox()
            use_filter.setStyleSheet("QCheckBox::indicator { width:20px; height: 20px;}")
            use_filter.setChecked(True)
            form_layout.addRow("use filter: ", use_filter)
            channel_form["use_filter"] = use_filter

            settle_time = qtw.QSpinBox()
            settle_time.setRange(1, 200)
            settle_time.setValue(5)
            settle_time.setSuffix("s")
            settle_time.setButtonSymbols(qtw.QAbstractSpinBox.ButtonSymbols.NoButtons)
            form_layout.addRow("settle time (1-200s): ", settle_time)
            channel_form["settle_time"] = settle_time

            window = qtw.QSpinBox()
            window.setRange(1, 80)
            window.setValue(10)
            window.setSuffix("%")
            window.setButtonSymbols(qtw.QAbstractSpinBox.ButtonSymbols.NoButtons)
            form_layout.addRow("window (1-80%): ", window)
            channel_form["window"] = window

            def use_filter_changed(is_checked, _settle_time, _window):
                _settle_time.setEnabled(is_checked)
                _window.setEnabled(is_checked)

            use_filter.stateChanged.connect(lambda a, b=settle_time, c=window: use_filter_changed(a, b, c))

            self.channel_forms.append(channel_form)

        # Connect to Lakeshore async
        def update_display():
            lakeshore = LakeshoreDevice(baud_rate=int(baud_rate.text()) if baud_rate.text().isdigit() else 0,
                                        ip_address=ip_address.text())
            lakeshore.connect(use_usb.isChecked(), use_ip.isChecked())
            if not lakeshore.connected:
                self.connection_status.setText("● Not Connected")
                self.connection_status.setStyleSheet("color: red")
                self.connection_status.setFont(ds.FONT)
                self.reconnect_btn.show()
                return

            self.tabs.show()
            self.connection_status.setText("● Connected")
            self.connection_status.setStyleSheet("color: green")
            self.connection_status.setFont(ds.FONT)

        t = Thread(daemon=True, target=update_display)
        t.start()

        # Bottom Buttons
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
            self.use_usb = use_usb.isChecked()
            self.baud_rate = baud_rate.text()
            self.use_ip = use_ip.isChecked()
            self.ip = ip_address.text()
            self.gui_setup.update_slots()
            self.gui_setup.save_setup_settings()
            # dlg.close()

        apply_btn.clicked.connect(apply_changes)

        dlg.exec()


if __name__ == "__main__":
    device = LakeshoreDevice([Model372.InputChannel.CONTROL, Model372.InputChannel.ONE, Model372.InputChannel.TEN])
    print(device.lakeshore.get_scanner_status())
    device.set_next_scanner_position()
    print(device.lakeshore.get_scanner_status())
    device.set_next_scanner_position()
    print(device.lakeshore.get_scanner_status())
