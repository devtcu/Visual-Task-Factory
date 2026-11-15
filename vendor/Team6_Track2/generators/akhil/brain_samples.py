"""One made-up sleep-study patient, four documents drawn from the same data, styled after real clinical printouts:
  1. EEG page in the longitudinal bipolar ("double banana") montage, with an ECG channel
  2. Alpha-band scalp map
  3. Hypnogram with an SpO2 panel, as in a polysomnography report
  4. Polysomnography summary report (one value is planted wrong on purpose)
plus brain_questions.json with questions, reference answers computed from the data, and trap answers.
Numbers in, PNG out. No AI images, no downloads.     Run:  python generate/brain_samples.py <out_dir>"""
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Polygon, Rectangle
from scipy.interpolate import RBFInterpolator

def save(fig, path):
    """Render to memory, then write with retries: on Windows another program (preview, indexer) can briefly lock the file."""
    import io as _io, time as _time
    buf = _io.BytesIO(); fig.savefig(buf, dpi=150, format="png"); plt.close(fig)
    for attempt in range(8):
        try:
            with open(path, "wb") as fh:
                fh.write(buf.getvalue())
            return
        except OSError:
            _time.sleep(0.5)
    raise OSError(f"could not write {path}")


LAB = "Northgate Sleep and Neurophysiology Lab"
LAB_ADDR = "41 Harbour Road, Suite 300  |  Tel 555-0142"

# 10-20 electrode positions, head seen from above, nose up. Odd = left, even = right, z = midline.
POS = {"Fp1": (-0.31, 0.92), "Fp2": (0.31, 0.92), "F7": (-0.78, 0.55), "F3": (-0.40, 0.50), "Fz": (0.0, 0.47),
       "F4": (0.40, 0.50), "F8": (0.78, 0.55), "T3": (-0.96, 0.0), "C3": (-0.48, 0.0), "Cz": (0.0, 0.0),
       "C4": (0.48, 0.0), "T4": (0.96, 0.0), "T5": (-0.78, -0.55), "P3": (-0.40, -0.50), "Pz": (0.0, -0.47),
       "P4": (0.40, -0.50), "T6": (0.78, -0.55), "O1": (-0.31, -0.92), "O2": (0.31, -0.92)}
# Longitudinal bipolar montage, chain by chain (left temporal, left parasagittal, midline, right parasagittal, right temporal).
CHAINS = [["Fp1", "F7", "T3", "T5", "O1"], ["Fp1", "F3", "C3", "P3", "O1"], ["Fz", "Cz", "Pz"],
          ["Fp2", "F4", "C4", "P4", "O2"], ["Fp2", "F8", "T4", "T6", "O2"]]
NIGHT = [("W", 18), ("N1", 8), ("N2", 26), ("N3", 38), ("N2", 14), ("R", 12), ("N2", 18), ("W", 1.5), ("N2", 10.5),
         ("N3", 28), ("N2", 16), ("R", 22), ("W", 6), ("N1", 6), ("N2", 44), ("R", 30), ("N2", 22), ("W", 2), ("N2", 12),
         ("N1", 8), ("R", 36), ("W", 12), ("N2", 30), ("R", 24), ("W", 36)]


def patient(seed):
    rng = np.random.default_rng(seed)
    alpha_hz = 10.0
    alpha_uv = {ch: round(float(5 + 36 * max(0.0, -y) ** 1.5 + (5 if x < 0 and y < -0.4 else 0) + rng.uniform(-1, 1)), 1)
                for ch, (x, y) in POS.items()}
    return {"seed": seed, "patient_id": "SL-2047", "age": 46, "sex": "F", "date": "14 Nov 2026",
            "lights_out": "23:00:00", "lights_on": "07:00:00", "epoch_s": 30,
            "eeg": {"start_clock": [23, 11, 40], "seconds": 10, "alpha_hz": alpha_hz, "sens_uv_per_mm": 7,
                    "spike": {"electrode": "C4", "time_s": 6.6, "peak_uv": -95.0, "spread_uv": -35.0},
                    "blink_time_s": 2.4, "ecg_bpm": 66},
            "alpha_uv": alpha_uv, "night": NIGHT}


