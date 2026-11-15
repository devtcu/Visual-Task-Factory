# Evidence for the seven-task draft

These checks were performed on 2026-11-14. They establish software validation and reproducibility of this draft, not model difficulty or final submission readiness.

| Evidence | Meaning |
|---|---|
| `final_build.json` | All seven tasks passed validation inside the built Linux image. `verified_reported: true` means regenerated fingerprints matched the frozen submission. No source-code volume was mounted. |
| `final_fingerprints.json` | SHA-256 image/data hashes plus exact questions, reference answers, types, seeds, tolerances, and generator versions. This equals root `reported_fingerprints.json`. |
| `fresh_build.json` | The built image generated and validated a fresh fiber task, seed 7001, with no API key or evaluation. This diagnostic is not an eighth reported task. |
| `fresh_fingerprints.json` | Fingerprint of that diagnostic fresh task. |
| `scoring_smoke.json` | 42 offline cases across the seven reported tasks: correct reference accepted; wrong, empty, and malformed answers rejected. Includes exact inputs and source hashes. |
| `docker_verification.json` | Tested image identity, commands, exit statuses, and relevant source hashes. The build used the pinned base image and locked Python dependencies. |
| `draft_format_report.json` | Organizer checker v1.0.0 run on the packaged draft ZIP inside Linux Docker: 24 passes, one warning for seven rather than ten tasks, and one failure for intentionally absent final response files. |

`tasks/final/validation.json` contains each task's detailed checks. `HANDCHECK.md` describes the separate Codex-assisted image inspections and numerical review. No final-model generation calls were made. Historical results are preserved separately and are not used as final results.

The final ZIP was checked again after adding these evidence files. Its report is saved beside the ZIP as `Team6_Track2.check.json`; the archived report records the same 24-pass/1-warning/1-failure outcome from the draft check. Running the official checker directly on Windows produces native-path false errors, so the README documents the Linux Docker invocation without modifying the official script.
