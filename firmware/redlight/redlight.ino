/*
 * RedLight - product firmware
 *
 * Runs on a "CYD" (ESP32-2432S028R, ILI9341 2.8" + XPT2046 touch).
 * Draws RECORD / PLAY / STOP buttons and sends commands over WiFi to the
 * companion desktop app (RedLight), which simulates whatever keyboard
 * shortcut the buyer's DAW uses.
 *
 * First-boot setup (no code editing, no computer needed for the board):
 *   1. Board powers on with no saved WiFi -> starts its own access point
 *      named "RedLight-Setup".
 *   2. Buyer connects a phone/laptop to that AP - a setup page opens
 *      automatically (captive portal).
 *   3. Buyer picks their home WiFi, enters the password, and pastes in
 *      the Pairing Code shown by the desktop app.
 *   4. Board reboots, joins WiFi, and finds the desktop app automatically
 *      via mDNS (no IP address needed) at redlight.local.
 *
 * To redo setup later (new WiFi network, etc.): hold the screen anywhere
 * for 5+ seconds while powering on.
 *
 * Libraries needed (Arduino Library Manager):
 *   - TFT_eSPI (Bodmer)
 *   - XPT2046_Touchscreen (PaulStoffregen)
 *   - WiFiManager (tzapu)
 *   - ESPmDNS (bundled with ESP32 board package)
 *   - Preferences (bundled with ESP32 board package)
 *
 * TFT_eSPI must be configured for the ESP32-2432S028R - see
 * product/firmware/TFT_eSPI_Setup/Setup_CYD_2432S028R.h in this repo.
 */

#include <WiFi.h>
#include <WiFiManager.h>
#include <ESPmDNS.h>
#include <HTTPClient.h>
#include <Preferences.h>
#include <SPI.h>
#include <TFT_eSPI.h>
#include <XPT2046_Touchscreen.h>

// --- Fixed hardware config ----------------------------------------------

#define XPT2046_CS   33
#define XPT2046_IRQ  36

#define TOUCH_MIN_X 200
#define TOUCH_MAX_X 3700
#define TOUCH_MIN_Y 240
#define TOUCH_MAX_Y 3800

const char* MDNS_HOSTNAME = "redlight"; // resolves to redlight.local
const int SERVER_PORT = 5005;
const unsigned long RESET_HOLD_MS = 5000;

// --------------------------------------------------------------------------

TFT_eSPI tft = TFT_eSPI();
SPIClass touchSPI = SPIClass(VSPI);
XPT2046_Touchscreen ts(XPT2046_CS, XPT2046_IRQ);
Preferences prefs;

String pairingToken;
String resolvedServerIP;
unsigned long lastMdnsLookup = 0;
const unsigned long MDNS_REFRESH_MS = 30000;

struct Button {
  const char* label;
  int x, y, w, h;
  uint16_t color;
  const char* endpoint;
};

Button buttons[] = {
  { "RECORD", 20,  40, 200, 70, TFT_RED,   "/record" },
  { "PLAY",   20, 130, 200, 70, TFT_GREEN, "/play"   },
  { "STOP",   20, 220, 200, 70, TFT_BLUE,  "/stop"   },
};
const int NUM_BUTTONS = sizeof(buttons) / sizeof(buttons[0]);

unsigned long lastTouchMs = 0;
const unsigned long TOUCH_DEBOUNCE_MS = 400;
bool wasTouched = false;

// --- Setup portal (pairing code custom field) ----------------------------

WiFiManagerParameter pairingParam("pairing", "Pairing Code (from desktop app)", "", 12);

void drawStatus(const char* line1, const char* line2 = "") {
  tft.fillScreen(TFT_BLACK);
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.setTextSize(2);
  tft.setCursor(10, 130);
  tft.print(line1);
  if (strlen(line2) > 0) {
    tft.setCursor(10, 160);
    tft.print(line2);
  }
}

void setupWiFi() {
  WiFiManager wm;
  wm.addParameter(&pairingParam);
  wm.setConfigPortalTimeout(300);
  wm.setAPCallback([](WiFiManager* mgr) {
    drawStatus("Setup mode", "Connect phone to: RedLight-Setup");
  });

  drawStatus("Connecting to WiFi...");
  bool connected = wm.autoConnect("RedLight-Setup");

  if (!connected) {
    drawStatus("WiFi setup timed out", "Restarting...");
    delay(3000);
    ESP.restart();
  }

  // Save pairing code if the portal was actually shown (field non-empty)
  String entered = pairingParam.getValue();
  if (entered.length() > 0) {
    prefs.putString("token", entered);
  }
  pairingToken = prefs.getString("token", "");
}

