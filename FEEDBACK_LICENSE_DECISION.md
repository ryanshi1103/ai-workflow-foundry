# Feedback Intelligence License Decision

Status: **HUMAN_DECISION_REQUIRED**

Release classification: **READY_FOR_REVIEW_PENDING_LICENSE**, subject also to
the separate FlowFoundry history blocker

This document is engineering decision support, not legal advice. Git authorship
alone does not establish ownership of every copyright interest. The owner must
confirm rights and select exactly one publication model before any public
FlowFoundry or standalone Feedback push.

## Current state

- The standalone Feedback tip `93b646baf6c92437b97abc0e13d6b6e53b8811eb`
  has no `LICENSE`, `COPYING`, or `NOTICE` in its reachable tree or recorded
  history.
- Its `pyproject.toml` has no project license metadata, license files, or license
  classifier.
- Its README and the FlowFoundry catalog describe the application as learning
  and internal use and explicitly avoid asserting an open-source license.
- The FlowFoundry root is MIT and does not currently state that
  `applications/feedback-intelligence-system/` is excluded. The same code tree
  therefore has an ambiguous boundary when bundled into the monorepo.
- The canonical and bundled source trees match; the excluded archive history
  was not connected. No SQLite user database, export, cache, session, or secret
  is tracked by the canonical Feedback tip.
- The public repository identity remains `feedback-analysis-system`; no rename
  has occurred.

## Direct dependency license inventory

The current direct declarations are permissively licensed according to their
recorded upstream project metadata:

| Dependency | Recorded upstream license |
|---|---|
| Streamlit | Apache-2.0 |
| SQLAlchemy | MIT |
| Pydantic | MIT |
| openai-python | Apache-2.0 |
| pandas | BSD-3-Clause |
| Plotly.py | MIT |
| HTTPX | BSD-3-Clause |
| apify-client | Apache-2.0 |
| APScheduler | MIT |
| python-dotenv | BSD-3-Clause |
| Tenacity | Apache-2.0 |
| pytest / pytest-cov / Ruff | MIT |

No direct strong-copyleft dependency was identified. This is not a complete
binary-distribution audit: dependencies use lower bounds, and the project has no
lock file, SBOM, or transitive third-party notice inventory. Create those before
shipping a wheel, container, desktop bundle, or formal release artifact.

## Options and engineering impact

### MIT

- Add an MIT `LICENSE` to the standalone application.
- Add SPDX-compatible project metadata and a license classifier.
- Replace internal-use language in the standalone and bundled README/catalog.
- The bundled application can then align with the FlowFoundry root MIT license.
- Preserve required dependency notices in binary distributions.

### Apache-2.0

- Add Apache-2.0 `LICENSE` and an appropriate `NOTICE`.
- Update package metadata, README, catalog, and copyright/notice surfaces.
- Document the application as an independently licensed subtree in FlowFoundry;
  the root MIT file alone is insufficient to express that boundary.
- Preserve Apache/BSD notices and complete patent/notice review for releases.

### All rights reserved / proprietary

- Add explicit proprietary terms instead of relying on the absence of a license.
- State clearly that the FlowFoundry root MIT license does not cover the
  Feedback subtree.
- Update root README, application README, catalog, packaging and distribution
  configuration so the subtree is not described or shipped as open source.
- Keep the source on a private or access-controlled remote unless counsel/owner
  approves source visibility under those terms.

### Do not publish the source yet

- Exclude the application subtree from a public sanitized FlowFoundry candidate.
- Keep the standalone migration branch local/private.
- Continue internal review until ownership, license, dependency lock/SBOM, and
  distribution obligations are resolved.
- Public documentation may describe the architecture without publishing the
  restricted implementation.

## The one required owner decision

Select one of the four models above and record:

- decision owner and approval reference;
- effective commit and date;
- copyright holder and year;
- whether the FlowFoundry root MIT license covers or excludes the subtree;
- whether source visibility and binary distribution are both authorized.

Until that selection is applied, Feedback is not
`READY_FOR_PUBLIC_RELEASE` and no public push should include the bundled or
standalone source.

## Files to synchronize after the decision

- standalone application `LICENSE` and, when applicable, `NOTICE`;
- `applications/feedback-intelligence-system/pyproject.toml`;
- standalone and bundled application README usage/license sections;
- `catalog/feedback-intelligence-system.json`;
- FlowFoundry root README and license exception/boundary text when the chosen
  license differs from root MIT;
- lock/constraints, SBOM and third-party notices before artifact distribution.
