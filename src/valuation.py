import os
import pandas as pd
import numpy as np

# ─────────── Config ───────────
MACRO_CSV    = "data/processed/macro_data.csv"
MC_PARQUET   = "data/processed/mc_paths.parquet"
OUT_PARQUET  = "data/processed/valuations.parquet"

ERP          = 0.05     # Equity risk premium
GROWTH_RATE  = 0.03     # CF growth (years 1–5)
TERM_RATE    = 0.02     # Perpetual growth for terminal value
FORECAST_YRS = 5

# ─────────── Helpers ───────────
def compute_betas(macro_df, companies, sector_map):
    ret = macro_df.pct_change(fill_method=None).dropna()
    betas = {}
    for comp in companies:
        sector = sector_map[comp]
        cov   = ret[comp].cov(ret[sector])
        var   = ret[sector].var()
        betas[comp] = cov / var if var > 0 else np.nan
    return pd.Series(betas)

# ─────────── Main ───────────
def main():
    macro = pd.read_csv(MACRO_CSV, index_col=0, parse_dates=True)
    mc    = pd.read_parquet(MC_PARQUET)

    companies = [
        c for c in macro.columns
        if c.isupper() and c not in {"Technology","Consumer","Industrials"}
    ]
    sector_map = {c: "Technology" if c in ["AAPL","MSFT","GOOGL"] else "Consumer"
                  for c in companies}

    betas = compute_betas(macro, companies, sector_map)

    records = []
    for scenario, df_s in mc.groupby(level=0):
        rf_series     = df_s["FedFunds"] / 100
        spread_series = df_s["HY_OAS"]   / 100

        for comp in companies:
            beta        = betas[comp]
            last_cf     = 1_000_000  # replace with actual last cash flow
            cf_proj     = [
                last_cf * (1 + GROWTH_RATE) ** i
                for i in range(1, FORECAST_YRS + 1)
            ]
            wacc_series = rf_series + beta * ERP + spread_series

            # project & discount each CF
            for year_idx, cf in enumerate(cf_proj, start=1):
                discount_rate = wacc_series.iloc[year_idx - 1]
                pv = cf / ((1 + discount_rate) ** year_idx)
                records.append({
                    "company":     comp,
                    "scenario":    scenario,
                    "year":        year_idx,
                    "projected_cf": cf,
                    "wacc":        discount_rate,
                    "pv_cf":       pv
                })

            # terminal value
            tv    = cf_proj[-1] * (1 + TERM_RATE) / (wacc_series.iloc[-1] - TERM_RATE)
            pv_tv = tv / ((1 + wacc_series.iloc[-1]) ** FORECAST_YRS)
            records.append({
                "company":     comp,
                "scenario":    scenario,
                "year":        "TV",
                "projected_cf": tv,
                "wacc":        wacc_series.iloc[-1],
                "pv_cf":       pv_tv
            })

    df_val = pd.DataFrame(records)

    # Cast 'year' to string so Parquet doesn't choke on mixed types
    df_val["year"] = df_val["year"].astype(str)

    df_val.to_parquet(OUT_PARQUET, index=False)
    print(f"Saved valuations to {OUT_PARQUET}")

if __name__ == "__main__":
    main()

