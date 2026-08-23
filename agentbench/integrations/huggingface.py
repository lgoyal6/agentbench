"""Load custom eval suites from HuggingFace datasets."""

from __future__ import annotations

from typing import Any

from agentbench.suites.base import EvalSuite, EvalTask


def load_hf_suite(
    dataset_name: str,
    *,
    split: str = "test",
    input_field: str = "question",
    expected_field: str = "answer",
    id_field: str | None = None,
    difficulty_field: str | None = None,
    scorer_type: str = "exact",
    suite_name: str | None = None,
    max_tasks: int | None = None,
) -> EvalSuite:
    """Load a HuggingFace dataset and convert it into an :class:`EvalSuite`.

    Args:
        dataset_name: e.g. ``"gsm8k"`` (or any ``datasets.load_dataset`` argument).
        split: The dataset split to load.
        input_field: Column to use as the task input.
        expected_field: Column to use as the expected output.
        id_field: Optional column to use as the task id. Falls back to row index.
        difficulty_field: Optional column to use as difficulty.
        scorer_type: One of ``"exact"`` / ``"semantic"`` / ``"llm_judge"``.
        suite_name: Override the resulting suite's name.
        max_tasks: Optional cap on the number of tasks loaded.

    Returns:
        A populated :class:`EvalSuite`.
    """
    try:
        from datasets import load_dataset
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "datasets is required for load_hf_suite; install with `pip install datasets`."
        ) from exc

    ds = load_dataset(dataset_name, split=split)
    tasks: list[EvalTask] = []
    for idx, row in enumerate(ds):
        if max_tasks is not None and len(tasks) >= max_tasks:
            break
        if input_field not in row or expected_field not in row:
            continue
        diff: Any = row.get(difficulty_field) if difficulty_field else "medium"
        if diff not in {"easy", "medium", "hard"}:
            diff = "medium"
        tasks.append(
            EvalTask(
                id=str(row.get(id_field, idx)) if id_field else f"{dataset_name}-{idx}",
                input={input_field: row[input_field]},
                expected_output=row[expected_field],
                difficulty=diff,
                scorer_type=scorer_type,  # type: ignore[arg-type]
                metadata={"source": dataset_name, "split": split},
            )
        )
    return EvalSuite(
        name=suite_name or dataset_name,
        version="hf",
        description=f"Loaded from HuggingFace dataset {dataset_name} ({split}).",
        tasks=tasks,
    )