# ------------------------------------------------------------------ derived numbers (the reference answers)
def night_stats(p):
    t, rows = 0.0, []
    for st, m in p["night"]:
        rows.append((st, t, t + m)); t += m
    trt = t
    onset = next(a for st, a, b in rows if st != "W")
    first_rem = next(a for st, a, b in rows if st == "R")
    tst = sum(b - a for st, a, b in rows if st != "W")
    waso = sum(b - a for st, a, b in rows if st == "W" and a >= onset)
    awakenings = sum(1 for st, a, b in rows if st == "W" and a > onset)
    stage_min = {s: sum(b - a for st, a, b in rows if st == s) for s in ("N1", "N2", "N3", "R")}
    rem_starts = [a for st, a, b in rows if st == "R"]
    return {"TRT": trt, "TST": tst, "SE": round(100 * tst / trt, 1), "SL": onset, "REML": first_rem - onset,
            "REML_from_lights_out": first_rem, "second_REM_from_onset": rem_starts[1] - onset, "WASO": waso,
            "awakenings": awakenings, "stage_min": stage_min,
            "stage_pct": {s: round(100 * v / tst, 1) for s, v in stage_min.items()}, "rows": rows}


def stage_at(p, minutes_after_lights_out):
    for st, a, b in night_stats(p)["rows"]:
        if a <= minutes_after_lights_out < b:
            return st


# ------------------------------------------------------------------ 1. EEG page
def electrode_signals(p, t):
    e, rng = p["eeg"], np.random.default_rng(p["seed"] + 1)
    phase = {"L": rng.uniform(0, 6.28), "R": rng.uniform(0, 6.28), "Z": rng.uniform(0, 6.28)}
    sig = {}
    for ch, (x, y) in POS.items():
        side = "L" if x < 0 else "R" if x > 0 else "Z"
        v = p["alpha_uv"][ch] * np.sin(2 * np.pi * e["alpha_hz"] * t + phase[side] + rng.normal(0, 0.15))
        for f in (1.3, 2.7, 4.6, 6.1, 15.0, 19.0):
            v += rng.uniform(2, 6) * np.sin(2 * np.pi * f * t + rng.uniform(0, 6.28))
        v += rng.normal(0, 2.2, t.size)
        sig[ch] = v
    # Eye blink: large positive deflection at the frontopolar electrodes, both sides.
    blink = 160 * np.exp(-((t - e["blink_time_s"]) ** 2) / (2 * 0.09 ** 2))
    for ch, w in (("Fp1", 1.0), ("Fp2", 1.0), ("F7", 0.3), ("F8", 0.3), ("F3", 0.25), ("F4", 0.25), ("Fz", 0.25)):
        sig[ch] = sig[ch] + w * blink
    # Focal sharp wave: negative peak at one electrode, smaller at its neighbours.
    s = e["spike"]
    shape = np.clip(1 - np.abs(t - s["time_s"]) / 0.045, 0, None) - 0.35 * np.exp(-((t - s["time_s"] - 0.12) ** 2) / (2 * 0.05 ** 2))
    neighbours = {n for c in CHAINS for i, n in enumerate(c) if s["electrode"] in c[max(0, i - 1):i + 2] and n != s["electrode"]}
    sig[s["electrode"]] = sig[s["electrode"]] + s["peak_uv"] * shape
    for ch in neighbours:
        sig[ch] = sig[ch] + s["spread_uv"] * shape
    return sig


