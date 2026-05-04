import streamlit as st
from openai import AzureOpenAI

# ---------------------------------------------------------
# LOAD FROM STREAMLIT SECRETS
# ---------------------------------------------------------


def load_azure_creds():
    try:
        endpoint = st.secrets["AZURE_OPENAI_ENDPOINT"]
        key = st.secrets["AZURE_OPENAI_API_KEY"]
        model = st.secrets["AZURE_OPENAI_MODEL"]
        return endpoint, key, model
    except Exception:
        st.error(
            "❌ Azure OpenAI credentials missing.\n\n"
            "Add them to `.streamlit/secrets.toml`:\n\n"
            "AZURE_OPENAI_ENDPOINT = \"https://...\"\n"
            "AZURE_OPENAI_API_KEY = \"your-key\"\n"
            "AZURE_OPENAI_MODEL = \"gpt-5.4-nano\"\n"
        )
        return None, None, None


SYSTEM_MESSAGE = (
    "You are a friendly, bubbly cooking assistant. "
    "You only answer questions about cooking, recipes, ingredients, substitutions, "
    "kitchen techniques, food science, meal planning, or anything food-related. "
    "If the user asks something unrelated to cooking, politely redirect them back to food topics. "
    "Your tone is upbeat, warm, and encouraging, like a cheerful kitchen companion. "
    "If the user asks for recipe recommendations, you MUST ONLY recommend recipes "
    "from kosher.com. Never recommend recipes from any other site. "
    "Phrase suggestions like: 'You might enjoy the kosher.com recipe for ___'. "
)


def get_client():
    endpoint, key, model = load_azure_creds()
    if not endpoint:
        return None, None

    client = AzureOpenAI(
        api_key=key,
        api_version="2024-02-15-preview",
        azure_endpoint=endpoint
    )
    return client, model


# ---------------------------------------------------------
# CHAT WITH HISTORY
# ---------------------------------------------------------

def ask_ai_with_history(chat_history, user_message):
    client, model = get_client()
    if not client:
        return "Azure OpenAI credentials missing — cannot process request."

    chat_history.append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_MESSAGE},
                *chat_history
            ]
        )

        reply = response.choices[0].message.content.strip()
        chat_history.append({"role": "assistant", "content": reply})
        return reply

    except Exception as e:
        st.error(f"❌ Azure OpenAI error: {e}")
        return "There was an error contacting Azure OpenAI."


# ---------------------------------------------------------
# ONE-SHOT CHEAPER SUBSTITUTION (WITH RECIPE NAME)
# ---------------------------------------------------------

def ask_cheaper_substitution(ingredient_name, ingredient_cost, recipe_title):
    """
    Suggest a cheaper substitution for an ingredient,
    tailored to the specific recipe, and recommend a kosher.com recipe.
    """
    client, model = get_client()
    if not client:
        return "Azure OpenAI credentials missing — cannot process request."

    prompt = (
        f"You are helping with the recipe '{recipe_title}'. "
        f"The ingredient '{ingredient_name}' in this recipe costs ${ingredient_cost}. "
        f"Suggest a cheaper substitution that keeps the recipe kosher and similar in flavor. "
        f"Explain briefly why it is cheaper and how it affects the dish. "
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_MESSAGE},
                {"role": "user", "content": prompt}
            ]
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        st.error(f"❌ Azure OpenAI error: {e}")
        return "There was an error contacting Azure OpenAI."
