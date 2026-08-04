# Decisions — FlowFoundry AI

## 1. Monorepo structure with independent component boundaries

**Decision:** Bundle the workspace runtime, media skills, feedback application, and
nameplate generator in one monorepo while preserving their independent runtimes,
licenses, and release boundaries.

**Why:** Components share a common workflow lifecycle philosophy but differ in
users, dependencies, licensing, and release artifacts. A monorepo is the canonical
integration point without forcing them to share a single runtime.

**Date:** 2026-08-03

## 2. Preserved Git histories for bundled components

**Decision:** Each bundled component retains its original Git history through
subtree merges rather than being copied as a snapshot.

**Why:** Preserves authorship, version history, and provenance. The monorepo is a
canonical integration point, not a rewrite.

**Date:** 2026-08-03

## 3. Catalog as the integration contract

**Decision:** Machine-readable JSON manifests in `catalog/` validated against a
JSON Schema, with a dependency-free Python validator that enforces the critical
subset without external runtime dependencies.

**Why:** Components can be validated before execution. The catalog declares what
is bundled, what safety boundaries exist, and what maturity level to expect. The
dependency-free validator ensures the contract can be checked in any environment.

**Date:** 2026-08-03

## 4. Safety-first lifecycle

**Decision:** All components must declare: local-first operation, originals
preservation, review-before-side-effects, secret policy, and network policy.

**Why:** AI-authored proposals are untrusted candidates. Trusted application code
must own command construction, path resolution, credential access, and
irreversible actions. This principle is enforced structurally in the schema.

**Date:** 2026-08-03

## 5. Explicit maturity labeling

**Decision:** Every component declares maturity as experimental, alpha, beta, or
stable. No component is presented as production-ready without evidence.

**Why:** Prevents overclaiming. The nameplate generator is stable (deterministic);
the AI-dependent components are beta. This honesty is part of the safety contract.

**Date:** 2026-08-03

## 6. Components not integrated

**Decision:** The Confera desktop release, photo archive, Android control, Minimal
Focus GRUB theme, Hunan presentation, camp print materials, and Taobao automation
remain separate products or private case studies.

**Why:** They serve different audiences, have different licensing/legal
constraints, or contain private data. The portfolio is strengthened by referencing
their patterns without bundling them.

**Date:** 2026-08-03

## 7. Portable workflow contracts with capability registry

**Decision:** Workflow contracts are validated against a JSON Schema independent of
any runtime. A capability registry maps reviewed intents (what a workflow stage does)
to trusted implementations. Contracts must declare their stages, artifacts, review
requirements, and execution preconditions before any code runs.

**Why:** A workflow contract must be validatable without importing the application
it describes. Hosts can reject unsafe or incompatible declarations before execution.
The capability registry prevents untrusted code from masquerading as a reviewed skill.

**Date:** 2026-08-04

## 8. Unified workspace-workflow package

**Decision:** Merge the workspace manager (`ai_project_manager`) into the FlowFoundry
package as a `workspace` subpackage. A single CLI (`flowfoundry`) now manages the full
lifecycle: define workflow contracts → register capabilities → create projects → launch
sessions → track/finalize → validate contracts. The old `aiproj` and `cc` scripts
become thin wrappers delegating to the unified CLI.

**Why:** Previously, the workspace manager (deployed to `~/.local/` by shell script)
and the flowfoundry package (installed via pip) were two completely separate Python
packages with zero code integration. Users ran `cc` for projects and `flowfoundry`
for validation — two separate tools with no shared awareness. Unifying them under one
package means: (1) one `pip install -e .` replaces a multi-step deploy.sh, (2) projects
can reference workflow contracts as their operational template, (3) `flowfoundry validate`
can cross-check project sessions against their declared contracts, (4) the interactive
cc launcher moves from 1000+ lines of bash to maintainable Python.

**Date:** 2026-08-04
