---
name: confera-audio-cleanup
description: Plan conservative, local audio cleanup through registered denoise capabilities. Use when an agent should recommend noise reduction for approved media without constructing shell commands, overwriting source audio, or starting a render.
---

Choose only capabilities supplied by the caller's trusted registry. Return an `EnhancementPlan` with evidence references and `human_review_required: true`. Do not construct commands, executable paths, arguments, or output paths. Never overwrite source audio or approve a render.
