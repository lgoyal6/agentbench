"""Ray Tune search space definitions for agent HPO.

The search space here is opinionated: it sweeps over the knobs we've found to
move the cost-accuracy tradeoff the most, not every conceivable agent setting.
Users with custom configurations can pass their own dict directly to
:class:`~agentbench.hpo.runner.HPORunner`.
"""

from __future__ import annotations

from typing import Any

SYSTEM_PROMPT_STYLES = ("concise", "verbose", "chain_of_thought", "role_play")
MODELS = ("gpt-4o-mini", "claude-haiku", "gemini-flash")


def default_search_space() -> dict[str, Any]:
    """Return the canonical AgentBench search space.

    Parameters:
        * ``system_prompt_style``: ``concise`` | ``verbose`` | ``chain_of_thought`` | ``role_play``
        * ``temperature``: uniform float in [0.0, 1.0]
        * ``max_tokens_per_node``: choice of 256 / 512 / 1024
        * ``few_shot_count``: choice of 0 / 1 / 3 / 5
        * ``model``: choice of gpt-4o-mini / claude-haiku / gemini-flash
        * ``use_cot_in_synthesizer``: bool
    """
    try:
        from ray import tune
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "ray[tune] is required for HPO; install with `pip install agentbench`."
        ) from exc

    return {
        "system_prompt_style": tune.choice(list(SYSTEM_PROMPT_STYLES)),
        "temperature": tune.uniform(0.0, 1.0),
        "max_tokens_per_node": tune.choice([256, 512, 1024]),
        "few_shot_count": tune.choice([0, 1, 3, 5]),
        "model": tune.choice(list(MODELS)),
        "use_cot_in_synthesizer": tune.choice([True, False]),
    }


SYSTEM_PROMPTS: dict[str, str] = {
    "concise": "You are a precise assistant. Answer briefly and correctly.",
    "verbose": (
        "You are a careful, thorough assistant. Think through the problem fully, "
        "explain your reasoning, and provide a complete answer."
    ),
    "chain_of_thought": (
        "You are a helpful assistant. Reason step-by-step. After reasoning, write "
        "the final answer on its own line in the format `Answer: <answer>`."
    ),
    "role_play": (
        "You are a domain expert who has been solving problems like this for 20 years. "
        "Approach the problem with confidence and arrive at the correct answer."
    ),
}


def get_system_prompt(style: str) -> str:
    """Look up the system prompt template for a given style."""
    return SYSTEM_PROMPTS.get(style, SYSTEM_PROMPTS["concise"])
