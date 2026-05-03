import pandas as pd

from core.db import get_connection
from core.cost_engine import calculate_recipe_cost


def list_recipes():
    conn = get_connection()
    df = pd.read_sql_query("SELECT id, title FROM recipes ORDER BY id", conn)
    conn.close()

    if df.empty:
        print("No recipes found in the database.")
        return None

    print("\nAvailable recipes:")
    for _, row in df.iterrows():
        print(f"  {row['id']}: {row['title']}")
    return df


def show_recipe_cost(recipe_id: int):
    print(f"\nCalculating cost for recipe id={recipe_id}...\n")
    result = calculate_recipe_cost(recipe_id)

    if not result:
        print("No result returned. Check that the recipe id exists.")
        return

    print(f"Recipe: {result['recipe_name']}")
    print(f"Servings: {result['servings']}")
    print(f"Total cost: ${result['total_cost']}")
    print(f"Cost per serving: ${result['cost_per_serving']}\n")

    print("Breakdown:")
    for item in result["breakdown"]:
        print(
            f"  - {item['ingredient']}: "
            f"qty={item['quantity']}, "
            f"price={item['price']}, "
            f"pkg={item['package_amount']} {item['package_unit']}, "
            f"cost=${item['cost']}"
        )


def main():
    print("=== Recipe Cost Debug CLI ===")

    df = list_recipes()
    if df is None or df.empty:
        print("\nNothing to test yet. Make sure your scraper has populated the recipes table.")
        return

    try:
        raw = input("\nEnter a recipe id to calculate cost (or press Enter for first): ").strip()
    except EOFError:
        raw = ""

    if raw == "":
        recipe_id = int(df["id"].iloc[0])
    else:
        try:
            recipe_id = int(raw)
        except ValueError:
            print("Invalid id.")
            return

    show_recipe_cost(recipe_id)


if __name__ == "__main__":
    main()
    