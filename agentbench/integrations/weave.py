"""W&B Weave tracker.

Implements :class:`~agentbench.runner.TrackerProtocol` against ``weave``. If
``weave`` is not installed, the tracker raises ``ImportError`` at construction.
"""

from __future__ import annotations

from typing import Any

from agentbench.agent import AgentResult
from agentbench.suites.base import EvalTask


class WeaveTracker:
    """Log AgentBench runs to Weights & Biases Weave."""

    def __init__(self, *, project: str) -> None:
        try:
            import weave
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "weave is required for WeaveTracker; install with `pip install agentbench[weave]`."
            ) from exc
        self._weave = weave
        self._weave.init(project)
        self.project = project
        self._calls: dict[str, Any] = {}

    def on_run_start(self, run_id: str, config: dict[str, Any]) -> None:
        self._calls[run_id] = self._weave.publish(
            {"event": "run_start", "config": config}, name=f"agentbench/{run_id}"
        )

    def on_task_complete(
        self,
        run_id: str,
        task: EvalTask,
        result: AgentResult,
        score: float,
    ) -> None:
        self._weave.publish(
            {
                "event": "task_complete",
                "run_id": run_id,
                "task_id": task.id,
                "score": score,
                "cost_usd": result.total_cost_usd,
                "latency_ms": result.total_latency_ms,
                "tokens": result.total_tokens,
            },
            name=f"agentbench/{run_id}/{task.id}",
        )

    def on_run_complete(self, run_id: str, report: Any) -> None:
        self._weave.publish(
            {"event": "run_complete", "report": report.model_dump()},
            name=f"agentbench/{run_id}/final",
        )
