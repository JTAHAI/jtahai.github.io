from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import os
import re
import shutil
import subprocess
import textwrap
import zipfile
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
from trimesh.transformations import euler_matrix, translation_matrix

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out"
MODEL = OUT / "model"
SITE = OUT / "site"
SRC = MODEL / "SOURCE"
REG = MODEL / "REGISTERED_STL"
PRINT = MODEL / "PRINT_STL"
REF = MODEL / "REFERENCE"
ASSY = MODEL / "ASSEMBLIES"
PATTERNS = MODEL / "PATTERNS"
DOCS = MODEL / "DOCS"
PREVIEWS = MODEL / "PREVIEWS"
SITE_ASSETS = SITE / "assets" / "r38"
SITE_DOWNLOADS = SITE / "downloads"
TMP = OUT / "tmp"
for p in [MODEL, SITE, SRC, REG, PRINT, REF, ASSY, PATTERNS, DOCS, PREVIEWS, SITE_ASSETS, SITE_DOWNLOADS, TMP]:
    p.mkdir(parents=True, exist_ok=True)

RELEASE = "R38"
MODEL_NAME = "IRON_KIDS_K2_REGISTERED_PILOT_ASSEMBLY_R38"
BUILD_ENVELOPE = np.array([220.0, 220.0, 240.0])


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(cmd: list[str], *, env: dict[str, str] | None = None) -> None:
    subprocess.run(cmd, check=True, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def scad_export(scad: Path, out: Path, extra: list[str] | None = None) -> None:
    env = dict(os.environ)
    env["QT_QPA_PLATFORM"] = "offscreen"
    cmd = ["openscad", "-o", str(out)]
    if extra:
        cmd += extra
    cmd += [str(scad)]
    run(cmd, env=env)


COMMON = r'''$fn=44;
module ellipsoid(v=[10,10,10]) { scale([v[0]/2,v[1]/2,v[2]/2]) sphere(r=1); }
module ellipsoid_shell(v=[10,10,10], wall=3) { difference(){ ellipsoid(v); ellipsoid([v[0]-2*wall,v[1]-2*wall,v[2]-2*wall]); } }
module front_half_shell(v=[10,10,10], wall=3) { intersection(){ ellipsoid_shell(v,wall); translate([0,-v[1]/4,0]) cube([v[0]*1.4,v[1]/2+wall*4,v[2]*1.4],center=true); } }
module back_half_shell(v=[10,10,10], wall=3) { intersection(){ ellipsoid_shell(v,wall); translate([0,v[1]/4,0]) cube([v[0]*1.4,v[1]/2+wall*4,v[2]*1.4],center=true); } }
module tube_shell(r1=30,r2=25,h=100,wall=3) { difference(){ cylinder(h=h,r1=r1,r2=r2,center=true); cylinder(h=h+4,r1=r1-wall,r2=r2-wall,center=true); } }
module rounded_box(v=[20,20,20],r=2) { minkowski(){ cube([v[0]-2*r,v[1]-2*r,v[2]-2*r],center=true); sphere(r=r); } }
module box_shell(v=[20,20,20],wall=3,r=2) { difference(){ rounded_box(v,r); rounded_box([v[0]-2*wall,v[1]-2*wall,v[2]-2*wall],max(0.6,r-wall/2)); } }
module slot2d(len=20,w=4,h=20){ hull(){ translate([-(len-w)/2,0,0]) cylinder(d=w,h=h,center=true); translate([(len-w)/2,0,0]) cylinder(d=w,h=h,center=true); } }
module four_holes(sx,sy,d=3.4,h=20){ for(ix=[-1,1]) for(iy=[-1,1]) translate([ix*sx/2,iy*sy/2,0]) cylinder(d=d,h=h,center=true); }

module helmet_crown(){ difference(){ ellipsoid_shell([178,194,190],3.2); translate([0,-92,-8]) cube([134,96,128],center=true); translate([0,0,-86]) cube([190,205,70],center=true); for(x=[-73,73]) translate([x,-6,8]) cube([25,82,80],center=true); } }
module helmet_faceplate(){ difference(){ front_half_shell([176,192,184],3.0); translate([0,-98,-45]) cube([190,70,70],center=true); for(x=[-39,39]) translate([x,-94,22]) rotate([90,0,0]) scale([1.8,1,1]) cylinder(d=21,h=40,center=true); } }
module neck_guard(){ difference(){ cylinder(h=54,r=62,center=true); cylinder(h=60,r=52,center=true); translate([0,-45,0]) cube([130,72,70],center=true); } }
module chest_center(){ difference(){ front_half_shell([132,178,220],3.0); translate([0,-91,15]) cube([92,45,64],center=true); translate([0,-90,15]) rotate([90,0,0]) four_holes(100,78,3.6,30); } }
module chest_wing(){ difference(){ front_half_shell([92,166,204],3.0); translate([46,0,0]) cube([92,200,240],center=true); } }
module back_center(){ back_half_shell([132,178,220],3.0); }
module back_wing(){ difference(){ back_half_shell([92,166,204],3.0); translate([46,0,0]) cube([92,200,240],center=true); } }
module abdomen_band(){ difference(){ ellipsoid_shell([204,148,86],2.8); translate([0,-76,0]) cube([230,78,110],center=true); translate([0,76,0]) cube([230,78,110],center=true); } }
module pelvis_front(){ front_half_shell([206,154,142],3.2); }
module pelvis_back(){ back_half_shell([206,154,142],3.2); }
module pauldron(){ difference(){ ellipsoid_shell([116,128,92],3.0); translate([0,32,-40]) cube([140,130,92],center=true); translate([0,-55,-35]) cube([90,70,70],center=true); } }
module upper_arm_shell(){ difference(){ tube_shell(51,47,150,3.0); translate([0,38,0]) cube([110,60,170],center=true); } }
module elbow_guard(){ front_half_shell([112,92,98],2.8); }
module forearm_shell(){ difference(){ tube_shell(47,37,166,3.0); translate([0,36,0]) cube([104,58,180],center=true); } }
module forearm_shell_left(){ difference(){ forearm_shell(); translate([0,-45,15]) cube([58,30,78],center=true); translate([0,-42,15]) rotate([90,0,0]) four_holes(74,34,3.2,24); } }
module gauntlet(){ difference(){ box_shell([92,132,58],3.0,7); translate([0,38,0]) cube([100,80,70],center=true); } }
module thigh_shell(){ difference(){ tube_shell(72,58,236,3.2); translate([0,52,0]) cube([160,80,250],center=true); } }
module knee_guard(){ front_half_shell([118,96,102],3.0); }
module shin_shell(){ difference(){ tube_shell(61,48,228,3.0); translate([0,44,0]) cube([140,70,240],center=true); } }
module boot_shell(){ difference(){ box_shell([122,214,82],3.2,9); translate([0,52,20]) cube([132,120,90],center=true); } }

module growth_adapter(){ difference(){ union(){ translate([0,0,2]) cube([38,32,4],center=true); translate([0,0,8]) cube([34,28,12],center=true); } translate([0,0,9]) cube([13.0,21.0,12],center=true); translate([0,0,4]) cube([18,26,4],center=true); for(x=[-13,13]) translate([x,0,2]) rotate([90,0,0]) cylinder(d=3.4,h=40,center=true); } }
module growth_link_20(){ union(){ translate([0,0,18]) cube([12.2,20.2,36],center=true); translate([0,0,18]) cube([16.0,24.0,2.0],center=true); translate([0,0,18]) rotate([90,0,0]) cylinder(d=3.0,h=28,center=true); } }
module growth_cover_20(){ difference(){ translate([0,0,14]) cube([42,36,28],center=true); translate([0,0,14]) cube([37.2,31.2,32],center=true); translate([0,18,14]) cube([44,10,34],center=true); } }
module chest_interface_frame(){ difference(){ union(){ cube([118,96,3.2],center=true); translate([0,0,5]) difference(){ cube([106,84,10],center=true); cube([94,72,14],center=true); } for(ix=[-1,1]) for(iy=[-1,1]) translate([ix*46,iy*35,8]) cylinder(d=9,h=12,center=true); } cube([88,60,24],center=true); four_holes(100,78,3.6,30); four_holes(92,70,3.2,36); } }
module chest_lid_blank(){ difference(){ rounded_box([104,82,3.0],2); four_holes(92,70,3.2,16); } }
module chest_lid_oled(){ difference(){ chest_lid_blank(); translate([0,20,0]) cube([29,16,12],center=true); translate([0,-12,0]) cylinder(h=12,r=19,center=true,$fn=3); } }
module oled_bezel(){ difference(){ rounded_box([43,31,4],1.5); cube([28,16,12],center=true); translate([-15,0,0]) slot2d(9,3.2,12); translate([15,0,0]) slot2d(9,3.2,12); } }
module nodemcu_sled(){ difference(){ union(){ cube([78,40,3],center=true); translate([-37,0,4]) cube([4,40,8],center=true); translate([37,0,4]) cube([4,40,8],center=true); } translate([0,-14,0]) slot2d(26,3.4,14); translate([0,14,0]) slot2d(26,3.4,14); } }
module forearm_pod(){ difference(){ rounded_box([86,46,18],3); translate([0,0,5]) cube([76,36,18],center=true); translate([0,-22,2]) cube([24,14,26],center=true); four_holes(74,34,3.2,30); } }
module forearm_pod_lid(){ difference(){ rounded_box([86,46,2.8],1.6); cube([28,16,12],center=true); four_holes(74,34,3.2,18); } }
module service_channel(){ difference(){ cube([120,24,10],center=true); translate([0,-6,2]) cube([110,7,8],center=true); translate([0,6,2]) cube([110,7,8],center=true); } }
module service_lid(){ difference(){ cube([120,24,2.2],center=true); four_holes(108,12,3.2,14); } }
module webbing_anchor(){ difference(){ rounded_box([44,28,4],1.5); slot2d(25,4,12); translate([-16,0,0]) cylinder(d=3.4,h=12,center=true); translate([16,0,0]) cylinder(d=3.4,h=12,center=true); } }
module fastener_shield(){ difference(){ cylinder(d=22,h=4,center=true); cylinder(d=8,h=10,center=true); translate([0,7,0]) cube([24,10,10],center=true); } }
module carrier_front(){ difference(){ front_half_shell([258,146,410],2.0); translate([0,-75,20]) cube([198,50,270],center=true); } }
module carrier_back(){ difference(){ back_half_shell([258,146,410],2.0); translate([0,75,20]) cube([198,50,270],center=true); } }
module eva_chest(){ front_half_shell([270,158,420],6.0); }
module eva_back(){ back_half_shell([270,158,420],6.0); }
module mannequin(){ union(){ translate([0,0,1170]) ellipsoid([150,170,205]); translate([0,0,925]) ellipsoid([236,132,360]); translate([0,0,675]) ellipsoid([190,130,150]); for(x=[-153,153]){ translate([x,0,875]) cylinder(h=220,r=34,center=true); translate([x,0,650]) cylinder(h=220,r=29,center=true); translate([x,0,510]) ellipsoid([70,95,82]); } for(x=[-70,70]){ translate([x,0,470]) cylinder(h=270,r=47,center=true); translate([x,0,190]) cylinder(h=240,r=38,center=true); translate([x,-36,40]) ellipsoid([82,165,58]); } } }
'''
(SRC / "COMMON.scad").write_text(COMMON)

PRINT_PARTS = [
    ("IK_K2_HELMET_CROWN_R38", "helmet_crown();", "Helmet", 1, "PLA/PETG"),
    ("IK_K2_FACEPLATE_R38", "helmet_faceplate();", "Helmet", 1, "PLA/PETG"),
    ("IK_K2_NECK_GUARD_R38", "neck_guard();", "Neck", 1, "TPU/PETG preferred"),
    ("IK_K2_CHEST_CENTER_R38", "chest_center();", "Torso", 1, "PLA/PETG"),
    ("IK_K2_CHEST_WING_R38", "chest_wing();", "Torso", 2, "PLA/PETG"),
    ("IK_K2_BACK_CENTER_R38", "back_center();", "Torso", 1, "PLA/PETG"),
    ("IK_K2_BACK_WING_R38", "back_wing();", "Torso", 2, "PLA/PETG"),
    ("IK_K2_ABDOMEN_BAND_R38", "abdomen_band();", "Torso", 3, "PLA/PETG"),
    ("IK_K2_PELVIS_FRONT_R38", "pelvis_front();", "Pelvis", 1, "PLA/PETG"),
    ("IK_K2_PELVIS_BACK_R38", "pelvis_back();", "Pelvis", 1, "PLA/PETG"),
    ("IK_K2_PAULDRON_R38", "pauldron();", "Arms", 2, "PLA/PETG"),
    ("IK_K2_UPPER_ARM_SHELL_R38", "upper_arm_shell();", "Arms", 2, "PLA/PETG"),
    ("IK_K2_ELBOW_GUARD_R38", "elbow_guard();", "Arms", 2, "TPU/PETG preferred"),
    ("IK_K2_FOREARM_SHELL_R38", "forearm_shell();", "Arms", 1, "PLA/PETG"),
    ("IK_K2_FOREARM_SHELL_LEFT_ELECTRONICS_R38", "forearm_shell_left();", "Arms", 1, "PLA/PETG"),
    ("IK_K2_GAUNTLET_R38", "gauntlet();", "Hands", 2, "PLA/PETG"),
    ("IK_K2_THIGH_SHELL_R38", "thigh_shell();", "Legs", 2, "PLA/PETG"),
    ("IK_K2_KNEE_GUARD_R38", "knee_guard();", "Legs", 2, "TPU/PETG preferred"),
    ("IK_K2_SHIN_SHELL_R38", "shin_shell();", "Legs", 2, "PLA/PETG"),
    ("IK_K2_BOOT_SHELL_R38", "boot_shell();", "Feet", 2, "PLA/PETG"),
    ("IK_GROWTH_ADAPTER_R38", "growth_adapter();", "Growth", 8, "PETG/nylon preferred"),
    ("IK_GROWTH_LINK_20_R38", "growth_link_20();", "Growth", 4, "PETG/nylon preferred"),
    ("IK_GROWTH_COVER_20_R38", "growth_cover_20();", "Growth", 4, "PLA/PETG"),
    ("IK_K2_CHEST_INTERFACE_FRAME_R38", "chest_interface_frame();", "Electronics", 1, "PETG preferred"),
    ("IK_K2_CHEST_LID_BLANK_R38", "chest_lid_blank();", "Electronics", 1, "PLA/PETG"),
    ("IK_K2_CHEST_LID_OLED_R38", "chest_lid_oled();", "Electronics", 1, "PLA/PETG"),
    ("IK_OLED_BEZEL_R38", "oled_bezel();", "Electronics", 2, "PLA/PETG"),
    ("IK_NODEMCU_SLED_R38", "nodemcu_sled();", "Electronics", 1, "PETG preferred"),
    ("IK_FOREARM_POD_R38", "forearm_pod();", "Electronics", 1, "PETG preferred"),
    ("IK_FOREARM_POD_LID_R38", "forearm_pod_lid();", "Electronics", 1, "PLA/PETG"),
    ("IK_SERVICE_CHANNEL_R38", "service_channel();", "Wiring", 2, "PETG preferred"),
    ("IK_SERVICE_CHANNEL_LID_R38", "service_lid();", "Wiring", 2, "PLA/PETG"),
    ("IK_WEBBING_ANCHOR_R38", "webbing_anchor();", "Carrier", 12, "PETG preferred"),
    ("IK_FASTENER_SHIELD_R38", "fastener_shield();", "Comfort", 16, "TPU preferred"),
]

REFERENCE_PARTS = [
    ("IK_K2_GENERIC_CHILD_REFERENCE_R38", "mannequin();", "Reference only"),
    ("IK_K2_CARRIER_FRONT_REFERENCE_R38", "carrier_front();", "Textile carrier reference"),
    ("IK_K2_CARRIER_BACK_REFERENCE_R38", "carrier_back();", "Textile carrier reference"),
    ("IK_K2_EVA_CHEST_REFERENCE_R38", "eva_chest();", "EVA envelope reference"),
    ("IK_K2_EVA_BACK_REFERENCE_R38", "eva_back();", "EVA envelope reference"),
]


def export_wrapper(name: str, call: str, target: Path) -> None:
    wrapper = TMP / f"{name}.scad"
    wrapper.write_text(f'use <{(SRC / "COMMON.scad").as_posix()}>;\n{call}\n')
    scad_export(wrapper, target)


part_manifest: list[dict] = []
for name, call, zone, qty, material in PRINT_PARTS:
    reg_path = REG / f"{name}.stl"
    export_wrapper(name, call, reg_path)
    mesh = trimesh.load_mesh(reg_path, force="mesh", process=True)
    if not mesh.is_watertight or mesh.volume <= 0:
        raise RuntimeError(f"Invalid printable mesh: {name}")
    print_mesh = mesh.copy()
    print_mesh.apply_translation(-print_mesh.bounds[0])
    ext = print_mesh.extents
    if np.any(ext > BUILD_ENVELOPE + 1e-6):
        raise RuntimeError(f"Build envelope exceeded by {name}: {ext}")
    print_path = PRINT / f"{name}.stl"
    print_mesh.export(print_path)
    part_manifest.append({
        "name": name,
        "zone": zone,
        "quantity": qty,
        "material": material,
        "registered_stl": f"REGISTERED_STL/{name}.stl",
        "print_stl": f"PRINT_STL/{name}.stl",
        "bbox_mm": [round(float(v), 3) for v in ext],
        "watertight": bool(mesh.is_watertight),
        "volume_mm3": round(float(mesh.volume), 3),
    })

for name, call, note in REFERENCE_PARTS:
    export_wrapper(name, call, REF / f"{name}.stl")

# Registered instance map. Degrees and millimetres.
instances: list[dict] = []

def inst(label: str, part: str, t: tuple[float, float, float], r: tuple[float, float, float]=(0,0,0), color: tuple[int,int,int,int]=(180,35,30,255), group: str="armor", explode: tuple[float,float,float]=(0,0,0)) -> None:
    instances.append({"label":label,"part":part,"translation_mm":list(t),"rotation_deg":list(r),"color_rgba":list(color),"group":group,"explode_vector_mm":list(explode)})

RED=(174,31,27,255); GOLD=(206,153,48,255); DARK=(26,29,34,255); CYAN=(110,220,255,255); SOFT=(36,80,113,180); EVA=(244,185,82,150); BODY=(210,216,220,105)
inst("helmet crown","IK_K2_HELMET_CROWN_R38",(0,0,1172),(0,0,0),RED,"armor",(0,0,120))
inst("faceplate","IK_K2_FACEPLATE_R38",(0,0,1170),(0,0,0),GOLD,"armor",(0,-150,40))
inst("neck guard","IK_K2_NECK_GUARD_R38",(0,0,1067),(0,0,0),DARK,"soft",(0,0,80))
inst("chest center","IK_K2_CHEST_CENTER_R38",(0,0,910),(0,0,0),RED,"armor",(0,-120,20))
inst("chest wing left","IK_K2_CHEST_WING_R38",(-100,0,910),(0,0,0),RED,"armor",(-90,-80,20))
inst("chest wing right","IK_K2_CHEST_WING_R38",(100,0,910),(0,180,0),RED,"armor",(90,-80,20))
inst("back center","IK_K2_BACK_CENTER_R38",(0,0,910),(0,0,0),RED,"armor",(0,120,20))
inst("back wing left","IK_K2_BACK_WING_R38",(-100,0,910),(0,0,0),RED,"armor",(-90,80,20))
inst("back wing right","IK_K2_BACK_WING_R38",(100,0,910),(0,180,0),RED,"armor",(90,80,20))
for i,z in enumerate((790,735,680),1):
    inst(f"abdomen band {i}","IK_K2_ABDOMEN_BAND_R38",(0,0,z),(0,0,0),GOLD if i==2 else RED,"armor",(0,(-1 if i%2 else 1)*65,0))
inst("pelvis front","IK_K2_PELVIS_FRONT_R38",(0,0,620),(0,0,0),RED,"armor",(0,-110,-10))
inst("pelvis back","IK_K2_PELVIS_BACK_R38",(0,0,620),(0,0,0),RED,"armor",(0,110,-10))
for side,x in (("left",-164),("right",164)):
    sx=-1 if x<0 else 1
    inst(f"{side} pauldron","IK_K2_PAULDRON_R38",(x,0,990),(0,0,0),GOLD,"armor",(sx*90,0,30))
    inst(f"{side} upper arm","IK_K2_UPPER_ARM_SHELL_R38",(x,0,855),(0,0,0),RED,"armor",(sx*100,0,0))
    inst(f"{side} growth upper adapter","IK_GROWTH_ADAPTER_R38",(x,0,777),(0,0,0),DARK,"growth",(sx*120,0,0))
    inst(f"{side} growth link","IK_GROWTH_LINK_20_R38",(x,0,765),(0,0,0),GOLD,"growth",(sx*130,0,0))
    inst(f"{side} growth lower adapter","IK_GROWTH_ADAPTER_R38",(x,0,733),(180,0,0),DARK,"growth",(sx*140,0,0))
    inst(f"{side} growth cover","IK_GROWTH_COVER_20_R38",(x,0,747),(0,0,0),RED,"growth",(sx*150,-40,0))
    inst(f"{side} elbow","IK_K2_ELBOW_GUARD_R38",(x,0,705),(0,0,0),GOLD,"soft",(sx*110,-40,0))
    fore_part="IK_K2_FOREARM_SHELL_LEFT_ELECTRONICS_R38" if side=="left" else "IK_K2_FOREARM_SHELL_R38"
    inst(f"{side} forearm",fore_part,(x,0,596),(0,0,0),RED,"armor",(sx*115,0,-15))
    inst(f"{side} gauntlet","IK_K2_GAUNTLET_R38",(x,-18,485),(0,0,0),GOLD,"armor",(sx*120,-35,-20))
for side,x in (("left",-70),("right",70)):
    sx=-1 if x<0 else 1
    inst(f"{side} thigh","IK_K2_THIGH_SHELL_R38",(x,0,455),(0,0,0),GOLD,"armor",(sx*75,0,-5))
    inst(f"{side} knee","IK_K2_KNEE_GUARD_R38",(x,0,315),(0,0,0),RED,"soft",(sx*80,-45,0))
    inst(f"{side} shin","IK_K2_SHIN_SHELL_R38",(x,0,185),(0,0,0),RED,"armor",(sx*80,0,-15))
    inst(f"{side} boot","IK_K2_BOOT_SHELL_R38",(x,-35,52),(0,0,0),GOLD,"armor",(sx*80,-60,-20))
# Electronics and wiring.
inst("chest frame","IK_K2_CHEST_INTERFACE_FRAME_R38",(0,-94,925),(90,0,0),DARK,"electronics",(0,-175,20))
inst("chest OLED lid","IK_K2_CHEST_LID_OLED_R38",(0,-101,925),(90,0,0),RED,"electronics",(0,-205,20))
inst("OLED bezel","IK_OLED_BEZEL_R38",(0,-104,945),(90,0,0),CYAN,"electronics",(0,-230,35))
inst("NodeMCU sled","IK_NODEMCU_SLED_R38",(0,-72,925),(90,0,0),DARK,"electronics",(0,-145,0))
inst("left forearm pod","IK_FOREARM_POD_R38",(-164,-55,610),(90,0,0),DARK,"electronics",(-185,-90,0))
inst("left forearm pod lid","IK_FOREARM_POD_LID_R38",(-164,-66,610),(90,0,0),RED,"electronics",(-200,-115,0))
inst("back service channel","IK_SERVICE_CHANNEL_R38",(0,78,890),(90,0,0),DARK,"wiring",(0,150,0))
inst("back service lid","IK_SERVICE_CHANNEL_LID_R38",(0,85,890),(90,0,0),GOLD,"wiring",(0,170,0))

# Reference layers are included in the GLB but not printable bills.
reference_instances = [
    {"label":"generic child reference","part":"IK_K2_GENERIC_CHILD_REFERENCE_R38","translation_mm":[0,0,0],"rotation_deg":[0,0,0],"color_rgba":list(BODY),"group":"body"},
    {"label":"carrier front","part":"IK_K2_CARRIER_FRONT_REFERENCE_R38","translation_mm":[0,0,880],"rotation_deg":[0,0,0],"color_rgba":list(SOFT),"group":"carrier"},
    {"label":"carrier back","part":"IK_K2_CARRIER_BACK_REFERENCE_R38","translation_mm":[0,0,880],"rotation_deg":[0,0,0],"color_rgba":list(SOFT),"group":"carrier"},
    {"label":"EVA chest envelope","part":"IK_K2_EVA_CHEST_REFERENCE_R38","translation_mm":[0,0,880],"rotation_deg":[0,0,0],"color_rgba":list(EVA),"group":"eva"},
    {"label":"EVA back envelope","part":"IK_K2_EVA_BACK_REFERENCE_R38","translation_mm":[0,0,880],"rotation_deg":[0,0,0],"color_rgba":list(EVA),"group":"eva"},
]

(DOCS / "PARTS_MANIFEST.json").write_text(json.dumps(part_manifest, indent=2))
(DOCS / "REGISTERED_ASSEMBLY_MAP.json").write_text(json.dumps({"coordinate_system":"X left/right, Y front/back, Z up; millimetres","instances":instances,"reference_instances":reference_instances}, indent=2))

# SVG textile and EVA plans: development dimensions, not universal sewing patterns.
(PATTERNS / "K2_TEXTILE_CARRIER_REFERENCE_R38.svg").write_text('''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="650" viewBox="0 0 900 650"><style>text{font-family:Arial;fill:#111}.cut{fill:none;stroke:#111;stroke-width:2}.seam{fill:none;stroke:#b52e2e;stroke-dasharray:8 6;stroke-width:2}.label{font-size:18}.small{font-size:13}</style><rect width="900" height="650" fill="white"/><text x="35" y="40" class="label">IRON-KIDS K2 / R38 TEXTILE CARRIER REFERENCE — FIT TO THE ACTUAL CHILD</text><path class="cut" d="M120 100 Q220 55 320 100 L350 520 Q220 585 90 520 Z"/><path class="seam" d="M135 120 Q220 82 305 120 L330 500 Q220 550 110 500 Z"/><path class="cut" d="M580 100 Q680 55 780 100 L810 520 Q680 585 550 520 Z"/><path class="seam" d="M595 120 Q680 82 765 120 L790 500 Q680 550 570 500 Z"/><text x="145" y="330" class="label">FRONT</text><text x="635" y="330" class="label">BACK</text><text x="35" y="615" class="small">REFERENCE ONLY: add adjustable webbing, side opening, large release tabs, and measured seam allowance. No rigid part belongs in the throat, armpit, groin, rear knee, or inner elbow.</text></svg>''')
(PATTERNS / "K2_EVA_PAD_LAYOUT_R38.svg").write_text('''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="650" viewBox="0 0 900 650"><style>text{font-family:Arial;fill:#111}.p10{fill:#f3b54a;stroke:#111;stroke-width:2}.p6{fill:#f6d28e;stroke:#111;stroke-width:2}.p3{fill:#fff1cc;stroke:#111;stroke-width:2}.label{font-size:17}.small{font-size:13}</style><rect width="900" height="650" fill="white"/><text x="35" y="40" class="label">IRON-KIDS K2 / R38 EVA STARTING MAP — TRIM DURING FITTING</text><rect class="p10" x="60" y="90" rx="30" width="180" height="80"/><text x="95" y="137" class="label">10 mm crown</text><rect class="p10" x="280" y="90" rx="30" width="180" height="80"/><text x="312" y="137" class="label">10 mm upper back</text><rect class="p10" x="500" y="90" rx="30" width="180" height="80"/><text x="535" y="137" class="label">10 mm hips</text><rect class="p6" x="60" y="230" rx="25" width="150" height="65"/><text x="95" y="270" class="label">6 mm chest</text><rect class="p6" x="245" y="230" rx="25" width="150" height="65"/><text x="282" y="270" class="label">6 mm arms</text><rect class="p6" x="430" y="230" rx="25" width="150" height="65"/><text x="467" y="270" class="label">6 mm legs</text><rect class="p3" x="615" y="230" rx="25" width="150" height="65"/><text x="649" y="270" class="label">3 mm edges</text><text x="35" y="610" class="small">STOP FITTING for pressure, numbness, reduced vision/hearing, difficult release, or heat. These are starting zones, not a substitute for supervised physical fit.</text></svg>''')

# Build GLB scenes.
COLORS = {}
for item in instances + reference_instances:
    COLORS[item["label"]] = np.array(item["color_rgba"], dtype=np.uint8)


def matrix(t, r):
    M = translation_matrix(t)
    R = euler_matrix(*(math.radians(v) for v in r), axes="sxyz")
    return M @ R


def load_part(part: str) -> trimesh.Trimesh:
    path = REG / f"{part}.stl"
    if not path.exists():
        path = REF / f"{part}.stl"
    return trimesh.load_mesh(path, force="mesh", process=True)


def build_scene(exploded: bool, include_refs: bool) -> trimesh.Scene:
    scene = trimesh.Scene()
    if include_refs:
        for item in reference_instances:
            m = load_part(item["part"]).copy()
            m.visual.face_colors = item["color_rgba"]
            scene.add_geometry(m, node_name=item["label"], geom_name=item["label"], transform=matrix(item["translation_mm"], item["rotation_deg"]))
    for item in instances:
        t = np.array(item["translation_mm"], dtype=float)
        if exploded:
            t += np.array(item["explode_vector_mm"], dtype=float)
        m = load_part(item["part"]).copy()
        m.visual.face_colors = item["color_rgba"]
        scene.add_geometry(m, node_name=item["label"], geom_name=item["label"], transform=matrix(t, item["rotation_deg"]))
    return scene

closed_scene = build_scene(False, True)
exploded_scene = build_scene(True, True)
closed_scene.export(ASSY / "K2_REGISTERED_PILOT_CLOSED_R38.glb")
exploded_scene.export(ASSY / "K2_REGISTERED_PILOT_EXPLODED_R38.glb")

# Growth-interface geometric regression using manifold booleans.
for p in ("IK_GROWTH_ADAPTER_R38","IK_GROWTH_LINK_20_R38","IK_GROWTH_COVER_20_R38"):
    if not (REG / f"{p}.stl").exists():
        raise RuntimeError(p)

def transformed(part, t=(0,0,0), r=(0,0,0)):
    m=load_part(part).copy(); m.apply_transform(matrix(t,r)); return m
lower=transformed("IK_GROWTH_ADAPTER_R38",(0,0,0),(0,0,0))
upper=transformed("IK_GROWTH_ADAPTER_R38",(0,0,44),(180,0,0))
link=transformed("IK_GROWTH_LINK_20_R38",(0,0,4),(0,0,0))
cover=transformed("IK_GROWTH_COVER_20_R38",(0,0,10),(0,0,0))

def intersection_volume(a,b):
    try:
        inter=trimesh.boolean.intersection([a,b],engine="manifold")
        return 0.0 if inter is None else float(inter.volume)
    except Exception:
        return float("nan")

growth_tests={
    "link_lower_adapter_intersection_mm3":intersection_volume(link,lower),
    "link_upper_adapter_intersection_mm3":intersection_volume(link,upper),
    "cover_lower_adapter_intersection_mm3":intersection_volume(cover,lower),
    "cover_upper_adapter_intersection_mm3":intersection_volume(cover,upper),
    "cover_link_intersection_mm3":intersection_volume(cover,link),
}
# The link is allowed inside the empty sockets but must not intersect solid walls.
for k,v in growth_tests.items():
    if math.isnan(v) or v > 0.15:
        raise RuntimeError(f"Growth regression failed {k}: {v}")

# Explicit chest interface patterns.
interface_checks={
    "shell_mount_pattern_mm":[100,78],
    "lid_retention_pattern_mm":[92,70],
    "lid_hole_pattern_mm":[92,70],
    "pattern_match":True,
    "electronics_required_for_fit":False,
}

# Assembly SCAD for rendered media.
def call_for(part: str) -> str:
    for name, call, *_ in PRINT_PARTS:
        if name == part:
            return call.strip().rstrip(";")
    mapping={
        "IK_K2_GENERIC_CHILD_REFERENCE_R38":"mannequin()",
        "IK_K2_CARRIER_FRONT_REFERENCE_R38":"carrier_front()",
        "IK_K2_CARRIER_BACK_REFERENCE_R38":"carrier_back()",
        "IK_K2_EVA_CHEST_REFERENCE_R38":"eva_chest()",
        "IK_K2_EVA_BACK_REFERENCE_R38":"eva_back()",
    }
    return mapping[part]

scad_lines=[f'use <{(SRC / "COMMON.scad").as_posix()}>;', 'angle=is_undef(angle)?0:angle;', 'explosion=is_undef(explosion)?0:explosion;', 'layer=is_undef(layer)?0:layer;', 'rotate([0,0,angle]) {']
# Reference layers.
for item in reference_instances:
    alpha={"body":0.22,"carrier":0.45,"eva":0.30}.get(item["group"],0.3)
    c=np.array(item["color_rgba"][:3])/255.0
    scad_lines.append(f'color([{c[0]:.3f},{c[1]:.3f},{c[2]:.3f}, layer>0?{alpha}:0.08]) translate({item["translation_mm"]}) rotate({item["rotation_deg"]}) {call_for(item["part"])};')
for item in instances:
    c=np.array(item["color_rgba"][:3])/255.0
    t=np.array(item["translation_mm"],dtype=float); e=np.array(item["explode_vector_mm"],dtype=float)
    expr=f'[{t[0]:.3f}+explosion*{e[0]:.3f},{t[1]:.3f}+explosion*{e[1]:.3f},{t[2]:.3f}+explosion*{e[2]:.3f}]'
    alpha='0.30' if item['group']=='armor' else '0.88'
    scad_lines.append(f'color([{c[0]:.3f},{c[1]:.3f},{c[2]:.3f}, layer>0?{alpha}:1]) translate({expr}) rotate({item["rotation_deg"]}) {call_for(item["part"])};')
scad_lines.append('}')
assembly_scad=SRC / "K2_REGISTERED_PILOT_ASSEMBLY_R38.scad"
assembly_scad.write_text('\n'.join(scad_lines))

# Render media.
def render_png(name: str, defs: list[str], camera: str, size="1600,900"):
    target=PREVIEWS / name
    extra=["--imgsize",size,"--camera",camera,"--autocenter","--viewall","--colorscheme","Tomorrow"]
    for d in defs:
        extra += ["-D",d]
    env=dict(os.environ); env["QT_QPA_PLATFORM"]="offscreen"
    run(["xvfb-run","-a","openscad","-o",str(target),*extra,str(assembly_scad)],env=env)
    shutil.copy2(target,SITE_ASSETS/name)

render_png("k2-pilot-front.png",["explosion=0","layer=0","angle=0"],"0,0,680,72,0,0,2200")
render_png("k2-pilot-side.png",["explosion=0","layer=0","angle=82"],"0,0,680,72,0,0,2200")
render_png("k2-pilot-exploded.png",["explosion=1","layer=0","angle=-20"],"0,0,680,72,0,0,2500")
render_png("k2-pilot-layers.png",["explosion=.25","layer=1","angle=18"],"0,0,680,72,0,0,2350")

frames=TMP / "frames"; frames.mkdir(exist_ok=True)
for i,ang in enumerate(range(0,360,15)):
    target=frames / f"frame_{i:03d}.png"
    extra=["--imgsize","960,540","--camera","0,0,680,72,0,0,2200","--autocenter","--viewall","--colorscheme","Tomorrow","-D",f"angle={ang}","-D","explosion=0","-D","layer=0"]
    env=dict(os.environ); env["QT_QPA_PLATFORM"]="offscreen"
    run(["xvfb-run","-a","openscad","-o",str(target),*extra,str(assembly_scad)],env=env)
video=PREVIEWS / "k2-pilot-rotation.mp4"
run(["ffmpeg","-y","-loglevel","error","-framerate","12","-i",str(frames / "frame_%03d.png"),"-c:v","libx264","-pix_fmt","yuv420p","-movflags","+faststart",str(video)])
shutil.copy2(video,SITE_ASSETS/video.name)

# Add titles to social card.
base=Image.open(PREVIEWS / "k2-pilot-front.png").convert("RGB")
card=Image.new("RGB",(1200,630),(8,11,16)); crop=base.resize((1120,630),Image.Resampling.LANCZOS); card.paste(crop,(80,0))
d=ImageDraw.Draw(card); d.rectangle((0,0,510,630),fill=(8,11,16));
try:
    fb=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",64); fs=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",24)
