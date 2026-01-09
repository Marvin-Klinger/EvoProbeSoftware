import time

import numpy as np
from lakeshore import Model372
from Model372Mock import Model372Mock, Model372InputSetupSettings

from collections import deque
from threading import Thread
from itertools import chain


class LakeshoreDevice:

    IP_ADDRESS = "192.168.0.12"
    DEBUG_MODE = True

    def __init__(self, input_channels: list[Model372.InputChannel], scanner_interval = 5):

        self.lakeshore: Model372 = None
        self.input_channels = input_channels
        self.scanner_queue = deque()
        self.current_channel = None
        self.is_ready = False
        self.is_cycling = False

        self.info = None

        self.initialize()

    def initialize(self):
        self.connect()
        self.scanner_queue.extend([c for c in self.input_channels if c != Model372.InputChannel.CONTROL])
        if len(self.scanner_queue):
            self.set_next_scanner_position()

    # starts changing scanner position every scanner_interval
    def start_scanner_cycle(self):
        if len([c for c in self.input_channels if c != Model372.InputChannel.CONTROL]) < 2:
            print("scanner cycling not necessary")
            return

        self.is_cycling = True

        def cycle():
            while self.is_cycling:
                self.set_next_scanner_position()

        t = Thread(target=cycle, daemon=True)
        t.start()

    # stops the scanner cycling
    def stop_scanner_cycle(self):
        self.is_cycling = False

    # gets raw readings from device and applies calibration if necessary
    def get_readings(self, input_channel: Model372.InputChannel):
        return self.lakeshore.get_all_input_readings(input_channel.value)

    # sets scanner to next channel in scanner_queue
    def set_next_scanner_position(self):
        if len(self.scanner_queue) > 1:
            channel = self.scanner_queue.popleft()
            self.lakeshore.set_scanner_status(channel.value, False)
            self.current_channel = channel
            self.scanner_queue.append(channel)

            self.is_ready = False

            def wait_for_ready():
                # TODO: find actual settle time
                time.sleep(1)
                self.is_ready = True

            t = Thread(target=wait_for_ready, daemon=True)
            t.start()

    # configures physical device
    def configure(self, input_channel: Model372.InputChannel, settings: Model372InputSetupSettings):
        self.lakeshore.configure_input(input_channel.value, settings)

    # establishes connection to the physical device
    def connect(self):
        if self.lakeshore is not None:
            return

        if LakeshoreDevice.DEBUG_MODE:
            self.lakeshore = Model372Mock(baud_rate=None)
            return

        try:
            self.lakeshore = Model372(baud_rate=None, ip_address=LakeshoreDevice.IP_ADDRESS)
        except:
            print("couldn't connect to lakeshore\n"
                  "trying again ...")
            try:
                self.lakeshore = Model372(baud_rate=None, ip_address=LakeshoreDevice.IP_ADDRESS)
            except:
                print("still couldn't connect to lakeshore\n"
                      "aborting process")


if __name__ == "__main__":
    device = LakeshoreDevice([Model372.InputChannel.CONTROL, Model372.InputChannel.ONE, Model372.InputChannel.TEN])
    print(device.lakeshore.get_scanner_status())
    device.set_next_scanner_position()
    print(device.lakeshore.get_scanner_status())
    device.set_next_scanner_position()
    print(device.lakeshore.get_scanner_status())
