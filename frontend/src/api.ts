import type { AttemptResult } from "./types";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export async function submitAttempt(input: {
  expectedText: string;
  observedText: string;
  audio: Blob | null;
}): Promise<AttemptResult> {
  const audioBase64 = input.audio ? await blobToBase64(input.audio) : undefined;
  const response = await fetch(`${API_URL}/v1/attempts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      // The stable browser-local learner ID is sufficient for the unauthenticated v1 demo.
      learner_id: getLearnerId(),
      expected_text: input.expectedText,
      observed_text: input.observedText || undefined,
      audio_base64: audioBase64,
      duration_seconds: input.audio ? undefined : 2.4,
    }),
  });
  if (!response.ok) {
    const problem = await response.json().catch(() => ({ detail: "Analysis failed" }));
    throw new Error(problem.detail ?? "Analysis failed");
  }
  return response.json() as Promise<AttemptResult>;
}

function getLearnerId(): string {
  const key = "speechmate-learner-id";
  const existing = localStorage.getItem(key);
  if (existing) return existing;
  const created = crypto.randomUUID();
  localStorage.setItem(key, created);
  return created;
}

function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(reader.error);
    reader.onload = () => resolve(String(reader.result).split(",", 2)[1]);
    reader.readAsDataURL(blob);
  });
}
