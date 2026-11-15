# Pipeline inventory

## Domain and generated images

This is a procedural instrument-reading benchmark in Python. The copied source is `generators/measurebench_ext/cli.py` and its local renderer registry. It draws analog pressure gauges, two-gauge composite panels, graduated-cylinder menisci, and vernier calipers with Matplotlib. WIKA pressure-gauge catalog pages and Mitutoyo caliper catalog pages are the source's stated visual-convention references. The glassware task is a conventional 100 mL graduated cylinder with a concave meniscus; ISO 4788 is cited for graduated-cylinder conventions. All benchmark images are drawn from generated numeric data; no reference photographs are copied.

## Entry points

- Standard member interface: `generators/measurebench_ext/adapter.py` (`generate_task`, `validate_task`).
- Build the 50-record, five-per-question-type set: `python generators/measurebench_ext/build_tasks.py --out tasks`.
- Run member validation: `python validate/measurebench_ext/run_validation.py --tasks tasks`.
- Original CLI copied as-is: `python -m measurebench_ext.cli list`, `generate`, `verify`, and `report`, with `PYTHONPATH=generators` when run from this bundle.
- The original `evaluate_run` function is present in the copied CLI. It is OpenRouter-only. It is documented here but was not run for this handoff.

## Question types and reasoning

| Question type | Instrument | Required reasoning |
|---|---|---|
| `analog_dial_single_reading` | Analog gauge | Read the needle against the numbered bar scale. |
| `analog_dial_precision` | Analog gauge | Interpolate to the nearest marked minor division. |
| `analog_dial_one_tick_counterfactual` | Paired analog gauges | Compare the left A gauge to the right B gauge and compute the increase. |
| `vernier_single_reading` | Vernier caliper | Read the jaw opening in centimeters. |
| `vernier_precision` | Vernier caliper | Resolve the indicated 0.01 cm division. |
| `meniscus_single_reading` | Graduated cylinder | Read the volume from the depicted scale. |
| `meniscus_meniscus_convention` | Graduated cylinder | Apply the bottom-of-concave-meniscus convention and use the nearest 5 mL mark. |
| `composite_panel_single_reading` | Two-gauge panel | Read the first pressure gauge. |
| `composite_panel_comparison` | Two-gauge panel | Compare readings and return the higher gauge's label. |
| `composite_panel_difference` | Two-gauge panel | Subtract the readings and report the difference to the nearest 0.2 bar. |

## Answer types and tolerance

Answers use `number`, `integer`, and `label`. The adapter preserves the source numeric values and derives answers from the structured values. For non-integer numeric questions, tolerance is absolute and also stated in the question: analog gauge ±0.099 bar, one-tick comparison ±0.099 bar, vernier ±0.0049 cm, and composite gauge reading/difference ±0.099 bar. Meniscus questions select an integer reading at the nearest 5 mL graduation; they do not interpolate. Gauge comparison answers are exact labels.

## Language, dependencies, and system requirements

- Language: Python. Tested here with Python 3.13.5.
- Runtime dependency: Matplotlib, pinned with its installed runtime dependencies in `requirements.txt` (Matplotlib 3.10.9).
- Renderer fonts: Matplotlib's bundled DejaVu Sans. `system_packages.txt` is empty; no additional apt packages were required for the tested Matplotlib wheel.
- Source tests import pytest, but the handoff uses the adapter's automatic validation workflow and does not copy or run those tests.

## What works and what is unfinished

- All four source generators render from seeded values. The original `verify_run` checks source-image hashes and several instrument-to-geometry mappings.
- The adapter adds the required task schema, stated numeric tolerances, a single side-by-side image for the existing two-image counterfactual question, saved source data, independent answer recomputation, and per-task validation results.
- The 50 generated tasks validate; rebuilding in the same pinned environment reproduces all images, questions, and answers byte-for-byte.
- Existing pilot results cover only `one_tick_counterfactual` (nine examples per API route). No prior pilot data exists for the other nine question types.
- The original evaluator is unfinished relative to the later merged-evaluation plan: it calls only OpenRouter, fixes `max_tokens` at 128, does not set reasoning effort, and does not persist `finish_reason` as a separate field. It was not run during this packaging job.
- Meniscus values are deliberately located on 5 mL marks, so those questions test mark selection and reading convention rather than interpolation.
