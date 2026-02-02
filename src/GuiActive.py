from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5.QtCore import Qt

from LiveGraph import Operations, QueueItemType


class GuiActive(qtw.QWidget):

    def __init__(self, main_window, controller):
        super().__init__()
        self.main_window = main_window
        self.controller = controller
        self.graph_queue = self.controller.datahub.graph_queue if controller else None
        self.graphs = {}

        self.setLayout(qtw.QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.setFont(qtg.QFont("Bahnschrift", 16))
        self.tabs = qtw.QTabWidget()
        self.layout().addWidget(self.tabs)

        self.load_sequence_tab()
        self.load_graph_tab()

    def load_sequence_tab(self):
        tab = qtw.QWidget()
        self.tabs.addTab(tab, "Sequence")

    def load_graph_tab(self):
        tab = qtw.QWidget()
        layout = qtw.QVBoxLayout()
        tab.setLayout(layout)

        auto_xlim = qtw.QCheckBox("Auto adjust X-Axis")
        auto_xlim.setChecked(True)
        layout.addWidget(auto_xlim)

        auto_ylim = qtw.QCheckBox("Auto adjust Y-Axis")
        layout.addWidget(auto_ylim)

        centre_graph = qtw.QPushButton("Centre Graph")
        centre_graph.clicked.connect(lambda: self.graph_queue.put([QueueItemType.OPERATION, Operations.CENTRE_GRAPHS]))
        layout.addWidget(centre_graph)

        def on_change_auto_lim(state: int, axis: str):
            print(f"{axis}-axis is set to {bool(state)}")
            if self.graph_queue is None:
                return

            if axis == "x":
                op = Operations.ENABLE_XLIM if state else Operations.DISABLE_XLIM
            else:
                op = Operations.ENABLE_YLIM if state else Operations.DISABLE_YLIM
            self.graph_queue.put([QueueItemType.OPERATION, op])

        auto_xlim.stateChanged.connect(lambda s, a="x": on_change_auto_lim(s, a))
        auto_ylim.stateChanged.connect(lambda s, a="y": on_change_auto_lim(s, a))

        reading_keys = []
        plotting_keys = []
        for device in (self.controller.devices if self.controller else []):
            reading_keys += device.logging_keys
            plotting_keys += device.plotting_keys

        def on_change_graph(state: int, key: str):
            self.graphs[key] = bool(state)
            print(self.graphs)
            print([x for x in reading_keys if self.graphs[x]])
            if self.graph_queue:
                self.graph_queue.put([QueueItemType.OPERATION, Operations.CHANGE_DISPLAYED_GRAPHS,
                                      [x for x in reading_keys if self.graphs[x]]])

        for col in reading_keys:
            graph = qtw.QCheckBox(col, tab)
            visible = col in plotting_keys
            graph.setChecked(visible)
            self.graphs[col] = visible
            layout.addWidget(graph)
            graph.stateChanged.connect(lambda s, k=col: on_change_graph(s, k))

        self.tabs.addTab(tab, "Graph")
