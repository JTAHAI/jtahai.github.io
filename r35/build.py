from __future__ import annotations

import hashlib
import html
import json
import os
import re
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "out" / "site"
ASSETS = SITE / "assets"
DOWNLOADS = SITE / "downloads"
SITE.mkdir(parents=True, exist_ok=True)
ASSETS.mkdir(parents=True, exist_ok=True)
DOWNLOADS.mkdir(parents=True, exist_ok=True)

RELEASE = "R35"
SITE_NAME = "IRON-DAD — Engineering a Family"
BASE_URL = os.environ.get("SITE_URL", "").rstrip("/")


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def url(path: str) -> str:
    return f"{BASE_URL}{path}" if BASE_URL else path


PROJECTS = [
    {
        "slug": "iron-dad",
        "number": "01",
        "title": "IRON-DAD",
        "scale": "Human scale",
        "headline": "Build the impossible around a human.",
        "description": "Articulated armor, assisted structure, distributed controls, and integrated AR—with independent access and evidence boundaries kept visible.",
        "accent": "red",
        "status": "Integrated architecture / physical validation incomplete",
    },
    {
        "slug": "iron-kitty",
        "number": "02",
        "title": "IRON-KITTY",
        "scale": "Feline sidekick",
        "headline": "Peach gets her own engineering branch.",
        "description": "A feline-first red-and-gold armor concept that preserves face, ears, whiskers, belly, paws, gait, and tail balance.",
        "accent": "gold",
        "status": "Printable geometry branch / not a live-animal validated wearable",
    },
    {
        "slug": "iron-kids",
        "number": "03",
        "title": "IRON-KIDS",
        "scale": "Future builders",
        "headline": "Grow the suit—not the joint.",
        "description": "Comfort-first PLA armor outside a textile carrier, removable EVA, modular growth interfaces, and optional low-voltage electronics.",
        "accent": "blue",
        "status": "K2 pilot architecture / child physical fit incomplete",
    },
]

DOWNLOAD_LABELS = {
    "IRON_KIDS_K2_INTEGRATED_ELECTRONICS_R32.zip": (
        "IRON-KIDS K2 Integrated Electronics R32",
        "Printable interfaces, NodeMCU/OLED mounts, blanking lids, protected power, wiring carriers, source, firmware, and verification.",
        "IRON-KIDS",
    ),
    "IRON_KITTY_GEOMETRY_R34.zip": (
        "IRON-KITTY Geometry R34",
        "Original feline reference geometry, armor concept parts, source, manifests, and evidence boundary documentation.",
        "IRON-KITTY",
    ),
}

PAGES = [
    {"path": "/", "title": SITE_NAME, "group": "Family", "description": "IRON-DAD, IRON-KITTY, and IRON-KIDS presented as one evidence-led personal engineering program."},
    {"path": "/family/", "title": "Engineering a Family", "group": "Family", "description": "The shared principles connecting IRON-DAD, IRON-KITTY, and IRON-KIDS."},
    {"path": "/iron-dad/", "title": "IRON-DAD", "group": "Project", "description": "Human-scale articulated armor, assisted structure, controls, and AR."},
    {"path": "/iron-kitty/", "title": "IRON-KITTY / Peach", "group": "Project", "description": "Peach’s feline-first armor geometry branch and sidekick project."},
    {"path": "/iron-kids/", "title": "IRON-KIDS", "group": "Project", "description": "Growth-friendly comfort-first PLA armor for future builders."},
    {"path": "/iron-kids/electronics/", "title": "IRON-KIDS Electronics", "group": "Engineering", "description": "Removable NodeMCU and OLED modules with no restraint authority."},
    {"path": "/models/", "title": "Model Atlas", "group": "Engineering", "description": "Current geometry branches, evidence status, and downloadable packages."},
    {"path": "/build/", "title": "Build Program", "group": "Build", "description": "Evidence-gated build sequence across the family."},
    {"path": "/downloads/", "title": "Downloads", "group": "Build", "description": "Verified current model and engineering artifacts with hashes."},
    {"path": "/evidence/", "title": "Evidence Ledger", "group": "Evidence", "description": "What is proposed, modeled, digitally checked, bench-tested, and physically validated."},
]

NAV = [
    ("/family/", "Family"),
    ("/iron-dad/", "IRON-DAD"),
    ("/iron-kitty/", "IRON-KITTY"),
    ("/iron-kids/", "IRON-KIDS"),
    ("/models/", "Models"),
    ("/downloads/", "Downloads"),
]


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def canonical(path: str) -> str:
    return url(path)


def nav(current: str) -> str:
    links = []
    for href, label in NAV:
        active = ' aria-current="page"' if current == href else ""
        links.append(f'<a href="{href}"{active}>{label}</a>')
    return f'''<header class="site-header">
<div class="site-shell nav-shell">
<a class="brand" href="/" aria-label="IRON-DAD home"><span class="brand-mark" aria-hidden="true"><i>J</i><b>T</b></span><span><strong>IRON—DAD</strong><small>JUSTIN TAHAI / ENGINEERING A FAMILY / {RELEASE}</small></span></a>
<nav class="desktop-nav" aria-label="Primary navigation">{''.join(links)}</nav>
<div class="nav-actions"><button class="icon-button" data-search-open aria-label="Search the project">⌕</button><a class="primary-mini" href="/build/">BUILD MAP ↗</a></div>
</div></header>'''


