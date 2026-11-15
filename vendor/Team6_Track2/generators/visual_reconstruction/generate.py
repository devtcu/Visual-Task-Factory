"""Seeded photo-restoration tasks with randomized holes, identities and transforms.

The licensed photograph is an immutable input asset. Structured crop coordinates,
candidate identities and transformations are selected before images render.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import random
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "assets" / "urban_lab_building.jpg"
OUT = ROOT / "runs" / "restoration"
PATCH_SIZE = 520
NEUTRAL = (128, 128, 128)
TRANSFORMS = [(r, f) for f in ("none", "horizontal") for r in (0, 90, 180, 270)]


def transform(piece, rotation, reflection):
    """Candidate creation: reflect first, then rotate clockwise."""
    if reflection == "horizontal":
        piece = ImageOps.mirror(piece)
    elif reflection == "vertical":
        piece = ImageOps.flip(piece)
    return piece.rotate(-rotation, expand=True, resample=Image.Resampling.NEAREST)


def inverse_transform(piece, rotation, reflection):
    piece = piece.rotate(rotation, expand=True, resample=Image.Resampling.NEAREST)
    if reflection == "horizontal":
        piece = ImageOps.mirror(piece)
    elif reflection == "vertical":
        piece = ImageOps.flip(piece)
    return piece


def overlap(a, b):
    return (min(a[0] + a[2], b[0] + b[2]) > max(a[0], b[0]) and
            min(a[1] + a[3], b[1] + b[3]) > max(a[1], b[1]))


def feature(img):
    arr = np.asarray(img.convert("RGB").resize((48, 48), Image.Resampling.BILINEAR))
    px = arr.reshape(-1, 3)
    hist, _ = np.histogramdd(px, bins=(8, 8, 8), range=((0, 256),) * 3)
    hist = hist.astype(np.float32).ravel()
    hist /= max(hist.sum(), 1)
    return np.concatenate([hist, (px.mean(axis=0) / 255).astype(np.float32)])


def make_puzzle(original, regions):
    puzzle = original.convert("RGB").copy()
    draw = ImageDraw.Draw(puzzle)
    font = ImageFont.load_default(size=48)
    for region in regions:
        x, y, w, h = region["bounding_box"]
        draw.rectangle((x, y, x + w - 1, y + h - 1), fill=NEUTRAL)
        draw.text((x + w / 2, y + h / 2), f"H{region['hole_id']}",
                  fill="white", font=font, anchor="mm", stroke_width=1)
    return puzzle


def make_sheet(candidates):
    cols, cell_w, cell_h = 3, 400, 440
    rows = math.ceil(len(candidates) / cols)
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), (235, 237, 239))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=30)
    for i, item in enumerate(candidates):
        x, y = (i % cols) * cell_w, (i // cols) * cell_h
        draw.rounded_rectangle((x + 8, y + 8, x + cell_w - 8, y + cell_h - 8),
                               radius=10, fill="white", outline=(180, 185, 190), width=2)
        with Image.open(item["path"]) as opened:
            thumb = opened.convert("RGB")
        thumb.thumbnail((cell_w - 42, cell_h - 70), Image.Resampling.LANCZOS)
        sheet.paste(thumb, (x + (cell_w - thumb.width) // 2, y + 15))
        draw.text((x + 20, y + cell_h - 48), item["id"], font=font, fill=(20, 32, 45))
    return sheet


def generate(seed=20261114, position_jitter=120, out_dir=OUT, num_holes=5):
    rng = random.Random(seed)
    out = Path(out_dir)
    for name in ("public", "private_ground_truth", "segments"):
        (out / name).mkdir(parents=True, exist_ok=True)
    with Image.open(SOURCE) as opened:
        original = opened.convert("RGB")
    w, h = original.size
    if (w, h) != (1920, 2560) or not 1 <= num_holes <= 8:
        raise ValueError("Expected the licensed 1920x2560 source and 1-8 holes")

    # Random cells across the entire photo replace the previous fixed anchors.
    # Within-cell variation also exceeds the 30 px scoring tolerance.
    cells = [(x, y) for y in range(0, h, 640) for x in range(0, w, 640)]
    selected = rng.sample(cells, num_holes)
    jitter = min(120, max(0, int(position_jitter)))
    boxes = [(x + rng.randint(0, jitter), y + rng.randint(0, jitter), PATCH_SIZE, PATCH_SIZE)
             for x, y in selected]
    boxes.sort(key=lambda b: (b[1], b[0]))
    candidate_ids = [chr(ord("A") + i) for i in range(num_holes * 3)]
    rng.shuffle(candidate_ids)
    chosen_transforms = [rng.choice(TRANSFORMS) for _ in boxes]
    while sum(t != (0, "none") for t in chosen_transforms) < math.ceil(num_holes * .6):
        chosen_transforms = [rng.choice(TRANSFORMS) for _ in boxes]

    truth, candidates = [], []
    for i, ((x, y, pw, ph), (rotation, reflection)) in enumerate(zip(boxes, chosen_transforms)):
        cid = candidate_ids[i]
        patch = original.crop((x, y, x + pw, y + ph)).convert("RGBA")
        piece = transform(patch, rotation, reflection)
        path = out / "segments" / f"{cid}.png"
        piece.save(path)
        candidates.append({"id": cid, "path": path})
        truth.append({"hole_id": i + 1, "segment_id": cid,
                      "bounding_box": [x, y, pw, ph],
                      "center_xy": [x + (pw - 1) / 2, y + (ph - 1) / 2],
                      "candidate_creation_rotation_clockwise": rotation,
                      "candidate_creation_reflection": reflection,
                      "required_undo_rotation_clockwise": (-rotation) % 360,
                      "required_undo_reflection": reflection,
                      "segment_file": f"segments/{cid}.png", "is_genuine": True})

    # Retrieve plausible same-photo distractors from windows outside all holes.
    locations = []
    for x in range(0, w - PATCH_SIZE + 1, 56):
        for y in range(0, h - PATCH_SIZE + 1, 56):
            if not any(overlap((x, y, PATCH_SIZE, PATCH_SIZE), b) for b in boxes):
                crop = original.crop((x, y, x + PATCH_SIZE, y + PATCH_SIZE))
                locations.append((x, y, feature(crop)))
    used = set()
    distractors = []
    for hole in truth:
        x, y, pw, ph = hole["bounding_box"]
        target = feature(original.crop((x, y, x + pw, y + ph)))
        ranked = sorted((float(np.linalg.norm(f - target)), px, py) for px, py, f in locations)
        picked = 0
        for distance, px, py in ranked:
            if (px, py) in used:
                continue
            used.add((px, py))
            cid = candidate_ids[num_holes + len(distractors)]
            rotation, reflection = rng.choice(TRANSFORMS)
            crop = original.crop((px, py, px + pw, py + ph)).convert("RGBA")
            piece = transform(crop, rotation, reflection)
            path = out / "segments" / f"{cid}.png"
            piece.save(path)
            candidates.append({"id": cid, "path": path})
            distractors.append({"segment_id": cid, "source_coordinates": [px, py, pw, ph],
                                "rotation_applied_clockwise": rotation, "reflection_applied": reflection,
                                "similarity_distance": distance})
            picked += 1
            if picked == 2:
                break
        if picked != 2:
            raise RuntimeError("Insufficient distinct distractor windows")

    rng.shuffle(candidates)
    puzzle = make_puzzle(original, truth)
    sheet = make_sheet(candidates)
    puzzle.save(out / "public" / "puzzle.png")
    sheet.save(out / "public" / "candidate_sheet.png")
    key = {"seed": seed, "position_jitter_px": jitter, "patch_size_px": PATCH_SIZE,
           "image_width": w, "image_height": h, "num_missing_regions": num_holes,
           "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
           "missing_regions": truth, "distractors": distractors,
           "candidate_order": [c["id"] for c in candidates]}
    (out / "private_ground_truth" / "answer_key.json").write_text(json.dumps(key, indent=2) + "\n", encoding="utf8")
    restored = puzzle.copy()
    for item in truth:
        with Image.open(out / item["segment_file"]) as opened:
            patch = inverse_transform(opened.convert("RGBA"), item["candidate_creation_rotation_clockwise"],
                                      item["candidate_creation_reflection"])
        x, y, _, _ = item["bounding_box"]
        restored.paste(patch.convert("RGB"), (x, y))
    exact = restored.tobytes() == original.tobytes()
    if not exact:
        raise AssertionError("Oracle did not reconstruct the source photograph")
    (out / "private_ground_truth" / "qa_report.json").write_text(json.dumps({"seed": seed, "checks": {
        "pixel_exact_reconstruction": exact, "hole_boxes_nonoverlapping": all(
            not overlap(a, b) for i, a in enumerate(boxes) for b in boxes[i + 1:]),
        "unique_candidate_ids": len({c['id'] for c in candidates}) == num_holes * 3}}, indent=2) + "\n", encoding="utf8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20261114)
    ap.add_argument("--holes", type=int, default=5)
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()
    generate(seed=args.seed, out_dir=args.out, num_holes=args.holes)

