from enum import Enum
from threading import Thread
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5.QtCore import Qt
import DefaultSettings as ds
from ExtraClasses import MeasurementDeviceType as mdType


class MeasurementDevice:

    # LOGGING_KEYS =

    def __init__(self):
        self.last_values = {}
        self.info = None
        self.calibration = None
        self.keys = []
        self.logging_keys = []
        self.plotting_keys = []
        self.connected = False

    # gets raw readings from device and applies calibration if necessary
    def get_readings(self):
        return {}

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
        pass

    # connects to the devices asynchronously to not freeze the GUI
    def connect_async(self):
        t = Thread(target=self.connect, daemon=True)
        t.start()

    @staticmethod
    def get_card(gui_setup, data=None):
        print("getting card")
        return DeviceCard(gui_setup, data if data is not None else {})


# Used to display added MeasurementDevice info and options
class DeviceCard(qtw.QFrame):
    NAME = "Dummy"
    TYPE = mdType.DUMMY

    running_index = 0

    def __init__(self, gui_setup, data):
        super().__init__()

        self.gui_setup = gui_setup
        self.id = DeviceCard.running_index
        DeviceCard.running_index += 1
        self.gui_elements = {}

        self.type = self.TYPE
        self.name = data.get("name", self.NAME)

        self.setLayout(qtw.QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.setFrameStyle(qtw.QFrame.StyledPanel | qtw.QFrame.Plain)
        self.setLineWidth(3)

        topbar = qtw.QWidget()
        topbar.setLayout(qtw.QHBoxLayout())
        topbar.layout().setContentsMargins(0, 0, 0, 0)
        topbar.layout().setSpacing(0)
        self.layout().addWidget(topbar)

        btn_size = (30, 30)
        info_btn = qtw.QPushButton("i")
        info_btn.setFixedSize(*btn_size)
        info_btn.setContentsMargins(0, 0, 0, 0)
        topbar.layout().addWidget(info_btn)
        topbar.layout().addStretch()
        edit_btn = qtw.QPushButton("Ξ")
        edit_btn.setFixedSize(*btn_size)
        edit_btn.setContentsMargins(0, 0, 0, 0)
        edit_btn.clicked.connect(self.open_edit_window)
        topbar.layout().addWidget(edit_btn)
        remove_btn = qtw.QPushButton("⨉")
        remove_btn.setFixedSize(*btn_size)
        remove_btn.setContentsMargins(0, 0, 0, 0)
        remove_btn.clicked.connect(lambda: self.gui_setup.remove_device(self))
        topbar.layout().addWidget(remove_btn)

        name_label = qtw.QLabel(self.name)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setFont(qtg.QFont("Bahnschrift", 26))
        name_label.setContentsMargins(20, 0, 20, 10)
        self.layout().addWidget(name_label)
        self.gui_elements["name"] = name_label

    def get_data(self, extra=None):
        return {"id": self.id, "type": self.type, "name": self.name}

    def get_extra(self, slot, selection=None):
        return qtw.QWidget()

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

