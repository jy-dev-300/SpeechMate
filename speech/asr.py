"""ASR adapters: commodity inference lives here; product logic does not."""

from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Protocol

from speech.types import Transcript


class ASRAdapter(Protocol):
    """Contract implemented by local or hosted transcription providers."""

    def transcribe(self, audio: bytes, *, hint: str | None = None) -> Transcript: ...


class DeterministicASR:
    """Offline adapter that treats an explicit hint as model output.

    It proves control flow and lets fixtures express known errors. It does not provide evidence of
    acoustic recognition quality and is rejected when no hint is supplied.
    """

    def transcribe(self, audio: bytes, *, hint: str | None = None) -> Transcript:
        if not hint or not hint.strip():
            raise ValueError("deterministic ASR requires observed_text")
        return Transcript(text=hint.strip(), confidence=0.92, provider="deterministic-fixture")


class FasterWhisperASR:
    """Optional local Whisper adapter used when ASR_PROVIDER=faster-whisper."""

    def __init__(self, model_name: str = "small.en") -> None:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError("install SpeechMate with the 'speech' extra") from exc
        self._model = WhisperModel(model_name, device="cpu", compute_type="int8")

    def transcribe(self, audio: bytes, *, hint: str | None = None) -> Transcript:
        # A named file gives FFmpeg a stable path while delete=False supports Windows file locking.
        path: Path | None = None
        try:
            with NamedTemporaryFile(suffix=".audio", delete=False) as temporary:
                temporary.write(audio)
                path = Path(temporary.name)
            segments, info = self._model.transcribe(str(path), language="en", beam_size=5)
            text = " ".join(segment.text.strip() for segment in segments).strip()
            # Whisper exposes language probability, not calibrated transcript correctness. The name
            # makes that limitation explicit while still propagating model uncertainty downstream.
            confidence = max(0.0, min(1.0, float(info.language_probability)))
            return Transcript(text=text, confidence=confidence, provider="faster-whisper")
        finally:
            if path is not None:
                path.unlink(missing_ok=True)
