import os
import json
import time
from datetime import datetime, timezone

import duckdb
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()
APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")

COUNTRY = "us"
SEARCH_TERMS = ["data engineer", "data analyst", "analytics engineer"]
PAGES_PER_TERM = 3        # 50 results per page
MAX_DAYS_OLD = 3          # only recent postings
DB_PATH = "jobs.duckdb"

RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def fetch_page(term, page, retries=4):
    url = f"https://api.adzuna.com/v1/api/jobs/{COUNTRY}/search/{page}"
    params = {
        "app_id": APP_ID,
        "app_key": APP_KEY,
        "what_phrase": term,
        "results_per_page": 50,
        "max_days_old": MAX_DAYS_OLD,
        "sort_by": "date",
        "content-type": "application/json",
    }
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, params=params, timeout=60)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            error = type(e).__name__
        else:
            if r.status_code not in RETRYABLE_STATUS:
                r.raise_for_status()  # errors like 401 (bad keys) stop immediately
                return r.json().get("results", [])
            error = f"HTTP {r.status_code}"

        if attempt == retries:
            raise RuntimeError(f"Adzuna request failed after {retries} attempts: {error}")
        wait = 30 * attempt
        print(f"Attempt {attempt} failed ({error}); retrying in {wait}s...", flush=True)
        time.sleep(wait)


def to_row(job, term, ingested_at):
    return {
        "job_id": str(job["id"]),
        "search_term": term,
        "title": job.get("title"),
        "company": (job.get("company") or {}).get("display_name"),
        "location": (job.get("location") or {}).get("display_name"),
        "description": job.get("description"),
        "created_at": job.get("created"),
        "salary_min": job.get("salary_min"),
        "salary_max": job.get("salary_max"),
        "contract_time": job.get("contract_time"),
        "category": (job.get("category") or {}).get("label"),
        "redirect_url": job.get("redirect_url"),
        "raw_json": json.dumps(job),
        "ingested_at": ingested_at,
    }


def main():
    if not APP_ID or not APP_KEY:
        raise SystemExit("Missing API keys. Check your .env file.")

    ingested_at = datetime.now(timezone.utc).replace(tzinfo=None)
    rows = []

    for term in SEARCH_TERMS:
        for page in range(1, PAGES_PER_TERM + 1):
            results = fetch_page(term, page)
            print(f"'{term}' page {page}: {len(results)} postings")
            rows.extend(to_row(j, term, ingested_at) for j in results)
            if len(results) < 50:
                break
            time.sleep(2)  # be polite to the API

    if not rows:
        print("No postings returned.")
        return

    df = pd.DataFrame(rows).drop_duplicates(subset="job_id")
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True).dt.tz_localize(None)

    con = duckdb.connect(DB_PATH)
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    con.execute("""
        CREATE TABLE IF NOT EXISTS raw.job_postings (
            job_id VARCHAR PRIMARY KEY,
            search_term VARCHAR,
            title VARCHAR,
            company VARCHAR,
            location VARCHAR,
            description VARCHAR,
            created_at TIMESTAMP,
            salary_min DOUBLE,
            salary_max DOUBLE,
            contract_time VARCHAR,
            category VARCHAR,
            redirect_url VARCHAR,
            raw_json VARCHAR,
            ingested_at TIMESTAMP
        )
    """)

    before = con.execute("SELECT COUNT(*) FROM raw.job_postings").fetchone()[0]
    con.register("new_jobs", df)
    con.execute("""
        INSERT INTO raw.job_postings
        SELECT * FROM new_jobs
        WHERE job_id NOT IN (SELECT job_id FROM raw.job_postings)
    """)
    after = con.execute("SELECT COUNT(*) FROM raw.job_postings").fetchone()[0]
    con.close()

    print(f"Fetched {len(df)} postings, inserted {after - before} new. Total: {after}")


if __name__ == "__main__":
    main()