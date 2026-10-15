"""Cheap safety checks performed before expensive model inference."""

import io
import wave
from dataclasses import dataclass

MAX_AUDIO_BYTES = 15 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class AudioInfo:
    byte_count: int
    container: str
    duration_seconds: float | None
    sample_rate_hz: int | None


def inspect_audio(audio: bytes) -> AudioInfo:
    """Reject empty/oversized payloads and extract WAV metadata when available.

    Compressed formats are intentionally preserved for the ASR provider to decode. This avoids a
    lossy transcode and makes FFmpeg an ASR-adapter concern rather than a request-path requirement.
    """

    if not audio:
        raise ValueError("audio payload is empty")
    if len(audio) > MAX_AUDIO_BYTES:
        raise ValueError(f"audio payload exceeds {MAX_AUDIO_BYTES} bytes")

    if not audio.startswith(b"RIFF"):
        return AudioInfo(len(audio), "compressed-or-unknown", None, None)

    try:
        with wave.open(io.BytesIO(audio), "rb") as source:
            rate = source.getframerate()
            duration = source.getnframes() / rate if rate else None
            return AudioInfo(len(audio), "wav", duration, rate)
    except wave.Error as exc:
        raise ValueError("payload has a RIFF header but is not a valid WAV file") from exc
