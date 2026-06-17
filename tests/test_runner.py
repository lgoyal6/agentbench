"""End-to-end tests for the eval runner."""

from __future__ import annotations

from agentbench.runner import EvalRunner, RunConfig


def test_runner_perfect_agent(perfect_agent, tiny_suite) -> None:
    report = EvalRunner(perfect_agent, tiny_suite, RunConfig(concurrency=2)).run()
    assert report.accuracy == 1.0
    assert report.n_correct == 3
    assert report.n_tasks == 3
    assert report.total_cost_usd > 0
    assert report.cost_adjusted_accuracy > 0


def test_runner_partial_correct(half_right_agent, tiny_suite) -> None:
    report = EvalRunner(half_right_agent, tiny_suite).run()
    assert report.n_correct == 2
    assert abs(report.accuracy - (2 / 3)) < 1e-9
    assert report.cost_per_correct_answer > 0


def test_runner_max_tasks(perfect_agent, tiny_suite) -> None:
    config = RunConfig(max_tasks=2)
    report = EvalRunner(perfect_agent, tiny_suite, config).run()
    assert report.n_tasks == 2


def test_runner_invokes_tracker(perfect_agent, tiny_suite) -> None:
    calls: list[str] = []

    class FakeTracker:
        def on_run_start(self, run_id, config):
            calls.append("start")

        def on_task_complete(self, run_id, task, result, score):
            calls.append(f"task:{task.id}")

        def on_run_complete(self, run_id, report):
            calls.append("complete")

    EvalRunner(perfect_agent, tiny_suite, tracker=FakeTracker()).run()
    assert calls[0] == "start"
    assert calls[-1] == "complete"
    assert {"task:t1", "task:t2", "task:t3"} <= set(calls)


def test_runner_handles_agent_errors(tiny_suite) -> None:
    class BoomAgent:
        name = "boom"

        def invoke(self, input):  # noqa: A002
            raise RuntimeError("kaboom")

    report = EvalRunner(BoomAgent(), tiny_suite, RunConfig(fail_fast=False)).run()
    assert report.n_errors == 3
    assert report.accuracy == 0.0
    assert all(o.error and "kaboom" in o.error for o in report.outcomes)
