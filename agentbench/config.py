"""Global configuration via pydantic-settings.

All settings can be overridden via environment variables prefixed with ``AGENTBENCH_``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentBenchSettings(BaseSettings):
    """Runtime configuration for AgentBench.

    Resolved from (highest precedence first): explicit kwargs, environment variables
    prefixed ``AGENTBENCH_``, then defaults.
    """

    model_config = SettingsConfigDict(
        env_prefix="AGENTBENCH_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Storage
    data_dir: Path = Field(
        default_factory=lambda: Path.home() / ".agentbench",
        description="Directory for local persistence (leaderboard, cached datasets).",
    )

    # LLM defaults
    default_model: str = Field(default="gpt-4o-mini", description="Default LiteLLM model id.")
    default_judge_model: str = Field(
        default="gpt-4o-mini",
        description="Default judge model for LLMJudgeScorer.",
    )

    # Execution
    max_concurrency: int = Field(default=8, ge=1, description="Default parallelism for runner.")
    request_timeout_s: float = Field(default=60.0, ge=1.0)

    # Leaderboard backend
    leaderboard_backend: Literal["local", "supabase"] = Field(default="local")
    supabase_url: str | None = Field(default=None)
    supabase_key: str | None = Field(default=None)

    # Tracking integrations
    weave_project: str | None = Field(default=None)
    mlflow_tracking_uri: str | None = Field(default=None)

    def ensure_data_dir(self) -> Path:
        """Create the data directory if it doesn't exist and return it."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return self.data_dir


_settings: AgentBenchSettings | None = None


def get_settings() -> AgentBenchSettings:
    """Return the process-wide settings singleton."""
    global _settings
    if _settings is None:
        _settings = AgentBenchSettings()
    return _settings


def reset_settings() -> None:
    """Reset the settings singleton. Useful for tests."""
    global _settings
    _settings = None
