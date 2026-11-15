"""Load local settings without overriding variables supplied by the environment."""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL, make_url

BACKEND_DIRECTORY = Path(__file__).resolve().parent
load_dotenv(BACKEND_DIRECTORY / '.env')
load_dotenv(BACKEND_DIRECTORY.parent / '.env')


def database_url(value: str | None = None) -> URL:
    """Accept Neon PostgreSQL URLs and explicitly select the installed psycopg driver."""
    url = make_url(
        value if value is not None else os.getenv('DATABASE_URL', 'sqlite:///./rankings.db')
    )
    if url.drivername in {'postgres', 'postgresql'}:
        url = url.set(drivername='postgresql+psycopg')
    return url
