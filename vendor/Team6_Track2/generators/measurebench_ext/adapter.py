"""Thin Track 2 adapter for the MeasureBench extension generators."""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

import matplotlib
import matplotlib.image as mpimg
import matplotlib.pyplot as plt

from .cli import (
    DIFFICULTIES,
    GENERATORS,
    PALETTES,
    STYLES,
    TYPES,
    VERSION,
    _questions,
    _samples,
    _style,
)

GENERATOR_VERSION = "measurebench_ext-2.0"

QUESTION_MAP = {
    "analog_dial_single_reading": ("analog_dial", "single_reading"),
    "analog_dial_precision": ("analog_dial", "precision"),
    "analog_dial_one_tick_counterfactual": ("analog_dial", "one_tick_counterfactual"),
    "vernier_single_reading": ("vernier", "single_reading"),
    "vernier_precision": ("vernier", "precision"),
    "meniscus_single_reading": ("meniscus", "single_reading"),
    "meniscus_meniscus_convention": ("meniscus", "meniscus_convention"),
    "composite_panel_single_reading": ("composite_panel", "single_reading"),
    "composite_panel_comparison": ("composite_panel", "comparison"),
    "composite_panel_difference": ("composite_panel", "difference"),
}
# Legacy names remain accepted, but wording-only aliases are not advertised as
# separate reasoning capabilities by the merged factory.
QUESTION_ALIASES = {
    "analog_dial_precision": "analog_dial_single_reading",
    "vernier_precision": "vernier_single_reading",
    "meniscus_meniscus_convention": "meniscus_single_reading",
}
QUESTION_TYPES = [name for name in QUESTION_MAP if name not in QUESTION_ALIASES]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _instrument_ids(kind: str) -> list[str]:
    if kind == "composite_panel":
        return ["P-101", "P-102"]
    if kind == "vernier":
        return ["VC-07"]
    if kind == "meniscus":
        return ["LG-22"]
    return ["PG-104"]


def _pair_delta(seed: int, value: float) -> float:
    """Choose a signed, seed-dependent change of one to five minor divisions."""
    steps = [step for step in (-5, -4, -3, -2, -1, 1, 2, 3, 4, 5)
             if 0.4 <= value + step * 0.2 <= 9.6]
    return round(random.Random(f"measurebench-pair-v2:{seed}").choice(steps) * 0.2, 1)


def _tolerance(kind: str, answer_type: str) -> float | None:
    if answer_type != "number":
        return None
    return {"analog_dial": 0.099, "vernier": 0.0049, "meniscus": 2.49, "composite_panel": 0.099}[kind]


def _question(base: str, kind: str, qtype: str, answer_type: str, unit: str, tol: float | None) -> str:
    ids = _instrument_ids(kind)
    if qtype == "one_tick_counterfactual":
        base = (f"Compare the two views of instrument {ids[0]}. Image A is the left gauge and Image B is the right gauge. "
                "Calculate the signed pressure change from A to B: reading B minus reading A. "
                "A decrease must be reported as a negative number.")
    if qtype == "comparison":
        return f"{base} Answer with only the gauge ID ({ids[0]} or {ids[1]}), no explanation."
    if answer_type == "integer":
        return f"{base} Read the bottom of the concave meniscus at the nearest 5 mL graduation. Give the integer mark with mL; do not interpolate between marks."
    if tol is not None:
        return f"{base} Allowed absolute error: ±{tol:g} {unit}. Answer with a number and the unit."
    return base


def _combine_pair(left: Path, right: Path, output: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14.4, 5.6), dpi=170, facecolor="#132432")
    for axis, path, label in zip(axes, (left, right), ("IMAGE A", "IMAGE B")):
        axis.imshow(mpimg.imread(path))
        axis.set_title(label, fontsize=11, color="white", weight="bold", pad=5)
        axis.axis("off")
    fig.tight_layout(pad=0.25)
    fig.savefig(output, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)


def generate_task(seed: int, question_type: str | None = None, out_dir: str = ".") -> dict:
    """Generate one deterministic task using the original procedural renderer."""
    with matplotlib.rc_context(matplotlib.rcParamsDefault):
        matplotlib.rcParams["font.family"] = "DejaVu Sans"
        return _generate_task(seed, question_type, out_dir)


