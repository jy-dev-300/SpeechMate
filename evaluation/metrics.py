"""Metrics compare detector output with labels instead of asking an LLM to judge it."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DetectionLabel:
    phoneme: str
    kind: str


@dataclass(frozen=True, slots=True)
class EvaluationCase:
    case_id: str
    expected: frozenset[DetectionLabel]
    predicted: frozenset[DetectionLabel]


@dataclass(frozen=True, slots=True)
class DetectionMetrics:
    precision: float
    recall: float
    false_positive_rate: float
    exact_case_accuracy: float


def calculate_metrics(cases: list[EvaluationCase]) -> DetectionMetrics:
    """Compute micro detection metrics and strict whole-recording agreement."""

    true_positives = false_positives = false_negatives = exact = 0
    for case in cases:
        true_positives += len(case.expected & case.predicted)
        false_positives += len(case.predicted - case.expected)
        false_negatives += len(case.expected - case.predicted)
        exact += case.expected == case.predicted

    precision = _safe_divide(true_positives, true_positives + false_positives)
    recall = _safe_divide(true_positives, true_positives + false_negatives)
    # Without labeled true-negative phoneme positions, FP / all predicted negatives would be
    # misleading. This operational rate answers: how much emitted feedback was spurious?
    false_positive_rate = _safe_divide(false_positives, true_positives + false_positives)
    return DetectionMetrics(
        precision=round(precision, 4),
        recall=round(recall, 4),
        false_positive_rate=round(false_positive_rate, 4),
        exact_case_accuracy=round(_safe_divide(exact, len(cases)), 4),
    )


def consistency_rate(recording_predictions: list[frozenset[DetectionLabel]]) -> float:
    """Measure repeated-recording stability against the modal prediction set."""

    if not recording_predictions:
        return 0.0
    modal = max(set(recording_predictions), key=recording_predictions.count)
    matching = sum(prediction == modal for prediction in recording_predictions)
    return round(matching / len(recording_predictions), 4)


def _safe_divide(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0

