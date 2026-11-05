# articles-PumpSave

Tariff-aware scheduling of a tank-fed pump (LP day-ahead plan and hourly re-planning) on the **BattLeDIM L-Town** SCADA data
(pump flow and tank level, 5-minute, 2019; hourly aggregates). The L-Town data are hydraulic-model based benchmark data, **not
field measurements**; the electricity tariff and the energy per cubic metre are **assumptions**. TRL 4 (simulation-based).

```
pip install -e ".[dev]" && python -m pytest
# data: Zenodo 4017659 (BattLeDIM) files 2019_SCADA_Flows.csv and 2019_SCADA_Levels.csv (not committed)
python research/run_study.py <dir with those two files>
```
