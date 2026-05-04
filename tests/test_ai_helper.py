from unittest.mock import MagicMock
from ai.ai_helper import ask_ai_with_history, ask_cheaper_substitution


def test_chat_history_calls_azure(monkeypatch, mock_azure_response):
    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = mock_azure_response

    monkeypatch.setattr("ai.ai_helper.get_client", lambda: (fake_client, "fake-model"))

    history = []
    reply = ask_ai_with_history(history, "Hello")

    assert "Mocked Azure response" in reply
    assert len(history) == 2  # user + assistant


def test_cheaper_substitution(monkeypatch, mock_azure_response):
    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = mock_azure_response

    monkeypatch.setattr("ai.ai_helper.get_client", lambda: (fake_client, "fake-model"))

    reply = ask_cheaper_substitution("Eggs", 3.50, "Omelette")

    assert "Mocked Azure response" in reply
