from __future__ import annotations

import numpy as np
from scipy.optimize import linprog

QP = 43.7  # m3/h, pump flow when running (observed plateau of PUMP_1)


def plan(
    h0: float,
    demand: np.ndarray,
    price: np.ndarray,
    area: float,
    hmin: float,
    hmax: float,
    terminal_min: float | None = None,
    qp: float = QP,
    penalty: float = 1e4,
) -> np.ndarray:
    """Cheapest duty fractions u_t in [0, 1] over the horizon keeping hmin <= h <= hmax.

    h_{t+1} = h_t + (qp * u_t - demand_t) / area; cost = sum(price_t * u_t) (energy per m3 assumed constant).
    The terminal level should be at least ``terminal_min`` (default: h0). Level bounds and the terminal
    level are soft (slack variables with a large penalty per metre), so the LP is always feasible.
    """
    n = len(demand)
    tm = h0 if terminal_min is None else terminal_min
    L = np.tril(np.ones((n, n))) * qp / area
    base = h0 - np.cumsum(demand) / area
    # variables: u (n), s_lo (n), s_hi (n), s_T (1)
    c = np.concatenate([price, np.full(2 * n + 1, penalty)])
    eye = np.eye(n)
    A1 = np.hstack([-L, -eye, np.zeros((n, n)), np.zeros((n, 1))])  # h >= hmin - s_lo
    b1 = base - hmin
    A2 = np.hstack([L, np.zeros((n, n)), -eye, np.zeros((n, 1))])  # h <= hmax + s_hi
    b2 = hmax - base
    A3 = np.hstack([-L[-1:], np.zeros((1, 2 * n)), -np.ones((1, 1))])  # h_n >= tm - s_T
    b3 = [base[-1] - tm]
    res = linprog(
        c,
        A_ub=np.vstack([A1, A2, A3]),
        b_ub=np.concatenate([b1, b2, b3]),
        bounds=[(0, 1)] * n + [(0, None)] * (2 * n + 1),
        method="highs",
    )
    if not res.success:
        return np.clip(demand / qp, 0, 1)
    return res.x[:n]


def simulate(
    h0: float, u: np.ndarray, demand: np.ndarray, area: float, qp: float = QP
) -> np.ndarray:
    h = np.empty(len(u) + 1)
    h[0] = h0
    for t in range(len(u)):
        h[t + 1] = h[t] + (qp * u[t] - demand[t]) / area
    return h
