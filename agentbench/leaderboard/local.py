"""Local JSON-backed leaderboard."""

from __future__ import annotations

import json
from pathlib import Path

from agentbench.config import get_settings
from agentbench.exceptions import LeaderboardError
from agentbench.leaderboard.schema import LeaderboardEntry


class LocalLeaderboard:
    """File-backed leaderboard at ``~/.agentbench/leaderboard.json``."""

    DEFAULT_METRIC = "cost_adjusted_accuracy"

    def __init__(self, path: Path | None = None) -> None:
        if path is None:
            settings = get_settings()
            path = settings.ensure_data_dir() / "leaderboard.json"
        self.path = path

    def _load_all(self) -> list[LeaderboardEntry]:
        if not self.path.exists():
            return []
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise LeaderboardError(f"Leaderboard file corrupted at {self.path}: {exc}") from exc
        return [LeaderboardEntry.model_validate(e) for e in raw]

    def _save_all(self, entries: list[LeaderboardEntry]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps([e.model_dump() for e in entries], indent=2, default=str),
            encoding="utf-8",
        )

    def submit(self, entry: LeaderboardEntry) -> LeaderboardEntry:
        entries = self._load_all()
        entries.append(entry)
        self._save_all(entries)
        return entry

    def list(
        self,
        *,
        suite: str | None = None,
        top: int | None = None,
        metric: str = DEFAULT_METRIC,
    ) -> list[LeaderboardEntry]:
        entries = self._load_all()
        if suite is not None:
            entries = [e for e in entries if e.suite_name == suite]
        entries.sort(key=lambda e: getattr(e.score, metric), reverse=True)
        if top is not None:
            entries = entries[:top]
        return entries

    def clear(self) -> None:
        if self.path.exists():
            self.path.unlink()
