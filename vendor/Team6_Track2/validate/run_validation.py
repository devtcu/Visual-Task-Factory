"""Validate saved records with the exact checks shipped in validate/."""
import argparse
import json
from pathlib import Path
import tempfile

from PIL import Image, ImageChops
from pipelines import adapter_for


def validate_record(task, task_dir):
    task_dir = Path(task_dir)
    adapter, _, _ = adapter_for(task["pipeline"])
    result = adapter.validate_task(task, str(task_dir))
    if not isinstance(result, dict):
        raise TypeError("Validator must return a dictionary")
    details = dict(result.get("checks", {k: v for k, v in result.items() if k != "passed"}))
    details["member_validation"] = result.get("passed") is True
    required = ("task_id", "image", "question", "answer", "answer_type", "seed", "generator_version", "data")
    details["required_fields"] = all(key in task for key in required)
    for key in ("image", "data"):
        path = (task_dir / task[key]).resolve()
        details[f"{key}_path"] = path.is_relative_to(task_dir.resolve()) and path.is_file()
    if task.get("overview_generated"):
        from generators.common import make_overview
        with tempfile.TemporaryDirectory() as tmp:
            expected = Path(tmp) / "overview.png"
            make_overview([task_dir / p for p in task["images"]], expected)
            with Image.open(expected) as a, Image.open(task_dir / task["image"]) as b:
                details["overview_matches_components"] = a.size == b.size and ImageChops.difference(a.convert("RGB"), b.convert("RGB")).getbbox() is None
    # Member checks may include explanatory strings alongside the required boolean verdict.
    base_pass = result.get("passed") is True
    shared = (details["required_fields"] and details["image_path"] and details["data_path"]
              and details.get("overview_matches_components", True))
    return {"passed": bool(base_pass and shared), "checks": details}


def validate_folder(folder):
    folder = Path(folder)
    tasks = [json.loads(line) for line in (folder / "tasks.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    results = {task["task_id"]: validate_record(task, folder) for task in tasks}
    output = {"passed": all(r["passed"] for r in results.values()), "n_tasks": len(tasks), "tasks": results}
    (folder / "validation.json").write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("tasks")
    args = parser.parse_args(); result = validate_folder(args.tasks)
    print(json.dumps({k: v for k, v in result.items() if k != "tasks"}, indent=2))
    raise SystemExit(0 if result["passed"] else 1)
