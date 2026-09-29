"""
Failure prediction: turn indicators (+ the ML probability) into one
0-100 risk score, a level, and a recommended action.

Combination is a noisy-OR over indicator scores treated as independent
probabilities: risk = 1 - prod(1 - s_i/100). One strong signal is
enough to raise risk, several moderate ones compound, and an indicator
at 0 contributes nothing — unlike a weighted average, which would let
many healthy readings dilute one real problem.

The ML probability enters as one more indicator, capped at ML_MAX_SCORE:
the time-aware model's precision is 0.38 on held-out days (~6 in 10 of
its alarms are false), so on its own it can only raise a device to
MEDIUM — "watch", no alert. HIGH/CRITICAL (which notify) always need a
physical measurement behind them; the ML score still compounds with
that evidence through the noisy-OR.
"""

from app.modules.failure_prediction.indicators import Indicator

LEVELS = [(75.0, "CRITICAL"), (50.0, "HIGH"), (25.0, "MEDIUM"), (0.0, "LOW")]

ML_THRESHOLD_SCORE = 30.0
ML_MAX_SCORE = 45.0

_ACTIONS = {
    "performance_ratio": "Inspect the array: soiling, shading, a failed string or bypass diodes. Compare string currents.",
    "daylight_trips": "Check inverter event log for grid/isolation faults; inspect DC connectors and string fuses.",
    "inverter_temperature": "Clean inverter air intakes/filters and check cooling fans; verify ambient ventilation.",
    "voltage_deviation": "Grid voltage out of band — check the point of connection and inverter voltage settings with the utility.",
    "frequency_deviation": "Frequency excursions — review grid events; if local, check generator/inverter frequency control.",
    "ml_fault_probability": "Model expects a PV fault within 3 hours — watch output closely and have a technician on call.",
    "state_of_health": "Plan battery module replacement; run a capacity test to confirm remaining capacity.",
    "battery_temperature": "Check battery room HVAC and BMS thermal readings; reduce charge/discharge rate until cooled.",
    "round_trip_efficiency": "Efficiency loss suggests cell imbalance or ageing — run a BMS balancing cycle and capacity test.",
    "cycle_wear": "Battery approaching rated cycle life — budget for replacement.",
    "deep_discharge": "Raise the minimum SOC setpoint; frequent deep discharge shortens battery life.",
    "soc_flatline": "SOC not tracking current — check BMS communication and recalibrate SOC.",
    "consecutive_errors": "Check device network link, credentials and gateway; power-cycle the logger if needed.",
    "offline": "Device not reporting — check power, network and gateway on site.",
    "data_gaps": "Intermittent connectivity — check network stability and the data logger.",
    "no_data": "No telemetry received — verify the device is powered and connected.",
    "data_quality": "Many readings fail validation — check sensor wiring and device configuration.",
}


def ml_indicator(probability: float, threshold: float, fault_type: str | None) -> Indicator:
    if probability < threshold:
        score = ML_THRESHOLD_SCORE * probability / threshold
    else:
        score = ML_THRESHOLD_SCORE + (ML_MAX_SCORE - ML_THRESHOLD_SCORE) * (
            (probability - threshold) / (1 - threshold)
        )
    diagnosis = f" Current behaviour resembles: {fault_type}." if fault_type else ""
    return Indicator(
        "ml_fault_probability", "ML", "Fault within 3 h (ML)",
        round(probability, 3), "probability", round(threshold, 3), round(score, 1),
        f"Model probability {probability:.0%} of a PV fault in the next 3 hours "
        f"(alarm threshold {threshold:.0%}).{diagnosis}",
    )


def level_for(score: float) -> str:
    return next(name for floor, name in LEVELS if score >= floor)


def combine(indicators: list[Indicator]) -> tuple[float, str, Indicator | None, str | None]:
    survival = 1.0
    for ind in indicators:
        survival *= 1.0 - min(max(ind.score, 0.0), 100.0) / 100.0
    score = round((1.0 - survival) * 100.0, 1)

    top = max(indicators, key=lambda i: i.score, default=None)
    if top is None or top.score <= 0:
        return score, level_for(score), None, None
    return score, level_for(score), top, _ACTIONS.get(top.code)
