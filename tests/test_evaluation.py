from evaluation.metrics import (
    DetectionLabel,
    EvaluationCase,
    calculate_metrics,
    consistency_rate,
)

R_TO_L = DetectionLabel("R", "substitution")


def test_metrics_are_derived_from_explicit_labels() -> None:
    cases = [
        EvaluationCase("hit", frozenset({R_TO_L}), frozenset({R_TO_L})),
        EvaluationCase("false-positive", frozenset(), frozenset({R_TO_L})),
        EvaluationCase("miss", frozenset({R_TO_L}), frozenset()),
    ]

    metrics = calculate_metrics(cases)

    assert metrics.precision == 0.5
    assert metrics.recall == 0.5
    assert metrics.false_positive_rate == 0.5


def test_consistency_uses_the_modal_prediction() -> None:
    predictions = [frozenset({R_TO_L}), frozenset({R_TO_L}), frozenset()]

    assert consistency_rate(predictions) == 0.6667
