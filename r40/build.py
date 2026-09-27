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
import zipfile
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out"
MODEL = OUT / "model"
SITE = OUT / "site"
VALIDATION = MODEL / "PHYSICAL_VALIDATION_R40"
STL = VALIDATION / "STL"
SCAD = VALIDATION / "SCAD"
DOCS = VALIDATION / "DOCS"
PREVIEWS = VALIDATION / "PREVIEWS"
SOURCE = VALIDATION / "SOURCE"
SITE_ASSETS = SITE / "assets" / "r40"
SITE_DOWNLOADS = SITE / "downloads"

RELEASE = "R40"
PACKAGE_NAME = "IRON_KIDS_K2_PHYSICAL_VALIDATION_R40.zip"
BUILD_ENVELOPE = np.array([220.0, 220.0, 240.0])

for directory in [STL, SCAD, DOCS, PREVIEWS, SOURCE, SITE_ASSETS, SITE_DOWNLOADS]:
    directory.mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def font(size: int, bold: bool = False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


COMMON_SCAD = r'''$fn=56;
module rounded_box(v=[20,20,6], r=2) {
  minkowski() {
    cube([v[0]-2*r, v[1]-2*r, v[2]-2*r], center=true);
    sphere(r=r);
  }
}
module slot(len=20, width=4, height=20) {
  hull() {
    translate([-(len-width)/2,0,0]) cylinder(d=width,h=height,center=true);
    translate([(len-width)/2,0,0]) cylinder(d=width,h=height,center=true);
  }
}
module four_holes(sx,sy,d=3.4,h=20) {
  for(ix=[-1,1]) for(iy=[-1,1]) translate([ix*sx/2,iy*sy/2,0]) cylinder(d=d,h=h,center=true);
}
'''

FIXTURES = [
    (
        "IK_K2_WEBBING_SLIP_WITNESS_R40",
        r'''difference(){ rounded_box([34,30,8],2); translate([0,0,1]) cube([22.5,4.2,12],center=true); translate([0,12,0]) cube([4,10,12],center=true); }''',
        "Webbing",
        "Clip-on witness marker for 20 mm webbing. Mark its start line on the strap and record movement after each test.",
        "PETG preferred",
    ),
    (
        "IK_K2_EVA_COMPRESSION_STEP_GAUGE_R40",
        r'''union(){ for(i=[0:5]) translate([-50+i*20,0,(i+1)]) cube([18,24,2*(i+1)],center=true); translate([0,0,1]) cube([120,8,2],center=true); }''',
        "Comfort",
        "Six-step 2/4/6/8/10/12 mm gauge for checking available foam and clearance space without measuring against skin.",
        "PLA/PETG",
    ),
    (
        "IK_K2_FASTENER_PROTRUSION_GAUGE_R40",
        r'''difference(){ rounded_box([92,34,8],2); for(i=[0:4]) translate([-34+i*17,0,4-i*0.75]) cube([10,20,8],center=true); translate([42,0,0]) cylinder(d=3.5,h=16,center=true); }''',
        "Hardware",
        "Stepped 0/0.75/1.5/2.25/3.0 mm recess comparison gauge for checking screw and insert protrusion before padding is installed.",
        "PETG preferred",
    ),
    (
        "IK_K2_EDGE_RADIUS_COUPON_R40",
        r'''union(){ translate([0,0,-2]) rounded_box([120,26,4],1.5); for(i=[0:4]) translate([-44+i*22,0,1+i*0.5]) rotate([90,0,0]) cylinder(r=2+i,h=24,center=true); }''',
        "Comfort",
        "Reference coupon with increasing rounded edge sizes for selecting an acceptable finished edge before producing wearable shells.",
        "PLA/PETG",
    ),
    (
        "IK_K2_RELEASE_PULL_HANDLE_R40",
        r'''difference(){ rounded_box([82,42,10],5); rounded_box([48,18,14],4); translate([0,16,0]) slot(28,4.2,16); }''',
        "Release",
        "Large pull handle for a manually operated textile release strap. The release itself remains mechanical and independently reachable.",
        "PETG preferred",
    ),
    (
        "IK_K2_BREAKAWAY_PULL_TEST_JIG_R40",
        r'''difference(){ union(){ rounded_box([150,70,10],3); translate([-55,0,16]) rounded_box([22,46,34],3); translate([55,0,16]) rounded_box([22,46,34],3); } translate([-55,0,16]) slot(24,5,40); translate([55,0,16]) slot(24,5,40); four_holes(126,46,4.2,30); }''',
        "Electrical",
        "Bench fixture for holding two breakaway-connector leads while pull force is measured with an external scale. Not a certified load fixture.",
        "PETG preferred",
    ),
    (
        "IK_K2_GROWTH_INTERFACE_CYCLE_JIG_R40",
        r'''difference(){ union(){ rounded_box([150,70,10],3); translate([-42,0,12]) rounded_box([46,42,24],3); translate([42,0,12]) rounded_box([46,42,24],3); } translate([-42,0,15]) cube([18,26,24],center=true); translate([42,0,15]) cube([18,26,24],center=true); for(x=[-58,-26,26,58]) translate([x,0,12]) rotate([90,0,0]) cylinder(d=3.5,h=60,center=true); four_holes(126,46,4.2,30); }''',
        "Growth interface",
        "Bench fixture for repetitive insertion, pinning, removal, and inspection of the R38 growth-interface parts before shell integration.",
        "PETG preferred",
    ),
    (
        "IK_K2_PRESSURE_FILM_BACKER_R40",
        r'''difference(){ rounded_box([116,76,4],2); for(x=[-48:16:48]) translate([x,0,2]) cube([0.8,66,1.2],center=true); for(y=[-28:14:28]) translate([0,y,2]) cube([106,0.8,1.2],center=true); four_holes(100,60,3.2,12); }''',
        "Comfort",
        "Grid backer for pressure-indicating film or transfer paper used only on a bench form or padded mannequin, not directly against a child.",
        "PLA/PETG",
    ),
    (
        "IK_K2_HELMET_CLEARANCE_COMB_R40",
        r'''union(){ rounded_box([132,18,5],2); for(i=[0:5]) translate([-55+i*22,0,4+(i+1)*3]) cube([8,16,8+(i+1)*6],center=true); }''',
        "Helmet",
        "Progressive non-contact clearance comb for mapping nominal liner space at 6 mm increments before padding is installed.",
        "PLA/PETG",
    ),
    (
        "IK_K2_CABLE_BEND_RADIUS_GAUGE_R40",
        r'''difference(){ rounded_box([128,72,5],2); for(i=[0:3]) translate([-45+i*30,0,0]) cylinder(r=6+i*4,h=12,center=true); translate([55,0,0]) slot(24,4.5,12); }''',
        "Electrical",
        "6/10/14/18 mm radius comparison gauge for keeping removable low-voltage harnesses from being routed too tightly.",
        "PETG preferred",
    ),
    (
        "IK_K2_THERMAL_PROBE_CLIP_R40",
        r'''difference(){ rounded_box([38,30,8],2); translate([0,0,2]) cube([22,16,10],center=true); translate([0,12,0]) cube([4,10,12],center=true); translate([0,-10,0]) slot(18,3.2,12); }''',
        "Thermal",
        "Removable clip for placing a small logging probe on the outside of the textile/EVA stack during supervised bench and wearer-adjacent tests.",
        "PETG preferred",
    ),
    (
        "IK_K2_RELEASE_ROUTE_FLAG_R40",
        r'''difference(){ rounded_box([72,34,5],2); translate([-22,0,0]) slot(22,4.2,12); translate([18,0,0]) cylinder(d=10,h=12,center=true); }''',
        "Release",
        "High-visibility routing tag for marking manual-release straps during assembly and timed extraction drills.",
        "PETG preferred",
    ),
]


def openscad_export(source: Path, target: Path) -> None:
    env = dict(os.environ)
    env["QT_QPA_PLATFORM"] = "offscreen"
    subprocess.run(
        ["openscad", "-o", str(target), str(source)],
        check=True,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def build_fixtures() -> list[dict[str, object]]:
    manifest: list[dict[str, object]] = []
    for name, body, category, purpose, material in FIXTURES:
        scad_path = SCAD / f"{name}.scad"
        stl_path = STL / f"{name}.stl"
        write(scad_path, COMMON_SCAD + "\n" + body + "\n")
        openscad_export(scad_path, stl_path)
        mesh = trimesh.load_mesh(stl_path, force="mesh")
        extents = np.asarray(mesh.extents, dtype=float)
        manifest.append(
            {
                "name": name,
                "category": category,
                "purpose": purpose,
                "material": material,
                "stl": str(stl_path.relative_to(VALIDATION)),
                "source": str(scad_path.relative_to(VALIDATION)),
                "bbox_mm": [round(float(value), 3) for value in extents],
                "watertight": bool(mesh.is_watertight),
                "positive_volume": bool(abs(mesh.volume) > 0.01),
                "within_220x220x240": bool(np.all(extents <= BUILD_ENVELOPE + 1e-6)),
                "sha256": sha256(stl_path),
            }
        )
    write(DOCS / "FIXTURE_MANIFEST_R40.json", json.dumps(manifest, indent=2))
    with (DOCS / "FIXTURE_MANIFEST_R40.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Name", "Category", "Material", "X mm", "Y mm", "Z mm", "Watertight", "Purpose"])
        for item in manifest:
            writer.writerow(
                [
                    item["name"],
                    item["category"],
                    item["material"],
                    *item["bbox_mm"],
                    item["watertight"],
                    item["purpose"],
                ]
            )
    return manifest


TEST_ROWS = [
    ["P00", "Configuration record", "Photograph and inventory the exact revision set", "All installed parts and optional modules identified", "Before every session"],
    ["P01", "Bench visual inspection", "Inspect print seams, fasteners, strap routing, cable exits, and foam", "No crack, sharp edge, exposed fastener, trapped cable, or blocked release", "Before every session"],
    ["P02", "Mass", "Weigh each region and the complete configured suit", "Recorded; compared to previous session; no unexplained increase", "Each revision"],
    ["P03", "Release access", "Operate every manual release while standing and seated", "All releases reachable without electronics or tools", "Five repetitions"],
    ["P04", "Timed extraction", "Remove the configured suit with a second adult present", "Time recorded; no snag or powered dependency", "Three repetitions"],
    ["P05", "Carrier slip", "Mark witness clips and perform controlled movement sequence", "Slip recorded by region; no migration into joint or throat zones", "Ten-minute sequence"],
    ["P06", "Joint clearance", "Slowly map shoulder, elbow, wrist, hip, knee, and ankle range", "No hard stop, pinch, or shell-to-shell capture", "Both sides"],
    ["P07", "Sitting and recovery", "Sit, stand, kneel only if cleared, and return upright", "No release obstruction or rear-shell instability", "Supervised"],
    ["P08", "Vision/hearing/airflow", "Check sightlines, speech, hearing, breathing, and faceplate removal", "No obstruction; faceplate immediately removable", "Helmet sessions"],
    ["P09", "Electrical power-off", "Disconnect every optional power source", "Fit and manual removal remain unchanged", "Every powered configuration"],
    ["P10", "Thermal rise", "Log textile/EVA temperatures at fixed intervals", "Rise, duration, ambient conditions, and stop reason recorded", "Bench first; then supervised"],
    ["P11", "Breakaway routing", "Pull each removable low-voltage branch on the bench fixture", "Connector separates before cable becomes a restraint", "Three repetitions per branch"],
    ["P12", "Growth-interface cycling", "Insert, pin, remove, and inspect the interface in the cycle jig", "No crack, pin migration, binding, or new sharp edge", "50 bench cycles minimum"],
    ["P13", "Post-session inspection", "Repeat visual inspection and compare witness marks", "No damage or undocumented movement", "After every session"],
]


GATES = [
    {
        "id": "G0",
        "name": "Digital release complete",
        "pass": "Current hashes, model revisions, firmware builds, and print manifest are recorded.",
        "evidence": "R39/R40 verification files",
    },
    {
        "id": "G1",
        "name": "Bench hardware clear",
        "pass": "All printed parts and fixtures are inspected; no body-facing hard point remains exposed.",
        "evidence": "P01, fastener gauge, edge coupon",
    },
    {
        "id": "G2",
        "name": "Manual release clear",
        "pass": "Power-off release and extraction trials pass repeatedly from standing and seated positions.",
        "evidence": "P03, P04, P09",
    },
    {
        "id": "G3",
        "name": "Partial-body motion clear",
        "pass": "One arm and one leg remain clear through the planned motion envelope without pinch or migration.",
        "evidence": "P05, P06",
    },
    {
        "id": "G4",
        "name": "Helmet clear",
        "pass": "Vision, hearing, airflow, speech, and immediate manual face access are demonstrated.",
        "evidence": "P08",
    },
    {
        "id": "G5",
        "name": "Thermal and electrical clear",
        "pass": "Temperature and breakaway results are logged; electronics can be removed without changing fit.",
        "evidence": "P09, P10, P11",
    },
    {
        "id": "G6",
        "name": "Pilot session complete",
        "pass": "The session ends with a post-inspection, issue list, and explicit go/no-go decision for the next revision.",
        "evidence": "P13 and exported local session record",
    },
]


def create_docs(manifest: list[dict[str, object]]) -> None:
    with (DOCS / "PILOT_TEST_MATRIX_R40.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Test ID", "Test", "Method", "Pass condition", "Cadence"])
        writer.writerows(TEST_ROWS)

    log_fields = [
        "session_id",
        "date",
        "operator",
        "wearer_code",
        "configuration_hash",
        "ambient_c",
        "height_mm",
        "wearer_mass_kg",
        "suit_mass_kg",
        "don_time_s",
        "release_time_s_1",
        "release_time_s_2",
        "release_time_s_3",
        "chest_temp_start_c",
        "chest_temp_end_c",
        "helmet_temp_start_c",
        "helmet_temp_end_c",
        "left_shoulder_slip_mm",
        "right_shoulder_slip_mm",
        "waist_slip_mm",
        "pressure_hotspots_count",
        "vision_pass",
        "hearing_pass",
        "airflow_pass",
        "power_off_release_pass",
        "post_inspection_pass",
        "decision",
        "notes",
    ]
    with (DOCS / "PILOT_SESSION_LOG_R40.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(log_fields)
        for _ in range(12):
            writer.writerow([""] * len(log_fields))

    write(DOCS / "PASS_FAIL_GATES_R40.json", json.dumps(GATES, indent=2))
    with (DOCS / "RISK_REGISTER_R40.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Risk", "Trigger", "Immediate response", "Required disposition"])
        writer.writerows(
            [
                ["Blocked breathing or speech", "Any breathing difficulty, panic, or inability to speak normally", "Stop and remove helmet/suit immediately", "No further wear until root cause is corrected"],
                ["Pinch or hard stop", "Pain, captured clothing, joint lock, or shell collision", "Stop motion and remove affected region", "Revise geometry/carrier location and repeat partial-body test"],
                ["Thermal rise", "Unexpected heat, sweating, sensor alarm, or discomfort", "Power off and remove affected module/armor region", "Record temperature/time; improve ventilation or duty cycle"],
                ["Cable restraint", "Cable carries load or fails to disconnect", "Stop and manually disconnect", "Replace routing/connector before further wear"],
                ["Release inaccessible", "Wearer or helper cannot reach release", "Use secondary helper removal route", "Fail gate; redesign release routing"],
                ["Print crack or fastener movement", "Visible whitening, crack, loose insert, or witness-mark movement", "Retire part from wear", "Reprint or redesign; log revision"],
            ]
        )

    protocol = textwrap.dedent(
        """
        # IRON-KIDS K2 R40 physical-pilot protocol

        R40 does **not** claim that a child-worn pilot has been completed. It converts the remaining physical-validation work into a controlled, evidence-producing process and provides fixtures for the tests that can be performed off-body first.

        ## Sequence

        1. Freeze the exact digital release and record its hashes.
        2. Print and inspect the fixtures before wearable parts.
        3. Complete all bench tests with no child inside the armor.
        4. Fit the textile carrier and removable EVA separately.
        5. Advance one arm and one leg through partial-body supervised fitting.
        6. Add torso and helmet only after the release, motion, and comfort gates pass.
        7. Add optional electronics last, and repeat the power-off extraction test.
        8. End every session with a post-inspection and explicit go/no-go decision.

        ## Stop conditions

        Stop immediately for pain, panic, breathing difficulty, blocked speech, loss of balance, vision loss, trapped clothing, joint capture, unexpected heat, electrical odor, loose hardware, cracking, or any release that cannot be reached. A stopped test is valid evidence; it is not a failed child.

        ## Evidence discipline

        Record actual measurements. Do not convert missing results into assumed passes. A digital check, successful firmware compilation, or watertight STL is not physical validation. The local website console stores records only in the current browser and can export JSON/CSV for the build archive.
        """
    ).strip() + "\n"
    write(DOCS / "PHYSICAL_PILOT_PROTOCOL_R40.md", protocol)

    fixture_guide = ["# R40 fixture guide", ""]
    for item in manifest:
        fixture_guide.extend(
            [
                f"## {item['name']}",
                "",
                str(item["purpose"]),
                "",
                f"Suggested material: **{item['material']}**. Bounding box: {item['bbox_mm'][0]} × {item['bbox_mm'][1]} × {item['bbox_mm'][2]} mm.",
                "",
            ]
        )
    write(DOCS / "FIXTURE_USE_GUIDE_R40.md", "\n".join(fixture_guide))

    write(
        DOCS / "DATA_DICTIONARY_R40.md",
        textwrap.dedent(
            """
            # R40 session-data dictionary

            - `session_id`: unique non-personal identifier for the test session.
            - `wearer_code`: pseudonymous code; do not put a child's full name in a public release.
            - `configuration_hash`: SHA-256 or manifest identifier for the exact installed revision set.
            - `release_time_s_1..3`: three timed manual extractions; retain every result rather than only the best.
            - `*_slip_mm`: movement of witness markers after the controlled motion sequence.
            - `*_temp_*_c`: measured temperature at defined probe locations and times.
            - `decision`: `STOP`, `REVISE`, `REPEAT`, or `ADVANCE`.
            - Empty values remain unknown; they are never interpreted as passes.
            """
        ).strip()
        + "\n",
    )

    write(
        DOCS / "ASSEMBLY_READINESS_CHECKLIST_R40.md",
        textwrap.dedent(
            """
            # R40 assembly-readiness checklist

            - [ ] Exact model ZIP and SHA-256 recorded.
            - [ ] Print manifest reviewed in the slicer.
            - [ ] Carrier and EVA fit without PLA installed.
            - [ ] Every body-facing fastener shielded.
            - [ ] Every edge rounded and hand-inspected.
            - [ ] Manual releases reachable by wearer and helper.
            - [ ] Electronics removable without changing fit.
            - [ ] No cable crosses the throat or blocks a release.
            - [ ] One arm and one leg passed partial-body motion checks.
            - [ ] Helmet sight, hearing, speech, airflow, and removal checks complete.
            - [ ] Bench thermal and breakaway tests logged.
            - [ ] Session stop conditions reviewed with all adults present.
            """
        ).strip()
        + "\n",
    )


