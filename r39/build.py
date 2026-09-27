from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import textwrap
import unittest
import zipfile
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out"
MODEL = OUT / "model"
SITE = OUT / "site"
PRINT_STL = MODEL / "PRINT_STL"
DOCS = MODEL / "DOCS"
FIRMWARE = MODEL / "FIRMWARE_R39"
PRINT_DOCS = MODEL / "PRINT_RELEASE_R39"
SOURCE = MODEL / "SOURCE_R39"
SITE_ASSETS = SITE / "assets" / "r39"
SITE_DOWNLOADS = SITE / "downloads"

RELEASE = "R39"
MODEL_ZIP_NAME = "IRON_KIDS_K2_COMMISSIONING_R39.zip"
BUILD_ENVELOPE = np.array([220.0, 220.0, 240.0])

for p in [FIRMWARE, PRINT_DOCS, SOURCE, SITE_ASSETS, SITE_DOWNLOADS]:
    p.mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run(cmd: list[str], cwd: Path | None = None) -> None:
    subprocess.run(cmd, check=True, cwd=str(cwd) if cwd else None)


PROTOCOL_H = r'''#pragma once
#include <Arduino.h>

namespace ik {

enum FaultFlags : uint16_t {
  FAULT_NONE = 0,
  FAULT_SENSOR_MISSING = 1 << 0,
  FAULT_SENSOR_STALE = 1 << 1,
  FAULT_OVER_TEMP = 1 << 2,
  FAULT_LOW_POWER = 1 << 3,
};

struct Telemetry {
  const char* role;
  uint32_t boot_id;
  uint32_t sequence;
  uint32_t uptime_ms;
  int16_t temperature_c_x100;
  uint16_t humidity_pct_x100;
  uint16_t supply_mv;
  uint16_t fault_flags;
};

inline uint16_t crc16(const uint8_t* data, size_t len) {
  uint16_t crc = 0xFFFF;
  for (size_t i = 0; i < len; ++i) {
    crc ^= static_cast<uint16_t>(data[i]) << 8;
    for (uint8_t bit = 0; bit < 8; ++bit) {
      crc = (crc & 0x8000) ? static_cast<uint16_t>((crc << 1) ^ 0x1021) : static_cast<uint16_t>(crc << 1);
    }
  }
  return crc;
}

inline uint16_t canonicalCrc(const Telemetry& t) {
  char canonical[196];
  const int count = snprintf(
      canonical, sizeof(canonical),
      "1|%s|%lu|%lu|%lu|%d|%u|%u|%u",
      t.role,
      static_cast<unsigned long>(t.boot_id),
      static_cast<unsigned long>(t.sequence),
      static_cast<unsigned long>(t.uptime_ms),
      static_cast<int>(t.temperature_c_x100),
      static_cast<unsigned int>(t.humidity_pct_x100),
      static_cast<unsigned int>(t.supply_mv),
      static_cast<unsigned int>(t.fault_flags));
  if (count <= 0) return 0;
  return crc16(reinterpret_cast<const uint8_t*>(canonical), static_cast<size_t>(count));
}

inline void emitJson(HardwareSerial& out, const Telemetry& t) {
  const uint16_t crc = canonicalCrc(t);
  out.printf(
      "{\"v\":1,\"role\":\"%s\",\"boot_id\":%lu,\"sequence\":%lu,"
      "\"uptime_ms\":%lu,\"temperature_c_x100\":%d,\"humidity_pct_x100\":%u,"
      "\"supply_mv\":%u,\"fault_flags\":%u,\"crc16\":%u}\n",
      t.role,
      static_cast<unsigned long>(t.boot_id),
      static_cast<unsigned long>(t.sequence),
      static_cast<unsigned long>(t.uptime_ms),
      static_cast<int>(t.temperature_c_x100),
      static_cast<unsigned int>(t.humidity_pct_x100),
      static_cast<unsigned int>(t.supply_mv),
      static_cast<unsigned int>(t.fault_flags),
      static_cast<unsigned int>(crc));
}

}  // namespace ik
'''

