# Inventory ? Finance reconciliation handoff

## Scope and document types
The exported focus is synthetic accounts-payable price reconciliation. It imitates six commercial record types: purchase orders, posted goods-receipt notes (two receipts), supplier tax invoices, split-billing invoices, and authorized purchase-order amendments. The focused 12-task set uses one logical question type (`price_rule`): sum merchandise overcharge across invoice lines after checking the PO/amendment effective on the invoice date, discounts, and split-billing quantities. Other families (`quantity`, `balance`) remain in the copied engine but are outside this focused task set.

## Entry points
- Existing generator: `python -m visionforge_finance.generate --seed 2400 --difficulty hard --family price_rule --count 12 --output runs/finance_price_rule_stress_v2`.
- Handoff API: `generators/finance_reconciliation/adapter.py::generate_task(seed, question_type, out_dir)` and `validate_task(task, out_dir)`.
- Handoff task runner/validator: `python -m validate.finance_reconciliation.validate` (from the handoff root).
- Existing evaluator code is copied to `eval/evaluate.py` for future merged-run use. It was not run as part of this export. Existing results are copied to `prior_results/`.

## Questions, answers, and tolerances
One template, price-rule merchandise overcharge: inspect the invoice, PO, any effective amendments, and any split invoice; compute the sum of positive discounted unit-rate differences times billed quantity. Answer is a numeric USD value, scored within an absolute $0.01. Questions in the handoff state that tolerance explicitly. Layout variants L0/L1/L2 select the three original page designs; they are render variants, not different reasoning templates.

## Language and dependencies
- Python 3.13.5 in the source workspace; implementation uses Python 3.10+ syntax and the standard library.
- Playwright 1.64.0 renders SVG to PNG with Chromium. No Pillow or external asset library is required.
- Browser system packages: Linux Chromium dependencies can be installed with `python -m playwright install --with-deps chromium`; the handoff `system_packages.txt` records the common packages required by the browser. Source fonts use Arial with sans-serif fallback.

## Current state
- Structured scenes use seeded `random.Random`, prices use `Decimal` with half-up cent rounding, and each task carries source data and solver trace.
- The focused 12-task cents-level run generated 72 full-resolution source pages; both existing model evaluations completed without API errors or token truncation.
- The adapter emits the standard single `image` field as a contact sheet and also stores all six full-resolution source PNGs in `images`. Prior model scores were measured with the six pages attached separately; the contact-sheet representation is a packaging adapter and was not evaluated. Downstream multi-image evaluation should use the task record's `images` array to reproduce the prior input format.
- The source renderer, generator, and report code are complete. The task bundle intentionally contains no `.env`, credentials, or API settings with secret values.
