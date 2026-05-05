# PAIR Paper Example

This folder contains a paper-specific implementation of Prompt Automatic
Iterative Refinement (PAIR), based on `Jailbreaking Black Box Large Language
Models in Twenty Queries` (`2310.08419`).

The example maps the paper mechanics onto Mesmer primitives:

- `PairSeed` creates independent PAIR streams;
- the attacker model proposes one refined prompt per stream;
- the target model is queried once per stream per iteration;
- an evaluator model scores the target response;
- evaluator feedback is fed back into the same stream;
- the run stops when the score threshold or iteration budget is reached.

The built-in objectives are benign authorization-flow readiness checks. This
keeps the example runnable as a normal framework smoke test while preserving the
PAIR control flow. Authorized local datasets can be supplied with `--dataset-csv`
or `--dataset-jsonl`.

## Run

```bash
export GEMINI_API_KEY=...
uv run python examples/papers/pair/run_pair.py --rows 1 --streams 2 --iterations 2 --max-parallel 2
```

Override models through the same environment variables used by the other paper
examples:

```bash
MESMER_ATTACKER_MODEL=groq/llama-3.3-70b-versatile \
MESMER_EVALUATOR_MODEL=groq/llama-3.3-70b-versatile \
MESMER_TARGET_MODEL=groq/llama-3.3-70b-versatile \
GROQ_API_KEY=... \
uv run python examples/papers/pair/run_pair.py
```

Useful controls:

```bash
export MESMER_PAIR_ROWS=1
export MESMER_PAIR_STREAMS=3
export MESMER_PAIR_ITERATIONS=20
export MESMER_PAIR_MAX_PARALLEL=3
export MESMER_LOG_FORMAT=rich
```

## Token And Cost Reporting

The script prints token usage after every run:

```text
pair_token_usage_summary={...}
pair_token_usage_trace=[...]
```

The summary aggregates attacker, evaluator, and target calls. The trace records
one entry per LiteLLM call with role, model, prompt tokens, completion tokens,
total tokens, latency, and `cost_usd` when LiteLLM can calculate pricing for the
provider/model. Use `--no-usage-trace` to keep only the aggregate summary.
