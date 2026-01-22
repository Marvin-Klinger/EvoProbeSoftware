from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5.QtCore import Qt

from src.MeasurementDevice import MeasurementDevice


class GuiSequence(qtw.QWidget):

    def __init__(self, main_window, sequence, devices: list[MeasurementDevice]):
        super().__init__()
        self.main_window = main_window
        self.sequence = sequence
        self.devices = devices

        self.setFont(qtg.QFont("Bahnschrift", 16))
        self.setLayout(qtw.QVBoxLayout())
        self.setContentsMargins(0, 0, 0, 0)

        # Topbar Section
        topbar_holder = qtw.QWidget()
        topbar_layout = qtw.QHBoxLayout()
        topbar_holder.setLayout(topbar_layout)
        self.layout().addWidget(topbar_holder)

        back_btn = qtw.QPushButton("↩")
        back_btn.clicked.connect(self.main_window.load_sequence_select_window)
        topbar_layout.addWidget(back_btn)

        topbar_layout.addStretch()

        start_btn = qtw.QPushButton("GO!")
        topbar_layout.addWidget(start_btn)

        # Setting Section
        setting_holder = qtw.QWidget()
        setting_layout = qtw.QFormLayout()
        setting_holder.setLayout(setting_layout)
        self.layout().addWidget(setting_holder)

        title_setting = qtw.QLabel("Settings")
        title_setting.setFont(qtg.QFont("Bahnschrift", 20))
        setting_layout.addRow(title_setting)

        sample_edit = qtw.QLineEdit()
        setting_layout.addRow(" Sample ", sample_edit)

        # Preview Section
        preview_holder = qtw.QWidget()
        preview_layout = qtw.QFormLayout()
        preview_holder.setLayout(preview_layout)
        self.layout().addWidget(preview_holder)

        title_preview = qtw.QLabel("Control Device")
        title_preview.setFont(qtg.QFont("Bahnschrift", 20))
        title_preview.setContentsMargins(0, 10, 0, 0)
        preview_layout.addRow(title_preview)

        devices_holder = qtw.QWidget()
        devices_layout = qtw.QHBoxLayout()
        devices_holder.setLayout(devices_layout)
        preview_layout.addRow(devices_holder)

        for device in self.devices:
            print("creating preview")
            device_holder = qtw.QWidget()
            device_layout = qtw.QFormLayout()
            device_holder.setLayout(device_layout)
            devices_layout.addWidget(device_holder)

            device_name = qtw.QLabel(device.info.name)
            device_layout.addRow(device_name)

            print("getting readings")
            readings = device.get_logging_readings()
            print(readings)
            print("got readings")
            for i, key in enumerate(device.logging_keys):
                device_layout.addRow(f"{key}: ", qtw.QLabel(str(readings[i])))

        self.layout().addStretch()

        print("finished")
