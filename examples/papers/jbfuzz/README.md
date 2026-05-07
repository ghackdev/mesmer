# JBFuzz Paper Example

This folder contains a JBFuzz-inspired Mesmer example based on `2503.08990v1`.

The current implementation uses the new architecture:

```text
Technique: techniques.PopulationFuzzing
Operators: ops.LoadPopulation -> ops.GenerateFromPopulation -> ops.QueryTarget -> ops.Evaluate -> ops.AssignReward -> ops.StopWhen
Strategies: sources.List, selectors.UCB, mutators.Mutator, evaluators.Contains
State: inferred population pool, reward ledger, frontier, attempts, responses, evaluations
Trace: recorded as operator transitions in state_history
```

The script is a benign canary smoke test. It preserves the JBFuzz lifecycle:
load seeds, select a seed, mutate/materialize a candidate, query the target,
evaluate the response, update rewards, and stop on success.

Run:

```bash
export GROQ_API_KEY=...
uv run python examples/papers/jbfuzz/run_jbfuzz.py --rows 1 --iterations 1 --branching-factor 1 --seed-mode builtin --evaluator llm
```

Optional NLP/ML extras are no longer required for this smoke example.
