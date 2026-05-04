from __future__ import annotations

from mesmer.core.errors import RuntimeExecutionError
from mesmer.flows.base import AttackContext
from mesmer.objectives.models import Objective
from mesmer.runtime.component import Program, RuntimeContext
from mesmer.runtime.state import RuntimeState


class ProgramExecutor:
    def __init__(self, program: Program) -> None:
        self.program = program

    async def execute(self, objective: Objective, context: AttackContext) -> RuntimeState:
        state = self.program.state.for_objective(objective)
        try:
            self.program.validate(state.provided)
            state.apply_patch(await self.program.apply(state, RuntimeContext(attack=context)))
        except Exception as exc:
            self._finalize_state(state)
            raise RuntimeExecutionError(str(exc), state=state) from exc
        self._finalize_state(state)
        return state

    def _finalize_state(self, state: RuntimeState) -> None:
        state.attack_state.metadata["runtime_state_type"] = state.__class__.__name__
        state.attack_state.metadata["state_history"] = [
            transition.model_dump(mode="json") for transition in state.history
        ]
