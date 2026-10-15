"""Environment-backed runtime configuration.

Keeping configuration in one immutable object makes provider selection visible and keeps secrets
out of domain logic. Tests can construct Settings directly without mutating global environment.
"""

import os
from dataclasses import dataclass

DEFAULT_DATABASE_URL = "sqlite:///./speechmate.sqlite3"
DEFAULT_ASR_PROVIDER = "deterministic"
DEFAULT_WHISPER_MODEL = "small.en"
DEFAULT_ALLOWED_ORIGIN = "http://localhost:5173"


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str = DEFAULT_DATABASE_URL
    asr_provider: str = DEFAULT_ASR_PROVIDER
    whisper_model: str = DEFAULT_WHISPER_MODEL
    allowed_origins: tuple[str, ...] = (DEFAULT_ALLOWED_ORIGIN,)

    @classmethod
    def from_environment(cls) -> "Settings":
        """Read process configuration once at application startup."""

        origins = os.getenv("ALLOWED_ORIGINS", DEFAULT_ALLOWED_ORIGIN)
        return cls(
            database_url=os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL),
            asr_provider=os.getenv("ASR_PROVIDER", DEFAULT_ASR_PROVIDER),
            whisper_model=os.getenv("WHISPER_MODEL", DEFAULT_WHISPER_MODEL),
            allowed_origins=tuple(item.strip() for item in origins.split(",") if item.strip()),
        )
