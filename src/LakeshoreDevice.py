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

from collections import deque
from threading import Thread, Lock
from itertools import chain


class LakeshoreDevice:

    IP_ADDRESS = "192.168.0.12"
    DEBUG_MODE = True

    def __init__(self, input_channels: list[Model372.InputChannel], scanner_interval = 5):

        self.lakeshore: Model372 = None
        self.input_channels = input_channels
        self.scanner_queue = deque()
        self.scanner_interval = scanner_interval
        self.current_channel = None
        self.is_ready = False
        self.is_cycling = False
        self.connected = False
        self.lock = Lock()

        self.info = None

        self.initialize_async()

    def initialize(self):
        self.connect()
        self.scanner_queue.extend([c for c in self.input_channels if c != Model372.InputChannel.CONTROL])
        self.lock.acquire(blocking=True)
        if len(self.scanner_queue) and self.connected:
            self.set_next_scanner_position()
        self.lock.release()

    # initializes the lakeshore asynchronously to not freeze the GUI
    def initialize_async(self):
        t = Thread(target=self.initialize, daemon=True)
        t.start()

    # starts changing scanner position every scanner_interval
    def start_scanner_cycle(self):
        if len(self.scanner_queue) < 2:
            print("scanner cycling not necessary")
            return

        self.is_cycling = True

        def cycle():
            while self.is_cycling:
                time.sleep(self.scanner_interval)
                self.set_next_scanner_position()

        t = Thread(target=cycle, daemon=True)
        t.start()

    # stops the scanner cycling
    def stop_scanner_cycle(self):
        self.is_cycling = False

    # gets raw readings from device and applies calibration if necessary
    def get_readings(self, input_channel: Model372.InputChannel):
        return self.lakeshore.get_all_input_readings(input_channel.value)

    # sets scanner to next channel in scanner_queue
    def set_next_scanner_position(self):
        if len(self.scanner_queue):
            channel = self.scanner_queue.popleft()
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
    def connect(self):
        print("connecting to lakeshore ...")
        self.lock.acquire(blocking=True)
        if self.lakeshore is not None:
            self.lock.release()
            return

        if LakeshoreDevice.DEBUG_MODE:
            self.lakeshore = Model372Mock(baud_rate=None)
            self.connected = True
            print("connection successful")
            self.lock.release()
            return

        try:
            self.lakeshore = Model372(baud_rate=None, ip_address=LakeshoreDevice.IP_ADDRESS)
        except:
            print("couldn't connect to lakeshore\n"
                  "trying again ...")
            try:
                self.lakeshore = Model372(baud_rate=None, ip_address=LakeshoreDevice.IP_ADDRESS)
            except:
                print("still couldn't connect to lakeshore\n"
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


class LakeshoreCard(DeviceCard):
    NAME = "Lakeshore"
    TYPE = mdType.LAKESHORE

    def __init__(self, gui_setup, data):
        super().__init__(gui_setup, data)

        self.channel = Model372.InputChannel(data.get("channel", "A"))
        self.ip = data.get("ip", "192.168.0.12")

    def get_data(self, extra=None):
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

        ip_address = qtw.QLineEdit()
        ip_address.setInputMask("000.000.0.00;_")
        ip_address.setText(self.ip)
        form_layout.addRow("ip: ", ip_address)

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
            self.gui_setup.update_slots()
            self.gui_setup.save_setup_settings()
            dlg.close()

        apply_btn.clicked.connect(apply_changes)

        dlg.exec()


if __name__ == "__main__":
    device = LakeshoreDevice([Model372.InputChannel.CONTROL, Model372.InputChannel.ONE, Model372.InputChannel.TEN])
    print(device.lakeshore.get_scanner_status())
    device.set_next_scanner_position()
    print(device.lakeshore.get_scanner_status())
    device.set_next_scanner_position()
    print(device.lakeshore.get_scanner_status())
