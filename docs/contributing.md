# Contributing

We welcome contributions. The most useful are new suites, new scorers, and
performance improvements.

## Dev setup

```bash
git clone https://github.com/agentbench/agentbench
cd agentbench
pip install -e ".[dev]"
pytest
```

## Add a new suite

1. Create `agentbench/suites/<your_suite>.py` exporting an `EvalSuite` instance.
2. Register it in `agentbench/suites/__init__.py` (add to `_SUITE_REGISTRY`).
3. Add a test in `tests/test_suites.py` asserting the suite loads and has the
   expected number of tasks.

Task content should be **real**, not lorem ipsum. If you adapt a public
benchmark, cite it in the suite's `description`. If the suite touches sensitive
or licensed data, mark `metadata={"license": "..."}` on every task.

## Add a new scorer

1. Implement the `Scorer` protocol in `agentbench/metrics/accuracy.py` (or a new
   module if it has different dependencies).
2. Register it in `agentbench.runner._scorer_for`.
3. Add to the `ScorerType` literal in `agentbench/suites/base.py`.
4. Cover it in `tests/test_metrics.py` with at least one known input/output
   pair.

## PR checklist

* `ruff check agentbench/ tests/` is clean.
* `mypy agentbench/` is clean.
* `pytest --cov=agentbench` does not regress coverage.
* New public API has docstrings.
* For new metrics: include the math in the docstring (LaTeX-rendered in MkDocs).

## Release process (maintainers)

1. Bump `version` in `pyproject.toml` and `agentbench/__init__.py`.
2. Tag `vX.Y.Z`. GitHub Actions publishes to PyPI via trusted publishing.
