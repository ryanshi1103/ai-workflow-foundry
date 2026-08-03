---
name: confera-timeline-review
description: Review a media timeline and propose a new candidate revision. Use when an agent should identify pacing, ordering, overlap, or duration issues without mutating the current timeline, preserving an old export approval, approving changes, or rendering media.
---

Use supplied timeline metadata and controlled probe evidence only. Return a `TimelineRevisionCandidate`. Never mutate the current revision, approve, or export. Require the application layer to create an immutable revision, invalidate stale export approval, and request human review.
