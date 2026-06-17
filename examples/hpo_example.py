"""Full HPO run example.

Sweeps over system prompt style, temperature, and model, optimizing for
``cost_adjusted_accuracy`` on the math_reasoning suite.
"""

from __future__ import annotations

import os
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from agentbench.agent import AgentWrapper
from agentbench.hpo import HPOConfig, HPORunner, default_search_space
from agentbench.hpo.search_space import get_system_prompt
from agentbench.integrations.litellm import completion_with_capture
from agentbench.suites import get_suite


class State(TypedDict):
    question: str
    answer: str


def build_agent(config: dict[str, Any]) -> AgentWrapper:
    """Build an agent for a single HPO trial config."""
    system_prompt = get_system_prompt(config["system_prompt_style"])
    model = config["model"]
    temperature = float(config["temperature"])
    max_tokens = int(config["max_tokens_per_node"])

    def reason(state: State) -> State:
        response = completion_with_capture(
            model=model,
            node="reason",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": state["question"]},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        try:
            content = response["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            content = ""
        return {"question": state["question"], "answer": content}

    g = StateGraph(State)
    g.add_node("reason", reason)
    g.add_edge(START, "reason")
    g.add_edge("reason", END)
    return AgentWrapper(g.compile(), name=f"hpo-{model}", model=model)


def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("Set OPENAI_API_KEY first.")

    suite = get_suite("math_reasoning").sample(5, seed=0)
    runner = HPORunner(
        trainable_factory=build_agent,
        suite=suite,
        search_space=default_search_space(),
        config=HPOConfig(num_samples=10, max_concurrent_trials=2, eval_max_tasks=5),
    )
    result = runner.run()
    print("Best config:", result.best_config)
    print(f"Best {result.metric_name}: {result.best_metric:.4f}")
    print("Top trials:")
    for t in result.top(3):
        print(f"  {t.get('trial_id')}: {t.get(result.metric_name, 0):.4f}")


if __name__ == "__main__":
    main()
