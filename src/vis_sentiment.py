import os
import pandas as pd
import psycopg
from dotenv import load_dotenv
import plotly.express as px

load_dotenv()
DB = os.environ["DATABASE_URL"]

SQL = """
SELECT
  date_trunc('day', a.published_at)::date AS day,
  COUNT(*) AS n_articles,
  AVG(s.pos) AS pos_mean,
  AVG(s.neg) AS neg_mean,
  AVG(s.neu) AS neu_mean,
  AVG(s.pos - s.neg) AS net_sent_mean
FROM public.articles a
JOIN public.article_sentiment s ON s.article_id = a.id
WHERE s.model = 'ProsusAI/finbert'
GROUP BY 1
ORDER BY 1;
"""

def main():
    with psycopg.connect(DB) as conn:
        df = pd.read_sql(SQL, conn)

    if df.empty:
        print("No data returned. Have you scored articles yet?")
        return

    fig = px.line(
        df,
        x="day",
        y=["net_sent_mean", "pos_mean", "neg_mean"],
        title="Daily sentiment (FinBERT) from GDELT headlines",
        hover_data=["n_articles"],
    )
    fig.show()

if __name__ == "__main__":
    main()