export interface ParameterScore {
  parameter: string;
  category: string;
  score: number;
  confidence: number;
  evidence: string;
  strengths: string[];
  improvements: string[];
}

export interface DeliveryMetrics {
  duration_seconds: number;
  speaking_time_seconds: number;
  silence_time_seconds: number;
  speech_silence_ratio: number;
  average_pause_length_seconds: number;
  long_pause_count: number;
  words_per_minute: number;
}

export interface AudioMetrics {
  delivery: DeliveryMetrics;
  confidence: {
    pitch_average_hz: number;
    pitch_variance: number;
    pitch_stability: number;
    rms_energy: number;
    energy_variance: number;
    vocal_intensity: number;
  };
  engagement: {
    energy_variation: number;
    pitch_variation: number;
    monotone_score: number;
    enthusiasm_score: number;
  };
  quality: {
    background_noise_estimate: number;
    audio_quality_score: number;
    clipping_detected: boolean;
  };
}

export interface VideoMetrics {
  eye_contact_score?: number;
  posture_score?: number;
  gestures_score?: number;
  frames_analyzed: number;
  notes: string;
}

export interface CategoryScores {
  score: number;
  parameters: ParameterScore[];
}

export interface AnalyzeResponse {
  status: string;
  overallScore: number;
  hireRecommendation: string;
  communicationScore: number;
  technicalScore: number;
  behavioralScore: number;
  confidenceScore: number;
  engagementScore: number;
  communication: CategoryScores;
  technical: CategoryScores;
  behavioral: CategoryScores;
  audioMetrics: AudioMetrics;
  videoMetrics?: VideoMetrics;
  transcript: string;
  parameterScores: ParameterScore[];
  processingTimeSeconds: number;
}
