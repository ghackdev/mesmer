from __future__ import annotations

import mesmer


def test_removed_public_names_are_not_exported() -> None:
    removed = [
        "runtime",
        "topology",
        "generation",
        "evaluation",
        "selection",
        "variation",
        "population",
        "stopping",
        "targeting",
        "initialization",
        "constraints",
        "data",
        "search",
        "flows",
        "attackers",
    ]

    assert all(not hasattr(mesmer, name) for name in removed)


def test_taxonomy_modules_are_exported() -> None:
    assert mesmer.sources.ObjectiveSource
    assert mesmer.techniques.FrontierSearch
    assert mesmer.ops.Propose
    assert mesmer.ops.QueryTarget
    assert mesmer.ops.Evaluate
    assert mesmer.ops.StopWhen
    assert mesmer.proposers.Template
    assert mesmer.evaluators.Contains
    assert mesmer.selectors.TopKSelector
    assert mesmer.conditions.ScoreAtLeast
