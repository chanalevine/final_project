import sqlite3
import pandas as pd
import streamlit as st
import os

from calculate.recipe_cost import estimate_cost
from ai.ai_helper import ask_ai_with_history, ask_cheaper_substitution

# ---------------------------------------------------------
# DATABASE ACCESS
# ---------------------------------------------------------



def get_connection():
    db_path = os.path.join("database", "food_data.db")
    return sqlite3.connect(db_path)


@st.cache_data
def load_data():
    conn = get_connection()

    recipes = pd.read_sql_query("SELECT * FROM recipes", conn)
    ingredients = pd.read_sql_query("SELECT * FROM ingredients", conn)

    try:
        walmart = pd.read_sql_query("SELECT * FROM walmart_products", conn)
    except Exception:
        walmart = pd.DataFrame(columns=["normalized_name", "price", "package_amount", "package_unit"])

    conn.close()
    return recipes, ingredients, walmart


# ---------------------------------------------------------
# COST CALCULATION USING DATAFRAMES
# ---------------------------------------------------------

def calculate_cost_df(recipe_id, recipes_df, ingredients_df, walmart_df):
    recipe_row = recipes_df.loc[recipes_df["id"] == recipe_id].iloc[0]
    servings = recipe_row.get("servings", 1) or 1

    recipe_ings = ingredients_df[ingredients_df["recipe_id"] == recipe_id]

    breakdown = []
    total = 0.0

    for _, row in recipe_ings.iterrows():
        normalized = row.get("normalized_name")
        quantity = row.get("quantity")
        ingredient_name = row.get("ingredient_name")

        wmatch = walmart_df[walmart_df["normalized_name"] == normalized] if normalized else pd.DataFrame()

        if wmatch.empty:
            price = None
            package_amount = None
            package_unit = None
        else:
            price = float(wmatch["price"].iloc[0])
            package_amount = wmatch["package_amount"].iloc[0]
            package_unit = wmatch["package_unit"].iloc[0]

        cost = estimate_cost(quantity, price, package_amount, package_unit)
        total += cost

        breakdown.append({
            "ingredient": ingredient_name,
            "quantity": quantity,
            "normalized": normalized,
            "price": price,
            "package_amount": package_amount,
            "package_unit": package_unit,
            "cost": round(cost, 2)
        })

    total = round(total, 2)
    cost_per_serving = round(total / servings, 2) if servings else None

    return {
        "recipe_name": recipe_row["name"],
        "servings": servings,
        "total_cost": total,
        "cost_per_serving": cost_per_serving,
        "breakdown": breakdown
    }


