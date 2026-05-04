import random
from core.db import get_connection


def estimate_cost(quantity, price, price_unit, package_size):
    """
    Convert recipe quantity into cost using stored DB price info.
    """

    if price is None:
        return 0

    # If quantity is missing, assume recipe uses 10% of the package
    if quantity is None or str(quantity).strip() == "":
        return round(price * 0.10, 2)

    q = str(quantity).lower().strip()

    # Extract numeric amount
    try:
        first = q.split()[0]
        if "/" in first:
            num = eval(first)
        else:
            num = float(first)
    except Exception:
        num = 1

    # Basic fallback rules
    if "onion" in q:
        return num * 0.50

    if "garlic" in q or "clove" in q:
        return num * 0.10

    if "tsp" in q:
        return num * 0.05

    if "tbsp" in q:
        return num * 3 * 0.05

    if "olive oil" in q:
        return num * 0.13

    # If no unit conversion logic applies, return full package price
    return price


def calculate_recipe_cost(recipe_id):
    conn = get_connection()
    cursor = conn.cursor()

    # Get recipe name
    cursor.execute("SELECT title FROM recipes WHERE id = ?", (recipe_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    recipe_name = row[0]
    servings = 1

    # Load recipe ingredients
    cursor.execute("""
        SELECT
            ri.quantity,
            ing.id,
            ing.name,
            ing.price,
            ing.price_unit,
            ing.package_size
        FROM recipe_ingredients ri
        JOIN ingredients ing ON ri.ingredient_id = ing.id
        WHERE ri.recipe_id = ?
    """, (recipe_id,))

    ingredients = cursor.fetchall()

    total_cost = 0
    breakdown = []

    ingredient_ids = []  # for picking a random ingredient later

    for quantity, ing_id, name, price, price_unit, package_size in ingredients:

        ingredient_ids.append(ing_id)

        cost = estimate_cost(quantity, price, price_unit, package_size)
        total_cost += cost

        breakdown.append({
            "ingredient": name,
            "quantity": quantity,
            "price": price,
            "price_unit": price_unit,
            "package_size": package_size,
            "cost": round(cost, 2)
        })

    # ---------------------------------------------------------
    # PICK A RANDOM INGREDIENT WITH A REAL DESCRIPTION
    # ---------------------------------------------------------

    featured_ingredient = None
    featured_description = None

    random.shuffle(ingredient_ids)

    for ing_id in ingredient_ids:
        cursor.execute("""
            SELECT ingredient_name, description
            FROM nutrition
            WHERE ingredient_name = (
                SELECT name FROM ingredients WHERE id = ?
            )
        """, (ing_id,))

        row = cursor.fetchone()
        if row and row[1] and row[1].strip():
            featured_ingredient = row[0]
            featured_description = row[1].strip()
            break

    conn.close()

    return {
        "recipe_name": recipe_name,
        "servings": servings,
        "total_cost": round(total_cost, 2),
        "cost_per_serving": round(total_cost / servings, 2),
        "breakdown": breakdown,
        "featured_ingredient": featured_ingredient,
        "featured_description": featured_description
    }
