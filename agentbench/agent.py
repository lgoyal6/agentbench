"""Agent protocol and wrapper for instrumenting LangGraph StateGraphs.

The framework is intentionally permissive about what an "agent" is: anything that
satisfies :class:`AgentProtocol` works. :class:`AgentWrapper` provides a turn-key
way to take a compiled LangGraph and get token-and-latency instrumentation for free.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field


class NodeUsage(BaseModel):
    """Token + latency usage attributed to a single graph node."""

    model_config = ConfigDict(extra="allow")

    node: str
    model: str | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0

    @property
    def tokens(self) -> int:
        """Total tokens consumed by this node call (alias for total_tokens)."""
        return self.total_tokens


class AgentResult(BaseModel):
    """The structured output of an agent invocation.

    Designed so that every metric in the framework can be computed from it without
    re-running the agent.
    """

    model_config = ConfigDict(extra="allow", arbitrary_types_allowed=True)

    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    final_answer: str
    node_usage: list[NodeUsage] = Field(default_factory=list)
    total_latency_ms: float = 0.0
    messages: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None

    @property
    def total_tokens(self) -> int:
        return sum(u.total_tokens for u in self.node_usage)

    @property
    def total_cost_usd(self) -> float:
        return sum(u.cost_usd for u in self.node_usage)


@runtime_checkable
class AgentProtocol(Protocol):
    """Protocol every evaluatable agent must satisfy.

    Implementations should be deterministic enough that re-invoking with the same
    input produces comparable results — but the framework does NOT require strict
    determinism (temperature > 0 is fine and explicitly supported).
    """

    def invoke(self, input: dict[str, Any]) -> AgentResult:  # noqa: A002
        """Run the agent on a single task input and return a structured result."""
        ...


class AgentWrapper:
    """Wrap a compiled LangGraph ``StateGraph`` and instrument it for evaluation.

    The wrapper intercepts node calls to capture per-node latency, and registers a
    LiteLLM callback for token+cost capture. Users who need finer control should
    subclass and override :meth:`extract_answer` and :meth:`build_input`.
    """

    def __init__(
        self,
        graph: Any,
        *,
        name: str = "agent",
        model: str | None = None,
        answer_key: str = "answer",
        input_key: str = "question",
        config: dict[str, Any] | None = None,
    ) -> None:
        self.graph = graph
        self.name = name
        self.model = model
        self.answer_key = answer_key
        self.input_key = input_key
        self.config = config or {}

    def build_input(self, task_input: dict[str, Any]) -> dict[str, Any]:
        """Translate a task input dict into the graph's expected state shape.

        Default behavior wraps the value under ``self.input_key`` if the input is a
        single-value dict; otherwise it is passed through unchanged.
        """
        if self.input_key in task_input:
            return task_input
        if len(task_input) == 1 and "input" in task_input:
            return {self.input_key: task_input["input"]}
        return task_input

    def extract_answer(self, state: Any) -> str:
        """Pull the final answer out of the graph's final state."""
        if isinstance(state, dict):
            if self.answer_key in state:
                return str(state[self.answer_key])
            for key in ("output", "final_answer", "result", "response"):
                if key in state:
                    return str(state[key])
            messages = state.get("messages")
            if messages:
                last = messages[-1]
                content = getattr(last, "content", None) or (
                    last.get("content") if isinstance(last, dict) else None
                )
                if content is not None:
                    return str(content)
        return str(state)

    def invoke(self, input: dict[str, Any]) -> AgentResult:  # noqa: A002
        """Run the underlying graph, capturing usage via LiteLLM callbacks."""
        from agentbench.integrations.litellm import usage_capture

        graph_input = self.build_input(input)
        with usage_capture() as captured:
            start = time.perf_counter()
            err: str | None = None
            final_state: Any = None
            try:
                final_state = self.graph.invoke(graph_input, config=self.config or None)
            except Exception as exc:  # pragma: no cover - re-raised wrapper below
                err = f"{type(exc).__name__}: {exc}"
                raise
            finally:
                total_ms = (time.perf_counter() - start) * 1000.0

        answer = self.extract_answer(final_state) if final_state is not None else ""
        return AgentResult(
            final_answer=answer,
            node_usage=captured.to_node_usage(),
            total_latency_ms=total_ms,
            messages=captured.messages,
            metadata={"agent_name": self.name, "model": self.model},
            error=err,
        )
