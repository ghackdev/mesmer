---
name: mesmer-paper-primitive-extractor
description: Extract reusable Mesmer primitives from a research paper PDF, arXiv text, appendix, or paper notes. Use when working in this Mesmer repository to add source-backed prompt patterns, transform/encoder primitives, tests, docs, and examples from a paper while avoiding overlap with existing primitives and preserving the distinction between prompt patterns and mechanical transforms.
---

# Mesmer Paper Primitive Extractor

Use this skill inside the Mesmer repository when the user gives a paper and asks to "extract things", "add patterns", "document the paper", "implement techniques", or "do the same as the previous paper".

## Workflow

1. Read the repository shape before editing:
   - `src/mesmer/prompts/__init__.py`
   - `src/mesmer/transforms/__init__.py`
   - `tests/unit/test_prompt_patterns_and_transforms.py`
   - `docs/primitive-taxonomy-audit.md`
   - relevant `examples/` and `README.md` sections
   - search existing primitives with `rg` before proposing new classes
2. Extract the paper taxonomy from primary text:
   - Prefer appendix sections titled attacks, methods, algorithms, prompts, ablations, or implementation details.
   - For PDFs, use `pdftotext <paper.pdf> /private/tmp/<paper>.txt` when available.
   - If extraction is noisy, inspect multiple relevant sections and preserve source uncertainty in metadata or final notes.
3. Classify each technique before implementing:
   - **PromptPattern**: reusable prompt tactic, framing, template, roleplay, style constraint, distractor, few-shot shape, proposer inspiration, or combination recipe.
   - **Transform**: deterministic message rewrite such as Base64, ROT13, cipher, encoding, character rewrite, translation wrapper, payload splitting, variable substitution, compression, or format-preserving mechanical mutation.
   - **Proposer/evaluator/topology**: LLM-driven generation, scoring, selection, iteration, branching, pruning, budget logic, or feedback loop.
4. Run a primitive-overlap review before adding anything:
   - Prefer composing `runtime.Program`, `topology.Iterate`, `generation.Propose`, `prompts.Select`, `transforms.Apply`/`Expand`, `selection.Select`, `evaluation.Assess`, `feedback.Refine`, and `stopping.StopWhen` over creating a new primitive.
   - Add a new primitive only when no existing primitive family can express the responsibility cleanly.
   - Do not duplicate topology, generation, selection, evaluation, mutation, or transform responsibilities under a paper-specific name.
   - Keep paper names in pattern ids, examples, docs, CLI flags, metadata, or paper-specific state only. Use responsibility names for reusable primitives.
   - Preserve provenance when adding primitives: metadata should record source paper, operator chain, parent ids, transform specs, or evaluation facts as appropriate.
5. Add prompt-level techniques to the built-in prompt library:
   - Use `prompts.PromptPattern`.
   - Set stable ids like `paper.<short_slug>.<paper_attack_id>`.
   - Set `source="paper:<arxiv_or_identifier>"`.
   - Put `paper`, `arxiv_id` or equivalent, section/appendix, and original technique id in `metadata`.
   - Include `templates` only when a reusable concrete wrapper is appropriate.
   - Include `proposer_hint` for inspiration-based use by `generation.Propose`.
6. Keep encoders and mechanical rewrites out of the prompt library:
   - Implement reusable mechanics under `src/mesmer/transforms/__init__.py`.
   - Reference transforms from patterns via `suggested_transforms` only when a paper combination pattern depends on them.
   - Do not create prompt pattern ids/tags like `paper.foo.base64` or `paper.foo.rot13` for pure encoders.
7. Preserve safety and research scope:
   - Do not embed highly actionable harmful payloads as built-in examples.
   - Use neutral objective placeholders such as `{prompt}` and canary-style examples.
   - Summarize public jailbreak prompts as reusable structures instead of copying long verbatim attack text.
8. Update validation:
   - Add tests that the expected paper prompt-pattern ids exist.
   - Add tests that encoder-only techniques are absent from `prompts.BuiltinSource`.
   - Add tests for any new transform primitive.
   - Add a test that combination patterns reference transforms through `suggested_transforms`.
   - Add overlap-regression tests when practical, such as proving an encoder remains a transform and not a prompt pattern.
9. Update docs:
   - Mention source-tagged built-ins in `README.md` when user-facing.
   - Update `docs/primitive-taxonomy-audit.md` if adding or clarifying primitive families.
   - Add or update examples only when they make developer usage clearer.
10. Run verification:
   - `uv run ruff check .`
   - `uv run pytest`

Read `references/extraction-checklist.md` for the compact classification checklist and implementation template.
