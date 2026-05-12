# Jailbreak Framework Strategic Architecture Review

Prepared: 2026-05-10, Asia/Makassar.

Implementation note: the first substrate pass has been implemented in code.
Capability profiles, evidence/budget/judge ledgers, conversation trace and
cumulative-risk slices, cross-objective memory/transfer ledgers,
system-surface records, capability-gated query operators, and transform
provenance are now available as primitives. The plan below remains the roadmap
for hardening and expanding those primitives.

This review rethinks Mesmer's current framework design against the jailbreak
technique evolution summarized in
`docs/research/evolution-of-llm-jailbreaking-techniques.md` and the existing
architecture docs in this folder.

## Verdict

Mesmer's core is robust enough to become a strategic constant for the next
evolution of jailbreak frameworks.

The durable center should remain:

```text
State + Operator + Transition + Workflow
```

That kernel is stronger than a jailbreak-taxonomy-first design because the field
keeps changing tactics while preserving the same experiment mechanics:
generate candidates, transform them, query targets, evaluate responses, record
evidence, select survivors, assign reward, reuse memory, and replay what
happened.

The current design is therefore directionally right. The missing work is not a
foundation rewrite. The missing work is to promote several currently implicit
research objects into first-class state slices, operators, strategy interfaces,
and reporting artifacts.

## Existing Design Strengths

### 1. The kernel is stable

`primitive-architecture.md` makes the right move by demoting named techniques
to recipes. PAIR, TAP, Best-of-N, JCB, LATS, TemplateFuzz, and autonomous LRM
agents are not fundamentally different worlds. They are different compositions
of state transitions.

The current implementation reflects this:

- `Technique` compiles to a `Workflow`.
- `Workflow` composes `Operator` instances.
- `Operator` declares typed `reads` and `writes`.
- `State` stores typed state slices.
- `Transition` records before/patch/after evidence.

This should stay fixed.

### 2. Target calls are visible

`ops.QueryTarget` is an explicit boundary. This is important because query cost,
target adapter behavior, serialized messages, latency, token usage, and target
metadata are part of the experimental claim.

Future work should add more target-boundary operators, but it should not hide
target calls inside proposers, evaluators, transforms, or dataset loaders.

### 3. Evaluation, stopping, and feedback are separated

This is one of the strongest design principles in the repo.

- Evaluation writes evidence.
- Stopping consumes evidence.
- Feedback turns evidence into future attacker context or credit assignment.

Modern jailbreak research needs this separation. Multi-turn, Best-of-N,
cross-behavior, and judge-panel experiments all require evidence even when a
run does not stop.

### 4. Techniques are correctly treated as recipes

`Probe`, `BestOfNProbe`, `FrontierSearch`, `ConversationAgentProbe`, and
`PopulationFuzzing` are good top-level shapes. They give users names for common
experiments without forcing every paper to become a new framework primitive.

The extension ladder is also right:

1. Add/configure a strategy.
2. Add an operator.
3. Add a workflow block.
4. Add a technique only for a distinct algorithm skeleton.

## Strategic Gaps

### Gap 1: Conversation state is still too implicit

Current support:

- `Candidate.messages` stores target-visible messages.
- `CandidateTrajectory.last_response` stores the latest target response.
- `ops.ContinueConversation` appends target responses back into the candidate.
- `ConversationAgentProbe` provides a multi-turn loop.

Problem:

The framework can run multi-turn experiments, but it does not yet model
conversation as a first-class audit object. Autonomous LRM attacks, LATS, and
salami-slicing style tests need more than candidate messages. They need turn
records, role ownership, private attacker context, target-visible context,
per-turn risk, cumulative risk, and strategy annotations.

Missing primitives:

- `ConversationTrace` state slice.
- `TurnLedger` state slice.
- `PrivateContext` or `ActorState` state slice for attacker-private memory.
- `ops.AppendTurn` for target-visible and actor-private turns.
- `ops.ScoreConversationRisk` for cumulative risk across turns.
- `ops.AnnotateStrategy` for persuasion/style/anchor/cumulative-risk labels.

Design principle to add:

Conversation is not metadata. It is experiment state.

### Gap 2: Cross-objective memory is not strong enough

Current support:

- `PopulationPool`
- `RewardLedger`
- `GenerateFromPopulation`
- `AssignReward`

Problem:

This is enough for JBFuzz-style population search, but JCB-style work needs
transfer-aware memory across objectives, targets, behavior clusters, and runs.
Right now, memory is mostly per-run state. Successful candidate lineage can be
recorded, but it is not yet a first-class research asset.

Missing primitives:

