import os
import openai
from dotenv import load_dotenv

load_dotenv()  # <-- THIS MUST RUN BEFORE load_api_key()
def load_api_key():
    """
    Load the OpenAI API key from environment variables.
    In Streamlit Cloud, set this in Secrets as OPENAI_API_KEY.
    """
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY in environment or Streamlit Secrets.")
    return key


# ---------------------------------------------------------
# BASE SYSTEM MESSAGE
# ---------------------------------------------------------

SYSTEM_MESSAGE = (
    "You are a friendly, bubbly cooking assistant. "
    "You only answer questions about cooking, recipes, ingredients, substitutions, "
    "kitchen techniques, food science, meal planning, or anything food-related. "
    "If the user asks something unrelated to cooking, politely redirect them back to food topics. "
    "Your tone is upbeat, warm, and encouraging, like a cheerful kitchen companion."
)


# ---------------------------------------------------------
# CHAT WITH HISTORY
# ---------------------------------------------------------

def ask_ai_with_history(chat_history, user_message):
    """
    Chat with the AI using full conversation history.
    chat_history: list of {"role": "user"/"assistant", "content": str}
    user_message: latest user input
    """
    openai.api_key = load_api_key()

    # Add user message
    chat_history.append({"role": "user", "content": user_message})

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_MESSAGE},
            *chat_history
        ],
        max_tokens=350,
        temperature=0.7,
    )

    ai_message = response["choices"][0]["message"]["content"].strip()

    # Save assistant reply
    chat_history.append({"role": "assistant", "content": ai_message})

    return ai_message


# ---------------------------------------------------------
# ONE-SHOT CHEAPER SUBSTITUTION (NO HISTORY)
# ---------------------------------------------------------

def ask_cheaper_substitution(ingredient_name, ingredient_cost):
    """
    Ask the AI for a cheaper substitution for a single ingredient.
    Does not use chat history.
    """
    openai.api_key = load_api_key()

    prompt = (
        f"The ingredient '{ingredient_name}' costs ${ingredient_cost}. "
        f"Suggest a cheaper substitution that keeps the recipe kosher and similar in flavor. "
        f"Explain briefly why it is cheaper and how it affects the dish."
    )

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_MESSAGE},
            {"role": "user", "content": prompt}
        ],
        max_tokens=250,
        temperature=0.7,
    )

    return response["choices"][0]["message"]["content"].strip()