def footer() -> str:
    project_links = ''.join(f'<a href="/{p["slug"]}/">{p["title"]}</a>' for p in PROJECTS)
    return f'''<footer class="site-footer"><div class="site-shell footer-grid">
<div><span class="kicker">INDEPENDENT ENGINEERING / PERSONAL PROJECT</span><h2>Make the impossible<br><em>inspectable.</em></h2><p>One human-scale system, one feline sidekick, and one builder program—connected by comfort, agency, evidence, and possibility.</p></div>
<div><h3>Projects</h3>{project_links}</div>
<div><h3>Current release</h3><a href="/models/">Model atlas</a><a href="/downloads/">Verified downloads</a><a href="/evidence/">Evidence ledger</a></div>
</div><div class="site-shell footer-bottom"><span>IRON-DAD / {RELEASE}</span><span>STATIC · LOCAL-FIRST · NO ANALYTICS</span><button data-top>Back to top ↑</button></div></footer>'''


def search_dialog() -> str:
    return '''<dialog class="search-dialog" data-search-dialog aria-labelledby="search-title"><form method="dialog" class="search-head"><div><span class="kicker">LOCAL PROJECT SEARCH</span><h2 id="search-title">Find a project, model, or build record.</h2></div><button aria-label="Close search">×</button></form><label class="sr-only" for="project-search">Search</label><input id="project-search" data-search-input type="search" autocomplete="off" placeholder="Helmet, Peach, electronics, evidence…"><div class="search-results" data-search-results></div><p class="search-note">No network search. No tracking.</p></dialog>'''


def card(project: dict) -> str:
    return f'''<article class="project-card accent-{project['accent']}">
<span class="project-number">{project['number']} / {project['scale']}</span><h2>{project['title']}</h2><h3>{project['headline']}</h3><p>{project['description']}</p><span class="status-chip">{project['status']}</span><a href="/{project['slug']}/">Open project <span aria-hidden="true">↗</span></a></article>'''


def layout(path: str, title: str, description: str, body: str, *, og_image: str = "/assets/social-card.svg") -> str:
    page_title = title if title == SITE_NAME else f"{title} — IRON-DAD"
    canonical_href = canonical(path)
    json_ld = {
        "@context": "https://schema.org",
        "@type": "CreativeWork" if path != "/" else "WebSite",
        "name": title,
        "creator": {"@type": "Person", "name": "Justin Tahai"},
        "description": description,
        "isPartOf": {"@type": "WebSite", "name": SITE_NAME},
    }
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#090b0f"><title>{esc(page_title)}</title><meta name="description" content="{esc(description)}"><link rel="canonical" href="{esc(canonical_href)}"><meta property="og:type" content="website"><meta property="og:site_name" content="{esc(SITE_NAME)}"><meta property="og:title" content="{esc(page_title)}"><meta property="og:description" content="{esc(description)}"><meta property="og:image" content="{esc(url(og_image))}"><meta name="twitter:card" content="summary_large_image"><link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><link rel="manifest" href="/manifest.webmanifest"><link rel="stylesheet" href="/assets/site.css"><script defer src="/assets/site.js"></script><script type="application/ld+json">{json.dumps(json_ld, separators=(',', ':'))}</script></head><body data-route="{path}"><a class="skip-link" href="#main">Skip to content</a>{nav(path)}<div class="family-ribbon"><div class="site-shell"><span>ENGINEERING A FAMILY</span><a href="/iron-dad/">HUMAN</a><i>+</i><a href="/iron-kitty/">SIDEKICK</a><i>+</i><a href="/iron-kids/">BUILDERS</a><b>{RELEASE}</b></div></div><main id="main">{body}</main>{footer()}{search_dialog()}</body></html>'''


home_body = f'''<section class="hero"><div class="site-shell hero-grid"><div class="hero-copy"><span class="kicker">JUSTIN TAHAI / PERSONAL SYSTEMS ENGINEERING</span><h1>ENGINEERING<br><em>A FAMILY.</em></h1><p>IRON-DAD explores the human-scale machine. IRON-KITTY gives Peach a feline-first sidekick branch. IRON-KIDS turns the same imagination into a comfort-first builder program.</p><div class="button-row"><a class="button" href="/family/">Explore the family ↗</a><a class="button secondary" href="/models/">Inspect the models ↗</a></div><div class="truth-row"><span><b>PROPOSED</b> Architecture</span><span><b>MODELED</b> Geometry</span><span><b>CHECKED</b> Digital evidence</span><span><b>OPEN</b> Physical validation</span></div></div><div class="family-orbit" aria-label="Three connected project branches"><div class="orbit-core"><span>JT</span></div><a class="orbit-node dad" href="/iron-dad/"><b>IRON-DAD</b><small>Human</small></a><a class="orbit-node kitty" href="/iron-kitty/"><b>IRON-KITTY</b><small>Peach</small></a><a class="orbit-node kids" href="/iron-kids/"><b>IRON-KIDS</b><small>Builders</small></a></div></div></section><section class="section paper"><div class="site-shell"><span class="kicker dark">THREE BRANCHES / ONE DESIGN DISCIPLINE</span><h2 class="section-title">Different bodies.<br>Shared standards.</h2><div class="project-grid">{''.join(card(p) for p in PROJECTS)}</div></div></section><section class="section dark-section"><div class="site-shell split"><div><span class="kicker">CURRENT ENGINEERING DOWNLOADS</span><h2 class="section-title">Real files.<br><em>Clear boundaries.</em></h2><p class="large-copy">The current deployment includes the R32 IRON-KIDS electronics interfaces and the R34 IRON-KITTY geometry package. Every download lists its evidence state and SHA-256 digest.</p></div><div class="stacked-links"><a href="/downloads/"><strong>Open the verified download desk</strong><span>Hashes, sizes, scope, and source boundaries ↗</span></a><a href="/evidence/"><strong>Read the evidence ledger</strong><span>What has and has not been physically proven ↗</span></a></div></div></section>'''

