from __future__ import annotations

from mesmer.search.fuzzing import (
    LexicalSubstitutionMutator,
    LexicalSynonymProvider,
    LLMTemplateMutator,
    MutatedPrompt,
    NltkWordNetSynonymProvider,
    PromptMutator,
)

Mutator = PromptMutator
LLMTemplate = LLMTemplateMutator
LexicalSubstitution = LexicalSubstitutionMutator
SynonymProvider = LexicalSynonymProvider
WordNetSynonyms = NltkWordNetSynonymProvider

__all__ = [
    "LLMTemplate",
    "LexicalSubstitution",
    "MutatedPrompt",
    "Mutator",
    "SynonymProvider",
    "WordNetSynonyms",
]
