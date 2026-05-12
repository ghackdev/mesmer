# Evolution of LLM Jailbreaking Techniques

This document is based on the local paper set in
`/Users/galihlarasprakoso/Downloads/LLM Jailbreaking` as of 2026-05-10
in the local Asia/Makassar environment.
It is written as a research map for Mesmer, not as an operational jailbreak
guide. The goal is to understand which technique families still matter, which
ones are mostly historical, and what primitives Mesmer should support for the
next wave of LLM jailbreak research.

## Executive Summary

LLM jailbreaking did not evolve from weak prompts to one perfect attack. It
evolved from prompt tricks into experiment systems.

The early 2023 view was: jailbreaks work because safety training fails under
competing objectives and mismatched generalization. The field then split into
two tracks. One track optimized input strings, suffixes, templates, and surface
forms. The other track automated the red-team loop: propose candidates, query
the target, judge the response, refine, branch, prune, and reuse successful
patterns.

Across the 2026 papers in this corpus, the attack surface is no longer only
"the user's prompt". The papers study long context, multi-turn conversation
state, style shifts, sampling variance, cross-behavior memory, chat templates,
classifier boundaries, reasoning-agent behavior, and sometimes model internals.
The defensive lesson is also clearer: refusal behavior that works on obvious
single-turn harmful requests does not prove robust safety.

## Corpus Scanned

The folder contains 25 PDFs:

| File | Paper |
| --- | --- |
| `2307.02483v1.pdf` | Jailbroken: How Does LLM Safety Training Fail? |
| `2307.15043v2.pdf` | Universal and Transferable Adversarial Attacks on Aligned Language Models |
| `2308.03825v2.pdf` | "Do Anything Now": Characterizing and Evaluating In-The-Wild Jailbreak Prompts on Large Language Models |
| `2308.06463v2.pdf` | GPT-4 Is Too Smart To Be Safe: Stealthy Chat with LLMs via Cipher |
| `2310.08419v4.pdf` | Jailbreaking Black Box Large Language Models in Twenty Queries |
| `2310.15140v2.pdf` | AutoDAN: Interpretable Gradient-Based Adversarial Attacks on Large Language Models |
| `2312.02119v3.pdf` | Tree of Attacks: Jailbreaking Black-Box LLMs Automatically |
| `2402.04249v2.pdf` | HarmBench: A Standardized Evaluation Framework for Automated Red Teaming and Robust Refusal |
| `2404.01318v5.pdf` | JailbreakBench: An Open Robustness Benchmark for Jailbreaking Large Language Models |
| `2404.02151v4.pdf` | Jailbreaking Leading Safety-Aligned LLMs with Simple Adaptive Attacks |
| `079017-4121open.pdf` | Many-shot Jailbreaking |
| `2404.16873v2.pdf` | AdvPrompter: Fast Adaptive Adversarial Prompting for LLMs |
| `2412.03556v2.pdf` | Best-of-N Jailbreaking |
| `2502.12970v3.pdf` | Reasoning-to-Defend: Safety-Aware Reasoning Can Defend Large Language Models from Jailbreaking |
| `2503.08990v2.pdf` | Effective and Efficient Jailbreaks of Black-Box LLMs with Cross-Behavior Attacks |
| `2508.04039v1.pdf` | Large Reasoning Models Are Autonomous Jailbreak Agents |
| `2511.15304v3.pdf` | Adversarial Poetry as a Universal Single-Turn Jailbreak Mechanism in Large Language Models |
| `2601.02670v1.pdf` | Multi-Turn Jailbreaking of Aligned LLMs via Lexical Anchor Tree Search |
| `2602.15001v2.pdf` | Boundary Point Jailbreaking of Black-Box LLMs |
| `2604.10326v1.pdf` | Jailbreaking the Matrix: Nullspace Steering for Controlled Model Subversion |
| `2604.11309v1.pdf` | The Salami Slicing Threat: Exploiting Cumulative Risks in LLM Systems |
| `2604.12232v1.pdf` | TemplateFuzz: Fine-Grained Chat Template Fuzzing for Jailbreaking and Red Teaming LLMs |
| `2604.18487v1.pdf` | Adversarial Humanities Benchmark: Results on Stylistic Robustness in Frontier Model Safety |
| `AB_jailbreaking_-_a_novel_hybrid_framework_for_exp.pdf` | AB Jailbreaking - A Novel Hybrid Framework for Exploitation of Adversarial Vulnerabilities in LLMs |
| `s41467-026-69010-1.pdf` | Large Reasoning Models Are Autonomous Jailbreak Agents, Nature Communications version |

