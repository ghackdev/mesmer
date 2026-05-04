# Large Reasoning Models Are Autonomous Jailbreak Agents

This example maps the paper's harness mechanics onto Mesmer primitives:

- an attacker model proposes the next user turn;
- the target model receives the target-visible conversation transcript;
- an evaluator model scores the latest target response;
- evaluator feedback is fed back to the attacker;
- the run stops when the score threshold or turn budget is reached.

The paper does not provide an official public machine-readable dataset URL like the TAP
example's remote CSV. The script therefore uses a small benign built-in objective set by
default, and accepts authorized local datasets with `--dataset-csv` or `--dataset-jsonl`.

## Run

```bash
uv run python examples/papers/large_reasoning_models_autonomous_jailbreak_agents/run_autonomous_jailbreak_agent.py
```

By default the script uses `groq/llama-3.3-70b-versatile` for attacker, evaluator, and
target. Set `GROQ_API_KEY`, or override:

```bash
MESMER_ATTACKER_MODEL=gemini/gemini-2.5-flash \
MESMER_EVALUATOR_MODEL=gemini/gemini-2.5-flash \
MESMER_TARGET_MODEL=gemini/gemini-2.5-flash \
uv run python examples/papers/large_reasoning_models_autonomous_jailbreak_agents/run_autonomous_jailbreak_agent.py
```

Local dataset examples:

```bash
uv run python examples/papers/large_reasoning_models_autonomous_jailbreak_agents/run_autonomous_jailbreak_agent.py \
  --dataset-csv ./authorized_objectives.csv \
  --goal-column goal \
  --rows 5
```

```bash
uv run python examples/papers/large_reasoning_models_autonomous_jailbreak_agents/run_autonomous_jailbreak_agent.py \
  --dataset-jsonl ./authorized_objectives.jsonl \
  --rows 5
```

## New Generic Primitives Used

`ProposalMessageMode.APPEND_USER` lets `StructuredLLMProposer` append the generated user
message to the parent trajectory transcript instead of replacing the candidate with a
single-message prompt.

`ContinueConversation` appends each target response back into the trajectory as an
assistant message, so the next target call sees the full target-visible transcript.