family_body = f'''<section class="page-hero"><div class="site-shell"><span class="kicker">THE WHOLE PROGRAM</span><h1>THREE BRANCHES.<br><em>ONE DISCIPLINE.</em></h1><p>Comfort, agency, evidence, and possibility connect the human, feline, and child-scale work without pretending they have the same engineering maturity.</p></div></section><section class="section paper"><div class="site-shell principles"><article><span>01</span><h2>Comfort</h2><p>Textile carriers, removable EVA, ventilation, pressure-free folds, and body-specific clearances.</p></article><article><span>02</span><h2>Agency</h2><p>Reachable releases, passive escape, and electronics with no authority over restraint or fit.</p></article><article><span>03</span><h2>Evidence</h2><p>Concept art, modeled geometry, digital checks, bench work, and physical proof remain distinct.</p></article><article><span>04</span><h2>Possibility</h2><p>Ambitious presentation should make the engineering easier to inspect—not easier to overstate.</p></article></div></section><section class="section"><div class="site-shell project-grid">{''.join(card(p) for p in PROJECTS)}</div></section>'''


def project_body(project: dict, features: list[tuple[str, str]], next_href: str, next_label: str) -> str:
    feature_html = ''.join(f'<article><h3>{esc(a)}</h3><p>{esc(b)}</p></article>' for a,b in features)
    return f'''<section class="page-hero project-hero accent-{project['accent']}"><div class="site-shell"><span class="kicker">{project['number']} / {project['scale'].upper()}</span><h1>{project['title']}</h1><h2>{project['headline']}</h2><p>{project['description']}</p><span class="status-chip hero-status">{project['status']}</span><div class="button-row"><a class="button" href="{next_href}">{next_label} ↗</a><a class="button secondary" href="/evidence/">Evidence status ↗</a></div></div></section><section class="section paper"><div class="site-shell feature-grid">{feature_html}</div></section>'''

iron_dad_body = project_body(PROJECTS[0], [
    ("Articulated exterior", "Overlapping sections and local cartridges instead of one rigid two-piece shell."),
    ("Assisted load path", "A separate frame and counterbalance program intended to move mass toward the ground."),
    ("Distributed control", "Local deterministic nodes, a supervisory computer, independent power removal, and manual release."),
    ("Integrated optics", "Head-referenced optics, removable processing and power, and immediate manual vision access."),
], "/models/", "Inspect integration status")

iron_kitty_body = project_body(PROJECTS[1], [
    ("Feline reference", "A Peach-proportioned development datum is explicitly not presented as a scan."),
    ("Open face", "No shell crosses the nose, whiskers, mouth, or throat."),
    ("Passive breakaway", "Any future live-wear concept remains lightweight, passive, supervised, and immediately removable."),
    ("Printable display branch", "The current geometry package is suitable for display and development rather than a validated animal wearable."),
], "/downloads/#iron-kitty", "Download R34 geometry")

iron_kids_body = project_body(PROJECTS[2], [
    ("Soft carrier first", "The textile carrier and removable EVA are the real fit system; PLA remains outside."),
    ("Grow between joints", "Extension interfaces add coverage without spanning or relocating a child’s joint center."),
    ("Optional electronics", "NodeMCU and OLED modules provide status and effects only; blanking lids preserve electronics-free use."),
    ("Physical pilot required", "A full child wearable remains incomplete until fit, movement, heat, and release are physically tested."),
], "/iron-kids/electronics/", "Open R32 electronics")

electronics_body = '''<section class="page-hero accent-blue"><div class="site-shell"><span class="kicker">IRON-KIDS / R32 / INTEGRATED ELECTRONICS</span><h1>FUN INSIDE.<br><em>FREEDOM OUTSIDE.</em></h1><p>Chest and forearm interfaces, NodeMCU and OLED mounts, blanking lids, protected USB power, service channels, and fit gauges—without any authority over restraint, closure, or release.</p><div class="button-row"><a class="button" href="/downloads/#iron-kids">Download R32 package ↗</a><a class="button secondary" href="#configuration">Configure a module set ↓</a></div></div></section><section class="section paper"><div class="site-shell architecture"><article><span>CHEST</span><h2>Local status node</h2><p>NodeMCU, OLED, temperature/humidity sensing, diffused lighting, and local controls.</p></article><article><span>ARMS</span><h2>Optional pods</h2><p>Independent forearm displays with blank lids available when no electronics are installed.</p></article><article><span>POWER</span><h2>Protected USB</h2><p>Commercial enclosed power bank in an open, ventilated, strap-retained pocket.</p></article><article class="critical"><span>AUTHORITY</span><h2>None</h2><p>No command exists for fit, latch, closure, restraint, or release.</p></article></div></section><section class="section" id="configuration"><div class="site-shell config-grid"><div><span class="kicker">LOCAL CONFIGURATOR</span><h2 class="section-title">Choose only<br>what the build needs.</h2><button class="config-button" data-module="Chest NodeMCU + OLED" aria-pressed="true">Chest NodeMCU + OLED</button><button class="config-button" data-module="Left forearm OLED" aria-pressed="false">Left forearm OLED</button><button class="config-button" data-module="Right forearm OLED" aria-pressed="false">Right forearm OLED</button><button class="config-button" data-module="Protected USB power" aria-pressed="true">Protected USB power</button></div><pre class="config-readout" data-config-output></pre></div></section>'''