CHEST_CPP = r'''#include <Arduino.h>
#include <Wire.h>
#include <ESP8266WiFi.h>
#include <U8g2lib.h>
#include <Adafruit_AHTX0.h>
#include <Adafruit_INA219.h>
#include <Adafruit_NeoPixel.h>
#include <IKProtocol.h>

constexpr uint8_t PIN_SDA = D2;      // GPIO4
constexpr uint8_t PIN_SCL = D1;      // GPIO5
constexpr uint8_t PIN_LED = D5;      // GPIO14 through a current-limited 5 V branch
constexpr uint8_t PIN_HAPTIC = D6;   // GPIO12 through a MOSFET
constexpr uint8_t PIN_MENU = D7;     // GPIO13, internal pull-up
constexpr uint8_t PIN_SELECT = D0;   // GPIO16, EXTERNAL pull-up required
constexpr uint8_t PIXEL_COUNT = 1;
constexpr int16_t TEMP_INVALID = -32768;
constexpr uint16_t VALUE_INVALID = 65535;

U8G2_SSD1306_128X64_NONAME_F_HW_I2C display(U8G2_R0, U8X8_PIN_NONE);
Adafruit_AHTX0 aht;
Adafruit_INA219 ina219;
Adafruit_NeoPixel pixel(PIXEL_COUNT, PIN_LED, NEO_GRB + NEO_KHZ800);

bool ahtPresent = false;
bool inaPresent = false;
uint8_t page = 0;
uint32_t bootId = 0;
uint32_t sequenceNumber = 0;
uint32_t lastSensorMs = 0;
uint32_t lastTelemetryMs = 0;
uint32_t lastDisplayMs = 0;
uint32_t hapticUntilMs = 0;
int16_t tempX100 = TEMP_INVALID;
uint16_t humidityX100 = VALUE_INVALID;
uint16_t supplyMv = VALUE_INVALID;
uint16_t faults = ik::FAULT_NONE;
bool lastMenu = true;
bool lastSelect = true;

void setPixel(uint8_t r, uint8_t g, uint8_t b) {
  pixel.setPixelColor(0, pixel.Color(r, g, b));
  pixel.show();
}

void pulseHaptic(uint16_t milliseconds) {
  digitalWrite(PIN_HAPTIC, HIGH);
  hapticUntilMs = millis() + milliseconds;
}

void readSensors() {
  faults &= static_cast<uint16_t>(~(ik::FAULT_SENSOR_MISSING | ik::FAULT_SENSOR_STALE | ik::FAULT_OVER_TEMP | ik::FAULT_LOW_POWER));
  bool valid = false;
  if (ahtPresent) {
    sensors_event_t humidityEvent;
    sensors_event_t tempEvent;
    aht.getEvent(&humidityEvent, &tempEvent);
    if (isfinite(tempEvent.temperature) && isfinite(humidityEvent.relative_humidity)) {
      tempX100 = static_cast<int16_t>(lroundf(tempEvent.temperature * 100.0f));
      humidityX100 = static_cast<uint16_t>(constrain(lroundf(humidityEvent.relative_humidity * 100.0f), 0L, 10000L));
      valid = true;
      if (tempX100 >= 3200) faults |= ik::FAULT_OVER_TEMP;
    }
  }
  if (!ahtPresent) faults |= ik::FAULT_SENSOR_MISSING;
  if (!valid) {
    tempX100 = TEMP_INVALID;
    humidityX100 = VALUE_INVALID;
  } else {
    lastSensorMs = millis();
  }

  if (inaPresent) {
    const float busVoltage = ina219.getBusVoltage_V();
    if (isfinite(busVoltage) && busVoltage > 0.0f) {
      supplyMv = static_cast<uint16_t>(constrain(lroundf(busVoltage * 1000.0f), 0L, 65534L));
      if (supplyMv < 4600) faults |= ik::FAULT_LOW_POWER;
    } else {
      supplyMv = VALUE_INVALID;
    }
  } else {
    supplyMv = VALUE_INVALID;
  }
}

void drawValue(const char* label, const char* value, int y) {
  display.setFont(u8g2_font_6x12_tf);
  display.drawStr(0, y, label);
  display.drawStr(56, y, value);
}

void renderDisplay() {
  display.clearBuffer();
  display.setFont(u8g2_font_7x13B_tf);
  display.drawStr(0, 12, "IRON-KIDS R39");
  char value[32];
  if (page == 0) {
    display.setFont(u8g2_font_6x12_tf);
    display.drawStr(0, 27, "CHEST / LOCAL MODE");
    if (tempX100 != TEMP_INVALID) snprintf(value, sizeof(value), "%d.%02d C", tempX100 / 100, abs(tempX100 % 100));
    else snprintf(value, sizeof(value), "N/A");
    drawValue("TEMP", value, 42);
    if (humidityX100 != VALUE_INVALID) snprintf(value, sizeof(value), "%u.%02u %%", humidityX100 / 100, humidityX100 % 100);
    else snprintf(value, sizeof(value), "N/A");
    drawValue("HUM", value, 57);
  } else if (page == 1) {
    display.setFont(u8g2_font_6x12_tf);
    display.drawStr(0, 27, "POWER / HEALTH");
    if (supplyMv != VALUE_INVALID) snprintf(value, sizeof(value), "%u mV", supplyMv);
    else snprintf(value, sizeof(value), "USB / N.A.");
    drawValue("BUS", value, 42);
    snprintf(value, sizeof(value), "0x%04X", faults);
    drawValue("FLAGS", value, 57);
  } else {
    display.setFont(u8g2_font_6x12_tf);
    display.drawStr(0, 29, "EFFECTS ONLY");
    display.drawStr(0, 44, "NO FIT / LATCH");
    display.drawStr(0, 59, "OR RELEASE CONTROL");
  }
  display.sendBuffer();
}

void emitTelemetry() {
  ik::Telemetry packet{
      "chest",
      bootId,
      ++sequenceNumber,
      millis(),
      tempX100,
      humidityX100,
      supplyMv,
      faults};
  ik::emitJson(Serial, packet);
}

void handleButtons() {
  const bool menuNow = digitalRead(PIN_MENU);
  const bool selectNow = digitalRead(PIN_SELECT);
  if (lastMenu && !menuNow) {
    page = static_cast<uint8_t>((page + 1) % 3);
    pulseHaptic(45);
  }
  if (lastSelect && !selectNow) {
    pulseHaptic(80);
    setPixel(0, 12, 26);
  }
  lastMenu = menuNow;
  lastSelect = selectNow;
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_HAPTIC, OUTPUT);
  pinMode(PIN_MENU, INPUT_PULLUP);
  pinMode(PIN_SELECT, INPUT);  // External pull-up required on D0/GPIO16.
  digitalWrite(PIN_HAPTIC, LOW);
  WiFi.persistent(false);
  WiFi.mode(WIFI_OFF);
  WiFi.forceSleepBegin();
  delay(1);

  Wire.begin(PIN_SDA, PIN_SCL);
  display.begin();
  display.setContrast(92);
  ahtPresent = aht.begin(&Wire);
  inaPresent = ina219.begin(&Wire);
  pixel.begin();
  pixel.setBrightness(24);
  setPixel(18, 6, 0);

  bootId = ESP.getChipId() ^ micros() ^ static_cast<uint32_t>(analogRead(A0));
  readSensors();
  renderDisplay();
}

void loop() {
  const uint32_t now = millis();
  handleButtons();
  if (hapticUntilMs && static_cast<int32_t>(now - hapticUntilMs) >= 0) {
    digitalWrite(PIN_HAPTIC, LOW);
    hapticUntilMs = 0;
    if (faults) setPixel(24, 0, 0);
    else setPixel(0, 16, 22);
  }
  if (now - lastSensorMs >= 1000) readSensors();
  if (ahtPresent && now - lastSensorMs > 3000) faults |= ik::FAULT_SENSOR_STALE;
  if (now - lastDisplayMs >= 125) {
    lastDisplayMs = now;
    renderDisplay();
  }
  if (now - lastTelemetryMs >= 1000) {
    lastTelemetryMs = now;
    emitTelemetry();
  }
  delay(5);
}
'''

