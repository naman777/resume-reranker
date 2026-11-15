"""Skill recognition with aliases, source evidence and explicit negation handling."""

import re

from backend.evidence import passages
from backend.taxonomy import SKILLS

NEGATION = r'\b(?:no|not|without|lack(?:s|ing)?|never)\b'


def alias_pattern(alias: str) -> str:
    return r'(?<!\w)' + re.escape(alias) + r'(?!\w)'


def is_negated(text: str, start: int, end: int) -> bool:
    """Conservatively reject local claims such as 'no Python experience'."""
    prefix = re.split(r'[,;:]|\bbut\b|\bhowever\b', text[:start], flags=re.I)[-1]
    suffix = text[end:]
    return bool(
        re.search(NEGATION + r'(?:\W+\w+){0,5}\W*$', prefix, re.I)
        or re.match(r'\s+(?:is\s+)?(?:not|never)\s+(?:used|known|supported)', suffix, re.I)
    )


def skill_evidence(text: str) -> dict[str, list[dict]]:
    evidence = {}
    source_passages = passages(text)
    for skill, aliases in SKILLS.items():
        supporting = []
        for passage in source_passages:
            content = passage['text']
            if any(
                not is_negated(content, match.start(), match.end())
                for alias in aliases
                for match in re.finditer(alias_pattern(alias), content, re.I)
            ):
                supporting.append(passage)
        if supporting:
            evidence[skill] = supporting[:3]
    return evidence


def skills(text: str) -> list[str]:
    return list(skill_evidence(text))
