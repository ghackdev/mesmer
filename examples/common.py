from __future__ import annotations

import os

from mesmer import LiteLLMTarget

DEFAULT_GROQ_MODEL = "groq/llama-3.3-70b-versatile"

ATTACKER_MODEL = os.getenv("MESMER_ATTACKER_MODEL", DEFAULT_GROQ_MODEL)
TARGET_MODEL = os.getenv("MESMER_TARGET_MODEL", DEFAULT_GROQ_MODEL)
JUDGE_MODEL = os.getenv("MESMER_JUDGE_MODEL", DEFAULT_GROQ_MODEL)
VERBOSE = os.getenv("MESMER_VERBOSE", "true").lower() not in {"0", "false", "no"}
LOG_FORMAT = os.getenv("MESMER_LOG_FORMAT", "rich")


def ensure_model_env() -> None:
    uses_groq = any(
        model.startswith("groq/") for model in (ATTACKER_MODEL, TARGET_MODEL, JUDGE_MODEL)
    )
    if uses_groq and not os.getenv("GROQ_API_KEY"):
        raise RuntimeError(
            "Set GROQ_API_KEY, or override MESMER_ATTACKER_MODEL and MESMER_TARGET_MODEL "
            "with models for another configured provider."
        )


def model_target(system_prompt: str, *, temperature: float = 0) -> LiteLLMTarget:
    return LiteLLMTarget(
        name="model",
        model=TARGET_MODEL,
        system_prompt=system_prompt,
        generation_params={"temperature": temperature},
    )


def print_attempts(result) -> None:
    print(f"succeeded={result.succeeded} attempts={result.attempts_count}")
    for state in result.states:
        for attempt in state.attempts:
            response = attempt.response.text.replace("\n", " ")[:180]
            print(
                f"turn={attempt.turn} "
                f"score={attempt.judgements[0].score:.1f} "
                f"response={response}"
            )
