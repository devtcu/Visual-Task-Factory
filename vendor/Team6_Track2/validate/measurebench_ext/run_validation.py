"""Run each task through its member-specific checks."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "generators"))
from measurebench_ext.adapter import validate_task  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", default=str(ROOT / "tasks"))
    args = parser.parse_args()
    task_root = Path(args.tasks)
    tasks = [json.loads(line) for line in (task_root / "tasks.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    failures = []
    for task in tasks:
        result = validate_task(task, str(task_root))
        task["checks"] = result
        if not result["passed"]:
            failures.append({"task_id": task["task_id"], "checks": result})
    (task_root / "tasks.jsonl").write_text("".join(json.dumps(task, ensure_ascii=False) + "\n" for task in tasks), encoding="utf-8")
    summary = {"total": len(tasks), "passed": len(tasks) - len(failures), "failed": failures}
    (task_root / "validation_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
