---
name: confera-quality-review
description: Produce a read-only final media quality report from controlled proxy evidence and metadata. Use when an agent should identify technical risks without modifying media, approving a revision, finalizing artifacts, or starting export.
---

Review only evidence and metadata supplied by the caller. Return a `QualityReview` with `evidence_refs`. Distinguish measured facts from recommendations. Never modify final media, change review state, approve, call a finalizer, or start export.
