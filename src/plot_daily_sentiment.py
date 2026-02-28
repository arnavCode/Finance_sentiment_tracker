import os
import pandas as pd
import psycopg
from dotenv import load_dotenv
import plotly.graph_objects as go

load_dotenv()
DB = os.environ["DATABASE_URL"]

# Pick ONE of these depending on what you created in SQL
VIEW_NAME = "public.v_daily_sentiment"  # or "public.v_daily_sentiment_features"

def main():
    query = f"SELECT * FROM {VIEW_NAME} ORDER BY day;"
    with psycopg.connect(DB) as conn:
        df = pd.read_sql(query, conn)

    if df.empty:
        print(f"No rows returned from {VIEW_NAME}.")
        return

    # Ensure proper datetime parsing
    df["day"] = pd.to_datetime(df["day"])

    # Decide which lines to plot based on available columns
    y_cols = []
    for c in ["net_sent_mean", "net_sent_ma7", "net_sent_ma14", "pos_mean", "neg_mean"]:
        if c in df.columns:
            y_cols.append(c)

    if not y_cols:
        raise RuntimeError(f"No expected sentiment columns found in {VIEW_NAME}. Columns: {list(df.columns)}")

    fig = go.Figure()
    for c in y_cols:
        fig.add_trace(go.Scatter(x=df["day"], y=df[c], mode="lines", name=c))

    fig.update_layout(
        title=f"Daily Sentiment ({VIEW_NAME})",
        xaxis=dict(rangeslider=dict(visible=True), type="date"),
    )
    fig.show()

if __name__ == "__main__":
    main()
