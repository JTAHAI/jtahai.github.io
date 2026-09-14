export type Project = {
  slug: string; title: string; eyebrow: string; business: string; status: string;
  summary: string; challenge: string; approach: string; evidence: string; live?: string;
  tags: string[]; accent: string;
};

export const projects: Project[] = [
  {
    slug: 'tahai-web-services', title: 'TAHAI Web Services', eyebrow: 'Service platform',
    business: 'TAHAI Web Services · Justin Tahai’s personal DBA', status: 'Current', accent: 'cobalt',
    summary: 'A clear public service surface for web, IT, and operational systems work.',
    challenge: 'Present a broad technical practice without turning the site into a list of disconnected capabilities.',
    approach: 'Use a small service architecture, direct entry points, durable static content, and plain-language explanations of what changes for a client.',
    evidence: 'Public site and its information architecture are the evidence surface; service claims remain scoped to published content.',
    live: 'https://tahai.net/', tags: ['information architecture', 'static delivery', 'accessibility']
  },
  {
    slug: 'tahai-portal', title: 'TAHAI Portal', eyebrow: 'Ecosystem navigation',
    business: 'TAHAI Web Services', status: 'Current', accent: 'violet',
    summary: 'A navigable map of related tools, knowledge, and product contexts.',
    challenge: 'Keep a multi-route portal coherent while supporting media, reduced motion, keyboard navigation, and small screens.',
    approach: 'Treat motion as optional atmosphere, retain a usable static state, and make hierarchy work before any cinematic layer appears.',
    evidence: 'The public portal exposes the route and content structure. The portfolio describes the design constraints, not internal operations.',
    live: 'https://tahaiportal.com/ecosystem/', tags: ['responsive systems', 'motion fallback', 'content modeling']
  },
  {
    slug: 'mainely-code', title: 'MAINELY CODE LLC', eyebrow: 'Company platform',
    business: 'MAINELY CODE LLC', status: 'Current', accent: 'amber',
    summary: 'The company/product context for a family of software and technical initiatives.',
    challenge: 'Make the company identity legible while preserving distinct product roles and honest availability signals.',
    approach: 'Use product status as structured content, keep navigation specific, and avoid treating early concepts as released software.',
    evidence: 'Public company pages establish published positioning; future products and private implementation details are intentionally excluded.',
    live: 'https://mainelycode.com/', tags: ['product language', 'system design', 'content contracts']
  },
  {
    slug: 'northstar', title: 'Northstar', eyebrow: 'Technical direction',
    business: 'MAINELY CODE LLC', status: 'Current public surface', accent: 'mint',
    summary: 'A focused public experience for a distinct Mainely Code initiative.',
    challenge: 'Translate a specialized product direction into a compact, understandable public route without collapsing it into the parent company.',
    approach: 'Separate product identity, documented public paths, and technical context; preserve its own runtime and delivery constraints.',
    evidence: 'The public Northstar site is the source for current public wording and routes.',
    live: 'https://mainelynorthstar.com/', tags: ['product identity', 'routing', 'documentation']
  },
  {
    slug: 'project-sasquatch', title: 'Project Sasquatch', eyebrow: 'Product experience',
    business: 'MAINELY CODE LLC', status: 'Access details require verification', accent: 'coral',
    summary: 'A product surface with its own application, product, and access context.',
    challenge: 'Avoid letting a marketing route imply account, entitlement, or hosting facts that have not been verified.',
    approach: 'Keep public copy explicit about product context, preserve app routes, and treat access decisions as a separate operational concern.',
    evidence: 'Public product pages are cited as public context only. No account, seat, or private-service behavior is represented here.',
    live: 'https://projectsasquatch.com/', tags: ['trust boundaries', 'public/private split', 'product status']
  },
  {
    slug: 'static-first-notes', title: 'Static-first systems', eyebrow: 'Engineering publication',
    business: 'Independent technical writing', status: 'Current', accent: 'sky',
    summary: 'A growing set of practical notes on stable public systems and the choices behind them.',
    challenge: 'Explain technical tradeoffs in language useful to both implementers and decision makers.',
    approach: 'Start from concrete constraints: ownership, routes, performance, accessibility, and future handoff.',
    evidence: 'Published notes, checklist, and local tools on this site.',
    tags: ['technical writing', 'maintenance', 'delivery']
  },
  {
    slug: 'civic-information', title: 'Civic information systems', eyebrow: 'Separate context',
    business: 'Independent civic work', status: 'Separate from commercial work', accent: 'slate',
    summary: 'Public-interest information with an emphasis on readable routes, source context, and durable publishing.',
    challenge: 'Keep civic authorship and commercial services distinct while designing for people who need to find and understand information quickly.',
    approach: 'Use clear provenance, stable routes, accessible reading patterns, and a deliberate boundary from company/product claims.',
    evidence: 'Linked public sites retain their own authorship and source practices.',
    live: 'https://www.jtforme.com/', tags: ['public information', 'provenance', 'accessibility']
  },
  {
    slug: 'living-blueprint', title: 'Living Blueprint', eyebrow: 'This portfolio',
    business: 'Justin Tahai', status: 'Current build', accent: 'blueprint',
    summary: 'A static portfolio that demonstrates the design and systems principles it explains.',
    challenge: 'Build a more useful professional surface than a résumé-like landing page without manufacturing metrics or product screenshots.',
    approach: 'Use content-driven routes, an explicit Pages workflow, progressive enhancement, and small explanatory tools that run locally in the browser.',
    evidence: 'This repository, its generated pages, and the public deployment form the reproducible artifact.',
    live: 'https://github.com/JTAHAI/jtahai.github.io', tags: ['Astro', 'GitHub Pages', 'progressive enhancement']
  }
];

export const notes = [
  { slug: 'static-first', title: 'Static-first is a maintenance strategy', date: '2026-09-14', deck: 'Why public content benefits from a smaller, more explicit runtime surface.' },
  { slug: 'responsive-constraints', title: 'Responsive layouts need constraints, not rescue rules', date: '2026-09-14', deck: 'How long labels, short viewports, and real zoom levels reveal the actual design.' },
  { slug: 'motion-with-consent', title: 'Motion earns its place when it can stop', date: '2026-09-14', deck: 'Background media, reduced motion, and the static state that must stand on its own.' },
  { slug: 'delivery-parity', title: 'A domain, a deployment, and a source tree must agree', date: '2026-09-14', deck: 'A practical way to prevent one public URL from hiding several conflicting truths.' },
  { slug: 'product-status-data', title: 'Product status is data, not decorative copy', date: '2026-09-14', deck: 'Why availability, ownership, and release language need an authoritative source.' },
  { slug: 'portfolio-as-proof', title: 'A portfolio should be a working argument', date: '2026-09-14', deck: 'Building evidence into the experience without turning it into a control room.' }
];

export const routes = [
  { label: 'MAINELY CODE LLC', href: 'https://mainelycode.com/', detail: 'Company and product work' },
  { label: 'TAHAI Web Services', href: 'https://tahai.net/', detail: 'Justin Tahai’s personal DBA' },
  { label: 'Professional hub', href: 'https://justintahai.jtforme.com/', detail: 'Concise professional routing' },
  { label: 'Personal context', href: 'https://jtahai.jtforme.com/', detail: 'Background and personal work' }
];
