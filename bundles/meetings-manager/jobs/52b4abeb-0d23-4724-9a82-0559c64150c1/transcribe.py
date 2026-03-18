import subprocess, sqlite3, os, glob

# Dynamic path discovery
def find_meetings_db():
    for db in glob.glob(os.path.expanduser("~/PAPR/jobs/*/data/data.db")):
        try:
            conn = sqlite3.connect(db)
            tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            conn.close()
            if 'meetings' in tables:
                return db
        except: pass
    return None

def find_recorder_dir():
    for d in glob.glob(os.path.expanduser("~/PAPR/jobs/*/data/recording.wav")):
        return os.path.dirname(d)
    for d in glob.glob(os.path.expanduser("~/PAPR/jobs/*/recorder")):
        return os.path.join(os.path.dirname(d), "data")
    return None

MEETINGS_DB = find_meetings_db()
RECORDER_JOB_DIR = find_recorder_dir()

if not MEETINGS_DB:
    print("ERROR: meetings DB not found"); exit(1)
if not RECORDER_JOB_DIR:
    print("ERROR: recorder job dir not found"); exit(1)

AUDIO_PATH = os.path.join(RECORDER_JOB_DIR, "recording.wav")

print(f"DB: {MEETINGS_DB}")
print(f"Audio: {AUDIO_PATH}")

conn = sqlite3.connect(MEETINGS_DB)
rows = conn.execute("SELECT id, title FROM meetings WHERE status='recorded' AND (transcript IS NULL OR transcript='')").fetchall()

if not rows:
    print("No meetings to transcribe"); exit(0)

for mid, title in rows:
    print(f"Transcribing: {title} ({mid})")
    if not os.path.exists(AUDIO_PATH):
        print(f"  No audio file at {AUDIO_PATH}, skipping"); continue
    
    result = subprocess.run(
        ["curl", "-s", "https://api.openai.com/v1/audio/transcriptions",
         "-H", f"Authorization: Bearer {os.environ.get('OPENAI_API_KEY','')}",
         "-F", f"file=@{AUDIO_PATH}", "-F", "model=whisper-1"],
        capture_output=True, text=True
    )
    
    import json
    try:
        transcript = json.loads(result.stdout).get("text", "")
    except:
        print(f"  Whisper error: {result.stdout[:200]}"); continue
    
    conn.execute("UPDATE meetings SET transcript=?, status='pending', updated_at=strftime('%s','now') WHERE id=?", (transcript, mid))
    conn.commit()
    print(f"  Done - {len(transcript)} chars")

conn.close()
print("All done")
