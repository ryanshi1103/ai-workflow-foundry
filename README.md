<p align="center">
  <img src="branding/logo.png" width="144" alt="FlowFoundry AI logo">
</p>

<h1 align="center">FlowFoundry AI</h1>
<p align="center"><strong>Local-first foundations for AI work that stays reviewable, recoverable, and reusable.</strong></p>

FlowFoundry AI is an open foundation for designing and operating bounded AI
workflows. It combines a real project/workspace runtime with a small, validated
catalog contract for workflow packs and reference applications. The product is
broader than one phone, one model, or one content type: it focuses on the
lifecycle shared by useful AI work.

中文说明：FlowFoundry AI 是一套本地优先的 AI 工作流基础平台。它统一管理真实
项目、工具权限、会话恢复、工作流组件目录和安全契约，让不同领域的 AI 能力遵循
“受控输入 → AI 候选 → 人工审核 → 可验证产物 → 可恢复操作”的共同流程。

## What is real today

- A bundled, tested workspace runtime for Claude, DeepSeek, and Codex under
  [`core/workspace-manager`](core/workspace-manager/README.md).
- A dependency-free catalog validator and CLI for describing related workflow
  packs, applications, their maturity, and safety boundaries.
- Four cataloged components with explicit integration modes instead of claims
  that unrelated repositories are one executable.
- A generic component schema, product architecture, project-pattern audit, and
  staged roadmap toward a reusable workflow runner.

This is a foundation release, not yet a universal workflow executor or a single
graphical application. The catalog distinguishes bundled code, compatible
extensions, reference applications, and reference workflows.

## Product architecture

```text
real project + controlled inputs
              |
              v
   workspace and permission runtime
              |
              v
      bounded workflow component
              |
              v
 AI candidate / immutable revision
              |
              v
 human review + explicit approval
              |
              v
 validated artifact + audit record
```

| Layer | Component | Relationship |
|---|---|---|
| Core runtime | [AI Workspace Manager](core/workspace-manager/README.md) | Bundled with preserved Git history |
| Media workflow pack | [Confera Media Skills](https://github.com/ryanshi1103/confera-media-skills) | Compatible extension; independently versioned |
| Customer intelligence | [Feedback Analysis System](https://github.com/ryanshi1103/feedback-analysis-system) | Reference application; independently deployable |
| Document automation | [Print-ready Nameplate Generator](https://github.com/ryanshi1103/print-ready-nameplate-generator) | Reference workflow; independently deployable |

These projects are connected by contracts and design principles. They remain
separate where their users, release cycles, dependencies, or licensing differ.

## Try the catalog

No third-party package is required:

```bash
PYTHONPATH=src python3 -m flowfoundry validate
PYTHONPATH=src python3 -m flowfoundry list
PYTHONPATH=src python3 -m flowfoundry show confera-media-skills
```

Install the CLI in an isolated environment if desired:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -e .
flowfoundry validate
```

## Design principles

- Local-first operation with network use declared, never implied.
- AI produces bounded candidates; trusted code owns tools and side effects.
- Human review is separate from export or destructive approval.
- Originals and AI source results remain available for comparison.
- Artifacts are addressable, validated, and written atomically where possible.
- Every component declares maturity honestly: experimental is not production.
- Separate products may reuse contracts without pretending to share one runtime.

See [Architecture](docs/ARCHITECTURE.md),
[Product Lines](docs/PRODUCT-LINES.md),
[Project Pattern Audit](docs/PROJECT-PATTERN-AUDIT.md), and
[Roadmap](docs/ROADMAP.md).

## Test

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v

# Bundled workspace runtime regression suite
cd core/workspace-manager
./tests/test-cc.sh
./tests/test-cc-eof-fix.sh
./tests/test-deploy-profile-preservation.sh
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_*.py' -v
```

## License

FlowFoundry AI is MIT licensed. Bundled components retain their own license
files. External catalog entries are links and are governed by their respective
repositories.
