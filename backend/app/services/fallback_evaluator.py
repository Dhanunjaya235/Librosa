"""Rule-based fallback assessment when LLM is unavailable."""

import re

from app.models.schemas import AssessmentReport, AudioMetrics, ParameterScore, TranscriptResult
from app.services.parameters import ALL_TRANSCRIPT_PARAMS, VIDEO_PARAMS
from app.services.scoring_engine import ScoringEngine


FILLER_PATTERN = re.compile(
    r"\b(um|uh|like|you know|basically|actually|sort of|kind of|i mean)\b",
    re.IGNORECASE,
)


class FallbackEvaluator:
    """Heuristic assessment based on transcript and audio metrics."""

    def evaluate(
        self,
        transcript: TranscriptResult,
        audio_metrics: AudioMetrics,
        has_video: bool = False,
    ) -> AssessmentReport:
        text = transcript.full_transcript
        words = text.split()
        word_count = len(words)
        fillers = len(FILLER_PATTERN.findall(text))
        filler_ratio = fillers / max(word_count, 1)

        wpm = audio_metrics.delivery.words_per_minute
        pause_avg = audio_metrics.delivery.average_pause_length_seconds
        pitch_stab = audio_metrics.confidence.pitch_stability
        enthusiasm = audio_metrics.engagement.enthusiasm_score
        monotone = audio_metrics.engagement.monotone_score
        quality = audio_metrics.quality.audio_quality_score

        base = 65.0
        if word_count > 100:
            base += 5
        if word_count > 300:
            base += 5

        scores: list[ParameterScore] = []

        param_heuristics: dict[str, float] = {
            "Clarity": base + (5 if word_count > 50 else -5),
            "Fluency": base - filler_ratio * 100,
            "Grammar": base,
            "Vocabulary": base + min(word_count / 50, 10),
            "Pace": base - abs(wpm - 140) / 5,
            "Filler Words": max(30, 100 - filler_ratio * 300),
            "Active Listening": base - 5,
            "Conciseness": base - max(0, word_count - 500) / 20,
            "Adaptability": base,
            "Confidence Level": pitch_stab * 0.6 + base * 0.4,
            "Vocal Energy": enthusiasm,
            "Professionalism": base + 3,
            "Accuracy": base,
            "Completeness": base + min(word_count / 100, 8),
            "Depth of Knowledge": base,
            "Relevance": base,
            "Problem Solving": base,
            "Real-world Examples": base - 5 if "example" not in text.lower() else base + 5,
            "Trade-off Analysis": base - 10 if "trade" not in text.lower() else base + 5,
            "Decision Making": base,
            "Learning Agility": base,
            "STAR Framework": base - 10 if "result" not in text.lower() else base + 5,
            "Ownership": base,
            "Collaboration": base,
            "Leadership Potential": base,
            "Conflict Resolution": base,
            "Audience Engagement": enthusiasm * 0.7 + base * 0.3,
            "Storytelling": base + 5 if "story" in text.lower() or "when i" in text.lower() else base - 5,
            "Persuasion": base,
            "Structure & Coherence": base - pause_avg * 5,
            "Answer Organization": base,
            "Follow-up Handling": base - 5,
            "Time Management": base - audio_metrics.delivery.long_pause_count * 2,
            "Consistency": base,
        }

        for param in ALL_TRANSCRIPT_PARAMS:
            score = max(30, min(90, param_heuristics.get(param, base)))
            snippet = text[:200] + "..." if len(text) > 200 else text
            scores.append(
                ParameterScore(
                    parameter=param,
                    category=_category_for(param),
                    score=round(score, 1),
                    confidence=50,
                    evidence=f"Heuristic analysis of transcript ({word_count} words). Sample: \"{snippet[:120]}\"",
                    strengths=["Transcript captured successfully for review."],
                    improvements=["Enable OpenAI API for detailed LLM-based assessment."],
                )
            )

        engine = ScoringEngine()
        overall = engine.compute_overall(scores)

        return AssessmentReport(
            overallScore=overall,
            hireRecommendation=engine.get_hire_recommendation(overall),
            communicationScore=engine.compute_category_score(scores, "communication"),
            technicalScore=engine.compute_category_score(scores, "technical"),
            behavioralScore=engine.compute_category_score(scores, "behavioral"),
            confidenceScore=round(pitch_stab * 0.5 + quality * 0.5, 1),
            engagementScore=round((100 - monotone) * 0.4 + enthusiasm * 0.6, 1),
            communication=engine.build_category_scores(scores, "communication"),
            technical=engine.build_category_scores(scores, "technical"),
            behavioral=engine.build_category_scores(scores, "behavioral"),
            parameterScores=scores,
        )


def _category_for(param: str) -> str:
    comm = {"Clarity", "Fluency", "Grammar", "Vocabulary", "Pace", "Filler Words",
            "Active Listening", "Conciseness", "Adaptability",
            "Confidence Level", "Vocal Energy", "Professionalism"}
    tech = {"Accuracy", "Completeness", "Depth of Knowledge", "Relevance",
            "Problem Solving", "Real-world Examples", "Trade-off Analysis",
            "Decision Making", "Learning Agility"}
    if param in comm:
        return "communication"
    if param in tech:
        return "technical"
    return "behavioral"
