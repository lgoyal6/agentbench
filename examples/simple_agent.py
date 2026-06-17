"""Minimal runnable LangGraph agent for AgentBench.

Prerequisites
-------------
* ``pip install agentbench langgraph langchain-openai``
* Set ``OPENAI_API_KEY`` in your environment.

Run it
------
.. code-block:: bash

    python examples/simple_agent.py
    # or, against the full math_reasoning suite:
    agentbench run --agent examples/simple_agent.py --suite math_reasoning --trials 5
"""

from __future__ import annotations

import os
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from agentbench.agent import AgentWrapper
from agentbench.integrations.litellm import completion_with_capture


class State(TypedDict, total=False):
    question: str
    source: str
    task: str
    answer: str


SYSTEM_PROMPT = (
    "You are a careful reasoner. Read the input, think step-by-step, and "
    "give a concise final answer. For numeric questions, end with a line "
    "of the form `Answer: <number>`."
)


def _build_user_message(state: State) -> str:
    if "question" in state:
        return state["question"]
    if "source" in state:
        task = state.get("task") or "Summarize the following text in one sentence."
        return f"{task}\n\n{state['source']}"
    return "\n".join(f"{k}: {v}" for k, v in state.items() if k != "answer")


def reason(state: State) -> State:
    """Single LLM node that handles any suite input shape."""
    import time

    model = os.getenv("AGENTBENCH_EXAMPLE_MODEL", "gpt-4o-mini")
    throttle = float(os.getenv("AGENTBENCH_EXAMPLE_THROTTLE_S", "0"))
    if throttle > 0:
        time.sleep(throttle)
    response = completion_with_capture(
        model=model,
        node="reason",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_message(state)},
        ],
        temperature=0.0,
        max_tokens=1024,
    )
    try:
        content = response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        content = ""
    return {**state, "answer": content}


def build_graph() -> AgentWrapper:
    graph = StateGraph(State)
    graph.add_node("reason", reason)
    graph.add_edge(START, "reason")
    graph.add_edge("reason", END)
    compiled = graph.compile()
    return AgentWrapper(compiled, name="simple-reasoner", model="gpt-4o-mini")


# AgentBench's CLI looks for a top-level ``agent`` attribute.
agent = build_graph()


if __name__ == "__main__":
    from rich.console import Console

    from agentbench.runner import EvalRunner, RunConfig
    from agentbench.suites import get_suite

    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("Set OPENAI_API_KEY to run this example against a real model.")

    suite = get_suite("math_reasoning").sample(3, seed=42)
    report = EvalRunner(agent, suite, RunConfig(concurrency=2)).run()
    Console().print(report.model_dump(mode="json"))
