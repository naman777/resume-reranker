"""Explicit duration claims, separated into general and skill-specific experience."""

import re

from backend.evidence import passages
from backend.skills import skills

DURATION = re.compile(
    r'\b(?P<minimum>\d+(?:\.\d+)?)'
    r'(?:\s*(?:[-–—]|to)\s*(?P<maximum>\d+(?:\.\d+)?))?'
    r'\s*\+?\s*(?P<unit>years?|yrs?|months?|mos?)\b',
    re.I,
)
IRRELEVANT_DURATION = re.compile(
    r'\b(?:degree|course|program|programme|warranty|contract duration|old|ago)\b', re.I
)
EXPERIENCE_CONTEXT = re.compile(
    r'\b(?:experience|experienced|worked|working|built|building|developing|development|'
    r'engineer|developer|professional|career|internship|intern|using|with|in)\b',
    re.I,
)


def experience_claims(text: str) -> list[dict]:
    claims = []
    for passage in passages(text):
        # Separate independent claims so "8 years total; 2 years Python" stays distinct.
        for clause in re.split(r'[,;]|\band\s+(?=\d)', passage['text'], flags=re.I):
            for match in DURATION.finditer(clause):
                context = clause.strip()
                if IRRELEVANT_DURATION.search(context) or not (
                    EXPERIENCE_CONTEXT.search(context) or skills(context)
                ):
                    continue
                if re.search(r'\b(?:no|not|never)\b', context, re.I):
                    continue
                divisor = 12 if match['unit'].lower().startswith('mo') else 1
                minimum = float(match['minimum']) / divisor
                maximum = float(match['maximum']) / divisor if match['maximum'] else None
                if maximum is not None and maximum < minimum:
                    continue
                claims.append(
                    {
                        'years': round(minimum, 2),
                        'maximum_years': round(maximum, 2) if maximum is not None else None,
                        'skills': []
                        if re.search(r'\b(?:total|overall)\b', context, re.I)
                        else skills(context),
                        'line': passage['line'],
                        'text': context,
                    }
                )
    return claims


def experience(text: str) -> float | None:
    claims = experience_claims(text)
    general = [claim for claim in claims if not claim['skills']]
    return max((claim['years'] for claim in general or claims), default=None)


def compare_experience(claims: list[dict], requirements: dict) -> dict:
    """Prefer explicit required-skill claims; never transfer unrelated tenure to a role."""
    required = set(requirements.get('required_skills', requirements['skills']))
    scoped = [claim for claim in claims if claim['skills']]
    relevant = [claim for claim in scoped if required.intersection(claim['skills'])]
    general = [claim for claim in claims if not claim['skills']]
    if relevant:
        selected, basis = relevant, 'relevant_claim'
    elif general:
        selected, basis = general, 'general_claim'
    elif not required:
        selected, basis = scoped, 'general_claim'
    else:
        selected, basis = [], 'unrelated_or_missing'
    return {
        'years': max((claim['years'] for claim in selected), default=None),
        'required_years': requirements['experience'],
        'basis': basis,
        'evidence': selected,
        'limitation': (
            'Explicit claims only; employment dates are not reconstructed or summed. '
            'Skill-specific claims may cover only part of the role requirements.'
        ),
    }
