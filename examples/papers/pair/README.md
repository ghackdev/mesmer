# PAIR Paper Example

This folder contains a PAIR-inspired Mesmer example based on Prompt Automatic
Iterative Refinement (`2310.08419`).

The current implementation uses the new architecture:

```text
Technique: techniques.FrontierSearch
Operators: ops.Propose -> ops.QueryTarget -> ops.Evaluate -> ops.StopWhen -> ops.AddFeedback -> ops.Select
Strategies: proposers.StructuredLLMProposer, evaluators.Contains, feedback.TemplateFeedback, selectors.TopKSelector
State: inferred from operator reads/writes
Trace: recorded as operator transitions in state_history
```

The script keeps the PAIR shape: multiple streams, one target query per stream,
feedback into the next proposal, and a stop condition. The objective is a benign
canary test so it can run as a normal framework smoke example.

Run:

```bash
export GROQ_API_KEY=...
uv run python examples/papers/pair/run_pair.py --rows 1 --streams 2 --iterations 2
```
