---
name: clip-watcher
description: Autonomous live stream highlight clipping pipeline for Twitch broadcasts. Monitors anonymous IRC chat velocity, detects 3x reaction surges, extracts video clips with FFmpeg (-30s pre-roll), transcribes subtitles via Whisper, and generates streamer credit metadata. Tested live with https://www.twitch.tv/lexigraham.
author: abhinavm945
version: 1.0.0
inputs:
  channel: Twitch username or stream handle (e.g. lexigraham)
  output_dir: Directory for saved clips (default: ./clips)
  multiplier: Chat velocity surge threshold (default: 3.0x)
  pre_roll: Offset seconds prior to chat reaction (default: 30s)
  duration: Video clip duration in seconds (default: 45s)
outputs:
  raw_clip: clips/clip_<channel>_<ts>_raw.mp4
  captioned_clip: clips/clip_<channel>_<ts>.mp4
  subtitles: clips/clip_<channel>_<ts>.srt
  attribution: clips/clip_<channel>_<ts>_attribution.json
  credits: clips/clip_<channel>_<ts>_credits.txt
tags:
  - twitch
  - live-streaming
  - video-clipping
  - ffmpeg
  - whisper
  - autonomous-agent
  - claude-code
---

# Clip Watcher: Autonomous Stream Highlight Clipper

Clip Watcher is an autonomous execution skill for AI coding assistants (Claude Code, Cursor, Windsurf) and background daemons. It monitors live broadcasts, tracks chat velocity without requiring a user account, detects moments of intense audience reaction, and cuts highlight clips with burned subtitles and creator attribution.

## Core Operational Mechanics

1. **Continuous Stream Recording:** Runs `streamlink` with continuous reconnection retry (`--retry-streams 30`), capturing the raw broadcast to `stream.ts`.
2. **Anonymous Chat Velocity Tracking:** Connects to Twitch IRC (`irc.chat.twitch.tv:6667`) using anonymous credentials (`justinfan<random>`), logging timestamps to `chat.log`.
3. **Statistical Spike Detection:** Computes sliding 10-second message velocity against a rolling 5-minute baseline. When chat rate surges to 3x baseline, a highlight spike is triggered.
4. **Time-Offset Video Extraction:** Cuts 45-second segments starting 30 seconds before the chat reaction using FFmpeg (`-ss <spike-30> -t 45 -i stream.ts -c copy`).
5. **Whisper Transcription & Subtitle Burning:** Transcribes audio to `.srt` format using `whisper-cli` and burns high-visibility captions into the final video.
6. **Mandatory Streamer Attribution:** Automatically produces `credits.txt` and `attribution.json` containing the original streamer URL, handle, and fair-use attribution notice.

## Live Target Demonstration
Tested and verified with live Twitch channel: `https://www.twitch.tv/lexigraham`.

## AI Assistant Directives

When instructed to watch, monitor, or clip a stream, perform the following steps:

### 1. Launch Continuous Monitoring
```bash
python -m clip_watcher watch --channel lexigraham --output-dir ./clips
```

### 2. Inspect Existing Chat Logs for Spikes
When given an existing `chat.log` file, inspect velocity spikes:
```bash
python -m clip_watcher analyze --log-file chat.log --multiplier 3.0
```

### 3. Extract Specific Timestamp Highlights
When a spike is detected at offset `$T` seconds:
```bash
# Calculate start = T - 30s
python -m clip_watcher cut --stream stream.ts --start <T-30> --duration 45 --output ./clips/highlight.mp4
```

### 4. Burn Subtitles and Generate Attribution
```bash
python -m clip_watcher transcribe --clip ./clips/highlight.mp4
```

## Mandatory Attribution Rule
Every generated clip must credit the original streamer and include a direct link to their live channel (e.g. `https://www.twitch.tv/lexigraham`).
