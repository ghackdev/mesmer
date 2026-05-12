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
| State slices | Typed runtime memory. | `state.Frontier`, `state.Attempts`, `state.Evaluations`, `state.Constraints`, `state.PopulationPool`, `state.RewardLedger`, `state.PromptPatternLedger`, `state.InferenceLedger` |
| Evidence slices | Benchmark-grade research evidence. | `state.EvidenceLedger`, `state.BudgetLedger`, `state.JudgeLedger`, `state.ConversationTraceSlice`, `state.CumulativeRiskLedger`, `state.SystemSurfaceState` |
| Operators | Executable state transitions. | `ops.Propose`, `ops.SelectPromptPatterns`, `ops.ApplyTransforms`, `ops.CheckConstraints`, `ops.Filter`, `ops.QueryTarget`, `ops.MarkPromptPatternsTried`, `ops.ExtractClaims`, `ops.SynthesizeHypothesis`, `ops.Evaluate`, `ops.StopWhen`, `ops.AddFeedback`, `ops.GenerateFromPopulation`, `ops.AppendTurn`, `ops.ScoreConversationRisk`, `ops.RenderChatTemplate`, `ops.QueryClassifier` |
| Workflows | Internal control algebra. | `workflow.Sequence`, `workflow.Loop` |
| Transitions | Replay/debug record for each operator run. | `transitions.Transition` |
| Techniques | User-facing algorithm recipes. | `techniques.Probe`, `techniques.BestOfNProbe`, `techniques.FrontierSearch`, `techniques.ElicitationSearch`, `techniques.ConversationAgentProbe`, `techniques.PopulationFuzzing` |
| Strategies/services | Non-executable behavior used by operators. | `proposers.Template`, `evaluators.JudgePanel`, `selectors.TopKSelector`, `mutators.LexicalSubstitutionMutator`, `conditions.ScoreAtLeast`, `sources.ListSeedPoolSource` |
| Benchmark evidence | Cross-run comparison and budget views. | `benchmarking.EvidenceMatrix`, `benchmarking.BudgetCurve` |

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
| Single-shot probes | One prepared candidate, one target query, evaluation, optional stop. | `techniques.Probe`, `ops.Propose`, `ops.ApplyTransforms`, response evaluators. |
| Best-of-N / repeated sampling | Bounded batch sampling, query, evaluation, select. | `techniques.BestOfNProbe`, structured proposer, evaluator panel, top-k selector. |
| TAP | Frontier search with branching, constraints, selection, target query, evaluation, stop. | Structured proposer, `pre_query` constraint gates, selector, evaluator, feedback. |
| PAIR | Frontier search with parallel streams and feedback into refinement. | Structured proposer, feedback builder, top-k selector, post-evaluation hooks. |
| JBFuzz | Population fuzzing with seed selection, mutation, query, evaluation, reward. | Seed source, seed selector, mutator, reward operator. |
| GCG-style suffix attacks | Suffix proposal/search with target-completion scoring, multi-prompt evaluation, multi-model evidence, and optional ensemble attempts. | Source-tagged prompt patterns, `proposers.SuffixOnlyLLMProposer`, `ops.ApplyTransforms`, `transforms.AppendSuffix`, prefix/refusal-shape evaluators, plus existing selection, feedback, and stopping pieces. |
| Autonomous agents | Explicit multi-turn target-visible transcript loop. | `techniques.ConversationAgentProbe`, structured proposer, `ops.ContinueConversation`, feedback operator. |
| LATS / salami-style multi-turn risk | Target-visible turns, lexical anchors, per-turn and cumulative scoring. | `ops.AppendTurn`, `transforms.LexicalAnchorInject`, `ops.ScoreConversationRisk`, `state.ConversationTraceSlice`, `state.CumulativeRiskLedger`. |
| JCB / cross-behavior memory | Reuse successful candidates and score transfer across objectives. | `state.MemoryBank`, `state.TransferLedger`, `ops.LoadMemoryBank`, `ops.PromoteSuccessfulCandidate`, `ops.ScoreTransfer`. |
| Elicitation / hypothesis accumulation | Query, extract partial evidence, annotate provenance, synthesize a best-current hypothesis, and feed it back into later prompts. | `state.InferenceLedger`, actor-backed claim extractors and hypothesis synthesizers, claim evidence tracks/provenance, `ops.ExtractClaims`, `ops.AnnotateClaimProvenance`, `ops.SynthesizeHypothesis`, `ops.CalibrateEvidenceScores`, `ops.PromoteTacticMemory`, `selectors.InferenceDiversitySelector`, `feedback.InferenceFeedback`, `techniques.ElicitationSearch`. |
| TemplateFuzz / system surface | Chat-template mutation, serialization evidence, classifier decisions. | `ops.RenderChatTemplate`, `ops.MutateChatTemplate`, `ops.QueryClassifier`, `state.SystemSurfaceState`, capability checks. |
| Many-shot / Best-of-N transforms | Long-context demonstration packing and text augmentation. | `transforms.DemonstrationPack`, `transforms.AugmentText`, `transforms.TransformProvenance`, `BestOfNProbe`. |
| Judge reliability | Judge runs and panel agreement evidence. | `evaluators.JudgePanel`, `state.JudgeLedger`, `evidence.JudgeRun`, `evidence.JudgeAgreement`. |

## Boundary Decisions

- Evaluation is not stopping. Evaluators write evidence; stop conditions consume evidence.
- Feedback is not evaluation. Feedback becomes future attacker context or credit assignment.
- Prompt patterns are data and proposer context. `ops.SelectPromptPatterns`
  attaches selected pattern context to the frontier, usage is tracked in
  `state.PromptPatternLedger`, and concrete templates/transforms still execute
  only through `ops.ApplyTransforms`.
- Elicitation search should use soft triage, not hard pruning. Weird probes,
  placeholders, encodings, roleplay, and hypothesis replay can be tried, but
  extracted claims must separate `content`, `behavior`, `echo`, and `artifact`
  tracks and provenance (`target_observed`, `prompt_seeded`, `hypothesis_seeded`,
  `artifact`, etc.) so seeded clues are retained without inflating confidence.
- Deterministic rewrites are transform strategies executed through `ops.ApplyTransforms`.
- Constraints are typed evidence. Use `ops.CheckConstraints` to record them and
  `ops.Filter` or selectors to retain candidates.
- Black-box GCG-inspired work should keep suffix generation, suffix application, and response-shape evaluation separate; token-gradient optimization remains a future white-box capability.
- Targets are only called through `ops.QueryTarget`; target adapters stay portable.
- Built-in techniques infer state schemas from operator reads/writes and expose them through `state_schema()`.
- Benchmark reports should preserve both row-level evidence and budget curves so
  technique comparisons are not reduced to one final success number.
- Operator capabilities are executable threat-model requirements. A workflow
  using prefill, logprobs, chat-template control, classifier feedback, or
  white-box internals must declare those capabilities and validate them against
  the target capability profile.
- Conversation turns, serialized inputs, classifier decisions, judge runs, and
  cumulative-risk scores are evidence records, not incidental metadata.