- `MemoryBank` state slice for cross-objective seed/candidate records.
- `TransferLedger` state slice for source objective -> target objective reuse.
- `ops.LoadMemoryBank`
- `ops.PromoteSuccessfulCandidate`
- `ops.ScoreTransfer`
- `selectors.TransferAwareSelector`
- persistent storage schema for memory records and lineage.

Design principle to add:

Successful attacks are reusable evidence, not only final outputs.

### Gap 3: Evidence is too flat for benchmark-grade comparisons

Current support:

- `Attempts`
- `TargetResponses`
- `Evaluations`
- `Transition`
- benchmark modules for reports and budget curves.

Problem:

Modern benchmark claims require multi-axis evidence:

- objective category;
- target model and guardrail version;
- target adapter capability;
- judge model and aggregation policy;
- turn index;
- query index;
- candidate lineage;
- transform chain;
- refusal/harm/disclaimer labels;
- cost and latency;
- failure cases, not only winners.

The current `Evaluations` list and `Attempt` metadata can carry some of this,
but too much lands in generic metadata. That weakens validation, reporting, and
replay.

Missing primitives:

- `EvidenceLedger` state slice.
- `BudgetLedger` state slice.
- `JudgeLedger` state slice.
- `RunMatrix` report artifact for objective x target x technique x judge.
- `ops.RecordEvidence` or stronger evidence emission from existing operators.
- typed `EvidenceRecord` model with objective, target, candidate, judge, turn,
  query, score, cost, and artifact references.

Design principle to add:

ASR is a view over evidence, not the evidence itself.

### Gap 4: System-boundary attacks need their own surface

Current support:

- `Target` adapters.
- `TargetContext`.
- transforms over message content.
- target response metadata.

Problem:

TemplateFuzz, BPJ, simple adaptive attacks, and API-specific jailbreaks expand
the target from "model response" to "system behavior". The framework does not
yet make chat templates, serialized messages, classifier decisions, prefill
state, logprobs, or guardrail boundaries explicit enough.

Missing primitives:

- `SystemSurface` model for prompt template, role layout, tool gates,
  classifiers, and serialization.
- `SerializedConversation` artifact.
- `ClassifierDecision` state/evidence model.
- `ops.RenderChatTemplate`
- `ops.MutateChatTemplate`
- `ops.QueryClassifier`
- `ops.QueryWithPrefill`
- `ops.QueryWithLogprobs`
- capability flags such as `target.logprobs`, `target.prefill`,
  `target.classifier_feedback`, and `target.chat_template_control`.

Design principle to add:

The target is a pipeline, not only a model.

### Gap 5: Transform semantics are under-specified

Current support:

- `Encode`
- `TemplateWrap`
- `AppendSuffix`
- `PayloadSplit`
- `CharacterRewrite`
- `Compose`
- `FromPromptPattern`

Problem:

Transforms are strategically important, but the current transform metadata is
mostly operational. For research, Mesmer needs to know what kind of semantic
pressure a transform applies: encoding, style transfer, lexical anchoring,
demonstration packing, suffix pressure, template mutation, modality shift, or
surface perturbation.

Missing primitives:

- `TransformKind` enum.
- `TransformProvenance` model.
- `StyleTransfer` transform.
- `LexicalAnchorInject` transform.
- `DemonstrationPack` transform for many-shot and context-window tests.
- `AugmentText` transform for Best-of-N perturbations.
- `TemplateMutation` transform or operator for TemplateFuzz.

Design principle to add:

Transforms must declare intent-preservation and surface-change metadata.

### Gap 6: Judge reliability needs first-class accounting

Current support:

- `ResponseEvaluator`
- `JudgePanel`
- `EvaluationResult`

Problem:

`JudgePanel` currently aggregates by mean normalized score and `any_pass`. That
is useful for simple experiments, but benchmark-grade jailbreak work needs
judge agreement, disagreement records, adjudication, calibration sets, and
separate refusal/harm/disclaimer labels.

Missing primitives:

- `JudgeRun` model.
- `JudgeAgreement` model.
- `AdjudicationRecord` model.
- `JudgeLedger` state slice.
- `evaluators.RefusalClassifier`
- `evaluators.DisclaimerClassifier`
- `evaluators.HarmRubric`
- `ops.AdjudicateJudges`

Design principle to add:

A judge result is a measurement with uncertainty, not an oracle.

### Gap 7: Capability boundaries are not explicit enough

Current support:

- `Operator.capabilities`
- `Technique.capabilities`
- target adapters with metadata.

Problem:

