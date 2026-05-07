# TAP Paper Example

This folder contains a TAP-inspired Mesmer example based on Tree of Attacks with
Pruning (`2312.02119v3`).

The current implementation uses the new architecture:

```text
Technique: techniques.FrontierSearch
Operators: ops.Propose -> ops.QueryTarget -> ops.Evaluate -> ops.StopWhen -> ops.Select
Strategies: proposers.StructuredLLM, evaluators.Contains, selectors.TopK
State: inferred from operator reads/writes
Trace: recorded as operator transitions in state_history
```

The script is intentionally a benign canary smoke test. Paper-specific harmful
datasets are not copied into this repository.

Run:

```bash
export GROQ_API_KEY=...
uv run python examples/papers/tap/run_tap.py --limit 1 --iterations 1 --width 1 --branching-factor 1
```

Use `MESMER_LOG_FORMAT=compact` when JSONL output is preferred.
