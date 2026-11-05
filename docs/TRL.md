# TRL assessment – PumpSave

**Claimed level: TRL 4** (simulation-based validation). Not TRL 5: benchmark-network data, assumed tariff and energy model, no pump curve, no network hydraulics.

Data: BattLeDIM L-Town 2019 (hourly): tank T1, pump PUMP_1 (runs at about 43.7 m3/h when on), mean outflow 34.1 m3/h, 8736 hours. Relative tariff: peak 3 (17–21 h), shoulder 1.5 (07–17 h), off-peak 1. Cost in relative units per m3 pumped; "outside limits" = hours with level beyond 2.0–4.0 m.

| Policy | Cost per m3 | Saving vs historical | Net level change (m) | Hours outside limits | Min / max level (m) |
|---|---|---|---|---|---|
| Historical (recorded pump flow) | 1.582 | 0.0 % | -0.49 | 0 | 2.09 / 3.90 |
| Day-ahead LP, true demand | 1.307 | 17.4 % | -0.06 | 0 | 3.04 / 3.90 |
| Day-ahead LP, forecast demand (open loop) | 1.304 | 17.6 % | +0.51 | 399 | 1.33 / 4.36 |
| Hourly re-planning (MPC), forecast demand | 1.288 | 18.6 % | +0.00 | 1 | 2.05 / 4.01 |

Sensitivity of the hourly re-planning policy to the assumed tariff (peak, shoulder, off-peak):

| Tariff | Saving vs historical | Hours outside limits |
|---|---|---|
| peak1, shoulder1, off1 | -0.0 % | 9 |
| peak1.5, shoulder1.25, off1 | 5.7 % | 1 |
| peak3, shoulder1.5, off1 | 18.6 % | 1 |
| peak5, shoulder2, off1 | 27.1 % | 1 |

## Findings and caveats
- Under the assumed tariff the schedule saves 17–19 % of the electricity cost per m3 against the recorded operation, which was not tariff-aware. **The saving is entirely a consequence of the assumed tariff**: it is 0 % with a flat price, 5.7 % with a mild spread (1.5 / 1.25 / 1) and 27 % with a steep one (5 / 2 / 1).
- With a demand forecast (previous-7-day same-hour mean) and no feedback, the day-ahead plan keeps the cost advantage but leaves the tank limits for 399 hours (level 1.33–4.36 m): the open-loop plan is not safe. Re-planning every hour with the measured level removes almost all violations (1 hour, 4.01 m) at no loss of saving.
- The saving ignores that pumping at different times changes pump head and network pressure, that start/stop cycles and efficiency affect energy and wear, and that the energy per m3 is taken as constant.
- "Demand" is the outflow implied by the volume balance of the benchmark data; it is not metered consumption.
- Terminal-level and soft-bound penalties were set by hand (1e4 per metre) and not tuned.
