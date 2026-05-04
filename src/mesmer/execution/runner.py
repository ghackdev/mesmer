from __future__ import annotations

from pydantic import Field

from mesmer.core.config import MesmerModel
from mesmer.core.enums import LogFormat, RunOutcome, RunStatus, SpanName
from mesmer.core.errors import RuntimeExecutionError
from mesmer.execution.budgets import BudgetTracker
from mesmer.execution.run import Run
from mesmer.execution.state import AttackState, Attempt
from mesmer.flows.base import AttackContext
from mesmer.telemetry.logger import RunLogger
from mesmer.telemetry.tracing import start_span


class RunResult(MesmerModel):
    run_id: str
    status: RunStatus
    states: list[AttackState] = Field(default_factory=list)
    error: str | None = None

    @property
    def attempts_count(self) -> int:
        return sum(len(state.attempts) for state in self.states)

    @property
    def succeeded(self) -> bool:
        return any(attempt.succeeded for state in self.states for attempt in state.attempts)

    @property
    def outcome(self) -> RunOutcome:
        if self.status == RunStatus.FAILED:
            return RunOutcome.EXECUTION_FAILED
        if self.succeeded:
            return RunOutcome.OBJECTIVE_SUCCEEDED
        return RunOutcome.OBJECTIVE_FAILED


class Runner(MesmerModel):
    name: str = "runner"
    verbose: bool = False
    log_format: LogFormat = LogFormat.RICH
    max_log_text_chars: int | None = None
    results: list[RunResult] = Field(default_factory=list)

    async def run(self, run: Run) -> RunResult:
        logger = RunLogger(
            verbose=self.verbose,
            log_format=self.log_format,
            max_text_chars=self._resolved_max_log_text_chars(),
        )
        logger.emit(
            "run.start",
            run_id=run.id,
            attack=run.attack.name,
            target=run.target.name,
            judges=[judge.name for judge in run.judges],
        )
        with start_span(SpanName.RUN.value, {"run.id": run.id, "attack": run.attack.name}):
            await run.recorder.start_run(run.id)
            states: list[AttackState] = []
            try:
                for objective in run.objectives:
                    logger.emit("objective.start", objective_id=objective.id, goal=objective.goal)
                    with start_span(
                        SpanName.OBJECTIVE.value,
                        {"objective.id": objective.id, "objective.goal": objective.goal},
                    ):
                        budget_tracker = BudgetTracker(run.budget)
                        context = AttackContext(
                            target=run.target,
                            judges=run.judges,
                            budget_tracker=budget_tracker,
                            recorder=run.recorder,
                            logger=logger,
                        )
                        state = await run.attack.execute(objective, context)
                        self._emit_objective_success(
                            logger,
                            state,
                            attack_name=run.attack.name,
                            target_name=run.target.name,
                            target_system_prompt=getattr(run.target, "system_prompt", None),
                        )
                        states.append(state)
                result = RunResult(run_id=run.id, status=RunStatus.SUCCEEDED, states=states)
            except Exception as exc:
                logger.emit("run.error", error=str(exc))
                if isinstance(exc, RuntimeExecutionError):
                    states.append(exc.state.attack_state)
                result = RunResult(
                    run_id=run.id,
                    status=RunStatus.FAILED,
                    states=states,
                    error=str(exc),
                )
            await run.recorder.finish_run(run.id)
            logger.emit(
                "run.finish",
                outcome=result.outcome.value,
                execution_status=result.status.value,
                succeeded=result.succeeded,
                attempts=result.attempts_count,
            )
            self.results.append(result)
            return result

    def _resolved_max_log_text_chars(self) -> int | None:
        if self.max_log_text_chars is not None:
            return self.max_log_text_chars
        if self.log_format == LogFormat.COMPACT:
            return None
        return 600

    def _emit_objective_success(
        self,
        logger: RunLogger,
        state: AttackState,
        *,
        attack_name: str,
        target_name: str,
        target_system_prompt: str | None,
    ) -> None:
        attempt = next((item for item in state.attempts if item.succeeded), None)
        if attempt is None:
            return
        artifact = _reproduction_artifact(
            attempt,
            attack_name=attack_name,
            target_name=target_name,
            target_system_prompt=target_system_prompt,
        )
        state.metadata["successful_reproduction"] = artifact
        logger.emit("objective.success", **artifact)


def _reproduction_artifact(
    attempt: Attempt,
    *,
    attack_name: str,
    target_name: str,
    target_system_prompt: str | None,
) -> dict[str, object]:
    messages = [
        {
            "role": message.role.value,
            "content": message.content,
        }
        for message in attempt.candidate.messages
    ]
    user_messages = [message["content"] for message in messages if message["role"] == "user"]
    final_prompt = str(user_messages[-1]) if user_messages else ""
    successful_judgement = next(
        (judgement for judgement in attempt.judgements if judgement.status.value == "pass"),
        attempt.judgements[0] if attempt.judgements else None,
    )
    score = successful_judgement.score if successful_judgement is not None else None
    reason = successful_judgement.reason if successful_judgement is not None else ""
    mode = "single_turn" if len(messages) == 1 else "multi_turn"
    reproduction = (
        f"Run the {mode} candidate against target '{target_name}' using attack '{attack_name}'. "
        "Use the listed target system prompt, then send the listed message sequence in order. "
        "The final user prompt is the candidate that produced the successful target response."
    )
    return {
        "objective_id": attempt.objective.id,
        "goal": attempt.objective.goal,
        "attempt_id": attempt.id,
        "candidate_id": attempt.candidate.id,
        "response_id": attempt.response.id,
        "turn": attempt.turn,
        "mode": mode,
        "target": target_name,
        "target_system_prompt": target_system_prompt,
        "prompt": final_prompt,
        "messages": messages,
        "response": attempt.response.text,
        "score": score,
        "reason": reason,
        "reproduction": reproduction,
    }
