"""Runtime settings."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings:
    def __init__(self) -> None:
        self.data_provider: str = os.getenv("DATA_PROVIDER", "mock").lower()
        self.signals_path: Path = Path(
            os.getenv("SIGNALS_PATH", str(BASE_DIR / "config" / "signals.json"))
        )
        self.llm_provider: str = os.getenv("LLM_PROVIDER", "heuristic").lower()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
