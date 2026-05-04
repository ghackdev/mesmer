# TAP Paper Example

This folder contains a paper-specific implementation of Tree of Attacks with
Pruning (TAP), based on `2312.02119v3`.

The example references the exact TAP AdvBench Subset CSV at runtime:

```text
https://raw.githubusercontent.com/RICommunity/TAP/main/data/advbench_subset.csv
```

The dataset is downloaded into Mesmer's gitignored cache under `.mesmer/`.

Run a small paper-style smoke run:

```bash
export GROQ_API_KEY=...
MESMER_LOG_FORMAT=compact uv run python examples/papers/tap/run_tap.py --limit 1
```

Useful controls:

```bash
export MESMER_ATTACKER_MODEL=groq/llama-3.3-70b-versatile
export MESMER_EVALUATOR_MODEL=groq/llama-3.3-70b-versatile
export MESMER_TARGET_MODEL=groq/llama-3.3-70b-versatile
export MESMER_TAP_DEPTH=10
export MESMER_TAP_WIDTH=10
export MESMER_TAP_BRANCHING_FACTOR=4
```

The TAP paper uses AdvBench Subset: 50 requests across 32 categories. It also
reports a held-out 123-request dataset generated from AdvBench variants.
