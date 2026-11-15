"""Build the member's deterministic reported task set (no model/API calls)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from measurebench_ext.adapter import QUESTION_TYPES, generate_task


def build(out_dir: str, repeats: int = 5) -> list[dict]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    tasks = [
        generate_task(seed, question_type, str(root))
        for question_type in QUESTION_TYPES
        for seed in range(1, repeats + 1)
    ]
    (root / "tasks.jsonl").write_text(
        "".join(json.dumps(task, ensure_ascii=False) + "\n" for task in tasks),
        encoding="utf-8",
    )
    return tasks


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="tasks")
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()
    rows = build(args.out, args.repeats)
    print(f"Generated {len(rows)} task rows across {len(QUESTION_TYPES)} question types in {args.out}")
