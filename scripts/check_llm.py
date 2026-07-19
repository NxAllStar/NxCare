#!/usr/bin/env python
"""Check the configured LLM provider connection using the key/base_url/model from .env.

Run it to verify the hosted provider actually answers before relying on the arrival agent:

    uv run python scripts/check_llm.py
    # or: PYTHONPATH=src python scripts/check_llm.py

It reads settings via `vaic.config.get_settings()` (LLM_API_KEY, LLM_API_BASE_URL, LLM_CHAT_MODEL),
sends one tiny chat completion, and prints OK/FAIL. The API key itself is never printed. This is a
manual connectivity check, not a test - the test suite never touches the network (testing.md).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running straight from the repo root without installing the package.
_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from vaic.config import get_settings  # noqa: E402


def main() -> int:
    settings = get_settings()
    print(f"base_url : {settings.llm_api_base_url or '(unset)'}")
    print(f"model    : {settings.llm_chat_model}")
    print(f"api_key  : {'present' if settings.llm_api_key else 'MISSING'}")

    if not settings.chat_configured:
        print("RESULT   : NOT CONFIGURED - set LLM_API_KEY and LLM_API_BASE_URL in .env")
        return 2

    from openai import OpenAI, OpenAIError

    client = OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_api_base_url)
    try:
        response = client.chat.completions.create(
            model=settings.llm_chat_model,
            messages=[{"role": "user", "content": "Reply with the single word: pong"}],
            temperature=0,
            max_tokens=10,
        )
    except OpenAIError as exc:
        print(f"RESULT   : FAIL - provider call failed: {exc}")
        return 1

    reply = (response.choices[0].message.content or "").strip()
    print(f"reply    : {reply!r}")
    print("RESULT   : OK" if reply else "RESULT   : FAIL - empty reply")
    return 0 if reply else 1


if __name__ == "__main__":
    raise SystemExit(main())
