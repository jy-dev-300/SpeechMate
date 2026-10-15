"""Application-level orchestration for one pronunciation attempt."""

from dataclasses import dataclass

from speech.alignment import add_uniform_timing, align_phonemes
from speech.asr import ASRAdapter
from speech.phonemes import PhonemeAdapter
from speech.preprocessing import AudioInfo, inspect_audio
from speech.scoring import ScoringPolicy, score_alignment
from speech.types import AlignedUnit, Phoneme, PronunciationObservation, Transcript


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    transcript: Transcript
    audio: AudioInfo
    expected_phonemes: tuple[Phoneme, ...]
    observed_phonemes: tuple[Phoneme, ...]
    alignment: tuple[AlignedUnit, ...]
    observations: tuple[PronunciationObservation, ...]


class PronunciationPipeline:
    """Coordinate model adapters and deterministic engineering logic."""

    def __init__(
        self,
        asr: ASRAdapter,
        phonemizer: PhonemeAdapter,
        scoring_policy: ScoringPolicy | None = None,
    ) -> None:
        self._asr = asr
        self._phonemizer = phonemizer
        self._scoring_policy = scoring_policy or ScoringPolicy()

    def analyze(
        self,
        *,
        expected_text: str,
        audio: bytes,
        observed_text: str | None = None,
        duration_seconds: float | None = None,
    ) -> AnalysisResult:
        """Run one recording through the pipeline without performing persistence."""

        if not expected_text.strip():
            raise ValueError("expected_text must not be blank")
        audio_info = inspect_audio(audio)
        transcript = self._asr.transcribe(audio, hint=observed_text)
        expected = self._phonemizer.phonemize(expected_text)
        observed = self._phonemizer.phonemize(transcript.text)
        if not expected:
            raise ValueError("expected_text did not produce any English phonemes")

        # Transcript confidence is copied onto each observed unit so uncertainty survives alignment.
        observed = [
            Phoneme(symbol=item.symbol, word=item.word, confidence=transcript.confidence)
            for item in observed
        ]
        timing_duration = audio_info.duration_seconds or duration_seconds
        observed = add_uniform_timing(observed, timing_duration)
        alignment = align_phonemes(expected, observed)
        observations = score_alignment(alignment, self._scoring_policy)
        return AnalysisResult(
            transcript=transcript,
            audio=audio_info,
            expected_phonemes=tuple(expected),
            observed_phonemes=tuple(observed),
            alignment=tuple(alignment),
            observations=tuple(observations),
        )
