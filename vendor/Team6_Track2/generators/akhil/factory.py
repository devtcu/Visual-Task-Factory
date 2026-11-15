"""Factory family: one filling-line shift per (seed, level). See docs/FACTORY-SET.md.
Documents: individuals control chart, operator shift log. Questions: first_signal, count_beyond_2s, longest_run_above,
signal_time, cause_event (level 3+). Every answer comes from signals(), the rule checker, which reads only the weights.
Run:  python -m generate.factory tasks/factory --seeds 301-304 --levels 1-5"""
import argparse
import json
import os
import random

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

GEN_VERSION = "factory-1.0"
N_BY_LEVEL = {1: 25, 2: 25, 3: 50, 4: 75, 5: 100}
RULES_BY_LEVEL = {1: [1], 2: [1, 2], 3: [1, 2, 3, 4], 4: [1, 2, 3, 4], 5: [1, 2, 3, 4]}
MARGIN = 0.12          # every point is at least this many sigma from every drawn line (fairness: >= ~5 px)
PRODUCTS = [("Sparkling water 500 mL", "Filling line 3", 500.0, 2.0), ("Orange juice 1 L", "Filling line 1", 1000.0, 3.0),
            ("Cola 330 mL can", "Can line 2", 330.0, 1.5), ("Still water 1.5 L", "Filling line 5", 1500.0, 4.0)]
RULE_TEXT = {
    1: "Rule 1: one sample beyond 3 sigma (above UCL or below LCL). The signal is at that sample.",
    2: "Rule 2: two of any three consecutive samples beyond 2 sigma on the same side of the centre line. The signal is at the later of those two samples.",
    3: "Rule 3: four of any five consecutive samples beyond 1 sigma on the same side of the centre line. The signal is at the fourth of those samples.",
    4: "Rule 4: eight consecutive samples on the same side of the centre line. The signal is at the eighth sample.",
}
EVENTS_DECOY = ["Label roll changed", "Operator break cover (RT)", "Carton magazine refilled", "Cap hopper topped up",
                "Line stopped 4 min: jam at capper", "Date coder ink replaced", "Shift supervisor walk-round",
                "Conveyor guard re-latched", "Sample sent to lab (routine)"]
EVENTS_CAUSE = ["Nozzle 4 replaced", "Filler speed raised 600 to 660 bpm", "New CO2 cylinder connected",
                "Fill-height probe recalibrated", "Product tank switched to tank B", "Filler valve seals changed"]


# ------------------------------------------------------------------ the checker (independent of planting)
def signals(x, centre, sigma, rules):
    """Apply the printed rules point by point. Returns 1-based first signal (0 if none) and per-sample rule hits."""
    z = [(v - centre) / sigma for v in x]
    hits = []
    for i in range(len(z)):
        fired = []
        if 1 in rules and abs(z[i]) > 3:
            fired.append(1)
        for side in (1, -1):
            w3, w5, w8 = z[max(0, i - 2):i + 1], z[max(0, i - 4):i + 1], z[i - 7:i + 1] if i >= 7 else []
            if 2 in rules and side * z[i] > 2 and sum(side * v > 2 for v in w3) >= 2:
                fired.append(2)
            if 3 in rules and side * z[i] > 1 and sum(side * v > 1 for v in w5) >= 4:
                fired.append(3)
            if 4 in rules and len(w8) == 8 and all(side * v > 0 for v in w8):
                fired.append(4)
        hits.append(sorted(set(fired)))
    first = next((i + 1 for i, h in enumerate(hits) if h), 0)
    return {"first": first, "hits": hits, "z": z}


def longest_run(z, side):
    best = cur = 0
    for v in z:
        cur = cur + 1 if side * v > 0 else 0
        best = max(best, cur)
    return best


def clock(start_min, interval, n):
    t = (start_min + (n - 1) * interval) % 1440
    return f"{t // 60:02d}:{t % 60:02d}"


