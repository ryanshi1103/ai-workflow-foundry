# Security Policy

## Supported status

FlowFoundry is currently an Alpha developer preview. No production-supported
release line exists yet. Security fixes target the latest owner-approved
publication candidate after reproducing the issue in a safe local environment.

## Reporting a vulnerability

Do not open a public issue for a vulnerability, credential exposure, private
content exposure, unsafe path/command behavior, or a way to bypass permission,
approval, workspace, provider, or cancellation controls.

Use GitHub private vulnerability reporting once it is enabled on the approved
public repository. Until then, contact the repository owner through a private,
verified channel shown on the GitHub profile. Share only the minimum information
needed to establish impact; do not transmit secrets or private datasets.

Include when safe:

- affected commit/version and platform;
- component and execution mode;
- minimal reproduction using synthetic data;
- expected versus actual trust boundary;
- whether network, credentials, user data, or irreversible actions are involved;
- suggested containment, if known.

## Trust boundaries

Model output is untrusted. Trusted code owns path resolution, command
construction, credential access, side effects, validation, and approval state.
Real-provider calls require explicit opt-in. Git writer isolation does not
replace an OS/container sandbox, and tool exposure is not a universal network
or filesystem boundary.

See [Multi-Agent Security Model](MULTI_AGENT_SECURITY_MODEL.md) and
[Current Status](docs/CURRENT_STATUS.md).

## Preserved historical incident

An older migration history has a documented remote-exposure incident involving
historical session paths. This candidate is a separate new-root allowlist
snapshot and does not descend from that history. Do not republish or merge the
preserved history into this candidate. Remote ref changes, visibility changes,
credential response, and hosting-provider requests still require explicit owner
authorization and the controlled private runbooks.

Do not include forbidden content, exact retrieval identifiers, or credentials in
a public report.

## Disclosure process

Maintainers should acknowledge a report, establish a private reproduction,
assess affected versions and data boundaries, prepare a fix and regression test,
and coordinate disclosure. Release or remote remediation happens only after
owner review and any required credential/privacy response.
