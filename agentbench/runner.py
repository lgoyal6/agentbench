"""Core eval orchestration.

The runner is intentionally tracking-backend-agnostic. It accepts an optional
:class:`TrackerProtocol` and calls it if present. The same code path runs whether
you're logging to Weave, MLflow, or nothing at all.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from agentbench.agent import AgentProtocol, AgentResult
from agentbench.exceptions import AgentInvocationError
from agentbench.metrics.accuracy import (
    ExactMatchScorer,
    LLMJudgeScorer,
    Scorer,
    SemanticSimilarityScorer,
)
from agentbench.metrics.composite import cost_adjusted_accuracy, efficiency_score
from agentbench.metrics.cost import CostTracker
from agentbench.metrics.latency import LatencyTracker
from agentbench.suites.base import EvalSuite, EvalTask


@runtime_checkable
class TrackerProtocol(Protocol):
    """Optional experiment-tracking hook."""

    def on_run_start(self, run_id: str, config: dict[str, Any]) -> None: ...
    def on_task_complete(
        self,
        run_id: str,
        task: EvalTask,
        result: AgentResult,
        score: float,
    ) -> None: ...
    def on_run_complete(self, run_id: str, report: EvalReport) -> None: ...


class RunConfig(BaseModel):
    """Configuration for a single eval run."""

    model_config = ConfigDict(extra="forbid")

    concurrency: int = Field(default=4, ge=1, le=64)
    max_tasks: int | None = Field(default=None, ge=1)
    judge_model: str = Field(default="gpt-4o-mini")
    fail_fast: bool = Field(default=False)
    include_messages: bool = Field(default=False)
    seed: int | None = Field(default=None)


class TaskOutcome(BaseModel):
    """Per-task evaluation outcome."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    task_id: str
    score: float
    correct: bool
    cost_usd: float
    latency_ms: float
    total_tokens: int
    prediction: str
    expected: str
    error: str | None = None


