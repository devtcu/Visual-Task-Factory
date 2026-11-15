"""Brain connectivity network family: functional resilience questions on synthetic connectome diagrams.

Graphs are synthetic and only neuroscience-inspired: regions grouped into modules (sensory, thalamic, association,
motor, limbic), dense links inside a module, fewer links between modules, some redundant routes. Nothing here claims
to reproduce real brain anatomy or function, and no question asks for a diagnosis.

Question types
  redundant_edge  Four connections are marked A-D. Exactly one can be removed without increasing the shortest-path
                  distance from the sensory input region to the motor output region. Which one?
  min_edge_cut    The minimum number of connections whose removal disconnects the input region from the output region.
  critical_count  How many connections are critical: removing any one of them on its own increases the shortest-path
                  distance (or disconnects). The reader must test every connection, not four marked ones.
  delay_after_failure  Two marked connections X and Y fail together. What is the new shortest-path distance?

Levels
  1  undirected, every connection is one step            8-10 regions, 3 modules
  2  undirected, conduction delays printed on the lines  10-12 regions, 4 modules
  3  as 2 with tied fastest routes                       12-15 regions, 5 modules
  4  one-way connections (arrows); some region pairs have two curved arrows, one each way.
     Every level-4 task is built so that ignoring the arrow direction gives a different answer.  11-14 regions, 4 modules
  5  level 4 plus three rules from real circuit diagrams, each one a trap for a reader who only follows lines:
     inhibitory connections (flat bar end) cannot carry the signal; a lesioned region lets no signal through; every
     region passed through adds its own processing delay. Same size as level 4: the difficulty is in the rules.
  6  connectogram layout, as in published connectome figures: regions on a circle grouped by module, one-way
     connections drawn as curves that sweep through the centre and cross. Every line has to be traced through
     crossings. Fairness guard: no two lines may run alongside each other, and no line may pass close to a region
     it does not connect.  12-14 regions, 4 modules

Reference answers come from NetworkX. resolve() recomputes them with a separate hand-written Dijkstra and max-flow."""
import heapq
from collections import deque
from itertools import combinations

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, Patch, Polygon
from PIL import Image

from . import common

FAMILY = "connectome"
QUESTION_TYPES = ("redundant_edge", "min_edge_cut", "critical_count", "delay_after_failure")
LEVELS = (1, 2, 3, 4, 5, 6)
LEVELS_FOR = {"redundant_edge": (1, 2, 3, 4), "min_edge_cut": (1, 2, 3, 4, 6),
              "critical_count": (1, 2, 3, 4, 5, 6), "delay_after_failure": (1, 2, 3, 4, 5, 6)}
DESIGN_TRIES = 1500         # candidate graphs per seed; hard levels accept only a few in a thousand
MODULES = {
    "Sensory": ("#3b7dd8", ["V1", "V2", "V4", "MT", "A1", "S1", "S2"]),
    "Thalamic": ("#8a5cc7", ["LGN", "MGN", "VPL", "Pulv", "MD", "VA"]),
    "Association": ("#2a9d8f", ["PPC", "IT", "STS", "dlPFC", "TPJ", "PCC", "FEF"]),
    "Motor": ("#c8473c", ["M1", "PMd", "PMv", "SMA", "BG", "Cb"]),
    "Limbic": ("#c98a12", ["Hipp", "Amyg", "ACC", "Ins", "OFC", "EC"]),
}
RING = ["Sensory", "Thalamic", "Association", "Motor", "Limbic"]
LEVEL_MODULES = {1: ["Sensory", "Association", "Motor"], 2: ["Sensory", "Thalamic", "Association", "Motor"], 3: RING, 4: ["Sensory", "Thalamic", "Association", "Motor"],
                 5: ["Sensory", "Thalamic", "Association", "Motor"]}
LEVEL_NODES = {1: (8, 10), 2: (10, 12), 3: (12, 15), 4: (11, 14), 5: (11, 14)}
NODE_R = 0.032
STAGE = {"Sensory": 0, "Thalamic": 1, "Association": 2, "Limbic": 2, "Motor": 3}   # usual direction of flow at level 4
BEND = 0.2                  # curvature of each arrow in a two-way pair
HEAD_L, HEAD_W = 0.022, 0.0085
EDGE_RGB = (74, 79, 87)
REFERENCES = {
    "redundant_edge": ["Dijkstra EW. A note on two problems in connexion with graphs. Numer Math. 1959;1:269-271",
                       "Sporns O. Networks of the Brain. MIT Press, 2010 (modular, redundant connectivity)"],
    "min_edge_cut": ["Menger's theorem: minimum s-t edge cut = maximum number of edge-disjoint s-t paths",
                     "Ford LR, Fulkerson DR. Maximal flow through a network. Can J Math. 1956;8:399-404"],
}


# ---------------------------------------------------------------- geometry
def _seg_dist(p, a, b):
    ab = b - a
    t = np.clip(np.dot(p - a, ab) / np.dot(ab, ab), 0, 1)
    return float(np.linalg.norm(p - (a + t * ab)))


def _poly_dist(p, pts):
    a, b = pts[:-1], pts[1:]
    ab = b - a
    t = np.clip(np.einsum("ij,ij->i", p - a, ab) / np.maximum(np.einsum("ij,ij->i", ab, ab), 1e-12), 0, 1)
    return float(np.min(np.linalg.norm(p - (a + t[:, None] * ab), axis=1)))


def _bezier(p0, p2, bend, t):
    """Quadratic curve from p0 to p2. Control point as matplotlib's arc3: midpoint + bend * (dy, -dx)."""
    d = p2 - p0
    c = (p0 + p2) / 2 + bend * np.array([d[1], -d[0]])
    t = np.atleast_1d(t)[:, None]
    return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * c + t ** 2 * p2


def curve(pos, u, v, bend, n=None):
    """Points along a connection: just the two ends for a straight line, 40 points for a curve, or n if given."""
    return _bezier(pos[u], pos[v], bend, np.linspace(0, 1, n or (40 if bend else 2)))


def _polys_cross(P, Q):
    if (P.max(0) < Q.min(0)).any() or (Q.max(0) < P.min(0)).any():
        return False
    o = lambda p, q, r: np.sign((q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0]))
    for a, b in zip(P[:-1], P[1:]):
        for c, d in zip(Q[:-1], Q[1:]):
            if o(a, b, c) * o(a, b, d) < 0 and o(c, d, a) * o(c, d, b) < 0:
                return True
    return False


def _ekey(u, v, directed):
    return f"{u}>{v}" if directed else "|".join(sorted((u, v)))


def arrow_head(pos, u, v, bend, tip_r):
    """Arrowhead triangle where the curve u->v meets a circle of radius tip_r around v."""
    pts = curve(pos, u, v, bend, 400)
    i = int(np.flatnonzero(np.linalg.norm(pts - pos[v], axis=1) > tip_r)[-1])
    tip, back = pts[i], pts[max(0, i - 8)]
    d = (tip - back) / np.linalg.norm(tip - back)
    n = np.array([-d[1], d[0]])
    base = tip - d * HEAD_L
    return np.array([tip, base + n * HEAD_W, base - n * HEAD_W]), d, n


