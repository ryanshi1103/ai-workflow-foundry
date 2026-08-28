# License Decision

Date: 2026-08-23
Decision: **exclude Feedback Intelligence from the public candidate**

## Rationale

The Feedback Intelligence source has no approved public license, package
license metadata, or recorded copyright-holder authorization to apply a new
license. Release engineering cannot create that authority. The safe public
Alpha decision is therefore exclusion, not an inferred MIT grant.

This is an engineering release decision, not legal advice. It does not change
the ownership or license status of the excluded source.

## Applied boundary

The candidate excludes:

- `applications/feedback-intelligence-system/`;
- its component catalog manifest;
- its four executable capability-registry entries;
- its executable workflow contract;
- Feedback-specific package/test paths; and
- the Customer Intelligence demo and storyboard.

Public documentation may state that Feedback Intelligence was excluded pending
an owner-approved license. It must not claim that the implementation ships, is
MIT licensed through the repository root, or was tested as part of this
candidate.

The included FlowFoundry root package remains MIT licensed. Included components
retain their own license files and documented boundaries.

## Re-entry gate

Feedback Intelligence may return only after the owner records the copyright
holder, effective license, publication authority, package metadata, dependency
notice obligations, and whether source and binary distribution are both
authorized. Its tests and demo must then be rerun on a new candidate.

## Result

Candidate license ambiguity: **PASS by exclusion**.
