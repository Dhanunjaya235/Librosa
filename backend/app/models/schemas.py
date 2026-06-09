from typing import Any, Optional

from pydantic import BaseModel, Field


class ParameterScore(BaseModel):
    parameter: str
    category: str
    score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=100)
    evidence: str
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)


class CategoryScores(BaseModel):
    score: float = Field(ge=0, le=100)
    parameters: list[ParameterScore] = Field(default_factory=list)


class DeliveryMetrics(BaseModel):
    duration_seconds: float
    speaking_time_seconds: float
    silence_time_seconds: float
    speech_silence_ratio: float
    average_pause_length_seconds: float
    long_pause_count: int
    words_per_minute: float


class ConfidenceMetrics(BaseModel):
    pitch_average_hz: float
    pitch_variance: float
    pitch_stability: float
    rms_energy: float
    energy_variance: float
    vocal_intensity: float


class EngagementMetrics(BaseModel):
    energy_variation: float
    pitch_variation: float
    monotone_score: float
    enthusiasm_score: float


class QualityMetrics(BaseModel):
    background_noise_estimate: float
    audio_quality_score: float
    clipping_detected: bool


class AudioMetrics(BaseModel):
    delivery: DeliveryMetrics
    confidence: ConfidenceMetrics
    engagement: EngagementMetrics
    quality: QualityMetrics


class VideoMetrics(BaseModel):
    eye_contact_score: Optional[float] = None
    posture_score: Optional[float] = None
    gestures_score: Optional[float] = None
    frames_analyzed: int = 0
    notes: str = ""


class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str


class TranscriptResult(BaseModel):
    full_transcript: str
    word_count: int
    segments: list[TranscriptSegment]
    language: str = "en"


class AnalyzeResponse(BaseModel):
    status: str = "success"
    overallScore: float
    hireRecommendation: str
    communicationScore: float
    technicalScore: float
    behavioralScore: float
    confidenceScore: float
    engagementScore: float
    communication: CategoryScores
    technical: CategoryScores
    behavioral: CategoryScores
    audioMetrics: AudioMetrics
    videoMetrics: Optional[VideoMetrics] = None
    transcript: str
    parameterScores: list[ParameterScore]
    processingTimeSeconds: float = 0.0


class ErrorResponse(BaseModel):
    status: str = "error"
    detail: str


class AssessmentReport(BaseModel):
    overallScore: float
    hireRecommendation: str
    communicationScore: float
    technicalScore: float
    behavioralScore: float
    confidenceScore: float
    engagementScore: float
    communication: dict[str, Any]
    technical: dict[str, Any]
    behavioral: dict[str, Any]
    parameterScores: list[ParameterScore]