# ---------------------------------------------------------------- graph
def _graph(rng, level, weighted):
    if level == 6:
        return _ring_graph(rng, weighted)
    mods = LEVEL_MODULES[level]
    k = len(mods)
    n = int(rng.integers(LEVEL_NODES[level][0], LEVEL_NODES[level][1] + 1))
    sizes = np.full(k, 2)
    for _ in range(n - 2 * k):
        sizes[rng.integers(k)] += 1
    if sizes.max() > 4:
        return None
    off, nodes, by_mod = rng.uniform(0, 2 * np.pi), [], {}
    for i, m in enumerate(mods):
        ang = off + 2 * np.pi * i / k
        c = 0.5 + 0.31 * np.array([np.cos(ang), np.sin(ang)])
        rm, phi0 = 0.05 + 0.018 * sizes[i], rng.uniform(0, 2 * np.pi)
        names = [str(x) for x in rng.choice(MODULES[m][1], sizes[i], replace=False)]
        by_mod[m] = names
        for j, name in enumerate(names):
            phi = phi0 + 2 * np.pi * j / sizes[i] + rng.uniform(-0.2, 0.2)
            x, y = c + rm * np.array([np.cos(phi), np.sin(phi)])
            if not (0.06 < x < 0.94 and 0.06 < y < 0.94):
                return None
            nodes.append({"name": name, "module": m, "x": round(float(x), 4), "y": round(float(y), 4)})
    pos = {nd["name"]: np.array([nd["x"], nd["y"]]) for nd in nodes}
    pairs = set()

    def add(u, v):
        """Only add a line that stays clear of every region it does not connect."""
        if any(_seg_dist(p, pos[u], pos[v]) < NODE_R + 0.015 for x, p in pos.items() if x not in (u, v)):
            return
        if level >= 4 and weighted and np.linalg.norm(pos[u] - pos[v]) < 0.13:
            return                                    # too short to hold both a delay label and an arrowhead
        pairs.add(tuple(sorted((u, v))))

    p_in = {1: 0.3, 2: 0.4, 3: 0.5, 4: 0.5, 5: 0.5}[level]
    for names in by_mod.values():
        if len(names) == 2:
            add(*names)
            continue
        for j in range(len(names)):
            add(names[j], names[(j + 1) % len(names)])
        for a, b in combinations(names, 2):
            if rng.random() < p_in:
                add(a, b)
    for i in range(k):
        A, B = by_mod[mods[i]], by_mod[mods[(i + 1) % k]]
        near = sorted((float(np.linalg.norm(pos[a] - pos[b])), a, b) for a in A for b in B)[:5]
        for idx in rng.choice(len(near), int(rng.integers(1, 3 + (level > 1))), replace=False):
            add(near[idx][1], near[idx][2])
    if level >= 2:
        far = [(i, j) for i in range(k) for j in range(i + 2, k) if not (i == 0 and j == k - 1)]
        for _ in range(int(rng.integers(0, min(level, 3)))):
            i, j = far[rng.integers(len(far))]
            a, b = min(((float(np.linalg.norm(pos[a] - pos[b])), a, b) for a in by_mod[mods[i]] for b in by_mod[mods[j]]))[1:]
            add(a, b)
    hi_w = 9 if level == 2 else 5     # levels 3-4 use a narrow delay range so tied fastest routes occur
    weight = lambda: int(rng.integers(1, hi_w + 1)) if weighted else 1
    directed = level >= 4
    mod_of = {nd["name"]: nd["module"] for nd in nodes}
    G = nx.DiGraph() if directed else nx.Graph()
    G.add_nodes_from(pos)
    for u, v in sorted(pairs):
        if not directed:
            G.add_edge(u, v, weight=weight(), bend=0.0)
        elif np.linalg.norm(pos[u] - pos[v]) > 0.2 and rng.random() < 0.3:
            G.add_edge(u, v, weight=weight(), bend=BEND); G.add_edge(v, u, weight=weight(), bend=BEND)
        else:
            fwd = (u, v) if STAGE[mod_of[u]] <= STAGE[mod_of[v]] else (v, u)   # mostly sensory -> motor
            a, b = fwd if rng.random() < 0.75 else fwd[::-1]
            G.add_edge(a, b, weight=weight(), bend=0.0)
    if directed:
        _space_arrowheads(G, pos)
    connected = nx.is_weakly_connected(G) if directed else nx.is_connected(G)
    if not connected or not _readable(G, pos, level):
        return None
    return G, nodes, pos, by_mod


def _space_arrowheads(G, pos):
    """Arrowheads arriving at one region must not overlap (a reader could not tell which line points in). Walk the
    connections in a fixed order; one whose head would overlap a head already kept is turned around when its other
    end has room and no reverse connection exists, and dropped otherwise."""
    tip = lambda u, v, b: arrow_head(pos, u, v, b, NODE_R * 1.12)[0][0]
    kept = {v: [] for v in G}
    for u, v in sorted(G.edges):
        b = G[u][v]["bend"]
        if all(np.linalg.norm(tip(u, v, b) - t) >= 1.5 * HEAD_W for t in kept[v]):
            kept[v].append(tip(u, v, b))
            continue
        w, rb = G[u][v]["weight"], -b
        G.remove_edge(u, v)
        if not G.has_edge(v, u) and all(np.linalg.norm(tip(v, u, rb) - t) >= 1.5 * HEAD_W for t in kept[u]):
            G.add_edge(v, u, weight=w, bend=rb)        # the same curve, now pointing the other way
            kept[u].append(tip(v, u, rb))
    return G


def _curves(G, pos):
    return {(u, v): curve(pos, u, v, G[u][v]["bend"]) for u, v in G.edges}


def _readable(G, pos, level):
    """Nodes well apart, no line passes through a region it does not connect, few line crossings."""
    names = list(pos)
    if any(np.linalg.norm(pos[a] - pos[b]) < 3.0 * NODE_R for a, b in combinations(names, 2)):
        return False
    cv = _curves(G, pos)
    for (u, v), pts in cv.items():
        if any(_poly_dist(pos[x], pts) < NODE_R + 0.015 for x in names if x not in (u, v)):
            return False
    if G.is_directed():                               # arrowheads arriving at one region must not overlap
        for v in names:
            tips = [arrow_head(pos, u, v, G[u][v]["bend"], NODE_R * 1.12)[0][0] for u in G.predecessors(v)]
            if any(np.linalg.norm(a - b) < 1.5 * HEAD_W for a, b in combinations(tips, 2)):   # closer = heads overlap
                return False
    E = list(cv)
    crossings = sum(_polys_cross(cv[e], cv[f]) for e, f in combinations(E, 2) if not set(e) & set(f))
    return crossings <= (60 if level == 6 else 2 * min(level, 3) + 1)   # level 6 is meant to cross


def _anchors(G, pos, labelled, big=()):
    """Where each edge label sits (fraction along its curve): clear of every node, every other label and other lines."""
    directed, cv = G.is_directed(), _curves(G, pos)
    ring = all(abs(np.linalg.norm(p - 0.5) - RING_R) < 1e-3 for p in pos.values())
    tips = {e: arrow_head(pos, *e, G[e[0]][e[1]]["bend"], NODE_R * 1.55)[0] for e in G.edges} if directed else {}
    big = {tuple(e) for e in big}
    wide = any(w != 1 for _, _, w in G.edges(data="weight"))   # marked labels read "X: 4 ms" (wide) or just "A" (narrow)
    big_line, big_node = (0.035, 0.065) if wide else (0.02, 0.045)
    placed, out = [], {}
    labelled = sorted(labelled, key=lambda e: tuple(e) not in big)     # the big marked labels are placed first
    for u, v in labelled:
        # a label must sit unambiguously on its own line: other lines keep clear of the whole label box
        clear = big_line if tuple((u, v)) in big else (0.022 if ring else 0.014)
        order = (0.4, 0.35, 0.45, 0.3, 0.5, 0.25, 0.55, 0.2, 0.6) if directed else (0.5, 0.45, 0.55, 0.4, 0.6, 0.35, 0.65, 0.3, 0.7, 0.25, 0.75)
        if ring:                                      # connectogram: busy centre, so search finely, source end first
            order = tuple(sorted(np.round(np.arange(0.12, 0.8, 0.02), 2), key=lambda x: abs(x - 0.25)))
        for t in order:                               # one-way: arrowheads sit at the target end, so try the source half first
            p = _bezier(pos[u], pos[v], G[u][v]["bend"], t)[0]
            # the whole label box, not just its centre, stays clear of every region (big marked boxes are wider)
            ok = all(np.linalg.norm(p - q) > NODE_R + (big_node if tuple((u, v)) in big else 0.028) for q in pos.values())
            ok = ok and all(np.linalg.norm(p - q) > 0.045 for q in placed)
            ok = ok and all(_poly_dist(p, np.r_[h, h[:1]]) > 0.02 for h in tips.values())
            ok = ok and all(_poly_dist(p, pts) > clear for e, pts in cv.items() if e != (u, v) and (directed or set(e) != {u, v}))
            if ok:
                placed.append(p); out[_ekey(u, v, directed)] = t
                break
        else:
            return None
    return out


