from datetime import UTC, datetime

from models.learner import SessionEvidence, build_learner_profile
from speech.types import IssueKind, PronunciationObservation


def evidence(session_number: int, word: str, *, error: bool = True) -> SessionEvidence:
    observation = PronunciationObservation(
        expected_symbol="R",
        observed_symbol="L",
        word=word,
        kind=IssueKind.SUBSTITUTION,
        confidence=0.9,
        start_seconds=None,
        end_seconds=None,
        explanation="fixture",
    )
    return SessionEvidence(
        session_id=f"session-{session_number}",
        recorded_at=datetime.now(UTC),
        expected_symbols=("R", "EH", "D"),
        observations=(observation,) if error else (),
    )


def test_one_error_is_not_called_a_persistent_weakness() -> None:
    profile = build_learner_profile([evidence(1, "red")])

    assert profile[0].persistent is False


def test_repeated_error_across_words_and_sessions_becomes_persistent() -> None:
    history = [
        evidence(1, "red"),
        evidence(2, "road"),
        evidence(3, "really"),
        evidence(4, "remote"),
    ]

    profile = build_learner_profile(history)

    assert profile[0].persistent is True
    assert profile[0].distinct_sessions == 4

