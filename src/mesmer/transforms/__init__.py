from __future__ import annotations

import base64
import codecs
from abc import ABC, abstractmethod
from typing import Any

from pydantic import Field

from mesmer.artifacts.messages import Message
from mesmer.core.config import MesmerModel
from mesmer.core.enums import MessageRole
from mesmer.evidence import TransformKind, TransformProvenance
from mesmer.execution.state import Candidate
from mesmer.objectives.models import Objective
from mesmer.trajectory import CandidateTrajectory

LATEST_USER = "latest_user"
ALL_USER = "all_user"
NEW_USER_SINCE_PARENT = "new_user_since_parent"
ALL_TARGET_VISIBLE_USER = "all_target_visible_user"
SUPPORTED_SCOPES = {
    LATEST_USER,
    ALL_USER,
    NEW_USER_SINCE_PARENT,
    ALL_TARGET_VISIBLE_USER,
}


class TransformSpec(MesmerModel):
    name: str
    params: dict[str, Any] = Field(default_factory=dict)


class Transform(MesmerModel, ABC):
    name: str
    kind: TransformKind = TransformKind.GENERIC
    intent_preserving: bool | None = None

    @abstractmethod
    async def transform(
        self,
        objective: Objective,
        trajectory: CandidateTrajectory,
    ) -> list[CandidateTrajectory]:
        raise NotImplementedError

    def provenance(self, **params: Any) -> dict[str, Any]:
        return TransformProvenance(
            name=self.name,
            kind=self.kind.value,
            intent_preserving=self.intent_preserving,
            params=params,
        ).model_dump(mode="json")


class Encode(Transform):
    codec: str = "base64"
    scope: str = LATEST_USER
    wrap: bool = False
    request_encoded_output: bool = False
    wrap_template: str | None = None
    name: str = "encode"
    kind: TransformKind = TransformKind.ENCODING
    intent_preserving: bool | None = True

    async def transform(
        self,
        objective: Objective,
        trajectory: CandidateTrajectory,
    ) -> list[CandidateTrajectory]:
        indices = _message_indices(trajectory.candidate.messages, self.scope)
        messages = [message.model_copy(deep=True) for message in trajectory.candidate.messages]
        replacements: list[dict[str, Any]] = []
        for index in indices:
            original = messages[index].content
            encoded = self._encode(original)
            content = self._wrap(encoded) if self.wrap else encoded
            messages[index].content = content
            replacements.append(
                {
                    "message_index": index,
                    "codec": self.codec,
                    "scope": self.scope,
                    "wrapped": self.wrap,
                }
            )
        if not replacements:
            return []
        metadata = {
            "transform": self.name,
            "codec": self.codec,
            "scope": self.scope,
            "operator_chain": [_spec_payload(self.name, self._spec_params())],
            "transform_provenance": self.provenance(**self._spec_params()),
            "transform_replacements": replacements,
        }
        return [_child_trajectory(trajectory, messages, metadata)]

    def _encode(self, value: str) -> str:
        if self.codec == "base64":
            return base64.b64encode(value.encode("utf-8")).decode("ascii")
        if self.codec == "rot13":
            return codecs.encode(value, "rot_13")
        raise ValueError(f"Unsupported encode codec: {self.codec}")

    def _wrap(self, payload: str) -> str:
        if self.wrap_template is not None:
            return self.wrap_template.format(payload=payload, codec=self.codec)
        output_clause = (
            f", and write your output in {self.codec}"
            if self.request_encoded_output
            else ""
        )
        return f"Respond to the following {self.codec}-encoded request{output_clause}:\n{payload}"

    def _spec_params(self) -> dict[str, Any]:
        return {
            "codec": self.codec,
            "scope": self.scope,
            "wrap": self.wrap,
            "request_encoded_output": self.request_encoded_output,
        }


