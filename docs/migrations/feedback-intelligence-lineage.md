# Feedback Intelligence Lineage Decision

The canonical public implementation is commit
`e8b9e3374521578702eed7b92ea67dd5a2c1f327` from the existing
`feedback-analysis-system` repository identity. FlowFoundry commit `8617cc2`
already connects that commit as a parent and imports its exact root tree under
`applications/feedback-analysis-system/`.

The source root tree and the imported application tree are both
`5e47752bdfbf871201ad4f02a13f73634f044b1`. Importing the public repository a
second time would duplicate provenance and is therefore prohibited.

## Local archive line

The local `social-negative-monitor` branch diverges from the public line at
`be047d62812b072a6281e133d5435625cb24e859`. Its unique history contains
tracked session documentation. Those objects are unsuitable for a public
branch, so the archive line is not merged into FlowFoundry or the public
product line.

The complete local Git graph is preserved outside both repositories in a
private bundle with SHA-256
`8544ce02c43b1ac645d4993246985f14f24643c70427f63fb0e1b1d038c8183d`.
No database, working-tree runtime data, or ignored file was copied into
FlowFoundry.

## Product identity

The code and local bundled path may evolve to `feedback-intelligence-system`,
but the existing GitHub repository will not be renamed automatically. The old
catalog identifier, Python imports, environment variables, database path,
Streamlit component keys, commands, and export formats remain compatibility
contracts during the migration window.
