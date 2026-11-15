from __future__ import annotations

import base64
import hashlib
import json
import tempfile
from decimal import Decimal
from pathlib import Path

from .engine import D, make_docs, make_scene, question, render_svg

GENERATOR_VERSION = "finance-reconciliation-1.1"
QUESTION_TYPES = ["price_rule_L0", "price_rule_L1", "price_rule_L2"]
PAGE_SIZE = (1654, 2339)
CONTACT_SIZE = (3308, 7017)
TOLERANCE_INSTRUCTIONS = " Accepted answer tolerance is $0.01. Answer as a USD amount to two decimal places."


def task_question(scene: dict) -> str:
    """One exact prompt for both the contact sheet and the six source-page views."""
    return question(scene)[0] + TOLERANCE_INSTRUCTIONS


def _paths(task_id: str, out_dir: str):
    root = Path(out_dir)
    return root, root / "images" / task_id, root / "images" / f"{task_id}_contact.png", root / "data" / f"{task_id}.json"


def _render_pages(scene: dict, docs: list[str], task_id: str, out_dir: str) -> tuple[list[str], str, dict]:
    from playwright.sync_api import sync_playwright

    root, page_dir, contact_path, _ = _paths(task_id, out_dir)
    page_dir.mkdir(parents=True, exist_ok=True)
    contact_path.parent.mkdir(parents=True, exist_ok=True)
    source_images = []
    text_bounds = {}
    with tempfile.TemporaryDirectory(prefix="finance_reconciliation_") as temp:
        tmp = Path(temp)
        jobs = []
        for i, kind in enumerate(docs, 1):
            svg_path = tmp / f"{i:02d}_{kind}.svg"
            png_path = page_dir / f"{i:02d}_{kind}.png"
            svg_path.write_text(render_svg(scene, kind), encoding="utf-8")
            jobs.append((svg_path, png_path))
            source_images.append(png_path.relative_to(root).as_posix())
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": PAGE_SIZE[0], "height": PAGE_SIZE[1]}, device_scale_factor=1,
                                    locale="en-US", timezone_id="UTC", color_scheme="light", reduced_motion="reduce")
            for kind, (svg_path, png_path) in zip(docs, jobs):
                page.goto(svg_path.resolve().as_uri(), wait_until="domcontentloaded", timeout=120000)
                page.evaluate("document.fonts.ready")
                text_bounds[kind] = page.evaluate("""() => {
                    const nodes = [...document.querySelectorAll('svg text')];
                    const bad = nodes.filter(n => { const b=n.getBBox();
                        return b.x < 0 || b.y < 0 || b.x+b.width > 1654 || b.y+b.height > 2339;
                    });
                    return {count:nodes.length, outside:bad.map(n=>n.textContent),
                            minimum_font_px:Math.min(...nodes.map(n=>Number(n.getAttribute('font-size'))))};
                }""")
                page.screenshot(path=str(png_path), full_page=False, timeout=120000, animations="disabled", caret="hide")
            # The standard handoff schema requires one image. Keep all six original pages above
            # and provide a full-resolution contact sheet for single-image consumers.
            tiles = "".join(
                f'<img src="data:image/png;base64,{base64.b64encode(png.read_bytes()).decode("ascii")}" />'
                for _, png in jobs
            )
            html = ("<!doctype html><meta charset='utf-8'><style>html,body{margin:0;padding:0}"
                    ".grid{display:grid;grid-template-columns:1654px 1654px;width:3308px}"
                    "img{display:block;width:1654px;height:2339px;margin:0}</style>"
                    f"<div class='grid'>{tiles}</div>")
            sheet = browser.new_page(viewport={"width": CONTACT_SIZE[0], "height": CONTACT_SIZE[1]}, device_scale_factor=1,
                                     locale="en-US", timezone_id="UTC", color_scheme="light", reduced_motion="reduce")
            sheet.set_content(html, wait_until="load", timeout=120000)
            sheet.screenshot(path=str(contact_path), full_page=True, timeout=120000, animations="disabled", caret="hide")
            browser.close()
    contact_rel = contact_path.relative_to(root).as_posix()
    evidence = {"document_order": docs, "page_size": list(PAGE_SIZE), "contact_size": list(CONTACT_SIZE),
                "text_bounds": text_bounds,
                "image_sha256": {p: hashlib.sha256((root / p).read_bytes()).hexdigest()
                                 for p in [*source_images, contact_rel]}}
    return source_images, contact_rel, evidence


def generate_task(seed: int, question_type: str | None = None, out_dir: str = ".") -> dict:
    """Build one deterministic hard price-rule case and its image/data files.

    question_type selects a page layout (price_rule_L0 through price_rule_L2),
    which lets the same seed reproduce the paired layout comparison.
    """
    qtype = question_type or QUESTION_TYPES[seed % len(QUESTION_TYPES)]
    if qtype not in QUESTION_TYPES:
        raise ValueError(f"Unsupported question_type {qtype!r}; choose one of {QUESTION_TYPES}")
    layout = int(qtype[-1])
    # Render the same canonical values that validation reloads from the saved JSON.
    # This avoids Decimal display differences such as 3.00% versus 3.0% on a re-render.
    scene = json.loads(json.dumps(make_scene(seed, "hard", "price_rule", layout, 0), default=float),
                       parse_float=Decimal)
    task_id = f"fin-{seed:05d}-pri-h-L{layout}"
    docs = make_docs(scene)
    source_images, contact_image, render_evidence = _render_pages(scene, docs, task_id, out_dir)
    _, answer, _answer_type, evidence, trace = question(scene)
    qtext = task_question(scene)
    data_rel = Path("data", f"{task_id}.json").as_posix()
    _, _, _, data_path = _paths(task_id, out_dir)
    data_path.parent.mkdir(parents=True, exist_ok=True)
    data_path.write_text(json.dumps({"scene": scene, "evidence_ids": evidence, "solver_trace": trace,
                                    "render_evidence": render_evidence},
                                    indent=2, ensure_ascii=False, default=float), encoding="utf-8")
    task = {
        "task_id": task_id,
        "image": contact_image,
        "images": source_images,
        "question": qtext,
        "answer": float(D(answer.replace("$", "").replace(",", ""))),
        "answer_type": "number",
        "tolerance_abs": 0.01,
        "seed": seed,
        "generator_version": GENERATOR_VERSION,
        "question_type": qtype,
        "family": "price_rule",
        "layout": layout,
        "data": data_rel,
    }
    task["checks"] = validate_task(task, out_dir)
    if not task["checks"]["passed"]:
        raise ValueError(f"Generated task did not validate: {task_id}: {task['checks']}")
    return task


def validate_task(task: dict, out_dir: str = ".") -> dict:
    """Delegate all checking to the submission's validate package."""
    from validate.finance_reconciliation.checks import validate_task as run_checks
    return run_checks(task, out_dir)
