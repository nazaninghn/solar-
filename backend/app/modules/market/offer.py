"""
Day-ahead sell offer builder (pure functions, no DB).

Inputs per delivery hour: forecast PV energy, expected factory load,
and the PTF forecast (P10/P50/P90). Output: what to sell, store or
discharge, and — in GOP_BID mode — the price/quantity bids.

1. Surplus = PV - load (never negative; the factory's own use comes
   first — it displaces retail electricity, worth more than PTF).
2. Battery arbitrage (if a battery exists): repeatedly pair the
   cheapest remaining surplus hour c with the most expensive later
   hour d, and shift energy c -> d while
       p50[d] * efficiency  >  p50[c] + degradation cost
   within capacity and power limits. The battery is assumed to start
   the day at its minimum SOC — tomorrow's opening SOC isn't known at
   12:30 today, so this never counts energy that may not be there.
3. Bids (GOP_BID):
   tier 1 — PV surplus sold directly. PV has ~zero marginal cost, so
     the rational bid is "any price >= min_price": a price-taker bid at
     the floor that always clears when PTF >= min_price.
   tier 2 — battery discharge, bid at its opportunity cost
     p50[charge hour] / efficiency + degradation: if PTF clears below
     that, not selling (keeping the energy) was the better choice
     anyway, so the bid simply doesn't clear.
   Quantities are rounded down to whole GÖP lots (0.1 MWh); remainders
   are reported, not bid.
   NET_METERING: same energy plan, no bids — surplus is exported and
   valued at the PTF forecast.

This is a decision aid: bids go to the market through a licensed
participant or aggregator (EPİAŞ participant systems), never from here.
"""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

LOT_MWH = 0.1


@dataclass
class BatterySpec:
    usable_kwh: float
    charge_kw: float
    discharge_kw: float
    efficiency: float  # round-trip, 0-1
    degradation_try_per_kwh: float = 0.0


@dataclass
class OfferHour:
    timestamp: pd.Timestamp
    tier: int
    action: str
    quantity_mwh: float
    price_try_mwh: float | None
    expected_ptf: float
    revenue_p10: float
    revenue_p50: float
    revenue_p90: float
    inputs: dict = field(default_factory=dict)


@dataclass
class OfferPlan:
    hours: list[OfferHour]
    unbid_remainder_mwh: float
    battery_cycles_kwh: float
    notes: list[str]

    @property
    def expected_revenue(self) -> float:
        return round(sum(h.revenue_p50 for h in self.hours), 2)


def plan_battery(
    surplus_kwh: np.ndarray, p50: np.ndarray, battery: BatterySpec | None
) -> tuple[np.ndarray, np.ndarray, list[tuple[int, int, float]]]:
    """Returns (charge_kwh, discharge_kwh, moves). Discharge is energy
    delivered to the grid (after losses)."""
    n = len(surplus_kwh)
    charge = np.zeros(n)
    discharge = np.zeros(n)
    moves: list[tuple[int, int, float]] = []
    if battery is None or battery.usable_kwh <= 0:
        return charge, discharge, moves

    eff = battery.efficiency
    degradation = battery.degradation_try_per_kwh * 1000  # TL/MWh
    # soc[b] = energy held at the boundary between hour b-1 and hour b;
    # a move c -> d occupies boundaries c+1 .. d.
    soc = np.zeros(n + 1)
    blocked: set[tuple[int, int]] = set()

    # Each iteration either moves > 1e-6 kWh or blocks one (c, d) pair,
    # and there are finitely many pairs, so this terminates.
    while True:
        best = None
        for c in range(n):
            if min(surplus_kwh[c] - charge[c], battery.charge_kw - charge[c]) <= 1e-6:
                continue
            for d in range(c + 1, n):
                if (c, d) in blocked:
                    continue
                gain = p50[d] * eff - p50[c] - degradation
                if gain > 0 and (best is None or gain > best[2]):
                    best = (c, d, gain)
        if best is None:
            break
        c, d, _ = best
        headroom = battery.usable_kwh - soc[c + 1 : d + 1].max()
        energy_in = min(
            surplus_kwh[c] - charge[c],
            battery.charge_kw - charge[c],
            (battery.discharge_kw - discharge[d]) / eff,
            headroom,
        )
        if energy_in <= 1e-6:
            blocked.add((c, d))
            continue
        charge[c] += energy_in
        discharge[d] += energy_in * eff
        soc[c + 1 : d + 1] += energy_in
        moves.append((c, d, energy_in))
    return charge, discharge, moves