The field now mixes strict black-box, black-box with logprobs, black-box with
prefill, classifier-boundary feedback, open-weight logits, and white-box
gradients. Mesmer should make these distinctions mechanically visible so a
paper extraction cannot accidentally model a white-box method as black-box.

Missing primitives:

- `CapabilityProfile` for target and technique.
- validation that workflow-required capabilities are available.
- capability labels for `logprobs`, `prefill`, `classifier_feedback`,
  `chat_template_control`, `tokenizer`, `logits`, `gradients`,
  `activation_patch`, and `weights`.
- separate white-box experimental namespace for HMNS/GCG-style internals.

Design principle to add:

Threat model is executable configuration, not prose.

### Gap 8: Workflow control algebra is minimal

Current support:

- `Sequence`
- `Loop`

Problem:

`Sequence` and `Loop` are enough for many techniques, but future attack systems
will need standard control blocks for branch-and-bound, budgeted sampling,
multi-target matrices, retry policies, and asynchronous judge panels. These
should be workflow blocks, not ad hoc logic inside techniques.

Missing primitives:

- `workflow.Branch`
- `workflow.MapObjectives`
- `workflow.MapTargets`
- `workflow.BudgetedLoop`
- `workflow.Retry`
- `workflow.RaceUntil`
- `workflow.ParallelPanel`

Design principle to add:

Control flow belongs in workflow blocks, not hidden inside operators.

## Strategic Constants To Keep

These should be treated as non-negotiable unless future evidence is very strong:

1. `State + Operator + Transition + Workflow` remains the kernel.
2. Techniques remain recipes, not the framework foundation.
3. Target calls stay visible and budgeted.
4. Evaluation, stopping, feedback, and reward stay separate.
5. Prompt patterns are context/data, not executable attack nodes.
6. Transforms are executable only through operators.
7. Threat model and capability profile must be explicit.
8. Replay must include failures, rejected candidates, and cost, not only
   successes.
9. Harmful operational payloads should not become repo examples; use canaries,
   synthetic objectives, and redactions.

## Fix Plan

### Phase 0: Align Architecture Docs

Goal: make the design target unambiguous before implementation.

Tasks:

1. Update `primitive-architecture.md` with the new strategic constants.
2. Add a "Future-Proofing Surface" section covering conversation, memory,
   evidence, system boundary, transforms, judges, capabilities, and workflow
   control.
3. Update `primitive-taxonomy-audit.md` with a "missing first-class primitives"
   table.
4. Mark `primitive-component-tree.md` as historical only and avoid extending
   its vocabulary.

Acceptance criteria:

- Docs distinguish strategic constants from planned primitives.
- Every missing primitive has a target layer: state slice, operator, strategy,
  workflow block, technique, report, or storage artifact.

### Phase 1: Capability And Evidence Foundation

Status: first pass implemented.

Goal: make threat model and evidence explicit before adding more attack shapes.

Tasks:

1. Add `CapabilityProfile` models for targets, techniques, and operators.
2. Validate workflow capability requirements before execution.
3. Add `EvidenceRecord`, `EvidenceLedger`, `BudgetLedger`, and `JudgeLedger`
   state slices.
4. Extend `ops.QueryTarget` and `ops.Evaluate` to emit typed evidence records.
5. Extend benchmark reports to read from ledgers rather than only attempts and
   flat evaluations.

Acceptance criteria:

- A run can report exact capability assumptions.
- A benchmark can produce objective x target x technique x judge rows.
- Query counts, latency, tokens, evaluator identity, and candidate lineage are
  captured without generic metadata spelunking.

### Phase 2: First-Class Conversation Runtime

Status: first pass implemented for conversation turns, target continuations,
strategy annotations, and cumulative-risk scoring. Further work remains for
private attacker context and richer actor state.

Goal: support autonomous agents, LATS, and salami-slicing style experiments as
typed conversation systems.

Tasks:

1. Add `ConversationTrace`, `TurnLedger`, `ActorState`, and
   `CumulativeRiskLedger` state slices.
2. Add `ops.AppendTurn`, `ops.ContinueConversation` replacement or extension,
   `ops.ScoreConversationRisk`, and `ops.AnnotateStrategy`.
3. Update `ConversationAgentProbe` to use the new conversation slices.
4. Add a safe canary example for direct prompt vs multi-turn steering vs
   cumulative-risk escalation.

Acceptance criteria:

- Each turn has actor, visibility, target, candidate, response, evaluation, and
  risk metadata.
- Private attacker context is separated from target-visible transcript.
- Cumulative risk can be scored across turns.

### Phase 3: Cross-Objective Memory

