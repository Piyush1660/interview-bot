from flask import Flask, render_template
import sqlite3
import os

app = Flask(__name__)

DB_FILE = "interviews.db"

def fetch_logs():
    """Fetch all interview logs from the database"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT username, joined_at, left_at, duration FROM interview_logs ORDER BY id DESC")
        logs = cursor.fetchall()
        conn.close()
        return logs
    except Exception as e:
        print(f"❌ Dashboard Error: {e}")
        return []

@app.route('/')
def home():
    logs = fetch_logs()
    return render_template("dashboard.html", logs=logs)

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))  # Use Railway's assigned port
    app.run(host="0.0.0.0", port=port)