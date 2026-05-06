# Extraction Checklist

## Paper Extraction

- Record title, arXiv id or stable identifier, version, section/appendix, and original technique names.
- Search extracted text for: `Attack`, `Method`, `Prompt`, `Ablation`, `Appendix`, `Algorithm`, `Table`, `Combination`, `Obfuscation`, `Encoding`, `Mutation`, `Evaluator`.
- Prefer paper-authored names over invented names. If names are missing, create concise responsibility names and store source notes in `metadata`.

## Classification Rules

Before adding a primitive, answer these questions in implementation notes or code review reasoning:

- Can `runtime.Program` plus existing components express this technique?
- Can `prompts.PromptPattern` plus `prompts.Select` express it as data/inspiration?
- Can `transforms.Transform` express it as a deterministic rewrite?
- Can `variation.Mutator` express it as stochastic or learned mutation?
- Can `generation.Propose`, `selection.Select`, `evaluation.Assess`, `feedback.Refine`, or `stopping.StopWhen` express the loop behavior?
- Is the new concept paper-specific metadata/example code rather than a reusable primitive?

Create a new reusable primitive only after these checks fail.

Use `PromptPattern` for:

- prefix or suffix response shaping
- refusal suppression or response-style constraints
- roleplay, persona, developer-mode, system-prompt-inspired structures
- distractor tasks and topic framing
- few-shot continuation shapes
- website/article/report/JSON/poem framing
- high-level combination recipes
- LLM proposer inspiration

Use `Transform` for:

- Base64, ROT13, Morse, ciphers, or other encoders
- disemvowel, leetspeak, Unicode substitution, character-level rewrite
- payload splitting, token smuggling, variable stitching
- wrapping selected messages with deterministic templates
- deterministic translation or compression passes when implemented locally

Use existing or new search primitives for:

- LLM-driven proposal or mutation
- random or exhaustive variant selection
- without-replacement ledgers
- scoring, evaluation, pruning, stopping, and feedback loops

## Primitive Discipline

- Prefer composition over new classes. A paper technique should usually become a `runtime.Program` sequence plus source-backed data.
- Do not add paper-named primitives when a responsibility-named primitive already exists.
- Do not add a second class for an existing responsibility. Extend the existing primitive only if the added behavior is generic and backward compatible.
- Keep prompt patterns as data/context. They may include templates, proposer hints, tags, metadata, and `suggested_transforms`; they should not execute rewrites themselves.
- Keep transforms mechanical and deterministic. They should rewrite candidate messages and preserve operator provenance.
- Keep `variation` for stochastic or learned mutation. Do not hide LLM-driven mutation inside `transforms`.
- Keep selectors separate from generators and evaluators. Selection ranks/retains; generation creates; evaluation scores.
- Keep target calls at `targeting.Query` or `targeting.Continue`. Do not hide target IO inside pattern or transform primitives.
- Keep paper-specific prompts, datasets, thresholds, model names, and marker strings in examples, pattern metadata, or docs unless the primitive is only meaningful with them.
- If adding a new primitive family, update `docs/primitive-taxonomy-audit.md` with its responsibility boundary and duplication analysis.

## PromptPattern Template

```python
PromptPattern(
    id="paper.<slug>.<technique_id>",
    name="<Human name>",
    family="paper_<slug>",
    prompt="<short abstract tactic>",
    description="<paper section and concise description>",
    templates=("<safe reusable wrapper with {prompt}>",),
    proposer_hint="<how Propose should use this as inspiration>",
    suggested_transforms=(
        TransformSpec(name="<transform>", params={...}),
    ),
    tags=("paper", "<slug>", "<family>", "<mechanism>"),
    source="paper:<identifier>",
    metadata={
        "paper": "<title>",
        "arxiv_id": "<id>",
        "section": "<section>",
        "paper_attack_id": "<original id>",
    },
)
```

Omit `templates` when a technique is inspiration-only or cannot safely materialize as a user-message wrapper. Omit `suggested_transforms` unless the paper pattern composes with an actual mechanical transform.

## Validation Rules

- Assert every prompt-level paper technique id exists in `BuiltinSource`.
- Assert pure encoders are not represented as prompt pattern ids or tags.
- Assert transform-backed combinations carry `TransformSpec`.
- Assert new transforms operate on `LATEST_USER` without modifying earlier dialogue unless the scope says otherwise.
- Run full tests and ruff before final response.
