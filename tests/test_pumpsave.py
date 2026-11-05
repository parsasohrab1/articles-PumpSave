import numpy as np

from pumpsave.data import tariff
from pumpsave.optim import plan, simulate

A = 200.0


def test_tariff_levels():
    assert list(tariff(np.array([3, 8, 18, 22]))) == [1.0, 1.5, 3.0, 1.0]


def test_plan_respects_bounds_and_terminal_level():
    d = np.full(24, 30.0)
    price = tariff(np.arange(24))
    u = plan(3.0, d, price, A, 2.1, 3.9)
    h = simulate(3.0, u, d, A)
    assert h.min() >= 2.1 - 1e-6 and h.max() <= 3.9 + 1e-6 and h[-1] >= 3.0 - 1e-6


def test_plan_is_cheaper_than_constant_duty_and_avoids_peak():
    d = np.full(24, 30.0)
    price = tariff(np.arange(24))
    u = plan(3.0, d, price, A, 2.1, 3.9)
    const = np.full(24, 30.0 / 43.7)
    assert float(price @ u) <= float(price @ const) + 1e-9
    assert u[17:21].sum() < const[17:21].sum()
