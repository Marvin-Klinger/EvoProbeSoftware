from MeasurementDevice import MeasurementDevice, DeviceCard
from threading import Thread
from ExtraClasses import MeasurementDeviceType as mdType
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
import MultiPyVu as mpv
import DefaultSettings as ds
from enum import IntEnum


class PPMS6000(MeasurementDevice):
    LOGGING_KEYS = ["current", "resistance"]

    def __init__(self, data):
        super().__init__(data)
        pass

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

        self.current_limit = data.get("current_limit", 10)
        self.power_limit = data.get("power_limit", 100)
        self.voltage_limit = data.get("voltage_limit", 5)
        self.calibration_mode = data.get("calibration_mode", 0)
        self.drive_mode = data.get("drive_mode", 0)

    def get_device_data(self):
        return {"id": self.id, "type": self.type, "name": self.name,
                "current_limit": self.current_limit, "power_limit": self.power_limit,
                "voltage_limit": self.voltage_limit, "calibration_mode": self.calibration_mode,
                "drive_mode": self.calibration_mode}

    def get_slot_data(self, extra=None):
        data = {"id": self.id, "type": self.type, "name": self.name}
        if extra is not None:
            data["channel"] = extra.currentData().value
        return data

    def get_extra(self, slot, selection=None):
        index = selection if selection is not None else 0
        extra = qtw.QComboBox()
        for i in range(1, 5):
            extra.addItem(f"Channel {i}", BrideChannel(i))
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

        # Settings
        current_limit = qtw.QLineEdit()
        current_limit.setValidator(qtg.QDoubleValidator())
        current_limit.setText(str(self.current_limit))
        form_layout.addRow("Current Limit ", current_limit)

        power_limit = qtw.QLineEdit()
        power_limit.setValidator(qtg.QDoubleValidator())
        power_limit.setText(str(self.power_limit))
        form_layout.addRow("Power Limit ", power_limit)

        voltage_limit = qtw.QLineEdit()
        voltage_limit.setValidator(qtg.QDoubleValidator())
        voltage_limit.setText(str(self.voltage_limit))
        form_layout.addRow("Voltage Limit ", voltage_limit)

        calibration_mode = qtw.QComboBox()
        calibration_mode.addItem("Standard", CalibrationMode.STANDARD)
        calibration_mode.addItem("Fast", CalibrationMode.FAST)
        calibration_mode.addItem("Hi-Res", CalibrationMode.HI_RES)
        calibration_mode.setCurrentIndex(self.calibration_mode)
        form_layout.addRow("Calibration Mode ", calibration_mode)

        drive_mode = qtw.QComboBox()
        drive_mode.addItem("AC", DriveMode.AC)
        drive_mode.addItem("DC", DriveMode.DC)
        drive_mode.setCurrentIndex(self.drive_mode)
        form_layout.addRow("Drive Mode ", drive_mode)

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
            self.current_limit = current_limit.text()
            self.voltage_limit = voltage_limit.text()
            self.power_limit = power_limit.text()
            self.calibration_mode = calibration_mode.currentData()
            self.drive_mode = drive_mode.currentData()

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


class BrideChannel(IntEnum):
    CHANNEL_1 = 1
    CHANNEL_2 = 2
    CHANNEL_3 = 3
    CHANNEL_4 = 4
