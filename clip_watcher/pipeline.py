"""
End-to-end autonomous clipping orchestration engine.
"""

import threading
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
        if spike:
            spike_time, recent_rate, baseline_rate = spike
            ratio = recent_rate / max(baseline_rate, 0.001)
            print(f"[Chat Spike] Rate: {recent_rate:.1f} msg/s vs Baseline: {baseline_rate:.2f} msg/s ({ratio:.1f}x surge) at {spike_time.strftime('%H:%M:%S')}")
            
            if self.clipper and self.config.stream_output_file.exists():
                elapsed_at_spike = time.time() - self.start_epoch
                clip_start = max(0.0, elapsed_at_spike - self.config.pre_roll_seconds)
                timestamp_str = spike_time.strftime("%Y%m%d_%H%M%S")
                clip_name = f"clip_{self.config.channel}_{timestamp_str}"
                
                delay = float(self.config.post_roll_seconds)
                print(f"[Clipper] Spike captured! Waiting {delay:.0f}s to record 20s post-reaction buffer for a 1-minute clip...")
                
                # Buffer 20s after the reaction so the clip contains 40s before and 20s after
                timer = threading.Timer(
                    delay,
                    self._extract_clip,
                    args=[clip_start, float(self.config.clip_duration_seconds), clip_name, spike_time],
                )
                timer.daemon = True
                timer.start()
            elif not self.config.stream_output_file.exists():
                print(f"[Clipper Notice] Stream buffer {self.config.stream_output_file} not ready yet.")

    def _extract_clip(self, clip_start: float, duration: float, clip_name: str, spike_time: datetime):
        raw_clip = self.config.clips_dir / f"{clip_name}_raw.mp4"
        final_clip = self.config.clips_dir / f"{clip_name}.mp4"
        
        print(f"[Clipper] Extracting 1-minute clip (40s earlier, 20s after) from stream.ts at offset {clip_start:.1f}s...")
        try:
            # 1. Cut clip with -i before -ss for frame-accurate timing
            self.clipper.cut_clip(
                stream_file=self.config.stream_output_file,
                start_seconds=clip_start,
                duration_seconds=duration,
                output_path=raw_clip,
                fast_copy=True,
            )
            print(f"[Clipper] Raw 1-minute highlight saved to {raw_clip}")

            # 2. Transcribe & Burn Subtitles if Whisper is available
            srt_path = self.transcriber.transcribe(raw_clip)
            if srt_path and self.config.burn_subtitles:
                print(f"[Whisper] Burning captions into {final_clip}...")
                self.transcriber.burn_subtitles(raw_clip, srt_path, final_clip)
            else:
                if raw_clip.exists():
                    raw_clip.rename(final_clip)
            print(f"[Clipper] Completed 1-minute highlight: {final_clip}")

            # 3. Generate streamer credit and attribution metadata
            AttributionManager.generate_credits(
                channel=self.config.channel,
                clip_name=clip_name,
                output_dir=self.config.clips_dir,
                stream_timestamp=spike_time.isoformat(),
                duration_seconds=duration,
            )
            print(f"[Attribution] Streamer credits saved to clips/{clip_name}_credits.txt")
        except Exception as e:
            print(f"[Clipper Error] {e}")
