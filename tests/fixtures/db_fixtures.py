import pytest


@pytest.fixture
def mock_conn():
    class FakeConn:
        def cursor(self):
            return self

        def execute(self, *args, **kwargs):
            return self

        def fetchall(self):
            return []

        def close(self):
            pass
    return FakeConn()
