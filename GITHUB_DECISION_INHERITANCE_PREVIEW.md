# GitHub Decision Inheritance Preview

Status: read-only preview; no GitHub, README, release-candidate, or remote change

Compared state:

- protected public candidate: `e9692132c20285b348b261d3483c9ae04cfd362e`;
- completed reconciliation / feature base:
  `eac78b3b2375d22e751694ad3f04d9ca6f0ca3d0`;
- task query: `modify GitHub hero`;
- deterministic domains: `BRAND`, `DOCUMENTATION`, `GITHUB`, `PRODUCT`;
- deterministic surfaces: `brand`, `github`, `github-hero`, `readme`,
  `visual-identity`;
- project scope: `flowfoundry`.

No provider call was used. The preview uses the validated Decision Ledger,
deterministic resolver, current files, and `git show` against the immutable
candidate.

## Decisions injected for a GitHub hero task

| ID | Status | Semantic slot | Exact slot value / effect |
|---|---|---|---|
| `FF-PRODUCT-001` | BINDING | `official_name` | `FlowFoundry` |
| `FF-PRODUCT-002` | BINDING | `product_category` | `Local-first Adaptive AI Team Runtime` |
| `FF-PRODUCT-003` | BINDING | `primary_product_principle` | The smallest sufficient Agent or Team |
| `FF-PRODUCT-004` | BINDING | `primary_tagline` | `One goal. The smallest sufficient AI team.` |
| `FF-PRODUCT-005` | BINDING | `chinese_headline` | `你定目标，AI组队实现` |
| `FF-RELEASE-002` | BINDING | `release_authority_boundary` | Remote/release effects require explicit Human authorization |
| `FF-BRAND-002` | ADOPTED | `logo_direction` | Council Mark |
| `FF-BRAND-003` | ADOPTED | `identity_palette` | Midnight/Charles Blue, warm ivory, restrained ice-blue glass |
| `FF-BRAND-005` | ADOPTED | `github_hero_hierarchy` | Mark/name → tagline → category → mechanism → quick start → workflow/proof |
| `FF-BRAND-006` | ADOPTED | `campus_poster_hierarchy` | Chinese headline-led campus hierarchy |
| `FF-PRODUCT-007` | ADOPTED | `current_stage_label` | Local-first AI coordination layer |
| `FF-RELEASE-004` | ADOPTED | `github_product_surface` | Concise product surface rather than history archive |

`FF-PRODUCT-006` also matches and produces `OPEN_DECISION_WARNING` for the
unresolved canonical plain-Chinese explanation. It is not injected as
authority.

## Slot reconciliation

| Semantic slot | Protected `e969213` presentation | Reconciled current README | Preview result |
|---|---|---|---|
| `official_name` | `FlowFoundry` | `FlowFoundry` | Matches `FF-PRODUCT-001` |
| `primary_tagline` | `AI is moving from individual models to coordinated systems.` | `One goal. The smallest sufficient AI team.` | Candidate wording conflicts with `FF-PRODUCT-004`; reconciled wording matches |
| `product_category` | `local-first AI coordination layer` | `Local-first Adaptive AI Team Runtime` | Candidate wording conflicts with `FF-PRODUCT-002`; reconciled wording matches |
| `current_stage_label` | Used in the category position | Current Alpha described as a coordination layer below the category | Reconciled hierarchy preserves `FF-PRODUCT-007` without category replacement |
| `vision_narrative` | Used in the primary-tagline position | `AI is moving...` appears under `Why now?` | Correct separate advisory narrative slot (`FF-PRODUCT-008`) |
| `logo_direction` | Older `branding/logo.png` surface | Council Mark SVG and explicit alt text | Reconciled surface matches `FF-BRAND-002`; candidate does not |
| `release_authority_boundary` | No automatic remote authority claimed | README repeats no push/tag/release authority | Matches `FF-RELEASE-002` |

On the reconciled feature lineage there is no current identity-slot conflict.
Against the still-protected `e969213` presentation, a slot-aware task would
surface two conflicts instead of silently editing: the advisory launch
narrative occupying `primary_tagline`, and the adopted stage label occupying
`product_category`.

## Missing, separate, and superseded decisions

Missing from protected `e969213` but restored/preserved on the reconciliation
lineage:

- exact binding tagline (`FF-PRODUCT-004`);
- exact binding product category (`FF-PRODUCT-002`);
- explicit smallest-sufficient hero hierarchy (`FF-PRODUCT-003`,
  `FF-BRAND-005`);
- Human-approved Council Mark direction (`FF-BRAND-002`); and
- the DeepSeek-origin Chinese headline in product/brand guidance
  (`FF-PRODUCT-005`).

Legitimate separate slots:

- `AI is moving from individual models to coordinated systems.` remains useful
  as `vision_narrative`; it is not a replacement tagline;
- `Local-first AI coordination layer` remains the adopted current-stage label;
  it is not the official product category;
- the Chinese headline is binding brand/campus context but need not be forced
  into the English GitHub hero; its unresolved explanatory sentence remains
  open.

Legitimately superseded:

- `FF-BRAND-001` (`SYNTHESIS`) is excluded from active authority because the
  Human-approved Council Mark (`FF-BRAND-002`) supersedes it with explicit
  forward and reverse links. It remains discoverable provenance, not an
  instruction to reinstall the old mark.

## Input to the next GitHub reconciliation task

Use the protected candidate only through an explicitly authorized, isolated
GitHub/release reconciliation workflow. Before proposing copy, declare the
semantic slots being changed. Preserve `vision_narrative` and
`current_stage_label` in their separate positions, and treat any change to
`official_name`, `primary_tagline`, `product_category`, `logo_direction`, or
`release_authority_boundary` as a decision conflict requiring the appropriate
supersession process.

This preview grants no authority to edit, merge, push, tag, publish, or mutate
remote refs.
