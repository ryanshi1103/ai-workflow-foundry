# Security Policy

## Supported status

FlowFoundry is currently an Alpha developer preview. No production-supported
release line exists yet. Security fixes target the latest owner-approved
publication candidate after reproducing the issue in a safe local environment.

## Reporting a vulnerability

Do not open a public issue for a vulnerability, credential exposure, private
content exposure, unsafe path/command behavior, or a way to bypass permission,
approval, workspace, provider, or cancellation controls.

Use GitHub private vulnerability reporting if the repository offers it. Otherwise,
contact the repository owner through a private, verified channel shown on the
GitHub profile. Share only the minimum information needed to establish impact;
do not transmit secrets or private datasets.

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

See [current status](docs/CURRENT_STATUS.md) for maturity boundaries.

## Publication boundary

Do not merge private session history, credentials, real customer data, or
unreviewed historical branches into the public repository. Report a suspected
exposure privately using the channel above.

## Disclosure process

Maintainers should acknowledge a report, establish a private reproduction,
assess affected versions and data boundaries, prepare a fix and regression test,
and coordinate disclosure. Release or remote remediation happens only after
owner review and any required credential/privacy response.
