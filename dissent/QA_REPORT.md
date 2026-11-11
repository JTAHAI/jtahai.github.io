# DISSENT 1.0.0-RC2 QA Report

## Release focus

RC2 validates a single adaptive release across desktop keyboard/mouse and mobile touch devices. The underlying campaign, authentic vehicle, procedural generator, persistence, boss reversal, extraction, and result systems remain covered by the RC1 campaign suite; RC2 adds dedicated display, fullscreen, orientation, touch, and standalone coverage.

## Automated source checks

- `game.js`: syntax valid under Node.js.
- `generator-core.js`: syntax valid under Node.js.
- `jetta-model-data.js`: syntax valid under Node.js and loads in Chromium.
- `sw.js`: syntax valid; manifest JSON valid with two install icons, fullscreen display override, and landscape-primary orientation.
- HTML DOM audit: zero duplicate IDs and zero JavaScript-referenced missing IDs.
- Touch flight deck contains separate hold and action controls with no duplicate IDs.
- Optimized Jetta payload remains checksum-verified against the Grand Prix manifest.

## Authentic vehicle integration

- Runtime source: `GRAND PRIX MK IV LOD2`
- Source vehicle triangles: 10,129
- Total DISSENT hero-ship triangles after original wing kit: 10,417
- Runtime byte count: 729,288
- Runtime checksum: `f07efefdb685ed1f5252cbb8d3fcbef182ca439d4b196f4686e738225dd96abf`
- Procedural fallback remains available and was not selected in passing browser tests.

## Generator regression

- Generator version: `G7-ABSURDITY-1`
- Total generated layouts: **25,000**
- Quick runs: 5,000
- Grand runs: 15,000
- Endless runs: 5,000
- Failures: **0**
- Average rooms: 35.71
- Minimum rooms: 16
- Maximum rooms: 45

Each case was checked for structural validity, full traversal connectivity, deterministic reproduction, required strata, critical-path endpoints, objectives, boss placement, and extraction placement.

## Desktop campaign/WebGL2 suite

Environment:

- Chromium with WebGL2 through SwiftShader
- 1440 × 900 viewport

Verified:

- WebGL2 context available.
- Authentic Grand Prix Jetta loaded.
- Hero-ship triangle count exceeded 10,000.
- Quick, Grand, and Endless formats generated correctly.
- Expose, Protect, and Archive choices executed.
- Camera cycle and seven-floor automap rendered.
- Checkpoint save, availability, disturbance, and restoration passed.
- Final machine unlocked.
- False-victory reversal executed.
- Actual final defeat and win outcome executed.
- Result-card PNG data produced.
- Console errors: **0**.
- Unhandled page errors: **0**.
- Result: **PASS**.

## Adaptive desktop-resolution suite

Environment:

- 1920 × 1080 viewport
- Device scale factor 1.5
- Keyboard/mouse device profile

Verified:

- Touch UI remained hidden.
- Adaptive Auto resolved to Desktop High.
- Auto internal framebuffer: **2880 × 1620**.
- Desktop Ultra internal framebuffer: **3600 × 2025**.
- Desktop Ultra exceeded CSS resolution while remaining under its guarded pixel budget.
- Authentic Jetta and campaign state remained valid.

## Landscape-phone suite

Environment:

- 844 × 390 landscape viewport
- Device scale factor 2.5
- Android/mobile user agent
- Touch and coarse-pointer capabilities enabled

Verified:

- Device resolved to `TOUCH FLIGHT DECK` and Mobile quality under Adaptive Auto.
- Internal framebuffer: **1392 × 643**.
- Mobile architecture streaming reduced the nearby static scene to 3,182 triangles.
- Both virtual sticks and all action clusters displayed.
- Simultaneous movement, aim, fire, and boost state moved the ship.
- Touch camera action cycled to hood camera.
- Touch map action opened the map; explicit close control returned to play.
- Fullscreen entered successfully after a trusted click on **Fullscreen / Landscape**.
- Console errors: **0**.
- Page errors: **0**.
- Result: **PASS**.

## Portrait-phone suite

Environment:

- 390 × 844 portrait viewport
- Device scale factor 2.5
- iPhone-style mobile user agent

Verified:

- Touch mode detected.
- Portrait state detected.
- Gameplay displayed the **Rotate the Jetta** landscape gate.
- Result: **PASS**.

## Standalone suite

The self-contained HTML was loaded directly as one document in separate desktop and mobile contexts.

Verified:

- No external runtime script or model was required.
- Authentic Jetta loaded in both contexts.
- Desktop resolved to keyboard/mouse mode.
- Mobile resolved to touch mode and displayed the touch flight deck during play.
- Console errors: **0**.
- Page errors: **0**.
- Result: **PASS**.

## Fullscreen and browser limits

Chromium fullscreen entry passed from user activation. Android-class browsers should provide the intended fullscreen landscape experience where their implementation permits it. General-page fullscreen remains browser-dependent on iPhone/iPad Safari; the manifest requests fullscreen landscape presentation for installed Home Screen use, and ordinary Safari retains a full-visual-viewport fallback with rotation guidance.

## PWA registration limitation

The environment blocked browser navigation to a local HTTP origin, so service-worker registration itself could not be exercised here. The service-worker source, manifest, icons, registration guard, and Cloudflare headers were validated statically. Registration and offline reload remain explicit production-domain checks.

## Remaining physical-device checks

Automated testing does not replace sustained physical-device play. Before final 1.0 promotion, test:

- Multi-touch stick + fire + boost combinations on a real Android phone.
- iPhone/iPad Safari and installed Home Screen presentation.
- Display cutouts, rounded corners, and browser navigation bars.
- Thermal behavior during a 20–30 minute Grand Descent.
- Desktop Ultra on the intended GPU and monitor.
- Audio, haptics, wake lock, checkpoints, and downloads under ordinary device permissions.
- Production-domain caching, certificate, fullscreen, and orientation behavior.
