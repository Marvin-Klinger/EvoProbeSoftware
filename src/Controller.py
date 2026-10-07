import sys
import threading

from PyQt5 import QtWidgets as qtw

from src.Data.DataHub import DataHub
import src.FileHandler as FileHandler
from src.ExtraClasses import MeasurementDeviceType as mdType
from src.Gui.GuiMain import GuiMain
from src.Devices.LakeshoreChannel import LakeshoreChannel
from src.Devices.QDInstrumentChannel import QDInstrumentChannel
from MPVWrapper import MPVWrapper


class Controller:

    def __init__(self):
        self.devices = []
        self.datahub = None

        app = qtw.QApplication(sys.argv)
        self.main_window = GuiMain(self)
        app.exec_()

    # instantiates measurement_devices from data in setup.json
    def instantiate_devices(self):
        devices = []
        setup_json = FileHandler.get_setup_json()
        slots = setup_json.get("slots", [])
        settings = {d["id"]: d for d in setup_json.get("devices", [])}
        for i, slot in enumerate(slots):
            if slot is None:
                continue

            print(slot)
            match slot.get("type", None):
                case mdType.LAKESHORE:
                    devices.append(LakeshoreChannel(slot, settings.get(slot["id"], None)))
                case mdType.QDInstrument:
                    devices.append(QDInstrumentChannel(slot, settings.get(slot["id"], None)))
                case _:
                    pass
        self.devices = devices
        self.devices.append(MPVWrapper.get_device())
        print("Devices:", self.devices)

        for device in self.devices:
            device.connect_async()

        for device in self.devices:
            t = threading.Thread(target=device.start_reading, daemon=True)
            t.start()

    # starts the data reading and logging process and selected sequence
    def start_sequence(self, save_path):
        self.datahub = DataHub(self.devices, save_path, self)
        self.datahub.start_logging()