## Validation Notes

I validated the document against extracted text from the local PDFs, not against
live web metadata. One PDF extraction emitted a repair warning from `pdftotext`,
but text was still produced and scanned. The Nature Communications PDF and the
`2508.04039v1` PDF are two versions of the same study, so they are treated as a
single research item in the analysis even though both files are listed.

The relevance labels in this document are judgments for Mesmer research
planning, not universal rankings. Relevance depends on threat model:
open-weight vs closed API, white-box vs black-box, single-turn vs multi-turn,
text-only vs multimodal, and whether the system exposes logprobs, prefilling,
chat templates, or classifier feedback.

The validation pass corrected two weak assumptions from the initial draft:

- The in-the-wild DAN paper supports prompt injection, privilege escalation,
  deception, and virtualization as major observed strategies. Broader families
  such as attention shifting and persuasion are real in the surrounding
  literature, but should not be attributed as the main taxonomy of that paper.
- Unreadable GCG-style suffixes are more exposed to perplexity and input-shape
  filtering than readable attacks, but "detectable" is not a complete defense
  claim. The GCG paper itself discusses attacking detectors, and AutoDAN is
  explicitly designed to bypass perplexity-style filters.

## Paper-by-Paper Validation Summary

| Paper | Local evidence checked | Implication used in this document |
| --- | --- | --- |
| Jailbroken | Abstract and method sections propose competing objectives and mismatched generalization, then instantiate jailbreak families from those failure modes. | Foundation for labeling later techniques by failure mode. |
| Universal and Transferable Adversarial Attacks | Abstract describes optimizing suffixes that make affirmative responses more likely across behaviors; paper reports transfer across models. | Token-level suffix optimization is a core historical and stress-test technique. |
| Do Anything Now | Abstract and contribution text describe 1,405 in-the-wild prompts, prompt sharing platforms, prompt injection, privilege escalation, deception, virtualization, and prompt evolution over time. | Use as in-the-wild taxonomy evidence, not as proof of every later prompt family. |
| CipherChat | Abstract proposes CipherChat and SelfCipher to test unsafe requests represented through ciphered forms. | Encoding and representation shifts test mismatched generalization. |
| PAIR | Abstract and conclusion describe Prompt Automatic Iterative Refinement using an attacker LLM, target LLM, iterative querying, and semantic prompt-level jailbreaks with black-box access. | Canonical black-box propose-query-evaluate-refine loop. |
| AutoDAN | Abstract introduces interpretable gradient-based attacks that optimize for jailbreak and readability, including bypass of perplexity filters. | Readable optimization bridges GCG-style search and human-readable prompts. |
| TAP | Abstract presents Tree of Attacks with Pruning, using attacker and evaluator LLMs, branching, pruning, and black-box target access. | Search topology and pruning become first-class mechanics. |
| HarmBench | Abstract describes standardized automated red-team evaluation, 18 methods, 33 LLMs/defenses, breadth, comparability, and robust metrics. | Evaluation claims need comparable behavior sets, judges, costs, and defenses. |
| JailbreakBench | Abstract describes open artifacts, 100 behaviors, threat model, system prompts, chat templates, scoring functions, and leaderboard. | Reproducible artifacts and exact harness details matter. |
| Simple Adaptive Attacks | Abstract emphasizes logprob access, target-specific templates, random suffix search, Claude prefilling/transfer, and API-specific vulnerabilities. | Adaptivity and API details can dominate static prompt comparisons. |
| Many-shot Jailbreaking | Abstract describes hundreds of demonstrations, larger context windows, power-law behavior, and broad closed-model success. | Long context is an attack surface, not just more room for the same prompt. |
| AdvPrompter | Abstract describes a trained adversarial prompt generator that produces human-readable prompts quickly and transfers to black-box models. | Prompt generation can become a learned component rather than per-objective search. |
| Best-of-N Jailbreaking | Abstract describes repeated augmented sampling across text, vision, and audio, with power-law-like ASR scaling and composition with other attacks. | Sampling variance and multimodal augmentation are practical black-box primitives. |
| Reasoning-to-Defend | Abstract proposes safety-aware reasoning, pivot tokens, and Contrastive Pivot Optimization. | Reasoning is a defensive mechanism as well as an attack capability. |
| JCB | Abstract describes reusing successes from past behaviors, no auxiliary LLM calls for discovery, fewer queries, and zero-shot transferability. | Cross-behavior memory and seed reuse should be first-class Mesmer objects. |
| Large Reasoning Models Are Autonomous Jailbreak Agents | Abstract describes four LRMs steering nine target models in multi-turn conversations from private instructions; Nature version reports the same study as a peer-reviewed article. | Reasoning models can act as autonomous adversarial conversation drivers. |
| Adversarial Poetry | Abstract describes poetic reformulation as a universal single-turn technique across providers and risk domains, validated with LLM judges and human checks. | Stylistic transformation alone can be a high-leverage representation shift. |
| LATS | Abstract describes attacker-LLM-free lexical anchor injection with breadth-first tree search over multi-turn dialogues and low query counts. | Multi-turn search can be structured and lexical, not only generated by an attacker LLM. |
| BPJ | Abstract describes black-box boundary-point optimization using only binary classifier feedback and curricula of intermediate targets. | Deployed classifiers and guardrails are target surfaces with their own search loops. |
| HMNS | Abstract proposes Head-Masked Nullspace Steering with causal-head attribution, masking, nullspace perturbation, and closed-loop intervention. | White-box internal steering is important but threat-model-specific. |
| Salami Slicing | Abstract proposes cumulative low-risk inputs that individually evade thresholds but accumulate harmful intent across turns and modalities. | Risk scoring needs transcript-level accumulation, not only per-turn classification. |
| TemplateFuzz | Abstract describes fine-grained chat-template mutation, heuristic search, active-learning oracle, open-source and commercial-model evaluations. | Chat serialization and templates are first-class red-team surfaces. |
| Adversarial Humanities Benchmark | Abstract describes humanities-style transformations preserving harmful intent, with transformed ASR far above original baseline prompts. | Safety evaluation must test stylistic robustness, not only explicit harmful phrasing. |
| AB-JB | Abstract describes a three-stage hybrid framework combining black-box semantic variants, judge filtering, and embedding/token suffix optimization. | Hybrid semantic plus lower-level optimization is a practical pipeline pattern. |

