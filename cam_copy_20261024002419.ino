#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>

// ===== Wi-Fi: 2.4 GHz network/hotspot =====
// Enter your Wi-Fi password locally before uploading. Do not share it publicly.
const char* WIFI_SSID = "POCO F6";
const char* WIFI_PASS = "Deepu0627";

// ===== AI Thinker ESP32-CAM pin mapping =====
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

WebServer server(80);
bool cameraReady = false;

void handleHome() {
  server.send(200, "text/html", R"HTML(
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AgriGuardian ESP32-CAM</title>
<style>
body{font-family:Arial,sans-serif;margin:20px;background:#f3f6f1;color:#203329}
img{display:block;width:100%;max-width:640px;min-height:80px;object-fit:contain;background:#e5e9e3;border-radius:10px;margin:12px 0}
button{padding:12px 16px;margin:8px 4px 8px 0;cursor:pointer}
#status{font-weight:600}
</style>
</head>
<body>
<h2>AgriGuardian — ESP32-CAM Leaf Camera</h2>
<p>Position a leaf in front of the camera with good lighting.</p>
<img id="preview" alt="ESP32-CAM preview">
<br><button id="captureButton" onclick="capture()">Capture fresh image</button>
<p id="status">Connecting to ESP32-CAM...</p>
<img id="photo" alt="Fresh captured leaf image">
<script>
const preview=document.getElementById('preview');
const photo=document.getElementById('photo');
const statusText=document.getElementById('status');
const captureButton=document.getElementById('captureButton');
let busy=false, previewUrl=null, photoUrl=null;

async function getJpeg(){
  const response=await fetch('/capture?t='+Date.now(),{cache:'no-store'});
  if(!response.ok) throw new Error('Camera returned HTTP '+response.status);
  if(!(response.headers.get('content-type')||'').includes('image/jpeg'))
    throw new Error('Camera did not return a JPEG image');
  return await response.blob();
}
async function refreshPreview(){
  if(busy)return;
  try{
    const blob=await getJpeg();
    const url=URL.createObjectURL(blob);
    preview.src=url;
    if(previewUrl)URL.revokeObjectURL(previewUrl);
    previewUrl=url;
    statusText.textContent='ESP32-CAM connected';
  }catch(e){statusText.textContent='Preview error: '+e.message;}
}
async function capture(){
  if(busy)return;
  busy=true;captureButton.disabled=true;
  statusText.textContent='Capturing fresh image...';
  try{
    const blob=await getJpeg();
    const url=URL.createObjectURL(blob);
    photo.src=url;
    if(photoUrl)URL.revokeObjectURL(photoUrl);
    photoUrl=url;
    statusText.textContent='Fresh image captured successfully';
  }catch(e){statusText.textContent='Capture failed: '+e.message;}
  finally{busy=false;captureButton.disabled=false;}
}
refreshPreview();
setInterval(refreshPreview,1500);
</script>
</body>
</html>
)HTML");
}

void handleCapture() {
  if (!cameraReady || WiFi.status() != WL_CONNECTED) {
    server.send(503, "text/plain", "Camera unavailable");
    return;
  }

  camera_fb_t* fb = esp_camera_fb_get();
  if (fb == nullptr) {
    server.send(500, "text/plain", "Image capture failed");
    return;
  }
  if (fb->format != PIXFORMAT_JPEG) {
    esp_camera_fb_return(fb);
    server.send(500, "text/plain", "Image is not JPEG");
    return;
  }

  WiFiClient client = server.client();
  client.setNoDelay(true);
  client.print(
    "HTTP/1.1 200 OK\r\n"
    "Content-Type: image/jpeg\r\n"
    "Cache-Control: no-store, no-cache, must-revalidate\r\n"
    "Access-Control-Allow-Origin: *\r\n"
    "Connection: close\r\n"
  );
  client.printf("Content-Length: %u\r\n\r\n", static_cast<unsigned int>(fb->len));
  size_t total = fb->len;
  size_t sent = client.write(fb->buf, total);
  if (sent != total) {
    Serial.printf("JPEG send incomplete: %u/%u bytes\n",
                  static_cast<unsigned int>(sent),
                  static_cast<unsigned int>(total));
  }
  esp_camera_fb_return(fb);
  delay(1);
}

void handleStatus() {
  String json = "{";
  json += "\"camera_ready\":";
  json += cameraReady ? "true" : "false";
  json += ",\"wifi_connected\":";
  json += WiFi.status() == WL_CONNECTED ? "true" : "false";
  json += ",\"ip\":\"" + WiFi.localIP().toString() + "\"}";
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.send(200, "application/json", json);
}

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\nAgriGuardian ESP32-CAM starting");

  camera_config_t config = {};
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_VGA;
  config.jpeg_quality = 15;
  config.fb_count = 1;
  config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  config.fb_location = CAMERA_FB_IN_PSRAM;

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed: 0x%x\n", err);
    cameraReady = false;
    return;
  }
  cameraReady = true;

  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("Connecting to Wi-Fi");
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 20000) {
    delay(500);
    Serial.print(".");
  }
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("\nWi-Fi failed. Check the 2.4 GHz hotspot and credentials.");
    return;
  }

  Serial.println("\nWi-Fi connected");
  Serial.print("Camera page: http://");
  Serial.println(WiFi.localIP());

  // Snapshot preview avoids a blocking MJPEG stream handler.
  server.on("/", HTTP_GET, handleHome);
  server.on("/capture", HTTP_GET, handleCapture);
  server.on("/status", HTTP_GET, handleStatus);
  server.onNotFound([]() {
    server.send(404, "text/plain", "Not found. Use /, /capture, or /status.");
  });
  server.begin();
  Serial.println("Camera server ready");
}

void loop() {
  server.handleClient();
  delay(2);
}
