# SpeechMate engineering drills

These are explanation and extension prompts for the completed production path—not unfinished
student implementations.

1. Trace one request from `App.tsx` to the learner profile and identify every uncertainty handoff.
2. Swap Faster Whisper for a hosted ASR provider without changing alignment or scoring.
3. Explain why ASR text alone cannot prove a phoneme-level pronunciation error.
4. Add a true forced-alignment adapter and state what evidence validates it.
5. Diagnose an edit-distance error that lands on the phoneme adjacent to the actual mistake.
6. Calibrate `ScoringPolicy` to reduce false positives without destroying recall.
7. Add a known /r/→/l/ confusion report while avoiding accent-based overgeneralization.
8. Make learner-profile updates incremental and idempotent under request retries.
9. Add streaming feedback while preserving a stable final session record.
10. Explain why deterministic fixtures, model evaluation, and device/browser tests prove different
    things.

## Five oral-exam questions

1. Which outputs in this system come from models, and which are deterministic engineering logic?
2. How does global sequence alignment distinguish substitution from insertion plus omission?
3. Why does one /r/ observation not create a persistent weakness?
4. What would you label to measure pronunciation precision and false-positive rate honestly?
5. Where can confidence become miscalibrated, and how does the product avoid overclaiming?