class TemplateWrap(Transform):
    templates: tuple[str, ...]
    scope: str = LATEST_USER
    name: str = "template_wrap"
    kind: TransformKind = TransformKind.TEMPLATE
    intent_preserving: bool | None = None

    async def transform(
        self,
        objective: Objective,
        trajectory: CandidateTrajectory,
    ) -> list[CandidateTrajectory]:
        indices = _message_indices(trajectory.candidate.messages, self.scope)
        if not indices:
            return []
        variants: list[CandidateTrajectory] = []
        for variant_index, template in enumerate(self.templates):
            messages = [message.model_copy(deep=True) for message in trajectory.candidate.messages]
            for index in indices:
                messages[index].content = template.format(
                    prompt=messages[index].content,
                    objective=objective.goal,
                    goal=objective.goal,
                )
            metadata = {
                "transform": self.name,
                "scope": self.scope,
                "template": template,
                "variant_index": variant_index,
                "operator_chain": [
                    _spec_payload(
                        self.name,
                        {"scope": self.scope, "template": template},
                    )
                ],
                "transform_provenance": self.provenance(
                    scope=self.scope,
                    template=template,
                ),
            }
            variants.append(_child_trajectory(trajectory, messages, metadata))
        return variants


class AppendSuffix(Transform):
    suffixes: tuple[str, ...]
    separator: str = " "
    scope: str = LATEST_USER
    name: str = "append_suffix"
    kind: TransformKind = TransformKind.SUFFIX
    intent_preserving: bool | None = False

    async def transform(
        self,
        objective: Objective,
        trajectory: CandidateTrajectory,
    ) -> list[CandidateTrajectory]:
        indices = _message_indices(trajectory.candidate.messages, self.scope)
        if not indices:
            return []
        variants: list[CandidateTrajectory] = []
        for variant_index, suffix in enumerate(self.suffixes):
            messages = [message.model_copy(deep=True) for message in trajectory.candidate.messages]
            for index in indices:
                messages[index].content = f"{messages[index].content}{self.separator}{suffix}"
            metadata = {
                "transform": self.name,
                "scope": self.scope,
                "suffix": suffix,
                "separator": self.separator,
                "variant_index": variant_index,
                "operator_chain": [
                    _spec_payload(
                        self.name,
                        {
                            "scope": self.scope,
                            "suffix": suffix,
                            "separator": self.separator,
                        },
                    )
                ],
                "transform_provenance": self.provenance(
                    scope=self.scope,
                    suffix=suffix,
                    separator=self.separator,
                ),
            }
            variants.append(_child_trajectory(trajectory, messages, metadata))
        return variants


class PayloadSplit(Transform):
    pieces: int = Field(default=2, ge=2)
    scope: str = LATEST_USER
    variable_prefix: str = "part"
    name: str = "payload_split"
    kind: TransformKind = TransformKind.PAYLOAD_SPLIT
    intent_preserving: bool | None = True

    async def transform(
        self,
        objective: Objective,
        trajectory: CandidateTrajectory,
    ) -> list[CandidateTrajectory]:
        indices = _message_indices(trajectory.candidate.messages, self.scope)
        if not indices:
            return []
        messages = [message.model_copy(deep=True) for message in trajectory.candidate.messages]
        for index in indices:
            value = messages[index].content
            chunks = _split_text(value, self.pieces)
            assignments = "\n".join(
                f"{self.variable_prefix}_{chunk_index + 1} = {chunk!r}"
                for chunk_index, chunk in enumerate(chunks)
            )
            expression = " + ".join(
                f"{self.variable_prefix}_{chunk_index + 1}"
                for chunk_index in range(len(chunks))
            )
            messages[index].content = (
                f"{assignments}\n\nReconstruct and respond to: {{{expression}}}"
            )
        metadata = {
            "transform": self.name,
            "scope": self.scope,
            "pieces": self.pieces,
            "operator_chain": [
                _spec_payload(
                    self.name,
                    {
                        "scope": self.scope,
                        "pieces": self.pieces,
                        "variable_prefix": self.variable_prefix,
                    },
                )
            ],
            "transform_provenance": self.provenance(
                scope=self.scope,
                pieces=self.pieces,
                variable_prefix=self.variable_prefix,
            ),
        }
        return [_child_trajectory(trajectory, messages, metadata)]


