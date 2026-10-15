"""Aggregation logic that separates one-off mistakes from persistent weaknesses."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

from speech.types import IssueKind, PronunciationObservation


@dataclass(frozen=True, slots=True)
class SessionEvidence:
    session_id: str
    recorded_at: datetime
    expected_symbols: tuple[str, ...]
    observations: tuple[PronunciationObservation, ...]


@dataclass(frozen=True, slots=True)
class PhonemeWeakness:
    phoneme: str
    error_rate: float
    weighted_confidence: float
    opportunity_count: int
    error_count: int
    distinct_words: int
    distinct_sessions: int
    persistent: bool
    recommended_prompt: str


def build_learner_profile(history: list[SessionEvidence]) -> list[PhonemeWeakness]:
    """Aggregate evidence by expected phoneme using conservative persistence thresholds.

    A Beta(1,1) prior smooths small samples, so one error never appears as 100% failure. Uncertain
    observations are retained for auditability but excluded from weakness evidence.
    """

    opportunities: dict[str, int] = defaultdict(int)
    errors: dict[str, list[tuple[str, str, float]]] = defaultdict(list)

    for session in history:
        for symbol in session.expected_symbols:
            opportunities[symbol] += 1
        for observation in session.observations:
            if observation.expected_symbol and observation.kind is not IssueKind.UNCERTAIN:
                errors[observation.expected_symbol].append(
                    (session.session_id, observation.word, observation.confidence)
                )

    weaknesses: list[PhonemeWeakness] = []
    for symbol, evidence in errors.items():
        count = len(evidence)
        total = opportunities[symbol]
        sessions = {item[0] for item in evidence}
        words = {item[1] for item in evidence}
        posterior_rate = (count + 1) / (total + 2)
        confidence = sum(item[2] for item in evidence) / count
        persistent = (
            len(sessions) >= 3
            and len(words) >= 3
            and count >= 4
            and posterior_rate >= 0.35
            and confidence >= 0.6
        )
        weaknesses.append(
            PhonemeWeakness(
                phoneme=symbol,
                error_rate=round(posterior_rate, 3),
                weighted_confidence=round(confidence, 3),
                opportunity_count=total,
                error_count=count,
                distinct_words=len(words),
                distinct_sessions=len(sessions),
                persistent=persistent,
                recommended_prompt=_practice_prompt(symbol, persistent),
            )
        )

    return sorted(weaknesses, key=lambda item: (item.persistent, item.error_rate), reverse=True)


def _practice_prompt(symbol: str, persistent: bool) -> str:
    """Generate deterministic practice without delegating correctness to an LLM."""

    intensity = "focused minimal-pair" if persistent else "short review"
    return f"Try a {intensity} drill for /{symbol}/, then record the phrase again."

