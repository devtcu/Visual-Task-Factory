# Team 6 Visual Task Factory

This is the **seven-task preparation draft** requested by Team 6. It contains one selected task from each of seven working pipelines. Three additional tasks will be supplied later. Final model evaluation has deliberately not been run. This archive is ready to extend and reproduce; it is not the completed ten-task evaluation submission yet.

## Problem statement

The project creates reproducible visual reasoning tasks from structured data, computes reference answers in code, and checks the delivered images and answers. The seven pipelines cover industrial process control, fiber connectivity, EEG reading, roadway earthwork, invoice reconciliation, instrument reading, and spatial reconstruction.

## How the pipeline works

`selection.json` records the pipeline, question type, and seed for each reported task. `factory.py` dispatches to the member adapters, runs the checks in `validate/`, writes standard task records, and records image/data fingerprints. The shared evaluator in `eval/` sends only the question, response instructions, and required images to the models. It scores replies using the declared answer type and tolerance; spatial reconstruction uses its own geometry-aware scoring.

| Pipeline | Selected task | Seed |
|---|---|---:|
| SPC charts | First signal among six filling heads | 401 |
| Fiber patching | Trace a port through two MTP trunks | 22 |
| Brain documents | Locate an EEG sharp wave by phase reversal | 306 |
| Roadway cross sections | Identify the interval with the largest cut volume | 20260707 |
| Finance reconciliation | Calculate merchandise overcharge across the document packet | 2400 |
| MeasureBench | Compare two gauge readings and give the signed change | 6 |
| Visual reconstruction | Place five transformed patches using scene context | 20261114 |

Received tennis artifacts were excluded at Team 6's request because the generator source was missing. The adapters retain additional supported question types, but this draft reports exactly one task per pipeline.

## Reported folders

- Task folder: `tasks/final`
- Results folder: `results/final`

`results/final/run_config.json` is an explicitly marked planned configuration. There are no final model responses in this draft. The primary `image` is a complete view of the task. When a record has an additional `images` array, the evaluator sends those full-resolution component images in their stated order; for finance this is the six-page packet. This input choice is saved in evaluation logs.

## Pilot results

The supplied historical runs inform the project, but they used earlier task versions and sometimes different model routes/settings. They are preserved under `prior_results/` with their original member notes under `member_notes/`.

- Akhil's SPC v1.1 pilot: Claude 4/20 and GPT 2/20 correct. Fiber v3: Claude 8/16 and GPT 2/16. The brain spike pilot reported Claude 2/8 and GPT 6/8. Cross sections were comparatively easy. These are member-reported historical measurements.
- Finance's prior focused set reported GPT 10/12 and Claude 5/12. Review found an unstated unit-rounding convention that explains several marked misses. The repaired questions now state the policy, so those scores must not be attributed to the revised tasks.
- MeasureBench's saved counterfactual pilot used Claude Sonnet 4.5 and reported 1/9 through each of two routes. It did not evaluate the required final pair of models. The current generator varies the signed change and repairs the cylinder scale; the old scores do not measure this revision.
- Reconstruction's old five-hole pilot reported Claude 0/50 fully correct placements and GPT 19/45 over nine completed instances. Exact transform scoring and fixed answers were flawed. Revised scoring accepts equivalent transforms, and the generator varies labels, positions, and transforms. Prior failures are not clean difficulty evidence for this version.

No new model API calls were made to assemble this draft. After the other three tasks arrive, evaluate the fixed ten-task set consistently and report all twenty complete responses.

## How the tasks were made hard and what made the models fail

Tasks require following crossing chart lines, composing connectivity rules, interpreting waveform phase reversals, integrating cross-section geometry, reconciling dated financial rules, reading instrument scales, or matching transformed image regions. The merge corrects unfairness and answer defects before claiming difficulty. Current model failures and findings will be filled from the final evaluation, rather than inferred from obsolete pilot results.

## Key findings

Format checks alone did not detect the incorrect cylinder scale, hidden finance rounding policy, weak brain checks, or equivalent spatial transformations. The repaired validators check independent numerical logic and the actual delivered image content. Reproduction fingerprints guard against changes in questions, answers, images, and data.

## Hand-check notes

The [per-task review notes](HANDCHECK.md) and [offline task gallery](review.html) cover the seven delivered tasks. These are Codex-assisted visual inspections and independent numerical checks, not human team signoff or model scores. Automatic validation results are stored in `tasks/final/validation.json`. Add the remaining three reviews when those tasks arrive and have Team 6 inspect the final set before upload.

| Task ID | Review finding |
|---|---|
| `akhil_heads_401` | H1's eight samples below the center line first signal at sample 29; markers and labels are visible. |
| `akhil_fiber_trace_22` | Both Type C polarity swaps give route 03 -> 11 -> 12 -> 01 -> 02 -> 08; port labels and crossing cords are visible. |
| `akhil_brain_p306_spike` | Opposite deflections in T3-T5 and T5-O1 identify T5; the blink is separate. |
| `akhil_xsec_hard_max_cut_interval_20260707` | Interval 15+75-16+50 has approximately 1,908.062 cubic yards of cut, exceeding the runner-up by 346.078. Review the dense sheet at full resolution. |
| `fin-02400-pri-h-L0` | All six pages inspected. Dated PO rules and rounded unit differences yield $0.36 + $3.92 + $0.87 = $5.15. |
| `measurebench_ext_analog_dial_one_tick_counterfactual_0006` | Visible readings A=3.0 and B=2.4 bar give signed change -0.6 bar. |
| `visual_reconstruction_global_spatial_reconstruction_s20261114` | H1-H5 labels, rulers, and candidates are readable; independent pixel matching verifies the five placements and equivalent-transform scoring. |

## Reused components

