import os
import pandas as pd
import yfinance as yf
import psycopg
from dotenv import load_dotenv

load_dotenv()
DB = os.environ["DATABASE_URL"]

def ingest_prices(ticker: str = "AAPL", period: str = "100d"):
    df = yf.download(ticker, period=period, interval="1d", auto_adjust=False, progress=False)

    if df is None or df.empty:
        raise RuntimeError("No price data returned from yfinance.")

    # If columns are multi-index, flatten them
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.reset_index()
    df["Date"] = pd.to_datetime(df["Date"]).dt.date

    with psycopg.connect(DB) as conn, conn.cursor() as cur:
        for _, r in df.iterrows():
            cur.execute(
                """
                INSERT INTO public.prices_daily (ticker, day, open, high, low, close, volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ticker, day) DO UPDATE SET
                  open   = EXCLUDED.open,
                  high   = EXCLUDED.high,
                  low    = EXCLUDED.low,
                  close  = EXCLUDED.close,
                  volume = EXCLUDED.volume
                """,
                (
                    ticker,
                    r["Date"],
                    float(r["Open"]),
                    float(r["High"]),
                    float(r["Low"]),
                    float(r["Close"]),
                    int(r["Volume"]) if pd.notna(r["Volume"]) else None,
                ),
            )

    print(f"Upserted {len(df)} daily rows for {ticker}")

if __name__ == "__main__":
    ingest_prices("AAPL", "100d")