```
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║                     ███   ████ █████ █   █ █████                     ║
║                    █   █ █     █     ██  █   █                       ║
║                    █████ █  ██ ███   █ █ █   █                       ║
║                    █   █ █   █ █     █  ██   █                       ║
║                    █   █  ████ █████ █   █   █                       ║
║                                                                      ║
║                    ████  █████ █   █  ████ █   █                     ║
║                    █   █ █     ██  █ █     █   █                     ║
║                    ████  ███   █ █ █ █     █████                     ║
║                    █   █ █     █  ██ █     █   █                     ║
║                    ████  █████ █   █  ████ █   █                     ║
║                                                                      ║
║              token economics + accuracy, in one number               ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
```

[![CI](https://github.com/lgoyal6/agentbench/actions/workflows/ci.yml/badge.svg)](https://github.com/lgoyal6/agentbench/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)

**AgentBench is an evaluation framework for LangGraph agents that treats token
economics as a first-class metric, alongside accuracy and latency.** A frontier
model that scores 5 points higher in accuracy but burns 50× more tokens is not
always the right choice. AgentBench surfaces that tradeoff with a single number
(`cost_adjusted_accuracy`) so you can pick the right model for the right job,
not just the highest-scoring one.

## Features

- **Single CLI command** to point at any LangGraph `StateGraph` and get back a
  full eval report.
- **Four built-in eval suites** - math reasoning (20), tool use (15),
  summarization (10), multi-hop QA (10).
- **Three scorers** - exact match (with numeric fallback), semantic similarity
  via `sentence-transformers`, and LLM-as-judge via LiteLLM.
- **Per-node token & cost tracking** via LiteLLM, model-agnostic.
- **Composite metrics** - `cost_adjusted_accuracy` and `efficiency_score`.
- **HPO via Ray Tune + ASHA** over prompt style, model, temperature, and decoding.
- **Leaderboards** - local JSON by default, optional Supabase backend.
- **Tracking integrations** - W&B Weave, MLflow, or BYO (`TrackerProtocol`).
- **FastAPI HTTP service** - `POST /run`, `GET /run/{id}`, `GET /leaderboard`.

## Install

```bash
pip install git+https://github.com/lgoyal6/agentbench
```

Optional extras:

```bash
pip install "agentbench[weave,mlflow,supabase,hf] @ git+https://github.com/lgoyal6/agentbench"
```

## Quickstart

```python
from typing import TypedDict
from langgraph.graph import END, START, StateGraph
from agentbench.agent import AgentWrapper
from agentbench.integrations.litellm import completion_with_capture
from agentbench.runner import EvalRunner
from agentbench.suites import get_suite

class State(TypedDict):
    question: str
    answer: str

def reason(state):
    r = completion_with_capture(model="gpt-4o-mini", node="reason",
        messages=[{"role": "user", "content": state["question"]}])
    return {"question": state["question"], "answer": r["choices"][0]["message"]["content"]}

g = StateGraph(State); g.add_node("reason", reason)
g.add_edge(START, "reason"); g.add_edge("reason", END)
agent = AgentWrapper(g.compile(), name="quickstart", model="gpt-4o-mini")

report = EvalRunner(agent, get_suite("math_reasoning")).run()
print(f"accuracy={report.accuracy:.2f}  cost=${report.total_cost_usd:.4f}  CAA={report.cost_adjusted_accuracy:.2f}")
```

Or from the shell:

```bash
agentbench run --agent my_agent.py --suite math_reasoning --trials 20
```

## Benchmark results

First reference run, all four suites (n=55 tasks), agent =
[`examples/simple_agent.py`](examples/simple_agent.py), single-node LangGraph,
no tools, no few-shot, `temperature=0`. Raw JSON in
[`benchmarks/v0.1.0/`](benchmarks/v0.1.0/).

| suite          | model                | n  | accuracy | avg_cost_per_run | p50_latency | p95_latency |
| -------------- | -------------------- | -- | -------- | ---------------- | ----------- | ----------- |
| math_reasoning | claude-haiku-4-5     | 20 | 0.950    | $0.00107         | 2222 ms     | 2619 ms     |
| tool_use       | claude-haiku-4-5     | 15 | 1.000    | $0.00059         | 1745 ms     | 3216 ms     |
| summarization  | claude-haiku-4-5     | 10 | 1.000    | $0.00035         | 1420 ms     | 22615 ms    |
| multihop_qa    | claude-haiku-4-5     | 10 | 0.900    | $0.00081         | 1992 ms     | 3357 ms     |
| **overall**    | **claude-haiku-4-5** | 55 | **0.964**| **$0.00076**     | -           | -           |

Run on 2026-06-16 against `claude-haiku-4-5-20251001` via LiteLLM. Total
spend: $0.0417 across all 55 tasks (\~$0.001 per task, end-to-end). The
summarization p95 outlier is a single slow API response - p50 is 1.4 s.

Multi-model comparison rows (gpt-4o-mini, gemini-2.5-flash) are pending:
OpenAI account needs billing enabled, and Gemini free-tier daily quota was
exhausted during preliminary runs. Re-run instructions are in
[`benchmarks/v0.1.0/README.md`](benchmarks/v0.1.0/README.md).

The framework's intended takeaway - that highest-accuracy is rarely the same
model as best `cost_adjusted_accuracy` - needs the cross-model comparison to
demonstrate. Watch this space.

## Architecture

```
            ┌──────────────────┐
            │  LangGraph agent │
            └────────┬─────────┘
                     │
                     ▼
            ┌──────────────────┐         ┌─────────────────┐
            │   AgentWrapper   │────────▶│ LiteLLM capture │
            └────────┬─────────┘         │  (per-node $$$) │
                     │                   └─────────────────┘
                     ▼
   ┌─────────────────────────────────┐
   │           EvalRunner            │   ──▶  TrackerProtocol (Weave, MLflow, ...)
   │  ┌──────────┐  ┌─────────────┐  │
   │  │ Scorers  │  │ CostTracker │  │
   │  └──────────┘  └─────────────┘  │
   │  ┌────────────────────────────┐ │
   │  │   LatencyTracker (p50/95)  │ │
   │  └────────────────────────────┘ │
   └────────────────┬────────────────┘
                    ▼
            ┌──────────────────┐
            │    EvalReport    │ ──▶ CLI / JSON / Leaderboard / FastAPI
            └──────────────────┘
                    │
                    ▼
            ┌──────────────────┐
            │  HPORunner (Ray) │  sweeps prompts/models for best CAA
            └──────────────────┘
```

## Documentation

- [Quickstart](docs/quickstart.md)
- [Concepts](docs/concepts.md) - the math behind `cost_adjusted_accuracy`
- [API reference](docs/api_reference.md)
- [Contributing](docs/contributing.md)

## License

MIT - see [LICENSE](LICENSE).
