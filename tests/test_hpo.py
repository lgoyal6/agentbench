"""Tests for HPO config and reporter (mock-only; we don't spin up Ray)."""

from __future__ import annotations

import pytest

from agentbench.exceptions import HPOError
from agentbench.hpo.reporter import HPOResult
from agentbench.hpo.runner import HPOConfig, HPORunner
from agentbench.hpo.search_space import SYSTEM_PROMPTS, get_system_prompt


def test_hpo_config_default_metric() -> None:
    cfg = HPOConfig()
    assert cfg.metric == "cost_adjusted_accuracy"
    assert cfg.mode == "max"


def test_hpo_runner_rejects_unknown_metric() -> None:
    def factory(config):
        raise NotImplementedError

    with pytest.raises(HPOError):
        HPORunner(
            trainable_factory=factory,
            suite=None,  # type: ignore[arg-type]
            search_space={},
            config=HPOConfig(metric="not_a_metric"),
        )


def test_hpo_result_top_returns_sorted() -> None:
    result = HPOResult(
        best_config={"a": 1},
        best_metric=0.9,
        metric_name="cost_adjusted_accuracy",
        n_trials=3,
        n_completed=3,
        trials=[
            {"trial_id": "1", "cost_adjusted_accuracy": 0.7},
            {"trial_id": "2", "cost_adjusted_accuracy": 0.9},
            {"trial_id": "3", "cost_adjusted_accuracy": 0.8},
        ],
    )
    top = result.top(2)
    assert [t["trial_id"] for t in top] == ["2", "3"]


def test_system_prompts_cover_all_styles() -> None:
    expected = {"concise", "verbose", "chain_of_thought", "role_play"}
    assert expected <= set(SYSTEM_PROMPTS)


def test_get_system_prompt_unknown_falls_back() -> None:
    assert get_system_prompt("never_heard_of_it") == SYSTEM_PROMPTS["concise"]
