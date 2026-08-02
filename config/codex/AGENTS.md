# Global Project Rules

- `CC_ACTIVE_PROJECT` is the real project root set by `cc` at launch. Respect it.
- Do NOT auto-create timestamp session directories under `~/Projects/`.
- Do NOT switch to a different project directory without user consent.
- At session start, quickly check README, AGENTS.md, Git status, and `.ai/PROJECT_STATE.md`.
- Do NOT run full deep hygiene on every launch — that's handled by `cc-projects-maintain`.
- Do NOT rename the current working directory during an active session.
- Never delete user original files, data, photos, videos, keys, or uncommitted work.
- Clean up temporary test files after tests pass.
- Run relevant tests after making changes.
- `ai-project-workspace-manager` is the source of truth for `cc`, Codex integration, and AI Project Manager.
- Before modifying user-level deployment files, update the source project first, then deploy via the official deploy script.
- Do NOT read or output `~/.codex/auth.json` from within a project session.
