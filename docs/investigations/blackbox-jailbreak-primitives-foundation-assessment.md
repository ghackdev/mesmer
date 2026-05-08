# Black-Box Jailbreak Primitive Foundation Assessment

Prepared: 2026-05-09, Asia/Makassar

## Bottom Line

Mesmer does not need a foundation rewrite. The current durable kernel,

```text
State + Operator + Transition + Workflow
```

is aligned with the main evolution of black-box LLM jailbreaking from 2023
through the 2025-2026 frontier. The field has not converged on one special
prompt trick. It has converged on experiment mechanics: generate variants,
query targets, judge responses, select or reward candidates, feed evidence back
into the next step, preserve cost and replay artifacts, and compare across
objectives, targets, and defenses.

That is exactly the kind of problem a typed state-transition runtime should
model.

The adjustment is not "replace the kernel with a jailbreak taxonomy." The
adjustment is to promote a few currently implicit experiment objects into
first-class state and operators:

- conversation-level state, not only latest candidate messages;
- cross-objective memory, not only per-objective frontier state;
- multi-target, multi-judge, multi-turn evidence matrices, not only a flat list
  of response evaluations;
- distributional sampling and budget curves, not only final success/failure;
- optional API-internal evidence such as logprobs or prefill state, clearly
  separated from strict black-box access;
- multimodal content blocks for future text, image, audio, and tool-mediated
  red-team runs.

So the answer is:

1. The first principles are correct.
2. The strategic constants are mostly correct.
3. The first-citizen primitive set is directionally correct, but should expand
   around conversation, cohort memory, and benchmark-grade evidence.
4. Mesmer will stay relevant if it keeps treating papers as sources of reusable
   mechanics, not as prompts to copy.

## Evidence Basis

Local repository sources:

- [`docs/research/llm-jailbreaking-papers-map.md`](../research/llm-jailbreaking-papers-map.md)
- [`docs/learn/llm-jailbreak-paper-reading-path.md`](../learn/llm-jailbreak-paper-reading-path.md)
- [`docs/tech/primitive-architecture.md`](../tech/primitive-architecture.md)
- [`docs/tech/primitive-taxonomy-audit.md`](../tech/primitive-taxonomy-audit.md)
- [`CLAUDE.md`](../../CLAUDE.md)
- [`docs/papers/2508.04039v1-large-reasoning-models-autonomous-jailbreak-agents.md`](../papers/2508.04039v1-large-reasoning-models-autonomous-jailbreak-agents.md)
- Runtime implementation in [`src/mesmer/techniques.py`](../../src/mesmer/techniques.py), [`src/mesmer/ops.py`](../../src/mesmer/ops.py), [`src/mesmer/state.py`](../../src/mesmer/state.py), [`src/mesmer/workflow.py`](../../src/mesmer/workflow.py), [`src/mesmer/proposers.py`](../../src/mesmer/proposers.py), [`src/mesmer/transforms/__init__.py`](../../src/mesmer/transforms/__init__.py), and [`src/mesmer/population_strategies.py`](../../src/mesmer/population_strategies.py)

External primary sources checked for recency:

