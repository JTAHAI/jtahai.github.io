# Justin Tahai — flagship technical portfolio

This repository powers [jtahai.github.io](https://jtahai.github.io/): Justin Tahai’s public technical portfolio, engineering publication, and local explanatory-lab collection.

The portfolio carries work evidence and technical writing. It is separate from:

- [MAINELY CODE LLC](https://mainelycode.com/), the company and product context.
- [TAHAI Web Services](https://tahai.net/), Justin Tahai’s personal DBA for services and related technical work.

## Local development

Requires Node.js 24 or a current Node LTS release.

```sh
npm ci
npm run dev
```

Run the release check and static build with:

```sh
npm run build
```

The site is a static Astro build. Public pages live in `src/pages/`; project records and notes are in `src/data/content.ts`; global styling is in `src/styles/global.css`.

## Deployment and rollback

Pushing a reviewed change to `main` triggers `.github/workflows/deploy.yml`, which builds `dist/` and deploys the artifact to GitHub Pages. Repository Pages must use **GitHub Actions** as its build source.

Before promotion, run `npm ci` and `npm run build` from a clean checkout and verify the canonical root plus changed nested routes. Record the promoted source SHA and Pages deployment URL. To roll back, revert the release commit on `main`, run the same checks, and let the workflow deploy the prior static artifact. Do not place credentials, audit evidence, source archives, or private SDK/application code in this repository or its published output.
