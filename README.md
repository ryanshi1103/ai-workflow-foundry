<p align="center">
  <img src="branding/logo.png" width="144" alt="FlowFoundry AI logo">
</p>

<h1 align="center">FlowFoundry AI</h1>
<p align="center"><strong>Local-first foundations for AI work that stays reviewable, recoverable, and reusable.</strong></p>

FlowFoundry AI is an open, integrated foundation for designing and operating
bounded AI workflows. It combines a real project/workspace runtime with media
skills, a feedback-intelligence application, deterministic document automation,
and a validated component contract in one repository. The product is
broader than one phone, one model, or one content type: it focuses on the
lifecycle shared by useful AI work.

中文说明：FlowFoundry AI 是一套本地优先的 AI 工作流基础平台。它统一管理真实
项目、工具权限、会话恢复、工作流组件目录和安全契约，让不同领域的 AI 能力遵循
“受控输入 → AI 候选 → 人工审核 → 可验证产物 → 可恢复操作”的共同流程。

## What is real today

- A bundled, tested workspace runtime for Claude, DeepSeek, and Codex under
  [`core/workspace-manager`](core/workspace-manager/README.md).
- Three physically integrated workflow components with their original Git
  histories: Confera Media Skills, Feedback Intelligence System, and the
  Print-ready Nameplate Generator.
- A sanitized application contract for the private Huiying / MediaFlow product;
  its commercial implementation, real media, configuration, and release assets
  remain outside this public repository.
- A dependency-free catalog validator and CLI that verifies bundled paths,
  maturity declarations, and safety boundaries.
- A generic component schema, product architecture, project-pattern audit, and
  staged roadmap toward a reusable workflow runner.

This is an integrated monorepo, not a claim that every component shares one UI
or dependency environment. Components retain explicit boundaries and can still
be released independently from their monorepo paths.

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
| Media workflow pack | [Confera Media Skills](components/confera-media-skills/README.md) | Bundled under `components/` with preserved history |
| Customer intelligence | [Feedback Intelligence System](applications/feedback-intelligence-system/README.md) | Bundled under `applications/`; independently runnable; legacy catalog IDs remain aliases |
| Private media application | [Huiying / MediaFlow](applications/mediaflow/README.md) | Public workflow and policy contract only; private source and product data remain isolated |
| Document automation | [Print-ready Nameplate Generator](workflows/print-ready-nameplate-generator/README.md) | Bundled under `workflows/`; independently runnable |

The monorepo is the canonical integration point. Component boundaries remain
because users, dependencies, licensing, and release artifacts differ—not
because the code lives in unrelated local projects.

## Try it

One package, one CLI — the full lifecycle:

```bash
# Validate all components, contracts, and capabilities
PYTHONPATH=src python3 -m flowfoundry validate

# Browse catalog
PYTHONPATH=src python3 -m flowfoundry list
PYTHONPATH=src python3 -m flowfoundry capabilities

# Manage projects (was aiproj)
PYTHONPATH=src python3 -m flowfoundry project status
PYTHONPATH=src python3 -m flowfoundry project list

# Interactive launcher (was cc)
PYTHONPATH=src python3 -m flowfoundry project launch
```

Install the CLI to use anywhere:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -e .
flowfoundry validate
flowfoundry project launch
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

# From the repository root: bundled component contract tests
python3 -m unittest discover -s components/confera-media-skills/tests -v
python3 -m unittest discover -s workflows/print-ready-nameplate-generator/tests -v

# Feedback application (after installing its dev dependencies)
python3 -m pip install -e "applications/feedback-intelligence-system[dev]"
ruff check applications/feedback-intelligence-system/feedback_intelligence \
  applications/feedback-intelligence-system/src \
  applications/feedback-intelligence-system/tests \
  applications/feedback-intelligence-system/app.py \
  applications/feedback-intelligence-system/pages
pytest applications/feedback-intelligence-system/tests -q
```

## License

FlowFoundry AI is MIT licensed. Bundled components retain their own license
files and notices; the Feedback Intelligence component keeps its more restrictive
learning/internal-use terms.
