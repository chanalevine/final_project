import pytest
import pandas as pd


@pytest.fixture
def sample_recipe_tables():
    recipes = pd.DataFrame([{"id": 1, "title": "Test Recipe"}])
    recipe_ingredients = pd.DataFrame([
        {"id": 1, "recipe_id": 1, "ingredient_id": 10, "quantity": "2 cups"}
    ])
    ingredients = pd.DataFrame([
        {"id": 10, "name": "Sugar", "price": 4.00, "package_size": "1 lb", "price_unit": "lb"}
    ])
    return recipes, recipe_ingredients, ingredients
