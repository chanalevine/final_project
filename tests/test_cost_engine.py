import pandas as pd
from core.cost_engine import calculate_recipe_cost


def test_calculate_recipe_cost_basic(monkeypatch):
    # Fake DB tables
    recipes = pd.DataFrame([{"id": 1, "title": "Test Recipe"}])
    recipe_ingredients = pd.DataFrame([
        {"id": 1, "recipe_id": 1, "ingredient_id": 10, "quantity": "2 cups"}
    ])
    ingredients = pd.DataFrame([
        {"id": 10, "name": "Sugar", "price": 4.00, "package_size": "1 lb", "price_unit": "lb"}
    ])

    # Patch DB loader
    monkeypatch.setattr(
        "core.cost_engine.load_all_tables",
        lambda: (recipes, recipe_ingredients, ingredients)
    )

    result = calculate_recipe_cost(1)

    assert result["total_cost"] == 4.00
    assert result["cost_per_serving"] > 0
    assert result["breakdown"][0]["ingredient"] == "Sugar"