def build_offer(
    timestamps: pd.DatetimeIndex,
    pv_kwh: np.ndarray,
    load_kwh: np.ndarray,
    ptf: pd.DataFrame,
    mode: str = "GOP_BID",
    min_price: float = 0.0,
    battery: BatterySpec | None = None,
) -> OfferPlan:
    p10 = ptf["p10"].to_numpy(dtype=float)
    p50 = ptf["p50"].to_numpy(dtype=float)
    p90 = ptf["p90"].to_numpy(dtype=float)
    surplus = np.clip(pv_kwh - load_kwh, 0.0, None)

    charge, discharge, moves = plan_battery(surplus, p50, battery)
    sell_pv = surplus - charge
    # For each discharge hour, the (energy-weighted) price of the hour it
    # was charged in — the opportunity cost its bid must cover.
    charge_cost = np.zeros(len(timestamps))
    for c, d, e in moves:
        charge_cost[d] += e * p50[c]
    notes: list[str] = []
    hours: list[OfferHour] = []
    remainder = 0.0

    def revenue(q_mwh: float, i: int, price: float | None) -> tuple[float, float, float]:
        clears = [(pp >= (price or 0.0)) for pp in (p10[i], p50[i], p90[i])]
        return tuple(round(q_mwh * pp * ok, 2) for pp, ok in zip((p10[i], p50[i], p90[i]), clears))

    for i, ts in enumerate(timestamps):
        base_inputs = {
            "pv_kwh": round(float(pv_kwh[i]), 2),
            "load_kwh": round(float(load_kwh[i]), 2),
            "surplus_kwh": round(float(surplus[i]), 2),
            "battery_charge_kwh": round(float(charge[i]), 2),
            "battery_discharge_kwh": round(float(discharge[i]), 2),
            "p10": round(float(p10[i]), 2),
            "p90": round(float(p90[i]), 2),
        }
        pv_mwh = sell_pv[i] / 1000
        dis_mwh = discharge[i] / 1000

        if mode == "GOP_BID":
            lots_pv = np.floor(pv_mwh / LOT_MWH + 1e-9) * LOT_MWH
            lots_dis = np.floor(dis_mwh / LOT_MWH + 1e-9) * LOT_MWH
            remainder += (pv_mwh - lots_pv) + (dis_mwh - lots_dis)
            if lots_pv > 0:
                r10, r50, r90 = revenue(lots_pv, i, min_price)
                hours.append(OfferHour(ts, 1, "SELL", round(lots_pv, 1), round(min_price, 2), round(p50[i], 2), r10, r50, r90, base_inputs))
            if lots_dis > 0:
                opportunity = charge_cost[i] / (discharge[i] / battery.efficiency) / battery.efficiency
                opportunity += battery.degradation_try_per_kwh * 1000
                price = round(max(min_price, opportunity), 2)
                r10, r50, r90 = revenue(lots_dis, i, price)
                hours.append(OfferHour(ts, 2, "DISCHARGE_SELL", round(lots_dis, 1), price, round(p50[i], 2), r10, r50, r90, base_inputs))
        else:
            if charge[i] > 0:
                hours.append(OfferHour(ts, 2, "STORE", round(charge[i] / 1000, 4), None, round(p50[i], 2), 0.0, 0.0, 0.0, base_inputs))
            if pv_mwh > 0:
                r10, r50, r90 = revenue(pv_mwh, i, None)
                hours.append(OfferHour(ts, 1, "SELL", round(pv_mwh, 4), None, round(p50[i], 2), r10, r50, r90, base_inputs))
            if dis_mwh > 0:
                r10, r50, r90 = revenue(dis_mwh, i, None)
                hours.append(OfferHour(ts, 3, "DISCHARGE_SELL", round(dis_mwh, 4), None, round(p50[i], 2), r10, r50, r90, base_inputs))

    if mode == "GOP_BID" and remainder > 0:
        notes.append(
            f"{remainder:.3f} MWh fell below whole 0.1 MWh GÖP lots and is not bid "
            "(it is settled as imbalance at SMF, or kept for own use)."
        )
    if surplus.sum() == 0:
        notes.append("No PV surplus is expected tomorrow: the factory is forecast to use all its generation.")
    return OfferPlan(hours, round(float(remainder), 4), round(float(charge.sum()), 2), notes)