def _data(G, nodes, s, t, weighted, candidates, label_t):
    return {"nodes": nodes, "directed": G.is_directed(), "weighted": weighted,
            "edges": [[u, v, int(G[u][v]["weight"]), float(G[u][v]["bend"])] for u, v in sorted(G.edges)],
            "input": s, "output": t, "candidates": candidates, "label_t": label_t,
            "modules": sorted({nd["module"] for nd in nodes}, key=RING.index)}


def _endpoints(rng, G, by_mod):
    s, t = str(rng.choice(by_mod["Sensory"])), str(rng.choice(by_mod["Motor"]))
    if G.has_edge(s, t) or G.has_edge(t, s) or not nx.has_path(G, s, t):
        return None, None
    return s, t


def _undirected(G):
    """How a reader who ignores the arrows sees the graph: one line per region pair, at the faster of its delays."""
    U = nx.Graph()
    U.add_nodes_from(G)
    for u, v, w in G.edges(data="weight"):
        if not U.has_edge(u, v) or w < U[u][v]["weight"]:
            U.add_edge(u, v, weight=w)
    return U


def make(seed, level, qtype="redundant_edge"):
    rng = np.random.default_rng(seed)
    if level not in LEVELS_FOR[qtype]:
        return None
    if level == 5:
        return _rules_task(rng, qtype)
    return {"redundant_edge": _redundant_edge, "min_edge_cut": _min_edge_cut, "critical_count": _critical_count,
            "delay_after_failure": _delay_after_failure}[qtype](rng, level)


INTRO = "This diagram shows a synthetic brain connectivity network. Each circle is a neural region. "
LINES = {False: "Each line is a bidirectional connection. ",
         True: "Each arrow is a one-way connection: a signal can only travel along it in the direction of the arrowhead. "
               "Where two regions are joined by two curved arrows, these are two separate one-way connections. "}


# ---------------------------------------------------------------- level 6: connectogram (ring) layout
RING_R = 0.37
RING_MODULES = ["Sensory", "Thalamic", "Association", "Motor"]


def _toward_centre_bend(p0, p2, k):
    """The bend that puts the curve's control point a fraction k of the way from the chord's midpoint to the centre.
    For two points on a circle the midpoint-to-centre direction is perpendicular to the chord, so this is exact."""
    d, mid = p2 - p0, (p0 + p2) / 2
    off = k * (np.array([0.5, 0.5]) - mid)
    return float(np.dot(off, [d[1], -d[0]]) / np.dot(d, d))


def _ring_graph(rng, weighted):
    n = int(rng.integers(12, 15))
    sizes = np.full(4, 3)
    for _ in range(n - 12):
        sizes[rng.integers(4)] += 1
    step, off = 2 * np.pi / (n + 4), rng.uniform(0, 2 * np.pi)      # one empty slot between modules
    nodes, by_mod, slot = [], {}, 0
    for i, m in enumerate(RING_MODULES):
        names = [str(x) for x in rng.choice(MODULES[m][1], sizes[i], replace=False)]
        by_mod[m] = names
        for name in names:
            a = off + step * slot
            slot += 1
            x, y = 0.5 + RING_R * np.cos(a), 0.5 + RING_R * np.sin(a)
            nodes.append({"name": name, "module": m, "x": round(float(x), 4), "y": round(float(y), 4)})
        slot += 1
    pos = {nd["name"]: np.array([nd["x"], nd["y"]]) for nd in nodes}
    mod_of = {nd["name"]: nd["module"] for nd in nodes}
    pairs = set()
    for names in by_mod.values():
        for a, b in zip(names, names[1:]):
            if rng.random() < 0.8:
                pairs.add((a, b))
        if len(names) >= 3 and rng.random() < 0.4:
            pairs.add((names[0], names[-1]))
    allp = [(a, b) for a, b in combinations(list(pos), 2) if mod_of[a] != mod_of[b]]
    for i in rng.choice(len(allp), int(rng.integers(n - 2, n + 2)), replace=False):
        pairs.add(allp[i])
    weight = lambda: int(rng.integers(1, 6)) if weighted else 1
    G = nx.DiGraph()
    G.add_nodes_from(pos)
    for u, v in sorted(pairs):
        span = np.linalg.norm(pos[u] - pos[v]) / (2 * RING_R)
        k = 0.06 + 0.3 * span                         # gentle sweep: lines cross at clear angles instead of bundling
        fwd = (u, v) if STAGE[mod_of[u]] <= STAGE[mod_of[v]] else (v, u)
        if span > 0.4 and rng.random() < 0.25:        # two-way pair: two curves, bowed by different amounts
            G.add_edge(*fwd, weight=weight(), bend=_toward_centre_bend(pos[fwd[0]], pos[fwd[1]], k))
            G.add_edge(fwd[1], fwd[0], weight=weight(), bend=_toward_centre_bend(pos[fwd[1]], pos[fwd[0]], -k * 0.6))
        else:
            a, b = fwd if rng.random() < 0.75 else fwd[::-1]
            bend = _toward_centre_bend(pos[a], pos[b], k)
            if span < 0.35:                           # short link between ring neighbours: an arc outside the ring,
                bend = -np.sign(bend) * 0.6           # clear of the crossing traffic and with room for its label
            G.add_edge(a, b, weight=weight(), bend=bend)
    _space_arrowheads(G, pos)
    if not nx.is_weakly_connected(G) or not _readable(G, pos, 6) or not _traceable(G, pos):
        return None
    return G, nodes, pos, by_mod


def _traceable(G, pos):
    """Fairness guard for crossing curves: lines may cross, but no two may run alongside each other (a reader could
    switch lines there). Near a region both lines touch, closeness is expected and ignored."""
    cv = {e: curve(pos, *e, G[e[0]][e[1]]["bend"], 40) for e in G.edges}
    E = list(cv)
    for e, f in combinations(E, 2):
        shared = set(e) & set(f)
        A, B = cv[e], cv[f]
        if (A.max(0) < B.min(0) - 0.02).any() or (B.max(0) < A.min(0) - 0.02).any():
            continue
        pts = [p for p in A if all(np.linalg.norm(p - pos[s]) > 0.1 for s in shared)]
        if sum(_poly_dist(p, B) < 0.008 for p in pts) > 3:   # passes a crossing steeper than ~20 deg, fails a parallel run
            return False
    return True


# ---------------------------------------------------------------- question type 1: functional redundancy
def _dist(G, s, t, weight, drop=None):
    """Shortest-path distance s->t, after removing one edge (u, v) or a list of edges."""
    H = G.copy()
    for e in ([drop] if drop and not isinstance(drop, list) else drop or []):
        H.remove_edge(*e)
    try:
        return nx.shortest_path_length(H, s, t, weight=weight)
    except nx.NetworkXNoPath:
        return float("inf")


