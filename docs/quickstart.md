# Quickstart

## Install

```bash
pip install agentbench
```

Optional extras:

```bash
pip install "agentbench[supabase,weave,mlflow,hf]"
```

## Set up credentials

AgentBench uses LiteLLM, so any LiteLLM-supported provider works. The default
example uses OpenAI:

```bash
export OPENAI_API_KEY=sk-...
```

## Wrap a LangGraph agent

```python
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from agentbench.agent import AgentWrapper
from agentbench.integrations.litellm import completion_with_capture


class State(TypedDict):
    question: str
    answer: str


def reason(state: State) -> State:
    response = completion_with_capture(
        model="gpt-4o-mini",
        node="reason",
        messages=[
            {"role": "system", "content": "Answer concisely."},
            {"role": "user", "content": state["question"]},
        ],
    )
    return {"question": state["question"], "answer": response["choices"][0]["message"]["content"]}


g = StateGraph(State)
g.add_node("reason", reason)
g.add_edge(START, "reason")
g.add_edge("reason", END)
agent = AgentWrapper(g.compile(), name="my-agent", model="gpt-4o-mini")
```

The key call is `completion_with_capture` - that's what registers token usage
into AgentBench's capture buffer.

## Run an eval

```python
from agentbench.runner import EvalRunner, RunConfig
from agentbench.suites import get_suite

report = EvalRunner(agent, get_suite("math_reasoning"), RunConfig(concurrency=4)).run()
print(report.model_dump_json(indent=2))
```

Or from the CLI:

```bash
agentbench run --agent my_agent.py --suite math_reasoning --output report.json
agentbench report --input report.json --format markdown
```

## Submit to the leaderboard

```bash
agentbench leaderboard submit \
    --results report.json \
    --name "my-agent-v1" \
    --author "your-handle" \
    --model "gpt-4o-mini"

agentbench leaderboard show --suite math_reasoning --top 10
```

## What next?

* Read [concepts](concepts.md) to understand the metrics.
* See [contributing](contributing.md) to add a custom suite or scorer.
