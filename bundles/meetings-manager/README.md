# ✦ Meetings Manager

> **macOS only** — requires [Paprwork](https://papr.ai), a native Mac AI workspace.

An AI-powered meeting manager for Paprwork. Schedule, prep, record, transcribe, and summarize meetings — with intelligent context pulled from your meeting history and memory.

![Meetings Manager](apps/ea6d8d7c-a15e-4c02-8273-117450b498f4/logo.svg)

---

## Features

- **Week view** — day-of-week pills with `‹ ›` week navigation, meeting dots for days with events
- **Meeting cards** — clean list per day showing time, attendees, live/soon/past status
- **AI Prep** — one-click meeting prep doc with TL;DR, attendee profiles, context from prior meetings, talking points, and recent news
- **Memory-first prep** — searches your PAPR Memory for prior meeting context before hitting the web; only web-enriches external attendees not already in memory
- **Relevance filtering** — prior meetings are classified as DIRECTLY_RELATED / TANGENTIALLY_RELATED / UNRELATED before being included in prep
- **Record & transcribe** — record meetings, auto-transcribe and summarize via the Meeting Summarizer job
- **Notes** — editable notes per meeting, auto-saved
- **Prep editing** — prep docs are editable and auto-saved
- **Memory sync** — summaries, participants, and key decisions are stored to PAPR Memory after each meeting for future prep lookups

---

## Requirements

- macOS (uses macOS-native audio capture via `sox`)
- [Paprwork](https://papr.ai) desktop app
- API keys (configured in Paprwork Settings → API Keys):
  - `ANTHROPIC_API_KEY` — for AI summarization and prep generation
  - `APOLLO_API_KEY` — for attendee enrichment (optional)
  - `EXA_API_KEY` — for recent news search (optional)

---

## Installation

### Via Paprwork (recommended)

1. Open Paprwork
2. Ask the AI: *"Import the Meetings Manager app from github.com/Papr-ai/paprwork-community-apps"*
3. The app and jobs install automatically

### Manual

```bash
# Clone the community apps repo
git clone https://github.com/Papr-ai/paprwork-community-apps
cd paprwork-community-apps/meetings-manager

# Import via Paprwork AI
# "Import app bundle from ~/path/to/meetings-manager"
```

---

## How it works

```
Google Calendar sync
        ↓
   Meeting cards (week view)
        ↓
   ✦ Prep button → Meeting Prep Agent
        ├── Searches PAPR Memory (prior meetings, attendee profiles)
        ├── Reads meeting DB for related prior meetings
        ├── Web enriches unknown external attendees (Apollo + Exa)
        └── Generates prep doc → saved to calendar_events.prep_doc
        ↓
   Record → Transcribe → Meeting Summarizer Job
        ↓
   Summary + notes saved → Memory Sync Job → PAPR Memory
```

---

## Privacy

This bundle contains **no personal data** — all database files and logs are excluded via `.gitignore`. Your meeting data stays on your machine in Paprwork's local SQLite database.

---

## Contributing

PRs welcome to [paprwork-community-apps](https://github.com/Papr-ai/paprwork-community-apps).
