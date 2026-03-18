#!/bin/bash
DB="$HOME/PAPR/jobs/8eea1893-4ca5-48ed-bfb4-187b9456fb31/data/data.db"

echo "Creating calendar_events table..."
sqlite3 "$DB" "CREATE TABLE IF NOT EXISTS calendar_events (
  id TEXT PRIMARY KEY,
  title TEXT,
  start_time TEXT,
  end_time TEXT,
  calendar_name TEXT,
  location TEXT DEFAULT '',
  meeting_id TEXT DEFAULT '',
  updated_at INTEGER DEFAULT (strftime('%s','now'))
);"

echo "Querying Calendar.app (including recurring events)..."
EVENTS=$(osascript << 'APPLESCRIPT'
set output to ""
set today to current date
-- Start from midnight today
set startDay to today - (time of today)
-- End 8 days out
set endDay to startDay + (8 * days)

tell application "Calendar"
  repeat with c in calendars
    try
      -- This filter works on occurrence dates, so recurring events ARE included
      set evList to (every event of c whose start date >= startDay and start date < endDay)
      repeat with e in evList
        set t to summary of e
        if t is not "" then
          set sd to start date of e
          set ed to end date of e
          -- Skip all-day events (start at midnight, duration is exactly 1 day)
          set startH to hours of sd
          set startM to minutes of sd
          if not (startH = 0 and startM = 0) then
            set startStr to (year of sd as string) & "-" & text -2 thru -1 of ("0" & ((month of sd as integer) as string)) & "-" & text -2 thru -1 of ("0" & (day of sd as string)) & "T" & text -2 thru -1 of ("0" & (hours of sd as string)) & ":" & text -2 thru -1 of ("0" & (minutes of sd as string))
            set endStr to (year of ed as string) & "-" & text -2 thru -1 of ("0" & ((month of ed as integer) as string)) & "-" & text -2 thru -1 of ("0" & (day of ed as string)) & "T" & text -2 thru -1 of ("0" & (hours of ed as string)) & ":" & text -2 thru -1 of ("0" & (minutes of ed as string))
            set calName to name of c
            set row to startStr & "|||" & endStr & "|||" & t & "|||" & calName & "
"
            set output to output & row
          end if
        end if
      end repeat
    end try
  end repeat
end tell
return output
APPLESCRIPT
)

if [ $? -ne 0 ]; then
  echo "AppleScript failed"
  exit 1
fi

if [ -z "$EVENTS" ]; then
  echo "No events found in the next 8 days"
  exit 0
fi

echo "$EVENTS" | while IFS= read -r line; do
  [ -z "$line" ] && continue
  START=$(echo "$line" | awk -F'[|][|][|]' '{print $1}')
  END=$(echo "$line" | awk -F'[|][|][|]' '{print $2}')
  TITLE=$(echo "$line" | awk -F'[|][|][|]' '{print $3}')
  CAL=$(echo "$line" | awk -F'[|][|][|]' '{print $4}')
  [ -z "$START" ] && continue
  [ -z "$TITLE" ] && continue
  # ID = start_time + title — recurring instances get unique IDs per occurrence
  ID="${START}_${TITLE:0:30}"
  TITLE_SAFE=$(echo "$TITLE" | sed "s/'/''/g")
  CAL_SAFE=$(echo "$CAL" | sed "s/'/''/g")
  ID_SAFE=$(echo "$ID" | sed "s/'/''/g" | tr ' ' '_')
  echo "  $START — $TITLE"
  sqlite3 "$DB" "INSERT OR REPLACE INTO calendar_events (id, title, start_time, end_time, calendar_name, updated_at) VALUES ('$ID_SAFE', '$TITLE_SAFE', '$START', '$END', '$CAL_SAFE', strftime('%s','now'));"
done

# Remove stale events from before today
TODAY=$(date +%Y-%m-%dT00:00:00)
sqlite3 "$DB" "DELETE FROM calendar_events WHERE start_time < '$TODAY';"

COUNT=$(sqlite3 "$DB" "SELECT COUNT(*) FROM calendar_events;")
echo "Done. $COUNT events in DB (recurring instances included)."
