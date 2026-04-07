from flask import Flask, jsonify, render_template
from collections import deque
import time

import snap7
from snap7.util import get_int
from snap7.type import Areas

from pymodbus.client import ModbusTcpClient

app = Flask(__name__)

# ----------------------------
# S7-300
# ----------------------------
S7_IP = "192.168.10.11"
S7_RACK = 0
S7_SLOT = 2
S7_QW288_BYTE = 288

# ----------------------------
# LOGO Modbus TCP
# ----------------------------
LOGO_IP = "192.168.10.41"
LOGO_PORT = 510
LOGO_DID = 1
LOGO_VW200_ADDR = 100   # VW200 => adresa 100 (0-based)

# ----------------------------
# dashboard
# ----------------------------
POLL_SEC = 2
HIST_LEN = 10

hist_plc = deque(maxlen=HIST_LEN)
hist_logo = deque(maxlen=HIST_LEN)

s7_client = snap7.client.Client()
logo_client = None


def ensure_s7():
    if not s7_client.get_connected():
        s7_client.connect(S7_IP, S7_RACK, S7_SLOT)


def ensure_logo():
    global logo_client
    if logo_client is None:
        logo_client = ModbusTcpClient(host=LOGO_IP, port=LOGO_PORT)
    if not logo_client.connected:
        logo_client.connect()


def read_s7_qw288():
    try:
        ensure_s7()
        data = s7_client.read_area(Areas.PA, 0, S7_QW288_BYTE, 2)
        value = get_int(data, 0)
        return value, True, None    #pokus
    except Exception as e:
        return None, False, str(e) #pokus
    


def read_logo_vw200():
    try:
        ensure_logo()
        rr = logo_client.read_holding_registers(
            address=LOGO_VW200_ADDR,
            count=1,
            device_id=LOGO_DID
        )

        if rr.isError():
            return None, False, f"Modbus error: {rr}"

        raw_value = rr.registers[0]
        value = raw_value / 10.0

        print(f"KAHL1 raw={raw_value} scaled={value}")

        return value, True, None
    except Exception as e:
        return None, False, str(e)


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/live")
def api_live():
    plc_value, plc_ok, plc_err = read_s7_qw288()
    logo_value, logo_ok, logo_err = read_logo_vw200()

    print(f"S7={plc_value}  LOGO={logo_value}")

    if plc_value is None:
        plc_value = hist_plc[-1] if hist_plc else 0

    if logo_value is None:
        logo_value = hist_logo[-1] if hist_logo else 0

    hist_plc.append(plc_value)
    hist_logo.append(logo_value)

    return jsonify({
        "plc": plc_value,
        "logo": logo_value,
        "hist_plc": list(hist_plc),
        "hist_logo": list(hist_logo),
        "time": time.strftime("%H:%M:%S"),
        "plc_ok": plc_ok,
        "plc_err": plc_err,
        "logo_ok": logo_ok,
        "logo_err": logo_err,
        "poll_sec": POLL_SEC
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)