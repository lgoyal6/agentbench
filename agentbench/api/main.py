"""FastAPI app.

Endpoints
---------

* ``GET  /health`` — liveness check.
* ``POST /run`` — kick off an async eval run.
* ``GET  /run/{run_id}`` — status + partial / final report.
* ``GET  /leaderboard`` — top entries per suite.
"""

from __future__ import annotations

import asyncio
import importlib
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException

from agentbench import __version__
from agentbench.api.schemas import (
    LeaderboardResponse,
    RunCreatedResponse,
    RunRequest,
    RunStatusResponse,
)
from agentbench.exceptions import SuiteLoadError
from agentbench.leaderboard import get_leaderboard
from agentbench.runner import EvalReport, EvalRunner
from agentbench.suites import get_suite

app = FastAPI(title="AgentBench", version=__version__)

_runs: dict[str, dict[str, Any]] = {}
_run_lock = asyncio.Lock()


def _resolve_agent(path: str) -> Any:
    """Resolve a dotted import path like ``my_pkg.my_module:my_agent``."""
    if ":" in path:
        module_path, attr = path.split(":", 1)
    elif "." in path:
        module_path, attr = path.rsplit(".", 1)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid agent path '{path}'. Expected 'module:attr' or 'module.attr'.",
        )
    try:
        module = importlib.import_module(module_path)
    except ImportError as exc:
        raise HTTPException(status_code=400, detail=f"Cannot import {module_path}: {exc}") from exc
    if not hasattr(module, attr):
        raise HTTPException(status_code=400, detail=f"{module_path} has no attribute {attr}")
    return getattr(module, attr)


async def _execute_run(run_id: str, request: RunRequest) -> None:
    state = _runs[run_id]
    state["status"] = "running"
    try:
        agent = _resolve_agent(request.agent_path)
        try:
            suite = get_suite(request.suite)
        except SuiteLoadError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        runner = EvalRunner(agent, suite, request.config, agent_name=request.agent_name)
        report: EvalReport = await runner.arun()
        state["status"] = "complete"
        state["report"] = report
        state["progress"] = 1.0
    except Exception as exc:
        state["status"] = "failed"
        state["error"] = f"{type(exc).__name__}: {exc}"


_background_tasks: set[asyncio.Task[None]] = set()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@app.post("/run", response_model=RunCreatedResponse)
async def create_run(request: RunRequest) -> RunCreatedResponse:
    run_id = str(uuid.uuid4())
    async with _run_lock:
        _runs[run_id] = {
            "status": "pending",
            "report": None,
            "error": None,
            "progress": 0.0,
        }
    task = asyncio.create_task(_execute_run(run_id, request))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return RunCreatedResponse(run_id=run_id, status="pending")


@app.get("/run/{run_id}", response_model=RunStatusResponse)
async def get_run(run_id: str) -> RunStatusResponse:
    state = _runs.get(run_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return RunStatusResponse(
        run_id=run_id,
        status=state["status"],
        error=state.get("error"),
        report=state.get("report"),
        progress=state.get("progress", 0.0),
    )


@app.get("/leaderboard", response_model=LeaderboardResponse)
async def list_leaderboard(suite: str | None = None, top: int = 10) -> LeaderboardResponse:
    lb = get_leaderboard()
    entries = lb.list(suite=suite, top=top)
    return LeaderboardResponse(suite=suite, entries=entries)