def _generate_task(seed: int, question_type: str | None, out_dir: str) -> dict:
    if question_type is None:
        question_type = QUESTION_TYPES[seed % len(QUESTION_TYPES)]
    if question_type not in QUESTION_MAP:
        raise ValueError(f"Unknown question_type {question_type!r}; expected one of {QUESTION_TYPES}")
    if not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a non-negative integer")

    kind, qtype = QUESTION_MAP[question_type]
    root = Path(out_dir)
    images_dir, data_dir = root / "images", root / "data"
    images_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    difficulty = DIFFICULTIES[seed % len(DIFFICULTIES)]
    style = _style(seed)
    values = _samples(kind, seed, difficulty)
    ids = _instrument_ids(kind)
    scene_key = f"measurebench_{kind}_{seed:04d}"
    task_id = f"measurebench_ext_{kind}_{qtype}_{seed:04d}"

    image_a_rel = Path("images") / f"{scene_key}.png"
    image_a = root / image_a_rel
    geometry_a = GENERATORS[kind](values, style, difficulty, image_a, ids)
    pair_components = None
    if qtype == "one_tick_counterfactual":
        delta = _pair_delta(seed, values[0])
        twin_value = round(values[0] + delta, 1)
        twin_rel = Path("images") / f"{scene_key}_view_b.png"
        twin_path = root / twin_rel
        geometry_b = GENERATORS[kind]([twin_value], style, difficulty, twin_path, ids)
        final_rel = Path("images") / f"{task_id}.png"
        _combine_pair(image_a, twin_path, root / final_rel)
        pair_components = {
            "image_a": image_a_rel.as_posix(),
            "image_a_sha256": _sha256(image_a),
            "image_b": twin_rel.as_posix(),
            "image_b_sha256": _sha256(twin_path),
            "value_a": values[0],
            "value_b": twin_value,
            "geometry_b": geometry_b,
            "delta": delta,
        }
        image_rel = final_rel
    else:
        image_rel = image_a_rel

    question_rows = _questions(kind, ids, values, difficulty)
    if qtype == "one_tick_counterfactual":
        answer, unit = round(twin_value - values[0], 1), "bar"
        base_question = ""
    else:
        match = next((row for row in question_rows if row[3] == qtype), None)
        if match is None:
            raise ValueError(f"No original question template for {kind}/{qtype}")
        base_question, answer, unit, _ = match

    answer_type = "label" if qtype == "comparison" else ("integer" if kind == "meniscus" else "number")
    tolerance_abs = _tolerance(kind, answer_type)
    question = _question(base_question, kind, qtype, answer_type, unit, tolerance_abs)
    answer_dict = {"value": answer, "unit": unit}
    if tolerance_abs is not None:
        answer_dict["tolerance_abs"] = tolerance_abs

    data_rel = Path("data") / f"{task_id}.json"
    data = {
        "task_id": task_id,
        "seed": seed,
        "generator_version": GENERATOR_VERSION,
        "source_generator_version": VERSION,
        "generator": kind,
        "question_type": question_type,
        "base_question_type": qtype,
        "difficulty": difficulty,
        "style": style,
        "instrument_ids": ids,
        "values": values,
        "unit": unit,
        "answer": answer,
        "answer_type": answer_type,
        "tolerance_abs": tolerance_abs,
        "question": question,
        "image": image_rel.as_posix(),
        "image_sha256": _sha256(root / image_rel),
        "geometry": geometry_a,
        "pair_components": pair_components,
    }
    (root / data_rel).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    task = {
        "task_id": task_id,
        "image": image_rel.as_posix(),
        "question": question,
        "answer": answer,
        "answer_type": answer_type,
        "seed": seed,
        "generator_version": GENERATOR_VERSION,
        "question_type": question_type,
        "data": data_rel.as_posix(),
    }
    if tolerance_abs is not None:
        task["tolerance_abs"] = tolerance_abs
    task["checks"] = validate_task(task, str(root))
    return task


def validate_task(task: dict, out_dir: str = ".") -> dict:
    """Delegate all checks to the required root-level validation package."""
    import sys
    project_root = str(Path(__file__).resolve().parents[2])
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from validate.measurebench_ext.checks import validate
    return validate(task, out_dir)