## Timeline

| Period | Technique family | Representative papers | What changed |
| --- | --- | --- | --- |
| Mid 2023 | Failure-mode framing | Jailbroken | Jailbreaks became explainable as failures of objective conflict and generalization, not just internet prompt folklore. |
| Mid to late 2023 | Token and suffix optimization | Universal and Transferable Adversarial Attacks, AutoDAN | Attacks became machine-generated. Optimized suffixes can transfer, but unreadable suffixes are more exposed to filtering and are less representative of many closed black-box API settings. |
| Late 2023 | In-the-wild prompt taxonomies | Do Anything Now | Jailbreak culture was organized from observed prompt-sharing communities. The paper highlights prompt injection, privilege escalation, deception, virtualization, and long prompt evolution. |
| Late 2023 | Representation and encoding shifts | CipherChat | Safety training failed outside familiar natural-language forms even when model capability remained intact. |
| Late 2023 to 2024 | Black-box LLM attacker loops | PAIR, TAP | Jailbreak discovery became a search problem with attacker models, target calls, judges, feedback, branching, pruning, and budgets. |
| 2024 | Standardized evaluation | HarmBench, JailbreakBench | The field started treating ASR claims as incomplete unless threat model, behavior set, judge, cost, and artifacts were comparable. |
| 2024 to 2025 | Adaptive black-box search | Simple Adaptive Attacks, AdvPrompter | Model-specific APIs, logprobs, prefilling, suffix restrictions, and trained adversarial prompt generators showed that simple adaptation often beats static prompts. |
| 2024 to 2025 | Scaling and variance attacks | Many-shot Jailbreaking, Best-of-N Jailbreaking | Long context and repeated sampling became attack surfaces. More attempts, more demonstrations, and more modality-specific augmentations improved success. |
| 2025 to 2026 | Reasoning as both defense and attack | Reasoning-to-Defend, Large Reasoning Models Are Autonomous Jailbreak Agents | Reasoning can support safety-aware self-checking, but reasoning models can also become persuasive autonomous adversaries. |
| 2025 to 2026 | Cross-behavior and population memory | JCB | Successes from previous objectives became reusable attack assets, reducing query cost for new objectives. |
| 2026 | Low-cost multi-turn structure | LATS, Salami Slicing | Multi-turn attacks moved from attacker-LLM persuasion toward structured accumulation: lexical anchors, benign-looking turns, and cumulative risk. |
| 2026 | Boundary and classifier attacks | Boundary Point Jailbreaking | The target expanded from the assistant model to deployed guardrail classifiers, optimized with only pass/fail feedback. |
| 2026 | Style as a benchmarked attack surface | Adversarial Poetry, Adversarial Humanities Benchmark | Stylistic transformations showed that safety can overfit explicit harmful phrasings while missing semantically equivalent literary or humanities-style forms. |
| 2026 | System surface fuzzing | TemplateFuzz | Chat templates became a first-class attack surface, not just the invisible wrapper around a prompt. |
| 2026 | Hybrid and internal steering | AB-JB, HMNS | Hybrid pipelines combine semantic variants with lower-level optimization; white-box or model-internal methods explore attention heads, nullspaces, and intervention-style subversion. |

