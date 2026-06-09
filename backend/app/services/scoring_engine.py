from app.models.schemas import CategoryScores, ParameterScore


class ScoringEngine:
    """Aggregate parameter scores and derive hire recommendations."""

    HIRE_THRESHOLDS = [
        (90, "Strong Hire"),
        (80, "Hire"),
        (70, "Lean Hire"),
        (60, "Borderline"),
        (0, "No Hire"),
    ]

    CATEGORY_KEYWORDS: dict[str, set[str]] = {
        "communication": {
            "clarity", "fluency", "grammar", "vocabulary", "pace", "filler",
            "active listening", "conciseness", "adaptability",
            "confidence level", "vocal energy", "professionalism",
        },
        "technical": {
            "accuracy", "completeness", "depth", "relevance", "problem solving",
            "real-world", "trade-off", "decision making", "learning agility",
        },
        "behavioral": {
            "star", "ownership", "collaboration", "leadership", "conflict",
            "engagement", "storytelling", "persuasion", "structure", "coherence",
            "organization", "follow-up", "time management", "consistency",
            "eye contact", "posture", "gestures",
        },
    }

    def get_hire_recommendation(self, overall_score: float) -> str:
        for threshold, label in self.HIRE_THRESHOLDS:
            if overall_score >= threshold:
                return label
        return "No Hire"

    def compute_overall(self, scores: list[ParameterScore]) -> float:
        if not scores:
            return 0.0
        return round(sum(s.score for s in scores) / len(scores), 1)

    def compute_category_score(
        self, scores: list[ParameterScore], category: str
    ) -> float:
        filtered = [s for s in scores if self._matches_category(s, category)]
        if not filtered:
            return 0.0
        return round(sum(s.score for s in filtered) / len(filtered), 1)

    def build_category_scores(
        self, scores: list[ParameterScore], category: str
    ) -> dict:
        filtered = [s for s in scores if self._matches_category(s, category)]
        cat_score = self.compute_category_score(scores, category)
        return {
            "score": cat_score,
            "parameters": [s.model_dump() for s in filtered],
        }

    def _matches_category(self, param: ParameterScore, category: str) -> bool:
        if param.category == category:
            return True
        keywords = self.CATEGORY_KEYWORDS.get(category, set())
        param_lower = param.parameter.lower()
        return any(kw in param_lower for kw in keywords)

    def enrich_with_audio(
        self,
        report_scores: list[ParameterScore],
        audio_confidence: float,
        audio_engagement: float,
    ) -> list[ParameterScore]:
        """Supplement LLM scores with audio-derived signals where applicable."""
        audio_map = {
            "Vocal Energy": audio_engagement,
            "Confidence Level": audio_confidence,
            "Pace": None,
        }
        existing = {s.parameter for s in report_scores}
        for param_name, audio_score in audio_map.items():
            if param_name in existing and audio_score is not None:
                for s in report_scores:
                    if s.parameter == param_name:
                        blended = round(s.score * 0.7 + audio_score * 0.3, 1)
                        s.score = blended
        return report_scores
