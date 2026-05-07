# LLM Jailbreak Paper Reading Path

This guide orders LLM jailbreak papers from the 2023 classics to modern
2025-2026 work. It assumes the first Mesmer blog post already covers
["Jailbroken: How Does LLM Safety Training Fail?"](https://arxiv.org/abs/2307.02483),
so the rest of the list builds outward from that foundation.

Use this as a learning sequence, not as an endorsement of running attacks
against systems you do not own or have permission to test. When turning these
papers into Mesmer examples or posts, keep payloads benign and focus on the
mechanism, trace, evaluator, and reproducibility story.

## Reading Path

| Order | Paper | Year | Theme | Why Read It |
| ---: | --- | ---: | --- | --- |
| 0 | [Jailbroken: How Does LLM Safety Training Fail?](https://arxiv.org/abs/2307.02483) | 2023 | Failure modes | Already covered in the current blog post. It gives the core language: competing objectives, mismatched generalization, and safety-capability parity. |
| 1 | [Universal and Transferable Adversarial Attacks on Aligned Language Models](https://arxiv.org/abs/2307.15043) | 2023 | Token and suffix optimization | The classic GCG-style adversarial suffix paper. Read it to understand why unreadable suffix attacks can transfer across models. |
| 2 | ["Do Anything Now": Characterizing and Evaluating In-The-Wild Jailbreak Prompts on Large Language Models](https://arxiv.org/abs/2308.03825) | 2023 | Jailbreak culture and taxonomy | A bridge from theory to real prompt families: roleplay, privilege escalation, prompt injection, and prompt communities. |
| 3 | [GPT-4 Is Too Smart To Be Safe: Stealthy Chat with LLMs via Cipher](https://arxiv.org/abs/2308.06463) | 2023 | Encodings and representation shift | A direct continuation of mismatched generalization: safety fails on formats the model can still understand. |
| 4 | [Jailbreaking Black Box Large Language Models in Twenty Queries](https://arxiv.org/abs/2310.08419) | 2023 | LLM-as-attacker loop | PAIR. Very useful for Mesmer because it maps cleanly to proposer, target, judge, and feedback refinement. |
| 5 | [AutoDAN: Interpretable Gradient-Based Adversarial Attacks on Large Language Models](https://arxiv.org/abs/2310.15140) | 2023 | Readable automated attacks | Combines optimization with human-readable jailbreaks. Read after GCG to see the move from opaque suffixes toward interpretable attacks. |
| 6 | [Tree of Attacks: Jailbreaking Black-Box LLMs Automatically](https://arxiv.org/abs/2312.02119) | 2023 | Tree search and pruning | TAP. The natural next step after PAIR: branching, pruning, scoring, and search-budget management. |
| 7 | [HarmBench: A Standardized Evaluation Framework for Automated Red Teaming and Robust Refusal](https://arxiv.org/abs/2402.04249) | 2024 | Evaluation benchmark | Read before comparing attack claims. It standardizes red-team evaluation across methods, models, and defenses. |
| 8 | [JailbreakBench: An Open Robustness Benchmark for Jailbreaking Large Language Models](https://arxiv.org/abs/2404.01318) | 2024 | Open benchmark and artifacts | Complements HarmBench with reproducible artifacts, behavior sets, judge choices, defenses, and a leaderboard. |
| 9 | [Jailbreaking Leading Safety-Aligned LLMs with Simple Adaptive Attacks](https://arxiv.org/abs/2404.02151) | 2024 | Adaptive attacks | Shows why simple adaptive search, logprobs, transfer, and API-specific behavior matter. |
| 10 | [Many-shot Jailbreaking](https://proceedings.neurips.cc/paper_files/paper/2024/hash/ea456e232efb72d261715e33ce25f208-Abstract-Conference.html) | 2024 | Long-context attacks | A key trend paper: larger context windows create a new attack surface through in-context learning. |
| 11 | [AdvPrompter: Fast Adaptive Adversarial Prompting for LLMs](https://arxiv.org/abs/2404.16873) | 2024 | Trained attack generator | Moves from one-off optimization to a trained model that can quickly generate adversarial prompts. |
| 12 | [Best-of-N Jailbreaking](https://arxiv.org/abs/2412.03556) | 2024-2025 | Sampling and multimodal variance | Shows how repeated prompt variation can scale across text, vision, and audio settings. |
| 13 | [Reasoning-to-Defend: Safety-Aware Reasoning Can Defend Large Language Models from Jailbreaking](https://arxiv.org/abs/2502.12970) | 2025 | Defense via reasoning | A useful counterpoint: reasoning can be used for safety-aware refusal, not only attack generation. |
| 14 | [Effective and Efficient Jailbreaks of Black-Box LLMs with Cross-Behavior Attacks](https://arxiv.org/abs/2503.08990) | 2025 | Cross-behavior transfer | The repo references `2503.08990v1` as JBFuzz. The latest arXiv version is framed as JCB, so compare versions when extracting primitives. |
| 15 | [Large Reasoning Models Are Autonomous Jailbreak Agents](https://arxiv.org/abs/2508.04039) / [Nature Communications version](https://www.nature.com/articles/s41467-026-69010-1) | 2025-2026 | Autonomous reasoning agents | A modern endpoint: large reasoning models act as multi-turn adversarial agents with little external scaffolding. |

## Themes And Trends

## 2023: Why Jailbreaks Work

The first wave explains the failure surface. The important shift is from
"jailbreaks are magic strings" to "jailbreaks are pressure tests against
training objectives, representation coverage, and refusal generalization."

Core papers:

- Jailbroken
- Universal and Transferable Adversarial Attacks
- Do Anything Now
- CipherChat

What to extract for Mesmer:

- Prompt-pattern families
- Mechanical transforms such as encoding or representation shift
- Safe canary-style tests for competing objectives and mismatched generalization

## Late 2023: Automation Starts

The next wave turns jailbreak discovery into a search loop. Human prompt writing
is replaced or augmented by attacker models, judges, feedback, branching, and
pruning.

Core papers:

- PAIR
- AutoDAN
- TAP

What to extract for Mesmer:

- `ops.Propose`
- `ops.QueryTarget`
- `ops.Evaluate`
- `feedback.Refine`
- `selection.TopK`
- `techniques.FrontierSearch`

## 2024: Evaluation Becomes Serious

By 2024, attack success rates were difficult to compare across papers because
datasets, judges, generation parameters, cost accounting, and threat models often
differed. HarmBench and JailbreakBench are important because they make the
evaluation substrate explicit.

Core papers:

- HarmBench
- JailbreakBench

What to extract for Mesmer:

- Behavior datasets
- Standardized judge interfaces
- Attack and defense comparison reports
- Over-refusal and robust-refusal measurements

## 2024-2025: Scaling, Sampling, And Cheap Black-Box Search

This period shows that simple scalable methods are dangerous: long context,
many-shot examples, repeated prompt perturbations, adaptive search, and trained
prompt generators all exploit variance or generalization gaps.

Core papers:

- Simple Adaptive Attacks
- Many-shot Jailbreaking
- AdvPrompter
- Best-of-N Jailbreaking

What to extract for Mesmer:

- Budgeted black-box search
- Prompt augmentation and mutation operators
- Long-context test harnesses
- Sampling curves and query-cost traces

## 2025-2026: Reasoning And Agency

The modern trend is that reasoning models change both sides of the problem. They
can reason about safety before answering, but they can also act as autonomous
multi-turn adversaries.

Core papers:

- Reasoning-to-Defend
- Cross-Behavior Attacks / JBFuzz / JCB
- Large Reasoning Models Are Autonomous Jailbreak Agents

What to extract for Mesmer:

- Conversation-level state
- Multi-turn objective persistence
- Reasoning-aware evaluators
- Agentic attack loops with bounded, benign objectives

## Suggested Next Blog Posts

1. **PAIR**: Best practical continuation. The loop is easy to explain and already
   maps to Mesmer examples.
2. **GCG / Universal Transferable Attacks**: Best strict historical continuation.
   This adds token-level optimization to the conceptual foundation.
3. **HarmBench or JailbreakBench**: Best infrastructure post. This shifts the
   blog from "how attacks work" to "how to measure them responsibly."
4. **Many-shot Jailbreaking**: Best modern capability-scaling post. It connects
   context windows, in-context learning, and safety regression.
5. **Large Reasoning Models Are Autonomous Jailbreak Agents**: Best frontier post.
   This is the modern endpoint, but it will land better after PAIR/TAP and
   benchmark posts.

## Recommended Learning Order

For a smooth learning path, read and write in this order:

1. Jailbroken
2. GCG / Universal Transferable Attacks
3. PAIR
4. TAP
5. HarmBench or JailbreakBench
6. Many-shot Jailbreaking
7. Best-of-N Jailbreaking
8. JBFuzz / JCB
9. Large Reasoning Models Are Autonomous Jailbreak Agents
