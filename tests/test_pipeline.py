from speech.asr import DeterministicASR
from speech.phonemes import LexiconPhonemeAdapter
from speech.pipeline import PronunciationPipeline
from speech.types import IssueKind


def test_offline_pipeline_detects_r_to_l_substitution() -> None:
    pipeline = PronunciationPipeline(DeterministicASR(), LexiconPhonemeAdapter())

    result = pipeline.analyze(expected_text="red", observed_text="led", audio=b"fixture")

    assert result.transcript.provider == "deterministic-fixture"
    assert result.observations[0].expected_symbol == "R"
    assert result.observations[0].observed_symbol == "L"
    assert result.observations[0].kind is IssueKind.SUBSTITUTION

