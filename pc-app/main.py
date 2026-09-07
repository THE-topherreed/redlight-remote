"""
RedLight - desktop companion app.

Runs quietly in the system tray. Advertises this PC on the LAN as
'redlight.local' so a paired CYD touchscreen board can find it without
anyone typing an IP address, and simulates the buyer's own DAW keyboard
shortcuts when the board's Record/Play/Stop buttons are tapped.
"""

import sys
import threading
import webbrowser

from flask import Flask, render_template, request, redirect, abort

import pyautogui
import pygetwindow as gw
from PIL import Image, ImageDraw
import pystray

import config_store
import mdns_advertise

PORT = 5005

config = config_store.load_config()
app = Flask(__name__)


def focus_daw():
    hint = config.get("window_title_hint", "").strip().lower()
    if not hint:
        return
    matches = [w for w in gw.getAllWindows() if hint in w.title.lower()]
    if not matches:
        return
    win = matches[0]
    try:
        if win.isMinimized:
            win.restore()
        win.activate()
    except Exception:
        pass


def press_keys(keys):
    keys = [k.strip() for k in keys if k.strip()]
    if not keys:
        return
    if len(keys) == 1:
        pyautogui.press(keys[0])
    else:
        pyautogui.hotkey(*keys)


def check_auth():
    if request.args.get("token", "") != config.get("token"):
        abort(403)


@app.route("/record")
def route_record():
    check_auth()
    focus_daw()
    press_keys(config["key_record"])
    return "ok\n"


@app.route("/play")
def route_play():
    check_auth()
    focus_daw()
    press_keys(config["key_play"])
    return "ok\n"


@app.route("/stop")
def route_stop():
    check_auth()
    focus_daw()
    press_keys(config["key_stop"])
    return "ok\n"


@app.route("/ping")
def route_ping():
    return "ok\n"


@app.route("/", methods=["GET"])
def route_settings():
    return render_template("settings.html", config=config, saved=False)


@app.route("/settings", methods=["POST"])
def route_save_settings():
    config["window_title_hint"] = request.form.get("window_title_hint", "").strip()
    config["key_record"] = [k.strip() for k in request.form.get("key_record", "").split(",") if k.strip()]
    config["key_play"] = [k.strip() for k in request.form.get("key_play", "").split(",") if k.strip()]
    config["key_stop"] = [k.strip() for k in request.form.get("key_stop", "").split(",") if k.strip()]
    config_store.save_config(config)
    return render_template("settings.html", config=config, saved=True)


@app.route("/regenerate-token", methods=["POST"])
def route_regenerate_token():
    config_store.regenerate_token(config)
    return redirect("/")


def run_flask():
    app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)


def make_tray_icon():
    img = Image.new("RGB", (64, 64), "#0a7d3c")
    draw = ImageDraw.Draw(img)
    draw.ellipse((16, 16, 48, 48), fill="white")
    return img


def open_settings(icon, item):
    webbrowser.open(f"http://localhost:{PORT}")


def quit_app(icon, item):
    icon.stop()
    sys.exit(0)


def main():
    threading.Thread(target=run_flask, daemon=True).start()

    zc, info = mdns_advertise.start_advertising(PORT)

    menu = pystray.Menu(
        pystray.MenuItem("Open Settings", open_settings, default=True),
        pystray.MenuItem("Quit", quit_app),
    )
    icon = pystray.Icon("RedLight", make_tray_icon(), "RedLight", menu)
    try:
        icon.run()
    finally:
        mdns_advertise.stop_advertising(zc, info)


if __name__ == "__main__":
    main()
