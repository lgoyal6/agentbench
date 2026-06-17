"""MLflow tracker.

Implements :class:`~agentbench.runner.TrackerProtocol` against ``mlflow``.
"""

from __future__ import annotations

from typing import Any

from agentbench.agent import AgentResult
from agentbench.suites.base import EvalTask


class MLflowTracker:
    """Log AgentBench runs to MLflow."""

    def __init__(self, *, experiment: str = "agentbench", tracking_uri: str | None = None) -> None:
        try:
            import mlflow
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "mlflow is required for MLflowTracker; install with `pip install agentbench[mlflow]`."
            ) from exc
        self._mlflow = mlflow
        if tracking_uri is not None:
            mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment(experiment)
        self._runs: dict[str, Any] = {}

    def on_run_start(self, run_id: str, config: dict[str, Any]) -> None:
        run = self._mlflow.start_run(run_name=f"agentbench-{run_id}")
        self._runs[run_id] = run
        for k, v in config.items():
            self._mlflow.log_param(k, v)

    def on_task_complete(
        self,
        run_id: str,
        task: EvalTask,
        result: AgentResult,
        score: float,
    ) -> None:
        self._mlflow.log_metric(f"score_{task.id}", score)
        self._mlflow.log_metric(f"cost_usd_{task.id}", result.total_cost_usd)
        self._mlflow.log_metric(f"latency_ms_{task.id}", result.total_latency_ms)

    def on_run_complete(self, run_id: str, report: Any) -> None:
        for key, value in report.model_dump().items():
            if isinstance(value, (int, float)):
                self._mlflow.log_metric(key, value)
        self._mlflow.end_run()
        self._runs.pop(run_id, None)