models_body = '''<section class="page-hero"><div class="site-shell"><span class="kicker">MODEL ATLAS / CURRENT TRUTH</span><h1>GEOMETRY WITH<br><em>A STATUS LABEL.</em></h1><p>Each branch is presented according to the strongest evidence actually available—not according to how cinematic the artwork looks.</p></div></section><section class="section paper"><div class="site-shell model-table-wrap"><table><thead><tr><th>Branch</th><th>Current geometry</th><th>Strongest evidence</th><th>Open work</th></tr></thead><tbody><tr><td>IRON-DAD</td><td>Full-body integration architecture and source-derived exterior studies</td><td>Local mechanisms and system interfaces modeled</td><td>Registered physical suit, load testing, safe independent entry</td></tr><tr><td>IRON-KITTY</td><td>Original feline reference and display armor geometry</td><td>Printable R34 files with explicit boundaries</td><td>Peach scan/mannequin validation; live-wear branch remains unproven</td></tr><tr><td>IRON-KIDS</td><td>K2 growth, carrier, electronics, and fit-interface development parts</td><td>Printable interfaces and digital export checks</td><td>Complete registered child assembly and physical pilot</td></tr></tbody></table></div></section><section class="section"><div class="site-shell stacked-links"><a href="/downloads/"><strong>Download current model packages</strong><span>Verified hashes and scope notes ↗</span></a><a href="/evidence/"><strong>Open the evidence ledger</strong><span>Proposed · modeled · checked · tested ↗</span></a></div></section>'''

build_body = '''<section class="page-hero"><div class="site-shell"><span class="kicker">EVIDENCE-GATED BUILD PROGRAM</span><h1>BUILD ONE<br><em>TRUTH AT A TIME.</em></h1><p>Measure, establish the soft carrier, prove coupons, complete partial assemblies, validate release and motion, and add electronics only after the body-facing system works without them.</p></div></section><section class="section paper"><div class="site-shell build-steps"><article><b>01</b><h2>Measure</h2><p>Record body datums, joint centers, padding, clothing, and growth envelope.</p></article><article><b>02</b><h2>Carrier</h2><p>Fit the textile/EVA system with ventilation and immediate release.</p></article><article><b>03</b><h2>Coupons</h2><p>Print gauges and test actual fasteners, boards, displays, and cable bends.</p></article><article><b>04</b><h2>Partial builds</h2><p>Prove one arm, one leg, helmet, and torso interfaces before a full suit.</p></article><article><b>05</b><h2>Physical pilot</h2><p>Record mass, movement, heat, don/doff time, pressure, and release performance.</p></article><article><b>06</b><h2>Electronics</h2><p>Add removable effects only after the costume remains usable without them.</p></article></div></section>'''

# Build download metadata only from files physically present.
download_records = []
for path in sorted(DOWNLOADS.glob("*.zip")):
    title, desc, branch = DOWNLOAD_LABELS.get(path.name, (path.stem.replace("_", " "), "Current packaged artifact.", "Project"))
    download_records.append({
        "filename": path.name,
        "title": title,
        "description": desc,
        "branch": branch,
        "bytes": path.stat().st_size,
        "sha256": digest(path),
    })

rows = []
for r in download_records:
    anchor = "iron-kids" if "IRON_KIDS" in r["filename"] else "iron-kitty" if "IRON_KITTY" in r["filename"] else quote(r["filename"])
    rows.append(f'''<article class="download-card" id="{anchor}"><span class="kicker dark">{esc(r['branch'])}</span><h2>{esc(r['title'])}</h2><p>{esc(r['description'])}</p><dl><div><dt>Size</dt><dd>{r['bytes']/1048576:.2f} MiB</dd></div><div><dt>SHA-256</dt><dd><code>{r['sha256']}</code></dd></div></dl><a class="button" href="/downloads/{quote(r['filename'])}" download>Download ZIP ↗</a></article>''')

downloads_body = f'''<section class="page-hero"><div class="site-shell"><span class="kicker">VERIFIED CURRENT ARTIFACTS</span><h1>DOWNLOADS WITH<br><em>RECEIPTS.</em></h1><p>Only files physically present in this release appear here. Sizes and SHA-256 digests are generated from the packaged bytes.</p></div></section><section class="section paper"><div class="site-shell download-grid">{''.join(rows) if rows else '<p>No model packages were bundled.</p>'}</div></section>'''

evidence_body = '''<section class="page-hero"><div class="site-shell"><span class="kicker">EVIDENCE LEDGER</span><h1>AMBITION STAYS.<br><em>BOUNDARIES STAY VISIBLE.</em></h1><p>A release badge describes the strongest supporting evidence, not the intended destination of the project.</p></div></section><section class="section paper"><div class="site-shell evidence-grid"><article class="evidence proposed"><span>PROPOSED</span><h2>System architecture</h2><p>Requirements, mechanisms, control boundaries, and build plans.</p></article><article class="evidence modeled"><span>MODELED</span><h2>Digital geometry</h2><p>Printable parts, reference assemblies, interfaces, and documented source.</p></article><article class="evidence checked"><span>DIGITALLY CHECKED</span><h2>Scoped verification</h2><p>Export integrity, topology, selected geometry, and local software behavior.</p></article><article class="evidence tested"><span>PHYSICALLY TESTED</span><h2>Still limited</h2><p>No complete human, child, or animal wearable has been commissioned by this release.</p></article></div></section>'''

