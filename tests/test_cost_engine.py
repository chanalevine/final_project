from core.cost_engine import calculate_recipe_cost


# ---------------------------------------------------------
# Fake DB cursor + connection to match your real code
# ---------------------------------------------------------
class FakeCursor:
    def __init__(self):
        self.call_index = 0

    def execute(self, query, params=None):
        self.call_index += 1

    def fetchone(self):
        # First fetchone() → recipe title
        if self.call_index == 1:
            return ("Test Recipe",)

        # Later fetchone() calls → no featured ingredient description
        return None

    def fetchall(self):
        # Ingredient rows returned by the JOIN query
        return [
            ("2 cups", 10, "Sugar", 4.00, "lb", "1 lb")
        ]


class FakeConn:
    def cursor(self):
        return FakeCursor()

    def close(self):
        pass


# ---------------------------------------------------------
# TEST: Basic cost calculation
# ---------------------------------------------------------
def test_calculate_recipe_cost_basic(monkeypatch):
    """
    Ensure calculate_recipe_cost() loads recipe + ingredients
    and computes cost correctly using estimate_cost().
    """

    # Patch get_connection() so no real DB is used
    monkeypatch.setattr(
        "core.cost_engine.get_connection",
        lambda: FakeConn()
    )

    result = calculate_recipe_cost(1)

    # Validate structure
    assert result["recipe_name"] == "Test Recipe"
    assert result["total_cost"] > 0
    assert result["cost_per_serving"] == result["total_cost"]

    # Validate breakdown
    breakdown = result["breakdown"]
    assert len(breakdown) == 1
    assert breakdown[0]["ingredient"] == "Sugar"
    assert breakdown[0]["price"] == 4.00

    # Featured ingredient should be None because FakeCursor returns no description
    assert result["featured_ingredient"] is None
    assert result["featured_description"] is None
