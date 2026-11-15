"""Roadway cut/fill cross-section task generator.

Data first, image second: every sheet is a pure function of the JSON data
(plus the seed, which only drives optional scan noise). Reference answers are
computed from the data, never from the picture.
"""
import math
import numpy as np

GEN_VERSION = "xsec-0.2"
GX = 100.0        # ground survey extent each side of CL (ft)
U_MAX = 99.0      # farthest daylight search (ft)
DITCH_DEPTH = 1.5

LEVELS = {
    "easy":   dict(n=4,  spacings=[50],              ve=2.0, mixed=False, ditch="flat", asym=False, density=0, noise=0.0),
    "medium": dict(n=6,  spacings=[25, 50, 75],      ve=4.0, mixed=True,  ditch="mix",  asym=False, density=1, noise=0.0),
    "hard":   dict(n=8,  spacings=[25, 50, 75, 100], ve=5.0, mixed=True,  ditch="mix",  asym=False, density=2, noise=3.0),
    "expert": dict(n=10, spacings=[25, 50, 75, 100], ve=5.0, mixed=True,  ditch="mix",  asym=True,  density=2, noise=4.0),
}

PROJECTS = ["SR 114 REALIGNMENT", "CR 22 WIDENING AND DRAINAGE", "US 50 RECONSTRUCTION",
            "FOREST ROUTE 7  -  MP 4.2 TO MP 5.1", "RIVERSIDE PARKWAY EXTENSION"]


class Retry(Exception):
    """Raised when a random draw gives an invalid / ambiguous geometry."""