page_specs = {
    "/": (SITE_NAME, PAGES[0]["description"], home_body),
    "/family/": ("Engineering a Family", PAGES[1]["description"], family_body),
    "/iron-dad/": ("IRON-DAD", PAGES[2]["description"], iron_dad_body),
    "/iron-kitty/": ("IRON-KITTY / Peach", PAGES[3]["description"], iron_kitty_body),
    "/iron-kids/": ("IRON-KIDS", PAGES[4]["description"], iron_kids_body),
    "/iron-kids/electronics/": ("IRON-KIDS Electronics", PAGES[5]["description"], electronics_body),
    "/models/": ("Model Atlas", PAGES[6]["description"], models_body),
    "/build/": ("Build Program", PAGES[7]["description"], build_body),
    "/downloads/": ("Downloads", PAGES[8]["description"], downloads_body),
    "/evidence/": ("Evidence Ledger", PAGES[9]["description"], evidence_body),
}

for path, (title, description, body) in page_specs.items():
    target = SITE / ("index.html" if path == "/" else path.strip("/") + "/index.html")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(layout(path, title, description, body))

# Search index generated from the same manifest.
search_index = []
for p in PAGES:
    search_index.append({"title": p["title"], "href": p["path"], "group": p["group"], "description": p["description"]})
for r in download_records:
    search_index.append({"title": r["title"], "href": f"/downloads/#{'iron-kids' if 'IRON_KIDS' in r['filename'] else 'iron-kitty'}", "group": "Download", "description": r["description"]})
(ASSETS / "search.json").write_text(json.dumps(search_index, indent=2))

