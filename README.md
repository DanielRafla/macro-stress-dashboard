[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](/LICENSE)

# Macro-Stress Dashboard 



**Description:** A lightweight Dash app that lets you apply ±shock scenarios to the Fed Funds rate and instantly see how it propagates through the yield curve (2Y/10Y) and broader macro forecasts. Great for treasury, IB or fintech teams to stress‑test funding & liquidity assumptions.

**Goal:** Trace a ±250 bp Fed Funds shock through yield curves, credit spreads, WACC, DCF valuations & equity prices for 50 firms.


## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## QUICK START
```bash
python -m src.fetch_fomc

python -m src.fetch_macro

python -m src.var_mc

python -m src.valuation

python -m src.dashboard
```
## Usage

# Launch the interactive dashboard
python src/dashboard.py

## Deploying
```bash
docker build -t macro-stress-dashboard .
docker run -p 8050:8050 macro-stress-dashboard
```    

## Demo

### Yield Curve Under +100 bp Shock
![Yield‑curve +100 bp](src/shock_100bps.png)

### Yield Curve Under +300 bp Shock
![Yield‑curve +300 bp](src/%2B300BPS.png)
