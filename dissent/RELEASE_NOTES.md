# DISSENT 1.0.0-RC2 — Adaptive Flight Deck

RC2 converts DISSENT into a single device-adaptive release for `procedural4.JTforME.com`.

## Complete mobile controls

- Two analog virtual sticks for movement and aim.
- Dedicated rise, descend, roll-left, and roll-right controls.
- Hold-to-fire cannons.
- Missile, boost, brake, scan, fitted-module, ledger, map, camera, pause, and fullscreen controls.
- Multi-touch pointer handling with independent stick and button state.
- Safe-area positioning for notches and rounded display edges.
- Light haptic response where supported.
- Screen wake lock during active mobile play where supported.

## Fullscreen and orientation

- Fullscreen is requested from user interaction on phone launch and from a dedicated menu/game button.
- Landscape orientation lock is requested where the browser exposes it.
- The PWA manifest requests fullscreen landscape-primary presentation.
- A same-origin service worker caches the core game shell for installed/offline replay after the first successful load.
- Portrait gameplay displays a clear rotation gate.
- iOS gracefully falls back to the full visual viewport and Home Screen installation guidance when general-page fullscreen is unavailable.

## Desktop resolution path

- Added Adaptive Auto, Battery Saver, Balanced, Desktop High, and Desktop Ultra profiles.
- Desktop Ultra supersamples standard-DPI displays and retains high-DPI/native 4K output within a guarded pixel budget.
- Mobile Auto caps framebuffer cost independently from desktop quality.
- Rendering distance, streamed architecture radius, particles, effects, fog, and resolution now follow the resolved device profile.
- The menu reports input mode, resolved quality, internal framebuffer size, and fullscreen state.

## HUD adaptations

- Mobile readouts move to a compact top strip.
- Touch controls occupy the lower flight-deck area without covering health, energy, objective, or boss status.
- Radar and desktop-only instruction surfaces are removed on small touch layouts.
- Map and Ledger remain full overlays with explicit close controls.

## QA

- Existing desktop campaign smoke suite: PASS.
- Adaptive desktop/phone/portrait suite: PASS.
- Browser fullscreen user-activation test: PASS.
- 25,000 deterministic facilities: 0 failures.
- Console errors: 0.
- Page errors: 0.

The authentic Grand Prix Mk IV integration, procedural campaign, Absurdity Director, Truth Ledger, final machines, false victory, extraction, checkpoints, portable progress, synthesized audio, and local result system remain intact.
