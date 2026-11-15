# Report: Akhil's handoff bundle (Mode A, member export)

**In the bundle:** 4 generator families behind one adapter (`generators/akhil/adapter.py`): factory heads, fiber v3,
brain, cross sections (teammate's code, packaged). 12 question types, **44 tasks, 44 valid, deterministic**.
**Tennis (2 sets, received tasks only, no generator code in the repo):** `received/tennis3d/` (5 multi-camera line calls, hard:
Claude 0/5, GPT 1/5) and `received/tennis_v3/` (10 side-view ball-tracking tasks, easy: Claude 10/10, GPT 9/10). Their results
are in `prior_results/tennis3d/` and `prior_results/tennis_v3/`. To rebuild them from seeds, the tennis teammate must add
the generator (`tennis_3d.corner_task`); then it is a 10-minute adapter addition.

**Regenerate + validate + determinism:**
```
pip install -r requirements.txt
python build.py tasks --verify        # writes tasks/tasks.jsonl, images/, data/, determinism.json
```
One task: `python -c "from generators.akhil import adapter as A; print(A.generate_task(410, 'heads_first_signal', 'out'))"`

**Determinism:** two full rebuilds give identical SHA-256 for every image, question and answer (`tasks/determinism.json`).
First attempt was NOT deterministic: the xsec renderer sets `matplotlib.rcParams["font.family"]` globally, so charts built
after it in the same process changed font. Fixed in the adapter by rendering every task inside `matplotlib.rc_context(defaults)`.

**Validation:** `validate/akhil/checks.py` recomputes every answer with separate code (factory heads: own Western Electric
implementation; fiber: own permutation trace; brain: stored true values / spike electrode / changed rows; xsec: the teammate's
validator with dense integration, Shapely clipping, re-render pixel check, reading sensitivity). All 44 pass.

**Checker (official, on a zip of this folder):** task file passes every check (fields, tolerances stated in the question,
seed, generator_version, question_type, check results, data JSON, no secrets). Remaining FAILs are merged-repo items
expected at this stage: root README, Dockerfile, "Reported folders" section, Docker section. WARN: 44 tasks, not 10 (merge
picks 10). Note: run the checker on a ZIP on Windows; on a folder it builds backslash paths and wrongly reports missing folders.

**Eval:** not run in this job. `eval/` holds our runner (client.py, run.py, score.py: OpenRouter, temp 0, effort high,
max_tokens 32000, retries, raw logs) and the teammate's `xsec_run_eval.py`. Prior results (`prior_results/*.prior.csv`,
renamed so they are not mistaken for this bundle's results) used the same models and settings; see PILOT_NOTES.md.

**Decide when merging:**
- Pick the hard ones for the final 10: factory heads (16/20 fail both models in the pilot) and fiber v3 (8/16), plus brain p306/p308 spike.
- `score.py` here adds an `int_pair` answer type used in the pilot for heads; in this bundle heads answers are a standard `sequence`.
- `eval/` names (`client.py`, `run.py`, `score.py`) may collide with other members' eval code.
- Fonts: matplotlib's bundled DejaVu only; no system packages.
- Cross sections may also arrive from the teammate who wrote it: keep one copy (this one has the noise and determinism fixes).
