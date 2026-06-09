import { useState } from "react";
import { analyzeInterview } from "./api";
import ResultsPanel from "./components/ResultsPanel";
import { AnalyzeResponse } from "./types";

const ACCEPT = ".mp3,.wav,.mp4,.mov,audio/mpeg,audio/wav,video/mp4,video/quicktime";

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await analyzeInterview(file);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 960, margin: "0 auto", padding: 24, fontFamily: "system-ui, sans-serif" }}>
      <h1 style={{ marginBottom: 4 }}>AI Interview Assessment</h1>
      <p style={{ color: "#6b7280", marginBottom: 24 }}>
        Upload an interview recording (MP3, WAV, MP4, MOV) for comprehensive AI evaluation.
      </p>

      <form
        onSubmit={handleSubmit}
        style={{
          background: "#fff",
          border: "1px solid #e5e7eb",
          borderRadius: 12,
          padding: 24,
          marginBottom: 32,
        }}
      >
        <input
          type="file"
          accept={ACCEPT}
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          style={{ marginBottom: 16, display: "block" }}
        />
        <button
          type="submit"
          disabled={!file || loading}
          style={{
            background: loading ? "#9ca3af" : "#2563eb",
            color: "#fff",
            border: "none",
            padding: "10px 24px",
            borderRadius: 8,
            cursor: loading || !file ? "not-allowed" : "pointer",
            fontSize: "1rem",
          }}
        >
          {loading ? "Analyzing… (this may take a few minutes)" : "Analyze Interview"}
        </button>
      </form>

      {error && (
        <div
          style={{
            background: "#fef2f2",
            border: "1px solid #fecaca",
            color: "#dc2626",
            padding: 16,
            borderRadius: 8,
            marginBottom: 24,
          }}
        >
          {error}
        </div>
      )}

      {result && <ResultsPanel result={result} />}
    </div>
  );
}
