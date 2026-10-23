#include <WiFi.h>
#include <WebServer.h>
#include <HTTPClient.h>
#include <SPI.h>
#include <DHT.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <MFRC522.h>
#include <math.h>
#include <WiFiClientSecure.h>
// =============== WIFI ===============
// ESP32 supports 2.4 GHz ONLY. Set your phone hotspot band to 2.4 GHz
// (POCO F6: Hotspot settings -> AP band -> 2.4 GHz) and keep the hotspot
// screen open while the ESP32 connects.
const char* WIFI_SSID = "POCO F6";
const char* WIFI_PASS = "Deepu0627";   // <-- change this

// Keep empty until your actual server API is confirmed.
const char* TELEMETRY_URL =
    "https://fantasy-chaffing-postage.ngrok-free.dev/telemetry";

const char* TELEMETRY_KEY = "ab1156b556106ec67626b677847fff24129dd0df043342fafcca566837b3dfdd";
// =============== PIN ASSIGNMENTS ===============
#define SOIL1_PIN 34
#define SOIL2_PIN 35
#define WATER_PIN 33
#define MQ2_PIN 32

#define DHT1_PIN 4
#define DHT2_PIN 16
#define DHT_TYPE DHT22
#define DS18_PIN 13

#define PUMP_RELAY 26
#define FAN_RELAY 25

#define RFID_SS 5
#define RFID_RST 22
#define RFID_SCK 18
#define RFID_MISO 19
#define RFID_MOSI 23

// Change to false if your relay is active-HIGH.
const bool RELAY_ACTIVE_LOW = true;

// =============== OBJECTS ===============
DHT dht1(DHT1_PIN, DHT_TYPE);
DHT dht2(DHT2_PIN, DHT_TYPE);

OneWire oneWire(DS18_PIN);
DallasTemperature ds18(&oneWire);

MFRC522 rfid(RFID_SS, RFID_RST);
WebServer server(80);

// =============== CALIBRATION ===============
// Replace with values measured from YOUR sensors
// (see the /raw page: dry in air, then wet in water).
const int SOIL1_DRY = 3000;
const int SOIL1_WET = 1400;

const int SOIL2_DRY = 4095;
const int SOIL2_WET = 1400;

const int WATER_EMPTY = 330;
const int WATER_FULL = 650;

// A raw ADC value this close to the rails means a disconnected/floating
// or mis-powered sensor, NOT a real reading.
const int ADC_FAULT_HIGH = 4090;
const int ADC_FAULT_LOW = 20;

// =============== CONTROL SETTINGS ===============
const float SOIL_START = 30.0;
const float SOIL_STOP = 45.0;
const float TANK_MIN = 15.0;

const float FAN_TEMP_ON = 32.0;
const float FAN_TEMP_OFF = 29.0;

const float FAN_HUM_ON = 75.0;
const float FAN_HUM_OFF = 65.0;

const unsigned long MAX_PUMP_MS = 30000UL;
const unsigned long PUMP_COOLDOWN_MS = 60000UL;
const unsigned long SENSOR_INTERVAL_MS = 2500UL;
const unsigned long TELEMETRY_INTERVAL_MS = 30000UL;
const unsigned long WIFI_RETRY_MS = 10000UL;
const unsigned long WIFI_REPORT_MS = 10000UL;

// =============== SENSOR VALUES ===============
float soil1 = NAN;
float soil2 = NAN;
float tankPercent = NAN;

int rawSoil1 = 0;
int rawSoil2 = 0;
int rawWater = 0;

float ambientTemp = NAN;
float ambientHumidity = NAN;

float storageTempAir = NAN;
float storageHumidity = NAN;

float soilTemp = NAN;
float grainTemp = NAN;

int mq2Raw = 0;
const int MQ2_SMOKE_THRESHOLD = 850;  // Initial test value
bool smokeDetected = false;

bool pumpOn = false;
bool fanOn = false;

bool soilFault = true;
bool tankFault = true;

unsigned long pumpStarted = 0;
unsigned long lastPumpStopped = 0;
unsigned long lastSensorRead = 0;
unsigned long lastTelemetry = 0;
unsigned long lastWifiRetry = 0;
unsigned long lastWifiReport = 0;

// =============== RELAY CONTROL ===============
void relayWrite(int pin, bool on) {
  digitalWrite(
    pin,
    RELAY_ACTIVE_LOW
      ? (on ? LOW : HIGH)
      : (on ? HIGH : LOW)
  );
}

