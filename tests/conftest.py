"""Keep API regression tests isolated from the configured development database."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from backend import database
from backend.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    engine = create_engine(f'sqlite:///{(tmp_path / "test.db").as_posix()}')
    monkeypatch.setattr(database, 'engine', engine)
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        engine.dispose()
