import os
import uuid

from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, session, url_for
from openai import OpenAI

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-secret-key")

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = "You are a helpful assistant."

# Conversations are kept on the server, one per browser session
conversations = {}


def get_history():
    cid = session.get("cid")
    if cid not in conversations:
        cid = uuid.uuid4().hex
        session["cid"] = cid
        conversations[cid] = []
    return conversations[cid]


@app.route("/", methods=["GET", "POST"])
def index():
    history = get_history()
    error = None
    last_text = ""

    if request.method == "POST":
        last_text = request.form.get("message", "").strip()
        if last_text:
            history.append({"role": "user", "content": last_text})
            messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history
            try:
                response = client.chat.completions.create(model=MODEL, messages=messages)
                history.append(
                    {"role": "assistant", "content": response.choices[0].message.content}
                )
                return redirect(url_for("index", _anchor="bottom"))
            except Exception as e:
                history.pop()  # remove the message that failed
                error = str(e)

    return render_template("index.html", history=history, error=error, last_text=last_text)


@app.route("/new", methods=["POST"])
def new_chat():
    get_history().clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
