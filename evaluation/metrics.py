"""Ranking metrics with expected tie treatment, independent of candidate ID order."""

from itertools import combinations, groupby
from math import isfinite, log2


def ranking_metrics(scores: dict[str, float], grades: dict[str, int], k: int = 5) -> dict:
    if not scores or scores.keys() != grades.keys() or not 1 <= k <= len(scores):
        raise ValueError(
            'Scores and labels must cover the same nonempty candidate set; k must fit.'
        )
    if any(not isfinite(score) for score in scores.values()):
        raise ValueError('Scores must be finite.')
    if any(type(grade) is not int or grade not in range(4) for grade in grades.values()):
        raise ValueError('Grades must be integers from zero through three.')
    ordered = sorted(scores, key=lambda identifier: -scores[identifier])
    dcg, relevant_count, position = 0.0, 0.0, 0
    for _, grouped in groupby(ordered, key=scores.get):
        identifiers = list(grouped)
        included = max(0, min(len(identifiers), k - position))
        mean_gain = sum(2 ** grades[identifier] - 1 for identifier in identifiers) / len(
            identifiers
        )
        mean_relevant = sum(grades[identifier] >= 2 for identifier in identifiers) / len(
            identifiers
        )
        dcg += mean_gain * sum(1 / log2(rank + 2) for rank in range(position, position + included))
        relevant_count += mean_relevant * included
        position += len(identifiers)
    ideal = sorted(grades.values(), reverse=True)[:k]
    ideal_dcg = sum((2**grade - 1) / log2(index + 2) for index, grade in enumerate(ideal))
    agreement, pairs = 0.0, 0
    for left, right in combinations(grades, 2):
        if grades[left] == grades[right]:
            continue
        grade_difference = grades[left] - grades[right]
        score_difference = scores[left] - scores[right]
        agreement += (
            0.5 if score_difference == 0 else float(grade_difference * score_difference > 0)
        )
        pairs += 1
    return {
        f'ndcg_at_{k}': dcg / ideal_dcg if ideal_dcg else 0.0,
        f'precision_at_{k}': relevant_count / k,
        'pairwise_agreement': agreement / pairs if pairs else 1.0,
        'comparable_pairs': pairs,
    }