Original member code and historical notes are retained with attribution in `member_notes/`. The shared pipeline uses Python, NumPy, Matplotlib, Pillow, SciPy, Shapely, Requests, and Playwright/Chromium. Visual references appear in each record and the member `REFERENCES.md` files. The reconstruction photograph is by Warren LeMay under CC BY-SA 4.0; its attribution and license files remain beside the source asset. Preserve these terms in any redistribution. The supplied organizer checker is included unchanged in `tools/check_submission.py`.

## Manual interventions

Codex assisted with adapting and merging the member code, fixing validation/scoring defects, adding visible rounding and coordinate conventions, normalizing dependencies, and building the Docker workflow. Source changes are implemented in the generators/validators so future tasks reproduce them. Generated answers are not hand-corrected. The seven initial pipeline/seed choices are recorded in `selection.json`; model results were not used to cherry-pick revised tasks.

## Limitations

- Three final tasks and all final evaluation responses are pending by Team 6's instruction.
- Prior results concern earlier versions. They cannot establish the revised set's accuracy or difficulty.
- Reconstruction currently uses one licensed photograph; a real-world training/application purpose and broader source diversity should be discussed in the demo.
- Cross-section generation can reject seeds under readability/sensitivity checks. The selected seed passes; arbitrary fresh seeds may need replacement with the actual seed recorded.
- Image reproduction is established in the pinned Linux Docker environment. Host-native Windows rendering is not the submission's reproduction contract.
- Some model registry entries omit temperature support. The evaluator requests temperature 0 per the brief and records the registry and actual request; it does not silently claim to verify a provider's internal temperature handling.
- Human contributor names beyond Akhil were not included in the handoff filenames. Replace the role labels below with the actual names before final upload.

## Team contributions

- Akhil: SPC, fiber, brain, and cross-section pipeline bundle, earlier pilots, and task documentation. The cross-section source was identified as another teammate's work in his handoff; confirm the original author's name.
- Finance contributor: synthetic business documents, reconciliation generator, and earlier finance pilots.
- MeasureBench contributor: instrument renderers, question templates, and earlier gauge pilot.
- Reconstruction contributor: photo reconstruction generator, source attribution, and earlier spatial pilots.
- Team 6 merge owner, assisted by Codex: shared adapters/CLI, validation and scoring repairs, Docker reproduction, and submission assembly.

## Run in Docker

Run these commands from the extracted repository root. Only Docker is required on the host. The volume keeps generated artifacts outside the container. The first commands build and reproduce the current seven-task draft without an API key.

```bash
docker build -t team6-track2:latest .
docker run --rm -v "${PWD}/out:/app/out" team6-track2:latest --build-reported --verify-reported --out /app/out
docker run --rm -v "${PWD}/out:/app/out" team6-track2:latest --fresh --pipeline fiber --seed 7001 --out /app/out
```

The selected seeds are in `selection.json`. For one fresh task, choose `--pipeline` from `spc`, `fiber`, `brain`, `cross_sections`, `finance`, `measurebench`, or `reconstruction`; use `--question-type` to select a supported variant. The output record always retains the actual seed and generator version.

After the other three tasks have been incorporated and the final fingerprints refreshed, run both required models through OpenRouter. The key must already be set in the host environment. Docker passes its value at runtime; it is not included in the image or ZIP.

```bash
docker run --rm -e OPENROUTER_API_KEY -v "${PWD}/out:/app/out" team6-track2:latest --build-reported --verify-reported --evaluate --out /app/out
docker run --rm -e OPENROUTER_API_KEY -v "${PWD}/out:/app/out" team6-track2:latest --fresh --pipeline fiber --seed 7001 --evaluate --out /app/out
```

Both models run by default. `--model anthropic/claude-haiku-5.5` or `--model openai/gpt-6-luna` selects one for a separate diagnostic run. Final evaluation requires both. Settings are temperature 0, high reasoning, and a common 32,768-token cap. If that cap changes, rerun the whole set; the cache fingerprint includes settings, prompts, and image bytes. Incomplete runs do not produce a purported complete responses file.

Outputs land in `out/tasks/final`, `out/results/final`, and `out/evidence`; fresh examples use `out/tasks/fresh` and `out/results/fresh`. When assembling the final upload, copy the completed reported tasks/results/evidence back into the matching repository folders, run the checker on the final ZIP, and include all required member names. A Docker image TAR or registry upload is not required by the supplied Track 2 brief; the Dockerfile rebuilds the image.

## Adding the remaining three tasks

Add their generator/validator adapters and registry entries if they introduce new pipelines. Append exactly three specs to `selection.json`, regenerate and validate all ten in Docker, freeze the new fingerprints, inspect all ten images, and then evaluate the complete set. Do not copy pilot CSVs into final results or fabricate missing response rows. `COMPLETION_STATUS.json` tracks the intentionally pending work.

After updating the reported task records, refresh the offline gallery with `python tools/build_review.py`. Build a clean archive with `python tools/package_submission.py --out ../Team6_Track2.zip`. These optional packaging utilities require Python; generating and evaluating tasks requires only Docker on the host.

Run the organizer's unchanged checker inside Linux Docker. Its use of native path separators produces false folder errors on Windows, including when inspecting a ZIP.

```bash
docker run --rm --entrypoint python -v "${PWD}/../Team6_Track2.zip:/input/Team6_Track2.zip:ro" team6-track2:latest tools/check_submission.py /input/Team6_Track2.zip
```

The seven-task draft's actual ZIP check reports 24 passes, one warning (7 of the final 10 tasks), and one failure (final responses are intentionally absent). Those two pending items prevent final upload until the other tasks and evaluation are added. `evidence/README.md` explains the generation, scoring, reproduction, and format checks.
