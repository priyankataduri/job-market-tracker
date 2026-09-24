#!/bin/bash
set -e
cd "$(dirname "$0")"
mkdir -p logs
echo "=== Run started: $(date) ==="
source venv/bin/activate
python ingest.py
cd jobs_dbt
dbt build
echo "=== Run finished: $(date) ==="
