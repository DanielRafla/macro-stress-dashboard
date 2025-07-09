import os
import pandas as pd
from fredapi import Fred
import yfinance as yf

# Config
fred_api_key = os.getenv("FRED_API_KEY")
if not fred_api_key:
    raise RuntimeError("FRED_API_KEY not set")
fred = Fred(api_key=fred_api_key)

OUT_CSV = os.path.join("data", "processed", "macro_data.csv")

FRED_SERIES = {
    "2Y_Treasury": "DGS2",
    "10Y_Treasury": "DGS10",
    "FedFunds":    "DFEDTARU",
    "HY_OAS":      "BAMLH0A0HYM2",
}

SECTOR_TICKERS = {
    "Technology":  "XLK",
    "Consumer":    "XLY",
    "Industrials": "XLI",
}

COMPANY_TICKERS = ["AAPL", "MSFT", "GOOGL"]

# Fetchers
def fetch_fred():
    dfs = []
    for name, code in FRED_SERIES.items():
        print(f"Fetching {code} as {name}")
        series = fred.get_series(code)
        df = series.to_frame(name=name)
        dfs.append(df)
    return pd.concat(dfs, axis=1)

def fetch_sectors():
    print("Fetching sector ETFs")
    df = yf.download(
        list(SECTOR_TICKERS.values()),
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

# Main
def main():
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    fred_df    = fetch_fred()
    sector_df  = fetch_sectors()
    comp_df    = fetch_companies()
    merged     = fred_df.join(sector_df, how="outer").join(comp_df, how="outer")
    merged.to_csv(OUT_CSV)
    print(f"Saved macro data to {OUT_CSV}")

if __name__ == "__main__":
    main()