FOREARM_CPP = r'''#include <Arduino.h>
#include <Wire.h>
#include <ESP8266WiFi.h>
#include <U8g2lib.h>
#include <Adafruit_NeoPixel.h>
#include <IKProtocol.h>

#ifndef IK_ROLE
#define IK_ROLE "forearm"
#endif

constexpr uint8_t PIN_SDA = D2;
constexpr uint8_t PIN_SCL = D1;
constexpr uint8_t PIN_LED = D5;
constexpr uint8_t PIN_MENU = D7;
constexpr uint8_t PIN_SELECT = D0;  // External pull-up required.
constexpr int16_t TEMP_INVALID = -32768;
constexpr uint16_t VALUE_INVALID = 65535;

U8G2_SSD1306_128X64_NONAME_F_HW_I2C display(U8G2_R0, U8X8_PIN_NONE);
Adafruit_NeoPixel pixel(1, PIN_LED, NEO_GRB + NEO_KHZ800);
uint32_t bootId = 0;
uint32_t sequenceNumber = 0;
uint32_t lastTelemetryMs = 0;
uint32_t lastDisplayMs = 0;
uint8_t page = 0;
bool lastMenu = true;
bool lastSelect = true;

void renderDisplay() {
  display.clearBuffer();
  display.setFont(u8g2_font_7x13B_tf);
  display.drawStr(0, 12, "IRON-KIDS R39");
  display.setFont(u8g2_font_6x12_tf);
  if (page == 0) {
    display.drawStr(0, 30, IK_ROLE);
    display.drawStr(0, 46, "LOCAL STATUS POD");
    display.drawStr(0, 61, "LINK OPTIONAL");
  } else {
    display.drawStr(0, 30, "EFFECTS ONLY");
    display.drawStr(0, 46, "NO PHYSICAL");
    display.drawStr(0, 61, "AUTHORITY");
  }
  display.sendBuffer();
}

void emitTelemetry() {
  ik::Telemetry packet{
      IK_ROLE,
      bootId,
      ++sequenceNumber,
      millis(),
      TEMP_INVALID,
      VALUE_INVALID,
      VALUE_INVALID,
      ik::FAULT_NONE};
  ik::emitJson(Serial, packet);
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_MENU, INPUT_PULLUP);
  pinMode(PIN_SELECT, INPUT);
  WiFi.persistent(false);
  WiFi.mode(WIFI_OFF);
  WiFi.forceSleepBegin();
  delay(1);
  Wire.begin(PIN_SDA, PIN_SCL);
  display.begin();
  display.setContrast(88);
  pixel.begin();
  pixel.setBrightness(18);
  pixel.setPixelColor(0, pixel.Color(0, 12, 20));
  pixel.show();
  bootId = ESP.getChipId() ^ micros() ^ static_cast<uint32_t>(analogRead(A0));
  renderDisplay();
}

void loop() {
  const uint32_t now = millis();
  const bool menuNow = digitalRead(PIN_MENU);
  const bool selectNow = digitalRead(PIN_SELECT);
  if (lastMenu && !menuNow) page = static_cast<uint8_t>((page + 1) % 2);
  if (lastSelect && !selectNow) {
    pixel.setPixelColor(0, pixel.Color(0, 24, 30));
    pixel.show();
  }
  lastMenu = menuNow;
  lastSelect = selectNow;
  if (now - lastDisplayMs >= 150) {
    lastDisplayMs = now;
    renderDisplay();
  }
  if (now - lastTelemetryMs >= 1000) {
    lastTelemetryMs = now;
    emitTelemetry();
  }
  delay(5);
}
'''

PLATFORMIO_CHEST = r'''[platformio]
default_envs = nodemcuv2

[env:nodemcuv2]
platform = espressif8266@4.2.1
board = nodemcuv2
framework = arduino
monitor_speed = 115200
lib_deps =
  olikraus/U8g2@^2.36.12
  adafruit/Adafruit AHTX0@^2.0.5
  adafruit/Adafruit INA219@^1.2.3
  adafruit/Adafruit NeoPixel@^1.12.3
build_flags =
  -D PIO_FRAMEWORK_ARDUINO_LWIP2_LOW_MEMORY
'''

PLATFORMIO_ARM = r'''[platformio]
default_envs = nodemcuv2

[env:nodemcuv2]
platform = espressif8266@4.2.1
board = nodemcuv2
framework = arduino
monitor_speed = 115200
lib_deps =
  olikraus/U8g2@^2.36.12
  adafruit/Adafruit NeoPixel@^1.12.3
build_flags =
  -D PIO_FRAMEWORK_ARDUINO_LWIP2_LOW_MEMORY
  -D IK_ROLE=\"forearm\"
'''

SUPERVISOR_PY = r'''from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

REQUIRED = {
    "v", "role", "boot_id", "sequence", "uptime_ms",
    "temperature_c_x100", "humidity_pct_x100", "supply_mv",
    "fault_flags", "crc16",
}


def crc16(data: bytes) -> int:
    crc = 0xFFFF
    for value in data:
        crc ^= value << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def canonical(packet: dict[str, Any]) -> bytes:
    return (
        f"1|{packet['role']}|{packet['boot_id']}|{packet['sequence']}|{packet['uptime_ms']}|"
        f"{packet['temperature_c_x100']}|{packet['humidity_pct_x100']}|"
        f"{packet['supply_mv']}|{packet['fault_flags']}"
    ).encode("ascii")


def validate_packet(packet: dict[str, Any]) -> None:
    missing = REQUIRED.difference(packet)
    if missing:
        raise ValueError(f"missing fields: {sorted(missing)}")
    if packet["v"] != 1:
        raise ValueError("unsupported protocol version")
    if not isinstance(packet["role"], str) or not packet["role"]:
        raise ValueError("invalid role")
    expected = crc16(canonical(packet))
    if int(packet["crc16"]) != expected:
        raise ValueError("crc mismatch")


@dataclass
class NodeState:
    role: str
    boot_id: int
    sequence: int
    last_seen: float
    packet: dict[str, Any]


class Supervisor:
    """Read-only status supervisor. It intentionally exposes no actuator commands."""

    def __init__(self, stale_after: float = 2.5) -> None:
        self.stale_after = stale_after
        self.nodes: dict[str, NodeState] = {}
        self.rejected_packets = 0

    def ingest(self, packet: dict[str, Any], now: float | None = None) -> bool:
        validate_packet(packet)
        now = time.monotonic() if now is None else now
        role = packet["role"]
        current = self.nodes.get(role)
        if current is not None and packet["boot_id"] == current.boot_id and packet["sequence"] <= current.sequence:
            self.rejected_packets += 1
            return False
        self.nodes[role] = NodeState(
            role=role,
            boot_id=int(packet["boot_id"]),
            sequence=int(packet["sequence"]),
            last_seen=now,
            packet=dict(packet),
        )
        return True

    def ingest_line(self, line: str, now: float | None = None) -> bool:
        return self.ingest(json.loads(line), now=now)

    def status(self, now: float | None = None) -> dict[str, str]:
        now = time.monotonic() if now is None else now
        result: dict[str, str] = {}
        for role, node in self.nodes.items():
            if now - node.last_seen > self.stale_after:
                result[role] = "STALE"
            elif int(node.packet["fault_flags"]):
                result[role] = "FAULT"
            else:
                result[role] = "LOCAL"
        return result
'''

