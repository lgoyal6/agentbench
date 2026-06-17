"""10 multi-hop QA tasks requiring 2-3 reasoning steps."""

from __future__ import annotations

from agentbench.suites.base import EvalSuite, EvalTask

_TASKS_RAW: list[tuple[str, str, str, str]] = [
    (
        "mhqa-01",
        "If the author of '1984' was born in 1903 and died at age 46, in what year did he die?",
        "1950",
        "medium",
    ),
    (
        "mhqa-02",
        "The Eiffel Tower is 330 meters tall. The Empire State Building is 443 meters tall. "
        "If you stacked the Eiffel Tower on top of the Empire State Building, how many "
        "meters tall would the combined structure be?",
        "773",
        "easy",
    ),
    (
        "mhqa-03",
        "Marie Curie won Nobel Prizes in Physics (1903) and Chemistry (1911). How many years "
        "separated her two Nobel Prizes?",
        "8",
        "easy",
    ),
    (
        "mhqa-04",
        "The Mona Lisa was painted by Leonardo da Vinci, who was born in 1452 and died in 1519. "
        "If the painting was completed in 1517, how old was Leonardo when he completed it?",
        "65",
        "medium",
    ),
    (
        "mhqa-05",
        "Mount Everest is approximately 8848 meters tall. Mount Kilimanjaro is 5895 meters tall. "
        "By what percentage (rounded to the nearest whole number) is Mount Everest taller than "
        "Mount Kilimanjaro?",
        "50",
        "hard",
    ),
    (
        "mhqa-06",
        "If a person is born on January 1, 2000, how old will they be on July 1, 2050, in "
        "completed years?",
        "50",
        "medium",
    ),
    (
        "mhqa-07",
        "The American Civil War ended in 1865. World War I ended in 1918. How many years "
        "passed between the end of the Civil War and the end of World War I?",
        "53",
        "easy",
    ),
    (
        "mhqa-08",
        "Light travels at about 300000 kilometers per second. The sun is about 150 million "
        "kilometers from Earth. How many minutes does it take light to travel from the sun "
        "to Earth (rounded to the nearest whole number)?",
        "8",
        "hard",
    ),
    (
        "mhqa-09",
        "Shakespeare was born in 1564 and died in 1616. Beethoven was born in 1770 and died "
        "in 1827. How many years after Shakespeare's death was Beethoven born?",
        "154",
        "medium",
    ),
    (
        "mhqa-10",
        "If the Great Wall of China is approximately 21000 kilometers long, and a person can "
        "walk 5 kilometers per hour for 8 hours per day, how many days (rounded to the nearest "
        "whole number) would it take to walk its entire length?",
        "525",
        "hard",
    ),
]


multihop_qa_suite = EvalSuite(
    name="multihop_qa",
    version="0.1.0",
    description=(
        "10 multi-hop reasoning QA tasks that require chaining 2-3 factual or "
        "arithmetic inferences."
    ),
    tasks=[
        EvalTask(
            id=tid,
            input={"question": q},
            expected_output=ans,
            difficulty=diff,  # type: ignore[arg-type]
            scorer_type="exact",
            metadata={"category": "multihop_qa", "hops": 2},
        )
        for tid, q, ans, diff in _TASKS_RAW
    ],
)
