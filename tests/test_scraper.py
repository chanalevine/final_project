from unittest.mock import MagicMock
import scraping.kosher_scraper as ks


def test_fetch_page(monkeypatch):
    """Make sure fetch_page sends the right request and parses JSON."""

    # fake JSON response that looks like Typesense
    fake_json = {
        "results": [
            {
                "found": 1,
                "hits": [
                    {"document": {"id": 123, "title": "Fake Recipe"}}
                ]
            }
        ]
    }

    fake_resp = MagicMock()
    fake_resp.json.return_value = fake_json
    fake_resp.raise_for_status.return_value = None

    # patch requests.post
    monkeypatch.setattr("requests.post", lambda *args, **kwargs: fake_resp)

    result = ks.fetch_page(1)

    assert result["found"] == 1
    assert result["hits"][0]["document"]["title"] == "Fake Recipe"
