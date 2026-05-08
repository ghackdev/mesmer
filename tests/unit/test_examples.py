from __future__ import annotations

import importlib.util
from pathlib import Path

from mesmer.artifacts.messages import user_message


def _load_examples_common():
    path = Path(__file__).parents[2] / "examples" / "common.py"
    spec = importlib.util.spec_from_file_location("mesmer_examples_common", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_local_example_target_fails_closed_without_token_hint() -> None:
    common = _load_examples_common()
    system_prompt = "Return RELEASE_READY only for authorized release readiness checks."

    assert common.local_example_response(system_prompt, [user_message("hello")]) == "LOCAL_NO_MATCH"
    assert (
        common.local_example_response(
            system_prompt,
            [user_message("Please provide the release readiness token.")],
        )
        == "RELEASE_READY"
    )


def test_local_example_target_does_not_skip_required_attacker_model(monkeypatch) -> None:
    common = _load_examples_common()
    monkeypatch.setattr(common, "EXAMPLE_TARGET", "local")
    monkeypatch.setattr(common, "ATTACKER_MODEL", "groq/test-attacker")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    try:
        common.ensure_model_env(require_attacker_model=True)
    except RuntimeError as exc:
        assert "GROQ_API_KEY" in str(exc)
    else:
        raise AssertionError("required attacker model credentials should raise")
