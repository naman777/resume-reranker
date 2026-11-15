"""Extract candidate identity, qualifications, skills and evidence-backed duration claims."""

import re
from pathlib import Path

from backend.experience import experience, experience_claims
from backend.skills import skill_evidence
from backend.taxonomy import QUALIFICATIONS

EMAIL = re.compile(r'[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}')
HEADINGS = re.compile(
    r'^(?:resume|curriculum vitae|cv|profile|summary|contact(?: information)?|'
    r'skills|education|experience|professional summary|'
    r'(?:senior |junior |full stack |backend |frontend |software |web |data )*'
    r'(?:engineer|developer|scientist))$',
    re.I,
)


def candidate_name(text: str, filename: str = '') -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines[:10]:
        labeled = re.match(r'^(?:candidate\s+)?name\s*:\s*(.+)$', line, re.I)
        if labeled:
            return labeled[1][:100]
    for line in lines[:5]:
        if (
            len(line.split()) <= 5
            and not HEADINGS.fullmatch(line)
            and not EMAIL.search(line)
            and not re.search(r'https?://|\d{4,}|[|:@]', line)
            and not re.search(r'\b(?:years?|months?|skills|experience|degree)\b', line, re.I)
        ):
            return line[:100]
    return Path(filename).stem.replace('_', ' ').replace('-', ' ') or 'Unknown candidate'


def extract(text: str, filename: str = '') -> dict:
    evidence = skill_evidence(text)
    return {
        'name': candidate_name(text, filename),
        'email': next(iter(EMAIL.findall(text)), None),
        'experience': experience(text),
        'experience_claims': experience_claims(text),
        'skills': list(evidence),
        'skill_evidence': evidence,
        'qualifications': [
            name for name, pattern in QUALIFICATIONS.items() if re.search(pattern, text, re.I)
        ],
    }


def scoring_text(text: str) -> str:
    name = candidate_name(text)
    lines = [
        line
        for line in text.splitlines()
        if line.strip() != name and not re.match(r'^(?:candidate\s+)?name\s*:', line, re.I)
    ]
    return EMAIL.sub('', '\n'.join(lines))
