#!/usr/bin/env python3
"""Read macOS Calendar events using EventKit (properly expands recurring events)."""

import EventKit
import datetime
import sqlite3
import hashlib
import json
from Foundation import NSDate

import glob
import os

def find_meetings_db():
    """Find the meetings database dynamically (works on any machine)."""
    for db_path in sorted(glob.glob(os.path.expanduser("~/PAPR/jobs/*/data/data.db"))):
        try:
            conn = sqlite3.connect(db_path)
            tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            conn.close()
            if "meetings" in tables:
                return db_path
        except Exception:
            continue
    raise RuntimeError("Could not find meetings database")

DB_PATH = find_meetings_db()

def main():
    store = EventKit.EKEventStore.alloc().init()

    now = datetime.datetime.now()
    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    fetch_start = start_of_today - datetime.timedelta(days=60)
    end_range = start_of_today + datetime.timedelta(days=30)

    start_ns = NSDate.dateWithTimeIntervalSince1970_(fetch_start.timestamp())
    end_ns = NSDate.dateWithTimeIntervalSince1970_(end_range.timestamp())

    predicate = store.predicateForEventsWithStartDate_endDate_calendars_(start_ns, end_ns, None)
    events = store.eventsMatchingPredicate_(predicate)

    print(f"Found {len(events)} events (including recurring instances)")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS calendar_events (
        id TEXT PRIMARY KEY,
        title TEXT,
        start_time TEXT,
        end_time TEXT,
        calendar_name TEXT,
        location TEXT DEFAULT '',
        meeting_id TEXT DEFAULT '',
        attendees TEXT DEFAULT '[]',
        prep_status TEXT DEFAULT '',
        prep_doc TEXT DEFAULT '',
        updated_at INTEGER DEFAULT (strftime('%s','now'))
    )""")

    cutoff = (start_of_today - datetime.timedelta(days=60)).strftime('%Y-%m-%dT00:00')
    conn.execute("DELETE FROM calendar_events WHERE start_time < ?", (cutoff,))

    inserted = 0
    skipped_allday = 0

    for e in events:
        title = e.title() or ""
        if not title.strip():
            continue

        if e.isAllDay():
            skipped_allday += 1
            continue

        sd = datetime.datetime.fromtimestamp(e.startDate().timeIntervalSince1970())
        ed = datetime.datetime.fromtimestamp(e.endDate().timeIntervalSince1970())
        cal_name = e.calendar().title() if e.calendar() else "Unknown"
        location = e.location() or ""

        start_str = sd.strftime('%Y-%m-%dT%H:%M')
        end_str = ed.strftime('%Y-%m-%dT%H:%M')

        # Extract attendees
        attendee_list = []
        raw_attendees = e.attendees() or []
        for a in raw_attendees:
            name = a.name() or ""
            email = ""
            if a.URL():
                email = a.URL().resourceSpecifier() or ""
            if "@group.calendar.google.com" in email:
                continue
            if name or email:
                attendee_list.append({"name": name, "email": email})

        # Add organizer
        organizer = e.organizer()
        if organizer:
            org_name = organizer.name() or ""
            org_email = ""
            if organizer.URL():
                org_email = organizer.URL().resourceSpecifier() or ""
            if org_email and "@group.calendar.google.com" not in org_email:
                existing_emails = [a["email"] for a in attendee_list]
                if org_email not in existing_emails:
                    attendee_list.insert(0, {"name": org_name, "email": org_email, "organizer": True})

        attendees_json = json.dumps(attendee_list)

        raw_id = f"{start_str}_{title[:30]}"
        event_id = hashlib.md5(raw_id.encode()).hexdigest()[:16]

        conn.execute("""INSERT INTO calendar_events 
            (id, title, start_time, end_time, calendar_name, location, attendees, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, strftime('%s','now'))
            ON CONFLICT(id) DO UPDATE SET
                title=excluded.title, start_time=excluded.start_time,
                end_time=excluded.end_time, calendar_name=excluded.calendar_name,
                location=excluded.location, attendees=excluded.attendees,
                updated_at=strftime('%s','now')""",
            (event_id, title, start_str, end_str, cal_name, location, attendees_json))

        print(f"  {sd.strftime('%a %b %d %H:%M')} — {title} ({len(attendee_list)} attendees)")
        inserted += 1

    conn.commit()

    # Match unlinked calendar events to recorded meetings
    # Strategy: same calendar day + title word overlap (ignoring generic "Meeting — " titles)
    # Falls back to nearest-time match for generic titled meetings
    unlinked = conn.execute(
        "SELECT id, title, start_time FROM calendar_events WHERE meeting_id IS NULL OR meeting_id = ''"
    ).fetchall()

    matched = 0
    for ev_id, ev_title, ev_start in unlinked:
        try:
            ev_dt = datetime.datetime.strptime(ev_start, '%Y-%m-%dT%H:%M')
        except ValueError:
            continue

        day_str = ev_dt.strftime('%Y-%m-%d')
        # Exact title match + same day only
        match = conn.execute(
            "SELECT id FROM meetings WHERE LOWER(title) = LOWER(?) AND date LIKE ?",
            (ev_title, day_str + '%')
        ).fetchone()

        if match:
            conn.execute(
                "UPDATE calendar_events SET meeting_id = ? WHERE id = ?",
                (match[0], ev_id)
            )
            print(f"  Linked: '{ev_title}' → meeting {match[0][:8]}…")
            matched += 1

    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM calendar_events").fetchone()[0]
    conn.close()
    print(f"\nDone. {inserted} events upserted, {skipped_allday} all-day skipped, {matched} meetings linked. {total} total in DB.")

if __name__ == "__main__":
    main()
