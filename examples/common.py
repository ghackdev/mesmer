from __future__ import annotations

import base64
import os
import re

from mesmer import LiteLLMTarget, PythonCallableTarget

DEFAULT_GROQ_MODEL = "groq/llama-3.3-70b-versatile"

ATTACKER_MODEL = os.getenv("MESMER_ATTACKER_MODEL", DEFAULT_GROQ_MODEL)
TARGET_MODEL = os.getenv("MESMER_TARGET_MODEL", DEFAULT_GROQ_MODEL)
JUDGE_MODEL = os.getenv("MESMER_JUDGE_MODEL", DEFAULT_GROQ_MODEL)
EXAMPLE_TARGET = os.getenv("MESMER_EXAMPLE_TARGET", "model").lower()
VERBOSE = os.getenv("MESMER_VERBOSE", "true").lower() not in {"0", "false", "no"}
LOG_FORMAT = os.getenv("MESMER_LOG_FORMAT", "rich")
TOKEN_PATTERN = re.compile(r"\b[A-Z][A-Z0-9_]{2,}\b")


def ensure_model_env(*, require_attacker_model: bool = False) -> None:
    models = [ATTACKER_MODEL] if require_attacker_model else []
    if EXAMPLE_TARGET != "local":
        models.extend([TARGET_MODEL, JUDGE_MODEL])
    if not models:
        return
    uses_groq = any(model.startswith("groq/") for model in models)
    if uses_groq and not os.getenv("GROQ_API_KEY"):
        raise RuntimeError(
            "Set GROQ_API_KEY, or override MESMER_ATTACKER_MODEL, MESMER_TARGET_MODEL, "
            "and MESMER_JUDGE_MODEL with models for another configured provider."
        )


def model_target(
    system_prompt: str,
    *,
    temperature: float = 0,
) -> LiteLLMTarget | PythonCallableTarget:
    if EXAMPLE_TARGET == "local":
        return PythonCallableTarget(
            name="local_example_target",
            fn=lambda messages, context: local_example_response(system_prompt, messages),
        )
    return LiteLLMTarget(
        name="model",
        model=TARGET_MODEL,
        system_prompt=system_prompt,
        generation_params={"temperature": temperature},
    )


def local_example_response(system_prompt: str, messages) -> str:
    """Deterministic target for smoke-testing examples without model credentials."""
    prompt = messages[-1].content if messages else ""
    decoded = _maybe_decode_base64(prompt)
    candidate = f"{prompt}\n{decoded}".lower()
    tokens = TOKEN_PATTERN.findall(system_prompt)
    if not tokens:
        return "LOCAL_OK"

    for token in tokens:
        hints = [part.lower() for part in token.split("_") if len(part) > 2]
        if token.lower() in candidate or any(hint in candidate for hint in hints):
            return token
    return "LOCAL_NO_MATCH"


def _maybe_decode_base64(text: str) -> str:
    value = text.strip()
    if not value or len(value) % 4:
        return ""
    try:
        return base64.b64decode(value, validate=True).decode("utf-8")
    except Exception:
        return ""


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
