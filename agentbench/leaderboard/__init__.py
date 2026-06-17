"""Leaderboard backends (local JSON-backed by default)."""

from __future__ import annotations

from agentbench.config import get_settings
from agentbench.leaderboard.local import LocalLeaderboard
from agentbench.leaderboard.schema import LeaderboardEntry, ScoreBreakdown


def get_leaderboard() -> LocalLeaderboard:
    """Return the configured leaderboard backend."""
    settings = get_settings()
    if settings.leaderboard_backend == "supabase":
        from agentbench.leaderboard.supabase import SupabaseLeaderboard

        return SupabaseLeaderboard(url=settings.supabase_url, key=settings.supabase_key)  # type: ignore[return-value]
    return LocalLeaderboard()


__all__ = [
    "LeaderboardEntry",
    "ScoreBreakdown",
    "LocalLeaderboard",
    "get_leaderboard",
]
