from __future__ import annotations

from abc import ABC, abstractmethod

from mesmer.artifacts.messages import assistant_message, user_message
from mesmer.attackers.agent.actions import AgentAction
from mesmer.attackers.agent.memory import EpisodicMemory
from mesmer.attackers.agent.policy import AgentPolicy
from mesmer.core.config import MesmerModel
from mesmer.execution.state import Candidate
from mesmer.objectives.models import Objective


class ActionLoop(MesmerModel, ABC):
    name: str
    policy: AgentPolicy = AgentPolicy()

    @abstractmethod
    async def next_candidate(
        self,
        objective: Objective,
        memory: EpisodicMemory,
        history: list[AgentAction],
    ) -> Candidate | None:
        raise NotImplementedError


class ReActLoop(ActionLoop):
    name: str = "react"

    async def next_candidate(
        self,
        objective: Objective,
        memory: EpisodicMemory,
        history: list[AgentAction],
    ) -> Candidate | None:
        if len(history) >= self.policy.max_steps:
            return None
        messages = list(objective.initial_state.messages)
        if not messages:
            messages = [user_message(objective.goal)]
        if memory.entries:
            messages.insert(0, assistant_message(f"Prior observations:\n{memory.render()}"))
        return Candidate(messages=messages, metadata={"loop": self.name, "step": len(history) + 1})


class PlanExecuteLoop(ReActLoop):
    name: str = "plan_execute"


class TreeSearchLoop(ReActLoop):
    name: str = "tree_search"


class DebateLoop(ReActLoop):
    name: str = "debate"


class ScriptedLoop(ReActLoop):
    name: str = "scripted"
