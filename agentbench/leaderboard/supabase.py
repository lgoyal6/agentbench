"""Optional Supabase-backed leaderboard.

Enabled via ``AGENTBENCH_LEADERBOARD_BACKEND=supabase``. Expects two env vars:
``AGENTBENCH_SUPABASE_URL`` and ``AGENTBENCH_SUPABASE_KEY``.

Table schema (run as a Supabase migration):

.. code-block:: sql

    create table public.agentbench_leaderboard (
        id uuid primary key default gen_random_uuid(),
        agent_name text not null,
        author text not null,
        suite_name text not null,
        suite_version text not null,
        model_used text not null,
        score jsonb not null,
        agentbench_version text not null,
        timestamp double precision not null,
        n_tasks int not null,
        notes text
    );
"""

from __future__ import annotations

from typing import Any

from agentbench.exceptions import LeaderboardError
from agentbench.leaderboard.schema import LeaderboardEntry, ScoreBreakdown


class SupabaseLeaderboard:
    """Supabase-backed leaderboard."""

    TABLE = "agentbench_leaderboard"
    DEFAULT_METRIC = "cost_adjusted_accuracy"

    def __init__(self, *, url: str | None, key: str | None) -> None:
        if not url or not key:
            raise LeaderboardError(
                "Supabase leaderboard requires AGENTBENCH_SUPABASE_URL and AGENTBENCH_SUPABASE_KEY."
            )
        try:
            from supabase import create_client
        except ImportError as exc:  # pragma: no cover
            raise LeaderboardError(
                "supabase-py not installed; install with `pip install agentbench[supabase]`."
            ) from exc
        self._client = create_client(url, key)

    def submit(self, entry: LeaderboardEntry) -> LeaderboardEntry:
        payload = entry.model_dump()
        try:
            self._client.table(self.TABLE).insert(payload).execute()
        except Exception as exc:  # pragma: no cover
            raise LeaderboardError(f"Supabase insert failed: {exc}") from exc
        return entry

    def list(
        self,
        *,
        suite: str | None = None,
        top: int | None = None,
        metric: str = DEFAULT_METRIC,
    ) -> list[LeaderboardEntry]:
        query = self._client.table(self.TABLE).select("*")
        if suite is not None:
            query = query.eq("suite_name", suite)
        try:
            response = query.execute()
        except Exception as exc:  # pragma: no cover
            raise LeaderboardError(f"Supabase query failed: {exc}") from exc
        rows: list[dict[str, Any]] = response.data or []
        entries: list[LeaderboardEntry] = []
        for row in rows:
            score_data = row.get("score") or {}
            entries.append(
                LeaderboardEntry(
                    agent_name=row["agent_name"],
                    author=row["author"],
                    suite_name=row["suite_name"],
                    suite_version=row["suite_version"],
                    model_used=row["model_used"],
                    score=ScoreBreakdown.model_validate(score_data),
                    agentbench_version=row["agentbench_version"],
                    timestamp=row["timestamp"],
                    n_tasks=row["n_tasks"],
                    notes=row.get("notes"),
                )
            )
        entries.sort(key=lambda e: getattr(e.score, metric), reverse=True)
        if top is not None:
            entries = entries[:top]
        return entries

    def clear(self) -> None:  # pragma: no cover
        self._client.table(self.TABLE).delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
