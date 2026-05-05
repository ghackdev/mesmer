# Primitive Taxonomy Audit

This audit records the primitive taxonomy that now shapes the public Mesmer API
after the TAP, PAIR, JBFuzz, and autonomous jailbreak-agent examples.

## Executive Verdict

The strongest path is to treat `runtime.Program` plus ordered `Component` trees as the
canonical execution substrate for paper techniques. TAP, PAIR, JBFuzz, and the
autonomous jailbreak-agent example already map cleanly onto that substrate.

The main duplication was older topology code: graph-style and direct-flow
classes encoded control loops that overlapped with `runtime.Program`,
`topology.Iterate`, `generation.Propose`, `targeting.Query`,
`evaluation.Assess`, `stopping.StopWhen`, and `feedback.Refine`. Those surfaces
have been removed from the public API instead of kept as compatibility shims.

The largest gap exposed by the paper examples is evolutionary and population
search. JBFuzz introduced reusable seed pools, seed selectors, mutators, and
reward updates, but these are still named around prompt fuzzing rather than a
general evolutionary search family.

## Taxonomy Verdicts

| Family | Current primitives | Verdict | Notes |
| --- | --- | --- | --- |
| Execution substrate | `runtime.Program`, `Component`, `ContainerComponent`, `RuntimeState`, `StatePatch`, `StateFact`, `topology.Search` | Keep and formalize | This is the clearest reusable core. `StatePatch` plus transition history makes execution typed and replayable enough for current papers. |
| Algorithm topology | `topology.Iterate`, removed legacy direct-flow surfaces | Merge and deprecate legacy topology | `topology.Iterate` inside `runtime.Program` is the generic topology. Legacy flows duplicate orchestration and should not be the default authoring path for new papers. |
| State initialization | `initialization.Seed`, `population.Initialize`, paper state subclasses such as `TapState`, `PairState`, `JBFuzzState` | Formalize | `initialization.Seed` is generic. `population.Initialize` is reusable but should eventually sit under evolutionary/population search. Paper-specific state subclasses are acceptable when they document algorithm data. |
| Candidate generation | `generation.Propose`, `generation.StructuredLLM`, `generation.Template`, `population.Generate` | Generalize | `generation.Propose` plus `Proposer` is solid for LLM proposal. Fuzz generation is reusable but should become a population/evolutionary generator. |
| Candidate transformation/mutation | `variation.Mutator`, `variation.LLMTemplate`, `variation.LexicalSubstitution` | Generalize and merge | Mutation is the broader concept. Deterministic rewrites should use generation or variation primitives with typed provenance. |
| Filtering and selection | `constraints.Filter`, `selection.Select`, `feedback.Refine`, `selection.TopK`, `selection.ConstraintScore`, population selectors | Formalize and merge | Selectors are core. Population selectors are selection policies and should remain separate from frontier selectors unless a shared ranking protocol emerges. |
| Target interaction | `targeting.Query`, `targeting.Continue`, target bindings | Keep | `targeting.Query` is the right target boundary. `targeting.Continue` cleanly models multi-turn transcript accumulation. |
| Evaluation and judgement | `evaluation.Assess`, `evaluation.Evaluator`, `evaluation.LLMRating`, classifier evaluators, legacy `Judge` implementations | Merge gradually | `evaluation.Assess` with `evaluation.Evaluator` is the right search-time API. Legacy `Judge` remains useful at the run boundary and for existing flows, but new paper loops should prefer evaluators inside `evaluation.Assess`. |
| Stopping | `stopping.StopWhen`, `stopping.ScoreAtLeast`, `topology.Policy`, budget trackers | Keep and formalize | Stop conditions correctly consume evaluation facts. Budget policy remains outside the component tree and should stay there. |
| Feedback and learning | `feedback.Template`, trajectory feedback/history, seed reward updates | Generalize | Feedback is well separated from evaluation. Seed reward update should become a more general population-credit primitive. |
| Data sources | `ObjectiveSource`, `RemoteDatasetSource`, `SeedPoolSource` variants | Keep | Objective data sources are mature. Seed-pool sources should be documented as population initialization sources, not only fuzzing. |
| Observability and replay | `RuntimeState.history`, attempts, reproduction artifacts, metadata, recorder | Keep and formalize | This is a project strength. New primitives should preserve typed provenance and replay messages. |

## Paper Mapping

