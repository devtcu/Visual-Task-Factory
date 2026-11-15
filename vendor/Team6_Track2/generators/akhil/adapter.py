"""Standard interface over Akhil's four generators (thin wrappers; generator logic unchanged).

Families: factory heads (6 crossing control-chart lines), fiber v3 (5-stage patching with 2 MTP trunks),
brain (sleep study + EEG), xsec (roadway cut/fill cross sections, a teammate's generator packaged here).
Tennis 3D has no generator code, so it is not in QUESTION_TYPES (finished tasks only, see REPORT.md).
"""
import json
import os

GENERATOR_VERSION = "akhil-team6-2.0"
QUESTION_TYPES = [
    "heads_first_signal",
    "fiber_trace", "fiber_fault",
    "brain_rem_latency", "brain_awakenings", "brain_spike_location", "brain_report_audit", "brain_find_fix",
    "xsec_cut_total_easy", "xsec_cut_total_medium", "xsec_cut_total_hard", "xsec_max_cut_interval_hard",
]
BRAIN_SUFFIX = {"brain_rem_latency": "rem_latency", "brain_awakenings": "awakenings", "brain_spike_location": "spike",
                "brain_report_audit": "audit", "brain_find_fix": "find_fix"}


def _dirs(out_dir):
    os.makedirs(os.path.join(out_dir, "images"), exist_ok=True)
    os.makedirs(os.path.join(out_dir, "data"), exist_ok=True)


def _save(out_dir, task_id, data):
    rel = f"data/{task_id}.json"
    json.dump(data, open(os.path.join(out_dir, rel), "w", encoding="utf-8"), indent=1)
    return rel


def _heads(seed, out_dir):
    from . import factory_heads as F
    d = F.shift(seed)
    tid = f"akhil_heads_{seed}"
    img = f"images/{tid}.png"
    F.draw(d, os.path.join(out_dir, img))
    h, sm = d["answer_head"], d["answer_sample"]
    r1 = [(f, i + 1) for i, f in enumerate(d["rule1_by_head"]) if f]
    traps = {"obvious_event": d["obvious_event"], "rule1_only": list(min(r1)[::-1]) if r1 else None,
             "one_early": [h, sm - 1], "one_late": [h, sm + 1],
             "biggest_point": [d["biggest_point"]["head"], d["biggest_point"]["sample"]]}
    return dict(task_id=tid, image=img, question=F.QUESTION, answer=[h, sm], answer_type="sequence",
                question_type="heads_first_signal", seed=seed, generator_version=F.GEN_VERSION,
                data=_save(out_dir, tid, d), traps={k: v for k, v in traps.items() if v and v != [h, sm]},
                scoring_note="sequence [head, sample]; our eval parses 'head, sample' (score.py int_pair)")


def _fiber(seed, mode, out_dir):
    from . import fiber_v3 as V
    d = V.make(seed)
    tid = f"akhil_fiber_{mode}_{seed}"
    img = f"images/{tid}.png"
    V.render(d, os.path.join(out_dir, img), mode)
    q = V.Q_TRACE.format(src=d["trace"]["source_port"]) if mode == "trace" else V.Q_FAULT
    return dict(task_id=tid, image=img, question=q, answer=d[mode]["answer"], answer_type="integer",
                question_type=f"fiber_{mode}", seed=seed, generator_version=V.VERSION, data=_save(out_dir, tid, d),
                traps=d[mode]["traps"], trunks=d["trunk1"] + d["trunk2"])


def _brain(seed, qtype, out_dir):
    from . import brain_factory as BF
    sub = os.path.join(out_dir, "_brain_work", str(seed))
    tasks, _ = BF.tasks_for(seed, sub)
    t = next(x for x in tasks if x["task_id"].endswith("_" + BRAIN_SUFFIX[qtype]))
    tid = f"akhil_{t['task_id']}"
    imgs = []
    for k, rel in enumerate(t["images"]):                       # copy images to images/<task_id>[_k].png
        name = f"images/{tid}.png" if k == 0 else f"images/{tid}_{k + 1}.png"
        with open(os.path.join(sub, rel), "rb") as a, open(os.path.join(out_dir, name), "wb") as b:
            b.write(a.read())
        imgs.append(name)
    data = json.load(open(os.path.join(sub, t["data"]), encoding="utf-8"))
    rec = dict(task_id=tid, image=imgs[0], question=t["question"], answer=t["answer"], answer_type=t["answer_type"],
               question_type=qtype, seed=seed, generator_version=BF.GEN_VERSION, data=_save(out_dir, tid, data),
               traps=t.get("traps", {}))
    if len(imgs) > 1:
        rec["images"] = imgs
    if "tolerance_abs" in t:
        rec["tolerance_abs"] = t["tolerance_abs"]
    if rec["answer_type"] == "sequence" and not isinstance(rec["answer"], list):
        rec["answer"] = [rec["answer"]]
    return rec


def _xsec(seed, qtype, out_dir):
    from .xsecgen import xsec as X, render as R
    import numpy as np
    level = qtype.rsplit("_", 1)[1]
    base = "max_cut_interval" if "max_cut" in qtype else "cut_total"
    data = X.make_data(seed, level)
    data["noise"] = 0.0      # adapter change: noisy PNGs are ~16 MB, over Anthropic's 10 MB image limit (see REPORT.md)
    q = X.make_question(data, base, np.random.default_rng([seed, 7]))
    tid = f"akhil_xsec_{level}_{base}_{seed}"
    img = f"images/{tid}.png"
    R.render_sheet(data, os.path.join(out_dir, img))
    rec = dict(task_id=tid, image=img, question=q["question"], answer=q["answer"], answer_type=q["answer_type"],
               question_type=qtype, seed=seed, generator_version=X.GEN_VERSION, data=_save(out_dir, tid, data),
               qspec={k: q[k] for k in ("qtype", "key", "from_sta", "to_sta")}, level=level)
    if "tolerance_rel" in q:
        rec["tolerance_rel"] = q["tolerance_rel"]
    return rec


def generate_task(seed, question_type=None, out_dir="."):
    """Deterministic: same seed + question_type -> identical image, question, answer."""
    question_type = question_type or "heads_first_signal"
    if question_type not in QUESTION_TYPES:
        raise ValueError(f"unknown question_type {question_type}")
    _dirs(out_dir)
    import matplotlib
    # Each task renders with matplotlib defaults, so no task leaks global state into the next
    # (xsec's renderer sets rcParams["font.family"], which made later charts depend on build order).
    with matplotlib.rc_context(matplotlib.rcParamsDefault):
        task = _generate(seed, question_type, out_dir)
        task["generator_version"] += "+team6.2"
        return task


def _generate(seed, question_type, out_dir):
    if question_type == "heads_first_signal":
        return _heads(seed, out_dir)
    if question_type.startswith("fiber_"):
        return _fiber(seed, question_type.split("_")[1], out_dir)
    if question_type.startswith("brain_"):
        return _brain(seed, question_type, out_dir)
    return _xsec(seed, question_type, out_dir)


def validate_task(task, out_dir="."):
    import sys
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if root not in sys.path:
        sys.path.insert(0, root)
    from validate.akhil import checks
    return checks.validate(task, out_dir)
