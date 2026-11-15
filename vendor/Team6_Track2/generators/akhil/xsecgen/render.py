"""CAD-style multi-panel cross-section sheet rendered purely from the data JSON."""
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.ticker import MultipleLocator
from PIL import Image
from .xsec import fmt_sta

DPI = 150
STYLES = [
    dict(bg="#f6f3ea", gmaj="#b4bfca", gmin="#e2e5e6", eg="#2a2a2a", prop="#a82a2a", cl="#1f4e79", txt="#161616", font="DejaVu Sans"),
    dict(bg="#ffffff", gmaj="#9c9c9c", gmin="#e8e8e8", eg="#000000", prop="#000000", cl="#444444", txt="#000000", font="DejaVu Sans Mono"),
    dict(bg="#f3f7ef", gmaj="#9fbf9a", gmin="#dde9d8", eg="#3a3a3a", prop="#0b4f8a", cl="#7a3b00", txt="#101810", font="DejaVu Serif"),
]


def _window(data):
    xs = [abs(p[0]) for s in data["sections"] for p in s["template"]]
    xw = max(60, int(math.ceil((max(xs) + 8) / 10.0) * 10))
    need, loc = 0.0, []
    for s in data["sections"]:
        ys = [z for x, z in s["ground"] if abs(x) <= xw] + [p[1] for p in s["template"]]
        loc.append(min(ys))
        need = max(need, max(ys) - min(ys) + 2)
    span = int(math.ceil((need + 2) / 2.0) * 2)
    return xw, span, loc


