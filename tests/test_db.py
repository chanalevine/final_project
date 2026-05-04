from core.db import get_connection


def test_get_connection(monkeypatch, mock_conn):
    monkeypatch.setattr("sqlite3.connect", lambda *args, **kwargs: mock_conn)

    conn = get_connection()
    assert conn is mock_conn