SUPERVISOR_TESTS = r'''from __future__ import annotations

import json
import unittest

from ik_supervisor import Supervisor, canonical, crc16, validate_packet


def packet(role="chest", boot=11, seq=1, uptime=1000, flags=0):
    value = {
        "v": 1,
        "role": role,
        "boot_id": boot,
        "sequence": seq,
        "uptime_ms": uptime,
        "temperature_c_x100": 2450,
        "humidity_pct_x100": 5000,
        "supply_mv": 5010,
        "fault_flags": flags,
        "crc16": 0,
    }
    value["crc16"] = crc16(canonical(value))
    return value


class SupervisorTests(unittest.TestCase):
    def test_crc_validation(self):
        validate_packet(packet())
        bad = packet()
        bad["supply_mv"] = 4200
        with self.assertRaises(ValueError):
            validate_packet(bad)

    def test_same_session_replay_rejected(self):
        supervisor = Supervisor()
        self.assertTrue(supervisor.ingest(packet(seq=5), now=1.0))
        self.assertFalse(supervisor.ingest(packet(seq=4), now=1.1))
        self.assertEqual(supervisor.nodes["chest"].sequence, 5)

    def test_reboot_sequence_reset_accepted(self):
        supervisor = Supervisor()
        self.assertTrue(supervisor.ingest(packet(boot=10, seq=1000), now=1.0))
        self.assertTrue(supervisor.ingest(packet(boot=12, seq=1), now=1.1))
        self.assertEqual(supervisor.nodes["chest"].boot_id, 12)
        self.assertEqual(supervisor.nodes["chest"].sequence, 1)

    def test_stale_and_fault_states(self):
        supervisor = Supervisor(stale_after=2.5)
        supervisor.ingest(packet(flags=0), now=10.0)
        self.assertEqual(supervisor.status(now=11.0)["chest"], "LOCAL")
        self.assertEqual(supervisor.status(now=13.0)["chest"], "STALE")
        supervisor.ingest(packet(seq=2, flags=4), now=14.0)
        self.assertEqual(supervisor.status(now=14.1)["chest"], "FAULT")

    def test_json_line(self):
        supervisor = Supervisor()
        self.assertTrue(supervisor.ingest_line(json.dumps(packet()), now=1.0))


if __name__ == "__main__":
    unittest.main()
'''

