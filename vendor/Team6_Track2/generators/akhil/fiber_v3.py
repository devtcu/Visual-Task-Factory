"""Fiber v3 (copy of generate_v2.py; v2 is unchanged). Two changes that make it harder but keep it fair:
1. Five stages instead of three: patch -> MTP trunk -> patch -> MTP trunk -> patch. The two trunks usually have
   different polarity types, so the model must apply two printed rules in order.
2. A second question type, fault diagnosis: one cord is marked CUT (red X). Which GPU port lost its link?
   That needs a backward trace through both trunk rules. The X is placed only where no other cord passes nearby,
   so the cut cord is never ambiguous.
Run:  python generate_v3.py <out_dir> <seed> [<seed> ...]   (each seed makes one trace task and one fault task)"""
import json
import os
import random
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Rectangle

N, VERSION = 12, "fiber-3.0"
AQUA = "#13a3b4"
TYPES = {"A": lambda p: p, "B": lambda p: N + 1 - p, "C": lambda p: p + 1 if p % 2 else p - 1}
RULE_TEXT = {"A": "Type A: position n exits at position n", "B": "Type B: position n exits at position 13 - n",
             "C": "Type C: pairs flipped (1<->2, 3<->4, ... 11<->12)"}
XS = [0.8, 6.0, 11.2, 16.4, 21.6, 26.8]
LABELS = ["GPU-TRAY-07", "PP-A", "PP-B", "PP-C", "PP-D", "SW-CORE-02"]
Y = [(N - i) * 1.15 for i in range(N)]


def forward(d, src):
    """GPU port -> list of port numbers at each of the 6 banks."""
    a = d["stage1"][src - 1]; b = TYPES[d["trunk1"]](a); c = d["stage3"][b - 1]
    e = TYPES[d["trunk2"]](c); f = d["stage5"][e - 1]
    return [src, a, b, c, e, f]


def cords(d):
    """Every drawn patch cord as (stage, from_port, to_port, curve points). Curve shapes come from the seed."""
    rng = random.Random(d["seed"] + 7)
    out = []
    for stage, perm, (xa, xb) in ((1, d["stage1"], XS[0:2]), (3, d["stage3"], XS[2:4]), (5, d["stage5"], XS[4:6])):
        x0, x1 = xa + .14, xb - .14
        for i, tgt in enumerate(perm):
            yi, yo = Y[i], Y[tgt - 1]
            k1, k2 = rng.uniform(.25, .6) * (x1 - x0), rng.uniform(.25, .6) * (x1 - x0)
            t = np.linspace(0, 1, 80)[:, None]
            p0, p1, p2, p3 = map(np.array, ([x0, yi], [x0 + k1, yi], [x1 - k2, yo], [x1, yo]))
            pts = ((1 - t) ** 3) * p0 + 3 * ((1 - t) ** 2) * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3
            out.append((stage, i + 1, tgt, pts))
    return out


def pick_cut(d, rng):
    """Choose a cord in stage 3 or 5 and a point on it where no other cord comes within 0.45 units (fair, unambiguous)."""
    allc = cords(d)
    options = []
    for stage, frm, to, pts in allc:
        if stage == 1:
            continue
        others = np.vstack([p for s, f, _, p in allc if s == stage and f != frm])
        for k in range(20, 61, 4):
            if np.min(np.hypot(*(others - pts[k]).T)) > .45:
                options.append((stage, frm, to, k)); break
    return rng.choice(options)


