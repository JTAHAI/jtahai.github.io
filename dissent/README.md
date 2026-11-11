# DISSENT: Carpooling to Hell

**Version 1.0.0-RC2 — Adaptive Flight Deck**  
Target deployment: **https://procedural4.JTforME.com**

DISSENT is an original, local-first WebGL2 six-degrees-of-freedom arcade roguelite. You pilot Justin's winged black 1999½ Mk IV Jetta through a procedurally generated judicial underworld, recover the buried record, decide what to expose, protect, or archive, disable the machinery beneath the bench, and bring the surviving record back into daylight.

> THE COURTS HAVE BASEMENTS. HELL HAS SEVEN. THE JETTA HAS WINGS.

## RC2 headline

RC2 turns the release candidate into **one adaptive game build** rather than separate desktop and phone games:

- Desktop devices use keyboard/mouse, pointer lock, optional gamepad support, and high-resolution rendering.
- Phones and coarse-pointer devices receive a complete two-stick touch flight deck.
- Mobile play requests fullscreen and landscape orientation where the browser permits it.
- Installed web-app mode uses the manifest's fullscreen landscape presentation and a same-origin offline shell.
- Portrait play presents a rotation gate instead of squeezing the flight controls into an unusable layout.
- The renderer chooses a safe mobile resolution automatically while allowing desktop High and Ultra supersampling.

The optimized Grand Prix Mk IV model remains the actual hero vehicle. The complete release has no runtime third-party requests.

## Adaptive display modes

| Setting | Intended use |
|---|---|
| Adaptive Auto | Detects touch/desktop capability and selects a safe profile |
| Battery Saver | Reduced geometry, effects, and internal resolution |
| Balanced | Midrange laptops, tablets, and integrated GPUs |
| Desktop High | Native high-DPI and 4K-capable desktop rendering |
| Desktop Ultra | Supersampled desktop output within a guarded pixel budget |

The renderer respects device pixel ratio but also applies per-profile pixel budgets so high-DPI phones do not accidentally attempt desktop-scale framebuffers. Desktop Ultra can render above CSS resolution on standard-DPI monitors and retains native 4K output where hardware and browser limits permit it.

## Mobile flight deck

Landscape touch controls include:

- Left virtual stick: forward/reverse thrust and strafe.
- Right virtual stick: yaw and pitch.
- Dedicated rise and descend controls.
- Dedicated roll-left and roll-right controls for true 6DOF movement.
- Hold-to-fire wing cannons.
- Homing missile, afterburner, airbrake, scan, equipped module, and Truth Ledger buttons.
- Map, camera, pause, and fullscreen controls.
- Safe-area positioning for display cutouts and browser chrome.
- Screen wake lock where supported.
- Light haptic confirmation where supported.

On iPhone and iPad, browser fullscreen availability depends on Safari and install state. The game still uses the full visual viewport in ordinary Safari and instructs the player to add it to the Home Screen for the closest true fullscreen experience.

## Desktop controls

| Control | Action |
|---|---|
| W / S | Forward / reverse thrust |
| A / D | Strafe left / right |
| Space / Ctrl | Rise / descend |
| Mouse | Pitch / yaw |
| Q / E | Roll |
| Shift | Afterburner |
| B | Airbrake |
| Left mouse / J | Cannons |
| F / right mouse | Homing missile |
| Z | Scan / Procedural Shoehorn |
| C | Motion to Compel EMP, when equipped |
| X | Leave to Amend, when equipped |
| V | Cycle camera |
| Tab | Full seven-floor automap |
| L | Truth Ledger |
| P / Escape | Pause |
| 1 / 2 / 3 | Evidence disposition |

## The complete game

- True 6DOF flight with a fixed 120 Hz simulation.
- Chase, hood, and cockpit cameras.
- Deterministic connected facilities with loops, alternate paths, vertical shafts, secrets, landmarks, and multiple objective routes.
- One More Filing, The Grand Descent, and Endless Appeal formats.
- Seven circles of increasingly infernal judicial machinery.
- Seven institutional enemy machines and seven procedural hazard systems.
- The Absurdity Director, which changes rules during play and generates solvable procedural disasters.
- Truth Ledger choices that alter score, survivability, secrets, record integrity, and boss armor.
- Six Garage of Appeals modules, with two selected per run.
- Five visually and mechanically distinct final machines.
- A false-victory reversal in full-length modes.
- A collapsing extraction run with a final-page pursuit.
- Automatic local checkpoints, portable JSON progress, local history, and result cards.
- No account, analytics, cookies, cloud save, database, or runtime API.
- Same-origin service worker caches the game shell for installed/offline replay after the first successful production load.

## Run objective

1. Recover every required exhibit.
2. Destroy every active suppression seal.
3. Defeat the final machine and survive any procedural reversal.
4. Carry the last page through the collapsing undercourt.
5. Reach the Public Gates before the record is erased.

## Technical notes

- WebGL2 required.
- No build step required.
- Runtime is plain HTML and JavaScript.
- `jetta-model-data.js` embeds the optimized vehicle payload for reliable deployment and standalone use.
- Raw model manifest and LOD2 payload remain in `assets/vehicles/jetta-mkiv/` for provenance and validation.
- Procedural output is deterministic for a given seed, sector, mode, and generator version.
- Cloudflare headers explicitly permit same-origin fullscreen and screen-wake-lock use while denying unrelated sensitive capabilities.

## Validation completed

- JavaScript syntax checks passed.
- DOM ID audit passed with zero missing and zero duplicate IDs.
- **25,000 generated facilities** passed structural, connectivity, objective, critical-path, and determinism checks with zero failures.
- Desktop Chromium/WebGL2 campaign smoke suite passed.
- 1920×1080 desktop at 1.5 device scale rendered Auto at 2880×1620 and Ultra at 3600×2025.
- 844×390 landscape phone emulation selected the mobile profile, rendered at 1392×643, displayed all touch controls, accepted touch-flight state, cycled camera, and opened/closed the map.
- 390×844 portrait phone emulation displayed the landscape rotation gate.
- Browser fullscreen was successfully entered from the mobile launch control in Chromium.
- Console errors: 0. Unhandled page errors: 0.

See `QA_REPORT.md`, `QA_GENERATOR_REPORT.json`, `QA_BROWSER_REPORT.json`, and `QA_ADAPTIVE_REPORT.json`.

## Deployment

Upload the Cloudflare ZIP through Pages Direct Upload so `index.html` is at the deployment root, then attach `procedural4.jtforme.com`. See `DEPLOY_PROCEDURAL4.md`.

The package is prepared but is **not deployed by this build process**.

## Content note

DISSENT is fictional institutional satire. Hostile entities are machines, procedures, forms, and invented abstractions. It does not depict or encourage violence against identifiable people.
