import io
from pathlib import Path
from unittest.mock import patch

from docx import Document

from backend.extraction import extract
from backend.matching import rank


def test_skill_boundaries_and_aliases():
    info = extract('Candidate\nJavaScript PostgreSQL RESTful APIs 3+ years experience')
    assert 'Java' not in info['skills']
    assert {'JavaScript', 'SQL', 'PostgreSQL', 'REST APIs'} <= set(info['skills'])
    assert info['experience'] == 3


def test_score_explanation_and_missing_experience():
    jd = 'Python React developer with 4 years experience'
    _, results = rank(
        jd,
        [
            {'filename': 'a.txt', 'text': 'Alice\nPython React 4 years experience'},
            {'filename': 'b.txt', 'text': 'Bob\nJava'},
        ],
        lambda j, t: [0.8, 0.2],
    )
    assert results[0]['score'] == 91
    assert results[1]['missing_skills'] == ['Python', 'React']
    assert results[1]['breakdown']['experience']['score'] == 0
    assert abs(sum(x['weight'] for x in results[0]['breakdown'].values()) - 1) < 1e-5


def test_batch_docx_partial_failure_and_saved_run(client):
    doc = Document()
    doc.add_paragraph('Synthetic Candidate')
    doc.add_paragraph('Python React FastAPI 4 years of experience building reliable systems')
    buf = io.BytesIO()
    doc.save(buf)
    with patch('backend.matching.semantic_scores', return_value=[0.8] * 10):
        response = client.post(
            '/api/match',
            data={'jd': 'Python React developer with 3 years experience building web systems'},
            files=[('resumes', (f'candidate-{i}.docx', buf.getvalue())) for i in range(10)]
            + [('resumes', ('bad.pdf', b'invalid'))],
        )
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body['candidates']) == 10 and len(body['errors']) == 1
    assert client.get('/api/runs/' + body['id']).json() == body
    client.delete('/api/runs/' + body['id'])
    assert client.get('/api/runs/' + body['id']).status_code == 404


def test_unrecognized_requirements_use_only_semantic_similarity():
    _, candidates = rank(
        'Build reliable distributed services',
        [{'filename': 'sample.txt', 'text': 'Synthetic Candidate\nBuilt reliable services'}],
        lambda jd, texts: [0.8],
    )
    assert candidates[0]['score'] == 80
    assert set(candidates[0]['breakdown']) == {'semantic'}
    assert candidates[0]['breakdown']['semantic']['weight'] == 1


def test_mixed_pdf_docx_batch(client):
    sample_directory = Path(__file__).resolve().parents[1] / 'samples'
    paths = sorted(sample_directory.glob('*.pdf'))[:5]
    paths += sorted(sample_directory.glob('*.docx'))[:5]
    assert len(paths) == 10

    with patch('backend.matching.semantic_scores', return_value=[0.8] * 10):
        response = client.post(
            '/api/match',
            data={'jd': 'Python React developer with 3 years experience building web systems'},
            files=[('resumes', (path.name, path.read_bytes())) for path in paths],
        )

    assert response.status_code == 200, response.text
    run = response.json()
    try:
        assert len(run['candidates']) == 10
        assert not run['errors']
        assert all(
            candidate['name'].startswith('Synthetic Candidate') for candidate in run['candidates']
        )
    finally:
        client.delete('/api/runs/' + run['id'])
