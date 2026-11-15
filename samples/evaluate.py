"""Evaluate field extraction on the ten fictional fixtures and generated documents."""

import asyncio
import io
import json
from pathlib import Path

from fastapi import UploadFile

from backend.extraction import extract
from backend.parsing import parse_upload

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT.parent / 'frontend/src/data/candidates.json'


async def evaluate() -> dict:
    fields = ('name', 'experience', 'skills', 'qualifications')
    report = {kind: {field: 0 for field in fields} for kind in ('text', 'pdf', 'docx')}
    failures = []
    fixtures = json.loads(FIXTURES.read_text())
    for fixture in fixtures:
        for kind in report:
            text = fixture['text']
            if kind != 'text':
                path = ROOT / f'{fixture["id"]}.{kind}'
                upload = UploadFile(filename=path.name, file=io.BytesIO(path.read_bytes()))
                text = await parse_upload(upload)
            actual = extract(text, fixture['id'])
            for field in fields:
                expected = fixture['expected'][field]
                value = actual[field]
                correct = (
                    sorted(value) == sorted(expected)
                    if isinstance(expected, list)
                    else value == expected
                )
                report[kind][field] += int(correct)
                if not correct:
                    failures.append({'candidate': fixture['id'], 'format': kind, 'field': field})
    return {
        'candidates_per_format': len(fixtures),
        'correct_fields': report,
        'failures': failures,
        'limitation': 'Small synthetic regression set, not an independent accuracy benchmark.',
    }


if __name__ == '__main__':
    result = asyncio.run(evaluate())
    print(json.dumps(result, indent=2))
    raise SystemExit(bool(result['failures']))
