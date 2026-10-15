from speech.alignment import align_phonemes
from speech.types import AlignmentOperation, Phoneme


def phone(symbol: str) -> Phoneme:
    return Phoneme(symbol=symbol, word="fixture")


def test_alignment_prefers_substitution_for_one_replaced_sound() -> None:
    aligned = align_phonemes(
        [phone("R"), phone("EH"), phone("D")],
        [phone("L"), phone("EH"), phone("D")],
    )

    assert [unit.operation for unit in aligned] == [
        AlignmentOperation.SUBSTITUTION,
        AlignmentOperation.MATCH,
        AlignmentOperation.MATCH,
    ]
    assert aligned[0].expected.symbol == "R"
    assert aligned[0].observed.symbol == "L"


def test_alignment_exposes_an_omitted_final_sound() -> None:
    aligned = align_phonemes([phone("R"), phone("AY"), phone("T")], [phone("R"), phone("AY")])

    assert aligned[-1].operation is AlignmentOperation.OMISSION
    assert aligned[-1].expected.symbol == "T"
