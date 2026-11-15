# Member export report

## Bundle contents

This bundle contains the copied procedural renderers, a thin Track 2 adapter, the generated task set with source data and images, a member validation runner, the original evaluation implementation reference, and copies of existing pilot results.

## Regenerate and validate

From this directory, with the pinned requirements installed:

```text
python generators/measurebench_ext/build_tasks.py --out tasks
python validate/measurebench_ext/run_validation.py --tasks tasks
```

No model APIs are needed or called by these commands.

## Results

- Determinism: PASS. Two builds created the same 50 task records, 30 images, questions, and answers.
- Automatic validation: PASS, 50 of 50 tasks.
- The Appendix checker found the task folder and all 50 task records in the ZIP. Required fields, relative image paths, numeric tolerances in the questions, automatic check results, and secret scanning all passed. There were no task-related warnings or failures.
- The ZIP checker reports seven expected member-export failures: the required archive-name pattern is for the final team submission; a root README, Dockerfile, README sections/Reported folders, model-result folder, and Docker commands belong to the later merged repository. Model evaluation was intentionally not run, so no current result folder is included. These are not task-field or secret failures.
- Running the checker directly on the Windows folder also exposed a path-separator issue in the checker (`--tasks tasks` is not recognized there). The ZIP form uses standard forward-slash entries and the checker resolves all 50 tasks correctly. The temporary `.venv`, determinism rebuild, and contact sheet are excluded from the ZIP.
- The unzipped working folder's prior `responses.jsonl` was mistaken for current evaluation output, producing results-schema/task-ID failures; this is prior pilot material, not a run from this job. The ZIP preserves the same file contents under `prior_openrouter_responses.jsonl` so it is not offered as a current results folder. The folder checker also reports temporary `.venv`/cache bloat, which is excluded from the ZIP.

## Known issues and merge decisions

- The original evaluator caps output at 128 tokens and lacks reasoning-effort and finish-reason handling; do not use it for the merged benchmark without a separate, approved integration step.
- All ten task types share the `measurebench_ext` namespace and package name. Prefix task IDs with a member name if another member uses the same prefix.
- The bundle pins Matplotlib and its runtime dependencies. No system package/font conflict is known; it uses bundled DejaVu Sans.
- Only one question type has prior pilot results. The other nine types remain unpiloted.