def ecg_trace(t, bpm, rng):
    v, rr = np.zeros_like(t), 60 / bpm
    for b in np.arange(0.3, t[-1] + rr, rr):
        for dt, a, w in ((-0.18, 0.1, 0.025), (-0.025, -0.15, 0.008), (0, 1.0, 0.010), (0.03, -0.25, 0.01), (0.25, 0.3, 0.045)):
            v += a * np.exp(-((t - b - dt) ** 2) / (2 * w ** 2))
    return v * 110 + rng.normal(0, 2, t.size)


def draw_eeg(p, path):
    e = p["eeg"]
    t = np.linspace(0, e["seconds"], 3000)
    sig = electrode_signals(p, t)
    rows = []
    for chain in CHAINS:
        rows += [(f"{a}-{b}", sig[a] - sig[b]) for a, b in zip(chain, chain[1:])]
        rows.append(None)                       # gap between chains
    rows[-1] = ("ECG", ecg_trace(t, e["ecg_bpm"], np.random.default_rng(p["seed"] + 2)))
    fig, ax = plt.subplots(figsize=(13, 9.4))
    gap, y, scale = 68.0, 0.0, 0.42             # scale: plot units per uV (sets sensitivity look)
    for r in rows:
        if r is None:
            y -= gap * 0.45; continue
        name, v = r
        ax.plot(t, y - v * scale, color="#111827", lw=0.65)   # negative up (EEG convention)
        ax.text(-0.08, y, name, ha="right", va="center", fontsize=8.6, family="DejaVu Sans")
        y -= gap
    bottom = y + gap * 0.4
    h, m, s = e["start_clock"]
    for k in range(e["seconds"] + 1):
        ax.axvline(k, color="#c4cad4", lw=0.6, zorder=0)
        ss = s + k
        ax.text(k, 50, f"{h:02d}:{m + ss // 60:02d}:{ss % 60:02d}", ha="right" if k == e["seconds"] else "center",
                va="bottom", fontsize=7.5, color="#4b5563")
    # calibration bar: 1 s and 50 uV
    ax.plot([e["seconds"] - 1.6, e["seconds"] - 0.6], [bottom - 14] * 2, color="black", lw=1.6)
    ax.plot([e["seconds"] - 0.6] * 2, [bottom - 14, bottom - 14 + 100 * scale], color="black", lw=1.6)
    ax.text(e["seconds"] - 1.1, bottom - 28, "1 s", ha="center", fontsize=7.5)
    ax.text(e["seconds"] - 0.52, bottom - 14 + 50 * scale, "100 µV", fontsize=7.5, va="center")
    ax.set_xlim(-0.02, e["seconds"] + 0.05); ax.set_ylim(bottom - 36, 66); ax.axis("off")
    fig.suptitle(f"{LAB}    Patient {p['patient_id']}    {p['date']}", x=0.01, ha="left", fontsize=10, weight="bold")
    ax.set_title("Montage: longitudinal bipolar (double banana)    Sens 7 µV/mm    LFF 1 Hz    HFF 70 Hz    "
                 "Notch 60 Hz    Paper 30 mm/s    Page 23 of 960", fontsize=8.5, loc="left", color="#374151", pad=16)
    fig.subplots_adjust(left=0.075, right=0.99, top=0.93, bottom=0.02)
    save(fig, path)


