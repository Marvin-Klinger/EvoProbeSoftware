from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5.QtCore import Qt

from lakeshore import Model372
from itertools import chain

import DefaultSettings as ds
from src.ExtraClasses import MeasurementDeviceType as mdType
import src.FileHandler as FileHandler
from MeasurementDevice import MeasurementDevice
from LakeshoreDevice import LakeshoreDevice


class GuiSetup(qtw.QWidget):

    DEVICES = {
        mdType.DUMMY: MeasurementDevice,
        mdType.LAKESHORE: LakeshoreDevice
    }

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.pause_saving = False

        self.setFont(ds.FONT)
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

        pucks = [ds.PUCK_SETTINGS] + FileHandler.get_pucks()
        self.puck_select = qtw.QComboBox()
        for i, puck in enumerate(pucks):
            self.puck_select.addItem(puck["id"], i)
        try:
            index = [puck["id"] for puck in pucks].index(setup_json["puck"])
        except (ValueError, KeyError):
            index = 0
        self.puck_select.setCurrentIndex(index)
        serial_form.addRow(" Puck ", self.puck_select)

        rod_select = qtw.QComboBox()
        rod_select.addItem("Rod 1")
        rod_select.addItem("Rod 2")
        serial_form.addRow(" Rod ", rod_select)

        serial_holder.setFixedWidth(serial_holder.sizeHint().width() + 20)

        # Control Device Section
        # control_holder = qtw.QWidget()
        # control_form = qtw.QFormLayout()
        # control_holder.setLayout(control_form)
        # self.layout().addWidget(control_holder)
        #
        # title_control = qtw.QLabel("Control Device")
        # title_control.setFont(qtg.QFont("Bahnschrift", 20))
        # title_control.setContentsMargins(0, 10, 0, 0)
        # control_form.addRow(title_control)
        #
        # control_hbox = qtw.QWidget()
        # control_hbox.setLayout(qtw.QHBoxLayout())
        # control_hbox.layout().setContentsMargins(10, 0, 0, 0)
        # control_form.addRow(control_hbox)
        #
        # ppms_btn = qtw.QPushButton("PPMS")
        # control_hbox.layout().addWidget(ppms_btn)
        # dynacool_btn = qtw.QPushButton("DynaCool")
        # control_hbox.layout().addWidget(dynacool_btn)
        # control_hbox.layout().addStretch()

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

        print("loading cards")
        self.cards = []
        for data in setup_json.get("devices", []):
            card = GuiSetup.DEVICES[mdType(data["type"])].get_card(self, data)
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
        print("loading config section")
        config_holder = qtw.QWidget()
        config_form = qtw.QFormLayout()
        config_holder.setLayout(config_form)
        self.layout().addWidget(config_holder)

        title_config = qtw.QLabel("Config")
        title_config.setFont(qtg.QFont("Bahnschrift", 20))
        title_config.setContentsMargins(0, 10, 0, 0)
        config_form.addRow(title_config)

        n_of_slots = pucks[self.puck_select.currentData()].get("n_of_slots", 1)
        self.slots = []
        self.slot_selections = []

        for i in range(n_of_slots):
            config_form.addRow(f" Slot {i + 1} ", self.create_slot())

        print("updating slots")
        self.update_slots()

        print("slotting")
        self.pause_saving = True
        for i, index in enumerate(setup_json.get("slots", [])):
            print(i, index)
            self.slots[i]["device"].setCurrentIndex(index)
            self.slot_selections[i]["device"] = self.slots[i]["device"].currentData()
        self.pause_saving = True
        self.update_slots()

        self.layout().addStretch()

        # Method Section (methods that have dependencies from later sections)
        def change_puck(index):
            print(index)
            n_of_slots = pucks[index].get("n_of_slots", 1)
            for i in range(len(self.slots) - n_of_slots):
                slot = self.slots.pop()
                self.slot_selections.pop()
                label = config_form.labelForField(slot["row"])
                label.hide()
                label.deleteLater()
                slot["row"].hide()
                slot["row"].deleteLater()

            for i in range(len(self.slots), n_of_slots):
                config_form.addRow(f" Slot {i + 1} ", self.create_slot())

            self.update_slots()
            self.save_setup_settings()

        self.puck_select.currentIndexChanged.connect(change_puck)

    def create_slot(self):
        row = qtw.QWidget()
        grid_layout = qtw.QGridLayout()
        row.setLayout(grid_layout)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        device = qtw.QComboBox()
        print(device.sizeAdjustPolicy())
        device.setSizeAdjustPolicy(qtw.QComboBox.SizeAdjustPolicy.AdjustToContents)

        def on_change(slot):
            row, device, extra = self.slots[slot]["row"], self.slots[slot]["device"], self.slots[slot]["extra"]
            if self.slot_selections[slot]["device"] != device.currentData():
                self.slot_selections[slot]["extra"] = None
            self.slot_selections[slot]["device"] = device.currentData()
            extra.hide()
            extra.deleteLater()
            try:
                extra = device.currentData().get_extra(slot, self.slot_selections[slot]["extra"])
            except AttributeError:
                extra = qtw.QWidget()
            grid_layout.addWidget(extra, 0, 1)
            self.slots[slot]["extra"] = extra
            self.save_setup_settings()

        device.currentIndexChanged.connect(lambda x, y=len(self.slots): on_change(y))
        grid_layout.addWidget(device, 0, 0)
        extra = qtw.QWidget()
        grid_layout.addWidget(extra, 0, 1)
        grid_layout.setColumnStretch(2, 1)
        self.slots.append({"row": row, "device": device, "extra": extra})
        self.slot_selections.append({"device": None, "extra": None})

        return row

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
        card = GuiSetup.DEVICES[md_type].get_card(self)
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
        dlg.setText(f"Delete {device.name}?")
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
        if self.pause_saving:
            return

        print("saving")
        data = {
            "puck": self.puck_select.currentText(),
            "devices": [card.get_data() for card in self.cards[:-1]],
            "slots": [slot["device"].currentIndex() for slot in self.slots]
        }
        FileHandler.save_setup_json(data)

    def update_slots(self):
        print(self.slot_selections)
        self.pause_saving = True
        options = self.cards[:-1]
        for i, slot in enumerate(self.slots):
            selected_device, selected_extra = self.slot_selections[i]["device"], self.slot_selections[i]["extra"]
            try:
                index = options.index(selected_device)
            except (ValueError, IndexError):
                index = -1

            row, device, extra = slot["row"], slot["device"], slot["extra"]
            device.clear()
            for option in options:
                device.addItem(option.name, option)
            if index != -1:
                self.slot_selections[i]["device"], self.slot_selections[i]["extra"] = selected_device, selected_extra
            device.setCurrentIndex(index)
            device.adjustSize()
        self.pause_saving = False



