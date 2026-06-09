import asyncio
import subprocess
from pathlib import Path

from app.config import settings


class AudioExtractor:
    """Extract and normalize audio from uploaded media files using FFmpeg."""

    VIDEO_EXTENSIONS = {".mp4", ".mov"}

    async def extract(self, input_path: Path, output_dir: Path) -> tuple[Path, bool]:
        """
        Extract audio to 16kHz mono WAV.

        Returns:
            Tuple of (wav_path, is_video_source)
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "normalized_audio.wav"
        is_video = input_path.suffix.lower() in self.VIDEO_EXTENSIONS

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            "-vn",
            "-acodec",
            "pcm_s16le",
            "-ar",
            str(settings.target_sample_rate),
            "-ac",
            "1",
            str(output_path),
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(
                f"FFmpeg failed: {stderr.decode('utf-8', errors='replace')[:500]}"
            )

        return output_path, is_video

    def get_duration(self, audio_path: Path) -> float:
        """Get audio duration in seconds via ffprobe."""
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(audio_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