def _redundant_edge(rng, level):
    """L1 step counts; the answer touches the fastest route. L2 delays; the answer is a slow shortcut between two
    regions on the fastest route. L3 delays; the answer lies ON a fastest route, but a tied route exists.
    L4 one-way delays; ignoring the arrows changes the fastest route."""
    weighted, directed = level >= 2, level == 4
    built = _graph(rng, level, weighted)
    if built is None:
        return None
    G, nodes, pos, by_mod = built
    s, t = _endpoints(rng, G, by_mod)
    if s is None:
        return None
    w = "weight" if weighted else None
    d0, h0 = _dist(G, s, t, w), _dist(G, s, t, None)
    U = _undirected(G) if directed else None
    if directed and _dist(U, s, t, w) >= d0:
        return None                                   # direction must matter
    paths = list(nx.all_shortest_paths(G, s, t, weight=w))
    on_nodes = set().union(*paths)
    on_edges = {(a, b) for p in paths for a, b in zip(p, p[1:])}
    on_edges |= set() if directed else {(b, a) for a, b in on_edges}
    removable = [e for e in G.edges if _dist(G, s, t, w, e) == d0]
    critical = [e for e in G.edges if _dist(G, s, t, w, e) > d0]
    pool = {1: [e for e in removable if e[0] in on_nodes or e[1] in on_nodes],
            2: [e for e in removable if e[0] in on_nodes and e[1] in on_nodes and e not in on_edges],
            3: [e for e in removable if e in on_edges],
            4: [e for e in removable if e[0] in on_nodes and e[1] in on_nodes]}[level]
    if directed:   # an arrow into IN or out of OUT is useless at a glance: never offer it
        pool = [e for e in pool if e[1] != s and e[0] != t]
    if not pool or len(critical) < 3:
        return None
    correct = pool[rng.integers(len(pool))]

    def und_safe(e):                                  # removable for a reader who ignores the arrows
        if not directed:
            return False
        H = G.copy(); H.remove_edge(*e)
        return _dist(_undirected(H), s, t, w) == _dist(U, s, t, w)

    hop_safe = [e for e in critical if _dist(G, s, t, None, e) == h0]
    lure = [e for e in critical if und_safe(e)] if directed else hop_safe
    if level in (2, 4) and not lure:
        return None
    first = [lure[rng.integers(len(lure))]] if (weighted and lure) else []
    rest = [e for e in critical if e not in first]
    picks = first + [rest[i] for i in rng.choice(len(rest), 3 - len(first), replace=False)]
    opts = [correct] + picks
    order = rng.permutation(4)
    cand = {"ABCD"[i]: list(opts[order[i]]) for i in range(4)}
    deg = {L: G.degree(u) + G.degree(v) for L, (u, v) in cand.items()}
    ans = next(L for L, e in cand.items() if tuple(e) == tuple(correct))
    if deg[ans] in (max(deg.values()), min(deg.values())) and list(deg.values()).count(deg[ans]) == 1:
        return None                                   # degree alone would give the answer away
    label_t = _anchors(G, pos, list(G.edges) if weighted else [tuple(e) for e in cand.values()], big=cand.values())
    if label_t is None:
        return None
    hub = max(deg, key=deg.get)
    slowest = max(cand, key=lambda L: G[cand[L][0]][cand[L][1]]["weight"])
    traps = {}
    for L, (u, v) in sorted(cand.items()):
        if L == ans:
            continue
        if und_safe((u, v)):
            name = "ignored_arrow_direction"
        elif weighted and _dist(G, s, t, None, (u, v)) == h0:
            name = "counted_steps_not_delays"
        elif L == hub:
            name = "picked_hub_connection"
        elif weighted and L == slowest:
            name = "slow_link_assumed_unused"
        else:
            name = "on_every_fastest_route"
        traps[name if name not in traps else f"{name}_{L}"] = L
    route = (f"A signal travels from the sensory input region {s} (marked IN) to the motor output region {t} "
             f"(marked OUT) along the route with the {'smallest total delay' if weighted else 'fewest steps'}. ")
    metric = ("Each connection is labelled with its conduction delay in milliseconds. " if weighted
              else "Every connection counts as one step. ")
    quantity = "smallest total delay" if weighted else "fewest number of steps"
    q = (INTRO + LINES[directed] + metric + route + f"Four connections are marked A, B, C and D. Exactly one of them "
         f"can be removed on its own without increasing the {quantity} from {s} to {t}. Which one? Answer with a single letter.")
    arrow = " -> " if directed else " - "
    spec = {"family": FAMILY, "question_type": "redundant_edge", "level": level,
            "data": _data(G, nodes, s, t, weighted, cand, label_t), "question": q, "answer": ans,
            "answer_type": "multiple_choice", "references": REFERENCES["redundant_edge"],
            "options": [f"{u}{arrow}{v}" + (f" ({G[u][v]['weight']} ms)" if weighted else "") for L, (u, v) in sorted(cand.items())],
            "wrong_answers": traps, "target_mistake": next(iter(traps)),
            "uniqueness": {"ok": True, "why": f"of the 4 marked connections only {ans} leaves the distance at {d0:g}; "
                                              f"removing each other one raises it ({len(paths)} fastest route(s))"},
            "facts": {"distance": d0, "hop_distance": h0, "fastest_routes": paths,
                      "distance_ignoring_arrows": _dist(U, s, t, w) if directed else None,
                      "distance_without": {L: _dist(G, s, t, w, tuple(e)) for L, e in cand.items()}}}
    return spec


# ---------------------------------------------------------------- question type 2: critical connection failure
def _min_edge_cut(rng, level):
    """Answer range rises with level and always sits below both endpoint degrees. At level 4 the answer counts
    one-way connections from IN to OUT, and ignoring the arrows must give a different number."""
    directed = level >= 4
    built = _graph(rng, level, weighted=False)
    if built is None:
        return None
    G, nodes, pos, by_mod = built
    s, t = _endpoints(rng, G, by_mod)
    if s is None:
        return None
    k = nx.edge_connectivity(G, s, t)
    lo, hi = {1: (1, 2), 2: (2, 3), 3: (3, 4), 4: (2, 3), 6: (2, 4)}[level]
    out_deg = G.out_degree(s) if directed else G.degree(s)
    in_deg = G.in_degree(t) if directed else G.degree(t)
    if not lo <= k <= hi or min(out_deg, in_deg) < k + 1:
        return None
    cut = sorted(tuple(e) if directed else tuple(sorted(e)) for e in nx.minimum_edge_cut(G, s, t))
    mod_s = {nd["name"] for nd in nodes if nd["module"] == "Sensory"}
    traps = {}
    if directed:
        U = _undirected(G)
        traps["ignored_arrow_direction"] = nx.edge_connectivity(U, s, t)
        traps["cut_in_reverse_direction"] = nx.edge_connectivity(G, t, s) if nx.has_path(G, t, s) else 0
        if traps["ignored_arrow_direction"] == k:
            return None                               # direction must matter
    traps.update({"min_degree_of_endpoints": min(out_deg, in_deg), "node_cut_size": nx.node_connectivity(G, s, t),
                  "hop_distance": nx.shortest_path_length(G, s, t), "assumed_single_bridge": 1,
                  "counted_edges_leaving_input_module": sum((u in mod_s) != (v in mod_s) for u, v in G.edges)})
    goal = "no signal can travel from" if directed else "no path at all remains between"
    q = (INTRO + LINES[directed] + f"What is the minimum number of connections that must be removed so that {goal} "
         f"the sensory input region {s} (marked IN) {'to' if directed else 'and'} the motor output region {t} (marked OUT)? "
         "Answer with a whole number.")
    spec = {"family": FAMILY, "question_type": "min_edge_cut", "level": level,
            "data": _data(G, nodes, s, t, False, {}, {}), "question": q, "answer": int(k), "answer_type": "integer",
            "references": REFERENCES["min_edge_cut"],
            "uniqueness": {"ok": True, "why": f"edge connectivity is a single number; one minimum cut: {cut}"},
            "facts": {"one_minimum_cut": cut, "degrees": {s: out_deg, t: in_deg}}}
    kept = {n: v for n, v in traps.items() if v != k}
    if not kept:
        return None
    spec["wrong_answers"], spec["target_mistake"] = kept, next(iter(kept))
    return spec


