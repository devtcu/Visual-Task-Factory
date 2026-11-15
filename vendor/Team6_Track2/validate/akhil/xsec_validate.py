"""Independent validation of generated tasks.

Checks (per task):
  dense_integration   cut/fill areas re-computed by dense numeric integration
  shapely_clipping    third method (polygon boolean ops) if shapely is installed
  answer_recompute    reference answer re-derived from data.json with the validator's own code
  daylight_on_ground  template end points lie on the ground line
  no_coincident       template and ground are not (nearly) coincident over any long stretch
  image_rerender      re-rendering from the data reproduces the stored PNG pixel-for-pixel
  image_matches_data  plotted vertices found in the stored PNG at the pixel positions the data implies
  legibility          pixels per foot, image size, minimum feature sizes
  reading_sensitivity answer moves less than the tolerance under a +/-0.1 ft vertical reading error
  mixed_cut_fill      (medium+) the interval range actually mixes cut and fill
  unique_answer       (label tasks) winner beats runner-up by >= 10%
"""
import json, os, sys, tempfile
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # handoff root
sys.path.insert(0, ROOT)
from generators.akhil.xsecgen import xsec as X, render as R

READ_ERR = 0.1   # ft, careful-reader vertical error on the sheet


def dense(g, t, mode, step=0.005):
    x0, x1 = t[0][0], t[-1][0]
    xs = np.arange(x0, x1, step) + step / 2
    gv = np.interp(xs, [p[0] for p in g], [p[1] for p in g]); tv = np.interp(xs, [p[0] for p in t], [p[1] for p in t])
    d = gv - tv if mode == "cut" else tv - gv
    return float(np.clip(d, 0, None).sum() * step)


def shapely_area(g, t, mode):
    from shapely.geometry import Polygon
    x0, x1 = t[0][0], t[-1][0]
    xs = sorted(set([p[0] for p in g if x0 < p[0] < x1] + [x0, x1]))
    gs = [(x, float(np.interp(x, [p[0] for p in g], [p[1] for p in g]))) for x in xs]
    floor = min(min(p[1] for p in gs), min(p[1] for p in t)) - 10
    G = Polygon(gs + [(x1, floor), (x0, floor)]).buffer(0)
    T = Polygon([tuple(p) for p in t] + [(x1, floor), (x0, floor)]).buffer(0)
    return (G.difference(T) if mode == "cut" else T.difference(G)).area


def _vol(areas, stations, lo, hi):
    return sum((areas[i] + areas[i + 1]) / 2 * (stations[i + 1] - stations[i]) / 27
               for i in range(len(stations) - 1) if stations[i] >= lo and stations[i + 1] <= hi)


