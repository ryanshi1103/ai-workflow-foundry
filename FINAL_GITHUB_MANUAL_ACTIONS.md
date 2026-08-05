# Final GitHub Manual Actions

No action below was performed by this closure run.

## Blocking decisions first

- [ ] Select and record the Feedback license/boundary model.
- [ ] Confirm copyright ownership/authority and apply the choice to every listed
      file before public source visibility changes.
- [ ] Authorize a sanitized FlowFoundry publication branch/history treatment;
      keep `portfolio-migration` and its verified bundle intact.
- [ ] Review and approve the sanitized branch after full tests and privacy scan.

## Branch and CI operations

- [ ] Fresh-fetch each remote and re-check ahead/behind and protected bases.
- [ ] Push the approved Feedback feature branch after its license commit.
- [ ] Push only the approved sanitized FlowFoundry branch; never push the current
      session-bearing `portfolio-migration` branch.
- [ ] Confirm Huiying/MediaFlow target repositories are private, then push only
      the reviewed migration/integration branches.
- [ ] Never push or merge the session-only local
      `meeting-media-auto/master` tip.
- [ ] Wait for remote `tests.yml` and any repository-specific packaging/privacy
      jobs; local tests are not GitHub Actions results.
- [ ] Merge through protected PR workflows using merge commits, without
      squashing lineage merges.

## Repository identity and portfolio UI

- [ ] Rename the existing Feedback repository in place only after protected
      merge/CI; do not create a duplicate repository.
- [ ] Verify old URL redirects for clone, browser and API use.
- [ ] Push the profile branch only after canonical URLs are stable.
- [ ] Review rendered profile links and project claims.
- [ ] Set repository descriptions, topics and pins manually after all merges.
- [ ] Archive only repositories explicitly approved by the owner after redirect
      and dependency checks.

## Releases and private platform gates

- [ ] Generate Feedback dependency lock/SBOM/third-party notices before binary
      distribution.
- [ ] Generate the Windows dependency/hash lock on the approved Windows build
      host; do not invent hashes on Linux.
- [ ] Run Windows install/upgrade/rollback/uninstall and signing verification.
- [ ] Verify Android signing-key custody/backup and run Android 8 and 15+ real
      device acceptance tests.
- [ ] Run authorized provider and real-media tests only in private environments;
      do not attach their inputs/logs to public issues or releases.
- [ ] Create GitHub releases only after CI, license, SBOM, signing and artifact
      provenance gates pass.
- [ ] Deploy last with approved production credentials; this run did not access
      credentials or deploy.
