import streamlit as st
import sqlite3
from normalizer import normalize_ingredient
from walmart_scraper import get_price_for_ingredient
from recipe_cost import calculate_recipe_cost
import streamlit as st
from ai_helper import ask_ai_with_history

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
# ---------------------------------------------------------
# DATABASE CONNECTION
# ---------------------------------------------------------

def get_conn():
    return sqlite3.connect("food_data.db", check_same_thread=False)


# ---------------------------------------------------------
# LOAD RECIPES
# ---------------------------------------------------------

def load_recipes():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM recipes ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return rows


# ---------------------------------------------------------
# LOAD INGREDIENTS FOR A RECIPE
# ---------------------------------------------------------

def load_ingredients(recipe_id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, ingredient_name, quantity, normalized_name
        FROM ingredients
        WHERE recipe_id = ?
    """, (recipe_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows


# ---------------------------------------------------------
# ADD NEW RECIPE
# ---------------------------------------------------------

def add_recipe(name, servings):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO recipes (name, servings) VALUES (?, ?)", (name, servings))
    conn.commit()
    conn.close()


# ---------------------------------------------------------
# ADD INGREDIENT
# ---------------------------------------------------------

def add_ingredient(recipe_id, ingredient_name, quantity):
    normalized = normalize_ingredient(ingredient_name)
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO ingredients (recipe_id, ingredient_name, quantity, normalized_name)
        VALUES (?, ?, ?, ?)
    """, (recipe_id, ingredient_name, quantity, normalized))
    conn.commit()
    conn.close()


# ---------------------------------------------------------
# STREAMLIT UI
# ---------------------------------------------------------

st.set_page_config(page_title="Recipe Cost Calculator", layout="wide")

st.title("🍲 Recipe Cost Calculator")
st.write("Automatically calculates recipe cost using Walmart prices.")

# ---------------------------------------------------------
# SIDEBAR — SELECT OR ADD RECIPE
# ---------------------------------------------------------

st.sidebar.header("📘 Recipes")

recipes = load_recipes()
recipe_names = {name: rid for rid, name in recipes}

selected_recipe_name = st.sidebar.selectbox(
    "Choose a recipe",
    list(recipe_names.keys()) if recipes else ["No recipes yet"]
)

selected_recipe_id = recipe_names.get(selected_recipe_name)

st.sidebar.markdown("---")
st.sidebar.subheader("➕ Add New Recipe")

new_recipe_name = st.sidebar.text_input("Recipe Name")
new_recipe_servings = st.sidebar.number_input("Servings", min_value=1, value=4)

if st.sidebar.button("Add Recipe"):
    if new_recipe_name.strip():
        add_recipe(new_recipe_name.strip(), new_recipe_servings)
        st.sidebar.success("Recipe added! Refresh the page.")
    else:
        st.sidebar.error("Enter a recipe name.")


# ---------------------------------------------------------
# MAIN AREA — SHOW RECIPE COST
# ---------------------------------------------------------

if selected_recipe_id:

    st.header(f"📌 {selected_recipe_name}")

    # Load cost breakdown
    result = calculate_recipe_cost(selected_recipe_id)

    st.subheader("💰 Cost Summary")
    col1, col2 = st.columns(2)
    col1.metric("Total Cost", f"${result['total_cost']}")
    col2.metric("Cost per Serving", f"${result['cost_per_serving']}")

    st.markdown("---")
    st.subheader("🧾 Ingredient Breakdown")

    for item in result["breakdown"]:
        st.write(f"**{item['ingredient']}** — {item['quantity']}")
        st.write(f"- Normalized: `{item['normalized']}`")
        st.write(f"- Walmart Price: ${item['price']}")
        st.write(f"- Package: {item['package_amount']} {item['package_unit']}")
        st.write(f"- Cost Used: **${item['cost']}**")
        st.markdown("---")

    # ---------------------------------------------------------
    # ADD INGREDIENTS
    # ---------------------------------------------------------

    st.subheader("➕ Add Ingredient")

    ing_name = st.text_input("Ingredient Name")
    ing_qty = st.text_input("Quantity (e.g., '2 onions', '3 tbsp', '1 lb')")

    if st.button("Add Ingredient"):
        if ing_name.strip() and ing_qty.strip():
            add_ingredient(selected_recipe_id, ing_name.strip(), ing_qty.strip())
            st.success("Ingredient added! Refresh the page.")
        else:
            st.error("Enter both ingredient name and quantity.")

else:
    st.info("Add a recipe in the sidebar to begin.")