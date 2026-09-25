from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out"
MODEL = OUT / "model"
SITE = OUT / "site"
SCAD = MODEL / "SCAD"
STL = MODEL / "STL"
DOCS = MODEL / "DOCS"
for p in [OUT, MODEL, SITE, SCAD, STL, DOCS]:
    p.mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

HEADER = r'''$fn=56;
module ellipsoid(v=[10,10,10]) { scale(v) sphere(r=1); }
module ellipsoid_shell(o=[10,10,10], t=2) { difference(){ ellipsoid(o); ellipsoid([o[0]-t,o[1]-t,o[2]-t]); } }
module ring_ellipsoid(o=[10,10,10], t=2, gap=0) { difference(){ ellipsoid_shell(o,t); if(gap>0) translate([0,-o[1],0]) cube([o[0]*2.4,gap,o[2]*2.4],center=true); } }
module slot2d(len=20,w=4,h=20){ hull(){ translate([-(len-w)/2,0,0]) cylinder(d=w,h=h,center=true); translate([(len-w)/2,0,0]) cylinder(d=w,h=h,center=true); } }
module rounded_box(v=[10,10,10], r=2){ minkowski(){ cube([v[0]-2*r,v[1]-2*r,v[2]-2*r],center=true); sphere(r=r); } }
'''

parts: list[dict] = []

