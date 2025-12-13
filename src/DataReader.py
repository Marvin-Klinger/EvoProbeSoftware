from DataHub import DataHub
from MeasurementDevice import MeasurementDevice
from threading import Thread
from datetime import datetime
import time


class DataReader(Thread):

    def __init__(self, datahub: DataHub, measurement_devices: list[MeasurementDevice], interval=2):
        super().__init__()
        self.datahub = datahub
        self.measurement_devices = measurement_devices
        self.interval = interval
        self.is_running = False

    def run(self):
        start_timestamp = datetime.now()
        start_time = time.monotonic()

        self.is_running = True
        while self.is_running:
            row = [datetime.now(), (datetime.now() - start_timestamp).total_seconds()]
            for device in self.measurement_devices:
                row += device.get_logging_readings()
            self.datahub.update_df(data=row)

            time.sleep(self.interval - ((time.monotonic() - start_time) % self.interval))

    def stop_reader(self):
        self.is_running = False
