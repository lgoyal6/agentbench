"""CLI smoke tests."""

from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

from typer.testing import CliRunner

from agentbench import __version__
from agentbench.cli import app, console

runner = CliRunner()

# Rich sizes tables to the detected terminal width, so assertions on rendered
# output are otherwise a function of whoever runs the suite. Pin a wide console.
console.width = 200


def test_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_suite_list() -> None:
    result = runner.invoke(app, ["suite", "list"])
    assert result.exit_code == 0
    assert "math_reasoning" in result.stdout
    assert "tool_use" in result.stdout


def test_suite_preview() -> None:
    result = runner.invoke(app, ["suite", "preview", "--suite", "math_reasoning", "--n", "2"])
    assert result.exit_code == 0
    assert "math-01" in result.stdout


def test_run_with_canned_agent(tmp_path: Path) -> None:
    """End-to-end CLI smoke test using a tiny canned agent."""
    agent_file = tmp_path / "tiny_agent.py"
    agent_file.write_text(
        textwrap.dedent(
            """
            from agentbench.agent import AgentResult, NodeUsage

            class Agent:
                name = "tiny"

                def invoke(self, input):
                    return AgentResult(
                        final_answer="28",
                        node_usage=[NodeUsage(node="llm", model="mock", total_tokens=10, cost_usd=0.0001, latency_ms=5.0)],
                        total_latency_ms=5.0,
                    )

            agent = Agent()
            """
        )
    )
    output_file = tmp_path / "report.json"
    result = runner.invoke(
        app,
        [
            "run",
            "--agent",
            str(agent_file),
            "--suite",
            "math_reasoning",
            "--trials",
            "1",
            "--output",
            str(output_file),
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert output_file.exists()
    data = json.loads(output_file.read_text())
    assert data["suite_name"] == "math_reasoning"
    assert data["n_tasks"] == 1
    # The first math task's answer is 28, so accuracy should be 1.0.
    assert data["accuracy"] == 1.0
    # Clean up importable path so subsequent tests aren't polluted.
    sys.path[:] = [p for p in sys.path if p != str(tmp_path)]


def test_report_table_format(tmp_path: Path, perfect_agent, tiny_suite) -> None:
    from agentbench.runner import EvalRunner

    report = EvalRunner(perfect_agent, tiny_suite).run()
    path = tmp_path / "r.json"
    path.write_text(report.model_dump_json())
    result = runner.invoke(app, ["report", "--input", str(path), "--format", "markdown"])
    assert result.exit_code == 0
    assert "accuracy" in result.stdout


def test_leaderboard_submit_and_show(
    tmp_path: Path, isolated_leaderboard, perfect_agent, tiny_suite
) -> None:
    from agentbench.runner import EvalRunner

    report = EvalRunner(perfect_agent, tiny_suite).run()
    report_path = tmp_path / "r.json"
    report_path.write_text(report.model_dump_json())
    submit = runner.invoke(
        app,
        [
            "leaderboard",
            "submit",
            "--results",
            str(report_path),
            "--name",
            "test-agent",
            "--author",
            "tester",
            "--model",
            "mock",
        ],
    )
    assert submit.exit_code == 0, submit.stdout
    show = runner.invoke(app, ["leaderboard", "show"])
    assert show.exit_code == 0
    assert "test-agent" in show.stdout