def render_sheet(data, path):
    """Render sheet to `path` (PNG). Returns pixel metadata used by validate/ to check image == data."""
    st = STYLES[data["style"] % len(STYLES)]
    plt.rcParams["font.family"] = st["font"]
    ve, dens = data["ve"], data["density"]
    secs = data["sections"]
    n = len(secs)
    rows = int(math.ceil(n / 2.0))
    xw, span, loc = _window(data)
    pw = 5.2
    h_ax = pw * span * ve / (2 * xw)
    pad = 1.15
    fig_h = rows * (h_ax + pad) + 2.7
    fig, axes = plt.subplots(rows, 2, figsize=(14, fig_h), dpi=DPI)
    fig.patch.set_facecolor(st["bg"])
    fig.subplots_adjust(left=0.07, right=0.975, top=1 - 1.25 / fig_h, bottom=1.45 / fig_h,
                        hspace=pad / h_ax, wspace=0.17)
    axes = np.atleast_1d(axes).flatten()
    rs = np.random.default_rng([data["seed"], 99])
    meta = dict(panels=[])
    for i, ax in enumerate(axes):
        if i >= n:
            ax.axis("off")
            continue
        s = secs[i]
        gx, gy = zip(*s["ground"]); tx, ty = zip(*s["template"])
        lo = 2 * math.floor((loc[i] - 1) / 2.0)
        ax.set_facecolor(st["bg"])
        ax.set_xlim(-xw, xw); ax.set_ylim(lo, lo + span); ax.set_aspect(ve)
        ax.xaxis.set_major_locator(MultipleLocator(20)); ax.xaxis.set_minor_locator(MultipleLocator(10))
        ax.yaxis.set_major_locator(MultipleLocator(2)); ax.yaxis.set_minor_locator(MultipleLocator(0.5))
        ax.grid(which="major", color=st["gmaj"], lw=0.6); ax.grid(which="minor", color=st["gmin"], lw=0.35)
        ax.set_axisbelow(True)
        ax.plot(gx, gy, color=st["eg"], lw=0.9, ls=(0, (5, 2)), label="EXISTING GROUND", zorder=3)
        ax.plot(tx, ty, color=st["prop"], lw=2.0, solid_capstyle="round", label="PROPOSED TEMPLATE", zorder=4)
        ax.axvline(0, color=st["cl"], lw=0.8, ls="-.", zorder=2)
        ax.text(1.2, lo + span - 0.5, "CL", color=st["cl"], fontsize=7, va="top")
        ax.set_title("STA %s" % fmt_sta(s["station"]), loc="left", fontsize=11, fontweight="bold", color=st["txt"])
        ax.set_title("CL PROP. FG EL %.2f" % s["fg"], loc="right", fontsize=7.5, color=st["txt"])
        ax.tick_params(labelsize=7, colors=st["txt"])
        ax.set_xlabel("OFFSET FROM CL (ft)", fontsize=7, color=st["txt"]); ax.set_ylabel("ELEVATION (ft)", fontsize=7, color=st["txt"])
        for sp in ax.spines.values():
            sp.set_linewidth(1.0); sp.set_color(st["txt"])
        for side in ("-1", "1"):
            inf = s["info"][side]
            dx, dy = inf["daylight"]
            seg = [p for p in s["template"] if (p[0] <= inf["edge"][0] if side == "-1" else p[0] >= inf["edge"][0])]
            ax.text(dx + (4 if side == "1" else -4), dy + 0.8, "%g:1" % inf["ratio"], fontsize=6, color=st["prop"], ha="center", va="bottom")
            if dens >= 1:
                ax.plot([dx], [dy], marker="o", ms=3, mfc="none", mec=st["prop"], mew=0.7, zorder=5)
                ax.text(dx, dy - 0.6, "%.1f'" % abs(dx), fontsize=5.5, color=st["txt"], ha="center", va="top")
        if dens >= 1:
            C = data["corridor"]
            y_top = lo + span - 1.2
            for xc, lab in ((-(12 + C["swL"] / 2.0), "%d'" % C["swL"]), (-6, "12'"), (6, "12'"), (12 + C["swR"] / 2.0, "%d'" % C["swR"])):
                ax.text(xc, y_top, lab, fontsize=5.5, ha="center", color=st["txt"])
        if dens >= 2:
            for xq in (-0.75 * xw, -0.45 * xw, 0.45 * xw, 0.75 * xw):
                j = int(np.argmin([abs(p[0] - xq) for p in s["ground"]]))
                ax.text(s["ground"][j][0], s["ground"][j][1] + 0.7, "%.1f" % s["ground"][j][1], fontsize=5, color=st["txt"], ha="center", clip_on=True)
        ax.legend(loc="lower center", fontsize=6, ncol=2, frameon=True, facecolor=st["bg"], edgecolor=st["gmaj"])
        s_meta = dict(station=s["station"], ground_px=[], template_px=[], axes_px=None)
        meta["panels"].append(s_meta)
    # sheet furniture
    fig.add_artist(Rectangle((0.004, 0.004), 0.992, 0.992, transform=fig.transFigure, fill=False, lw=1.6, ec=st["txt"]))
    tb = 0.95 / fig_h
    fig.add_artist(Rectangle((0.004, 0.004), 0.992, tb, transform=fig.transFigure, fill=False, lw=1.2, ec=st["txt"]))
    for xv in (0.38, 0.62, 0.80):
        fig.add_artist(plt.Line2D([xv, xv], [0.004, 0.004 + tb], transform=fig.transFigure, lw=0.9, color=st["txt"]))
    a, b = fmt_sta(data["stations"][0]), fmt_sta(data["stations"][-1])
    ty = 0.004 + tb / 2
    fig.text(0.012, ty, "PROJECT: %s\nSYNTHETIC TRAINING SHEET - NOT FOR CONSTRUCTION" % data["project"], fontsize=7.5, va="center", color=st["txt"])
    fig.text(0.39, ty, "ROADWAY CROSS SECTIONS\nSTA %s TO STA %s" % (a, b), fontsize=7.5, va="center", color=st["txt"])
    fig.text(0.63, ty, "SCALE  H: 1\" = 20'\n       V: 1\" = %g'   (%g:1 EXAGG.)" % (20.0 / ve, ve), fontsize=7.5, va="center", color=st["txt"])
    fig.text(0.81, ty, "SHEET XS-1\nGEN %s  SEED %d" % (data["generator_version"], data["seed"]), fontsize=7.5, va="center", color=st["txt"])
    fig.text(0.5, 1 - 0.45 / fig_h, "%s  -  ROADWAY CROSS SECTIONS" % data["project"], ha="center", fontsize=14, fontweight="bold", color=st["txt"])
    fig.text(0.5, 1 - 0.85 / fig_h, "TYPICAL SECTION: 2 @ 12' LANES, SHOULDER AND SLOPES AS SHOWN.  EXISTING GROUND DASHED, PROPOSED TEMPLATE SOLID.  UNITS: FEET.",
             ha="center", fontsize=7, color=st["txt"])
    fig.canvas.draw()
    W, H = fig.canvas.get_width_height()
    for i, s_meta in enumerate(meta["panels"]):
        ax, s = axes[i], secs[i]
        tr = ax.transData
        s_meta["ground_px"] = [[float(a_), float(H - b_)] for a_, b_ in tr.transform(s["ground"])]
        s_meta["template_px"] = [[float(a_), float(H - b_)] for a_, b_ in tr.transform(s["template"])]
        o, ex, ey = tr.transform((0, 0)), tr.transform((1, 0)), tr.transform((0, 1))
        s_meta["px_per_ft_x"] = float(abs(ex[0] - o[0])); s_meta["px_per_ft_y"] = float(abs(ey[1] - o[1]))
        s_meta["xlim"] = [-xw, xw]
    meta.update(width=W, height=H, xw=xw, span=span)
    arr = np.asarray(fig.canvas.buffer_rgba())[:, :, :3].astype(np.float32)
    plt.close(fig)
    if data["noise"] > 0:
        arr = arr + rs.normal(0, data["noise"], arr.shape)
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(path)
    return meta
