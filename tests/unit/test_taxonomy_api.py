from __future__ import annotations

import mesmer


def test_legacy_primitive_names_are_not_exported() -> None:
    removed = [
        "AttackGraph",
        "NodeFlow",
        "TreeSearchFlow",
        "AgentFlow",
        "SingleTurnFlow",
        "CandidateExpander",
        "CandidatePruner",
    ]

    assert all(not hasattr(mesmer, name) for name in removed)


def test_taxonomy_modules_are_exported() -> None:
    assert mesmer.generation.Propose
    assert mesmer.data.ObjectiveSource
    assert mesmer.selection.Select
    assert mesmer.evaluation.Assess
    assert mesmer.targeting.Query
