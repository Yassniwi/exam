import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from google import genai
from google.genai import types

from chatbot_config import (
    MAX_HISTORY_TURNS,
    MAX_MESSAGE_LENGTH,
    MODEL_NAME,
    SYSTEM_PROMPT,
)

load_dotenv()

app = Flask(__name__)

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None


def build_contents(history, message):
    """Convert the chat history from the browser into Gemini's message format."""
    contents = []

    for item in history[-MAX_HISTORY_TURNS:]:
        role = "model" if item.get("role") == "assistant" else "user"
        text = str(item.get("text", "")).strip()
        if text:
            contents.append(
                types.Content(role=role, parts=[types.Part(text=text)])
            )

    contents.append(types.Content(role="user", parts=[types.Part(text=message)]))
    return contents


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    if client is None:
        return jsonify({"error": "GEMINI_API_KEY is missing in the .env file."}), 500

    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    history = data.get("history", [])

    if not message:
        return jsonify({"error": "Please type a message."}), 400
    if len(message) > MAX_MESSAGE_LENGTH:
        return jsonify(
            {"error": f"Message is too long (max {MAX_MESSAGE_LENGTH} characters)."}
        ), 400
    if not isinstance(history, list):
        history = []

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=build_contents(history, message),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.6,
            ),
        )
        reply = (response.text or "").strip()
        if not reply:
            reply = "Sorry, I couldn't come up with a reply. Please try again."
        return jsonify({"reply": reply})

    except Exception as error:
        print(f"Gemini API error: {error}")
        return jsonify({"error": "Something went wrong. Please try again."}), 500


if __name__ == "__main__":
    app.run(debug=True)
