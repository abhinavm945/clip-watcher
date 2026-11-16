# Operational Instructions for Clip Watcher

These instructions govern autonomous AI agent execution of Clip Watcher within terminal sessions and coding IDEs.

## Workflow Overview

```
Broadcast Online ──> Streamlink (stream.ts)
                         │
Twitch IRC ─────────> Velocity Tracker (chat.log)
                         │
                    Spike Detector (>3x baseline)
                         │
                         ├──> FFmpeg Cut (-30s offset, 45s duration)
                         │
                         └──> Whisper Transcription + Caption Burn
                                  │
                                  └──> Streamer Attribution Metadata
```

## Step-by-Step Agent Procedures

### Step 1: Environment & Dependency Check
Verify prerequisites before beginning execution:
- `streamlink --version`
- `ffmpeg -version`
- `whisper-cli --help` or `whisper --help` (optional for captions)

Install missing Python packages:
```bash
pip install -r requirements.txt
```

### Step 2: Channel Initialization
Target the streamer channel without leading `#`:
```bash
python -m clip_watcher watch --channel streamername --output-dir ./clips
```

### Step 3: Headless Execution & Background Monitoring
When running autonomously overnight or in the background:
- Monitor process output for `Spike detected` notifications.
- Harvest completed clips from the `./clips` directory.
- Verify `credits.txt` is populated for each generated MP4.

### Step 4: Ethical Compliance & Fair Use
- Maintain the original streamer username in all exported file metadata.
- Do not remove or alter creator credit files.
- Link the streamer's live Twitch URL on all social distribution channels.
