"""Brain factory: one seed -> one new synthetic sleep-study patient, four documents, and five tasks.

The night follows normal adult sleep architecture (see docs/BRAIN-SET.md): sleep latency 8-25 min, ~90 min cycles,
N3 concentrated in the first two cycles, REM periods lengthening towards morning, brief arousals, a final awakening.
Each patient's report carries two planted bugs drawn from definition mix-ups that published polysomnography sources
actually disagree on (REM latency from lights out vs sleep onset; sleep efficiency denominator; WASO including the
final awakening; brief wakes not counted as awakenings) plus N3 mislabelled as N2. The report stays internally
consistent, so only the hypnogram reveals the bugs.
Run:  python generate/brain_factory.py tasks/brain_factory 201 202 203 204 205"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from . import brain_samples as B  # noqa: E402

GEN_VERSION = "brain-factory-1.0"
MIDDLE = ["F7", "T3", "T5", "F3", "C3", "P3", "F4", "C4", "P4", "F8", "T4", "T6"]   # phase reversal needs a chain middle
ROW_ORDER = ["Total recording time", "Total sleep time", "Sleep efficiency", "Sleep latency", "REM latency",
             "Wake after sleep onset", "Number of awakenings", "N1", "N2", "N3", "REM"]


def half(x):
    return round(x * 2) / 2                                    # 30 s epochs


def make_night(rng, total=480.0):
    night = [("W", half(rng.uniform(8, 25)))]
    night.append(("N1", half(rng.uniform(3, 8))))
    n_cycles = int(rng.integers(4, 6))
    for c in range(n_cycles):
        n3 = half(rng.uniform(25, 40)) if c == 0 else half(rng.uniform(15, 30)) if c == 1 else half(rng.uniform(0, 8))
        rem = half(min(45, rng.uniform(8, 14) + c * rng.uniform(5, 9)))
        n2a, n2b = half(rng.uniform(15, 30)), half(rng.uniform(8, 18))
        cyc = [("N2", n2a)] + ([("N3", n3)] if n3 >= 3 else []) + [("N2", n2b), ("R", rem)]
        if rng.random() < 0.55:                                  # brief arousal inside an N2 block
            i = 0 if rng.random() < 0.5 else len(cyc) - 2
            st, m = cyc[i]
            cut = half(m * rng.uniform(0.3, 0.7))
            cyc[i:i + 1] = [(st, cut), ("W", half(rng.uniform(1, 2))), (st, half(m - cut))]
        if c < n_cycles - 1 and rng.random() < 0.6:
            cyc.append(("W", half(rng.uniform(3, 12))))
            cyc.append(("N1", half(rng.uniform(2, 6))))
        night += cyc
    used = sum(m for _, m in night)
    final_w = half(rng.uniform(8, 35))
    scale = (total - final_w - night[0][1]) / (used - night[0][1])
    night = [night[0]] + [(s, max(0.5, half(m * scale)) if s != "W" or m > 2.5 else m) for s, m in night[1:]]
    night.append(("W", total - sum(m for _, m in night)))
    merged = []
    for s, m in night:
        if m <= 0:
            continue
        if merged and merged[-1][0] == s:
            merged[-1] = (s, merged[-1][1] + m)
        else:
            merged.append((s, m))
    return merged


def patient(seed):
    rng = np.random.default_rng(seed)
    p = B.patient(seed)
    p["patient_id"] = f"SL-{2000 + seed}"
    p["age"], p["sex"] = int(rng.integers(24, 71)), str(rng.choice(["F", "M"]))
    p["night"] = make_night(rng)
    sl = p["night"][0][1]
    m = int(rng.uniform(2, max(3, sl - 2)))
    p["eeg"]["start_clock"] = [23, m, int(rng.integers(0, 50))]                     # recorded during the first wake period
    p["eeg"]["spike"] = {"electrode": str(rng.choice(MIDDLE)), "time_s": round(float(rng.uniform(3.5, 8.5)), 2),
                         "peak_uv": float(-rng.uniform(85, 110)), "spread_uv": -35.0}
    p["eeg"]["blink_time_s"] = round(float(rng.uniform(1.0, 2.8)), 2)
    return p


def bugs(p, rng, mode="two"):
    """Returns plant dict (row prefix -> shown value), changed row names, and bug names; two bugs that clearly show."""
    s = B.night_stats(p)
    rows = s["rows"]
    final_w = rows[-1][2] - rows[-1][1] if rows[-1][0] == "W" else 0
    brief = sum(1 for st, a, b in rows if st == "W" and a > s["SL"] and b - a < 2.5)
    cands = []
    if final_w >= 8:
        cands.append(("waso_without_final_wake", {"Wake after sleep onset": s["WASO"] - final_w}, ["Wake after sleep onset"]))
    cands.append(("rem_latency_from_lights_out", {"REM latency": s["REML"] + s["SL"]}, ["REM latency"]))
    se_bad = round(100 * s["TST"] / (s["TRT"] - s["SL"]), 1)
    if se_bad - s["SE"] > 2:
        cands.append(("efficiency_over_sleep_period", {"Sleep efficiency": se_bad}, ["Sleep efficiency"]))
    if brief:
        cands.append(("brief_wakes_not_counted", {"Number of awakenings": s["awakenings"] - brief}, ["Number of awakenings"]))
    k = half(min(s["stage_min"]["N3"] - 5, rng.uniform(15, 25)))
    if k >= 10:
        cands.append(("n3_scored_as_n2", {"N2": s["stage_min"]["N2"] + k, "N3": s["stage_min"]["N3"] - k}, ["N2", "N3"]))
    arch = [c for c in cands if c[0] != "n3_scored_as_n2"]
    stage = [c for c in cands if c[0] == "n3_scored_as_n2"]
    waso = [c for c in cands if c[0] == "waso_without_final_wake"]
    subtle = [c for c in cands if c[0] in ("n3_scored_as_n2", "brief_wakes_not_counted")]
    if mode == "three":                      # audit: the bug models miss (WASO without final wake) + one more subtle bug;
        pool = waso + subtle                 # never the efficiency bug, which arithmetic on the report alone reveals
        pick = waso[:1] + ([subtle[int(rng.integers(len(subtle)))]] if subtle else [])
        if len(pick) < 2:
            pick = [cands[i] for i in rng.choice(len(cands), size=2, replace=False)]
    elif mode == "single_arch":              # find-and-fix: exactly one architecture bug (the subtle one), plus stage distractor
        pick = (waso or [arch[int(rng.integers(len(arch)))]])[:1] + stage
    else:
        pick = [cands[i] for i in rng.choice(len(cands), size=2, replace=False)]
    plant, changed = {}, []
    for _, pl, ch in pick:
        plant.update(pl); changed += ch
    return plant, [r for r in ROW_ORDER if r in changed], [n for n, _, _ in pick]


def tasks_for(seed, out_dir):
    rng = np.random.default_rng(seed + 1000)
    p = patient(seed)
    s = B.night_stats(p)
    plant, changed, bug_names = bugs(p, rng, "three")
    plant_a, changed_a, bug_a = bugs(p, rng, "single_arch")
    img = os.path.join(out_dir, "images")
    os.makedirs(img, exist_ok=True); os.makedirs(os.path.join(out_dir, "data"), exist_ok=True)
    f = {k: f"p{seed}_{k}.png" for k in ("eeg", "hypnogram", "report", "report_a")}
    B.draw_eeg(p, os.path.join(img, f["eeg"]))
    B.draw_hypnogram(p, os.path.join(img, f["hypnogram"]))
    B.draw_report(p, os.path.join(img, f["report"]), plant)
    B.draw_report(p, os.path.join(img, f["report_a"]), plant_a)
    sp = p["eeg"]["spike"]["electrode"]
    nb = sorted({n for c in B.CHAINS for i, n in enumerate(c) if sp in c[max(0, i - 1):i + 2] and n != sp})
    mirror = sp.translate(str.maketrans("13572468", "24681357")) if sp[-1].isdigit() else sp
    true_val = {"Wake after sleep onset": s["WASO"], "REM latency": s["REML"], "Sleep efficiency": s["SE"],
                "Number of awakenings": s["awakenings"], "N2": s["stage_min"]["N2"], "N3": s["stage_min"]["N3"]}
    first = [r for r in changed_a if r not in ("N2", "N3")][0]
    tol = {"Sleep efficiency": 2, "Number of awakenings": 0}.get(first, 6)
    data_rel = f"data/p{seed}.json"
    st = dict(s); st.pop("rows")
    json.dump({"patient": p, "true_values": st, "report_audit": {"planted": plant, "bugs": bug_names, "changed_rows": changed},
               "report_a": {"planted": plant_a, "bugs": bug_a, "changed_rows": changed_a}},
              open(os.path.join(out_dir, data_rel), "w"), indent=1)
    intro = ("Image 1 is a polysomnography summary report and image 2 is the hypnogram it was produced from "
             "(30-second epochs). ")
    base = {"seed": seed, "generator_version": GEN_VERSION, "data": data_rel}
    T = [
        {"task_id": f"brain_p{seed}_rem_latency", "level": "easy", "images": [f"images/{f['hypnogram']}"], "answer_type": "number",
         "tolerance_abs": 5, "answer": s["REML"], "question_type": "rem_latency",
         "question": "REM latency is the time from sleep onset (the first epoch scored as any sleep stage) to the first epoch "
                     "scored as REM. What is the REM latency on this hypnogram, in minutes? Answers within ±5 are accepted.",
         "traps": {"from_lights_out": s["REML"] + s["SL"], "second_rem": s["second_REM_from_onset"]}},
        {"task_id": f"brain_p{seed}_awakenings", "level": "medium", "images": [f"images/{f['hypnogram']}"], "answer_type": "integer",
         "answer": s["awakenings"], "question_type": "awakenings",
         "question": "An awakening is any period scored W that starts after sleep onset (the first epoch of any sleep stage), "
                     "however short, including a final awakening that lasts until lights on. How many awakenings are there?",
         "traps": {"missed_brief": s["awakenings"] - sum(1 for x, a, b in s["rows"] if x == "W" and a > s["SL"] and b - a < 2.5),
                   "excluded_final": s["awakenings"] - 1, "counted_initial": s["awakenings"] + 1}},
        {"task_id": f"brain_p{seed}_spike", "level": "medium", "images": [f"images/{f['eeg']}"], "answer_type": "label",
         "answer": sp, "question_type": "spike_location",
         "question": "This EEG page uses a longitudinal bipolar montage: each channel shows the first electrode minus the second, "
                     "and negative is drawn upward. One focal sharp wave appears on this page (ignore the eye blink in the "
                     "frontopolar channels). A sharp wave that deflects in opposite directions in two neighbouring channels of "
                     "the same chain (a phase reversal) is located at the electrode those two channels share. At which electrode "
                     "is the sharp wave located?",
         "traps": {**{f"neighbour_{n}": n for n in nb}, f"mirror_{mirror}": mirror, "midline_Cz": "Cz"}},
        {"task_id": f"brain_p{seed}_audit", "level": "hard", "images": [f"images/{f['report']}", f"images/{f['hypnogram']}"],
         "answer_type": "sequence", "answer": changed, "question_type": "report_audit",
         "question": intro + "Using the definitions printed in the report, check every row of the 'Sleep architecture' and "
                     "'Sleep stages' tables against the hypnogram. Which rows contain a value that differs from the hypnogram "
                     "by more than 5 minutes, more than 2 percentage points, or any amount for a count? List the row names in "
                     "the order they appear, separated by commas, without the part in brackets. If every row matches, answer none.",
         "traps": {"trusted_report": ["none"], **{f"missed_{c.replace(' ', '_')}": [r for r in changed if r != c] for c in changed}}},
        {"task_id": f"brain_p{seed}_find_fix", "level": "hard", "images": [f"images/{f['report_a']}", f"images/{f['hypnogram']}"],
         "answer_type": "integer" if tol == 0 else "number", "answer": true_val[first], "question_type": "report_find_and_fix",
         "question": intro + "Exactly one value in the 'Sleep architecture' table does not match the hypnogram (the 'Sleep "
                     "stages' table may also contain errors; ignore it). Using the definitions printed in the report, find that "
                     "value and give its correct value from the hypnogram. Answer with the number only."
                     + ("" if tol == 0 else f" Answers within ±{tol} are accepted."),
         "traps": {"kept_printed_value": plant_a.get(first), **{f"other_row_{k.replace(' ', '_')}": v for k, v in
                   {"REM latency": s["REML"], "Wake after sleep onset": s["WASO"], "Sleep latency": s["SL"]}.items() if k != first}}},
    ]
    for t in T:
        t["image"] = t["images"][0]
        if t["answer_type"] == "number":
            t.setdefault("tolerance_abs", tol)
        t.update(base)
    return T, bug_names


if __name__ == "__main__":
    out = sys.argv[1]
    seeds = [int(x) for x in sys.argv[2:]] or [201, 202, 203, 204, 205]
    allt = []
    for sd in seeds:
        t, bn = tasks_for(sd, out)
        allt += t
        print(sd, "bugs:", bn, "| audit answer:", t[3]["answer"], "| spike:", t[2]["answer"])
    with open(os.path.join(out, "tasks.jsonl"), "w", encoding="utf-8") as fh:
        for t in allt:
            fh.write(json.dumps(t, ensure_ascii=False) + "\n")
    print(len(allt), "tasks")
