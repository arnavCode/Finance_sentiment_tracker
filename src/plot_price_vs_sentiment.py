import os
import pandas as pd
import psycopg
from dotenv import load_dotenv
import plotly.graph_objects as go

load_dotenv()
DB = os.environ["DATABASE_URL"]

def main():
    with psycopg.connect(DB) as conn:
        df = pd.read_sql("SELECT * FROM public.v_sentiment_with_price;", conn)

    if df.empty:
        print("No rows returned from v_sentiment_with_price.")
        return

    df["day"] = pd.to_datetime(df["day"])
    df = df.sort_values("day")

    # Pick the best sentiment series available
    if "net_sent_ma7" in df.columns and df["net_sent_ma7"].notna().any():
        sent_col = "net_sent_ma7"
        sent_name = "Net Sentiment (MA7)"
    else:
        sent_col = "net_sent_mean"
        sent_name = "Net Sentiment"

    fig = go.Figure()

    # Price line (left axis)
    fig.add_trace(go.Scatter(
        x=df["day"],
        y=df["close"],
        mode="lines",
        name="Close (AAPL)",
        yaxis="y1",
        hovertemplate="Day=%{x|%Y-%m-%d}<br>Close=%{y}<extra></extra>",
    ))

    # Sentiment line (right axis)
    fig.add_trace(go.Scatter(
        x=df["day"],
        y=df[sent_col],
        mode="lines",
        name=sent_name,
        yaxis="y2",
        hovertemplate="Day=%{x|%Y-%m-%d}<br>Sent=%{y:.4f}<extra></extra>",
    ))

    # Optional: articles per day as bars (if present)
    if "n_articles" in df.columns and df["n_articles"].notna().any():
        fig.add_trace(go.Bar(
            x=df["day"],
            y=df["n_articles"],
            name="Articles/day",
            yaxis="y2",
            opacity=0.25,
            hovertemplate="Day=%{x|%Y-%m-%d}<br>Articles=%{y}<extra></extra>",
        ))

    fig.update_layout(
        title="AAPL Price vs News Sentiment",
        xaxis=dict(
            title="Day",
            rangeslider=dict(visible=True),
            type="date",
        ),
        yaxis=dict(title="Price (Close)"),
        yaxis2=dict(
            title="Sentiment / Volume",
            overlaying="y",
            side="right",
        ),
        legend=dict(orientation="h"),
        bargap=0.0,
    )

    fig.show()

if __name__ == "__main__":
    main()