void stopPump() {
  if (pumpOn) {
    relayWrite(PUMP_RELAY, false);
    pumpOn = false;
    lastPumpStopped = millis();
    Serial.println("PUMP OFF");
  }
}

void startPump() {
  if (!pumpOn) {
    relayWrite(PUMP_RELAY, true);
    pumpOn = true;
    pumpStarted = millis();
    Serial.println("PUMP ON");
  }
}

// =============== CONVERSION ===============
// Returns NAN when the raw value looks like a wiring fault.
// lowIsFault=false for the water-level sensor, which can read ~0 when dry.
float toPercent(int raw, int dry, int wet, bool lowIsFault) {
  if (dry == wet) return NAN;
  if (raw >= ADC_FAULT_HIGH) return NAN;
  if (lowIsFault && raw <= ADC_FAULT_LOW) return NAN;

  float value = 100.0 * (raw - dry) / float(wet - dry);
  return constrain(value, 0.0, 100.0);
}

String jsonFloat(float value) {
  if (isnan(value) || isinf(value)) {
    return "null";
  }
  return String(value, 1);
}

// =============== READ SENSORS ===============
void readSensors() {
  rawSoil1 = analogRead(SOIL1_PIN);
  rawSoil2 = analogRead(SOIL2_PIN);
  rawWater = analogRead(WATER_PIN);

  soil1 = toPercent(rawSoil1, SOIL1_DRY, SOIL1_WET, true);
  soil2 = toPercent(rawSoil2, SOIL2_DRY, SOIL2_WET, true);
  tankPercent = toPercent(rawWater, WATER_EMPTY, WATER_FULL, false);

  ambientTemp = dht1.readTemperature();
  ambientHumidity = dht1.readHumidity();

  storageTempAir = dht2.readTemperature();
  storageHumidity = dht2.readHumidity();

  mq2Raw = analogRead(MQ2_PIN);
  smokeDetected = (mq2Raw >= MQ2_SMOKE_THRESHOLD);
  

  // Read the previous DS18B20 conversion.
  soilTemp = ds18.getTempCByIndex(0);
  grainTemp = ds18.getTempCByIndex(1);

  if (soilTemp == DEVICE_DISCONNECTED_C ||
      soilTemp < -55 || soilTemp > 125) {
    soilTemp = NAN;
  }

  if (grainTemp == DEVICE_DISCONNECTED_C ||
      grainTemp < -55 || grainTemp > 125) {
    grainTemp = NAN;
  }

  // Irrigation relies on both soil sensors and the tank sensor.
  soilFault = isnan(soil1) || isnan(soil2);
  tankFault = isnan(tankPercent);

  Serial.println("\n===== AGRIGUARDIAN =====");

  Serial.printf("Soil 1: %.1f %% (raw %d)\n", soil1, rawSoil1);
  Serial.printf("Soil 2: %.1f %% (raw %d)\n", soil2, rawSoil2);
  Serial.printf("Tank: %.1f %% (raw %d)\n", tankPercent, rawWater);

  Serial.printf("Ambient: %.1f C, %.1f %% RH\n",
                ambientTemp, ambientHumidity);

  Serial.printf("Storage air: %.1f C, %.1f %% RH\n",
                storageTempAir, storageHumidity);

  Serial.printf("Soil temperature: %.1f C\n", soilTemp);
  Serial.printf("Grain temperature: %.1f C\n", grainTemp);

  Serial.printf("MQ-2 ADC: %d\n", mq2Raw);
  Serial.printf("Smoke status: %s\n",
              smokeDetected ? "DETECTED" : "NOT DETECTED");

  Serial.printf("Pump: %s | Fan: %s\n",
                pumpOn ? "ON" : "OFF",
                fanOn ? "ON" : "OFF");

  // Start next non-blocking DS18B20 conversion.
  ds18.requestTemperatures();
}

// =============== IRRIGATION CONTROL ===============
void controlPump() {
  if (soilFault || tankFault) {
    stopPump();
    Serial.println("Pump locked: sensor fault");
    return;
  }

  if (tankPercent <= TANK_MIN) {
    stopPump();
    Serial.println("Pump locked: low tank level");
    return;
  }

  if (pumpOn && millis() - pumpStarted >= MAX_PUMP_MS) {
    stopPump();
    Serial.println("Maximum pump runtime reached");
    return;
  }

  // A shared pump serves both soil zones.
  // Stop only when BOTH zones reach the target.
  if (pumpOn && soil1 >= SOIL_STOP && soil2 >= SOIL_STOP) {
    stopPump();
    return;
  }

  bool anyZoneDry = soil1 <= SOIL_START || soil2 <= SOIL_START;

  if (!pumpOn && anyZoneDry &&
      millis() - lastPumpStopped >= PUMP_COOLDOWN_MS) {
    startPump();
  }
}

