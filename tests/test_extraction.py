import json
from pathlib import Path

import pytest

from backend.experience import experience, experience_claims
from backend.extraction import extract
from backend.matching import rank
from backend.requirements import extract_requirements
from backend.skills import skills

FIXTURES = json.loads(
    (Path(__file__).resolve().parents[1] / 'frontend/src/data/candidates.json').read_text()
)


@pytest.mark.parametrize('fixture', FIXTURES, ids=lambda item: item['id'])
def test_varied_candidate_extraction(fixture):
    result = extract(fixture['text'], fixture['id'] + '.txt')
    for key, expected in fixture['expected'].items():
        actual = result[key]
        assert (
            sorted(actual) == sorted(expected) if isinstance(expected, list) else actual == expected
        )
    for passages in result['skill_evidence'].values():
        for passage in passages:
            assert passage['text'] in fixture['text'].splitlines()[passage['line'] - 1]


@pytest.mark.parametrize(
    ('text', 'expected'),
    [
        ('3-5 years of experience', 3),
        ('3 to 5 years building backend services', 3),
        ('18 months of professional experience', 1.5),
        ('2+ years using Python', 2),
        ('4 year degree; 2 year warranty', None),
        ('Worked from 2020 to 2024', None),
        ('5-3 years experience', None),
    ],
)
def test_duration_ranges_and_non_work_durations(text, expected):
    assert experience(text) == expected


def test_desirable_sections_and_required_occurrence_priority():
    requirements = extract_requirements(
        'Required skills:\nPython and React\nNice to have:\nDocker and NLP\n'
        'Must have Git. Python is also preferred.\nMinimum 3-5 years experience.'
    )
    assert requirements['required_skills'] == ['Git', 'Python', 'React']
    assert requirements['desirable_skills'] == ['Docker', 'NLP']
    assert requirements['experience'] == 3


def test_mixed_priority_sentence_and_optional_experience():
    requirements = extract_requirements(
        'Must have Python and React, Docker preferred.\n'
        '3 years of experience required.\n5 years of experience preferred.'
    )
    assert requirements['required_skills'] == ['Python', 'React']
    assert requirements['desirable_skills'] == ['Docker']
    assert requirements['experience'] == 3


def test_missing_required_skill_costs_more_than_missing_optional_skill():
    _, candidates = rank(
        'Required: Python. Docker is optional.',
        [
            {'filename': 'required.txt', 'text': 'Alex\nPython'},
            {'filename': 'optional.txt', 'text': 'Blair\nDocker'},
        ],
        lambda jd, texts: [0.8, 0.8],
    )
    assert candidates[0]['filename'] == 'required.txt'
    assert candidates[0]['breakdown']['skills']['score'] == 80
    assert candidates[1]['breakdown']['skills']['score'] == 20
    assert candidates[1]['missing_required_skills'] == ['Python']


def test_relevant_claim_overrides_total_and_unrelated_experience():
    _, candidates = rank(
        'Python developer. Minimum 3 years experience.',
        [
            {
                'filename': 'a.txt',
                'text': 'Alex\n8 years total experience\n2 years using Python\n6 years using Java',
            },
            {'filename': 'b.txt', 'text': 'Blair\n8 years of Java experience'},
        ],
        lambda jd, texts: [0.8, 0.8],
    )
    by_name = {candidate['name']: candidate for candidate in candidates}
    assert by_name['Alex']['experience'] == 8
    assert by_name['Alex']['experience_comparison']['years'] == 2
    assert by_name['Alex']['experience_comparison']['basis'] == 'relevant_claim'
    assert by_name['Alex']['breakdown']['experience']['score'] == 66.67
    assert by_name['Blair']['experience_comparison']['years'] is None
    assert by_name['Blair']['breakdown']['experience']['score'] == 0


def test_general_experience_is_explicitly_marked_unverified():
    _, candidates = rank(
        'Python developer with 3 years experience',
        [{'filename': 'a.txt', 'text': 'Alex\nPython\n4 years total experience'}],
        lambda jd, texts: [0.8],
    )
    assert candidates[0]['experience_comparison']['basis'] == 'general_claim'


def test_negated_skill_does_not_count_as_a_match():
    assert 'Python' not in skills('No Python experience, but experienced with React.')
    assert 'React' in skills('No Python experience, but experienced with React.')
    assert 'Java' not in skills('JavaScript developer')


def test_claim_evidence_is_verbatim_and_line_numbered():
    text = 'Alex\n2 years using Python; 3 years using React.'
    for claim in experience_claims(text):
        assert claim['line'] == 2
        assert claim['text'] in text.splitlines()[1]


def test_strongest_minimum_requirement_is_used():
    requirements = extract_requirements(
        '3-5 years experience required. Minimum 4 years experience.'
    )
    assert requirements['experience'] == 4
