# Feedback Intelligence Lineage Decision

The canonical public baseline is commit
`e8b9e3374521578702eed7b92ea67dd5a2c1f327` from the existing
`feedback-analysis-system` repository identity. FlowFoundry commit `8617cc2`
connected that baseline and imported its exact root tree under the original
`applications/feedback-analysis-system/` path.

The isolated migration branch advances that same public line to
`93b646baf6c92437b97abc0e13d6b6e53b8811eb`. Commit `d3ee954` connects the main
source commits with a non-squash, history-only merge: its tree is identical to
its first parent. The controlled vendor sync then moves the bundled path to
`applications/feedback-intelligence-system/`. The source and staged bundled
trees are both `2a2c2796a4176a0fc354ba94d73bdbe00e0f38c2`, proving that the
application snapshot is exact rather than hand-copied.

The source-only lint configuration follow-up is connected by `c8bac35`; this
second non-squash merge also preserves its first-parent tree exactly.

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

The code and local bundled path now use `feedback-intelligence-system`, but the
existing GitHub repository was not renamed automatically. The old
catalog identifier, Python imports, environment variables, database path,
Streamlit component keys, commands, and export formats remain compatibility
contracts during the migration window.
