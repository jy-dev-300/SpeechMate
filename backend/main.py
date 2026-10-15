"""FastAPI composition root: configuration, adapters, persistence, and HTTP translation."""

import base64
import binascii
from contextlib import asynccontextmanager
from dataclasses import asdict
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.config import Settings
from backend.database import Database, PracticeRepository
from backend.schemas import AnalyzeRequest, AnalyzeResponse
from models.learner import build_learner_profile
from speech.asr import DeterministicASR, FasterWhisperASR
from speech.phonemes import LexiconPhonemeAdapter
from speech.pipeline import PronunciationPipeline

settings = Settings.from_environment()
database = Database(settings.database_url)


def _build_pipeline() -> PronunciationPipeline:
    """Select model infrastructure once so requests never branch on provider details."""

    if settings.asr_provider == "deterministic":
        asr = DeterministicASR()
    elif settings.asr_provider == "faster-whisper":
        asr = FasterWhisperASR(settings.whisper_model)
    else:
        raise RuntimeError(f"unsupported ASR_PROVIDER: {settings.asr_provider}")
    return PronunciationPipeline(asr=asr, phonemizer=LexiconPhonemeAdapter())


pipeline = _build_pipeline()


@asynccontextmanager
async def lifespan(_: FastAPI):
    database.create_schema()
    yield


app = FastAPI(title="SpeechMate API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allowed_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def database_session() -> Session:
    """Provide one transaction scope per request and always release its connection."""

    yield from database.session()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "asr_provider": settings.asr_provider}


@app.post("/v1/attempts", response_model=AnalyzeResponse)
def analyze_attempt(
    request: AnalyzeRequest,
    session: Annotated[Session, Depends(database_session)],
) -> AnalyzeResponse:
    """Analyze, persist, then rebuild the learner profile from durable evidence."""

    try:
        if settings.asr_provider != "deterministic" and request.audio_base64 is None:
            raise ValueError("audio_base64 is required for the configured ASR provider")
        # Deterministic demos still pass non-empty bytes through the same preprocessing boundary.
        audio = (
            base64.b64decode(request.audio_base64, validate=True)
            if request.audio_base64
            else b"fixture"
        )
        analysis = pipeline.analyze(
            expected_text=request.expected_text,
            audio=audio,
            observed_text=request.observed_text,
            duration_seconds=request.duration_seconds,
        )
    except (ValueError, binascii.Error) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    repository = PracticeRepository(session)
    session_id = repository.save(
        learner_id=request.learner_id,
        expected_text=request.expected_text,
        analysis=analysis,
    )
    profile = build_learner_profile(repository.history(request.learner_id))
    return AnalyzeResponse(
        session_id=session_id,
        transcript=analysis.transcript.text,
        asr_provider=analysis.transcript.provider,
        observations=[
            {
                "expected_symbol": item.expected_symbol,
                "observed_symbol": item.observed_symbol,
                "word": item.word,
                "kind": item.kind.value,
                "confidence": item.confidence,
                "start_seconds": item.start_seconds,
                "end_seconds": item.end_seconds,
                "explanation": item.explanation,
            }
            for item in analysis.observations
        ],
        learner_profile=[asdict(item) for item in profile],
    )
