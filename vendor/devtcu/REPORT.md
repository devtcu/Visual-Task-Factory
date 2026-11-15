# REPORT: devtcu handoff (Brain Connections)

## What is in the bundle
- `generators/devtcu/`: the generator (`connectome.py`, `common.py`) and `adapter.py` with `generate_task` / `validate_task`.
- `validate/devtcu/checks.py`: shared checks; the connectome pixel check and second solver live in `connectome.py` and run through it.
- `tasks/`: **105 valid tasks**, 5 for each of the 21 question types (`<question>_L<level>`), with `images/`, `data/` (graph JSON + layout), `seeds_used.json`, `rejected.jsonl` (3 rejected for overlapping labels), `determinism.json`.
- `eval/`: the evaluation code, copied, not run. `prior_results/`: the four pilot runs (both models, raw replies, run configs) and `RESULTS.md`.
- `INVENTORY.md`, `PILOT_NOTES.md`, `HANDCHECK.md`, `REFERENCES.md`, `MANIFEST.json`, `requirements.txt`, `system_packages.txt` (empty), `build_tasks.py`.

## Commands (from `handoff/devtcu/`)
```bash
pip install -r requirements.txt
python build_tasks.py tasks                                   # rebuild the set (about 8 minutes on 8 cores)
python build_tasks.py /tmp/rebuild --seeds tasks/seeds_used.json   # rebuild exactly these seeds
python -c "from generators.devtcu import adapter; print(adapter.generate_task(42, 'critical_count_L6', 'out'))"   # one fresh task
```

## Determinism
All 105 tasks were built twice from `seeds_used.json` and compared by SHA-256 of image, data JSON, question, answer, options and predicted wrong answers: **0 differences**.

## Validation
105 of 108 built tasks pass every check; the 3 rejected ones overlap a delay label with the IN/OUT tag and are excluded, never scored.

## Checker (official `check_submission.py`, run on this folder with `--tasks tasks`)
5 FAIL, 2 WARN, all expected for one member's bundle: no README.md, no Dockerfile, no "Reported folders" / "Run in Docker" sections (merge step). WARN: 105 tasks instead of the reported 10 (the merge picks 10); `__pycache__` (excluded from the zip). Task fields, image paths, options lists, seeds, versions and check results pass; no secrets found.

## Changes made during this export (devtcu-1.1, all in my own pipeline)
- Overlapping arrowheads at busy regions are resolved by turning or dropping that one connection (found in a pilot hand check).
- Each seed now owns its own block of candidate layouts (an earlier build gave 14 duplicate tasks); the design search stops after 6 valid layouts and keeps the best (same result every run).
- Marked labels keep clearance sized to the label; the pixel check keeps clear of label-box borders (it had flagged false "phantom lines").
- Multiple-choice `options` are a list, as the checker requires; answer extraction accepts only the task's option letters.

## Known issues
- Hard levels generate slowly: level 5-6 tasks take about 10-60 s each (under 1% of candidate layouts pass every fairness rule).
- The shared ocr_numbers check needs the tesseract binary; without it the check is SKIPPED and reported as passing.
- connectome_min_edge_cut_L1_s1 and connectome_critical_count_L1_s1 share one diagram (two different questions, two answers).
- Pilot results in prior_results/ come from earlier generator versions; the tasks in tasks/ have not been evaluated.
- Region names are real abbreviations, but the wiring and delays are synthetic (stated in every image title).

## For the merge
- Suggested candidates for the reported 10: the level-6 tasks (`critical_count_L6`, `delay_after_failure_L6`, `min_edge_cut_L6`). In the pilots level 6 was the only level where both models failed often (Haiku 14/18, Luna 8/18); levels 1-3 were near 100% for both.
- Task IDs start with `connectome_`; prefix them with the member name if another member uses the same word.
- Dependencies: numpy 2.2.5, matplotlib 3.10.0, networkx 3.5, scipy 1.16.0, pillow 11.1.0 (requests for eval). No system packages or fonts (matplotlib's bundled DejaVu Sans).
- My eval code already writes every `responses.csv` column the checker requires, plus `trap_hit` (called-shot matching) and supports multi-image tasks; it could serve as the merged `eval/`.
