import { ReactNode } from "react";
import { AnalyzeResponse, ParameterScore } from "../types";

interface Props {
  result: AnalyzeResponse;
}

function ScoreBadge({ score }: { score: number }) {
  const color =
    score >= 80 ? "#16a34a" : score >= 60 ? "#ca8a04" : "#dc2626";
  return (
    <span style={{ color, fontWeight: 700, fontSize: "1.1rem" }}>
      {score.toFixed(0)}
    </span>
  );
}

function ParameterCard({ param }: { param: ParameterScore }) {
  return (
    <div
      style={{
        border: "1px solid #e5e7eb",
        borderRadius: 8,
        padding: 12,
        marginBottom: 8,
        background: "#fafafa",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <strong>{param.parameter}</strong>
        <ScoreBadge score={param.score} />
      </div>
      <div style={{ fontSize: "0.85rem", color: "#6b7280", marginTop: 4 }}>
        Confidence: {param.confidence.toFixed(0)}%
      </div>
      <p style={{ margin: "8px 0", fontSize: "0.9rem" }}>{param.evidence}</p>
      {param.strengths.length > 0 && (
        <div style={{ fontSize: "0.85rem" }}>
          <strong style={{ color: "#16a34a" }}>Strengths:</strong>{" "}
          {param.strengths.join("; ")}
        </div>
      )}
      {param.improvements.length > 0 && (
        <div style={{ fontSize: "0.85rem", marginTop: 4 }}>
          <strong style={{ color: "#dc2626" }}>Improvements:</strong>{" "}
          {param.improvements.join("; ")}
        </div>
      )}
    </div>
  );
}

export default function ResultsPanel({ result }: Props) {
  const hireColor: Record<string, string> = {
    "Strong Hire": "#16a34a",
    Hire: "#22c55e",
    "Lean Hire": "#ca8a04",
    Borderline: "#f97316",
    "No Hire": "#dc2626",
  };

  return (
    <div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
          gap: 12,
          marginBottom: 24,
        }}
      >
        {[
          ["Overall", result.overallScore],
          ["Communication", result.communicationScore],
          ["Technical", result.technicalScore],
          ["Behavioral", result.behavioralScore],
          ["Confidence", result.confidenceScore],
          ["Engagement", result.engagementScore],
        ].map(([label, score]) => (
          <div
            key={label as string}
            style={{
              background: "#fff",
              border: "1px solid #e5e7eb",
              borderRadius: 8,
              padding: 16,
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: "0.85rem", color: "#6b7280" }}>{label}</div>
            <ScoreBadge score={score as number} />
          </div>
        ))}
      </div>

      <div
        style={{
          background: hireColor[result.hireRecommendation] || "#333",
          color: "#fff",
          padding: "12px 20px",
          borderRadius: 8,
          marginBottom: 24,
          fontSize: "1.2rem",
          fontWeight: 600,
        }}
      >
        Recommendation: {result.hireRecommendation}
        <span style={{ fontSize: "0.85rem", marginLeft: 12, opacity: 0.9 }}>
          ({result.processingTimeSeconds}s processing)
        </span>
      </div>

      <Section title="Audio Metrics">
        <MetricsGrid
          items={[
            ["Duration", `${result.audioMetrics.delivery.duration_seconds}s`],
            ["WPM", `${result.audioMetrics.delivery.words_per_minute}`],
            ["Speech/Silence", `${result.audioMetrics.delivery.speech_silence_ratio}`],
            ["Avg Pause", `${result.audioMetrics.delivery.average_pause_length_seconds}s`],
            ["Long Pauses", `${result.audioMetrics.delivery.long_pause_count}`],
            ["Pitch Stability", `${result.audioMetrics.confidence.pitch_stability}`],
            ["Enthusiasm", `${result.audioMetrics.engagement.enthusiasm_score}`],
            ["Audio Quality", `${result.audioMetrics.quality.audio_quality_score}`],
          ]}
        />
      </Section>

      {result.videoMetrics && result.videoMetrics.frames_analyzed > 0 && (
        <Section title="Video Metrics">
          <MetricsGrid
            items={[
              ["Eye Contact", `${result.videoMetrics.eye_contact_score ?? "N/A"}`],
              ["Posture", `${result.videoMetrics.posture_score ?? "N/A"}`],
              ["Gestures", `${result.videoMetrics.gestures_score ?? "N/A"}`],
              ["Frames", `${result.videoMetrics.frames_analyzed}`],
            ]}
          />
        </Section>
      )}

      <Section title="Transcript">
        <pre
          style={{
            background: "#f3f4f6",
            padding: 16,
            borderRadius: 8,
            whiteSpace: "pre-wrap",
            fontSize: "0.9rem",
            maxHeight: 200,
            overflow: "auto",
          }}
        >
          {result.transcript || "(empty transcript)"}
        </pre>
      </Section>

      <Section title={`Parameter Scores (${result.parameterScores.length})`}>
        {result.parameterScores.map((p) => (
          <ParameterCard key={p.parameter} param={p} />
        ))}
      </Section>
    </div>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div style={{ marginBottom: 24 }}>
      <h2 style={{ fontSize: "1.1rem", borderBottom: "2px solid #e5e7eb", paddingBottom: 8 }}>
        {title}
      </h2>
      {children}
    </div>
  );
}

function MetricsGrid({ items }: { items: [string, string][] }) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
        gap: 8,
      }}
    >
      {items.map(([k, v]) => (
        <div
          key={k}
          style={{
            background: "#f9fafb",
            padding: "8px 12px",
            borderRadius: 6,
            fontSize: "0.9rem",
          }}
        >
          <span style={{ color: "#6b7280" }}>{k}: </span>
          <strong>{v}</strong>
        </div>
      ))}
    </div>
  );
}