SERIAL_MONITOR = r'''from __future__ import annotations

import argparse
import json
import sys
import time

from ik_supervisor import Supervisor


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only IRON-KIDS R39 serial status monitor")
    parser.add_argument("port")
    parser.add_argument("--baud", type=int, default=115200)
    args = parser.parse_args()
    try:
        import serial
    except ImportError:
        print("Install pyserial: python -m pip install pyserial", file=sys.stderr)
        return 2

    supervisor = Supervisor()
    with serial.Serial(args.port, args.baud, timeout=1) as link:
        while True:
            raw = link.readline().decode("utf-8", errors="replace").strip()
            if not raw:
                continue
            try:
                supervisor.ingest_line(raw)
            except Exception as exc:
                print(f"REJECTED: {exc}: {raw}")
                continue
            print(json.dumps(supervisor.status(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def write_firmware() -> None:
    shared = FIRMWARE / "shared" / "IKProtocol.h"
    write(shared, PROTOCOL_H)
    for project, source, ini in (
        ("chest", CHEST_CPP, PLATFORMIO_CHEST),
        ("forearm", FOREARM_CPP, PLATFORMIO_ARM),
    ):
        root = FIRMWARE / project
        write(root / "platformio.ini", ini)
        write(root / "src" / "main.cpp", source)
        write(root / "lib" / "IKProtocol" / "src" / "IKProtocol.h", PROTOCOL_H)
    write(FIRMWARE / "supervisor" / "ik_supervisor.py", SUPERVISOR_PY)
    write(FIRMWARE / "supervisor" / "test_supervisor.py", SUPERVISOR_TESTS)
    write(FIRMWARE / "supervisor" / "serial_monitor.py", SERIAL_MONITOR)
    write(FIRMWARE / "supervisor" / "requirements.txt", "pyserial==3.5\n")
    write(FIRMWARE / "README.md", """# IRON-KIDS R39 electronics firmware\n\nTwo independently compilable PlatformIO projects target the common NodeMCU ESP-12E/ESP-12F development-board family. The chest project drives a 128x64 SSD1306 OLED, optional AHT20 and INA219 sensors, one current-limited NeoPixel, two buttons, and a MOSFET-driven haptic output. The forearm project drives the OLED, local buttons, and one status pixel.\n\nWi-Fi is disabled by default. Both nodes emit CRC-protected newline-delimited JSON over USB serial. The Python supervisor accepts a sequence reset only when `boot_id` changes, fixing the stale-after-reboot failure identified in the R35 audit.\n\nThe protocol intentionally has no actuator command, latch command, fit command, or release command. These modules cannot restrain the wearer.\n\n## Pin allocation\n\n- D2 / GPIO4: I2C SDA\n- D1 / GPIO5: I2C SCL\n- D5 / GPIO14: current-limited addressable-light data\n- D6 / GPIO12: haptic MOSFET gate, chest only\n- D7 / GPIO13: menu button, internal pull-up\n- D0 / GPIO16: select button, **external pull-up required**\n\nAvoid ordinary controls on GPIO0, GPIO2, and GPIO15 because they participate in ESP8266 boot selection.\n")


def profile_for(name: str, material: str, category: str) -> dict[str, object]:
    upper = name.upper()
    flexible = "TPU" in material.upper() or any(token in upper for token in ("NECK", "ELBOW", "KNEE", "SCALE"))
    functional = any(token in upper for token in ("ADAPTER", "LINK", "FRAME", "SLED", "BEZEL", "CHANNEL", "ANCHOR", "SHIELD", "POD", "LID"))
    detail = any(token in upper for token in ("HELMET", "FACEPLATE"))
    if flexible:
        return {"profile": "TPU_FLOATING_024", "layer_mm": 0.24, "walls": 3, "infill_pct": 15, "material": "TPU preferred"}
    if functional:
        return {"profile": "PETG_FUNCTIONAL_020", "layer_mm": 0.20, "walls": 5, "infill_pct": 30, "material": "PETG preferred"}
    if detail:
        return {"profile": "PLA_DETAIL_016", "layer_mm": 0.16, "walls": 4, "infill_pct": 15, "material": "PLA/PETG"}
    return {"profile": "PLA_SHELL_020", "layer_mm": 0.20, "walls": 4, "infill_pct": 15, "material": "PLA/PETG"}


def create_print_docs() -> list[dict[str, object]]:
    source_manifest_path = DOCS / "PARTS_MANIFEST.json"
    source_manifest = json.loads(source_manifest_path.read_text()) if source_manifest_path.exists() else []
    source_map = {entry.get("name"): entry for entry in source_manifest}
    rows: list[dict[str, object]] = []
    for path in sorted(PRINT_STL.glob("*.stl")):
        mesh = trimesh.load_mesh(path, force="mesh")
        ext = np.asarray(mesh.extents, dtype=float)
        minimum = np.asarray(mesh.bounds[0], dtype=float)
        area = np.asarray(mesh.area_faces, dtype=float)
        normals = np.asarray(mesh.face_normals, dtype=float)
        total_area = float(area.sum()) if len(area) else 0.0
        downward = float(area[normals[:, 2] < -0.45].sum() / total_area) if total_area else 0.0
        info = source_map.get(path.stem, {})
        material = str(info.get("material", "PLA/PETG"))
        category = str(info.get("category", "Armor / hardware"))
        profile = profile_for(path.stem, material, category)
        height = float(ext[2])
        footprint_min = max(0.001, float(min(ext[0], ext[1])))
        brim = "8 mm brim" if height / footprint_min > 2.7 or footprint_min < 15 else "Optional 5 mm brim"
        if downward < 0.035:
            supports = "Likely none; inspect bridges in slicer"
        elif downward < 0.12:
            supports = "Build-plate-only organic/tree supports"
        else:
            supports = "Organic/tree supports; block internal cavities"
        density = 1.24 if "PLA" in profile["material"] else 1.27 if "PETG" in profile["material"] else 1.21
        solid_mass = float(abs(mesh.volume) / 1000.0 * density)
        rows.append({
            "file": path.name,
            "part": path.stem,
            "category": category,
            "quantity": int(info.get("quantity", 1)),
            "profile": profile["profile"],
            "material": profile["material"],
            "layer_mm": profile["layer_mm"],
            "walls": profile["walls"],
            "infill_pct": profile["infill_pct"],
            "supports": supports,
            "brim": brim,
            "bbox_x_mm": round(float(ext[0]), 3),
            "bbox_y_mm": round(float(ext[1]), 3),
            "bbox_z_mm": round(float(ext[2]), 3),
            "min_z_mm": round(float(minimum[2]), 4),
            "downward_area_ratio": round(downward, 4),
            "solid_equivalent_mass_g": round(solid_mass, 2),
            "watertight": bool(mesh.is_watertight),
            "within_220x220x240": bool(np.all(ext <= BUILD_ENVELOPE + 1e-6)),
        })

    with (PRINT_DOCS / "PRINT_MANIFEST_R39.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    write(PRINT_DOCS / "PRINT_MANIFEST_R39.json", json.dumps(rows, indent=2))

    profiles = {
        "PLA_SHELL_020.ini": "layer_height = 0.20\nperimeters = 4\ntop_solid_layers = 5\nbottom_solid_layers = 5\nfill_density = 15%\nfill_pattern = gyroid\nsupport_material = 0\nbrim_width = 5\nexternal_perimeter_speed = 35\nperimeter_speed = 45\n",
        "PLA_DETAIL_016.ini": "layer_height = 0.16\nperimeters = 4\ntop_solid_layers = 6\nbottom_solid_layers = 6\nfill_density = 15%\nfill_pattern = gyroid\nexternal_perimeter_speed = 28\nperimeter_speed = 38\n",
        "PETG_FUNCTIONAL_020.ini": "layer_height = 0.20\nperimeters = 5\ntop_solid_layers = 6\nbottom_solid_layers = 6\nfill_density = 30%\nfill_pattern = gyroid\nexternal_perimeter_speed = 30\nperimeter_speed = 40\n",
        "TPU_FLOATING_024.ini": "layer_height = 0.24\nperimeters = 3\ntop_solid_layers = 4\nbottom_solid_layers = 4\nfill_density = 15%\nfill_pattern = gyroid\nperimeter_speed = 22\nexternal_perimeter_speed = 18\nretract_length = 0.8\n",
    }
    for name, body in profiles.items():
        write(PRINT_DOCS / "SLICER_PROFILES" / name, body)

    hardware = [
        ["Chest frame to shell", "M3 x 12 mm machine screw", 4, "Use backing washers or captive backing plate; shield all body-facing hardware"],
        ["Chest lid to frame bosses", "M3 x 8 mm machine screw", 4, "92 x 70 mm lid pattern"],
        ["Forearm pod to interface", "M3 x 8 mm machine screw", 4, "Use the blank lid for initial fit"],
        ["Growth interface retention", "3 mm smooth pin / M3 shoulder screw", 2, "Bench-fit insertion and release before shell integration"],
        ["20 mm webbing anchors", "M3 x 10 mm machine screw", 2, "Backed anchor only; never fasten to unsupported thin shell"],
        ["Electronics power", "Protected enclosed USB power bank", 1, "No raw LiPo pouch in child armor"],
        ["Module disconnect", "Low-voltage breakaway connector", 3, "Chest and optional forearm modules"],
    ]
    with (PRINT_DOCS / "HARDWARE_BOM_R39.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Assembly", "Hardware", "Quantity", "Boundary"])
        writer.writerows(hardware)

    write(PRINT_DOCS / "PRINT_AND_ASSEMBLY_GUIDE_R39.md", """# IRON-KIDS K2 R39 print and commissioning guide\n\n## Build order\n\n1. Print calibration coupons and the chest cutout gauge before wearable shells.\n2. Fit the textile carrier and EVA layer. The carrier and foam—not PLA—are the body-fit system.\n3. Print helmet crown and faceplate as fit checks. Verify unobstructed vision, hearing, airflow, and immediate manual removal.\n4. Print one electronics-free arm and one growth-interface chain.\n5. Fit chest center with the blank lid before installing the OLED lid or any powered module.\n6. Print remaining shells only after the partial assemblies pass release and movement checks.\n7. Install optional electronics last. Every module must be removable without changing fit or preventing use.\n\n## Profiles\n\nThe included INI files are starting profiles, not printer certification. Verify extrusion width, dimensional compensation, bridging, and temperature on the exact printer and filament. Do not rescale individual mating parts independently.\n\n## Support interpretation\n\n`PRINT_MANIFEST_R39.csv` derives a support recommendation from downward-facing mesh area in the delivered orientation. It is a review aid, not a substitute for slicer preview. Block supports from trapped internal cavities.\n\n## Mass values\n\nThe manifest reports solid-equivalent geometry mass. It is not a slicer estimate and not a measured finished-suit mass. Record actual filament use and printed mass in the commissioning log.\n\n## Comfort boundary\n\nNo PLA edge, PCB, battery, screw head, cable tie, or printed boss belongs in the throat, armpit fold, inner elbow, palm-side wrist, groin crease, rear knee, or Achilles region.\n")
    create_contact_sheet(rows)
    create_wiring_svg()
    return rows


def font(size: int, bold: bool = False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def create_contact_sheet(rows: list[dict[str, object]]) -> None:
    cell_w, cell_h = 320, 230
    cols = 4
    count = len(rows)
    rows_n = math.ceil(count / cols)
    canvas = Image.new("RGB", (cell_w * cols, cell_h * rows_n + 90), (244, 239, 228))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, canvas.width, 90), fill=(9, 14, 21))
    draw.text((24, 18), "IRON-KIDS K2 / R39 PRINT ORIENTATION DESK", font=font(28, True), fill=(255, 250, 240))
    draw.text((24, 56), "Delivered build-plate orientation • verify support preview before printing", font=font(16), fill=(226, 203, 151))
    for index, row in enumerate(rows):
        path = PRINT_STL / str(row["file"])
        mesh = trimesh.load_mesh(path, force="mesh")
        x = (index % cols) * cell_w
        y = 90 + (index // cols) * cell_h
        draw.rectangle((x + 5, y + 5, x + cell_w - 5, y + cell_h - 5), fill=(255, 252, 245), outline=(198, 177, 129), width=2)
        verts = np.asarray(mesh.vertices)
        if len(verts):
            # Project X/Z to show delivered upright relationship.
            px = verts[:, 0]
            py = verts[:, 2]
            minx, maxx = float(px.min()), float(px.max())
            miny, maxy = float(py.min()), float(py.max())
            sx = 250.0 / max(1e-6, maxx - minx)
            sy = 135.0 / max(1e-6, maxy - miny)
            scale = min(sx, sy)
            ox = x + cell_w / 2 - (minx + maxx) * scale / 2
            oy = y + 160 + (miny + maxy) * scale / 2
            step = max(1, len(verts) // 6000)
            points = [(int(ox + vx * scale), int(oy - vz * scale)) for vx, vz in zip(px[::step], py[::step])]
            draw.point(points, fill=(25, 54, 91))
        label = str(row["part"]).replace("IK_K2_", "").replace("_R38", "")
        draw.text((x + 16, y + 16), label[:34], font=font(15, True), fill=(18, 28, 40))
        dims = f"{row['bbox_x_mm']:.0f} × {row['bbox_y_mm']:.0f} × {row['bbox_z_mm']:.0f} mm"
        draw.text((x + 16, y + 190), dims, font=font(13), fill=(70, 80, 91))
        draw.text((x + 16, y + 209), str(row["profile"]), font=font(12), fill=(142, 59, 46))
    target = PRINT_DOCS / "PRINT_ORIENTATION_CONTACT_SHEET_R39.png"
    canvas.save(target)
    shutil.copy2(target, SITE_ASSETS / "print-orientation-r39.png")


def create_wiring_svg() -> None:
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="760" viewBox="0 0 1400 760">
<rect width="1400" height="760" fill="#08101c"/><style>.t{font-family:Arial,sans-serif;fill:#f8f3e8}.s{font:18px Arial;fill:#bed0e4}.h{font:bold 34px Arial;fill:#f2d99b}.box{fill:#10243c;stroke:#3b79b9;stroke-width:3}.safe{fill:#18351f;stroke:#63b878;stroke-width:3}.warn{fill:#3b2d15;stroke:#d5aa46;stroke-width:3}.line{stroke:#72d9ff;stroke-width:5;fill:none;marker-end:url(#a)}.power{stroke:#e95b4f;stroke-width:5;fill:none;marker-end:url(#a)}</style><defs><marker id="a" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#72d9ff"/></marker></defs>
<text x="55" y="60" class="h">IRON-KIDS K2 / R39 LOW-VOLTAGE ELECTRONICS</text><text x="55" y="95" class="s">Optional, removable, local-first effects and status only. No restraint, closure, fit, or release authority.</text>
<rect x="55" y="150" width="280" height="150" rx="22" class="warn"/><text x="85" y="200" class="t" font-size="25" font-weight="bold">Protected USB power bank</text><text x="85" y="238" class="s">Enclosed commercial pack</text><text x="85" y="270" class="s">Breakaway 5 V connector</text>
<rect x="500" y="135" width="360" height="205" rx="22" class="box"/><text x="535" y="185" class="t" font-size="27" font-weight="bold">Chest NodeMCU ESP-12E/F</text><text x="535" y="225" class="s">D1/D2: I²C OLED + sensors</text><text x="535" y="258" class="s">D5: current-limited light data</text><text x="535" y="291" class="s">D6: haptic MOSFET gate</text><text x="535" y="324" class="s">USB serial: CRC status stream</text>
<rect x="1010" y="120" width="320" height="155" rx="22" class="box"/><text x="1045" y="170" class="t" font-size="25" font-weight="bold">Forearm status pod</text><text x="1045" y="210" class="s">Local OLED + buttons</text><text x="1045" y="243" class="s">Optional independent USB link</text>
<rect x="1010" y="350" width="320" height="155" rx="22" class="box"/><text x="1045" y="400" class="t" font-size="25" font-weight="bold">Second forearm pod</text><text x="1045" y="440" class="s">Same removable architecture</text><text x="1045" y="473" class="s">No module required for fit</text>
<rect x="500" y="470" width="360" height="170" rx="22" class="safe"/><text x="535" y="520" class="t" font-size="26" font-weight="bold">Read-only supervisor</text><text x="535" y="558" class="s">Session-aware boot ID + sequence</text><text x="535" y="590" class="s">CRC validation and stale detection</text><text x="535" y="622" class="s">No physical command API</text>
<path d="M335 225 H500" class="power"/><path d="M860 205 H1010" class="line"/><path d="M860 265 C940 265 935 425 1010 425" class="line"/><path d="M680 340 V470" class="line"/>
<text x="55" y="710" class="s">D0/GPIO16 select input requires an external pull-up. Keep every cable outside the throat and clear of manual releases.</text></svg>'''
    write(PRINT_DOCS / "WIRING_DIAGRAM_R39.svg", svg)
    write(SITE_ASSETS / "wiring-r39.svg", svg)


