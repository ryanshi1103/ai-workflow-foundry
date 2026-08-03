# Project Pattern Audit

Audit date: 2026-08-03

This is a lightweight product and architecture review of active projects. It is
not an automated cleanup pass. Original files, uncommitted work, private session
data, and the explicitly excluded VPN project were not modified.

| Project or line | Keep separate? | Reusable strength for the wider portfolio |
|---|---:|---|
| AI Project Workspace Manager | Bundled core | Real project root, multi-tool launcher, permission confirmation, recovery, retention-aware maintenance |
| Legacy AI manager workspaces | Yes; archive candidates | Historical implementation evidence only; no new public product |
| Confera/Huiying workbench | Yes | Stage contracts, tool registry, immutable revisions, artifact hashes, review/export separation |
| Confera desktop release | Yes | Release readiness, dependency licensing, SBOM/checksum discipline, platform acceptance |
| Feedback Analysis System | Yes | Original AI result retention, human audit trail, mock mode, safe imports, local database |
| Photo archive | Yes | `.partial` writes, SHA-256 verification, atomic promotion, deletion gate |
| Android control | Yes | Plan/apply/restore operations and device-specific capability checks |
| Minimal Focus GRUB theme | Yes | Backup/install/uninstall loop, rollback, visual preview, EFI-level validation |
| Print-ready nameplates | Yes | Structured input, deterministic geometry, editable output, safe filenames, target-app test |
| Hunan presentation | Yes/private | Source manifests, narrative structure, preview sheets, media license boundary |
| Camp print materials | Yes/private source | Separating personal input data from generic generation code |
| Taobao automation | Yes/private experimental | Inventory reservation, idempotency targets, operational audit ledger; production claims remain blocked |

## Consolidation decision

Only the workspace runtime is physically bundled because it provides the actual
project lifecycle foundation. Confera Skills, Feedback Analysis, and the
Nameplate Generator are registered as separate components with honest
integration modes. Other projects contribute design patterns and remain
independent products or private case studies.

This produces a coherent portfolio with one platform foundation and several
credible specialist products. It avoids two opposite failures: a flat list with
no visible relationship, and a monorepo that claims unrelated code is one app.