# ---------------------------------------------------------------- question type 3: how many connections are critical
def _weighted_setup(rng, level):
    weighted, directed = level >= 2, level >= 4
    built = _graph(rng, level, weighted)
    if built is None:
        return None
    G, nodes, pos, by_mod = built
    s, t = _endpoints(rng, G, by_mod)
    if s is None:
        return None
    return G, nodes, pos, s, t, weighted, directed, ("weight" if weighted else None)


def _route_text(s, t, weighted):
    return (f"A signal travels from the sensory input region {s} (marked IN) to the motor output region {t} (marked OUT) "
            f"along the route with the {'smallest total delay' if weighted else 'fewest steps'}. ")


def _metric_text(weighted):
    return ("Each connection is labelled with its conduction delay in milliseconds. " if weighted
            else "Every connection counts as one step. ")


def _critical_count(rng, level):
    """L1 steps. L2 delays. L3 delays with tied fastest routes (so the answer is not the length of one route).
    L4 one-way delays, and ignoring the arrows gives a different count."""
    setup = _weighted_setup(rng, level)
    if setup is None:
        return None
    G, nodes, pos, s, t, weighted, directed, w = setup
    d0 = _dist(G, s, t, w)
    critical = sorted(e for e in G.edges if _dist(G, s, t, w, e) > d0)
    k = len(critical)
    paths = list(nx.all_shortest_paths(G, s, t, weight=w))
    if k < 2 or (level == 3 and len(paths) < 2):
        return None
    union = {frozenset(e) if not directed else e for p in paths for e in zip(p, p[1:])}
    hop_path = nx.shortest_path(G, s, t)
    traps = {"counted_one_fastest_route": len(paths[0]) - 1, "counted_all_fastest_route_links": len(union),
             "counted_fewest_step_route": len(hop_path) - 1}
    if directed:
        U = _undirected(G)
        du = _dist(U, s, t, w)
        traps = {"ignored_arrow_direction": sum(_dist(U, s, t, w, e) > du for e in U.edges), **traps}
        if traps["ignored_arrow_direction"] == k:
            return None
    label_t = _anchors(G, pos, list(G.edges)) if weighted else {}
    if label_t is None:
        return None
    q = (INTRO + LINES[directed] + _metric_text(weighted) + _route_text(s, t, weighted) +
         f"A connection is critical if removing it on its own would increase the {'smallest total delay' if weighted else 'fewest number of steps'} "
         f"from {s} to {t}, or leave no route at all. How many connections in the network are critical? Answer with a whole number.")
    spec = {"family": FAMILY, "question_type": "critical_count", "level": level,
            "data": _data(G, nodes, s, t, weighted, {}, label_t), "question": q, "answer": k, "answer_type": "integer",
            "references": REFERENCES["redundant_edge"],
            "uniqueness": {"ok": True, "why": f"every one of the {G.number_of_edges()} connections tested by removal; {k} raise the distance {d0:g}"},
            "facts": {"distance": d0, "critical": [list(e) for e in critical], "fastest_routes": paths}}
    kept = {n: v for n, v in traps.items() if v != k}
    if not kept:
        return None
    spec["wrong_answers"], spec["target_mistake"] = kept, next(iter(kept))
    return spec


# ---------------------------------------------------------------- question type 4: delay after two failures
def _delay_after_failure(rng, level):
    """Two connections X and Y fail together. X lies on every fastest route; Y lies on every fastest route that is
    left once X has failed, so the obvious detour is blocked too."""
    setup = _weighted_setup(rng, level)
    if setup is None:
        return None
    G, nodes, pos, s, t, weighted, directed, w = setup
    d0 = _dist(G, s, t, w)
    xs = [e for e in G.edges if _dist(G, s, t, w, e) > d0]
    if not xs:
        return None
    X = xs[rng.integers(len(xs))]
    d_x = _dist(G, s, t, w, X)
    if d_x == float("inf"):
        return None
    ys = [e for e in G.edges if e != X and _dist(G, s, t, w, [X, e]) > d_x and _dist(G, s, t, w, [X, e]) < float("inf")]
    if not ys:
        return None
    Y = ys[rng.integers(len(ys))]
    d_xy = _dist(G, s, t, w, [X, Y])
    traps = {"ignored_both_failures": d0, "ignored_failure_Y": d_x, "ignored_failure_X": _dist(G, s, t, w, Y)}
    if weighted:
        H = G.copy(); H.remove_edges_from([X, Y])
        hop = nx.shortest_path(H, s, t)
        traps["took_fewest_step_detour"] = sum(H[a][b]["weight"] for a, b in zip(hop, hop[1:]))
        traps["added_failed_delays"] = d0 + G[X[0]][X[1]]["weight"] + G[Y[0]][Y[1]]["weight"]
    if directed:
        H = G.copy(); H.remove_edges_from([X, Y])
        traps = {"ignored_arrow_direction": _dist(_undirected(H), s, t, w), **traps}
        if traps["ignored_arrow_direction"] == d_xy:
            return None
    cand = {"X": list(X), "Y": list(Y)}
    label_t = _anchors(G, pos, list(G.edges) if weighted else [X, Y], big=[X, Y])
    if label_t is None:
        return None
    unit = "smallest total delay in milliseconds" if weighted else "fewest number of steps"
    q = (INTRO + LINES[directed] + _metric_text(weighted) + _route_text(s, t, weighted) +
         f"The two connections marked X and Y both fail at the same time and can no longer carry any signal. "
         f"After both failures, what is the {unit} from {s} to {t}? Answer with a whole number.")
    spec = {"family": FAMILY, "question_type": "delay_after_failure", "level": level,
            "data": {**_data(G, nodes, s, t, weighted, cand, label_t), "candidate_style": "failure"},
            "question": q, "answer": int(d_xy), "answer_type": "integer", "references": REFERENCES["redundant_edge"],
            "uniqueness": {"ok": True, "why": f"a single shortest-path distance: {d0:g} intact, {d_x:g} without X, {d_xy:g} without X and Y"},
            "facts": {"distance": d0, "without_X": d_x, "without_X_and_Y": d_xy}}
    kept = {n: int(v) for n, v in traps.items() if v != d_xy and v != float("inf")}
    if not kept:
        return None
    spec["wrong_answers"], spec["target_mistake"] = kept, next(iter(kept))
    return spec


# ---------------------------------------------------------------- level 5: circuit rules
RULE_NAMES = ("inhibitory", "lesion", "region_delay")
RULES_TEXT = ("Connections ending in an arrowhead are excitatory and carry the signal in the direction of the arrowhead. "
              "Connections ending in a flat bar are inhibitory and cannot carry the signal. "
              "The grey hatched region marked LESION is damaged: no signal can enter or pass through it. "
              "Each connection is labelled with its conduction delay in milliseconds. Every region the signal passes "
              "through between IN and OUT also adds its own processing delay, shown inside its circle. ")


