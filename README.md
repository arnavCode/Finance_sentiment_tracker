# Finance Sentiment Tracker

A local-first financial sentiment analysis pipeline that ingests news data from GDELT, scores it using a finance-specific NLP model (FinBERT), and stores structured results in PostgreSQL for downstream predictive modeling.

---

## Current Status

- ✅ Local PostgreSQL database (no Docker)
- ✅ GDELT news ingestion (English-only scope)
- ✅ Raw article storage in `articles`
- ✅ FinBERT sentiment scoring
- ✅ Sentiment probabilities stored in `article_sentiment`
- ⏳ Daily sentiment aggregation (not yet implemented)
- ⏳ Price ingestion and predictive modeling (next phase)

---

## Architecture Overview

### Database: PostgreSQL (local)

#### `articles`

| Column        | Type              | Description               |
|--------------|------------------|---------------------------|
| id           | BIGSERIAL (PK)   | Unique article ID         |
| published_at | TIMESTAMPTZ      | Article timestamp         |
| source       | TEXT             | Domain or publisher       |
| title        | TEXT             | Article headline          |
| url          | TEXT (UNIQUE)    | Deduplication key         |
| raw_json     | JSONB            | Full GDELT record         |
| created_at   | TIMESTAMPTZ      | Insert timestamp          |

---

#### `article_sentiment`

| Column      | Type              | Description                  |
|------------|------------------|------------------------------|
| article_id | BIGINT (FK)       | References `articles.id`     |
| model      | TEXT              | Sentiment model name         |
| pos        | DOUBLE PRECISION  | Positive probability         |
| neg        | DOUBLE PRECISION  | Negative probability         |
| neu        | DOUBLE PRECISION  | Neutral probability          |
| scored_at  | TIMESTAMPTZ       | Scoring timestamp            |

Primary key: `(article_id, model)`

---

## Project Structure

```
finance_sentiment_tracker/
│
├── .env
├── schema.sql
├── README.md
└── src/
    ├── ingest.py
    ├── score.py
    └── finbert.py
```

---

## Environment Setup

### 1. Install dependencies

```bash
pip install psycopg[binary] python-dotenv
pip install transformers torch
pip install gdeltdoc pandas
```

### 2. Configure database

Create a `.env` file in the project root:

```
DATABASE_URL=postgresql://app:app@localhost:5432/market
```

PostgreSQL runs locally and can be inspected using DBeaver or any PostgreSQL GUI.

---

## Data Pipeline

### Step 1 — Ingest News

```bash
python src/ingest.py
```

- Queries GDELT for English-language articles
- Inserts rows into `articles`
- Deduplicates via `UNIQUE(url)`

---

### Step 2 — Sentiment Scoring

```bash
python src/score.py
```

- Selects unscored articles
- Runs FinBERT (`ProsusAI/finbert`)
- Stores positive / negative / neutral probabilities in `article_sentiment`

---

## Example Validation Queries

Check article count:

```sql
SELECT COUNT(*) FROM public.articles;
```

Check sentiment count:

```sql
SELECT COUNT(*) FROM public.article_sentiment;
```

Inspect sentiment outputs:

```sql
SELECT a.title, s.pos, s.neg, s.neu
FROM public.articles a
JOIN public.article_sentiment s ON s.article_id = a.id
ORDER BY a.published_at DESC
LIMIT 10;
```

---

## Design Decisions (So Far)

- Local PostgreSQL for simplicity and full SQL control
- Headline-only sentiment scoring for consistency
- English-only ingestion to avoid multilingual noise
- Explicit probability storage instead of single-label classification
- Deterministic deduplication using `ON CONFLICT (url)`

---

## Current Limitations

- No daily aggregation layer
- No ticker/entity linking
- No price data integration
- No backtesting framework
- GDELT rate limiting requires controlled request frequency

---

## Roadmap

1. Implement daily sentiment aggregation views
2. Add ticker association logic
3. Ingest historical price data
4. Create forward-return training dataset
5. Build baseline predictive model
6. Incorporate related-company spillover signals

---

## Goal

Build a reproducible sentiment + market data research pipeline capable of generating leakage-safe training datasets and evaluating predictive performance on forward returns.
