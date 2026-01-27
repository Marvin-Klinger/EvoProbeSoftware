import sys

from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5.QtCore import Qt

from src.GuiSequence import GuiSequence
from src.GuiSequenceSelect import GuiSequenceSelect
from src.GuiSetup import GuiSetup
from src.MPVWrapper import MPVWrapper


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

    def load_sequence(self):
        self.controller.instantiate_devices()
        window = GuiSequence(self, None, self.controller.devices)
        self.setCentralWidget(window)
        self.setWindowTitle("Sequence")

