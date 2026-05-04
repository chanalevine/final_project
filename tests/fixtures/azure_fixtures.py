import pytest


@pytest.fixture
def mock_azure_response():
    class FakeMsg:
        content = "Mocked Azure response"

    class FakeChoice:
        message = FakeMsg()

    class FakeResponse:
        choices = [FakeChoice()]

    return FakeResponse()
