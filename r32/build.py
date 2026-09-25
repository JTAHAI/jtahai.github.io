from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out"
MODEL = OUT / "model"
SITE = OUT / "site"
SCAD = MODEL / "SCAD"
STL = MODEL / "STL"
FIRMWARE = MODEL / "FIRMWARE"
DOCS = MODEL / "DOCS"
for p in [OUT, MODEL, SITE, SCAD, STL, FIRMWARE, DOCS]:
    p.mkdir(parents=True, exist_ok=True)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

HEADER = '''$fn=48;
module slot2d(len=20,w=4,h=20){ hull(){ translate([-(len-w)/2,0,0]) cylinder(d=w,h=h,center=true); translate([(len-w)/2,0,0]) cylinder(d=w,h=h,center=true); } }
module plate_holes(x,y,z,sx,sy,d=3.4){ difference(){ cube([x,y,z],center=true); for(ix=[-1,1]) for(iy=[-1,1]) translate([ix*sx/2,iy*sy/2,0]) cylinder(d=d,h=z+4,center=true); } }
'''

parts: list[dict] = []

def build(name: str, body: str, category: str, notes: str, material: str="PLA/PETG") -> None:
    scad = SCAD / f"{name}.scad"
    stl = STL / f"{name}.stl"
    scad.write_text(HEADER + body + "\n")
    env = dict(os.environ)
    env["QT_QPA_PLATFORM"] = "offscreen"
    subprocess.run(["openscad", "-o", str(stl), str(scad)], check=True, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if stl.stat().st_size < 84:
        raise RuntimeError(f"empty STL: {name}")
    parts.append({"name":name,"category":category,"notes":notes,"material":material,"stl":f"STL/{stl.name}","source":f"SCAD/{scad.name}","bytes":stl.stat().st_size})

build("K2_CHEST_CUTOUT_GAUGE_R32", '''difference(){ cube([118,96,2],center=true); cube([82,56,6],center=true); for(ix=[-1,1]) for(iy=[-1,1]) translate([ix*50,iy*39,0]) cylinder(d=2.2,h=8,center=true); }''', "Fit gauge", "Print first; register against a sacrificial or unpainted shell before cutting.")

build("K2_CHEST_ELECTRONICS_INTERFACE_FRAME_R32", '''difference(){ union(){ cube([118,96,3.2],center=true); translate([0,0,4]) difference(){ cube([104,82,8],center=true); cube([96,74,12],center=true); } } cube([82,56,20],center=true); for(ix=[-1,1]) for(iy=[-1,1]) translate([ix*50,iy*39,0]) cylinder(d=3.6,h=20,center=true); }''', "Chest interface", "Backed interface frame for measured K2 chest opening.")

build("K2_CHEST_SERVICE_LID_BLANK_R32", '''plate_holes(104,82,2.6,92,70,3.6);''', "Chest lid", "Electronics-free blanking lid.")

build("K2_CHEST_SERVICE_LID_OLED_ARC_R32", '''difference(){ plate_holes(104,82,2.6,92,70,3.6); translate([0,20,0]) cube([28,15,8],center=true); translate([0,-12,0]) cylinder(h=8,r=19,center=true,$fn=3); }''', "Chest lid", "OLED and triangular illuminated-panel opening.")

build("OLED_093_096_ADJUSTABLE_BEZEL_R32", '''difference(){ cube([42,30,4],center=true); cube([27.5,15.5,10],center=true); translate([-15,0,0]) slot2d(9,3.2,12); translate([15,0,0]) slot2d(9,3.2,12); }''', "Display", "Adjustable bezel for common 0.93/0.96-inch OLED boards.")

build("NODEMCU_12E_12F_UNIVERSAL_SLED_R32", '''difference(){ union(){ cube([78,40,3],center=true); translate([-37,0,4]) cube([4,40,8],center=true); translate([37,0,4]) cube([4,40,8],center=true); } translate([0,-14,0]) slot2d(26,3.4,16); translate([0,14,0]) slot2d(26,3.4,16); }''', "Controller", "Strap-retained universal NodeMCU sled; measure the actual clone board.")

build("USB_POWER_BANK_BREAKAWAY_POCKET_R32", '''difference(){ cube([116,70,24],center=true); translate([0,0,5]) cube([106,60,24],center=true); translate([0,-35,2]) cube([34,18,30],center=true); translate([-42,0,0]) slot2d(22,4,30); translate([42,0,0]) slot2d(22,4,30); }''', "Power", "Open ventilated pocket for protected USB power bank; no raw pouch cell.")

build("DUAL_LANE_SERVICE_CHANNEL_120_R32", '''difference(){ cube([120,24,10],center=true); translate([0,-6,2]) cube([110,7,8],center=true); translate([0,6,2]) cube([110,7,8],center=true); }''', "Wiring", "Stationary two-lane carrier separating power and signal.")

build("DUAL_LANE_SERVICE_CHANNEL_LID_120_R32", '''plate_holes(120,24,2.2,108,12,3.2);''', "Wiring", "Removable channel lid.")

build("CABLE_BRIDGE_6_WIRE_R32", '''difference(){ cube([42,22,12],center=true); cube([28,14,10],center=true); translate([-16,0,0]) slot2d(8,3.2,18); translate([16,0,0]) slot2d(8,3.2,18); }''', "Wiring", "Guarded low-voltage cable bridge.")

build("SPLIT_STRAIN_RELIEF_GROMMET_R32", '''difference(){ cylinder(d=30,h=5,center=true); cylinder(d=14,h=12,center=true); cube([4,34,12],center=true); }''', "Wiring", "Split grommet; TPU preferred, PLA only as fit gauge.", "TPU preferred")

FOREARM = '''difference(){ union(){ cube([92,50,4],center=true); translate([{rail},0,4]) cube([4,38,8],center=true); } translate([0,0,1.6]) cube([72,28,2.2],center=true); for(ix=[-1,1]) for(iy=[-1,1]) translate([ix*34,iy*18,0]) slot2d(12,3.6,14); }'''
build("K2_FOREARM_ELECTRONICS_INTERFACE_LEFT_R32", FOREARM.format(rail=42), "Forearm interface", "Left backed interface coupon for pod alignment and straps.")
build("K2_FOREARM_ELECTRONICS_INTERFACE_RIGHT_R32", FOREARM.format(rail=-42), "Forearm interface", "Right mirrored interface coupon.")

build("FOREARM_DISPLAY_POD_BASE_R32", '''difference(){ cube([86,46,18],center=true); translate([0,0,4]) cube([76,36,18],center=true); translate([0,-23,3]) cube([24,14,24],center=true); translate([-32,0,0]) slot2d(15,3.5,30); translate([32,0,0]) slot2d(15,3.5,30); }''', "Forearm pod", "Ventilated removable forearm pod base.")

build("FOREARM_POD_LID_BLANK_R32", '''plate_holes(86,46,2.6,74,34,3.2);''', "Forearm lid", "Electronics-free pod lid.")
build("FOREARM_POD_LID_OLED_R32", '''difference(){ plate_holes(86,46,2.6,74,34,3.2); cube([28,16,8],center=true); }''', "Forearm lid", "OLED window pod lid.")

build("MOVING_SERVICE_LOOP_GUIDE_R32", '''difference(){ cube([55,30,10],center=true); cube([39,16,14],center=true); translate([0,8,0]) cube([9,32,14],center=true); }''', "Wiring", "Guide for a protected moving loop; final length comes from combined motion.")

build("ELECTRONICS_CASSETTE_BACKPLATE_R32", '''difference(){ plate_holes(128,92,3.2,112,76,4.2); translate([0,-32,0]) slot2d(34,4,12); translate([0,32,0]) slot2d(34,4,12); }''', "Carrier", "Backed mounting plate for removable low-voltage modules.")

build("WEBBING_ANCHOR_20MM_R32", '''difference(){ cube([44,28,4],center=true); slot2d(25,4,12); translate([-16,0,0]) cylinder(d=3.4,h=12,center=true); translate([16,0,0]) cylinder(d=3.4,h=12,center=true); }''', "Carrier", "Backed 20 mm webbing anchor.")

build("FASTENER_SHIELD_M3_R32", '''difference(){ cylinder(d=22,h=4,center=true); cylinder(d=8,h=10,center=true); translate([0,7,0]) cube([24,10,10],center=true); }''', "Comfort", "Fastener shield; keep rigid hardware outside body-contact padding.")

# Firmware references.
(FIRMWARE / "telemetry_v1.h").write_text(r'''#pragma once
#include <Arduino.h>
struct IkStatusV1 { uint8_t version=1; uint32_t sequence=0; uint32_t uptime_ms=0; int16_t temperature_c_x100=0; uint16_t humidity_pct_x100=0; uint16_t supply_mv=0; uint8_t module_attached=0; uint8_t local_mode=1; uint8_t faults=0; };
enum IkFault:uint8_t { SENSOR_STALE=1, OVER_TEMP=2, LOW_POWER=4, LINK_STALE=8 };
''')
(FIRMWARE / "iron_kids_chest_r32.ino").write_text(r'''#include <Arduino.h>
#include <Wire.h>
#include "telemetry_v1.h"
constexpr uint8_t PIN_SDA=D2, PIN_SCL=D1, PIN_LED=D5, PIN_HAPTIC=D6, PIN_MENU=D7, PIN_SELECT=D0;
IkStatusV1 statusFrame; uint32_t lastSensor=0;
void setup(){ pinMode(PIN_HAPTIC,OUTPUT); pinMode(PIN_MENU,INPUT_PULLUP); pinMode(PIN_SELECT,INPUT_PULLUP); digitalWrite(PIN_HAPTIC,LOW); Wire.begin(PIN_SDA,PIN_SCL); WiFi.mode(WIFI_OFF); }
void loop(){ statusFrame.sequence++; statusFrame.uptime_ms=millis(); if(millis()-lastSensor>2000){ statusFrame.faults|=SENSOR_STALE; digitalWrite(PIN_HAPTIC,LOW); } delay(50); }
''')
(FIRMWARE / "iron_kids_forearm_r32.ino").write_text(r'''#include <Arduino.h>
#include <Wire.h>
#include "telemetry_v1.h"
constexpr uint8_t PIN_SDA=D2, PIN_SCL=D1, PIN_BUTTON=D7; IkStatusV1 statusFrame;
void setup(){ pinMode(PIN_BUTTON,INPUT_PULLUP); Wire.begin(PIN_SDA,PIN_SCL); WiFi.mode(WIFI_OFF); }
void loop(){ statusFrame.sequence++; statusFrame.uptime_ms=millis(); statusFrame.local_mode=1; delay(50); }
''')
(FIRMWARE / "local_supervisor.py").write_text('''from dataclasses import dataclass\nfrom time import monotonic\n@dataclass\nclass Node:\n    name:str\n    last_seen:float=0.0\n    seq:int=0\n    faults:int=0\n    def fresh(self,timeout=2.0): return monotonic()-self.last_seen<=timeout\nclass Supervisor:\n    def __init__(self): self.nodes={}\n    def update(self,name,seq,faults):\n        n=self.nodes.setdefault(name,Node(name))\n        if seq>n.seq: n.seq,n.faults,n.last_seen=seq,faults,monotonic()\n    def status(self): return {k:("FAULT" if v.faults else "LOCAL") if v.fresh() else "STALE" for k,v in self.nodes.items()}\n''')

(DOCS / "README.md").write_text('''# IRON-KIDS K2 Integrated Electronics R32

R32 adds chest and forearm interface hardware, OLED and blank lids, a NodeMCU sled, protected USB power-bank retention, service channels, cable protection, backed anchors, firmware references, and fit gauges.

## Boundary
Electronics are optional, removable effects and status modules. They cannot control fit, closure, restraint, release, or joint motion. The costume must remain wearable with every module absent.

## Order
1. Print the chest cutout gauge.
2. Register it against an unpainted test shell and the real textile/EVA stack.
3. Fit the blank lid before an OLED lid.
4. Measure the actual NodeMCU and OLED clone boards.
5. Keep power-bank and PCB mass outside body-contact foam.
6. Fit one forearm interface with the blank lid before adding a display.
''')
(DOCS / "WIRING_PLAN.md").write_text('''# Low-voltage wiring
- D2/GPIO4: I2C SDA
- D1/GPIO5: I2C SCL
- D5/GPIO14: current-limited LED data
- D6/GPIO12: haptic MOSFET gate
- D7/GPIO13: menu
- D0/GPIO16: select
- Avoid GPIO0, GPIO2, and GPIO15 for normal switches because they affect ESP8266 boot mode.
- Use a protected USB power bank. No raw LiPo pouch inside child armor.
- No cable crosses the throat, acts as a restraint, or blocks a release.
''')
with (DOCS / "BOM.csv").open("w", newline="") as f:
    w=csv.writer(f); w.writerow(["Item","Qty","Boundary"])
    w.writerows([
        ["NodeMCU ESP-12E/F board","1 chest + optional arms","Measure clone dimensions"],
        ["0.93/0.96 SSD1306 OLED","1 chest + optional arms","PCB outlines vary"],
        ["Protected USB power bank","1","No raw pouch cell"],
        ["AHT20/SHT3x sensor","1 chest","Comfort indication only"],
        ["Current-limited LEDs","As needed","Diffused, brightness capped"],
        ["20 mm webbing","As needed","Carries module mass"],
    ])

verification={"release":"R32","parts":parts,"summary":{"part_count":len(parts),"stl_files":len(list(STL.glob('*.stl'))),"all_stl_nonempty":all(p.stat().st_size>84 for p in STL.glob('*.stl')),"physical_child_validation":False,"electronics_physical_authority":False}}
(DOCS / "VERIFICATION.json").write_text(json.dumps(verification,indent=2))
(DOCS / "PARTS_MANIFEST.json").write_text(json.dumps(parts,indent=2))
(MODEL / "RELEASE.txt").write_text("IRON-KIDS K2 Integrated Electronics R32\nRemaining roadmap passes after R32: 3\n")
checks=[]
for p in sorted(MODEL.rglob('*')):
    if p.is_file() and p.name!='SHA256SUMS.txt': checks.append(f"{sha(p)}  {p.relative_to(MODEL).as_posix()}")
(MODEL / "SHA256SUMS.txt").write_text("\n".join(checks)+"\n")

# Package for embedding in website.
(SITE / "downloads").mkdir(parents=True,exist_ok=True)
model_zip=SITE/"downloads/IRON_KIDS_K2_INTEGRATED_ELECTRONICS_R32.zip"
with zipfile.ZipFile(model_zip,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(MODEL.rglob('*')):
        if p.is_file(): z.write(p,p.relative_to(MODEL))

# Website.
(SITE / "assets").mkdir(exist_ok=True)
(SITE / "assets/site.css").write_text(''':root{--bg:#090b0f;--s:#131a24;--p:#f3ede1;--ink:#141b25;--red:#bd3631;--gold:#d4af4a;--cyan:#72d9ff;--line:#d4af4a55}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:#fff;font:16px/1.6 system-ui,Segoe UI,sans-serif}a{color:inherit}.shell{width:min(1400px,calc(100% - 2rem));margin:auto}.top{position:sticky;top:0;background:#090b0ff2;border-bottom:1px solid var(--line);z-index:5}.nav{min-height:72px;display:flex;align-items:center;justify-content:space-between;gap:1rem}.brand{text-decoration:none;font-weight:900;letter-spacing:.08em}.brand small{display:block;color:#f2deb0;font-size:.65rem}.links{display:flex;gap:1rem}.links a{text-decoration:none;font-weight:700;color:#dbe4ee}.hero{min-height:72vh;display:grid;grid-template-columns:1.1fr .9fr;align-items:center;gap:3rem;padding:6rem 0}.eyebrow{color:#f2deb0;text-transform:uppercase;letter-spacing:.16em;font-weight:800;font-size:.78rem}h1{font-size:clamp(3.6rem,8vw,8rem);line-height:.86;letter-spacing:-.06em;margin:.5rem 0}h1 em,h2 em{color:var(--gold);font-style:normal}.hero p,.lead{font-size:1.15rem;color:#d3dce7;max-width:64ch}.reactor{aspect-ratio:1;display:grid;place-items:center;border:1px solid var(--line);border-radius:50%;box-shadow:0 0 80px #d4af4a20}.core{width:48%;aspect-ratio:1;clip-path:polygon(50% 0,100% 100%,0 100%);background:radial-gradient(circle at 50% 65%,#fff 0 8%,#7de3ff 10% 20%,#0b3d91 22% 44%,#111722 45%);filter:drop-shadow(0 0 35px #72d9ffaa)}.button{display:inline-flex;padding:.8rem 1.1rem;border-radius:12px;background:linear-gradient(135deg,#e04d43,#a72828);text-decoration:none;font-weight:850;margin:.4rem .5rem .4rem 0}.button.alt{background:transparent;border:1px solid var(--line);color:#f2deb0}.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;padding-bottom:5rem}.card{background:linear-gradient(#182232,#101720);border:1px solid var(--line);border-radius:20px;padding:1.3rem}.card h2{font-size:2.3rem;margin:.35rem 0}.card p{color:#c9d2de}.paper{background:var(--p);color:var(--ink);padding:5rem 0}.paper p{color:#4b5663}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem}.spec{background:#fffaf0;border:1px solid #d9caab;border-radius:18px;padding:1.2rem}.page{padding:5rem 0 3rem}.page h1{font-size:clamp(3rem,7vw,7rem)}.panel{background:#081426;border:1px solid #2e5a88;border-radius:20px;padding:1.2rem}.nodes{display:grid;grid-template-columns:repeat(4,1fr);gap:.7rem}.node{background:#10223b;border:1px solid #2e5a88;border-radius:14px;padding:1rem}.node b{display:block;color:#fff}.node span{color:#c3d8ed}.controls{display:grid;grid-template-columns:1fr 1fr;gap:1rem;padding:4rem 0}.toggle{display:block;width:100%;padding:1rem;margin:.5rem 0;background:#10223b;color:#fff;border:1px solid #2e5a88;border-radius:12px;text-align:left}.toggle[aria-pressed=true]{border-color:var(--gold)}pre{background:#02050a;border:1px solid #2e5a88;color:#8de5ff;border-radius:14px;padding:1rem;min-height:230px;white-space:pre-wrap}.download{background:linear-gradient(135deg,#0b3d91,#071a3b);border:1px solid #2e6fbc;border-radius:20px;padding:1.3rem}.footer{padding:2.4rem 0;border-top:1px solid var(--line);color:#b7c0cc}.footer-grid{display:grid;grid-template-columns:2fr 1fr;gap:2rem}@media(max-width:900px){.links{display:none}.hero,.cards,.grid,.nodes,.controls,.footer-grid{grid-template-columns:1fr}.hero{min-height:auto;padding:4rem 0}.reactor{max-width:480px;margin:auto}}''')
(SITE / "assets/site.js").write_text('''const q=s=>document.querySelector(s),qa=s=>[...document.querySelectorAll(s)];function update(){let a=qa('[data-t][aria-pressed="true"]').map(x=>x.dataset.t),o=q('[data-out]');if(o)o.textContent=['IRON-KIDS K2 / R32','',...a.map(x=>'✓ '+x.toUpperCase()),'',a.includes('power')?'POWER: PROTECTED USB':'POWER: MODULE ABSENT',a.includes('chest')?'CHEST: LOCAL DISPLAY':'CHEST: BLANK LID','PHYSICAL AUTHORITY: NONE'].join('\n')}qa('[data-t]').forEach(b=>b.onclick=()=>{b.setAttribute('aria-pressed',b.getAttribute('aria-pressed')!=='true');update()});update();''')

def nav(): return '''<header class="top"><div class="shell nav"><a class="brand" href="/">IRON—DAD<small>ENGINEERING A FAMILY / R32</small></a><nav class="links"><a href="/family/">Family</a><a href="/iron-dad/">IRON-DAD</a><a href="/iron-kitty/">IRON-KITTY</a><a href="/iron-kids/">IRON-KIDS</a><a href="/iron-kids/electronics/">R32 Electronics</a></nav></div></header>'''
def footer(): return '''<footer class="footer"><div class="shell footer-grid"><div><b>IRON-DAD / Justin Tahai</b><p>Human-scale ambition, a feline sidekick, and a growth-friendly builder program.</p></div><div><a href="/downloads/IRON_KIDS_K2_INTEGRATED_ELECTRONICS_R32.zip">Download R32 model ZIP</a></div></div></footer>'''
def page(title,desc,body): return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#090b0f"><title>{title}</title><meta name="description" content="{desc}"><link rel="stylesheet" href="/assets/site.css"><script defer src="/assets/site.js"></script></head><body>{nav()}<main>{body}</main>{footer()}</body></html>'''

home='''<section class="shell hero"><div><span class="eyebrow">Justin Tahai / Personal systems engineering</span><h1>ENGINEERING<br><em>A FAMILY.</em></h1><p>IRON-DAD explores a human-scale articulated machine. IRON-KITTY gives Peach a feline-first sidekick project. IRON-KIDS turns the same imagination into a comfort-first PLA builder program.</p><a class="button" href="/family/">Explore the family ↗</a><a class="button alt" href="/iron-kids/electronics/">Open R32 electronics ↗</a></div><div class="reactor"><div class="core"></div></div></section><section class="shell cards"><article class="card"><span class="eyebrow">Human scale</span><h2>IRON-DAD</h2><p>Articulated skin, assisted structure, distributed controls, and AR.</p><a href="/iron-dad/">Open project ↗</a></article><article class="card"><span class="eyebrow">Sidekick</span><h2>IRON-KITTY</h2><p>Peach’s feline-first red-and-gold armor branch.</p><a href="/iron-kitty/">Meet Peach ↗</a></article><article class="card"><span class="eyebrow">Builders</span><h2>IRON-KIDS</h2><p>Growth-friendly shells, EVA comfort, soft carrier, optional electronics.</p><a href="/iron-kids/">Start building ↗</a></article></section>'''
(SITE/'index.html').write_text(page('IRON-DAD — Engineering a Family','IRON-DAD, IRON-KITTY, and IRON-KIDS.',home))

pages={
'family/index.html':('Engineering a Family','Three projects, one discipline','''<section class="shell page"><span class="eyebrow">The whole program</span><h1>THREE BRANCHES.<br><em>ONE DISCIPLINE.</em></h1><p class="lead">Comfort, agency, evidence, and possibility connect the human, feline, and child-scale projects.</p></section><section class="paper"><div class="shell grid"><article class="spec"><h2>Comfort</h2><p>Textile carriers, removable EVA, ventilation, and soft compression folds.</p></article><article class="spec"><h2>Agency</h2><p>Reachable releases and electronics with no restraint authority.</p></article><article class="spec"><h2>Evidence</h2><p>Concept, modeled, digitally checked, bench-tested, and physical proof stay distinct.</p></article></div></section>'''),
'iron-dad/index.html':('IRON-DAD','Human-scale articulated armor','''<section class="shell page"><span class="eyebrow">Human scale</span><h1>IRON—DAD.</h1><p class="lead">Articulated skin, assisted structure, distributed safety, and integrated optics.</p></section>'''),
'iron-kitty/index.html':('IRON-KITTY — Peach','Feline-first sidekick armor','''<section class="shell page"><span class="eyebrow">The official sidekick</span><h1>IRON—KITTY.<br><em>PEACH.</em></h1><p class="lead">Feline-first: free face, ears, whiskers, belly, paws, gait, and tail balance.</p></section>'''),
'iron-kids/index.html':('IRON-KIDS','Growth-friendly comfort-first armor','''<section class="shell page"><span class="eyebrow">The builder branch</span><h1>GROW WITH<br><em>THE HERO.</em></h1><p class="lead">PLA shells outside a textile carrier, removable EVA, modular growth, and optional low-voltage electronics.</p><a class="button" href="/iron-kids/electronics/">Open R32 electronics ↗</a></section>'''),
'iron-kids/electronics/index.html':('IRON-KIDS R32 Electronics','Integrated removable NodeMCU/OLED interfaces','''<section class="shell page"><span class="eyebrow">R32 / Integrated electronics</span><h1>FUN INSIDE.<br><em>FREEDOM OUTSIDE.</em></h1><p class="lead">Defined chest and forearm interfaces, blanking lids, NodeMCU/OLED mounts, protected power, cable service, and electronics-free alternatives.</p><a class="button" href="/downloads/IRON_KIDS_K2_INTEGRATED_ELECTRONICS_R32.zip">Download R32 model ZIP ↗</a></section><section class="paper"><div class="shell"><h2>LOCAL MODULES. NO RESTRAINT AUTHORITY.</h2><div class="panel nodes"><article class="node"><b>Chest node</b><span>NodeMCU, OLED, comfort sensor, light status.</span></article><article class="node"><b>Arm nodes</b><span>Optional local OLED modules.</span></article><article class="node"><b>Protected USB</b><span>Enclosed power bank in breakaway pocket.</span></article><article class="node"><b>Physical authority</b><span>NONE.</span></article></div></div></section><section class="shell controls"><div><h2>Choose a configuration</h2><button class="toggle" aria-pressed="true" data-t="chest">Chest NodeMCU + OLED</button><button class="toggle" aria-pressed="false" data-t="left arm">Left forearm OLED</button><button class="toggle" aria-pressed="false" data-t="right arm">Right forearm OLED</button><button class="toggle" aria-pressed="true" data-t="power">Protected USB power</button></div><pre data-out></pre></section><section class="paper"><div class="shell"><div class="download"><h2>IRON-KIDS K2 Integrated Electronics R32</h2><p>20 printable STL parts, editable OpenSCAD source, firmware, wiring, BOM, manifest, and verification.</p><a class="button" href="/downloads/IRON_KIDS_K2_INTEGRATED_ELECTRONICS_R32.zip">Download ZIP</a></div></div></section>'''),
'build/index.html':('Build program','Evidence-gated build path','''<section class="shell page"><span class="eyebrow">Build program</span><h1>BUILD ONE<br><em>TRUTH AT A TIME.</em></h1><p class="lead">Measure, fit the textile/EVA carrier, print gauges, prove partial limbs, fit torso and helmet, then add removable electronics.</p></section>'''),
'evidence/index.html':('Evidence status','R32 evidence boundary','''<section class="shell page"><span class="eyebrow">Evidence ledger</span><h1>SHOW WHAT<br><em>IS ACTUALLY TRUE.</em></h1><p class="lead">R32 adds generated, non-empty electronics interface STLs and firmware references. It does not claim child fit or physical commissioning.</p></section>''')}
for rel,(title,desc,body) in pages.items():
    p=SITE/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(page(title,desc,body))
(SITE/'_headers').write_text('/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n  Permissions-Policy: camera=(), microphone=(), geolocation=()\n')
(SITE/'_redirects').write_text('/r32 /iron-kids/electronics/ 301\n/kids-electronics /iron-kids/electronics/ 301\n')
(SITE/'robots.txt').write_text('User-agent: *\nAllow: /\n')

missing=[]
for hp in SITE.rglob('*.html'):
    for raw in re.findall(r'(?:href|src)=["\']([^"\']+)',hp.read_text()):
        if raw.startswith(('http:','https:','#','mailto:','tel:')): continue
        target=raw.split('#')[0].split('?')[0]
        if not target: continue
        fp=SITE/target.lstrip('/') if target.startswith('/') else hp.parent/target
        if target.endswith('/'): fp=fp/'index.html'
        if not fp.exists(): missing.append({'page':str(hp.relative_to(SITE)),'target':raw})
(SITE/'R32_VERIFICATION.json').write_text(json.dumps({'release':'R32','html_pages':len(list(SITE.rglob('*.html'))),'model_parts':len(parts),'missing_references':missing,'root_index_exists':(SITE/'index.html').exists(),'embedded_model_zip_sha256':sha(model_zip)},indent=2))
print(json.dumps({'parts':len(parts),'pages':len(list(SITE.rglob('*.html'))),'missing':len(missing)},indent=2))
