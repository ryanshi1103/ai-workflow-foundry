---
name: confera-media-inspector
description: Create evidence-bound media inspection plans from controlled metadata. Use when an agent should select a registered ffprobe capability without reading arbitrary files, constructing commands, uploading original media, or making unsupported content claims.
---

Accept only controlled artifact references and metadata supplied by the caller. Select a registered inspection capability and return an `EnhancementPlan` with evidence references and `human_review_required: true`. Never construct commands or paths and never request original-media upload.
