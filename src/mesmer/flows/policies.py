from __future__ import annotations

from mesmer.core.config import MesmerModel
from mesmer.core.constants import DEFAULT_MAX_TURNS


class TreeSearchPolicy(MesmerModel):
    depth: int = 3
    branching_factor: int = 3
    width: int = 2
    stop_on_success: bool = True


class ConversationPolicy(MesmerModel):
    max_turns: int = DEFAULT_MAX_TURNS
    stop_on_success: bool = True
    include_full_history: bool = True


class EvolutionaryPolicy(MesmerModel):
    population_size: int = 8
    generations: int = 3
    mutation_rate: float = 0.2
    selection_width: int = 4
    stop_on_success: bool = True
