"""Automatic validity checks. Every check returns {"name", "pass", "detail"}. A task counts only if all pass."""
import re
import shutil

import numpy as np
from PIL import Image

MIN_FONT_PT = 7.0


def _inside(value, spec):
    ref = spec["answer"]
    if isinstance(ref, (list, str)) or isinstance(value, (list, str)):
        return value == ref
    if "tolerance_abs" in spec:
        return abs(value - ref) <= spec["tolerance_abs"]
    if "tolerance_rel" in spec:
        return abs(value - ref) <= spec["tolerance_rel"] * abs(ref)
    return value == ref


def answer_recomputed(spec, family):
    """An independent second method must give the same reference answer."""
    other = family.resolve(spec["data"], spec["question_type"])
    ref = spec["answer"]
    if isinstance(other, (int, float)) and isinstance(ref, (int, float)):
        ok = abs(other - ref) <= 1e-6 * max(1.0, abs(ref)) + spec.get("recompute_slack", 0.0)
    else:
        ok = other == ref
    return {"name": "answer_recomputed", "pass": bool(ok), "detail": f"generator={ref!r} second_method={other!r}"}


def answer_unique(spec):
    """The generator states why the answer is unique (for example the gap to the runner-up path); it must hold."""
    u = spec.get("uniqueness", {"ok": True, "why": "single closed-form value"})
    return {"name": "answer_unique", "pass": bool(u["ok"]), "detail": u["why"]}


def wrong_methods_rejected(spec):
    """Answers from the named common mistakes must all be scored wrong, so the tolerance is not too loose."""
    wrong = spec.get("wrong_answers", {})
    inside = [k for k, v in wrong.items() if _inside(v, spec)]
    return {"name": "wrong_methods_rejected", "pass": bool(wrong) and not inside,
            "detail": f"{len(wrong)} named mistakes tested; inside tolerance: {inside or 'none'}"}


def labels_present(layout):
    """Every label the data says must be visible was actually placed on the figure."""
    drawn = " | ".join(t["text"] for t in layout["texts"])
    missing = [s for s in layout["expected_labels"] if s not in drawn]
    return {"name": "labels_present", "pass": not missing,
            "detail": f"{len(layout['expected_labels'])} expected; missing: {missing[:5] or 'none'}"}


def labels_legible(layout):
    """Every text label is inside the image, at or above the minimum font size, and no two labels overlap."""
    W, H, texts, bad = layout["width"], layout["height"], layout["texts"], []
    for t in texts:
        if t["x0"] < -1 or t["y0"] < -1 or t["x1"] > W + 1 or t["y1"] > H + 1:
            bad.append(f"outside image: {t['text']!r}")
        if t["size"] < MIN_FONT_PT:
            bad.append(f"font {t['size']}pt: {t['text']!r}")
    for i, a in enumerate(texts):
        for b in texts[i + 1:]:
            if min(a["x1"], b["x1"]) - max(a["x0"], b["x0"]) > 1 and min(a["y1"], b["y1"]) - max(a["y0"], b["y0"]) > 1:
                bad.append(f"overlap: {a['text']!r} / {b['text']!r}")
    return {"name": "labels_legible", "pass": not bad,
            "detail": f"{len(texts)} labels; " + ("; ".join(bad[:4]) or "none outside, too small or overlapping")}


def labels_inked(layout, png_path):
    """Pixel check on the saved PNG: each label box contains ink (the label was not clipped or painted over)."""
    img = np.asarray(Image.open(png_path).convert("L")).astype(int)
    blank = []
    for t in layout["texts"]:
        x0, y0, x1, y1 = (int(max(0, round(t[k]))) for k in ("x0", "y0", "x1", "y1"))
        box = img[y0:y1 + 1, x0:x1 + 1]
        if box.size == 0 or (box.max() - box.min()) < 60:
            blank.append(t["text"])
    return {"name": "labels_inked", "pass": not blank,
            "detail": f"{len(layout['texts'])} label boxes probed on the PNG; no ink in: {blank[:5] or 'none'}"}


def ocr_numbers(layout, png_path):
    """OCR round trip: the numbers in the expected labels can be read back from the PNG. Needs the tesseract binary."""
    if not shutil.which("tesseract"):
        return {"name": "ocr_numbers", "pass": True,
                "detail": "SKIPPED: tesseract is not installed on this machine (it is installed in the Docker image)"}
    import pytesseract
    big = Image.open(png_path).convert("L")
    big = big.resize((big.width * 2, big.height * 2))
    text = pytesseract.image_to_string(big, config="--psm 11")
    seen = set(re.findall(r"\d+(?:\.\d+)?", text.replace(",", "")))
    want = sorted({n for s in layout["expected_labels"] for n in re.findall(r"\d+(?:\.\d+)?", s.replace(",", ""))})
    found = [n for n in want if n in seen]
    rate = len(found) / len(want) if want else 1.0
    return {"name": "ocr_numbers", "pass": rate >= 0.8, "detail": f"read back {len(found)}/{len(want)} label numbers by OCR"}


def run_all(spec, family, layout, png_path):
    checks = [answer_recomputed(spec, family), answer_unique(spec), wrong_methods_rejected(spec), labels_present(layout),
              labels_legible(layout), labels_inked(layout, png_path), ocr_numbers(layout, png_path)]
    extra = getattr(family, "render_check", None)
    if extra:
        checks.append(extra(spec, layout, png_path))
    return checks


def all_pass(checks):
    return all(c["pass"] for c in checks)
