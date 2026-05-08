# Large Reasoning Models Are Autonomous Jailbreak Agents

This folder contains an autonomous-agent-inspired Mesmer example.

The current implementation uses the new architecture:

```text
Technique: techniques.FrontierSearch
Operators: ops.Propose -> ops.QueryTarget -> ops.Evaluate -> ops.StopWhen -> ops.AddFeedback -> ops.Select
Strategies: proposers.StructuredLLMProposer, evaluators.Contains, feedback.TemplateFeedback, selectors.TopKSelector
State: inferred from operator reads/writes
Trace: recorded as operator transitions in state_history
```

`ProposalMessageMode.APPEND_USER` lets the proposer append the generated user
message to the trajectory transcript, so each target call can preserve the
target-visible conversation. Feedback from the latest response is added before
the next proposal.

Run:

```bash
export GROQ_API_KEY=...
uv run python examples/papers/large_reasoning_models_autonomous_jailbreak_agents/run_autonomous_jailbreak_agent.py --iterations 2
```
