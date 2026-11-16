"""
Configuration settings and default parameters for Clip Watcher.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class WatcherConfig:
    channel: str
    irc_server: str = "irc.chat.twitch.tv"
    irc_port: int = 6667
    stream_output_file: Path = Path("stream.ts")
    chat_log_file: Path = Path("chat.log")
    clips_dir: Path = Path("clips")
    
    # Spike detection parameters
    window_seconds: int = 10
    baseline_seconds: int = 300
    spike_multiplier: float = 3.0
    min_spike_messages: int = 8
    cooldown_seconds: int = 60
    
    # Clip trimming parameters
    pre_roll_seconds: int = 30
    clip_duration_seconds: int = 45
    
    # Whisper subtitle settings
    whisper_model: str = "ggml-medium.en.bin"
    whisper_binary: str = "whisper-cli"
    burn_subtitles: bool = True
    
    # Streamlink retry delay
    streamlink_retry_delay: int = 30