# ------------------------------------------------------------------ 2. scalp map
def draw_scalp(p, path):
    names = list(POS)
    pts = np.array([POS[n] for n in names]); vals = np.array([p["alpha_uv"][n] for n in names])
    gx, gy = np.mgrid[-1.0:1.0:300j, -1.0:1.0:300j]
    interp = RBFInterpolator(pts, vals, kernel="thin_plate_spline", smoothing=0.5)
    grid = interp(np.column_stack([gx.ravel(), gy.ravel()])).reshape(gx.shape)
    grid[gx ** 2 + gy ** 2 > 1.0] = np.nan
    fig, ax = plt.subplots(figsize=(6.8, 6.6))
    im = ax.contourf(gx, gy, grid, levels=np.linspace(0, 45, 19), cmap="RdYlBu_r", extend="both")
    ax.contour(gx, gy, grid, levels=np.linspace(0, 45, 10), colors="k", linewidths=0.3, alpha=0.5)
    ax.add_patch(Circle((0, 0), 1.0, fill=False, lw=2, color="black"))
    ax.add_patch(Polygon([(-0.11, 0.994), (0, 1.13), (0.11, 0.994)], closed=False, fill=False, lw=2, color="black"))
    for sx in (-1, 1):
        ax.add_patch(Polygon([(sx * 0.995, 0.13), (sx * 1.07, 0.09), (sx * 1.07, -0.09), (sx * 0.995, -0.13)],
                             closed=False, fill=False, lw=2, color="black"))
    for n, (x, y) in POS.items():
        ax.plot(x, y, "o", ms=4.5, color="black")
        ax.text(x, y - 0.075, n, ha="center", va="top", fontsize=8.5)
    ax.text(-1.17, 1.0, "L", fontsize=13, weight="bold"); ax.text(1.09, 1.0, "R", fontsize=13, weight="bold")
    ax.set_xlim(-1.22, 1.22); ax.set_ylim(-1.15, 1.2); ax.set_aspect("equal"); ax.axis("off")
    cb = fig.colorbar(im, ax=ax, shrink=0.72, pad=0.02, ticks=range(0, 46, 5)); cb.set_label("Alpha (8-13 Hz) amplitude, µV")
    ax.set_title(f"Alpha band topography    Patient {p['patient_id']}\n{p['date']}  23:11:40-23:11:50, eyes closed, "
                 "average reference, top view", fontsize=9.5, loc="left")
    fig.tight_layout(); save(fig, path)


