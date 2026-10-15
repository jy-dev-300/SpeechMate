"""Shared immutable values passed between speech-processing stages."""

from dataclasses import dataclass
from enum import StrEnum


class AlignmentOperation(StrEnum):
    MATCH = "match"
    SUBSTITUTION = "substitution"
    OMISSION = "omission"
    INSERTION = "insertion"


class IssueKind(StrEnum):
    SUBSTITUTION = "substitution"
    OMISSION = "omission"
    INSERTION = "insertion"
    TIMING = "timing"
    UNCERTAIN = "uncertain"


@dataclass(frozen=True, slots=True)
class Transcript:
    """ASR output plus confidence, kept separate from the expected prompt."""

    text: str
    confidence: float
    provider: str


@dataclass(frozen=True, slots=True)
class Phoneme:
    """A phoneme symbol optionally grounded in audio time."""

    symbol: str
    word: str
    start_seconds: float | None = None
    end_seconds: float | None = None
    confidence: float = 1.0


@dataclass(frozen=True, slots=True)
class AlignedUnit:
    """One comparable expected/observed unit produced by sequence alignment."""

    expected: Phoneme | None
    observed: Phoneme | None
    operation: AlignmentOperation
    confidence: float


@dataclass(frozen=True, slots=True)
class PronunciationObservation:
    """A scored issue ready for persistence and learner-profile aggregation."""

    expected_symbol: str | None
    observed_symbol: str | None
    word: str
    kind: IssueKind
    confidence: float
    start_seconds: float | None
    end_seconds: float | None
    explanation: str

