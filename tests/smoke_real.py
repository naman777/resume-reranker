"""Manual smoke check using actual PDF/DOCX files and actual embeddings."""
from pathlib import Path
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)
paths = sorted(Path('samples').glob('*.pdf'))[:5] + sorted(Path('samples').glob('*.docx'))[:5]
assert len(paths) == 10
response = client.post('/api/match', data={'jd': 'Full Stack Developer\nSeeking 3 years of experience with Python, FastAPI, React, PostgreSQL, REST APIs, Docker, Git and automated testing. Build reliable backend services and accessible web applications.'}, files=[('resumes', (p.name, p.read_bytes())) for p in paths])
assert response.status_code == 200, response.text
body = response.json()
assert len(body['candidates']) == 10 and not body['errors'], body
assert body['candidates'][0]['score'] >= body['candidates'][-1]['score']
print('Real-model smoke passed: 10 PDF/DOCX resumes; score range', body['candidates'][-1]['score'], body['candidates'][0]['score'])
client.delete('/api/runs/'+body['id'])