# ---------------------------------------------------------
# SAVE BACK TO DATABASE
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
# STREAMLIT APPLICATION
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
    walmart_df = st.session_state.walmart_df

    st.title("Recipe Cost and Analysis")

    # -----------------------------------------------------
    # SIDEBAR: RECIPE SELECTION
    # -----------------------------------------------------

    st.sidebar.header("Recipes")

    recipe_names = recipes_df["name"].sort_values().tolist()
    selected_recipe_name = st.sidebar.selectbox("Select a recipe", recipe_names)

    selected_recipe_row = recipes_df.loc[recipes_df["name"] == selected_recipe_name].iloc[0]
    selected_recipe_id = int(selected_recipe_row["id"])

    st.sidebar.markdown("---")
    st.sidebar.subheader("Add New Recipe")

    new_recipe_name = st.sidebar.text_input("Recipe name")
    new_recipe_servings = st.sidebar.number_input("Servings", min_value=1, value=4)

    if st.sidebar.button("Add recipe"):
        if new_recipe_name.strip():
            new_id = int(recipes_df["id"].max()) + 1 if not recipes_df.empty else 1
            new_row = pd.DataFrame([{
                "id": new_id,
                "name": new_recipe_name.strip(),
                "servings": new_recipe_servings
            }])
            st.session_state.recipes_df = pd.concat([recipes_df, new_row], ignore_index=True)
            save_recipes(st.session_state.recipes_df)
            st.sidebar.success("Recipe added. Refresh to see it.")
        else:
            st.sidebar.error("Please enter a recipe name.")

    # -----------------------------------------------------
    # MAIN LAYOUT
    # -----------------------------------------------------

    col_left, col_right = st.columns([2, 1])

    # -----------------------------------------------------
    # LEFT COLUMN: RECIPE DETAILS
    # -----------------------------------------------------

    with col_left:
        st.header(selected_recipe_name)

        category = selected_recipe_row.get("category")
        prep_time = selected_recipe_row.get("prep_time")
        source_url = selected_recipe_row.get("source_url")

        if category:
            st.write(f"Category: {category}")
        if prep_time:
            st.write(f"Prep time: {prep_time}")
        if source_url:
            st.write(f"Original recipe: {source_url}")

        recipe_ingredients = ingredients_df[ingredients_df["recipe_id"] == selected_recipe_id]

        st.subheader("Ingredients")
        if recipe_ingredients.empty:
            st.info("No ingredients stored for this recipe.")
        else:
            st.dataframe(
                recipe_ingredients[["ingredient_name", "quantity", "normalized_name"]],
                use_container_width=True
            )

        st.subheader("Add Ingredient")

        ing_name = st.text_input("Ingredient name")
        ing_qty = st.text_input("Quantity (e.g., '2 onions', '3 tbsp')")

        if st.button("Add ingredient"):
            if ing_name.strip() and ing_qty.strip():
                new_ing_id = int(ingredients_df["id"].max()) + 1 if not ingredients_df.empty else 1
                new_row = pd.DataFrame([{
                    "id": new_ing_id,
                    "recipe_id": selected_recipe_id,
                    "ingredient_name": ing_name.strip(),
                    "quantity": ing_qty.strip(),
                    "normalized_name": None
                }])
                st.session_state.ingredients_df = pd.concat([ingredients_df, new_row], ignore_index=True)
                save_ingredients(st.session_state.ingredients_df)
                st.success("Ingredient added. Refresh to see it.")
            else:
                st.error("Please enter both ingredient name and quantity.")

    # -----------------------------------------------------
    # RIGHT COLUMN: COST CALCULATION
    # -----------------------------------------------------

    with col_right:
        st.subheader("Cost Calculation")

        if st.button("Calculate cost"):
            result = calculate_cost_df(
                selected_recipe_id,
                st.session_state.recipes_df,
                st.session_state.ingredients_df,
                st.session_state.walmart_df
            )
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
                use_container_width=True
            )

            # -----------------------------------------------------
            # STREAMLIT-ONLY PIE-STYLE BAR CHART
            # -----------------------------------------------------

            chart_data = breakdown_df[["ingredient", "cost"]].copy()
            chart_data = chart_data[chart_data["cost"] > 0]

            if chart_data.empty:
                st.info("No cost data available for this recipe.")
            else:
                total_cost = chart_data["cost"].sum()
                chart_data["percent"] = (chart_data["cost"] / total_cost) * 100

                st.bar_chart(chart_data, x="ingredient", y="percent")

                st.subheader("Highest Cost Ingredient")
                most_expensive = chart_data.loc[chart_data["cost"].idxmax(), "ingredient"]
                st.success(f"The ingredient contributing the most to cost is {most_expensive}")

            # -----------------------------------------------------
            # AI SUBSTITUTION TOOL
            # -----------------------------------------------------

            st.subheader("Cheaper Substitution Suggestion")

            ingredient_options = breakdown_df["ingredient"].tolist()
            selected_ing = st.selectbox("Select an ingredient", ingredient_options)

            if st.button("Suggest cheaper substitution"):
                row = breakdown_df[breakdown_df["ingredient"] == selected_ing].iloc[0]
                reply = ask_cheaper_substitution(row["ingredient"], row["cost"])
                st.write(reply)

    # -----------------------------------------------------
    # GENERAL COOKING CHAT
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