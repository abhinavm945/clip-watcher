"""
Audio transcription and caption burning module using Whisper and FFmpeg.
"""

import shutil
import subprocess
from pathlib import Path
from typing import Optional


class WhisperTranscriber:
    def __init__(
        self,
        model_name: str = "ggml-medium.en.bin",
        whisper_bin: str = "whisper-cli",
        ffmpeg_bin: Optional[str] = None,
    ):
        self.model_name = model_name
        self.whisper_bin = shutil.which(whisper_bin) or shutil.which("whisper")
        self.ffmpeg_bin = ffmpeg_bin or shutil.which("ffmpeg")

    def transcribe(self, clip_path: Path, output_srt: Optional[Path] = None) -> Optional[Path]:
        if not self.whisper_bin:
            return None

        if output_srt is None:
            output_srt = clip_path.with_suffix(".srt")

        # Check if running whisper.cpp (whisper-cli)
        if "whisper-cli" in Path(self.whisper_bin).name:
            cmd = [
                self.whisper_bin,
                "-m",
                self.model_name,
                "-f",
                str(clip_path.resolve()),
                "-osrt",
                "-of",
                str(clip_path.with_suffix("").resolve()),
            ]
        else:
            # Standard openai-whisper CLI
            cmd = [
                self.whisper_bin,
                str(clip_path.resolve()),
                "--output_format",
                "srt",
                "--output_dir",
                str(clip_path.parent.resolve()),
            ]

        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)
            if res.returncode == 0 and output_srt.exists():
                return output_srt
        except Exception:
            pass

        return None

    def burn_subtitles(self, clip_path: Path, srt_path: Path, output_path: Path) -> Path:
        if not self.ffmpeg_bin:
            raise FileNotFoundError("FFmpeg required to burn captions.")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        # Format subtitles path safely for FFmpeg vf filter (escape backslashes and colons)
        safe_srt = str(srt_path.resolve()).replace("\\", "/").replace(":", "\\:")

        vf_filter = (
            f"subtitles='{safe_srt}':force_style="
            "'FontName=Arial,FontSize=18,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
            "BorderStyle=3,Outline=2,Shadow=0,Alignment=2,MarginV=30'"
        )

        cmd = [
            self.ffmpeg_bin,
            "-y",
            "-i",
            str(clip_path.resolve()),
            "-vf",
            vf_filter,
            "-c:a",
            "copy",
            str(output_path.resolve()),
        ]

        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg caption burn failed: {res.stderr[:300]}")

        return output_path