def _effective(G, t, rules, ignore=(), drop=()):
    """The network the signal can actually use at level 5. Each arc costs its line delay plus the processing delay of
    the region it enters (OUT adds none). `ignore` switches a rule off, giving the answer of a reader who misses that
    rule ("direction" = arrows read as two-way). `drop` removes connections (failures and removal tests)."""
    E = nx.DiGraph()
    E.add_nodes_from(G)
    inh, drop = {tuple(e) for e in rules["inhibitory"]}, {tuple(e) for e in drop}
    for u, v, w in G.edges(data="weight"):
        if (u, v) in drop or ((u, v) in inh and "inhibitory" not in ignore):
            continue
        for a, b in ([(u, v), (v, u)] if "direction" in ignore else [(u, v)]):
            if rules["lesion"] in (a, b) and "lesion" not in ignore:
                continue
            cost = w + (0 if ("region_delay" in ignore or b == t) else rules["node_delay"].get(b, 0))
            if not E.has_edge(a, b) or cost < E[a][b]["weight"]:
                E.add_edge(a, b, weight=cost)
    return E


def _edist(E, s, t):
    try:
        return nx.shortest_path_length(E, s, t, weight="weight")
    except nx.NetworkXNoPath:
        return float("inf")


def _make_rules(rng, G, s, t):
    """Place the rules where they matter: the lesion sits on the route a line-only reader would take, and one connection
    on the next-best route is inhibitory, plus a few inhibitory connections elsewhere."""
    try:
        naive = nx.shortest_path(G, s, t, weight="weight")
    except nx.NetworkXNoPath:
        return None
    if len(naive) < 3:
        return None
    lesion = str(naive[1 + rng.integers(len(naive) - 2)])
    H = G.copy(); H.remove_node(lesion)
    try:
        second = nx.shortest_path(H, s, t, weight="weight")
    except nx.NetworkXNoPath:
        return None
    on_second = [e for e in zip(second, second[1:])]
    inh = {on_second[rng.integers(len(on_second))]}
    others = [e for e in G.edges if e not in inh and lesion not in e]
    for i in rng.choice(len(others), min(len(others), int(rng.integers(1, 3))), replace=False):
        inh.add(others[i])
    delay = {n: (0 if n in (s, t) else int(rng.integers(1, 5))) for n in G}
    return {"inhibitory": sorted([list(e) for e in inh]), "lesion": lesion, "node_delay": delay}


def _rules_task(rng, qtype):
    """Draw one level-5 graph, then try every sensory -> motor pair as IN/OUT until one gives a valid task."""
    built = _graph(rng, 5, True)
    if built is None:
        return None
    G, nodes, pos, by_mod = built
    pairs = [(a, b) for a in by_mod["Sensory"] for b in by_mod["Motor"]
             if not G.has_edge(a, b) and not G.has_edge(b, a) and nx.has_path(G, a, b)]
    for i in rng.permutation(len(pairs)):
        spec = _rules_for_pair(rng, qtype, G, nodes, pos, *pairs[i])
        if spec is not None:
            return spec
    return None


def _rules_for_pair(rng, qtype, G, nodes, pos, s, t):
    rules = _make_rules(rng, G, s, t)
    if rules is None:
        return None
    E = _effective(G, t, rules)
    d0 = _edist(E, s, t)
    if d0 == float("inf"):
        return None
    misses = {"ignored_inhibitory_bars": ("inhibitory",), "routed_through_lesion": ("lesion",),
              "ignored_region_delays": ("region_delay",), "ignored_arrow_direction": ("direction",)}
    usable = [e for e in G.edges if tuple(e) not in {tuple(x) for x in rules["inhibitory"]} and rules["lesion"] not in e]
    if qtype == "critical_count":
        critical = sorted(e for e in usable if _edist(_effective(G, t, rules, drop=[e]), s, t) > d0)
        answer = len(critical)
        if answer < 2:
            return None
        traps = {}
        for name, ign in misses.items():
            Ei = _effective(G, t, rules, ign)
            di = _edist(Ei, s, t)
            traps[name] = sum(_edist(_effective(G, t, rules, ign, [e]), s, t) > di for e in G.edges)
        traps["counted_one_fastest_route"] = len(nx.shortest_path(E, s, t, weight="weight")) - 1
        cand, facts = {}, {"distance": d0, "critical": [list(e) for e in critical]}
        ask = ("A connection is critical if removing it on its own would increase the smallest total delay from "
               f"{s} to {t}, or leave no route at all. How many connections in the network are critical? Answer with a whole number.")
    else:
        xs = [e for e in usable if _edist(_effective(G, t, rules, drop=[e]), s, t) > d0]
        if not xs:
            return None
        X = xs[rng.integers(len(xs))]
        d_x = _edist(_effective(G, t, rules, drop=[X]), s, t)
        ys = [e for e in usable if e != X and d_x < _edist(_effective(G, t, rules, drop=[X, e]), s, t) < float("inf")]
        if d_x == float("inf") or not ys:
            return None
        Y = ys[rng.integers(len(ys))]
        answer = _edist(_effective(G, t, rules, drop=[X, Y]), s, t)
        traps = {name: _edist(_effective(G, t, rules, ign, [X, Y]), s, t) for name, ign in misses.items()}
        traps.update({"ignored_both_failures": d0, "ignored_failure_Y": d_x,
                      "ignored_failure_X": _edist(_effective(G, t, rules, drop=[Y]), s, t)})
        cand, facts = {"X": list(X), "Y": list(Y)}, {"distance": d0, "without_X": d_x, "without_X_and_Y": answer}
        ask = ("The two connections marked X and Y both fail at the same time and can no longer carry any signal. "
               f"After both failures, what is the smallest total delay in milliseconds from {s} to {t}? Answer with a whole number.")
    rule_traps = [n for n in ("ignored_inhibitory_bars", "routed_through_lesion", "ignored_region_delays") if traps[n] != answer]
    if len(rule_traps) < 2:
        return None                                   # at least two of the three rules must change the answer
    label_t = _anchors(G, pos, list(G.edges), big=cand.values())
    if label_t is None:
        return None
    q = (INTRO + RULES_TEXT + f"A signal travels from the sensory input region {s} (marked IN) to the motor output "
         f"region {t} (marked OUT) along the route with the smallest total delay. " + ask)
    data = {**_data(G, nodes, s, t, True, cand, label_t), "rules": rules}
    if cand:
        data["candidate_style"] = "failure"
    spec = {"family": FAMILY, "question_type": qtype, "level": 5, "data": data, "question": q,
            "answer": int(answer), "answer_type": "integer", "references": REFERENCES["redundant_edge"] + [
                "Inhibitory connections drawn with a flat bar end, excitatory with an arrowhead: standard circuit-diagram notation"],
            "uniqueness": {"ok": True, "why": f"single shortest-path computation on the network that obeys all rules (intact delay {d0:g})"},
            "facts": {**facts, "rules_that_change_answer": rule_traps}}
    kept = {n: int(v) for n, v in traps.items() if v != answer and v != float("inf")}
    if not kept:
        return None
    spec["wrong_answers"], spec["target_mistake"] = kept, rule_traps[0]
    return spec


# ---------------------------------------------------------------- drawing
def _tip_r(d, v):
    return NODE_R * (1.55 if v in (d["input"], d["output"]) else 1.12)


