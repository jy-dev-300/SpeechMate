from speech.scoring import score_alignment
from speech.types import AlignedUnit, AlignmentOperation, IssueKind, Phoneme


def test_low_confidence_mismatch_is_uncertain_not_a_false_claim() -> None:
    unit = AlignedUnit(
        expected=Phoneme("R", "red"),
        observed=Phoneme("L", "led", confidence=0.3),
        operation=AlignmentOperation.SUBSTITUTION,
        confidence=0.3,
    )

    observations = score_alignment([unit])

    assert observations[0].kind is IssueKind.UNCERTAIN


def test_confident_match_emits_no_negative_feedback() -> None:
    phone = Phoneme("R", "red", start_seconds=0.0, end_seconds=0.15)
    unit = AlignedUnit(phone, phone, AlignmentOperation.MATCH, confidence=0.9)

    assert score_alignment([unit]) == []

