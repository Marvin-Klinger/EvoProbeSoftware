from enum import Enum
import pandas as pd
import random
import time
import pyqtgraph as pg
from itertools import chain
from ExtraClasses import ColorFactory


class LiveGraph(pg.PlotWidget):

    def __init__(self, dfs, x_axis):
        super().__init__()
        self.dfs = dfs
        self.columns = [list(self.dfs[0].columns[1:])] + [list(df.columns)[2:] for df in self.dfs[1:]]
        self.x_axis = x_axis
        self.y_axis = self.columns.copy()

        self.lines = [{} for i in range(len(self.dfs))]
        self.initialize_default()

    def initialize_default(self):
        self.setBackground("w")
        style = {"color": "grey", "font-size": "20px"}
        self.setLabel("bottom", "time (s)", **style)
        self.showGrid(True, True, alpha=0.3)
        self.setMinimumSize(400, 400)

        self.addLegend()
        self.setDownsampling(auto=True)
        self.setClipToView(True)
        # TODO: implement actual color/line variety
        color_generator = ColorFactory.make_colorgenerator()
        for i in range(1, len(self.columns)):
            for key in self.columns[i]:
                self.lines[i][key] = self.plot_line([], [], f"{i}-{key}", next(color_generator))

    def plot_line(self, x, y, name, color):
        pen = pg.mkPen(color=color, width=3)
        return self.plot(x, y, name=name, pen=pen)

    # updates line of id using data from dfs
    def update_default(self, id):
        df = self.dfs[id]
        x = list(df[self.x_axis])
        for key, line in self.lines[id].items():
            line.setData(x, list(df[key]))

    # sets the x/ylim values of the plot according to the min and max values in df
    def centre_graphs(self):
        pass

    def change_displayed_graphs(self, graphs):
        pass

    def hide_graphs(self, graphs=False):
        if not graphs:
            for line in chain(*[group.values() for group in self.lines]):
                line.hide()

    def show_graphs(self, graphs=False):
        if not graphs:
            for line in chain(*[group.values() for group in self.lines]):
                line.show()


class QueueItemType(Enum):
    DATA = 0
    OPERATION = 1


class Operations(Enum):
    ENABLE_XLIM = 0
    DISABLE_XLIM = 1
    ENABLE_YLIM = 2
    DISABLE_YLIM = 3
    CENTRE_GRAPHS = 4
    CHANGE_DISPLAYED_GRAPHS = 5