class EvalReport(BaseModel):
    """The final, serializable result of an eval run."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    run_id: str
    suite_name: str
    suite_version: str
    agent_name: str
    config: RunConfig

    accuracy: float
    total_cost_usd: float
    avg_cost_per_run: float
    cost_per_correct_answer: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    cost_adjusted_accuracy: float
    efficiency_score: float

    n_tasks: int
    n_correct: int
    n_errors: int

    outcomes: list[TaskOutcome] = Field(default_factory=list)

    started_at: float
    finished_at: float

    @property
    def wall_time_s(self) -> float:
        return self.finished_at - self.started_at


def _scorer_for(scorer_type: str, judge_model: str) -> Scorer:
    if scorer_type == "exact":
        return ExactMatchScorer()
    if scorer_type == "semantic":
        return SemanticSimilarityScorer()
    if scorer_type == "llm_judge":
        return LLMJudgeScorer(model=judge_model)
    raise ValueError(f"Unknown scorer_type: {scorer_type}")


class EvalRunner:
    """Run an agent against an eval suite and collect metrics.

    The runner is synchronous on the outside but uses asyncio + a thread pool for
    parallel agent invocations. Most LangGraph agents are blocking, so a thread
    pool gives us real parallelism without forcing users to write async code.
    """

    def __init__(
        self,
        agent: AgentProtocol,
        suite: EvalSuite,
        config: RunConfig | None = None,
        tracker: TrackerProtocol | None = None,
        *,
        agent_name: str | None = None,
    ) -> None:
        self.agent = agent
        self.suite = suite
        self.config = config or RunConfig()
        self.tracker = tracker
        self.agent_name: str = agent_name or str(
            getattr(agent, "name", None) or agent.__class__.__name__
        )
        self._scorer_cache: dict[str, Scorer] = {}

    def _get_scorer(self, scorer_type: str) -> Scorer:
        if scorer_type not in self._scorer_cache:
            self._scorer_cache[scorer_type] = _scorer_for(scorer_type, self.config.judge_model)
        return self._scorer_cache[scorer_type]

    def run(self) -> EvalReport:
        """Execute the run synchronously and return a finalized report."""
        return asyncio.run(self.arun())

    async def arun(self) -> EvalReport:
        """Async entrypoint. Most users should call :meth:`run` instead."""
        run_id = str(uuid.uuid4())
        started_at = time.time()

        if self.tracker is not None:
            self.tracker.on_run_start(run_id, self.config.model_dump())

        tasks = list(self.suite.tasks)
        if self.config.max_tasks is not None:
            tasks = tasks[: self.config.max_tasks]

        sem = asyncio.Semaphore(self.config.concurrency)
        executor = ThreadPoolExecutor(max_workers=self.config.concurrency)
        loop = asyncio.get_running_loop()

        async def _run_one(task: EvalTask) -> TaskOutcome:
            async with sem:
                return await loop.run_in_executor(executor, self._run_task_sync, run_id, task)

        try:
            outcomes = await asyncio.gather(
                *(_run_one(t) for t in tasks),
                return_exceptions=False,
            )
        finally:
            executor.shutdown(wait=False)

        cost_tracker = CostTracker()
        latency_tracker = LatencyTracker()
        n_correct = 0
        n_errors = 0
        for outcome in outcomes:
            cost_tracker.add_run(outcome.cost_usd, correct=outcome.correct)
            latency_tracker.add(outcome.latency_ms)
            if outcome.correct:
                n_correct += 1
            if outcome.error is not None:
                n_errors += 1

        accuracy = n_correct / len(outcomes) if outcomes else 0.0
        finished_at = time.time()
        p50, p95, p99 = latency_tracker.percentiles()

        report = EvalReport(
            run_id=run_id,
            suite_name=self.suite.name,
            suite_version=self.suite.version,
            agent_name=self.agent_name,
            config=self.config,
            accuracy=accuracy,
            total_cost_usd=cost_tracker.total_cost_usd,
            avg_cost_per_run=cost_tracker.avg_cost_per_run,
            cost_per_correct_answer=cost_tracker.cost_per_correct_answer,
            p50_latency_ms=p50,
            p95_latency_ms=p95,
            p99_latency_ms=p99,
            cost_adjusted_accuracy=cost_adjusted_accuracy(accuracy, cost_tracker.total_cost_usd),
            efficiency_score=efficiency_score(accuracy, latency_tracker.mean_latency_ms),
            n_tasks=len(outcomes),
            n_correct=n_correct,
            n_errors=n_errors,
            outcomes=outcomes,
            started_at=started_at,
            finished_at=finished_at,
        )

        if self.tracker is not None:
            self.tracker.on_run_complete(run_id, report)

        return report

    def _run_task_sync(self, run_id: str, task: EvalTask) -> TaskOutcome:
        scorer = self._get_scorer(task.scorer_type)
        start = time.perf_counter()
        try:
            result = self.agent.invoke(task.input)
        except Exception as exc:
            if self.config.fail_fast:
                raise AgentInvocationError(task.id, str(exc), cause=exc) from exc
            latency_ms = (time.perf_counter() - start) * 1000.0
            outcome = TaskOutcome(
                task_id=task.id,
                score=0.0,
                correct=False,
                cost_usd=0.0,
                latency_ms=latency_ms,
                total_tokens=0,
                prediction="",
                expected=str(task.expected_output),
                error=f"{type(exc).__name__}: {exc}",
            )
            if self.tracker is not None:
                # Build a minimal AgentResult so trackers see a uniform shape.
                self.tracker.on_task_complete(
                    run_id,
                    task,
                    AgentResult(final_answer="", error=outcome.error),
                    0.0,
                )
            return outcome

        score = scorer.score(result.final_answer, str(task.expected_output))
        correct = score >= 0.5
        outcome = TaskOutcome(
            task_id=task.id,
            score=score,
            correct=correct,
            cost_usd=result.total_cost_usd,
            latency_ms=result.total_latency_ms or ((time.perf_counter() - start) * 1000.0),
            total_tokens=result.total_tokens,
            prediction=result.final_answer,
            expected=str(task.expected_output),
        )
        if self.tracker is not None:
            self.tracker.on_task_complete(run_id, task, result, score)
        return outcome
