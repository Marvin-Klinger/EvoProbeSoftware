from lakeshore import Model372InputSetupSettings
from PyQt5 import QtGui as qtg

# Default Lakeshore Settings
LAKESHORE_CHANNEL_SETTINGS = Model372InputSetupSettings(
    mode=None,
    excitation_range=None,
    auto_range=None,
    current_source_shunted=False,
    units=None,
    resistance_range=None
)

LAKESHORE_FILTER_SETTINGS = (
    0,      # all input_channels
    None,   # state
    None,   # settle_time
    None    # window
)

# Default Puck
PUCK_SETTINGS = {
    "id": "default",
    "n_of_slots": 3,
    "slots": [
        {"name": "Sample 1", "read_only": False},
        {"name": "Sample 2", "read_only": False},
        {"name": "Thermometer", "read_only": True,
         "calibration": {"min_resistance": 0,
                         "max_resistance": 1000,
                         "rescale_0": 0,
                         "rescale_1": 0,
                         "func_params": [0, -0.5],
                         "min_temperature": 0,
                         "max_temperature": 4000}
         }
    ]
}

# Default Gui Settings
FONT = qtg.QFont("Bahnschrift", 16)

