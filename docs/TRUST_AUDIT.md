# Product Trust Audit

Audit date: **2026-08-25**
Scope: README, release/status reports, public product and mobile documents,
demos, launch materials, contribution guidance, and security references in the
local final-candidate branch.

## Decision

**Documentation boundary: PASS with warnings. Public launch trust gate:
BLOCKED.**

The public story consistently presents FlowFoundry as a local-first AI
coordination layer and separates current, designed, and future work. The launch
is still blocked because actual demo media, published-artifact installs, owner
candidate approval, final CI/security evidence, and external validation are not
complete.

This audit evaluates claims and evidence. It is not a penetration test, legal
opinion, security certification, or release authorization.

## Evidence hierarchy

When two documents disagree, use the following order:

1. executable behavior at the exact candidate SHA;
2. current-SHA test and clean-install output;
3. source and configuration at that SHA;
4. current release/status reports tied to that SHA;
5. diagrams and design documents;
6. roadmap, examples, and marketing copy.

Historical evidence cannot prove a later candidate. A rendered preview cannot
prove runtime behavior. A simulated persona cannot prove external adoption.

## Capability-boundary audit

| Boundary | Public treatment | Result | Evidence / action |
|---|---|---|---|
| AI coordination runtime | **Implemented / Alpha** | PASS | README and current-status materials describe planning, routing, execution, review, approval, recovery, evidence, and isolation as current capabilities |
| Provider coordination | **Implemented with bounded modes and limitations** | PASS WITH WARNING | Demos must show fake/offline versus live mode visibly; provider availability must not be generalized beyond tested adapters |
| Routing optimization, quality/cost selection | **Experimental** | PASS | Product materials do not claim an optimal or universally best selection system |
| Mobile Command Center and PWA | **Designed, not implemented** | PASS | Mobile documents and README label the work as design/future prototype scope |
| Personal memory and personalized intelligence | **Future** | PASS | Roadmaps discuss intended direction without claiming a shipped memory system |
| Personal AI OS | **Future vision** | PASS | Separated from the current coordination layer and framed as staged work |
| Autonomous publishing or human replacement | **Not claimed / outside boundary** | PASS | Human approval is preserved for side effects; launch materials reject replacement claims |

## Claim scan

A case-insensitive scan of public Markdown for `AGI`, `AI employee`,
`autonomous replacement`, positive claims that a mobile app exists, and positive
claims that personal memory exists found no affirmative product claim.

Matches are limited to:

- explicit prohibitions and limitations;
- audit criteria;
- future-stage labels;
- the name of AutoGen in competitive material;
- unrelated technical words such as packaging or pagination.

Re-run the claim scan against the final release tree because a passing
local candidate does not guarantee future copy remains aligned. Record
the final result in this audit or the Alpha Release Checklist rather than
creating another public-message audit.

## Trust findings

### T1 — Product category and boundaries

**Result: PASS**

The first README screen explains the coordination problem and distinguishes a
goal-first system from choosing a model. Shipped, designed, and future stages
are visible, and the Developer Preview label reduces the risk that a visitor
mistakes the Alpha for a finished hosted service.

### T2 — AI capability clarity

**Result: PASS WITH WARNING**

Current documentation describes roles, planning, review, approval, and recovery
as workflow capabilities, not proof of model intelligence. The risk is in
future media: narration can easily imply that named providers ran live even
when deterministic fake-provider mode produced the capture.

**Required action:** Put the execution mode on screen, in the caption, and in
the asset manifest.

### T3 — Screenshot and demo integrity

**Result: BLOCKED**

The repository has scripts, plans, and visual requirements, but the required
flagship video, social clip, real README screenshots, terminal GIF, and clean
installation recording are not verified as published assets. Existing rendered
launcher previews are explanatory previews, not runtime evidence.

**Required action:** Complete [DEMO_ASSET_CHECKLIST.md](DEMO_ASSET_CHECKLIST.md)
against the exact approved candidate. No placeholder or mockup can satisfy this
gate.

### T4 — Fake versus live provider state

**Result: PASS IN DOCUMENTATION; UNVERIFIED IN MEDIA**

Demo instructions use deterministic/offline or fake-provider behavior and
require labels. That is appropriate for a reproducible first experience, but a
viewer must never infer that an external provider was called or reviewed the
project when it did not.

**Required action:** Verify every public frame, caption, and narration statement
after recording.

### T5 — Installation and artifact identity

**Result: BLOCKED**

Source-checkout validation and isolated local evidence exist, but the final
public artifact, tag, hashes, and external clean-environment installs do not.
The exact approved candidate after documentation integration is also not yet
known.

**Required action:** Build from the approved SHA, verify hashes and provenance,
and obtain at least two independent clean installs using only public
instructions.

### T6 — Security and permission story

**Result: PARTIAL / BLOCKED FOR RELEASE**

The project documents local execution, approval boundaries, isolation, and
private security reporting. This is a strong design and documentation base, not
a certification. Final candidate security checks and the release-day review
still need recorded evidence.

**Required action:** Run current-SHA security checks, verify the private report
path, review artifact contents, and publish known limitations.

### T7 — Documentation consistency

**Result: PASS WITH DRIFT RISK**

The narrative is consistent, but many overlapping launch, roadmap, mobile, and
growth documents can drift. Internal `.ai/PROJECT_STATE.md` reflects an earlier
verification point and must not be used as current release evidence when it
differs from Git and executable checks.

**Required action:** Treat `docs/README.md` as the public index; designate a
canonical document for each topic; re-run link/version/SHA checks before
release; archive or mark superseded planning documents after launch.

### T8 — Adoption and community proof

**Result: BLOCKED**

Personas, plans, and good-first-issue drafts are useful preparation but do not
show that strangers can install, activate, return, or contribute.

**Required action:** Complete the first-10 observed cohort before broad
promotion and use [FIRST_100_USERS_EXPERIMENT.md](FIRST_100_USERS_EXPERIMENT.md)
for expansion.

## Public trust gate

| Gate | Current state |
|---|---|
| Implemented / Experimental / Future separation | READY |
| No exaggerated or replacement claims | READY |
| Fake/live state explained in documents | READY |
| Verified final candidate SHA and clean tree | BLOCKED |
| Final CI and security checks | BLOCKED |
| Published artifact, hashes, and provenance | BLOCKED |
| Two independent external installs | BLOCKED |
| Actual demo assets with manifests | BLOCKED |
| First outside-user activation evidence | BLOCKED |
| Maintainer/security response operation tested | BLOCKED |

## Highest-risk ways trust could be lost

1. Publishing polished mockups as product output.
2. Saying Claude, Codex, or DeepSeek performed a live task when the run used
   deterministic fake providers.
3. changing the candidate after recording without rebuilding the evidence;
4. asking users to install before artifact identity and rollback are clear;
5. exposing private paths, repository names, prompts, or credentials in media;
6. promoting mobile, memory, or autonomous behavior as current;
7. inviting contributors without a maintainer able to respond.

## Audit conclusion

FlowFoundry's public message is disciplined and suitable for a controlled
external-validation cohort. Trust for an open launch is not yet evidenced. The
next work is operational: lock the candidate, run final checks, publish and
independently install the artifact, capture real media, and observe first users.