// =============== STORAGE FAN CONTROL ===============
void controlFan() {
  // Use the grain-storage DHT22.
  if (isnan(storageTempAir) || isnan(storageHumidity)) {
    if (fanOn) {
      fanOn = false;
      relayWrite(FAN_RELAY, false);
    }
    Serial.println("Fan OFF: storage DHT22 fault");
    return;
  }

  bool highCondition =
      storageTempAir >= FAN_TEMP_ON ||
      storageHumidity >= FAN_HUM_ON;

  bool normalCondition =
      storageTempAir <= FAN_TEMP_OFF &&
      storageHumidity <= FAN_HUM_OFF;

  if (!fanOn && highCondition) {
    fanOn = true;
    relayWrite(FAN_RELAY, true);
    Serial.println("Storage fan ON");
  } else if (fanOn && normalCondition) {
    fanOn = false;
    relayWrite(FAN_RELAY, false);
    Serial.println("Storage fan OFF");
  }
}

// =============== RFID CLOUD REPORTING ===============
void sendRfidScan(const String& uid) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[RFID] Not sent: Wi-Fi is disconnected");
    return;
  }

  if (strlen(TELEMETRY_URL) == 0) {
    Serial.println("[RFID] Not sent: TELEMETRY_URL is empty");
    return;
  }

  // Reuse the telemetry server URL and API key.
  // Example: https://your-host/telemetry -> https://your-host/rfid-scan
  String scanUrl = String(TELEMETRY_URL);
  if (scanUrl.endsWith("/telemetry")) {
    scanUrl.remove(scanUrl.length() - String("/telemetry").length());
  }
  scanUrl += "/rfid-scan";

  WiFiClientSecure client;

  // Prototype only: skips certificate verification.
  // Configure CA certificate validation before production use.
  client.setInsecure();

  HTTPClient http;
  http.setTimeout(10000);

  Serial.print("[RFID] Sending UID to: ");
  Serial.println(scanUrl);

  if (!http.begin(client, scanUrl)) {
    Serial.println("[RFID] HTTPS begin failed");
    return;
  }

  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-API-Key", TELEMETRY_KEY);

  // RFID UIDs are hexadecimal characters, so no JSON escaping is needed.
  String payload = "{\"uid\":\"" + uid +
                   "\",\"scan_id\":\"esp32-" +
                   String((uint32_t)millis()) + "\"}";

  int result = http.POST(payload);

  Serial.printf("[RFID] HTTP status: %d\n", result);
  if (result > 0) {
    String response = http.getString();
    Serial.print("[RFID] Server response: ");
    Serial.println(response);

    if (result >= 200 && result < 300) {
      Serial.println("[RFID] Scan accepted by server");
    } else {
      Serial.println("[RFID] Server did not accept the scan; check API key/endpoint");
    }
  } else {
    Serial.printf("[RFID] Request failed: %s\n",
                  http.errorToString(result).c_str());
  }

  http.end();
}

// =============== RFID LIVESTOCK IDENTIFICATION ===============


void checkRFID() {
  if (!rfid.PICC_IsNewCardPresent()) return;
  if (!rfid.PICC_ReadCardSerial()) return;

  String uid = "";

  for (byte i = 0; i < rfid.uid.size; i++) {
    if (rfid.uid.uidByte[i] < 0x10) {
      uid += "0";
    }
    uid += String(rfid.uid.uidByte[i], HEX);
  }

  uid.toUpperCase();

  Serial.println("\n===== RFID SCAN =====");
  Serial.print("Tag UID: ");
  Serial.println(uid);
  // Send this UID to the AgriGuardian AWS livestock scan endpoint.
  sendRfidScan(uid);

  Serial.println("Associate this UID with an animal record.");

  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
}