def patch_site() -> None:
    # Preserve every R38 image and video; add an incremental R39 layer only.
    css = '''.r39-release{background:linear-gradient(135deg,#071b3a,#0f355f);border:1px solid rgba(115,220,255,.4);border-radius:22px;padding:1.35rem;margin:1.5rem 0}.r39-release h2{margin:.25rem 0;font-size:clamp(1.8rem,3vw,3.2rem)}.r39-release p{color:#cfdae7}.r39-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem}.r39-grid article{background:#fffaf0;border:1px solid #ddcfaf;border-radius:18px;padding:1.15rem;color:#15202c}.r39-grid p{color:#495563}.r39-media{display:grid;grid-template-columns:1fr 1fr;gap:1rem}.r39-media img{width:100%;height:auto;border-radius:18px;border:1px solid rgba(211,172,72,.35)}@media(max-width:900px){.r39-grid,.r39-media{grid-template-columns:1fr}}'''
    write(SITE_ASSETS / "r39.css", css)

    for html_path in SITE.rglob("*.html"):
        text = html_path.read_text(encoding="utf-8")
        text = text.replace("ENGINEERING A FAMILY / R38", "ENGINEERING A FAMILY / R39")
        text = text.replace("<b>R38</b>", "<b>R39</b>")
        text = text.replace("R38 PILOT ↗", "R39 COMMISSIONING ↗")
        if "/assets/r39/r39.css" not in text:
            text = text.replace("</head>", '<link rel="stylesheet" href="/assets/r39/r39.css"></head>')
        if "/iron-kids/commissioning/" not in text:
            text = text.replace("</nav>", '<a href="/iron-kids/commissioning/">Commissioning</a></nav>', 1)
        html_path.write_text(text, encoding="utf-8")

    banner = '''<section class="shell r39-release"><span class="kicker">R39 / ELECTRONICS + PRINT COMMISSIONING</span><h2>Compiled firmware. Session-aware telemetry. Reviewed print desk.</h2><p>R39 preserves the R38 pilot, images, and rotation film while adding reproducible NodeMCU builds, CRC-protected read-only status, print orientations, material profiles, hardware schedules, and wiring documentation.</p><div class="actions"><a class="button" href="/iron-kids/commissioning/">Open R39 commissioning ↗</a><a class="button alt" href="/downloads/IRON_KIDS_K2_COMMISSIONING_R39.zip">Download R39 package ↗</a></div></section>'''
    for relative in (Path("index.html"), Path("iron-kids/index.html"), Path("iron-kids/pilot/index.html")):
        target = SITE / relative
        if target.exists():
            text = target.read_text(encoding="utf-8")
            if "R39 / ELECTRONICS + PRINT COMMISSIONING" not in text:
                text = text.replace("</main>", banner + "</main>")
            target.write_text(text, encoding="utf-8")

    page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#080b10"><title>IRON-KIDS R39 — Electronics and Print Commissioning</title><meta name="description" content="Compiled NodeMCU firmware, session-aware telemetry, print profiles, orientations, wiring, and commissioning documents for the K2 pilot."><meta property="og:title" content="IRON-KIDS R39 Commissioning"><meta property="og:image" content="/assets/r39/print-orientation-r39.png"><link rel="stylesheet" href="/assets/site.css"><link rel="stylesheet" href="/assets/r39/r39.css"></head><body><header class="top"><div class="shell nav"><a class="brand" href="/"><span class="mark">JT</span><span>IRON—DAD<small>ENGINEERING A FAMILY / R39</small></span></a><nav class="links"><a href="/family/">Family</a><a href="/iron-dad/">IRON-DAD</a><a href="/iron-kitty/">IRON-KITTY</a><a href="/iron-kids/">IRON-KIDS</a><a href="/iron-kids/pilot/">K2 Pilot</a><a aria-current="page" href="/iron-kids/commissioning/">Commissioning</a><a href="/downloads/">Downloads</a></nav></div></header><main><section class="shell page-hero"><span class="kicker">R39 / K2 COMMISSIONING RELEASE</span><h1>MAKE IT<br><em>REPEATABLE.</em></h1><p>The K2 pilot now includes independently compilable chest and forearm firmware, CRC-protected serial status, boot-session recovery, printer-oriented documentation, material profiles, a fastener schedule, and a protected low-voltage wiring plan.</p><div class="actions"><a class="button" href="/downloads/{MODEL_ZIP_NAME}">Download R39 package ↗</a><a class="button alt" href="#firmware">Inspect the release ↓</a></div></section><section class="paper section" id="firmware"><div class="shell"><span class="kicker" style="color:#8a2b27">WORKING SOURCE / COMPILED IN CI</span><h2 class="section-title">FIRMWARE THAT<br>KNOWS ITS BOUNDARY.</h2><div class="r39-grid"><article><h3>Chest node</h3><p>SSD1306 OLED, optional AHT20 and INA219 sensing, bounded light output, menu buttons, and MOSFET-driven haptic effects.</p></article><article><h3>Forearm node</h3><p>Independent status OLED and controls. The pod remains optional and removable.</p></article><article><h3>Supervisor</h3><p>CRC validation, stale-link detection, and boot-ID handling fix the sequence-reset problem found in the R35 audit.</p></article></div></div></section><section class="section"><div class="shell r39-media"><img src="/assets/r39/print-orientation-r39.png" alt="R39 print orientation contact sheet"><img src="/assets/r39/wiring-r39.svg" alt="R39 low voltage wiring diagram"></div></section><section class="paper section"><div class="shell"><h2 class="section-title">PRINT THE<br><em>RIGHT THING.</em></h2><div class="r39-grid"><article><h3>Per-part manifest</h3><p>Quantity, delivered dimensions, material profile, walls, infill, support likelihood, brim guidance, and solid-equivalent mass.</p></article><article><h3>Starting profiles</h3><p>Separate PLA shell, detail, PETG functional, and TPU floating-part profiles. Builders must still verify the exact printer and filament.</p></article><article><h3>Hardware map</h3><p>Chest, forearm, growth interface, webbing, and breakaway low-voltage hardware are listed separately from printable parts.</p></article></div><div class="notice" style="margin-top:1rem"><strong>Evidence boundary:</strong> R39 establishes reproducible digital builds and documentation. It does not claim a printed, thermally commissioned, or child-fitted suit.</div></div></section></main><footer class="footer"><div class="shell footer-grid"><div><b>IRON-DAD / Justin Tahai</b><p>Human-scale ambition, Peach’s sidekick branch, and a comfort-first builder program.</p></div><div><a href="/iron-kids/pilot/">R38 registered pilot</a><br><a href="/iron-kids/commissioning/">R39 commissioning</a></div><div><a href="/downloads/{MODEL_ZIP_NAME}">Download R39</a></div></div></footer></body></html>'''
    target = SITE / "iron-kids" / "commissioning" / "index.html"
    write(target, page)

    # Rebuild the download desk so the current package is unmistakable.
    downloads = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>IRON-DAD R39 Downloads</title><meta name="description" content="Current IRON-DAD family engineering downloads."><link rel="stylesheet" href="/assets/site.css"><link rel="stylesheet" href="/assets/r39/r39.css"></head><body><header class="top"><div class="shell nav"><a class="brand" href="/"><span class="mark">JT</span><span>IRON—DAD<small>ENGINEERING A FAMILY / R39</small></span></a><nav class="links"><a href="/family/">Family</a><a href="/iron-kids/pilot/">K2 Pilot</a><a href="/iron-kids/commissioning/">Commissioning</a><a aria-current="page" href="/downloads/">Downloads</a></nav></div></header><main><section class="shell page-hero"><span class="kicker">CURRENT VERIFIED ARTIFACT</span><h1>R39<br><em>DOWNLOAD DESK.</em></h1><p>The complete R38 registered K2 pilot plus R39 firmware, compiled binaries, print profiles, wiring, manifests, and commissioning documentation.</p></section><section class="paper section"><div class="shell"><div class="download"><div><h2>IRON-KIDS K2 Commissioning R39</h2><p>Registered and print STLs, GLB assemblies, textile/EVA references, PlatformIO source, compiled NodeMCU binaries, Python supervisor tests, print desk, and SHA-256 records.</p></div><a class="button" href="/downloads/{MODEL_ZIP_NAME}">Download ZIP ↗</a></div></div></section></main><footer class="footer"><div class="shell"><a href="/">Back to IRON-DAD</a></div></footer></body></html>'''
    write(SITE / "downloads" / "index.html", downloads)


def local_reference_audit() -> list[dict[str, str]]:
    missing: list[dict[str, str]] = []
    for html_path in SITE.rglob("*.html"):
        text = html_path.read_text(encoding="utf-8")
        for raw in re.findall(r'(?:href|src)=["\']([^"\']+)', text):
            if raw.startswith(("http:", "https:", "mailto:", "tel:", "#", "data:")):
                continue
            target = raw.split("#", 1)[0].split("?", 1)[0]
            if not target:
                continue
            path = SITE / target.lstrip("/") if target.startswith("/") else html_path.parent / target
            if target.endswith("/"):
                path = path / "index.html"
            if not path.exists():
                missing.append({"page": str(html_path.relative_to(SITE)), "target": raw})
    return missing


def prepare() -> None:
    if not (SITE / "index.html").exists() or not (PRINT_STL.exists() and any(PRINT_STL.glob("*.stl"))):
        raise RuntimeError("R38 output must exist before R39 prepare")
    write_firmware()
    rows = create_print_docs()
    patch_site()
    write(SOURCE / "README.md", "R39 is an additive pass over the R38 registered K2 pilot. Run r38/build.py first, then r39/build.py prepare, compile both PlatformIO projects, and run r39/build.py finalize.\n")
    shutil.copy2(Path(__file__), SOURCE / "build.py")
    write(DOCS / "R39_PREPARE.json", json.dumps({"release": RELEASE, "print_parts_analyzed": len(rows), "remaining_planned_passes": 2}, indent=2))


def finalize() -> None:
    binaries = FIRMWARE / "bin"
    binaries.mkdir(parents=True, exist_ok=True)
    compiled = []
    for project in ("chest", "forearm"):
        source = FIRMWARE / project / ".pio" / "build" / "nodemcuv2" / "firmware.bin"
        if not source.exists():
            raise RuntimeError(f"missing compiled firmware: {source}")
        target = binaries / f"iron_kids_{project}_nodemcuv2_r39.bin"
        shutil.copy2(source, target)
        compiled.append({"project": project, "file": str(target.relative_to(MODEL)), "bytes": target.stat().st_size, "sha256": sha256(target)})

    # Run supervisor tests inside the packaged source tree.
    env = dict(os.environ)
    env["PYTHONPATH"] = str(FIRMWARE / "supervisor")
    subprocess.run([sys.executable, "-m", "unittest", "-v", "test_supervisor.py"], cwd=FIRMWARE / "supervisor", env=env, check=True)
    write(FIRMWARE / "COMPILE_MATRIX_R39.json", json.dumps({"platform": "NodeMCU v2 / ESP8266", "framework": "Arduino", "projects": compiled, "supervisor_tests": "passed"}, indent=2))

    print_rows = json.loads((PRINT_DOCS / "PRINT_MANIFEST_R39.json").read_text())
    print_checks = {
        "count": len(print_rows),
        "all_watertight": all(row["watertight"] for row in print_rows),
        "all_within_220x220x240": all(row["within_220x220x240"] for row in print_rows),
        "all_on_or_above_build_plate": all(row["min_z_mm"] >= -0.02 for row in print_rows),
    }
    verification = {
        "release": RELEASE,
        "base_pilot": "R38",
        "compiled_firmware": compiled,
        "supervisor_tests": "passed",
        "print_checks": print_checks,
        "media_preserved_from_r38": {
            "images": len([p for p in SITE.rglob("*") if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".svg"}]),
            "videos": len([p for p in SITE.rglob("*") if p.suffix.lower() in {".mp4", ".webm"}]),
        },
        "physical_child_validation": False,
        "remaining_planned_passes": 2,
    }
    write(DOCS / "VERIFICATION_R39.json", json.dumps(verification, indent=2))

    # Recalculate model checksums before packaging.
    checksum_path = MODEL / "SHA256SUMS.txt"
    if checksum_path.exists():
        checksum_path.unlink()
    entries = []
    for path in sorted(MODEL.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            entries.append(f"{sha256(path)}  {path.relative_to(MODEL).as_posix()}")
    write(checksum_path, "\n".join(entries) + "\n")

    model_zip = SITE_DOWNLOADS / MODEL_ZIP_NAME
    if model_zip.exists():
        model_zip.unlink()
    with zipfile.ZipFile(model_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(MODEL.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(MODEL))

    missing = local_reference_audit()
    site_verification = {
        "release": RELEASE,
        "root_index_exists": (SITE / "index.html").exists(),
        "html_pages": len(list(SITE.rglob("*.html"))),
        "image_files": len([p for p in SITE.rglob("*") if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".svg"}]),
        "video_files": len([p for p in SITE.rglob("*") if p.suffix.lower() in {".mp4", ".webm"}]),
        "missing_local_references": missing,
        "model_zip": MODEL_ZIP_NAME,
        "model_zip_bytes": model_zip.stat().st_size,
        "model_zip_sha256": sha256(model_zip),
        "compiled_firmware_projects": len(compiled),
        "remaining_planned_passes": 2,
    }
    write(SITE / "R39_VERIFICATION.json", json.dumps(site_verification, indent=2))
    if missing:
        raise RuntimeError(f"missing local references: {missing[:5]}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "prepare"
    if mode == "prepare":
        prepare()
    elif mode == "finalize":
        finalize()
    else:
        raise SystemExit("usage: build.py [prepare|finalize]")
