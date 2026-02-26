# src/score.py
import os
import psycopg
from dotenv import load_dotenv
from finbert import MODEL_NAME, score_titles

load_dotenv()
DB = os.environ["DATABASE_URL"]

def fetch_unscored(limit: int = 200):
    with psycopg.connect(DB) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT a.id, a.title
                FROM public.articles a
                LEFT JOIN public.article_sentiment s
                  ON s.article_id = a.id AND s.model = %s
                WHERE s.article_id IS NULL
                ORDER BY a.published_at DESC
                LIMIT %s
                """,
                (MODEL_NAME, limit),
            )
            return cur.fetchall()

def insert_scores(rows, probs, id2label):
    # Determine which column index corresponds to pos/neg/neu
    label2idx = {label.lower(): idx for idx, label in id2label.items()}
    pos_i = label2idx["positive"]
    neg_i = label2idx["negative"]
    neu_i = label2idx["neutral"]

    with psycopg.connect(DB) as conn:
        with conn.cursor() as cur:
            for (article_id, _title), p in zip(rows, probs):
                pos = float(p[pos_i].item())
                neg = float(p[neg_i].item())
                neu = float(p[neu_i].item())

                cur.execute(
                    """
                    INSERT INTO public.article_sentiment
                      (article_id, model, pos, neg, neu)
                    VALUES
                      (%s, %s, %s, %s, %s)
                    ON CONFLICT (article_id, model) DO NOTHING
                    """,
                    (article_id, MODEL_NAME, pos, neg, neu),
                )

def main():
    rows = fetch_unscored()
    if not rows:
        print("No unscored articles.")
        return

    titles = [t for (_id, t) in rows]
    probs, id2label = score_titles(titles)

    insert_scores(rows, probs, id2label)
    print(f"Scored {len(rows)} articles with {MODEL_NAME}")

if __name__ == "__main__":
    main()