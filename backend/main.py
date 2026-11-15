import io
import json
import os
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pypdf import PdfReader
from docx import Document
from sqlalchemy import create_engine, text
from backend.matching import rank

app = FastAPI(title='Resume Match API', version='1.0.0')
engine = create_engine(os.getenv('DATABASE_URL', 'sqlite:///./rankings.db'))
with engine.begin() as conn:
    conn.execute(text('CREATE TABLE IF NOT EXISTS runs (id VARCHAR(36) PRIMARY KEY, created_at TEXT NOT NULL, payload TEXT NOT NULL)'))
MAX_BYTES = 5 * 1024 * 1024

async def parse(file):
    data = await file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError('File exceeds 5 MB limit')
    suffix = Path(file.filename or '').suffix.lower()
    if suffix == '.pdf':
        reader = PdfReader(io.BytesIO(data))
        if len(reader.pages) > 50:
            raise ValueError('PDF exceeds 50 pages')
        content = '\n'.join(page.extract_text() or '' for page in reader.pages)
    elif suffix == '.docx':
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            if sum(i.file_size for i in archive.infolist()) > 20 * 1024 * 1024:
                raise ValueError('Expanded DOCX exceeds 20 MB')
        doc = Document(io.BytesIO(data))
        content = '\n'.join([p.text for p in doc.paragraphs] + [' '.join(c.text for c in row.cells) for t in doc.tables for row in t.rows])
    elif suffix == '.txt':
        content = data.decode('utf-8')
    else:
        raise ValueError('Use PDF, DOCX or TXT files')
    if len(content.strip()) < 30:
        raise ValueError('No readable text. Scanned PDFs need OCR before upload.')
    return content[:100000]

@app.get('/api/health')
def health():
    return {'status': 'ok', 'model': os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')}

@app.post('/api/match')
async def match(jd: str = Form(''), resumes: list[UploadFile] = File(...), jd_file: UploadFile | None = File(None)):
    if not 1 <= len(resumes) <= 50:
        raise HTTPException(400, 'Upload between 1 and 50 resumes per batch.')
    if jd_file and jd_file.filename:
        try:
            jd = await parse(jd_file)
        except Exception as exc:
            raise HTTPException(400, f'Job description: {exc}')
    if len(jd.strip()) < 30 or len(jd) > 100000:
        raise HTTPException(400, 'Provide a job description between 30 and 100,000 characters.')
    candidates, errors = [], []
    for file in resumes:
        try:
            candidates.append({'filename': file.filename, 'text': await parse(file)})
        except Exception as exc:
            errors.append({'filename': file.filename, 'error': str(exc)[:200]})
    if not candidates:
        raise HTTPException(400, {'message': 'No readable resumes', 'files': errors})
    # CPU model inference runs off the event loop.
    from starlette.concurrency import run_in_threadpool
    try:
        requirements, results = await run_in_threadpool(rank, jd, candidates)
    except Exception:
        raise HTTPException(503, 'Semantic model unavailable. Pre-download the model as described in README; retry when ready.')
    result = {'id': str(uuid4()), 'created_at': datetime.now(timezone.utc).isoformat(), 'requirements': requirements, 'candidates': results, 'errors': errors}
    with engine.begin() as conn:
        conn.execute(text('INSERT INTO runs (id, created_at, payload) VALUES (:id, :created_at, :payload)'), {**{k: result[k] for k in ('id','created_at')}, 'payload': json.dumps(result)})
    return result

@app.get('/api/runs')
def runs():
    with engine.connect() as conn:
        return [dict(row._mapping) for row in conn.execute(text('SELECT id, created_at FROM runs ORDER BY created_at DESC LIMIT 20'))]

@app.get('/api/runs/{run_id}')
def get_run(run_id: str):
    with engine.connect() as conn:
        payload = conn.execute(text('SELECT payload FROM runs WHERE id=:id'), {'id': run_id}).scalar()
    if not payload:
        raise HTTPException(404, 'Run not found')
    return json.loads(payload)

@app.delete('/api/runs/{run_id}')
def delete_run(run_id: str):
    with engine.begin() as conn:
        conn.execute(text('DELETE FROM runs WHERE id=:id'), {'id': run_id})
    return {'deleted': True}

static = Path(__file__).resolve().parents[1] / 'frontend' / 'dist'
if static.exists():
    app.mount('/', StaticFiles(directory=static, html=True), name='frontend')