# ------------------------------------------------------------------ 3. hypnogram + SpO2
def spo2_trace(p, minutes):
    rng = np.random.default_rng(p["seed"] + 3)
    base = 95.6 + 0.4 * np.sin(minutes / 37) + rng.normal(0, 0.25, minutes.size)
    for st, a, b in night_stats(p)["rows"]:
        if st == "R":
            for c in np.linspace(a + 3, b - 3, max(1, int((b - a) // 9))):
                base -= rng.uniform(3, 6) * np.exp(-((minutes - c) ** 2) / (2 * 0.9 ** 2))
    return np.clip(base, 80, 99)


def draw_hypnogram(p, path):
    st = night_stats(p)
    level = {"W": 4, "R": 3, "N1": 2, "N2": 1, "N3": 0}
    edges = [0] + [b for _, _, b in st["rows"]]
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(12, 5.6), sharex=True, gridspec_kw={"height_ratios": [2.4, 1]})
    lv = [level[s] for s, _, _ in st["rows"]]
    ax.step(edges, lv + [lv[-1]], where="post", color="#111827", lw=1.4)
    for s, a, b in st["rows"]:
        if s == "R":
            ax.add_patch(Rectangle((a, 2.86), b - a, 0.28, color="#c62828", lw=0))
    ax.set_yticks(range(5)); ax.set_yticklabels(["N3", "N2", "N1", "R", "W"])
    ax.set_ylim(-0.5, 4.5); ax.set_ylabel("Stage")
    m = np.arange(0, st["TRT"], 0.5)
    ax2.plot(m, spo2_trace(p, m), color="#1d4ed8", lw=0.8)
    ax2.set_ylim(84, 100); ax2.set_yticks([85, 90, 95, 100]); ax2.set_ylabel("SpO2 %")
    for a_ in (ax, ax2):
        a_.set_xticks(range(0, 481, 60)); a_.set_xticks(range(0, 481, 10), minor=True)
        a_.grid(which="major", axis="x", color="#9ca3af", lw=0.7); a_.grid(which="minor", axis="x", color="#e5e7eb", lw=0.4)
        a_.grid(which="major", axis="y", color="#eef0f3", lw=0.5)
    ax2.set_xticklabels([f"{(23 + h) % 24:02d}:00" for h in range(9)]); ax2.set_xlim(0, st["TRT"])
    ax2.set_xlabel("Clock time   (30 s epochs; minor gridlines every 10 min)")
    fig.suptitle(f"{LAB}    Polysomnogram, patient {p['patient_id']}, {p['date']}    Lights out 23:00:00, lights on 07:00:00",
                 x=0.01, ha="left", fontsize=10)
    ax.set_title("Hypnogram (AASM scoring)  -  REM periods marked in red", fontsize=9, loc="left", color="#374151")
    fig.tight_layout(); save(fig, path)


# ------------------------------------------------------------------ 4. summary report (one planted error)
# Report A: one big error in a single-reading measure.
# Report B: a realistic software bug (final wake left out of WASO) plus 20 min of N3 mislabelled as N2.
#           TST, efficiency and percentages stay internally consistent, so only the hypnogram reveals it.
PLANTS = {"A": {"REM latency": 68.0}, "B": {"Wake after sleep onset": 21.5, "N2": 212.5, "N3": 46.0}}
PLANT = PLANTS["A"]


def report_rows(p, plant=None):
    plant, s = plant or {}, night_stats(p)
    rows = [("Total recording time (TRT)", s["TRT"], "min"), ("Total sleep time (TST)", s["TST"], "min"),
            ("Sleep efficiency (TST / TRT)", s["SE"], "%"), ("Sleep latency (lights out to first sleep epoch)", s["SL"], "min"),
            ("REM latency (sleep onset to first REM epoch)", s["REML"], "min"),
            ("Wake after sleep onset (all wake from sleep onset to lights on)", s["WASO"], "min"),
            ("Number of awakenings (W periods after sleep onset, any length)", s["awakenings"], "")]
    return [(n, next((v for k, v in plant.items() if n.startswith(k)), val), u) for n, val, u in rows]


def stage_rows(p, plant=None):
    plant, s = plant or {}, night_stats(p)
    mins = {lab: plant.get(lab, s["stage_min"][k]) for k, lab in (("N1", "N1"), ("N2", "N2"), ("N3", "N3"), ("R", "REM"))}
    return [(lab, v, round(100 * v / s["TST"], 1)) for lab, v in mins.items()]


def fmt(v):
    return f"{v:.0f}" if float(v).is_integer() else f"{v:.1f}"


def draw_report(p, path, plant=None):
    s = night_stats(p)
    spo = spo2_trace(p, np.arange(0, s["TRT"], 0.5))
    fig = plt.figure(figsize=(8.27, 11.69)); ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")
    ax.set_xlim(0, 100); ax.set_ylim(0, 141)
    ax.add_patch(Rectangle((0, 132), 100, 9, color="#0f2a4a"))
    ax.text(6, 137.6, LAB, color="white", fontsize=14, weight="bold", va="center")
    ax.text(6, 134.2, LAB_ADDR, color="#cbd5e1", fontsize=8.5, va="center")
    ax.text(6, 127, "Polysomnography Summary Report", fontsize=15, weight="bold")
    ax.text(6, 123.8, "Diagnostic in-lab study, attended. Scored in 30 s epochs per AASM rules.", fontsize=8.5, color="#4b5563")

    def kv(x, y, k, v):
        ax.text(x, y, k, fontsize=8.5, color="#4b5563"); ax.text(x + 17, y, v, fontsize=8.5)
    kv(6, 118.5, "Patient ID", p["patient_id"]); kv(6, 115.8, "Age / Sex", f"{p['age']} / {p['sex']}")
    kv(6, 113.1, "Study date", p["date"]); kv(54, 118.5, "Lights out", p["lights_out"])
    kv(54, 115.8, "Lights on", p["lights_on"]); kv(54, 113.1, "Referring MD", "Dr. R. Okafor")
    ax.plot([6, 94], [110.5, 110.5], color="#cbd5e1", lw=1)

    def table(y, title, header, rows, widths):
        ax.text(6, y, title, fontsize=10.5, weight="bold"); y -= 3.4
        ax.add_patch(Rectangle((6, y - 1.1), 88, 3.0, color="#e8eef6", lw=0))
        x = 7
        for h, w in zip(header, widths):
            ax.text(x, y, h, fontsize=8.5, weight="bold"); x += w
        for i, r in enumerate(rows):
            y -= 3.1
            if i % 2:
                ax.add_patch(Rectangle((6, y - 1.1), 88, 3.1, color="#f7f9fc", lw=0))
            x = 7
            for c, w in zip(r, widths):
                ax.text(x, y, c, fontsize=8.5); x += w
        return y - 4.5
    y = table(106, "Sleep architecture", ["Measure", "Value", "Unit"],
              [(n, fmt(v), u) for n, v, u in report_rows(p, plant)], [62, 14, 10])
    y = table(y, "Sleep stages", ["Stage", "Minutes", "% of TST"],
              [(lab, fmt(v), fmt(pc)) for lab, v, pc in stage_rows(p, plant)], [62, 14, 10])
    y = table(y, "Oxygen saturation", ["Measure", "Value", "Unit"],
              [("Mean SpO2 during sleep", f"{spo.mean():.1f}", "%"), ("Lowest SpO2", f"{spo.min():.0f}", "%")], [62, 14, 10])
    ax.text(6, y, "Technologist notes", fontsize=10.5, weight="bold")
    ax.text(6, y - 3.4, "Study completed without technical problems. Brief eye-blink artifact at sleep onset.\n"
                        "Values above were generated from the scored hypnogram by the acquisition software.",
            fontsize=8.5, va="top", linespacing=1.6)
    ax.text(6, 9, "Interpreting physician: ______________________     Status: DRAFT - not yet signed", fontsize=8.5, color="#4b5563")
    ax.text(6, 5.5, f"Page 1 of 1    Patient {p['patient_id']}    Synthetic record generated for evaluation; not a real patient.",
            fontsize=7.2, color="#9ca3af")
    save(fig, path)


# ------------------------------------------------------------------ questions, answers, traps
REPORT_INTRO = ("Image 1 is a polysomnography summary report and image 2 is the hypnogram it was produced from "
                "(30-second epochs). ")


def hard_questions(p):
    """Medium and hard levels: many-step reading, auditing a report that is internally consistent, three-way checks."""
    s, sp = night_stats(p), p["eeg"]["spike"]
    rem_blocks = [b - a for st, a, b in s["rows"] if st == "R"]
    return [
        {"id": "m_hyp_n2_total", "level": "medium", "images": ["brain_hypnogram.png"], "answer_type": "number",
         "tolerance_abs": 10,
         "question": "On this hypnogram, how many minutes in total were scored as stage N2 across the whole night? "
                     "Answers within ±10 are accepted.",
         "answer": s["stage_min"]["N2"],
         "traps": {"included_N1": s["stage_min"]["N2"] + s["stage_min"]["N1"],
                   "included_N3": s["stage_min"]["N2"] + s["stage_min"]["N3"]}},
        {"id": "m_hyp_awakenings", "level": "medium", "images": ["brain_hypnogram.png"], "answer_type": "integer",
         "question": "An awakening is any period scored W that starts after sleep onset (the first epoch of any sleep "
                     "stage), however short it is, including a final awakening that lasts until lights on. How many "
                     "awakenings are there on this hypnogram?",
         "answer": s["awakenings"],
         "traps": {"missed_brief_wakes": s["awakenings"] - 2, "excluded_final_wake": s["awakenings"] - 1,
                   "counted_initial_wake": s["awakenings"] + 1}},
        {"id": "m_eeg_spike_location", "level": "medium", "images": ["brain_eeg_page.png"], "answer_type": "label",
         "question": "This EEG page uses a longitudinal bipolar montage: each channel shows the first electrode minus the "
                     "second, and negative is drawn upward. One focal sharp wave appears on this page. A sharp wave that "
                     "deflects in opposite directions in two neighbouring channels of the same chain (a phase reversal) "
                     "is located at the electrode those two channels share. At which electrode is the sharp wave located?",
         "answer": sp["electrode"],
         "traps": {"neighbour_F4": "F4", "neighbour_P4": "P4", "mirror_C3": "C3", "blink_Fp2": "Fp2", "blink_Fp1": "Fp1"}},
        {"id": "h_hyp_sleep_efficiency", "level": "hard", "images": ["brain_hypnogram.png"], "answer_type": "number",
         "tolerance_abs": 2,
         "question": "Sleep efficiency is total sleep time (all epochs scored N1, N2, N3 or R) divided by total recording "
                     "time from lights out to lights on, times 100. Using only this hypnogram, what is the sleep efficiency "
                     "in percent? Answers within ±2 are accepted.",
         "answer": s["SE"],
         "traps": {"stopped_at_final_wake": round(100 * s["TST"] / (s["TRT"] - 36), 1),
                   "only_initial_wake_removed": round(100 * (s["TRT"] - s["SL"]) / s["TRT"], 1)}},
        {"id": "h_report_audit_rows", "level": "hard", "images": ["brain_report_b.png", "brain_hypnogram.png"],
         "answer_type": "sequence",
         "question": REPORT_INTRO + "Using the definitions printed in the report, check every row of the 'Sleep "
                     "architecture' and 'Sleep stages' tables against the hypnogram. Which rows contain a value that differs "
                     "from the hypnogram by more than 5 minutes (or more than 2 percentage points)? List the row names in "
                     "the order they appear, separated by commas, without the part in brackets. If every row matches, "
                     "answer none.",
         "answer": ["Wake after sleep onset", "N2", "N3"],
         "traps": {"only_waso_found": ["Wake after sleep onset"], "only_stage_shift_found": ["N2", "N3"],
                   "trusted_report": ["none"], "waso_and_n3_only": ["Wake after sleep onset", "N3"]}},
        {"id": "h_report_true_n3", "level": "hard", "images": ["brain_report_b.png", "brain_hypnogram.png"],
         "answer_type": "number", "tolerance_abs": 8,
         "question": REPORT_INTRO + "The N3 minutes printed in the report are wrong. How many minutes of N3 does the "
                     "hypnogram actually show? Answers within ±8 are accepted.",
         "answer": s["stage_min"]["N3"],
         "traps": {"kept_printed_value": PLANTS["B"]["N3"], "first_N3_block_only": 38.0, "second_N3_block_only": 28.0}},
        {"id": "h_report_true_waso", "level": "hard", "images": ["brain_report_b.png", "brain_hypnogram.png"],
         "answer_type": "number", "tolerance_abs": 6,
         "question": REPORT_INTRO + "Using the WASO definition (all wake after sleep onset, up to lights on), how many "
                     "minutes of WASO does the hypnogram show? Answers within ±6 are accepted.",
         "answer": s["WASO"],
         "traps": {"kept_printed_value": PLANTS["B"]["Wake after sleep onset"],
                   "included_initial_wake": s["WASO"] + s["SL"]}},
        {"id": "h_longest_rem", "level": "hard", "images": ["brain_hypnogram.png"], "answer_type": "integer",
         "question": "Number the REM periods on this hypnogram 1, 2, 3 ... in time order. Which REM period is the longest? "
                     "Answer with its number.",
         "answer": int(np.argmax(rem_blocks)) + 1,
         "traps": {"last_period": len(rem_blocks), "picked_by_eye_fourth": 4 if int(np.argmax(rem_blocks)) + 1 != 4 else 3}},
    ]


def questions(p):
    s = night_stats(p)
    h, m, sec = p["eeg"]["start_clock"]
    eeg_min = (h - 23) * 60 + m + sec / 60
    easy = [
        {"id": "hyp_rem_latency", "images": ["brain_hypnogram.png"], "answer_type": "number", "tolerance_abs": 5,
         "question": "REM latency is the time from sleep onset (the first epoch scored as any sleep stage) to the first "
                     "epoch scored as REM. What is the REM latency on this hypnogram, in minutes? Answers within ±5 are accepted.",
         "answer": s["REML"], "traps": {"measured_from_lights_out": s["REML_from_lights_out"],
                                        "used_second_rem_period": s["second_REM_from_onset"]}},
        {"id": "eeg_plus_hypnogram_stage", "images": ["brain_eeg_page.png", "brain_hypnogram.png"], "answer_type": "label",
         "question": "Image 1 is an EEG page; its clock times are printed along the top. Image 2 is the hypnogram for the "
                     "same night. What sleep stage (W, N1, N2, N3 or R) was scored at the time this EEG page was recorded?",
         "answer": stage_at(p, eeg_min), "traps": {"next_stage": "N1", "light_sleep": "N2"}},
        {"id": "report_vs_hypnogram_line", "images": ["brain_report.png", "brain_hypnogram.png"], "answer_type": "label",
         "question": "Image 1 is a sleep study summary report and image 2 is the hypnogram it was produced from. Exactly one "
                     "value in the 'Sleep architecture' table does not match the hypnogram. Which measure is it? Answer with "
                     "the measure's name as printed, without the part in brackets.",
         "answer": "REM latency",
         "traps": {"sleep_latency": "Sleep latency", "waso": "Wake after sleep onset", "awakenings": "Number of awakenings"}},
        {"id": "report_vs_hypnogram_value", "images": ["brain_report.png", "brain_hypnogram.png"], "answer_type": "number",
         "tolerance_abs": 5,
         "question": "Image 1 is a sleep study summary report and image 2 is the hypnogram it was produced from. The REM "
                     "latency printed in the report is wrong. Using the definition printed in the report, what should it be, "
                     "in minutes? Answers within ±5 are accepted.",
         "answer": s["REML"], "traps": {"kept_printed_value": PLANTS["A"]["REM latency"], "measured_from_lights_out": s["REML_from_lights_out"],
                                        "used_second_rem_period": s["second_REM_from_onset"]}},
        {"id": "scalp_max_alpha", "images": ["brain_scalp_map.png"], "answer_type": "label",
         "question": "On this alpha-band scalp map (head seen from above, nose at the top, L = left), which labelled electrode "
                     "has the highest alpha amplitude?",
         "answer": max(p["alpha_uv"], key=p["alpha_uv"].get), "traps": {"mirror_side": "O2", "midline": "Pz"}},
    ]
    return [{**q, "level": q.get("level", "easy")} for q in easy] + hard_questions(p)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "samples/brain"
    os.makedirs(out, exist_ok=True)
    p = patient(11)
    draw_eeg(p, os.path.join(out, "brain_eeg_page.png"))
    draw_scalp(p, os.path.join(out, "brain_scalp_map.png"))
    draw_hypnogram(p, os.path.join(out, "brain_hypnogram.png"))
    draw_report(p, os.path.join(out, "brain_report.png"), PLANTS["A"])
    draw_report(p, os.path.join(out, "brain_report_b.png"), PLANTS["B"])
    st = night_stats(p); st.pop("rows")
    json.dump({"patient": p, "true_values": st, "planted_errors": PLANTS}, open(os.path.join(out, "brain_patient.json"), "w"), indent=1)
    json.dump(questions(p), open(os.path.join(out, "brain_questions.json"), "w"), indent=1)
    print(json.dumps(st, indent=1))