## What Is Still Relevant

### 1. Failure-mode thinking

The most durable contribution is still the framing from `Jailbroken`: competing
objectives and mismatched generalization. Most later papers can be explained as
variants of these two failures.

- Roleplay and persuasion create competing objectives.
- Cipher, poetry, humanities style, and template shifts create mismatched
  generalization.
- Multi-turn attacks create gradual objective drift.
- Sampling and Best-of-N attacks exploit variance in refusal behavior.
- Cross-behavior methods exploit the fact that successful attack structure is
  reusable across objectives.

For Mesmer, this means every technique should be labeled by the failure mode it
is testing, not only by paper name.

### 2. Black-box search loops

PAIR and TAP are still central because they define the reusable experiment
shape:

1. Seed or propose a candidate.
2. Query the target.
3. Evaluate the response.
4. Add feedback.
5. Select the next frontier.
6. Stop on success, budget, or convergence.

Many newer papers are variations on this loop: fewer queries, better candidate
reuse, stronger judges, multi-turn state, cross-objective memory, or different
mutation operators.

### 3. Benchmarks and judge discipline

HarmBench and JailbreakBench remain relevant because they changed what counts
as evidence. A modern jailbreak result needs:

- a behavior set;
- a threat model;
- target and guardrail details;
- generation parameters;
- cost and query budget;
- judge definition;
- refusal and harm scoring;
- artifacts or enough metadata for replay.

Without this, ASR is just a number.

### 4. Style and representation shifts

CipherChat, Adversarial Poetry, and Adversarial Humanities Benchmark show the
same general issue: safety policies often generalize less widely than model
capabilities. The attack does not need to be semantically clever if the surface
form moves outside the refusal distribution.

This remains highly relevant for Mesmer because style shifts are easy to model
as transforms and easy to evaluate with safe canary objectives.

### 5. Multi-turn and long-context state

Many-shot Jailbreaking, LATS, Salami Slicing, and autonomous LRM attacks all
point to one practical lesson: single-turn evaluation is no longer enough.

The target can be robust to an explicit one-line request and still fail when:

- hundreds of demonstrations appear in context;
- benign turns accumulate hidden risk;
- an adversary steers over several turns;
- lexical anchors slowly move the conversation toward a restricted objective;
- a reasoning model adapts persuasion strategy from the transcript.

