"""Request/response schemas for the FastAPI app."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from agentbench.leaderboard.schema import LeaderboardEntry
from agentbench.runner import EvalReport, RunConfig

RunStatus = Literal["pending", "running", "complete", "failed"]


class RunRequest(BaseModel):
    """Body of ``POST /run``."""

    model_config = ConfigDict(extra="forbid")

    agent_path: str = Field(..., description="Dotted import path to an AgentProtocol instance.")
    suite: str
    config: RunConfig = Field(default_factory=RunConfig)
    agent_name: str | None = None


class RunCreatedResponse(BaseModel):
    run_id: str
    status: RunStatus


class RunStatusResponse(BaseModel):
    run_id: str
    status: RunStatus
    error: str | None = None
    report: EvalReport | None = None
    progress: float = 0.0


class LeaderboardResponse(BaseModel):
    suite: str | None
    entries: list[LeaderboardEntry]
