# Clip Watcher: Autonomous Stream Highlight Clipper

Clip Watcher is an autonomous pipeline and AI assistant skill that monitors live Twitch broadcasts, tracks audience reaction velocity without requiring a user account, extracts precision 1-minute highlight clips (40 seconds prior to chat reaction + 20 seconds after), burns synchronized subtitles via Whisper, and packages clips with mandatory creator attribution.

* **Published on AIStoreHub:** [https://www.aistorehub.in/abhinavm945/catalog/clip-watcher](https://www.aistorehub.in/abhinavm945/catalog/clip-watcher)
* **GitHub Repository:** [https://github.com/abhinavm945/clip-watcher](https://github.com/abhinavm945/clip-watcher)
* **Live Target Example:** [https://www.twitch.tv/lexigraham](https://www.twitch.tv/lexigraham)
* **Author:** Abhinav Mishra (`@abhinavm945`)
* **License:** MIT License

---

## Architectural Workflow

```
[Live Twitch Broadcast: twitch.tv/lexigraham]
                         |
                         v
1. Streamlink Continuous Capture (stream.ts with -f force overwrite)
                         |
                         +---> 2. Anonymous Twitch IRC (chat.log)
                                      |
                                      v
                               3. Sliding Window Velocity Tracker
                                  (10s bucket vs 5-minute rolling average)
                                      |
                                      v (Velocity >= Multiplier Threshold)
                               4. Post-Reaction Buffering Delay (20s)
                                  (Buffers remaining 20s of broadcast to disk)
                                      |
                                      v
                               5. FFmpeg Container-Accurate Slicing
                                  (-i stream.ts -ss <start> -t 60 -c copy)
                                  [40s Earlier + 20s After = 60s Total]
                                      |
                                      v
                               6. Whisper Transcription & Caption Burning
                                      |
                                      v
                               7. Streamer Attribution & Credits Packaging
```

---

## Five Core Pillars

1. **Continuous Stream Capture Without Gaps:** Uses Streamlink with persistent retry policies (`--retry-streams 30`) and forced overwrite (`-f`) to capture the broadcast into a local stream buffer (`stream.ts`) without missing opening moments or stalling on TTY prompts.
2. **Account-Free Anonymous IRC:** Connects directly to `irc.chat.twitch.tv:6667` with a read-only `justinfan` handle. No Twitch API keys, OAuth tokens, developer credentials, or user accounts are required.
3. **Statistical Velocity Analysis:** Tracks incoming messages per 10-second sliding window relative to a rolling 5-minute baseline. Computes velocity ratios in real time, detecting sudden audience surges that indicate clutch plays, funny moments, or high-energy gameplay.
4. **Precision 1-Minute Clip Timing:** Viewers typically react in chat 15 to 30 seconds after an on-stream event. Clip Watcher calculates the start point **40 seconds prior** to the reaction, buffers **20 seconds after** the reaction, and cuts an exact **60-second highlight**. FFmpeg is executed with `-i` before `-ss` to ensure frame-accurate seeking across fragmented MP4 (fMP4) stream chunks.
5. **Whisper Transcription & Creator Credit:** Generates synchronized `.srt` subtitles using Whisper and burns high-contrast captions into the output video. Automatically compiles a credits manifest with the streamer handle, live channel URL, and timestamp.

---

## Input and Output Specifications

### Pipeline Inputs

| Parameter | CLI Flag | Type | Required | Default | Description | Example |
|---|---|---|---|---|---|---|
| `channel` | `--channel`, `-c` | string | Yes | - | Twitch username or live stream channel handle. | `lexigraham` |
| `output_dir` | `--output-dir`, `-o` | path | No | `./clips` | Target directory for highlight MP4s and credit logs. | `./clips` |
| `multiplier` | `--multiplier`, `-m` | float | No | `2.0` | Velocity threshold multiplier over rolling 5-min baseline. | `1.5` to `3.0` |
| `min_messages` | `--min-messages` | integer | No | `2` | Minimum messages in a 10s window to qualify as a spike. | `2` (relaxed) or `8` (high-traffic) |
| `pre_roll` | `--pre-roll` | integer | No | `40` | Seconds to look backward prior to chat reaction. | `40` seconds |
| `post_roll` | `--post-roll` | integer | No | `20` | Seconds to buffer after chat reaction. | `20` seconds |
| `duration` | `--duration`, `-d` | integer | No | `60` | Total duration of the extracted video clip (1 minute). | `60` seconds |
| `whisper_model` | `--model`, `-m` | string | No | `ggml-medium.en.bin` | Speech-to-text model for subtitle synthesis. | `ggml-medium.en.bin` |

### Pipeline Outputs

| Output Asset | Format | Location | Description |
|---|---|---|---|
| Highlight Video | `.mp4` | `clips/clip_<channel>_<ts>.mp4` | Extracted 1-minute highlight clip (40s earlier, 20s after). |
| Captioned Video | `.mp4` | `clips/clip_<channel>_<ts>_captioned.mp4` | Highlight video with high-visibility burned subtitles. |
| Subtitle Track | `.srt` | `clips/clip_<channel>_<ts>.srt` | Synchronized speech transcript generated by Whisper. |
| Attribution JSON | `.json` | `clips/clip_<channel>_<ts>_attribution.json` | Structured metadata (streamer handle, stream URL, clip timestamp). |
| Creator Credits | `.txt` | `clips/clip_<channel>_<ts>_credits.txt` | Preformatted caption crediting the streamer for social distribution. |
| Stream Buffer | `.ts` | `stream.ts` | Rolling local transport stream of live broadcast. |
| Chat Velocity Log | `.log` | `chat.log` | Timestamped log of anonymous chat messages for velocity auditing. |

---

## Prerequisites

- **Python:** 3.10 or higher (`python --version`)
- **Streamlink:** `pip install streamlink`
- **FFmpeg:** Installed and added to system `PATH` (`ffmpeg -version`)
- **Whisper (Optional):** `whisper-cli` (whisper.cpp) or `pip install openai-whisper` for subtitle burning. Video extraction functions without Whisper installed.

---

## Installation

```bash
git clone https://github.com/abhinavm945/clip-watcher.git
cd clip-watcher
pip install -r requirements.txt
```

Via AIStoreHub CLI:
```bash
aihub pull @abhinavm945/catalog/clip-watcher
```

---

## Live Usage Guide

### 1. Watch and Automatically Clip (Live Example: lexigraham)
Start automated background monitoring for `https://www.twitch.tv/lexigraham`:
```bash
python -m clip_watcher watch --channel lexigraham --multiplier 1.5 --min-messages 2 --output-dir ./clips
```

For high-volume streams (e.g. esports tournaments, large streamers):
```bash
python -m clip_watcher watch --channel shroud --multiplier 3.0 --min-messages 8 --output-dir ./clips
```

### 2. Analyze Existing Chat Logs for Spikes
Evaluate reaction surges in an existing `chat.log` file without streaming video:
```bash
python -m clip_watcher analyze --log-file chat.log --multiplier 1.5 --window 10
```

Sample output:
```text
                     Chat Reaction Spikes (1.5x Threshold)                     
┌───────────────────────────┬─────────────────────┬────────────────────┬─────────────┐
│ Timestamp                 │ Window Rate (msg/s) │ Baseline Rate      │ Spike Ratio │
├───────────────────────────┼─────────────────────┼────────────────────┼─────────────┤
│ 2026-11-16T11:12:01+00:00 │                 0.2 │               0.11 │       1.76x │
│ 2026-11-16T11:18:31+00:00 │                 0.2 │               0.03 │       7.38x │
└───────────────────────────┴─────────────────────┴────────────────────┴─────────────┘
```

### 3. Manual Extraction from Stream Buffer
Extract an exact 1-minute segment from `stream.ts` starting at offset 120 seconds:
```bash
python -m clip_watcher cut --stream stream.ts --start 120.0 --duration 60 --output ./clips/highlight.mp4
```

### 4. Transcribe and Burn Subtitles
Transcribe audio and burn high-contrast captions:
```bash
python -m clip_watcher transcribe --clip ./clips/highlight.mp4
```

---

## Claude Code & AI Agent Skill Integration

Clip Watcher includes a complete `SKILL.md` specification. Point Claude Code, Cursor, or Codex directly to this skill:

```bash
claude "Monitor https://www.twitch.tv/lexigraham overnight with clip-watcher and compile the top 1-minute highlights with creator attribution."
```

The agent will execute `python -m clip_watcher watch`, supervise the recording process, handle video slicing, and deliver packaged clips with transcriptions and attribution logs.

---

## Creator Attribution and Fair Use Rule

Clip Watcher enforces ethical content curation:
- Every generated clip produces `credits.txt` and `attribution.json`.
- Streamer handles and live broadcast URLs (e.g. `https://www.twitch.tv/lexigraham`) must be retained on all distribution formats (Shorts, Reels, TikTok, X).
- Designed for transformative highlights, community moments, and esports commentary under fair use.

Example output in `credits.txt`:
```text
CREATOR CREDIT:
Streamer: lexigraham
Watch live at: https://twitch.tv/lexigraham
Timestamp: 2026-11-16T11:28:32.927722+00:00

Shorts/TikTok caption:
Crazy moment from @lexigraham! Link: https://twitch.tv/lexigraham #twitch #lexigraham
```

---

## License

MIT License. Copyright (c) 2026 Abhinav Mishra.
