import sys

from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5.QtCore import Qt


class GuiSequenceSelect(qtw.QWidget):

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        self.setFont(qtg.QFont("Bahnschrift", 16))
        self.setLayout(qtw.QVBoxLayout())

        # Topbar Section
        topbar_holder = qtw.QWidget()
        topbar_layout = qtw.QHBoxLayout()
        topbar_holder.setLayout(topbar_layout)
        self.layout().addWidget(topbar_holder)

        topbar_layout.addStretch()
        setup_btn = qtw.QPushButton("Setup")
        # setup_btn.setFixedWidth(setup_btn.sizeHint().width())
        setup_btn.clicked.connect(main_window.load_setup_window)
        topbar_layout.addWidget(setup_btn)

        # Sequence Section
        sequence_holder = qtw.QWidget()
        grid_layout = qtw.QGridLayout()
        sequence_holder.setLayout(grid_layout)
        self.layout().addWidget(sequence_holder)

        sequence1 = qtw.QPushButton("Seq1\nΔTemp")
        grid_layout.addWidget(sequence1, 0, 0)
        sequence2 = qtw.QPushButton("Seq2\nΔField")
        grid_layout.addWidget(sequence2, 0, 1)

        self.layout().addStretch()


if __name__ == "__main__":
    app = qtw.QApplication(sys.argv)
    gui = GuiSequenceSelect()
    gui.show()
    app.exec_()
