from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5.QtCore import Qt

from LiveGraph import Operations, QueueItemType


class GuiActive(qtw.QWidget):

    def __init__(self, main_window, controller):
        super().__init__()
        self.main_window = main_window
        self.controller = controller
        self.datahub = self.controller.datahub if controller else None
        self.graph = self.datahub.graph

        self.setLayout(qtw.QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.setFont(qtg.QFont("Bahnschrift", 16))
        self.tabs = qtw.QTabWidget()
        self.layout().addWidget(self.tabs)

        self.load_sequence_tab()
        self.load_graph_tab()

        self.tabs.setCurrentIndex(1)

    def load_sequence_tab(self):
        tab = qtw.QWidget()
        self.tabs.addTab(tab, "Sequence")

    def load_graph_tab(self):
        tab = qtw.QWidget()
        layout = qtw.QHBoxLayout()
        tab.setLayout(layout)

        # Settings
        settings_holder = qtw.QWidget()
        settings_layout = qtw.QVBoxLayout()
        settings_holder.setLayout(settings_layout)
        layout.addWidget(settings_holder)

        x_axis_label = qtw.QLabel("Select X-Axis:")
        settings_layout.addWidget(x_axis_label)
        x_axis_select = qtw.QComboBox()
        for c in self.graph.x_axis_list:
            x_axis_select.addItem(c, c)
        x_axis_select.setCurrentIndex(self.graph.x_axis_list.index(self.graph.x_axis))
        settings_layout.addWidget(x_axis_select)
        x_axis_select.currentIndexChanged.connect(lambda i: self.graph.change_x_axis(x_axis_select.currentData()))
        settings_layout.addSpacing(10)

        centre_graph = qtw.QPushButton("Centre Graph")
        centre_graph.clicked.connect(lambda: self.graph_queue.put([QueueItemType.OPERATION, Operations.CENTRE_GRAPHS]))
        settings_layout.addWidget(centre_graph)

        visibility_holder = qtw.QWidget()
        visibility_layout = qtw.QHBoxLayout()
        visibility_holder.setLayout(visibility_layout)
        settings_layout.addWidget(visibility_holder)
        show_btn = qtw.QPushButton("Show All")
        visibility_layout.addWidget(show_btn)
        show_btn.clicked.connect(self.graph.show_graphs)
        hide_btn = qtw.QPushButton("Hide All")
        visibility_layout.addWidget(hide_btn)
        hide_btn.clicked.connect(self.graph.hide_graphs)

        settings_layout.addStretch()

        # Graph
        layout.addWidget(self.graph)

        self.tabs.addTab(tab, "Graph")
