"""
Streamer attribution and fair-use credit generator.
Enforces the mandatory rule: always clip, credit, and link the original content creator.
"""

import json
from datetime import datetime, timezone
from pathlib import Path


class AttributionManager:
    @staticmethod
    def generate_credits(
        channel: str,
        clip_name: str,
        output_dir: Path,
        stream_timestamp: str,
        duration_seconds: float,
    ) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        channel_clean = channel.lower().lstrip("#")
        stream_url = f"https://twitch.tv/{channel_clean}"
        
        metadata = {
            "clip_name": clip_name,
            "creator": channel_clean,
            "stream_url": stream_url,
            "clipped_at": datetime.now(timezone.utc).isoformat(),
            "stream_timestamp": stream_timestamp,
            "duration_seconds": duration_seconds,
            "attribution_text": f"Clip credit: @{channel_clean} ({stream_url})",
            "fair_use_notice": "Highlight extracted for transformative commentary, archival, and fair-use distribution.",
        }

        json_path = output_dir / f"{clip_name}_attribution.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        txt_path = output_dir / f"{clip_name}_credits.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"CREATOR CREDIT:\n")
            f.write(f"Streamer: {channel_clean}\n")
            f.write(f"Watch live at: {stream_url}\n")
            f.write(f"Timestamp: {stream_timestamp}\n\n")
            f.write(f"Shorts/TikTok caption:\n")
            f.write(f"Crazy moment from @{channel_clean}! Link: {stream_url} #twitch #{channel_clean}\n")

        return json_path
