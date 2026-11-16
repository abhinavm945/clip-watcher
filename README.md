# Clip Watcher: Autonomous Stream Highlight Clipper

Clip Watcher is an autonomous pipeline and AI assistant skill that records live Twitch broadcasts, tracks audience reaction spikes via anonymous chat monitoring, cuts highlight clips with FFmpeg using pre-reaction time offsets, burns subtitles with Whisper, and packages clips with mandatory streamer credits.

Published on AIStoreHub: [https://www.aistorehub.in/abhinavm945/catalog/clip-watcher](https://www.aistorehub.in/abhinavm945/catalog/clip-watcher)

---

## Architectural Workflow

```
[Live Broadcast]
       |
       v
1. Streamlink Recording (stream.ts)
       |
       +---> 2. Anonymous Twitch IRC (chat.log)
                    |
                    v
             3. Sliding Window Velocity Tracker
                (10s bucket vs 5-minute rolling average)
                    |
                    v (Rate >= 3x Baseline)
             4. FFmpeg Clip Extraction
                (-30s reaction offset, 45s duration)
                    |
                    v
             5. Whisper Transcription & Caption Burning
                    |
                    v
             6. Streamer Attribution & Credits Packaging
```

---

## Five Key Components

1. **Continuous Stream Capture:** Uses Streamlink with persistent retry policies (`--retry-streams 30`) to wait until the broadcast goes live and record without missing the opening seconds.
2. **Account-Free Anonymous IRC:** Connects directly to `irc.chat.twitch.tv:6667` with a read-only `justinfan` handle. No Twitch API keys, OAuth tokens, or user accounts are required.
3. **Statistical Velocity Analysis:** Tracks messages per 10-second window relative to a rolling 5-minute baseline. Detects sudden audience surges (chat velocity exceeding 3x baseline) signaling high-energy gameplay, clutch plays, or funny moments.
4. **Pre-Reaction Offset Cutting:** Audience reactions lag behind stream events by 15 to 30 seconds. Clip Watcher automatically offsets the extraction start time backwards by 30 seconds to capture the initiating moment rather than just the aftermath.
5. **Whisper Transcription & Creator Credit:** Generates synchronized `.srt` subtitles using Whisper and burns high-visibility captions. Automatically compiles a credits manifest with the streamer handle, live channel URL, and timestamp.

---

## Prerequisites

- **Python:** 3.10 or higher
- **FFmpeg:** Installed and added to system `PATH`
- **Streamlink:** `pip install streamlink`
- **Whisper:** `whisper-cli` (whisper.cpp) or `openai-whisper` (optional, for burning subtitles)

---

## Installation

```bash
git clone https://github.com/abhinavm945/clip-watcher.git
cd clip-watcher
pip install -r requirements.txt
```

Via AIStoreHub CLI:
```bash
aihub pull @abhinavm945/clip-watcher
```

---

## CLI Usage

### 1. Watch and Automatically Clip
Start automated background monitoring for any Twitch channel:
```bash
python -m clip_watcher watch --channel shroud --output-dir ./clips
```

### 2. Analyze Existing Chat Logs
Find velocity spikes in an existing `chat.log` file:
```bash
python -m clip_watcher analyze --log-file chat.log --multiplier 3.0 --window 10
```

### 3. Manual Extraction
Extract a specific highlight offset:
```bash
python -m clip_watcher cut --stream stream.ts --start 1420.0 --duration 45 --output ./clips/highlight.mp4
```

### 4. Transcribe and Burn Subtitles
Transcribe audio and burn high-contrast captions:
```bash
python -m clip_watcher transcribe --clip ./clips/highlight.mp4
```

---

## Claude Code & AI Agent Integration

Clip Watcher includes a complete `SKILL.md` specification. You can point Claude Code, Cursor, or Codex directly to this repository:

```bash
claude "Monitor twitch.tv/streamer overnight with clip-watcher and summarize extracted highlights in the morning."
```

The agent will execute `python -m clip_watcher watch`, manage process lifecycle, and deliver completed clips with transcriptions and attribution logs.

---

## Creator Ethics and Fair Use

Clip Watcher enforces ethical content repurposing:
- Every clip generates a companion `credits.txt` and `attribution.json`.
- Streamer links and channel usernames must be preserved on all publishing destinations (YouTube Shorts, TikTok, Instagram Reels, X).
- Intended for transformative commentary, news aggregation, and community highlights under fair use.

---

## License

MIT License. Copyright (c) 2026 Abhinav Mishra.
