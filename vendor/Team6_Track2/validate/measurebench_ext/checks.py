"""Validate MeasureBench data, answers and the pixels a solver receives.

The meniscus check reads the drawn tick marks and liquid boundary from the PNG.
It deliberately does not reuse the renderer's volume-to-height calibration.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import tempfile

import matplotlib
import numpy as np
from PIL import Image


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rgb(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("RGB"))


def _color(hex_color: str) -> np.ndarray:
    return np.array([int(hex_color[i:i + 2], 16) for i in (1, 3, 5)])


def _matches(pixels: np.ndarray, color: np.ndarray, tolerance: int = 28) -> np.ndarray:
    return np.max(np.abs(pixels.astype(np.int16) - color), axis=-1) <= tolerance


def _groups(indices: np.ndarray) -> list[float]:
    if len(indices) == 0:
        return []
    groups = np.split(indices, np.where(np.diff(indices) > 2)[0] + 1)
    return [float(np.mean(group)) for group in groups]


def _meniscus_from_pixels(pixels: np.ndarray, style: str) -> tuple[float, int]:
    """Read the PNG using its 0 and 100 mL ticks, independently of data geometry."""
    height, width = pixels.shape[:2]
    # The fixed rendering canvas places the cylinder at axes [.25,.08,.50,.82].
    # Inspect the printed ticks, then use their observed endpoints as calibration.
    tick_x = int(round(width * (.25 + .50 * 3.3 / 5)))
    lo, hi = int(height * .17), int(height * .85)
    ink = _color("#e2eaeb" if style == "navy_bench" else
                 ("#303a39" if style == "ivory_lab" else "#26333b"))
    tick_rows = np.where(_matches(pixels[lo:hi, tick_x - 1:tick_x + 2], ink).any(axis=1))[0] + lo
    tick_centers = _groups(tick_rows)
    if len(tick_centers) != 21:
        raise ValueError(f"Expected 21 visible cylinder ticks, found {len(tick_centers)}")
    center_x = width // 2
    liquid_rows = np.where(_matches(pixels[lo:hi, center_x - 2:center_x + 3],
                                   _color("#648d94")).any(axis=1))[0] + lo
    if not len(liquid_rows) or len(liquid_rows) > 12:
        raise ValueError("Could not isolate the visible meniscus bottom")
    liquid_y = float(np.median(liquid_rows))
    full_y, zero_y = tick_centers[0], tick_centers[-1]
    return 100.0 * (zero_y - liquid_y) / (zero_y - full_y), len(tick_centers)


def _gauge_from_pixels(pixels: np.ndarray, geometry: dict) -> float:
    """Find the colored needle tip and read its angle against the 0..10 scale."""
    cx, cy = geometry["center_px"]
    radius = geometry["unit_radius_px"]
    height, width = pixels.shape[:2]
    x0, x1 = max(0, int(cx - radius)), min(width, int(cx + radius) + 1)
    y0, y1 = max(0, int(cy - radius)), min(height, int(cy + radius) + 1)
    yy, xx = np.mgrid[y0:y1, x0:x1]
    distances = np.hypot(xx - cx, yy - cy)
    colored = _matches(pixels[y0:y1, x0:x1], _color(geometry["needle_color"]))
    mask = colored & (distances > .60 * radius) & (distances < .86 * radius)
    if mask.sum() < 3:
        raise ValueError("Could not find the visible gauge needle")
    farthest = float(distances[mask].max())
    tip = mask & (distances >= farthest - 2.5)
    tx, ty = float(xx[tip].mean()), float(yy[tip].mean())
    angle = math.degrees(math.atan2(cy - ty, tx - cx))
    return ((225.0 - angle) % 360.0) * 10.0 / 270.0


def _recompute(data: dict) -> object:
    values, qtype = data["values"], data["base_question_type"]
    if qtype == "one_tick_counterfactual":
        pair = data["pair_components"]
        return round(pair["value_b"] - pair["value_a"], 1)
    if qtype == "comparison":
        return data["instrument_ids"][0 if values[0] > values[1] else 1]
    if qtype == "difference":
        return round(abs(values[0] - values[1]), 1)
    return values[0]


def _rerender_matches(data: dict, root: Path) -> bool:
    from generators.measurebench_ext.cli import GENERATORS
    from generators.measurebench_ext.adapter import _combine_pair
    with tempfile.TemporaryDirectory(prefix="measurebench-render-") as temporary:
        out = Path(temporary)
        with matplotlib.rc_context(matplotlib.rcParamsDefault):
            matplotlib.rcParams["font.family"] = "DejaVu Sans"
            a = out / "a.png"
            GENERATORS[data["generator"]](data["values"], data["style"], data["difficulty"],
                                          a, data["instrument_ids"])
            pair = data.get("pair_components")
            if pair:
                b, composite = out / "b.png", out / "composite.png"
                GENERATORS[data["generator"]]([pair["value_b"]], data["style"], data["difficulty"],
                                              b, data["instrument_ids"])
                _combine_pair(a, b, composite)
                return (_hash(a) == _hash(root / pair["image_a"])
                        and _hash(b) == _hash(root / pair["image_b"])
                        and _hash(composite) == _hash(root / data["image"]))
            return _hash(a) == _hash(root / data["image"])


def validate(task: dict, out_dir: str = ".") -> dict:
    root = Path(out_dir)
    checks: dict[str, bool | str] = {}
    measurements: dict[str, object] = {}
    try:
        data_path, image_path = root / task["data"], root / task["image"]
        data = json.loads(data_path.read_text(encoding="utf-8"))
        pixels = _rgb(image_path)
        checks["data_exists"] = data_path.is_file()
        checks["image_hash_matches"] = _hash(image_path) == data["image_sha256"]
        checks["image_decodes_and_is_legible_size"] = bool(
            pixels.shape[1] >= 700 and pixels.shape[0] >= 300 and image_path.stat().st_size > 5000)
        checks["task_data_identity_matches"] = all(
            task.get(key) == data.get(key) for key in
            ("task_id", "question", "image", "seed", "generator_version", "question_type", "answer_type"))
        from generators.measurebench_ext.cli import _samples
        checks["generator_seed_values_match"] = (
            _samples(data["generator"], data["seed"], data["difficulty"]) == data["values"])
        checks["answer_recomputed"] = _recompute(data) == task["answer"] == data["answer"]
        checks["image_rerender_matches_saved_data"] = _rerender_matches(data, root)
        if task["answer_type"] == "number":
            tolerance = task.get("tolerance_abs")
            checks["question_states_tolerance_and_unit"] = bool(
                isinstance(tolerance, (int, float)) and tolerance > 0
                and tolerance == data.get("tolerance_abs")
                and f"{tolerance:g}" in task["question"] and data["unit"] in task["question"])
        elif task["answer_type"] == "integer":
            checks["question_states_mark_resolution"] = "nearest 5 mL graduation" in task["question"]
        else:
            checks["question_states_answer_format"] = "gauge ID" in task["question"]
        kind = data["generator"]
        if kind == "meniscus":
            drawn, count = _meniscus_from_pixels(pixels, data["style"])
            measurements["visible_volume_ml"] = round(drawn, 4)
            checks["printed_scale_has_21_ticks"] = count == 21
            checks["meniscus_pixels_match_reference"] = abs(drawn - data["values"][0]) <= .5
            checks["visible_nearest_graduation_matches_answer"] = round(drawn / 5) * 5 == task["answer"]
        elif kind in ("analog_dial", "composite_panel"):
            pair = data.get("pair_components")
            if pair:
                a = _gauge_from_pixels(_rgb(root / pair["image_a"]), data["geometry"][0])
                b = _gauge_from_pixels(_rgb(root / pair["image_b"]), pair["geometry_b"][0])
                measurements["visible_readings_bar"] = [round(a, 4), round(b, 4)]
                checks["both_needle_pixels_match_values"] = (
                    abs(a - pair["value_a"]) < .06 and abs(b - pair["value_b"]) < .06)
                checks["signed_change_matches_visible_needles"] = abs((b - a) - task["answer"]) < .08
                checks["pair_data_matches_components"] = (
                    pair["value_a"] == data["values"][0]
                    and round(pair["value_b"] - pair["value_a"], 1) == pair["delta"]
                    and _hash(root / pair["image_a"]) == pair["image_a_sha256"]
                    and _hash(root / pair["image_b"]) == pair["image_b_sha256"])
            else:
                observed = [_gauge_from_pixels(pixels, g) for g in data["geometry"]]
                measurements["visible_readings_bar"] = [round(value, 4) for value in observed]
                checks["needle_pixels_match_values"] = all(
                    abs(actual - reference) < .06 for actual, reference in zip(observed, data["values"]))
        elif kind == "vernier":
            checks["jaw_geometry_matches_structured_value"] = (
                abs(data["geometry"][0]["jaw_position"] - .8 - data["values"][0]) < 1e-7)
    except Exception as exc:
        checks["validation_exception"] = f"{type(exc).__name__}: {exc}"
    return {"passed": all(value is True for value in checks.values()),
            "checks": checks, "measurements": measurements}
