import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from core.db import get_connection
from core.cost_engine import calculate_recipe_cost
from core.normalizer import normalize_ingredient
from ai.ai_helper import ask_ai_with_history, ask_cheaper_substitution


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

@st.cache_data
def load_data():
    conn = get_connection()

    recipes = pd.read_sql_query("SELECT * FROM recipes", conn)
    ingredients = pd.read_sql_query("SELECT * FROM ingredients", conn)

    try:
        walmart = pd.read_sql_query("SELECT * FROM walmart_products", conn)
    except Exception:
        walmart = pd.DataFrame(columns=[
            "query", "name", "price", "url", "image",
            "package_amount", "package_unit"
        ])

    conn.close()
    return recipes, ingredients, walmart


# ---------------------------------------------------------
# SAVE HELPERS
# ---------------------------------------------------------

def save_recipes(recipes_df):
    conn = get_connection()
    recipes_df.to_sql("recipes", conn, if_exists="replace", index=False)
    conn.close()


def save_ingredients(ingredients_df):
    conn = get_connection()
    ingredients_df.to_sql("ingredients", conn, if_exists="replace", index=False)
    conn.close()


# ---------------------------------------------------------
# MAIN APP
# ---------------------------------------------------------

def main():

    st.set_page_config(page_title="Recipe Cost and Analysis", layout="wide")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "recipes_df" not in st.session_state:
        recipes_df, ingredients_df, walmart_df = load_data()
        st.session_state.recipes_df = recipes_df
        st.session_state.ingredients_df = ingredients_df
        st.session_state.walmart_df = walmart_df

    recipes_df = st.session_state.recipes_df
    ingredients_df = st.session_state.ingredients_df

    st.title("Recipe Cost and Analysis")

    # -----------------------------------------------------
    # SIDEBAR — SELECT RECIPE
    # -----------------------------------------------------

    st.sidebar.header("Recipes")

    recipe_names = recipes_df["title"].sort_values().tolist()
    selected_recipe_name = st.sidebar.selectbox("Select a recipe", recipe_names)

    selected_recipe_row = recipes_df.loc[recipes_df["title"] == selected_recipe_name].iloc[0]
    selected_recipe_id = int(selected_recipe_row["id"])

    # -----------------------------------------------------
    # SIDEBAR — ADD RECIPE
    # -----------------------------------------------------

    st.sidebar.markdown("---")
    st.sidebar.subheader("Add New Recipe")

    new_title = st.sidebar.text_input("Title")
    new_author = st.sidebar.text_input("Author (optional)")
    new_instructions = st.sidebar.text_area("Instructions (optional)")

    if st.sidebar.button("Add recipe"):
        if new_title.strip():
            new_id = int(recipes_df["id"].max()) + 1 if not recipes_df.empty else 1
            new_row = pd.DataFrame([{
                "id": new_id,
                "title": new_title.strip(),
                "author": new_author.strip() if new_author else None,
                "image_url": None,
                "instructions": new_instructions.strip() if new_instructions else None,
                "date": None,
                "url_slug": None,
                "raw_json": None
            }])
            st.session_state.recipes_df = pd.concat([recipes_df, new_row], ignore_index=True)
            save_recipes(st.session_state.recipes_df)
            st.sidebar.success("Recipe added. Refresh to see it.")
        else:
            st.sidebar.error("Please enter a title.")

    # -----------------------------------------------------
    # SIDEBAR — EDIT RECIPE
    # -----------------------------------------------------

    st.sidebar.markdown("---")
    st.sidebar.subheader("Edit Recipe")

    edit_title = st.sidebar.text_input("Edit title", selected_recipe_row["title"])
    edit_author = st.sidebar.text_input("Edit author", selected_recipe_row.get("author", ""))
    edit_instructions = st.sidebar.text_area("Edit instructions", selected_recipe_row.get("instructions", ""))

    if st.sidebar.button("Save changes"):
        idx = recipes_df.index[recipes_df["id"] == selected_recipe_id][0]
        st.session_state.recipes_df.at[idx, "title"] = edit_title
        st.session_state.recipes_df.at[idx, "author"] = edit_author
        st.session_state.recipes_df.at[idx, "instructions"] = edit_instructions
        save_recipes(st.session_state.recipes_df)
        st.sidebar.success("Recipe updated. Refresh to see changes.")

    # -----------------------------------------------------
    # SIDEBAR — DELETE RECIPE
    # -----------------------------------------------------

    st.sidebar.markdown("---")
    st.sidebar.subheader("Delete Recipe")

    if st.sidebar.button("Delete recipe"):
        st.session_state.recipes_df = recipes_df[recipes_df["id"] != selected_recipe_id]
        st.session_state.ingredients_df = ingredients_df[ingredients_df["recipe_id"] != selected_recipe_id]
        save_recipes(st.session_state.recipes_df)
        save_ingredients(st.session_state.ingredients_df)
        st.sidebar.success("Recipe deleted. Refresh to update.")

    # -----------------------------------------------------
    # MAIN LAYOUT
    # -----------------------------------------------------

    col_left, col_right = st.columns([2, 1])

    # -----------------------------------------------------
    # LEFT — INGREDIENTS
    # -----------------------------------------------------

    with col_left:
        st.header(selected_recipe_name)

        recipe_ingredients = ingredients_df[ingredients_df["recipe_id"] == selected_recipe_id]

        st.subheader("Ingredients")

        if recipe_ingredients.empty:
            st.info("No ingredients stored for this recipe.")
        else:
            if "last_cost_result" in st.session_state and st.session_state.last_cost_result:
                breakdown_df = pd.DataFrame(st.session_state.last_cost_result["breakdown"])

                merged = recipe_ingredients.merge(
                    breakdown_df,
                    left_on="ingredient_name",
                    right_on="ingredient",
                    how="left"
                )

                display_df = merged[["ingredient_name", "quantity", "cost"]]
            else:
                display_df = recipe_ingredients[["ingredient_name", "quantity"]]
                display_df["cost"] = None

            st.dataframe(display_df, hide_index=True, use_container_width=True)

        # -------------------------------------------------
        # ADD INGREDIENT
        # -------------------------------------------------

        st.subheader("Add Ingredient")

        ing_name = st.text_input("Ingredient name")
        ing_qty = st.text_input("Quantity (e.g., '2 onions', '3 tbsp')")

        if st.button("Add ingredient"):
            if ing_name.strip() and ing_qty.strip():
                new_ing_id = int(ingredients_df["id"].max()) + 1 if not ingredients_df.empty else 1
                normalized = normalize_ingredient(ing_name.strip())

                new_row = pd.DataFrame([{
                    "id": new_ing_id,
                    "recipe_id": selected_recipe_id,
                    "ingredient_name": ing_name.strip(),
                    "quantity": ing_qty.strip(),
                    "unit": None,
                    "raw_text": None,
                    "normalized_name": normalized
                }])

                st.session_state.ingredients_df = pd.concat(
                    [ingredients_df, new_row], ignore_index=True
                )
                save_ingredients(st.session_state.ingredients_df)
                st.success("Ingredient added. Refresh to see it.")
            else:
                st.error("Please enter both ingredient name and quantity.")

    # -----------------------------------------------------
    # RIGHT — COST CALCULATION
    # -----------------------------------------------------

    with col_right:
        st.subheader("Cost Calculation")

        if st.button("Calculate cost"):
            result = calculate_recipe_cost(selected_recipe_id)
            st.session_state.last_cost_result = result

        result = st.session_state.get("last_cost_result")

        if result:
            st.markdown(f"Total cost: ${result['total_cost']}")
            st.markdown(f"Cost per serving: ${result['cost_per_serving']}")

            servings_slider = st.slider(
                "Adjust servings",
                min_value=1,
                max_value=20,
                value=int(result["servings"])
            )

            scaled_total = round(
                result["total_cost"] * servings_slider / max(result["servings"], 1), 2
            )
            st.markdown(f"Cost for {servings_slider} servings: ${scaled_total}")

            breakdown_df = pd.DataFrame(result["breakdown"])

            st.subheader("Cost Breakdown by Ingredient")
            st.dataframe(
                breakdown_df[
                    ["ingredient", "quantity", "price", "package_amount", "package_unit", "cost"]
                ],
                hide_index=True,
                use_container_width=True
            )

            chart_data = breakdown_df[["ingredient", "cost"]].copy()
            chart_data = chart_data[chart_data["cost"] > 0]

            if chart_data.empty:
                st.info("No cost data available for this recipe.")
            else:
                fig, ax = plt.subplots(figsize=(5, 5))
                ax.pie(
                    chart_data["cost"],
                    labels=chart_data["ingredient"],
                    autopct="%1.1f%%",
                    startangle=90
                )
                ax.axis("equal")
                st.pyplot(fig)

                st.subheader("Highest Cost Ingredient")
                most_expensive = chart_data.loc[chart_data["cost"].idxmax(), "ingredient"]
                st.success(f"The ingredient contributing the most to cost is {most_expensive}")

        # -------------------------------------------------
        # CHEAPER SUBSTITUTION
        # -------------------------------------------------

        st.subheader("Cheaper Substitution Suggestion")

        if result:
            ingredient_options = breakdown_df["ingredient"].tolist()
            selected_ing = st.selectbox("Select an ingredient", ingredient_options)

            if st.button("Suggest cheaper substitution"):
                row = breakdown_df[breakdown_df["ingredient"] == selected_ing].iloc[0]
                reply = ask_cheaper_substitution(row["ingredient"], row["cost"])
                st.write(reply)

    # -----------------------------------------------------
    # CHATBOT
    # -----------------------------------------------------

    st.markdown("---")
    st.subheader("Cooking Questions")

    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"You: {msg['content']}")
        elif msg["role"] == "assistant":
            st.markdown(f"Assistant: {msg['content']}")

    user_input = st.text_input("Ask a cooking question")

    col_a, col_b = st.columns(2)

    with col_a:
        if st.button("Send question"):
            if user_input.strip():
                ask_ai_with_history(st.session_state.chat_history, user_input)
                st.experimental_rerun()

    with col_b:
        if st.button("Clear conversation"):
            st.session_state.chat_history = []
            st.experimental_rerun()


if __name__ == "__main__":
    main()
    