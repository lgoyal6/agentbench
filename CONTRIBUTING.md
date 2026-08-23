# Contributing to AgentBench

Thanks for your interest! This file is a short pointer; the full guide lives at
[docs/contributing.md](docs/contributing.md).

## TL;DR

```bash
git clone https://github.com/agentbench/agentbench
cd agentbench
pip install -e ".[dev]"

ruff check agentbench tests
mypy agentbench
pytest --cov=agentbench
```

## Where things live

| Path                       | What it is                                          |
| -------------------------- | --------------------------------------------------- |
| `agentbench/agent.py`      | Protocol every agent satisfies + LangGraph wrapper. |
| `agentbench/runner.py`     | The eval orchestrator.                              |
| `agentbench/metrics/`      | Scorers + cost / latency / composite metrics.       |
| `agentbench/suites/`       | Built-in evals. New suites go here.                 |
| `agentbench/hpo/`          | Ray Tune sweeps.                                    |
| `agentbench/cli.py`        | Typer entry point.                                  |
| `tests/`                   | pytest. No live network calls - mock LLMs.          |

## Code style

* Ruff governs lint; mypy governs types. CI runs both.
* Keep public APIs Pydantic v2 models - they serialize for free into reports
  and leaderboard entries.
* Prefer pure functions in `metrics/` so they can be tested without fixtures.
* No `print`. Use `rich.console.Console` for CLI output and `logging` elsewhere.

## License

By contributing you agree that your contributions are licensed under the MIT
License, same as the project.
