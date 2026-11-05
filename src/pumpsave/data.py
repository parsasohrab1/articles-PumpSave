from __future__ import annotations

import numpy as np
import pandas as pd

TANK_AREA_M2 = float(np.pi * 8.0**2)  # tank T1 diameter 16 m (L-TOWN.inp)


def load_year(flows_csv: str, levels_csv: str) -> pd.DataFrame:
    """BattLeDIM SCADA files -> hourly table: pump flow (m3/h), tank level (m) and inferred demand (m3/h).

    demand_t = pump_t - A * (h_{t+1} - h_t): the outflow of the tank implied by a volume balance.
    """
    f = pd.read_csv(flows_csv, sep=";", decimal=",", parse_dates=["Timestamp"], index_col=0)
    lv = pd.read_csv(levels_csv, sep=";", decimal=",", parse_dates=["Timestamp"], index_col=0)
    q = f["PUMP_1"].resample("1h").mean()
    h = lv["T1"].resample("1h").first()
    d = q - TANK_AREA_M2 * (h.shift(-1) - h)
    out = pd.DataFrame({"pump": q, "level": h, "demand": d}).dropna()
    return out


def tariff(
    hours: np.ndarray, peak: float = 3.0, shoulder: float = 1.5, off: float = 1.0
) -> np.ndarray:
    """Assumed time-of-use price (relative units): peak 17-21 h, shoulder 7-17 h, off-peak otherwise."""
    h = np.asarray(hours) % 24
    return np.where(
        (h >= 17) & (h < 21), peak, np.where((h >= 7) & (h < 17), shoulder, off)
    ).astype(float)
