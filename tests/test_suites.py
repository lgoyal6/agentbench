"""Tests for suite registration and built-in content."""

from __future__ import annotations

import pytest

from agentbench.exceptions import SuiteLoadError
from agentbench.suites import get_suite, list_suites
from agentbench.suites.base import EvalSuite, EvalTask
from agentbench.suites.tool_use import mock_search


def test_all_builtin_suites_load() -> None:
    names = {s.name for s in list_suites()}
    assert {"math_reasoning", "tool_use", "summarization", "multihop_qa"} <= names


def test_math_reasoning_has_20_tasks() -> None:
    assert len(get_suite("math_reasoning")) == 20


def test_tool_use_has_15_tasks() -> None:
    assert len(get_suite("tool_use")) == 15


def test_summarization_has_10_tasks() -> None:
    assert len(get_suite("summarization")) == 10


def test_multihop_qa_has_10_tasks() -> None:
    assert len(get_suite("multihop_qa")) == 10


def test_unknown_suite_raises() -> None:
    with pytest.raises(SuiteLoadError):
        get_suite("nope")


def test_mock_search_known_key() -> None:
    assert "Paris" in mock_search("capital of France")


def test_mock_search_unknown() -> None:
    assert mock_search("totally bogus query xyz") == "no results found"


def test_suite_filter() -> None:
    suite = get_suite("math_reasoning")
    easy = suite.filter(difficulty="easy")
    assert all(t.difficulty == "easy" for t in easy.tasks)
    assert len(easy) > 0


def test_suite_sample_is_deterministic() -> None:
    suite = get_suite("math_reasoning")
    a = suite.sample(5, seed=0)
    b = suite.sample(5, seed=0)
    assert [t.id for t in a.tasks] == [t.id for t in b.tasks]


def test_custom_suite_construction() -> None:
    s = EvalSuite(
        name="custom",
        tasks=[
            EvalTask(
                id="x1",
                input={"q": "?"},
                expected_output="a",
            )
        ],
    )
    assert len(s) == 1
    assert s.tasks[0].id == "x1"
