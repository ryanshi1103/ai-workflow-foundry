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

The source-only lint configuration follow-up is connected by `c8bac35`. The
final version-display/CI repair tip `93b646b` is connected by `c335a3d`; both
non-squash merges preserve their first-parent trees exactly. The final
FlowFoundry tree is `f6a8a3a7f5ea0501e2785f05a1e29ed675a6a2b4` before and after
the last history connection.

The complete canonical source branch is also preserved in a repository-external
`feedback-intelligence-phase2-final.bundle` with SHA-256
`cc4c0f4bda959edc33f7882c3d3daf506a2266612f29b7f0b1c5a61612bf8cc2`.

## Local archive line

The local `social-negative-monitor` archive tip is
`62a1e00efa7504a8207cc3a752c72268a9c0a0b6`, with tree
`be047d62812b072a6281e133d5435625cb24e859`. That archive has no common
ancestor with the public product line. Its unique history contains tracked
session documentation, so those objects are unsuitable for a public branch
and the archive line is intentionally not merged into FlowFoundry or the
public product line.

The excluded local archive Git graph is preserved outside both repositories in
a separate private bundle with SHA-256
`8544ce02c43b1ac645d4993246985f14f24643c70427f63fb0e1b1d038c8183d`.
No database, working-tree runtime data, or ignored file was copied into
FlowFoundry.

## Product identity

The code and local bundled path now use `feedback-intelligence-system`, but the
existing GitHub repository was not renamed automatically. The old
catalog identifier, Python imports, environment variables, database path,
Streamlit component keys, commands, and export formats remain compatibility
contracts during the migration window.
