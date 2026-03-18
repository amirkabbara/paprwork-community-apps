#!/usr/bin/env python3
"""Meeting Monitor - Calendar + process detection."""
import sqlite3, subprocess, os, json, glob, uuid
from datetime import datetime, timedelta

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'monitor_state.json')

def find_meetings_db():
    for p in sorted(glob.glob(os.path.expanduser('~/PAPR/jobs/*/data/data.db'))):
        try:
            c = sqlite3.connect(p)
            t = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            c.close()
            if 'meetings' in t and 'calendar_events' in t:
                return p
        except: continue
    raise RuntimeError('No meetings DB found')

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f: return json.load(f)
        except: pass
    return {'notified': {}, 'proc_notified': {}, 'cleanup': ''}

def save_state(s):
    with open(STATE_FILE, 'w') as f: json.dump(s, f)

APP_ID = 'ea6d8d7c-a15e-4c02-8273-117450b498f4'

def notify(title, msg, subtitle='', meeting_id=None):
    open_url = f'paprwork://app/{APP_ID}?meeting={meeting_id}' if meeting_id else f'paprwork://app/{APP_ID}'
    cmd = ['terminal-notifier',
           '-title', title,
           '-message', msg,
           '-sound', 'default',
           '-group', 'paprwork-meeting',
           '-actions', 'Record',
           '-closeLabel', 'Dismiss',
           '-open', open_url]
    if subtitle: cmd += ['-subtitle', subtitle]
    subprocess.run(cmd, capture_output=True)
    print(f'NOTIFIED: {title} - {subtitle} - {msg} (url: {open_url})')

def check_calendar(conn, state):
    now = datetime.now()
    today = now.strftime('%Y-%m-%d')
    events = conn.execute(
        'SELECT id, title, start_time, location FROM calendar_events WHERE start_time LIKE ? AND start_time >= ? ORDER BY start_time',
        (today+'%', now.strftime('%Y-%m-%dT%H:%M'))
    ).fetchall()
    for ev_id, title, start_time, location in events:
        try: ev_start = datetime.strptime(start_time, '%Y-%m-%dT%H:%M')
        except: continue
        mins = (ev_start - now).total_seconds() / 60
        if 0 <= mins <= 2:
            key = f'{ev_id}_{today}'
            if key not in state['notified']:
                t = ev_start.strftime('%I:%M %p').lstrip('0')
                msg = title
                if location and any(x in location.lower() for x in ['zoom','meet.google','teams']):
                    msg += ' (video call)'
                # Auto-create meeting in DB if not linked
                linked = conn.execute('SELECT meeting_id FROM calendar_events WHERE id=?', (ev_id,)).fetchone()
                mid = linked[0] if linked and linked[0] else None
                if not mid:
                    mid = str(uuid.uuid4())
                    conn.execute('INSERT OR IGNORE INTO meetings (id,title,date,status) VALUES (?,?,?,?)',
                                 (mid, title, now.isoformat(), 'scheduled'))
                    conn.execute('UPDATE calendar_events SET meeting_id=? WHERE id=?', (mid, ev_id))
                    conn.commit()
                    print(f'Created meeting: {title} ({mid[:8]})')
                notify('Meeting Starting', msg, f'At {t}', meeting_id=mid)
                state['notified'][key] = now.isoformat()

def check_processes(conn, state):
    now = datetime.now()
    today = now.strftime('%Y-%m-%d')
    try: ps = subprocess.check_output(['ps','aux'], text=True)
    except: return
    active = []
    if 'CptHost' in ps or 'aomhost' in ps: active.append('Zoom')
    try:
        r = subprocess.run(['osascript','-e','tell app "Google Chrome" to get URL of active tab of first window'],
                          capture_output=True, text=True, timeout=3)
        if 'meet.google.com' in (r.stdout or ''): active.append('Google Meet')
    except: pass
    if 'MSTeamsCall' in ps: active.append('Teams')
    if not active:
        state['proc_notified'] = {}
        return
    cur = conn.execute('SELECT id FROM calendar_events WHERE start_time<=? AND end_time>=? AND start_time LIKE ?',
        (now.strftime('%Y-%m-%dT%H:%M'), now.strftime('%Y-%m-%dT%H:%M'), today+'%')).fetchone()
    if cur: return
    app = active[0]
    key = f'{app}_{now.strftime("%Y%m%d%H")}'
    if key not in state['proc_notified']:
        notify('Unscheduled Meeting', f'{app} call detected \u2014 want to record?', app, meeting_id=None)
        state['proc_notified'][key] = now.isoformat()

def main():
    conn = sqlite3.connect(find_meetings_db())
    state = load_state()
    today = datetime.now().strftime('%Y-%m-%d')
    if state.get('cleanup') != today:
        cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
        state['notified'] = {k:v for k,v in state['notified'].items() if v > cutoff}
        state['proc_notified'] = {}
        state['cleanup'] = today
    check_calendar(conn, state)
    check_processes(conn, state)
    save_state(state)
    conn.close()
    print(f'Check done {datetime.now().strftime("%H:%M:%S")}')

if __name__ == '__main__': main()
