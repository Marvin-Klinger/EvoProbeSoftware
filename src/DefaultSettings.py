from lakeshore import Model372InputSetupSettings

# Lakeshore settings
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
