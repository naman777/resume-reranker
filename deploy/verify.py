"""Verify the public deployment with synthetic data; delete only the test run."""

import argparse
import re
from pathlib import Path
from time import monotonic

import httpx

ROOT = Path(__file__).resolve().parents[1]
JOB_DESCRIPTION = """Full Stack Developer
Required skills: Python, FastAPI, React, PostgreSQL, REST APIs and Git.
Minimum 3 years of professional experience.
Nice to have: Docker, automated testing and NLP.
Build reliable backend services and accessible web applications."""


def verify(base_url: str) -> None:
    with httpx.Client(base_url=base_url, timeout=180, follow_redirects=True) as client:
        page = client.get('/')
        page.raise_for_status()
        assert 'Shortlist' in page.text
        assets = re.findall(r'(?:src|href)="(/assets/[^\"]+)"', page.text)
        assert assets
        for path in assets:
            client.get(path).raise_for_status()
        health = client.get('/api/health')
        health.raise_for_status()
        assert health.json()['status'] == 'ok'
        print('HTTPS frontend, assets and API health passed.')

        paths = sorted((ROOT / 'samples').glob('*.pdf'))[:5]
        paths += sorted((ROOT / 'samples').glob('*.docx'))[5:]
        assert len(paths) == 10
        started = monotonic()
        response = client.post(
            '/api/match',
            data={'jd': JOB_DESCRIPTION},
            files=[('resumes', (path.name, path.read_bytes())) for path in paths]
            + [('resumes', ('invalid.pdf', b'not a PDF'))],
        )
        response.raise_for_status()
        run = response.json()
        try:
            candidates = {candidate['name']: candidate for candidate in run['candidates']}
            assert len(candidates) == 10
            assert len(run['errors']) == 1
            assert run['scoring_version'] == '2.0'
            assert all(0 <= candidate['score'] <= 100 for candidate in candidates.values())
            assert (
                candidates['Synthetic Candidate 01']['score']
                > candidates['Synthetic Candidate 06']['score']
            )
            assert candidates['Synthetic Candidate 03']['experience_comparison']['years'] == 2
            assert candidates['Synthetic Candidate 04']['experience'] is None
            assert candidates['Synthetic Candidate 06']['experience_comparison']['years'] is None
            restored = client.get('/api/runs/' + run['id'])
            restored.raise_for_status()
            assert restored.json() == run
            print(
                f'Ten mixed PDF/DOCX resumes matched with real embeddings in {monotonic() - started:.1f}s.'
            )
            print('Score explanations, partial upload failure and database persistence passed.')
        finally:
            client.delete('/api/runs/' + run['id']).raise_for_status()
        assert client.get('/api/runs/' + run['id']).status_code == 404
        print('Synthetic verification run deleted; existing saved runs preserved.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('url', nargs='?', default='https://resume-reranker.namankundra.com')
    verify(parser.parse_args().url)
