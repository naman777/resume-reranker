"""HTTP endpoints for matching resumes and managing saved runs."""

import logging
import os
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

from backend import database
from backend.matching import rank
from backend.parsing import MAX_TEXT_CHARACTERS, MIN_TEXT_CHARACTERS, parse_upload
from backend.scoring import SCORING_VERSION

router = APIRouter(prefix='/api')
logger = logging.getLogger(__name__)
MAX_RESUMES = 50


@router.get('/health')
def health():
    return {
        'status': 'ok',
        'model': os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2'),
    }


@router.post('/match')
async def match(
    jd: str = Form(''),
    resumes: list[UploadFile] = File(...),
    jd_file: UploadFile | None = File(None),
):
    if not 1 <= len(resumes) <= MAX_RESUMES:
        raise HTTPException(400, 'Upload between 1 and 50 resumes per batch.')

    if jd_file and jd_file.filename:
        try:
            jd = await parse_upload(jd_file)
        except Exception as error:
            raise HTTPException(400, f'Job description: {error}') from error

    if len(jd.strip()) < MIN_TEXT_CHARACTERS or len(jd) > MAX_TEXT_CHARACTERS:
        raise HTTPException(400, 'Provide a job description between 30 and 100,000 characters.')

    candidates, errors = [], []
    for file in resumes:
        try:
            candidates.append({'filename': file.filename, 'text': await parse_upload(file)})
        except Exception as error:
            # A corrupt upload should not prevent valid resumes from being ranked.
            errors.append({'filename': file.filename, 'error': str(error)[:200]})

    if not candidates:
        raise HTTPException(400, {'message': 'No readable resumes', 'files': errors})

    try:
        # CPU inference must not block the async request loop.
        requirements, results = await run_in_threadpool(rank, jd, candidates)
    except Exception as error:
        logger.exception('Resume matching failed')
        raise HTTPException(
            503,
            'Semantic model unavailable. Pre-download the model as described in README; retry when ready.',
        ) from error

    run = {
        'id': str(uuid4()),
        'created_at': datetime.now(timezone.utc).isoformat(),
        'requirements': requirements,
        'candidates': results,
        'errors': errors,
        'scoring_version': SCORING_VERSION,
    }
    database.save_run(run)
    return run


@router.get('/runs')
def list_runs():
    return database.list_runs()


@router.get('/runs/{run_id}')
def get_run(run_id: str):
    run = database.get_run(run_id)
    if run is None:
        raise HTTPException(404, 'Run not found')
    return run


@router.delete('/runs/{run_id}')
def delete_run(run_id: str):
    database.delete_run(run_id)
    return {'deleted': True}
