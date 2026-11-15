"""Standard interface for the repaired photo-restoration task family."""
from __future__ import annotations
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from .generate import generate as _generate

GENERATOR_VERSION = "visual_reconstruction-2.0"
QUESTION_TYPES = ["global_spatial_reconstruction"]
PATCH_SIZE = 520
HOLES = 5
CENTER_TOLERANCE_PX = 30
DISPLAY_SCALE = 0.8


def _answer_from_regions(regions):
    return [{"hole_id": r["hole_id"], "center": list(r["center_xy"]),
             "candidate_id": r["segment_id"],
             "undo_rotation_clockwise": r["required_undo_rotation_clockwise"],
             "undo_reflection": r["required_undo_reflection"]}
            for r in sorted(regions, key=lambda r: r["hole_id"])]


def _composite(puzzle: Image.Image, sheet: Image.Image) -> Image.Image:
    """Public composite with explicit original-photo coordinate rulers."""
    left, top, gap, bottom = 90, 160, 60, 70
    right_x = left + puzzle.width + gap
    canvas = Image.new("RGB", (right_x + sheet.width + 30, top + max(puzzle.height, sheet.height) + bottom), "white")
    draw = ImageDraw.Draw(canvas)
    title_font = ImageFont.load_default(size=34)
    font = ImageFont.load_default(size=25)
    small = ImageFont.load_default(size=20)
    draw.text((left, 18), "PHOTO RESTORATION AND SPATIAL REGISTRATION", fill=(22, 34, 48), font=title_font)
    draw.text((left, 74), f"MASKED PHOTO: {puzzle.width} x {puzzle.height} original pixels", fill=(22, 34, 48), font=font)
    draw.text((left, 108), "H1-H5 are hole IDs. Origin: upper-left pixel. x increases right; y increases down.", fill=(22, 34, 48), font=small)
    draw.text((right_x, 74), "SHUFFLED CANDIDATE PATCHES", fill=(22, 34, 48), font=font)
    draw.text((right_x, 108), "Each printed letter identifies one candidate.", fill=(22, 34, 48), font=small)
    canvas.paste(puzzle.convert("RGB"), (left, top))
    canvas.paste(sheet.convert("RGB"), (right_x, top))
    x_ticks = list(range(0, puzzle.width, 320)) + [puzzle.width - 1]
    y_ticks = list(range(0, puzzle.height, 320)) + [puzzle.height - 1]
    for x in x_ticks:
        draw.line((left + x, top - 8, left + x, top), fill="black", width=2)
        draw.text((left + x, top - 12), str(x), fill="black", font=small, anchor="ms")
    for y in y_ticks:
        draw.line((left - 8, top + y, left, top + y), fill="black", width=2)
        draw.text((left - 13, top + y), str(y), fill="black", font=small, anchor="rm")
    draw.text((left, top + puzzle.height + 18), "Coordinates and 30 px tolerance refer to the photo panel, excluding this page's margins.", fill=(22, 34, 48), font=small)
    # Keep a readable single PNG below the provider's image payload limit.
    # Rulers retain original-photo coordinates after display scaling.
    return canvas.resize((round(canvas.width * DISPLAY_SCALE), round(canvas.height * DISPLAY_SCALE)), Image.Resampling.LANCZOS)


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def generate_task(seed: int, question_type: str | None = None, out_dir: str = ".") -> dict:
    qtype = question_type or QUESTION_TYPES[0]
    if qtype not in QUESTION_TYPES:
        raise ValueError(f"Unknown question type: {qtype}")
    root = Path(out_dir)
    for folder in ("images", "data"):
        (root / folder).mkdir(parents=True, exist_ok=True)
    task_id = f"visual_reconstruction_{qtype}_s{seed:04d}"
    with tempfile.TemporaryDirectory(prefix="reconstruction_") as temp:
        generated = Path(temp)
        _generate(seed=seed, position_jitter=120, out_dir=generated, num_holes=HOLES)
        key = json.loads((generated / "private_ground_truth" / "answer_key.json").read_text(encoding="utf8"))
        image_rel = f"images/{task_id}.png"
        puzzle_rel = f"images/{task_id}_puzzle.png"
        sheet_rel = f"images/{task_id}_candidate_sheet.png"
        patches_rel = f"images/{task_id}_patches"
        shutil.copyfile(generated / "public" / "puzzle.png", root / puzzle_rel)
        shutil.copyfile(generated / "public" / "candidate_sheet.png", root / sheet_rel)
        (root / patches_rel).mkdir(parents=True, exist_ok=True)
        patch_files = {}
        for source in sorted((generated / "segments").glob("*.png")):
            rel = f"{patches_rel}/{source.name}"
            shutil.copyfile(source, root / rel)
            patch_files[source.stem] = rel
        for region in key["missing_regions"]:
            region["segment_file"] = patch_files[region["segment_id"]]
        with Image.open(root / puzzle_rel) as puzzle, Image.open(root / sheet_rel) as sheet:
            _composite(puzzle, sheet).save(root / image_rel, format="PNG", optimize=False)
        data_rel = f"data/{task_id}.json"
        data = {"task_id": task_id, "seed": seed, "generator_version": GENERATOR_VERSION,
                "question_type": qtype, "source_sha256": key["source_sha256"],
                "source_attribution_file": "generators/visual_reconstruction/assets/SOURCE_LICENSE.json",
                "patch_size_px": PATCH_SIZE, "display_scale": DISPLAY_SCALE, "num_missing_regions": HOLES,
                "num_candidates": len(patch_files),
                "component_images": {"puzzle": puzzle_rel, "candidate_sheet": sheet_rel},
                "component_sha256": {"puzzle": _sha(root / puzzle_rel), "candidate_sheet": _sha(root / sheet_rel)},
                "patch_files": patch_files, "ground_truth": key}
        (root / data_rel).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    question = (
        "Restore the masked photograph using the shuffled candidate patches. The photo panel is 1920 pixels wide "
        "and 2560 pixels high. Its origin (0,0) is the center of its upper-left pixel; x increases right to 1919, "
        "and y increases down to 2559. The page is displayed at reduced size: use its printed coordinate rulers, "
        "not page-image pixels. Ignore the surrounding page margins. The five gray regions are labeled H1-H5. "
        "For each hole, select the matching candidate letter and the transformation that restores the source photo. "
        "Estimate the hole center [x,y] in original-photo pixels; Euclidean error of at most 30 pixels is accepted. "
        "Apply undo_rotation_clockwise (0,90,180,270 degrees) FIRST, then undo_reflection "
        "('none', 'horizontal' meaning a left-right flip, or 'vertical' meaning a top-bottom flip). "
        "Equivalent rotation/reflection combinations are accepted. Return only a JSON array of exactly five objects, "
        "each with hole_id (integer 1-5 matching the H label), center [x,y], candidate_id (printed letter), "
        "undo_rotation_clockwise, and undo_reflection. Array order does not matter. Use every hole once and "
        "each selected candidate once; the other candidates are distractors."
    )
    task = {"task_id": task_id, "image": image_rel, "question": question,
            "answer": _answer_from_regions(key["missing_regions"]), "answer_type": "sequence",
            "seed": seed, "generator_version": GENERATOR_VERSION, "question_type": qtype,
            "data": data_rel, "scoring": {"kind": "spatial_reconstruction", "center_tolerance_px": CENTER_TOLERANCE_PX},
            "references": ["Warren LeMay, Urban Lab Building photograph, Wikimedia Commons, CC BY-SA 4.0",
                           "Noroozi and Favaro (2016), Unsupervised Learning of Visual Representations by Solving Jigsaw Puzzles"]}
    task["checks"] = validate_task(task, str(root))
    return task


def validate_task(task: dict, out_dir: str = ".") -> dict:
    from validate.visual_reconstruction.validate import validate_task as check
    return check(task, out_dir)

