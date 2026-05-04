from __future__ import annotations

from pydantic import Field

from mesmer.artifacts.messages import Message, assistant_message, system_message
from mesmer.core.config import MesmerModel
from mesmer.core.enums import LogFormat, RunOutcome, RunStatus, SpanName
from mesmer.core.errors import RuntimeExecutionError
from mesmer.execution.budgets import BudgetTracker
from mesmer.execution.run import Run
from mesmer.execution.state import (
    AttackState,
    Attempt,
    ReproductionArtifact,
    ReproductionTarget,
)
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
                        self._store_objective_success(
                            state,
                            attack_name=run.attack.name,
                            target_name=run.target.name,
                            target_model=getattr(run.target, "model", None),
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
            self._emit_reproduction_artifacts(logger, states)
            self.results.append(result)
            return result

    def _resolved_max_log_text_chars(self) -> int | None:
        if self.max_log_text_chars is not None:
            return self.max_log_text_chars
        if self.log_format == LogFormat.COMPACT:
            return None
        return 600

    def _store_objective_success(
        self,
        state: AttackState,
        *,
        attack_name: str,
        target_name: str,
        target_model: str | None,
        target_system_prompt: str | None,
    ) -> None:
        attempts = [item for item in state.attempts if item.succeeded]
        if not attempts:
            return
        artifacts = [
            _reproduction_artifact(
                attempt,
                attack_name=attack_name,
                target_name=target_name,
                target_model=target_model,
                target_system_prompt=target_system_prompt,
            ).model_dump(mode="json")
            for attempt in attempts
        ]
        state.metadata["reproduction_artifacts"] = artifacts

    def _emit_reproduction_artifacts(
        self,
        logger: RunLogger,
        states: list[AttackState],
    ) -> None:
        for state in states:
            artifacts = state.metadata.get("reproduction_artifacts", [])
            if not isinstance(artifacts, list):
                continue
            for artifact in artifacts:
                if isinstance(artifact, dict):
                    logger.emit("objective.success", **_compact_success_fields(artifact))


def _reproduction_artifact(
    attempt: Attempt,
    *,
    attack_name: str,
    target_name: str,
    target_model: str | None,
    target_system_prompt: str | None,
) -> ReproductionArtifact:
    messages = _reproduction_messages(attempt, target_system_prompt)
    successful_judgement = next(
        (judgement for judgement in attempt.judgements if judgement.status.value == "pass"),
        attempt.judgements[0] if attempt.judgements else None,
    )
    raw_score = (
        successful_judgement.metadata.get("raw_score")
        if successful_judgement is not None
        else None
    )
    normalized_score = successful_judgement.score if successful_judgement is not None else None
    reason = successful_judgement.reason if successful_judgement is not None else ""
    return ReproductionArtifact(
        objective=attempt.objective,
        attempt_id=attempt.id,
        candidate_id=attempt.candidate.id,
        response_id=attempt.response.id,
        turn=attempt.turn,
        target=ReproductionTarget(
            name=target_name,
            model=target_model,
            system_prompt=target_system_prompt,
        ),
        messages=messages,
        score=raw_score if raw_score is not None else normalized_score,
        normalized_score=normalized_score,
        reason=reason,
        judgement=successful_judgement,
        trace={
            "attack": attack_name,
            **attempt.metadata.get("trace", {}),
        },
    )


def _compact_success_fields(artifact: dict[str, object]) -> dict[str, object]:
    objective = artifact.get("objective", {})
    assert isinstance(objective, dict)
    return {
        "artifact_id": artifact.get("id"),
        "objective_id": objective.get("id"),
        "goal": objective.get("goal"),
        "attempt_id": artifact.get("attempt_id"),
        "candidate_id": artifact.get("candidate_id"),
        "response_id": artifact.get("response_id"),
        "turn": artifact.get("turn"),
        "target": artifact.get("target"),
        "messages": artifact["messages"],
        "score": artifact.get("score"),
        "normalized_score": artifact.get("normalized_score"),
        "reason": artifact.get("reason"),
        "trace": artifact.get("trace", {}),
    }


def _reproduction_messages(
    attempt: Attempt,
    target_system_prompt: str | None,
) -> list[Message]:
    messages: list[Message] = []
    if target_system_prompt:
        messages.append(system_message(target_system_prompt))
    messages.extend(attempt.candidate.messages)
    messages.append(
        assistant_message(attempt.response.text).model_copy(
            update={
                "metadata": {
                    "response_id": attempt.response.id,
                    "finish_reason": attempt.response.metadata.get("finish_reason"),
                    "input_tokens": attempt.response.input_tokens,
                    "output_tokens": attempt.response.output_tokens,
                    "latency_ms": attempt.response.latency_ms,
                    **attempt.response.metadata,
                }
            }
        )
    )
    return messages