# ------------------------------------------------------------------ one shift
def _nudge(z, keep):
    """Move every non-decoy point at least MARGIN sigma away from each line (0, +-1, +-2, +-3)."""
    out = []
    for i, v in enumerate(z):
        if i not in keep:
            for line in (-3, -2, -1, 0, 1, 2, 3):
                if abs(v - line) < MARGIN:
                    v = line + (MARGIN if v >= line else -MARGIN)
        out.append(v)
    return out


def shift(seed, level):
    rng = random.Random(seed * 10 + level)
    product, line, centre, sigma = rng.choice(PRODUCTS)
    n, rules = N_BY_LEVEL[level], RULES_BY_LEVEL[level]
    start = rng.choice([6 * 60, 14 * 60, 22 * 60])      # 22:00 start crosses midnight
    interval = rng.choice([15, 20, 30])
    for _ in range(500):
        z = [max(-1.7, min(1.7, rng.gauss(0, 0.65))) for _ in range(n)]
        decoys, side = {}, rng.choice([1, -1])
        k = rng.randint(3, n - 12)                      # disturbance start, anywhere in the shift
        plan = "none"
        if level == 1:
            plan = rng.choice(["spike", "spike", "none"])
            if plan == "spike":
                z[k] = side * rng.uniform(3.2, 3.8)
        elif level == 2:
            plan = "pair"
            gap = rng.choice([1, 2])
            z[k], z[k + gap] = side * rng.uniform(2.2, 2.8), side * rng.uniform(2.2, 2.8)
            if gap == 2:
                z[k + 1] = -side * abs(z[k + 1])
            d = rng.randrange(1, k)                     # decoy just inside 2 sigma, earlier
            z[d] = rng.choice([1, -1]) * rng.uniform(1.8, 1.88); decoys[d] = "inside_2s"
            j = rng.randint(min(n - 1, k + gap + 3), n - 1)
            z[j] = -side * rng.uniform(3.2, 3.8)        # the obvious spike (rule 1) comes later
        else:
            plan = "shift"
            for i in range(k, min(n, k + 9)):           # mean shift: rule 3 or rule 4 fires
                z[i] = side * abs(rng.gauss(1.15, 0.45))
            for _d in range(min(3, level - 1)):          # decoys just inside 1 or 2 sigma
                d = rng.randrange(0, n)
                if k - 1 <= d <= k + 10:
                    continue
                lvl = rng.choice([1, 2])
                z[d] = rng.choice([1, -1]) * rng.uniform(lvl - .2, lvl - .1); decoys[d] = f"inside_{lvl}s"
            j = rng.randint(min(n - 1, k + 10), n - 1)
            z[j] = rng.choice([1, -1]) * rng.uniform(3.2, 3.8)
            taken = set(range(k - 3, k + 12)) | {j - 1, j, j + 1} | set(decoys)
            for _e in range(rng.randint(0, level)):      # isolated single excursions beyond 2 sigma
                e = rng.randrange(0, n)
                if any(q in taken for q in range(e - 3, e + 4)):
                    continue
                z[e] = rng.choice([1, -1]) * rng.uniform(2.15, 2.9); taken.add(e)
        z = _nudge(z, set(decoys))
        x = [round(centre + v * sigma, 2) for v in z]
        s = signals(x, centre, sigma, rules)
        r1 = signals(x, centre, sigma, [1])["first"]
        if plan == "none" and s["first"] != 0:
            continue
        if plan != "none" and s["first"] == 0:
            continue
        if level >= 2 and s["first"] == r1:            # the rule-1 trap must differ from the answer
            continue
        if any(abs(abs(v) - L) < MARGIN - 1e-9 for i, v in enumerate(s["z"]) if i not in decoys for L in (1, 2, 3)):
            continue                                    # rounding pushed a point too close to a line
        break
    else:
        raise RuntimeError(f"no valid shift for seed {seed} level {level}")
    d = {"seed": seed, "level": level, "generator_version": GEN_VERSION, "product": product, "line": line, "unit": "g",
         "centre": centre, "sigma": sigma, "start": clock(start, 1, 1), "start_min": start, "interval_min": interval,
         "rules": rules, "samples": x, "planted": {"type": plan, "start_sample": k + 1 if plan != "none" else None,
                                                 "decoys": {str(i + 1): v for i, v in decoys.items()}}}
    if level >= 3:
        d["log"] = make_log(d, s["first"], r1, rng)
    return d


