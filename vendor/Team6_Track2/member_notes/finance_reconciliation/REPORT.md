# Member export report

**Mode:** A ? member export (`finance_reconciliation`).

## Bundle

This handoff contains the 12-case hard price-rule subset, the deterministic adapter, original generator/render/report code, automatic validation, two pre-existing pilot result copies, and document references. Each task includes six full-resolution source PNGs and the required single-image contact sheet.

## Rebuild and validate

From this directory:

```powershell
python build_reported.py --out tasks
python -m validate.finance_reconciliation.validate --tasks tasks
```

## Verification

- Rebuilt all 12 tasks a second time. SHA-256 comparison found **0 differences** across 84 images; question, answer, tolerance, seed, and question-type fields also matched.
- Automatic validation passed **12/12** tasks.
- Official checker run on the ZIP with `--tasks tasks --expected-tasks 12`: **14 PASS, 7 FAIL, 1 WARN**. All task-format checks passed, including image paths, answer types, numeric tolerance stated in each question, seeds, generator version, automatic checks, and secret scan. The seven FAILs are the member ZIP name not matching the final-team `_Track2.zip` pattern, absent root Dockerfile, and final-merge README/results-folder/Docker requirements. The one WARN is the final-merge README topic checklist. The master prompt says to ignore those final-repository checks in Mode A. No API evaluation was run for this export.

## Known issues and merge notes

- Existing model scores were obtained with six source pages attached separately. The contact sheet in the required single `image` field was not evaluated; a merged multi-image runner should consume the extra `images` array to reproduce prior results.
- Claude Haiku 5.5 rejects `temperature`; its prior run used the provider default and high effort. GPT-6 Luna used temperature 0 and high reasoning. Both used 16,384 max tokens and had no truncated replies.
- Prefix the task IDs during final merge if another member exports overlapping IDs. The three `price_rule_L0/L1/L2` values identify renderer variants of one logical question type.
- The bundle was rendered on Python 3.13.5 with Playwright 1.64.0 and Chromium. No model API was called while building or validating it.
