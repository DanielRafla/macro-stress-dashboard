import os
import pickle
import numpy as np
import pandas as pd
from statsmodels.tsa.api import VAR
from pandas.tseries.offsets import BDay

INPUT_CSV   = "data/processed/macro_data.csv"
VAR_PKL     = "data/processed/var_model.pkl"
MC_PARQUET  = "data/processed/mc_paths.parquet"

SHOCK_BP = 2.5    # 250 basis points
HORIZON  = 252    # simulation length in trading days


def fit_var(data):
    model   = VAR(data)
    results = model.fit(maxlags=5, trend="n")  # no constant term
    with open(VAR_PKL, "wb") as f:
        pickle.dump(results, f)
    return results


def forecast_paths(results, data, shock_sign):
    lags      = results.k_ar
    initial   = data.values[-lags:]
    shocked   = initial.copy()
    idx       = list(data.columns).index("FedFunds")
    shocked[-1, idx] += SHOCK_BP * shock_sign
    sims      = results.forecast(shocked, HORIZON)

    # build a business-day index starting the next trading day
    last_date = data.index[-1]
    dates     = pd.bdate_range(start=last_date + BDay(1), periods=HORIZON)

    return pd.DataFrame(sims, index=dates, columns=data.columns)


if __name__ == "__main__":
    os.makedirs(os.path.dirname(VAR_PKL), exist_ok=True)
    df         = pd.read_csv(INPUT_CSV, index_col=0, parse_dates=True)
    var_series = df[["FedFunds", "HY_OAS", "Technology"]].dropna()

    results      = fit_var(var_series)
    initial_vals = var_series.values[-results.k_ar:]

    df_base = pd.DataFrame(
        results.forecast(initial_vals, HORIZON),
        index=pd.bdate_range(start=var_series.index[-1] + BDay(1), periods=HORIZON),
        columns=var_series.columns
    )
    df_up   = forecast_paths(results, var_series,  1)
    df_down = forecast_paths(results, var_series, -1)

    out = pd.concat(
        {"base": df_base, "up": df_up, "down": df_down},
        names=["scenario"]
    )
    out.to_parquet(MC_PARQUET)
    print(f"Saved VAR forecasts with real dates to {MC_PARQUET}")

