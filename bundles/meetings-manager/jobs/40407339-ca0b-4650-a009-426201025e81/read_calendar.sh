#!/bin/bash
# Find meetings DB dynamically
DB=$(for db in ~/PAPR/jobs/*/data/data.db; do sqlite3 "$db" "SELECT name FROM sqlite_master WHERE name='meetings'" 2>/dev/null | grep -q meetings && echo "$db" && break; done)
if [ -z "$DB" ]; then echo "ERROR: meetings DB not found"; exit 1; fi
echo "Using DB: $DB"
python3 read_calendar.py "$DB"
