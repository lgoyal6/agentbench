"""Build the JSON the results page reads.

Reads the committed EvalReport dumps in benchmarks/v0.1.0/ and adds one thing
they do not carry: a Wilson 95% interval on each accuracy. At n = 10 a single
task is ten percentage points, and a run that reports 1.00 without an interval
invites being read as "perfect" rather than "no failures in ten tries".

Runs that contain transport errors are marked void rather than summarised. An
errored call is scored 0.0 and folded into accuracy, so an incomplete run reads
as a low model score, which it is not.

    python3 scripts/make_page_data.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "benchmarks" / "v0.1.0"
OUT = ROOT / "docs" / "data"

Z = 1.959964   # 95%


def wilson(k: int, n: int) -> tuple[float, float]:
    """Interval for k successes in n trials. Never runs past 0 or 1."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    denom = 1 + Z * Z / n
    centre = (p + Z * Z / (2 * n)) / denom
    half = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def main() -> None:
    runs, void = [], []
    for path in sorted(SRC.glob("*.json")):
        d = json.loads(path.read_text())
        errored = [o for o in d["outcomes"] if o.get("error")]
        row = {
            "file": path.name,
            "suite": d["suite_name"],
            "agent": d["agent_name"],
            "n_tasks": d["n_tasks"],
            "n_correct": d["n_correct"],
            "n_errors": d["n_errors"],
            "accuracy": d["accuracy"],
            "total_cost_usd": d["total_cost_usd"],
            "avg_cost_per_run": d["avg_cost_per_run"],
            "cost_per_correct_answer": d["cost_per_correct_answer"],
            "p50_latency_ms": d["p50_latency_ms"],
            "p95_latency_ms": d["p95_latency_ms"],
            "p99_latency_ms": d["p99_latency_ms"],
            "judge_model": d["config"].get("judge_model"),
            "concurrency": d["config"].get("concurrency"),
        }
        if errored:
            # Not a model result. Recorded so the page can say what went wrong
            # without ever printing the accuracy as a score.
            row["error_kind"] = (errored[0].get("error") or "").split(":")[0]
            row["n_errored"] = len(errored)
            void.append(row)
            continue
        lo, hi = wilson(d["n_correct"], d["n_tasks"])
        row["wilson_lo"], row["wilson_hi"] = lo, hi
        row["tasks"] = [
            {
                "task_id": o["task_id"],
                "correct": bool(o["correct"]),
                "cost_usd": o["cost_usd"],
                "latency_ms": o["latency_ms"],
                "total_tokens": o.get("total_tokens"),
            }
            for o in d["outcomes"]
        ]
        runs.append(row)

    payload = {"runs": runs, "void": void, "suite_version": "0.1.0"}
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "runs.json"
    path.write_text(json.dumps(payload, indent=1) + "\n")
    print(f"{path.relative_to(ROOT)}  {path.stat().st_size / 1024:.1f} kB")
    for r in runs:
        print(f"  {r['suite']:<16} {r['n_correct']}/{r['n_tasks']} = {r['accuracy']:.2f} "
              f"[{r['wilson_lo']:.2f}, {r['wilson_hi']:.2f}]  ${r['cost_per_correct_answer']:.5f}/correct")
    for v in void:
        print(f"  VOID {v['suite']:<12} {v['n_errored']}/{v['n_tasks']} calls errored ({v['error_kind']})")


if __name__ == "__main__":
    main()