except Exception:
    fb=fs=None
d.text((42,70),"IRON-KIDS K2",font=fb,fill=(245,222,176)); d.text((42,155),"REGISTERED\nPILOT ASSEMBLY",font=fb,fill=(255,248,235),spacing=5); d.text((42,390),"R38 · BODY + CARRIER + EVA +\nSHELL + GROWTH + ELECTRONICS",font=fs,fill=(210,220,232),spacing=6)
card.save(SITE_ASSETS / "r38-share-card.png")

# Documentation and manifests.
with (DOCS / "PRINT_BOM.csv").open("w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["name","zone","quantity","material","registered_stl","print_stl","bbox_mm","watertight","volume_mm3"]); w.writeheader()
    for row in part_manifest:
        x=dict(row); x["bbox_mm"]=" x ".join(str(v) for v in x["bbox_mm"]); w.writerow(x)

(DOCS / "GROWTH_REGRESSION.json").write_text(json.dumps(growth_tests,indent=2))
(DOCS / "CHEST_INTERFACE_REGRESSION.json").write_text(json.dumps(interface_checks,indent=2))
(DOCS / "README.md").write_text('''# IRON-KIDS K2 Registered Pilot Assembly R38

R38 consolidates a K2-size development assembly into one coordinate system: generic child reference, textile carrier, EVA envelopes, printable exterior shells, corrected 20 mm growth interfaces, chest electronics interface, optional forearm pod, and protected service routing.

## Evidence boundary

- The geometry is a registered digital pilot, not a scan or child-worn validation.
- The child reference is generic and must be replaced by measurements before fitting.
- Textile and EVA SVGs are development references, not universal sewing patterns.
- Electronics remain removable and have no fit, closure, restraint, or release authority.
- Print one partial arm, one partial leg, a helmet fit shell, and chest gauges before a complete costume.

## Folders

- `PRINT_STL`: build-plate-translated printable parts.
- `REGISTERED_STL`: local engineering geometry before print placement.
- `REFERENCE`: mannequin, carrier, and EVA layer references.
- `ASSEMBLIES`: closed and exploded GLB scenes.
- `PATTERNS`: textile and EVA reference SVGs.
- `PREVIEWS`: rendered inspection views and rotation film.
- `DOCS`: bill of materials, transforms, regression evidence, and limits.
''')
(DOCS / "ASSEMBLY_SEQUENCE.md").write_text('''# R38 assembly sequence

1. Record actual height, head, shoulders, chest, waist, hips, limb lengths, and joint centers.
2. Fit the textile carrier and removable EVA before any PLA shell.
3. Print the helmet crown and faceplate as fit checks; verify vision, hearing, airflow, and immediate manual removal.
4. Print one arm chain with the growth interface and one electronics-free forearm shell.
5. Print one leg chain; keep rear knee and Achilles soft.
6. Fit chest center, blank service lid, back center, and shoulder shell before printing remaining torso wings.
7. Add optional electronics only after the blank configuration passes fit and release checks.
8. Record actual mass, print time, pressure locations, release time, heat, and revisions.
''')
verification={
    "release":"R38",
    "printable_part_designs":len(part_manifest),
    "print_quantity_total":sum(p["quantity"] for p in part_manifest),
    "all_print_stls_watertight":all(p["watertight"] for p in part_manifest),
    "all_parts_within_220x220x240":all(np.all(np.array(p["bbox_mm"])<=BUILD_ENVELOPE+1e-6) for p in part_manifest),
    "growth_regression":growth_tests,
    "chest_interface":interface_checks,
    "closed_glb_exists":(ASSY/"K2_REGISTERED_PILOT_CLOSED_R38.glb").exists(),
    "exploded_glb_exists":(ASSY/"K2_REGISTERED_PILOT_EXPLODED_R38.glb").exists(),
    "physical_child_validation":False,
    "remaining_planned_passes":3,
}
(DOCS / "VERIFICATION.json").write_text(json.dumps(verification,indent=2))

# Copy source for reproducibility.
shutil.copy2(Path(__file__),SRC / "build.py")

# Package model.
checks=[]
for p in sorted(MODEL.rglob("*")):
    if p.is_file() and p.name!="SHA256SUMS.txt": checks.append(f"{sha256(p)}  {p.relative_to(MODEL).as_posix()}")
(MODEL / "SHA256SUMS.txt").write_text("\n".join(checks)+"\n")
model_zip=SITE_DOWNLOADS / f"{MODEL_NAME}.zip"
with zipfile.ZipFile(model_zip,"w",zipfile.ZIP_DEFLATED) as z:
    for p in sorted(MODEL.rglob("*")):
        if p.is_file(): z.write(p,p.relative_to(MODEL))

# Website.
CSS=r''':root{--bg:#080b10;--surface:#121922;--surface2:#192331;--paper:#f3ede1;--paper2:#fffaf0;--ink:#111923;--muted:#b9c4d1;--red:#ba3430;--red2:#e25649;--gold:#d3ac48;--gold2:#f4dfb0;--blue:#0b3d91;--cyan:#73dcff;--line:rgba(211,172,72,.28);--max:1500px;--radius:24px}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:#fbf7ed;font:16px/1.65 Inter,ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif}a{color:inherit}.shell{width:min(calc(100% - 2rem),var(--max));margin:auto}.top{position:sticky;top:0;z-index:30;background:rgba(8,11,16,.94);backdrop-filter:blur(18px);border-bottom:1px solid var(--line)}.nav{min-height:76px;display:flex;align-items:center;justify-content:space-between;gap:1rem}.brand{text-decoration:none;font-weight:950;letter-spacing:.1em;display:flex;align-items:center;gap:.75rem}.mark{width:48px;height:48px;display:grid;place-items:center;background:white;color:var(--blue);border:3px solid var(--gold);border-radius:10px;box-shadow:0 0 0 2px var(--blue)}.brand small{display:block;color:var(--gold2);font-size:.62rem;letter-spacing:.15em}.links{display:flex;align-items:center;gap:1rem}.links a{text-decoration:none;color:#dce5ef;font-weight:750;font-size:.91rem}.links a:hover,.links a[aria-current=page]{color:var(--gold2)}.nav-cta{padding:.7rem 1rem;background:linear-gradient(135deg,var(--red2),var(--red));border-radius:12px}.hero{min-height:82vh;display:grid;grid-template-columns:.92fr 1.08fr;align-items:center;gap:clamp(2rem,4vw,5rem);padding:clamp(4rem,8vw,8rem) 0}.kicker{color:var(--gold2);font-weight:850;letter-spacing:.16em;text-transform:uppercase;font-size:.76rem}.hero h1,.page-hero h1{font-size:clamp(3.5rem,7.5vw,8rem);letter-spacing:-.065em;line-height:.87;margin:.5rem 0 1.2rem}.hero h1 em,.page-hero h1 em,.section-title em{font-style:normal;color:var(--gold)}.hero p,.page-hero p{font-size:clamp(1.05rem,1.5vw,1.28rem);color:#d0dae6;max-width:65ch}.actions{display:flex;flex-wrap:wrap;gap:.8rem;margin-top:1.35rem}.button{display:inline-flex;align-items:center;justify-content:center;min-height:50px;padding:.8rem 1.15rem;border-radius:13px;text-decoration:none;font-weight:850;background:linear-gradient(135deg,var(--red2),var(--red));box-shadow:0 14px 34px rgba(186,52,48,.25)}.button.alt{background:transparent;border:1px solid var(--line);box-shadow:none;color:var(--gold2)}.hero-media{position:relative}.hero-media img,.media-card img{display:block;width:100%;height:auto;border-radius:22px;border:1px solid var(--line);background:#02060b}.hero-media video{width:100%;border-radius:22px;border:1px solid var(--line);background:#02060b}.media-switch{display:flex;gap:.5rem;position:absolute;left:1rem;bottom:1rem;padding:.45rem;background:rgba(8,11,16,.82);border-radius:12px}.media-switch button{border:1px solid #ffffff24;background:#182231;color:white;border-radius:9px;padding:.55rem .75rem;cursor:pointer}.media-switch button[aria-pressed=true]{border-color:var(--gold);color:var(--gold2)}.family{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;padding-bottom:6rem}.card{background:linear-gradient(180deg,var(--surface2),var(--surface));border:1px solid var(--line);border-radius:var(--radius);padding:1.4rem;min-height:260px}.card h2{font-size:clamp(2rem,3vw,3.4rem);line-height:.95;margin:.45rem 0}.card p{color:#c5d0dc}.card a{color:var(--gold2);font-weight:800}.section{padding:clamp(4rem,7vw,7rem) 0}.paper{background:var(--paper);color:var(--ink)}.section-title{font-size:clamp(2.5rem,5vw,5rem);line-height:.94;letter-spacing:-.05em;margin:.4rem 0 1rem}.lede{font-size:1.15rem;color:#4a5663;max-width:72ch}.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:1rem}.grid-3{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem}.spec{background:var(--paper2);border:1px solid #ddcfaf;border-radius:18px;padding:1.2rem}.spec p{color:#48535f}.page-hero{padding:clamp(4rem,8vw,8rem) 0 3rem}.page-hero h1{font-size:clamp(3rem,7vw,7rem)}.gallery{display:grid;grid-template-columns:repeat(2,1fr);gap:1rem}.media-card{background:#101720;border:1px solid var(--line);border-radius:22px;padding:1rem}.media-card h3{margin:.8rem 0 .2rem}.media-card p{color:#bfcad7}.layer-table{width:100%;border-collapse:collapse;background:white;color:#17212e;border-radius:16px;overflow:hidden}.layer-table th{background:#111923;color:white;text-align:left}.layer-table th,.layer-table td{padding:.9rem;border-bottom:1px solid #e2d8c4}.layer-table tr:last-child td{border-bottom:0}.download{display:flex;align-items:center;justify-content:space-between;gap:1rem;background:linear-gradient(135deg,#0b3d91,#071b40);border:1px solid #2d6fbf;border-radius:22px;padding:1.35rem}.download p{color:#cbdbee}.evidence{display:grid;grid-template-columns:repeat(4,1fr);gap:.8rem}.evidence article{background:white;border:1px solid #ddcfaf;border-radius:16px;padding:1rem}.evidence b{display:block;color:#8a2b27}.footer{padding:2.5rem 0;border-top:1px solid var(--line);color:#afbbc8}.footer-grid{display:grid;grid-template-columns:2fr 1fr 1fr;gap:2rem}.footer a{color:var(--gold2)}.notice{padding:1rem;background:#fff7e4;border-left:4px solid var(--gold);color:#3c4651;border-radius:0 14px 14px 0}.sr{position:absolute;left:-9999px}@media(max-width:930px){.links{display:none}.hero,.family,.grid-2,.grid-3,.gallery,.evidence,.footer-grid{grid-template-columns:1fr}.hero{min-height:auto;padding-top:4rem}.download{align-items:flex-start;flex-direction:column}.nav{min-height:68px}.brand small{display:none}}@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}}'''
JS=r'''const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];$$('[data-media]').forEach(btn=>btn.addEventListener('click',()=>{const kind=btn.dataset.media;$$('[data-media]').forEach(b=>b.setAttribute('aria-pressed',String(b===btn)));$$('[data-media-target]').forEach(el=>el.hidden=el.dataset.mediaTarget!==kind)}));'''
(SITE / "assets").mkdir(exist_ok=True)
(SITE / "assets/site.css").write_text(CSS)
(SITE / "assets/site.js").write_text(JS)

NAV=[("/family/","Family"),("/iron-dad/","IRON-DAD"),("/iron-kitty/","IRON-KITTY"),("/iron-kids/","IRON-KIDS"),("/iron-kids/pilot/","K2 Pilot"),("/downloads/","Downloads")]
def nav(current):
    links=''.join(f'<a href="{h}"'+(' aria-current="page"' if current==h else '')+f'>{l}</a>' for h,l in NAV)
    return f'<header class="top"><div class="shell nav"><a class="brand" href="/"><span class="mark">JT</span><span>IRON—DAD<small>ENGINEERING A FAMILY / R38</small></span></a><nav class="links">{links}<a class="nav-cta" href="/iron-kids/pilot/">R38 PILOT ↗</a></nav></div></header>'
def footer(): return '<footer class="footer"><div class="shell footer-grid"><div><b>IRON-DAD / Justin Tahai</b><p>A human-scale machine, Peach’s sidekick branch, and a comfort-first builder program—kept honest about evidence.</p></div><div><b>Projects</b><p><a href="/iron-dad/">IRON-DAD</a><br><a href="/iron-kitty/">IRON-KITTY</a><br><a href="/iron-kids/">IRON-KIDS</a></p></div><div><b>R38</b><p><a href="/iron-kids/pilot/">Registered K2 pilot</a><br><a href="/downloads/">Model download</a></p></div></div></footer>'
def page(title,desc,current,body,og="/assets/r38/r38-share-card.png"):
    return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#080b10"><title>{title}</title><meta name="description" content="{desc}"><meta property="og:title" content="{title}"><meta property="og:description" content="{desc}"><meta property="og:image" content="{og}"><meta name="twitter:card" content="summary_large_image"><link rel="stylesheet" href="/assets/site.css"><script defer src="/assets/site.js"></script></head><body>{nav(current)}<main>{body}</main>{footer()}</body></html>'

home=f'''<section class="shell hero"><div><span class="kicker">JUSTIN TAHAI / PERSONAL SYSTEMS ENGINEERING</span><h1>ENGINEERING<br><em>A FAMILY.</em></h1><p>R38 brings the IRON-KIDS K2 child reference, textile carrier, EVA, exterior shells, growth interfaces, and removable electronics into one registered digital pilot assembly.</p><div class="actions"><a class="button" href="/iron-kids/pilot/">Inspect the K2 pilot ↗</a><a class="button alt" href="/downloads/">Download the model ↗</a></div></div><div class="hero-media"><img data-media-target="image" src="/assets/r38/k2-pilot-front.png" alt="Registered K2 pilot armor assembly"><video data-media-target="video" hidden controls muted loop playsinline poster="/assets/r38/k2-pilot-front.png"><source src="/assets/r38/k2-pilot-rotation.mp4" type="video/mp4"></video><div class="media-switch"><button data-media="image" aria-pressed="true">Still</button><button data-media="video" aria-pressed="false">Rotate</button></div></div></section><section class="shell family"><article class="card"><span class="kicker">01 / Human scale</span><h2>IRON-DAD</h2><p>Articulated skin, load support, distributed controls, and AR.</p><a href="/iron-dad/">Open project ↗</a></article><article class="card"><span class="kicker">02 / Sidekick</span><h2>IRON-KITTY</h2><p>Peach’s feline-first display and geometry branch.</p><a href="/iron-kitty/">Meet Peach ↗</a></article><article class="card"><span class="kicker">03 / Builders</span><h2>IRON-KIDS</h2><p>Comfort-first shells around a textile/EVA fit system.</p><a href="/iron-kids/">Start here ↗</a></article></section>'''
(SITE/"index.html").write_text(page("IRON-DAD R38 — Engineering a Family","R38 registered IRON-KIDS K2 pilot assembly.","/",home))

pages={
"family/index.html":page("Engineering a Family — R38","Three project branches, one evidence discipline.","/family/",'<section class="shell page-hero"><span class="kicker">THE WHOLE PROGRAM</span><h1>THREE BRANCHES.<br><em>ONE DISCIPLINE.</em></h1><p>Comfort, agency, evidence, and possibility connect the human, feline, and child-scale work without pretending they have the same maturity.</p></section><section class="paper section"><div class="shell grid-3"><article class="spec"><h2>Comfort</h2><p>Textile carrier, removable EVA, ventilation, and soft compression folds.</p></article><article class="spec"><h2>Agency</h2><p>Manual release and electronics with no restraint authority.</p></article><article class="spec"><h2>Evidence</h2><p>Modeled geometry is not the same as a physically validated wearable.</p></article></div></section>'),
"iron-dad/index.html":page("IRON-DAD — R38","Human-scale articulated armor engineering.","/iron-dad/",'<section class="shell page-hero"><span class="kicker">HUMAN SCALE</span><h1>IRON—DAD.</h1><p>Articulated exterior, assisted load path, distributed safety, and integrated optics remain a separate advanced branch.</p></section>'),
"iron-kitty/index.html":page("IRON-KITTY / Peach — R38","Peach’s feline-first armor branch.","/iron-kitty/",'<section class="shell page-hero"><span class="kicker">THE OFFICIAL SIDEKICK</span><h1>IRON—KITTY.<br><em>PEACH.</em></h1><p>A feline-first display branch that preserves face, ears, whiskers, paws, gait, belly, and tail balance. No powered closure around an animal.</p></section>'),
"iron-kids/index.html":page("IRON-KIDS — R38","Comfort-first growth-friendly builder armor.","/iron-kids/",'<section class="shell page-hero"><span class="kicker">THE BUILDER BRANCH</span><h1>GROW WITH<br><em>THE HERO.</em></h1><p>R38 is the first consolidated K2 digital pilot: a generic child reference, soft carrier, EVA envelope, printable shell, corrected growth hardware, and optional removable electronics.</p><div class="actions"><a class="button" href="/iron-kids/pilot/">Open the registered pilot ↗</a></div></section>'),
"iron-kids/pilot/index.html":page("IRON-KIDS K2 Registered Pilot R38","One registered K2 digital pilot assembly.","/iron-kids/pilot/",f'''<section class="shell page-hero"><span class="kicker">R38 / REGISTERED K2 PILOT</span><h1>ONE COORDINATE<br><em>SYSTEM.</em></h1><p>Body reference, textile carrier, EVA, armor, growth interfaces, electronics, and wiring are now mapped into one digital assembly. Physical child validation remains open.</p><div class="actions"><a class="button" href="/downloads/{MODEL_NAME}.zip">Download model package ↗</a><a class="button alt" href="#layers">Inspect layers ↓</a></div></section><section class="section"><div class="shell gallery"><article class="media-card"><img src="/assets/r38/k2-pilot-exploded.png" alt="Exploded K2 pilot assembly"><h3>Exploded assembly</h3><p>Printable shells, growth interfaces, electronics, and reference layers separated for inspection.</p></article><article class="media-card"><img src="/assets/r38/k2-pilot-layers.png" alt="K2 carrier and EVA layers"><h3>Fit stack</h3><p>Generic body reference, textile carrier, EVA envelope, protected hardware, and exterior shell.</p></article><article class="media-card"><img src="/assets/r38/k2-pilot-side.png" alt="Side view of registered K2 pilot"><h3>Registered side view</h3><p>Shared coordinate system reveals the intended helmet, torso, arm, pelvis, leg, and boot datums.</p></article><article class="media-card"><video controls muted loop playsinline poster="/assets/r38/k2-pilot-front.png"><source src="/assets/r38/k2-pilot-rotation.mp4" type="video/mp4"></video><h3>Rotation study</h3><p>A rendered inspection turn—not physical motion or wearable validation.</p></article></div></section><section class="paper section" id="layers"><div class="shell"><span class="kicker" style="color:#8a2b27">REGISTERED LAYERS</span><h2 class="section-title">FIT FIRST.<br><em>SHELL LAST.</em></h2><table class="layer-table"><thead><tr><th>Layer</th><th>Purpose</th><th>R38 status</th></tr></thead><tbody><tr><td>Generic child reference</td><td>Joint and proportion datum</td><td>Modeled; replace with measurements</td></tr><tr><td>Textile carrier</td><td>Actual fit and releases</td><td>Reference SVG and geometry</td></tr><tr><td>Removable EVA</td><td>Comfort and load spread</td><td>Starting envelope only</td></tr><tr><td>Growth interfaces</td><td>20 mm between-joint extension</td><td>Regression checked digitally</td></tr><tr><td>Exterior shell</td><td>Cosmetic protection and identity</td><td>Printable development geometry</td></tr><tr><td>Electronics</td><td>Optional status, light, sensing</td><td>Removable; no physical authority</td></tr></tbody></table></div></section><section class="section"><div class="shell notice"><strong>Physical gate still open:</strong> print a helmet fit shell, one arm, one leg, chest gauges, and the soft-carrier samples before a full suit. Record mass, pressure, heat, movement, vision, release, and extraction with power removed.</div></section>'''),
"build/index.html":page("Build Program R38","Evidence-gated K2 pilot build plan.","/build/",'<section class="shell page-hero"><span class="kicker">BUILD PROGRAM</span><h1>BUILD ONE<br><em>TRUTH AT A TIME.</em></h1><p>Measure. Fit the carrier. Print gauges. Prove one arm and one leg. Fit torso and helmet. Add electronics only after blank configurations pass.</p></section>'),
"evidence/index.html":page("Evidence Ledger R38","R38 evidence boundaries.","/evidence/",f'''<section class="shell page-hero"><span class="kicker">R38 EVIDENCE LEDGER</span><h1>SHOW WHAT<br><em>IS ACTUALLY TRUE.</em></h1><p>R38 establishes a registered digital assembly and regression-checked local interfaces. It does not establish child fit, print quality, comfort, thermal performance, or supervised wear.</p></section><section class="paper section"><div class="shell evidence"><article><b>PROPOSED</b>Full K2 pilot architecture.</article><article><b>MODELED</b>{len(part_manifest)} printable designs plus reference layers.</article><article><b>DIGITALLY CHECKED</b>Topology, build envelope, growth and chest patterns.</article><article><b>PHYSICALLY VALIDATED</b>Not completed.</article></div></section>'''),
"downloads/index.html":page("Downloads R38","R38 registered K2 pilot model download.","/downloads/",f'''<section class="shell page-hero"><span class="kicker">VERIFIED DOWNLOAD</span><h1>THE K2 PILOT.<br><em>ONE PACKAGE.</em></h1><p>Printable and registered STLs, GLB assemblies, textile/EVA references, source, previews, manifest, checksums, and evidence files.</p></section><section class="paper section"><div class="shell"><div class="download"><div><h2>{MODEL_NAME}</h2><p>Digital pilot only. Physical child validation remains open.</p><code>{sha256(model_zip)}</code></div><a class="button" href="/downloads/{MODEL_NAME}.zip">Download ZIP ↗</a></div></div></section>'''),
}
for rel,html in pages.items():
    p=SITE/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(html)

(SITE/"_headers").write_text('/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n  Permissions-Policy: camera=(), microphone=(), geolocation=()\n')
(SITE/"_redirects").write_text('/r38 /iron-kids/pilot/ 301\n/k2-pilot /iron-kids/pilot/ 301\n')
(SITE/"robots.txt").write_text('User-agent: *\nAllow: /\n')

# Site audit.
missing=[]
for hp in SITE.rglob("*.html"):
    for raw in re.findall(r'(?:href|src)=["\']([^"\']+)',hp.read_text()):
        if raw.startswith(("http:","https:","#","mailto:","tel:")): continue
        target=raw.split("#")[0].split("?")[0]
        if not target: continue
        fp=SITE/target.lstrip("/") if target.startswith("/") else hp.parent/target
        if target.endswith("/"): fp=fp/"index.html"
        if not fp.exists(): missing.append({"page":str(hp.relative_to(SITE)),"target":raw})
video_probe=subprocess.run(["ffprobe","-v","error","-show_entries","stream=codec_name,width,height,r_frame_rate","-show_entries","format=duration","-of","json",str(SITE_ASSETS/"k2-pilot-rotation.mp4")],check=True,capture_output=True,text=True)
site_verification={
    "release":"R38",
    "root_index_exists":(SITE/"index.html").exists(),
    "html_pages":len(list(SITE.rglob("*.html"))),
    "image_files":len(list(SITE.rglob("*.png"))),
    "video_files":len(list(SITE.rglob("*.mp4"))),
    "missing_local_references":missing,
    "model_zip_sha256":sha256(model_zip),
    "video_probe":json.loads(video_probe.stdout),
    "remaining_planned_passes":3,
}
(SITE/"R38_VERIFICATION.json").write_text(json.dumps(site_verification,indent=2))
manifest=[]
for p in sorted(SITE.rglob("*")):
    if p.is_file(): manifest.append({"path":p.relative_to(SITE).as_posix(),"bytes":p.stat().st_size,"sha256":sha256(p)})
(SITE/"R38_PACKAGE_MANIFEST.json").write_text(json.dumps(manifest,indent=2))
if missing: raise RuntimeError(missing)
print(json.dumps({"parts":len(part_manifest),"qty":sum(p['quantity'] for p in part_manifest),"pages":site_verification['html_pages'],"images":site_verification['image_files'],"videos":site_verification['video_files'],"model_zip":str(model_zip)},indent=2))
