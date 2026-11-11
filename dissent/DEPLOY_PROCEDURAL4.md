# Deploy DISSENT RC2 to procedural4.JTforME.com

## Release artifact

Use:

`DISSENT_Carpooling_to_Hell_v1.0.0_RC2_PROCEDURAL4_CLOUDFLARE.zip`

The ZIP has `index.html` at its root and includes every runtime dependency locally.

## Cloudflare Pages direct upload

1. Open Cloudflare Dashboard.
2. Go to **Workers & Pages**.
3. Create or open the Pages project intended for DISSENT.
4. Choose **Direct Upload**.
5. Upload the release ZIP, or upload its extracted contents.
6. Confirm `index.html` is at the deployment root.
7. Open **Custom domains**.
8. Add `procedural4.jtforme.com`.
9. Confirm DNS points to this Pages deployment rather than a prior project.
10. Wait for the Pages certificate to become active.

## Desktop production smoke test

- Menu reports `KEYBOARD + MOUSE`.
- Ship status says `GRAND PRIX MK IV LOD2`.
- Adaptive Auto renders at the expected native/high-DPI size.
- Desktop Ultra increases internal resolution on a standard-DPI display.
- Mouse capture, keyboard movement, weapons, camera, map, pause, and gamepad remain functional.

## Mobile production smoke test

- Open on an Android phone and an iPhone/iPad.
- Rotate to landscape.
- Tap **Fullscreen / Landscape** and then start a run.
- Confirm both sticks and every touch button are visible and separated from the HUD.
- Confirm simultaneous movement/aim/fire works.
- Confirm map and Ledger close through their explicit buttons.
- Confirm the portrait rotation gate appears after rotating upright.
- On iOS Safari, also test Add to Home Screen and launch from the installed icon for fullscreen presentation.
- Confirm the display status reports `TOUCH FLIGHT DECK` and the mobile profile under Adaptive Auto.

## Shared smoke test

- Audio begins only after interaction.
- Checkpoint appears after a room transition or ten seconds of play.
- Reloading offers **Resume the Buried Record**.
- Export progress downloads JSON.
- Result-card download produces PNG.
- Browser console contains no errors.
- Network panel shows no third-party runtime requests.
- `sw.js` registers successfully on HTTPS and the second load can recover the core shell from cache.

## Cache and permissions

The release includes `_headers`. HTML and core scripts revalidate; immutable vehicle assets receive longer cache lifetimes. The permissions policy allows same-origin fullscreen and screen wake lock while denying camera, microphone, geolocation, payment, and USB.

Do not reuse an old deployment without replacing `index.html`, `game.js`, `jetta-model-data.js`, and `manifest.webmanifest` together.

## Rollback

Cloudflare Pages retains deployment history. Promote the immediately prior successful deployment if RC2 fails. The full source/QA archive contains validation reports and checksums for identifying the deployed build.

## Status

This package prepares the deployment. It does not itself attach the domain or publish the project.