def fmt_sta(s):
    return "%d+%02d" % (s // 100, s % 100)


def interp(poly, x):
    return float(np.interp(x, [p[0] for p in poly], [p[1] for p in poly]))


# ----------------------------------------------------------------- terrain
def make_terrain(rng):
    return dict(
        z0=float(rng.uniform(380, 520)), long_slope=float(rng.uniform(-0.025, 0.025)),
        cross=float(rng.uniform(-0.12, 0.12)),
        hills=[dict(a=float(rng.uniform(-3.5, 3.5)), sc=float(rng.uniform(-0.1, 1.0)),
                    sw=float(rng.uniform(0.25, 0.5)), xc=float(rng.uniform(-70, 70)),
                    xw=float(rng.uniform(15, 35))) for _ in range(3)],
        ph=[float(v) for v in rng.uniform(0, 2 * math.pi, 3)])


def ground_z(T, x, s, s0, L):
    u, ds = (s - s0) / L, s - s0
    z = T["z0"] + T["long_slope"] * ds + T["cross"] * x
    for h in T["hills"]:
        z += h["a"] * math.exp(-((x - h["xc"]) / h["xw"]) ** 2 - ((u - h["sc"]) / h["sw"]) ** 2)
    z += 0.9 * math.sin(x / 19 + T["ph"][0] + ds / 70) + 0.35 * math.sin(x / 7.3 + T["ph"][1] - ds / 35)
    z += 0.12 * math.sin(x / 2.9 + T["ph"][2] + s / 11)
    return z


def survey_shots(rng):
    xs = np.arange(-GX, GX + 0.1, 5.0)
    xs[1:-1] += rng.uniform(-1.2, 1.2, len(xs) - 2)
    return sorted(set([round(float(x), 1) for x in xs] + [0.0]))


# ---------------------------------------------------------------- template
def first_crossing(P_u, g_u):
    pu, py = [p[0] for p in P_u], [p[1] for p in P_u]
    gu, gz = [p[0] for p in g_u], [p[1] for p in g_u]
    us = sorted(set(pu + [u for u in gu if pu[0] < u < pu[-1]]))
    d = lambda u: float(np.interp(u, pu, py) - np.interp(u, gu, gz))
    pu_, pd_ = us[0], d(us[0])
    for u in us[1:]:
        dd = d(u)
        if pd_ * dd < 0 or (dd == 0 and pd_ != 0):
            uc = pu_ + (pd_ / (pd_ - dd)) * (u - pu_)
            return uc, float(np.interp(uc, pu, py))
        pu_, pd_ = u, dd
    return None


def make_corridor(rng, cfg):
    sw = int(rng.choice([4, 6, 8, 10]))
    C = dict(lane=12, swL=sw, swR=sw, cf=float(rng.choice([0.02, 0.025, 0.03])),
             cfsh=float(rng.choice([0.04, 0.05, 0.06])), super=False,
             r_fill=int(rng.choice([2, 3, 4])), rc=int(rng.choice([2, 3])), fb=3.0)
    if cfg["asym"]:
        C["swR"] = int(rng.choice([4, 6, 8, 10]))
        C["super"] = bool(rng.random() < 0.5)
        C["r_fill"] = int(rng.choice([2, 3]))
        C["rc"] = 2
    return C


def build_template(C, fg, g, ditch):
    """Template polyline [(x, y)] from left daylight to right daylight, plus slope info."""
    sL, sR = C["cf"], (C["cf"] if C["super"] else -C["cf"])      # lane slope dy/dx
    pts, info = {}, {}
    for side, sw, sl in ((-1, C["swL"], sL), (1, C["swR"], sR)):
        y12 = fg + sl * side * 12
        ssh = math.copysign(C["cfsh"], sl)
        xe = side * (12 + sw)
        ye = y12 + ssh * (xe - side * 12)
        pts[side] = [(side * 12, y12), (xe, ye)]
        u0 = abs(xe)
        g_u = sorted([(side * x, z) for x, z in g])
        cut = interp(g, xe) > ye
        if cut:
            ub = u0 + 6 + (C["fb"] if ditch == "flat" else 0.0)
            P = [(u0, ye), (u0 + 6, ye - DITCH_DEPTH)]
            if ditch == "flat":
                P.append((ub, ye - DITCH_DEPTH))
            P.append((GX, ye - DITCH_DEPTH + (GX - ub) / C["rc"]))
            ratio = C["rc"]
        else:
            P = [(u0, ye), (GX, ye - (GX - u0) / C["r_fill"])]
            ratio = C["r_fill"]
        hit = first_crossing(P, g_u)
        if hit is None or hit[0] > U_MAX:
            raise Retry("no daylight")
        uc, yc = hit
        kept = [p for p in P[1:] if p[0] < uc - 1e-6]
        pts[side] += [(side * p[0], p[1]) for p in kept] + [(side * uc, yc)]
        info[side] = dict(kind="cut" if cut else "fill", ratio=ratio, ditch=ditch if cut else None,
                          daylight=[round(side * uc, 3), round(yc, 3)], edge=[round(xe, 3), round(ye, 3)])
    allp = pts[-1] + [(0.0, fg)] + pts[1]
    tmpl = sorted(set((round(x, 3), round(y, 3)) for x, y in allp), key=lambda p: p[0])
    return tmpl, info


# ------------------------------------------------------------------ areas
def area_between(g, t, mode="cut"):
    """Exact area of max(g-t,0) ('cut') or max(t-g,0) ('fill') over the template extent."""
    x0, x1 = t[0][0], t[-1][0]
    bps = sorted(set([p[0] for p in g if x0 <= p[0] <= x1] + [p[0] for p in t] + [x0, x1]))
    sgn = 1.0 if mode == "cut" else -1.0
    d = lambda x: sgn * (interp(g, x) - interp(t, x))
    tot = 0.0
    for a, b in zip(bps[:-1], bps[1:]):
        da, db = d(a), d(b)
        if da >= 0 and db >= 0:
            tot += (da + db) / 2 * (b - a)
        elif da <= 0 and db <= 0:
            continue
        else:
            xc = a + (b - a) * da / (da - db)
            tot += da / 2 * (xc - a) if da > 0 else db / 2 * (b - xc)
    return tot


# ------------------------------------------------------------------- data
def make_data(seed, level, attempt_limit=50):
    cfg = LEVELS[level]
    for attempt in range(attempt_limit):
        rng = np.random.default_rng([seed, attempt])
        try:
            return _make_data(rng, seed, level, cfg, attempt)
        except Retry:
            continue
    raise Retry("could not build geometry for seed %s" % seed)


def _make_data(rng, seed, level, cfg, attempt):
    s0 = 1000 + 100 * int(rng.integers(0, 6))
    stations = [s0]
    for _ in range(cfg["n"] - 1):
        stations.append(stations[-1] + int(rng.choice(cfg["spacings"])))
    L = stations[-1] - s0
    T = make_terrain(rng)
    C = make_corridor(rng, cfg)
    gl = float(rng.uniform(-0.02, 0.02))
    lin = lambda s: gl * (s - s0)
    shots = {s: survey_shots(rng) for s in stations}
    gz = {s: [(x, round(ground_z(T, x, s, s0, L), 2)) for x in shots[s]] for s in stations}
    if cfg["mixed"]:
        c = float(np.median([interp(gz[s], 0.0) - lin(s) for s in stations])) + float(rng.uniform(-0.8, 0.8))
    else:
        c = min(min(z for x, z in gz[s] if abs(x) <= 32) - 1.0 - lin(s) for s in stations)
    secs = []
    for s in stations:
        fg = round(c + lin(s), 2)
        ditch = "flat" if cfg["ditch"] == "flat" else str(rng.choice(["v", "flat"]))
        tmpl, info = build_template(C, fg, gz[s], ditch)
        sec = dict(station=s, fg=fg, ground=[list(p) for p in gz[s]], template=[list(p) for p in tmpl],
                   info={str(k): v for k, v in info.items()})
        sec["cut_area"] = round(area_between(gz[s], tmpl, "cut"), 3)
        sec["fill_area"] = round(area_between(gz[s], tmpl, "fill"), 3)
        secs.append(sec)
    return dict(seed=seed, level=level, attempt=attempt, generator_version=GEN_VERSION, units="ft",
                ve=cfg["ve"], density=cfg["density"], noise=cfg["noise"], corridor=C,
                project=PROJECTS[int(rng.integers(len(PROJECTS)))], style=int(rng.integers(3)),
                stations=stations, sections=secs)


# -------------------------------------------------------------- questions
def evaluate(data, q, ground_shift=0.0):
    key = q["key"]
    A = {s["station"]: area_between([(x, z + ground_shift) for x, z in s["ground"]], s["template"], key)
         for s in data["sections"]}
    st = [s["station"] for s in data["sections"]]
    vols = [(a, b, (A[a] + A[b]) / 2 * (b - a) / 27) for a, b in zip(st[:-1], st[1:])]
    if q["qtype"] == "max_cut_interval":
        a, b, _ = max(vols, key=lambda t: t[2])
        return dict(value="%s-%s" % (fmt_sta(a), fmt_sta(b)), vols=vols)
    sel = [v for v in vols if q["from_sta"] <= v[0] and v[1] <= q["to_sta"]]
    return dict(value=sum(v[2] for v in sel), vols=vols)


def make_question(data, qtype, rng):
    st = data["stations"]
    n = len(st)
    q = dict(qtype=qtype, key="fill" if qtype == "fill_total" else "cut", from_sta=st[0], to_sta=st[-1])
    if qtype == "cut_between":
        span = int(rng.integers(3, min(5, n) + 1))
        i = int(rng.integers(0, n - span + 1))
        q["from_sta"], q["to_sta"] = st[i], st[i + span - 1]
    intro = "The sheet shows roadway cross sections of existing ground and the proposed template. "
    method = ("Use the average end-area method, V = (A1 + A2)/2 x L / 27, and use the station intervals shown on the sheet. ")
    tail = "Answer to the nearest cubic yard. Tolerance: +/-5%."
    A, B = fmt_sta(q["from_sta"]), fmt_sta(q["to_sta"])
    if qtype in ("cut_total", "cut_between"):
        text = intro + method + "Do not net cut against fill. What is the total CUT volume from Sta %s to Sta %s, in cubic yards? " % (A, B) + tail
    elif qtype == "fill_total":
        text = intro + method + "Do not net cut against fill. What is the total FILL volume from Sta %s to Sta %s, in cubic yards? " % (A, B) + tail
    else:
        text = intro + method + "Between which two consecutive stations is the CUT volume largest? Answer in the form 11+00-11+50."
    res = evaluate(data, q)
    label = qtype == "max_cut_interval"
    q.update(question=text, answer=res["value"] if label else round(res["value"], 1),
             answer_type="label" if label else "number")
    if not label:
        q["tolerance_rel"] = 0.05
    return q
