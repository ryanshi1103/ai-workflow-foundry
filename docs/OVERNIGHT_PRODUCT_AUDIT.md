# Overnight Product Audit

Status: documentation and presentation audit only
Audit baseline: `de887134f127ec8f587a94b438f7c553040b1357`
Audit date: **2026-08-25**

## Scope and method

This audit reviewed the repository landing page, canonical documentation index,
product and technical architecture, current status, limitations, roadmap,
positioning, visual system, mobile design, demo specifications, community
model, release gates, and every committed image/SVG asset. Runtime behavior,
schemas, contracts, providers, agents, and release refs were out of scope.

Executable behavior and candidate evidence remain authoritative. Product polish
may make truth easier to understand; it must not broaden that truth.

## Existing approved assets

| Asset | Purpose | Status | Source and preservation decision |
|---|---|---|---|
| `branding/logo.svg` | Editable brand mark: several inputs converge into one validated output | Approved brand source | Preserve unchanged |
| `branding/logo.png` | GitHub-compatible logo export | Approved raster export | Preserve and retain in README hero |
| `docs/assets/screenshots/launcher-preview.svg` | Explain the adaptive terminal launcher | Rendered preview derived from tested layout contract; not a screenshot | Preserve unchanged and keep its explicit preview label |
| `docs/assets/demos/ai-project-manager-placeholder.svg` | AI Project Manager storyboard | Placeholder, not runtime evidence | Preserve as historical demo planning material; do not promote as a screenshot |
| `docs/assets/demos/personal-learning-placeholder.svg` | Learning-assistant concept storyboard | Future concept | Preserve with concept label; do not place in the current-product hero |
| `docs/assets/demos/personal-ai-manager-plan.json` | Deterministic expected plan | Current fixture evidence | Preserve unchanged |
| `docs/assets/demos/personal-ai-manager-demo-output.txt` | Normalized offline demo evidence | Current fixture evidence | Preserve unchanged and never relabel as live-provider output |
| Existing Mermaid architecture diagrams | Reviewable technical/product flows | Approved explanatory diagrams | Preserve; add simpler GitHub overview assets without replacing canonical architecture |

## Productization SVG inventory

| Asset | Purpose | Status | Source |
|---|---|---|---|
| `docs/assets/architecture-overview.svg` | Hero-level goal → coordination → evidence → approval explanation | Current Alpha explanatory diagram | Canonical product architecture and current status |
| `docs/assets/product-evolution.svg` | Contrast manual fragmentation with bounded coordination | Conceptual problem/solution diagram | Positioning, visual story, and approved product message |
| `docs/assets/github-release-flow.svg` | Explain the verified flagship demo lifecycle and stop | Synthetic Alpha demo diagram | Exact GitHub Release Assistant fixture and canonical demo guide |
| `docs/assets/roadmap.svg` | Make current/designed/future stages unambiguous | Product roadmap diagram | Canonical Product Roadmap and mobile/Personal AI OS boundaries |

All four use the existing brand palette, transparent background treatment,
system typography, accessible titles/descriptions, and explicit maturity
labels. None is a product screenshot.

The new product SVGs reuse the approved visual language and explain existing
behavior. They are diagrams, not screenshots or evidence of a graphical client.

## Existing UI language

### Colors

- foundation navy `#10172F` for dependable infrastructure;
- surface navy `#1D2B50` for panels and terminal selections;
- coordination violet `#8B7CFF` for inputs and planning;
- flow cyan `#4BD4E6` for active coordination;
- verified green `#43E6A0` only after validation;
- attention amber `#FFC65A` for human decisions and experimental states; and
- risk red `#FF6B78` only for blockers or consequential risk.

### Layout

The approved layout is calm and technical: generous spacing, bounded cards,
thin flow lines, short evidence labels, left-to-right user journeys, and
top-to-bottom architecture. The terminal launcher is compact, keyboard-first,
content-aware, and explicit about clean/dirty and permission state.

### Terminology

Use `goal`, `coordination`, `minimum sufficient path`, `candidate`, `review`,
`approval`, `evidence`, `recovery`, and `human authority`. Use `agent identity`
or `routed role` when an offline fixture does not call a live provider.

Avoid `AI employee`, `AGI`, `autonomous replacement`, `universal intelligence`,
`best model` without evidence, and any wording that turns a designed mobile or
memory layer into a shipped capability.

### Visual style

Preserve system sans-serif and monospace typography, accessible contrast,
semantic color, transparent status labels, and provider-independent imagery.
Do not introduce robots, glowing brains, provider-logo collages, magic
sparkles, fake dashboards, or futuristic remote-desktop scenes.

## Existing product story

### Current — AI Coordination Layer

The Alpha coordinates bounded goals through planning, capability routing,
deterministic/offline execution, review, approval, recovery, evidence, and Git
isolation. Real-provider parity, public artifacts, external install evidence,
and adoption validation remain incomplete.

### Designed — Personal AI Command Center

The approved direction is an approval and intelligence interface, not remote
desktop. The phone submits bounded goals, reviews plans and evidence, and signs
exact actions; projects, credentials, and execution remain on the computer.
No mobile application or PWA is implemented.

### Future — Personal AI OS

The long-term direction adds user-owned, provenance-aware context and resource
coordination. Personal data must remain private by default, inspectable,
correctable, exportable, expirable, and removable. This is roadmap work, not an
Alpha capability.

## Conflicts and confusion risks

| Finding | Risk | Resolution |
|---|---|---|
| The old README explained the product accurately but repeated definition, examples, demos, repository internals, and roadmap before completing the first-user story | A stranger understands the architecture before knowing the fastest reason to try | Tighten the landing sequence to problem → current boundary → workflow → demo → quick start → roadmap → contribution |
| `docs/demos/PERSONAL_AI_MANAGER.md` and `personal-ai-manager-demo.md` overlap | Two “official” scripts can drift | Keep both for history; identify the lowercase 90-second script as the executable canonical walkthrough in the documentation map |
| `AI Project Manager` and `Personal Learning Assistant` documents use legacy demo numbering | “Demo 2” appears more than once and can look like a launch order | Treat GitHub Release Assistant as flagship; classify the others as supporting Alpha story or future concept |
| Product terms include Personal AI Manager, Assistant, Command Center, and OS | Designed/future terms may look like parallel shipped products | Use three maturity stages consistently: Coordination Layer / Command Center / Personal AI OS |
| `WEBSITE_STRUCTURE.md` specifies information architecture while new launch copy is also required | A second website plan could duplicate structure | Keep `WEBSITE_STRUCTURE.md` as IA and use `WEBSITE_CONTENT.md` only for approved draft copy/evidence slots |
| Historical names such as `MARKETING_PLAN.md` and `OPEN_SOURCE_LAUNCH.md` were removed during candidate consolidation | Recreating them would restore duplicate launch authorities | Use one new `MARKETING_LAUNCH_PLAN.md`; keep release authority in the Alpha checklist and runbook |
| Release reports correctly carry multiple SHA/evidence boundaries | Product readers may confuse a runtime baseline, documentation candidate, and future artifact | Keep SHA detail in release documents; the README links current status without making release claims |
| Placeholder SVGs can be mistaken for product screens | Visual polish could accidentally overstate maturity | Keep “placeholder”, “rendered preview”, “Designed”, and “Future” labels visible; add no fake screenshot |

## First-impression decision

Preserve the brand and product truth. Improve hierarchy, visual explanation,
demo prominence, quick-start scannability, and contributor invitation. Do not
replace approved architecture, rename the product, add badges without evidence,
or create a new product surface.