def make_fixture_contact_sheet(manifest: list[dict[str, object]]) -> None:
    width, height = 1600, 1000
    image = Image.new("RGB", (width, height), (244, 239, 228))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, width, 120), fill=(7, 14, 24))
    draw.text((42, 28), "IRON-KIDS K2 / R40 PHYSICAL VALIDATION FIXTURES", font=font(34, True), fill=(255, 250, 240))
    draw.text((42, 78), "Bench-first tools for fit, release, routing, thermal, and inspection evidence", font=font(20), fill=(227, 204, 151))
    cols = 3
    card_w = 500
    card_h = 200
    gap_x = 25
    gap_y = 18
    start_x = 25
    start_y = 145
    for index, item in enumerate(manifest):
        col = index % cols
        row = index // cols
        x = start_x + col * (card_w + gap_x)
        y = start_y + row * (card_h + gap_y)
        draw.rounded_rectangle((x, y, x + card_w, y + card_h), radius=18, fill=(255, 252, 245), outline=(197, 173, 116), width=2)
        name = str(item["name"]).replace("IK_K2_", "").replace("_R40", "").replace("_", " ")
        draw.text((x + 22, y + 18), name[:38], font=font(19, True), fill=(15, 28, 42))
        draw.text((x + 22, y + 50), str(item["category"]).upper(), font=font(14, True), fill=(149, 56, 46))
        purpose = str(item["purpose"])
        words = purpose.split()
        lines: list[str] = []
        current = ""
        for word in words:
            trial = f"{current} {word}".strip()
            if len(trial) > 58:
                lines.append(current)
                current = word
            else:
                current = trial
        if current:
            lines.append(current)
        for line_index, line in enumerate(lines[:4]):
            draw.text((x + 22, y + 82 + line_index * 22), line, font=font(14), fill=(69, 80, 92))
        dims = " × ".join(str(round(float(value), 1)) for value in item["bbox_mm"]) + " mm"
        draw.text((x + 22, y + 170), dims, font=font(13), fill=(27, 61, 100))
    target = PREVIEWS / "R40_FIXTURE_CONTACT_SHEET.png"
    image.save(target)
    shutil.copy2(target, SITE_ASSETS / "r40-fixtures.png")


