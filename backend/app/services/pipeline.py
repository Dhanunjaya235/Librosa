import asyncio
import shutil
import time
import uuid
from pathlib import Path

from app.config import settings
from app.models.schemas import AnalyzeResponse, CategoryScores, ParameterScore
from app.services.audio_analyzer import AudioAnalyzer
from app.services.audio_extractor import AudioExtractor
from app.services.scoring_engine import ScoringEngine
from app.services.transcriber import Transcriber
from app.services.transcript_analyzer import TranscriptAnalyzer
from app.services.video_analyzer import VideoAnalyzer


class InterviewPipeline:
    """Orchestrates the full interview analysis workflow."""

    def __init__(self) -> None:
        self.audio_extractor = AudioExtractor()
        self.transcriber = Transcriber()
        self.audio_analyzer = AudioAnalyzer()
        self.video_analyzer = VideoAnalyzer()
        self.transcript_analyzer = TranscriptAnalyzer()
        self.scoring_engine = ScoringEngine()

    async def run(self, file_path: Path, original_name: str) -> AnalyzeResponse:
        work_dir = Path(settings.upload_dir) / str(uuid.uuid4())
        work_dir.mkdir(parents=True, exist_ok=True)
        start = time.time()

        try:
            dest = work_dir / original_name
            if file_path != dest:
                shutil.copy2(file_path, dest)

            wav_path, is_video = await self.audio_extractor.extract(dest, work_dir)

            transcript = await self.transcriber.transcribe(wav_path)
            audio_metrics = await self.audio_analyzer.analyze(wav_path, transcript)

            video_metrics = None
            if is_video:
                video_metrics = await self.video_analyzer.analyze(dest)

            assessment = await self.transcript_analyzer.evaluate(
                transcript, audio_metrics, video_metrics
            )

            audio_conf = audio_metrics.confidence.pitch_stability
            audio_eng = audio_metrics.engagement.enthusiasm_score
            enriched = self.scoring_engine.enrich_with_audio(
                assessment.parameterScores, audio_conf, audio_eng
            )

            overall = self.scoring_engine.compute_overall(enriched)
            hire_rec = self.scoring_engine.get_hire_recommendation(overall)

            comm_score = self.scoring_engine.compute_category_score(enriched, "communication")
            tech_score = self.scoring_engine.compute_category_score(enriched, "technical")
            beh_score = self.scoring_engine.compute_category_score(enriched, "behavioral")

            elapsed = round(time.time() - start, 2)

            return AnalyzeResponse(
                status="success",
                overallScore=overall,
                hireRecommendation=hire_rec,
                communicationScore=comm_score,
                technicalScore=tech_score,
                behavioralScore=beh_score,
                confidenceScore=assessment.confidenceScore,
                engagementScore=assessment.engagementScore,
                communication=CategoryScores(
                    score=comm_score,
                    parameters=[s for s in enriched if s.category == "communication"
                                or self.scoring_engine._matches_category(s, "communication")],
                ),
                technical=CategoryScores(
                    score=tech_score,
                    parameters=[s for s in enriched if self.scoring_engine._matches_category(s, "technical")],
                ),
                behavioral=CategoryScores(
                    score=beh_score,
                    parameters=[s for s in enriched if self.scoring_engine._matches_category(s, "behavioral")],
                ),
                audioMetrics=audio_metrics,
                videoMetrics=video_metrics,
                transcript=transcript.full_transcript,
                parameterScores=enriched,
                processingTimeSeconds=elapsed,
            )
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)


_pipeline: InterviewPipeline | None = None


def get_pipeline() -> InterviewPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = InterviewPipeline()
    return _pipeline
