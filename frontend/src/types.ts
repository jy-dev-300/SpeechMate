export type Observation = {
  expected_symbol: string | null;
  observed_symbol: string | null;
  word: string;
  kind: "substitution" | "omission" | "insertion" | "timing" | "uncertain";
  confidence: number;
  explanation: string;
};

export type Weakness = {
  phoneme: string;
  error_rate: number;
  error_count: number;
  distinct_sessions: number;
  persistent: boolean;
  recommended_prompt: string;
};

export type AttemptResult = {
  session_id: string;
  transcript: string;
  asr_provider: string;
  observations: Observation[];
  learner_profile: Weakness[];
};