def make_validation_video() -> None:
    frames = OUT / "r40-video-frames"
    if frames.exists():
        shutil.rmtree(frames)
    frames.mkdir(parents=True)
    stages = [
        ("01", "FREEZE THE RELEASE", "Record exact models, firmware, and hashes."),
        ("02", "BENCH FIRST", "Inspect, cycle, pull-test, and measure off-body."),
        ("03", "CARRIER + EVA", "Prove the soft fit system before exterior shells."),
        ("04", "PARTIAL BODY", "Advance one arm and one leg through slow motion."),
        ("05", "RELEASE + THERMAL", "Repeat extraction, power-off, and heat checks."),
        ("06", "DECIDE WITH EVIDENCE", "Stop, revise, repeat, or advance—never assume."),
    ]
    total_frames = len(stages) * 24
    for frame_index in range(total_frames):
        stage_index = min(len(stages) - 1, frame_index // 24)
        local = frame_index % 24
        progress = local / 23.0
        canvas = Image.new("RGB", (1280, 720), (5, 10, 17))
        draw = ImageDraw.Draw(canvas)
        draw.rectangle((0, 0, 1280, 12), fill=(197, 45, 43))
        draw.text((70, 52), "IRON-KIDS K2 / R40 PHYSICAL PILOT", font=font(25, True), fill=(232, 207, 151))
        number, title, subtitle = stages[stage_index]
        draw.text((70, 150), number, font=font(92, True), fill=(88, 170, 231))
        draw.text((250, 160), title, font=font(54, True), fill=(255, 250, 240))
        draw.text((255, 240), subtitle, font=font(25), fill=(188, 205, 223))
        y = 390
        for index, (_, stage_title, _) in enumerate(stages):
            x = 80 + index * 190
            active = index < stage_index or (index == stage_index and progress > 0.12)
            color = (213, 172, 72) if active else (57, 72, 89)
            draw.ellipse((x, y, x + 54, y + 54), fill=color)
            if index < len(stages) - 1:
                line_end = x + 185
                fill_end = int(x + 54 + max(0.0, min(1.0, progress if index == stage_index else 1.0 if index < stage_index else 0.0)) * (line_end - x - 54))
                draw.rectangle((x + 54, y + 24, line_end, y + 30), fill=(57, 72, 89))
                if fill_end > x + 54:
                    draw.rectangle((x + 54, y + 24, fill_end, y + 30), fill=(213, 172, 72))
            draw.text((x - 4, y + 72), str(index + 1).zfill(2), font=font(16, True), fill=(196, 207, 220))
        draw.rounded_rectangle((70, 580, 1210, 660), radius=18, outline=(56, 108, 155), width=2, fill=(11, 29, 48))
        draw.text((98, 603), "NO RESULT IS A PASS UNTIL IT IS MEASURED, RECORDED, AND REVIEWED.", font=font(25, True), fill=(130, 218, 255))
        canvas.save(frames / f"frame-{frame_index:04d}.png")

    output = SITE_ASSETS / "r40-validation-sequence.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-framerate",
            "24",
            "-i",
            str(frames / "frame-%04d.png"),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    poster = Image.open(frames / "frame-0000.png")
    poster.save(SITE_ASSETS / "r40-validation-poster.png")
    shutil.copy2(output, PREVIEWS / output.name)
    shutil.copy2(SITE_ASSETS / "r40-validation-poster.png", PREVIEWS / "R40_VALIDATION_POSTER.png")
    shutil.rmtree(frames)


DASHBOARD_JS = r'''(() => {
  const KEY = 'ironKidsR40Sessions';
  const form = document.querySelector('#r40-session-form');
  const tableBody = document.querySelector('#r40-session-rows');
  const status = document.querySelector('#r40-storage-status');
  const fields = [...form.querySelectorAll('[name]')];

  function readSessions() {
    try { return JSON.parse(localStorage.getItem(KEY) || '[]'); }
    catch (_) { return []; }
  }
  function writeSessions(sessions) {
    localStorage.setItem(KEY, JSON.stringify(sessions));
    status.textContent = `${sessions.length} local session record${sessions.length === 1 ? '' : 's'}`;
  }
  function formRecord() {
    const record = {};
    fields.forEach(field => {
      record[field.name] = field.type === 'checkbox' ? field.checked : field.value;
    });
    record.saved_at = new Date().toISOString();
    return record;
  }
  function escapeText(value) {
    return String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  }
  function render() {
    const sessions = readSessions();
    tableBody.innerHTML = sessions.map((session, index) => `
      <tr>
        <td>${escapeText(session.session_id || '—')}</td>
        <td>${escapeText(session.date || '—')}</td>
        <td>${escapeText(session.decision || '—')}</td>
        <td>${escapeText(session.release_time_s_1 || '—')}</td>
        <td>${escapeText(session.suit_mass_kg || '—')}</td>
        <td><button type="button" class="tiny" data-delete="${index}">Delete</button></td>
      </tr>`).join('');
    writeSessions(sessions);
  }
  function download(name, text, type) {
    const blob = new Blob([text], {type});
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = name;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  function csvCell(value) {
    const text = String(value ?? '');
    return `"${text.replaceAll('"', '""')}"`;
  }

  form.addEventListener('submit', event => {
    event.preventDefault();
    const record = formRecord();
    if (!record.session_id) {
      alert('Session ID is required.');
      return;
    }
    const sessions = readSessions();
    sessions.push(record);
    writeSessions(sessions);
    form.reset();
    render();
  });
  document.querySelector('#r40-export-json').addEventListener('click', () => {
    download('IRON_KIDS_R40_SESSION_EXPORT.json', JSON.stringify(readSessions(), null, 2), 'application/json');
  });
  document.querySelector('#r40-export-csv').addEventListener('click', () => {
    const sessions = readSessions();
    const keys = [...new Set(sessions.flatMap(Object.keys))];
    const rows = [keys.map(csvCell).join(','), ...sessions.map(session => keys.map(key => csvCell(session[key])).join(','))];
    download('IRON_KIDS_R40_SESSION_EXPORT.csv', rows.join('\n'), 'text/csv');
  });
  document.querySelector('#r40-clear').addEventListener('click', () => {
    if (confirm('Delete every locally stored R40 session record in this browser?')) {
      localStorage.removeItem(KEY);
      render();
    }
  });
  tableBody.addEventListener('click', event => {
    const button = event.target.closest('[data-delete]');
    if (!button) return;
    const sessions = readSessions();
    sessions.splice(Number(button.dataset.delete), 1);
    writeSessions(sessions);
    render();
  });
  render();
})();
'''


R40_CSS = r'''.r40-banner{background:linear-gradient(135deg,#071a36,#102d4b);border:1px solid rgba(115,220,255,.4);border-radius:24px;padding:1.4rem;margin:1.5rem auto}.r40-banner h2{font-size:clamp(1.8rem,3vw,3.2rem);margin:.3rem 0}.r40-banner p{color:#d0dbe8}.r40-gates{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem}.r40-gate{background:#fffaf0;border:1px solid #ddcfaf;border-radius:18px;padding:1.2rem;color:#15202c}.r40-gate b{display:block;color:#8d2e28;letter-spacing:.08em}.r40-gate p{color:#4b5662}.r40-media{display:grid;grid-template-columns:1fr 1fr;gap:1rem}.r40-media img,.r40-media video{display:block;width:100%;height:auto;border:1px solid rgba(211,172,72,.35);border-radius:20px;background:#02060b}.r40-console{background:#07101b;border:1px solid #2f648e;border-radius:22px;padding:1.2rem}.r40-form-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:.8rem}.r40-console label{display:grid;gap:.35rem;color:#d7e2ee;font-weight:750}.r40-console input,.r40-console select,.r40-console textarea{width:100%;background:#111d2c;border:1px solid #315d82;border-radius:10px;color:#fff;padding:.7rem;font:inherit}.r40-console textarea{min-height:110px;resize:vertical}.r40-checks{display:grid;grid-template-columns:repeat(3,1fr);gap:.6rem;margin:1rem 0}.r40-checks label{display:flex;align-items:center;gap:.5rem;background:#101d2c;border-radius:10px;padding:.7rem}.r40-checks input{width:auto}.r40-actions{display:flex;flex-wrap:wrap;gap:.6rem}.r40-actions button,.tiny{border:1px solid #4f86b3;background:#12304c;color:#fff;border-radius:10px;padding:.7rem 1rem;font-weight:800;cursor:pointer}.r40-actions button.primary{background:linear-gradient(135deg,#df5548,#a92a28);border-color:#e36053}.r40-table-wrap{overflow:auto;margin-top:1rem}.r40-table{width:100%;border-collapse:collapse;background:#fff;color:#15202c}.r40-table th{background:#142334;color:#fff}.r40-table th,.r40-table td{padding:.7rem;border-bottom:1px solid #dce2e8;text-align:left}.local-only{color:#9fc5e6;font-size:.92rem}@media(max-width:950px){.r40-gates,.r40-media,.r40-form-grid,.r40-checks{grid-template-columns:1fr}}'''


def patch_site() -> None:
    write(SITE_ASSETS / "r40.css", R40_CSS)
    write(SITE_ASSETS / "r40-dashboard.js", DASHBOARD_JS)

    for html_path in SITE.rglob("*.html"):
        text = html_path.read_text(encoding="utf-8")
        text = text.replace("ENGINEERING A FAMILY / R39", "ENGINEERING A FAMILY / R40")
        text = text.replace("<b>R39</b>", "<b>R40</b>")
        text = text.replace("R39 COMMISSIONING ↗", "R40 VALIDATION ↗")
        if "/assets/r40/r40.css" not in text:
            text = text.replace("</head>", '<link rel="stylesheet" href="/assets/r40/r40.css"></head>')
        if "/iron-kids/validation/" not in text:
            text = text.replace("</nav>", '<a href="/iron-kids/validation/">Validation</a></nav>', 1)
        html_path.write_text(text, encoding="utf-8")

    banner = '''<section class="shell r40-banner"><span class="kicker">R40 / PHYSICAL PILOT READINESS</span><h2>The digital pilot now has a real validation path.</h2><p>R40 adds printable bench fixtures, explicit pass/fail gates, a controlled physical-pilot protocol, and a local-only session console without pretending that unperformed physical tests have passed.</p><div class="actions"><a class="button" href="/iron-kids/validation/">Open R40 validation ↗</a><a class="button alt" href="/downloads/IRON_KIDS_K2_PHYSICAL_VALIDATION_R40.zip">Download R40 package ↗</a></div></section>'''
    for relative in [Path("index.html"), Path("iron-kids/index.html"), Path("iron-kids/pilot/index.html"), Path("iron-kids/commissioning/index.html")]:
        target = SITE / relative
        if target.exists():
            text = target.read_text(encoding="utf-8")
            if "R40 / PHYSICAL PILOT READINESS" not in text:
                text = text.replace("</main>", banner + "</main>")
            target.write_text(text, encoding="utf-8")

    gates_html = "".join(
        f'<article class="r40-gate"><b>{gate["id"]} / {gate["name"]}</b><p>{gate["pass"]}</p><small>{gate["evidence"]}</small></article>'
        for gate in GATES
    )
    validation_page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#080b10"><title>IRON-KIDS R40 — Physical Pilot Validation</title><meta name="description" content="Printable validation fixtures, evidence gates, and a local-only physical pilot console for the K2 armor program."><meta property="og:title" content="IRON-KIDS R40 Physical Pilot Validation"><meta property="og:image" content="/assets/r40/r40-validation-poster.png"><link rel="stylesheet" href="/assets/site.css"><link rel="stylesheet" href="/assets/r39/r39.css"><link rel="stylesheet" href="/assets/r40/r40.css"></head><body><header class="top"><div class="shell nav"><a class="brand" href="/"><span class="mark">JT</span><span>IRON—DAD<small>ENGINEERING A FAMILY / R40</small></span></a><nav class="links"><a href="/family/">Family</a><a href="/iron-dad/">IRON-DAD</a><a href="/iron-kitty/">IRON-KITTY</a><a href="/iron-kids/">IRON-KIDS</a><a href="/iron-kids/pilot/">K2 Pilot</a><a href="/iron-kids/commissioning/">Commissioning</a><a aria-current="page" href="/iron-kids/validation/">Validation</a><a href="/downloads/">Downloads</a></nav></div></header><main><section class="shell page-hero"><span class="kicker">R40 / PHYSICAL PILOT READINESS</span><h1>TEST WHAT<br><em>THE MODEL CANNOT.</em></h1><p>R40 turns the uncompleted physical pilot into a measured, staged process: bench fixtures first, textile and EVA fit next, partial-body movement before complete assembly, and electronics last.</p><div class="actions"><a class="button" href="/downloads/{PACKAGE_NAME}">Download R40 package ↗</a><a class="button alt" href="#console">Open local session console ↓</a></div></section><section class="section"><div class="shell r40-media"><video controls muted loop playsinline poster="/assets/r40/r40-validation-poster.png"><source src="/assets/r40/r40-validation-sequence.mp4" type="video/mp4"></video><img src="/assets/r40/r40-fixtures.png" alt="R40 physical validation fixture contact sheet"></div></section><section class="paper section"><div class="shell"><span class="kicker" style="color:#8a2b27">EVIDENCE GATES</span><h2 class="section-title">ADVANCE ONLY<br><em>WHEN THE GATE PASSES.</em></h2><div class="r40-gates">{gates_html}</div><div class="notice" style="margin-top:1rem"><strong>Current status:</strong> R40 provides the process and fixtures. It does not claim a printed, thermally commissioned, or child-fitted suit.</div></div></section><section class="section" id="console"><div class="shell"><span class="kicker">LOCAL-ONLY FIELD CONSOLE</span><h2 class="section-title">RECORD THE<br><em>ACTUAL SESSION.</em></h2><p class="local-only">Data stays in this browser's local storage unless you export it. Do not enter a child's full name in a public engineering archive.</p><div class="r40-console"><form id="r40-session-form"><div class="r40-form-grid"><label>Session ID<input name="session_id" required placeholder="K2-SESSION-001"></label><label>Date<input type="date" name="date"></label><label>Wearer code<input name="wearer_code" placeholder="PILOT-A"></label><label>Configuration hash<input name="configuration_hash" placeholder="SHA-256 / manifest ID"></label><label>Ambient °C<input type="number" step="0.1" name="ambient_c"></label><label>Suit mass kg<input type="number" step="0.01" name="suit_mass_kg"></label><label>Don time seconds<input type="number" step="0.1" name="don_time_s"></label><label>Release time 1 seconds<input type="number" step="0.1" name="release_time_s_1"></label><label>Release time 2 seconds<input type="number" step="0.1" name="release_time_s_2"></label><label>Release time 3 seconds<input type="number" step="0.1" name="release_time_s_3"></label><label>Chest start °C<input type="number" step="0.1" name="chest_temp_start_c"></label><label>Chest end °C<input type="number" step="0.1" name="chest_temp_end_c"></label><label>Helmet start °C<input type="number" step="0.1" name="helmet_temp_start_c"></label><label>Helmet end °C<input type="number" step="0.1" name="helmet_temp_end_c"></label><label>Left shoulder slip mm<input type="number" step="0.1" name="left_shoulder_slip_mm"></label><label>Right shoulder slip mm<input type="number" step="0.1" name="right_shoulder_slip_mm"></label><label>Waist slip mm<input type="number" step="0.1" name="waist_slip_mm"></label><label>Pressure hotspots<input type="number" step="1" min="0" name="pressure_hotspots_count"></label><label>Decision<select name="decision"><option value="">Select</option><option>STOP</option><option>REVISE</option><option>REPEAT</option><option>ADVANCE</option></select></label></div><div class="r40-checks"><label><input type="checkbox" name="vision_pass">Vision pass</label><label><input type="checkbox" name="hearing_pass">Hearing pass</label><label><input type="checkbox" name="airflow_pass">Airflow pass</label><label><input type="checkbox" name="power_off_release_pass">Power-off release pass</label><label><input type="checkbox" name="post_inspection_pass">Post-inspection pass</label></div><label>Notes<textarea name="notes" placeholder="Unknown values remain blank. Record stop conditions and defects exactly."></textarea></label><div class="r40-actions"><button class="primary" type="submit">Save local record</button><button type="button" id="r40-export-json">Export JSON</button><button type="button" id="r40-export-csv">Export CSV</button><button type="button" id="r40-clear">Clear local records</button></div></form><p id="r40-storage-status" class="local-only"></p><div class="r40-table-wrap"><table class="r40-table"><thead><tr><th>Session</th><th>Date</th><th>Decision</th><th>Release 1</th><th>Mass</th><th></th></tr></thead><tbody id="r40-session-rows"></tbody></table></div></div></div></section></main><footer class="footer"><div class="shell footer-grid"><div><b>IRON-DAD / Justin Tahai</b><p>Engineering a family—and keeping digital work separate from physical proof.</p></div><div><a href="/iron-kids/pilot/">R38 pilot</a><br><a href="/iron-kids/commissioning/">R39 commissioning</a><br><a href="/iron-kids/validation/">R40 validation</a></div><div><a href="/downloads/{PACKAGE_NAME}">Download R40</a></div></div></footer><script src="/assets/r40/r40-dashboard.js"></script></body></html>'''
    write(SITE / "iron-kids" / "validation" / "index.html", validation_page)

    downloads = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>IRON-DAD R40 Downloads</title><meta name="description" content="Current IRON-DAD family engineering downloads."><link rel="stylesheet" href="/assets/site.css"><link rel="stylesheet" href="/assets/r39/r39.css"><link rel="stylesheet" href="/assets/r40/r40.css"></head><body><header class="top"><div class="shell nav"><a class="brand" href="/"><span class="mark">JT</span><span>IRON—DAD<small>ENGINEERING A FAMILY / R40</small></span></a><nav class="links"><a href="/family/">Family</a><a href="/iron-kids/pilot/">K2 Pilot</a><a href="/iron-kids/commissioning/">Commissioning</a><a href="/iron-kids/validation/">Validation</a><a aria-current="page" href="/downloads/">Downloads</a></nav></div></header><main><section class="shell page-hero"><span class="kicker">CURRENT VERIFIED ARTIFACT</span><h1>R40<br><em>DOWNLOAD DESK.</em></h1><p>The complete registered K2 pilot, compiled R39 electronics, print release, and the R40 physical-validation fixtures, logs, gates, and protocol.</p></section><section class="paper section"><div class="shell"><div class="download"><div><h2>IRON-KIDS K2 Physical Validation R40</h2><p>R38 registered models, R39 compiled firmware and print commissioning, twelve R40 validation fixtures, field logs, test matrix, risk register, and verification evidence.</p></div><a class="button" href="/downloads/{PACKAGE_NAME}">Download ZIP ↗</a></div></div></section></main><footer class="footer"><div class="shell"><a href="/">Back to IRON-DAD</a></div></footer></body></html>'''
    write(SITE / "downloads" / "index.html", downloads)


def audit_references() -> list[dict[str, str]]:
    missing: list[dict[str, str]] = []
    for html_path in SITE.rglob("*.html"):
        text = html_path.read_text(encoding="utf-8")
        for raw in re.findall(r'(?:href|src)=["\']([^"\']+)', text):
            if raw.startswith(("http:", "https:", "mailto:", "tel:", "#", "data:")):
                continue
            target = raw.split("#", 1)[0].split("?", 1)[0]
            if not target:
                continue
            resolved = SITE / target.lstrip("/") if target.startswith("/") else html_path.parent / target
            if target.endswith("/"):
                resolved = resolved / "index.html"
            if not resolved.exists():
                missing.append({"page": str(html_path.relative_to(SITE)), "target": raw})
    return missing


def package_release(manifest: list[dict[str, object]]) -> None:
    write(SOURCE / "build.py", Path(__file__).read_text(encoding="utf-8"))
    validation_report = {
        "release": RELEASE,
        "base_release": "R39",
        "fixture_count": len(manifest),
        "all_fixture_stls_watertight": all(bool(item["watertight"]) for item in manifest),
        "all_fixture_stls_positive_volume": all(bool(item["positive_volume"]) for item in manifest),
        "all_fixture_stls_within_220x220x240": all(bool(item["within_220x220x240"]) for item in manifest),
        "test_matrix_rows": len(TEST_ROWS),
        "evidence_gates": len(GATES),
        "physical_child_validation_performed": False,
        "remaining_planned_passes": 1,
    }
    write(DOCS / "VERIFICATION_R40.json", json.dumps(validation_report, indent=2))

    checks: list[str] = []
    for path in sorted(VALIDATION.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS_R40.txt":
            checks.append(f"{sha256(path)}  {path.relative_to(VALIDATION).as_posix()}")
    write(VALIDATION / "SHA256SUMS_R40.txt", "\n".join(checks) + "\n")

    package = SITE_DOWNLOADS / PACKAGE_NAME
    if package.exists():
        package.unlink()
    with zipfile.ZipFile(package, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(MODEL.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(MODEL))

    missing = audit_references()
    site_report = {
        "release": RELEASE,
        "root_index_exists": (SITE / "index.html").exists(),
        "html_pages": len(list(SITE.rglob("*.html"))),
        "image_files": len([p for p in SITE.rglob("*") if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".svg"}]),
        "video_files": len([p for p in SITE.rglob("*") if p.suffix.lower() in {".mp4", ".webm"}]),
        "missing_local_references": missing,
        "package": PACKAGE_NAME,
        "package_bytes": package.stat().st_size,
        "package_sha256": sha256(package),
        "validation_console_present": (SITE / "iron-kids" / "validation" / "index.html").exists(),
        "physical_child_validation_performed": False,
        "remaining_planned_passes": 1,
    }
    write(SITE / "R40_VERIFICATION.json", json.dumps(site_report, indent=2))
    if missing:
        raise RuntimeError(f"missing local references: {missing[:8]}")


def main() -> None:
    if not (SITE / "R39_VERIFICATION.json").exists():
        raise RuntimeError("R39 output is required before R40")
    manifest = build_fixtures()
    create_docs(manifest)
    make_fixture_contact_sheet(manifest)
    make_validation_video()
    patch_site()
    package_release(manifest)
    print(
        json.dumps(
            {
                "release": RELEASE,
                "fixtures": len(manifest),
                "pages": len(list(SITE.rglob("*.html"))),
                "images": len([p for p in SITE.rglob("*") if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".svg"}]),
                "videos": len([p for p in SITE.rglob("*") if p.suffix.lower() in {".mp4", ".webm"}]),
                "remaining_planned_passes": 1,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
