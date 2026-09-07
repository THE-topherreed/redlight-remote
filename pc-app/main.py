"""
RedLight - desktop companion app.

Runs quietly in the system tray. Advertises this PC on the LAN as
'redlight.local' so a paired CYD touchscreen board can find it without
anyone typing an IP address, and simulates the buyer's own DAW keyboard
shortcuts when the board's Record/Play/Stop buttons are tapped.
"""

import os
import socket
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
from daw_presets import PRESETS

PORT = 5005

# A fixed local port used purely as a single-instance lock (never served
# on). Binding it is how we tell whether another copy of the app is
# already running - a tray-only app gives no visual sign when a second
# copy launches, so without this, every extra double-click on the
# Desktop/Start Menu icon silently piles up another background process
# and another duplicate tray icon.
_INSTANCE_LOCK_PORT = 45177
_instance_lock_socket = None


def _acquire_single_instance_lock():
    global _instance_lock_socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", _INSTANCE_LOCK_PORT))
        s.listen(1)
        _instance_lock_socket = s  # keep alive for the app's lifetime
        return True
    except OSError:
        s.close()
        return False

# First run = no config file exists yet anywhere on this machine. Checked
# before load_config() creates one, so this only ever fires once per
# install - a non-technical buyer shouldn't have to go hunting for a
# taskbar icon just to see their pairing code for the first time.
IS_FIRST_RUN = not os.path.exists(config_store.CONFIG_PATH) and not os.path.exists(config_store._OLD_CONFIG_PATH)

config = config_store.load_config()
app = Flask(__name__)


@app.after_request
def no_cache(response):
    # The settings page changes (new presets, saved edits) but a browser
    # tab left open for days will otherwise keep showing whatever it
    # first loaded - this has caused real confusion (a preset that was
    # clearly on the server not showing up client-side). Never cache.
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response


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


@app.route("/mode")
def route_mode():
    check_auth()
    toggle = config["key_play"] == config["key_stop"]
    return {"play_stop_toggle": toggle}


@app.route("/", methods=["GET"])
def route_settings():
    return render_template("settings.html", config=config, saved=False, presets=PRESETS)


@app.route("/settings", methods=["POST"])
def route_save_settings():
    config["window_title_hint"] = request.form.get("window_title_hint", "").strip()
    config["key_record"] = [k.strip() for k in request.form.get("key_record", "").split(",") if k.strip()]
    config["key_play"] = [k.strip() for k in request.form.get("key_play", "").split(",") if k.strip()]
    config["key_stop"] = [k.strip() for k in request.form.get("key_stop", "").split(",") if k.strip()]
    config_store.save_config(config)
    return render_template("settings.html", config=config, saved=True, presets=PRESETS)


@app.route("/regenerate-token", methods=["POST"])
def route_regenerate_token():
    config_store.regenerate_token(config)
    return redirect("/")


def run_flask():
    app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)


def make_tray_icon():
    # The brand mark - a red dot with a darker bezel ring and a small
    # specular highlight - drawn small and crisp (no blur; it renders
    # at 16-32px in the tray, where a soft glow just looks muddy).
    size = 128
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx = cy = size // 2
    r = int(size * 0.42)
    draw.ellipse(
        [cx - r, cy - r, cx + r, cy + r],
        fill=(217, 74, 63, 255),
        outline=(122, 26, 21, 255),
        width=max(2, int(size * 0.045)),
    )
    hx, hy = int(size * 0.41), int(size * 0.385)
    hrx, hry = int(size * 0.11), int(size * 0.075)
    draw.ellipse([hx - hrx, hy - hry, hx + hrx, hy + hry], fill=(255, 255, 255, 110))
    return img


def open_settings(icon, item):
    webbrowser.open(f"http://localhost:{PORT}")


def quit_app(icon, item):
    icon.stop()
    sys.exit(0)


def main():
    if not _acquire_single_instance_lock():
        # Already running - just show it instead of starting a duplicate.
        webbrowser.open(f"http://localhost:{PORT}")
        return

    threading.Thread(target=run_flask, daemon=True).start()

    if IS_FIRST_RUN:
        threading.Timer(1.0, open_settings, args=(None, None)).start()

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
