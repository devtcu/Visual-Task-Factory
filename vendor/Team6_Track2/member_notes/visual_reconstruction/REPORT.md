# Member export report

## Contents and reproduction

The bundle contains the copied photo generator and asset, a standard adapter, five task records with composite images and per-task structured data, independent validation, prior evaluation artifacts, notes, and the copied evaluator (not run).

From this folder:

```powershell
py -3.12 -m pip install -r requirements.txt
py -3.12 build_tasks.py --out tasks
py -3.12 -m validate.visual_reconstruction.validate tasks/tasks.jsonl --out tasks/validation_report.json
```

## Verification

- Determinism: PASS. Rebuilt seeds 1–5; SHA-256 matched for every image, exact question, and answer.
- Adapter and oracle validation: PASS, 5/5 tasks. Component image hashes and composite rendering match; hole geometry, candidate assets, answer recomputation, and generator QA pass.
- Official checker v1.0.0 (folder mode): 5 FAIL, 5 WARN, 13 PASS. Task fields, image paths, automatic checks, and secrets checks all PASS. The expected partial-bundle warning is five tasks rather than the final merged set's ten.
- Official checker v1.0.0 (ZIP mode): 6 FAIL, 5 WARN, 17 PASS. The extra ZIP-level FAIL is the expected `handoff_visual_reconstruction.zip` filename; final TeamName naming applies after team merge. Other FAILs are merged-repository items intentionally absent here: no Dockerfile, no final reported results folder, and no Docker build/run commands or API-key runtime configuration. The member export did not evaluate models.
- No checker FAIL/WARN concerns malformed task fields or secrets. Docker instructions and result-folder checks are intentionally deferred to the merged submission.

## Known issues and merge decisions

Only one CC BY-SA 4.0 source photo and one question type are included. The ten prior five-hole instances are seed variants of that same photo; GPT-6 Luna has no completed answer for instance 10. Human ambiguity review has not been performed. Candidate labels may use a host-dependent font fallback.

The merge owner should choose the final member/package prefix, preserve the photograph's attribution and share-alike terms, and resolve any `global_spatial_reconstruction` question-type overlap. Requirements are pinned to NumPy 1.26.4 and Pillow 11.1.0; the system package list is empty. No shared font files are required.

The member archive is `handoff_visual_reconstruction.zip` (122.4 MB compressed, CRC verified). It is below the checker’s 200 MB upload limit.
