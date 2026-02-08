import sys
import os

from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5.QtCore import Qt

from src.GuiSequence import GuiSequence
from src.GuiSequenceSelect import GuiSequenceSelect
from src.GuiSetup import GuiSetup
from src.GuiActive import GuiActive
from src.MPVWrapper import MPVWrapper
import src.FileHandler as FileHandler


class GuiMain(qtw.QMainWindow):

    def __init__(self, controller):
        super().__init__()
        self.controller = controller

        self.setFont(qtg.QFont("Bahnschrift", 16))
        self.setGeometry(600, 200, 400, 0)
        self.setCentralWidget(qtw.QLabel("Hi"))
        self.load_sequence_select_window()
        self.show()

    def load_sequence_select_window(self):
        window = GuiSequenceSelect(self)
        self.setCentralWidget(window)
        self.setWindowTitle("Sequences")

    def load_setup_window(self):
        window = GuiSetup(self)
        self.setCentralWidget(window)
        self.setWindowTitle("Setup")

    def load_sequence_window(self):
        self.controller.instantiate_devices()
        window = GuiSequence(self, None, self.controller.devices)
        self.setCentralWidget(window)
        self.setWindowTitle("Sequence")

    def load_active_window(self):
        user_data = FileHandler.get_user_data_json()
        path = user_data.get("save_path", "")
        if not os.path.exists(os.path.dirname(path)):
            path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "default.csv"))
        save_path = qtw.QFileDialog.getSaveFileName(self, "Save", path)[0]
        if save_path == "":
            return

        user_data["save_path"] = save_path
        FileHandler.save_user_data_json(user_data)
        self.controller.start_sequence(save_path)
        window = GuiActive(self, self.controller)
        self.setCentralWidget(window)
        self.setWindowTitle("Running")

