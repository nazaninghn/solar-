VALID_SCENARIOS = {"NORMAL", "SUNNY", "CLOUDY", "PEAK_PRICE", "BATTERY_LOW", "DEVICE_OFFLINE"}

# 26.37: a single in-process switch, not a per-device/per-factory DB
# setting — this is a testing tool for exercising the whole pipeline
# (simulator -> polling -> aggregation -> alerts -> dashboard) end to
# end before real hardware exists, not a production feature, so it
# deliberately doesn't carry the weight of a migration + per-device
# config. Affects every SIMULATOR-connected device process-wide.
_current_scenario = "NORMAL"


def set_scenario(scenario: str) -> None:
    if scenario not in VALID_SCENARIOS:
        raise ValueError(f"Unknown scenario. Must be one of: {', '.join(sorted(VALID_SCENARIOS))}")

    global _current_scenario
    _current_scenario = scenario


def get_scenario() -> str:
    return _current_scenario