def export_part(name: str, code: str, category: str, status: str, notes: str, material: str = "PLA/PETG") -> None:
    scad = SCAD / f"{name}.scad"
    stl = STL / f"{name}.stl"
    scad.write_text(HEADER + code + "\n")
    env = dict(os.environ)
    env["QT_QPA_PLATFORM"] = "offscreen"
    subprocess.run(["openscad", "-o", str(stl), str(scad)], check=True, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if stl.stat().st_size < 84:
        raise RuntimeError(f"Empty STL: {name}")
    parts.append({
        "name": name,
        "category": category,
        "status": status,
        "notes": notes,
        "material": material,
        "stl": f"STL/{stl.name}",
        "source": f"SCAD/{scad.name}",
        "bytes": stl.stat().st_size,
    })

# --- Generic Peach-proportioned reference mannequin (display datum, not a scan) ---
export_part(
    "PEACH_GENERIC_REFERENCE_MANNEQUIN_R34",
    r'''union(){
      translate([0,0,112]) ellipsoid([82,170,78]);
      translate([0,-172,162]) ellipsoid([58,62,58]);
      translate([-38,-188,210]) rotate([0,18,-8]) cylinder(h=58,r1=22,r2=4,center=true,$fn=3);
      translate([38,-188,210]) rotate([0,-18,8]) cylinder(h=58,r1=22,r2=4,center=true,$fn=3);
      for(x=[-55,55]) translate([x,-82,48]) ellipsoid([22,30,66]);
      for(x=[-58,58]) translate([x,92,45]) ellipsoid([26,36,68]);
      for(x=[-55,55]) translate([x,-94,2]) ellipsoid([28,45,15]);
      for(x=[-58,58]) translate([x,108,0]) ellipsoid([31,49,16]);
      translate([0,155,115]) rotate([74,0,0]) rotate_extrude(angle=210) translate([74,0,0]) circle(r=10);
    }''',
    "Reference",
    "modeled",
    "Generic Peach-proportioned feline reference datum. Not a body scan and not a validated live-animal fit model.",
)

# Helmet crown: open face, open underside, ear clearance.
export_part(
    "IK_HELMET_CROWN_OPEN_FACE_R34",
    r'''difference(){
      translate([0,0,0]) ellipsoid_shell([65,72,62],3);
      translate([0,-62,-8]) cube([102,70,72],center=true);
      translate([0,0,-55]) cube([150,150,62],center=true);
      translate([-39,-14,38]) rotate([0,12,-8]) cylinder(h=72,r=16,center=true);
      translate([39,-14,38]) rotate([0,-12,8]) cylinder(h=72,r=16,center=true);
      translate([0,45,8]) cube([62,48,42],center=true);
    }''',
    "Helmet",
    "modeled",
    "Open-face, open-ear, open-underside crown intended for display or supervised fit studies only.",
)

export_part(
    "IK_HELMET_BROW_VISOR_R34",
    r'''difference(){
      intersection(){ ellipsoid_shell([61,70,55],3); translate([0,-48,8]) cube([118,36,36],center=true); }
      translate([0,-62,10]) cube([76,52,17],center=true);
    }''',
    "Helmet",
    "modeled",
    "Decorative brow/visor shell that leaves the face and whisker field open.",
)

# Ear guards as open rings.
for side, x in [("LEFT", -1), ("RIGHT", 1)]:
    export_part(
        f"IK_EAR_GUARD_{side}_R34",
        f'''translate([{x*38},0,0]) difference(){{
          rotate([0,{x*-10},0]) cylinder(h=56,r1=23,r2=5,center=true,$fn=3);
          rotate([0,{x*-10},0]) translate([0,0,-2]) cylinder(h=60,r1=17,r2=2,center=true,$fn=3);
          translate([{-x*10},0,-16]) cube([46,46,32],center=true);
        }}''',
        "Helmet",
        "modeled",
        "Open ear guard with no intended pressure on the pinna.",
    )

# Chest and back shells with open belly and throat.
export_part(
    "IK_CHEST_PLATE_R34",
    r'''difference(){
      intersection(){ translate([0,0,0]) ellipsoid_shell([84,118,62],3); translate([0,-78,0]) cube([150,90,92],center=true); }
      translate([0,-118,-20]) cube([112,88,46],center=true);
      translate([0,-110,28]) cylinder(h=20,r=20,center=true,$fn=3);
    }''',
    "Torso",
    "modeled",
    "Front shell study with open throat, open abdomen, and triangular chest-light opening.",
)

export_part(
    "IK_BACK_PLATE_R34",
    r'''difference(){
      intersection(){ ellipsoid_shell([86,122,64],3); translate([0,82,4]) cube([154,96,104],center=true); }
      translate([0,118,-28]) cube([120,82,38],center=true);
      translate([0,62,22]) cube([44,34,28],center=true);
    }''',
    "Torso",
    "modeled",
    "Back shell study with open lower abdomen and removable service opening.",
)

# Shoulder and hip plates.
for side, x in [("LEFT", -1), ("RIGHT", 1)]:
    export_part(
        f"IK_SHOULDER_PLATE_{side}_R34",
        f'''difference(){{
          translate([{x*52},0,0]) intersection(){{ ellipsoid_shell([38,48,30],2.6); translate([{x*-18},0,0]) cube([48,100,70],center=true); }}
          translate([{x*52},0,-25]) cube([90,90,34],center=true);
        }}''',
        "Shoulder",
        "modeled",
        "Floating shoulder plate study; intended to mount to a soft carrier, not the animal.",
    )
    export_part(
        f"IK_HIP_PLATE_{side}_R34",
        f'''difference(){{
          translate([{x*58},0,0]) intersection(){{ ellipsoid_shell([40,54,38],2.8); translate([{x*-18},0,0]) cube([54,110,82],center=true); }}
          translate([{x*58},0,-32]) cube([96,96,40],center=true);
        }}''',
        "Hip",
        "modeled",
        "Floating lateral hip plate with belly and groin kept open.",
    )

# Leg cuffs: split/open on inward side, four positions.
leg_specs = [
    ("FRONT_LEFT", -1, -1), ("FRONT_RIGHT", 1, -1),
    ("REAR_LEFT", -1, 1), ("REAR_RIGHT", 1, 1),
]
for name, sx, sy in leg_specs:
    export_part(
        f"IK_LEG_CUFF_{name}_R34",
        f'''difference(){{
          ellipsoid_shell([27,34,54],2.4);
          translate([{sx*-20},0,0]) cube([26,90,120],center=true);
          translate([0,0,-48]) cube([80,90,26],center=true);
        }}''',
        "Leg",
        "modeled",
        "Open-side cosmetic leg cuff. No closed ring around a limb.",
    )

# Paw guards: top-only shells.
for name, sx, sy in leg_specs:
    export_part(
        f"IK_PAW_GUARD_{name}_R34",
        r'''difference(){
          intersection(){ ellipsoid_shell([34,50,19],2.2); translate([0,0,10]) cube([90,120,28],center=true); }
          translate([0,0,-6]) cube([100,130,14],center=true);
        }''',
        "Paw",
        "modeled",
        "Top-only paw guard study; paw pads and underside remain fully open.",
    )

# Tail base and segments. Split/open underside rings.
export_part(
    "IK_TAIL_BASE_SADDLE_R34",
    r'''difference(){
      rotate([90,0,0]) ring_ellipsoid([32,32,24],3,10);
      translate([0,-14,0]) cube([68,28,56],center=true);
    }''',
    "Tail",
    "modeled",
    "Open saddle around the tail base; never a closed ring.",
)

for i, dims in enumerate([(24,21,16),(21,19,15),(19,17,14),(17,15,13),(15,13,12)], start=1):
    export_part(
        f"IK_TAIL_SEGMENT_{i:02d}_R34",
        f'''difference(){{
          rotate([90,0,0]) ring_ellipsoid([{dims[0]},{dims[1]},{dims[2]}],2.2,9);
          translate([0,-{dims[1]-4},0]) cube([{dims[0]*2.5},18,{dims[2]*2.5}],center=true);
        }}''',
        "Tail",
        "modeled",
        "Open, decorative tail segment for display or non-contact rig studies.",
    )

export_part(
    "IK_CHEST_LIGHT_BEZEL_R34",
    r'''difference(){ cylinder(h=4,r=22,center=true,$fn=3); cylinder(h=10,r=15,center=true,$fn=3); }''',
    "Lighting",
    "modeled",
    "Triangular diffused-light bezel. Low-voltage effects only.",
)

export_part(
    "IK_BREAKAWAY_HARNESS_ANCHOR_R34",
    r'''difference(){ rounded_box([46,30,5],2); slot2d(25,4,14); translate([-17,0,0]) cylinder(d=3.6,h=14,center=true); translate([17,0,0]) cylinder(d=3.6,h=14,center=true); }''',
    "Carrier",
    "modeled",
    "Backed anchor for a breakaway textile carrier. Not a direct body attachment.",
)

export_part(
    "IK_DISPLAY_STAND_BASE_R34",
    r'''difference(){ rounded_box([320,260,16],8); translate([0,0,7]) rounded_box([274,214,10],5); for(x=[-125,125]) for(y=[-95,95]) translate([x,y,0]) cylinder(d=8,h=24,center=true); }''',
    "Display",
    "modeled",
    "Display base for the printable concept geometry branch.",
)

export_part(
    "IK_DISPLAY_SUPPORT_ARCH_R34",
    r'''difference(){
      union(){ translate([0,0,105]) rotate([90,0,0]) cylinder(h=14,r=92,center=true); translate([-92,0,50]) cube([18,14,110],center=true); translate([92,0,50]) cube([18,14,110],center=true); }
      translate([0,0,105]) rotate([90,0,0]) cylinder(h=22,r=74,center=true);
      translate([0,0,145]) cube([220,40,100],center=true);
    }''',
    "Display",
    "modeled",
    "Open display arch supporting the concept assembly without enclosing an animal.",
)

# Assembly source and display assembly STL.
assembly_code = HEADER + r'''
// Generic armored-cat display assembly. Not a live-wear validation.
color("gray") union(){
  translate([0,0,112]) ellipsoid([82,170,78]);
  translate([0,-172,162]) ellipsoid([58,62,58]);
  translate([-38,-188,210]) rotate([0,18,-8]) cylinder(h=58,r1=22,r2=4,center=true,$fn=3);
  translate([38,-188,210]) rotate([0,-18,8]) cylinder(h=58,r1=22,r2=4,center=true,$fn=3);
  for(x=[-55,55]) translate([x,-82,48]) ellipsoid([22,30,66]);
  for(x=[-58,58]) translate([x,92,45]) ellipsoid([26,36,68]);
  for(x=[-55,55]) translate([x,-94,2]) ellipsoid([28,45,15]);
  for(x=[-58,58]) translate([x,108,0]) ellipsoid([31,49,16]);
  translate([0,155,115]) rotate([74,0,0]) rotate_extrude(angle=210) translate([74,0,0]) circle(r=10);
}
color("firebrick") union(){
  translate([0,-172,162]) difference(){ ellipsoid_shell([65,72,62],3); translate([0,-62,-8]) cube([102,70,72],center=true); translate([0,0,-55]) cube([150,150,62],center=true); translate([-39,-14,38]) rotate([0,12,-8]) cylinder(h=72,r=16,center=true); translate([39,-14,38]) rotate([0,-12,8]) cylinder(h=72,r=16,center=true); }
  translate([0,-78,118]) rotate([90,0,0]) difference(){ intersection(){ ellipsoid_shell([84,118,62],3); translate([0,-78,0]) cube([150,90,92],center=true); } translate([0,-118,-20]) cube([112,88,46],center=true); }
  translate([0,78,118]) rotate([90,0,180]) difference(){ intersection(){ ellipsoid_shell([86,122,64],3); translate([0,82,4]) cube([154,96,104],center=true); } translate([0,118,-28]) cube([120,82,38],center=true); }
  for(x=[-1,1]) translate([x*55,-75,55]) ellipsoid_shell([27,34,54],2.4);
  for(x=[-1,1]) translate([x*58,95,52]) ellipsoid_shell([27,34,54],2.4);
}
'''
assembly_scad = SCAD / "IRON_KITTY_DISPLAY_ASSEMBLY_R34.scad"
assembly_scad.write_text(assembly_code)
assembly_stl = STL / "IRON_KITTY_DISPLAY_ASSEMBLY_R34.stl"
env = dict(os.environ); env["QT_QPA_PLATFORM"] = "offscreen"
subprocess.run(["openscad", "-o", str(assembly_stl), str(assembly_scad)], check=True, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
parts.append({"name":"IRON_KITTY_DISPLAY_ASSEMBLY_R34","category":"Assembly","status":"modeled","notes":"Generic armored-cat display assembly; not a live-wear validation.","material":"PLA/PETG","stl":f"STL/{assembly_stl.name}","source":f"SCAD/{assembly_scad.name}","bytes":assembly_stl.stat().st_size})

# Documentation.
(DOCS / "README.md").write_text('''# IRON-KITTY Geometry R34

R34 creates the first actual printable feline geometry branch for the IRON-DAD family site. It includes a generic Peach-proportioned reference mannequin, individual red-and-gold armor concept parts, open-face/open-ear helmet geometry, open-belly torso panels, floating shoulders and hips, split leg cuffs, top-only paw guards, open tail segments, breakaway carrier hardware, and a display stand.

## Critical boundary

This is a display and engineering-study geometry package. It is not a validated live-animal wearable. The reference mannequin is generic and not a scan of Peach. No part should be placed on an animal without an independent veterinary, welfare, materials, breakaway, heat, movement, and supervision review.

## Design rules retained

- Face, nostrils, mouth, whiskers, ears, throat, belly, paw pads, groin, joints, and tail underside remain open.
- No powered closure.
- No closed rigid ring around a limb or tail.
- Any future live-wear exploration must use a soft breakaway textile carrier and extremely lightweight cosmetic shells.
- Display geometry and live-wear concepts remain separate.
''')

(DOCS / "PART_MAP.md").write_text('''# Part map

## Helmet
- `IK_HELMET_CROWN_OPEN_FACE_R34`
- `IK_HELMET_BROW_VISOR_R34`
- `IK_EAR_GUARD_LEFT_R34`
- `IK_EAR_GUARD_RIGHT_R34`

## Torso
- `IK_CHEST_PLATE_R34`
- `IK_BACK_PLATE_R34`
- `IK_SHOULDER_PLATE_LEFT_R34`
- `IK_SHOULDER_PLATE_RIGHT_R34`
- `IK_HIP_PLATE_LEFT_R34`
- `IK_HIP_PLATE_RIGHT_R34`

## Legs and paws
- Four open-side leg cuffs
- Four top-only paw guards

## Tail
- Open tail-base saddle
- Five open decorative tail segments

## Other
- Chest-light bezel
- Breakaway harness anchor
- Display base and support arch
- Generic reference mannequin
- Full display assembly
''')

(DOCS / "COLOR_FINISH.md").write_text('''# Suggested display finish
- Primary shell: metallic red
- Secondary transitions: warm gold
- Mechanical gaps: graphite
- Chest light: diffuse cool white-blue
- Peach reference mannequin: gray with white nose, chest, belly, and paws
''')

manifest = {"release":"R34","part_count":len(parts),"parts":parts,"remaining_passes_after_r34":1,"physical_live_animal_validation":False}
(DOCS / "MANIFEST.json").write_text(json.dumps(manifest, indent=2))

checks=[]
for p in sorted(MODEL.rglob('*')):
    if p.is_file() and p.name!='SHA256SUMS.txt':
        checks.append(f"{sha256(p)}  {p.relative_to(MODEL).as_posix()}")
(MODEL / "SHA256SUMS.txt").write_text("\n".join(checks)+"\n")
(MODEL / "RELEASE.txt").write_text("IRON-KITTY Geometry R34\nRemaining roadmap passes after R34: 1\n")

# Package model into site.
(SITE / "downloads").mkdir(parents=True, exist_ok=True)
model_zip = SITE / "downloads/IRON_KITTY_GEOMETRY_R34.zip"
with zipfile.ZipFile(model_zip, "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(MODEL.rglob('*')):
        if p.is_file(): z.write(p, p.relative_to(MODEL))

# --- Website ---
(SITE / "assets").mkdir(exist_ok=True)
(SITE / "assets/site.css").write_text(r''':root{--bg:#090b0f;--surface:#121923;--surface2:#1b2431;--paper:#f3ede1;--paper2:#fffaf0;--ink:#151d28;--muted:#aeb8c6;--red:#b32d2d;--red2:#e05245;--gold:#d4af4a;--gold2:#f4dfb1;--blue:#0b3d91;--cyan:#73dcff;--line:rgba(212,175,74,.28);--max:1460px}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:#faf7ef;font:16px/1.65 Inter,ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif}a{color:inherit}.shell{width:min(calc(100% - 2rem),var(--max));margin:auto}.top{position:sticky;top:0;z-index:20;background:rgba(9,11,15,.94);backdrop-filter:blur(16px);border-bottom:1px solid var(--line)}.nav{min-height:74px;display:flex;align-items:center;justify-content:space-between;gap:1rem}.brand{text-decoration:none;font-weight:950;letter-spacing:.08em}.brand small{display:block;font-size:.62rem;color:var(--gold2);letter-spacing:.16em}.links{display:flex;gap:1rem;align-items:center}.links a{text-decoration:none;color:#dce4ed;font-weight:750}.links a:hover,.links a[aria-current=true]{color:var(--gold2)}.pill{padding:.72rem 1rem;border-radius:12px;background:linear-gradient(135deg,var(--red2),var(--red));color:white}.hero{min-height:74vh;display:grid;grid-template-columns:1.05fr .95fr;gap:clamp(2rem,5vw,5rem);align-items:center;padding:clamp(4rem,8vw,8rem) 0}.eyebrow{color:var(--gold2);text-transform:uppercase;letter-spacing:.17em;font-weight:850;font-size:.78rem}.hero h1,.page h1{font-size:clamp(3.5rem,8vw,8rem);line-height:.86;letter-spacing:-.065em;margin:.55rem 0 1.15rem}.hero h1 em,.page h1 em,h2 em{font-style:normal;color:var(--gold)}.hero p,.page p{font-size:1.14rem;color:#d5dde7;max-width:64ch}.actions{display:flex;flex-wrap:wrap;gap:.8rem;margin-top:1.3rem}.button{display:inline-flex;min-height:48px;align-items:center;padding:.8rem 1.1rem;border-radius:13px;background:linear-gradient(135deg,var(--red2),var(--red));text-decoration:none;font-weight:850;box-shadow:0 14px 35px rgba(179,45,45,.24)}.button.alt{background:transparent;border:1px solid var(--line);box-shadow:none;color:var(--gold2)}.family-stage{aspect-ratio:1.2;position:relative;border:1px solid var(--line);border-radius:34px;background:radial-gradient(circle at 50% 50%,#42201b,#0b0f16 66%);display:grid;place-items:center;overflow:hidden}.cat-mark{width:72%;aspect-ratio:1.1;position:relative;filter:drop-shadow(0 0 38px rgba(212,175,74,.18))}.cat-mark:before{content:'';position:absolute;left:24%;right:24%;top:18%;bottom:26%;border-radius:48% 48% 44% 44%;background:linear-gradient(140deg,#9c2525,#dd4d3e 60%,#5f1114)}.cat-mark:after{content:'';position:absolute;left:12%;right:12%;bottom:5%;height:35%;border-radius:45%;background:linear-gradient(160deg,#8d1e20,#c53a32)}.ears{position:absolute;top:2%;left:18%;right:18%;height:32%}.ears:before,.ears:after{content:'';position:absolute;width:30%;height:100%;background:linear-gradient(160deg,var(--gold),#9f6c18);clip-path:polygon(50% 0,100% 100%,0 100%)}.ears:before{left:0;transform:rotate(-8deg)}.ears:after{right:0;transform:rotate(8deg)}.chest-light{position:absolute;width:17%;aspect-ratio:1;bottom:22%;left:41.5%;clip-path:polygon(50% 0,100% 100%,0 100%);background:#dff8ff;box-shadow:0 0 25px #73dcff,0 0 70px #73dcff66;z-index:3}.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;padding-bottom:5rem}.card{background:linear-gradient(180deg,var(--surface2),var(--surface));border:1px solid var(--line);border-radius:22px;padding:1.4rem;min-height:250px}.card h2{font-size:2.5rem;line-height:1;margin:.45rem 0}.card p{color:#c8d1dd}.card a{color:var(--gold2);font-weight:850}.paper{background:var(--paper);color:var(--ink)}.section{padding:clamp(4rem,7vw,7rem) 0}.section h2{font-size:clamp(2.4rem,5vw,5rem);line-height:.95;letter-spacing:-.05em;margin:.4rem 0 1rem}.paper p{color:#4d5865}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:1rem}.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem}.spec{background:var(--paper2);border:1px solid #d9caaa;border-radius:18px;padding:1.2rem}.spec h3{margin:.2rem 0 .5rem}.page{padding:clamp(4rem,8vw,8rem) 0 3rem}.page h1{font-size:clamp(3.2rem,7vw,7rem)}.viewer{background:#07101c;border:1px solid #2d5a88;border-radius:22px;padding:1rem}.layers{display:grid;grid-template-columns:repeat(4,1fr);gap:.7rem}.layer{background:#10213a;border:1px solid #2d5a88;border-radius:14px;padding:1rem;min-height:135px}.layer b{display:block;color:#fff}.layer span{color:#c2d8ed;font-size:.92rem}.download{background:linear-gradient(135deg,#0b3d91,#071b40);border:1px solid #2f6fbc;border-radius:22px;padding:1.4rem}.status{display:grid;grid-template-columns:repeat(4,1fr);gap:.8rem}.status article{background:#fff;border:1px solid #d9caaa;border-radius:16px;padding:1rem}.status b{display:block;color:#922b24}.table{width:100%;border-collapse:collapse;background:white;color:#18212d;border-radius:16px;overflow:hidden}.table th{background:#111722;color:white;text-align:left}.table th,.table td{padding:.85rem;border-bottom:1px solid #e2d8c4}.footer{border-top:1px solid var(--line);padding:2.4rem 0;color:#b4beca}.footer-grid{display:grid;grid-template-columns:2fr 1fr 1fr;gap:2rem}.footer a{color:var(--gold2)}@media(max-width:900px){.links{display:none}.hero,.cards,.grid2,.grid3,.layers,.status,.footer-grid{grid-template-columns:1fr}.hero{min-height:auto;padding:4rem 0}.family-stage{max-width:560px;margin:auto}}''')
(SITE / "assets/site.js").write_text("document.querySelectorAll('[data-copy]').forEach(b=>b.onclick=async()=>{await navigator.clipboard.writeText(location.href);b.textContent='Link copied'});\n")

def nav(current=''):
    items=[('/family/','Family'),('/iron-dad/','IRON-DAD'),('/iron-kitty/','IRON-KITTY'),('/iron-kids/','IRON-KIDS'),('/build/','Build'),('/evidence/','Evidence')]
    return '<header class="top"><div class="shell nav"><a class="brand" href="/">IRON—DAD<small>ENGINEERING A FAMILY / R34</small></a><nav class="links" aria-label="Primary">'+''.join(f'<a href="{h}"'+(' aria-current="true"' if h==current else '')+f'>{t}</a>' for h,t in items)+'<a class="pill" href="/iron-kitty/geometry/">R34 GEOMETRY</a></nav></div></header>'
def footer(): return '''<footer class="footer"><div class="shell footer-grid"><div><b>IRON-DAD / Justin Tahai</b><p>Human-scale augmentation, Peach’s sidekick geometry, and a comfort-first builder program.</p></div><div><b>Projects</b><p><a href="/iron-dad/">IRON-DAD</a><br><a href="/iron-kitty/">IRON-KITTY</a><br><a href="/iron-kids/">IRON-KIDS</a></p></div><div><b>R34</b><p><a href="/iron-kitty/geometry/">Geometry branch</a><br><a href="/downloads/IRON_KITTY_GEOMETRY_R34.zip">Model ZIP</a></p></div></div></footer>'''
def page(title,desc,current,body): return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#090b0f"><title>{title}</title><meta name="description" content="{desc}"><link rel="stylesheet" href="/assets/site.css"><script defer src="/assets/site.js"></script></head><body>{nav(current)}<main>{body}</main>{footer()}</body></html>'''

home='''<section class="shell hero"><div><span class="eyebrow">Justin Tahai / personal systems engineering</span><h1>ENGINEERING<br><em>A FAMILY.</em></h1><p>IRON-DAD explores the human-scale machine. IRON-KITTY now has its first actual printable feline geometry branch. IRON-KIDS carries the idea forward for builders.</p><div class="actions"><a class="button" href="/family/">Explore the family ↗</a><a class="button alt" href="/iron-kitty/geometry/">Open R34 geometry ↗</a></div></div><div class="family-stage" aria-label="Stylized red and gold IRON-KITTY silhouette"><div class="cat-mark"><div class="ears"></div><div class="chest-light"></div></div></div></section><section class="shell cards"><article class="card"><span class="eyebrow">01 / Human scale</span><h2>IRON-DAD</h2><p>Articulated skin, assisted structure, controls, and integrated optics.</p><a href="/iron-dad/">Open project ↗</a></article><article class="card"><span class="eyebrow">02 / Sidekick</span><h2>IRON-KITTY</h2><p>Peach’s feline-first project now has printable geometry, not only artwork.</p><a href="/iron-kitty/geometry/">Inspect R34 geometry ↗</a></article><article class="card"><span class="eyebrow">03 / Builders</span><h2>IRON-KIDS</h2><p>Growth-friendly PLA, removable EVA, soft carriers, and optional electronics.</p><a href="/iron-kids/">Start building ↗</a></article></section>'''
(SITE / "index.html").write_text(page("IRON-DAD R34 — Engineering a Family","R34 adds printable IRON-KITTY feline geometry.","/",home))

pages={
"family/index.html": page("Engineering a Family","Three project branches, one discipline.","/family/",'''<section class="shell page"><span class="eyebrow">The whole program</span><h1>THREE BRANCHES.<br><em>ONE DISCIPLINE.</em></h1><p>Comfort, agency, evidence, and possibility connect the human, feline, and child-scale branches.</p></section><section class="paper section"><div class="shell grid3"><article class="spec"><h3>Comfort</h3><p>Soft carriers, removable EVA, open compression zones, and ventilation.</p></article><article class="spec"><h3>Agency</h3><p>Manual release and no software-dependent restraint.</p></article><article class="spec"><h3>Evidence</h3><p>Concept, modeled, digitally checked, bench-tested, and physically validated remain separate.</p></article></div></section>'''),
"iron-dad/index.html": page("IRON-DAD","Human-scale articulated armor engineering.","/iron-dad/",'''<section class="shell page"><span class="eyebrow">Human-scale branch</span><h1>IRON—DAD.</h1><p>Articulated metal skin, a separate load path, distributed safety, and head-referenced optics.</p></section>'''),
"iron-kitty/index.html": page("IRON-KITTY — Peach","Peach’s feline-first sidekick project.","/iron-kitty/",'''<section class="shell page"><span class="eyebrow">The official sidekick</span><h1>IRON—KITTY.<br><em>PEACH.</em></h1><p>R34 moves the project from concept artwork into actual printable feline geometry while keeping live-animal welfare boundaries explicit.</p><div class="actions"><a class="button" href="/iron-kitty/geometry/">Inspect R34 geometry ↗</a><a class="button alt" href="/downloads/IRON_KITTY_GEOMETRY_R34.zip">Download model ZIP ↗</a></div></section>'''),
"iron-kitty/geometry/index.html": page("IRON-KITTY R34 Geometry","Printable feline display and engineering-study geometry.","/iron-kitty/",'''<section class="shell page"><span class="eyebrow">R34 / first printable geometry branch</span><h1>CAT-SHAPED.<br><em>ACTUALLY MODELED.</em></h1><p>Thirty printable files establish a generic Peach-proportioned datum, open-face/open-ear helmet, open-belly torso plates, floating shoulder and hip plates, split leg cuffs, top-only paw guards, open tail segments, breakaway carrier hardware, and a display assembly.</p><div class="actions"><a class="button" href="/downloads/IRON_KITTY_GEOMETRY_R34.zip">Download R34 model ZIP ↗</a><button class="button alt" data-copy>Copy page link</button></div></section><section class="paper section"><div class="shell"><span class="eyebrow">Geometry layers</span><h2>DISPLAY FIRST.<br>WELFARE ALWAYS.</h2><div class="viewer"><div class="layers"><article class="layer"><b>Reference datum</b><span>Generic Peach proportions; not a body scan.</span></article><article class="layer"><b>Helmet and torso</b><span>Open face, ears, throat, abdomen, and belly.</span></article><article class="layer"><b>Limbs and paws</b><span>Split cuffs and top-only guards; no closed rigid rings.</span></article><article class="layer"><b>Tail and carrier</b><span>Open segments and breakaway textile attachment concepts.</span></article></div></div></div></section><section class="section"><div class="shell grid2"><div><h2>WHAT THE PACKAGE CONTAINS</h2><p>Individual STL files, editable OpenSCAD sources, full display assembly, generic mannequin, part map, finish guide, manifest, and SHA-256 list.</p></div><div class="download"><h3>IRON-KITTY Geometry R34</h3><p>Printable display and engineering-study models. No live-animal fit claim.</p><a class="button" href="/downloads/IRON_KITTY_GEOMETRY_R34.zip">Download ZIP</a></div></div></section>'''),
"iron-kids/index.html": page("IRON-KIDS","Comfort-first growth-friendly PLA armor.","/iron-kids/",'''<section class="shell page"><span class="eyebrow">Builder branch</span><h1>GROW WITH<br><em>THE HERO.</em></h1><p>PLA shells outside a textile carrier, removable EVA, between-joint growth modules, and optional low-voltage electronics.</p></section>'''),
"build/index.html": page("Build program","Evidence-gated project roadmap.","/build/",'''<section class="shell page"><span class="eyebrow">Build program</span><h1>BUILD ONE<br><em>TRUTH AT A TIME.</em></h1><p>R34 completes the feline geometry branch. The remaining pass is the consolidated site and artifact-delivery rebuild.</p></section><section class="paper section"><div class="shell"><table class="table"><thead><tr><th>Pass</th><th>Status</th><th>Primary output</th></tr></thead><tbody><tr><td>R33</td><td>Completed</td><td>IRON-DAD full-body integration pass</td></tr><tr><td>R34</td><td>Completed</td><td>IRON-KITTY printable geometry branch</td></tr><tr><td>R35</td><td>Remaining</td><td>Unified generated site architecture and delivery cleanup</td></tr></tbody></table></div></section>'''),
"evidence/index.html": page("Evidence status","R34 model and validation boundaries.","/evidence/",'''<section class="shell page"><span class="eyebrow">R34 evidence ledger</span><h1>SHOW WHAT<br><em>IS ACTUALLY TRUE.</em></h1><p>R34 produces printable geometry and editable sources. It does not establish safe live-animal wear, comfort, heat, breakaway performance, or veterinary acceptance.</p></section><section class="paper section"><div class="shell status"><article><b>Proposed</b>Live-wear welfare and breakaway architecture.</article><article><b>Modeled</b>Individual armor components and display assembly.</article><article><b>Digitally checked</b>Every STL generated nonempty and packaged with source.</article><article><b>Physical validation</b>Not completed.</article></div></section>''')
}
for rel, html in pages.items():
    p=SITE/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(html)

(SITE / "_headers").write_text("/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n  Permissions-Policy: camera=(), microphone=(), geolocation=()\n")
(SITE / "_redirects").write_text("/kitty-geometry /iron-kitty/geometry/ 301\n/r34 /iron-kitty/geometry/ 301\n")
(SITE / "robots.txt").write_text("User-agent: *\nAllow: /\n")

missing=[]
for hp in SITE.rglob("*.html"):
    for raw in re.findall(r'(?:href|src)=["\']([^"\']+)', hp.read_text()):
        if raw.startswith(("http:","https:","#","mailto:","tel:")): continue
        target=raw.split("#")[0].split("?")[0]
        if not target: continue
        fp=SITE/target.lstrip("/") if target.startswith("/") else hp.parent/target
        if target.endswith("/"): fp=fp/"index.html"
        if not fp.exists(): missing.append({"page":str(hp.relative_to(SITE)),"target":raw})

verification={"release":"R34","html_pages":len(list(SITE.rglob('*.html'))),"model_part_count":len(parts),"local_missing_references":missing,"root_index_exists":(SITE/'index.html').exists(),"embedded_model_zip_sha256":sha256(model_zip),"physical_live_animal_validation":False,"remaining_passes":1}
(SITE / "R34_VERIFICATION.json").write_text(json.dumps(verification,indent=2))
print(json.dumps({"parts":len(parts),"pages":verification["html_pages"],"missing":len(missing)},indent=2))
