from enum import Enum
from multiprocessing import Process, Queue
import pandas as pd
import random
import time
import matplotlib.pyplot as plt
from matplotlib import style


class LiveGraph(Process):
    STYLE = "seaborn-v0_8-whitegrid"

    def __init__(self, queue: Queue, df: pd.DataFrame, x_axis: str, y_axis: list[str]):
        super().__init__()
        self.queue = queue
        self.df = df
        self.columns = list(self.df.columns)[2:]
        self.x_axis = x_axis
        self.y_axis = y_axis
        self.fig = None
        self.lines: dict[str, plt.Line2D] = {}
        self.running = False

        self.auto_xlim = True
        self.auto_ylim = False
        self.ylim_values = [0.1, 500]

        # for testing
        self.timestamp = time.monotonic()
        self.timer = 0

    def run(self):
        print("start")
        self.initialize()
        self.running = True
        while self.running:
            self.check_queue()
            self.update()

    def initialize(self):
        style.use(LiveGraph.STYLE)
        self.fig = plt.figure()
        self.fig.canvas.mpl_connect("close_event", self.on_close)
        ax = self.fig.add_subplot(111)
        plt.yscale("log")
        plt.ylim(0.1, 500)
        plt.xlim(0, 10)
        plt.ion()
        for y in list(self.df.columns)[2:]:
            ln, = ax.plot([], [])
            self.lines[y] = ln
            if y not in self.y_axis:
                ln.set_visible(False)
        ax.legend(self.df.columns[2:], loc="upper right", frameon=True, bbox_to_anchor=(1.2, 1))
        plt.tight_layout()
        plt.pause(0.1)

    def on_close(self, event):
        self.running = False

    def check_queue(self):
        while not self.queue.empty():
            item = self.queue.get()
            match item[0]:
                case QueueItemType.DATA:
                    self.add_data(item[1])
                case QueueItemType.OPERATION:
                    self.execute_operation(*item[1:])
                case _:
                    pass

    def add_data(self, data):
        self.df.loc[len(self.df)] = data

    def execute_operation(self, op, content=None):
        match op:
            case Operations.ENABLE_XLIM:
                self.auto_xlim = True
            case Operations.DISABLE_XLIM:
                self.auto_xlim = False
            case Operations.ENABLE_YLIM:
                self.auto_ylim = True
                self.centre_graphs()
            case Operations.DISABLE_YLIM:
                self.auto_ylim = False
            case Operations.CENTRE_GRAPHS:
                self.centre_graphs()
            case Operations.CHANGE_DISPLAYED_GRAPHS:
                self.change_displayed_graphs(content)
            case _:
                pass

    # sets the x/ylim values of the plot according to the min and max values in df
    def centre_graphs(self):
        if self.df.empty:
            return

        x_vals = self.df[self.x_axis]
        plt.xlim(x_vals[0], x_vals[len(x_vals) - 1] + 5)

        y_vals = self.df[self.y_axis].replace(0, 1)
        self.ylim_values = [y_vals.min().min(), y_vals.max().max()]
        plt.ylim(self.ylim_values[0] * 0.9, self.ylim_values[1] * 1.1)

    def change_displayed_graphs(self, graphs):
        self.y_axis = graphs
        for key in self.lines.keys():
            if key in self.y_axis:
                self.lines[key].set_visible(True)
            else:
                self.lines[key].set_visible(False)
        plt.legend(self.df.columns[2:], loc="upper right", frameon=True, bbox_to_anchor=(1.2, 1))

    def update(self):
        if self.df.empty:
            return

        x_vals = self.df[self.x_axis].tolist()
        val_len = len(x_vals)

        for key in self.y_axis:
            y_vals = self.df[key].tolist()[:val_len]
            self.lines[key].set_xdata(x_vals)
            self.lines[key].set_ydata(y_vals)
            if 0 < y_vals[-1] < self.ylim_values[0]:
                self.ylim_values[0] = y_vals[-1]
            if y_vals[-1] > self.ylim_values[1]:
                self.ylim_values[1] = y_vals[-1]

        if self.auto_xlim:
            plt.xlim(x_vals[0], max(10, x_vals[-1]))
        if self.auto_ylim:
            plt.ylim(self.ylim_values[0] * 0.9, self.ylim_values[1] * 1.1)

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

        # used for performance testing
        # temp = time.monotonic()
        # self.timer += temp - self.timestamp
        # if self.timer > 1:
        #     self.timer = 0
        #     print(f"time: {temp - self.timestamp}\nfps: {(temp - self.timestamp) ** -1}")
        # self.timestamp = temp


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