def render(spec, png_path):
    d = spec["data"]
    pos = {nd["name"]: np.array([nd["x"], nd["y"]]) for nd in d["nodes"]}
    colour = {nd["name"]: MODULES[nd["module"]][0] for nd in d["nodes"]}
    edge_col = "#%02x%02x%02x" % EDGE_RGB
    fig = plt.figure(figsize=(10.2, 10.7))
    ax = fig.add_axes([0.02, 0.02, 0.96, 0.84])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_aspect("equal"); ax.axis("off")
    cand = {_ekey(*e, d["directed"]): L for L, e in d["candidates"].items()}
    rules = d.get("rules")
    inh = {tuple(e) for e in rules["inhibitory"]} if rules else set()
    for u, v, w, bend in d["edges"]:
        pts = curve(pos, u, v, bend, 80 if bend else None)
        if (u, v) in inh:     # inhibitory: the line stops at a flat bar instead of entering the region
            pts = pts[np.linalg.norm(pts - pos[v], axis=1) > _tip_r(d, v)] if bend else np.array(
                [pos[u], arrow_head(pos, u, v, bend, _tip_r(d, v))[0][0]])
        ax.add_line(Line2D(pts[:, 0], pts[:, 1], color=edge_col, lw=1.7, zorder=1))
        if d["directed"]:
            tri, _, nv = arrow_head(pos, u, v, bend, _tip_r(d, v))
            if (u, v) in inh:
                bar = np.array([tri[0] + nv * HEAD_W * 1.25, tri[0] - nv * HEAD_W * 1.25])
                ax.add_line(Line2D(bar[:, 0], bar[:, 1], color=edge_col, lw=3.2, solid_capstyle="butt", zorder=2))
            else:
                ax.add_patch(Polygon(tri, closed=True, fc=edge_col, ec=edge_col, lw=0.5, zorder=2))
        k = _ekey(u, v, d["directed"])
        if k in d["label_t"]:
            p = _bezier(pos[u], pos[v], bend, d["label_t"][k])[0]
            if k in cand:
                txt = f"{cand[k]}: {w} ms" if d["weighted"] else cand[k]
                fail = d.get("candidate_style") == "failure"
                ax.text(*p, txt, fontsize=9, fontweight="bold", ha="center", va="center", zorder=4,
                        bbox=dict(boxstyle="round,pad=0.25", fc="#f7b6b0" if fail else "#ffe08a", ec="black", lw=0.9))
            else:
                ax.text(*p, str(w), fontsize=8.5, ha="center", va="center", zorder=4,
                        bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="#9aa0a6", lw=0.6))
    centre = np.array([0.5, 0.5])
    for name, p in pos.items():
        lesioned = rules and name == rules["lesion"]
        ax.add_patch(Circle(p, NODE_R, fc="#d5d5d5" if lesioned else colour[name], ec="#555" if lesioned else "white",
                            lw=1.5, hatch="////" if lesioned else None, zorder=3))
        delay = rules["node_delay"].get(name, 0) if rules else 0
        label = f"{name}\n{delay} ms" if delay else name
        ax.text(*p, label, fontsize=8 if len(name) < 5 else 7.2, color="#222" if lesioned else "white",
                fontweight="bold", ha="center", va="center", zorder=5, linespacing=1.0)
    if rules:
        p = pos[rules["lesion"]]
        out = (p - np.array([0.5, 0.5])) / (np.linalg.norm(p - np.array([0.5, 0.5])) or 1)
        ax.text(*(p + out * (NODE_R + 0.045)), "LESION", fontsize=8.5, fontweight="bold", color="#555", ha="center", va="center", zorder=5)
    for name, tag in ((d["input"], "IN"), (d["output"], "OUT")):
        p = pos[name]
        ax.add_patch(Circle(p, NODE_R * 1.28, fill=False, ec="black", lw=2.2, zorder=3))
        out = (p - centre) / (np.linalg.norm(p - centre) or 1)
        ax.text(*(p + out * (NODE_R + 0.04)), tag, fontsize=9.5, fontweight="bold", ha="center", va="center", zorder=5)
    n_mod = len(d["modules"])
    fig.text(0.03, 0.965, f"Synthetic brain connectivity network ({len(pos)} regions, {n_mod} modules)", fontsize=12.5, va="center")
    kind = "One-way connections (arrowheads show direction)" if d["directed"] else "Lines: bidirectional connections"
    if rules:
        kind = "Numbers on lines: conduction delay (ms). Number inside a region: its processing delay (ms)"
    sub = kind + ("." if rules else ". Numbers: conduction delay (ms)." if d["weighted"] else (". " if d["directed"] else " (all equivalent)."))
    fig.text(0.03, 0.935, sub, fontsize=9.5, va="center", color="#333")
    fig.legend(handles=[Patch(fc=MODULES[m][0], label=m) for m in d["modules"]], loc="center left",
               bbox_to_anchor=(0.025, 0.895), ncol=n_mod, frameon=False, fontsize=9, handlelength=1.2, columnspacing=1.4)
    if rules:
        hs = [Line2D([], [], color=edge_col, lw=1.7, marker=">", markersize=7, markevery=[-1], label="excitatory (carries signal)"),
              Line2D([], [], color=edge_col, lw=1.7, marker="|", markersize=11, markeredgewidth=3, markevery=[-1], label="inhibitory (cannot carry signal)"),
              Patch(fc="#d5d5d5", ec="#555", hatch="////", label="lesioned region (no signal passes)")]
        fig.legend(handles=hs, loc="center left", bbox_to_anchor=(0.025, 0.862), ncol=3, frameon=False, fontsize=9,
                   handlelength=2.2, columnspacing=1.6)
    fig.set_dpi(common.DPI); fig.canvas.draw()
    h_px = fig.canvas.get_width_height()[1]
    o = ax.transData.transform((0, 0)); x1 = ax.transData.transform((1, 1))
    layout = common.save_figure(fig, png_path, list(pos) + ["IN", "OUT"] + list(d["candidates"]) + (["LESION"] if rules else []))
    layout["data_to_px"] = [float(o[0]), float(h_px - o[1]), float(x1[0] - o[0]), float(o[1] - x1[1])]
    return layout


# ---------------------------------------------------------------- second solver (no NetworkX)
def _adj(d):
    adj = {nd["name"]: {} for nd in d["nodes"]}
    for u, v, w, _ in d["edges"]:
        adj[u][v] = w if d["weighted"] else 1
        if not d["directed"]:
            adj[v][u] = adj[u][v]
    return adj


def _dijkstra(adj, s, t, drop=None, drops=()):
    """drop: one (u, v, both_ways) to skip; drops: a list of them."""
    skip = set()
    for u0, v0, both in ([drop] if drop else []) + list(drops):
        skip.add((u0, v0))
        if both:
            skip.add((v0, u0))
    dist, heap = {s: 0}, [(0, s)]
    while heap:
        du, u = heapq.heappop(heap)
        if u == t:
            return du
        if du > dist[u]:
            continue
        for v, w in adj[u].items():
            if (u, v) in skip:
                continue
            if du + w < dist.get(v, float("inf")):
                dist[v] = du + w; heapq.heappush(heap, (du + w, v))
    return float("inf")


def _max_flow_unit(adj, s, t):
    """Edmonds-Karp, capacity 1 on every arc (both arcs of an undirected edge) = number of edge-disjoint paths."""
    cap = {}
    for u in adj:
        for v in adj[u]:
            cap[(u, v)] = cap.get((u, v), 0) + 1
            cap.setdefault((v, u), 0)
    nbr = {u: set() for u in adj}
    for u, v in cap:
        nbr[u].add(v)
    flow = 0
    while True:
        prev, q = {s: None}, deque([s])
        while q and t not in prev:
            u = q.popleft()
            for v in sorted(nbr[u]):
                if v not in prev and cap[(u, v)] > 0:
                    prev[v] = u; q.append(v)
        if t not in prev:
            return flow
        v = t
        while prev[v] is not None:
            u = prev[v]; cap[(u, v)] -= 1; cap[(v, u)] += 1; v = u
        flow += 1


