import sys

from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5.QtCore import Qt

from src.GuiSequence import GuiSequence
from src.GuiSequenceSelect import GuiSequenceSelect
from src.GuiSetup import GuiSetup


class GuiMain(qtw.QMainWindow):

    def __init__(self):
        super().__init__()

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
        window = GuiSequence(self, None, [])
        self.setCentralWidget(window)
        self.setWindowTitle("Sequence")


# starts the MainWindow for the rest of the windows
def show_gui():
    app = qtw.QApplication(sys.argv)
    gui = GuiMain()
    app.exec_()


# just for testing ui
if __name__ == "__main__":
    show_gui()
