# Visual Design System

FlowFoundry should look like dependable infrastructure: calm, precise,
technical, and human-centered. Visuals should explain coordination and trust,
not decorate the repository with futuristic AI clichés.

## Brand position

Core idea: **many capabilities enter a controlled coordination core; one
reviewable outcome leaves.**

Keywords:

- coordination;
- intelligence infrastructure;
- personal AI;
- open source;
- human-centered;
- controlled and recoverable.

Avoid robots, glowing brains, humanoids, magic sparkles, unreadable dashboards,
and claims of autonomous intelligence.

## Logo concept

The existing mark already expresses the desired idea:

- three input nodes represent models, tools, and context;
- paths converge into a central diamond/check representing coordination and
  validation;
- one output node represents a reviewable artifact;
- the dark foundation color signals infrastructure;
- violet, cyan, and green distinguish inputs, flow, and verified output.

Keep `branding/logo.svg` as the editable source and `branding/logo.png` as the
GitHub-compatible raster export. Future refinements should preserve this
semantic structure and test legibility at 24, 48, 128, and 512 pixels.

Do not place provider logos inside the mark. FlowFoundry must remain visibly
provider-independent.

## README banner concept

Recommended 1600×480 composition:

```text
┌─────────────────────────────────────────────────────────────────┐
│ [FlowFoundry mark]  FLOWFOUNDRY                                 │
│                     AI Coordination Layer for Personal AI       │
│                                                                 │
│ Goal  →  Coordinator  →  Models / Tools / Context  →  Review   │
│                                                                 │
│ Local-first · Human-centered · Open source                      │
└─────────────────────────────────────────────────────────────────┘
```

Use a dark navy-to-deep-teal background, generous negative space, thin flow
lines, and one clear sentence. The banner should not list every provider,
feature, or roadmap phase. Export SVG plus a 2× PNG and keep all source files in
`branding/`.

The current README intentionally uses the existing logo and a text-based first
screen until a reproducible banner is approved.

## Color system

| Token | Hex | Use |
|---|---|---|
| Foundation navy | `#10172F` | primary background |
| Surface navy | `#1D2B50` | panels and terminal selections |
| Coordination violet | `#8B7CFF` | multi-input or planning paths |
| Flow cyan | `#4BD4E6` | active coordination and links |
| Verified green | `#43E6A0` | successful validation or safe completion |
| Attention amber | `#FFC65A` | experimental state or human decision |
| Risk red | `#FF6B78` | blockers and destructive risk only |
| Primary text | `#F4F8FF` | dark-background text |
| Secondary text | `#9FACCA` | metadata and annotations |

Never use green for a model-generated answer before validation. Never use red
for ordinary incomplete roadmap work.

## Typography

- GitHub/documentation: system sans-serif for prose and system monospace for
  commands and state.
- Marketing banner: Inter, IBM Plex Sans, or an equivalent open font.
- Terminal and code visuals: SFMono, Menlo, JetBrains Mono, or a system fallback.
- Avoid ultra-light weights and all-caps paragraphs.

## Screenshot style

Screenshots should prove a user outcome or trust property.

- Crop to one decision at a time.
- Use synthetic project and user data.
- Show the relevant goal, plan reason, permission, candidate, validation, or
  approval—not a full desktop.
- Use a consistent 16:10 or 16:9 canvas with a neutral light outer background
  and the dark product surface.
- Keep terminal text at a readable size; do not add perspective effects.
- Add a short caption distinguishing **actual screenshot**, **rendered preview**,
  or **concept mockup**.
- Redact paths, account identifiers, tokens, provider request IDs, and private
  branch names before capture.

The current `docs/assets/screenshots/launcher-preview.svg` is labeled as a
rendered preview and should be replaced by a real clean-checkout capture only
after the adaptive launcher regression suite is green.

## Demo GIF style

Target length: 60–90 seconds; 1280×720; 15–24 fps; no audio dependency.

Each GIF should use:

1. a three-second goal frame;
2. a visible coordination explanation;
3. scoped roles/context/permissions;
4. a validation or conflict moment;
5. a human review/approval decision;
6. the final artifact and evidence receipt.

Use gentle crossfades or direct cuts. Avoid rapid typing capture, cursor loops,
fake loading screens, and text too small to read on the GitHub page. Provide a
poster PNG and accessible transcript beside every GIF.

The current demo SVG files are storyboard placeholders. They must not be
described as recorded product behavior.

## Diagram rules

- Prefer Mermaid for architecture and lifecycle diagrams so changes are
  reviewable.
- Use left-to-right flows for short user journeys and top-to-bottom diagrams for
  architecture.
- Keep models/providers at the same visual level; do not imply one permanent
  winner.
- Show human approval as an explicit decision node.
- Show planned layers with dashed edges and a legend.
- Limit a diagram to one main question.

## Asset checklist

Before public launch, prepare:

- approved README banner (`.svg` and 2× `.png`);
- light and dark logo exports;
- one actual launcher screenshot;
- AI Project Manager poster, GIF/MP4, and transcript;
- Open Graph social card with the exact public release version;
- source files and an asset license/provenance record.
