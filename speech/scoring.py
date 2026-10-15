"""Explainable pronunciation scoring built on aligned phoneme units."""

from dataclasses import dataclass

from speech.types import AlignedUnit, AlignmentOperation, IssueKind, PronunciationObservation


@dataclass(frozen=True, slots=True)
class ScoringPolicy:
    """Thresholds are data, so evaluation can tune them without rewriting control flow."""

    minimum_confidence: float = 0.55
    minimum_duration_seconds: float = 0.035
    maximum_duration_seconds: float = 0.45


def score_alignment(
    units: list[AlignedUnit], policy: ScoringPolicy | None = None
) -> list[PronunciationObservation]:
    """Convert edit operations and timing evidence into user-facing observations."""

    policy = policy or ScoringPolicy()
    observations: list[PronunciationObservation] = []
    for unit in units:
        expected_symbol = unit.expected.symbol if unit.expected else None
        observed_symbol = unit.observed.symbol if unit.observed else None
        anchor = unit.expected or unit.observed
        if anchor is None:  # Defensive only: the aligner never emits a doubly-empty unit.
            continue

        if unit.confidence < policy.minimum_confidence:
            kind = IssueKind.UNCERTAIN
            explanation = "The evidence is too weak to label this sound as an error."
        elif unit.operation is AlignmentOperation.SUBSTITUTION:
            kind = IssueKind.SUBSTITUTION
            explanation = f"Expected /{expected_symbol}/ but heard /{observed_symbol}/."
        elif unit.operation is AlignmentOperation.OMISSION:
            kind = IssueKind.OMISSION
            explanation = f"The expected /{expected_symbol}/ was not detected."
        elif unit.operation is AlignmentOperation.INSERTION:
            kind = IssueKind.INSERTION
            explanation = f"An extra /{observed_symbol}/ was detected."
        else:
            duration = _duration(unit)
            in_expected_range = (
                duration is not None
                and policy.minimum_duration_seconds <= duration <= policy.maximum_duration_seconds
            )
            if duration is None or in_expected_range:
                continue
            kind = IssueKind.TIMING
            explanation = (
                f"/{expected_symbol}/ duration ({duration:.2f}s) is outside the practice range."
            )

        observations.append(
            PronunciationObservation(
                expected_symbol=expected_symbol,
                observed_symbol=observed_symbol,
                word=anchor.word,
                kind=kind,
                confidence=round(unit.confidence, 3),
                start_seconds=unit.observed.start_seconds if unit.observed else None,
                end_seconds=unit.observed.end_seconds if unit.observed else None,
                explanation=explanation,
            )
        )
    return observations


def _duration(unit: AlignedUnit) -> float | None:
    """Return an observed duration only when both acoustic boundaries exist."""

    if (
        unit.observed is None
        or unit.observed.start_seconds is None
        or unit.observed.end_seconds is None
    ):
        return None
    return max(0.0, unit.observed.end_seconds - unit.observed.start_seconds)
