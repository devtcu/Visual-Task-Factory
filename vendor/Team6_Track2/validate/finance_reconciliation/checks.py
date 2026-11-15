"""Independent finance arithmetic and validation of the saved rendered packet.

The arithmetic uses the PO, amendment and each billed document separately. It does
not trust cached totals, the generator's answer, or its private solver trace.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import struct
import tempfile
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

CENT = Decimal("0.01")


def _decimal(value) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _cent(value) -> Decimal:
    return _decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def independent_answer(scene: dict) -> Decimal:
    """Reconcile the actual billed rows using the model-visible rounding rule."""
    purchase_order = scene["purchase_order"]
    po_lines = {row["line"]: row for row in purchase_order["lines"]}
    if len(po_lines) != len(purchase_order["lines"]):
        raise ValueError("Duplicate PO line number")
    amendment = scene["amendment"]
    if amendment["po_id"] != purchase_order["id"]:
        raise ValueError("Amendment belongs to another purchase order")
    amended = set(amendment["lines"])
    invoice = scene["invoice"]
    documents = [invoice]
    if scene.get("sibling_invoice"):
        documents.append(scene["sibling_invoice"])
    total = Decimal("0.00")
    for document in documents:
        if document["po_id"] != purchase_order["id"]:
            raise ValueError("Billed document belongs to another purchase order")
        if document["date"] != invoice["date"]:
            raise ValueError("This packet requires the linked invoices to share an effective date")
        seen = set()
        for billed_row in document["lines"]:
            line_number = billed_row["line"]
            if line_number in seen:
                raise ValueError("Duplicate line in one billed document")
            seen.add(line_number)
            po_row = po_lines[line_number]
            if billed_row["sku"] != po_row["sku"] or billed_row["uom"] != po_row["uom"]:
                raise ValueError("Billed item does not match the PO line")
            authorized = po_row["po_unit_price"]
            if line_number in amended and invoice["date"] >= amendment["effective_date"]:
                authorized = po_row["amended_unit_price"]
            authorized_net = _cent(_decimal(authorized) * (1 - _decimal(po_row["discount_pct"]) / 100))
            billed_net = _cent(_decimal(billed_row["invoice_unit_price"]) *
                               (1 - _decimal(billed_row["discount_pct"]) / 100))
            quantity = _decimal(billed_row["invoice_qty"])
            if quantity < 0 or quantity != quantity.to_integral_value():
                raise ValueError("Billed quantity must be a nonnegative whole number")
            total += _cent(max(Decimal(0), billed_net - authorized_net) * quantity)
    return _cent(total)


def validate_source_svg(scene: dict, kind: str, svg_text: str) -> dict:
    """Check document arithmetic and the renderer's semantic/text-bound output."""
    po = scene["purchase_order"]
    invoice = scene["invoice"]
    lines = po["lines"]
    assert len({row["sku"] for row in lines}) == len(lines), "Duplicate PO SKU"
    po_subtotal = sum((_cent(_cent(_decimal(row["po_unit_price"]) *
                                    (1 - _decimal(row["discount_pct"]) / 100)) * row["qty_ordered"])
                       for row in lines), Decimal(0))
    assert _cent(po_subtotal) == _decimal(po["subtotal"]), "PO subtotal violates the printed unit-rounding rule"
    assert _decimal(po["total"]) == _cent(_decimal(po["subtotal"]) + _decimal(po["freight"]) + _decimal(po["tax"]))
    documents = [invoice] + ([scene["sibling_invoice"]] if scene.get("sibling_invoice") else [])
    for document in documents:
        subtotal = Decimal(0)
        for row in document["lines"]:
            extension = _cent(_cent(_decimal(row["invoice_unit_price"]) *
                                    (1 - _decimal(row["discount_pct"]) / 100)) * row["invoice_qty"])
            assert extension == _decimal(row["invoice_line_total"]), "Invoice extension violates unit-rounding rule"
            subtotal += extension
        assert _cent(subtotal) == _decimal(document["subtotal"]), "Invoice subtotal mismatch"
        assert _decimal(document["total"]) == _cent(subtotal + _decimal(document["freight"]) + _decimal(document["tax"]))
    for row in lines:
        assert row["invoice_qty"] + row["sibling_invoice_qty"] == row["invoice_qty_total"]
        factor = row["conversion_factor"]
        for receipt in (1, 2):
            for field in ("accepted", "received", "rejected"):
                assert row[f"grn{receipt}_{field}"] == row[f"grn{receipt}_{field}_raw"] * factor
            assert row[f"grn{receipt}_accepted_raw"] + row[f"grn{receipt}_rejected_raw"] <= row[f"grn{receipt}_received_raw"]
    linked_credit = sum((_decimal(c["amount"]) for c in scene["credit_memos"]
                         if c["invoice_id"] == invoice["id"]), Decimal(0))
    assert linked_credit == _decimal(scene["linked_credit_total"])
    cleared = sum((_decimal(p["amount"]) for p in scene["payments"]
                   if p["status"] == "CLEARED" and p["date"] <= scene["as_of_date"]), Decimal(0))
    assert _cent(_decimal(invoice["total"]) - linked_credit - cleared) >= 0
    assert "<svg" in svg_text and "</svg>" in svg_text
    text_pattern = r'<text x="([\d.]+)" y="([\d.]+)" font-family="[^"]+" font-size="(\d+)" fill="[^"]+" font-weight="\d+">(.*?)</text>'
    for match in re.finditer(text_pattern, svg_text):
        x, y, size = float(match[1]), float(match[2]), int(match[3])
        content = html.unescape(match[4])
        assert x >= 0 and 20 <= y <= 2310 and x + len(content) * size * .58 <= 1644, f"Text outside page: {content[:50]}"
    if kind in ("purchase_order", "invoice", "grn1", "grn2"):
        for row in lines:
            assert html.escape(row["sku"]) in svg_text and html.escape(row["description"]) in svg_text
    if kind in ("purchase_order", "invoice", "invoice_sibling", "amendment"):
        assert "round half-up" in svg_text and "before multiplying by quantity" in svg_text
    return {"valid": True, "financial_invariants": True, "unit_rounding_consistent": True,
            "text_bounds_valid": True, "layout": scene["variant"], "svg_chars": len(svg_text)}