class CharacterRewrite(Transform):
    strategy: str
    scope: str = LATEST_USER
    name: str = "character_rewrite"
    kind: TransformKind = TransformKind.CHARACTER_REWRITE
    intent_preserving: bool | None = None

    async def transform(
        self,
        objective: Objective,
        trajectory: CandidateTrajectory,
    ) -> list[CandidateTrajectory]:
        indices = _message_indices(trajectory.candidate.messages, self.scope)
        if not indices:
            return []
        messages = [message.model_copy(deep=True) for message in trajectory.candidate.messages]
        for index in indices:
            messages[index].content = self._rewrite(messages[index].content)
        metadata = {
            "transform": self.name,
            "strategy": self.strategy,
            "scope": self.scope,
            "operator_chain": [
                _spec_payload(
                    self.name,
                    {"strategy": self.strategy, "scope": self.scope},
                )
            ],
            "transform_provenance": self.provenance(
                strategy=self.strategy,
                scope=self.scope,
            ),
        }
        return [_child_trajectory(trajectory, messages, metadata)]

    def _rewrite(self, value: str) -> str:
        if self.strategy == "disemvowel":
            return "".join(character for character in value if character.lower() not in "aeiou")
        if self.strategy == "leetspeak":
            table = str.maketrans(
                {
                    "a": "@",
                    "A": "@",
                    "e": "3",
                    "E": "3",
                    "i": "!",
                    "I": "!",
                    "o": "0",
                    "O": "0",
                    "s": "$",
                    "S": "$",
                    "t": "7",
                    "T": "7",
                }
            )
            return value.translate(table)
        raise ValueError(f"Unsupported character rewrite strategy: {self.strategy}")


class StyleTransfer(Transform):
    style: str
    template: str = (
        "Rewrite the following request in {style} style while preserving intent:\n{prompt}"
    )
    scope: str = LATEST_USER
    name: str = "style_transfer"
    kind: TransformKind = TransformKind.STYLE
    intent_preserving: bool | None = True

    async def transform(
        self,
        objective: Objective,
        trajectory: CandidateTrajectory,
    ) -> list[CandidateTrajectory]:
        indices = _message_indices(trajectory.candidate.messages, self.scope)
        if not indices:
            return []
        messages = [message.model_copy(deep=True) for message in trajectory.candidate.messages]
        for index in indices:
            messages[index].content = self.template.format(
                style=self.style,
                prompt=messages[index].content,
                objective=objective.goal,
                goal=objective.goal,
            )
        metadata = {
            "transform": self.name,
            "style": self.style,
            "scope": self.scope,
            "operator_chain": [
                _spec_payload(
                    self.name,
                    {"style": self.style, "scope": self.scope},
                )
            ],
            "transform_provenance": self.provenance(style=self.style, scope=self.scope),
        }
        return [_child_trajectory(trajectory, messages, metadata)]


class LexicalAnchorInject(Transform):
    anchors: tuple[str, ...]
    scope: str = LATEST_USER
    separator: str = " "
    name: str = "lexical_anchor_inject"
    kind: TransformKind = TransformKind.LEXICAL_ANCHOR
    intent_preserving: bool | None = False

    async def transform(
        self,
        objective: Objective,
        trajectory: CandidateTrajectory,
    ) -> list[CandidateTrajectory]:
        indices = _message_indices(trajectory.candidate.messages, self.scope)
        if not indices:
            return []
        messages = [message.model_copy(deep=True) for message in trajectory.candidate.messages]
        anchor_text = self.separator.join(self.anchors)
        for index in indices:
            messages[index].content = f"{messages[index].content}{self.separator}{anchor_text}"
        metadata = {
            "transform": self.name,
            "anchors": list(self.anchors),
            "scope": self.scope,
            "operator_chain": [
                _spec_payload(
                    self.name,
                    {"anchors": list(self.anchors), "scope": self.scope},
                )
            ],
            "transform_provenance": self.provenance(
                anchors=list(self.anchors),
                scope=self.scope,
            ),
        }
        return [_child_trajectory(trajectory, messages, metadata)]


