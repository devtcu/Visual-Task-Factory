"""Akhil's automatic checks. Each family's answer is recomputed here from the saved data with separate code
(not the generator's solver), and the image is checked to exist and be readable."""
import json
import os
import tempfile

from PIL import Image, ImageChops


def _img_ok(task, out_dir):
    paths = task.get("images", [task["image"]])
    for p in paths:
        fp = os.path.join(out_dir, p)
        if not os.path.exists(fp) or os.path.getsize(fp) == 0:
            return f"missing {p}"
        w, h = Image.open(fp).size
        if w < 800 or h < 300:
            return f"too small {w}x{h}"
        if os.path.getsize(fp) > 9_500_000:
            return f"{p} over ~10 MB (Anthropic image limit)"
    return True


# ---------------------------------------------------------------- factory heads
def _we_first(x, c, s):
    """Independent Western Electric rules 1-4; returns first signalling sample (1-based) or 0."""
    z = [(v - c) / s for v in x]
    for i in range(len(z)):
        if abs(z[i]) > 3:
            return i + 1
        for sg in (1, -1):
            a = z[max(0, i - 2):i + 1]
            if sg * z[i] > 2 and sum(1 for v in a if sg * v > 2) >= 2:
                return i + 1
            b = z[max(0, i - 4):i + 1]
            if sg * z[i] > 1 and sum(1 for v in b if sg * v > 1) >= 4:
                return i + 1
            if i >= 7 and all(sg * v > 0 for v in z[i - 7:i + 1]):
                return i + 1
    return 0


def _heads(task, d):
    c, s = d["centre"], d["sigma"]
    firsts = [_we_first(x, c, s) for x in d["heads"]]
    sig = sorted((f, h + 1) for h, f in enumerate(firsts) if f)
    out = {"answer_recomputed": bool(sig) and [sig[0][1], sig[0][0]] == task["answer"],
           "unique_first": len(sig) < 2 or sig[1][0] > sig[0][0] + 1}
    near = min(abs(abs((v - c) / s) - L) for x in d["heads"] for v in x for L in (0, 1, 2, 3))
    out["points_clear_of_lines"] = near >= 0.1 - 1e-9 or f"closest point {near:.3f} sigma from a line"
    return out


# ---------------------------------------------------------------- fiber v3
def _fiber(task, d):
    T = {"A": lambda p: p, "B": lambda p: 13 - p, "C": lambda p: p + 1 if p % 2 else p - 1}

    def fwd(src):
        a = d["stage1"][src - 1]; b = T[d["trunk1"]](a); c = d["stage3"][b - 1]; e = T[d["trunk2"]](c)
        return [src, a, b, c, e, d["stage5"][e - 1]]

    out = {"stages_are_permutations": all(sorted(d[k]) == list(range(1, 13)) for k in ("stage1", "stage3", "stage5"))}
    if task["question_type"] == "fiber_trace":
        out["answer_recomputed"] = fwd(d["trace"]["source_port"])[-1] == task["answer"]
    else:
        f = d["fault"]
        bank = {3: 2, 5: 4}[f["cut_stage"]]
        victims = [s for s in range(1, 13) if fwd(s)[bank] == f["cut_cord_from_port"]]
        out["answer_recomputed"] = victims == [task["answer"]]
    out["traps_differ_from_answer"] = task["answer"] not in task.get("traps", {}).values()
    return out


