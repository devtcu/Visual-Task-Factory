"""Offline regressions for the repaired reconstruction pipeline (no model calls)."""
from __future__ import annotations
import copy
import hashlib
import tempfile
from pathlib import Path
from PIL import Image
from generators.visual_reconstruction.adapter import generate_task, validate_task
from .scoring import score_answer


def _hashes(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file()}


def main():
    with tempfile.TemporaryDirectory(prefix="reconstruction_selfcheck_") as tmp:
        root = Path(tmp)
        first = generate_task(20261114, out_dir=str(root / "first"))
        second = generate_task(20261114, out_dir=str(root / "second"))
        fresh = generate_task(20261115, out_dir=str(root / "fresh"))
        assert first["checks"]["passed"] and second["checks"]["passed"] and fresh["checks"]["passed"]
        assert first == second and _hashes(root / "first") == _hashes(root / "second")
        assert first["answer"] != fresh["answer"]
        assert not score_answer(fresh, first["answer"])["correct"], "a reused answer must not solve the fresh seed"
        assert score_answer(first, first["answer"])["correct"]
        equivalent = copy.deepcopy(first["answer"])
        for row in equivalent:
            if row["undo_reflection"] != "none":
                row["undo_rotation_clockwise"] = (row["undo_rotation_clockwise"] + 180) % 360
                row["undo_reflection"] = "vertical" if row["undo_reflection"] == "horizontal" else "horizontal"
        assert score_answer(first, list(reversed(equivalent)))["correct"]
        boundary = copy.deepcopy(first["answer"])
        boundary[0]["center"][0] += 30
        assert score_answer(first, boundary)["correct"]
        boundary[0]["center"][0] += .01
        assert not score_answer(first, boundary)["correct"]
        duplicate = copy.deepcopy(first["answer"])
        duplicate[1]["candidate_id"] = duplicate[0]["candidate_id"]
        assert not score_answer(first, duplicate)["correct"]
        malformed = copy.deepcopy(first["answer"])
        malformed[0]["center"][0] = float("nan")
        assert not score_answer(first, malformed)["correct"]
        wrong = copy.deepcopy(first)
        wrong["answer"][0]["candidate_id"] = "Z"
        assert not validate_task(wrong, str(root / "first"))["passed"]
        # Actual delivered-image corruption must fail independently of saved flags.
        cid = first["answer"][0]["candidate_id"]
        patch = root / "first" / "images" / f"{first['task_id']}_patches" / f"{cid}.png"
        with Image.open(patch) as im:
            altered = im.convert("RGBA")
        pixel = altered.getpixel((0, 0))
        altered.putpixel((0, 0), ((pixel[0] + 1) % 256, *pixel[1:]))
        altered.save(patch)
        assert not validate_task(first, str(root / "first"))["passed"]
    print("PASS: source/pixel validation, same-seed file determinism, seed variation, oracle scoring,")
    print("equivalent transforms, 30px boundary, duplicate/NaN rejection, and corrupted candidate/reference detection.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

