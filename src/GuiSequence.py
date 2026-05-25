from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5.QtCore import Qt

from src.MeasurementDevice import MeasurementDevice
import time
from threading import Thread
import DefaultSettings as ds


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

        def _back():
            for device in self.devices:
                device.stop_reading()
            self.main_window.load_sequence_select_window()

        back_btn.clicked.connect(_back)
        topbar_layout.addWidget(back_btn)

        topbar_layout.addStretch()

        start_btn = qtw.QPushButton("GO!")
        start_btn.clicked.connect(self.main_window.load_active_window)
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

        title_preview = qtw.QLabel("Preview")
        title_preview.setFont(qtg.QFont("Bahnschrift", 20))
        title_preview.setContentsMargins(0, 10, 0, 0)
        preview_layout.addRow(title_preview)

        devices_holder = qtw.QWidget()
        devices_layout = qtw.QHBoxLayout()
        devices_holder.setLayout(devices_layout)
        preview_layout.addRow(devices_holder)

        for device in self.devices:
            print("previewing device: ", device)
            card = PreviewCard(device, devices_layout)

        self.layout().addStretch()


class PreviewCard:

    def __init__(self, device: MeasurementDevice, parent_layout: qtw.QHBoxLayout):
        self.device = device
        self.parent_layout = parent_layout
        self.is_active = True

        device_holder = qtw.QWidget()
        device_layout = qtw.QFormLayout()
        device_holder.setLayout(device_layout)
        parent_layout.addWidget(device_holder)

        device_name = qtw.QLabel(device.info.name)
        device_layout.addRow(device_name)

        self.reading_displays = {}
        is_connected = self.device.connected
        status = qtw.QLabel("● connected" if is_connected else "● offline")
        status.setStyleSheet(f"color: {'green' if is_connected else 'red'}")
        status.setFont(ds.FONT)
        self.reading_displays["status"] = status
        device_layout.addRow(status)

        for key in device.logging_keys:
            display = qtw.QLabel("-")
            self.reading_displays[key] = display
            device_layout.addRow(f"{key}: ", display)

        t = Thread(daemon=True, target=self.update)
        t.start()

    def update(self):
        while self.is_active:
            try:
                status = self.reading_displays["status"]
                if self.device.connected:
                    status.setText("● connected")
                    status.setStyleSheet(f"color: green")
                else:
                    status.setText("● offline")
                    status.setStyleSheet(f"color: red")

                readings = self.device.get_logging_readings()
                for i, key in enumerate(self.device.logging_keys):
                    self.reading_displays[key].setText(f"{readings[i]:.1f}")
            except RuntimeError:
                self.is_active = False
                return

            time.sleep(3)