def make_log(d, first, r1, rng):
    """Events with clock times between samples. The cause is the last event before the first signal."""
    st, iv, n = d["start_min"], d["interval_min"], len(d["samples"])
    t_sig = st + (first - 1) * iv
    used, ev = set(), []

    def add(t, text, role):
        t = max(st + 1, min(st + (n - 1) * iv - 1, t))
        if t % iv == st % iv or t in used:                 # never exactly on a sample time
            t += 3
        used.add(t); ev.append({"t": t, "text": text, "role": role})

    cause, *decoy = rng.sample(EVENTS_CAUSE, 1) + rng.sample(EVENTS_DECOY, 5)
    add(t_sig - rng.randint(1, iv * 3 - 2), cause, "cause")
    add(t_sig + rng.randint(2, iv - 2), decoy[0], "just_after_signal")
    if r1 > first:
        add(st + (r1 - 1) * iv - rng.randint(2, iv - 2), decoy[1], "before_rule1_spike")
    else:
        add(t_sig + iv * 4 + 7, decoy[1], "later")
    for txt in decoy[2:]:
        add(st + rng.randint(5, (n - 1) * iv - 5), txt, "other")
    ev = [e for e in ev if not (e["role"] == "other" and t_sig - iv * 3 <= e["t"] < t_sig + iv)]
    ev.sort(key=lambda e: e["t"])
    before = [e for e in ev if e["t"] < t_sig]
    assert before and before[-1]["role"] == "cause", "cause must be the last event before the signal"
    for e in ev:
        e["time"] = clock(e["t"], 1, 1)
        e["initials"] = rng.choice(["JM", "AK", "RT", "SP", "LD"])
    return ev


# ------------------------------------------------------------------ drawing
def draw_chart(d, path, style="zones"):
    c, s, y = d["centre"], d["sigma"], d["samples"]
    n = len(y)
    fig, ax = plt.subplots(figsize=(max(10, n * 0.17), 5.6))
    xs = list(range(1, n + 1))
    ax.plot(xs, y, color="#1b3a5c", lw=1.2, marker="o", ms=4.2 if n > 50 else 5, zorder=3)
    lines = ((3, "-", "UCL +3s"), (2, "--", "+2 sigma"), (1, ":", "+1 sigma"), (0, "-", "CL"),
             (-1, ":", "-1 sigma"), (-2, "--", "-2 sigma"), (-3, "-", "LCL -3s"))
    if style == "plant":
        lines = ((3, "-", "UCL"), (0, "-", "CL"), (-3, "-", "LCL"))
        ax.yaxis.set_major_locator(MultipleLocator(s)); ax.yaxis.set_minor_locator(MultipleLocator(s / 2))
        ax.grid(axis="y", which="major", color="#d1d5db", lw=0.7, zorder=0)
        ax.grid(axis="y", which="minor", color="#eef0f3", lw=0.5, zorder=0)
    for k, ls_, lab in lines:
        ax.axhline(c + k * s, color="#b3261e" if abs(k) == 3 else "#6b7280", lw=1.1 if k in (3, 0, -3) else 0.9, ls=ls_, zorder=1)
        ax.text(n + 0.8, c + k * s, f"{lab}  {c + k * s:g}", va="center", fontsize=8.5)
    ax.set_xlim(0.5, n + 0.5); ax.set_ylim(c - 4.2 * s, c + 4.2 * s)
    ax.xaxis.set_major_locator(MultipleLocator(1 if n <= 50 else 5)); ax.xaxis.set_minor_locator(MultipleLocator(1))
    ax.grid(axis="x", which="both", color="#e5e7eb", lw=0.6, zorder=0)
    ax.tick_params(axis="x", labelsize=8)
    ax.set_xlabel(f"Sample number. Sample 1 taken at {d['start']}, then one sample every {d['interval_min']} minutes")
    ax.set_ylabel(f"Fill weight ({d['unit']})")
    sig = "" if style == "plant" else f"  -  sigma = {s:g} {d['unit']}"
    ax.set_title(f"Individuals control chart  -  {d['product']}  -  {d['line']}{sig}", fontsize=11, loc="left")
    fig.subplots_adjust(right=0.88, left=0.07); fig.savefig(path, dpi=130); plt.close(fig)