| Paper example | Topology | Initialization | Generation and mutation | Filtering/selection | Target/evaluation | Stopping/feedback |
| --- | --- | --- | --- | --- | --- | --- |
| TAP | `runtime.Program` -> `initialization.Seed` -> `topology.Iterate` | `TapState`, remote AdvBench source | `generation.StructuredLLM` with TAP attacker prompts | `LLMLabelConstraint`, `selection.ConstraintScore`, `selection.TopK` in `feedback.Refine` | `targeting.Query`, `evaluation.LLMRating` | `ScoreAtLeast(10)`, TAP feedback template |
| PAIR | `runtime.Program` -> `PairSeed` -> `topology.Iterate` | `PairState`, built-in/local objectives | `generation.StructuredLLM`; `PairSeed` creates independent streams | `selection.TopK(k=streams)` in `feedback.Refine` | Metered actor/target wrappers, `evaluation.LLMRating` | `stopping.ScoreAtLeast`, feedback template, usage trace |
| JBFuzz | `runtime.Program` -> `population.Initialize` -> `initialization.Seed` -> `topology.Iterate` | `JBFuzzState` with `population.Pool`; remote question/seed datasets | `population.Generate`; `variation.Mutator` via LLM or lexical substitution | Seed selectors (`WeightedRandom`, `UCB`, `EXP3`), `selection.TopK` | `targeting.Query`; LLM, HF, or embedding classifier evaluators | `population.UpdateRewards`, `stopping.ScoreAtLeast`, optional successful seed insertion |
| Autonomous jailbreak agent | `runtime.Program` -> `initialization.Seed` -> `topology.Iterate` | `AutonomousJailbreakAgentState`, built-in/local objectives | `generation.StructuredLLM` with `APPEND_USER` message mode | `selection.TopK(k=1)` in `feedback.Refine` | `targeting.Query`, `evaluation.LLMRating`, `targeting.Continue` | `stopping.ScoreAtLeast`, transcript-aware feedback |

## Duplication Matrix

| Overlap | Duplicated responsibility | Preferred direction |
| --- | --- | --- |
| Legacy graph topology vs `runtime.Program`/`Component` | Both define ordered execution, frontier mutation, target calls, stopping, and attempt recording. | `runtime.Program`/`Component` is canonical. The graph topology has been removed from the public API rather than kept as a compatibility wrapper. |
| Legacy direct flows vs `topology.Search` | Direct flow classes encoded search loops that `topology.Iterate` plus components can already express. | New paper examples should use `topology.Search`; the duplicate direct-flow surface has been removed. |
| Legacy expander/pruner protocols vs `Proposer`/`FrontierSelector` | Expanders generated candidates and pruners selected frontiers without trajectory history or typed evaluation results. | Prefer `Proposer` and `FrontierSelector`; useful template and keyword behavior now lives under `generation` and `selection`. |
| `Judge` vs `evaluation.Evaluator` inside `evaluation.Assess` | Both score target responses and produce pass/fail style results. | Use `evaluation.Evaluator` inside search loops. Keep `Judge` as the run-level compatibility API and bridge judges to evaluators only where necessary. |
| Fuzzing seed/reward mechanics vs evolutionary primitives | `population.Pool`, seed selectors, mutators, and rewards are useful beyond JBFuzz but named narrowly. | Promote them into a formal evolutionary/population search family with generic population, variation, selection, and credit assignment responsibilities. |
| `Transform` vs `variation.Mutator` | Both rewrite candidate text. `Transform` returns candidate lists; mutators return mutation provenance and are used by fuzz generation. | Keep transforms for deterministic one-off candidate rewriting; use mutators for stochastic or learned variation with reward/provenance. Document the boundary. |

## Evaluation Criteria By Category

### Core vs Paper Specific

Core primitives are those that describe recurring runtime responsibilities:
execution, topology, initialization, proposal, mutation, selection, query,
assessment, stopping, feedback, data loading, and replay.

Paper-specific material should stay in examples when it is a prompt template,
dataset URL, threshold, marker string, model choice, CLI default, or paper-named
state subclass whose only purpose is explanation.

### Naming

Generic primitive names should describe responsibility, not paper origin.
`generation.StructuredLLM`, `selection.TopK`, `stopping.ScoreAtLeast`, and
`RemoteDatasetSource` pass this test. `TapState`, `PairSeed`, and
`JBFuzzState` are acceptable because they live in examples. `population.Generate`
and `population.Pool` are reusable but narrow; future extraction should keep the
semantic-slot DSL instead of restoring long suffix names.

### Declarative Parameters

The newer search primitives are mostly declarative: policies carry iterations,
width, branching factor, parallelism, and stop behavior; selectors carry `k` or
scoring fields; evaluators carry scales and failure policies. The weak spots are
paper scripts that directly implement metering wrappers or local preflight
helpers.

### Typed And Replayable State

`RuntimeState`, `CandidateTrajectory`, `EvaluationResult`, `ConstraintResult`,
`Attempt`, and reproduction artifacts are typed enough to replay successful
target calls. `StatePatch.summary()` intentionally stores compact transition
history rather than full state dumps. That is the right default, provided new
components continue to put replay-critical details into candidate metadata,
trajectory provenance, attempts, or reproduction artifacts.

