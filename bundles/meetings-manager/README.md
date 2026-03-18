# Meetings Manager

An AI-powered meeting management app for macOS that handles the full lifecycle: **calendar sync → meeting prep → recording → transcription → summarization → memory sync**.

## What It Does

- **📅 Calendar Sync** — Reads your macOS Calendar (via EventKit) and displays upcoming meetings with attendees
- **🎙️ Recording** — Records system audio during meetings with one-click start/stop
- **✍️ Transcription** — Transcribes recordings using OpenAI Whisper
- **📝 AI Summarization** — Generates structured summaries with key decisions, action items, and follow-ups
- **🔍 Meeting Prep** — Auto-generates prep docs by searching PAPR Memory, prior meeting notes, and external sources (Apollo, Exa) for attendee context
- **🧠 Memory Sync** — Stores meeting summaries and participant profiles in PAPR Memory for future reference

## Pipeline (8 Jobs)

| Job | Type | What it does |
|-----|------|-------------|
| **Calendar Reader** | Python (EventKit) | Syncs macOS calendar events to SQLite — 60 days back, 30 days forward |
| **Check Screen Recording Permission** | Bash | Verifies macOS screen recording permission for audio capture |
| **System Audio Recorder** | Bash | Records system audio to WAV using native recorder binary |
| **Stop Recorder** | Bash | Sends stop signal to end recording |
| **Whisper Transcriber** | Python | Sends WAV to OpenAI Whisper API, writes transcript to DB |
| **Meeting Summarizer** | AI Agent | Generates structured summary + topic tags from transcript |
| **Meeting Prep Agent** | AI Agent | Builds prep docs from memory, prior notes, Apollo, and Exa |
| **Meeting Memory Sync** | AI Agent | Stores summaries and attendee profiles in PAPR Memory |

## Requirements

| Key | Required? | Used by |
|-----|-----------|---------|
| `ANTHROPIC_API_KEY` | **Yes** | Meeting Summarizer, Memory Sync, Prep Agent |
| `OPENAI_PLATFORM_KEY` | Optional | Whisper Transcriber (transcription) |
| `APOLLO_API_KEY` | Optional | Meeting Prep Agent (attendee enrichment) |
| `EXA_API_KEY` | Optional | Meeting Prep Agent (web search) |
| `PAPR_MEMORY_API_KEY` | Optional | Meeting Memory Sync (long-term memory storage) |

## Platform

**macOS only** — uses EventKit for calendar access and a native audio recorder binary.

## Install

Import this bundle in Paprwork → Community Apps, or manually:

```
paprwork import-bundle ./bundle-1773825249864
```

After import, grant Calendar and Screen Recording permissions when prompted.