// =============== LOCAL WEB API ===============
String buildStatusJson(bool forTelemetry) {
  String j = "{";

  if (forTelemetry) {
    j += "\"device_id\":\"agriguardian-esp32-01\",";
  }

  j += "\"soil1_percent\":" + jsonFloat(soil1) + ",";
  j += "\"soil2_percent\":" + jsonFloat(soil2) + ",";
  j += "\"tank_percent\":" + jsonFloat(tankPercent) + ",";

  j += "\"ambient_temp_c\":" + jsonFloat(ambientTemp) + ",";
  j += "\"ambient_humidity\":" + jsonFloat(ambientHumidity) + ",";

  j += "\"storage_air_temp_c\":" + jsonFloat(storageTempAir) + ",";
  j += "\"storage_humidity\":" + jsonFloat(storageHumidity) + ",";

  j += "\"soil_temp_c\":" + jsonFloat(soilTemp) + ",";
  j += "\"grain_temp_c\":" + jsonFloat(grainTemp) + ",";

  j += "\"mq2_raw\":" + String(mq2Raw) + ",";
  j += "\"pump_on\":" + String(pumpOn ? "true" : "false") + ",";
  j += "\"fan_on\":" + String(fanOn ? "true" : "false") + ",";
  j += "\"soil_fault\":" + String(soilFault ? "true" : "false") + ",";
  j += "\"tank_fault\":" + String(tankFault ? "true" : "false");
  j += ",\"smoke_detected\":";
j += (smokeDetected ? "true" : "false");

  j += "}";
  return j;
}

void handleStatus() {
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.send(200, "application/json", buildStatusJson(false));
}

// Raw ADC values + millivolts, for calibration.
void handleRaw() {
  String j = "{";
  j += "\"soil1_raw\":" + String(analogRead(SOIL1_PIN)) + ",";
  j += "\"soil1_mv\":" + String(analogReadMilliVolts(SOIL1_PIN)) + ",";
  j += "\"soil2_raw\":" + String(analogRead(SOIL2_PIN)) + ",";
  j += "\"soil2_mv\":" + String(analogReadMilliVolts(SOIL2_PIN)) + ",";
  j += "\"tank_raw\":" + String(analogRead(WATER_PIN)) + ",";
  j += "\"tank_mv\":" + String(analogReadMilliVolts(WATER_PIN)) + ",";
  j += "\"mq2_raw\":" + String(analogRead(MQ2_PIN));
  j += "}";
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.send(200, "application/json", j);
}

