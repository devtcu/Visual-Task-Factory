"""Factory variant: 6 filling heads on one chart, 100 samples, x labels every 10th sample.
Question: which head signals first, and at which sample? Answer from factory.signals() per head.
Run:  python -m generate.factory_heads <out> --seeds 401-420"""
import argparse
import json
import os
import random

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

from .factory import MARGIN, RULE_TEXT, signals

GEN_VERSION = "factory-heads-1.1"
N, HEADS, RULES = 100, 6, [1, 2, 3, 4]
COLOURS = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e", "#111111"]   # 1.1: six clearly different colours
MARKERS = ["o", "s", "^", "D", "v", "P"]


def nudge(z, keep):
    out = []
    for i, v in enumerate(z):
        if i not in keep:
            for line in (-3, -2, -1, 0, 1, 2, 3):
                if abs(v - line) < MARGIN:
                    v = line + (MARGIN if v >= line else -MARGIN)
        out.append(v)
    return out


def shift(seed):
    rng = random.Random(seed)
    centre, sigma = 500.0, 2.0
    for _ in range(1000):
        Z = [[max(-1.6, min(1.6, rng.gauss(0, 0.6))) for _ in range(N)] for _ in range(HEADS)]
        h_true, h_spike, h_late = rng.sample(range(HEADS), 3)
        k = rng.randint(8, 75)
        side = rng.choice([1, -1])
        for i in range(k, min(N, k + 9)):                         # true head: mean shift, rule 3 or 4 fires
            Z[h_true][i] = side * abs(rng.gauss(1.2, 0.4))
        j = rng.randint(min(N - 1, k + 6), N - 1)                  # obvious spike on another head, later
        Z[h_spike][j] = rng.choice([1, -1]) * rng.uniform(3.2, 3.8)
        k2 = rng.randint(min(N - 4, k + 3), N - 3)                 # a 2-of-3 pair on a third head, later still
        s2 = rng.choice([1, -1])
        Z[h_late][k2], Z[h_late][k2 + 2] = s2 * rng.uniform(2.2, 2.8), s2 * rng.uniform(2.2, 2.8)
        Z[h_late][k2 + 1] = -s2 * abs(Z[h_late][k2 + 1])
        Z = [nudge(z, set()) for z in Z]
        X = [[round(centre + v * sigma, 2) for v in z] for z in Z]
        firsts = [signals(x, centre, sigma, RULES)["first"] for x in X]
        sig = [(f, h) for h, f in enumerate(firsts) if f]
        if not sig:
            continue
        f0, h0 = min(sig)
        if sum(1 for f, _ in sig if f == f0) > 1:                  # earliest signal must be unique
            continue
        if sum(1 for f, _ in sig if f <= f0 + 1) > 1:              # no rival head signalling one sample later
            continue
        break
    else:
        raise RuntimeError(seed)
    r1 = [signals(x, centre, sigma, [1])["first"] for x in X]
    r12 = [signals(x, centre, sigma, [1, 2])["first"] for x in X]
    ob = min((f, h + 1) for h, f in enumerate(r12) if f) if any(r12) else None
    big = max(((abs(X[h][i] - centre), h, i) for h in range(HEADS) for i in range(N)))
    return {"seed": seed, "generator_version": GEN_VERSION, "centre": centre, "sigma": sigma, "heads": X,
            "first_by_head": firsts, "answer_head": h0 + 1, "answer_sample": f0,
            "rule1_by_head": r1, "obvious_event": [ob[1], ob[0]] if ob else None, "biggest_point": {"head": big[1] + 1, "sample": big[2] + 1},
            "planted": {"true_head": h_true + 1, "shift_start": k + 1, "spike_head": h_spike + 1, "spike_sample": j + 1,
                        "pair_head": h_late + 1, "pair_start": k2 + 1}}


