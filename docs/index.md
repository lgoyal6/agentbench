# AgentBench

**AgentBench is an evaluation framework for LangGraph agents that treats token economics as a first-class metric, alongside accuracy and latency.**

The core insight: a frontier model that scores 5 points higher in accuracy but
burns 50× more tokens is not always the right choice. Every metric in
AgentBench is reported in the context of cost, so the tradeoff is visible at a
glance.

## Quickstart

```bash
pip install agentbench
agentbench run --agent examples/simple_agent.py --suite math_reasoning --trials 10
```

That's it. The CLI imports your agent, runs the suite in parallel, and prints a
table with accuracy, total cost, latency percentiles, and the composite
`cost_adjusted_accuracy` metric.

## What you get

* **4 built-in suites** - math reasoning, tool use, summarization, multihop QA.
* **3 scorers** - exact match (with numeric extraction), semantic similarity,
  LLM-as-judge.
* **Cost tracking via LiteLLM** - works with any provider LiteLLM supports.
* **HPO via Ray Tune** - sweep prompt styles, models, and decoding settings,
  optimizing for `cost_adjusted_accuracy`.
* **Leaderboards** - local JSON by default; Supabase backend behind a flag.
* **FastAPI HTTP server** - `POST /run`, `GET /leaderboard`.
* **Tracking-backend-agnostic** - bring W&B Weave, MLflow, or nothing.

See the [quickstart](quickstart.md) for a full walkthrough or
[concepts](concepts.md) for the design rationale.
