"""Persistence for completed matching runs. Raw uploads are never stored."""

import json

from sqlalchemy import create_engine, text

from backend.config import database_url

url = database_url()
connect_args = {'connect_timeout': 10} if url.get_backend_name() == 'postgresql' else {}
engine = create_engine(url, pool_pre_ping=True, pool_recycle=300, connect_args=connect_args)


def initialize_database() -> None:
    with engine.begin() as connection:
        connection.execute(
            text("""
            CREATE TABLE IF NOT EXISTS runs (
                id VARCHAR(36) PRIMARY KEY,
                created_at TEXT NOT NULL,
                payload TEXT NOT NULL
            )
        """)
        )


def save_run(run: dict) -> None:
    with engine.begin() as connection:
        connection.execute(
            text('INSERT INTO runs (id, created_at, payload) VALUES (:id, :created_at, :payload)'),
            {
                'id': run['id'],
                'created_at': run['created_at'],
                'payload': json.dumps(run),
            },
        )


def list_runs() -> list[dict]:
    with engine.connect() as connection:
        rows = connection.execute(
            text('SELECT id, created_at FROM runs ORDER BY created_at DESC LIMIT 20')
        )
        return [dict(row._mapping) for row in rows]


def get_run(run_id: str) -> dict | None:
    with engine.connect() as connection:
        payload = connection.execute(
            text('SELECT payload FROM runs WHERE id=:id'), {'id': run_id}
        ).scalar()
    return json.loads(payload) if payload else None


def delete_run(run_id: str) -> None:
    with engine.begin() as connection:
        connection.execute(text('DELETE FROM runs WHERE id=:id'), {'id': run_id})