def make(seed):
    rng = random.Random(seed)
    perms = []
    for _ in range(3):
        p = list(range(1, N + 1)); rng.shuffle(p); perms.append(p)
    t1 = rng.choice("BC"); t2 = rng.choice("BC")
    d = {"seed": seed, "generator_version": VERSION, "stage1": perms[0], "trunk1": t1, "stage3": perms[1],
         "trunk2": t2, "stage5": perms[2]}
    # Trace question
    src = rng.randint(1, N)
    path = forward(d, src)
    alt = dict(d)
    traps = {}
    for name, (a1, a2) in {"ignored_both_trunks": ("A", "A"), "ignored_trunk1": ("A", t2),
                           "ignored_trunk2": (t1, "A"), "swapped_trunk_rules": (t2, t1)}.items():
        alt.update(trunk1=a1, trunk2=a2)
        traps[name] = forward(alt, src)[-1]
    d["trace"] = {"source_port": src, "path": path, "answer": path[-1],
                  "traps": {k: v for k, v in traps.items() if v != path[-1]}}
    # Fault question: one cut cord; answer = the GPU port whose path uses it
    stage, frm, to, k = pick_cut(d, rng)
    bank = {3: 2, 5: 4}[stage]          # bank index whose port feeds that cord
    victim = next(s for s in range(1, N + 1) if forward(d, s)[bank] == frm)
    ftraps = {}
    for name, (a1, a2) in {"ignored_both_trunks": ("A", "A"), "ignored_trunk1": ("A", t2),
                           "ignored_trunk2": (t1, "A")}.items():
        alt.update(trunk1=a1, trunk2=a2)
        ftraps[name] = next(s for s in range(1, N + 1) if forward(alt, s)[bank] == frm)
    ftraps["read_cut_cord_far_end"] = next(s for s in range(1, N + 1) if forward(d, s)[bank + 1] == frm)
    d["fault"] = {"cut_stage": stage, "cut_cord_from_port": frm, "cut_cord_to_port": to, "cut_point_index": k,
                  "answer": victim, "victim_path": forward(d, victim),
                  "traps": {kk: v for kk, v in ftraps.items() if v != victim}}
    return d


def render(d, path, mode):
    fig, ax = plt.subplots(figsize=(22, 8.6), dpi=100)
    fig.patch.set_facecolor("#f6f8fb"); ax.set_facecolor("#f6f8fb")
    for j, x in enumerate(XS):
        ax.add_patch(Rectangle((x - .5, 0.4), 1, 15.1, facecolor="#e2e8f0", edgecolor="#475569", lw=1.2, zorder=0))
        ax.text(x, 15.9, LABELS[j], ha="center", va="bottom", fontsize=10, weight="bold", color="#1e293b")
        for i, yy in enumerate(Y):
            ax.add_patch(Circle((x, yy), .12, facecolor="#fff", edgecolor="#334155", lw=.8, zorder=5))
            ax.text(x - .19, yy, f"{i + 1:02}", ha="right", va="center", fontsize=8, color="#0f172a", zorder=6,
                    bbox=dict(facecolor="#e2e8f0", edgecolor="none", pad=.4))
    for stage, frm, to, pts in cords(d):
        ax.plot(pts[:, 0], pts[:, 1], color=AQUA, lw=1.7, solid_capstyle="round", zorder=2)
    for stage, (xa, xb) in ((1, XS[0:2]), (3, XS[2:4]), (5, XS[4:6])):
        ax.text((xa + xb) / 2, 14.9, f"STAGE {stage}  (duplex cords)", ha="center", fontsize=9, weight="bold", color="#334155")
    for stage, key, (xa, xb) in ((2, "trunk1", XS[1:3]), (4, "trunk2", XS[3:5])):
        x0, x1, ym = xa + .14, xb - .14, sum(Y) / N
        for yy in Y:
            ax.plot([x0, x0 + 1.2], [yy, ym], color="#64748b", lw=.9, zorder=2)
            ax.plot([x1 - 1.2, x1], [ym, yy], color="#64748b", lw=.9, zorder=2)
        ax.add_patch(Rectangle((x0 + 1.2, ym - .35), (x1 - x0) - 2.4, .7, facecolor="#94a3b8", edgecolor="#334155", lw=1, zorder=3))
        ax.text((x0 + x1) / 2, ym, f"MTP-12  TYPE {d[key]}", ha="center", va="center", fontsize=9, weight="bold", color="#0f172a", zorder=4)
        ax.text((x0 + x1) / 2, 14.9, f"STAGE {stage}  (MTP trunk)", ha="center", fontsize=9, weight="bold", color="#334155")
    ax.text(XS[2] + 2.6, -0.75, "Trunk polarity (TIA-568):  " + "   |   ".join(RULE_TEXT.values()), ha="center", va="bottom",
            fontsize=8.5, color="#1e293b", bbox=dict(facecolor="white", edgecolor="#94a3b8", pad=4), zorder=4)
    if mode == "trace":
        sy = Y[d["trace"]["source_port"] - 1]
        ax.add_patch(Circle((XS[0], sy), .21, facecolor="none", edgecolor="#e11d48", lw=2.8, zorder=8))
        ax.text(XS[0] - .3, sy + .32, "START", fontsize=8, weight="bold", color="#be123c", ha="right")
    else:
        f = d["fault"]
        pts = next(p for s, fr, _, p in cords(d) if s == f["cut_stage"] and fr == f["cut_cord_from_port"])
        cx, cy = pts[f["cut_point_index"]]
        ax.plot([cx - .22, cx + .22], [cy - .22, cy + .22], color="#e11d48", lw=3, zorder=9)
        ax.plot([cx - .22, cx + .22], [cy + .22, cy - .22], color="#e11d48", lw=3, zorder=9)
        ax.text(cx, cy + .35, "CUT", ha="center", fontsize=8, weight="bold", color="#be123c", zorder=9)
    ax.text(13.8, 17.0, "AI CLUSTER | FIBER PATCHING AS-BUILT", ha="center", fontsize=15, weight="bold", color="#0f172a")
    ax.text(13.8, 16.45, "All patch cords are aqua OM4. Crossings are not connections. Port and trunk positions are numbered "
            "top-to-bottom. Trunk position n connects to port n on the panel at each end.", ha="center", fontsize=9, color="#334155")
    ax.set_xlim(-.45, 27.45); ax.set_ylim(-1.3, 17.6); ax.axis("off")
    fig.savefig(path, bbox_inches="tight", pad_inches=.15); plt.close(fig)


