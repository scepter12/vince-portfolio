from flask import Flask, render_template, request, jsonify
import requests
import json
import os

app = Flask(__name__)

LM_STUDIO_URL = "http://127.0.0.1:1234/v1/chat/completions"
MODEL = "llama-3.2-3b-instruct"
HISTORY_FILE = "/tmp/chat_history.json" if os.environ.get("VERCEL") else "chat_history.json"

DEFAULT_SYSTEM_PROMPT = {
    "role": "system",
    "content": """
You are "Scepter", the advanced virtual assistant of Vince Villapando.
Your purpose is to assist visitors to Vince's portfolio website.
Answer questions about Vince's background, education, experience, and skills in a polite, helpful, and professional manner.
Vince's information:
- Name: Vince Villapando
- Contact Number: +63 9055660995
- Email: villapandobins@yahoo.com
- Address: Bulacnin, Lipa City, Batangas
- About: Vince is a BS Metallurgical Engineering student at Batangas State University (2023-2027). He is highly flexible, has experience as a salesman, tutor, virtual assistant, and assistant researcher. He is fluent in Filipino, and can understand and speak English.
- Education:
  * College: Batangas State University (2023-2027), BS Metallurgical Engineering
  * Senior High School: Lipa City Colleges
- Experience:
  * Salesman (public market during high school years)
  * Tutor (for middle school students)
  * Virtual Assistant (managing emails, data entry)
  * Assistant Researcher (plant designs, thesis, academic research)
- Skills: Auditing, Financial Accounting, Data Entry, Research, Writing, Proof Reading.

Rules:
1. Speak in a helpful and professional manner.
2. Answer questions accurately using Vince's info.
3. If asked about things outside Vince's portfolio, redirect politely back to helping them learn about Vince.
4. Do not use emojis in your responses.
"""
}

def load_conversation():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return [DEFAULT_SYSTEM_PROMPT]

def save_conversation(conv):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(conv, f, indent=4, ensure_ascii=False)
    except Exception:
        pass

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/history", methods=["GET"])
def get_history():
    conversation = load_conversation()
    # Filter out system messages for front-end rendering
    user_visible_messages = [msg for msg in conversation if msg["role"] != "system"]
    return jsonify({"history": user_visible_messages})

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")
    conversation = load_conversation()

    conversation.append({
        "role": "user",
        "content": user_message
    })

    payload = {
        "model": MODEL,
        "messages": conversation,
        "temperature": 0.7,
        "max_tokens": 500
    }

    try:
        response = requests.post(LM_STUDIO_URL, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        ai_message = data["choices"][0]["message"]["content"]
    except Exception as e:
        ai_message = "Hindi maabot ang LM Studio server. Siguraduhing naka-run ito sa port 1234."

    conversation.append({
        "role": "assistant",
        "content": ai_message
    })

    save_conversation(conversation)

    return jsonify({
        "response": ai_message
    })

@app.route("/reset", methods=["POST"])
def reset():
    conversation = [DEFAULT_SYSTEM_PROMPT]
    save_conversation(conversation)
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(debug=True)