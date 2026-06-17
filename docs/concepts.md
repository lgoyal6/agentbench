# Concepts

## EvalTask

A single evaluation case. Has an `id`, an `input` dict (passed verbatim to your
agent), an `expected_output`, a `difficulty`, a `scorer_type`, and free-form
`metadata`. Tasks are Pydantic v2 models, so they serialize cleanly.

## EvalSuite

A named, versioned collection of tasks. Suites are immutable in spirit — bump
the `version` when you change the task set so leaderboard entries remain
comparable. Built-in suites are registered by name and discoverable via
`agentbench suite list`.

## Scorer

A scorer maps `(prediction, reference) -> [0, 1]`. AgentBench ships three:

* **ExactMatchScorer** — string equality after normalization, with a numeric
  fallback that extracts the last number in the prediction. This is what makes
  chain-of-thought outputs like "...therefore the answer is 42." score correctly.
* **SemanticSimilarityScorer** — cosine of `all-MiniLM-L6-v2` embeddings.
* **LLMJudgeScorer** — calls a configurable LLM via LiteLLM, parses a strict
  JSON `{"score": ..., "reasoning": ...}` response. Falls back to 0 on parse
  failure rather than crashing.

A score ≥ 0.5 is treated as "correct" when computing accuracy.

## CostTracker

Wraps LiteLLM's `completion_cost`. Tracks:

* `total_cost_usd` — sum across all runs.
* `avg_cost_per_run` — total / N.
* `cost_per_correct_answer` — total / N correct. Returns `inf` when there are
  no correct answers, so it remains sortable.

Per-node breakdowns are available via `CostTracker.per_node()`.

## LatencyTracker

Captures wall-clock time per node and total. Computes p50, p95, p99 using
linear-interpolation percentiles.

## cost_adjusted_accuracy

The signature AgentBench metric:

```
cost_adjusted_accuracy = accuracy / (total_cost_cents + epsilon)
```

The unit is "accuracy per cent". For a $0.01 run that scored 0.8, the result is
roughly 80. It is intentionally **not** normalized to [0, 1] — comparisons are
only meaningful within the same suite and number of tasks.

## efficiency_score

```
efficiency_score = accuracy * (1 / log(latency_ms + 1))
```

A logarithm dampens the latency penalty so that a 10× slowdown only roughly
halves the score, matching how humans perceive latency at the second-scale.

## Why HPO over prompt variants matters

Most of the cost-accuracy frontier shifts agents have come not from better
models but from better prompting and decoding choices: chain-of-thought vs. concise,
temperature 0 vs. 0.3, 0-shot vs. 5-shot. AgentBench's HPO sweeps these
explicitly with `cost_adjusted_accuracy` as the objective, so the result is the
*economically optimal* configuration, not just the highest-accuracy one.

The default search space sweeps:

| parameter              | values                                                      |
| ---------------------- | ----------------------------------------------------------- |
| `system_prompt_style`  | concise / verbose / chain_of_thought / role_play            |
| `temperature`          | uniform(0.0, 1.0)                                           |
| `max_tokens_per_node`  | choice(256, 512, 1024)                                      |
| `few_shot_count`       | choice(0, 1, 3, 5)                                          |
| `model`                | gpt-4o-mini / claude-haiku / gemini-flash                   |
| `use_cot_in_synthesizer` | bool                                                      |

ASHA early-stops trials that look unpromising, so you can afford 50 trials.