RULES = ("The path runs GPU-TRAY-07 -> stage 1 cords -> PP-A -> stage 2 MTP trunk -> PP-B -> stage 3 cords -> PP-C -> "
         "stage 4 MTP trunk -> PP-D -> stage 5 cords -> SW-CORE-02. Cords may cross without connecting. In each trunk, "
         "the fibre entering at port n of the left panel exits at the right-panel port given by that trunk's printed "
         "polarity type.")
Q_TRACE = ("In this as-built AI cluster fiber diagram, start at GPU-TRAY-07 port {src:02d} (red circle). " + RULES +
           " Which SW-CORE-02 port does the path end at? Answer with the port number only.")
Q_FAULT = ("In this as-built AI cluster fiber diagram, exactly one patch cord has been cut (marked with a red X and CUT). " + RULES +
           " Every GPU-TRAY-07 port has exactly one path to SW-CORE-02. Which GPU-TRAY-07 port has lost its link because "
           "of the cut? Answer with the port number only.")

if __name__ == "__main__":
    out, seeds = sys.argv[1], [int(s) for s in sys.argv[2:]]
    os.makedirs(os.path.join(out, "images"), exist_ok=True); os.makedirs(os.path.join(out, "data"), exist_ok=True)
    with open(os.path.join(out, "tasks.jsonl"), "w", encoding="utf-8") as fh:
        for sd in seeds:
            d = make(sd)
            json.dump(d, open(os.path.join(out, "data", f"fiber3_{sd}.json"), "w"), indent=1)
            for mode, q in (("trace", Q_TRACE.format(src=d["trace"]["source_port"])), ("fault", Q_FAULT)):
                img = f"images/fiber3_{sd}_{mode}.png"
                render(d, os.path.join(out, img), mode)
                fh.write(json.dumps({"task_id": f"fiber3_{sd}_{mode}", "image": img, "question": q, "answer": d[mode]["answer"],
                                     "answer_type": "integer", "question_type": f"fiber3_{mode}_{d['trunk1']}{d['trunk2']}",
                                     "traps": d[mode]["traps"], "seed": sd, "generator_version": VERSION,
                                     "data": f"data/fiber3_{sd}.json"}) + "\n")
            print(sd, d["trunk1"], d["trunk2"], "trace", d["trace"]["path"], "fault", d["fault"]["cut_stage"], d["fault"]["victim_path"])
