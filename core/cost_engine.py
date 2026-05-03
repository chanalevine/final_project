import sqlite3
from core.db import get_connection
from core.normalizer import normalize_ingredient
from core.walmart import get_price_for_ingredient


def estimate_cost(quantity, price, package_amount, package_unit):
    if price is None:
        return 0

    q = str(quantity).lower().strip()

    try:
        first = q.split()[0]
        if "/" in first:
            num = eval(first)
        else:
            num = float(first)
    except Exception:
        num = 1

    if package_amount and package_unit:
        unit = str(package_unit).lower()

        if "oz" in unit:
            unit_price = price / package_amount

            if "tsp" in q:
                return (num * (1/6)) * unit_price

            if "tbsp" in q:
                return (num * 0.5) * unit_price

            if "cup" in q:
                return (num * 8) * unit_price

            if "oz" in q:
                return num * unit_price

        if "lb" in unit or "pound" in unit:
            unit_price = price / package_amount

            if "lb" in q or "pound" in q:
                return num * unit_price

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

    return price


def calculate_recipe_cost(recipe_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT title FROM recipes WHERE id = ?", (recipe_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    recipe_name = row[0]
    servings = 1

    cursor.execute("""
        SELECT id, ingredient_name, quantity, normalized_name
        FROM ingredients
        WHERE recipe_id = ?
    """, (recipe_id,))
    ingredients = cursor.fetchall()

    total_cost = 0
    breakdown = []

    for ing_id, ingredient_name, quantity, normalized in ingredients:

        if not normalized:
            normalized = normalize_ingredient(ingredient_name)
            cursor.execute(
                "UPDATE ingredients SET normalized_name = ? WHERE id = ?",
                (normalized, ing_id)
            )
            conn.commit()

        price, package_amount, package_unit = get_price_for_ingredient(conn, normalized)

        cost = estimate_cost(quantity, price, package_amount, package_unit)
        total_cost += cost

        breakdown.append({
            "ingredient": ingredient_name,
            "normalized": normalized,
            "quantity": quantity,
            "price": price,
            "package_amount": package_amount,
            "package_unit": package_unit,
            "cost": round(cost, 2)
        })

    conn.close()

    return {
        "recipe_name": recipe_name,
        "servings": servings,
        "total_cost": round(total_cost, 2),
        "cost_per_serving": round(total_cost / servings, 2),
        "breakdown": breakdown
    }
