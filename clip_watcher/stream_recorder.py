"""
Live stream capture manager using Streamlink.
Continuously attempts to connect and records live broadcast to a transport stream file.
"""

import shutil
import subprocess
import sys
import threading
from pathlib import Path
from typing import Optional


class StreamRecorder:
    def __init__(
        self,
        channel: str,
        output_file: Path = Path("stream.ts"),
        retry_delay: int = 30,
        quality: str = "best",
    ):
        self.channel = channel.lower().lstrip("#")
        self.output_file = Path(output_file)
        self.retry_delay = retry_delay
        self.quality = quality
        self.process: Optional[subprocess.Popen] = None
        self._thread: Optional[threading.Thread] = None

    def start(self):
        streamlink_bin = shutil.which("streamlink")
        if streamlink_bin:
            base_cmd = [streamlink_bin]
        else:
            base_cmd = [sys.executable, "-m", "streamlink"]

        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        url = f"twitch.tv/{self.channel}"

        cmd = base_cmd + [
            url,
            self.quality,
            "-o",
            str(self.output_file.resolve()),
            "--retry-streams",
            str(self.retry_delay),
        ]

        def _runner():
            try:
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )
                if self.process.stdout:
                    for line in self.process.stdout:
                        clean_line = line.strip()
                        if "Opening stream" in clean_line or "Writing output" in clean_line:
                            print(f"[Streamlink] {clean_line}")
            except Exception as e:
                print(f"[Streamlink Error] {e}")

        self._thread = threading.Thread(target=_runner, daemon=True)
        self._thread.start()

    def is_recording(self) -> bool:
        return self.process is not None and self.process.poll() is None

    def stop(self):
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                self.process.kill()
