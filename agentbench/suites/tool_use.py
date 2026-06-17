"""15 tool-use tasks.

Each task expects the agent to call a mock ``search`` tool and synthesize the
result. The framework provides a built-in mock search tool callable that suite
adopters can wire into their LangGraph. The expected output is the synthesized
answer, scored either by exact match or LLM judge depending on the task.
"""

from __future__ import annotations

from agentbench.suites.base import EvalSuite, EvalTask

# A simple in-memory knowledge base the mock tool can search.
MOCK_KNOWLEDGE_BASE: dict[str, str] = {
    "capital of france": "Paris",
    "capital of japan": "Tokyo",
    "capital of australia": "Canberra",
    "capital of canada": "Ottawa",
    "capital of brazil": "Brasilia",
    "tallest mountain": "Mount Everest, at 8848 meters above sea level.",
    "longest river": "The Nile River, approximately 6650 kilometers long.",
    "speed of light": "The speed of light in vacuum is approximately 299,792 km/s.",
    "boiling point of water": "Water boils at 100 degrees Celsius at standard atmospheric pressure.",
    "freezing point of water": "Water freezes at 0 degrees Celsius at standard atmospheric pressure.",
    "first president of the united states": "George Washington",
    "year of moon landing": "1969",
    "inventor of the telephone": "Alexander Graham Bell",
    "author of hamlet": "William Shakespeare",
    "largest planet": "Jupiter",
    "smallest planet": "Mercury",
    "number of continents": "7",
    "number of elements in periodic table": "118",
    "currency of japan": "Japanese Yen",
    "currency of united kingdom": "Pound Sterling",
}


def mock_search(query: str) -> str:
    """A deterministic mock search tool over a small in-memory KB.

    Returns the best partial-match result, or "no results found".
    """
    q = query.strip().lower()
    if q in MOCK_KNOWLEDGE_BASE:
        return MOCK_KNOWLEDGE_BASE[q]
    for key, value in MOCK_KNOWLEDGE_BASE.items():
        if key in q or q in key:
            return value
    return "no results found"


_TASKS_RAW: list[tuple[str, str, str, str, str]] = [
    # (id, question, expected_answer, difficulty, scorer)
    ("tool-01", "What is the capital of France?", "Paris", "easy", "exact"),
    ("tool-02", "What is the capital of Japan?", "Tokyo", "easy", "exact"),
    ("tool-03", "What is the tallest mountain in the world?", "Mount Everest", "easy", "exact"),
    ("tool-04", "Who was the first president of the United States?", "George Washington", "easy", "exact"),
    ("tool-05", "In what year did humans first land on the moon?", "1969", "easy", "exact"),
    ("tool-06", "What is the largest planet in our solar system?", "Jupiter", "easy", "exact"),
    ("tool-07", "Who invented the telephone?", "Alexander Graham Bell", "medium", "exact"),
    ("tool-08", "Who wrote the play Hamlet?", "William Shakespeare", "medium", "exact"),
    ("tool-09", "How many continents are there?", "7", "easy", "exact"),
    ("tool-10", "What is the currency of Japan?", "Japanese Yen", "medium", "exact"),
    (
        "tool-11",
        "What is the boiling point of water in Celsius at standard atmospheric pressure?",
        "100",
        "medium",
        "exact",
    ),
    (
        "tool-12",
        "Summarize in one sentence what the mock search tool returns for 'speed of light'.",
        "The speed of light in vacuum is approximately 299792 kilometers per second.",
        "medium",
        "semantic",
    ),
    (
        "tool-13",
        "Use the search tool to find the longest river and report its approximate length in kilometers.",
        "6650",
        "medium",
        "exact",
    ),
    (
        "tool-14",
        "What is the currency used in the United Kingdom?",
        "Pound Sterling",
        "medium",
        "exact",
    ),
    (
        "tool-15",
        "Compare the boiling and freezing points of water at standard atmospheric pressure. Express the difference in Celsius.",
        "100",
        "hard",
        "exact",
    ),
]


tool_use_suite = EvalSuite(
    name="tool_use",
    version="0.1.0",
    description=(
        "15 tasks requiring the agent to call a mock search tool over a small "
        "in-memory knowledge base and synthesize the answer."
    ),
    tasks=[
        EvalTask(
            id=tid,
            input={"question": q, "tool": "search"},
            expected_output=ans,
            difficulty=diff,  # type: ignore[arg-type]
            scorer_type=scorer,  # type: ignore[arg-type]
            metadata={"category": "tool_use", "available_tools": ["search"]},
        )
        for tid, q, ans, diff, scorer in _TASKS_RAW
    ],
)
