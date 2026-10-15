from pathlib import Path

from backend.database import Database, PracticeRepository
from models.learner import build_learner_profile
from speech.asr import DeterministicASR
from speech.phonemes import LexiconPhonemeAdapter
from speech.pipeline import PronunciationPipeline


def test_attempts_survive_repository_boundaries_and_update_profile(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'test.sqlite3'}")
    database.create_schema()
    pipeline = PronunciationPipeline(DeterministicASR(), LexiconPhonemeAdapter())

    for expected, observed in [
        ("red", "led"),
        ("road", "load"),
        ("really", "leally"),
        ("remote", "lemote"),
    ]:
        analysis = pipeline.analyze(
            expected_text=expected,
            observed_text=observed,
            audio=b"fixture",
        )
        with next(database.session()) as session:
            PracticeRepository(session).save(
                learner_id="learner-1",
                expected_text=expected,
                analysis=analysis,
            )

    with next(database.session()) as session:
        history = PracticeRepository(session).history("learner-1")
        profile = build_learner_profile(history)

    assert len(history) == 4
    assert profile[0].phoneme == "R"
    assert profile[0].persistent is True

