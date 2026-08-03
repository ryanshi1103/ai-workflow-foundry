---
name: confera-ffmpeg-render
description: Translate reviewed edit intent into registered FFmpeg capability choices. Use when an agent should produce a non-executable render plan while a trusted application layer retains control of commands, paths, validation, finalization, and export approval.
---

Choose only registered `ffmpeg` or `ffprobe` capabilities. Return an `EnhancementPlan`. Do not emit commands, executable paths, arguments, `filter_complex`, output paths, or final exports. Let the trusted tool registry generate execution details and require human review.
