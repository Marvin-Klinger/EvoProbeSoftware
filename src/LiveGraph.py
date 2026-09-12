from datetime import timedelta
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
        self.columns = [list(df.columns)[2:] for df in self.dfs]
        self.x_axis = x_axis
        self.x_axis_list = list(self.dfs[0].columns)
        self.use_custom_x_axis = False
        self.y_axis = self.columns.copy()
        self.legend = None

        self.lines = [{} for i in range(len(self.dfs))]
        self.initialize()

    def initialize(self):
        self.setMinimumSize(400, 400)
        self.setBackground("w")
        style = {"color": "grey", "font-size": "20px"}
        self.setLabel("bottom", self.x_axis, **style)
        self.showGrid(True, True, alpha=0.3)

        self.legend = self.addLegend()
        self.setDownsampling(auto=True)
        self.setClipToView(True)
        color_generator = ColorFactory.make_colorgenerator()
        for i in range(1, len(self.columns)):
            for key in self.columns[i]:
                self.lines[i][key] = self.plot_line([], [], f"{i}-{key}", next(color_generator))

    def plot_line(self, x, y, name, color):
        pen = pg.mkPen(color=color, width=3)
        return self.plot(x, y, name=name, pen=pen)

    # updates line of id using data from dfs
    def update_data(self, id, master_update=False):
        if not self.use_custom_x_axis and not master_update:
            df = self.dfs[id]
            if self.x_axis == "timestamp":
                x = list(df[self.x_axis].map(lambda d: d.timestamp()))
            else:
                x = list(df[self.x_axis])
            for key, line in self.lines[id].items():
                line.setData(x, list(df[key]))

        elif self.use_custom_x_axis and master_update:
            df = self.dfs[0]
            x = list(df[self.x_axis])
            for key, line in self.lines[id].items():
                key = f"{id}-{key}"
                # if self.x_axis == key:
                #     continue
                line.setData(x, list(df[key]))

    def centre_graphs(self):
        pass

    def hide_graphs(self, graphs=False):
        if not graphs:
            for line in chain(*[group.values() for group in self.lines]):
                line.hide()

    def show_graphs(self, graphs=False):
        if not graphs:
            for line in chain(*[group.values() for group in self.lines]):
                line.show()

    # changes the x_axis used to display the graphs and handles whether to use master or individual dfs
    def change_x_axis(self, x_axis):
        print(x_axis)
        self.x_axis = x_axis
        self.use_custom_x_axis = x_axis not in ["timestamp", "timedelta"]
        if x_axis == "timestamp":
            self.setAxisItems({"bottom": pg.DateAxisItem()})
        else:
            self.setAxisItems({"bottom": pg.AxisItem(orientation="bottom")})
        for i in range(1, len(self.dfs)):
            self.update_data(i, master_update=self.use_custom_x_axis)
        style = {"color": "grey", "font-size": "20px"}
        self.setLabel("bottom", x_axis, **style)

    def set_legend_visibility(self, visible=True):
        if visible:
            self.legend.show()
            self.legend.anchor((-0.4, -0.4), (0, 0))
        else:
            self.legend.hide()


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
