from PyQt5.QtCore import QThread


class GuiThread(QThread):

    def __init__(self, target):
        super().__init__()
        self.target = target

    def run(self):
        self.target()
