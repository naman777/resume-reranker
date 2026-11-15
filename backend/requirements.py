"""Recognize required versus desirable skills and minimum experience in a JD."""

import re

from backend.evidence import passages
from backend.experience import experience_claims
from backend.extraction import extract
from backend.skills import skill_evidence

DESIRABLE = re.compile(
    r'\b(?:nice[- ]to[- ]have|desirable|preferred|optional|bonus|a plus|advantage|not required)\b',
    re.I,
)
REQUIRED = re.compile(
    r'(?<!not )\b(?:required|must[- ]have|must|essential|mandatory|minimum)\b', re.I
)


def extract_requirements(text: str) -> dict:
    requirements = extract(text)
    priorities, evidence, required_claims = {}, {}, []
    section = 'required'
    for passage in passages(text):
        content = passage['text']
        optional = DESIRABLE.search(content)
        mandatory = REQUIRED.search(content)
        priority = 'required' if mandatory else ('desirable' if optional else section)
        # Headings set the section default; a prose preference applies to its own sentence.
        if len(content.split()) <= 6 and (content.endswith(':') or not skill_evidence(content)):
            if optional or mandatory:
                section = priority
        clauses = content.split(',') if optional and mandatory else [content]
        for clause in clauses:
            clause_priority = priority
            if optional and mandatory:
                clause_priority = 'desirable' if DESIRABLE.search(clause) else 'required'
            for skill, sources in skill_evidence(clause).items():
                # A required occurrence wins if a skill appears in both sections.
                if priorities.get(skill) != 'required':
                    priorities[skill] = clause_priority
                evidence.setdefault(skill, []).append({**sources[0], 'line': passage['line']})
        if priority == 'required':
            required_claims.extend(experience_claims(content))

    general_claims = [claim for claim in required_claims if not claim['skills']]
    experience = max((claim['years'] for claim in general_claims or required_claims), default=None)
    return {
        **requirements,
        'experience': experience,
        'required_skills': sorted(
            skill for skill, priority in priorities.items() if priority == 'required'
        ),
        'desirable_skills': sorted(
            skill for skill, priority in priorities.items() if priority == 'desirable'
        ),
        'skill_priorities': priorities,
        'skill_evidence': evidence,
        'experience_claims': required_claims,
    }
