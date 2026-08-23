"""Shared pytest fixtures."""

from __future__ import annotations

from typing import Any

import pytest

from agentbench.agent import AgentResult, NodeUsage
from agentbench.suites.base import EvalSuite, EvalTask


class CannedAgent:
    """An agent that returns a pre-configured answer per task id.

    Used throughout tests to avoid any network/LLM dependency.
    """

    def __init__(
        self,
        answers: dict[str, str],
        *,
        cost_usd: float = 0.001,
        latency_ms: float = 25.0,
        tokens: int = 100,
        name: str = "canned",
    ) -> None:
        self.answers = answers
        self.cost_usd = cost_usd
        self.latency_ms = latency_ms
        self.tokens = tokens
        self.name = name

    def invoke(self, input: dict[str, Any]) -> AgentResult:
        # The runner passes task.input which carries an "id" key only when callers
        # explicitly include one; otherwise tests can use a `task_id` field.
        task_id = input.get("task_id", "")
        answer = self.answers.get(task_id, "")
        return AgentResult(
            final_answer=answer,
            node_usage=[
                NodeUsage(
                    node="llm",
                    model="mock-model",
                    prompt_tokens=self.tokens // 2,
                    completion_tokens=self.tokens // 2,
                    total_tokens=self.tokens,
                    cost_usd=self.cost_usd,
                    latency_ms=self.latency_ms,
                )
            ],
            total_latency_ms=self.latency_ms,
        )


@pytest.fixture
def tiny_suite() -> EvalSuite:
    return EvalSuite(
        name="tiny",
        version="0.0.1",
        description="three trivial tasks",
        tasks=[
            EvalTask(
                id="t1",
                input={"task_id": "t1"},
                expected_output="alpha",
                scorer_type="exact",
            ),
            EvalTask(
                id="t2",
                input={"task_id": "t2"},
                expected_output="beta",
                scorer_type="exact",
            ),
            EvalTask(
                id="t3",
                input={"task_id": "t3"},
                expected_output="gamma",
                scorer_type="exact",
            ),
        ],
    )


@pytest.fixture
def perfect_agent() -> CannedAgent:
    return CannedAgent(answers={"t1": "alpha", "t2": "beta", "t3": "gamma"})


@pytest.fixture
def half_right_agent() -> CannedAgent:
    return CannedAgent(answers={"t1": "alpha", "t2": "wrong", "t3": "gamma"})


@pytest.fixture
def isolated_leaderboard(tmp_path, monkeypatch) -> Any:
    """Point the leaderboard at a tmp dir for the duration of one test."""
    monkeypatch.setenv("AGENTBENCH_DATA_DIR", str(tmp_path))
    from agentbench.config import reset_settings

    reset_settings()
    yield tmp_path
    reset_settings()