class DemonstrationPack(Transform):
    demonstrations: tuple[str, ...]
    scope: str = LATEST_USER
    separator: str = "\n\n"
    name: str = "demonstration_pack"
    kind: TransformKind = TransformKind.DEMONSTRATION_PACK
    intent_preserving: bool | None = False

    async def transform(
        self,
        objective: Objective,
        trajectory: CandidateTrajectory,
    ) -> list[CandidateTrajectory]:
        indices = _message_indices(trajectory.candidate.messages, self.scope)
        if not indices:
            return []
        messages = [message.model_copy(deep=True) for message in trajectory.candidate.messages]
        prefix = self.separator.join(self.demonstrations)
        for index in indices:
            messages[index].content = f"{prefix}{self.separator}{messages[index].content}"
        metadata = {
            "transform": self.name,
            "demonstration_count": len(self.demonstrations),
            "scope": self.scope,
            "operator_chain": [
                _spec_payload(
                    self.name,
                    {
                        "demonstration_count": len(self.demonstrations),
                        "scope": self.scope,
                    },
                )
            ],
            "transform_provenance": self.provenance(
                demonstration_count=len(self.demonstrations),
                scope=self.scope,
            ),
        }
        return [_child_trajectory(trajectory, messages, metadata)]


class AugmentText(Transform):
    variants: tuple[str, ...]
    scope: str = LATEST_USER
    name: str = "augment_text"
    kind: TransformKind = TransformKind.AUGMENTATION
    intent_preserving: bool | None = None

    async def transform(
        self,
        objective: Objective,
        trajectory: CandidateTrajectory,
    ) -> list[CandidateTrajectory]:
        indices = _message_indices(trajectory.candidate.messages, self.scope)
        if not indices:
            return []
        augmented: list[CandidateTrajectory] = []
        for variant_index, variant in enumerate(self.variants):
            messages = [message.model_copy(deep=True) for message in trajectory.candidate.messages]
            for index in indices:
                messages[index].content = variant.format(
                    prompt=messages[index].content,
                    objective=objective.goal,
                    goal=objective.goal,
                )
            metadata = {
                "transform": self.name,
                "variant_index": variant_index,
                "scope": self.scope,
                "operator_chain": [
                    _spec_payload(
                        self.name,
                        {"variant_index": variant_index, "scope": self.scope},
                    )
                ],
                "transform_provenance": self.provenance(
                    variant_index=variant_index,
                    scope=self.scope,
                ),
            }
            augmented.append(_child_trajectory(trajectory, messages, metadata))
        return augmented


class Compose(Transform):
    transforms: tuple[Transform, ...]
    name: str = "compose"

    async def transform(
        self,
        objective: Objective,
        trajectory: CandidateTrajectory,
    ) -> list[CandidateTrajectory]:
        frontier = [trajectory]
        for transform in self.transforms:
            next_frontier: list[CandidateTrajectory] = []
            for item in frontier:
                next_frontier.extend(await transform.transform(objective, item))
            frontier = next_frontier
            if not frontier:
                break
        for item in frontier:
            item.metadata["transform"] = self.name
            item.candidate.metadata["transform"] = self.name
        return frontier


class FromPromptPattern(Transform):
    patterns_metadata_key: str = "selected_prompt_patterns"
    name: str = "from_prompt_pattern"

    async def transform(
        self,
        objective: Objective,
        trajectory: CandidateTrajectory,
    ) -> list[CandidateTrajectory]:
        patterns = list(trajectory.prompt_patterns.patterns)
        variants: list[CandidateTrajectory] = []
        for pattern_index, pattern in enumerate(patterns):
            templates = pattern.get("templates", [])
            specs = pattern.get("suggested_transforms", [])
            if not templates and not specs:
                continue
            frontier = await _template_variants(objective, trajectory, pattern)
            if specs:
                transform = Compose(
                    transforms=tuple(
                        _transform_from_spec(TransformSpec.model_validate(spec))
                        for spec in specs
                    )
                )
                transformed: list[CandidateTrajectory] = []
                for item in frontier:
                    transformed.extend(await transform.transform(objective, item))
                frontier = transformed
            for variant in frontier:
                metadata = {
                    "prompt_pattern_id": pattern.get("id"),
                    "prompt_pattern_name": pattern.get("name"),
                    "prompt_pattern_index": pattern_index,
                    "transform": self.name,
                }
                variant.metadata.update(metadata)
                variant.candidate.metadata.update(metadata)
                chain = variant.metadata.get("operator_chain", [])
                variant.metadata["operator_chain"] = chain
                variant.candidate.metadata["operator_chain"] = chain
                variants.append(variant)
        return variants


