"""
End-to-end autonomous clipping orchestration engine.
"""

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .attribution import AttributionManager
from .clipper import StreamClipper
from .config import WatcherConfig
from .irc_listener import TwitchChatListener
from .spike_detector import SpikeDetector
from .stream_recorder import StreamRecorder
from .whisper_transcriber import WhisperTranscriber


class WatcherPipeline:
    def __init__(self, config: WatcherConfig):
        self.config = config
        self.recorder = StreamRecorder(
            channel=config.channel,
            output_file=config.stream_output_file,
            retry_delay=config.streamlink_retry_delay,
        )
        self.detector = SpikeDetector(
            window_seconds=config.window_seconds,
            baseline_seconds=config.baseline_seconds,
            spike_multiplier=config.spike_multiplier,
            min_spike_messages=config.min_spike_messages,
            cooldown_seconds=config.cooldown_seconds,
        )
        self.clipper: Optional[StreamClipper] = None
        self.transcriber = WhisperTranscriber(model_name=config.whisper_model)
        self.listener: Optional[TwitchChatListener] = None
        self.start_epoch: float = 0.0

    def start(self):
        try:
            self.clipper = StreamClipper()
        except FileNotFoundError:
            self.clipper = None

        self.start_epoch = time.time()
        
        # Start stream recording
        try:
            self.recorder.start()
        except FileNotFoundError:
            pass

        # Start anonymous chat monitoring
        self.listener = TwitchChatListener(
            channel=self.config.channel,
            log_file=self.config.chat_log_file,
            on_message=self._on_chat_message,
        )
        self.listener.start()

    def stop(self):
        if self.listener:
            self.listener.stop()
        if self.recorder:
            self.recorder.stop()

    def _on_chat_message(self, dt: datetime, sender: str, content: str):
        spike = self.detector.record_message(dt)
        if spike and self.clipper and self.config.stream_output_file.exists():
            spike_time, recent_rate, baseline_rate = spike
            current_elapsed = time.time() - self.start_epoch
            
            # Chat reacts ~30 seconds after the event happens on stream
            clip_start = max(0.0, current_elapsed - self.config.pre_roll_seconds)
            timestamp_str = spike_time.strftime("%Y%m%d_%H%M%S")
            clip_name = f"clip_{self.config.channel}_{timestamp_str}"
            
            raw_clip = self.config.clips_dir / f"{clip_name}_raw.mp4"
            final_clip = self.config.clips_dir / f"{clip_name}.mp4"
            
            try:
                # 1. Cut clip
                self.clipper.cut_clip(
                    stream_file=self.config.stream_output_file,
                    start_seconds=clip_start,
                    duration_seconds=self.config.clip_duration_seconds,
                    output_path=raw_clip,
                    fast_copy=True,
                )

                # 2. Transcribe & Burn Subtitles if Whisper is available
                srt_path = self.transcriber.transcribe(raw_clip)
                if srt_path and self.config.burn_subtitles:
                    self.transcriber.burn_subtitles(raw_clip, srt_path, final_clip)
                else:
                    raw_clip.rename(final_clip)

                # 3. Generate streamer credit and attribution metadata
                AttributionManager.generate_credits(
                    channel=self.config.channel,
                    clip_name=clip_name,
                    output_dir=self.config.clips_dir,
                    stream_timestamp=spike_time.isoformat(),
                    duration_seconds=self.config.clip_duration_seconds,
                )
            except Exception:
                pass
