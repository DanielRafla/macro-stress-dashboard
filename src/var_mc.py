import os
import pickle
import numpy as np
import pandas as pd
from statsmodels.tsa.api import VAR

# ─────────── Paths & Params ───────────
INPUT_CSV   = "data/processed/macro_data.csv"
VAR_PKL     = "data/processed/var_model.pkl"
MC_PARQUET  = "data/processed/mc_paths.parquet"

SHOCK_BP = 2.5    # 250 basis points
HORIZON  = 252    # trading days

# ─────────── Fit VAR ───────────
def fit_var(data):
    model   = VAR(data)
    results = model.fit(maxlags=5, trend="n")  # no constant term
    with open(VAR_PKL, "wb") as f:
        pickle.dump(results, f)
    return results

# ─────────── Forecast Paths ───────────
def forecast_paths(results, initial_vals, shock_sign):
    # initial_vals shape = (lags, neqs)
    lags      = results.k_ar
    shocked   = initial_vals.copy()
    idx       = list(results.names).index("FedFunds")
    shocked[-1, idx] += SHOCK_BP * shock_sign
    sims = results.forecast(shocked, HORIZON)
    return pd.DataFrame(sims, columns=results.names)

# ─────────── Main ───────────
if __name__ == "__main__":
    os.makedirs(os.path.dirname(VAR_PKL), exist_ok=True)

    df = pd.read_csv(INPUT_CSV, index_col=0, parse_dates=True)
    var_series = df[["FedFunds", "HY_OAS", "Technology"]].dropna()

    results      = fit_var(var_series)
    initial_vals = var_series.values[-results.k_ar :]

    base = results.forecast(initial_vals, HORIZON)
    up   = forecast_paths(results, initial_vals,  1)
    down = forecast_paths(results, initial_vals, -1)

    df_base = pd.DataFrame(base, columns=var_series.columns)
    df_up   = up
    df_down = down

    out = pd.concat(
        {"base": df_base, "up": df_up, "down": df_down},
        names=["scenario"]
    )
    out.to_parquet(MC_PARQUET)
    print(f"Saved VAR forecasts to {MC_PARQUET}")

