from __future__ import annotations

import argparse
import json
from pathlib import Path

from generators.finance_reconciliation.adapter import validate_task


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a handoff tasks.jsonl and its source images/data.")
    parser.add_argument("--tasks", default="tasks", help="Task folder containing tasks.jsonl, images/, and data/")
    args = parser.parse_args()
    root = Path(args.tasks)
    records = [json.loads(line) for line in (root / "tasks.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    failed = []
    for task in records:
        result = validate_task(task, str(root))
        print(f"{task['task_id']}: {'PASS' if result['passed'] else 'FAIL'}")
        if not result["passed"]:
            failed.append({"task_id": task["task_id"], **result})
    report = {"n_tasks": len(records), "n_valid": len(records) - len(failed), "failures": failed}
    (root / "validation_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Validated {report['n_valid']}/{report['n_tasks']} tasks.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
