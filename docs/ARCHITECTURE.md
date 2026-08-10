# Architecture

FlowFoundry AI combines a shared workflow lifecycle and its reusable public
components in one monorepo. Components do not have to share one dependency
environment or user interface.

## Product boundary

The repository currently contains these implemented layers:

1. The bundled AI Workspace Manager runtime: project selection, tool selection,
   explicit permission modes, session records, recovery, and careful workspace
   maintenance.
2. Confera's safety-bounded media skill pack.
3. The local feedback-intelligence reference application.
4. The deterministic CSV-to-PPTX nameplate workflow.
5. The FlowFoundry catalog contract: machine-readable declarations and a
   dependency-free validator for every physically bundled component.
6. The bounded orchestration runtime: adaptive task routing, meetings, durable
   provider cancellation, and managed Git worktrees for write-capable candidate
   execution.

Automatic candidate integration and publication remain roadmap capabilities;
the implemented writer-isolation layer deliberately stops at candidate diff and
validation.

## Shared lifecycle

```text
Project context
  -> Controlled inputs and declared network policy
  -> Bounded AI or deterministic stage
  -> Schema-valid candidate / artifact
  -> Human review when judgment or side effects are involved
  -> Explicit execution or export approval
  -> Validation, audit record, and recovery path
```

This lifecycle generalizes patterns already proven in the project portfolio:

- AI Workspace Manager supplies an authoritative project root, permission
  confirmation, recoverable sessions, and backup-first deployment.
- Confera supplies bounded skill manifests, a trusted tool registry, immutable
  revisions, and separate review/export gates.
- Feedback Analysis preserves the original AI result and appends human review
  records rather than silently overwriting model output.
- Photo archiving supplies hash verification, partial outputs, atomic promotion,
  and an explicit deletion gate.
- Minimal Focus supplies backup, install, uninstall, rollback, and standalone
  acceptance testing as one product loop.
- Android utilities use plan/apply/restore as an understandable operational
  contract.
- Document automation separates structured content from deterministic layout
  and validates output in the real target application.
- Presentation work records source provenance alongside generated assets.

## Integration modes

| Mode | Meaning |
|---|---|
| `bundled` | Code is present in this repository and the path is validated. |
| `compatible-extension` | A future separately versioned package follows compatible safety and review concepts; install is explicit. |
| `reference-application` | A future independent product demonstrates the lifecycle without claiming plug-and-play integration. |
| `reference-workflow` | A future focused workflow provides reusable implementation patterns without being bundled. |

This vocabulary prevents a portfolio link from being mistaken for an installed
plugin or a universal executor.

## Trust boundary

AI-authored text or plans are untrusted candidates. Trusted application code
must own command construction, path resolution, credential access, file writes,
artifact validation, and irreversible actions. Human review does not by itself
grant export or destructive authority; those approvals should be explicit and
separate.

## Component manifest

Each file in `catalog/` declares:

- product identity, kind, maturity, source, and license;
- whether the relationship is bundled, compatible, or referential;
- user-facing capabilities and reusable design patterns;
- lifecycle stages and approval points;
- local, original-preservation, secret, and network boundaries.

The JSON Schema is useful to editors and external tools. The standard-library
validator intentionally enforces the critical subset without adding a runtime
dependency.

## Repository layout

```text
branding/                 product logo
catalog/                  validated component declarations
core/workspace-manager/   bundled runtime with preserved project history
components/               reusable workflow packs with preserved histories
applications/             runnable vertical applications with preserved histories
workflows/                focused deterministic workflows with preserved histories
docs/                     architecture, audit, product lines, roadmap
schemas/                  reusable JSON contract
src/flowfoundry/           catalog library and CLI
tests/                     foundation contract tests
```
