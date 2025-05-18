import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, jsonify
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Ensure database and table exist
def init_db():
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()
    conn.close()

# Log a message to the database
def log_message(role, content):
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Messages (role, content) VALUES (?, ?)", (role, content))
    conn.commit()
    conn.close()

# Retrieve conversation history
def get_conversation():
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    cursor.execute("SELECT role, content FROM Messages ORDER BY timestamp ASC")
    messages = [{"role": role, "content": content} for role, content in cursor.fetchall()]
    conn.close()
    return messages

# Get AI response from OpenRouter API
def get_ai_response(messages):
    api_url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": messages,
        "max_tokens": 1000
    }
    response = requests.post(api_url, headers=headers, json=payload)
    if response.status_code == 200:
        data = response.json()
        return data["choices"][0]["message"]["content"]
    else:
        print("Error:", response.text)
        return "Sorry, I couldn't process your request."

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.form['message']
    log_message('user', user_input)

    conversation = get_conversation()
    ai_response = get_ai_response(conversation)
    log_message('assistant', ai_response)

    return jsonify({'response': ai_response})

# Initialize database when the app starts
init_db()

if __name__ == '__main__':
    app.run(debug=True)