def draw_log(d, path):
    ev = d["log"]
    fig, ax = plt.subplots(figsize=(8.5, 1.4 + 0.42 * len(ev)))
    ax.axis("off"); fig.patch.set_facecolor("#fbf8ee")
    ax.set_xlim(0, 1); ax.set_ylim(len(ev) + 1.6, -0.2)
    ax.text(0, 0, f"SHIFT LOG  -  {d['line']}  -  {d['product']}", fontsize=12, weight="bold")
    ax.text(0, 0.6, f"Shift start {d['start']}. Times are clock times (24 h).", fontsize=9, color="#374151")
    for j, h in enumerate(("Time", "By", "Event")):
        ax.text([0, .13, .23][j], 1.4, h, fontsize=10, weight="bold")
    for i, e in enumerate(ev):
        yy = 2.2 + i * 1.0 * 0.95
        ax.plot([0, 1], [yy + .45, yy + .45], color="#9ca3af", lw=.6)
        ax.text(0, yy, e["time"], fontsize=10, family="monospace")
        ax.text(.13, yy, e["initials"], fontsize=10)
        ax.text(.23, yy, e["text"], fontsize=10)
    fig.savefig(path, dpi=130, bbox_inches="tight"); plt.close(fig)


# ------------------------------------------------------------------ tasks
def tasks_for(seed, level, out_dir, style="zones"):
    d = shift(seed, level)
    s = signals(d["samples"], d["centre"], d["sigma"], d["rules"])
    r1 = signals(d["samples"], d["centre"], d["sigma"], [1])["first"]
    z, n, first = s["z"], len(d["samples"]), s["first"]
    tag = f"s{seed}_L{level}" + ("_plant" if style == "plant" else "")
    os.makedirs(os.path.join(out_dir, "images"), exist_ok=True); os.makedirs(os.path.join(out_dir, "data"), exist_ok=True)
    chart = f"images/{tag}_chart.png"
    draw_chart(d, os.path.join(out_dir, chart), style)
    d["answers"] = {"first_signal": first, "rule1_only": r1, "hits": {str(i + 1): h for i, h in enumerate(s["hits"]) if h}}
    json.dump(d, open(os.path.join(out_dir, "data", f"{tag}.json"), "w"), indent=1)
    rules = " ".join(RULE_TEXT[r] for r in d["rules"])
    intro = (f"This is an individuals control chart of fill weights. Sample numbers run along the bottom; the centre line, "
             f"the 1, 2 and 3 sigma lines and their values are labelled on the right. ")
    if style == "plant":
        intro = ("This is an individuals control chart of fill weights, drawn the way the plant's SPC software draws it: only "
                 "the centre line (CL) and the 3-sigma control limits (UCL, LCL) are drawn and labelled on the right. "
                 "Sigma = (UCL - CL) / 3; the 1-sigma and 2-sigma levels are not drawn but fall on the labelled y-axis "
                 "gridlines (one labelled gridline per sigma). Sample numbers run along the bottom. ")
    base = {"seed": seed, "level": level, "generator_version": GEN_VERSION, "data": f"data/{tag}.json"}
    biggest = max(range(n), key=lambda i: abs(z[i])) + 1
    c2 = sum(abs(v) > 2 for v in z)
    near2 = sum(1 for i, v in enumerate(z) if 1.8 <= abs(v) <= 2)
    T = []

    def add(qt, q, ans, atype, traps, images=(chart,)):
        tr = {k: v for k, v in traps.items() if v is not None and v != ans}
        T.append({"task_id": f"factory_{tag}_{qt}", "style": style, "images": list(images), "image": images[0], "question": q, "answer": ans,
                  "answer_type": atype, "question_type": qt, "traps": tr, **base})

    add("first_signal", intro + "The plant uses these rules, and only these: " + rules +
        " A sample exactly on a line is not beyond it. Which sample number is the first to signal under any of these rules? "
        "Answer with the sample number only, or 0 if no sample signals.", first, "integer",
        {"rule1_only": r1 if level >= 2 else None, "one_early": first - 1 if first > 1 else None, "one_late": first + 1 if first else None,
         "biggest_spike": biggest, "said_none": 0})
    add("count_beyond_2s", intro + "How many samples are beyond 2 sigma, on either side of the centre line (samples beyond "
        "3 sigma count too)? A sample exactly on a line is not beyond it. Answer with a whole number.", c2, "integer",
        {"counted_near_line": c2 + near2 if near2 else None, "excluded_beyond_3s": sum(2 < abs(v) <= 3 for v in z),
         "one_side_only": max(sum(v > 2 for v in z), sum(v < -2 for v in z))})
    run_up, run_dn = longest_run(z, 1), longest_run(z, -1)
    add("longest_run_above", intro + "What is the longest run of consecutive samples that are all above the centre line? "
        "Answer with a whole number.", run_up, "integer",
        {"gave_run_below": run_dn, "one_short": run_up - 1, "one_long": run_up + 1})
    if first:
        add("signal_time", intro + "The plant uses these rules, and only these: " + rules + " A sample exactly on a line is "
            "not beyond it. The x-axis label gives the time of sample 1 and the sampling interval. At what clock time was the "
            "first signalling sample taken? Answer in 24-hour HH:MM form.", clock(d["start_min"], d["interval_min"], first),
            "label", {"n_times_interval": clock(d["start_min"] + d["interval_min"], d["interval_min"], first),
                      "rule1_sample_time": clock(d["start_min"], d["interval_min"], r1) if r1 and level >= 2 else None})
    if level >= 3:
        log = f"images/{tag}_log.png"
        draw_log(d, os.path.join(out_dir, log))
        ev = d["log"]
        letters = "ABCDEFGH"
        order = list(range(len(ev))); random.Random(seed * 7 + level).shuffle(order)   # options not in log order
        opts = "; ".join(f"{letters[j]}) {ev[i]['text']}" for j, i in enumerate(order))
        role_letter = {ev[i]["role"]: letters[j] for j, i in enumerate(order)}
        ans = role_letter["cause"]
        traps = {r: role_letter[r] for r in ("just_after_signal", "before_rule1_spike") if r in role_letter}
        lead = (intro.replace("This is an", "Image 1 is an") + "The x-axis label gives the time of sample 1 and the sampling "
                "interval. " if style == "plant" else "Image 1 is an individuals control chart of fill weights (the x-axis "
                "label gives the time of sample 1 and the sampling interval). ")
        add("cause_event", lead + "Image 2 is the operator shift log for the same shift. The plant uses these rules, "
            "and only these: " + rules + " A sample exactly on a line is not beyond it. Find the first signalling sample and "
            "its clock time. Which logged event happened most recently before that sample was taken? Options: " + opts +
            ". Answer with the letter only.", ans, "multiple_choice", traps, images=(chart, log))
    return T


def parse_range(s):
    a, _, b = s.partition("-")
    return list(range(int(a), int(b or a) + 1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out"); ap.add_argument("--seeds", default="301-304"); ap.add_argument("--levels", default="1-5")
    ap.add_argument("--style", default="zones", choices=["zones", "plant"])
    a = ap.parse_args()
    allt = []
    for sd in parse_range(a.seeds):
        for lv in parse_range(a.levels):
            allt += tasks_for(sd, lv, a.out, a.style)
    with open(os.path.join(a.out, "tasks.jsonl"), "w", encoding="utf-8") as f:
        for t in allt:
            f.write(json.dumps(t) + "\n")
    print(len(allt), "tasks")
