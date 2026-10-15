# SpeechMate

SpeechMate is an English pronunciation coach that remembers patterns across practice sessions. It
does more than send a transcript to an LLM: an explicit speech pipeline aligns phoneme sequences,
scores likely pronunciation events with uncertainty, stores evidence, and promotes a problem to a
persistent weakness only after it recurs across multiple words and sessions.

## What ships in this first version

- a FastAPI API with SQLite for zero-configuration use and PostgreSQL in Docker Compose;
- replaceable deterministic and Faster Whisper ASR adapters;
- an explainable English grapheme-to-phoneme adapter;
- global phoneme-sequence alignment and rule-based error scoring;
- a persistent learner profile with sample-size and confidence gates;
- labeled evaluation metrics that do not use an LLM as the judge;
- a responsive React recording and feedback experience;
- deterministic tests for the complete offline control flow.

The bundled lexicon and uniform timing adapter are intentionally small. They make the product and
engineering path runnable, but they are not evidence of real acoustic forced-alignment quality.
See [ARCHITECTURE.md](ARCHITECTURE.md) for that boundary.

## Run locally

The target runtime is Python 3.12 and Node 22.

```powershell
cd speechmate
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python -m pytest -q
.venv\Scripts\python -m uvicorn backend.main:app --reload
```

In another terminal:

```powershell
cd speechmate\frontend
npm.cmd install
npm.cmd run dev
```

Open `http://localhost:5173`. The default `deterministic` provider uses the “Offline demo
transcript” as known model output. Change `really` to `leally` or `red` to `led` to exercise the
alignment and learner-state path.

For local model inference:

```powershell
cd speechmate
.venv\Scripts\python -m pip install -e ".[speech]"
$env:ASR_PROVIDER = "faster-whisper"
.venv\Scripts\python -m uvicorn backend.main:app --reload
```

Or run PostgreSQL, the API, and the frontend together:

```powershell
docker compose up --build
```

## One recording through the system

1. The browser captures audio and sends it with the target phrase.
2. `inspect_audio` enforces payload limits and reads WAV metadata when present.
3. the configured `ASRAdapter` transcribes commodity model output.
4. `PhonemeAdapter` creates comparable expected and observed phoneme sequences.
5. `align_phonemes` uses global dynamic programming to label matches, substitutions, omissions,
   and insertions.
6. `score_alignment` converts confident evidence into explainable observations and retains weak
   evidence as uncertain.
7. `PracticeRepository` writes the immutable attempt and its normalized observations.
8. `build_learner_profile` recomputes recurring weaknesses across all of the learner’s sessions.
9. The API returns immediate feedback and a targeted deterministic practice recommendation.

## Model inference vs. our engineering

**Model inference:** audio decoding/transcription in Faster Whisper; a future acoustic forced
aligner; a future full-vocabulary G2P model.

**Engineering implemented here:** request validation, adapter contracts, phoneme normalization,
sequence alignment, confidence policy, error classification, database schema, cross-session
aggregation, practice selection, labeled metrics, and the consumer workflow.

## Read the code in dependency order

1. `speech/types.py` — values passed between stages.
2. `speech/asr.py` and `speech/phonemes.py` — replaceable model boundaries.
3. `speech/alignment.py` — the central dynamic-programming algorithm.
4. `speech/scoring.py` — interprets aligned units conservatively.
5. `models/learner.py` — turns sessions into personalized state.
6. `speech/pipeline.py` — one-attempt orchestration.
7. `backend/database.py` and `backend/main.py` — persistence and HTTP composition.
8. `evaluation/metrics.py` and `tests/` — proof and failure contracts.
9. `frontend/src/App.tsx` — the user journey.

## Current evidence boundary

The deterministic tests validate control flow, alignment, scoring, state aggregation, and metric
math. They do **not** validate microphone quality, Whisper accuracy, phoneme recognition, forced
alignment, model latency, or pronunciation-detection accuracy on real recordings. Record those
results in [RESULTS.md](RESULTS.md) only after running a consented labeled audio set.
