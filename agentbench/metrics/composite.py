"""Composite metrics that combine accuracy, cost, and latency.

These are the metrics that make AgentBench distinctive: a frontier model that
scores higher accuracy but burns 50x more tokens is *not* always the right
choice, and a single scalar makes that tradeoff visible at a glance.
"""

from __future__ import annotations

import math

EPSILON = 1e-6


def cost_adjusted_accuracy(accuracy: float, total_cost_usd: float, *, epsilon: float = EPSILON) -> float:
    r"""Compute accuracy per cent spent.

    .. math::

        \mathrm{CAA} = \frac{\mathrm{accuracy}}{\mathrm{total\_cost\_cents} + \varepsilon}

    Where :math:`\varepsilon` is a small constant (default :math:`10^{-6}`) to
    avoid division by zero when an agent runs free or hasn't been billed yet.

    Higher is better. Two practical notes:

    1. The unit is "accuracy per cent". For a $0.01 run that scored 0.8, the
       result is roughly 80.
    2. The metric is intentionally *not* normalized to [0, 1]. Comparisons are
       only meaningful within the same suite and number of tasks.

    Args:
        accuracy: Mean accuracy on the suite, in [0, 1].
        total_cost_usd: Total cost of the run in USD.
        epsilon: Numerical stability constant.

    Returns:
        Cost-adjusted accuracy, higher is better.
    """
    cents = total_cost_usd * 100.0
    return accuracy / (cents + epsilon)


def efficiency_score(accuracy: float, latency_ms: float) -> float:
    r"""Combine accuracy with a logarithmic latency penalty.

    .. math::

        \mathrm{efficiency} = \mathrm{accuracy} \cdot \frac{1}{\log(\mathrm{latency\_ms} + 1)}

    The logarithm dampens the penalty so that a 10x slowdown only roughly
    halves the score, matching how users perceive latency at the second-scale.

    Args:
        accuracy: Mean accuracy on the suite, in [0, 1].
        latency_ms: Mean latency in milliseconds (use the mean, not p95, so the
            metric is symmetric with cost - both are sums divided by N).

    Returns:
        Efficiency score, higher is better. Returns 0 when latency is 0.
    """
    if latency_ms <= 0:
        return 0.0
    return accuracy * (1.0 / math.log(latency_ms + 1.0))
