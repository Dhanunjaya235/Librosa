"""Generate a sample WAV file with synthetic speech-like tones for testing."""

import math
import struct
import wave
from pathlib import Path

SAMPLE_RATE = 16000
DURATION = 15
OUTPUT = Path(__file__).parent / "sample_interview.wav"


def generate_tone_wav(path: Path, duration: int = DURATION) -> None:
    """Generate a simple multi-tone WAV simulating pauses and speech segments."""
    segments = [
        (0.0, 3.0, 220),
        (3.5, 6.0, 280),
        (6.5, 9.0, 200),
        (9.5, 12.0, 260),
        (12.5, 14.5, 240),
    ]

    samples = []
    total_samples = int(SAMPLE_RATE * duration)

    for i in range(total_samples):
        t = i / SAMPLE_RATE
        value = 0.0
        for start, end, freq in segments:
            if start <= t <= end:
                envelope = min(1.0, (t - start) * 10) * min(1.0, (end - t) * 10)
                value += envelope * 0.3 * math.sin(2 * math.pi * freq * t)
                value += envelope * 0.1 * math.sin(2 * math.pi * freq * 2 * t)
        noise = 0.02 * (math.sin(i * 0.7) + math.cos(i * 1.3))
        sample = max(-1.0, min(1.0, value + noise))
        samples.append(int(sample * 32767))

    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(struct.pack(f"<{len(samples)}h", *samples))

    print(f"Generated {path} ({duration}s, {SAMPLE_RATE}Hz mono)")


if __name__ == "__main__":
    generate_tone_wav(OUTPUT)
