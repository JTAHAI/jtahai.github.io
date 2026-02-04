---
layout: page
title: Static Launch Checklist
permalink: /checklists/static-launch-checklist/
---

# Static launch checklist

This is the checklist I use when I want a static-first site to stay fast, accessible, and easy to maintain.

## Content & IA
- One clear **purpose** per page (what it is + who it’s for).
- Navigation matches audience tasks (not internal org structure).
- Every page has a “next step” link (don’t dead-end people).

## Accessibility (baseline)
- Headings in order (H1 → H2 → H3), no jumps.
- Contrast passes on all text, especially over images.
- Keyboard-only navigation works (Tab/Shift+Tab/Enter/Escape).
- Focus states are visible (don’t remove outlines without replacing them).

## Performance (no tricks)
- Images sized correctly, compressed, and lazy-loaded where appropriate.
- Minimize third-party scripts; defer anything non-critical.
- CSS is tokenized; avoid huge unused frameworks.

## Security & privacy
- Prefer **no forms** unless needed; if needed, use a narrow endpoint/service.
- Avoid tracking you don’t need. If you must measure, use privacy-friendly analytics.
- Set sensible security headers at the edge (CSP where feasible).

## SEO & sharing
- `sitemap.xml` and `robots.txt` exist and are correct.
- OpenGraph/Twitter tags are present (nice share cards).
- Canonical URLs are set when content overlaps across sites.

## Operations / handoff
- Deployment is documented in the repo (one page, step-by-step).
- A new maintainer can change content without learning a framework.
- Backups exist for any non-static content (if applicable).

---

If you want this as a one-page “go/no-go” sheet, I can generate a printable PDF version later.