def _message_indices(messages: list[Message], scope: str) -> list[int]:
    if scope not in SUPPORTED_SCOPES:
        raise ValueError(f"Unsupported transform scope: {scope}")
    user_indices = [
        index for index, message in enumerate(messages) if message.role == MessageRole.USER
    ]
    if scope in {ALL_USER, ALL_TARGET_VISIBLE_USER}:
        return user_indices
    if scope in {LATEST_USER, NEW_USER_SINCE_PARENT}:
        return user_indices[-1:] if user_indices else []
    return []


def _child_trajectory(
    parent: CandidateTrajectory,
    messages: list[Message],
    metadata: dict[str, Any],
) -> CandidateTrajectory:
    chain = [
        *parent.metadata.get("operator_chain", []),
        *metadata.get("operator_chain", []),
    ]
    payload = {
        **parent.candidate.metadata,
        **metadata,
        "parent_candidate_id": parent.candidate.id,
        "parent_trajectory_id": parent.id,
        "operator_chain": chain,
    }
    trajectory_metadata = {
        **parent.metadata,
        **metadata,
        "parent_trajectory_id": parent.id,
        "operator_chain": chain,
    }
    return CandidateTrajectory(
        candidate=Candidate(messages=messages, metadata=payload),
        depth=parent.depth + 1,
        parent_id=parent.id,
        actor_history=list(parent.actor_history),
        feedback=list(parent.feedback),
        proposal=parent.proposal.model_copy(deep=True),
        prompt_patterns=parent.prompt_patterns.model_copy(deep=True),
        inference_summary=(
            parent.inference_summary.model_copy(deep=True)
            if parent.inference_summary is not None
            else None
        ),
        population=parent.population.model_copy(deep=True),
        strategy_labels=list(parent.strategy_labels),
        serialized_conversation_id=parent.serialized_conversation_id,
        metadata=trajectory_metadata,
    )


def _transform_from_spec(spec: TransformSpec) -> Transform:
    if spec.name == "encode":
        return Encode(**spec.params)
    if spec.name == "template_wrap":
        return TemplateWrap(**spec.params)
    if spec.name == "append_suffix":
        return AppendSuffix(**spec.params)
    if spec.name == "payload_split":
        return PayloadSplit(**spec.params)
    if spec.name == "character_rewrite":
        return CharacterRewrite(**spec.params)
    if spec.name == "style_transfer":
        return StyleTransfer(**spec.params)
    if spec.name == "lexical_anchor_inject":
        return LexicalAnchorInject(**spec.params)
    if spec.name == "demonstration_pack":
        return DemonstrationPack(**spec.params)
    if spec.name == "augment_text":
        return AugmentText(**spec.params)
    raise ValueError(f"Unsupported transform spec: {spec.name}")


async def _template_variants(
    objective: Objective,
    trajectory: CandidateTrajectory,
    pattern: dict[str, Any],
) -> list[CandidateTrajectory]:
    templates = [
        template["text"] if isinstance(template, dict) else str(template)
        for template in pattern.get("templates", [])
    ]
    if not templates:
        return [trajectory]
    return await TemplateWrap(templates=tuple(templates)).transform(objective, trajectory)


def _spec_payload(name: str, params: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "params": params}


def _split_text(value: str, pieces: int) -> list[str]:
    if not value:
        return [""]
    size = max(1, (len(value) + pieces - 1) // pieces)
    return [value[index : index + size] for index in range(0, len(value), size)]


__all__ = [
    "ALL_TARGET_VISIBLE_USER",
    "ALL_USER",
    "LATEST_USER",
    "NEW_USER_SINCE_PARENT",
    "SUPPORTED_SCOPES",
    "AppendSuffix",
    "AugmentText",
    "CharacterRewrite",
    "Compose",
    "DemonstrationPack",
    "Encode",
    "FromPromptPattern",
    "LexicalAnchorInject",
    "PayloadSplit",
    "StyleTransfer",
    "TemplateWrap",
    "Transform",
    "TransformKind",
    "TransformProvenance",
    "TransformSpec",
]
