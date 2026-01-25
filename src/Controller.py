import sys

from src.GuiMain import GuiMain

from PyQt5 import QtWidgets as qtw


class Controller:

    def __init__(self):
        app = qtw.QApplication(sys.argv)
        self.main_window = GuiMain()
        app.exec_()

    # instantiates measurement_devices from data in setup.json
    def instantiate_devices(self):
        pass