def draw(d, path):
    c, s = d["centre"], d["sigma"]
    fig, ax = plt.subplots(figsize=(22, 7))
    xs = list(range(1, N + 1))
    for h, y in enumerate(d["heads"]):
        ax.plot(xs, y, color=COLOURS[h], lw=1.1, marker=MARKERS[h], ms=4.5, label=f"H{h + 1}", zorder=3)

    for end, xi, xt, ha in ((0, 1, -0.4, "right"), (N - 1, N, N + 1.0, "left")):   # end labels, spread so none overlap
        order = sorted(range(HEADS), key=lambda h: d["heads"][h][end])
        ys = [d["heads"][h][end] for h in order]
        for i in range(1, len(ys)):
            ys[i] = max(ys[i], ys[i - 1] + 0.55)
        shift_ = (sum(d["heads"][h][end] for h in order) - sum(ys)) / len(ys)
        for h, yy in zip(order, ys):
            ax.annotate(f"H{h + 1}", (xi, d["heads"][h][end]), (xt, yy + shift_), color=COLOURS[h], fontsize=9, weight="bold",
                        ha=ha, va="center", arrowprops=dict(arrowstyle="-", color=COLOURS[h], lw=0.6))
    for k, ls_, lab in ((3, "-", "UCL +3s"), (2, "--", "+2 sigma"), (1, ":", "+1 sigma"), (0, "-", "CL"),
                        (-1, ":", "-1 sigma"), (-2, "--", "-2 sigma"), (-3, "-", "LCL -3s")):
        ax.axhline(c + k * s, color="#b3261e" if abs(k) == 3 else "#6b7280", lw=1.1 if k in (3, 0, -3) else 0.9, ls=ls_, zorder=1)
        ax.text(N + 3.6, c + k * s, f"{lab}  {c + k * s:g}", va="center", fontsize=8.5)
    ax.set_xlim(-2.5, N + 3.0); ax.set_ylim(c - 4.2 * s, c + 4.2 * s)
    ax.xaxis.set_major_locator(MultipleLocator(10)); ax.xaxis.set_minor_locator(MultipleLocator(1))
    ax.grid(axis="x", which="minor", color="#eef0f3", lw=0.5, zorder=0)
    ax.grid(axis="x", which="major", color="#c7ccd3", lw=0.8, zorder=0)
    ax.set_xlabel("Sample number (labelled every 10th sample; one light gridline per sample)")
    ax.set_ylabel("Fill weight (g)")
    ax.legend(loc="upper left", ncol=6, fontsize=9, frameon=False)
    ax.set_title("Individuals control chart by filling head  -  Sparkling water 500 mL  -  Rotary filler, line 3  -  "
                 "heads H1-H6, sigma = 2 g", fontsize=11, loc="left")
    fig.subplots_adjust(left=0.05, right=0.92); fig.savefig(path, dpi=100); plt.close(fig)


QUESTION = ("This control chart shows fill weights from six filling heads (H1-H6) of one rotary filler, one colour and "
            "marker shape per head (see the legend), all sampled at the same times. The centre line and the 1, 2 and 3 sigma lines are labelled on "
            "the right; they apply to every head. Sample numbers are labelled every 10th sample, with one light gridline "
            "per sample. Apply these rules to each head separately, and only these: " + " ".join(RULE_TEXT[r] for r in RULES) +
            " A sample exactly on a line is not beyond it. Which head is the first to signal, and at which sample number? "
            "Answer in the form: head number, sample number (for example: 4, 37).")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--seeds", default="401-420")
    a = ap.parse_args()
    lo, _, hi = a.seeds.partition("-")
    os.makedirs(os.path.join(a.out, "images"), exist_ok=True); os.makedirs(os.path.join(a.out, "data"), exist_ok=True)
    with open(os.path.join(a.out, "tasks.jsonl"), "w", encoding="utf-8") as f:
        for sd in range(int(lo), int(hi or lo) + 1):
            d = shift(sd)
            img = f"images/heads_{sd}.png"
            draw(d, os.path.join(a.out, img))
            json.dump(d, open(os.path.join(a.out, "data", f"heads_{sd}.json"), "w"), indent=1)
            h, sm = d["answer_head"], d["answer_sample"]
            r1 = [(f, i + 1) for i, f in enumerate(d["rule1_by_head"]) if f]
            traps = {"obvious_event": d["obvious_event"], "rule1_only": list(min(r1)[::-1]) if r1 else None, "one_early": [h, sm - 1], "one_late": [h, sm + 1],
                     "biggest_point": [d["biggest_point"]["head"], d["biggest_point"]["sample"]]}
            traps = {k: v for k, v in traps.items() if v and v != [h, sm]}
            f.write(json.dumps({"task_id": f"factory_heads_{sd}", "image": img, "images": [img], "question": QUESTION,
                                "answer": [h, sm], "answer_type": "int_pair", "question_type": "heads_first_signal",
                                "traps": traps, "seed": sd, "generator_version": GEN_VERSION,
                                "data": f"data/heads_{sd}.json"}) + "\n")
            print(sd, "head", h, "sample", sm, "planted", d["planted"])