### 6. Cheap black-box methods

Best-of-N, JCB, LATS, and BPJ matter because they reduce assumptions. They do
not require full white-box gradients. Some need only target outputs, pass/fail
signals, or reusable successful seeds.

For deployed systems, this is more realistic than pure white-box optimization.

## What Is Less Relevant Now

### 1. Static jailbreak memes as a serious evaluation strategy

DAN-style prompts are historically important and still useful as taxonomy
examples. But as standalone evaluation, static prompt lists are weak. They are
comparatively easy to block or overfit against, and they do not measure
adaptive behavior.

Relevant today: the categories behind them, such as roleplay, authority,
fictional framing, and goal hijacking.

Less relevant today: treating known prompt strings as durable attacks.

### 2. Pure unreadable suffixes as the main practical threat model

GCG-style suffix attacks are still scientifically important. They prove that
alignment can be brittle under token-level optimization and they remain useful
for stress testing open-weight models.

But for many real deployments, pure unreadable suffixes are less representative
than black-box, readable, adaptive, multi-turn, or stylistic attacks. They are
also more directly targeted by perplexity filters, content filters, and
input-shape heuristics, although those defenses are not complete and can
themselves become attack targets.

Relevant today: suffix search as a primitive and as a robustness test.

Less relevant today: assuming white-box gradients are the default attacker
capability.

### 3. Single ASR without cost and judge context

Attack success rate is still useful, but only with context. By itself it hides
query budget, model settings, judge strictness, harmful behavior definitions,
and whether the result transfers.

Relevant today: ASR curves, budget curves, judge agreement, and reproducible
artifacts.

Less relevant today: headline ASR divorced from the evaluation harness.

### 4. Single-turn explicit harmful requests as a safety proxy

Frontier systems often refuse obvious harmful requests. That does not imply
robust safety under style shifts, long context, tools, multi-turn escalation, or
classifier-boundary probing.

Relevant today: single-turn probes as a baseline.

Less relevant today: using only obvious single-turn requests to declare a model
safe.

## Emerging Patterns

### Pattern 1: Jailbreaking is becoming stateful

Early attacks fit inside one prompt. Newer attacks treat the conversation as a
state machine. The important object is no longer just `prompt`; it is:

```text
objective + transcript + hidden attacker plan + target response + judge result + memory
```

Mesmer should treat multi-turn state as a first-class object, not as a list of
strings hidden inside one prompt.

### Pattern 2: The attacker is often a search policy

PAIR, TAP, AdvPrompter, JCB, LATS, BPJ, and BoN all differ in implementation,
but they share a search-policy view. The attacker proposes candidates under a
budget and receives feedback from a target or judge.

The useful abstraction is not "jailbreak prompt". It is candidate generation,
mutation, evaluation, selection, and stopping.

### Pattern 3: Reuse beats invention

JCB and population-style approaches show that old successes are useful for new
objectives. The corpus suggests the next timeline will depend more on memory:

- seed pools;
- behavior clusters;
- transfer records;
- prompt lineage;
- mutation provenance;
- success/failure replay.

Mesmer should make cross-run memory inspectable and auditable.

### Pattern 4: Surface form remains under-defended

Cipher, poetry, humanities style, and template fuzzing all attack the same weak
spot: safety systems often learn familiar forms of harmful intent, while the
base model remains capable of understanding transformed forms.

This makes transforms a core primitive:

- encoding;
- paraphrase;
- style transfer;
- role or genre shift;
- chat-template mutation;
- lexical anchor injection;
- demonstration packing;
- modality-specific augmentation.

### Pattern 5: Defenses and attacks are converging on reasoning

Reasoning-to-Defend uses explicit safety-aware reasoning to improve refusal.
Autonomous LRM attacks use reasoning to plan and persuade. This creates a
research tension:

- reasoning can make a model more reflective about safety;
- reasoning can also make an attacker more adaptive;
- hidden or private reasoning makes evaluation harder;
- judge models may share the same weaknesses as target models.