# ---------------------------------------------------------------- brain
def _brain(task, d):
    # Rebuild the statistics from the raw scored stage durations, not saved answers.
    qt = task["question_type"]
    night = d["patient"]["night"]
    elapsed = 0.0
    periods = []
    for stage, duration in night:
        periods.append((stage, elapsed, float(duration)))
        elapsed += float(duration)
    onset = next(start for stage, start, dur in periods if stage != "W")
    rem = next(start for stage, start, dur in periods if stage == "R")
    asleep = sum(dur for stage, start, dur in periods if stage != "W")
    truth = {"Total recording time": elapsed, "Total sleep time": asleep,
             "Sleep efficiency": round(100 * asleep / elapsed, 1), "Sleep latency": onset,
             "REM latency": rem - onset,
             "Wake after sleep onset": sum(dur for stage, start, dur in periods if stage == "W" and start >= onset),
             "Number of awakenings": sum(stage == "W" and start > onset for stage, start, dur in periods)}
    for stage, label in (("N1", "N1"), ("N2", "N2"), ("N3", "N3"), ("R", "REM")):
        truth[label] = sum(dur for s, start, dur in periods if s == stage)
    out = {}
    if qt == "brain_rem_latency":
        out["answer_recomputed"] = abs(task["answer"] - truth["REM latency"]) < 1e-6
    elif qt == "brain_awakenings":
        out["answer_recomputed"] = task["answer"] == truth["Number of awakenings"]
    elif qt == "brain_spike_location":
        import numpy as np
        from generators.akhil import brain_samples as B
        p = d["patient"]
        times = np.linspace(0, p["eeg"]["seconds"], 3000)
        signals = B.electrode_signals(p, times)
        at = int(np.argmin(abs(times - p["eeg"]["spike"]["time_s"])))
        baseline = (times > times[at] - .25) & (times < times[at] - .10)
        candidates = []
        for chain in B.CHAINS:
            for a, b, c in zip(chain, chain[1:], chain[2:]):
                left, right = signals[a] - signals[b], signals[b] - signals[c]
                dl = float(left[at] - np.median(left[baseline]))
                dr = float(right[at] - np.median(right[baseline]))
                if dl > 0 and dr < 0:
                    candidates.append((min(dl, -dr), b))
        candidates.sort(reverse=True)
        out["answer_recomputed_from_phase_reversal"] = bool(candidates) and candidates[0][1] == task["answer"]
        out["sharp_wave_visible"] = bool(candidates) and candidates[0][0] > 25
    elif qt == "brain_report_audit":
        plant = d["report_audit"]["planted"]
        changed = []
        for name, expected in truth.items():
            shown = float(plant.get(name, expected))
            threshold = 0 if name == "Number of awakenings" else 2 if name == "Sleep efficiency" else 5
            differs = abs(shown - expected) > threshold
            if name in ("N1", "N2", "N3", "REM"):
                differs |= abs(round(100 * shown / asleep, 1) - round(100 * expected / asleep, 1)) > 2
            if differs:
                changed.append(name)
        out["answer_recomputed"] = task["answer"] == (changed or ["none"])
    else:
        architecture = list(truth)[:7]
        plant = d["report_a"]["planted"]
        changed = [name for name in architecture if abs(float(plant.get(name, truth[name])) - truth[name]) > 1e-6]
        out["one_architecture_error"] = len(changed) == 1
        out["answer_recomputed"] = len(changed) == 1 and abs(float(task["answer"]) - truth[changed[0]]) < 1e-6
        out["planted_value_differs"] = task.get("traps", {}).get("kept_printed_value") != task["answer"]
    return out


def _image_matches_data(task, data, out_dir):
    """Re-render the delivered visual from saved data and compare actual RGB pixels."""
    import matplotlib
    qt = task["question_type"]
    original = task.get("images", [task["image"]])
    with tempfile.TemporaryDirectory() as tmp, matplotlib.rc_context(matplotlib.rcParamsDefault):
        rendered = []
        if qt == "heads_first_signal":
            from generators.akhil import factory_heads as F
            p = os.path.join(tmp, "heads.png"); F.draw(data, p); rendered.append(p)
        elif qt.startswith("fiber_"):
            from generators.akhil import fiber_v3 as F
            p = os.path.join(tmp, "fiber.png"); F.render(data, p, qt.split("_")[1]); rendered.append(p)
        elif qt.startswith("brain_"):
            from generators.akhil import brain_samples as B
            p = data["patient"]
            if qt in ("brain_report_audit", "brain_find_fix"):
                path = os.path.join(tmp, "report.png")
                B.draw_report(p, path, data["report_audit" if qt == "brain_report_audit" else "report_a"]["planted"])
                rendered.append(path)
            path = os.path.join(tmp, "signal.png")
            (B.draw_eeg if qt == "brain_spike_location" else B.draw_hypnogram)(p, path)
            rendered.append(path)
        for rel, expected in zip(original, rendered):
            with Image.open(os.path.join(out_dir, rel)) as a, Image.open(expected) as b:
                if a.size != b.size or ImageChops.difference(a.convert("RGB"), b.convert("RGB")).getbbox() is not None:
                    return False
        return len(original) == len(rendered)


def validate(task, out_dir="."):
    d = json.load(open(os.path.join(out_dir, task["data"]), encoding="utf-8"))
    qt = task["question_type"]
    checks = {"image_ok": _img_ok(task, out_dir)}
    if qt == "heads_first_signal":
        checks.update(_heads(task, d))
    elif qt.startswith("fiber_"):
        checks.update(_fiber(task, d))
    elif qt.startswith("brain_"):
        checks.update(_brain(task, d))
    elif qt.startswith("xsec_"):
        from validate.akhil import xsec_validate as XV
        r = XV.check_task(task, out_dir)
        checks.update({k: (True if v["passed"] else v["detail"]) for k, v in r["checks"].items()})
    if not qt.startswith("xsec_"):
        checks["image_matches_saved_data"] = _image_matches_data(task, d, out_dir)
    passed = all(v is True for v in checks.values())
    return {"passed": passed, "checks": checks}
