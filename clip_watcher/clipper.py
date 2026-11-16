"""
Video extraction module using FFmpeg.
Cuts time-bounded highlight segments from the recorded live transport stream.
"""

import shutil
import subprocess
from pathlib import Path
from typing import Optional


class StreamClipper:
    def __init__(self, ffmpeg_path: Optional[str] = None):
        self.ffmpeg_path = ffmpeg_path or shutil.which("ffmpeg")
        if not self.ffmpeg_path:
            raise FileNotFoundError(
                "ffmpeg executable not found in PATH. Install ffmpeg to enable video cutting."
            )

    def cut_clip(
        self,
        stream_file: Path,
        start_seconds: float,
        duration_seconds: float,
        output_path: Path,
        fast_copy: bool = True,
    ) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        safe_start = max(0.0, start_seconds)

        cmd = [
            self.ffmpeg_path,
            "-y",
            "-i",
            str(stream_file.resolve()),
            "-ss",
            f"{safe_start:.2f}",
            "-t",
            f"{duration_seconds:.2f}",
        ]

        if fast_copy:
            cmd.extend(["-c", "copy", "-avoid_negative_ts", "make_zero", str(output_path.resolve())])
        else:
            cmd.extend([
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "22",
                "-c:a", "aac",
                "-b:a", "192k",
                str(output_path.resolve())
            ])

        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg failed with exit code {res.returncode}: {res.stderr[:300]}")

        return output_path
