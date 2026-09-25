#!/usr/bin/env python3
"""Build IRON-DAD R33 full-body integration, IRON-KITTY R34 geometry,
and the R34 Cloudflare Pages engineering site.

This is a deterministic CAD-development package generator. Geometry is original
engineering-study geometry and is explicitly not load-rated or animal-wear approved.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"
R33 = OUT / "IRON_DAD_FULL_BODY_INTEGRATION_R33"
R34K = OUT / "IRON_KITTY_GEOMETRY_R34"
SITE = OUT / "IRON_DAD_CLOUDFLARE_PAGES_R34"

COLORS = {
    "red": (160, 25, 30, 255),
    "gold": (205, 160, 60, 255),
    "blue": (20, 92, 180, 255),
    "cyan": (65, 205, 255, 255),
    "graphite": (35, 40, 48, 255),
    "silver": (170, 180, 192, 255),
    "white": (240, 242, 245, 255),
    "gray": (105, 112, 122, 255),
}

@dataclass
class Part:
    name: str
    mesh: trimesh.Trimesh
    category: str
    color: Tuple[int, int, int, int]
    notes: str
    print_material: str = "PETG/PLA prototype"
    evidence: str = "modeled"


def fresh(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def box(extents, pos=(0, 0, 0), rot=None) -> trimesh.Trimesh:
    m = trimesh.creation.box(extents=np.asarray(extents, dtype=float))
    if rot is not None:
        m.apply_transform(rot)
    m.apply_translation(np.asarray(pos, dtype=float))
    return m


def cyl(radius, height, pos=(0, 0, 0), axis=(0, 0, 1), sections=40) -> trimesh.Trimesh:
    m = trimesh.creation.cylinder(radius=radius, height=height, sections=sections)
    axis = np.asarray(axis, dtype=float)
    axis /= np.linalg.norm(axis)
    T = trimesh.geometry.align_vectors([0, 0, 1], axis)
    if T is not None:
        m.apply_transform(T)
    m.apply_translation(np.asarray(pos, dtype=float))
    return m


def link_between(a, b, radius=10, sections=32) -> trimesh.Trimesh:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    v = b - a
    length = float(np.linalg.norm(v))
    return cyl(radius, length, (a + b) / 2.0, v / length, sections)


def ellipsoid(radii, pos=(0, 0, 0), subdivisions=3) -> trimesh.Trimesh:
    m = trimesh.creation.icosphere(subdivisions=subdivisions, radius=1.0)
    m.apply_scale(np.asarray(radii, dtype=float))
    m.apply_translation(np.asarray(pos, dtype=float))
    return m


def wedge(extents, pos=(0, 0, 0), tilt_deg=0, axis=(1, 0, 0)) -> trimesh.Trimesh:
    m = box(extents)
    if tilt_deg:
        R = trimesh.transformations.rotation_matrix(math.radians(tilt_deg), axis)
        m.apply_transform(R)
    m.apply_translation(pos)
    return m


def paint(mesh: trimesh.Trimesh, color) -> trimesh.Trimesh:
    mesh.visual.face_colors = np.tile(np.asarray(color, dtype=np.uint8), (len(mesh.faces), 1))
    return mesh


def print_orient(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    m = mesh.copy()
    bounds = m.bounds
    center_xy = (bounds[0, :2] + bounds[1, :2]) / 2.0
    m.apply_translation([-center_xy[0], -center_xy[1], -bounds[0, 2]])
    return m


def part_record(part: Part) -> dict:
    b = part.mesh.bounds
    ext = part.mesh.extents
    return {
        "name": part.name,
        "category": part.category,
        "notes": part.notes,
        "print_material": part.print_material,
        "evidence": part.evidence,
        "watertight": bool(part.mesh.is_watertight),
        "winding_consistent": bool(part.mesh.is_winding_consistent),
        "volume_mm3": round(float(abs(part.mesh.volume)), 3),
        "assembly_bounds_mm": np.asarray(b).round(3).tolist(),
        "extents_mm": np.asarray(ext).round(3).tolist(),
        "centroid_mm": np.asarray(part.mesh.centroid).round(3).tolist(),
    }


def export_package(base: Path, parts: List[Part], title: str, readme: str,
                   scene_name: str, preview_title: str, category_colors: Dict[str, str]) -> dict:
    for sub in ["STL_PRINT", "ASSEMBLY", "MANIFEST", "PREVIEWS", "SOURCE", "DOCS"]:
        (base / sub).mkdir(parents=True, exist_ok=True)

    records = []
    scene = trimesh.Scene()
    exploded = trimesh.Scene()
    centers = np.array([p.mesh.centroid for p in parts])
    global_center = centers.mean(axis=0) if len(centers) else np.zeros(3)

    for p in parts:
        pm = print_orient(p.mesh)
        pm.export(base / "STL_PRINT" / f"{p.name}.stl")
        colored = paint(p.mesh.copy(), p.color)
        scene.add_geometry(colored, node_name=p.name, geom_name=p.name)
        em = colored.copy()
        vec = np.asarray(p.mesh.centroid) - global_center
        norm = np.linalg.norm(vec)
        if norm > 1e-6:
            em.apply_translation(vec / norm * 90.0)
        exploded.add_geometry(em, node_name=p.name, geom_name=p.name)
        rec = part_record(p)
        rec["print_stl"] = f"STL_PRINT/{p.name}.stl"
        records.append(rec)

    scene.export(base / "ASSEMBLY" / f"{scene_name}_ASSEMBLY.glb")
    exploded.export(base / "ASSEMBLY" / f"{scene_name}_EXPLODED.glb")
    (base / "MANIFEST" / "PARTS.json").write_text(json.dumps(records, indent=2))
    with (base / "MANIFEST" / "PARTS.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "category", "x_mm", "y_mm", "z_mm", "watertight", "material", "evidence", "notes"])
        for r in records:
            w.writerow([r["name"], r["category"], *r["extents_mm"], r["watertight"], r["print_material"], r["evidence"], r["notes"]])
    (base / "README.md").write_text(readme)
    (base / "DOCS" / "EVIDENCE_BOUNDARY.md").write_text(
        "# Evidence boundary\n\nAll geometry in this package is **modeled development geometry**. "
        "STL/GLB export and mesh checks are digital evidence only. They do not establish load capacity, "
        "comfort, animal suitability, human safety, collision-free movement, or production readiness.\n"
    )
    (base / "DOCS" / "LICENSE_AND_PROVENANCE.md").write_text(
        "# License and provenance\n\nThe engineering-study geometry in this package is original to this pass. "
        "IRON-DAD and IRON-KITTY remain visual/concept descendants of the wider Mk6-inspired project direction. "
        "No DaDave mesh bytes are included in these procedural integration-study parts.\n"
    )
    shutil.copy2(__file__, base / "SOURCE" / "iron_family_builder.py")
    make_preview(parts, base / "PREVIEWS" / f"{scene_name}_PREVIEW.png", preview_title, category_colors)

    validation = {
        "package": title,
        "part_count": len(parts),
        "watertight_count": sum(bool(p.mesh.is_watertight) for p in parts),
        "winding_consistent_count": sum(bool(p.mesh.is_winding_consistent) for p in parts),
        "positive_volume_count": sum(abs(float(p.mesh.volume)) > 1e-6 for p in parts),
        "assembly_glb": f"ASSEMBLY/{scene_name}_ASSEMBLY.glb",
        "exploded_glb": f"ASSEMBLY/{scene_name}_EXPLODED.glb",
        "status": "MODELED / NOT PHYSICALLY VALIDATED",
    }
    (base / "MANIFEST" / "VALIDATION.json").write_text(json.dumps(validation, indent=2))
    return validation


def make_preview(parts: List[Part], path: Path, title: str, category_colors: Dict[str, str]) -> None:
    fig = plt.figure(figsize=(15, 9), facecolor="#070b10")
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor("#070b10")
    for p in parts:
        b = p.mesh.bounds
        lo, hi = b[0], b[1]
        verts = np.array([
            [lo[0], lo[1], lo[2]], [hi[0], lo[1], lo[2]], [hi[0], hi[1], lo[2]], [lo[0], hi[1], lo[2]],
            [lo[0], lo[1], hi[2]], [hi[0], lo[1], hi[2]], [hi[0], hi[1], hi[2]], [lo[0], hi[1], hi[2]],
        ])
        faces = [[0,1,2,3],[4,5,6,7],[0,1,5,4],[2,3,7,6],[1,2,6,5],[3,0,4,7]]
        poly = Poly3DCollection([[verts[i] for i in f] for f in faces], alpha=.42,
                                facecolor=category_colors.get(p.category, "#b88a3c"),
                                edgecolor="#e8d6ad", linewidth=.25)
        ax.add_collection3d(poly)
    all_bounds = np.vstack([p.mesh.bounds for p in parts])
    mins, maxs = all_bounds.min(axis=0), all_bounds.max(axis=0)
    center = (mins + maxs) / 2
    span = max(maxs - mins)
    for setter, c in [(ax.set_xlim, center[0]), (ax.set_ylim, center[1]), (ax.set_zlim, center[2])]:
        setter(c - span*.55, c + span*.55)
    ax.view_init(elev=12, azim=-68)
    ax.set_axis_off()
    fig.suptitle(title, color="#f4e9d4", fontsize=28, fontweight="bold", x=.04, ha="left", y=.95)
    fig.text(.04, .89, "DIGITAL ASSEMBLY STUDY · MODELED, NOT PHYSICALLY VALIDATED", color="#d6ae58", fontsize=11)
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def adult_parts() -> List[Part]:
    P: List[Part] = []
    def add(name, mesh, category, color, notes, material="PETG/PLA prototype"):
        P.append(Part(name, mesh, category, COLORS[color], notes, material))

    for side, sx in [("L", -1), ("R", 1)]:
        add(f"ID33_SHOULDER_YOKE_{side}", box((135, 42, 34), (sx*68, -58, 1535)), "frame", "gold", "Split shoulder-yoke half with center coupling datum.")
        add(f"ID33_SPINE_RAIL_UPPER_{side}", box((24, 34, 205), (sx*72, -105, 1405)), "frame", "gold", "Upper torso rail; frame study only.")
        add(f"ID33_SPINE_RAIL_LOWER_{side}", box((24, 34, 205), (sx*72, -105, 1200)), "frame", "gold", "Lower torso rail; frame study only.")
        add(f"ID33_PELVIS_SIDE_{side}", box((42, 86, 170), (sx*142, -18, 980)), "frame", "gold", "Pelvis load-path side plate; no load rating.")
        add(f"ID33_PELVIS_FRONT_HALF_{side}", box((150, 34, 38), (sx*75, 62, 1028)), "frame", "gold", "Split pelvis front crossmember.")
        add(f"ID33_PELVIS_REAR_HALF_{side}", box((150, 34, 38), (sx*75, -98, 1028)), "frame", "gold", "Split pelvis rear crossmember.")
        add(f"ID33_HIP_PIVOT_CARRIER_{side}", cyl(34, 30, (sx*150, -20, 930), (1,0,0)), "joint", "silver", "Hip pivot carrier envelope; bearing stack unselected.")
        add(f"ID33_MANUAL_RELEASE_HANDLE_{side}", box((24, 18, 110), (sx*210, 58, 1120)), "release", "cyan", "Reachable mechanical-release handle study.")

    add("ID33_CHEST_SERVICE_PANEL", wedge((215, 22, 185), (0, 85, 1390), -6, (1,0,0)), "skin", "red", "Removable frame-referenced chest service panel.")
    add("ID33_BACK_SERVICE_PANEL", wedge((220, 22, 210), (0, -132, 1370), 5, (1,0,0)), "skin", "red", "Removable back service panel with electronics clearance envelope.")
    add("ID33_COLLAR_FRONT", box((165, 24, 35), (0, 45, 1580)), "soft_interface", "blue", "Collar transition datum; throat remains soft.")
    add("ID33_COLLAR_REAR", box((165, 24, 35), (0, -105, 1580)), "soft_interface", "blue", "Rear collar datum; not a neck restraint.")
    add("ID33_HELMET_BROW_RAIL", box((175, 28, 22), (0, -8, 1785)), "ar", "cyan", "Head-supported optical datum rail envelope.")
    add("ID33_HELMET_REAR_RAIL", box((165, 28, 22), (0, -132, 1770)), "ar", "cyan", "Rear optical carrier datum envelope.")

    for side, sx in [("L", -1), ("R", 1)]:
        shoulder = np.array([sx*275, -25, 1515.0])
        elbow = np.array([sx*355, 0, 1265.0])
        wrist = np.array([sx*385, 28, 1045.0])
        mid1 = shoulder + (elbow-shoulder)*.48
        mid2 = elbow + (wrist-elbow)*.5
        add(f"ID33_UPPER_ARM_LINK_A_{side}", link_between(shoulder, mid1, 13), "frame", "gold", "Upper-arm proximal rail segment.")
        add(f"ID33_UPPER_ARM_LINK_B_{side}", link_between(mid1, elbow, 13), "frame", "gold", "Upper-arm distal rail segment.")
        add(f"ID33_ELBOW_CARRIER_{side}", cyl(30, 28, elbow, (1,0,0)), "joint", "silver", "Elbow carrier envelope; alignment requires wearer measurement.")
        add(f"ID33_FOREARM_LINK_A_{side}", link_between(elbow, mid2, 11), "frame", "gold", "Forearm proximal rail segment.")
        add(f"ID33_FOREARM_LINK_B_{side}", link_between(mid2, wrist, 11), "frame", "gold", "Forearm distal rail segment.")
        add(f"ID33_WRIST_CARRIER_{side}", cyl(27, 24, wrist, (1,0,0)), "joint", "silver", "Wrist carrier envelope; palm-side remains soft.")
        for i, dz in enumerate([35, 5, -25], 1):
            add(f"ID33_SHOULDER_PETAL_{side}_{i}", wedge((105-i*8, 14, 48), (sx*(250+i*12), 5, 1515+dz), sx*4, (0,1,0)), "skin", "red", "Independent shoulder coverage petal.")

    for side, sx in [("L", -1), ("R", 1)]:
        hip = np.array([sx*150, -18, 930.0])
        knee = np.array([sx*165, 5, 545.0])
        ankle = np.array([sx*165, 18, 150.0])
        q1 = hip + (knee-hip)*.33
        q2 = hip + (knee-hip)*.66
        s1 = knee + (ankle-knee)*.33
        s2 = knee + (ankle-knee)*.66
        for label,a,b in [("A",hip,q1),("B",q1,q2),("C",q2,knee)]:
            add(f"ID33_THIGH_LINK_{label}_{side}", link_between(a,b,15), "frame", "gold", "Segmented thigh load-path rail.")
        add(f"ID33_KNEE_CARRIER_{side}", cyl(36, 30, knee, (1,0,0)), "joint", "silver", "Knee carrier envelope; rear knee remains soft.")
        for label,a,b in [("A",knee,s1),("B",s1,s2),("C",s2,ankle)]:
            add(f"ID33_SHIN_LINK_{label}_{side}", link_between(a,b,14), "frame", "gold", "Segmented shin load-path rail.")
        add(f"ID33_ANKLE_CARRIER_{side}", cyl(30, 28, ankle, (1,0,0)), "joint", "silver", "Ankle carrier envelope; Achilles remains soft.")
        add(f"ID33_FOOT_PLATE_FRONT_{side}", box((105, 175, 18), (sx*165, 70, 65)), "ground", "graphite", "Front foot load-path plate study.")
        add(f"ID33_FOOT_PLATE_HEEL_{side}", box((90, 90, 18), (sx*165, -55, 65)), "ground", "graphite", "Heel load-path plate study.")
        add(f"ID33_THIGH_SKIN_PANEL_{side}", wedge((92, 26, 205), (sx*178, 48, 745), sx*3, (0,1,0)), "skin", "red", "Removable thigh skin panel envelope.")
        add(f"ID33_SHIN_SKIN_PANEL_{side}", wedge((82, 24, 210), (sx*178, 52, 340), sx*2, (0,1,0)), "skin", "red", "Removable shin skin panel envelope.")

    add("ID33_HARNESS_CHEST_BRIDGE", box((180, 12, 55), (0, 35, 1350)), "harness", "blue", "Soft-carrier chest bridge representation.", "TPU/textile reference")
    add("ID33_HARNESS_BACK_BRIDGE", box((180, 12, 55), (0, -92, 1350)), "harness", "blue", "Soft-carrier back bridge representation.", "TPU/textile reference")
    add("ID33_TORSO_COMPUTER_CASSETTE", box((155, 55, 205), (0, -170, 1270)), "electronics", "graphite", "Removable torso-computer envelope; not a finished enclosure.")
    add("ID33_POWER_CASSETTE_LEFT", box((78, 48, 165), (-205, -60, 1020)), "electronics", "graphite", "Accessible power-cassette envelope.")
    add("ID33_HARDWIRED_STOP_GUARD", box((70, 45, 95), (210, -60, 1190)), "release", "cyan", "Independent stop/release control guard envelope.")
    return P


def kitty_parts() -> Tuple[List[Part], List[Part]]:
    armor: List[Part] = []
    mannequin: List[Part] = []
    def add_a(name, mesh, category, color, notes, material="PLA display prototype"):
        armor.append(Part(name, mesh, category, COLORS[color], notes, material))
    def add_m(name, mesh, color, notes):
        mannequin.append(Part(name, mesh, "mannequin", COLORS[color], notes, "Reference only"))

    add_m("IK34_MANNEQUIN_TORSO", ellipsoid((95, 165, 92), (0, 5, 235)), "gray", "Approximate feline torso reference.")
    add_m("IK34_MANNEQUIN_HEAD", ellipsoid((72, 68, 72), (0, -150, 350)), "gray", "Approximate Peach head reference; not a scan.")
    add_m("IK34_MANNEQUIN_MUZZLE", ellipsoid((48, 35, 30), (0, -207, 332)), "white", "White muzzle/nose region reference.")
    add_m("IK34_MANNEQUIN_UNDERBELLY", ellipsoid((55, 120, 55), (0, 22, 205)), "white", "White underbelly reference.")
    leg_positions = [(-62,-88), (62,-88), (-65,112), (65,112)]
    for i,(x,y) in enumerate(leg_positions,1):
        add_m(f"IK34_MANNEQUIN_LEG_{i}", cyl(29, 150, (x,y,120), (0,0,1)), "gray", "Approximate feline leg reference.")
        add_m(f"IK34_MANNEQUIN_PAW_{i}", ellipsoid((38,48,22),(x,y-5,38)), "white" if i < 3 else "gray", "Approximate paw reference.")
    for side,sx in [("L",-1),("R",1)]:
        add_m(f"IK34_MANNEQUIN_EAR_{side}", wedge((38,28,70),(sx*42,-162,425),sx*8,(0,1,0)), "gray", "Ear clearance reference.")
    tail_pts=[]
    for i in range(8):
        t=i/7
        tail_pts.append(np.array([45*math.sin(t*1.7), 165+t*220, 275+t*80]))
    for i in range(len(tail_pts)-1):
        add_m(f"IK34_MANNEQUIN_TAIL_{i+1:02d}", link_between(tail_pts[i],tail_pts[i+1],16), "gray", "Segmented tail reference.")

    add_a("IK34_CHEST_PLATE", wedge((145, 24, 125),(0,-72,250),-12,(1,0,0)), "skin", "red", "Feline chest plate with open throat/belly boundaries.")
    add_a("IK34_CHEST_LIGHT_BEZEL", cyl(28, 10,(0,-88,270),(0,1,0)), "light", "cyan", "Chest-light bezel study; electronics unselected.")
    add_a("IK34_BACK_PLATE_FRONT", wedge((150, 28, 115),(0,15,294),8,(1,0,0)), "skin", "red", "Forward back plate.")
    add_a("IK34_BACK_PLATE_REAR", wedge((145, 28, 105),(0,118,282),-5,(1,0,0)), "skin", "red", "Rear back plate.")
    add_a("IK34_COLLAR_LEFT", box((54,22,34),(-42,-104,331)), "transition", "gold", "Left floating collar scale; throat remains open.")
    add_a("IK34_COLLAR_RIGHT", box((54,22,34),(42,-104,331)), "transition", "gold", "Right floating collar scale; throat remains open.")
    add_a("IK34_HELMET_BROW", wedge((120,18,45),(0,-170,399),-8,(1,0,0)), "helmet", "red", "Open-face brow shell; not fitted to a live animal.")
    add_a("IK34_HELMET_REAR", wedge((125,24,68),(0,-112,392),8,(1,0,0)), "helmet", "red", "Rear helmet shell with ear clearance envelope.")
    for side,sx in [("L",-1),("R",1)]:
        add_a(f"IK34_CHEEK_GUARD_{side}", wedge((28,54,64),(sx*58,-176,349),sx*10,(0,1,0)), "helmet", "gold", "Open cheek guard; whisker path remains clear.")
        add_a(f"IK34_EAR_FRAME_{side}", wedge((48,18,76),(sx*43,-155,425),sx*7,(0,1,0)), "helmet", "gold", "Non-contact ear frame envelope.")
        add_a(f"IK34_SHOULDER_CAP_FRONT_{side}", ellipsoid((43,52,32),(sx*82,-72,287)), "skin", "red", "Front shoulder cap study.")
        add_a(f"IK34_SHOULDER_CAP_REAR_{side}", ellipsoid((42,50,30),(sx*84,38,287)), "skin", "red", "Rear shoulder cap study.")
        add_a(f"IK34_HIP_PLATE_{side}", wedge((54,70,72),(sx*82,112,225),sx*7,(0,1,0)), "skin", "gold", "Floating hip plate study.")
    for i,(x,y) in enumerate(leg_positions,1):
        front = i <= 2
        add_a(f"IK34_LEG_CUFF_UPPER_{i}", cyl(37,48,(x,y,151),(0,0,1)), "limb", "red" if front else "gold", "Floating upper leg cuff; open/soft liner required.")
        add_a(f"IK34_LEG_CUFF_LOWER_{i}", cyl(34,42,(x,y,88),(0,0,1)), "limb", "gold" if front else "red", "Floating lower leg cuff; paw remains free.")
        add_a(f"IK34_PAW_GUARD_{i}", wedge((58,68,18),(x,y-8,54),0), "limb", "red", "Dorsal paw-guard display geometry; no live-animal approval.")
    for i,p in enumerate(tail_pts[:-1],1):
        q=tail_pts[i]
        mid=(p+q)/2
        add_a(f"IK34_TAIL_SCALE_{i:02d}", wedge((42,52,18),mid+(0,0,22),i*3,(0,1,0)), "tail", "red" if i%2 else "gold", "Floating decorative tail scale; display alpha only.")
    add_a("IK34_BREAKAWAY_BACKPLATE", box((105,12,52),(0,64,335)), "harness", "blue", "Breakaway harness interface study; textile system not included.", "TPU/textile reference")
    add_a("IK34_VISIBILITY_TAG", box((42,8,22),(0,150,330)), "visibility", "cyan", "Passive visibility/NFC tag carrier envelope.")
    return armor, mannequin


def make_combined_kitty_scene(base: Path, armor: List[Part], mannequin: List[Part]) -> None:
    scene=trimesh.Scene()
    for p in mannequin+armor:
        scene.add_geometry(paint(p.mesh.copy(),p.color),node_name=p.name,geom_name=p.name)
    scene.export(base/"ASSEMBLY"/"IRON_KITTY_R34_WITH_MANNEQUIN.glb")
    (base/"REFERENCE").mkdir(exist_ok=True)
    ref=trimesh.Scene()
    for p in mannequin:
        ref.add_geometry(paint(p.mesh.copy(),p.color),node_name=p.name,geom_name=p.name)
    ref.export(base/"REFERENCE"/"PEACH_APPROXIMATE_MANNEQUIN_R34.glb")
    (base/"REFERENCE"/"MANNEQUIN_PARTS.json").write_text(json.dumps([part_record(p) for p in mannequin],indent=2))


def zip_directory(src: Path, out: Path) -> None:
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(src.rglob("*")):
            if p.is_file():
                z.write(p,p.relative_to(src))


def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()


def site_files(r33_validation: dict, r34_validation: dict, r33_zip: Path, r34_zip: Path) -> None:
    fresh(SITE)
    for d in ["assets","iron-dad-integration","iron-kitty-geometry","evidence","downloads"]:
        (SITE/d).mkdir(parents=True,exist_ok=True)
    shutil.copy2(R33/"PREVIEWS"/"IRON_DAD_R33_PREVIEW.png",SITE/"assets"/"iron-dad-r33.png")
    shutil.copy2(R34K/"PREVIEWS"/"IRON_KITTY_R34_PREVIEW.png",SITE/"assets"/"iron-kitty-r34.png")
    shutil.copy2(r33_zip,SITE/"downloads"/r33_zip.name)
    shutil.copy2(r34_zip,SITE/"downloads"/r34_zip.name)
    shutil.copy2(R33/"MANIFEST"/"VALIDATION.json",SITE/"evidence"/"r33-validation.json")
    shutil.copy2(R34K/"MANIFEST"/"VALIDATION.json",SITE/"evidence"/"r34-validation.json")

    (SITE/"assets"/"jt-monogram.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160"><rect width="160" height="160" rx="20" fill="#fff"/><path d="M80 15 145 80 80 145 15 80Z" fill="none" stroke="#0b377d" stroke-width="7"/><path d="M80 27 133 80 80 133 27 80Z" fill="none" stroke="#d6ae58" stroke-width="5"/><path d="M45 50h63v13H84v51H68V63H45zm66 0h15v64h-15z" fill="#0b377d"/></svg>')
    css=':root{--bg:#090d13;--panel:#111823;--paper:#f5f0e6;--ink:#121a25;--gold:#d6ae58;--red:#bd3039;--cyan:#51c8ff;--line:#2d3745}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:#f8f4e9;font-family:Inter,Segoe UI,Arial,sans-serif;line-height:1.6}a{color:inherit}.header{position:sticky;top:0;z-index:9;display:flex;align-items:center;gap:22px;padding:14px 3vw;background:#fff;color:var(--ink);border-bottom:1px solid #d9dce1}.brand{display:flex;align-items:center;gap:13px;text-decoration:none;font-weight:900;letter-spacing:.1em}.brand img{width:46px;height:46px}.brand small{display:block;font-size:8px;letter-spacing:.16em;color:#53677d}.nav{margin-left:auto;display:flex;gap:18px;font-size:14px}.nav a{text-decoration:none;font-weight:700}.hero{min-height:78vh;display:grid;grid-template-columns:1.1fr .9fr;gap:3vw;align-items:center;padding:7vw 5vw;background:radial-gradient(circle at 85% 20%,#541a2077,transparent 34%),linear-gradient(135deg,#090d13,#121923)}.eyebrow{color:var(--gold);font-size:12px;letter-spacing:.18em;text-transform:uppercase}.hero h1{font-size:clamp(58px,8vw,130px);line-height:.86;letter-spacing:-.055em;margin:.25em 0}.hero h1 em{font-style:normal;color:var(--gold);-webkit-text-stroke:1px #f2deb1}.hero p{max-width:720px;color:#dbe0e8;font-size:18px}.hero img{width:100%;border:1px solid #55442d;border-radius:22px;box-shadow:0 28px 80px #0008}.actions{display:flex;flex-wrap:wrap;gap:12px;margin-top:28px}.button{display:inline-flex;padding:14px 20px;background:linear-gradient(135deg,#d34149,#ad202c);border:1px solid #ef7379;border-radius:10px;text-decoration:none;font-weight:800}.button.alt{background:#fff;color:#101824;border-color:#fff}.section{padding:72px 5vw}.paper{background:var(--paper);color:var(--ink)}.section h2{font-size:clamp(36px,5vw,72px);line-height:.95;margin:.25em 0 .5em}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}.card{background:var(--panel);border:1px solid var(--line);border-radius:22px;overflow:hidden}.paper .card{background:#fff;border-color:#d8d3c8}.card img{display:block;width:100%;aspect-ratio:16/9;object-fit:cover}.card-body{padding:24px}.card h3{font-size:28px;margin:0 0 10px}.metric-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:30px 0}.metric{padding:18px;border:1px solid #384354;background:#101722;color:#fff;border-radius:14px}.metric b{display:block;font-size:28px;color:var(--gold)}.notice{padding:18px 20px;border-left:4px solid var(--cyan);background:#10233a;color:#eaf4ff}.list{display:grid;gap:11px}.list div{display:flex;justify-content:space-between;gap:14px;border-bottom:1px solid #ddd3c0;padding:12px 0}.footer{padding:50px 5vw;border-top:2px solid var(--gold);color:#cfd6df}.footer b{color:#fff}.status{color:#ffdc8b;font:12px ui-monospace,monospace}.download-row{display:flex;justify-content:space-between;gap:18px;align-items:center;padding:18px 0;border-bottom:1px solid #ddd}.quote{font-size:clamp(28px,4vw,55px);line-height:1.1;color:var(--gold);max-width:1000px}@media(max-width:850px){.nav{display:none}.hero,.grid{grid-template-columns:1fr}.metric-grid{grid-template-columns:1fr 1fr}.hero h1{font-size:58px}}'
    (SITE/"assets"/"site.css").write_text(css)
    (SITE/"assets"/"site.js").write_text("document.querySelectorAll('[data-copy]').forEach(b=>b.addEventListener('click',async()=>{await navigator.clipboard.writeText(new URL(b.dataset.copy,location.href).href);b.textContent='Link copied';}));")
    header='<header class="header"><a class="brand" href="/"><img src="/assets/jt-monogram.svg" alt=""><span>IRON—DAD<small>JUSTIN TAHAI / SYSTEMS ENGINEERING</small></span></a><nav class="nav"><a href="/">Home</a><a href="/iron-dad-integration/">R33 Integration</a><a href="/iron-kitty-geometry/">R34 IRON-KITTY</a><a href="/evidence/">Evidence</a></nav></header>'
    footer='<footer class="footer"><b>IRON-DAD R34 / INTEGRATION BATCH</b><p>Original development geometry. Modeled evidence is not physical validation.</p></footer>'
    index=f'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>IRON-DAD R34 — Integration Batch</title><link rel="icon" href="/assets/jt-monogram.svg"><link rel="stylesheet" href="/assets/site.css"><script defer src="/assets/site.js"></script></head><body>{header}<main><section class="hero"><div><span class="eyebrow">R33 + R34 / TWO ENGINEERING PASSES</span><h1>INTEGRATE<br><em>THE FAMILY.</em></h1><p>This batch advances the adult machine toward a registered full-body architecture and gives Peach an actual printable geometry branch instead of artwork alone.</p><div class="actions"><a class="button" href="/iron-dad-integration/">Open R33 integration ↗</a><a class="button alt" href="/iron-kitty-geometry/">Open IRON-KITTY geometry ↗</a></div></div><img src="/assets/iron-dad-r33.png" alt="R33 full-body integration preview"></section><section class="section paper"><span class="eyebrow">ONE FAMILY / DIFFERENT BODIES</span><h2>Two modeled systems.<br>One evidence standard.</h2><div class="grid"><article class="card"><img src="/assets/iron-dad-r33.png" alt="IRON-DAD integration model"><div class="card-body"><span class="status">MODELED / R33</span><h3>IRON-DAD full-body integration</h3><p>{r33_validation["part_count"]} printable study parts registered in one assembly.</p><a class="button" href="/iron-dad-integration/">Inspect R33 ↗</a></div></article><article class="card"><img src="/assets/iron-kitty-r34.png" alt="IRON-KITTY geometry model"><div class="card-body"><span class="status">MODELED / R34</span><h3>IRON-KITTY geometry branch</h3><p>{r34_validation["part_count"]} original armor-study parts plus an approximate feline mannequin.</p><a class="button" href="/iron-kitty-geometry/">Inspect R34 ↗</a></div></article></div></section><section class="section"><p class="quote">The next useful result is one coordinate system, one assembly, and one honest evidence boundary.</p></section></main>{footer}</body></html>'
    (SITE/"index.html").write_text(index)
    r33_page=f'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>R33 Full-Body Integration — IRON-DAD</title><link rel="stylesheet" href="/assets/site.css"><script defer src="/assets/site.js"></script></head><body>{header}<main><section class="hero"><div><span class="eyebrow">R33 / FULL-BODY INTEGRATION</span><h1>ONE BODY.<br><em>ONE DATUM.</em></h1><p>Frame rails, joint carriers, removable armor envelopes, releases, optical datums and service cassettes are represented together.</p><div class="actions"><a class="button" href="/downloads/{r33_zip.name}">Download R33 model ZIP ↗</a><button class="button alt" data-copy="/iron-dad-integration/">Copy page link</button></div></div><img src="/assets/iron-dad-r33.png" alt="R33 assembly"></section><section class="section paper"><div class="metric-grid"><div class="metric"><b>{r33_validation["part_count"]}</b>parts</div><div class="metric"><b>{r33_validation["watertight_count"]}</b>watertight</div><div class="metric"><b>2</b>GLB assemblies</div><div class="metric"><b>0</b>physical tests</div></div><p class="notice"><b>Boundary:</b> Not load-rated, collision-cleared, fitted, or approved for powered human trials.</p></section></main>{footer}</body></html>'
    (SITE/"iron-dad-integration"/"index.html").write_text(r33_page)
    kitty_page=f'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>R34 IRON-KITTY Geometry — Peach</title><link rel="stylesheet" href="/assets/site.css"><script defer src="/assets/site.js"></script></head><body>{header}<main><section class="hero"><div><span class="eyebrow">R34 / IRON-KITTY GEOMETRY BRANCH</span><h1>PEACH GETS<br><em>REAL GEOMETRY.</em></h1><p>Original feline mannequin and printable armor-study parts: helmet, chest/back plates, shoulder/hip coverage, cuffs, paw guards and tail scales.</p><div class="actions"><a class="button" href="/downloads/{r34_zip.name}">Download R34 model ZIP ↗</a><button class="button alt" data-copy="/iron-kitty-geometry/">Copy page link</button></div></div><img src="/assets/iron-kitty-r34.png" alt="IRON-KITTY geometry"></section><section class="section paper"><div class="metric-grid"><div class="metric"><b>{r34_validation["part_count"]}</b>armor parts</div><div class="metric"><b>{r34_validation["watertight_count"]}</b>watertight</div><div class="metric"><b>1</b>feline reference</div><div class="metric"><b>0</b>live-animal tests</div></div><p class="notice"><b>Boundary:</b> Display alpha only. No part is approved for use on Peach or another live animal.</p></section></main>{footer}</body></html>'
    (SITE/"iron-kitty-geometry"/"index.html").write_text(kitty_page)
    evidence=f'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Evidence — IRON-DAD R34</title><link rel="stylesheet" href="/assets/site.css"></head><body>{header}<main><section class="section paper"><span class="eyebrow">EVIDENCE / RELEASE GATE</span><h2>Modeled clearly.<br>Claimed narrowly.</h2><div class="download-row"><div><b>R33 full-body integration</b></div><a class="button" href="/downloads/{r33_zip.name}">Download</a></div><div class="download-row"><div><b>R34 IRON-KITTY geometry</b></div><a class="button" href="/downloads/{r34_zip.name}">Download</a></div><div class="list"><div><b>Geometry exported</b><span>Yes</span></div><div><b>Registered GLB assemblies</b><span>Included</span></div><div><b>Physical fit</b><span>Not tested</span></div><div><b>Human/animal wear approval</b><span>No</span></div></div></section></main>{footer}</body></html>'
    (SITE/"evidence"/"index.html").write_text(evidence)
    (SITE/"robots.txt").write_text("User-agent: *\nAllow: /\n")
    (SITE/"_headers").write_text("/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n  X-Frame-Options: SAMEORIGIN\n")
    (SITE/"_redirects").write_text("/r33 /iron-dad-integration/ 301\n/r34 /iron-kitty-geometry/ 301\n")
    missing=[]
    for html in SITE.rglob("*.html"):
        for target in re.findall(r'(?:href|src)="([^"]+)"',html.read_text()):
            if target.startswith(("http","#","mailto:")): continue
            clean=target.split("#",1)[0].split("?",1)[0]
            if not clean: continue
            dest=SITE/clean.lstrip("/")
            if clean.endswith("/"): dest=dest/"index.html"
            if not dest.exists(): missing.append({"page":str(html.relative_to(SITE)),"target":target})
    report={"html_pages":len(list(SITE.rglob("*.html"))),"missing_local_refs":missing,"r33":r33_validation,"r34":r34_validation}
    (SITE/"evidence"/"SITE_VALIDATION.json").write_text(json.dumps(report,indent=2))
    if missing: raise RuntimeError(f"Missing site references: {missing}")


def main() -> None:
    fresh(OUT); fresh(R33); fresh(R34K)
    adult=adult_parts()
    r33_val=export_package(R33,adult,"IRON-DAD R33 Full-Body Integration","# IRON-DAD Full-Body Integration R33\n\nRegistered digital integration study. Modeled only; not load-rated or human-wear approved.\n","IRON_DAD_R33","IRON-DAD R33 — REGISTERED FULL-BODY INTEGRATION",{"frame":"#d1a641","joint":"#adb7c6","skin":"#a71920","release":"#4ad4ff","ar":"#4ad4ff","soft_interface":"#1f63b7","harness":"#1f63b7","electronics":"#333b46","ground":"#20252d"})
    kitty,mannequin=kitty_parts()
    r34_val=export_package(R34K,kitty,"IRON-KITTY R34 Geometry Branch","# IRON-KITTY Geometry Branch R34\n\nPrintable display-alpha geometry and approximate feline reference. No live-animal approval.\n","IRON_KITTY_R34","IRON-KITTY R34 — PEACH GEOMETRY BRANCH",{"skin":"#a71920","light":"#4ad4ff","transition":"#d1a641","helmet":"#a71920","limb":"#bd3039","tail":"#d1a641","harness":"#1f63b7","visibility":"#4ad4ff"})
    make_combined_kitty_scene(R34K,kitty,mannequin)
    temp=OUT/"download_zips"; temp.mkdir(exist_ok=True)
    r33_zip=temp/"IRON_DAD_FULL_BODY_INTEGRATION_R33.zip"; r34_zip=temp/"IRON_KITTY_GEOMETRY_R34.zip"
    zip_directory(R33,r33_zip); zip_directory(R34K,r34_zip); site_files(r33_val,r34_val,r33_zip,r34_zip)
    for base in [R33,R34K,SITE]:
        entries=[]
        for p in sorted(base.rglob("*")):
            if p.is_file(): entries.append({"path":str(p.relative_to(base)),"bytes":p.stat().st_size,"sha256":sha256(p)})
        (base/"PACKAGE_MANIFEST.json").write_text(json.dumps(entries,indent=2))
    summary={"r33":r33_val,"r34":r34_val,"website_pages":len(list(SITE.rglob("*.html"))),"remaining_passes_after_batch":1}
    (OUT/"BATCH_SUMMARY.json").write_text(json.dumps(summary,indent=2)); print(json.dumps(summary,indent=2))

if __name__ == "__main__": main()
