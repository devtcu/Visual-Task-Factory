"""Standard handoff interface for the devtcu pipeline (Brain Connections: brain-network resilience tasks).

It wraps the generator's own functions (connectome.make via common.design, connectome.render, the checks in
validate/devtcu); nothing here changes how a task is designed, drawn or checked. Paths are relative to out_dir and
every random choice is seeded from `seed`, so the same seed and question type give the same image, question and answer.

Question types are named <question>_L<level>: the question (redundant_edge, min_edge_cut, critical_count,
delay_after_failure) and the difficulty level (1 plain lines ... 6 connectogram); see connectome.py's docstring."""
import json
import math
import os

from validate.devtcu import checks
from . import common, connectome

GENERATOR_VERSION = "devtcu-1.1"
QUESTION_TYPES = [f"{q}_L{lv}" for q in connectome.QUESTION_TYPES for lv in connectome.LEVELS_FOR[q]]
DEFAULT_TYPE = "critical_count_L6"


def _split(question_type):
    base, level = question_type.rsplit("_L", 1)
    return base, int(level)


def _clean(o):
    """JSON without Infinity: an unreachable distance is written as the string 'unreachable'."""
    if isinstance(o, float) and math.isinf(o):
        return "unreachable"
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    return o


def generate_task(seed: int, question_type: str | None = None, out_dir: str = ".") -> dict:
    """Deterministic. Writes <out_dir>/images/<task_id>.png and <out_dir>/data/<task_id>.json; returns the task
    record. Raises ValueError when no layout for this seed passes the generator's rules (try another seed)."""
    question_type = question_type or DEFAULT_TYPE
    if question_type not in QUESTION_TYPES:
        raise ValueError(f"unknown question_type {question_type!r}; one of {QUESTION_TYPES}")
    base, level = _split(question_type)
    spec = common.design(connectome.make, seed, level, tries=connectome.DESIGN_TRIES, qtype=base)
    task_id = f"connectome_{question_type}_s{seed}"
    image_rel, data_rel = f"images/{task_id}.png", f"data/{task_id}.json"
    os.makedirs(os.path.join(out_dir, "images"), exist_ok=True)
    os.makedirs(os.path.join(out_dir, "data"), exist_ok=True)
    layout = connectome.render(spec, os.path.join(out_dir, image_rel))
    with open(os.path.join(out_dir, data_rel), "w", encoding="utf-8") as f:
        json.dump(_clean({"data": spec["data"], "layout": layout, "uniqueness": spec["uniqueness"],
                          "facts": spec.get("facts", {}), "level": level, "trap_margin": spec.get("trap_margin")}), f, indent=1)
    rec = common.task_record(spec, task_id, image_rel, data_rel, [])
    rec.update({"generator_version": GENERATOR_VERSION, "question_type": question_type, "level": level})
    rec["checks"] = validate_task(rec, out_dir)
    return rec


def validate_task(task: dict, out_dir: str = ".") -> dict:
    """Runs this member's automatic checks on a written task. Returns {"passed": bool, "checks": {name: bool},
    "details": {name: str}}: answer recomputed by a second solver, answer unique, every predicted wrong answer scored
    wrong, labels present / legible / inked, and the pixel check that drawn lines, arrowheads and bars match the data."""
    with open(os.path.join(out_dir, task["data"]), encoding="utf-8") as f:
        stored = json.load(f)
    base, _ = _split(task["question_type"])
    spec = {**task, "question_type": base, "data": stored["data"], "uniqueness": stored["uniqueness"]}
    results = checks.run_all(spec, connectome, stored["layout"], os.path.join(out_dir, task["image"]))
    return {"passed": checks.all_pass(results), "checks": {c["name"]: bool(c["pass"]) for c in results},
            "details": {c["name"]: c["detail"] for c in results}}