def _adj_rules(d, drops=()):
    """Level 5, written separately from _effective: skip inhibitory arcs, arcs touching the lesion, and failed arcs;
    each arc costs its line delay plus the processing delay of the region it enters (OUT adds none)."""
    r, t = d["rules"], d["output"]
    banned = {tuple(e) for e in r["inhibitory"]} | {tuple(e) for e in drops}
    adj = {nd["name"]: {} for nd in d["nodes"]}
    for u, v, w, _ in d["edges"]:
        if (u, v) in banned or r["lesion"] in (u, v):
            continue
        adj[u][v] = w + (0 if v == t else r["node_delay"][v])
    return adj


def resolve(d, qtype):
    if d.get("rules"):
        s, t = d["input"], d["output"]
        if qtype == "delay_after_failure":
            return _dijkstra(_adj_rules(d, [d["candidates"]["X"], d["candidates"]["Y"]]), s, t)
        d0 = _dijkstra(_adj_rules(d), s, t)
        return sum(_dijkstra(_adj_rules(d, [(u, v)]), s, t) > d0 for u, v, _, _ in d["edges"])
    adj = _adj(d)
    if qtype == "min_edge_cut":
        return _max_flow_unit(adj, d["input"], d["output"])
    s, t, both = d["input"], d["output"], not d["directed"]
    d0 = _dijkstra(adj, s, t)
    if qtype == "critical_count":
        return sum(_dijkstra(adj, s, t, drop=(u, v, both)) > d0 for u, v, _, _ in d["edges"])
    if qtype == "delay_after_failure":
        return _dijkstra(adj, s, t, drops=[(*d["candidates"]["X"], both), (*d["candidates"]["Y"], both)])
    keep = [L for L, (u, v) in d["candidates"].items()
            if _dijkstra(adj, d["input"], d["output"], drop=(u, v, not d["directed"])) == d0]
    return keep[0] if len(keep) == 1 else f"AMBIGUOUS{keep}"


# ---------------------------------------------------------------- picture check: drawn lines == stored adjacency
def render_check(spec, layout, png_path):
    """Every stored connection is drawn, no line appears between unconnected regions, and (one-way networks) every
    arrowhead is drawn at the target end of its connection and not at the source end."""
    d = spec["data"]
    img = np.asarray(Image.open(png_path).convert("RGB")).astype(int)
    H, W = img.shape[:2]
    ink = (np.abs(img - np.array(EDGE_RGB)).max(axis=2) < 60) & (img.max(axis=2) - img.min(axis=2) < 40)
    ox, oy, sx, sy = layout["data_to_px"]
    to_px = lambda p: np.array([ox + p[0] * sx, oy + p[1] * sy]) if np.ndim(p) == 1 else np.c_[ox + p[:, 0] * sx, oy + p[:, 1] * sy]
    pos = {nd["name"]: np.array([nd["x"], nd["y"]]) for nd in d["nodes"]}
    node = {n: to_px(p) for n, p in pos.items()}
    boxes = [(t["x0"] - 12, t["y0"] - 12, t["x1"] + 12, t["y1"] + 12) for t in layout["texts"]]   # incl. the label box border
    polys = {(u, v): to_px(curve(pos, u, v, b, 60)) for u, v, _, b in d["edges"]}
    heads = {(u, v): to_px(arrow_head(pos, u, v, b, _tip_r(d, v))[0]) for u, v, _, b in d["edges"]} if d["directed"] else {}

    ring = {d["input"]: 1.45, d["output"]: 1.45}

    def free(p, own=None):
        if any(np.linalg.norm(p - q) < NODE_R * ring.get(n, 1.12) * sx + 4 for n, q in node.items()):
            return False
        if any(b[0] <= p[0] <= b[2] and b[1] <= p[1] <= b[3] for b in boxes):
            return False
        others = [pts for e, pts in polys.items() if e != own]
        return (all(_poly_dist(p, pts) > 9 for pts in others)
                and all(_poly_dist(p, np.r_[h, h[:1]]) > 9 for e, h in heads.items() if e != own))

    def hit(p, r):
        x, y = int(round(p[0])), int(round(p[1]))
        return bool(ink[max(0, y - r):min(H, y + r + 1), max(0, x - r):min(W, x + r + 1)].any())

    missing, probes_e = [], 0
    for e, pts in polys.items():
        sample = [pts[i] for i in range(6, 55, 4)]
        sample = [p for p in sample if free(p, own=e)]
        probes_e += len(sample)
        if len(sample) < 2 or sum(hit(p, 2) for p in sample) < 0.8 * len(sample):
            missing.append("{}-{}".format(*e))
    linked = {frozenset(e) for e in polys}
    phantom, probes_n = [], 0
    for u, v in combinations(node, 2):
        if frozenset((u, v)) in linked:
            continue
        for f in (0.33, 0.5, 0.67):
            p = node[u] + f * (node[v] - node[u])
            if free(p):
                probes_n += 1
                if hit(p, 1):
                    phantom.append(f"{u}-{v}")
                    break
    bad_heads = []
    inh = {tuple(e) for e in d["rules"]["inhibitory"]} if d.get("rules") else set()
    for (u, v), tri in heads.items():
        tip, base_mid = tri[0], (tri[1] + tri[2]) / 2
        side = (tri[1] - tri[2]) / np.linalg.norm(tri[1] - tri[2])
        probe = tip + 0.6 * (base_mid - tip)
        filled = hit(probe + side * 4, 1) and hit(probe - side * 4, 1)
        if (u, v) in inh:     # inhibitory: a flat bar across the tip, and no filled arrowhead behind it
            half = np.linalg.norm(tri[1] - tri[2]) / 2
            bar_ok = hit(tip + side * 0.9 * half, 1) and hit(tip - side * 0.9 * half, 1)
            wide = 0.6 * half                       # inside a real arrowhead, well clear of the line's own width
            looks_filled = hit(probe + side * wide, 0) and hit(probe - side * wide, 0)
            if not bar_ok or looks_filled:
                bad_heads.append(f"{u}-|{v} bar {'missing' if not bar_ok else 'drawn as an arrowhead'}")
        elif not filled:
            bad_heads.append(f"{u}->{v} head missing")
        if any(e[:2] == [v, u] for e in d["edges"]):
            continue                                       # two-way pair: the other arrow really does end at u
        rev = to_px(arrow_head(pos, v, u, 0.0, _tip_r(d, u))[0])   # where a wrongly drawn head would sit
        rp = rev[0] + 0.6 * ((rev[1] + rev[2]) / 2 - rev[0])
        rside = (rev[1] - rev[2]) / np.linalg.norm(rev[1] - rev[2])
        if free(rp, own=(u, v)) and hit(rp + rside * 5, 1) and hit(rp - rside * 5, 1):
            bad_heads.append(f"{u}->{v} has a head at the source end")
    detail = (f"{len(polys)} stored connections, {probes_e} probes on drawn lines; missing: {missing[:4] or 'none'}; "
              f"{probes_n} probes between unconnected regions; phantom lines: {phantom[:4] or 'none'}")
    if d["directed"]:
        detail += (f"; {len(heads)} line ends checked ({len(inh)} inhibitory bars, {len(heads) - len(inh)} arrowheads) at "
                   f"target and source; wrong: {bad_heads[:4] or 'none'}")
    return {"name": "edges_match_adjacency", "pass": not missing and not phantom and not bad_heads, "detail": detail}