def _resolve(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or Path(relative).is_absolute():
        raise ValueError("Expected a task-relative file path")
    candidate = (root / relative).resolve()
    if not candidate.is_relative_to(root.resolve()):
        raise ValueError("Task path escapes its output folder")
    return candidate


def _png_dimensions(path: Path) -> tuple[int, int]:
    header = path.read_bytes()[:24]
    if header[:8] != b"\x89PNG\r\n\x1a\n" or len(header) != 24:
        raise ValueError("Invalid PNG header")
    return struct.unpack(">II", header[16:24])


def validate_task(task: dict, out_dir: str = ".") -> dict:
    from generators.finance_reconciliation.adapter import (
        CONTACT_SIZE, GENERATOR_VERSION, PAGE_SIZE, _render_pages, task_question,
    )
    from generators.finance_reconciliation.engine import make_docs, question, render_svg

    root = Path(out_dir)
    checks: dict[str, bool | str] = {}
    try:
        payload = json.loads(_resolve(root, task["data"]).read_text(encoding="utf-8"), parse_float=Decimal)
        scene = payload["scene"]
        docs = make_docs(scene)
        svgs = {kind: render_svg(scene, kind) for kind in docs}
        source_checks = [validate_source_svg(scene, kind, svgs[kind]) for kind in docs]
        checks["source_pages_valid"] = len(source_checks) == 6 and all(c["valid"] for c in source_checks)
        checks["question_matches_scene_exactly"] = task["question"] == task_question(scene)
        checks["model_visible_rounding_rule"] = "ROUND_HALF_UP" in task["question"] and "exact half-cent rounds up" in task["question"]
        checks["question_states_tolerance"] = "Accepted answer tolerance is $0.01." in task["question"]
        checks["answer_type_and_tolerance"] = (task["answer_type"] == "number" and
                                                isinstance(task["answer"], (int, float, Decimal)) and
                                                not isinstance(task["answer"], bool) and
                                                _decimal(task.get("tolerance_abs", -1)) == CENT and
                                                "tolerance_rel" not in task)
        expected = independent_answer(scene)
        checks["independent_answer_recompute"] = _decimal(task["answer"]) == expected
        _, generator_answer, _, evidence_ids, _ = question(scene)
        checks["generator_answer_agrees"] = _decimal(generator_answer.replace("$", "").replace(",", "")) == expected
        visible = " ".join(svgs.values())
        checks["evidence_ids_are_visible"] = all(html.escape(identifier) in visible for identifier in evidence_ids)
        checks["seed_and_version_match"] = task["seed"] == scene["seed"] and task["generator_version"] == GENERATOR_VERSION

        paths = task.get("images", [])
        checks["six_source_images_exist"] = len(paths) == 6 and all(_resolve(root, p).is_file() for p in paths)
        checks["source_image_dimensions"] = len(paths) == 6 and all(_png_dimensions(_resolve(root, p)) == PAGE_SIZE for p in paths)
        checks["contact_sheet_dimensions"] = _png_dimensions(_resolve(root, task["image"])) == CONTACT_SIZE
        stored = payload.get("render_evidence", {})
        actual_hashes = {p: hashlib.sha256(_resolve(root, p).read_bytes()).hexdigest() for p in [*paths, task["image"]]}
        checks["recorded_render_hashes_match"] = actual_hashes == stored.get("image_sha256")
        checks["document_order_recorded"] = stored.get("document_order") == docs

        # Re-render from the persisted data, then compare every source page and the
        # contact sheet. A wrong, stale, swapped or blank saved image fails here.
        with tempfile.TemporaryDirectory(prefix="finance_validate_") as scratch:
            regenerated_pages, regenerated_contact, rerender = _render_pages(scene, docs, "reference", scratch)
            expected_hashes = rerender["image_sha256"]
            checks["saved_pages_match_data"] = len(paths) == len(regenerated_pages) and all(
                actual_hashes[actual] == expected_hashes[regenerated]
                for actual, regenerated in zip(paths, regenerated_pages))
            checks["contact_sheet_matches_source_pages"] = actual_hashes[task["image"]] == expected_hashes[regenerated_contact]
            bounds = rerender["text_bounds"]
            checks["rendered_text_inside_canvas"] = len(bounds) == 6 and all(b["count"] > 0 and not b["outside"] for b in bounds.values())
            checks["minimum_font_size"] = len(bounds) == 6 and all(b["minimum_font_px"] >= 13 for b in bounds.values())
            checks["render_bounds_evidence_matches"] = stored.get("text_bounds") == bounds
    except Exception as exc:
        checks["validation_error"] = str(exc)
    return {"passed": bool(checks) and all(value is True for value in checks.values()), "checks": checks}
