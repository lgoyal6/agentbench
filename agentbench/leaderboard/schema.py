"""Leaderboard data model."""

from __future__ import annotations

import time

from pydantic import BaseModel, ConfigDict, Field

from agentbench.runner import EvalReport


class ScoreBreakdown(BaseModel):
    """Scalar metrics tracked per leaderboard entry."""

    model_config = ConfigDict(extra="forbid")

    accuracy: float
    total_cost_usd: float
    avg_cost_per_run: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    cost_adjusted_accuracy: float
    efficiency_score: float


class LeaderboardEntry(BaseModel):
    """One leaderboard row."""

    model_config = ConfigDict(extra="forbid")

    agent_name: str
    author: str
    suite_name: str
    suite_version: str
    model_used: str
    score: ScoreBreakdown
    agentbench_version: str
    timestamp: float = Field(default_factory=time.time)
    n_tasks: int
    notes: str | None = None

    @classmethod
    def from_report(
        cls,
        report: EvalReport,
        *,
        agent_name: str,
        author: str,
        model_used: str,
        agentbench_version: str,
        notes: str | None = None,
    ) -> "LeaderboardEntry":
        return cls(
            agent_name=agent_name,
            author=author,
            suite_name=report.suite_name,
            suite_version=report.suite_version,
            model_used=model_used,
            score=ScoreBreakdown(
                accuracy=report.accuracy,
                total_cost_usd=report.total_cost_usd,
                avg_cost_per_run=report.avg_cost_per_run,
                p50_latency_ms=report.p50_latency_ms,
                p95_latency_ms=report.p95_latency_ms,
                p99_latency_ms=report.p99_latency_ms,
                cost_adjusted_accuracy=report.cost_adjusted_accuracy,
                efficiency_score=report.efficiency_score,
            ),
            agentbench_version=agentbench_version,
            n_tasks=report.n_tasks,
            notes=notes,
        )
