# SpeechMate results

This file is a template until real labeled audio evaluation is run. Do not replace `TBD` values
with deterministic-fixture results; offline fixtures prove software behavior, not speech quality.

## Evaluation snapshot

| Measure | Result | Dataset / conditions |
| --- | ---: | --- |
| ASR word error rate | TBD | Provider, model version, microphone/noise slices |
| Pronunciation precision | TBD | Human-reviewed phoneme labels |
| Pronunciation recall | TBD | Human-reviewed phoneme labels |
| Emitted-feedback false-positive rate | TBD | Especially clean/native-like recordings |
| Repeated-recording consistency | TBD | Same speakers and phrases, repeated takes |
| p50 / p95 end-to-end latency | TBD | Hardware and concurrency documented |

## Model comparison

| ASR / aligner | Accuracy | p95 latency | Cost | Notes |
| --- | ---: | ---: | ---: | --- |
| Deterministic fixture | Not applicable | TBD | $0 | Control-flow evidence only |
| Faster Whisper `small.en` | TBD | TBD | Local compute | Run on documented hardware |
| Candidate forced aligner | TBD | TBD | TBD | Must expose phoneme confidence |

## Failure cases

Record the audio conditions, expected label, system output, confidence, root cause, and whether the
failure came from ASR, phonemization, alignment, scoring, or profile aggregation.

## Release decision

Document threshold targets and the go/no-go decision here before exposing corrective feedback to
real learners. False positive feedback should be treated as a product-safety problem, not merely a
metric regression.
