"""Typer CLI for AgentBench."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from agentbench import __version__
from agentbench.exceptions import SuiteLoadError
from agentbench.leaderboard import get_leaderboard
from agentbench.leaderboard.schema import LeaderboardEntry
from agentbench.runner import EvalReport, EvalRunner, RunConfig
from agentbench.suites import get_suite, list_suites

app = typer.Typer(
    name="agentbench",
    help="AgentBench: token-economics-aware evaluation framework for LangGraph agents.",
    no_args_is_help=True,
)
suite_app = typer.Typer(help="Inspect available eval suites.", no_args_is_help=True)
leaderboard_app = typer.Typer(help="Submit and view leaderboard entries.", no_args_is_help=True)
app.add_typer(suite_app, name="suite")
app.add_typer(leaderboard_app, name="leaderboard")

console = Console()


def _import_agent(spec: str) -> Any:
    """Resolve ``module:attr``, ``module.attr``, or a path to a .py file with ``agent`` attribute."""
    if spec.endswith(".py"):
        path = Path(spec).resolve()
        if not path.exists():
            raise typer.BadParameter(f"Agent file not found: {spec}")
        sys.path.insert(0, str(path.parent))
        mod = importlib.import_module(path.stem)
        if not hasattr(mod, "agent"):
            raise typer.BadParameter(f"{spec} must export a top-level `agent` object")
        return mod.agent
    if ":" in spec:
        module_path, attr = spec.split(":", 1)
    elif "." in spec:
        module_path, attr = spec.rsplit(".", 1)
    else:
        raise typer.BadParameter(f"Invalid agent spec: {spec}")
    module = importlib.import_module(module_path)
    return getattr(module, attr)


@app.command()
def version() -> None:
    """Print the AgentBench version."""
    console.print(f"agentbench {__version__}")


@app.command()
def run(
    agent: str = typer.Option(..., "--agent", help="Path to agent module or .py file."),
    suite: str = typer.Option(..., "--suite", help="Suite name (e.g. math_reasoning)."),
    trials: int | None = typer.Option(
        None, "--trials", help="Cap on number of tasks; runs all if omitted."
    ),
    metric: str = typer.Option(
        "cost_adjusted_accuracy", "--metric", help="Metric to highlight in the summary."
    ),
    concurrency: int = typer.Option(4, "--concurrency", min=1, max=64),
    judge_model: str = typer.Option("gpt-4o-mini", "--judge-model"),
    output: Path | None = typer.Option(None, "--output", help="Where to write JSON report."),
) -> None:
    """Run an eval and (optionally) write a JSON report."""
    try:
        suite_obj = get_suite(suite)
    except SuiteLoadError as exc:
        console.print(f"[red]error:[/red] {exc}")
        raise typer.Exit(code=2) from exc

    agent_obj = _import_agent(agent)
    config = RunConfig(concurrency=concurrency, max_tasks=trials, judge_model=judge_model)
    console.print(
        f"Running [bold]{suite_obj.name}[/bold] ({len(suite_obj)} tasks, concurrency={concurrency})…"
    )
    report = EvalRunner(agent_obj, suite_obj, config).run()
    _print_report(report, highlight_metric=metric)

    if output is not None:
        output.write_text(report.model_dump_json(indent=2), encoding="utf-8")
        console.print(f"\n[green]Wrote report to {output}[/green]")


@app.command()
def report(
    input: Path = typer.Option(..., "--input", help="JSON report from `agentbench run`."),
    format: str = typer.Option("table", "--format", help="One of: table, json, markdown."),
) -> None:
    """Re-render an existing report in a different format."""
    if not input.exists():
        console.print(f"[red]error:[/red] {input} not found")
        raise typer.Exit(code=2)
    data = json.loads(input.read_text(encoding="utf-8"))
    rep = EvalReport.model_validate(data)
    if format == "table":
        _print_report(rep)
    elif format == "json":
        console.print_json(data=rep.model_dump(mode="json"))
    elif format == "markdown":
        console.print(_report_as_markdown(rep))
    else:
        console.print(f"[red]error:[/red] unknown format {format}")
        raise typer.Exit(code=2)


def _print_report(report: EvalReport, *, highlight_metric: str = "cost_adjusted_accuracy") -> None:
    table = Table(title=f"Report: {report.suite_name} v{report.suite_version}")
    table.add_column("metric", style="cyan")
    table.add_column("value", justify="right")

    metric_rows: list[tuple[str, str]] = [
        ("accuracy", f"{report.accuracy:.3f}"),
        ("n_correct / n_tasks", f"{report.n_correct} / {report.n_tasks}"),
        ("total_cost_usd", f"${report.total_cost_usd:.4f}"),
        ("avg_cost_per_run", f"${report.avg_cost_per_run:.4f}"),
        ("cost_per_correct_answer", f"${report.cost_per_correct_answer:.4f}"),
        ("p50_latency_ms", f"{report.p50_latency_ms:.1f}"),
        ("p95_latency_ms", f"{report.p95_latency_ms:.1f}"),
        ("p99_latency_ms", f"{report.p99_latency_ms:.1f}"),
        ("cost_adjusted_accuracy", f"{report.cost_adjusted_accuracy:.4f}"),
        ("efficiency_score", f"{report.efficiency_score:.4f}"),
    ]
    for label, value in metric_rows:
        if highlight_metric in label:
            table.add_row(f"[bold yellow]{label}[/bold yellow]", f"[bold yellow]{value}[/bold yellow]")
        else:
            table.add_row(label, value)
    console.print(table)


def _report_as_markdown(report: EvalReport) -> str:
    return (
        f"## AgentBench report — {report.suite_name} v{report.suite_version}\n\n"
        f"Agent: **{report.agent_name}**\n\n"
        f"| metric | value |\n|---|---|\n"
        f"| accuracy | {report.accuracy:.3f} |\n"
        f"| n_correct / n_tasks | {report.n_correct} / {report.n_tasks} |\n"
        f"| total_cost_usd | ${report.total_cost_usd:.4f} |\n"
        f"| avg_cost_per_run | ${report.avg_cost_per_run:.4f} |\n"
        f"| cost_per_correct_answer | ${report.cost_per_correct_answer:.4f} |\n"
        f"| p50_latency_ms | {report.p50_latency_ms:.1f} |\n"
        f"| p95_latency_ms | {report.p95_latency_ms:.1f} |\n"
        f"| p99_latency_ms | {report.p99_latency_ms:.1f} |\n"
        f"| cost_adjusted_accuracy | {report.cost_adjusted_accuracy:.4f} |\n"
        f"| efficiency_score | {report.efficiency_score:.4f} |\n"
    )


@suite_app.command("list")
def suite_list() -> None:
    """List all built-in suites."""
    table = Table(title="Available suites")
    table.add_column("name", style="cyan")
    table.add_column("version")
    table.add_column("n_tasks", justify="right")
    table.add_column("description")
    for s in list_suites():
        table.add_row(s.name, s.version, str(len(s)), s.description)
    console.print(table)


@suite_app.command("preview")
def suite_preview(
    suite: str = typer.Option(..., "--suite"),
    n: int = typer.Option(3, "--n", min=1),
) -> None:
    """Print the first ``n`` tasks of a suite."""
    s = get_suite(suite)
    for i, task in enumerate(s.tasks[:n]):
        console.rule(f"[bold]{task.id}[/bold] ({task.difficulty}, scorer={task.scorer_type})")
        console.print(task.input)
        console.print(f"[dim]expected:[/dim] {task.expected_output}")
        if i < n - 1:
            console.print()


@leaderboard_app.command("submit")
def leaderboard_submit(
    results: Path = typer.Option(..., "--results", help="JSON report from `agentbench run`."),
    name: str = typer.Option(..., "--name"),
    author: str = typer.Option(..., "--author"),
    model: str = typer.Option("unknown", "--model"),
    notes: str | None = typer.Option(None, "--notes"),
) -> None:
    """Submit an eval report to the leaderboard."""
    data = json.loads(results.read_text(encoding="utf-8"))
    rep = EvalReport.model_validate(data)
    entry = LeaderboardEntry.from_report(
        rep,
        agent_name=name,
        author=author,
        model_used=model,
        agentbench_version=__version__,
        notes=notes,
    )
    get_leaderboard().submit(entry)
    console.print(f"[green]Submitted {name} to {rep.suite_name} leaderboard.[/green]")


@leaderboard_app.command("show")
def leaderboard_show(
    suite: str | None = typer.Option(None, "--suite"),
    top: int = typer.Option(10, "--top", min=1),
    metric: str = typer.Option("cost_adjusted_accuracy", "--metric"),
) -> None:
    """Show the leaderboard, sorted by ``metric``."""
    entries = get_leaderboard().list(suite=suite, top=top, metric=metric)
    title = f"Leaderboard — {suite or 'all suites'} (sorted by {metric})"
    table = Table(title=title)
    table.add_column("rank", justify="right")
    table.add_column("agent", style="cyan")
    table.add_column("author")
    table.add_column("suite")
    table.add_column("model")
    table.add_column("accuracy", justify="right")
    table.add_column("cost_usd", justify="right")
    table.add_column("p95 ms", justify="right")
    table.add_column("CAA", justify="right")
    for i, e in enumerate(entries, start=1):
        s = e.score
        table.add_row(
            str(i),
            e.agent_name,
            e.author,
            e.suite_name,
            e.model_used,
            f"{s.accuracy:.3f}",
            f"${s.total_cost_usd:.4f}",
            f"{s.p95_latency_ms:.0f}",
            f"{s.cost_adjusted_accuracy:.3f}",
        )
    console.print(table)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
