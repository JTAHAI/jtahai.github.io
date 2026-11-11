# Deploy DISSENT to procedural4.JTforME.com

## Release artifact

Use:

`DISSENT_Carpooling_to_Hell_v1.0.0_RC1_PROCEDURAL4_CLOUDFLARE.zip`

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

## Production smoke test

- Menu loads with no missing-resource messages.
- Ship status says `GRAND PRIX MK IV LOD2`.
- First launch opens the training brief.
- Starting enters a WebGL2 run.
- Chase camera shows the authentic Jetta body and wing kit.
- Audio begins only after interaction.
- Checkpoint appears after a room transition or ten seconds of play.
- Reloading the page offers **Resume the Buried Record**.
- Export progress downloads JSON.
- Result-card download produces PNG.
- Browser console contains no errors.
- Network panel shows no third-party runtime requests.

## Cache note

The release includes `_headers`. HTML and core scripts revalidate; immutable vehicle assets receive longer cache lifetimes. Do not reuse an old deployment without replacing `jetta-model-data.js` and `game.js` together.

## Rollback

Cloudflare Pages retains deployment history. Promote the immediately prior successful deployment if RC1 fails. The full source/QA archive also includes the validation reports and checksums needed to identify the deployed build.

## Status

This package prepares the deployment. It does not itself attach the domain or publish the project.
