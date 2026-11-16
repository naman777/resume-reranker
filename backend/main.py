"""Application setup. Request handling lives in routes; storage in database."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.database import initialize_database
from backend.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    if os.getenv('PRELOAD_MODEL') == '1':
        from backend.semantic import model

        model()
    yield


app = FastAPI(title='Resume Match API', version='1.0.0', lifespan=lifespan)
app.include_router(router)

frontend_build = Path(__file__).resolve().parents[1] / 'frontend' / 'dist'
if frontend_build.exists():
    app.mount('/', StaticFiles(directory=frontend_build, html=True), name='frontend')
