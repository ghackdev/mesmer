# Primitive Taxonomy Audit

This audit supersedes the old component-tree taxonomy. The historical analysis is
preserved in `primitive-component-tree.md`; the target architecture is documented
in `primitive-architecture.md`.

## Current Cornerstone

Mesmer's durable kernel is:

```text
State + Operator + Transition + Workflow
```

The public design layers are:

| Layer | Responsibility | Examples |
| --- | --- | --- |
| State slices | Typed runtime memory. | `state.Frontier`, `state.Attempts`, `state.Evaluations`, `state.PopulationPool`, `state.RewardLedger` |
| Operators | Executable state transitions. | `ops.Propose`, `ops.QueryTarget`, `ops.Evaluate`, `ops.StopWhen`, `ops.AddFeedback`, `ops.GenerateFromPopulation` |
| Workflows | Internal control algebra. | `workflow.Sequence`, `workflow.Loop` |
| Transitions | Replay/debug record for each operator run. | `transitions.Transition` |
| Techniques | User-facing algorithm recipes. | `techniques.SingleTurnProbe`, `techniques.FrontierSearch`, `techniques.PopulationFuzzing` |
| Strategies/services | Non-executable behavior used by operators. | `proposers.Template`, `evaluators.Contains`, `selectors.TopKSelector`, `mutators.LexicalSubstitutionMutator`, `conditions.ScoreAtLeast`, `sources.ListSeedPoolSource` |

## Extension Rule

Prefer the smallest extension that carries the idea:

1. Add or configure a strategy for normal experimentation.
2. Add an operator for a new reusable state transition.
3. Add a workflow block for genuinely new control algebra.
4. Add a technique for a distinct algorithm skeleton.

Do not add new public topology wrappers or direct flow classes for paper work.

## Paper Mapping

| Paper style | Technique shape | Reusable pieces |
| --- | --- | --- |
| TAP | Frontier search with branching, selection, target query, evaluation, stop. | Structured proposer, selector, evaluator, feedback. |
| PAIR | Frontier search with parallel streams and feedback into refinement. | Structured proposer, feedback builder, top-k selector. |
| JBFuzz | Population fuzzing with seed selection, mutation, query, evaluation, reward. | Seed source, seed selector, mutator, reward operator. |
| Autonomous agents | Frontier search with append-user proposals and conversation continuation. | Structured proposer, conversation operator, feedback operator. |

## Boundary Decisions

- Evaluation is not stopping. Evaluators write evidence; stop conditions consume evidence.
- Feedback is not evaluation. Feedback becomes future attacker context or credit assignment.
- Prompt patterns are proposer context, not executable transforms.
- Deterministic rewrites should be custom operators when they are part of an executable technique.
- Targets are only called through `ops.QueryTarget`; target adapters stay portable.
- Built-in techniques infer state schemas from operator reads/writes and expose them through `state_schema()`.
