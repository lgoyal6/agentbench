"""Reporting helpers for HPO results."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class HPOResult(BaseModel):
    """Final outcome of an HPO run."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    best_config: dict[str, Any]
    best_metric: float
    metric_name: str
    n_trials: int
    n_completed: int
    trials: list[dict[str, Any]] = Field(default_factory=list)

    def to_dataframe(self) -> Any:
        """Convert ``trials`` to a pandas DataFrame.

        Returns ``None`` if pandas is not installed.
        """
        try:
            import pandas as pd
        except ImportError:  # pragma: no cover
            return None
        if not self.trials:
            return pd.DataFrame()
        return pd.DataFrame(self.trials)

    def top(self, n: int = 5) -> list[dict[str, Any]]:
        """Return the top-N trials by metric (descending)."""
        return sorted(self.trials, key=lambda t: t.get(self.metric_name, 0.0), reverse=True)[:n]
