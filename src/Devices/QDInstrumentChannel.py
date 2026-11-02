from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5.QtCore import Qt

from src.ExtraClasses import MeasurementDeviceType as mdType, DeviceInfo
from src.Devices.MeasurementDevice import MeasurementDevice
from src.Devices.QDInstrumentAPI import BridgeChannel, BridgeConfig, CalibrationMode, DriveMode
from src.Devices.QDInstrumentDevice import QDInstrumentDevice
import src.DefaultSettings as ds
from src.Gui.GuiThread import GuiThread


class QDInstrumentChannel(MeasurementDevice):

    KEYS = ["current", "resistance", "temperature"]
    UNITS = ["A", "Ω", "K"]
    CALIBRATION_MAPPING = {"resistance": "temperature"}
    DEFAULT_PLOT_KEYS = [True, False, True]

    def __init__(self, data, settings=None):
        super().__init__(data, settings)
        self.bridge_channel = BridgeChannel(data["channel"])
        self.qd_instrument = QDInstrumentDevice.get_device()

        self.last_values = {}
        self.info = DeviceInfo(name=f"Bridge {self.bridge_channel}", version=0)
        key_bool_map = [True, True, self.calibration is not None]
        self.keys = [key for key, use in zip(QDInstrumentChannel.KEYS, key_bool_map) if use]
        self.units = [unit for unit, use in zip(QDInstrumentChannel.UNITS, key_bool_map) if use]
        self.logging_keys = [f"{key[:3]}_{self.bridge_channel}" for key in self.keys]
        self.default_plot_keys = [state for state, use in zip(QDInstrumentChannel.DEFAULT_PLOT_KEYS, key_bool_map) if use]
        self.calibration_mapping = QDInstrumentChannel.CALIBRATION_MAPPING

    # gets raw readings from device
    def get_readings(self):
        return self.qd_instrument.get_channel_readings(self.bridge_channel)

    # configures physical device
    def configure(self, settings: BridgeConfig):
        self.qd_instrument.set_bridge_config(self.bridge_channel, settings)

    # establishes connection to the physical device
    def connect(self):
        self.qd_instrument.connect()
        self.connected = self.qd_instrument.connected

    # starts routines necessary for measuring data
    def start_reading(self):
        pass

    # stops routines necessary for measuring data
    def stop_reading(self):
        pass

    # returns the widget used for settings in GuiActive and its name
    def get_settings_tab(self):
        print("getting tab")
        # Settings
        channel_holder = qtw.QWidget()
        channel_holder.setFont(ds.FONT)
        form_layout = qtw.QFormLayout()
        channel_holder.setLayout(form_layout)

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

        # Settings
        current_limit = qtw.QLineEdit()
        current_limit.setValidator(qtg.QDoubleValidator())
        current_limit.setText("0")
        form_layout.addRow("Current Limit ", current_limit)

        power_limit = qtw.QLineEdit()
        power_limit.setValidator(qtg.QDoubleValidator())
        power_limit.setText("0")
        form_layout.addRow("Power Limit ", power_limit)

        voltage_limit = qtw.QLineEdit()
        voltage_limit.setValidator(qtg.QDoubleValidator())
        voltage_limit.setText("0")
        form_layout.addRow("Voltage Limit ", voltage_limit)

        calibration_mode = qtw.QComboBox()
        calibration_mode.addItem("Standard", CalibrationMode.STANDARD)
        calibration_mode.addItem("Fast", CalibrationMode.FAST)
        calibration_mode.addItem("Hi-Res", CalibrationMode.HI_RES)
        form_layout.addRow("Calibration Mode ", calibration_mode)
        calibration_mode_label = form_layout.labelForField(calibration_mode)
        calibration_mode_label.hide()
        calibration_mode.hide()

        drive_mode = qtw.QComboBox()
        drive_mode.addItem("AC", DriveMode.AC)
        drive_mode.addItem("DC", DriveMode.DC)
        form_layout.addRow("Drive Mode ", drive_mode)
        drive_mode_label = form_layout.labelForField(drive_mode)
        drive_mode_label.hide()
        drive_mode.hide()

        def update_display():
            if not self.qd_instrument.connected:
                connection_status.setText("● Not Connected")
                connection_status.setStyleSheet("color: red")
                connection_status.setFont(ds.FONT)
                reconnect_btn.show()
                return

            connection_status.setText("● Connected")
            connection_status.setStyleSheet("color: green")
            connection_status.setFont(ds.FONT)
            # self.reconnect_btn.show()

            config = self.qd_instrument.get_bridge_config(self.bridge_channel)
            if not config:
                return

            current_limit.setText(str(config.current_limit))
            power_limit.setText(str(config.power_limit))
            voltage_limit.setText(str(config.voltage_limit))
            if self.qd_instrument.type == mdType.PPMS6000:
                calibration_mode.setCurrentIndex(config.calibration_mode)
                calibration_mode_label.show()
                calibration_mode.show()
                drive_mode.setCurrentIndex(config.drive_mode)
                drive_mode_label.show()
                drive_mode.show()
            else:
                calibration_mode_label.hide()
                calibration_mode.hide()
                drive_mode_label.hide()
                drive_mode.hide()

        # t = GuiThread(target=self.connect)
        # t.start()
        # t.finished.connect(update_display)

        def reconnect():
            connection_status.setText("● connecting...")
            connection_status.setStyleSheet("color: orange")
            connection_status.setFont(ds.FONT)
            reconnect_btn.hide()
            t = GuiThread(target=self.connect)
            t.start()
            t.finished.connect(update_display)

        reconnect_btn.clicked.connect(reconnect)

        btn_holder = qtw.QWidget()
        btn_holder.setLayout(qtw.QHBoxLayout())
        btn_holder.setContentsMargins(0, 10, 0, 0)
        form_layout.addWidget(btn_holder)
        btn_holder.layout().addStretch()
        apply_btn = qtw.QPushButton("Apply")
        btn_holder.layout().addWidget(apply_btn)

        def apply_changes():
            self.qd_instrument.set_bridge_config(self.bridge_channel, BridgeConfig(
                float(current_limit.text()),
                float(voltage_limit.text()),
                float(power_limit.text()),
                calibration_mode.currentData(),
                drive_mode.currentData()
            ))

        apply_btn.clicked.connect(apply_changes)

        return channel_holder, f"QDI_{self.bridge_channel}"
