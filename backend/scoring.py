"""Scoring weights and pure component calculations."""

SCORING_VERSION = '2.0'

SCORE_WEIGHTS = {
    'semantic': 0.45,
    'skills': 0.40,
    'experience': 0.15,
}

DESIRABLE_SKILL_WEIGHT = 0.25


def skill_coverage(matched: list[str], requirements: dict) -> float | None:
    priorities = requirements.get('skill_priorities', {})
    weights = {
        skill: DESIRABLE_SKILL_WEIGHT if priorities.get(skill) == 'desirable' else 1.0
        for skill in requirements['skills']
    }
    return sum(weights[skill] for skill in matched) / sum(weights.values()) if weights else None


def experience_fit(actual: float | None, required: float | None) -> float | None:
    """Missing requirements omit this component; missing candidate claims score zero."""
    if not required:
        return None
    if actual is None:
        return 0.0
    return min(actual / required, 1.0)


def score_breakdown(components: dict[str, float | None]) -> dict:
    """Redistribute weights for unavailable components and expose their contributions."""
    total_weight = sum(
        SCORE_WEIGHTS[name] for name, score in components.items() if score is not None
    )
    return {
        name: {
            'score': round(score * 100, 2),
            'weight': round(SCORE_WEIGHTS[name] / total_weight, 6),
            'contribution': round(score * SCORE_WEIGHTS[name] / total_weight * 100, 2),
        }
        for name, score in components.items()
        if score is not None
    }
