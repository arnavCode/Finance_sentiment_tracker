Finance Sentiment Tracker

A local-first financial sentiment analysis pipeline that ingests news data, scores it using a domain-specific NLP model (FinBERT), and stores structured results in PostgreSQL for downstream predictive modeling.

Current Status

The project currently supports:
	•	✅ Local PostgreSQL database (no Docker)
	•	✅ GDELT news ingestion (English-filtered scope)
	•	✅ Storage of raw article data in articles
	•	✅ FinBERT-based sentiment scoring
	•	✅ Storage of sentiment probabilities in article_sentiment
	•	⏳ Daily sentiment aggregation (not yet implemented)
	•	⏳ Price ingestion and predictive modeling (next phase)

⸻

Architecture Overview

Database: PostgreSQL (local)

articles

Stores raw news data from GDELT.

Column	Type	Description
id	BIGSERIAL (PK)	Unique article ID
published_at	TIMESTAMPTZ	Article timestamp
source	TEXT	Domain or publisher
title	TEXT	Headline
url	TEXT (UNIQUE)	De-duplication key
raw_json	JSONB	Full GDELT record
created_at	TIMESTAMPTZ	Insert timestamp

article_sentiment

Stores FinBERT probabilities.

Column	Type	Description
article_id	BIGINT (FK)	References articles.id
model	TEXT	Sentiment model name
pos	DOUBLE	Positive probability
neg	DOUBLE	Negative probability
neu	DOUBLE	Neutral probability
scored_at	TIMESTAMPTZ	Scoring timestamp

Primary key: (article_id, model)

⸻

Project Structure

finance_sentiment_tracker/
│
├── .env
├── schema.sql
├── README.md
└── src/
    ├── ingest.py
    ├── score.py
    └── finbert.py


⸻

Environment Setup

1) Install dependencies

pip install psycopg[binary] python-dotenv
pip install transformers torch
pip install gdeltdoc pandas

2) Configure database

.env

DATABASE_URL=postgresql://app:app@localhost:5432/market

PostgreSQL runs locally and is accessed via DBeaver for inspection.

⸻

Data Pipeline

Step 1 — Ingest News

python src/ingest.py
	•	Queries GDELT for English articles
	•	Inserts into articles
	•	Deduplicates using UNIQUE(url)

Step 2 — Sentiment Scoring

python src/score.py
	•	Selects unscored articles
	•	Uses FinBERT (ProsusAI/finbert)
	•	Stores positive / negative / neutral probabilities

⸻

Design Decisions (So Far)
	•	Local Postgres instead of Docker for simplicity.
	•	Headline-only sentiment scoring for consistency.
	•	English-only ingestion to avoid multilingual noise.
	•	ON CONFLICT (url) used for deterministic de-duplication.
	•	Explicit probability storage instead of single label classification.

⸻

Example Validation Queries

Check article count:

SELECT COUNT(*) FROM public.articles;

Check sentiment count:

SELECT COUNT(*) FROM public.article_sentiment;

Inspect sentiment results:

SELECT a.title, s.pos, s.neg, s.neu
FROM public.articles a
JOIN public.article_sentiment s ON s.article_id = a.id
ORDER BY a.published_at DESC
LIMIT 10;


⸻

Next Steps
	1.	Implement daily sentiment aggregation view
	2.	Add ticker association logic
	3.	Ingest historical price data
	4.	Create forward-return training dataset
	5.	Build first baseline predictive model

⸻

Current Limitations
	•	No company-level entity linking yet
	•	No sentiment aggregation (daily or rolling)
	•	No price data integration
	•	No backtesting framework
	•	GDELT rate limiting requires cautious request frequency

⸻

Goal

To build a reproducible sentiment + market data research pipeline capable of:
	•	Generating daily sentiment signals
	•	Combining sentiment with fundamentals
	•	Incorporating related-company spillover
	•	Producing leakage-safe training datasets
	•	Evaluating predictive performance on forward returns
