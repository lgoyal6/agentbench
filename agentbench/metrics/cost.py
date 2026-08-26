"""Token cost tracking via LiteLLM's pricing tables."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from agentbench.agent import AgentResult, NodeUsage


def _safe_completion_cost(**kwargs: Any) -> float:
    """Wrap ``litellm.completion_cost`` so an unknown model doesn't raise."""
    try:
        from litellm import completion_cost

        return float(completion_cost(**kwargs))
    except Exception:
        # LiteLLM raises for unknown models / missing pricing. Treat as $0.
        return 0.0


class CostTracker:
    """Track cost across an eval run.

    The tracker computes three useful quantities:

    * :attr:`total_cost_usd` - sum of cost over every run.
    * :attr:`avg_cost_per_run` - total cost / number of runs.
    * :attr:`cost_per_correct_answer` - total cost / number correct, with a
      sentinel value (``float('inf')``) when no answers were correct.
    """

    def __init__(self) -> None:
        self._runs: list[tuple[float, bool]] = []
        self._node_totals: dict[str, float] = defaultdict(float)

    def add_run(self, cost_usd: float, *, correct: bool) -> None:
        self._runs.append((cost_usd, correct))

    def add_node(self, node: str, cost_usd: float) -> None:
        self._node_totals[node] += cost_usd

    def add_result(self, result: AgentResult, *, correct: bool) -> None:
        self.add_run(result.total_cost_usd, correct=correct)
        for u in result.node_usage:
            self.add_node(u.node, u.cost_usd)

    @property
    def total_cost_usd(self) -> float:
        return sum(c for c, _ in self._runs)

    @property
    def n_runs(self) -> int:
        return len(self._runs)

    @property
    def n_correct(self) -> int:
        return sum(1 for _, ok in self._runs if ok)

    @property
    def avg_cost_per_run(self) -> float:
        if not self._runs:
            return 0.0
        return self.total_cost_usd / len(self._runs)

    @property
    def cost_per_correct_answer(self) -> float:
        """Total cost divided by number of correct answers.

        Returns ``float('inf')`` if no answers were correct, so this value
        can still be sorted/compared in a leaderboard without special-casing.
        """
        n = self.n_correct
        if n == 0:
            return float("inf") if self.total_cost_usd > 0 else 0.0
        return self.total_cost_usd / n

    def per_node(self) -> dict[str, float]:
        """Cost breakdown per node (USD)."""
        return dict(self._node_totals)


def usage_from_litellm_response(
    response: Any, model: str, node: str, latency_ms: float = 0.0
) -> NodeUsage:
    """Build a :class:`NodeUsage` from a LiteLLM ``ModelResponse``.

    The function tolerates both object and dict responses since LiteLLM mirrors
    its output across providers.
    """
    try:
        usage = response["usage"]
        prompt = int(usage["prompt_tokens"])
        completion = int(usage["completion_tokens"])
        total = int(usage.get("total_tokens") or prompt + completion)
    except (KeyError, TypeError):
        try:
            prompt = int(response.usage.prompt_tokens)
            completion = int(response.usage.completion_tokens)
            total = int(getattr(response.usage, "total_tokens", prompt + completion))
        except AttributeError:
            prompt = completion = total = 0

    cost = _safe_completion_cost(completion_response=response, model=model)
    return NodeUsage(
        node=node,
        model=model,
        prompt_tokens=prompt,
        completion_tokens=completion,
        total_tokens=total,
        cost_usd=cost,
        latency_ms=latency_ms,
    )
