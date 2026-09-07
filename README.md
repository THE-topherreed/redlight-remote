# RedLight

A touchscreen Record / Play / Stop remote for a vocal booth. Tap the screen, your DAW responds — no computer inside the booth, no engineer required.

**[Install the firmware →](https://the-topherreed.github.io/redlight-remote/)**

## How it works

- A "CYD" touchscreen board (ESP32-2432S028R) runs the firmware in [`firmware/`](firmware/), drawing three buttons and sending WiFi requests when tapped.
- A small desktop app ([`pc-app/`](pc-app/)) runs on the studio computer, advertises itself on the LAN via mDNS as `redlight.local`, and simulates whatever keyboard shortcut your DAW uses for Record/Play/Stop.
- First-time setup uses a WiFi captive portal (no code editing) and a 6-digit pairing code shown by the desktop app — see the install guide for the full walkthrough.

## Repo layout

```
firmware/       Arduino sketch (WiFiManager + mDNS + touchscreen UI)
pc-app/         Python source for the desktop companion app
docs/           GitHub Pages site - the browser-based firmware installer
```

## Building it yourself

**Firmware:** Arduino IDE or `arduino-cli`, ESP32 board package, plus the `TFT_eSPI` and `XPT2046_Touchscreen` libraries. Configure `TFT_eSPI`'s `User_Setup_Select.h` to use `firmware/TFT_eSPI_Setup/Setup_CYD_2432S028R.h`.

**Desktop app:**
```
cd pc-app
pip install -r requirements.txt
python main.py
```
Package a standalone Windows build with `build.bat` (PyInstaller), then compile `installer.iss` with Inno Setup for a distributable installer.

## Availability

RedLight is currently sold in small batches, direct to buyers, rather than through public retail. It has not yet gone through independent FCC/CE certification testing — the ESP32 module it's built on carries its own radio certification from Espressif when genuinely sourced, but the finished board hasn't been through the separate compliance testing that full retail sale would require. If that matters for your use case, ask before buying.

## License

All rights reserved.
