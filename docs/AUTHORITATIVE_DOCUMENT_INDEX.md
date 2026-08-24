# Authoritative Document Index

Status: **canonical documentation map for the Alpha candidate**
Last audited: **2026-08-25**

## Precedence rule

When public documents disagree, use this order:

1. executable behavior and tests at the exact approved candidate SHA;
2. the canonical document named below;
3. supporting evidence documents;
4. design documents and future strategy;
5. historical reports and drafts.

An older test report cannot prove a later SHA. A roadmap cannot override the
current capability boundary. A recording or screenshot cannot prove behavior
unless its asset manifest identifies the same candidate.

## Five primary documents

| Topic | Canonical document | Purpose | Supporting documents |
|---|---|---|---|
| Product landing | [README.md](../README.md) | Ten-second definition, current boundary, first install, first successful workflow | [Current Status](CURRENT_STATUS.md), [Alpha User Guide](ALPHA_USER_GUIDE.md) |
| Architecture | [FlowFoundry Product Architecture](FLOWFOUNDRY_PRODUCT_ARCHITECTURE.md) | Canonical product layers, trust boundaries, and current/future separation | [Technical Architecture](ARCHITECTURE.md), [Multi-Agent Security Model](../MULTI_AGENT_SECURITY_MODEL.md) |
| Roadmap | [Product Roadmap](PRODUCT_ROADMAP.md) | Current AI Coordination Layer and future Personal AI Assistant / Personal AI OS stages | [Personal AI OS Strategy](PERSONAL_AI_OS_STRATEGY.md), mobile design documents |
| Candidate and Alpha release | [Final Candidate Checklist](FINAL_CANDIDATE_CHECKLIST.md) for local assembly; [Alpha Release Checklist](ALPHA_RELEASE_CHECKLIST.md) for publication | Exact candidate identity and every mandatory GO/NO-GO gate | [Final Release Status](FINAL_RELEASE_STATUS.md), [Final Candidate Report](../FINAL_CANDIDATE_REPORT.md), [Release Day Runbook](RELEASE_DAY_RUNBOOK.md) |
| Security | [Security Policy](../SECURITY.md) | Supported versions, trust boundaries, private vulnerability reporting, and disclosure expectations | [Multi-Agent Security Model](../MULTI_AGENT_SECURITY_MODEL.md), [Trust Audit](TRUST_AUDIT.md), [Alpha Limitations](LIMITATIONS.md) |

The Final Candidate Checklist is authoritative for local candidate assembly.
The Alpha Release Checklist is authoritative for later public-release gates.
Neither document authorizes a push, merge, tag, GitHub Release, deployment, or
announcement.

## Canonical documents by task

| User need | Canonical document | Boundary |
|---|---|---|
| What is shipped now? | [Current Status](CURRENT_STATUS.md) | Capability and evidence summary |
| How do I install and reach first value? | [Alpha User Guide](ALPHA_USER_GUIDE.md) | External Alpha journey |
| Exact installation mechanics | [Installation](INSTALLATION.md) | Supported environments, build behavior, expected output |
| Installation failed | [Troubleshooting](TROUBLESHOOTING.md) | Safe diagnostics and failure report |
| Common product questions | [FAQ](FAQ.md) | New-user explanations |
| Known limitations | [Limitations](LIMITATIONS.md) | Current non-capabilities and operational risks |
| What is the first demo? | [GitHub Release Assistant](demos/github-release-assistant.md) | Canonical executable demo truth |
| How is the demo recorded? | [Demo Recording Checklist](DEMO_RECORDING_CHECKLIST.md) | Capture and review procedure |
| Which assets are release evidence? | [Demo Asset Checklist](DEMO_ASSET_CHECKLIST.md) | Asset provenance and publication status |
| What blocks launch? | [Launch Scorecard](LAUNCH_SCORECARD.md) | Current numeric score and zero-blocker rule |
| What exactly is in this local candidate? | [Final Candidate Report](../FINAL_CANDIDATE_REPORT.md) | Included/excluded files, checks, and remaining blockers |
| What public release copy is approved? | [Launch Package](LAUNCH_PACKAGE.md) | Draft GitHub Release copy; never an authority grant |
| How should contributors start? | [Contributing](CONTRIBUTING.md) | Contributor setup and policy |
| Which starter tasks are prepared? | [Good First Issues](GOOD_FIRST_ISSUES.md) | Five maintained issue proposals |
| How are external users measured? | [First 100 Users Experiment](FIRST_100_USERS_EXPERIMENT.md) | Consented activation and retention protocol |
| How is trust assessed? | [Trust Audit](TRUST_AUDIT.md) | Claim, screenshot, provider-mode, and evidence audit |
| How is FlowFoundry positioned? | [Final Competitive Positioning](COMPETITIVE_POSITIONING_FINAL.md) | Public category comparison without replacement claims |

