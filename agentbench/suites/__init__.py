"""Built-in eval suites."""

from agentbench.exceptions import SuiteLoadError
from agentbench.suites.base import EvalSuite, EvalTask
from agentbench.suites.math_reasoning import math_reasoning_suite
from agentbench.suites.multihop_qa import multihop_qa_suite
from agentbench.suites.summarization import summarization_suite
from agentbench.suites.tool_use import tool_use_suite

_SUITE_REGISTRY: dict[str, EvalSuite] = {
    math_reasoning_suite.name: math_reasoning_suite,
    tool_use_suite.name: tool_use_suite,
    summarization_suite.name: summarization_suite,
    multihop_qa_suite.name: multihop_qa_suite,
}


def get_suite(name: str) -> EvalSuite:
    """Look up a built-in suite by name."""
    if name not in _SUITE_REGISTRY:
        available = ", ".join(sorted(_SUITE_REGISTRY))
        raise SuiteLoadError(f"Unknown suite '{name}'. Available: {available}")
    return _SUITE_REGISTRY[name]


def list_suites() -> list[EvalSuite]:
    """All registered suites."""
    return list(_SUITE_REGISTRY.values())


def register_suite(suite: EvalSuite) -> None:
    """Register a custom suite by name. Useful for third-party packages."""
    _SUITE_REGISTRY[suite.name] = suite


__all__ = [
    "EvalSuite",
    "EvalTask",
    "get_suite",
    "list_suites",
    "register_suite",
    "math_reasoning_suite",
    "tool_use_suite",
    "summarization_suite",
    "multihop_qa_suite",
]
