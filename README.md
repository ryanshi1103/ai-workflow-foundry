<p align="center">
  <img src="branding/logo.png" width="128" alt="Confera Media Skills logo">
</p>

# Confera Media Skills

Ten safety-bounded AI skills for media review and editing workflows. They let an
agent inspect evidence and propose candidates while the application—not the
model—keeps control of files, commands, approvals, finalization, and export.

中文说明：这是一组用于照片、音频、字幕、分镜和时间线的 AI Skill。它们的
核心不是“让 AI 自动剪片”，而是把 AI 限制为“提出有证据的候选方案”；原素材、
工具执行、审核和导出仍由受信任程序及人工控制。

## The core idea

```text
controlled evidence -> bounded skill -> schema-valid candidate
                                      -> human review
trusted registry -> generated execution details -> validated artifact
                                      -> separate export approval
```

A skill cannot silently turn a suggestion into a destructive action. Every
manifest declares allowed and forbidden tools, privacy/network policy, output
schema, runtime limit, provenance, and `human_review_required`.

## What each skill does

| Skill | Plain-language purpose |
|---|---|
| `confera-media-inspector` | Plans safe metadata inspection without opening arbitrary files. |
| `confera-photo-polish` | Suggests restrained photo corrections without changing faces or originals. |
| `confera-audio-cleanup` | Plans local denoise choices without constructing shell commands. |
| `confera-caption-layout` | Recommends readable subtitle layout without approving the transcript. |
| `confera-story-editor` | Proposes an evidence-linked storyboard revision. |
| `confera-timeline-review` | Reviews pacing and ordering, then proposes a new immutable revision. |
| `confera-narration-draft` | Drafts evidence-linked narration without TTS or voice imitation. |
| `confera-ffmpeg-render` | Maps reviewed intent to registered capabilities, never raw commands. |
| `confera-quality-review` | Produces a read-only technical quality report. |
| `confera-chatcut-exchange` | Describes a consented manual exchange package without web automation. |

The seven files in `agents/` are companion Claude subagent profiles used by the
original Confera application. The `manifest.json` beside each skill documents
the stronger application-level contract. The portable `SKILL.md` files keep
only standard `name` and `description` frontmatter.

## Install for inspection or explicit use

Copy one or more folders under `skills/` into your Codex skills directory. For
example:

```bash
cp -R skills/confera-story-editor ~/.codex/skills/
```

These skills intentionally produce plans and candidates. ToolRegistry,
immutable revisions, schema validation, and export approval are application
responsibilities; copying a skill does not install the full Confera runtime.

## Validate

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q tests
```

The tests check names, standard frontmatter, manifest/folder consistency,
human-review gates, network/privacy declarations, and forbidden execution
capabilities.

## Provenance

Nine skills are project-native. `confera-ffmpeg-render` is a non-executable
safety wrapper derived from the planning methodology of
`ychoi-kr/claude-ffmpeg-skill` at commit
`b88cb5ce08337ab55c66c67674100b8de29cf232`, licensed under MIT. No upstream
installer or executable code is bundled here.

## License

MIT.
