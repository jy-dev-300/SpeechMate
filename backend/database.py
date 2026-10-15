"""SQLAlchemy persistence for sessions and normalized pronunciation observations."""

import json
from collections.abc import Iterator
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, create_engine, select
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)
from sqlalchemy.pool import StaticPool

from models.learner import SessionEvidence
from speech.pipeline import AnalysisResult
from speech.types import IssueKind, PronunciationObservation


class Base(DeclarativeBase):
    pass


class PracticeSession(Base):
    """One immutable attempt; corrections should become new sessions, not silent edits."""

    __tablename__ = "practice_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    learner_id: Mapped[str] = mapped_column(String(100), index=True)
    expected_text: Mapped[str] = mapped_column(Text)
    transcript: Mapped[str] = mapped_column(Text)
    asr_provider: Mapped[str] = mapped_column(String(50))
    expected_symbols_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    observations: Mapped[list["Observation"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class Observation(Base):
    """Normalized issue rows support phoneme-level aggregation across sessions."""

    __tablename__ = "observations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("practice_sessions.id"), index=True)
    expected_symbol: Mapped[str | None] = mapped_column(String(16), index=True)
    observed_symbol: Mapped[str | None] = mapped_column(String(16))
    word: Mapped[str] = mapped_column(String(100))
    kind: Mapped[str] = mapped_column(String(30))
    confidence: Mapped[float] = mapped_column(Float)
    start_seconds: Mapped[float | None] = mapped_column(Float)
    end_seconds: Mapped[float | None] = mapped_column(Float)
    explanation: Mapped[str] = mapped_column(Text)
    session: Mapped[PracticeSession] = relationship(back_populates="observations")


class Database:
    """Own the engine and short-lived unit-of-work sessions."""

    def __init__(self, url: str) -> None:
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        # A shared pool keeps an in-memory SQLite schema visible across FastAPI worker threads.
        in_memory = url in {"sqlite://", "sqlite:///:memory:"}
        pool_options = {"poolclass": StaticPool} if in_memory else {}
        self.engine = create_engine(url, connect_args=connect_args, **pool_options)
        self._session_factory = sessionmaker(self.engine, expire_on_commit=False)

    def create_schema(self) -> None:
        Base.metadata.create_all(self.engine)

    def session(self) -> Iterator[Session]:
        with self._session_factory() as database_session:
            yield database_session


class PracticeRepository:
    """Translate database rows to domain evidence used by learner aggregation."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(
        self,
        *,
        learner_id: str,
        expected_text: str,
        analysis: AnalysisResult,
        session_id: str | None = None,
    ) -> str:
        identifier = session_id or str(uuid4())
        row = PracticeSession(
            id=identifier,
            learner_id=learner_id,
            expected_text=expected_text,
            transcript=analysis.transcript.text,
            asr_provider=analysis.transcript.provider,
            expected_symbols_json=json.dumps([item.symbol for item in analysis.expected_phonemes]),
            created_at=datetime.now(UTC),
        )
        row.observations = [
            Observation(
                id=str(uuid4()),
                expected_symbol=item.expected_symbol,
                observed_symbol=item.observed_symbol,
                word=item.word,
                kind=item.kind.value,
                confidence=item.confidence,
                start_seconds=item.start_seconds,
                end_seconds=item.end_seconds,
                explanation=item.explanation,
            )
            for item in analysis.observations
        ]
        self._session.add(row)
        self._session.commit()
        return identifier

    def history(self, learner_id: str) -> list[SessionEvidence]:
        statement = (
            select(PracticeSession)
            .where(PracticeSession.learner_id == learner_id)
            .order_by(PracticeSession.created_at)
        )
        rows = self._session.scalars(statement).unique().all()
        return [
            SessionEvidence(
                session_id=row.id,
                recorded_at=row.created_at,
                expected_symbols=tuple(json.loads(row.expected_symbols_json)),
                observations=tuple(_to_domain(item) for item in row.observations),
            )
            for row in rows
        ]


def _to_domain(row: Observation) -> PronunciationObservation:
    return PronunciationObservation(
        expected_symbol=row.expected_symbol,
        observed_symbol=row.observed_symbol,
        word=row.word,
        kind=IssueKind(row.kind),
        confidence=row.confidence,
        start_seconds=row.start_seconds,
        end_seconds=row.end_seconds,
        explanation=row.explanation,
    )
