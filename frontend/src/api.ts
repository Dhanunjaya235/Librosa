import { AnalyzeResponse } from "./types";

const API_BASE = import.meta.env.VITE_API_URL || "";

export async function analyzeInterview(file: File): Promise<AnalyzeResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/api/v1/interview/analyze`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(err.detail || "Analysis failed");
  }

  return response.json();
}
