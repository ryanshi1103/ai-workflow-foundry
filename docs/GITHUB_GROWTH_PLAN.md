# FlowFoundry GitHub growth plan

## Objective

Build a small, technically engaged contributor community around FlowFoundry as
an **AI coordination layer**. The first launch should optimize for successful
installs, useful technical feedback, and repeat contributors—not raw impressions
or stars.

This plan authorizes no post, tag, push, release, or outreach. Execute it only
after the release-day gates are signed off.

## Launch guardrails

- Link every public post to the immutable `v0.2.0-alpha.1` release or tag, not a
  working branch.
- Lead with the deterministic offline demo and the problem it solves.
- Keep implemented, experimental, and planned capabilities visibly separate.
- Say “AI coordination layer”; do not use AGI, human-replacement, or autonomous-
  everything positioning.
- Do not imply that fake-provider output is live-model evidence.
- Do not publish while privacy containment, exact-SHA CI, artifact verification,
  anonymous-clone verification, or license gates remain open.
- Do not solicit votes, stars, reposts, or artificial engagement.

## Launch sequence

### Before launch

1. Publish the reviewed tag and GitHub Release from the approved SHA.
2. Attach the wheel, sdist, SHA-256 manifest, notices/SBOM if required, demo
   transcript, and captioned recording.
3. Verify the release from an anonymous clean clone and a clean Python 3.11
   environment.
4. Seed three public issues with clear acceptance criteria: one documentation
   issue, one deterministic fixture issue, and one bounded provider/runtime
   issue. Label only genuinely small work as `good first issue`.
5. Assign a named maintainer and response window for launch-week issues,
   security reports, and discussions.

GitHub releases are tag-based and can package release notes and binary assets;
the public release should therefore be the canonical launch destination. See
[GitHub's release documentation](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases).

### Launch day

1. Publish the GitHub Release and verify every asset from a separate download.
2. Publish the repository announcement using
   [LAUNCH_ANNOUNCEMENT.md](LAUNCH_ANNOUNCEMENT.md).
3. Publish the captioned 90-second demo.
4. Open a launch discussion with three questions: What failed during install?
   Was the routing decision understandable? Which boundary should be improved
   first?
5. Post to one external community at a time. Stay available to answer questions
   before opening the next channel.

### First two weeks

- Triage reproducible failures before feature requests.
- Publish a short daily launch log for the first three days, then a weekly
  summary of fixes, rejected claims, and open questions.
- Convert repeated confusion into documentation or fixtures.
- Thank contributors in release notes when their work ships; do not promise
  deadlines that do not have an assigned maintainer.
- Review metrics after 14 days and decide whether the next Alpha should focus on
  install reliability, provider evidence, workflow contracts, or operator UX.

## First GitHub announcement

### Release title

**FlowFoundry v0.2.0-alpha.1 — local-first AI coordination, with an offline demo**

### Short repository post

> FlowFoundry is an open-source AI coordination layer for bounded workflows.
> This first Alpha can plan a minimum sufficient agent path, run deterministic
> offline builder/reviewer workflows, preserve review and recovery evidence, and
> isolate write-capable tasks in managed Git worktrees.
>
> It is a developer preview: real-provider parity, personal memory, broad local-
> model support, and a polished personal-manager interface are not complete.
>
> Start with the 90-second Personal AI Manager demo, then tell us where install,
> routing clarity, permissions, or recovery breaks for you.

Use the longer [launch announcement](LAUNCH_ANNOUNCEMENT.md) as the GitHub
Release body. Mark the release as a pre-release.

## Hacker News strategy

Use **Show HN: FlowFoundry – a local-first coordination layer for bounded AI workflows**.
Submit the repository or exact release URL, not a landing page. Post only when a
new user can clone, install, and run the offline demo without credentials or a
signup. This follows the official [Show HN guidance](https://news.ycombinator.com/showhn.html),
which asks for something people can try and explicitly prohibits soliciting
votes.

The maintainer should write the first comment in their own voice; do not paste
AI-generated or AI-edited comment text. Cover:

- the coordination problem that motivated the project;
- why minimum-path planning and fake-provider fixtures were chosen;
- one surprising engineering tradeoff, such as durable cancellation or Git
  writer isolation;
- the exact Alpha limitations; and
- two narrow questions for technical feedback.

Remain present for the discussion, answer failures directly, and avoid debating
the project's popularity or the voting. The broader
[HN guidelines](https://news.ycombinator.com/newsguidelines.html) favor original
sources, curiosity, and human conversation over promotion.

## Reddit strategy

Treat candidate communities as audiences to evaluate, not a broadcast list:

- `r/opensource` for governance, licensing, and contributor experience;
- `r/Python` for packaging, API, and test feedback;
- `r/commandline` for the terminal launcher and operator experience; and
- a relevant project-showcase community only when its current rules explicitly
  allow self-promotion.

Before each post, read the current community rules and recent moderator guidance.
Ask moderators first if the policy is ambiguous. Publish one tailored technical
post, disclose that the poster maintains the project, and ask a community-
specific question. Do not paste the same copy across communities, mass-message
users, or ask for votes. Reddit notes that promotional content is governed by
community-specific policies and may be limited by a 10% self-promotion rule;
see its current [spam guidance](https://support.reddithelp.com/hc/en-us/articles/28012014962580-How-do-I-keep-spam-out-of-my-community).

Suggested post structure:

1. one-sentence problem and maintainer disclosure;
2. a 20–30 second clip or one legible image;
3. three implemented capabilities;
4. two explicit limitations;
5. exact offline reproduction steps; and
6. one focused request for critique.

## X/Twitter strategy

Publish a compact four-post thread after the GitHub release is live:

1. problem: AI tasks need coordination, controls, validation, and recovery;
2. demo clip: goal → minimum reviewed path → offline report;
3. engineering detail: explicit permissions, fake-by-default providers, and Git
   isolation; and
4. limitation plus invitation: Alpha boundaries and the most useful issue areas.

Use captions on video and alt text on the image. Link only once, to the exact
release. Avoid engagement bait, model-versus-model claims, and unsupported
performance comparisons. Reply with reproducible commands when questions are
technical.

## Developer community strategy

- Make GitHub Issues and Discussions the source of truth for public technical
  feedback; do not fragment decisions across private chat rooms.
- Maintain a small issue ladder: documentation-only, fixture/test, bounded bug,
  and design-discussion work.
- Publish contributor setup commands and expected results before asking for
  contributions.
- Hold architecture discussions before changes to permissions, persisted state,
  provider interfaces, personal context, or public contracts.
- Convert the first successful outside contribution into an annotated example
  of the expected issue → test → review path.
- Offer a recurring public triage session only if a maintainer and schedule are
  actually committed; otherwise use an asynchronous weekly update.
- Track contributor retention and response quality without collecting personal
  telemetry from the runtime.

## Measures of healthy growth

Review these at days 2, 7, 14, and 30:

- clean-install and offline-demo success rate from voluntary reports;
- number of reproducible issues versus vague reports;
- median first maintainer response time;
- documentation changes caused by user confusion;
- first-time and repeat contributors;
- accepted versus declined design proposals, with reasons; and
- unresolved security, privacy, license, or release-integrity reports.

Stars, views, and follower counts are context, not success criteria. Pause
promotion when maintainers cannot respond safely or a release-integrity issue is
open.
