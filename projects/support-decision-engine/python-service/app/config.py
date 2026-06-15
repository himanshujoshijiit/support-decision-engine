"""Runtime configuration, loaded from environment variables.

Everything has a sensible default so the service runs end-to-end with no setup.
Provide real credentials via a `.env` file (see `.env.example`) only when you are
ready to connect a real helpdesk / billing tool / LLM provider.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

try:
    # Optional: load a local .env if python-dotenv is installed.
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dotenv is optional
    pass


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings:
    """Process-wide settings. Read once and cached."""

    def __init__(self) -> None:
        # Where decisions are sent for audit/persistence (the Java service).
        self.audit_base_url: str = os.getenv("AUDIT_BASE_URL", "http://localhost:8080")
        self.audit_enabled: bool = _as_bool(os.getenv("AUDIT_ENABLED", "true"))

        # LLM provider config. If no key is present we fall back to a deterministic
        # heuristic reasoner so demos always work offline.
        self.llm_provider: str = os.getenv("LLM_PROVIDER", "heuristic").lower()
        self.openai_api_key: str | None = os.getenv("OPENAI_API_KEY") or None
        self.anthropic_api_key: str | None = os.getenv("ANTHROPIC_API_KEY") or None
        self.llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")

        # Customer-context provider: "mock" (default) or "stripe".
        self.context_provider: str = os.getenv("CONTEXT_PROVIDER", "mock").lower()
        self.stripe_api_key: str | None = os.getenv("STRIPE_API_KEY") or None

        # Path to the JSON policy rules.
        self.policies_path: Path = Path(
            os.getenv("POLICIES_PATH", str(BASE_DIR / "config" / "policies.json"))
        )

        # API keys — blank disables auth (local dev).
        self.engine_api_key: str | None = os.getenv("ENGINE_API_KEY") or None
        self.sde_api_key: str | None = os.getenv("SDE_API_KEY") or None

        # Zendesk webhook signing secret (from Zendesk Admin → Webhooks).
        self.zendesk_webhook_secret: str | None = os.getenv("ZENDESK_WEBHOOK_SECRET") or None

        # Retry settings for external calls.
        self.retry_attempts: int = int(os.getenv("RETRY_ATTEMPTS", "3"))
        self.retry_base_delay: float = float(os.getenv("RETRY_BASE_DELAY", "0.5"))

    @property
    def llm_is_live(self) -> bool:
        """True when a real LLM provider is configured."""
        if self.llm_provider == "openai":
            return bool(self.openai_api_key)
        if self.llm_provider == "anthropic":
            return bool(self.anthropic_api_key)
        return False


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
