"""Shared helpers: save a figure with a layout record, design a task around a mistake, write a task folder."""
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.text

GENERATOR_VERSION = "1.0.0"
DPI = 150


def save_figure(fig, png_path, expected_labels):
    """Draw, record where every text label landed (in PNG pixels), save the PNG. The record feeds validate/."""
    fig.set_dpi(DPI)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    width, height = fig.canvas.get_width_height()
    texts = []
    for t in fig.findobj(matplotlib.text.Text):
        s = t.get_text().strip()
        if not s or not t.get_visible():
            continue
        bb = t.get_window_extent(renderer)
        texts.append({"text": s, "x0": round(bb.x0, 1), "y0": round(height - bb.y1, 1), "x1": round(bb.x1, 1),
                      "y1": round(height - bb.y0, 1), "size": t.get_fontsize()})
    fig.savefig(png_path, dpi=DPI)
    plt.close(fig)
    return {"width": width, "height": height, "texts": texts, "expected_labels": [str(x) for x in expected_labels]}


def within_tolerance(value, spec):
    ref = spec["answer"]
    if isinstance(ref, (list, str)) or isinstance(value, (list, str)):
        return value == ref
    if "tolerance_abs" in spec:
        return abs(value - ref) <= spec["tolerance_abs"]
    if "tolerance_rel" in spec:
        return abs(value - ref) <= spec["tolerance_rel"] * abs(ref)
    return value == ref


def trap_margin(spec):
    """How far the nearest wrong-method answer sits from the right one, in units of the tolerance (bigger = clearer)."""
    ref, worst = spec["answer"], float("inf")
    for v in spec.get("wrong_answers", {}).values():
        if isinstance(ref, (list, str)) or isinstance(v, (list, str)):
            worst = min(worst, 0.0 if v == ref else 10.0)
            continue
        tol = spec.get("tolerance_abs", spec.get("tolerance_rel", 0) * abs(ref)) or 0.5
        worst = min(worst, abs(v - ref) / tol)
    return worst


def design(make, seed, level, tries=60, enough=6, **kw):
    """Mistake-first design: try many candidate data sets from this seed and keep the one whose wrong-method answers
    are all clearly wrong (far outside the tolerance) while the task stays valid. Deterministic for a given seed."""
    best, best_score, found, k = None, -1.0, 0, -1
    assert tries <= 100_000, "seed blocks are 100,000 candidates wide"
    for k in range(tries):
        spec = make(seed * 100_000 + k, level, **kw)    # each seed owns its own block of candidates: no two seeds share one
        if spec is None or not spec.get("uniqueness", {"ok": True})["ok"]:
            continue
        score = trap_margin(spec)
        found += 1
        if score > best_score:
            best, best_score = spec, score
        if found >= enough:                              # deterministic early stop: best of the first `enough` valid designs
            break
    if best is None:
        raise ValueError(f"no valid design for seed {seed} level {level}")
    best["seed"], best["design_tries"], best["trap_margin"] = seed, k + 1, round(best_score, 2)
    return best


def task_record(spec, task_id, image_rel, data_rel, checks):
    rec = {"task_id": task_id, "image": image_rel, "question": spec["question"], "answer": spec["answer"],
           "answer_type": spec["answer_type"], "question_type": spec["question_type"], "family": spec["family"],
           "level": spec["level"], "seed": spec["seed"], "generator_version": GENERATOR_VERSION, "data": data_rel,
           "target_mistake": spec.get("target_mistake", ""), "wrong_answers": spec.get("wrong_answers", {}),
           "references": spec["references"], "checks": checks}
    for k in ("tolerance_rel", "tolerance_abs", "options"):
        if k in spec:
            rec[k] = spec[k]
    return rec


def write_tasks(task_dir, records):
    os.makedirs(task_dir, exist_ok=True)
    with open(os.path.join(task_dir, "tasks.jsonl"), "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
