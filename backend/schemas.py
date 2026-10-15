"""Validated API contracts kept separate from SQLAlchemy rows and domain values."""

from pydantic import BaseModel, Field, field_validator


class AnalyzeRequest(BaseModel):
    learner_id: str = Field(min_length=1, max_length=100)
    expected_text: str = Field(min_length=1, max_length=500)
    audio_base64: str | None = None
    observed_text: str | None = Field(default=None, max_length=500)
    duration_seconds: float | None = Field(default=None, gt=0, le=120)

    @field_validator("expected_text", "learner_id")
    @classmethod
    def reject_whitespace_only(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value.strip()


class ObservationResponse(BaseModel):
    expected_symbol: str | None
    observed_symbol: str | None
    word: str
    kind: str
    confidence: float
    start_seconds: float | None
    end_seconds: float | None
    explanation: str


class WeaknessResponse(BaseModel):
    phoneme: str
    error_rate: float
    weighted_confidence: float
    opportunity_count: int
    error_count: int
    distinct_words: int
    distinct_sessions: int
    persistent: bool
    recommended_prompt: str


class AnalyzeResponse(BaseModel):
    session_id: str
    transcript: str
    asr_provider: str
    observations: list[ObservationResponse]
    learner_profile: list[WeaknessResponse]