Status: first pass implemented for loading memory records, promoting
successful candidates, and scoring transfer overlap. Further work remains for
persistent storage, richer similarity policies, and transfer-aware selectors.

Goal: support JCB-style transfer and population reuse across runs.

Tasks:

1. Add `MemoryBank`, `TransferLedger`, and persistent storage for memory records.
2. Add `ops.LoadMemoryBank`, `ops.PromoteSuccessfulCandidate`, and
   `ops.ScoreTransfer`.
3. Add transfer-aware selectors and reward policies.
4. Add a safe cross-behavior canary example that reuses successful benign
   patterns across objective categories.

Acceptance criteria:

- Successful candidates can be promoted to reusable memory.
- Later runs can select memory by source objective, target, transform chain,
  score, and failure mode.
- Reports can show transfer benefit and query savings.

### Phase 4: System Surface And Template Fuzzing

Status: first pass implemented for chat-template rendering, template mutation,
classifier decisions, and capability-gated prefill/logprob query operators.
Further work remains for external classifier adapters and richer template
mutation strategies.

Goal: model the deployed system boundary, not only message text.

Tasks:

1. Add `SystemSurface`, `SerializedConversation`, and `ClassifierDecision`
   models.
2. Add `ops.RenderChatTemplate`, `ops.MutateChatTemplate`,
   `ops.QueryClassifier`, and optional `ops.QueryWithPrefill` /
   `ops.QueryWithLogprobs`.
3. Add target capability flags for template control, classifier feedback,
   logprobs, and prefilling.
4. Build a local test target for template mutation before real model APIs.

Acceptance criteria:

- A run records exact serialized target input when available.
- Template mutations are traceable and reversible.
- Classifier feedback is recorded as evidence, not hidden in target metadata.

### Phase 5: Transform Semantics And Long-Context Support

Status: first pass implemented for transform kind/provenance plus style,
lexical-anchor, demonstration-pack, and augmentation transforms. Further work
remains for tokenizer-aware long-context curves and modality-specific
augmentations.

Goal: make representation-shift, style-shift, Best-of-N, and many-shot work
auditable.

Tasks:

1. Add `TransformKind` and `TransformProvenance`.
2. Add `StyleTransfer`, `LexicalAnchorInject`, `DemonstrationPack`, and
   `AugmentText`.
3. Add transform-level intent-preservation metadata.
4. Add long-context budget accounting for prompt tokens and demonstration count.

Acceptance criteria:

- Every transformed candidate records what changed and why.
- Best-of-N and many-shot runs can show sampling curves and context-length
  curves.
- Transform families can be compared without relying on prompt strings.

### Phase 6: Judge Reliability

Status: first pass implemented for judge runs and panel agreement records.
Further work remains for adjudication operators and specialized refusal,
disclaimer, and harm-rubric evaluators.

Goal: make judge uncertainty visible.

Tasks:

1. Add `JudgeRun`, `JudgeAgreement`, and `AdjudicationRecord`.
2. Extend `JudgePanel` to support aggregation policies beyond `any_pass`.
3. Add refusal, disclaimer, and harm-rubric evaluators.
4. Add disagreement and spot-check sections to benchmark reports.

Acceptance criteria:

- Judge-panel output reports agreement and disagreement.
- Runs can separate refusal, disclaimer, harmfulness, and task-completion
  measurements.
- Manual adjudication can be recorded without overwriting raw judge outputs.

### Phase 7: Workflow Control Algebra

Goal: remove hidden control logic from techniques and operators.

Tasks:

1. Add `BudgetedLoop`, `MapTargets`, `MapObjectives`, `RaceUntil`, and
   `ParallelPanel` workflow blocks.
2. Refactor techniques to use workflow blocks instead of custom embedded logic
   where useful.
3. Add workflow graph rendering with nested block structure, not only flat
   operator names.

Acceptance criteria:

- Complex techniques can be described by workflow algebra.
- Reports show nested workflow structure.
- Operators remain single state transitions.

## Implementation Order

Do not start with new attack techniques. Start with the substrate that makes
new techniques trustworthy.

Recommended order:

1. Capability profile and evidence ledgers.
2. Conversation state and cumulative risk.
3. Cross-objective memory.
4. System-surface operators.
5. Transform semantics and long-context transforms.
6. Judge reliability.
7. Workflow control blocks.

This order keeps the kernel stable while expanding the surface where the next
jailbreak frameworks are likely to evolve.

## One-Sentence North Star

Mesmer should become the framework where a jailbreak paper is not copied as a
prompt, but decomposed into typed state, explicit operators, capability
assumptions, reusable memory, benchmark-grade evidence, and replayable
transitions.
