"""Arithmetic regressions for the finance task's published rounding convention."""
from __future__ import annotations

import copy
import unittest
from decimal import Decimal, ROUND_HALF_UP

from generators.finance_reconciliation.adapter import task_question
from generators.finance_reconciliation.engine import make_scene, render_svg
from validate.finance_reconciliation.checks import independent_answer, validate_source_svg


class FinanceChecksTests(unittest.TestCase):
    def test_known_disagreement_uses_explicit_unit_rounding(self):
        # The earlier pilot's $4.99 response used a different, formerly unstated
        # line-rounding convention. The corrected question explicitly selects $5.15.
        scene = make_scene(2400, "hard", "price_rule", 0)
        self.assertEqual(independent_answer(scene), Decimal("5.15"))
        prompt = task_question(scene)
        self.assertIn("ROUND_HALF_UP", prompt)
        self.assertIn("exact half-cent rounds up", prompt)
        self.assertIn("Accepted answer tolerance is $0.01", prompt)

    def test_known_finance_answers(self):
        expected = {2403: "25.08", 2404: "4.77", 2407: "19.12", 2408: "1.56", 2411: "17.73"}
        for seed, answer in expected.items():
            with self.subTest(seed=seed):
                self.assertEqual(independent_answer(make_scene(seed, "hard", "price_rule", seed % 3)), Decimal(answer))

    def test_po_subtotal_uses_rounded_unit_prices(self):
        scene = make_scene(2400, "hard", "price_rule", 0)
        total = Decimal(0)
        for row in scene["purchase_order"]["lines"]:
            rate = (row["po_unit_price"] * (1 - row["discount_pct"] / 100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            total += rate * row["qty_ordered"]
        self.assertEqual(total, scene["purchase_order"]["subtotal"])
        self.assertTrue(validate_source_svg(scene, "purchase_order", render_svg(scene, "purchase_order"))["valid"])

    def test_recompute_does_not_trust_cached_combined_quantity(self):
        scene = make_scene(2400, "hard", "price_rule", 0)
        changed = copy.deepcopy(scene)
        for row in changed["invoice"]["lines"]:
            row["invoice_qty_total"] = 999999
        self.assertEqual(independent_answer(scene), independent_answer(changed))

    def test_recompute_rejects_wrong_po_link(self):
        scene = make_scene(2400, "hard", "price_rule", 0)
        scene["sibling_invoice"]["po_id"] = "UNRELATED"
        with self.assertRaisesRegex(ValueError, "another purchase order"):
            independent_answer(scene)


if __name__ == "__main__":
    unittest.main()
