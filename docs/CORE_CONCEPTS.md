# FlowFoundry core concepts

The default product answers five questions around one human goal:

1. **What is the goal?** Preserve the user's actual outcome, not an invented DAG.
2. **What is binding?** Load only relevant authoritative project decisions and
   preserve their provenance and supersession semantics.
3. **What is sufficient?** Select capabilities first and use one executor unless
   current context, ambiguity, or material disagreement justifies more.
4. **What counts as done?** Deterministic evidence creates `PASS`; partial or
   non-deterministic evidence creates `PARTIAL` or `UNKNOWN`; failures create `FAIL`.
5. **Who has authority?** AI may prepare local work. Publication, deployment,
   payment, destructive deletion, and external communication return to a human.

FlowFoundry owns these coordination semantics and compact evidence. It borrows
execution from Codex and future replaceable tools or agents.

## Persistent local coordination

`flowfoundry do "<goal>" --background` creates one durable task file under
`.flowfoundry/coordinator/tasks/` and starts an isolated worker process. The CLI
returns immediately, so another goal can be submitted while the first worker
runs. `status` reconciles dead PIDs as `PROCESS_LOST` failures rather than
claiming work is still running. Worker context is references to relevant files
and decisions, not another copy of conversation history.

Tasks waiting for external communication, publication, payment, permission
changes, merge/deploy, or destructive deletion remain `WAITING_HUMAN`; approving
one task does not block unrelated tasks. Remote/cloud continuation is deferred.

## Small contracts

- `ExecutorRequest(goal, context, constraints)`
- `ExecutorResult(status, output, artifacts, usage, evidence, errors)`
- `BrokerDecision(selected_executor, selected_capabilities, selected_tools,
  reason, execution_instruction, expected_result, needs_second_opinion,
  verification_hint)`
- `Evaluation(PASS | PARTIAL | FAIL | UNKNOWN, evidence, needs_user)`

Grok is an optional semantic broker, never authority, memory, executor, or final
evaluator. An obvious repository task skips it. Current-context research may use
it when available and otherwise follows a deterministic capability fallback.

The legacy Meeting remains only an optional disagreement-resolution mechanism in
the hidden `team` compatibility path. It is not part of ordinary goal execution.
