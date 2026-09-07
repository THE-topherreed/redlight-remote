"""Persistent settings for RedLight, stored in the user's AppData."""

import json
import os
import secrets
import shutil

APP_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "RedLight")
CONFIG_PATH = os.path.join(APP_DIR, "config.json")

# One-time migration from the product's old working name.
_OLD_APP_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "VocalBoothRemote")
_OLD_CONFIG_PATH = os.path.join(_OLD_APP_DIR, "config.json")

DEFAULT_CONFIG = {
    "token": None,  # generated on first run
    "window_title_hint": "",
    "key_record": ["ctrl", "r"],
    "key_play": ["space"],
    "key_stop": ["num0"],
    "key_beginning": [],  # optional 4th button - "go to start"; empty hides it
}


def _generate_token():
    return "".join(secrets.choice("0123456789") for _ in range(6))


def load_config():
    os.makedirs(APP_DIR, exist_ok=True)
    if not os.path.exists(CONFIG_PATH) and os.path.exists(_OLD_CONFIG_PATH):
        shutil.copy(_OLD_CONFIG_PATH, CONFIG_PATH)
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        config = dict(DEFAULT_CONFIG)

    changed = False
    for key, value in DEFAULT_CONFIG.items():
        if key not in config:
            config[key] = value
            changed = True
    if not config.get("token"):
        config["token"] = _generate_token()
        changed = True

    if changed:
        save_config(config)
    return config


def save_config(config):
    os.makedirs(APP_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def regenerate_token(config):
    config["token"] = _generate_token()
    save_config(config)
    return config
