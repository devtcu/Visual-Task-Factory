"""Task-specific scoring for spatial reconstruction.

A task passes only when all five unique hole placements pass. Coordinate tolerance
is applied in original-photo pixels and equivalent dihedral transforms are equal.
"""
from __future__ import annotations
import math
from typing import Any


def transform_signature(rotation, reflection):
    """Canonical action on an asymmetric 3x3 grid, rotation THEN reflection."""
    if isinstance(rotation, bool):
        raise ValueError("rotation must be a quarter-turn angle")
    try:
        r = int(rotation)
    except (ValueError, TypeError, OverflowError):
        raise ValueError("invalid rotation") from None
    if str(rotation).strip() not in ("0", "90", "180", "270", "0.0", "90.0", "180.0", "270.0"):
        raise ValueError("rotation must be 0, 90, 180 or 270")
    ref = str(reflection).strip().lower()
    if ref not in ("none", "horizontal", "vertical"):
        raise ValueError("invalid reflection")
    grid = [[0, 1, 2], [3, 4, 5], [6, 7, 8]]
    for _ in range(r // 90):
        grid = [list(row) for row in zip(*grid[::-1])]
    if ref == "horizontal":
        grid = [row[::-1] for row in grid]
    elif ref == "vertical":
        grid = grid[::-1]
    return tuple(value for row in grid for value in row)


def _hole_id(value):
    if isinstance(value, bool):
        raise ValueError("invalid hole ID")
    if isinstance(value, str):
        value = value.strip().upper().removeprefix("H")
    n = int(value)
    if float(value) != n:
        raise ValueError("invalid hole ID")
    return n


def score_answer(task: dict, parsed: Any, task_root=None) -> dict:
    """Return correct, fractional score and per-hole details for the central evaluator."""
    if isinstance(parsed, dict):
        parsed = parsed.get("placements", parsed.get("answer"))
    truth = {int(r["hole_id"]): r for r in task["answer"]}
    expected_n = len(truth)
    tolerance = float(task.get("scoring", {}).get("center_tolerance_px", 30))
    if not isinstance(parsed, list) or len(parsed) != expected_n:
        return {"correct": False, "score": 0.0, "details": [], "error": f"expected {expected_n} placements"}
    rows = {}
    used = set()
    try:
        for row in parsed:
            if not isinstance(row, dict):
                raise ValueError("placement must be an object")
            hid = _hole_id(row.get("hole_id"))
            cid = str(row.get("candidate_id", "")).strip().upper()
            if hid not in truth or hid in rows or not cid or cid in used:
                raise ValueError("unknown or duplicate hole/candidate ID")
            rows[hid] = row
            used.add(cid)
    except (TypeError, ValueError, OverflowError) as exc:
        return {"correct": False, "score": 0.0, "details": [], "error": str(exc)}
    details = []
    for hid, target in sorted(truth.items()):
        row = rows[hid]
        detail = {"hole_id": hid, "candidate_correct": False, "transform_correct": False, "center_correct": False}
        try:
            center = row["center"]
            if not isinstance(center, list) or len(center) != 2 or any(isinstance(v, bool) for v in center):
                raise ValueError("center must be two finite numbers")
            center = [float(v) for v in center]
            if not all(math.isfinite(v) for v in center):
                raise ValueError("center must be finite")
            error = math.dist(center, target["center"])
            detail.update(candidate_correct=str(row["candidate_id"]).strip().upper() == target["candidate_id"],
                          transform_correct=transform_signature(row["undo_rotation_clockwise"], row["undo_reflection"]) ==
                                            transform_signature(target["undo_rotation_clockwise"], target["undo_reflection"]),
                          center_correct=error <= tolerance, center_error_px=error)
        except (KeyError, ValueError, TypeError, OverflowError) as exc:
            detail["error"] = str(exc)
        detail["correct"] = all(detail[k] for k in ("candidate_correct", "transform_correct", "center_correct"))
        details.append(detail)
    fraction = sum(d["correct"] for d in details) / expected_n if expected_n else 0.0
    return {"correct": bool(expected_n) and fraction == 1.0, "score": fraction, "details": details}