Mesmer should support separate roles for target, attacker, judge, and safety
monitor, with traces that make each role auditable.

### Pattern 6: The system boundary is larger than the model

TemplateFuzz and BPJ make this explicit. Modern jailbreak research has to test:

- model prompts;
- chat templates;
- input classifiers;
- output classifiers;
- safety monitors;
- tool gates;
- system-message layout;
- conversation serialization;
- API features such as prefilling and logprobs.

The model is one component in a larger safety pipeline.

## Technique Relevance Matrix

| Technique family | Current relevance | Why |
| --- | --- | --- |
| Manual roleplay and DAN-style prompts | Medium | Useful taxonomy and baseline, but brittle as a primary attack method. |
| Failure-mode-derived prompt design | High | Still explains most successful families. |
| Cipher and encoding transforms | High | Directly tests mismatched generalization. |
| GCG and token suffix optimization | Medium to high | Strong for open-weight stress testing; less realistic for strict black-box deployments. |
| AutoDAN and readable optimization | High | Bridges optimization with human-readable prompts. |
| PAIR and TAP | High | Canonical black-box automation loops. |
| HarmBench and JailbreakBench | High | Evaluation substrate for credible comparisons. |
| Simple adaptive attacks | High | API-specific adaptation is realistic and often effective. |
| AdvPrompter | Medium to high | Trained attack generators matter, but require training infrastructure. |
| Many-shot and long-context attacks | High | The paper shows large context windows create a distinct attack surface through many in-context demonstrations. |
| Best-of-N | High | Simple, scalable, multimodal, and composes with other attacks. |
| Reasoning-to-Defend | High | Important defensive direction and a useful counterpoint to attack-only work. |
| Cross-behavior attacks | High | Query efficiency and transfer are central to practical red teaming. |
| Autonomous LRM adversaries | High | Strong signal that frontier reasoning models can become scalable attackers. |
| Adversarial poetry and humanities style | High | Shows safety brittleness under style-preserving semantic transformations. |
| Lexical anchor tree search | High | Low-query multi-turn structure without requiring an attacker LLM. |
| Boundary point jailbreaking | High | Targets deployed classifier boundaries with minimal feedback. |
| Salami slicing | High | Models cumulative risk across turns and modalities. |
| Template fuzzing | High | Exposes chat serialization and template design as safety surfaces. |
| Nullspace steering and internal interventions | Medium | Important for white-box research, less applicable to closed commercial APIs. |
| Hybrid semantic plus low-level optimization | High | Observed in AB-JB and consistent with the broader move toward composed attack pipelines. |

## Mesmer Implications

Mesmer should model jailbreak research as typed, traceable state transitions.
The papers point to these primitive families:

| Research need | Mesmer primitive shape |
| --- | --- |
| One-shot baseline tests | `Probe` with fixed prompt or transformed prompt |
| Encoding and style attacks | `ops.ApplyTransforms` with source-tagged transforms |
| PAIR and TAP | `FrontierSearch` with proposer, judge, feedback, and selector |
| Best-of-N | repeated candidate sampling plus top-k or first-success selection |
| JCB and population reuse | seed pools, reward ledgers, and cross-objective memory |
| LATS and salami slicing | multi-turn state, anchor injection, cumulative-risk evaluators |
| LRM adversaries | `ConversationAgentProbe` with attacker, target, judge, and transcript state |
| HarmBench and JailbreakBench style evidence | benchmark runners, standardized objective sources, budget curves, judge reports |
| BPJ | binary classifier target, boundary-point selection, curriculum over intermediate objectives |
| TemplateFuzz | chat-template mutation operators, accuracy-preservation constraints, active-learning oracle |
| R2D-style defense | safety-aware evaluator, refusal classifier, self-check trace, safe pivot markers |
| HMNS or white-box attacks | optional model-internal intervention interface, separate from black-box public API |

The important design rule: do not encode every paper as a separate one-off
technique. Extract the reusable operators and let named techniques compile those
operators into workflows.

## Topics To Master For The Next Timeline

To contribute to the next timeline through Mesmer, focus on these topics in
order.

### 1. Evaluation literacy

