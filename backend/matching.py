"""Combine semantic alignment, skill coverage and experience into explainable scores."""

from collections.abc import Callable

from backend.experience import compare_experience
from backend.extraction import extract
from backend.requirements import extract_requirements
from backend.scoring import SCORING_VERSION, experience_fit, score_breakdown, skill_coverage
from backend.semantic import semantic_scores


def score_candidate(candidate: dict, requirements: dict, similarity: float) -> dict:
    info = extract(candidate['text'], candidate['filename'])
    required_skills = set(requirements['skills'])
    candidate_skills = set(info['skills'])
    matched = sorted(required_skills & candidate_skills)
    missing = sorted(required_skills - candidate_skills)
    comparison = compare_experience(info['experience_claims'], requirements)
    actual_years = comparison['years']
    required_years = requirements['experience']

    breakdown = score_breakdown(
        {
            'semantic': float(similarity),
            'skills': skill_coverage(matched, requirements),
            'experience': experience_fit(actual_years, required_years),
        }
    )
    score = round(sum(component['contribution'] for component in breakdown.values()), 1)
    reasons = [
        f'Matched {len(matched)} of {len(required_skills)} recognized JD skills.',
        f'Semantic similarity: {similarity * 100:.1f}% (text similarity, not probability of success).',
        f'Explicit experience: {actual_years if actual_years is not None else "not found"} years; '
        f'JD: {required_years if required_years else "not specified"}.',
        'Required skills carry four times the weight of desirable skills.',
        {
            'relevant_claim': 'Experience uses explicit claims linked to at least one required skill.',
            'general_claim': 'Experience uses a general claim; role relevance is not verified.',
            'unrelated_or_missing': 'No applicable experience claim was detected; unrelated tenure is not credited.',
        }[comparison['basis']],
    ]
    return {
        **info,
        'filename': candidate['filename'],
        'score': score,
        'matched_skills': matched,
        'missing_skills': missing,
        'required_experience': required_years,
        'experience_comparison': comparison,
        'missing_required_skills': sorted(set(missing) & set(requirements['required_skills'])),
        'missing_desirable_skills': sorted(set(missing) & set(requirements['desirable_skills'])),
        'scoring_version': SCORING_VERSION,
        'breakdown': breakdown,
        'reasons': reasons,
    }


def rank(
    jd: str,
    candidates: list[dict],
    semantic_fn: Callable[[str, list[str]], list[float]] | None = None,
) -> tuple[dict, list[dict]]:
    requirements = extract_requirements(jd)
    similarity_function = semantic_fn or semantic_scores
    similarities = similarity_function(jd, [candidate['text'] for candidate in candidates])
    results = [
        score_candidate(candidate, requirements, similarity)
        for candidate, similarity in zip(candidates, similarities, strict=True)
    ]
    return requirements, sorted(results, key=lambda result: (-result['score'], result['name']))
