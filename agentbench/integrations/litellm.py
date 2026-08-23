"""LiteLLM integration: model-agnostic LLM calls + token tracking.

Exposes two things:

* :func:`completion_with_capture` — a thin wrapper around ``litellm.completion``
  that also records a :class:`~agentbench.agent.NodeUsage` entry into the
  thread-local capture buffer.
* :func:`usage_capture` — a context manager that opens a fresh capture buffer
  and yields a :class:`CapturedUsage` accumulator. The wrapper used inside the
  context records into it.

This lets :class:`~agentbench.agent.AgentWrapper` instrument arbitrary
LangGraph graphs as long as the graph calls ``completion_with_capture`` (or any
function that ultimately calls it) from inside its node functions.
"""

from __future__ import annotations

import contextvars
import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from agentbench.agent import NodeUsage
from agentbench.metrics.cost import usage_from_litellm_response


class CapturedUsage:
    """Thread-safe accumulator of :class:`NodeUsage` entries."""

    def __init__(self) -> None:
        self.entries: list[NodeUsage] = []
        self.messages: list[dict[str, Any]] = []

    def add(self, usage: NodeUsage) -> None:
        self.entries.append(usage)

    def add_messages(self, messages: list[dict[str, Any]]) -> None:
        self.messages.extend(messages)

    def to_node_usage(self) -> list[NodeUsage]:
        return list(self.entries)

    @property
    def total_tokens(self) -> int:
        return sum(u.total_tokens for u in self.entries)

    @property
    def total_cost_usd(self) -> float:
        return sum(u.cost_usd for u in self.entries)


_current_capture: contextvars.ContextVar[CapturedUsage | None] = contextvars.ContextVar(
    "agentbench_capture", default=None
)


@contextmanager
def usage_capture() -> Iterator[CapturedUsage]:
    """Open a fresh per-invocation capture buffer.

    Re-entrant: nested uses get fresh, isolated buffers via ``contextvars``.
    """
    captured = CapturedUsage()
    token = _current_capture.set(captured)
    try:
        yield captured
    finally:
        _current_capture.reset(token)


def completion_with_capture(
    *,
    model: str,
    messages: list[dict[str, Any]],
    node: str = "llm",
    **kwargs: Any,
) -> Any:
    """Call ``litellm.completion`` and record usage into the active buffer."""
    from litellm import completion

    start = time.perf_counter()
    response = completion(model=model, messages=messages, **kwargs)
    latency_ms = (time.perf_counter() - start) * 1000.0
    captured = _current_capture.get()
    if captured is not None:
        captured.add(
            usage_from_litellm_response(response, model=model, node=node, latency_ms=latency_ms)
        )
        try:
            content = response["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            content = ""
        captured.add_messages([*messages, {"role": "assistant", "content": content}])
    return response
