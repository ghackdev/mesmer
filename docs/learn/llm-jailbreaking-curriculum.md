# LLM Jailbreaking Practical Curriculum

This curriculum is a six-week whitehat path for learning modern LLM
jailbreaking and AI red teaming in a way that can transfer to real bug bounty
work. It is not a prompt dump. The goal is to understand attack surfaces,
measurement, evidence, and responsible reporting.

The practicals are built from scratch. They do not reuse Mesmer's existing
examples. The subject is real AI red-team work: how to choose an authorized
target, model the attack surface, run the right kind of probe or search, collect
evidence, and decide whether the finding is bounty-worthy. Mesmer is the
facility for making those experiments reproducible.

## Operating Boundary

Only test systems you own, local labs, deliberately vulnerable apps, or assets
where the program scope explicitly permits AI red-team testing. Do not submit a
generic "model said bad content" result unless the program says safety-policy
bypasses are in scope. Many programs reward AI issues when the finding causes a
concrete security impact: unauthorized tool action, cross-tenant data exposure,
prompt injection through trusted content, sensitive information disclosure,
policy bypass in a safety product, or reliable compromise of an agent workflow.

Labs use harmless canaries, fake secrets, dummy tools, and redacted case shapes.
When a real technique would include harmful instructions, the curriculum teaches
the mechanism without publishing the harmful payload.

## Source Backbone

- [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- [OWASP Agentic AI Security Initiative](https://owasp.org/www-project-agentic-ai-security-initiative/)
- [NIST AI 600-1 Generative AI Profile](https://www.nist.gov/itl/ai-risk-management-framework)
- [MITRE ATLAS](https://atlas.mitre.org/)
- [Microsoft PyRIT](https://github.com/Azure/PyRIT)
- [NVIDIA garak](https://github.com/NVIDIA/garak)
- [Inspect AI](https://inspect.aisi.org.uk/)
- [HarmBench](https://arxiv.org/abs/2402.04249)
- [JailbreakBench](https://arxiv.org/abs/2404.01318)
- [Best-of-N Jailbreaking](https://arxiv.org/abs/2412.03556)
- [AgentDojo](https://arxiv.org/abs/2406.13352)
- [OpenAI Safety Bug Bounty Program](https://bugcrowd.com/openai-safety)
- [Google AI Vulnerability Reward Program](https://bughunters.google.com/about/rules/google-friends/6625378258649088/google-ai-vulnerability-reward-program-rules)
- [HackerOne AI Red Teaming](https://www.hackerone.com/product/ai-red-teaming)

## Weekly Path

| Week | Focus | Materials |
| --- | --- | --- |
| 0 | Lab harness primitives by retyping | `mesmer-primitives-for-jailbreak-labs` |
| 1 | Authorization, scope, threat models | `00`, `01`, `02` |
| 2 | Prompt families and representation shifts | `03`, `04` |
| 3 | Black-box search and suffix optimization | `05`, `06` |
| 4 | Evaluation, sampling, population memory | `07`, `08`, `09` |
| 5 | Multi-turn, agentic, RAG, tools, templates | `10`, `11`, `12` |
| 6 | Defense, remediation, reporting, portfolio | `13`, `14` |

## Lab Standard

Every lab should produce these artifacts:

- Scope statement: what target is authorized and what is out of scope.
- Threat model: direct prompt, indirect prompt injection, agent tool misuse,
  RAG data exposure, template issue, or model-safety bypass.
- Reproduction trace: prompt or input sequence, target metadata, model settings,
  response, judge result, and timestamp.
- Impact statement: what security boundary failed.
- Remediation hypothesis: input isolation, tool confirmation, retrieval
  filtering, policy hardening, judge improvement, context separation, or
  monitoring.

## Code Practice Rule

Before Week 1, read and retype
[`mesmer-primitives-for-jailbreak-labs.md`](mesmer-primitives-for-jailbreak-labs.md).
Each later module includes code snippets. Treat them as typing drills first and
engineering assets second: copy the shape into your hands, run it locally, then
modify one variable at a time.

## Real Model Practice Rule

Every material includes a `Real Model Lab` section. Those snippets use real
models through `LiteLLMTarget` and, when the material is about generated or
agentic attacks, a real attacker model through `LiteLLMChatActor`. The target
asset is still synthetic: fake hidden notes, fake tool markers, benign canaries,
and strict query budgets.

Set credentials in your shell:

```bash
export OPENAI_API_KEY="..."
export MESMER_TARGET_MODEL="openai/gpt-4o-mini"
export MESMER_ATTACKER_MODEL="openai/gpt-4o-mini"
```

Swap the model name for another LiteLLM-supported provider when needed. Do not
put API keys in the docs or in committed code.

## Real-World Lab Map

Each module starts from the AI red-team situation first. The Mesmer technique is
chosen only because it fits that situation:

| Material | Real-World Skill | Mesmer Facility |
| --- | --- | --- |
| `00` | Read scope, set budget, avoid non-reportable testing. | `Probe` for one controlled target call. |
| `01` | Map LLM app boundaries: user, document, memory, tool, output. | `Probe` with explicit target/evaluator. |
| `02` | Separate jailbreak, prompt injection, and model misuse. | `Probe` + `JudgePanel`. |
| `03` | Generate and classify classic pattern families. | `FrontierSearch` + `StructuredLLMProposer`. |
| `04` | Test representation and style robustness. | `FrontierSearch` + `StructuredLLMProposer`. |
| `05` | Run PAIR/TAP-style black-box refinement. | `FrontierSearch` + feedback. |
| `06` | Study suffix search and transfer without harmful suffixes. | `FrontierSearch` + `SuffixOnlyLLMProposer`. |
| `07` | Build credible judges, ASR, refusal, and overrefusal evidence. | `Probe` + `JudgePanel`. |
| `08` | Run Best-of-N generated variants under a query budget. | High-branching `FrontierSearch`. |
| `09` | Reuse and mutate seeds across objectives. | Search loop plus seed reward math. |
| `10` | Test long-context and multi-turn drift. | `ConversationAgentProbe`. |
| `11` | Test agentic prompt injection against tools/RAG. | `ConversationAgentProbe`. |
| `12` | Fuzz chat templates and deployment surfaces. | `Probe` + `RenderChatTemplate`. |
| `13` | Replay findings after remediation. | `Probe` regression run. |
| `14` | Package evidence into a report. | `Probe` plus result summarization. |

## Completion Criteria

You are ready for beginner AI bug bounty work when you can:

- Read a program scope and decide whether a prompt result is reportable.
- Build a synthetic vulnerable LLM app and prove the exploit path.
- Separate model misuse from application security impact.
- Run a small benchmark with a consistent judge and budget.
- Write a concise report with replayable evidence and a realistic fix.
- Stop testing when scope, safety, or consent is unclear.
