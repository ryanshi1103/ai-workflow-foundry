# Current status

FlowFoundry is an **Alpha developer preview**. The public snapshot contains
the local Python CLI, goal and route contracts, evidence/evaluation code,
workspace integration, tests, and independent example components.

The supported first path is local repository work with an installed,
authenticated Codex CLI. Provider availability is checked at runtime and
depends on the user's own CLI and account. Other routes are experimental or
environment-specific; availability on the maintainer's machine does not prove
general support.

The desktop File Bridge contains a React/Tauri shell and read-only Linux Samba
diagnostics. A Fedora native build and package were produced on one development
host, but a packaged app has not been installed or tested on another machine.
The app does not yet configure shares or provide file operations. Manual
Linux/iPhone SMB transfer is documented separately. Windows, Android, and
cross-network behavior still require device validation.

The repository's MIT license covers the root project; bundled components with
their own license files retain those notices. The Feedback Intelligence
application is not included in this snapshot because its publication license
is unresolved.

This snapshot omits private session records, historical migration archives,
local runtime state, secrets, and unfinished working-tree changes. A released
artifact, green CI, or real-device acceptance should be claimed only when
there is corresponding evidence.
