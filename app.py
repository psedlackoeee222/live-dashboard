from flask import Flask, jsonify, render_template
import time
import random
from collections import deque

app = Flask(__name__)

# buffer posledných 10 hodnôt
hist_plc = deque(maxlen=10)
hist_logo = deque(maxlen=10)

plc_val = 100
logo_val = 5.0


def read_values():
    global plc_val, logo_val

    # simulácia (neskôr sem dáme Snap7 + Modbus)
    plc_val += random.randint(-2, 2)
    logo_val += random.uniform(-0.1, 0.1)

    hist_plc.append(plc_val)
    hist_logo.append(round(logo_val, 2))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/live")
def api_live():
    read_values()

    return jsonify({
        "plc": plc_val,
        "logo": round(logo_val, 2),
        "hist_plc": list(hist_plc),
        "hist_logo": list(hist_logo),
        "time": time.strftime("%H:%M:%S")
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)