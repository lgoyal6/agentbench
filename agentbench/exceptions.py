"""Typed exception hierarchy for AgentBench."""

from __future__ import annotations


class AgentBenchError(Exception):
    """Base exception for all AgentBench errors."""


class AgentInvocationError(AgentBenchError):
    """Raised when an agent fails to invoke on a task."""

    def __init__(self, task_id: str, message: str, cause: Exception | None = None) -> None:
        super().__init__(f"Agent failed on task '{task_id}': {message}")
        self.task_id = task_id
        self.cause = cause


class SuiteLoadError(AgentBenchError):
    """Raised when a suite cannot be loaded by name."""


class ScorerError(AgentBenchError):
    """Raised when a scorer fails to produce a score."""


class ConfigError(AgentBenchError):
    """Raised when configuration is invalid."""


class LeaderboardError(AgentBenchError):
    """Raised when leaderboard operations fail."""


class HPOError(AgentBenchError):
    """Raised when HPO orchestration fails."""
