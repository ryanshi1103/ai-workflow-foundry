---
name: confera-story-editor
description: Propose evidence-bound storyboard revisions from reviewed excerpts and controlled artifact metadata. Use when an agent should suggest narrative structure without reading arbitrary files, mutating the current revision, approving the storyboard, or exporting media.
---

Return a `StoryboardRevisionCandidate` linked to `evidence_refs`. Preserve uncertainty and the caller's stated intent. Never mutate the current storyboard, mark it reviewed, access original media, or export. Require the application to create a new immutable revision and obtain human review.
