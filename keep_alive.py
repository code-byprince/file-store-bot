from flask import Flask
from threading import Thread
from config import Config

app = Flask(__name__)


@app.route("/")
def home():
    return "✅ File Storage Bot is alive and running!"


def run():
    app.run(host="0.0.0.0", port=Config.PORT)


def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
