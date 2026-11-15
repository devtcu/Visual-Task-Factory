"""Independent source-pixel and placement validation for reconstruction tasks."""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
from PIL import Image, ImageOps
from .scoring import score_answer

CANONICAL_TRANSFORMS = [(r, f) for f in ("none", "horizontal") for r in (0, 90, 180, 270)]


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _same(a, b):
    return a.size == b.size and a.convert("RGBA").tobytes() == b.convert("RGBA").tobytes()


def _undo(piece, rotation, reflection):
    """Independent application of a model's rotation-then-reflection answer."""
    result = piece.rotate(-rotation, expand=True, resample=Image.Resampling.NEAREST)
    if reflection == "horizontal":
        result = ImageOps.mirror(result)
    elif reflection == "vertical":
        result = ImageOps.flip(result)
    return result


def _creation(source_crop, rotation, reflection):
    result = source_crop
    if reflection == "horizontal":
        result = ImageOps.mirror(result)
    elif reflection == "vertical":
        result = ImageOps.flip(result)
    return result.rotate(-rotation, expand=True, resample=Image.Resampling.NEAREST)


def validate_task(task: dict, out_dir: str = ".") -> dict:
    from generators.visual_reconstruction.generate import SOURCE, make_puzzle, make_sheet, overlap
    from generators.visual_reconstruction.adapter import _composite, GENERATOR_VERSION
    root = Path(out_dir)
    checks = {}
    try:
        data = json.loads((root / task["data"]).read_text(encoding="utf8"))
        key = data["ground_truth"]
        with Image.open(SOURCE) as opened:
            original = opened.convert("RGBA")
        checks["source_asset_hash_verified"] = _sha(SOURCE) == data["source_sha256"] == key["source_sha256"]
        checks["source_dimensions_verified"] = original.size == (key["image_width"], key["image_height"]) == (1920, 2560)
        checks["metadata_consistent"] = (task["seed"] == data["seed"] == key["seed"] and
                                         task["generator_version"] == data["generator_version"] == GENERATOR_VERSION and
                                         task["question_type"] == data["question_type"] == "global_spatial_reconstruction")
        regions = sorted(key["missing_regions"], key=lambda r: r["hole_id"])
        boxes = [r["bounding_box"] for r in regions]
        checks["five_unique_labeled_holes"] = [r["hole_id"] for r in regions] == [1, 2, 3, 4, 5]
        checks["valid_crop_geometry"] = all(w == h == 520 and x >= 0 and y >= 0 and
                                            x + w <= original.width and y + h <= original.height
                                            for x, y, w, h in boxes)
        checks["hole_boxes_nonoverlapping"] = all(not overlap(a, b) for i, a in enumerate(boxes) for b in boxes[i + 1:])
        patch_files = data["patch_files"]
        checks["fifteen_unique_candidate_files"] = len(patch_files) == data["num_candidates"] == 15 and len(set(patch_files.values())) == 15
        pieces = {}
        for cid, rel in patch_files.items():
            with Image.open(root / rel) as opened:
                pieces[cid] = opened.convert("RGBA")
        checks["all_candidate_patches_520_square"] = all(p.size == (520, 520) for p in pieces.values())
        # Index EVERY delivered candidate under all eight distinct D4 transforms.
        # Matching actual source pixels determines identity/orientation independently
        # of the generator's stored answer fields or QA booleans.
        pixel_index = {}
        for cid, piece in pieces.items():
            for rotation, reflection in CANONICAL_TRANSFORMS:
                restored = _undo(piece, rotation, reflection)
                digest = hashlib.sha256(restored.tobytes()).hexdigest()
                pixel_index.setdefault(digest, []).append((cid, rotation, reflection))
        derived = []
        matches_by_hole = {}
        for region in regions:
            x, y, w, h = region["bounding_box"]
            target = original.crop((x, y, x + w, y + h))
            matches = pixel_index.get(hashlib.sha256(target.tobytes()).hexdigest(), [])
            matches_by_hole[region["hole_id"]] = matches
            if len(matches) == 1:
                cid, rotation, reflection = matches[0]
                derived.append({"hole_id": region["hole_id"], "center": [x + (w - 1) / 2, y + (h - 1) / 2],
                                "candidate_id": cid, "undo_rotation_clockwise": rotation, "undo_reflection": reflection})
        checks["unique_pixel_verified_candidate_and_orientation_per_hole"] = len(derived) == 5
        if len(derived) == 5:
            reference = {"answer": derived, "scoring": {"center_tolerance_px": 0}}
            checks["answer_independently_recomputed_from_source_pixels"] = score_answer(reference, task["answer"])["correct"]
            checks["ground_truth_centers_match_geometry"] = all(
                math.dist(region["center_xy"], expected["center"]) < 1e-9 for region, expected in zip(regions, derived))
        else:
            checks["answer_independently_recomputed_from_source_pixels"] = False

        # All candidate files, including distractors, must match their declared source crop.
        source_checks = []
        for item in regions:
            x, y, w, h = item["bounding_box"]
            expected = _creation(original.crop((x, y, x + w, y + h)),
                                 item["candidate_creation_rotation_clockwise"], item["candidate_creation_reflection"])
            source_checks.append(_same(expected, pieces[item["segment_id"]]))
        for item in key["distractors"]:
            x, y, w, h = item["source_coordinates"]
            expected = _creation(original.crop((x, y, x + w, y + h)),
                                 item["rotation_applied_clockwise"], item["reflection_applied"])
            source_checks.append(_same(expected, pieces[item["segment_id"]]))
        checks["all_candidates_match_archived_source_data"] = len(source_checks) == 15 and all(source_checks)
        checks["distractors_avoid_missing_regions"] = all(
            not overlap(item["source_coordinates"], box) for item in key["distractors"] for box in boxes)

        with Image.open(root / data["component_images"]["puzzle"]) as opened:
            puzzle = opened.convert("RGB")
        with Image.open(root / data["component_images"]["candidate_sheet"]) as opened:
            sheet = opened.convert("RGB")
        checks["component_hashes_match_data"] = all(
            _sha(root / rel) == data["component_sha256"][name] for name, rel in data["component_images"].items())
        checks["masked_photo_matches_source_geometry_and_labels"] = _same(make_puzzle(original, regions), puzzle)
        order = key["candidate_order"]
        checks["candidate_order_is_complete_permutation"] = len(order) == 15 and set(order) == set(pieces)
        rendered_sheet = make_sheet([{"id": cid, "path": root / patch_files[cid]} for cid in order])
        checks["candidate_sheet_pixels_and_labels_match_data"] = _same(rendered_sheet, sheet)
        restored_original = puzzle.copy()
        for answer in derived:
            region = next(r for r in regions if r["hole_id"] == answer["hole_id"])
            patch = _undo(pieces[answer["candidate_id"]], answer["undo_rotation_clockwise"], answer["undo_reflection"])
            restored_original.paste(patch.convert("RGB"), tuple(region["bounding_box"][:2]))
        checks["independent_pixel_exact_oracle_reconstruction"] = len(derived) == 5 and _same(restored_original, original)
        with Image.open(root / task["image"]) as opened:
            delivered = opened.convert("RGB")
        checks["public_composite_matches_verified_components"] = _same(_composite(puzzle, sheet), delivered)
        checks["public_image_under_9_5_mb"] = (root / task["image"]).stat().st_size < 9_500_000
        checks["coordinate_conventions_and_tolerance_stated"] = all(
            text in task["question"] for text in ("1920", "2560", "upper-left", "x increases right", "y increases down",
                                                  "30 pixels", "H1-H5", "Equivalent rotation/reflection"))
        checks["task_specific_scoring_contract"] = task.get("scoring") == {"kind": "spatial_reconstruction", "center_tolerance_px": 30}
        checks["sequence_answer_type"] = task.get("answer_type") == "sequence" and isinstance(task.get("answer"), list)
    except Exception as exc:
        checks["validation_exception"] = f"{type(exc).__name__}: {exc}"
    return {"passed": bool(checks) and all(v is True for v in checks.values()), "checks": checks}


def validate_jsonl(tasks_file: str | Path, task_root: str | Path | None = None) -> dict:
    tasks_file = Path(tasks_file)
    root = Path(task_root) if task_root is not None else tasks_file.parent
    results, seen = [], set()
    for line_no, line in enumerate(tasks_file.read_text(encoding="utf8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            task = json.loads(line)
            result = validate_task(task, str(root))
            if task.get("task_id") in seen:
                result["checks"]["unique_task_id"] = False
                result["passed"] = False
            seen.add(task.get("task_id"))
            results.append({"line": line_no, "task_id": task.get("task_id"), **result})
        except Exception as exc:
            results.append({"line": line_no, "task_id": None, "passed": False, "checks": {"parse": str(exc)}})
    return {"passed": bool(results) and all(r["passed"] for r in results), "n_tasks": len(results),
            "n_valid": sum(r["passed"] for r in results), "tasks": results}


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("tasks", nargs="?", default="tasks/tasks.jsonl")
    ap.add_argument("--task-root", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    result = validate_jsonl(args.tasks, args.task_root)
    rendered = json.dumps(result, indent=2)
    if args.out:
        Path(args.out).write_text(rendered + "\n", encoding="utf8")
    print(rendered)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

