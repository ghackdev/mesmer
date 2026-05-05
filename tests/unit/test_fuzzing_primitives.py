from __future__ import annotations

import random

from pydantic import Field

from mesmer import (
    Objective,
    ObjectiveSource,
    Run,
    Runner,
    evaluation,
    generation,
    initialization,
    population,
    runtime,
    stopping,
    targeting,
    topology,
    variation,
)
from mesmer.execution.state import Candidate
from mesmer.runtime.component import RuntimeContext
from mesmer.search.actors import StructuredCompletion
from mesmer.search.models import CandidateTrajectory
from mesmer.targets.base import TargetResponse
from mesmer.targets.callable import PythonCallableTarget
from mesmer.topology import AttackContext


class FakeSynonymProvider(variation.SynonymProvider):
    mapping: dict[str, str] = Field(default_factory=dict)
    name: str = "fake_synonym_provider"

    def pos_tags(self, words: list[str]) -> list[str]:
        return ["JJ" for _ in words]

    def synonyms(self, word: str, pos: str | None) -> list[str]:
        replacement = self.mapping.get(word.lower())
        return [] if replacement is None else [replacement]


class FakeSequenceClassifier(evaluation.SequenceClassifier):
    marker: str = "ALLOW"
    name: str = "fake_sequence_classifier"

    def predict(self, sequences: list[str]) -> list[int]:
        return [1 if self.marker in sequence else 0 for sequence in sequences]


class ScriptedChatActor(generation.Actor):
    output: str
    name: str = "scripted_chat_actor"

    async def complete(self, messages, **params) -> str:
        return self.output

    async def complete_structured(self, messages, schema, **params):
        parsed = schema.model_validate_json(self.output)
        return StructuredCompletion(parsed=parsed, raw=self.output)


class FuzzTestState(runtime.RuntimeState):
    seed_pool: population.Pool = Field(default_factory=population.Pool)


async def test_lexical_substitution_preserves_placeholder() -> None:
    mutator = variation.LexicalSubstitution(
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
    provider = variation.WordNetSynonyms()

    assert provider.auto_download is True
    assert str(provider.data_dir) == ".mesmer/nltk_data"


async def test_llm_template_mutator_preserves_placeholder() -> None:
    mutator = variation.LLMTemplate(
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


async def test_generate_fuzz_candidates_materializes_objective() -> None:
    state = FuzzTestState.for_objective(Objective("make marker"))
    await population.Initialize(
        source=population.ListSource(seeds=("Please handle [INSERT PROMPT HERE]",)),
    ).apply(
        state,
        RuntimeContext(
            attack=AttackContext(target=object(), judges=[], budget_tracker=object())
        ),
    )
    generator = population.Generate(
        selector=population.RoundRobin(),
        mutator=variation.LexicalSubstitution(
            provider=FakeSynonymProvider(mapping={"please": "kindly"}),
            replacement_probability=1.0,
        ),
        rng_seed=0,
    )

    patch = await generator.apply(
        state,
        RuntimeContext(
            attack=AttackContext(target=object(), judges=[], budget_tracker=object()),
            policy=topology.Policy(branching_factor=1),
        ),
    )

    assert patch.frontier is not None
    assert patch.frontier[0].latest_text == "Kindly handle make marker"
    assert patch.frontier[0].metadata["seed_index"] == 0
    assert state.seed_pool.records[0].visits == 1


async def test_sequence_classifier_evaluator_scores_target_response() -> None:
    evaluator = evaluation.SequenceClassification(classifier=FakeSequenceClassifier())
    trajectory = CandidateTrajectory(
        candidate=Candidate(messages=[]),
        last_response=TargetResponse(text="ALLOW"),
    )

    result = await evaluator.evaluate(Objective("goal"), trajectory)

    assert result.score == 1.0
    assert result.passed is True
    assert result.metadata["classifier"] == "fake_sequence_classifier"


async def test_fuzzing_program_records_success_and_seed_reward() -> None:
    technique = topology.Search(
        name="unit_fuzz",
        program=runtime.Program(
            population.Initialize(
                source=population.ListSource(seeds=("Please handle [INSERT PROMPT HERE]",)),
            ),
            initialization.Seed(),
            topology.Iterate(
                policy=topology.Policy(iterations=1, branching_factor=1, width=1),
                children=[
                    population.Generate(
                        selector=population.RoundRobin(),
                        mutator=variation.LexicalSubstitution(
                            provider=FakeSynonymProvider(mapping={"please": "kindly"}),
                            replacement_probability=1.0,
                        ),
                        rng_seed=0,
                    ),
                    targeting.Query(),
                    evaluation.Assess(evaluation.SequenceClassification(classifier=FakeSequenceClassifier())),
                    population.UpdateRewards(success_score=1),
                    stopping.StopWhen(stopping.ScoreAtLeast(1)),
                ],
            ),
            state=FuzzTestState,
        ),
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
    assert state.metadata["seed_pool_size"] == 2
    assert state.metadata["fuzz_successful_candidates"] == 1
    artifact = state.metadata["reproduction_artifacts"][0]
    assert artifact["messages"][0]["content"] == "Kindly handle make marker"