void maybeResetSettings() {
  // Hold the screen during boot to force the WiFi/pairing setup portal again.
  ts.begin(touchSPI);
  ts.setRotation(0);
  delay(50);
  if (!ts.touched()) return;

  unsigned long start = millis();
  drawStatus("Release to cancel...", "Hold to reset WiFi setup");
  while (ts.touched() && millis() - start < RESET_HOLD_MS) {
    delay(50);
  }
  if (millis() - start >= RESET_HOLD_MS) {
    drawStatus("Resetting WiFi setup...");
    WiFiManager wm;
    wm.resetSettings();
    // wm.resetSettings() alone doesn't reliably wipe ESP32's own WiFi NVS
    // credential store, so the old network gets silently reused on the
    // next boot. Explicitly erase it too (eraseap=true).
    WiFi.mode(WIFI_STA);
    WiFi.disconnect(true, true);
    delay(200);
    prefs.remove("token");
    delay(1000);
    ESP.restart();
  }
}

// --- mDNS discovery of the desktop app ------------------------------------

bool resolveServer() {
  IPAddress ip = MDNS.queryHost(MDNS_HOSTNAME, 3000);
  if (ip.toString() == "0.0.0.0") return false;
  resolvedServerIP = ip.toString();
  return true;
}

// --- UI --------------------------------------------------------------------

void drawButtons() {
  tft.fillScreen(TFT_BLACK);
  for (int i = 0; i < NUM_BUTTONS; i++) {
    Button& b = buttons[i];
    tft.fillRoundRect(b.x, b.y, b.w, b.h, 10, b.color);
    tft.drawRoundRect(b.x, b.y, b.w, b.h, 10, TFT_WHITE);
    tft.setTextColor(TFT_WHITE, b.color);
    tft.setTextSize(3);
    int textW = strlen(b.label) * 18;
    tft.setCursor(b.x + (b.w - textW) / 2, b.y + b.h / 2 - 12);
    tft.print(b.label);
  }
  tft.setTextSize(1);
  tft.setTextColor(TFT_DARKGREY, TFT_BLACK);
  tft.setCursor(20, 300);
  tft.print(WiFi.status() == WL_CONNECTED ? "Connected" : "Disconnected");
}

void flashButton(int index) {
  Button& b = buttons[index];
  tft.fillRoundRect(b.x, b.y, b.w, b.h, 10, TFT_WHITE);
  delay(120);
  tft.fillRoundRect(b.x, b.y, b.w, b.h, 10, b.color);
  tft.drawRoundRect(b.x, b.y, b.w, b.h, 10, TFT_WHITE);
  tft.setTextColor(TFT_WHITE, b.color);
  tft.setTextSize(3);
  int textW = strlen(b.label) * 18;
  tft.setCursor(b.x + (b.w - textW) / 2, b.y + b.h / 2 - 12);
  tft.print(b.label);
}

void sendCommand(const char* endpoint) {
  if (WiFi.status() != WL_CONNECTED) return;

  if (resolvedServerIP.length() == 0 || millis() - lastMdnsLookup > MDNS_REFRESH_MS) {
    if (resolveServer()) lastMdnsLookup = millis();
  }
  if (resolvedServerIP.length() == 0) {
    Serial.println("Desktop app not found on network (mDNS lookup failed)");
    return;
  }

  HTTPClient http;
  String url = "http://" + resolvedServerIP + ":" + String(SERVER_PORT) + endpoint + "?token=" + pairingToken;
  http.begin(url);
  int code = http.GET();
  Serial.printf("GET %s -> %d\n", url.c_str(), code);
  if (code <= 0) resolvedServerIP = ""; // force re-resolve next time
  http.end();
}

void setup() {
  Serial.begin(115200);
  prefs.begin("redlight", false);

  tft.init();
  tft.setRotation(0); // portrait

  touchSPI.begin(25, 39, 32, XPT2046_CS);

  maybeResetSettings();

  setupWiFi();

  if (!MDNS.begin("cyd-redlight")) {
    Serial.println("mDNS init failed");
  }

  drawButtons();
}

void loop() {
  bool isTouched = ts.touched();

  if (isTouched && !wasTouched && millis() - lastTouchMs > TOUCH_DEBOUNCE_MS) {
    TS_Point p = ts.getPoint();
    int x = map(p.x, TOUCH_MIN_X, TOUCH_MAX_X, 0, tft.width());
    int y = map(p.y, TOUCH_MIN_Y, TOUCH_MAX_Y, 0, tft.height());

    for (int i = 0; i < NUM_BUTTONS; i++) {
      Button& b = buttons[i];
      if (x >= b.x && x <= b.x + b.w && y >= b.y && y <= b.y + b.h) {
        flashButton(i);
        sendCommand(b.endpoint);
        lastTouchMs = millis();
        break;
      }
    }
  }
  wasTouched = isTouched;

  static unsigned long lastStatusUpdate = 0;
  if (millis() - lastStatusUpdate > 5000) {
    lastStatusUpdate = millis();
    tft.fillRect(0, 295, 240, 20, TFT_BLACK);
    tft.setTextColor(TFT_DARKGREY, TFT_BLACK);
    tft.setTextSize(1);
    tft.setCursor(20, 300);
    tft.print(WiFi.status() == WL_CONNECTED ? "Connected" : "Disconnected");
  }
}
