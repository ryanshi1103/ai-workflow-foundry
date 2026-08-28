# Real Demo Asset Checklist

Status: **asset production plan**. No item in this document is evidence until
the file exists, its manifest is complete, and an independent reviewer has
verified it.

## Non-negotiable asset rules

- Capture only the final owner-approved candidate.
- Record the exact commit SHA; do not inherit `64f1563...` or any earlier SHA
  merely because it appears in planning documents.
- Use actual runtime output. Explanatory animation and conceptual mobile art
  must be labeled as such and cannot substitute for a product capture.
- Show fake-provider or offline mode visibly whenever it is used.
- Never include credentials, private repository names, usernames, filesystem
  paths, tokens, notifications, or unrelated terminal history.
- Preserve the raw capture privately long enough to audit the edit, and publish
  only the sanitized derivative.
- Captions, narration, and README text must claim no more than the captured run
  proves.

## Source identity for all assets

The source SHA for every item is currently:

`TBD — exact final approved release candidate`

Before recording, the operator must capture:

```text
git rev-parse HEAD
git branch --show-current
git status --short
flowfoundry --version
```

A dirty tree or identity mismatch is a stop condition.

## Asset manifest

| Asset | Purpose | Required content | Source SHA | Verification method | Status |
|---|---|---|---|---|---|
| 90-second flagship video | Explain the need, workflow, evidence, and human boundary | 0–10s fragmentation; 10–30s goal; 30–60s coordination; 60–80s evidence; 80–90s approval | TBD | Re-run commands on same SHA; compare timeline and outputs; two-person claim/privacy review | BLOCKED — not recorded |
| 30-second social clip | Earn a qualified visit to the repository | Problem, one goal, coordinated plan, evidence, “human remains in control” | TBD | Trace every frame to flagship raw capture; verify captions and landing link | BLOCKED — depends on flagship video |
| README screenshots | Let a visitor inspect real behavior without video | Goal/plan, evidence/review, approval boundary | TBD | Match each image to raw capture and runtime output; inspect metadata and redaction | BLOCKED — not captured |
| Architecture diagram | Explain components and trust boundaries | Goal, coordination layer, supported provider/tool boundary, project/evidence, human approval; future layers visually separated | N/A for runtime; record docs source SHA | Review against canonical product architecture and current capability matrix | PLANNED — explanatory visual |
| Terminal GIF | Show time-to-value in the README | Exact offline command from goal to verified result, with idle time trimmed but no outcome altered | TBD | Reproduce in clean environment; compare expected output; verify speed-up disclosure | BLOCKED — not captured |
| Installation recording | Prove the public artifact works for a newcomer | Clean environment, artifact install, validation, offline first workflow, elapsed time | TBD | Independent external run from published artifact; record platform, Python, hash, timing | BLOCKED — no public artifact |

## 1. Ninety-second flagship video

Use [DEMO_RECORDING_CHECKLIST.md](DEMO_RECORDING_CHECKLIST.md) as the canonical timeline
and [github-release-assistant.md](demos/github-release-assistant.md) as the
capability boundary. The screen should show one goal, a bounded plan, explicit
agent roles, evidence, and the approval boundary. Narration must say that the
demonstration uses deterministic/offline or fake-provider mode when applicable.

Acceptance requires a transcript, captions, audio-level check, 1080p readable
terminal text, exact command appendix, SHA overlay, sanitization review, and a
second person reproducing the outcome.

## 2. Thirty-second social clip

Cut this only from verified flagship material. It should not compress away the
mode label or human-control boundary. End with a factual invitation such as
“View the Developer Preview and reproduce the offline workflow,” not a claim of
autonomy or universal support.

Acceptance requires burned-in captions, a readable call to action, correct
aspect-ratio versions, and frame-by-frame traceability to the flagship source.

## 3. README screenshots

Capture a maximum of three images. Crop for readability without hiding
warnings, modes, or approval states. Each caption should state what is shown,
which mode produced it, and what is not shown.

Acceptance requires descriptive alt text, no private data, no misleading
composites, consistent terminal theme, and a manifest entry for every image.

## 4. Architecture diagram

This is explanatory artwork, not proof that every depicted future interface is
implemented. Use solid styling for shipped components, dashed styling for
designed components, and muted styling for future components. If the launch
page needs only current behavior, omit future layers entirely.

Acceptance requires review against
[FLOWFOUNDRY_PRODUCT_ARCHITECTURE.md](FLOWFOUNDRY_PRODUCT_ARCHITECTURE.md), a
legend, accessible contrast, readable mobile layout, and a source file that can
be maintained in the repository.

## 5. Terminal GIF

Prefer a short deterministic offline run over a fast montage. Trimming silent
time is allowed if the caption discloses it; changing output, splicing different
runs, or implying provider calls that did not occur is not.

Acceptance requires a clean start state, command visibility, mode visibility,
final result, readable dimensions, optimized file size, and a linked full-text
transcript.

## 6. Installation recording

Record this from an environment not used to build the artifact. The participant
should follow only published instructions. Capture OS, architecture, Python
version, artifact filename and hash, start/end time, corrections required, and
the first workflow result.

Acceptance requires at least two external clean-environment successes, all
failures retained in the validation log, no preinstalled project checkout on
the path, and exact reproduction instructions.

## Per-file provenance record

Store this metadata beside the production checklist for every published asset:

```text
Asset filename:
Public URL:
Source commit SHA:
Branch/ref:
Capture date (UTC):
OS / terminal / Python:
Execution mode:
Commands:
Artifact filename and SHA-256 (if applicable):
Edits made:
Sanitization reviewer:
Technical verifier:
Accessibility reviewer:
Verification result:
Known limitations shown or linked:
```

## Asset publication gate

An asset is publishable only when the manifest is complete, the exact run is
reproducible, privacy review passes, captions are accessible, the claim matches
the evidence, and the linked candidate is the one actually approved for
release. Missing evidence keeps the item **BLOCKED**; a polished placeholder
does not move it to ready.
