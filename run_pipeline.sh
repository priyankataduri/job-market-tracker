#!/bin/bash
set -e
cd "$(dirname "$0")"
mkdir -p logs
echo "=== Run started: $(date) ==="

# Wait up to 2 minutes for the internet connection (e.g. right after waking from sleep)
for i in {1..12}; do
  if curl -s --head --max-time 5 https://api.adzuna.com > /dev/null; then
    echo "Network is up."
    break
  fi
  echo "Waiting for network... ($i/12)"
  sleep 10
done

source venv/bin/activate
python ingest.py
cd jobs_dbt
dbt build
echo "=== Run finished: $(date) ==="