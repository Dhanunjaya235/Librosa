# AI Interview Assessment PoC

Proof of Concept for evaluating candidate interview performance from uploaded audio or video files.

## Features

- **Upload**: MP3, WAV, MP4, MOV (up to 1 hour)
- **Audio extraction**: FFmpeg → 16kHz mono WAV
- **Speech-to-text**: Faster-Whisper with segment timestamps
- **Audio analysis**: Librosa delivery, confidence, engagement, and quality metrics
- **Video analysis**: OpenCV-based eye contact, posture, gestures (when video uploaded)
- **LLM assessment**: OpenAI GPT evaluation of 30+ parameters across communication, technical, and behavioral categories
- **Fallback mode**: Heuristic scoring when `OPENAI_API_KEY` is not configured

## Architecture

```
backend/app/
├── api/routes/interview.py     # POST /api/v1/interview/analyze
├── services/
│   ├── audio_extractor.py      # FFmpeg normalization
│   ├── transcriber.py            # Faster-Whisper STT
│   ├── audio_analyzer.py         # Librosa metrics
│   ├── video_analyzer.py         # OpenCV heuristics
│   ├── transcript_analyzer.py    # LLM evaluation
│   ├── scoring_engine.py         # Aggregation & hire recommendation
│   ├── fallback_evaluator.py     # Rule-based fallback
│   └── pipeline.py               # Orchestration
└── models/schemas.py             # Pydantic models
```

## Quick Start (Local)

### Prerequisites

- Python 3.11+
- Node.js 20+
- FFmpeg installed and on PATH

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env       # Set OPENAI_API_KEY for LLM assessment
uvicorn app.main:app --reload --port 8000
```

Swagger docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

UI: http://localhost:5173

### Generate Sample Audio

```bash
cd samples
python generate_sample.py
```

## Docker

```bash
# Set your OpenAI key (optional — fallback mode works without it)
set OPENAI_API_KEY=sk-...

docker compose up --build
```

- API: http://localhost:8000/docs
- UI: http://localhost:8080

## API

### POST /api/v1/interview/analyze

**Request**: `multipart/form-data` with field `file`

**Response** (abbreviated):

```json
{
  "status": "success",
  "overallScore": 72.5,
  "hireRecommendation": "Lean Hire",
  "communicationScore": 75.0,
  "technicalScore": 70.0,
  "behavioralScore": 68.0,
  "audioMetrics": { "delivery": {}, "confidence": {}, "engagement": {}, "quality": {} },
  "transcript": "...",
  "parameterScores": [
    {
      "parameter": "Clarity",
      "category": "communication",
      "score": 78,
      "confidence": 85,
      "evidence": "...",
      "strengths": ["..."],
      "improvements": ["..."]
    }
  ]
}
```

### Hire Recommendation Thresholds

| Score  | Recommendation |
|--------|----------------|
| 90–100 | Strong Hire    |
| 80–89  | Hire           |
| 70–79  | Lean Hire      |
| 60–69  | Borderline     |
| < 60   | No Hire        |

## Assessment Parameters

**Communication**: Clarity, Fluency, Grammar, Vocabulary, Pace, Filler Words, Active Listening, Conciseness, Adaptability, Confidence Level, Vocal Energy, Professionalism

**Technical**: Accuracy, Completeness, Depth of Knowledge, Relevance, Problem Solving, Real-world Examples, Trade-off Analysis, Decision Making, Learning Agility

**Behavioral**: STAR Framework, Ownership, Collaboration, Leadership Potential, Conflict Resolution, Audience Engagement, Storytelling, Persuasion, Structure & Coherence, Answer Organization, Follow-up Handling, Time Management, Consistency

**Video** (if video supplied): Eye Contact, Posture, Gestures

## Postman

Import `postman/Interview_Assessment_API.postman_collection.json`.

## Future Integrations

The modular analyzer architecture supports plugging in:

- **Azure Pronunciation Assessment** — replace or augment `AudioAnalyzer` confidence metrics
- **ElevenLabs Scribe** — replace `Transcriber` with Scribe API

## Environment Variables

| Variable            | Default        | Description                    |
|---------------------|----------------|--------------------------------|
| OPENAI_API_KEY      | (empty)        | OpenAI key for LLM assessment  |
| OPENAI_MODEL        | gpt-4o-mini    | LLM model name                 |
| WHISPER_MODEL       | base           | Faster-Whisper model size        |
| WHISPER_DEVICE      | cpu            | cpu or cuda                    |
| WHISPER_COMPUTE_TYPE| int8           | Quantization type              |
| UPLOAD_DIR          | /tmp/...       | Temp upload directory          |
