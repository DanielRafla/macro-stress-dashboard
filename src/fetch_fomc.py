import os
import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime

BASE_URL = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
OUT_CSV  = os.path.join("data", "processed", "fomc_sentiment.csv")
PATTERN  = re.compile(r"/monetarypolicy/files/fomc(\d{4})(\d{2})(\d{2})stmt\.htm", re.IGNORECASE)

def get_statement_links():
    resp = requests.get(BASE_URL); resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")
    links = []
    for a in soup.find_all("a", href=True):
        m = PATTERN.search(a["href"])
        if not m: 
            continue
        year, mon, day = m.groups()
        date = datetime(int(year), int(mon), int(day)).date()
        full = "https://www.federalreserve.gov" + a["href"]
        links.append((date, full))
    return sorted(links)

def scrape_and_score(links):
    analyzer = SentimentIntensityAnalyzer()
    records = []
    for date, url in links:
        resp = requests.get(url); resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        paras = soup.select("div#article p")
        text  = " ".join(p.get_text(" ", strip=True) for p in paras)
        score = analyzer.polarity_scores(text)["compound"]
        records.append({"date": date, "hawk_dove": score})
    return pd.DataFrame(records)

def main():
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    links = get_statement_links()
    df    = scrape_and_score(links)
    df.to_csv(OUT_CSV, index=False)
    print(f"Saved {len(df)} statement scores to {OUT_CSV}")

if __name__ == "__main__":
    main()