## Supporting technical documents

- [Technical Architecture](ARCHITECTURE.md) explains module-level implementation.
- [Sanitization Report](SANITIZATION_REPORT.md) records the candidate history
  boundary.
- [License Decision](LICENSE_DECISION.md) records why Feedback Intelligence is
  excluded.
- [Launcher layout evidence](launcher-layout-examples.md) covers the terminal
  launcher contract.

Supporting documents may add detail but must not broaden the public capability
claim beyond the canonical README and Current Status.

## Designed and future documents

The following documents are retained because they describe distinct design
boundaries. They are not evidence of shipped Alpha behavior:

- [Mobile AI Command Center](MOBILE_AI_COMMAND_CENTER.md)
- [Mobile PWA MVP](MOBILE_PWA_MVP.md)
- [Mobile Security Model](MOBILE_SECURITY_MODEL.md)
- [Remote Agent Architecture](REMOTE_AGENT_ARCHITECTURE.md)
- [Personal AI OS Strategy](PERSONAL_AI_OS_STRATEGY.md)
- [Personal AI Manager](PERSONAL_AI_MANAGER.md)

Every public link to these documents must preserve the **Designed** or
**Future** label.

## Consolidation performed

The 2026-08-25 audit removed the following superseded documents:

| Removed document(s) | Replacement |
|---|---|
| Root `RELEASE_CHECKLIST.md`, root `RELEASE_DAY_CHECKLIST.md`, `LAUNCH_DECISION_MATRIX.md`, `OPEN_SOURCE_LAUNCH.md`, `PUBLIC_RELEASE_PLAN.md` | [Alpha Release Checklist](ALPHA_RELEASE_CHECKLIST.md) and [Release Day Runbook](RELEASE_DAY_RUNBOOK.md) |
| `ROADMAP.md`, `PERSONAL_AI_OS_ROADMAP.md` | [Product Roadmap](PRODUCT_ROADMAP.md) and [Personal AI OS Strategy](PERSONAL_AI_OS_STRATEGY.md) |
| `DEMO_RECORDING_PLAN.md`, `DEMO_SCRIPT.md` | [GitHub Release Assistant](demos/github-release-assistant.md), [Demo Recording Checklist](DEMO_RECORDING_CHECKLIST.md), and [Demo Asset Checklist](DEMO_ASSET_CHECKLIST.md) |
| `FIRST_100_USERS_PLAN.md` | [First 100 Users Experiment](FIRST_100_USERS_EXPERIMENT.md) |
| `FIRST_USER_EXPERIENCE_AUDIT.md`, `GITHUB_FIRST_IMPRESSION_REVIEW.md`, `MATURITY_ASSESSMENT.md` | [Final Product Review](PRODUCT_FINAL_REVIEW.md) and [Launch Scorecard](LAUNCH_SCORECARD.md) |
| `PUBLIC_MESSAGE_AUDIT.md` | [Trust Audit](TRUST_AUDIT.md) |
| `GITHUB_GROWTH_PLAN.md`, `MARKETING_PLAN.md`, `OPEN_SOURCE_GROWTH_STRATEGY.md` | [GitHub Trusted-user Strategy](GITHUB_STAR_STRATEGY.md), [Community Operating Model](COMMUNITY_OPERATING_MODEL.md), and [First 100 Users Experiment](FIRST_100_USERS_EXPERIMENT.md) |
| `LAUNCH_ANNOUNCEMENT.md` | [Launch Package](LAUNCH_PACKAGE.md) |
| `PROJECT-PATTERN-AUDIT.md`, `PRODUCT-LINES.md` | Removed from the Alpha surface because they described unrelated/private portfolio lines; one contained an outdated Feedback inclusion claim |
| `REPOSITORY_STRUCTURE.md` | Removed because it was an unexecuted directory/SDK reorganization proposal, not current product architecture |

No source/runtime document or implementation was removed.

## Maintenance rules

- Update the canonical document first; supporting documents link to it.
- Put a date and exact SHA beside release evidence.
- Do not copy release gates into a new plan; link to the Alpha checklist.
- Do not create another roadmap. Extend the Product Roadmap only after product
  approval.
- Move point-in-time findings into the current scorecard or release status, then
  remove the obsolete audit from the public index.
- Run relative-link, version, SHA, and forbidden-claim checks before every
  release candidate.
- Review this index whenever a canonical document is renamed or removed.
