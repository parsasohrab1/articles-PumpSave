# Software Requirements Specification – PumpSave

- SR-1 `data.load_year`: hourly pump flow, tank level and inferred outflow ("demand") from the volume balance demand = pump - A (h_next - h) with tank area A = pi * 8^2 m2 (tank T1, diameter 16 m).
- SR-2 `data.tariff`: assumed time-of-use price (peak 17–21 h, shoulder 7–17 h, off-peak otherwise).
- SR-3 `optim.plan`: linear programme over duty fractions u_t in [0, 1] of a fixed-speed pump (43.7 m3/h) minimising the sum of price x u subject to level bounds and a terminal level, with soft (penalised) bounds so that it is always feasible. `optim.simulate`: tank mass balance.
- SR-4 `research/run_study.py`: whole-year simulation on the inferred demand for four policies (historical replay, day-ahead LP with true demand, day-ahead LP with a 7-day same-hour demand forecast, hourly re-planning with a 24 h horizon); tariff sensitivity of the MPC policy.
- SR-5 Three unit tests (tariff, bounds and terminal level, cost not above constant duty and less pumping at peak).
