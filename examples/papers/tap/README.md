# TAP Paper Example

This folder contains a paper-specific implementation of Tree of Attacks with
Pruning (TAP), based on `2312.02119v3`.

The example is implemented through Mesmer's declarative search lifecycle:
`propose -> constrain -> query -> assess -> stop -> refine`. The paper-specific
parts are the prompts, TAP hyperparameters, and AdvBench mapping.

It also declares `TapState`, the state structure that evolves during the run:
frontier candidates, current depth, target-call count, best candidate,
per-candidate constraints, responses, evaluations, and feedback. Framework
control state such as stopped/stop reason stays internal.
Mesmer records compact state transitions in `state_history` for replay/debugging.

The example references the exact TAP AdvBench Subset CSV at runtime:

```text
https://raw.githubusercontent.com/RICommunity/TAP/main/data/advbench_subset.csv
```

The dataset is downloaded into Mesmer's gitignored cache under `.mesmer/`.

Run a small paper-style smoke run:

```bash
export GROQ_API_KEY=...
uv run python examples/papers/tap/run_tap.py --rows 1 --depth 1 --width 1 --branching-factor 1 --max-parallel 1
```

The script defaults to rich logs. Use `--log-format compact` or
`MESMER_LOG_FORMAT=compact` when JSONL output is preferred.

Useful controls:

```bash
export MESMER_ATTACKER_MODEL=groq/llama-3.3-70b-versatile
export MESMER_EVALUATOR_MODEL=groq/llama-3.3-70b-versatile
export MESMER_TARGET_MODEL=groq/llama-3.3-70b-versatile
export MESMER_TAP_ROWS=1
export MESMER_TAP_DEPTH=10
export MESMER_TAP_WIDTH=10
export MESMER_TAP_BRANCHING_FACTOR=4
export MESMER_TAP_MAX_PARALLEL=5
export MESMER_TAP_KEEP_LAST_N=3
export MESMER_LOG_FORMAT=rich
```

The TAP paper uses AdvBench Subset: 50 requests across 32 categories. It also
reports a held-out 123-request dataset generated from AdvBench variants.
