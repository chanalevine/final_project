from unittest.mock import MagicMock
import sqlite3
import scraping.produce_description as pd


# ---------------------------------------------------------
# TEST 1 — get_wikipedia_description() basic success
# ---------------------------------------------------------
def test_get_wikipedia_description_basic(monkeypatch):
    """Make sure we pull the first real paragraph from fake HTML."""

    fake_html = """
    <html>
        <body>
            <p></p>
            <p>(pronunciation stuff)</p>
            <p>This is the real first paragraph about eggs.</p>
            <p>More text...</p>
        </body>
    </html>
    """

    fake_resp = MagicMock()
    fake_resp.status_code = 200
    fake_resp.text = fake_html

    monkeypatch.setattr("requests.get", lambda *args, **kwargs: fake_resp)

    desc = pd.get_wikipedia_description("Egg")

    assert desc == "This is the real first paragraph about eggs."


# ---------------------------------------------------------
# TEST 2 — get_wikipedia_description() handles disambiguation
# ---------------------------------------------------------
def test_get_wikipedia_description_disambiguation(monkeypatch):
    """If page has disambigbox, return None."""

    fake_html = """
    <html>
        <table id="disambigbox"></table>
        <p>This should not be returned.</p>
    </html>
    """

    fake_resp = MagicMock()
    fake_resp.status_code = 200
    fake_resp.text = fake_html

    monkeypatch.setattr("requests.get", lambda *args, **kwargs: fake_resp)

    desc = pd.get_wikipedia_description("Apple")
    assert desc is None


# ---------------------------------------------------------
# TEST 3 — store_description() inserts into DB
# ---------------------------------------------------------
def test_store_description(monkeypatch, tmp_path):
    """Make sure store_description writes to the nutrition table."""

    # create a temporary DB file
    db_file = tmp_path / "test.db"
    monkeypatch.setattr(pd, "DB_PATH", str(db_file))

    # create table manually
    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE nutrition (
            ingredient_name TEXT PRIMARY KEY,
            description TEXT
        )
    """)
    conn.commit()
    conn.close()

    # run function
    pd.store_description("Egg", "Eggs are great.")

    # verify insert
    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("SELECT description FROM nutrition WHERE ingredient_name='Egg'")
    row = cur.fetchone()

    assert row[0] == "Eggs are great."
    conn.close()


# ---------------------------------------------------------
# TEST 4 — update_all_descriptions() pulls missing ingredients
# ---------------------------------------------------------
def test_update_all_descriptions(monkeypatch, tmp_path):
    """Test the full loop but with everything mocked."""

    # create temp DB
    db_file = tmp_path / "test2.db"
    monkeypatch.setattr(pd, "DB_PATH", str(db_file))

    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()

    # create tables
    cur.execute("CREATE TABLE ingredients (name TEXT)")
    cur.execute("CREATE TABLE nutrition (ingredient_name TEXT, description TEXT)")
    conn.commit()

    # insert ingredients
    cur.execute("INSERT INTO ingredients VALUES ('Egg')")
    cur.execute("INSERT INTO ingredients VALUES ('Milk')")
    conn.commit()
    conn.close()

    # mock wikipedia fetch
    monkeypatch.setattr(pd, "get_wikipedia_description", lambda ing: f"{ing} desc")

    # mock sleep so tests run fast
    monkeypatch.setattr(pd.time, "sleep", lambda x: None)

    pd.update_all_descriptions()

    # verify both descriptions inserted
    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("SELECT ingredient_name, description FROM nutrition ORDER BY ingredient_name")
    rows = cur.fetchall()

    assert rows == [
        ("Egg", "Egg desc"),
        ("Milk", "Milk desc")
    ]

    conn.close()
