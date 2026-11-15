import io
from unittest.mock import patch
from fastapi.testclient import TestClient
from docx import Document
from backend.main import app
from backend.matching import extract, rank


def test_skill_boundaries_and_aliases():
    info = extract('Candidate\nJavaScript PostgreSQL RESTful APIs 3+ years experience')
    assert 'Java' not in info['skills']
    assert {'JavaScript', 'SQL', 'PostgreSQL', 'REST APIs'} <= set(info['skills'])
    assert info['experience'] == 3


def test_score_explanation_and_missing_experience():
    jd = 'Python React developer with 4 years experience'
    _, results = rank(jd, [{'filename': 'a.txt', 'text': 'Alice\nPython React 4 years experience'}, {'filename': 'b.txt', 'text': 'Bob\nJava'}], lambda j, t: [.8, .2])
    assert results[0]['score'] == 91
    assert results[1]['missing_skills'] == ['Python', 'React']
    assert results[1]['breakdown']['experience']['score'] == 0
    assert abs(sum(x['weight'] for x in results[0]['breakdown'].values()) - 1) < 1e-5


def test_batch_docx_partial_failure_and_saved_run():
    doc = Document()
    doc.add_paragraph('Synthetic Candidate')
    doc.add_paragraph('Python React FastAPI 4 years of experience building reliable systems')
    buf = io.BytesIO(); doc.save(buf)
    client = TestClient(app)
    with patch('backend.matching.semantic_scores', return_value=[.8]*10):
        # rank's default is bound at definition; patch the actual encoder boundary instead.
        class Encoder:
            def encode(self, texts, normalize_embeddings=True):
                import numpy as np
                return np.array([[1., 0.]] * len(texts))
        with patch('backend.matching.model', return_value=Encoder()):
            response = client.post('/api/match', data={'jd': 'Python React developer with 3 years experience building web systems'}, files=[('resumes', (f'candidate-{i}.docx', buf.getvalue())) for i in range(10)]+[('resumes', ('bad.pdf', b'invalid'))])
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body['candidates']) == 10 and len(body['errors']) == 1
    assert client.get('/api/runs/'+body['id']).json() == body
    client.delete('/api/runs/'+body['id'])
    assert client.get('/api/runs/'+body['id']).status_code == 404
