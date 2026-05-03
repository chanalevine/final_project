import os
import openai


def load_api_key():
    """
    Load the OpenAI API key from environment variables.
    In Streamlit Cloud, set this in Secrets as OPENAI_API_KEY.
    """
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY in environment or Streamlit Secrets.")
    return key


def ask_ai_with_history(chat_history, user_message):
    """
    Chat with a friendly, bubbly cooking-only assistant.
    - chat_history: list of {"role": "user"/"assistant", "content": str}
    - user_message: the latest user input (str)
    Returns the assistant's reply (str) and mutates chat_history in place.
    """
    openai.api_key = load_api_key()

    # Add the new user message to history
    chat_history.append({"role": "user", "content": user_message})

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a friendly, bubbly cooking assistant. "
                    "You ONLY answer questions about cooking, recipes, ingredients, substitutions, "
                    "kitchen tips, food science, meal planning, or anything food-related. "
                    "If the user asks something unrelated to cooking, politely redirect them back to food. "
                    "Your tone is upbeat, warm, and encouraging, like a cheerful kitchen buddy."
                )
            },
            *chat_history
        ],
        max_tokens=300,
        temperature=0.7,
    )

    ai_message = response["choices"][0]["message"]["content"].strip()

    # Save assistant reply to history
    chat_history.append({"role": "assistant", "content": ai_message})

    return ai_message