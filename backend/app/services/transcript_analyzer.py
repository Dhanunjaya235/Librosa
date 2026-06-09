import json
import re
from typing import Any, Optional

from openai import AsyncOpenAI

from app.config import settings
from app.models.schemas import (
    AssessmentReport,
    AudioMetrics,
    ParameterScore,
    TranscriptResult,
    VideoMetrics,
)
from app.services.parameters import (
    ALL_TRANSCRIPT_PARAMS,
    CATEGORY_MAP,
    VIDEO_PARAMS,
)


EVALUATOR_SYSTEM_PROMPT = """You are a senior technical interviewer with 15+ years of experience evaluating candidates across all levels (fresher to senior).

Your task is to evaluate an interview transcript and provide a rigorous, evidence-based assessment.

RULES:
1. Score each parameter independently on a 0-100 scale.
2. Provide a confidence score (0-100) for each parameter based on available evidence.
3. Justify every score with specific evidence quoted or paraphrased from the transcript.
4. Avoid score inflation — average candidates should score 60-75, strong candidates 75-85, exceptional 85+.
5. Be role-agnostic — evaluate communication and reasoning, not domain-specific jargon alone.
6. If a parameter cannot be assessed from the transcript, score conservatively (40-55) with low confidence and explain why.
7. Return ONLY valid JSON matching the required schema. No markdown, no commentary outside JSON.

For filler words, count instances of "um", "uh", "like", "you know", "basically", "actually" etc.
For STAR framework, look for Situation, Task, Action, Result structure in behavioral answers.
For pace/conciseness, consider transcript length vs content density."""


