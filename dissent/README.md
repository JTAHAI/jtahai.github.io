# DISSENT: Carpooling to Hell

**Version 1.0.0-RC1 — Return of the Record**  
Target deployment: **https://procedural4.JTforME.com**

DISSENT is an original, local-first WebGL2 six-degrees-of-freedom arcade roguelite. You pilot Justin's winged black 1999½ Mk IV Jetta through a procedurally generated judicial underworld, recover the buried record, decide what to expose, protect, or archive, disable the machinery beneath the bench, and bring the surviving record back into daylight.

> THE COURTS HAVE BASEMENTS. HELL HAS SEVEN. THE JETTA HAS WINGS.

## RC1 headline

This release replaces the old approximate car body with the **actual optimized Grand Prix Mk IV geometry** and then bolts the original DISSENT flight conversion around it: fighter wings, cannons, roll fins, thrusters, and an entirely unreasonable mandate to fly through hell.

The game remains dependency-free at runtime. The optimized vehicle payload is bundled locally and also embedded into the standalone release.

## The complete game

- True 6DOF flight: pitch, yaw, roll, strafe, rise, descend, reverse, airbrake, and afterburner.
- Fixed 120 Hz simulation with Arcade Assist, Classic Drift, and Precision Tunnel handling.
- Chase, hood, and cockpit cameras.
- Keyboard/mouse and dual-stick gamepad input.
- Deterministic connected facilities with loops, alternate paths, vertical shafts, secrets, landmarks, and multiple objective routes.
- Three formats:
  - **One More Filing:** a short three-circle run.
  - **The Grand Descent:** the full seven-circle campaign.
  - **Endless Appeal:** escalating sectors with carry-forward resources and Truth Ledger history.
- Seven circles:
  1. Public Facade
  2. Continuance Catacombs
  3. Sealed Registry
  4. Paywall Pits
  5. E-Filing Furnace
  6. Infernal Bench
  7. Null Tribunal
- Seven institutional enemy machines and seven procedural hazard systems.
- The Absurdity Director, which changes rules during play and generates solvable procedural disasters.
- Truth Ledger choices that alter score, survivability, secrets, record integrity, and boss armor.
- Six Garage of Appeals modules, with two selected per run.
- Five visually and mechanically distinct final machines.
- A deliberate false-victory reversal in full-length modes: relief may be granted and then procedurally ungranted.
- A collapsing extraction run with a final-page pursuit.

## New in 1.0 RC1

### Authentic Grand Prix Jetta

- Uses the optimized `lod2.bin` vehicle mesh generated for the Procedural Grand Prix.
- 10,129 source-model triangles; 10,417 total hero-ship triangles after the DISSENT wing conversion.
- Checksum-verified source payload.
- Classic Black and Iron Patriot finishes.
- Procedural fallback remains available if the payload is missing or corrupt.

### Local-first continuity

- Automatic local checkpoints during active runs.
- Resume button appears when a valid checkpoint exists.
- Local progress export/import as human-portable JSON.
- Settings, best score, recent runs, and checkpoints stay on the device.
- No account, analytics, cookies, cloud save, database, or runtime API.

### Presentation and onboarding

- Four-stage first-run training brief.
- Depth-reveal, false-victory, final-order, last-page, and resume cinematics.
- Distinct boss forms: mechanical rejection stamp, Grand Seal, Gatekeeper, Null Tribunal, and Erasure Engine.
- Procedural engine note, reactive pulse score, combat intensity, and boss escalation generated through Web Audio.
- Downloadable 1200×630 result card and copyable run record/code.
- High-contrast mode added alongside reduced motion, reduced flash, HUD scaling, inversion, sensitivity, graphics, and volume settings.

## Controls

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
- No external JavaScript, audio, font, model, analytics, advertising, or runtime network dependencies.
- `jetta-model-data.js` embeds the optimized vehicle payload for reliable deployment and standalone use.
- Raw model manifest and LOD2 payload are retained in `assets/vehicles/jetta-mkiv/` for provenance and validation.
- Procedural output is deterministic for a given seed, sector, mode, and generator version.

## Validation completed

- JavaScript syntax checks passed.
- DOM ID audit passed with zero missing and zero duplicate IDs.
- **25,000 generated facilities** passed structural, connectivity, objective, critical-path, and determinism checks with zero failures.
- Real Chromium/WebGL2 smoke test passed with zero console errors and zero page errors.
- Authentic model loading, model triangle count, all three modes, all evidence dispositions, automap, camera switching, local checkpoint save/restore, false victory, final defeat, run completion, and result-card rendering were exercised.

See `QA_REPORT.md`, `QA_GENERATOR_REPORT.json`, and `QA_BROWSER_REPORT.json`.

## Deployment

Upload the Cloudflare ZIP through Pages Direct Upload so `index.html` is at the deployment root, then attach `procedural4.jtforme.com`. See `DEPLOY_PROCEDURAL4.md`.

The package is prepared but is **not deployed by this build process**.

## Content note

DISSENT is fictional institutional satire. Hostile entities are machines, procedures, forms, and invented abstractions. It does not depict or encourage violence against identifiable people.
