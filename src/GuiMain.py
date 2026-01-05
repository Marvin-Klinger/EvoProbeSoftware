import sys

from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5.QtCore import Qt

from src.GuiSequenceSelect import GuiSequenceSelect


class GuiMain(qtw.QMainWindow):

    def __init__(self):
        super().__init__()

        self.setFont(qtg.QFont("Bahnschrift", 16))
        self.setCentralWidget(qtw.QLabel("Hi"))
        self.load_sequence_select_window()
        self.show()

    def load_sequence_select_window(self):
        window = GuiSequenceSelect()
        self.setCentralWidget(window)


# starts the MainWindow for the rest of the windows
def show_gui():
    app = qtw.QApplication(sys.argv)
    gui = GuiMain()
    app.exec_()


# just for testing ui
if __name__ == "__main__":
    show_gui()
