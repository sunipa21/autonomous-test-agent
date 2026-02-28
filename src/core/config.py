"""
Configuration loader for autonomous-test-agent.

All settings are read from environment variables (loaded via .env).
Call `Config.load()` explicitly at application startup.
"""
from __future__ import annotations

import os
from dotenv import load_dotenv


class Config:
    """Centralised application configuration."""

    # ── LLM Provider ──────────────────────────────────────────────────────────
    PROVIDER: str = "gemini"

    # ── Model names (overridable via env) ─────────────────────────────────────
    GEMINI_MODEL: str = "gemini-2.0-flash"
    OPENAI_MODEL: str = "gpt-4o"
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20240620"

    # ── Custom / Local LLM ────────────────────────────────────────────────────
    CUSTOM_BASE_URL: str = "http://localhost:11434/v1"
    CUSTOM_API_KEY: str = "sk-dummy"
    CUSTOM_MODEL_NAME: str = "llama3"

    @classmethod
    def load(cls) -> None:
        """Load environment variables from .env and populate class attributes."""
        load_dotenv()

        cls.PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()

        # Model names — allow override from env
        cls.GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        cls.OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
        cls.ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20240620")

        # Custom LLM
        cls.CUSTOM_BASE_URL = os.getenv("CUSTOM_BASE_URL", "http://localhost:11434/v1")
        cls.CUSTOM_API_KEY = os.getenv("CUSTOM_API_KEY", "sk-dummy")
        cls.CUSTOM_MODEL_NAME = os.getenv("CUSTOM_MODEL_NAME", "llama3")

    @staticmethod
    def get_api_key(provider: str) -> str | None:
        """Return the API key for the given provider."""
        keys: dict[str, str | None] = {
            "gemini": os.getenv("GOOGLE_API_KEY"),
            "openai": os.getenv("OPENAI_API_KEY"),
            "anthropic": os.getenv("ANTHROPIC_API_KEY"),
        }
        return keys.get(provider)


# Load config immediately on import so existing code that reads Config.PROVIDER etc.
# at module level continues to work without any changes.
Config.load()
