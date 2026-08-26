# benchmarks/v0.1.0/

Raw `EvalReport` JSON dumps from AgentBench's first reference run.

## What's here

| file                                       | suite          | model            | n  | accuracy | avg_cost |
| ------------------------------------------ | -------------- | ---------------- | -- | -------- | -------- |
| `claude-haiku-4-5.json`                    | math_reasoning | claude-haiku-4-5 | 20 | 0.950    | $0.00107 |
| `claude-haiku-4-5-tool_use.json`           | tool_use       | claude-haiku-4-5 | 15 | 1.000    | $0.00059 |
| `claude-haiku-4-5-summarization.json`      | summarization  | claude-haiku-4-5 | 10 | 1.000    | $0.00035 |
| `claude-haiku-4-5-multihop_qa.json`        | multihop_qa    | claude-haiku-4-5 | 10 | 0.900    | $0.00081 |

Generated on 2026-06-16 using `examples/simple_agent.py`.

## Reproducing

```bash
pip install -e ".[dev]"
export ANTHROPIC_API_KEY=sk-ant-...

for suite in math_reasoning tool_use summarization multihop_qa; do
  AGENTBENCH_EXAMPLE_MODEL=claude-haiku-4-5-20251001 \
    agentbench run \
      --agent examples/simple_agent.py \
      --suite "$suite" \
      --concurrency 4 \
      --output "benchmarks/v0.1.0/claude-haiku-4-5-${suite}.json"
done
```

## Adding new model rows

To compare another model, swap `AGENTBENCH_EXAMPLE_MODEL` to its LiteLLM id
(e.g. `gpt-4o-mini`, `gemini/gemini-2.5-flash`) and re-run. Gemini free tier
caps at 20 req/day per model - enable billing or expect partial runs.

## Caveats

- The example agent is a single LangGraph reasoning node with no tool calls.
  `tool_use` scoring at 1.000 means Claude answered the test questions from
  parametric knowledge; it does **not** demonstrate tool-calling capability.
- `temperature=0`, single trial per task - no variance bars.
- The `summarization` p95 (22.6 s) is an outlier from a single slow API
  response. Median p50 is 1.4 s.
