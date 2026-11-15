"""Team 6: build, check, reproduce and evaluate seven visual task pipelines."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import shutil
import time

from pipelines import PIPELINES, REFERENCES, adapter_for
from validate.run_validation import validate_record

ROOT = Path(__file__).resolve().parent


def write_json(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def fingerprint(task, folder):
    folder = Path(folder)
    files = sorted(set([task["image"], task["data"], *task.get("images", [])]))
    return {
        "task_id": task["task_id"], "pipeline": task["pipeline"], "seed": task["seed"],
        "question": task["question"], "answer": task["answer"], "answer_type": task["answer_type"],
        "generator_version": task["generator_version"],
        "tolerances": {k: task[k] for k in ("tolerance_abs", "tolerance_rel") if k in task},
        "files": {p: hashlib.sha256((folder / p).read_bytes()).hexdigest() for p in files},
    }


def generate(spec, folder):
    adapter, member, default = adapter_for(spec["pipeline"])
    task = adapter.generate_task(int(spec["seed"]), spec.get("question_type", default), str(folder))
    task.update(pipeline=spec["pipeline"], member=member)
    task.setdefault("references", REFERENCES[spec["pipeline"]])
    if len(task.get("images", [])) > 1 and task["image"] in task["images"]:
        from generators.common import make_overview
        rel = f"images/{task['task_id']}_overview.png"
        make_overview([folder / p for p in task["images"]], folder / rel)
        task["image"] = rel; task["overview_generated"] = True
    task["checks"] = validate_record(task, folder)
    return task


def build(specs, out, name, verify=False):
    started = time.monotonic(); out = Path(out).resolve()
    folder = out / "tasks" / name; folder.mkdir(parents=True, exist_ok=True)
    tasks = []
    for spec in specs:
        task = generate(spec, folder)
        print(f"{task['task_id']}: {'VALID' if task['checks']['passed'] else 'INVALID'}", flush=True)
        if not task["checks"]["passed"]:
            write_json(out / "evidence" / "failed_task.json", task)
            raise RuntimeError(f"Task failed validation: {task['task_id']}: {task['checks']}")
        tasks.append(task)
    if len({t["task_id"] for t in tasks}) != len(tasks):
        raise RuntimeError("Duplicate task IDs")
    working = (folder / "_brain_work").resolve()
    if working.exists() and working.is_relative_to(folder.resolve()):
        shutil.rmtree(working)
    (folder / "tasks.jsonl").write_text("".join(json.dumps(t, ensure_ascii=False) + "\n" for t in tasks), encoding="utf-8")
    write_json(folder / "validation.json", {"passed": True, "n_tasks": len(tasks), "tasks": {t["task_id"]: t["checks"] for t in tasks}})
    fingerprints = {t["task_id"]: fingerprint(t, folder) for t in tasks}
    write_json(out / "evidence" / f"{name}_fingerprints.json", fingerprints)
    if verify:
        expected = json.loads((ROOT / "reported_fingerprints.json").read_text(encoding="utf-8"))
        if fingerprints != expected:
            changed = sorted(k for k in set(fingerprints) | set(expected) if fingerprints.get(k) != expected.get(k))
            raise RuntimeError(f"Reported outputs differ from the submission: {changed}")
        print("REPRODUCTION: every reported image, data file, question and answer matches", flush=True)
    write_json(out / "evidence" / f"{name}_build.json", {"valid": len(tasks), "total": len(tasks), "pipelines": sorted({t["pipeline"] for t in tasks}), "wall_seconds": round(time.monotonic() - started, 3), "python": platform.python_version(), "platform": platform.platform(), "verified_reported": verify})
    return folder, tasks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--build-reported", action="store_true")
    mode.add_argument("--fresh", action="store_true")
    parser.add_argument("--pipeline", "--member", choices=sorted(PIPELINES), default="fiber")
    parser.add_argument("--question-type")
    parser.add_argument("--seed", type=int, default=7001)
    parser.add_argument("--out", default="out")
    parser.add_argument("--verify-reported", action="store_true")
    parser.add_argument("--evaluate", action="store_true", help="Call the selected models using OPENROUTER_API_KEY")
    parser.add_argument("--model", action="append", choices=["anthropic/claude-haiku-5.5", "openai/gpt-6-luna"])
    parser.add_argument("--max-tokens", type=int, default=32768)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--force-eval", action="store_true")
    args = parser.parse_args()
    if args.build_reported:
        specs = json.loads((ROOT / "selection.json").read_text(encoding="utf-8"))["tasks"]
        name = "final"
    else:
        spec = {"pipeline": args.pipeline, "seed": args.seed}
        if args.question_type: spec["question_type"] = args.question_type
        specs = [spec]; name = "fresh"
    folder, tasks = build(specs, args.out, name, args.verify_reported)
    if args.evaluate:
        from eval.run_eval import evaluate
        evaluate(folder, Path(args.out) / "results" / name, models=args.model,
                 max_tokens=args.max_tokens, workers=args.workers, force=args.force_eval)
    print(f"Completed {len(tasks)} tasks across {len({t['pipeline'] for t in tasks})} pipelines", flush=True)


if __name__ == "__main__":
    main()
