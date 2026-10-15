"""Sequence alignment converts two phoneme streams into comparable units."""

from speech.types import AlignedUnit, AlignmentOperation, Phoneme


def align_phonemes(expected: list[Phoneme], observed: list[Phoneme]) -> list[AlignedUnit]:
    """Globally align phonemes with deterministic Levenshtein dynamic programming.

    Each matrix cell stores the cheapest edit path for prefixes of the two sequences. Backtracking
    turns that global decision into units that downstream scoring can interpret independently.
    Substitution wins ties over two separate gaps, which avoids reporting one human sound as both
    an omission and insertion.
    """

    rows, columns = len(expected) + 1, len(observed) + 1
    costs = [[0] * columns for _ in range(rows)]
    for row in range(1, rows):
        costs[row][0] = row
    for column in range(1, columns):
        costs[0][column] = column

    for row in range(1, rows):
        for column in range(1, columns):
            substitution_cost = 0 if expected[row - 1].symbol == observed[column - 1].symbol else 1
            costs[row][column] = min(
                costs[row - 1][column - 1] + substitution_cost,
                costs[row - 1][column] + 1,
                costs[row][column - 1] + 1,
            )

    aligned: list[AlignedUnit] = []
    row, column = len(expected), len(observed)
    while row or column:
        # Prefer the diagonal on equal-cost paths because it preserves a one-to-one acoustic event.
        if row and column:
            same = expected[row - 1].symbol == observed[column - 1].symbol
            diagonal_cost = costs[row - 1][column - 1] + (0 if same else 1)
            if costs[row][column] == diagonal_cost:
                observed_item = observed[column - 1]
                aligned.append(
                    AlignedUnit(
                        expected=expected[row - 1],
                        observed=observed_item,
                        operation=(
                            AlignmentOperation.MATCH
                            if same
                            else AlignmentOperation.SUBSTITUTION
                        ),
                        confidence=observed_item.confidence,
                    )
                )
                row -= 1
                column -= 1
                continue

        if row and costs[row][column] == costs[row - 1][column] + 1:
            aligned.append(
                AlignedUnit(
                    expected=expected[row - 1],
                    observed=None,
                    operation=AlignmentOperation.OMISSION,
                    confidence=0.75,
                )
            )
            row -= 1
        else:
            observed_item = observed[column - 1]
            aligned.append(
                AlignedUnit(
                    expected=None,
                    observed=observed_item,
                    operation=AlignmentOperation.INSERTION,
                    confidence=observed_item.confidence,
                )
            )
            column -= 1

    aligned.reverse()
    return aligned


def add_uniform_timing(phonemes: list[Phoneme], duration_seconds: float | None) -> list[Phoneme]:
    """Create deterministic approximate segments when a true forced aligner is unavailable.

    These timings support UI highlighting, but their confidence is deliberately reduced so they
    cannot be mistaken for acoustic forced-alignment output.
    """

    if not phonemes or duration_seconds is None or duration_seconds <= 0:
        return phonemes
    segment_duration = duration_seconds / len(phonemes)
    return [
        Phoneme(
            symbol=item.symbol,
            word=item.word,
            start_seconds=index * segment_duration,
            end_seconds=(index + 1) * segment_duration,
            confidence=min(item.confidence, 0.6),
        )
        for index, item in enumerate(phonemes)
    ]