// Simple visual dashboard that polls /status every 3 seconds.
const char DASH_HTML[] PROGMEM = R"HTML(
<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AgriGuardian</title>
<style>
body{font-family:system-ui,sans-serif;margin:0;background:#f3f6f1;color:#1d2b1d}
h1{margin:0;padding:16px;background:#2e6b34;color:#fff;font-size:20px}
.g{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:12px;padding:12px}
.c{background:#fff;border-radius:10px;padding:12px;box-shadow:0 1px 3px #0002}
.c small{color:#667}.c b{display:block;font-size:24px;margin-top:4px}
.on{color:#1a7f37}.off{color:#888}.bad{color:#c62828}
</style></head><body>
<h1>AgriGuardian</h1><div class="g" id="g"></div>
<script>
const L=[["soil1_percent","Soil 1","%"],["soil2_percent","Soil 2","%"],
["tank_percent","Water tank","%"],["ambient_temp_c","Ambient temp"," C"],
["ambient_humidity","Ambient humidity","%"],["storage_air_temp_c","Storage temp"," C"],
["storage_humidity","Storage humidity","%"],["soil_temp_c","Soil temp"," C"],
["grain_temp_c","Grain temp"," C"],["mq2_raw","MQ-2 (raw)",""]];
const B=[["pump_on","Pump"],["fan_on","Fan"],["soil_fault","Soil sensor fault"],["tank_fault","Tank sensor fault"]];
async function u(){
 try{
  const d=await (await fetch('/status')).json();
  let h='';
  for(const [k,n,s] of L){const v=d[k];h+=`<div class="c"><small>${n}</small><b>${v===null?'--':v+s}</b></div>`;}
  for(const [k,n] of B){const v=d[k];const f=k.includes('fault');
   h+=`<div class="c"><small>${n}</small><b class="${v?(f?'bad':'on'):'off'}">${f?(v?'FAULT':'OK'):(v?'ON':'OFF')}</b></div>`;}
  document.getElementById('g').innerHTML=h;
 }catch(e){document.getElementById('g').innerHTML='<div class="c bad">Connection lost</div>';}
}
u();setInterval(u,3000);
</script></body></html>
)HTML";

void handleRoot() {
  server.send_P(200, "text/html", DASH_HTML);
}

// =============== OPTIONAL MCP TELEMETRY ===============

void sendTelemetry() {
  if (strlen(TELEMETRY_URL) == 0) return;
  if (WiFi.status() != WL_CONNECTED) return;

  WiFiClientSecure client;

  // Temporary prototype setting only:
  // disables HTTPS certificate verification.
  // Replace with CA certificate validation before production use.
  client.setInsecure();

  HTTPClient http;
  http.setTimeout(10000);

  if (!http.begin(client, TELEMETRY_URL)) {
    Serial.println("Telemetry: HTTPS begin failed");
    return;
  }

  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-API-Key", TELEMETRY_KEY);

  String payload = buildStatusJson(true);
  int result = http.POST(payload);

  Serial.printf("Telemetry HTTP status: %d\n", result);

  if (result > 0) {
    Serial.println(http.getString());
  } else {
    Serial.printf("Telemetry error: %s\n",
                  http.errorToString(result).c_str());
  }

  http.end();
}

// =============== WIFI HELPERS ===============
void onWifiEvent(WiFiEvent_t event, WiFiEventInfo_t info) {
  switch (event) {
    case ARDUINO_EVENT_WIFI_STA_CONNECTED:
      Serial.println("[WiFi] Associated with access point");
      break;
    case ARDUINO_EVENT_WIFI_STA_GOT_IP:
      Serial.print("[WiFi] Got IP: ");
      Serial.println(WiFi.localIP());
      break;
    case ARDUINO_EVENT_WIFI_STA_DISCONNECTED:
      // Reason 201 = SSID not found (often 5 GHz hotspot or out of range)
      // Reason 15 / 202 / 204 = wrong password / auth failure
      Serial.printf("[WiFi] Disconnected, reason code: %d\n",
                    info.wifi_sta_disconnected.reason);
      break;
    default:
      break;
  }
}

void connectWifi() {
  WiFi.disconnect(true, true);
  delay(200);
  WiFi.mode(WIFI_STA);
  WiFi.persistent(false);
  WiFi.setAutoReconnect(true);
  WiFi.setSleep(false);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
}

// =============== SETUP ===============
void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\n\nAgriGuardian booting...");

  analogReadResolution(12);

  // Set inactive relay levels before enabling outputs.
  digitalWrite(PUMP_RELAY, RELAY_ACTIVE_LOW ? HIGH : LOW);
  digitalWrite(FAN_RELAY, RELAY_ACTIVE_LOW ? HIGH : LOW);

  pinMode(PUMP_RELAY, OUTPUT);
  pinMode(FAN_RELAY, OUTPUT);

  relayWrite(PUMP_RELAY, false);
  relayWrite(FAN_RELAY, false);

  dht1.begin();
  dht2.begin();

  ds18.begin();
  ds18.setWaitForConversion(false);
  ds18.requestTemperatures();

  // RC522 uses the ESP32 VSPI pins defined above.
  SPI.begin(RFID_SCK, RFID_MISO, RFID_MOSI, RFID_SS);
  rfid.PCD_Init();
  Serial.println("RC522 initialized");

  WiFi.onEvent(onWifiEvent);
  connectWifi();

  Serial.print("Connecting to Wi-Fi");
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 20000UL) {
    delay(250);
    Serial.print(".");
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWi-Fi connected");
    Serial.print("ESP32 IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nWi-Fi unavailable; local control continues, will keep retrying");
  }

  server.on("/", HTTP_GET, handleRoot);
  server.on("/status", HTTP_GET, handleStatus);
  server.on("/raw", HTTP_GET, handleRaw);
  server.begin();

  lastPumpStopped = millis() - PUMP_COOLDOWN_MS;

  Serial.println("AgriGuardian system ready");
}

// =============== MAIN LOOP ===============
void loop() {
  server.handleClient();
  checkRFID();

  unsigned long now = millis();

  // Independent pump runtime protection.
  if (pumpOn && now - pumpStarted >= MAX_PUMP_MS) {
    stopPump();
    Serial.println("Pump safety timeout");
  }

  if (now - lastSensorRead >= SENSOR_INTERVAL_MS) {
    lastSensorRead = now;

    readSensors();
    controlPump();
    controlFan();
  }

  // Non-blocking Wi-Fi retry + periodic IP report.
  if (WiFi.status() != WL_CONNECTED) {
    if (now - lastWifiRetry >= WIFI_RETRY_MS) {
      lastWifiRetry = now;
      Serial.println("Wi-Fi not connected, retrying...");
      connectWifi();
    }
  }

  if (now - lastWifiReport >= WIFI_REPORT_MS) {
    lastWifiReport = now;
    if (WiFi.status() == WL_CONNECTED) {
      Serial.print("Dashboard: http://");
      Serial.println(WiFi.localIP());
    }
  }

  if (now - lastTelemetry >= TELEMETRY_INTERVAL_MS) {
    lastTelemetry = now;
    sendTelemetry();
  }

  delay(5);
}
