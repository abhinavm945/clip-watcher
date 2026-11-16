"""
Unit tests for the SpikeDetector algorithm.
"""

from datetime import datetime, timedelta, timezone
from clip_watcher.spike_detector import SpikeDetector


def test_spike_detector_steady_traffic():
    detector = SpikeDetector(window_seconds=10, baseline_seconds=300, spike_multiplier=3.0, min_spike_messages=8)
    now = datetime.now(timezone.utc)
    
    # Send 1 message per second steadily (rate: 1 msg/s)
    spikes = []
    for i in range(120):
        t = now + timedelta(seconds=i)
        res = detector.record_message(t)
        if res:
            spikes.append(res)

    # Steady traffic should not trigger a 3x spike
    assert len(spikes) == 0


def test_spike_detector_triggers_on_surge():
    detector = SpikeDetector(window_seconds=10, baseline_seconds=300, spike_multiplier=3.0, min_spike_messages=8)
    now = datetime.now(timezone.utc)
    
    # 60 seconds of low background chat (0.2 msgs/s)
    for i in range(60):
        detector.record_message(now + timedelta(seconds=i * 2))

    # Sudden burst of 25 messages in 5 seconds
    surge_start = now + timedelta(seconds=125)
    spike_detected = False
    for i in range(25):
        t = surge_start + timedelta(milliseconds=i * 200)
        res = detector.record_message(t)
        if res:
            spike_detected = True
            break

    assert spike_detected is True
