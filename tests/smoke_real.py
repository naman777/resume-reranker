"""Manual smoke check using actual PDF/DOCX files and actual embeddings."""

from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import app


def check_real_matching(client):
    paths = sorted(Path('samples').glob('*.pdf'))[:5] + sorted(Path('samples').glob('*.docx'))[5:]
    assert len(paths) == 10
    response = client.post(
        '/api/match',
        data={
            'jd': 'Full Stack Developer\nRequired skills: Python, FastAPI, React, PostgreSQL, REST APIs and Git.\nMinimum 3 years of professional experience.\nNice to have: Docker, automated testing and NLP.\nBuild reliable backend services and accessible web applications.'
        },
        files=[('resumes', (p.name, p.read_bytes())) for p in paths],
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body['candidates']) == 10 and not body['errors'], body
    candidates = {candidate['name']: candidate for candidate in body['candidates']}
    assert len(candidates) == 10
    assert (
        candidates['Synthetic Candidate 01']['score']
        > candidates['Synthetic Candidate 06']['score']
    )
    assert candidates['Synthetic Candidate 03']['experience_comparison']['years'] == 2
    assert candidates['Synthetic Candidate 06']['experience_comparison']['years'] is None
    assert candidates['Synthetic Candidate 04']['experience'] is None
    assert body['requirements']['desirable_skills'] == ['Docker', 'NLP', 'Testing']
    print(
        'Real-model smoke passed: 10 PDF/DOCX resumes; score range',
        body['candidates'][-1]['score'],
        body['candidates'][0]['score'],
    )
    client.delete('/api/runs/' + body['id'])


if __name__ == '__main__':
    with TestClient(app) as client:
        check_real_matching(client)
