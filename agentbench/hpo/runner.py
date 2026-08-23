"""HPO orchestration with Ray Tune + ASHA scheduler.

The runner is intentionally agent-shape-agnostic: callers supply a
``trainable_factory(config) -> AgentProtocol`` which produces an agent for a
given config dict. The runner handles the rest: running the eval, returning
the chosen metric back to Tune, and collecting the trial dataframe.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from agentbench.agent import AgentProtocol
from agentbench.exceptions import HPOError
from agentbench.hpo.reporter import HPOResult
from agentbench.runner import EvalReport, EvalRunner, RunConfig
from agentbench.suites.base import EvalSuite

TrainableFactory = Callable[[dict[str, Any]], AgentProtocol]

VALID_METRICS = {
    "cost_adjusted_accuracy",
    "accuracy",
    "efficiency_score",
    "p95_latency_ms",
    "total_cost_usd",
}


class HPOConfig(BaseModel):
    """Configuration for an HPO sweep."""

    model_config = ConfigDict(extra="forbid")

    metric: str = Field(default="cost_adjusted_accuracy")
    mode: Literal["max", "min"] = "max"
    num_samples: int = Field(default=50, ge=1)
    max_concurrent_trials: int = Field(default=4, ge=1)
    asha_max_t: int = Field(default=100, ge=1, description="Max budget per trial for ASHA.")
    asha_grace_period: int = Field(default=10, ge=1)
    asha_reduction_factor: int = Field(default=3, ge=2)
    eval_max_tasks: int | None = Field(default=None, ge=1)
    eval_concurrency: int = Field(default=4, ge=1)


class HPORunner:
    """Run a Ray Tune sweep over an agent factory."""

    def __init__(
        self,
        trainable_factory: TrainableFactory,
        suite: EvalSuite,
        search_space: dict[str, Any],
        *,
        config: HPOConfig | None = None,
    ) -> None:
        self.trainable_factory = trainable_factory
        self.suite = suite
        self.search_space = search_space
        self.config = config or HPOConfig()
        if self.config.metric not in VALID_METRICS:
            raise HPOError(
                f"Unknown metric '{self.config.metric}'. Valid: {sorted(VALID_METRICS)}"
            )

    def run(self) -> HPOResult:
        """Execute the sweep and return the best trial."""
        try:
            import ray
            from ray import tune
            from ray.tune.schedulers import ASHAScheduler
        except ImportError as exc:  # pragma: no cover
            raise HPOError(
                "ray[tune] is required for HPO; install with `pip install agentbench`."
            ) from exc

        cfg = self.config
        suite = self.suite
        factory = self.trainable_factory

        def _trainable(config: dict[str, Any]) -> None:
            agent = factory(config)
            run_cfg = RunConfig(
                concurrency=cfg.eval_concurrency,
                max_tasks=cfg.eval_max_tasks,
            )
            report: EvalReport = EvalRunner(agent, suite, run_cfg).run()
            value = float(getattr(report, cfg.metric))
            tune.report({cfg.metric: value, "accuracy": report.accuracy, "cost_usd": report.total_cost_usd})

        scheduler = ASHAScheduler(
            metric=cfg.metric,
            mode=cfg.mode,
            max_t=cfg.asha_max_t,
            grace_period=cfg.asha_grace_period,
            reduction_factor=cfg.asha_reduction_factor,
        )

        shutdown_after = not ray.is_initialized()
        if shutdown_after:
            ray.init(ignore_reinit_error=True, log_to_driver=False)

        try:
            analysis = tune.run(
                _trainable,
                config=self.search_space,
                num_samples=cfg.num_samples,
                scheduler=scheduler,
                max_concurrent_trials=cfg.max_concurrent_trials,
                verbose=0,
            )
        finally:
            if shutdown_after:
                ray.shutdown()

        best = analysis.get_best_trial(cfg.metric, cfg.mode, "last")
        if best is None:
            raise HPOError("No trials completed.")

        trials: list[dict[str, Any]] = []
        for t in analysis.trials:
            row = dict(t.config)
            row.update(t.last_result or {})
            row["trial_id"] = t.trial_id
            trials.append(row)

        return HPOResult(
            best_config=best.config,
            best_metric=float((best.last_result or {}).get(cfg.metric, 0.0)),
            metric_name=cfg.metric,
            n_trials=cfg.num_samples,
            n_completed=len([t for t in analysis.trials if t.last_result]),
            trials=trials,
        )
