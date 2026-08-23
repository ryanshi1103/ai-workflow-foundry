# Repository Organization Proposal

The candidate preserves product boundaries for the workspace runtime, media
skills, MediaFlow contract, and nameplate workflow. Feedback Intelligence is
excluded pending a license decision. A clean GitHub information architecture is valuable, but a
large directory move before the first safe public release would create noisy
history and broken links.

## Recommended public shape

```text
FlowFoundry/
├── README.md
├── ROADMAP.md
├── CONTRIBUTING.md
├── SECURITY.md
├── CHANGELOG.md
├── docs/
│   ├── vision/
│   ├── architecture/
│   ├── tutorials/
│   ├── demos/
│   ├── operations/
│   └── assets/
├── examples/
│   ├── personal-ai/
│   ├── coding-agent/
│   ├── research-agent/
│   └── automation/
├── src/flowfoundry/
├── tests/
├── catalog/
├── schemas/
├── core/
├── components/
├── applications/
└── workflows/
```

The final four directories should remain because they express real product and
license boundaries, not accidental clutter.

## What this pass changes

- Adds root GitHub convention files for roadmap, contribution, security, and
  changelog discovery.
- Adds a `docs/demos/` home and `docs/assets/` preview structure.
- Keeps required canonical documents at `docs/*.md` so public links remain
  stable.
- Keeps the existing offline orchestration example at its current stable path.

## Incremental migration

### Step 1 — Public launch candidate

Keep paths stable. Add a documentation index and consistent cross-links. Mark
historical audit/incident material separately from current product docs in the
sanitized publication candidate.

### Step 2 — Documentation information architecture

Move documents only with redirect stubs or link checks:

- `docs/vision/`: vision and personal AI direction;
- `docs/architecture/`: runtime, security, provider, and data architecture;
- `docs/tutorials/`: install, offline run, provider setup, workflow authoring;
- `docs/demos/`: flagship journeys and transcripts;
- `docs/operations/`: release, recovery, privacy, and incident runbooks.

### Step 3 — Example taxonomy

Add examples only when they run offline from a clean checkout:

- `personal-ai/`: context-policy and memory-safe fixtures;
- `coding-agent/`: planner/builder/reviewer/tester workflows;
- `research-agent/`: cited synthetic or local-corpus research;
- `automation/`: deterministic tools with explicit approval boundaries.

Every example needs a README, expected output, zero-secret fixture, maturity
label, and test.

### Step 4 — Extension boundaries

After the provider/workflow SDK stabilizes, consider:

```text
packages/
├── flowfoundry-core/
├── flowfoundry-provider-sdk/
├── flowfoundry-workflow-sdk/
└── flowfoundry-cli/
```

Do not split packages before independent versioning or dependency boundaries
justify it.

## Files to avoid publishing as product docs

Generated session transcripts, machine-specific state, test run directories,
real provider envelopes, credentials, customer exports, and private media must
remain outside a public candidate. Historical incident documents should be
sanitized and separated according to the approved history plan; directory
organization alone does not remove Git objects.

## Decision rule

Prefer a move only when it improves one of these outcomes:

- a new user finds the quick start faster;
- a contributor finds the correct extension contract faster;
- a maintainer can apply a clearer license/security/release boundary;
- automation can validate the structure more reliably.

Do not reorganize solely to make the tree look symmetrical.
