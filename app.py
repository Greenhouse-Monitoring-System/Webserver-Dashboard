from flask import *
from discord_bot import message_member, start_bot
import threading
import asyncio

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(port=8080, debug=True)