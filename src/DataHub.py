import datetime
import time

from DataReader import DataReader
from LiveGraph import LiveGraph, QueueItemType, Operations
from MeasurementDevice import MeasurementDevice
import pandas as pd
from multiprocessing import Process, Queue
import os


class DataHub:

    def __init__(self, measurement_devices: list[MeasurementDevice], save_path, controller):
        self.measurement_devices = measurement_devices
        self.controller = controller
        self.save_path = os.path.dirname(save_path)
        self.save_path_extensions = [os.path.basename(save_path)]
        self.start_time = None
        self.intervall = 2

        self.dfs = []
        self.initialize_files()

        self.graph_queue = Queue()
        plotting_keys = self.dfs[0].columns[2:]
        self.graph = LiveGraph(queue=self.graph_queue,
                               df=self.dfs[0],
                               x_axis="timedelta",
                               y_axis=plotting_keys)

    def initialize_files(self):
        # File Management
        self.save_path = os.path.join(self.save_path, str(datetime.date.today()))
        count = 1
        while os.path.exists(self.save_path + "_" + str(count)):
            count += 1
        self.save_path = self. save_path + "_" + str(count)
        os.mkdir(self.save_path)
        master_df = pd.DataFrame(columns=["timestamp", "timedelta"] +
                                         [f"{i+1}_{d.logging_keys}" for i, d in enumerate(self.measurement_devices)])
        self.dfs.append(master_df)
        master_df.to_csv(os.path.join(self.save_path, self.save_path_extensions[0]), encoding="utf-8", index=False)

        os.mkdir(os.path.join(self.save_path, "raw"))
        for i, device in enumerate(self.measurement_devices):
            self.save_path_extensions.append(os.path.join("raw", f"{i+1}-{device.name}.csv"))
            raw_df = pd.DataFrame(columns=["timestamp", "timedelta"] + device.logging_keys)
            self.dfs.append(raw_df)
            raw_df.to_csv(os.path.join(self.save_path, self.save_path_extensions[i+1]), encoding="utf-8", index=False)

    # starts the logging process and graph
    def start_logging(self):
        self.start_time = time.monotonic()
        self.graph.start()
        for device in self.measurement_devices:
            device.start_logging(self)

    # adds new row to df and propagate to other classes (graph)
    def update_df(self, data):
        self.graph_queue.put([QueueItemType.DATA, data])
        self.df.loc[len(self.df)] = data
        with open(self.save_path, "a") as file:
            file.write(",".join([str(i) for i in data]) + "\n")
        print(data)

