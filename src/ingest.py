# src/ingest.py
#
# Minimal GDELT -> Postgres ingestion script with robust rate-limit handling.
# Usage:
#   1) Ensure .env contains:
#        DATABASE_URL=postgresql://app:app@localhost:5432/market
#   2) Run:
#        python src/ingest.py
#
# Optional env vars:
#   GDELT_QUERY=Apple
#   GDELT_LOOKBACK_DAYS=1
#   GDELT_NUM_RECORDS=10
#   GDELT_MAX_RETRIES=8
#   GDELT_BASE_SLEEP_SECONDS=6

import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import psycopg
from dotenv import load_dotenv
from gdeltdoc import GdeltDoc, Filters
from gdeltdoc.errors import RateLimitError
from psycopg.types.json import Jsonb


def _require_env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return v


def fetch_gdelt_articles(
    query: str,
    lookback_days: int,
    num_records: int,
    max_retries: int,
    base_sleep_seconds: int,
) -> List[Dict[str, Any]]:
    """
    Fetch headline-level articles from GDELT via gdeltdoc.

    GDELT commonly rate-limits (roughly one request per ~5 seconds).
    num_records controls items per request, NOT request frequency.
    """
    gd = GdeltDoc()
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=lookback_days)

    filters = Filters(
        keyword=query,
        start_date=start,
        end_date=end,
        num_records=num_records,
        language="english",
    )

    for attempt in range(1, max_retries + 1):
        try:
            df = gd.article_search(filters)
            if df is None or df.empty:
                return []
            return df.to_dict(orient="records")
        except RateLimitError:
            # Conservative backoff; don't hammer. GDELT wants ~>=5s between requests.
            sleep_s = max(base_sleep_seconds, base_sleep_seconds * attempt)
            print(f"[GDELT] Rate limited. Sleeping {sleep_s}s (attempt {attempt}/{max_retries})...")
            time.sleep(sleep_s)
        except Exception as e:
            # Bubble up unknown errors; they are not rate limit.
            raise RuntimeError(f"GDELT fetch failed: {e}") from e

    raise RuntimeError("GDELT rate limit persisted after retries; wait a minute and try again.")


def to_published_at(value: Any) -> Optional[datetime]:
    """
    gdeltdoc commonly returns 'seendate' as:
      - a pandas Timestamp
      - an ISO-ish string
    psycopg can adapt datetimes; strings may work but we normalize if possible.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        # Ensure timezone-aware
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    # Try a few common formats
    s = str(value).strip()
    try:
        # ISO 8601
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None  # fallback handled by caller


def upsert_articles(db_url: str, rows: List[Dict[str, Any]]) -> int:
    """
    Insert articles into public.articles, de-duping via UNIQUE(url) constraint.
    """
    inserted = 0
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            for r in rows:
                published_at = to_published_at(r.get("seendate")) or datetime.now(timezone.utc)
                source = r.get("domain") or r.get("sourceCountry") or None
                title = r.get("title") or ""
                url = r.get("url")

                # Skip rows without URL (for MVP simplicity).
                # If you want to store them, we need a different de-dupe key (e.g., hash).
                if not url:
                    continue

                cur.execute(
                    """
                    INSERT INTO public.articles
                      (published_at, source, title, url, raw_json)
                    VALUES
                      (%s, %s, %s, %s, %s)
                    ON CONFLICT (url) DO NOTHING
                    """,
                    (published_at, source, title, url, Jsonb(r)),
                )
                # rowcount is 1 if inserted, 0 if conflict-do-nothing
                inserted += cur.rowcount

    return inserted


def main() -> None:
    load_dotenv()

    db_url = _require_env("DATABASE_URL")
    query = os.getenv("GDELT_QUERY", "Apple")
    lookback_days = int(os.getenv("GDELT_LOOKBACK_DAYS", "1"))
    num_records = int(os.getenv("GDELT_NUM_RECORDS", "10"))
    max_retries = int(os.getenv("GDELT_MAX_RETRIES", "8"))
    base_sleep_seconds = int(os.getenv("GDELT_BASE_SLEEP_SECONDS", "6"))

    print(
        f"[Config] query={query!r} lookback_days={lookback_days} "
        f"num_records={num_records} max_retries={max_retries} "
        f"base_sleep_seconds={base_sleep_seconds}"
    )

    # If you've been iterating quickly, a small initial sleep helps avoid immediate rate-limit.
    # Comment out once you're not repeatedly rerunning.
    time.sleep(2)

    rows = fetch_gdelt_articles(
        query=query,
        lookback_days=lookback_days,
        num_records=num_records,
        max_retries=max_retries,
        base_sleep_seconds=base_sleep_seconds,
    )
    print(f"[GDELT] fetched={len(rows)}")

    inserted = upsert_articles(db_url, rows)
    print(f"[DB] inserted={inserted} (dedup via url)")

    # Quick verification query
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM public.articles;")
            total = cur.fetchone()[0]
            print(f"[DB] total_articles={total}")


if __name__ == "__main__":
    main()
