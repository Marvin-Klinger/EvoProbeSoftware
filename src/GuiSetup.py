from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5.QtCore import Qt

from lakeshore import Model372
from itertools import chain

from src.ExtraClasses import MeasurementDeviceType as mdType
import src.FileHandler as FileHandler


class GuiSetup(qtw.QWidget):

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        self.setFont(qtg.QFont("Bahnschrift", 16))
        self.setLayout(qtw.QVBoxLayout())
        self.setContentsMargins(0, 0, 0, 0)
        setup_json = FileHandler.get_setup_json()

        # Topbar Section
        topbar_holder = qtw.QWidget()
        topbar_layout = qtw.QHBoxLayout()
        topbar_holder.setLayout(topbar_layout)
        self.layout().addWidget(topbar_holder)

        back_btn = qtw.QPushButton("↩")
        back_btn.clicked.connect(self.main_window.load_sequence_select_window)
        topbar_layout.addWidget(back_btn)
        topbar_layout.addStretch()

        # Serial Section
        serial_holder = qtw.QWidget()
        serial_form = qtw.QFormLayout()
        serial_holder.setLayout(serial_form)
        self.layout().addWidget(serial_holder)

        title_serial = qtw.QLabel("Serial")
        title_serial.setFont(qtg.QFont("Bahnschrift", 20))
        serial_form.addRow(title_serial)

        puck_select = qtw.QComboBox()
        puck_select.addItem("Puck 1")
        puck_select.addItem("Puck 2")
        serial_form.addRow(" Puck ", puck_select)

        rod_select = qtw.QComboBox()
        rod_select.addItem("Rod 1")
        rod_select.addItem("Rod 2")
        serial_form.addRow(" Rod ", rod_select)

        serial_holder.setFixedWidth(serial_holder.sizeHint().width()+20)

        # Control Device Section
        control_holder = qtw.QWidget()
        control_form = qtw.QFormLayout()
        control_holder.setLayout(control_form)
        self.layout().addWidget(control_holder)

        title_control = qtw.QLabel("Control Device")
        title_control.setFont(qtg.QFont("Bahnschrift", 20))
        title_control.setContentsMargins(0, 10, 0, 0)
        control_form.addRow(title_control)

        control_hbox = qtw.QWidget()
        control_hbox.setLayout(qtw.QHBoxLayout())
        control_hbox.layout().setContentsMargins(10, 0, 0, 0)
        control_form.addRow(control_hbox)

        ppms_btn = qtw.QPushButton("PPMS")
        control_hbox.layout().addWidget(ppms_btn)
        dynacool_btn = qtw.QPushButton("DynaCool")
        control_hbox.layout().addWidget(dynacool_btn)
        control_hbox.layout().addStretch()

        # Measurement Device Section
        measurement_holder = qtw.QWidget()
        measurement_form = qtw.QFormLayout()
        measurement_holder.setLayout(measurement_form)
        self.layout().addWidget(measurement_holder)

        title_measurement = qtw.QLabel("Measurement Device")
        title_measurement.setFont(qtg.QFont("Bahnschrift", 20))
        title_measurement.setContentsMargins(0, 10, 0, 0)
        measurement_form.addRow(title_measurement)

        measurement_gbox = qtw.QWidget()
        self.measurement_grid = qtw.QGridLayout()
        measurement_gbox.setLayout(self.measurement_grid)
        measurement_form.addRow(measurement_gbox)
        self.card_count = 0
        self.measurement_grid.setColumnStretch(4, 1)

        self.cards = []
        for data in setup_json.get("devices", []):
            card = DeviceCard(data, self)
            self.measurement_grid.addWidget(card, self.card_count // 4, self.card_count % 4)
            self.cards.append(card)
            self.card_count += 1

        add_btn = qtw.QPushButton("+")
        add_btn.setFont(qtg.QFont("Bahnschrift", 30, ))
        add_btn.setFixedSize(60, 60)
        add_btn.clicked.connect(self.open_add_device)
        self.measurement_grid.addWidget(add_btn, self.card_count // 4, self.card_count % 4)
        self.cards.append(add_btn)
        self.card_count += 1

        # Config Section
        config_holder = qtw.QWidget()
        config_form = qtw.QFormLayout()
        config_holder.setLayout(config_form)
        self.layout().addWidget(config_holder)

        title_config = qtw.QLabel("Config")
        title_config.setFont(qtg.QFont("Bahnschrift", 20))
        title_config.setContentsMargins(0, 10, 0, 0)
        config_form.addRow(title_config)

        self.slots = []

        for i in range(1, 4):
            slot = qtw.QComboBox()
            slot.currentIndexChanged.connect(self.save_setup_settings)
            config_form.addRow(f" Slot {i} ", slot)
            self.slots.append(slot)

        self.update_slots()

        print("slotting")
        for i, slot in enumerate(setup_json.get("slots", [])):
            print(i, slot)
            self.slots[i].setCurrentIndex(slot.get("index", -1))

        config_holder.setFixedWidth(300)

        self.layout().addStretch()

    def open_add_device(self):
        dlg = qtw.QDialog(self)
        dlg.setWindowTitle("New")
        dlg.setFont(qtg.QFont("Bahnschrift", 16))
        dlg_layout = qtw.QVBoxLayout()
        dlg.setLayout(dlg_layout)
        for md_type in mdType:
            md_btn = qtw.QPushButton(md_type.name)

            def select_device(t):
                self.add_device(t)
                dlg.close()

            md_btn.clicked.connect(lambda x, y=md_type: select_device(y))
            dlg_layout.addWidget(md_btn)
        dlg.exec()

    def add_device(self, md_type: mdType):
        card = DeviceCard({"type": md_type.value}, self)
        self.card_count -= 1
        self.measurement_grid.addWidget(card, self.card_count // 4, self.card_count % 4)
        self.card_count += 1
        add_btn = self.cards.pop()
        self.cards.append(card)
        self.measurement_grid.addWidget(add_btn, self.card_count // 4, self.card_count % 4)
        self.cards.append(add_btn)
        self.card_count += 1
        self.update_slots()
        self.save_setup_settings()

    def remove_device(self, device: qtw.QFrame):
        dlg = qtw.QMessageBox(self)
        dlg.setFont(qtg.QFont("Bahnschrift", 16))
        dlg.setWindowTitle("delete")
        dlg.setText(f"Delete {device.type.name}?")
        dlg.setStandardButtons(qtw.QMessageBox.Yes | qtw.QMessageBox.No)
        dlg.setIcon(qtw.QMessageBox.Question)
        button = dlg.exec()
        if button != qtw.QMessageBox.Yes:
            return

        device.hide()
        self.card_count = self.cards.index(device)
        self.cards.remove(device)
        for card in self.cards[self.card_count:]:
            self.measurement_grid.addWidget(card, self.card_count // 4, self.card_count % 4)
            self.card_count += 1
        device.deleteLater()
        self.update_slots()
        self.save_setup_settings()

    def save_setup_settings(self):
        print("saving")
        data = {
            "devices": [card.get_data() for card in self.cards[:-1]],
            "slots": [{"index": slot.currentIndex(), "data": slot.currentData()} for slot in self.slots]
        }
        print(data)
        FileHandler.save_setup_json(data)

    def open_edit_device(self, device):
        pass

    def update_slots(self):
        options = list(chain(*[card.get_channels() for card in self.cards[:-1]]))
        for slot in self.slots:
            # index = slot.currentIndex()
            slot.clear()
            for option in options:
                slot.addItem(option["name"], option)
            slot.setCurrentIndex(-1)


# Used to display added MeasurementDevice info and options
class DeviceCard(qtw.QFrame):

    def __init__(self, data, gui_setup):
        super().__init__()

        self.type = mdType(data["type"])
        self.gui_setup = gui_setup

        # self.setFixedWidth(250)
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
        topbar.layout().addWidget(edit_btn)
        remove_btn = qtw.QPushButton("⨉")
        remove_btn.setFixedSize(*btn_size)
        remove_btn.setContentsMargins(0, 0, 0, 0)
        remove_btn.clicked.connect(lambda: self.gui_setup.remove_device(self))
        topbar.layout().addWidget(remove_btn)

        name = qtw.QLabel(self.type.name)
        name.setAlignment(Qt.AlignCenter)
        name.setFont(qtg.QFont("Bahnschrift", 30))
        name.setContentsMargins(20, 0, 20, 10)
        self.layout().addWidget(name)

    def get_data(self):
        return {
            "type": self.type.value
        }

    def get_channels(self):
        match self.type:
            case mdType.MPV:
                return [{"device": self.type.value, "channel": self.type.value, "name": "Mpv"}]
            case mdType.LAKESHORE:
                return [{"device": self.type.value, "channel": Model372.InputChannel.CONTROL.value, "name": "Channel A"},
                        {"device": self.type.value, "channel": Model372.InputChannel.ONE.value, "name": "Channel 1"},
                        {"device": self.type.value, "channel": Model372.InputChannel.TWO.value, "name": "Channel 2"}]
            case _:
                return []
