# Deferred Technical Debt

Items here are non-blocking for the locally tested portfolio migration. Human
actions and release operations are listed separately in
`HUMAN_ACTIONS_REQUIRED.md`.

## FlowFoundry orchestration

- The local-command provider is an explicit development seam, not an OS
  sandbox. Add provider-native cancellation, resource quotas, and structured
  streaming before unattended real execution.
- Current per-task directories isolate orchestration state. Production adapters
  should provision approved worktrees or containers according to
  `workspace_mode`.
- File locking targets one compatible local filesystem; distributed scheduling
  and remote locking are outside the MVP.
- Run schema version 1 has no migration framework yet. Add signed/validated
  schema migrations before changing persisted fields.
- Add richer planner/provider adapters behind the current offline-stable plan
  schema; CI must continue using fake providers.

## Feedback Intelligence

- The owner must make an explicit standalone license decision.
- Exact database rollback remains backup-based; destructive down-migrations are
  intentionally absent.
- Add reproducible screenshots only from public or synthetic data.
- GitHub URL/badge changes wait for the manual in-place repository rename.

## Huiying / MediaFlow

- The private histories report 288 core and 317 desktop findings under the
  current strict Ruff baseline. Address them in bounded behavior-preserving
  batches rather than a migration-time mass rewrite.
- A clean desktop environment needs the approved Android SDK 36 toolchain for
  the one environment-dependent test.
- Windows lock hashes, signing, installer/upgrade verification, and release
  provenance require the protected release environment.
- Real-provider and real-media acceptance tests remain private operator work.

## Portfolio and component lifecycle

- Decide whether public component repositories remain independent release
  mirrors or become redirect/archive targets after FlowFoundry is pushed and CI
  is proven.
- Installed `flowfoundry validate` validates packaged declarations; only a
  source checkout can validate physical monorepo bundled paths. Keep this
  distinction explicit in future CLI wording.
- Pending DeepSeek reviews must remain `REVIEW_PENDING`; do not promote them to
  approval without review artifacts.
