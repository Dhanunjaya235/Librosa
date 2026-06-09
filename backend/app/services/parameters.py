"""Assessment parameter definitions for LLM evaluation."""

COMMUNICATION_PARAMS = [
    "Clarity",
    "Fluency",
    "Grammar",
    "Vocabulary",
    "Pace",
    "Filler Words",
    "Active Listening",
    "Conciseness",
    "Adaptability",
]

CONFIDENCE_PARAMS = [
    "Confidence Level",
    "Vocal Energy",
    "Professionalism",
]

TECHNICAL_PARAMS = [
    "Accuracy",
    "Completeness",
    "Depth of Knowledge",
    "Relevance",
    "Problem Solving",
    "Real-world Examples",
    "Trade-off Analysis",
    "Decision Making",
    "Learning Agility",
]

BEHAVIORAL_PARAMS = [
    "STAR Framework",
    "Ownership",
    "Collaboration",
    "Leadership Potential",
    "Conflict Resolution",
]

ENGAGEMENT_PARAMS = [
    "Audience Engagement",
    "Storytelling",
    "Persuasion",
]

STRUCTURE_PARAMS = [
    "Structure & Coherence",
    "Answer Organization",
]

INTERVIEW_SKILLS_PARAMS = [
    "Follow-up Handling",
    "Time Management",
    "Consistency",
]

VIDEO_PARAMS = [
    "Eye Contact",
    "Posture",
    "Gestures",
]

ALL_TRANSCRIPT_PARAMS = (
    COMMUNICATION_PARAMS
    + CONFIDENCE_PARAMS
    + TECHNICAL_PARAMS
    + BEHAVIORAL_PARAMS
    + ENGAGEMENT_PARAMS
    + STRUCTURE_PARAMS
    + INTERVIEW_SKILLS_PARAMS
)

CATEGORY_MAP: dict[str, list[str]] = {
    "communication": COMMUNICATION_PARAMS + CONFIDENCE_PARAMS,
    "technical": TECHNICAL_PARAMS,
    "behavioral": BEHAVIORAL_PARAMS + ENGAGEMENT_PARAMS + STRUCTURE_PARAMS + INTERVIEW_SKILLS_PARAMS,
}
