---
name: confera-caption-layout
description: Recommend readable caption layout from supplied caption segments. Use when an agent should propose line breaks, timing presentation, or placement without changing transcript review state or embedding subtitles into a final export.
---

Use only caption segments supplied by the caller. Return a `CaptionRecommendation`. Preserve wording and timing evidence. Never mark a transcript reviewed, mutate the current transcript, or embed subtitles into an export. Require human review.
