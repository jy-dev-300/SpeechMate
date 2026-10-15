# SpeechMate architecture

## System shape

```text
React recorder
  -> FastAPI request validation
  -> audio inspection
  -> ASR adapter                       MODEL INFERENCE
  -> expected + observed phonemization MODEL INFERENCE / DATA ADAPTER
  -> phoneme sequence alignment        ENGINEERING LOGIC
  -> issue scoring + uncertainty       ENGINEERING LOGIC
  -> session + observations            PERSISTENCE
  -> cross-session learner profile     ENGINEERING LOGIC
  -> targeted practice                 PRODUCT POLICY
```

Model outputs are treated as evidence, not truth. Provider confidence is carried into aligned
units; low-confidence mismatches become `uncertain` instead of negative learner feedback.

## Audio representation and preprocessing

The HTTP contract transports audio as base64 because it keeps the first API dependency-light and
works with browser `MediaRecorder` blobs. `speech/preprocessing.py` rejects empty or oversized
payloads before inference. It reads duration and sample rate from PCM WAV headers and otherwise
preserves the compressed bytes for the ASR provider’s decoder.

A production upload path should add content-type validation, object storage, retention controls,
malware scanning, and a server-side duration limit decoded from compressed media. Raw voice data
should not be retained unless the learner explicitly opts in.

## ASR

`ASRAdapter` prevents provider details from leaking into scoring. `DeterministicASR` makes known
fixtures runnable offline. `FasterWhisperASR` is the real local inference option and deliberately
lives behind an optional dependency. Whisper’s language probability is propagated as limited
uncertainty evidence; it is not described as calibrated word accuracy.

## Phoneme generation

The expected phrase and transcript need a common symbolic representation. The built-in adapter
uses a small ARPAbet-like lexicon plus a letter fallback so the entire path is inspectable. That
fallback is scaffolding, not a linguistically valid full-vocabulary G2P system. A deployable model
should replace it with CMUdict plus a G2P fallback and preserve word/phoneme boundaries.

## Forced alignment and timing

True forced alignment grounds expected phonemes in acoustic frames. This repository defines the
downstream timed `Phoneme` contract but does not pretend transcript-derived phonemes are acoustic
observations. When only recording duration is known, `add_uniform_timing` creates low-confidence UI
segments. That approximation must not be used to claim pronunciation accuracy.

The next model adapter should integrate Montreal Forced Aligner, WhisperX, or a pronunciation-
assessment API and emit per-phoneme timestamps and confidence. The alignment and scoring modules do
not need to change when that adapter is added.

## Alignment

`align_phonemes` builds a Levenshtein cost matrix over expected and observed symbols, then
backtracks to produce comparable `AlignedUnit` values. A diagonal substitution is preferred on
ties so one acoustic event is not inflated into an omission plus an insertion. Complexity is
`O(expected × observed)` in time and memory, acceptable for short v1 practice phrases.

## Scoring and uncertainty

Scoring is deterministic and reviewable:

- low confidence → uncertain;
- diagonal mismatch → substitution;
- expected-only unit → omission;
- observed-only unit → insertion;
- confident match with implausible duration → timing issue;
- otherwise → no negative feedback.

Thresholds live in `ScoringPolicy`, making them measurable configuration rather than hidden
constants. They require calibration on labeled recordings before production use.

## Persistent learner state

Every attempt is immutable. Expected phonemes count as opportunities; confident observations count
as error evidence. The profile uses a Beta(1,1)-smoothed rate and requires recurrence across at
least three sessions, three distinct words, four errors, adequate posterior rate, and confidence
before labeling a weakness persistent. This prevents one unusual recording from defining the
learner.

The profile is currently rebuilt from history for clarity. Once data volume makes that slow, an
incremental summary table can be added with idempotent event processing and periodic reconciliation.

## Persistence

SQLAlchemy maps sessions and observations to SQLite locally or PostgreSQL in Compose. Observations
are normalized because cross-session questions are phoneme-centric. Expected symbols remain a JSON
array on the session because their ordering matters and they are read as one sequence.

## Evaluation

`evaluation/metrics.py` computes precision, recall, emitted-feedback false-positive rate, exact
case accuracy, and repeated-recording consistency from explicit labels. Tests verify the metric
math separately from the detector. Real evaluation requires human-reviewed audio labels, fixed
dataset splits, provider/version metadata, and confidence intervals.

## Failure modes to monitor

- ASR “corrects” a learner’s pronunciation and hides a real acoustic mismatch.
- transcript error is incorrectly presented as pronunciation feedback.
- G2P chooses the wrong pronunciation for a heteronym.
- background noise lowers confidence unevenly across accents or devices.
- edit-distance tie-breaking shifts errors to adjacent phonemes.
- repeated phrases create apparent persistence without word diversity.
- uniform timing appears more precise in the UI than the evidence supports.
