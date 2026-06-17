"""Latency tracking: wall-clock per-node and percentiles across an eval run."""

from __future__ import annotations

from collections import defaultdict
from statistics import mean

from agentbench.agent import AgentResult


def _percentile(values: list[float], q: float) -> float:
    """Linear-interpolation percentile. ``q`` is a fraction in [0, 1]."""
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    s = sorted(values)
    pos = q * (len(s) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(s) - 1)
    frac = pos - lo
    return s[lo] * (1 - frac) + s[hi] * frac


class LatencyTracker:
    """Accumulate wall-clock latencies and produce summary statistics."""

    def __init__(self) -> None:
        self._totals: list[float] = []
        self._per_node: dict[str, list[float]] = defaultdict(list)

    def add(self, latency_ms: float) -> None:
        self._totals.append(latency_ms)

    def add_result(self, result: AgentResult) -> None:
        self._totals.append(result.total_latency_ms)
        for u in result.node_usage:
            self._per_node[u.node].append(u.latency_ms)

    @property
    def mean_latency_ms(self) -> float:
        return mean(self._totals) if self._totals else 0.0

    def percentiles(self) -> tuple[float, float, float]:
        """Return ``(p50, p95, p99)`` over the full run."""
        return (
            _percentile(self._totals, 0.50),
            _percentile(self._totals, 0.95),
            _percentile(self._totals, 0.99),
        )

    def per_node_percentiles(self) -> dict[str, tuple[float, float, float]]:
        """Return ``(p50, p95, p99)`` per node."""
        return {
            node: (
                _percentile(values, 0.50),
                _percentile(values, 0.95),
                _percentile(values, 0.99),
            )
            for node, values in self._per_node.items()
        }
