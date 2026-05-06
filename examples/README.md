# Mesmer Examples

Run from the repository root.

```bash
uv sync
export GROQ_API_KEY=...
export MESMER_ATTACKER_MODEL=groq/llama-3.3-70b-versatile
export MESMER_TARGET_MODEL=groq/llama-3.3-70b-versatile
export MESMER_VERBOSE=true
export MESMER_LOG_FORMAT=rich
```

`MESMER_ATTACKER_MODEL` is used by attacker-side generation components such as
`generation.StructuredLLM` in examples that call an attacker model.

`MESMER_TARGET_MODEL` is used by the target wrapper and is where the target system
prompt is configured.

If you want faster/cheaper Groq runs, override both models with
`groq/llama-3.1-8b-instant`.

Set `MESMER_VERBOSE=false` to hide framework execution logs.

Set `MESMER_LOG_FORMAT=compact` for plain JSONL diagnostic logs that include
hidden transform I/O and full event payloads. This is useful when pasting a run
trace into an AI assistant for analysis.

## Single Turn

Scenario: a release-readiness assistant. The attacker paraphrases a release-token
objective, then sends the resulting message to the target.

```bash
uv run python examples/single_turn.py
```

## Tree Search

Scenario: a support-routing assistant. The attacker expands and prunes candidate
support-ticket messages, then evaluates selected candidates against the target. It
stops on the first passing escalation-code candidate.

```bash
uv run python examples/tree_search.py
```

## Autonomous Agent

Scenario: an onboarding-gate assistant. The attacker agent observes target replies
and generates the next conversation turn until it obtains the approval code or
exhausts the turn budget.

```bash
uv run python examples/autonomous_agent.py
```

## Benchmark

Scenario: an operations router with multiple route codes. The benchmark compares
single-turn, tree-search, and autonomous-agent flows across several objective-specific
success criteria.

```bash
uv run python examples/benchmark.py
```

## Prompt Patterns

Scenario: a real model target receives a benign encoded readiness-check request.
The example shows both direct single-shot encoding and selecting a reusable prompt
pattern before applying an explicit encoder transform.

```bash
uv run python examples/prompt_patterns.py --mode single-shot
uv run python examples/prompt_patterns.py --mode pattern
```

## Paper Examples

Paper-specific examples live under `examples/papers/`.

The TAP example references the exact upstream AdvBench Subset CSV from the TAP
repository, downloads it at runtime, and caches it under `.mesmer/`:

```bash
MESMER_LOG_FORMAT=compact uv run python examples/papers/tap/run_tap.py --limit 1
```

Top-level examples use benign canary-style objectives. Paper-specific examples may
reference the original paper datasets at runtime for reproducibility.
