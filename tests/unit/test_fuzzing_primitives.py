from __future__ import annotations

import random

from pydantic import Field

from mesmer import (
    Objective,
    ObjectiveSource,
    Run,
    Runner,
    conditions,
    evaluators,
    mutators,
    ops,
    proposers,
    selectors,
    sources,
    techniques,
)
from mesmer.execution.state import Candidate
from mesmer.llm_actors import StructuredCompletion
from mesmer.targets.base import TargetResponse
from mesmer.targets.callable import PythonCallableTarget
from mesmer.trajectory import CandidateTrajectory


class FakeSynonymProvider(mutators.LexicalSynonymProvider):
    mapping: dict[str, str] = Field(default_factory=dict)
    name: str = "fake_synonym_provider"

    def pos_tags(self, words: list[str]) -> list[str]:
        return ["JJ" for _ in words]

    def synonyms(self, word: str, pos: str | None) -> list[str]:
        replacement = self.mapping.get(word.lower())
        return [] if replacement is None else [replacement]


class FakeSequenceClassifier(evaluators.SequenceClassifier):
    marker: str = "ALLOW"
    name: str = "fake_sequence_classifier"

    def predict(self, sequences: list[str]) -> list[int]:
        return [1 if self.marker in sequence else 0 for sequence in sequences]


class ScriptedChatActor(proposers.ChatActor):
    output: str
    name: str = "scripted_chat_actor"

    async def complete(self, messages, **params) -> str:
        return self.output

    async def complete_structured(self, messages, schema, **params):
        parsed = schema.model_validate_json(self.output)
        return StructuredCompletion(parsed=parsed, raw=self.output)


async def test_lexical_substitution_preserves_placeholder() -> None:
    mutator = mutators.LexicalSubstitutionMutator(
        provider=FakeSynonymProvider(mapping={"quick": "fast"}),
        replacement_probability=1.0,
    )

    result = await mutator.mutate(
        "Answer the quick request: [INSERT PROMPT HERE]",
        random.Random(0),
    )

    assert result.text == "Answer the fast request: [INSERT PROMPT HERE]"
    assert result.replacements == [{"from": "quick", "to": "fast", "pos": "JJ"}]


def test_nltk_provider_defaults_to_auto_download_cache() -> None:
    provider = mutators.NltkWordNetSynonymProvider()

    assert provider.auto_download is True
    assert str(provider.data_dir) == ".mesmer/nltk_data"


async def test_llm_template_mutator_preserves_placeholder() -> None:
    mutator = mutators.LLMTemplateMutator(
        actor=ScriptedChatActor(
            output='{"template":"In a realistic audit, analyze: [INSERT PROMPT HERE]"}'
        )
    )

    result = await mutator.mutate(
        "Please handle [INSERT PROMPT HERE]",
        random.Random(0),
    )

    assert result.text == "In a realistic audit, analyze: [INSERT PROMPT HERE]"
    assert result.metadata["actor"] == "scripted_chat_actor"


async def test_sequence_classifier_evaluator_scores_target_response() -> None:
    evaluator = evaluators.SequenceClassifierEvaluator(classifier=FakeSequenceClassifier())
    trajectory = CandidateTrajectory(
        candidate=Candidate(messages=[]),
        last_response=TargetResponse(text="ALLOW"),
    )

    result = await evaluator.evaluate(Objective(goal="goal"), trajectory)

    assert result.score == 1.0
    assert result.passed is True
    assert result.metadata["classifier"] == "fake_sequence_classifier"


async def test_population_fuzzing_records_success_and_seed_reward() -> None:
    technique = techniques.PopulationFuzzing(
        name="unit_fuzz",
        iterations=1,
        branching=1,
        width=1,
        load=ops.LoadPopulation(
            source=sources.ListSeedPoolSource(seeds=("Please handle [INSERT PROMPT HERE]",)),
        ),
        generate=ops.GenerateFromPopulation(
            selector=selectors.RoundRobinSeedSelector(),
            mutator=mutators.LexicalSubstitutionMutator(
                provider=FakeSynonymProvider(mapping={"please": "kindly"}),
                replacement_probability=1.0,
            ),
        ),
        evaluate=ops.Evaluate(
            evaluators=[
                evaluators.SequenceClassifierEvaluator(classifier=FakeSequenceClassifier())
            ]
        ),
        reward=ops.AssignReward(success_score=1),
        stop=ops.StopWhen(condition=conditions.ScoreAtLeast(score=1)),
    )
    run = Run(
        objectives=ObjectiveSource.single("make marker"),
        attack=technique,
        target=PythonCallableTarget(fn=lambda messages, context: "ALLOW"),
        judges=[],
    )

    result = await Runner().run(run)

    assert result.succeeded
    state = result.states[0]
    assert state.metadata["population_size"] == 2
    assert state.metadata["successful_candidates"] == 1
    artifact = state.metadata["reproduction_artifacts"][0]
    assert artifact["messages"][0]["content"] == "Kindly handle make marker"