# One current stylesheet.
(ASSETS / "site.css").write_text(r'''
:root{--bg:#090b0f;--surface:#111722;--surface-2:#171f2c;--paper:#f3eee4;--paper-2:#fffaf0;--ink:#111722;--muted:#aeb8c6;--red:#b83331;--red-2:#e04d43;--gold:#d4af4a;--gold-2:#f3dfb0;--blue:#0b3d91;--cyan:#72d9ff;--line:rgba(212,175,74,.28);--line-light:#dacba9;--radius:22px;--max:1500px;--shadow:0 24px 70px rgba(0,0,0,.18)}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:#f8f4ea;font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;line-height:1.65}a{color:inherit}.site-shell{width:min(calc(100% - 2.25rem),var(--max));margin:auto}.skip-link{position:absolute;left:-9999px;top:1rem;z-index:100}.skip-link:focus{left:1rem;background:white;color:black;padding:.75rem 1rem}.site-header{position:sticky;top:0;z-index:40;background:rgba(9,11,15,.95);backdrop-filter:blur(18px);border-bottom:1px solid var(--line)}.nav-shell{min-height:78px;display:flex;align-items:center;justify-content:space-between;gap:1rem}.brand{display:flex;align-items:center;gap:.8rem;text-decoration:none}.brand-mark{width:48px;height:48px;background:white;color:var(--blue);border:3px solid var(--gold);box-shadow:0 0 0 2px var(--blue);border-radius:10px;display:grid;grid-template-columns:1fr 1fr;place-items:center;font-weight:1000}.brand-mark i{font-style:normal;justify-self:end}.brand-mark b{justify-self:start}.brand strong{display:block;letter-spacing:.1em}.brand small{display:block;color:var(--gold-2);font-size:.62rem;letter-spacing:.14em}.desktop-nav{display:flex;gap:1.15rem}.desktop-nav a{text-decoration:none;font-size:.9rem;font-weight:750;color:#dce4ed}.desktop-nav a:hover,.desktop-nav a[aria-current=page]{color:var(--gold-2)}.nav-actions{display:flex;align-items:center;gap:.65rem}.icon-button,.primary-mini{border:1px solid var(--line);border-radius:11px;min-height:42px;padding:.65rem .85rem;background:transparent;color:white;text-decoration:none;font-weight:800;cursor:pointer}.primary-mini{background:linear-gradient(135deg,var(--red-2),var(--red));border-color:transparent}.family-ribbon{border-bottom:1px solid var(--line);background:#0e1219}.family-ribbon>div{min-height:38px;display:flex;align-items:center;gap:.75rem;font-size:.7rem;letter-spacing:.13em;font-weight:800;color:#bdc7d3}.family-ribbon a{text-decoration:none;color:var(--gold-2)}.family-ribbon b{margin-left:auto;color:var(--cyan)}.hero{min-height:76vh;display:grid;align-items:center}.hero-grid{display:grid;grid-template-columns:1.05fr .95fr;gap:clamp(2rem,6vw,7rem);align-items:center;padding:clamp(4rem,8vw,8rem) 0}.kicker{color:var(--gold-2);font-size:.76rem;font-weight:850;letter-spacing:.16em;text-transform:uppercase}.kicker.dark{color:#845e16}.hero h1,.page-hero h1{font-size:clamp(3.8rem,8.2vw,8.8rem);line-height:.86;letter-spacing:-.07em;margin:.5rem 0 1.25rem}.hero h1 em,.page-hero h1 em,.section-title em{font-style:normal;color:var(--gold)}.hero-copy>p,.page-hero p,.large-copy{font-size:clamp(1.05rem,1.6vw,1.3rem);color:#d3dce7;max-width:64ch}.button-row{display:flex;flex-wrap:wrap;gap:.8rem;margin-top:1.4rem}.button{display:inline-flex;align-items:center;justify-content:center;min-height:49px;padding:.8rem 1.15rem;border-radius:13px;background:linear-gradient(135deg,var(--red-2),var(--red));color:#fff;text-decoration:none;font-weight:850;box-shadow:0 14px 32px rgba(184,51,49,.24);border:0}.button.secondary{background:transparent;border:1px solid var(--line);box-shadow:none;color:var(--gold-2)}.truth-row{display:grid;grid-template-columns:repeat(4,1fr);gap:.55rem;margin-top:2rem}.truth-row span{font-size:.72rem;color:#b9c3d0;border-top:1px solid var(--line);padding-top:.65rem}.truth-row b{display:block;color:#fff;font-size:.65rem;letter-spacing:.11em}.family-orbit{aspect-ratio:1;max-width:640px;margin:auto;position:relative;border:1px solid var(--line);border-radius:50%;background:radial-gradient(circle,#162031 0 19%,transparent 20%),repeating-radial-gradient(circle,transparent 0 22%,rgba(212,175,74,.10) 22.2% 22.4%,transparent 22.6% 38%);box-shadow:0 0 90px rgba(212,175,74,.12)}.orbit-core{position:absolute;inset:36%;border:1px solid var(--line);border-radius:50%;display:grid;place-items:center;background:#0b3d91;box-shadow:0 0 40px rgba(114,217,255,.34)}.orbit-core span{font-size:2rem;font-weight:1000;color:var(--gold-2)}.orbit-node{position:absolute;width:31%;aspect-ratio:1;border-radius:50%;display:grid;place-content:center;text-align:center;text-decoration:none;border:1px solid var(--line);background:linear-gradient(145deg,var(--surface-2),var(--surface));box-shadow:var(--shadow)}.orbit-node b{font-size:clamp(.8rem,1.4vw,1.25rem)}.orbit-node small{color:var(--muted)}.orbit-node.dad{left:1%;top:34%}.orbit-node.kitty{right:7%;top:4%}.orbit-node.kids{right:4%;bottom:3%}.section{padding:clamp(4rem,7vw,7rem) 0}.paper{background:var(--paper);color:var(--ink)}.section-title{font-size:clamp(2.7rem,5.7vw,5.8rem);line-height:.92;letter-spacing:-.055em;margin:.45rem 0 1rem}.project-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem}.project-card{background:var(--paper-2);border:1px solid var(--line-light);border-radius:var(--radius);padding:1.35rem;color:var(--ink);display:flex;flex-direction:column;min-height:355px;position:relative;overflow:hidden}.project-card:after{content:"";position:absolute;width:180px;height:180px;border-radius:50%;right:-80px;bottom:-100px;background:radial-gradient(circle,rgba(212,175,74,.25),transparent 65%)}.project-number{font-size:.72rem;letter-spacing:.13em;text-transform:uppercase;color:#765719}.project-card h2{font-size:clamp(2rem,3.4vw,3.6rem);line-height:.95;margin:.75rem 0 .45rem}.project-card h3{font-size:1.18rem;margin:0 0 .6rem}.project-card p{color:#465360}.project-card>a{margin-top:auto;color:#8f2f27;font-weight:850;text-decoration:none}.status-chip{display:inline-flex;align-self:flex-start;border:1px solid #cdbf9e;border-radius:99px;padding:.35rem .65rem;font-size:.75rem;color:#4c5661;background:#fff;margin:.6rem 0}.dark-section{background:linear-gradient(145deg,#101722,#090b0f)}.split{display:grid;grid-template-columns:1fr 1fr;gap:2rem;align-items:start}.stacked-links{display:grid;gap:.85rem}.stacked-links a{display:flex;justify-content:space-between;gap:1rem;padding:1.15rem;border:1px solid var(--line);border-radius:16px;text-decoration:none;background:var(--surface)}.stacked-links span{color:var(--muted);font-size:.9rem}.page-hero{padding:clamp(5rem,9vw,9rem) 0 4rem;background:radial-gradient(circle at 80% 10%,rgba(212,175,74,.12),transparent 34%)}.page-hero>div{display:block}.page-hero h1{font-size:clamp(3.5rem,7.5vw,8rem)}.page-hero h2{font-size:clamp(1.6rem,3vw,3.2rem);margin:.4rem 0}.hero-status{background:#111722;color:#e8eef5;border-color:var(--line)}.principles{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem}.principles article,.feature-grid article,.architecture article,.build-steps article,.evidence{background:#fffaf0;border:1px solid var(--line-light);border-radius:18px;padding:1.2rem}.principles span{color:#8f2f27;font-weight:900}.principles h2,.feature-grid h3,.architecture h2{margin:.35rem 0}.principles p,.feature-grid p,.architecture p,.build-steps p{color:#4a5662}.feature-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem}.architecture{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem}.architecture article span{font-size:.7rem;color:#805d17;letter-spacing:.13em}.architecture .critical{background:#321718;color:#fff;border-color:#8e3d3d}.architecture .critical p{color:#f0caca}.config-grid{display:grid;grid-template-columns:1fr 1fr;gap:1rem}.config-button{width:100%;text-align:left;margin:.45rem 0;padding:1rem;background:#101e34;color:#fff;border:1px solid #2b5683;border-radius:13px;cursor:pointer;font:inherit;font-weight:700}.config-button[aria-pressed=true]{border-color:var(--gold);box-shadow:0 0 0 2px rgba(212,175,74,.17)}.config-readout{background:#02060c;color:#8fe4ff;border:1px solid #28577f;border-radius:16px;padding:1rem;white-space:pre-wrap;min-height:260px}.model-table-wrap{overflow-x:auto}table{width:100%;border-collapse:collapse;background:#fffaf0}th{background:#111722;color:#fff;text-align:left}th,td{padding:1rem;border-bottom:1px solid #d9ccb0;vertical-align:top}.build-steps{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem}.build-steps b{font-size:2rem;color:#8f2f27}.download-grid{display:grid;grid-template-columns:1fr 1fr;gap:1rem}.download-card{background:#fffaf0;border:1px solid var(--line-light);border-radius:20px;padding:1.3rem}.download-card p{color:#4a5662}.download-card dl{display:grid;gap:.65rem}.download-card dl div{display:grid;grid-template-columns:75px 1fr;gap:.75rem}.download-card dt{font-weight:800}.download-card dd{margin:0;overflow-wrap:anywhere}.download-card code{font-size:.78rem}.evidence-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem}.evidence span{font-size:.7rem;letter-spacing:.13em;color:#7c5b16}.evidence.tested{background:#321718;color:white;border-color:#8e3d3d}.evidence.tested p{color:#f1caca}.site-footer{border-top:1px solid var(--line);padding:4rem 0 1rem;background:#07090d}.footer-grid{display:grid;grid-template-columns:2fr 1fr 1fr;gap:2rem}.footer-grid h2{font-size:clamp(2.2rem,4vw,4.2rem);line-height:.95;margin:.5rem 0}.footer-grid h2 em{font-style:normal;color:var(--gold)}.footer-grid p{color:#b8c2ce}.footer-grid a{display:block;color:#f0deb3;margin:.35rem 0}.footer-bottom{display:flex;justify-content:space-between;gap:1rem;border-top:1px solid var(--line);padding-top:1rem;color:#aeb8c6;font-size:.78rem}.footer-bottom button{background:none;border:0;color:#f0deb3;cursor:pointer}.search-dialog{width:min(800px,calc(100% - 2rem));background:#111722;color:white;border:1px solid var(--line);border-radius:20px;padding:0;box-shadow:0 30px 100px rgba(0,0,0,.45)}.search-dialog::backdrop{background:rgba(0,0,0,.7)}.search-head{display:flex;justify-content:space-between;gap:1rem;padding:1.2rem;border-bottom:1px solid var(--line)}.search-head h2{margin:.25rem 0}.search-head button{font-size:2rem;background:none;border:0;color:white}.search-dialog input{width:calc(100% - 2.4rem);margin:1.2rem;padding:1rem;border-radius:12px;border:1px solid #365b83;background:#07101d;color:white;font:inherit}.search-results{display:grid;gap:.5rem;padding:0 1.2rem 1.2rem}.search-results a{display:grid;grid-template-columns:100px 1fr;gap:1rem;padding:.8rem;border:1px solid #2d4866;border-radius:12px;text-decoration:none}.search-results small{color:#f0deb3}.search-results span{color:#c6d0dc}.search-note{padding:1rem 1.2rem;border-top:1px solid var(--line);color:#9faab7}.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}a:focus-visible,button:focus-visible,input:focus-visible{outline:3px solid var(--cyan);outline-offset:3px}@media(max-width:1050px){.desktop-nav{display:none}.hero-grid,.split,.config-grid{grid-template-columns:1fr}.family-orbit{width:min(100%,580px)}.project-grid,.feature-grid,.architecture,.principles,.evidence-grid{grid-template-columns:1fr 1fr}.truth-row{grid-template-columns:1fr 1fr}}@media(max-width:680px){.site-shell{width:min(calc(100% - 1.2rem),var(--max))}.brand small{display:none}.primary-mini{display:none}.hero-grid{padding-top:3rem}.hero h1,.page-hero h1{font-size:clamp(3rem,17vw,5rem)}.project-grid,.feature-grid,.architecture,.principles,.evidence-grid,.build-steps,.download-grid{grid-template-columns:1fr}.truth-row{grid-template-columns:1fr}.family-ribbon a,.family-ribbon i{display:none}.footer-grid{grid-template-columns:1fr}.footer-bottom{display:grid}.search-results a{grid-template-columns:1fr}.orbit-node{width:34%}}@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}@media print{.site-header,.family-ribbon,.site-footer,.search-dialog,.button-row{display:none!important}body{background:white;color:black}.paper,.dark-section{background:white}.hero,.page-hero,.section{padding:1rem 0}.project-card,.principles article,.feature-grid article,.architecture article,.evidence,.download-card{break-inside:avoid;border-color:#999}.hero-copy>p,.page-hero p,.large-copy{color:#222}}
''')

