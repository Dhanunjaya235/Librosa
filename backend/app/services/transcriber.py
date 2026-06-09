import asyncio
from functools import lru_cache
from pathlib import Path

from faster_whisper import WhisperModel

from app.config import settings
from app.models.schemas import TranscriptResult, TranscriptSegment


class Transcriber:
    """Speech-to-text using Faster-Whisper with word and segment timestamps."""

    @staticmethod
    @lru_cache(maxsize=1)
    def _load_model() -> WhisperModel:
        return WhisperModel(
            settings.whisper_model,
            device=settings.whisper_device,
            compute_type=settings.whisper_compute_type,
        )

    async def transcribe(self, audio_path: Path) -> TranscriptResult:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._transcribe_sync, audio_path)

    def _transcribe_sync(self, audio_path: Path) -> TranscriptResult:
        model = self._load_model()
        segments_iter, info = model.transcribe(
            str(audio_path),
            word_timestamps=True,
            vad_filter=True,
        )

        segments: list[TranscriptSegment] = []
        full_parts: list[str] = []

        for seg in segments_iter:
            text = seg.text.strip()
            if not text:
                continue
            segments.append(
                TranscriptSegment(start=seg.start, end=seg.end, text=text)
            )
            full_parts.append(text)

        full_transcript = " ".join(full_parts)
        word_count = len(full_transcript.split())

        return TranscriptResult(
            full_transcript=full_transcript,
            word_count=word_count,
            segments=segments,
            language=info.language or "en",
        )