Master HarmBench and JailbreakBench first. Learn how behavior sets, judges,
refusal classifiers, target configuration, budgets, and artifacts change the
meaning of an ASR claim.

Deliverable in Mesmer: a benchmark report that compares at least two techniques
under the same objectives, target, judge, and budget.

### 2. Prompt-pattern taxonomy

Learn the durable prompt families behind the old jailbreak strings:

- roleplay;
- authority and policy inversion;
- fictional framing;
- attention shifting;
- goal hijacking;
- persuasion;
- representation shift;
- style shift.

Deliverable in Mesmer: source-tagged prompt patterns that use harmless canary
objectives instead of operational harmful content.

### 3. Transform design

Study CipherChat, adversarial poetry, humanities-style transformations,
Best-of-N augmentations, and TemplateFuzz. The skill is to separate semantic
intent from surface form.

Deliverable in Mesmer: transform operators for encoding, paraphrase, style,
lexical anchors, template mutation, and demonstration packing, each with
metadata describing what changed.

### 4. Search algorithms

Understand PAIR, TAP, BoN, JCB, LATS, and BPJ as search algorithms:

- candidate generation;
- mutation;
- branching;
- pruning;
- scoring;
- reward assignment;
- stopping;
- replay.

Deliverable in Mesmer: a frontier-search run with a trace showing every
candidate, target call, judge score, selection decision, and budget use.

### 5. Multi-turn safety

Single-turn probes are baselines. The next frontier is conversation state:
gradual escalation, cumulative risk, context poisoning, persuasion, and
objective persistence.

Deliverable in Mesmer: a multi-turn harness that can compare direct prompting,
structured escalation, and autonomous-adversary conditions on the same benign
canary task.

### 6. Judge and monitor reliability

Learn judge-panel design, refusal detection, harm scoring, inter-judge
agreement, false positives, false negatives, and evaluator leakage. A weak judge
can make a weak attack look strong or a strong defense look safe.

Deliverable in Mesmer: a judge report with disagreement analysis and a manual
spot-check protocol.

### 7. API and system-surface security

Study prefilling, logprobs, chat templates, classifier boundaries, system prompt
serialization, tool gates, and input/output filters. Many modern jailbreaks
attack the system wrapper rather than only the model.

Deliverable in Mesmer: a target adapter test that records the exact serialized
messages, template assumptions, guardrail responses, and classifier decisions.

### 8. Reasoning-model behavior

Learn how reasoning changes both sides of safety. Reasoning can support
self-critique and refusal, but it can also improve attacker planning and
multi-turn persuasion.

Deliverable in Mesmer: separate attacker, target, judge, and monitor roles with
auditable traces and no hidden blending of responsibilities.

### 9. Responsible artifact handling

The next timeline should be reproducible without becoming a payload library.
Use safe objectives, canaries, redactions, synthetic tasks, and policy-neutral
success criteria when publishing examples.

Deliverable in Mesmer: paper extraction notes that preserve mechanism,
workflow, metrics, and trace shape while omitting operational harmful prompts.

## Suggested Next Mesmer Work

1. Add a `style_transform_probe` example based on cipher, poetry, and humanities
   transformations, using harmless canary objectives.
2. Add a `multi_turn_cumulative_risk` example inspired by LATS and salami
   slicing, with explicit transcript state and cumulative scoring.
3. Add a `cross_behavior_seed_pool` example inspired by JCB, where successful
   benign canary patterns are reused across objectives.
4. Add a `template_fuzzing` prototype that mutates chat serialization in a local
   test target before touching real model APIs.
5. Add benchmark reports that show budget curves, not only final success rates.

## Bottom Line

The field is moving from prompt strings to attack systems. The papers suggest
that future jailbreak techniques will increasingly combine several properties:
black-box access, low query cost, multi-turn state, reusable memory, style or
template shifts, and credible evaluation artifacts.

For Mesmer, the opportunity is to make those systems inspectable. If a future
paper introduces a new jailbreak, we should be able to ask: what state changed,
which operator changed it, what evidence was recorded, and whether the result
replays under the same budget and judge.