# One current script.
(ASSETS / "site.js").write_text(r'''
const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
$('[data-top]')?.addEventListener('click',()=>window.scrollTo({top:0,behavior:'smooth'}));
const dialog=$('[data-search-dialog]'),open=$('[data-search-open]'),input=$('[data-search-input]'),results=$('[data-search-results]');
let index=[];fetch('/assets/search.json').then(r=>r.json()).then(x=>index=x).catch(()=>{});
function renderSearch(){const q=(input?.value||'').trim().toLowerCase();const rows=(q?index.filter(x=>(x.title+' '+x.description+' '+x.group).toLowerCase().includes(q)):index.slice(0,8)).slice(0,12);results.innerHTML=rows.map(x=>`<a href="${x.href}"><small>${x.group}</small><span><b>${x.title}</b><br>${x.description}</span></a>`).join('')||'<p>No local matches.</p>'}
open?.addEventListener('click',()=>{dialog.showModal();renderSearch();setTimeout(()=>input.focus(),0)});input?.addEventListener('input',renderSearch);document.addEventListener('keydown',e=>{if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='k'){e.preventDefault();dialog.showModal();renderSearch();setTimeout(()=>input.focus(),0)}});
const buttons=$$('[data-module]'),out=$('[data-config-output]');function updateConfig(){if(!out)return;const active=buttons.filter(b=>b.getAttribute('aria-pressed')==='true').map(b=>b.dataset.module);out.textContent=['IRON-KIDS K2 / LOCAL CONFIGURATION','',...active.map(x=>'✓ '+x.toUpperCase()),'',active.some(x=>x.includes('USB'))?'POWER: PROTECTED USB':'POWER: MODULE ABSENT',active.some(x=>x.includes('Chest'))?'CHEST: LOCAL DISPLAY':'CHEST: BLANK LID',active.some(x=>x.includes('forearm'))?'ARMS: OPTIONAL PODS':'ARMS: NO PODS','PHYSICAL AUTHORITY: NONE'].join('\n')}
buttons.forEach(b=>b.addEventListener('click',()=>{b.setAttribute('aria-pressed',b.getAttribute('aria-pressed')!=='true');updateConfig()}));updateConfig();
''')