- [Jailbroken: How Does LLM Safety Training Fail?](https://arxiv.org/abs/2307.02483)
- [Universal and Transferable Adversarial Attacks on Aligned Language Models](https://arxiv.org/abs/2307.15043)
- ["Do Anything Now": Characterizing and Evaluating In-The-Wild Jailbreak Prompts on Large Language Models](https://arxiv.org/abs/2308.03825)
- [GPT-4 Is Too Smart To Be Safe: Stealthy Chat with LLMs via Cipher](https://arxiv.org/abs/2308.06463)
- [Jailbreaking Black Box Large Language Models in Twenty Queries](https://arxiv.org/abs/2310.08419)
- [Tree of Attacks: Jailbreaking Black-Box LLMs Automatically](https://arxiv.org/abs/2312.02119)
- [HarmBench](https://arxiv.org/abs/2402.04249)
- [JailbreakBench](https://arxiv.org/abs/2404.01318)
- [Jailbreaking Leading Safety-Aligned LLMs with Simple Adaptive Attacks](https://arxiv.org/abs/2404.02151)
- [AdvPrompter](https://arxiv.org/abs/2404.16873)
- [Best-of-N Jailbreaking](https://arxiv.org/abs/2412.03556)
- [Reasoning-to-Defend](https://arxiv.org/abs/2502.12970)
- [Effective and Efficient Jailbreaks of Black-Box LLMs with Cross-Behavior Attacks](https://arxiv.org/abs/2503.08990)
- [Large reasoning models are autonomous jailbreak agents](https://www.nature.com/articles/s41467-026-69010-1)

This investigation intentionally avoids concrete harmful payloads. It discusses
attack mechanics at the abstraction level needed to design authorized red-team
infrastructure.

## What The Research Arc Actually Says

The key pattern across the literature is that "jailbreak" is the wrong center
of gravity if it means "a string." The more stable object is a search and
measurement process over target-visible interaction.

| Period | Research movement | Stable mechanism to extract |
| --- | --- | --- |
| 2023 failure modes | Jailbroken frames the problem as competing objectives, mismatched generalization, and safety-capability parity. In-the-wild jailbreak studies show recurring social and prompt families. Cipher-style work shows safety generalization gaps across representation. | Prompt-pattern guidance, representation transforms, benign canary tests, explicit threat-model metadata. |
| 2023 automation | PAIR and TAP turn jailbreak discovery into attacker-model loops with feedback, branching, pruning, judges, and query budgets. | Propose, query, evaluate, feedback, select, stop, trace. |
| 2023 token optimization | GCG shows that optimized suffix pressure can transfer across prompts and models, even when the visible suffix is not human-readable. | Separate suffix generation/application/scoring, multi-prompt evidence, multi-model transfer evidence, strict white-box boundary. |
| 2024 measurement | HarmBench and JailbreakBench make threat model, datasets, judges, artifacts, defenses, and cost accounting central. | Benchmarks, reproducible artifacts, judge metadata, over-refusal/robust-refusal metrics, standardized reports. |
| 2024-2025 cheap black-box scaling | Simple adaptive attacks, many-shot jailbreaks, AdvPrompter, and Best-of-N show that sampling, context length, trained generators, API quirks, and repeated augmentation can dominate clever hand design. | Budgeted search, augmentation operators, sampling curves, logprob/prefill capability flags, long-context state. |
| 2025 cross-behavior transfer | JCB uses successes from prior behaviors to reduce query cost on new behaviors. | Cross-objective memory, persistent seed pools, transfer-aware reward ledgers. |
| 2025-2026 reasoning and agency | Reasoning can strengthen defense, but LRMs can also become autonomous multi-turn adversaries. The Nature Communications version reports a simple adversary-target conversation harness with high observed ASR under their setup. | Conversation state, private adversary context, per-turn harm/refusal/disclaimer scores, strategy annotation, multi-judge agreement. |

The common denominator is not roleplay, suffixes, ciphers, trees, fuzzing, or
agents. Those are technique families. The common denominator is controlled
state evolution under observation.

That strongly supports Mesmer's current foundation.

## Current Mesmer Design In One Sentence

Mesmer is already becoming a typed red-team experiment runtime where named
techniques compile reusable operators into workflows, operators mutate typed
state through patches, target calls are explicit, and transitions preserve the
audit/replay trail.

This is the right abstraction level.

The current runtime exposes:

- `Technique`: user-facing recipe, such as `SingleTurnProbe`,
  `ProposedProbe`, `FrontierSearch`, or `PopulationFuzzing`.
- `Workflow`: internal control algebra, currently `Sequence` and `Loop`.
- `Operator`: executable state transition, such as `SeedFromObjective`,
  `Propose`, `QueryTarget`, `Evaluate`, `StopWhen`, `Select`,
  `AddFeedback`, `LoadPopulation`, `GenerateFromPopulation`, and
  `AssignReward`.
- `StateSlice`: typed runtime memory, including `Frontier`, `Attempts`,
  `TargetResponses`, `Evaluations`, `Feedback`, `PopulationPool`,
  `RewardLedger`, `StopSignal`, `Iteration`, and `Metadata`.
- `Transition`: before/patch/after execution record for replay and debugging.
- Strategy/service objects: proposers, evaluators, selectors, mutators,
  conditions, targets, actors, sources, and transforms.

The architecture decision in `CLAUDE.md` is also directionally correct: extract
stable reusable mechanics from papers, not paper-specific prompts, datasets,
thresholds, marker strings, or URLs.

## Alignment Assessment

### 1. Prompt Patterns Are Correctly Demoted

Early jailbreak research can tempt a framework into making prompt families the
root primitive. That would age badly.

Mesmer does the better thing:

- `prompts.PromptPattern` stores tactics, templates, proposer hints, source
  metadata, and transform suggestions.
- Prompt patterns are not executable by themselves.
- Concrete mechanical rewrites live under `transforms`.
- Model-generated candidates live under proposers.

This matches the research arc. "Do Anything Now" and the Jailbroken paper are
useful sources of pattern families, but PAIR, TAP, Best-of-N, JCB, and LRM
agents all show that the important part is how patterns are selected, mutated,
evaluated, and carried forward.

Verdict: keep this foundation.

### 2. Operator Runtime Matches Automated Black-Box Attacks

PAIR maps cleanly to:

```text
Seed -> Propose -> QueryTarget -> Evaluate -> StopWhen -> AddFeedback -> Select
```

TAP maps to the same core with branching and pruning pressure. JBFuzz/JCB-style
work maps to:

```text
LoadPopulation -> GenerateFromPopulation -> QueryTarget -> Evaluate -> AssignReward -> StopWhen
```

Best-of-N maps to high-volume proposal or transform sampling plus query budget,
evaluation, and early stop. AdvPrompter maps to a trained or hosted proposer.
The autonomous LRM paper maps to append-user proposal, explicit transcript
state, target query, per-turn evaluation, feedback, and loop control.

This is strong evidence that `Operator` is the right first-citizen extension
unit. Most new paper mechanics should become strategies inside existing
operators or new operators that read/write explicit state slices.

Verdict: keep `Operator` central.

### 3. Target Boundary Is A Strategic Constant

The target call is the expensive and safety-relevant boundary. Mesmer's
`ops.QueryTarget` makes it visible and records attempts/responses. This is
exactly what black-box red-team research needs because query counts, target
messages, target metadata, and response artifacts are part of the claim.

This also protects the architecture from a common mistake: hiding target calls
inside a proposer, evaluator, or dataset adapter. If target calls disappear into
helper services, query budgets and replay evidence become unreliable.

Verdict: keep all target interaction behind explicit target operators. Add
multi-target operators only if they preserve the same visibility.

### 4. Evaluation, Stopping, And Feedback Are Correctly Separate

The repo's rule that "evaluation is not stopping" and "feedback is not
evaluation" is one of the most important design constants.

Research supports this:

- PAIR and TAP need evaluator feedback even when no stop condition is met.
- Best-of-N needs repeated evaluation under a sampling budget.
- Benchmarks need scores and refusal labels even when no success is declared.
- LRM-agent experiments need per-turn harm, refusal, disclaimer, and strategy
  labels, not only a final pass/fail.

Collapsing these into a single judge primitive would make future comparisons
weak.

Verdict: keep the separation.

### 5. Black-Box GCG Handling Is Correct

The current docs are careful: Mesmer does not claim full GCG. True GCG requires
white-box access such as tokenizer, logits, losses, gradients, and token
replacement. Mesmer instead extracts black-box reusable mechanics:

- source-backed GCG prompt-pattern guidance;
- suffix-only proposal;
- deterministic suffix application;
- response-shape evaluation;
- selection, feedback, stopping, and replay around those pieces.

That is the right boundary. A hosted-model red-team framework should not pretend
it has gradients just because a paper uses gradients.

Verdict: keep black-box and white-box capability boundaries explicit.

### 6. Replay Is Not Nice-To-Have

Benchmarks and recent papers increasingly care about reproducibility,
artifacts, judge choice, costs, target versions, and threat model. Mesmer's
transition history, attempts, reproduction artifact direction, and benchmark
metrics line up with this.

The only caution: replay must expand from "successful prompt and response" to
"full experiment trajectory." For modern multi-turn and sampling attacks, the
failure cases, rejected candidates, per-turn scores, and budget curve are part
of the evidence.

Verdict: keep replay as a strategic constant, but widen what gets recorded.

## Where The Foundation Needs More First-Citizen Surface

These are not reasons to throw away the design. They are the next primitives
that should become obvious to users.

### 1. Conversation State Should Become First-Class

Current support:

- `Candidate.messages` can hold a target-visible transcript.
- `proposers.StructuredLLMProposer` supports `APPEND_USER`.
- `ops.ContinueConversation` can append target responses back into the
  candidate messages.
- Examples already model autonomous multi-turn canary tests with
  `FrontierSearch`.

This is enough to prove the kernel works, but it is not enough for the modern
LRM-agent research shape.

The LRM-agent paper needs:

- adversary-private system context;
- target-visible transcript;
- turn-by-turn target responses;
- per-turn harm, refusal, and disclaimer judgements;
- persuasive-strategy annotations for adversary messages;
- trajectory-level aggregates such as peak harm, average harm, refusal count,
  and success turn.

Recommended primitive additions:

| Primitive | Kind | Why |
| --- | --- | --- |
| `ConversationTrace` | State slice | Preserve target-visible turns separately from candidate metadata. |
| `AgentPrivateContext` | State slice or strategy-owned artifact | Keep hidden adversary objective and system instructions out of target replay while still auditable. |
| `TurnJudgements` | State slice | Store per-turn harm/refusal/disclaimer outputs and judge metadata. |
| `ops.AdvanceConversation` | Operator | Make adversary-target alternation explicit instead of encoding it as one proposer plus one target query. |
| `ops.AnnotateConversation` | Operator | Classify strategies and transcript-level patterns after turns accumulate. |
| `techniques.ConversationAgentProbe` | Technique | Give LRM-agent studies a named skeleton without forcing users to hand-roll loop order. |

Strategic point: `FrontierSearch` can express agent loops, but a named
conversation technique will make the threat model and evidence shape clearer.

### 2. Cross-Behavior Memory Needs A Durable Home

JCB's important shift is not synonym perturbation. It is cross-behavior
learning: previous successful prompts or seeds help new behavior searches.

Current support:

- `PopulationPool` and `RewardLedger` exist inside one objective run.
- Seed selectors include random, weighted, UCB, and EXP3.
- `AssignReward` can add successful seeds back into the pool.

Gap:

- The pool is still essentially run-local/objective-local.
- There is no obvious persistent memory that spans benchmark rows, target
  models, or behavior categories.

Recommended primitive additions:

| Primitive | Kind | Why |
| --- | --- | --- |
| `CrossBehaviorMemory` | State slice or benchmark-level service | Store transferable seeds, scores, source objective IDs, target IDs, and category metadata. |
| `MemoryBackedSeedPoolSource` | Source | Seed a new objective from prior successful or diverse candidates. |
| `ops.UpdateCrossBehaviorMemory` | Operator | Persist successful candidates and failed-but-informative variants after evaluation. |
| `TransferAwareSelector` | Selector | Rank candidates by both current score and historical cross-behavior utility. |

Strategic point: do not make a `JCBPrompt` primitive. Make cross-behavior
memory first-class.

### 3. Pre-Target Pruning Should Be Easier To Express

TAP's practical contribution includes pruning prompts before spending target
queries. Mesmer has the right pieces conceptually:

- `CandidateConstraint` exists in `strategies.py`.
- `ConstraintScoreSelector` can select by constraint results.
- The architecture documents constraints as operators whose workflow position
  determines when they run.

Gap:

- The current public operator set does not expose a clear `ops.Filter` or
  `ops.CheckConstraints`.
- `FrontierSearch` has a fixed body order of expand, query, evaluate, stop,
  feedback, select.

Recommended primitive additions:

| Primitive | Kind | Why |
| --- | --- | --- |
| `Constraints` | State slice | Store candidate-level pre-target assessments. |
| `ops.CheckConstraints` | Operator | Run LLM or deterministic checks before target calls. |
| `ops.Filter` | Operator | Drop or retain candidates before query. |
| `techniques.TreeSearch` or configurable `FrontierSearch` phases | Technique/workflow | Let TAP-style search place pruning before `QueryTarget` without custom workflow plumbing. |

Strategic point: pre-target pruning is not evaluation of target responses. It
deserves separate state and trace.

### 4. Evidence Matrices Should Become A Benchmark Primitive

Modern papers rarely claim "one prompt worked once." They claim performance
across:

- objectives;
- target models;
- judges;
- defenses;
- turns;
- attack variants;
- random seeds;
- budgets;
- sometimes modalities.

Current support:

- `Benchmark`, `BenchmarkRunner`, and basic metrics exist.
- `Run` binds objectives, attack, target, budget, recorder, and logger.
- Attempts preserve target metadata and judgements.

Gap:

- There is no first-class evidence matrix for multi-target/multi-judge/multi-turn
  aggregation inside a single report.
- Judge agreement is listed as a metric concept, but the richer paper shape
  needs per-judge records and agreement statistics.
- Peak harm, success turn, refusal count, disclaimer count, and per-turn
  trajectory curves are not yet obvious primitives.

Recommended primitive additions:

| Primitive | Kind | Why |
| --- | --- | --- |
| `EvidenceMatrix` | Benchmark/report model | Index results by objective, target, judge, turn, technique, defense, and seed. |
| `JudgePanel` | Strategy/service | Run multiple evaluators and preserve individual outputs before aggregation. |
| `AggregateEvidence` | Operator or benchmark stage | Compute peak score, average score, ASR, refusal rate, disclaimer rate, agreement, and confidence intervals. |
| `BudgetCurve` | Report model | Preserve success probability versus query/sample budget. |

Strategic point: benchmarks are becoming part of the primitive system, not only
an outer loop around attacks.

### 5. Sampling And Augmentation Need A Native Shape

Best-of-N shows a simple but important principle: repeated variation can scale
success with budget. Many-shot work shows context size itself can become the
attack surface. Simple adaptive attacks show that API details such as logprobs
or prefilling can matter.

Current support:

- `FrontierSearch` can branch.
- `PopulationFuzzing` can mutate seed templates.
- `transforms` can encode, wrap, split, rewrite characters, compose, and append
  suffixes.
- Budget tracking exists.

Gaps:

- There is no explicit "sample N variants and report curve" technique.
- Text transforms are not yet represented as an ordinary `ops.ApplyTransforms`
  operator in the current implementation.
- The message model is text-only, while BoN-style results extend across
  modalities.
- Logprob and prefill access are not modeled as explicit target capabilities.

Recommended primitive additions:

| Primitive | Kind | Why |
| --- | --- | --- |
| `ops.ApplyTransforms` | Operator | Execute deterministic transforms as traceable state transitions. |
| `techniques.BestOfNProbe` | Technique | Make high-volume sampling, early stop, and budget curves obvious. |
| `AugmentationPolicy` | Strategy | Choose randomization, casing, shuffling, formatting, modality-specific perturbations, and seeds. |
| `TargetCapabilities` | Target metadata | Declare strict black-box, logprob-enabled, prefill-enabled, multimodal, tool-enabled, or streaming access. |
| `ContentBlock` message model | Artifact model | Support text, image, audio, file, and tool result content without changing the runtime kernel. |

Strategic point: "black-box" should not become a vague label. Mesmer should
record the exact API affordances used by an experiment.

### 6. White-Box Should Stay Out Of The Black-Box Kernel

The user asked to think only about black-box for now. That is correct for
Mesmer's current priority.

But the architecture should reserve a future white-box capability boundary:

- tokenizer access;
- logits/logprobs;
- loss definitions;
- gradient access;
- token replacement;
- model weights or local inference hooks.

These should not be smuggled into `Proposer`. They should be a separate
capability family later, with a different target/model adapter and a different
optimizer strategy. Keeping that boundary clean is what lets the
black-box foundation stay honest.

## Strategic Constants To Keep

These constants are correct and should survive future primitive work.

### Authorized, Benign Harnesses First

Paper-inspired examples should use canaries, authorized readiness checks, safe
mirrors, or user-provided private benchmarks. Do not vendor harmful datasets or
operational payloads into core examples.

### Technique Names Are Recipes, Not Foundations

`PAIR`, `TAP`, `JBFuzz`, `GCG`, `BoN`, and LRM-agent examples are useful names
for examples and paper reproductions. They should not become the root
framework vocabulary. The root vocabulary should stay:

```text
State slices, operators, workflows, transitions, techniques, strategies,
sources, targets, evaluators, selectors, mutators, observability, benchmarks.
```

### Extract Mechanics, Not Prompts

This is already in `CLAUDE.md`, and it is the right rule. The durable extraction
from a paper is usually a loop shape, state requirement, scoring method,
selection strategy, memory rule, target capability, or benchmark schema.

### Keep Target Calls Visible

Any operator that queries a target should declare it, be budgeted, and produce
replayable messages and metadata. This becomes more important as techniques
move from single-turn prompts to multi-turn agents and high-volume sampling.

### Structured Output Is The Control Contract

Any LLM-backed primitive that drives machine-readable control flow should use
provider-enforced structured output and schema validation. This is especially
important for attacker proposers, judges, strategy annotators, and seed
generators.

### Replay Must Include The Path, Not Only The Winning Leaf

For modern black-box research, the failed branches, budgets, intermediate
judgements, target versions, and evaluator versions are part of the finding.
Winning prompts alone are weak evidence.

### Threat Model Metadata Is Required Evidence

Every run should preserve at least:

- target model and provider;
- attacker model and provider, if used;
- judge model and rubric, if used;
- generation parameters;
- target capability level;
- dataset/objective source;
- budget limits;
- safety or defense setting;
- timestamp or version metadata;
- replay messages.

## First-Principle Check

### Principle: Jailbreaks Are State Transitions Under Pressure

Correct. The techniques differ, but they all transform state: a prompt becomes
a candidate, a candidate becomes a response, a response becomes evidence,
evidence becomes feedback, feedback becomes new candidates, and the run either
stops or continues.

This principle will stay relevant.

### Principle: The Runtime Should Be More Stable Than The Technique Names

Correct. PAIR, TAP, BoN, JCB, and LRM-agent harnesses are all expressible as
different workflow recipes over shared primitives. This is exactly why
`Technique` should be a recipe layer rather than the foundation.

This principle will stay relevant.

### Principle: Evaluation Is Evidence, Not Control Flow

Correct. Evaluation outputs should be facts in state. Stop conditions, selectors,
feedback builders, and reports consume those facts differently.

This principle will stay relevant.

### Principle: Prompt Patterns Are Data, Not Execution

Correct. Prompt families are useful, but if prompt patterns become executable
runtime behavior, the framework becomes brittle and paper-shaped.

This principle will stay relevant.

### Principle: Black-Box And White-Box Are Different Capability Classes

Correct. Some papers report transfer from white-box methods to black-box
targets, but the mechanism that produced the artifact is still white-box.
Mesmer should model black-box analogues honestly and reserve white-box
optimization for a future capability family.

This principle will stay relevant.

### Principle: Reproducibility Is A Core Feature

Correct. The field is moving toward benchmark artifacts, threat models, cost
accounting, judge details, and defense comparisons. Replay and audit are not
secondary implementation concerns.

This principle will become more important.

## What Would Make Mesmer Drift Off Course

These are the failure modes to actively avoid.

### Failure Mode 1: Making Paper Names Core API

Bad direction:

```text
PAIRPrompt
TAPPrompt
JBFuzzPrompt
GCGPrompt
BoNPrompt
```

Better direction:

```text
StructuredLLMProposer
TopKSelector
ConstraintScoreSelector
PromptMutator
AppendSuffix
ApplyTransforms
CrossBehaviorMemory
EvidenceMatrix
ConversationTrace
```

Paper names belong in examples, docs, source metadata, and technique recipes.
Reusable primitives should name their responsibility.

### Failure Mode 2: Treating Metadata As A Substitute For State

Metadata is useful for irregular details, but core mechanics should become
typed state slices when they drive behavior or evidence. Conversation turns,
per-turn judgements, cross-behavior memory, and budget curves should not live
forever as loose dictionaries.

### Failure Mode 3: Hiding Expensive Calls In Strategies

Strategies can call helper models when they are explicitly attacker actors,
judges, mutators, or classifiers. But target calls should stay in target
operators. If a proposer quietly queries the target, the budget and replay model
break.

### Failure Mode 4: Only Recording Successes

For Best-of-N, JCB, TAP, and LRM-agent work, failures explain the search process.
If Mesmer records only the final successful candidate, it cannot support serious
research claims.

### Failure Mode 5: Hard-Coding Single-Turn Assumptions

Single-turn prompting was the first wave. The current frontier is multi-turn,
long-context, multi-objective, and multi-model. A future-proof Mesmer should
treat single-turn as a special case of a richer interaction trace.

## Recommended Architecture Decisions

### Decision 1: Keep The Kernel

Do not replace `State + Operator + Transition + Workflow`.

This kernel matches the evolution of black-box jailbreak research better than a
taxonomy tree of attack names.

### Decision 2: Promote Conversation To First-Citizen State

Add typed state and operators for multi-turn adversary-target experiments. Do
not rely only on `Candidate.messages` plus metadata for the long term.

Suggested sequence:

```text
SeedConversation
Loop:
  ProposeNextUserTurn
  QueryTarget
  RecordConversationTurn
  EvaluateTargetTurn
  AnnotateAdversaryTurn
  AddFeedback
  StopWhen
```

### Decision 3: Promote Cross-Behavior Memory

Add persistent memory that can span objectives inside a benchmark run and,
optionally, across saved experiment sessions. This is the reusable primitive
behind JCB-style efficiency.

### Decision 4: Add Pre-Target Constraint Operators

Make TAP-style pruning explicit. Add constraint state and filter/check
operators that can run before `QueryTarget`.

### Decision 5: Make Transform Execution Traceable

The transform library is useful, but deterministic transforms should have a
standard operator path so they appear in workflow graphs and transitions.

### Decision 6: Add Evidence Matrix Reporting

Benchmark reports should be able to represent:

- objective x target x judge x turn x technique x seed;
- peak score and success turn;
- refusal and disclaimer rates;
- judge agreement;
- query and cost curves;
- target capability metadata;
- replay references.

### Decision 7: Separate Strict Black-Box From API-Affordance Black-Box

Record whether an experiment used:

- ordinary chat completions only;
- logprobs;
- assistant prefill;
- system prompt control;
- multiple target models;
- tool calls;
- streaming;
- multimodal inputs.

This prevents "black-box" from hiding important differences across papers.

### Decision 8: Prepare Message Artifacts For Multimodal Runs

The current `Message.content: str` model is fine for text-only Mesmer. Future
BoN-style multimodal red-teaming needs structured content blocks. This can be
introduced without changing the kernel.

## Primitive Roadmap

Recommended priority order:

1. `ops.ApplyTransforms`, `Constraints`, `ops.CheckConstraints`, `ops.Filter`.
   This closes an immediate gap between documented transform/constraint
   concepts and traceable operator execution.
2. `ConversationTrace`, `TurnJudgements`, and `ConversationAgentProbe`. This
   aligns Mesmer with the 2025-2026 reasoning-agent direction.
3. `EvidenceMatrix`, `JudgePanel`, and richer benchmark reports. This makes
   Mesmer research-grade for paper comparisons.
4. `CrossBehaviorMemory` and memory-backed population sources. This captures
   JCB-style transfer and makes population fuzzing more strategic.
5. `BestOfNProbe`, `AugmentationPolicy`, and `BudgetCurve`. This captures
   cheap black-box sampling as a named technique.
6. `TargetCapabilities` and optional logprob/prefill metadata. This keeps
   threat models precise.
7. `ContentBlock` message artifacts. This prepares for multimodal black-box
   red-teaming without polluting the core runtime.

## Final Verdict

Mesmer's foundation is correct because it chooses the stable object:
replayable state-transition experiments.

The future of black-box jailbreaking will keep changing names. The
mechanics are more durable:

- search;
- mutation;
- feedback;
- selection;
- transfer;
- conversation;
- budget;
- evidence;
- replay.

Mesmer already has the right center for those mechanics. The next step is to
make the richer modern evidence objects first-class, especially conversation
state, cross-behavior memory, and benchmark matrices.

Do that, and Mesmer does not need to chase every paper with a new framework. It
can absorb each paper as another workflow recipe over a small set of durable
experiment primitives.
