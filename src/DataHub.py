from DataReader import DataReader
from LiveGraph import LiveGraph, QueueItemType, Operations
from MeasurementDevice import MeasurementDevice
import pandas as pd
from multiprocessing import Process, Queue


class DataHub:

    def __init__(self, measurement_devices: list[MeasurementDevice], save_path, controller):
        self.measurement_devices = measurement_devices
        self.save_path = save_path
        self.controller = controller

        columns = ["timestamp", "timedelta"]
        for device in self.measurement_devices:
            columns += device.logging_keys
        self.df = pd.DataFrame(columns=columns)

        self.reader = DataReader(datahub=self,
                                 measurement_devices=self.measurement_devices,
                                 interval=2)

        self.graph_queue = Queue()
        plotting_keys = []
        for device in self.measurement_devices:
            plotting_keys += device.plotting_keys
        self.graph = LiveGraph(queue=self.graph_queue,
                               df=self.df,
                               x_axis="timedelta",
                               y_axis=plotting_keys)

    # starts the logging process and graph
    def start_logging(self):
        self.reader.start()
        self.graph.start()

    # adds new row to df and propagate to other classes (graph)
    def update_df(self, data):
        self.graph_queue.put([QueueItemType.DATA, data])
        self.df.loc[len(self.df)] = data
        with open(self.save_path, "a") as file:
            file.write(",".join([str(i) for i in data]) + "\n")
        print(data)