def check_task(task, task_dir):
    data = json.load(open(os.path.join(task_dir, task["data"])))
    secs, st = data["sections"], [s["station"] for s in data["sections"]]
    q = task["qspec"]
    res = {}

    def rec(name, ok, detail=""):
        res[name] = dict(passed=bool(ok), detail=str(detail))

    # 1 dense integration
    worst = 0.0
    for s in secs:
        for mode, key in (("cut", "cut_area"), ("fill", "fill_area")):
            a = dense(s["ground"], s["template"], mode)
            worst = max(worst, abs(a - s[key]) / max(1.0, s[key]))
    rec("dense_integration", worst < 2e-3, "max rel diff %.2e" % worst)
    # 2 shapely
    try:
        worst = 0.0
        for s in secs:
            for mode, key in (("cut", "cut_area"), ("fill", "fill_area")):
                worst = max(worst, abs(shapely_area(s["ground"], s["template"], mode) - s[key]) / max(1.0, s[key]))
        rec("shapely_clipping", worst < 2e-3, "max rel diff %.2e" % worst)
    except ImportError:
        res["shapely_clipping"] = dict(passed=True, detail="skipped (shapely not installed)")
    # 3 answer recompute (validator's own volume code on densely integrated areas)
    key = q["key"]
    areas = [dense(s["ground"], s["template"], key) for s in secs]
    if q["qtype"] == "max_cut_interval":
        vols = [((areas[i] + areas[i + 1]) / 2 * (st[i + 1] - st[i]) / 27, i) for i in range(len(st) - 1)]
        vols.sort(reverse=True)
        lab = "%s-%s" % (X.fmt_sta(st[vols[0][1]]), X.fmt_sta(st[vols[0][1] + 1]))
        rec("answer_recompute", lab == task["answer"], "%s vs %s" % (lab, task["answer"]))
        margin = (vols[0][0] - vols[1][0]) / vols[0][0]
        rec("unique_answer", margin >= 0.10, "winner margin %.1f%%" % (100 * margin))
    else:
        v = _vol(areas, st, q["from_sta"], q["to_sta"])
        rec("answer_recompute", abs(v - task["answer"]) / v < 5e-3 if v > 0 else False, "%.1f vs %.1f" % (v, task["answer"]))
        rec("answer_size", v >= 150, "answer %.1f cy (min 150 cy)" % v)
    # 4 daylight on ground
    bad = 0.0
    for s in secs:
        for p in (s["template"][0], s["template"][-1]):
            bad = max(bad, abs(np.interp(p[0], [a for a, _ in s["ground"]], [b for _, b in s["ground"]]) - p[1]))
    rec("daylight_on_ground", bad < 0.02, "max gap %.4f ft" % bad)
    # 5 no coincident stretches
    worst = 0.0
    for s in secs:
        x0, x1 = s["template"][0][0], s["template"][-1][0]
        xs = np.arange(x0, x1, 0.25)
        d = np.abs(np.interp(xs, [a for a, _ in s["ground"]], [b for _, b in s["ground"]]) - np.interp(xs, [a for a, _ in s["template"]], [b for _, b in s["template"]]))
        run = best = 0
        for v in d:
            run = run + 1 if v < 0.05 else 0
            best = max(best, run)
        worst = max(worst, best * 0.25)
    rec("no_coincident", worst < 2.0, "longest near-coincident run %.2f ft" % worst)
    # 6/7/8 image checks
    img_path = os.path.join(task_dir, task["image"])
    tmp = tempfile.mktemp(suffix=".png")
    meta = R.render_sheet(data, tmp)
    a, b = np.asarray(Image.open(img_path).convert("RGB")), np.asarray(Image.open(tmp).convert("RGB"))
    same = a.shape == b.shape and int(np.abs(a.astype(int) - b.astype(int)).max()) == 0
    rec("image_rerender", same, "pixel-identical" if same else "re-render differs")
    os.remove(tmp)
    bg = np.median(a.reshape(-1, 3), axis=0)
    miss = tot = 0
    for pn in meta["panels"]:
        for key_, pts in (("g", pn["ground_px"]), ("t", pn["template_px"])):
            for (x, y) in pts[:: max(1, len(pts) // 12)]:
                if not (pn["xlim"][0] * 0 + 0 <= x < meta["width"] and 0 <= y < meta["height"]):
                    continue
                xi, yi = int(round(x)), int(round(y))
                win = a[max(0, yi - 4):yi + 5, max(0, xi - 4):xi + 5].astype(int)
                if win.size == 0:
                    continue
                tot += 1
                if (np.abs(win - bg).sum(axis=2) > 120).sum() < 3:
                    miss += 1
    rec("image_matches_data", tot > 20 and miss / tot < 0.08, "%d/%d sampled vertices without ink nearby" % (miss, tot))
    ppf = min(p["px_per_ft_y"] for p in meta["panels"])
    rec("legibility", ppf >= 8 and meta["width"] >= 1800, "min %.1f px/ft vertical, image %dx%d" % (ppf, meta["width"], meta["height"]))
    # 9 reading sensitivity
    if q["qtype"] == "max_cut_interval":
        ok = all(X.evaluate(data, q, e)["value"] == task["answer"] for e in (-READ_ERR, READ_ERR))
        rec("reading_sensitivity", ok, "label stable under +/-%.2f ft" % READ_ERR)
    else:
        v0 = X.evaluate(data, q)["value"]
        dv = max(abs(X.evaluate(data, q, e)["value"] - v0) / v0 for e in (-READ_ERR, READ_ERR))
        rec("reading_sensitivity", dv < task["tolerance_rel"], "%.1f%% change under +/-%.2f ft vs tol %.0f%%" % (100 * dv, READ_ERR, 100 * task["tolerance_rel"]))
    # 10 mixed
    if data["level"] != "easy":
        sel = [s for s in secs if q["from_sta"] <= s["station"] <= q["to_sta"]]
        rec("mixed_cut_fill", any(s["cut_area"] > 5 for s in sel) and any(s["fill_area"] > 5 for s in sel), "cut and fill both present in range")
    return dict(valid=all(v["passed"] for v in res.values()), checks=res)


def main(task_dir):
    tasks = [json.loads(l) for l in open(os.path.join(task_dir, "tasks.jsonl")) if l.strip()]
    out = {}
    for t in tasks:
        out[t["task_id"]] = check_task(t, task_dir)
        bad = [k for k, v in out[t["task_id"]]["checks"].items() if not v["passed"]]
        print("%-40s %s %s" % (t["task_id"], "VALID" if out[t["task_id"]]["valid"] else "INVALID", bad))
    json.dump(out, open(os.path.join(task_dir, "validation.json"), "w"), indent=1)
    return all(v["valid"] for v in out.values())


if __name__ == "__main__":
    sys.exit(0 if main(sys.argv[1] if len(sys.argv) > 1 else "tasks/reported") else 1)
