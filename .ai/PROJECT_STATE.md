# Project State — FlowFoundry

Canonical state date: 2026-08-14. This file records current operational truth
for the sanitized local publication baseline and supersedes older status claims.

## Current-truth precedence

When evidence differs, use this order:

1. `.ai/PROJECT_STATE.md`;
2. current deterministic runtime and status commands;
3. current durable manifests, receipts, and validation records;
4. historical reports.

Historical reports remain evidence. They are not current state and must not
override a newer canonical conclusion, test count, readiness result, or release
gate.

## Identity and release baseline

- **Official name:** FlowFoundry
- **Naming decision:** KEEP FLOWFOUNDRY
- **Category:** Local-first Adaptive AI Team Runtime
- **Core principle:** the smallest sufficient Agent or Team
- **Branch:** `portfolio-migration`
- **Sanitized local publication baseline:** PASS
- **Sanitized baseline HEAD:** `2ffa817cba37cfa876d19e5b60a31a1bfe2efc8b`
- **Local privacy blockers:** 0
- **Remote containment:** NOT COMPLETE
- **GitHub historical exposure / PR #2:** UNRESOLVED
- **Remote history replacement:** NOT AUTHORIZED
- **Release status:** BLOCKED_PENDING_GATE_D

The sanitized baseline proves a clean local publication history. It does not
prove that GitHub-hosted pull refs, cached objects, forks, clones, or mirrors no
longer retain older incident history.

## Provider profiles

| Provider | Profile | Authentication / identity | Readiness |
|---|---|---|---|
| Codex | `codex_native` | verified | READY |
| DeepSeek-compatible | `deepseek_compatible` | verified | READY |
| Claude-native | `claude_native` | not_authenticated | AVAILABLE_UNVERIFIED / NOT READY |

The executable name is a runtime detail, not provider identity. A shared
Claude-compatible executable configured for DeepSeek is not evidence of an
authenticated Anthropic account.

## Runtime truth

| Capability | Current state |
|---|---|
| Minimum Sufficient Path | IMPLEMENTED |
| Managed writer/worktree isolation | IMPLEMENTED / VERIFIED |
| Durable Process Identity v2 | IMPLEMENTED |
| Physical cancellation | LIVE VERIFIED |
| Workspace compatibility preflight | IMPLEMENTED / VERIFIED |
| Bounded Meeting | IMPLEMENTED |
| Deterministic conflict detection | IMPLEMENTED |
| Targeted Round 2 | IMPLEMENTED |
| Convergence with dissent | IMPLEMENTED |
| Cross-provider Meeting | LIVE VERIFIED |
| Durable RUNNING reconciliation runtime | IMPLEMENTED / VERIFIED / APPLIED TO KNOWN CASES |
| Known stale retained manifests | RECONCILED in C3B |

Reconciliation distinguishes execution terminality from candidate integration.
It preserves the original observed manifest state, uses Durable Process Identity
v2 and durable receipts, fails closed on conflicting or incomplete evidence,
and never infers success from a missing PID alone.

The two known retained manifests now preserve their original `RUNNING`
observations with auditable effective states:

- `adaptive-coding-execution-path-closure-1-candidate`:
  `COMPLETED_AWAITING_INTEGRATION`;
- `minimum-tool-policy-v0-candidate`: `FAILED_RETAINED`.

Neither candidate has been integrated, merged, published, or released.

## Brand state

- **Official product name:** FlowFoundry
- **Visual identity:** final candidate exists; NOT YET INSTALLED
- **Campus poster:** candidate exists; NOT YET INSTALLED
- **Product surface / README:** NOT YET RECONCILED
- **GitHub branding:** NOT UPDATED by the local design work

## Authoritative sanitized regression baseline

| Suite | Result |
|---|---|
| Foundation | 228 passed |
| Workspace launcher/contracts | 26 passed |
| Workspace provider-launch shell | 40 passed |
| Workspace profile/deploy preservation | 4 passed |
| Workspace Python | 68 passed |
| Confera contracts | 3 passed |
| Nameplate contracts | 3 passed |
| Product total | 372 passed, 0 failed |
| Ruff | UNAVAILABLE in the verified environment |
| Feedback optional pytest extras | UNAVAILABLE in the verified environment |

Unavailable optional tooling is not reported as passing.

## Remaining real gaps

### P0 — release

- Gate D remote history replacement and GitHub-side verification.

### P1

- Install approved brand assets and reconcile the product surface.

### Security foundation

- Deny-by-default network policy.
- Local secret boundary.
- Broader minimum-sufficient tool policy.

### Extensibility

- Project-local Provider Registry.
- Adapter entry points.

### Product

- Operator Experience 0.4.

Additional provider expansion is not a current release blocker.