class TranscriptAnalyzer:
    """LLM-based transcript evaluation for all assessment parameters."""

    def __init__(self) -> None:
        self._client: Optional[AsyncOpenAI] = None

    @property
    def client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        return self._client

    async def evaluate(
        self,
        transcript: TranscriptResult,
        audio_metrics: AudioMetrics,
        video_metrics: Optional[VideoMetrics] = None,
    ) -> AssessmentReport:
        if not settings.openai_api_key:
            from app.services.fallback_evaluator import FallbackEvaluator

            has_video = video_metrics is not None and video_metrics.frames_analyzed > 0
            report = FallbackEvaluator().evaluate(transcript, audio_metrics, has_video)
            if video_metrics and video_metrics.frames_analyzed > 0:
                report.parameterScores = self._merge_video_scores(
                    report.parameterScores, video_metrics
                )
            return report

        user_prompt = self._build_prompt(transcript, audio_metrics, video_metrics)
        response = await self.client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": EVALUATOR_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content or "{}"
        data = self._parse_json(raw)
        return self._build_report(data, video_metrics)

    def _build_prompt(
        self,
        transcript: TranscriptResult,
        audio_metrics: AudioMetrics,
        video_metrics: Optional[VideoMetrics],
    ) -> str:
        segments_text = "\n".join(
            f"[{s.start:.1f}s - {s.end:.1f}s] {s.text}"
            for s in transcript.segments[:200]
        )

        audio_summary = {
            "duration_seconds": audio_metrics.delivery.duration_seconds,
            "words_per_minute": audio_metrics.delivery.words_per_minute,
            "speech_silence_ratio": audio_metrics.delivery.speech_silence_ratio,
            "average_pause_seconds": audio_metrics.delivery.average_pause_length_seconds,
            "long_pause_count": audio_metrics.delivery.long_pause_count,
            "pitch_stability": audio_metrics.confidence.pitch_stability,
            "monotone_score": audio_metrics.engagement.monotone_score,
            "enthusiasm_score": audio_metrics.engagement.enthusiasm_score,
            "audio_quality_score": audio_metrics.quality.audio_quality_score,
        }

        video_section = ""
        if video_metrics and video_metrics.frames_analyzed > 0:
            video_section = f"""
VIDEO METRICS (supplement transcript analysis for video presence parameters):
- Eye Contact Score: {video_metrics.eye_contact_score}
- Posture Score: {video_metrics.posture_score}
- Gestures Score: {video_metrics.gestures_score}
"""

        params_list = ", ".join(f'"{p}"' for p in ALL_TRANSCRIPT_PARAMS)
        video_params = ""
        if video_metrics and video_metrics.frames_analyzed > 0:
            video_params = f'\nAlso evaluate video parameters: {", ".join(VIDEO_PARAMS)}'

        return f"""Evaluate this interview transcript and audio metrics.

TRANSCRIPT ({transcript.word_count} words, language: {transcript.language}):
{transcript.full_transcript}

SEGMENTED TRANSCRIPT:
{segments_text}

AUDIO METRICS:
{json.dumps(audio_summary, indent=2)}
{video_section}

Evaluate these parameters: {params_list}{video_params}

Return JSON with this exact structure:
{{
  "parameterScores": [
    {{
      "parameter": "Clarity",
      "category": "communication",
      "score": 75,
      "confidence": 80,
      "evidence": "Candidate clearly explained...",
      "strengths": ["..."],
      "improvements": ["..."]
    }}
  ],
  "overallScore": 75,
  "communicationScore": 78,
  "technicalScore": 72,
  "behavioralScore": 70,
  "confidenceScore": 76,
  "engagementScore": 68
}}

Categories for parameters:
- communication: {CATEGORY_MAP["communication"]}
- technical: {CATEGORY_MAP["technical"]}
- behavioral: {CATEGORY_MAP["behavioral"]} plus engagement/structure/interview skills and video params

Assign each parameter to the most appropriate category field value: "communication", "technical", or "behavioral"."""

    def _parse_json(self, raw: str) -> dict[str, Any]:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                return json.loads(match.group())
            raise ValueError("LLM returned invalid JSON") from None

    def _build_report(
        self, data: dict[str, Any], video_metrics: Optional[VideoMetrics]
    ) -> AssessmentReport:
        param_scores: list[ParameterScore] = []
        for item in data.get("parameterScores", []):
            try:
                param_scores.append(ParameterScore(**item))
            except Exception:
                continue

        if video_metrics and video_metrics.frames_analyzed > 0:
            param_scores = self._merge_video_scores(param_scores, video_metrics)

        from app.services.scoring_engine import ScoringEngine

        engine = ScoringEngine()
        hire_rec = engine.get_hire_recommendation(
            float(data.get("overallScore", engine.compute_overall(param_scores)))
        )

        comm = engine.build_category_scores(param_scores, "communication")
        tech = engine.build_category_scores(param_scores, "technical")
        beh = engine.build_category_scores(param_scores, "behavioral")

        return AssessmentReport(
            overallScore=float(
                data.get("overallScore", engine.compute_overall(param_scores))
            ),
            hireRecommendation=hire_rec,
            communicationScore=float(
                data.get("communicationScore", comm["score"])
            ),
            technicalScore=float(data.get("technicalScore", tech["score"])),
            behavioralScore=float(data.get("behavioralScore", beh["score"])),
            confidenceScore=float(data.get("confidenceScore", 70)),
            engagementScore=float(data.get("engagementScore", 70)),
            communication=comm,
            technical=tech,
            behavioral=beh,
            parameterScores=param_scores,
        )

    def _merge_video_scores(
        self, scores: list[ParameterScore], video: VideoMetrics
    ) -> list[ParameterScore]:
        existing = {s.parameter for s in scores}
        video_map = {
            "Eye Contact": video.eye_contact_score,
            "Posture": video.posture_score,
            "Gestures": video.gestures_score,
        }
        for param, val in video_map.items():
            if param not in existing and val is not None:
                scores.append(
                    ParameterScore(
                        parameter=param,
                        category="behavioral",
                        score=val,
                        confidence=60,
                        evidence="Derived from video frame analysis (face detection and motion heuristics).",
                        strengths=["Video presence detected and analyzed."],
                        improvements=["Manual review recommended for accurate video assessment."],
                    )
                )
        return scores
