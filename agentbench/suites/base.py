"""Base classes for eval tasks and suites."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Difficulty = Literal["easy", "medium", "hard"]
ScorerType = Literal["exact", "semantic", "llm_judge"]


class EvalTask(BaseModel):
    """A single evaluation task."""

    model_config = ConfigDict(extra="forbid")

    id: str
    input: dict[str, Any]
    expected_output: Any
    difficulty: Difficulty = "medium"
    scorer_type: ScorerType = "exact"
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvalSuite(BaseModel):
    """A named, versioned collection of eval tasks."""

    model_config = ConfigDict(extra="forbid")

    name: str
    version: str = "0.1.0"
    description: str = ""
    tasks: list[EvalTask] = Field(default_factory=list)

    def __len__(self) -> int:
        return len(self.tasks)

    def __iter__(self) -> Iterator[EvalTask]:  # type: ignore[override]
        return iter(self.tasks)

    def filter(
        self, *, difficulty: Difficulty | None = None, scorer_type: ScorerType | None = None
    ) -> EvalSuite:
        """Return a new suite filtered by difficulty and/or scorer type."""
        tasks = [
            t
            for t in self.tasks
            if (difficulty is None or t.difficulty == difficulty)
            and (scorer_type is None or t.scorer_type == scorer_type)
        ]
        return EvalSuite(
            name=f"{self.name}[filtered]",
            version=self.version,
            description=self.description,
            tasks=tasks,
        )

    def sample(self, n: int, *, seed: int = 0) -> EvalSuite:
        """Deterministically sample ``n`` tasks."""
        import random

        rng = random.Random(seed)
        tasks = list(self.tasks)
        rng.shuffle(tasks)
        return EvalSuite(
            name=f"{self.name}[sample={n}]",
            version=self.version,
            description=self.description,
            tasks=tasks[:n],
        )
