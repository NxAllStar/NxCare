"""The single settings module - the one place environment configuration is read and validated.

Every environment read goes through here, not scattered `os.environ` lookups across the code
(.claude/rules/code-quality.md "scattered config reads"). Values come from the process environment
and, for local development, from a `.env` file (copied from `.env.example`); in a deployed
environment they come from the platform's secret store. Secrets (`llm_api_key`) are never logged or
echoed (security-privacy.md); the key is kept out of log lines rather than relying on repr masking.

The variable contract matches `.env.example`:
- `LLM_API_KEY`         - spend authority for the hosted model provider.
- `LLM_API_BASE_URL`    - OpenAI-compatible base URL of the provider used for Journey chat.
- `LLM_CHAT_MODEL`      - model name for Journey chat; defaults to `nx-chat`.

Note: `.env.example` also defines `QWEN_BASE_URL`. Journey chat deliberately uses `LLM_API_BASE_URL`
(the hosted provider), not the Qwen endpoint - a decision recorded in the TASK-009 log and flagged
against tech-stack.md/ADR-001 for an owner-approved update.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_CHAT_MODEL = "nx-chat"


class Settings(BaseSettings):
    """Application settings, read from the environment and an optional local `.env`.

    Unknown environment variables are ignored (the file carries Redis, simulator, and frontend
    keys this module does not need). Field names map case-insensitively to the env var names.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    llm_api_key: str = ""
    llm_api_base_url: str = ""
    llm_chat_model: str = DEFAULT_CHAT_MODEL

    @property
    def chat_configured(self) -> bool:
        """True when both the provider URL and a key are present, so a real client can be built.

        When False, the caller falls back to the deterministic rule-based reasoner rather than
        failing - mirroring the forecast tool's baseline fallback (FR-07).
        """
        return bool(self.llm_api_base_url and self.llm_api_key)


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings singleton (constructed once, cached)."""
    return Settings()
