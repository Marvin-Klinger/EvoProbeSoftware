import datetime
import time

import numpy as np

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
        self.logging_progress = [0] * (len(measurement_devices)+1)
        self.last_readings = [None] * (len(measurement_devices)+1)
        self.initialize_files()

        self.graph = LiveGraph(dfs=self.dfs, x_axis="timedelta")

    def initialize_files(self):
        # File Management
        self.save_path = os.path.join(self.save_path, str(datetime.date.today()))
        count = 1
        while os.path.exists(self.save_path + "_" + str(count)):
            count += 1
        self.save_path = self. save_path + "_" + str(count)
        os.mkdir(self.save_path)
        # TODO: is timestamp necessary/sensible?
        columns = ["timedelta"]
        for i, d in enumerate(self.measurement_devices):
            columns += [f"{i+1}_{keys}" for keys in d.logging_keys]
        master_df = pd.DataFrame(columns=columns)
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
        for i, device in enumerate(self.measurement_devices):
            device.start_logging(self, i+1, self.start_time)

    # adds new row to df and propagate to other classes (graph)
    def update_df(self, data, logging_id):
        # self.graph_queue.put([QueueItemType.DATA, data])
        df = self.dfs[logging_id]
        df.loc[len(df)] = data
        with open(os.path.join(self.save_path, self.save_path_extensions[logging_id]), "a") as file:
            file.write(",".join([str(i) for i in data]) + "\n")
        self.graph.update_default(logging_id)

        while data[1] >= self.logging_progress[logging_id]*self.intervall:
            new_reading = []
            last_reading = self.last_readings[logging_id]
            if last_reading is None:
                new_reading = [np.nan] * (len(data)-2)
            else:
                t0, t1, t2 = self.logging_progress[logging_id]*self.intervall, last_reading[1], data[1]
                old_x, new_x = (t2-t0)/(t2-t1), (t0-t1)/(t2-t1)
                for i in range(2, len(data)):
                    new_reading.append(last_reading[i]*old_x + data[i]*new_x)
            master_df = self.dfs[0]
            columns = [f"{logging_id}_{key}" for key in df.columns[2:]]
            row = self.logging_progress[logging_id]
            if row >= len(master_df):
                master_df.loc[row, "timedelta"] = row * self.intervall
            master_df.loc[row, columns] = new_reading

            self.logging_progress[logging_id] += 1

            if min(self.logging_progress[1:]) > self.logging_progress[0]:
                with open(os.path.join(self.save_path, self.save_path_extensions[0]), "a") as file:
                    file.write(",".join([str(i) for i in master_df.loc[row]]) + "\n")
                self.logging_progress[0] += 1
                print(list(master_df.loc[row]))

        self.last_readings[logging_id] = data
