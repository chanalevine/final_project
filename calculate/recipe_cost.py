import sqlite3
from calculate.normalizer import normalize_ingredient
from scraping.walmart_scraper import get_price_for_ingredient

# ---------------------------------------------------------
# SMART QUANTITY → COST CONVERTER (USES PACKAGE SIZE)
# ---------------------------------------------------------

def estimate_cost(quantity, price, package_amount, package_unit):
    """
    Convert recipe quantity into cost contribution.
    Uses real Walmart package size when available.
    """

    if price is None:
        return 0

    q = quantity.lower().strip()

    # Extract numeric amount (handles 1, 2, 0.5, 1/2, etc.)
    try:
        first = q.split()[0]
        if "/" in first:
            num = eval(first)  # safe for simple fractions
        else:
            num = float(first)
    except:
        num = 1

    # -----------------------------------------------------
    # If we have package size → compute unit price
    # -----------------------------------------------------
    if package_amount and package_unit:

        unit = package_unit.lower()

        # Price per ounce
        if "oz" in unit:
            unit_price = price / package_amount

            # tsp → oz
            if "tsp" in q:
                ounces = num * (1/6)  # 1 tsp = 1/6 oz
                return ounces * unit_price

            # tbsp → oz
            if "tbsp" in q:
                ounces = num * 0.5  # 1 tbsp = 0.5 oz
                return ounces * unit_price

            # cup → oz
            if "cup" in q:
                ounces = num * 8
                return ounces * unit_price

            # direct oz
            if "oz" in q:
                return num * unit_price

        # Price per pound
        if "lb" in unit or "pound" in unit:
            unit_price = price / package_amount

            if "lb" in q or "pound" in q:
                return num * unit_price

    # -----------------------------------------------------
    # PRODUCE FALLBACKS (when no package size)
    # -----------------------------------------------------
    if "onion" in q:
        return num * 0.50

    if "garlic" in q or "clove" in q:
        return num * 0.10

    # -----------------------------------------------------
    # SPICE FALLBACKS
    # -----------------------------------------------------
    if "tsp" in q:
        return num * 0.05

    if "tbsp" in q:
        return num * 3 * 0.05

    # -----------------------------------------------------
    # OIL FALLBACK
    # -----------------------------------------------------
    if "olive oil" in q:
        return num * 0.13

    # -----------------------------------------------------
    # FINAL FALLBACK: assume whole price used
    # -----------------------------------------------------
    return price


# ---------------------------------------------------------
# RECIPE COST CALCULATOR
# ---------------------------------------------------------

def calculate_recipe_cost(recipe_id):
    conn = sqlite3.connect("food_data.db")
    cursor = conn.cursor()

    # 1. Load recipe info
    cursor.execute("SELECT name, servings FROM recipes WHERE id = ?", (recipe_id,))
    recipe = cursor.fetchone()

    if not recipe:
        conn.close()
        return None

    recipe_name, servings = recipe

    # 2. Load ingredients
    cursor.execute("""
        SELECT ingredient_name, quantity, normalized_name
        FROM ingredients
        WHERE recipe_id = ?
    """, (recipe_id,))
    ingredients = cursor.fetchall()

    total_cost = 0
    breakdown = []

    # 3. Process each ingredient
    for ingredient_name, quantity, normalized in ingredients:

        # Normalize if missing
        if not normalized:
            normalized = normalize_ingredient(ingredient_name)

        # 4. Get Walmart price + package size
        price, package_amount, package_unit = get_price_for_ingredient(conn, normalized)

        # 5. Convert quantity → cost
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


# ---------------------------------------------------------
# TESTING
# ---------------------------------------------------------

if __name__ == "__main__":
    result = calculate_recipe_cost(1)

    print("Recipe:", result["recipe_name"])
    print("Total Cost:", result["total_cost"])
    print("Cost per Serving:", result["cost_per_serving"])
    print("\nBreakdown:")
    for item in result["breakdown"]:
        print(f"- {item['ingredient']} → ${item['cost']}")