# Visual Design System

FlowFoundry should feel decisive, adaptive, grounded, capable, clear, and
constructive. It is dependable infrastructure with a friendly product surface,
not futuristic AI decoration.

## Brand position

Brand promise: **One goal. The smallest sufficient AI team.**

Official category: **Local-first Adaptive AI Team Runtime.**

Current product stage: **AI Coordination Layer.**

The Council Mark expresses independent capabilities organized around one
shared goal or resolved outcome. The principal star is not a superior model
ruling the smaller stars.

Keywords:

- decisive;
- adaptive;
- grounded;
- capable;
- clear;
- constructive.

Avoid robots, glowing brains, humanoids, generic magic sparkles, orbit rings,
crowns, rank symbols, unreadable dashboards, and claims of autonomous
intelligence.

## Logo concept

The canonical source is `branding/logo.svg`; its locked geometry is specified
in `branding/BRAND_ASSET_SPEC.md`:

- one principal star above three equal council stars;
- one repeated mother curve for all four stars;
- an exact `2:1` principal-to-council scale ratio;
- fixed centers on a `24 × 24` grid; and
- a monochrome silhouette that remains authoritative without material effects.

The Human-approved Council direction supersedes the earlier SYNTHESIS
rail/junction/block prototypes. SYNTHESIS remains an important historical
Meeting decision, not the current production direction. `branding/logo.png`
is a deterministic 512 px raster export of the canonical Council Mark SVG; the
SVG and locked geometry remain authoritative.

Do not place provider logos inside the mark. Do not interpret the principal
star as a preferred provider. FlowFoundry remains provider-independent.

## README banner concept

The GitHub first screen uses this semantic order:

```text
┌─────────────────────────────────────────────────────────────────┐
│ [Council Mark]  FLOWFOUNDRY                                    │
│                 One goal. The smallest sufficient AI team.     │
│                 Local-first Adaptive AI Team Runtime            │
│                                                                 │
│ Goal → Profile → Minimum Sufficient Team → Execute → Validate  │
│                                                                 │
│ local-first · bounded meetings · validation · recovery         │
└─────────────────────────────────────────────────────────────────┘
```

The current README uses the approved app-icon SVG on its controlled midnight
field rather than inventing a new banner. A future banner may add the hierarchy
above after release-asset and contrast validation. It must not list every
provider, feature, or roadmap phase.

## Color system

Identity and functional state colors are separate systems.

### Identity palette

| Token | Hex | Use |
|---|---|---|
| Midnight field | `#09142B` → `#172A52` | controlled app/avatar background |
| Charles Blue | `#20365F` | solid mark on light controlled surfaces |
| Warm ivory | `#F4F1EA` | solid mark on dark controlled surfaces |
| Ice blue/periwinkle | material range | restrained glass body on midnight field |

Glass is presentation, not geometry. Do not use translucent glass directly on
white or uncontrolled photography. Production contrast still requires release
validation.

### Functional state palette

| Token | Hex | Use |
|---|---|---|
| Foundation navy | `#10172F` | terminal/product background |
| Surface navy | `#1D2B50` | panels and terminal selections |
| Flow cyan | `#4BD4E6` | active coordination and links, not brand geometry |
| Verified green | `#43E6A0` | successful validation or safe completion |
| Attention amber | `#FFC65A` | experimental state or human decision |
| Risk red | `#FF6B78` | blockers and destructive risk only |
| Primary text | `#F4F8FF` | dark-background text |
| Secondary text | `#9FACCA` | metadata and annotations |

Never use green for a model-generated answer before validation. Never use red
for ordinary incomplete roadmap work. Functional colors do not recolor
individual Council stars.

## Favicon and avatar rules

- Use the controlled-field app icon for GitHub avatar and favicon contexts.
- Minimum app/favicon size is `16 px`; minimum standalone mark is `24 px`.
- Keep the four-star geometry and exact `2:1` ratio at every size.
- No wordmark, tagline, extra star, orbit, crown, face, arrow, or provider mark
  appears inside an avatar.
- For monochrome use pure black or pure white, not simulated glass.

## Campus poster hierarchy

The adopted campus order is:

1. `你定目标，AI组队实现`;
2. large Council Mark;
3. one plain-Chinese explanation—the exact canonical sentence remains open;
4. compact proof: `目标 → 组队执行 → 检查交付`;
5. one real, verified action or QR target; and
6. small FlowFoundry name and English tagline.

Do not fabricate a URL, download claim, QR code, event, or shipped capability.

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

- release-validated Council app icon, light/dark/monochrome exports, favicon,
  and checksums;
- optional approved README banner (`.svg` and 2× `.png`);
- one actual launcher screenshot;
- AI Project Manager poster, GIF/MP4, and transcript;
- Open Graph social card with the exact public release version;
- source files and an asset license/provenance record.
