import pytest

from backend.config import database_url


@pytest.mark.parametrize('scheme', ['postgres', 'postgresql', 'postgresql+psycopg'])
def test_neon_url_uses_psycopg_and_preserves_credentials_and_tls(scheme):
    url = database_url(
        f'{scheme}://sample:p%40ssword@sample.neon.tech/neondb?sslmode=require&channel_binding=require'
    )
    assert url.drivername == 'postgresql+psycopg'
    assert url.password == 'p@ssword'
    assert url.query == {'sslmode': 'require', 'channel_binding': 'require'}


def test_explicit_environment_setting_takes_precedence(monkeypatch):
    monkeypatch.setenv('DATABASE_URL', 'sqlite:///test.db')
    assert database_url().drivername == 'sqlite'


def test_production_requires_an_explicit_database(monkeypatch):
    monkeypatch.delenv('DATABASE_URL', raising=False)
    monkeypatch.setenv('APP_ENV', 'production')
    with pytest.raises(RuntimeError, match='DATABASE_URL'):
        database_url()
