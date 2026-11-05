"""BattLeDIM L-Town 2019 (tank T1 + PUMP_1, hourly): tariff-aware pump scheduling.

usage: python research/run_study.py <dir with 2019_SCADA_Flows.csv and 2019_SCADA_Levels.csv>
BattLeDIM SCADA data are hydraulic-model based (L-Town is a benchmark network), NOT field measurements of a real city.
The tariff and the constant energy per m3 are ASSUMPTIONS. Policies, simulated for the whole of 2019 on the inferred demand:
  historical   - the recorded hourly pump flow (cost computed with the assumed tariff)
  perfect      - day-ahead LP with the true demand of the day (upper bound on savings)
  forecast     - day-ahead LP with the demand forecast = same-hour mean of the previous 7 days, open loop
  mpc          - hourly re-planning (24 h horizon, forecast demand, actual simulated tank level)
Level bounds for planning: 2.1-3.9 m (observed range). Violation = hours outside 2.0-4.0 m (tank limits).
"""

import json
import sys
from pathlib import Path

import numpy as np

from pumpsave.data import TANK_AREA_M2 as A
from pumpsave.data import load_year, tariff
from pumpsave.optim import QP, plan, simulate

HMIN, HMAX = 2.1, 3.9
HARD_MIN, HARD_MAX = 2.0, 4.0
FALLBACK_DEMAND = 30.0  # m3/h, used only for forecasts with no history yet (first day)


def forecast(demand: np.ndarray, t0: int, n: int) -> np.ndarray:
    """Same-hour mean of the previous 7 days (uses only data before t0)."""
    out = np.empty(n)
    for k in range(n):
        idx = [t0 + k - 24 * j for j in range(1, 8) if t0 + k - 24 * j >= 0]
        idx = [i for i in idx if i < t0]
        out[k] = np.mean(demand[idx]) if idx else FALLBACK_DEMAND
    return out


def summarize(name, u, d, price, h0):
    h = simulate(h0, u, d, A)
    vol = float((QP * u).sum())
    cost = float(price @ u) * QP
    viol = (h[1:] < HARD_MIN) | (h[1:] > HARD_MAX)
    return {
        "cost": cost,
        "volume_pumped_m3": vol,
        "cost_per_m3_pumped": cost / vol,
        "net_level_change_m": float(h[-1] - h[0]),
        "hours_outside_tank_limits": int(viol.sum()),
        "min_level": float(h.min()),
        "max_level": float(h.max()),
    }


def main(folder: str):
    df = load_year(f"{folder}/2019_SCADA_Flows.csv", f"{folder}/2019_SCADA_Levels.csv")
    d = df["demand"].to_numpy()
    price = tariff(df.index.hour.to_numpy())
    n = (len(d) // 24) * 24
    d, price = d[:n], price[:n]
    h0 = float(df["level"].iloc[0])
    pump_hist = df["pump"].to_numpy()[:n] / QP  # unclipped: replays the recorded level exactly
    out = {
        "note": "L-Town benchmark data (hydraulic-model based), assumed tariff and constant energy per m3",
        "n_hours": n,
        "demand_mean_m3h": float(d.mean()),
        "policies": {},
    }
    out["policies"]["historical"] = summarize("historical", pump_hist, d, price, h0)
    # perfect foresight, day-ahead, level carried over (simulated)
    for name in ("perfect", "forecast"):
        h, us = h0, []
        for day in range(n // 24):
            t0 = day * 24
            dd = d[t0 : t0 + 24] if name == "perfect" else forecast(d, t0, 24)
            u = plan(h, np.maximum(dd, 0.0), price[t0 : t0 + 24], A, HMIN, HMAX)
            us.append(u)
            h = simulate(h, u, d[t0 : t0 + 24], A)[-1]
        out["policies"][name] = summarize(name, np.concatenate(us), d, price, h0)
    # MPC: replan hourly
    h, us = h0, []
    for t in range(n):
        horizon = min(24, n - t)
        fd = forecast(d, t, horizon)
        u = plan(
            float(np.clip(h, HMIN, HMAX)),
            np.maximum(fd, 0.0),
            price[t : t + horizon],
            A,
            HMIN,
            HMAX,
            terminal_min=min(h0, HMAX),
        )
        us.append(u[0])
        h = h + (QP * u[0] - d[t]) / A
    out["policies"]["mpc"] = summarize("mpc", np.array(us), d, price, h0)
    base = out["policies"]["historical"]["cost_per_m3_pumped"]
    for k, v in out["policies"].items():
        v["saving_vs_historical_pct"] = 100 * (1 - v["cost_per_m3_pumped"] / base)
        print(k, {a: round(b, 3) for a, b in v.items()})
    # sensitivity of the MPC saving to the assumed tariff spread (peak, shoulder, off-peak)
    out["tariff_sensitivity_mpc"] = {}
    for tar in ((1.0, 1.0, 1.0), (1.5, 1.25, 1.0), (3.0, 1.5, 1.0), (5.0, 2.0, 1.0)):
        pr = tariff(df.index.hour.to_numpy()[:n], *tar)
        h, us = h0, []
        for t in range(n):
            horizon = min(24, n - t)
            fd = np.maximum(forecast(d, t, horizon), 0.0)
            u = plan(
                float(np.clip(h, HMIN, HMAX)),
                fd,
                pr[t : t + horizon],
                A,
                HMIN,
                HMAX,
                terminal_min=min(h0, HMAX),
            )
            us.append(u[0])
            h = h + (QP * u[0] - d[t]) / A
        mpc = summarize("mpc", np.array(us), d, pr, h0)
        hist = summarize("historical", pump_hist, d, pr, h0)
        out["tariff_sensitivity_mpc"][f"peak{tar[0]:g}_shoulder{tar[1]:g}_off{tar[2]:g}"] = {
            "saving_vs_historical_pct": 100
            * (1 - mpc["cost_per_m3_pumped"] / hist["cost_per_m3_pumped"]),
            "hours_outside_tank_limits": mpc["hours_outside_tank_limits"],
        }
        print(
            tar, out["tariff_sensitivity_mpc"][f"peak{tar[0]:g}_shoulder{tar[1]:g}_off{tar[2]:g}"]
        )
    Path(__file__).with_name("results.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
