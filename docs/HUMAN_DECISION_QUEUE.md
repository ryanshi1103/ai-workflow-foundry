# Human Decision Queue

Only one unresolved product/brand choice remains. Release approvals and runtime
integration work are existing gates/tasks, not new product decisions.

## HDQ-001 — Canonical plain-Chinese explanation

**Question:** Which exact sentence should permanently accompany
`你定目标，AI组队实现` in campus-facing material?

**Historical options**

- Codex Round 2:
  `给出一个目标，FlowFoundry会按任务需要组织刚好够用的AI小队，执行、检查并交付结果。`
- DeepSeek Round 1:
  `FlowFoundry 是一个本地运行的 AI 工作助手。你只需要说出目标，它会自动组建最精简的 AI 团队，完成并验证工作。不是聊天机器人——你说目标，它出结果。`
- Poster prototype, English mechanism:
  `FlowFoundry organizes the smallest sufficient AI team.`

**Codex position:** The one-sentence Round 2 version is compact and keeps goal,
adaptive sizing, execution, checking, and delivery together. Its phrase
`刚好够用` should be tested because the Meeting rejected similar wording in
the headline.

**DeepSeek position:** The three-sentence version is more accessible and makes
local operation, validation, and anti-chatbot differentiation explicit, but is
too long for many poster placements and says `自动`, which can overstate human
control.

**Later productization position:** Use concise, evidence-bounded copy and avoid
implying autonomous execution or a shipped personal assistant.

**Evidence:**

- `.flowfoundry/runs/visual-identity-council-live-1/tasks/deepseek-visual-view/result.json`
- `.flowfoundry/runs/visual-identity-council-live-1/artifacts/meeting/round2/cross-conflict-001-codex-visual-view/provider-output.json`
- `.flowfoundry/runs/visual-identity-council-live-1/final/meeting-result.json`

**Impact:** Campus poster, Chinese landing copy, social cards, and explanatory
alt text. It does not change runtime or the adopted headline.

**Recommended default:** Until the owner chooses exact copy, use a clearly
marked non-canonical working explanation:

> 给出目标，FlowFoundry会按任务需要选择一个AI Agent或组成最小够用的团队，执行并验证结果。

This avoids `自动`, preserves the single-agent path, and keeps validation
explicit. It must remain labeled working copy rather than being entered as a
binding ledger decision.

**Risk of deferring:** Low for the GitHub Alpha; moderate for Chinese campus
material. Deferral must not block the English GitHub reconciliation.
