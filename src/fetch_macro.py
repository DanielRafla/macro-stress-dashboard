import os
import pandas as pd
from fredapi import Fred
import yfinance as yf

# ─────────── Configuration ───────────
fred_api_key = os.getenv("FRED_API_KEY")
if not fred_api_key:
    raise RuntimeError("FRED_API_KEY not set")

fred = Fred(api_key=fred_api_key)
OUT_CSV = os.path.join("data", "processed", "macro_data.csv")

# FRED series to pull
FRED_SERIES = {
    "2Y_Treasury": "DGS2",
    "10Y_Treasury": "DGS10",
    "FedFunds":    "DFEDTARU",
    "HY_OAS":      "BAMLH0A0HYM2",
}

# Map ETF ticker → sector name
SECTOR_TICKERS = {
    "XLK": "Technology",
    "XLY": "Consumer",
    "XLI": "Industrials",
}

# List of company tickers
COMPANY_TICKERS = ["AAPL", "MSFT", "GOOGL"]

# ─────────── Fetch functions ───────────
def fetch_fred():
    dfs = []
    for name, series_id in FRED_SERIES.items():
        print(f"Fetching FRED series {series_id} as {name}")
        s = fred.get_series(series_id)
        dfs.append(s.to_frame(name=name))
    return pd.concat(dfs, axis=1)

def fetch_sectors():
    print("Fetching sector ETFs")
    df = yf.download(
        list(SECTOR_TICKERS.keys()),
        progress=False,
        auto_adjust=False
    )["Adj Close"]
    return df.rename(columns=SECTOR_TICKERS)

def fetch_companies():
    print("Fetching company prices")
    df = yf.download(
        COMPANY_TICKERS,
        progress=False,
        auto_adjust=False
    )["Adj Close"]
    return df

# ─────────── Main pipeline ───────────
def main():
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)

    # Pull data
    fred_df   = fetch_fred()
    sector_df = fetch_sectors()
    comp_df   = fetch_companies()

    # Merge on dates
    merged = fred_df.join(sector_df, how="outer").join(comp_df, how="outer")
    merged.to_csv(OUT_CSV)
    print(f"Saved merged data to {OUT_CSV}")

if __name__ == "__main__":
    main()

