import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from core.db import get_connection
from core.cost_engine import calculate_recipe_cost
from ai.ai_helper import ask_ai_with_history, ask_cheaper_substitution


# ---------------------------------------------------------
# DATA LOADERS
# ---------------------------------------------------------
@st.cache_data
def load_data():
    conn = get_connection()
    recipes = pd.read_sql_query("SELECT * FROM recipes", conn)
    recipe_ingredients = pd.read_sql_query("SELECT * FROM recipe_ingredients", conn)
    ingredients = pd.read_sql_query("SELECT * FROM ingredients", conn)
    conn.close()
    return recipes, recipe_ingredients, ingredients


# ---------------------------------------------------------
# SAVE HELPERS
# ---------------------------------------------------------
def save_recipes(df):
    conn = get_connection()
    df.to_sql("recipes", conn, if_exists="replace", index=False)
    conn.close()


def save_recipe_ingredients(df):
    conn = get_connection()
    df.to_sql("recipe_ingredients", conn, if_exists="replace", index=False)
    conn.close()


def save_ingredients(df):
    conn = get_connection()
    df.to_sql("ingredients", conn, if_exists="replace", index=False)
    conn.close()


# ---------------------------------------------------------
# MAIN APP
# ---------------------------------------------------------
def main():
    st.set_page_config(page_title="Recipe Cost and Analysis", layout="wide")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "recipes_df" not in st.session_state:
        recipes_df, recipe_ingredients_df, ingredients_df = load_data()
        st.session_state.recipes_df = recipes_df
        st.session_state.recipe_ingredients_df = recipe_ingredients_df
        st.session_state.ingredients_df = ingredients_df

    recipes_df = st.session_state.recipes_df
    recipe_ingredients_df = st.session_state.recipe_ingredients_df
    ingredients_df = st.session_state.ingredients_df

    st.title("Recipe Cost and Analysis")

    # -----------------------------------------------------
    # SIDEBAR — SELECT / ADD / EDIT / DELETE RECIPE
    # -----------------------------------------------------
    st.sidebar.header("Recipes")

    recipe_names = recipes_df["title"].sort_values().tolist()
    selected_recipe_name = st.sidebar.selectbox("Select a recipe", recipe_names)

    selected_recipe_row = recipes_df.loc[recipes_df["title"] == selected_recipe_name].iloc[0]
    selected_recipe_id = int(selected_recipe_row["id"])

    # ADD RECIPE
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

    # EDIT RECIPE
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

    # DELETE RECIPE
    st.sidebar.markdown("---")
    st.sidebar.subheader("Delete Recipe")

    if st.sidebar.button("Delete recipe"):
        st.session_state.recipes_df = recipes_df[recipes_df["id"] != selected_recipe_id]
        st.session_state.recipe_ingredients_df = recipe_ingredients_df[
            recipe_ingredients_df["recipe_id"] != selected_recipe_id
        ]
        save_recipes(st.session_state.recipes_df)
        save_recipe_ingredients(st.session_state.recipe_ingredients_df)
        st.sidebar.success("Recipe deleted. Refresh to update.")

    # -----------------------------------------------------
    # TABS
    # -----------------------------------------------------
    tab_overview, tab_cost, tab_chat = st.tabs(["Overview", "Cost analysis", "Chatbot"])

    # -----------------------------------------------------
    # TAB 1 — OVERVIEW
    # -----------------------------------------------------
    with tab_overview:
        st.header(selected_recipe_name)

        recipe_ings = recipe_ingredients_df[
            recipe_ingredients_df["recipe_id"] == selected_recipe_id
        ]

        st.subheader("Ingredients")

        if recipe_ings.empty:
            st.info("No ingredients stored for this recipe.")
        else:
            merged = recipe_ings.merge(
                ingredients_df,
                left_on="ingredient_id",
                right_on="id",
                how="left",
                suffixes=("", "_ing")
            )

            merged["ingredient"] = merged["name"].fillna(merged["quantity"])
            display_df = merged[["ingredient", "quantity"]].copy()
            st.dataframe(display_df, hide_index=True, use_container_width=True)

        st.subheader("Add Ingredient")

        col_ing_name, col_ing_qty = st.columns(2)
        with col_ing_name:
            ing_name = st.text_input("Ingredient name", key="ing_name_input")
        with col_ing_qty:
            ing_qty = st.text_input("Quantity (e.g., '2 cups')", key="ing_qty_input")

        if st.button("Add ingredient", key="add_ing_btn"):
            if ing_name.strip() and ing_qty.strip():

                # 1) Find or create ingredient
                existing = ingredients_df[
                    ingredients_df["name"].str.lower() == ing_name.strip().lower()
                ]

                if not existing.empty:
                    ingredient_id = int(existing.iloc[0]["id"])
                else:
                    new_ing_id = int(ingredients_df["id"].max()) + 1 if not ingredients_df.empty else 1
                    new_ing_row = pd.DataFrame([{
                        "id": new_ing_id,
                        "name": ing_name.strip(),
                        "price": None,
                        "price_unit": None,
                        "package_size": None
                    }])
                    ingredients_df = pd.concat([ingredients_df, new_ing_row], ignore_index=True)
                    st.session_state.ingredients_df = ingredients_df
                    save_ingredients(st.session_state.ingredients_df)
                    ingredient_id = new_ing_id

                # 2) Insert into recipe_ingredients
                new_rec_ing_id = int(recipe_ingredients_df["id"].max()) + 1 if not recipe_ingredients_df.empty else 1
                new_row = pd.DataFrame([{
                    "id": new_rec_ing_id,
                    "recipe_id": selected_recipe_id,
                    "ingredient_id": ingredient_id,
                    "quantity": ing_qty.strip()
                }])

                recipe_ingredients_df = pd.concat(
                    [recipe_ingredients_df, new_row], ignore_index=True
                )
                st.session_state.recipe_ingredients_df = recipe_ingredients_df
                save_recipe_ingredients(st.session_state.recipe_ingredients_df)

                st.success("Ingredient added and linked. Refresh to see it.")
            else:
                st.error("Please enter both ingredient name and quantity.")

    # -----------------------------------------------------
    # TAB 2 — COST ANALYSIS
    # -----------------------------------------------------
    with tab_cost:
        st.header("Cost analysis")

        if st.button("Calculate cost", key="calc_cost_btn"):
            result = calculate_recipe_cost(selected_recipe_id)
            st.session_state.last_cost_result = result

        result = st.session_state.get("last_cost_result")

        if result:
            st.markdown(f"**Total cost:** ${result['total_cost']}")
            st.markdown(f"**Cost per serving:** ${result['cost_per_serving']}")

            breakdown_df = pd.DataFrame(result["breakdown"])

            st.subheader("Cost breakdown by ingredient")
            st.dataframe(
                breakdown_df[
                    ["ingredient", "price", "package_size", "price_unit", "cost"]
                ],
                hide_index=True,
                use_container_width=True
            )

            chart_data = breakdown_df[["ingredient", "cost"]].copy()
            chart_data = chart_data[chart_data["cost"] > 0]

            if chart_data.empty:
                st.info("No cost data available for this recipe.")
            else:
                st.subheader("Cost distribution")
                fig, ax = plt.subplots(figsize=(5, 5))
                ax.pie(
                    chart_data["cost"],
                    labels=chart_data["ingredient"],
                    autopct="%1.1f%%",
                    startangle=90
                )
                ax.axis("equal")
                st.pyplot(fig)

                st.subheader("Highest cost ingredient")
                most_expensive = chart_data.loc[chart_data["cost"].idxmax(), "ingredient"]
                st.success(f"The ingredient contributing the most to cost is **{most_expensive}**")

            if result.get("featured_ingredient"):
                st.subheader("✨ Ingredient spotlight")
                st.markdown(f"### {result['featured_ingredient']}")
                st.write(result["featured_description"])
            else:
                st.info("No ingredient description available.")

            st.subheader("Cheaper substitution suggestion")

            ingredient_options = breakdown_df["ingredient"].tolist()
            selected_ing = st.selectbox("Select an ingredient", ingredient_options, key="sub_ing_select")

            if st.button("Suggest cheaper substitution", key="sub_btn"):
                row = breakdown_df[breakdown_df["ingredient"] == selected_ing].iloc[0]
                reply = ask_cheaper_substitution(row["ingredient"], row["cost"])
                st.write(reply)
        else:
            st.info("Click 'Calculate cost' to see cost analysis for this recipe.")

    # -----------------------------------------------------
    # TAB 3 — CHATBOT
    # -----------------------------------------------------
    with tab_chat:
        st.header("Cooking questions")

        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f"**You:** {msg['content']}")
            else:
                st.markdown(f"**Assistant:** {msg['content']}")

        user_input = st.text_input("Ask a cooking question", key="chat_input")

        col_a, col_b = st.columns(2)

        with col_a:
            if st.button("Send question", key="chat_send"):
                if user_input.strip():
                    ask_ai_with_history(st.session_state.chat_history, user_input)
                    st.experimental_rerun()

        with col_b:
            if st.button("Clear conversation", key="chat_clear"):
                st.session_state.chat_history = []
                st.experimental_rerun()


if __name__ == "__main__":
    main()
    