# Inventory: Akhil's pipelines (HACKATHON repo)

| Family | Image type / imitates | Original code | Question types | Answer types / tolerance | Status |
|---|---|---|---|---|---|
| Factory heads | Per-head SPC individuals chart (rotary filler) | `generate/factory_heads.py` (+ `generate/factory.py` for the rules and the easy rung) | heads_first_signal | sequence [head, sample], exact | Works; hard (pilot 4/20, 2/20) |
| Fiber v3 | Data-centre fiber patching as-built, 2 MTP trunks | `tasks/fiber/generate_v3.py` | fiber_trace, fiber_fault | integer port, exact | Works; hard |
| Brain | PSG hypnogram, PSG report, bipolar EEG page | `generate/brain_factory.py` + `generate/brain_samples.py` | rem_latency, awakenings, spike_location, report_audit, find_fix | number (±5 min abs), integer, label, sequence | Works; spike hard for Claude, rest easy |
| Cross sections (teammate code, packaged here) | DOT roadway cut/fill cross-section sheet | `xsec_task_factory/xsecgen` | cut_total (easy/medium/hard), max_cut_interval | number ±5% rel, label | Works with adapter fix (noise 0); easy; fill questions never pass its validator |
| Tennis v3 (received) | Side-view ball tracking, 17 frames | not available | speed, landing, in/out, apex, net, spin | number/label | Tasks only (10); easy (10/10, 9/10) |
| Tennis 3D (received) | 3 rendered camera views of one shot | not available | multiview_corner_call | number, ±5 or ±10 cm abs | Tasks only; generator code missing |

Entry points: `build.py` (generate + validate + determinism), `generators/akhil/adapter.py` (`generate_task`, `validate_task`),
`validate/akhil/checks.py` (+ `xsec_validate.py`, the teammate's validator), `eval/run.py` (our OpenRouter runner, not run in this job).
Language Python 3.12 (works on 3.11 per the xsec Dockerfile); deps in requirements.txt; no system packages (matplotlib bundles DejaVu fonts).
Broken/unfinished: tennis 3D generator missing; xsec fill questions fail the ±5% reading check; xsec original build is slow (seed search re-renders each candidate) and only writes tasks.jsonl at the end.
