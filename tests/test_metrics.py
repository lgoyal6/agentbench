"""Unit tests for scorers, cost tracker, latency tracker, composite metrics."""

from __future__ import annotations

import pytest

from agentbench.metrics.accuracy import ExactMatchScorer, LLMJudgeScorer
from agentbench.metrics.composite import cost_adjusted_accuracy, efficiency_score
from agentbench.metrics.cost import CostTracker
from agentbench.metrics.latency import LatencyTracker, _percentile


def test_exact_match_basic() -> None:
    scorer = ExactMatchScorer()
    assert scorer.score("Paris", "paris") == 1.0
    assert scorer.score("the capital is Paris", "Paris") == 1.0
    assert scorer.score("London", "Paris") == 0.0


def test_exact_match_numeric_fallback() -> None:
    scorer = ExactMatchScorer()
    assert scorer.score("The answer is 42.", "42") == 1.0
    assert scorer.score("after thinking, I get 3.14159", "3.14159") == 1.0
    assert scorer.score("no number here", "42") == 0.0


def test_exact_match_returns_zero_on_empty_reference() -> None:
    scorer = ExactMatchScorer()
    assert scorer.score("anything", "") == 0.0


def test_llm_judge_parses_json(mocker) -> None:
    scorer = LLMJudgeScorer(model="mock-model")
    fake_response = {
        "choices": [{"message": {"content": '{"score": 0.8, "reasoning": "close enough"}'}}]
    }
    mocker.patch("litellm.completion", return_value=fake_response)
    assert scorer.score("a", "b") == 0.8
    assert scorer.last_reasoning == "close enough"


def test_llm_judge_handles_garbage_response(mocker) -> None:
    scorer = LLMJudgeScorer(model="mock-model")
    fake_response = {"choices": [{"message": {"content": "not json at all"}}]}
    mocker.patch("litellm.completion", return_value=fake_response)
    assert scorer.score("a", "b") == 0.0


def test_llm_judge_extracts_fenced_json(mocker) -> None:
    scorer = LLMJudgeScorer(model="mock-model")
    fake_response = {
        "choices": [
            {
                "message": {
                    "content": 'Here you go:\n```\n{"score": 0.6, "reasoning": "ok"}\n```'
                }
            }
        ]
    }
    mocker.patch("litellm.completion", return_value=fake_response)
    assert scorer.score("a", "b") == 0.6


def test_cost_tracker_totals() -> None:
    tracker = CostTracker()
    tracker.add_run(0.01, correct=True)
    tracker.add_run(0.02, correct=False)
    tracker.add_run(0.03, correct=True)
    assert tracker.total_cost_usd == pytest.approx(0.06)
    assert tracker.avg_cost_per_run == pytest.approx(0.02)
    # 0.06 / 2 correct
    assert tracker.cost_per_correct_answer == pytest.approx(0.03)


def test_cost_tracker_no_correct_answers() -> None:
    tracker = CostTracker()
    tracker.add_run(0.01, correct=False)
    assert tracker.cost_per_correct_answer == float("inf")


def test_cost_tracker_per_node() -> None:
    tracker = CostTracker()
    tracker.add_node("retriever", 0.001)
    tracker.add_node("synthesizer", 0.004)
    tracker.add_node("retriever", 0.002)
    by_node = tracker.per_node()
    assert by_node["retriever"] == pytest.approx(0.003)
    assert by_node["synthesizer"] == pytest.approx(0.004)


def test_latency_percentiles() -> None:
    tracker = LatencyTracker()
    for v in [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
        tracker.add(v)
    p50, p95, p99 = tracker.percentiles()
    assert 50 <= p50 <= 60
    assert p95 > p50
    assert p99 >= p95


def test_percentile_helper() -> None:
    assert _percentile([], 0.5) == 0.0
    assert _percentile([42.0], 0.99) == 42.0


def test_cost_adjusted_accuracy() -> None:
    # 0.8 accuracy at $0.01 total -> 0.8 / (1 cent + eps) ~ 0.8
    value = cost_adjusted_accuracy(0.8, 0.01)
    assert 0.79 < value < 0.81


def test_efficiency_score_zero_latency() -> None:
    assert efficiency_score(1.0, 0) == 0.0


def test_efficiency_score_decreases_with_latency() -> None:
    fast = efficiency_score(1.0, 100)
    slow = efficiency_score(1.0, 10000)
    assert fast > slow > 0
