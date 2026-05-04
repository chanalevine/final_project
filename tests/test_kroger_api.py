from unittest.mock import MagicMock
import sqlite3
import scraping.kroger_api as ka
# ---------------------------------------------------------
# TEST 1 — get_token() returns token from fake API
# ---------------------------------------------------------

DB_PATH = "database/food_data.db"


def test_get_token(monkeypatch):
    """Make sure get_token pulls the token from JSON."""

    fake_resp = MagicMock()
    fake_resp.json.return_value = {"access_token": "FAKE_TOKEN"}

    monkeypatch.setattr("requests.post", lambda *args, **kwargs: fake_resp)

    token = ka.get_token()

    assert token == "FAKE_TOKEN"


# ---------------------------------------------------------
# TEST 2 — kroger_search() parses product correctly
# ---------------------------------------------------------
def test_kroger_search_basic(monkeypatch):
    """Test that kroger_search extracts title, price, and size."""

    fake_json = {
        "data": [
            {
                "description": "Test Ingredient",
                "items": [
                    {
                        "price": {"regular": 3.99},
                        "size": "16 oz"
                    }
                ]
            }
        ]
    }

    fake_resp = MagicMock()
    fake_resp.json.return_value = fake_json

    monkeypatch.setattr("requests.get", lambda *args, **kwargs: fake_resp)

    title, price, size = ka.kroger_search("sugar", "FAKE_TOKEN")

    assert title == "Test Ingredient"
    assert price == 3.99
    assert size == "16 oz"


# ---------------------------------------------------------
# TEST 3 — kroger_search() handles missing data
# ---------------------------------------------------------
def test_kroger_search_no_results(monkeypatch):
    """If Kroger returns empty data list, return Nones."""

    fake_resp = MagicMock()
    fake_resp.json.return_value = {"data": []}

    monkeypatch.setattr("requests.get", lambda *args, **kwargs: fake_resp)

    title, price, size = ka.kroger_search("unknown", "FAKE_TOKEN")

    assert title is None
    assert price is None
    assert size is None


# ---------------------------------------------------------
# TEST 4 — update_all_ingredients() updates DB rows
# ---------------------------------------------------------
def test_update_all_ingredients(monkeypatch, tmp_path):
    """Test the full update loop with a fake DB + fake API."""

    # create temp DB
    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()

    # create ingredients table
    cur.execute("""
        CREATE TABLE ingredients (
            id INTEGER PRIMARY KEY,
            name TEXT,
            price REAL,
            price_unit TEXT,
            package_size TEXT
        )
    """)

    # insert fake ingredients
    cur.execute("INSERT INTO ingredients VALUES (1, 'Sugar', NULL, NULL, NULL)")
    cur.execute("INSERT INTO ingredients VALUES (2, 'Milk', NULL, NULL, NULL)")
    conn.commit()
    conn.close()

    # patch DB_PATH
    monkeypatch.setattr(ka, "DB_PATH", str(db_file))

    # fake token
    monkeypatch.setattr(ka, "get_token", lambda: "FAKE_TOKEN")

    # fake Kroger API response
    def fake_search(name, token):
        return f"{name} title", 2.50, "12 oz"

    monkeypatch.setattr(ka, "kroger_search", fake_search)

    # run update
    ka.update_all_ingredients()

    # verify DB updated
    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("SELECT name, price, package_size FROM ingredients ORDER BY id")
    rows = cur.fetchall()

    assert rows == [
        ("Sugar", 2.50, "12 oz"),
        ("Milk", 2.50, "12 oz")
    ]

    conn.close()
