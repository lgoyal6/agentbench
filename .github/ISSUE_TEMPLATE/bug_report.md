---
name: Bug report
about: Something broke when running AgentBench
title: "[BUG] "
labels: bug
---

**Describe the bug**

A clear, concise description of what went wrong.

**To reproduce**

Minimal code that triggers the issue. Ideally:

```python
from agentbench.runner import EvalRunner, RunConfig
from agentbench.suites import get_suite
# ... your agent ...
report = EvalRunner(agent, get_suite("math_reasoning")).run()
```

The exact CLI command if it was triggered via the CLI:

```bash
agentbench run --agent ... --suite ...
```

**Expected behavior**

What you expected to see.

**Observed behavior**

What you actually saw. Paste the full traceback inside a code block.

**Environment**

- AgentBench version (`agentbench version`):
- Python version:
- OS:
- Provider used (OpenAI / Anthropic / Gemini / ...):
- LangGraph version:

**Additional context**

Anything else that might help - full JSON report, debug logs, etc.