# Small self-contained marks.
(ASSETS / "favicon.svg").write_text('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#fff"/><path d="M10 11h44v42H10z" fill="none" stroke="#d4af4a" stroke-width="4"/><path d="M20 20h20v6h-7v21h-7V26h-6zm22 0h6v27h-6z" fill="#0b3d91"/></svg>''')
(ASSETS / "social-card.svg").write_text('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630"><rect width="1200" height="630" fill="#090b0f"/><circle cx="950" cy="315" r="220" fill="none" stroke="#d4af4a" stroke-width="2" opacity=".5"/><circle cx="950" cy="315" r="130" fill="#0b3d91"/><text x="950" y="345" text-anchor="middle" fill="#f3dfb0" font-family="Arial" font-weight="900" font-size="80">JT</text><text x="80" y="170" fill="#f3dfb0" font-family="Arial" font-size="24" letter-spacing="7">JUSTIN TAHAI / PERSONAL SYSTEMS ENGINEERING</text><text x="80" y="310" fill="#fff" font-family="Arial" font-weight="900" font-size="88">ENGINEERING</text><text x="80" y="408" fill="#d4af4a" font-family="Arial" font-weight="900" font-size="88">A FAMILY.</text><text x="80" y="500" fill="#c8d2df" font-family="Arial" font-size="28">IRON-DAD · IRON-KITTY · IRON-KIDS</text></svg>''')

manifest = {"name": SITE_NAME, "short_name": "IRON-DAD", "start_url": "/", "display": "standalone", "background_color": "#090b0f", "theme_color": "#090b0f", "icons": [{"src": "/assets/favicon.svg", "sizes": "any", "type": "image/svg+xml"}]}
(SITE / "manifest.webmanifest").write_text(json.dumps(manifest, indent=2))
(SITE / "robots.txt").write_text("User-agent: *\nAllow: /\nSitemap: /sitemap.xml\n")
(SITE / "_headers").write_text("/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n  Permissions-Policy: camera=(), microphone=(), geolocation=()\n  Cross-Origin-Opener-Policy: same-origin\n/assets/*\n  Cache-Control: public, max-age=31536000, immutable\n")
(SITE / "_redirects").write_text("/kids /iron-kids/ 301\n/kitty /iron-kitty/ 301\n/models /models/ 301\n/r35 /family/ 301\n")

sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>{esc(canonical(p[0]))}</loc></url>' for p in page_specs.items()) + '</urlset>'
(SITE / "sitemap.xml").write_text(sitemap)

not_found = layout("/404.html", "Page not found", "The requested IRON-DAD project page could not be found.", '<section class="page-hero"><div class="site-shell"><span class="kicker">404 / OFF THE MAP</span><h1>THIS PATH<br><em>ISN’T REGISTERED.</em></h1><p>Return to the family map or search the project locally.</p><div class="button-row"><a class="button" href="/">Return home ↗</a><a class="button secondary" href="/family/">Open family map ↗</a></div></div></section>')
(SITE / "404.html").write_text(not_found)

# Static checks.
missing = []
refs = 0
for page in SITE.rglob("*.html"):
    text = page.read_text()
    for raw in re.findall(r'(?:href|src)=["\']([^"\']+)', text):
        refs += 1
        if raw.startswith(("http:", "https:", "mailto:", "tel:", "#", "data:")):
            continue
        target = raw.split("#",1)[0].split("?",1)[0]
        if not target:
            continue
        fp = (SITE / target.lstrip("/")) if target.startswith("/") else (page.parent / target)
        if target.endswith("/"):
            fp = fp / "index.html"
        if not fp.exists():
            missing.append({"page": str(page.relative_to(SITE)), "target": raw})

verification = {
    "release": RELEASE,
    "generated_from_manifest": True,
    "html_pages": len(list(SITE.rglob("*.html"))),
    "css_files": len(list(SITE.rglob("*.css"))),
    "javascript_files": len(list(SITE.rglob("*.js"))),
    "local_references_checked": refs,
    "missing_references": missing,
    "download_count": len(download_records),
    "downloads": download_records,
    "root_index_exists": (SITE / "index.html").exists(),
    "remaining_passes": 0,
}
(SITE / "R35_VERIFICATION.json").write_text(json.dumps(verification, indent=2))
(SITE / "R35_PACKAGE_MANIFEST.json").write_text(json.dumps({"files": [{"path": str(p.relative_to(SITE)), "bytes": p.stat().st_size, "sha256": digest(p)} for p in sorted(SITE.rglob("*")) if p.is_file()]}, indent=2))
if missing:
    raise SystemExit(f"Missing local references: {missing}")
print(json.dumps({"pages": verification["html_pages"], "downloads": verification["download_count"], "references": refs, "missing": len(missing)}, indent=2))
