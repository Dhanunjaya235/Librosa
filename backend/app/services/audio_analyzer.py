import asyncio
from pathlib import Path

import librosa
import numpy as np

from app.config import settings
from app.models.schemas import (
    AudioMetrics,
    ConfidenceMetrics,
    DeliveryMetrics,
    EngagementMetrics,
    QualityMetrics,
    TranscriptResult,
)


class AudioAnalyzer:
    """Extract delivery, confidence, engagement, and quality metrics via Librosa."""

    SILENCE_THRESHOLD_DB = -40
    LONG_PAUSE_THRESHOLD = 2.0

    async def analyze(
        self, audio_path: Path, transcript: TranscriptResult
    ) -> AudioMetrics:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._analyze_sync, audio_path, transcript
        )

    def _analyze_sync(
        self, audio_path: Path, transcript: TranscriptResult
    ) -> AudioMetrics:
        y, sr = librosa.load(str(audio_path), sr=settings.target_sample_rate, mono=True)
        duration = float(librosa.get_duration(y=y, sr=sr))

        delivery = self._compute_delivery(y, sr, duration, transcript)
        confidence = self._compute_confidence(y, sr)
        engagement = self._compute_engagement(y, sr)
        quality = self._compute_quality(y, sr)

        return AudioMetrics(
            delivery=delivery,
            confidence=confidence,
            engagement=engagement,
            quality=quality,
        )

    def _compute_delivery(
        self, y: np.ndarray, sr: int, duration: float, transcript: TranscriptResult
    ) -> DeliveryMetrics:
        rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
        rms_db = librosa.amplitude_to_db(rms, ref=np.max)

        speech_frames = rms_db > self.SILENCE_THRESHOLD_DB
        frame_duration = 512 / sr

        speaking_time = float(np.sum(speech_frames) * frame_duration)
        silence_time = max(0.0, duration - speaking_time)
        ratio = speaking_time / silence_time if silence_time > 0 else float(speaking_time)

        pauses = self._detect_pauses(transcript.segments, duration)
        avg_pause = float(np.mean(pauses)) if pauses else 0.0
        long_pauses = sum(1 for p in pauses if p >= self.LONG_PAUSE_THRESHOLD)

        wpm = (transcript.word_count / duration * 60) if duration > 0 else 0.0

        return DeliveryMetrics(
            duration_seconds=round(duration, 2),
            speaking_time_seconds=round(speaking_time, 2),
            silence_time_seconds=round(silence_time, 2),
            speech_silence_ratio=round(ratio, 2),
            average_pause_length_seconds=round(avg_pause, 2),
            long_pause_count=long_pauses,
            words_per_minute=round(wpm, 1),
        )

    def _detect_pauses(self, segments, duration: float) -> list[float]:
        pauses: list[float] = []
        if not segments:
            return pauses

        if segments[0].start > 0.5:
            pauses.append(segments[0].start)

        for i in range(1, len(segments)):
            gap = segments[i].start - segments[i - 1].end
            if gap > 0.3:
                pauses.append(gap)

        last_end = segments[-1].end
        if duration - last_end > 0.5:
            pauses.append(duration - last_end)

        return pauses

    def _compute_confidence(self, y: np.ndarray, sr: int) -> ConfidenceMetrics:
        f0, voiced_flag, _ = librosa.pyin(
            y,
            fmin=librosa.note_to_hz("C2"),
            fmax=librosa.note_to_hz("C7"),
            sr=sr,
        )
        f0_clean = f0[~np.isnan(f0)] if f0 is not None else np.array([])

        pitch_avg = float(np.mean(f0_clean)) if len(f0_clean) > 0 else 0.0
        pitch_var = float(np.var(f0_clean)) if len(f0_clean) > 0 else 0.0
        pitch_stability = max(0.0, 100.0 - min(pitch_var / 50.0, 100.0))

        rms = librosa.feature.rms(y=y)[0]
        rms_mean = float(np.mean(rms))
        rms_var = float(np.var(rms))
        vocal_intensity = float(np.mean(np.abs(y)))

        return ConfidenceMetrics(
            pitch_average_hz=round(pitch_avg, 1),
            pitch_variance=round(pitch_var, 2),
            pitch_stability=round(pitch_stability, 1),
            rms_energy=round(rms_mean, 4),
            energy_variance=round(rms_var, 6),
            vocal_intensity=round(vocal_intensity, 4),
        )

    def _compute_engagement(self, y: np.ndarray, sr: int) -> EngagementMetrics:
        rms = librosa.feature.rms(y=y)[0]
        energy_var = float(np.std(rms) / (np.mean(rms) + 1e-8))

        f0, _, _ = librosa.pyin(
            y,
            fmin=librosa.note_to_hz("C2"),
            fmax=librosa.note_to_hz("C7"),
            sr=sr,
        )
        f0_clean = f0[~np.isnan(f0)] if f0 is not None else np.array([])
        pitch_var = float(np.std(f0_clean) / (np.mean(f0_clean) + 1e-8)) if len(f0_clean) > 0 else 0.0

        monotone = max(0.0, min(100.0, 100.0 - pitch_var * 200))
        enthusiasm = max(0.0, min(100.0, energy_var * 50 + pitch_var * 30))

        return EngagementMetrics(
            energy_variation=round(energy_var, 3),
            pitch_variation=round(pitch_var, 3),
            monotone_score=round(monotone, 1),
            enthusiasm_score=round(enthusiasm, 1),
        )

    def _compute_quality(self, y: np.ndarray, sr: int) -> QualityMetrics:
        rms = librosa.feature.rms(y=y)[0]
        noise_floor = float(np.percentile(rms, 10))
        signal_level = float(np.percentile(rms, 90))
        snr_estimate = signal_level / (noise_floor + 1e-8)
        noise_score = min(100.0, max(0.0, 20 * np.log10(snr_estimate + 1e-8) + 40))

        clipping = bool(np.any(np.abs(y) > 0.99))
        quality = max(0.0, noise_score - (20 if clipping else 0))

        return QualityMetrics(
            background_noise_estimate=round(float(noise_floor), 4),
            audio_quality_score=round(quality, 1),
            clipping_detected=clipping,
        )
