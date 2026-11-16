"""
Real-time chat velocity spike detector.
Calculates message frequency in sliding windows against a rolling baseline.
"""

from collections import deque
from datetime import datetime, timezone
from typing import Deque, List, Optional, Tuple


class SpikeDetector:
    def __init__(
        self,
        window_seconds: int = 10,
        baseline_seconds: int = 300,
        spike_multiplier: float = 3.0,
        min_spike_messages: int = 8,
        cooldown_seconds: int = 60,
    ):
        self.window_seconds = window_seconds
        self.baseline_seconds = baseline_seconds
        self.spike_multiplier = spike_multiplier
        self.min_spike_messages = min_spike_messages
        self.cooldown_seconds = cooldown_seconds
        
        self.timestamps: Deque[float] = deque()
        self.last_spike_epoch: float = 0.0

    def record_message(self, dt: Optional[datetime] = None) -> Optional[Tuple[datetime, float, float]]:
        if dt is None:
            dt = datetime.now(timezone.utc)
        
        epoch = dt.timestamp()
        self.timestamps.append(epoch)
        return self._evaluate(epoch, dt)

    def _evaluate(self, current_epoch: float, dt: datetime) -> Optional[Tuple[datetime, float, float]]:
        cutoff = current_epoch - self.baseline_seconds
        while self.timestamps and self.timestamps[0] < cutoff:
            self.timestamps.popleft()

        total_msgs = len(self.timestamps)
        if total_msgs < self.min_spike_messages:
            return None

        # Check cooldown period
        if current_epoch - self.last_spike_epoch < self.cooldown_seconds:
            return None

        # Require at least 30 seconds of historical chat or 2x window span for stable baseline
        baseline_span = max(float(self.window_seconds), current_epoch - self.timestamps[0])
        if baseline_span < self.window_seconds * 2:
            return None

        # Calculate recent window message count
        window_cutoff = current_epoch - self.window_seconds
        recent_count = sum(1 for t in self.timestamps if t >= window_cutoff)
        
        # Calculate rates per second
        recent_rate = recent_count / max(self.window_seconds, 1)
        baseline_rate = total_msgs / baseline_span

        if baseline_rate > 0 and recent_rate >= (baseline_rate * self.spike_multiplier) and recent_count >= self.min_spike_messages:
            self.last_spike_epoch = current_epoch
            return (dt, recent_rate, baseline_rate)

        return None

    @classmethod
    def parse_log_file(cls, log_path: str, window_seconds: int = 10, baseline_seconds: int = 300, multiplier: float = 3.0, min_messages: int = 8) -> List[dict]:
        detector = cls(
            window_seconds=window_seconds,
            baseline_seconds=baseline_seconds,
            spike_multiplier=multiplier,
            min_spike_messages=min_messages,
        )
        spikes = []
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.startswith("[") and "]" in line:
                    ts_str = line[1 : line.index("]")]
                    try:
                        dt = datetime.fromisoformat(ts_str)
                        res = detector.record_message(dt)
                        if res:
                            spikes.append({
                                "timestamp": res[0].isoformat(),
                                "recent_rate": round(res[1], 2),
                                "baseline_rate": round(res[2], 2),
                                "ratio": round(res[1] / max(res[2], 0.001), 2),
                            })
                    except Exception:
                        continue
        return spikes
