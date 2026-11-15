# Pipeline inventory

## Domain and image type

Real-photo spatial reconstruction: a masked photograph plus a shuffled candidate sheet of square image patches. Patches include genuine missing regions and same-photo distractors. Genuine pieces may be rotated or reflected. The source image is Warren LeMay's Urban Lab Building photograph (Wikimedia Commons, CC BY-SA 4.0). It imitates visual jigsaw, image restoration, and scene-context reasoning tasks.

## Entry points

- Generate one source puzzle: `py -3.12 generate.py --seed N --holes 5 --out PATH` (latest five-hole path). The default generator still makes eight holes unless `--holes 5` is passed.
- Score a saved model prediction: `py -3.12 score.py PREDICTION.json --run RUN_DIR`.
- Existing model evaluation code: `py -3.12 evaluate.py --run RUN_DIR --max-tokens 32768 --reasoning-effort high`; requires `OPENROUTER_API_KEY`. This evaluation was not run for this handoff.
- The source code does not yet implement the standard member `generate_task` / `validate_task` interface. The handoff adds a thin adapter and independent validation wrapper.

## Question and answer types

One question type: identify each real patch among distractors, match it to one of five holes, infer undo rotation and reflection, and estimate its center in the original photograph. The reference answer is a JSON sequence of placement objects. The prompt states a 30-pixel center tolerance. The scorer also reports piece identity, correspondence, orientation, mask IoU, and full reconstruction.

## Language, runtime, and dependencies

- Python 3.12.7
- Pillow 11.1.0
- NumPy 1.26.4
- System fonts: the original generator tries Arial and falls back. The handoff copy uses Pillow's bundled font at a fixed size for candidate labels, so no system font or apt package is required.

## What works

The copied generator uses a seeded RNG, emits uniform 520x520 square patches, produces shuffled candidates and a private answer key, checks reversible transforms and exact oracle reconstruction, and accepts five holes. The five-hole seeded instances already evaluated in the source project completed automatic generation QA. Existing pilot logs and score files are retained in the source project.

## Broken or unfinished

- The source generator is tied to one fixed licensed photograph and emits its own run-directory layout rather than the standard task record.
- The original prompt describes two separate model images. The adapter makes a single labeled composite image to fit the required `image` field.
- The standard adapter composites the generator's two original images into one task image; the existing evaluator is not yet wired to the standard task-record format.
- The checked-in README's evaluation command/settings are stale relative to the current evaluator defaults; the handoff records the actual prior settings from saved run configs.
- Only one photo source and one reasoning template are represented; this is not a cross-photo benchmark.
- The ten five-hole puzzles in source results share that one source image. Instance 10 has no completed GPT-6 Luna answer.
