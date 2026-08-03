# Architecture

FlowFoundry AI separates a shared workflow lifecycle from domain-specific
products. It does not require every product to share one codebase or one user
interface.

## Product boundary

The repository currently contains two implemented layers:

1. The bundled AI Workspace Manager runtime: project selection, tool selection,
   explicit permission modes, session records, recovery, and careful workspace
   maintenance.
2. The FlowFoundry catalog contract: machine-readable declarations and a
   dependency-free validator for bundled and separately versioned components.

The future workflow execution layer is deliberately documented as a roadmap,
not presented as completed code.

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
| `compatible-extension` | A separately versioned package follows compatible safety and review concepts; install is explicit. |
| `reference-application` | An independent product demonstrates the lifecycle but does not claim plug-and-play runtime integration. |
| `reference-workflow` | A focused deterministic workflow provides reusable implementation patterns. |

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
docs/                     architecture, audit, product lines, roadmap
schemas/                  reusable JSON contract
src/flowfoundry/           catalog library and CLI
tests/                     foundation contract tests
```
