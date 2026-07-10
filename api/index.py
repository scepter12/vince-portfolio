from flask import Flask, render_template, request, jsonify
import requests
import json
import os

# Resolve static and template paths dynamically relative to the current script location
api_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(api_dir)
template_dir = os.path.join(project_dir, "templates")
static_dir = os.path.join(project_dir, "static")

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

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

# Load Gemini API Key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY and os.path.exists(".env"):
    with open(".env", "r") as f:
        for line in f:
            if line.strip().startswith("GEMINI_API_KEY="):
                GEMINI_API_KEY = line.split("=", 1)[1].strip()
                break

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

    global GEMINI_API_KEY
    # Reload key if it wasn't loaded
    if not GEMINI_API_KEY and os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if line.strip().startswith("GEMINI_API_KEY="):
                    GEMINI_API_KEY = line.split("=", 1)[1].strip()
                    break

    if GEMINI_API_KEY:
        # Use Google Gemini API
        contents = []
        for msg in conversation:
            if msg["role"] == "system":
                continue
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })
            
        system_instruction = {
            "parts": [{"text": DEFAULT_SYSTEM_PROMPT["content"]}]
        }
        
        payload = {
            "contents": contents,
            "systemInstruction": system_instruction,
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 500
            }
        }
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            ai_message = data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            print("Gemini API Error:", e)
            ai_message = "Server Not Available."
    else:
        # Use local LM Studio fallback
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
            print("LM Studio Error:", e)
            ai_message = "Server Not Available."

    conversation.append({
        "role": "assistant",
        "content": ai_message
    })

    save_conversation(conversation)

    return jsonify({
        "response": ai_message
    })

@app.route("/contact", methods=["POST"])
def contact():
    data = request.json
    webhook_url = "https://basis-delirium-tulip.ngrok-free.dev/webhook-test/1c96d5ff-2e67-47cb-85f3-de7a8452b35d"
    try:
        # Gamitin ang GET request na may query parameters para tugmaan ang n8n setup mo
        response = requests.get(webhook_url, params=data, timeout=15)
        return jsonify({"success": response.ok}), response.status_code
    except Exception as e:
        print("Webhook Error:", e)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/reset", methods=["POST"])
def reset():
    conversation = [DEFAULT_SYSTEM_PROMPT]
    save_conversation(conversation)
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(debug=True)