The fuzzing seed pool is typed, but it is currently stored dynamically through
`state_field` and `setattr`. This works for paper examples but should be made
more explicit if population state becomes a core primitive family.

### Overlap Boundaries

The cleanest boundaries are:

- Components mutate runtime state; services such as actors, selectors,
  evaluators, mutators, targets, and data sources are invoked by components.
- Evaluators produce evaluation facts; stop components consume those facts.
- Constraints filter candidates at the point where they appear in the component
  order; they are not special pre-target gates.
- Feedback translates observations into attacker context; it is not evaluation.
- Target interaction is centralized in `targeting.Query`; conversation transcript updates
  happen in `targeting.Continue`.

## Proposed Formal Taxonomy

Future primitives should be classified into one of these families:

| Family | Responsibility boundary |
| --- | --- |
| Runtime substrate | Executes ordered components and records state transitions. Includes `runtime.Program`, `Component`, `RuntimeState`, `StatePatch`, and `StateFact`. |
| Topology components | Define loop or control shape without embedding paper prompts or scoring logic. Includes `topology.Iterate` and future population or beam-loop containers. |
| Initialization components | Create initial frontier, population, or state. Includes `initialization.Seed` and seed/pool initialization. |
| Generation services/components | Produce new candidate trajectories from state. Includes `generation.Propose`, `Proposer`, and future population generators. |
| Variation services | Transform or mutate candidate material with typed provenance. Includes `variation.Mutator`, lexical mutators, and LLM template mutators. |
| Constraint components | Check and optionally filter candidates according to declared constraints. Includes `constraints.Filter` and `CandidateConstraint`. |
| Selection services/components | Rank or retain frontier/population elements. Includes `FrontierSelector`, seed selectors, and future population selectors. |
| Target components | Call targets and append responses/attempts. Includes `targeting.Query` and target bindings. |
| Evaluation components/services | Score target responses or trajectories. Includes `evaluation.Assess` and `evaluation.Evaluator`. |
| Stopping components | Convert state facts into stop signals. Includes `stopping.StopWhen` and `TerminationCondition`. |
| Feedback/learning components | Convert observations into future search context or update credit. Includes `feedback.Template`, trajectory feedback, and seed reward updates. |
| Data sources | Load objectives, datasets, or initial populations. Includes `ObjectiveSource`, `RemoteDatasetSource`, and seed-pool sources. |
| Observability/replay | Record state history, attempts, artifacts, and provenance. Includes runtime history, recorders, and reproduction artifacts. |

## Naming Rules

- Use responsibility names for reusable primitives: `Proposer`, `Selector`,
  `Evaluator`, `Mutator`, `Condition`, `Source`, `Component`.
- Keep paper names in example files, prompts, state subclasses, CLI flags, and
  README text unless the primitive is only meaningful for that paper.
- Do not add a new topology class when an ordered `runtime.Program` with components can
  express the loop.
- Do not add a new evaluator-like class outside `evaluation.Evaluator` unless it is
  a run-level `Judge` compatibility object.
- Do not add a new selector/pruner family without explaining why
  `FrontierSelector`, seed selection, or future population selection cannot
  express it.
- Store replay-critical state in typed models or metadata with stable keys.

## Recommendation For The Next Paper

The next paper should target evolutionary/population search. JBFuzz already
forced most of the necessary primitives into existence, but their names and
state boundaries are still fuzzing-specific. A second evolutionary paper would
show whether seed pools, mutation, selection, and reward updates should be
formalized into generic population primitives or kept as a JBFuzz-style
specialization.

Multi-turn escalation is already represented by `targeting.Continue`,
`APPEND_USER` proposal mode, trajectory feedback, and the autonomous
jailbreak-agent example. Token/logit optimization is a larger substrate change
because it needs target/logprob capabilities and candidate representations below
message text. It should wait until the population-search boundary is clearer.

## CLAUDE.md Update Plan

The durable conventions from this audit should be recorded in `CLAUDE.md`:

- Accept the taxonomy families listed above as the default vocabulary.
- Treat `runtime.Program`/`Component`/`RuntimeState`/`StatePatch` as the canonical
  execution substrate for new paper techniques.
- Require new paper examples to justify any new primitive family against the
  existing topology, selector, evaluator, mutation, feedback, and data-source
  families.
- Keep paper-specific prompts, datasets, thresholds, URLs, and marker strings in
  examples unless they reveal a reusable mechanism.
- Avoid adding direct `Flow` subclasses, expander/pruner families, or judges for
  behavior that can be expressed as components, proposers, selectors, or response
  evaluators.
- Treat JBFuzz-style seed pools, mutation, selection, and reward updates as the
  candidate area for a future formal evolutionary/population taxonomy.
