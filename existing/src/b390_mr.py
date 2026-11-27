"""390 Forest Ave mechanical: where every duct, grille and cap goes.

Registers, return grilles, jump ducts and wall caps are placed by a search with clearances. Branches, return ducts, exhaust
ducts and vents are routed on a 3 in. grid through the joist space they run in, square to the walls, by least cost: short,
few bends, through the room served or the hall rather than another room, not across the trunk, the chase, a stair opening,
the panel's dedicated space or another flat, and not on top of a duct already placed. Anything that cannot meet a rule is
listed in layout()["problems"] and printed by the sheet builder.

Joist spaces: 3 = lower flat ceiling, 4 = middle flat ceiling, 5 = attic floor (upper flat main-floor ceiling AND attic floor
registers: one space, one trunk)."""
import heapq
import math
import os
import sys
from functools import lru_cache

import numpy as np
import shapely
import shapely.affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import nearest_points, unary_union

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build390 as b  # noqa: E402
import b390_eq as q  # noqa: E402
import b390_mq as mq  # noqa: E402
import b390_e as e  # noqa: E402

G = 0.25                                       # grid, ft
SPACE = {3: 3, 4: 4, 5: 5, 6: 5}
LEVELS = {3: (3,), 4: (4,), 5: (5, 6)}
FLAT = {3: "A", 4: "B", 5: "C", 6: "C"}
TRUNK_W = 14 / 12                              # 14 x 8 in. trunk, fits one joist bay at 16 in. o.c.
TRUNK_SIZE = "14 x 8"

# Supply trunks (plan ft). From the furnace's supply plenum, in the ceiling framing.
TRUNK = {3: [[(19.3, 3.3), (19.3, 11.95)], [(15.3, 11.95), (22.6, 11.95)], [(15.3, 11.95), (15.3, 16.1), (6.5, 16.1)]],
         4: [[(13.7, 7.35), (12.4, 7.35), (12.4, 13.0)], [(13.7, 7.35), (13.7, 5.55), (22.8, 5.55), (22.8, 15.6)]],
         5: [[(16.45, 11.0), (16.45, 17.0), (4.5, 17.0)], [(16.45, 17.0), (20.6, 17.0)]]}
# Return: grille in this room, duct to the drop beside the furnace (into its return platform).
RET = {3: dict(room="107", drop=(20.95, 3.33), name="R-A"), 4: dict(room="207", drop=(13.25, 9.1), name="R-B"),
       5: dict(room="306", drop=(18.5, 12.4), name="R-C1")}
RET2 = dict(fl=6, room="405", name="R-C2", cfm=160)        # attic: floor grille at the top of the stair, boot on the R-C1 duct below
# Upper flat: R-C1 (main-floor hall ceiling) and R-C2 (attic stair-hall floor) share one return box in the floor framing between them.
RET_AT = {5: ((18.7, 14.85), "x"), 6: ((18.7, 15.65), "x")}
VENTLESS = {4: "Heat-pump dryer, ventless: no outside wall the vent may use is within 35 ft equivalent (north windows, west neighbour, east stair, trunk)."}
# Vertical shafts: the old chimney becomes the chase; on the middle level the chimney is gone and the pipes rise behind the water heater.
CHASE = {3: (17.4, 6.4, 18.0, 9.38), 4: (16.45, 6.15, 18.7, 8.6), 5: (15.65, 6.2, 17.85, 8.6), 6: (15.7, 5.96, 17.75, 8.4)}
TSTAT = {3: (10.5, 13.12, (0, 1)), 4: (11.3, 13.55, (0, -1)), 5: (23.75, 18.6, (-1, 0))}
# Exhaust caps: which outside walls may take one, with a cost (ft of extra duct it is worth to avoid). None = never.
# West: the neighbour's house is a few feet away (3 ft to the property line). East: the wood stair and the property line.
# Lower flat north end: below grade. Lower flat south: the rear deck and the condensers under it.
CAPS = {3: dict(N=None, S=8.0, E=0.0, W=None), 4: dict(N=0.0, S=0.0, E=6.0, W=None), 5: dict(N=0.0, S=0.0, E=6.0, W=None)}
REG = {"ceiling": (1.1, 0.6), "floor": (0.9, 0.5)}         # drawn register size (ft)
RG_SIZE = {"14x20": (20 / 12, 14 / 12), "16x20": (20 / 12, 16 / 12), "20x20": (20 / 12, 20 / 12), "20x25": (25 / 12, 20 / 12)}

TURN = 8.0                                     # cost of a bend, in grid cells
NORTH = np.array([1.0, 0.0])


def side(n):
    """Outward normal (building frame) to N / S / E / W."""
    x, y = n
    if abs(x) >= abs(y): return "N" if x > 0 else "S"
    return "W" if y > 0 else "E"


# ---------------------------------------------------------------------------------------------- grids
class Grid:
    def __init__(self, space):
        self.space = space
        P = q.outline(space) if space != 5 else unary_union([q.outline(5), q.outline(6)])
        x0, y0, x1, y1 = P.bounds; x0 -= 1; y0 -= 1; x1 += 1; y1 += 1
        self.x0, self.y0 = x0, y0; self.nx, self.ny = int((x1 - x0) / G) + 1, int((y1 - y0) / G) + 1
        xs = x0 + (np.arange(self.nx) + .5) * G; ys = y0 + (np.arange(self.ny) + .5) * G
        self.X, self.Y = np.meshgrid(xs, ys, indexing="ij")
        O = q.outline(space)
        self.out = O
        self.inside = self.mask(O.buffer(-0.3))                 # passable for ducts
        self.capzone = self.mask(O) & ~self.mask(O.buffer(-0.55))
        self.wall = {fl: self.mask(e.solid(fl)) for fl in LEVELS[space]}
        self.rooms = {fl: self.roommap(fl) for fl in LEVELS[space]}
        if space == 5: self.attic = self.mask(q.outline(6).buffer(-0.3))
        blk = np.zeros_like(self.inside)
        for fl in LEVELS[space]:
            c = CHASE[fl]; blk |= self.mask(box(*c).buffer(0.05))
            L = b.LV[fl]
            for f in L["fx"]:
                if f[0] == "panel":                             # NEC 110.26(E): panel width x depth, floor to structure, no ducts
                    x0_, y0_, x1_, y1_ = f[1:5]; sd = f[5] if len(f) > 5 else -1
                    r = (min(x0_, x0_ + sd * .45), min(y0_, y1_) - .1, max(x0_, x0_ + sd * .45), max(y0_, y1_) + .1) if x0_ == x1_ else \
                        (min(x0_, x1_) - .1, min(y0_, y0_ + sd * .45), max(x0_, x1_) + .1, max(y0_, y0_ + sd * .45))
                    blk |= self.mask(box(*r))
        if space == 4:                                          # the upper flat's stair hall: no middle-flat duct over it
            r = next(r for r in b.LV[4]["rooms"] if r["no"] == "213"); blk |= self.mask(unary_union([box(*x) for x in r["rects"]]).buffer(0.3))
        if space == 5:                                          # stair openings through the attic floor
            for st in b.LV[6]["stairs"]: blk |= self.mask(box(*st[:4]))
            for st in b.LV[5]["stairs"]:
                if st[3] > 19.5: blk |= self.mask(box(*st[:4]))
        self.blocked = blk
        self.occ = np.zeros(self.inside.shape)                  # penalty for running on or beside ducts already placed
        self.band = np.zeros_like(self.inside)                  # trunk
        self.trunk_lines = []

    def mask(self, geom):
        return shapely.contains_xy(geom, self.X, self.Y)

    def roommap(self, fl):
        m = -np.ones(self.X.shape, int)
        for i, r in enumerate(b.LV[fl]["rooms"]):
            for qq in r["rects"]:
                m[self.mask(box(*qq))] = i
        return m

    def cell(self, p):
        return (min(self.nx - 1, max(0, int((p[0] - self.x0) / G))), min(self.ny - 1, max(0, int((p[1] - self.y0) / G))))

    def pt(self, c):
        return (self.x0 + (c[0] + .5) * G, self.y0 + (c[1] + .5) * G)

    def set_trunk(self, lines):
        self.trunk_lines = lines
        sh = unary_union([LineString(t).buffer(TRUNK_W / 2, cap_style="flat", join_style="mitre") for t in lines])
        self.trunk_shape = sh
        self.band = self.mask(sh.buffer(0.05))
        self.centre = np.zeros_like(self.band)
        for t in lines:
            for a, c in zip(t[:-1], t[1:]):
                n = max(2, int(math.dist(a, c) / (G / 2)))
                for s in np.linspace(0, 1, n):
                    i, j = self.cell((a[0] + (c[0] - a[0]) * s, a[1] + (c[1] - a[1]) * s)); self.centre[i, j] = True

    def occupy(self, path, r_on=0.3, r_near=0.65, on=30.0, near=3.0):
        if len(path) < 2: return
        ls = LineString(path)
        self.occ[self.mask(ls.buffer(r_near))] += near
        self.occ[self.mask(ls.buffer(r_on))] += on


@lru_cache(None)
def grid(space):
    g = Grid(space); g.set_trunk(TRUNK[space]); return g


def cost_map(g, fl, own, kind):
    """Per-cell cost of a duct of this kind on level fl's plan, serving rooms 'own' (set of room indices)."""
    L = b.LV[fl]; rm = g.rooms[fl]; k = FLAT[fl]
    circ = {i for i, r in enumerate(L["rooms"]) if r["kind"] in ("hall", "living", "kitchen") and mq.flat_of(fl, r) == k}
    other = {i for i, r in enumerate(L["rooms"]) if mq.flat_of(fl, r) != k}
    c = np.full(rm.shape, 4.0)                                  # another room of the flat, or no room (a wall)
    for i in circ: c[rm == i] = 1.6
    for i in own: c[rm == i] = 1.0
    for i in other: c[rm == i] = np.inf
    c = c + np.where(g.wall[fl], 2.0, 0.0)
    for f in L["fx"]:
        if f[0] == "tub": c[g.mask(box(*f[1:5]))] += 1.0
    c = c + g.occ
    ok = g.inside.copy()
    if kind in ("supply", "return") and g.space == 5: ok &= g.attic
    c[~ok] = np.inf
    c[g.blocked] = np.inf
    if kind == "supply": c[g.band & ~g.centre] += 6.0
    elif kind == "vent": c[g.band] += 10.0                       # small pipes leaving an appliance that sits under the plenum
    else: c[g.band] += 80.0
    return c


def dijkstra(g, cost, sources, goal):
    """Least-cost 4-way path with bend penalty. sources: {cell: start cost}; goal: set of cells (or a function cell -> bool).
    Returns the list of cells from a source to the goal, or None."""
    nx, ny = g.nx, g.ny; INF = float("inf")
    best = {}; hp = []
    for s, c0 in sources.items():
        for d in range(4):
            st = (s[0], s[1], d); best[st] = c0; heapq.heappush(hp, (c0, s[0], s[1], d))
    prev = {}; D = ((1, 0), (0, 1), (-1, 0), (0, -1)); isgoal = goal if callable(goal) else (lambda c: c in goal)
    while hp:
        cst, i, j, d = heapq.heappop(hp)
        if cst > best.get((i, j, d), INF): continue
        if isgoal((i, j)):
            out = [(i, j)]; st = (i, j, d)
            while st in prev: st = prev[st]; out.append((st[0], st[1]))
            out.reverse(); return out
        for nd, (di, dj) in enumerate(D):
            if (nd + 2) % 4 == d: continue
            a, bb = i + di, j + dj
            if not (0 <= a < nx and 0 <= bb < ny): continue
            w = cost[a, bb]
            if w == INF and not isgoal((a, bb)): continue
            nc = cst + (w if w != INF else 1.0) + (TURN if nd != d else 0.0)
            if nc < best.get((a, bb, nd), INF):
                best[(a, bb, nd)] = nc; prev[(a, bb, nd)] = (i, j, d); heapq.heappush(hp, (nc, a, bb, nd))
    return None


def corners(g, cells, a=None, z=None):
    """Grid cells to a polyline of corner points; first/last points replaced by a and z (kept square)."""
    if not cells: return []
    pts = [g.pt(c) for c in cells]
    out = [pts[0]]
    for p0, p1, p2 in zip(pts[:-2], pts[1:-1], pts[2:]):
        if (p1[0] - p0[0]) * (p2[1] - p1[1]) - (p1[1] - p0[1]) * (p2[0] - p1[0]) != 0: out.append(p1)
    out.append(pts[-1])
    if a is not None: out = snap_end(out, a, 0)
    if z is not None: out = snap_end(out, z, -1)
    clean = [out[0]]
    for p in out[1:]:
        if math.dist(p, clean[-1]) > 1e-6: clean.append(p)
    return clean


def snap_end(pts, p, i):
    """Move one end of a square polyline exactly to p, keeping the end segment square."""
    pts = list(pts)
    if len(pts) == 1: return [p, p]
    if i == 0:
        a, c = pts[0], pts[1]
        if abs(a[0] - c[0]) < 1e-6: pts[1] = (p[0], c[1])
        else: pts[1] = (c[0], p[1])
        pts[0] = p
        if len(pts) > 2:                                         # keep the next segment square
            n = pts[2]; m = pts[1]
            if abs(n[0] - c[0]) < 1e-6 and abs(m[0] - n[0]) > 1e-6: pts.insert(2, (m[0], n[1]))
            elif abs(n[1] - c[1]) < 1e-6 and abs(m[1] - n[1]) > 1e-6: pts.insert(2, (n[0], m[1]))
        return pts
    return list(reversed(snap_end(list(reversed(pts)), p, 0)))


# ---------------------------------------------------------------------------------------------- placement helpers
def room_of(fl, no):
    return next(r for r in b.LV[fl]["rooms"] if r["no"] == no)


def room_shape(r, m=0.0):
    return unary_union([box(*qq) for qq in r["rects"]]).buffer(-m, join_style="mitre") if m else unary_union([box(*qq) for qq in r["rects"]])


@lru_cache(None)
def swings(fl):
    L = b.LV[fl]; out = [b._swing_geom(d).buffer(0.02) for d in L["doors"]]
    for d in L["doors"]:                                          # the whole swept quarter circle
        axis, w0, a0, a1, hinge, sw = d[1:7]; wd = a1 - a0; hp = a0 if hinge == "lo" else a1
        c = (hp, w0) if axis == "h" else (w0, hp)
        pts = [c]
        far = a1 if hinge == "lo" else a0
        for t in np.linspace(0, math.pi / 2, 12):
            u = hp + (far - hp) * math.cos(t); v = w0 + sw * wd * math.sin(t); pts.append((u, v) if axis == "h" else (v, u))
        out.append(Polygon(pts).buffer(0))
    for bf in L["bifolds"]:
        r = (bf[3], min(bf[2], bf[2] + 0.5 * bf[5]), bf[4], max(bf[2], bf[2] + 0.5 * bf[5])) if bf[1] == "h" else (min(bf[2], bf[2] + 0.5 * bf[5]), bf[3], max(bf[2], bf[2] + 0.5 * bf[5]), bf[4])
        out.append(box(*r))
    for a in b.geom(fl)["arcs"]:
        if len(a) >= 3: out.append(Polygon(list(a) + [a[0]]).buffer(0.02).union(LineString(a).buffer(0.05)))
    return unary_union(out)


@lru_cache(None)
def fixtures(fl):
    """{kind: shape} of the fixtures a ceiling grille must not be drawn over."""
    L = b.LV[fl]; out = {}
    for f in L["fx"]:
        if f[0] == "xequip": continue
        out.setdefault(f[0], []).append(b._fx_geom(f))
    return {k: unary_union(v) for k, v in out.items()}


def windows_near(fl):
    return [(cx, cy, w) for cx, cy, w, h in mq.windows(fl)]


# ---------------------------------------------------------------------------------------------- the layout of one joist space
@lru_cache(None)
def layout(space):
    g = grid(space); out = dict(regs=[], rets=[], jumps=[], exh=[], dry=[], hood=[], vent=[], ls=[], heater=[], problems=[], items=[])
    items = out["items"]                                           # (shape, level) of everything placed, for clearances
    k = FLAT[space]; S = mq.system(k)

    def clear_of_items(shp, fl, pad=0.15):
        for o, f_ in items:
            if f_ == fl and o.distance(shp) < pad: return False
        return True

    # ---- return grille(s)
    rinfo = RET[space]; rcfm = S["cfm"] - (RET2["cfm"] if space == 5 else 0); rsize = mq.return_grille(rcfm)
    fl = space; r = room_of(fl, rinfo["room"]); gw, gh = RG_SIZE.get(rsize, (1.7, 1.4))
    best = None
    if space in RET_AT:
        (cx, cy), orient = RET_AT[space]; w_, h_ = (gw, gh) if orient == "x" else (gh, gw)
        best = (0, (cx, cy), orient, box(cx - w_ / 2, cy - h_ / 2, cx + w_ / 2, cy + h_ / 2))
    for qq in ([] if best else r["rects"]):
        for orient in ("x", "y"):
            w_, h_ = (gw, gh) if orient == "x" else (gh, gw)
            for cx in np.arange(qq[0] + w_ / 2 + .15, qq[2] - w_ / 2 - .15 + 1e-6, G):
                for cy in np.arange(qq[1] + h_ / 2 + .15, qq[3] - h_ / 2 - .15 + 1e-6, G):
                    shp = box(cx - w_ / 2, cy - h_ / 2, cx + w_ / 2, cy + h_ / 2)
                    if shp.intersects(g.trunk_shape.buffer(0.12)) or not room_shape(r).buffer(.05).contains(shp): continue
                    if shp.intersects(box(*CHASE[fl]).buffer(.1)): continue
                    i, j = g.cell((cx, cy))
                    if g.blocked[i, j]: continue
                    sc = math.dist((cx, cy), rinfo["drop"]) * 0.6 + (1.0 if shp.intersects(swings(fl)) else 0.0) + \
                        (5.0 if LineString([(cx, cy), rinfo["drop"]]).intersects(g.trunk_shape) else 0.0)
                    if best is None or sc < best[0]: best = (sc, (cx, cy), orient, shp)
    if best is None:
        out["problems"].append(f"no place for return grille {rinfo['name']} in room {rinfo['room']}"); rp = r["lab"]; shp = Point(rp).buffer(.6); orient = "x"
    else:
        _sc, rp, orient, shp = best
    items.append((shp, fl))
    cm = cost_map(g, fl, {i for i, rr in enumerate(b.LV[fl]["rooms"]) if rr["kind"] in ("hall", "mech")}, "return")
    cells = dijkstra(g, cm, {g.cell(rinfo["drop"]): 0.0}, {g.cell(rp)})
    rpath = corners(g, cells, rinfo["drop"], rp) if cells else [rinfo["drop"], rp]
    if not cells: out["problems"].append(f"return {rinfo['name']}: no route")
    g.occupy(rpath, r_on=0.55, r_near=0.9, on=60, near=6)
    out["rets"].append(dict(name=rinfo["name"], fl=fl, p=rp, size=rsize, orient=orient, path=list(reversed(rpath)), cfm=rcfm, kind="ceiling", shape=shp))
    if space == 5:                                                  # attic floor grille on the R-C1 duct
        r6 = room_of(6, RET2["room"]); R6 = room_shape(r6).buffer(-0.2); ls = LineString(rpath); s2 = mq.return_grille(RET2["cfm"])
        w2, h2 = RG_SIZE.get(s2, (1.7, 1.2)); cand = []
        if 6 in RET_AT:
            (px_, py_), o_ = RET_AT[6]; w_, h_ = (w2, h2) if o_ == "x" else (h2, w2)
            cand = [(0, (px_, py_), o_, box(px_ - w_ / 2, py_ - h_ / 2, px_ + w_ / 2, py_ + h_ / 2))]
            if not room_shape(r6).contains(cand[0][3]): out["problems"].append("R-C2 is not inside the attic stair hall")
            if cand[0][3].intersects(g.trunk_shape): out["problems"].append("R-C2 box is on the trunk")
            rpath = rpath[:-1] + [(px_, py_)] if False else rpath
        for t in ([] if cand else np.linspace(0, ls.length, 80)):
            p = ls.interpolate(t); seg_h = True
            for a, c in zip(rpath[:-1], rpath[1:]):
                if LineString([a, c]).distance(p) < 1e-6: seg_h = abs(a[1] - c[1]) < 1e-6
            w_, h_ = (w2, h2) if seg_h else (h2, w2)
            sh2 = box(p.x - w_ / 2, p.y - h_ / 2, p.x + w_ / 2, p.y + h_ / 2)
            if R6.contains(sh2) and not sh2.intersects(swings(6)): cand.append((abs(p.y - 16.0), (p.x, p.y), "x" if seg_h else "y", sh2))
        if cand:
            _s, p2, o2, sh2 = min(cand, key=lambda t: t[0]); path2 = [p2, p2]
        else:                                                       # not under the stair hall: its own short duct to R-C1's
            p2 = (18.7, 15.3); o2 = "x"; sh2 = box(p2[0] - w2 / 2, p2[1] - h2 / 2, p2[0] + w2 / 2, p2[1] + h2 / 2)
            cm6 = cost_map(g, 6, {next(i for i, rr in enumerate(b.LV[6]["rooms"]) if rr["no"] == RET2["room"])}, "return")
            tgt = {g.cell(pp) for pp in (ls.interpolate(t).coords[0] for t in np.linspace(0, ls.length, 60))}
            cells = dijkstra(g, cm6, {g.cell(p2): 0.0}, tgt); path2 = corners(g, cells, p2) if cells else [p2, p2]
            g.occupy(path2, r_on=.45, r_near=.8, on=60, near=6)
            out["problems"].append("R-C1's duct does not pass under the attic stair hall: R-C2 has its own duct")
        items.append((sh2, 6))
        out["rets"].append(dict(name=RET2["name"], fl=6, p=p2, size=s2, orient=o2, path=path2, cfm=RET2["cfm"], kind="floor", shape=sh2))

    # ---- supply registers
    ATTIC = q.outline(6).buffer(-0.35) if space == 5 else None
    fans = {}
    for fl in LEVELS[space]:
        for d in e.all_devices()[fl][0]:
            if d["k"] == "F": fans.setdefault((fl, d["room"]), []).append((d["x"], d["y"]))
    plan = []
    for x in S["served"]:
        fl = x["fl"]
        if SPACE[fl] != space: continue
        plan.append(x)
    plan.sort(key=lambda x: -x["cfm"])
    for x in plan:
        fl = x["fl"]; r = x["r"]; n = mq.n_registers(r, x["cfm"]); floor = (fl == 6); rw, rh = REG["floor" if floor else "ceiling"]
        R = room_shape(r); fx = fixtures(fl)
        bad = unary_union([fx.get(kk, Polygon()).buffer(.25) for kk in ("tub", "range", "wc")] + [fx.get(kk, Polygon()) for kk in ("van", "fridge", "furnace", "wh", "washer", "dryer", "wdstack")] if floor else
                          [fx.get(kk, Polygon()).buffer(.25) for kk in ("tub", "range")])
        if floor: bad = bad.union(unary_union([box(*f[1:5]) for f in b.LV[fl]["fx"] if f[0] in ("base", "sinkbase", "dw")]))
        pref = []
        for cx, cy, w, h, nv, br in sorted(x["wins"], key=lambda t: -t[2]):
            dd = 1.0 if floor else 1.5; pref.append((cx - nv[0] * dd, cy - nv[1] * dd))
        if len(pref) < n and x["edges"]:
            L_, nv, br, kind = max(x["edges"], key=lambda t: t[0]); x0, y0, x1, y1 = max(r["rects"], key=lambda qq: (qq[2] - qq[0]) * (qq[3] - qq[1]))
            dd = 1.0 if floor else 1.5
            for i in range(n - len(pref)):
                if nv[0] == 0: pref.append((x0 + (x1 - x0) * (i + 1) / (n - len(pref) + 1), (y1 - dd) if nv[1] > 0 else (y0 + dd)))
                else: pref.append(((x1 - dd) if nv[0] > 0 else (x0 + dd), y0 + (y1 - y0) * (i + 1) / (n - len(pref) + 1)))
        if r["kind"] == "bath" or not pref:
            # baths: away from the tub and the fan, over the floor in front of the vanity or by the door
            fr = R.buffer(-.5).difference(bad)
            pref = [(fr.centroid.x, fr.centroid.y)] if not fr.is_empty else [R.centroid.coords[0]]
        got = []
        for pi in range(n):
            pp = pref[pi % len(pref)]; best = None
            for qq in r["rects"]:
                for orient in ("x", "y"):
                    w_, h_ = (rw, rh) if orient == "x" else (rh, rw)
                    for cx in np.arange(qq[0] + w_ / 2 + .2, qq[2] - w_ / 2 - .2 + 1e-6, G):
                        for cy in np.arange(qq[1] + h_ / 2 + .2, qq[3] - h_ / 2 - .2 + 1e-6, G):
                            shp = box(cx - w_ / 2, cy - h_ / 2, cx + w_ / 2, cy + h_ / 2)
                            if not R.contains(shp) or shp.intersects(bad) or shp.intersects(g.trunk_shape.buffer(.15)): continue
                            if shp.intersects(box(*CHASE[fl]).buffer(.1)): continue
                            i, j = g.cell((cx, cy))
                            if g.blocked[i, j] or not g.inside[i, j]: continue
                            if space == 5 and not ATTIC.contains(shp): continue
                            if any(math.dist((cx, cy), f_) < 1.6 for f_ in fans.get((fl, r["no"]), [])): continue
                            if not clear_of_items(shp, fl, .5): continue
                            if any(math.dist((cx, cy), gp) < 3.0 for gp in got): continue
                            tr = g.trunk_shape.exterior.distance(Point(cx, cy))
                            sc = math.dist((cx, cy), pp) + 0.12 * tr + (2.0 if shp.intersects(swings(fl)) else 0.0) + (0.6 if orient != ("x" if abs(pp[0] - cx) < abs(pp[1] - cy) else "y") else 0.0)
                            if best is None or sc < best[0]: best = (sc, (cx, cy), orient, shp)
            if best is None:
                out["problems"].append(f"no place for a register in room {r['no']} (level {fl})"); continue
            _s, p, orient, shp = best; got.append(p); items.append((shp, fl))
            c = x["cfm"] / n
            out["regs"].append(dict(p=p, cfm=c, d=mq.round_duct(c), g=mq.register(c), room=r["no"], flat=k, fl=fl, floor=floor, orient=orient, shape=shp))
    # ---- jump ducts (levels 3 to 5) and transfer grilles (attic)
    for fl in LEVELS[space]:
        L = b.LV[fl]; sw = swings(fl)
        for d in L["doors"]:
            if not d[8] or not d[8].lower().startswith("bedroom"): continue
            axis, w0, a0, a1, hinge, swing = d[1:7]; cmid = (a0 + a1) / 2
            P = lambda u, v: (u, v) if axis == "h" else (v, u)
            bed = next((r for r in L["rooms"] if r["kind"] == "bed" and room_shape(r).contains(Point(P(cmid, w0 + .9)))), None); sgn = 1
            if bed is None:
                bed = next((r for r in L["rooms"] if r["kind"] == "bed" and room_shape(r).contains(Point(P(cmid, w0 - .9)))), None); sgn = -1
            if bed is None: continue
            hall = next((r for r in L["rooms"] if r is not bed and room_shape(r).contains(Point(P(cmid, w0 - sgn * .9)))), None)
            x_, _k = next(((xx, kk) for kk in [k] for xx in S["served"] if xx["fl"] == fl and xx["r"]["no"] == bed["no"]), (None, None))
            if x_ is None or hall is None: continue
            jd = mq.jump(x_["cfm"])
            if fl == 6:                                              # attic: through-wall transfer grilles beside the door
                best = None; Wsh = e.solid(fl)
                for t in list(np.arange(a1 + .35, a1 + 2.5, .1)) + list(np.arange(a0 - .35, a0 - 2.5, -.1)):
                    seg = LineString([P(t - .5, w0), P(t + .5, w0)])
                    if not Wsh.buffer(.02).contains(seg): continue
                    if seg.buffer(.3).intersects(sw): continue
                    if not room_shape(bed).buffer(.12).contains(Point(P(t, w0 + sgn * .35))) or not room_shape(hall).buffer(.12).contains(Point(P(t, w0 - sgn * .35))): continue
                    sc = abs(t - cmid)
                    if best is None or sc < best[0]: best = (sc, t)
                if best is None:
                    out["problems"].append(f"no wall beside door {d[0]} for a transfer grille"); continue
                t = best[1]; th = 0.2
                a_ = P(t, w0 + sgn * th); b_ = P(t, w0 - sgn * th)
                out["jumps"].append(dict(a=a_, b=b_, d=jd, room=bed["no"], fl=fl, kind="wall", axis=axis, size="14x6" if x_["cfm"] > 80 else "12x6"))
                items.append((LineString([a_, b_]).buffer(.5), fl)); continue
            Bsh, Hsh = room_shape(bed).buffer(-.4), room_shape(hall).buffer(-.4); best = None
            for t in np.arange(cmid - 4.0, cmid + 4.01, G):
                for d1 in np.arange(0.75, 2.6, G):
                    pa = P(t, w0 + sgn * d1); A = Point(pa).buffer(.38, cap_style="square")
                    if not Bsh.contains(A) or A.intersects(g.trunk_shape.buffer(.12)) or not clear_of_items(A, fl, .3): continue
                    ia, ja = g.cell(pa)
                    if g.blocked[ia, ja]: continue
                    for d2 in np.arange(0.75, 2.6, G):
                        pb = P(t, w0 - sgn * d2); B = Point(pb).buffer(.38, cap_style="square")
                        if not Hsh.contains(B) or B.intersects(g.trunk_shape.buffer(.12)) or not clear_of_items(B, fl, .3): continue
                        ib, jb = g.cell(pb)
                        if g.blocked[ib, jb]: continue
                        ln = LineString([pa, pb])
                        if ln.intersects(g.trunk_shape) or any(ln.intersects(o) for o, f_ in items if f_ == fl): continue
                        sc = abs(t - cmid) * .7 + d1 + d2 + g.occ[g.cell(pa)] * .02 + g.occ[g.cell(pb)] * .02 + 1.2 * A.intersects(sw) + 1.2 * B.intersects(sw)
                        if best is None or sc < best[0]: best = (sc, pa, pb)
            if best is None:
                out["problems"].append(f"no place for the jump duct of bedroom {bed['no']}"); continue
            _s, pa, pb = best
            out["jumps"].append(dict(a=pa, b=pb, d=jd, room=bed["no"], fl=fl, kind="ceiling"))
            for p in (pa, pb): items.append((Point(p).buffer(.38, cap_style="square"), fl))
            g.occupy([pa, pb], r_on=.45, r_near=.8, on=30, near=4)
    # ---- branches: farthest first
    for rg in sorted(out["regs"], key=lambda rg: -g.trunk_shape.distance(Point(rg["p"]))):
        fl = rg["fl"]; own = {i for i, rr in enumerate(b.LV[fl]["rooms"]) if rr["no"] == rg["room"]}
        cm = cost_map(g, fl, own, "supply"); gc = g.cell(rg["p"])
        cm[gc] = 1.0
        src = {(i, j): 0.0 for i, j in zip(*np.nonzero(g.centre))}
        cells = dijkstra(g, cm, src, {gc})
        if not cells:
            out["problems"].append(f"branch to room {rg['room']} (level {fl}): no route"); rg["path"] = [rg["p"]]; continue
        a = nearest_points(LineString(g.trunk_lines[0]) if len(g.trunk_lines) == 1 else unary_union([LineString(t) for t in g.trunk_lines]), Point(g.pt(cells[0])))[0]
        path = corners(g, cells, (a.x, a.y), rg["p"])
        if len(path) >= 3 and math.dist(path[-1], path[-2]) < 0.6:          # a short jog at the end: slide the register onto the run instead
            p0, p1 = path[-3], path[-2]; v = (path[-1][0] - p1[0], path[-1][1] - p1[1])
            np_ = (p1[0], p1[1])
            shp2 = shapely.affinity.translate(rg["shape"], -v[0], -v[1])
            if room_shape(room_of(fl, rg["room"])).contains(shp2):
                rg["p"] = np_; rg["shape"] = shp2; path = path[:-1]
        rg["path"] = path; g.occupy(path)
    # ---- vents and line sets: furnace and water heater to the chase (one level per space here: the mechanical room's level)
    fl = space; L = b.LV[fl]; ch = box(*CHASE[fl])
    tgt = {(i, j) for i, j in zip(*np.nonzero(g.mask(ch)))}
    mech = {i for i, rr in enumerate(L["rooms"]) if rr["kind"] == "mech"}; bundle = []
    for f in L["fx"]:
        if f[0] not in ("furnace", "wh"): continue
        c = ((f[1] + f[3]) / 2, (f[2] + f[4]) / 2) if f[0] == "furnace" else (f[1], f[2])
        for what in (["vent", "ls"] if f[0] == "furnace" else ["vent"]):
            cm = cost_map(g, fl, mech, "vent"); cm[g.blocked & g.mask(ch)] = 1.0
            fp = box(*f[1:5]) if f[0] == "furnace" else Point(c).buffer(.92)
            for i, j in zip(*np.nonzero(g.mask(fp))): cm[i, j] = min(cm[i, j], 1.0)
            src = {(i, j): math.dist(g.pt((i, j)), c) / G * .5 for i, j in zip(*np.nonzero(g.mask(fp)))}
            cells = dijkstra(g, cm, src, tgt)
            if not cells: out["problems"].append(f"{what} from the {f[0]}: no route to the chase"); continue
            path = corners(g, cells)
            bundle.append(path)                                   # vents and line sets run together: no penalty between them
            out["vent" if what == "vent" else "ls"].append(dict(path=path, what=f[0], fl=fl))
    for path in bundle: g.occupy(path, r_on=.2, r_near=.4, on=20, near=2)
    # ---- exhaust: bath fans, dryers, range hoods
    caps = []
    for fl in LEVELS[space]:
        L = b.LV[fl]
        jobs = []
        for d in e.all_devices()[fl][0]:
            if d["k"] == "F": jobs.append(("exh", (d["x"], d["y"]), d["room"], None))
        for f in L["fx"]:
            if f[0] in ("dryer", "wdstack"): jobs.append(("dry", ((f[1] + f[3]) / 2, (f[2] + f[4]) / 2), None, box(*f[1:5])))
            if f[0] == "range": jobs.append(("hood", ((f[1] + f[3]) / 2, (f[2] + f[4]) / 2), None, box(*f[1:5])))
        for kind, p, room, fp in jobs:
            if kind == "dry" and fl in VENTLESS:
                out["dry"].append(dict(a=p, path=[], cap=None, to="none", fl=fl, room=None, ventless=True, eq=0)); continue
            if fl == 6:                                              # attic baths: straight up through the roof slope
                ext = q.outline(6).exterior; bp = nearest_points(ext, Point(p))[0]; v = np.array([bp.x - p[0], bp.y - p[1]])
                v = v / (np.linalg.norm(v) or 1); v = np.array([0.0, np.sign(v[1])]) if abs(v[1]) > abs(v[0]) else np.array([np.sign(v[0]), 0.0])
                cap = (p[0] + v[0] * .9, p[1] + v[1] * .9)
                out["exh"].append(dict(a=p, path=[p, cap], cap=cap, to="roof", fl=fl, room=room)); continue
            rules = CAPS[fl]; tc = {}
            for i, j in zip(*np.nonzero(g.capzone)):
                pt_ = g.pt((i, j)); bp = nearest_points(g.out.exterior, Point(pt_))[0]
                n = np.array(pt_) - np.array([bp.x, bp.y]); n = -n / (np.linalg.norm(n) or 1)
                s = side(n); pen = rules.get(s)
                if pen is None: continue
                if any(math.dist(pt_, (wx, wy)) < 3.0 + w / 2 for wx, wy, w in windows_near(fl)): continue
                if any(math.dist(pt_, c_) < 3.0 for c_ in caps): continue
                if any(dd[8] and "entrance" in dd[8].lower() and LineString([((dd[3], dd[2]) if dd[1] == "h" else (dd[2], dd[3])), ((dd[4], dd[2]) if dd[1] == "h" else (dd[2], dd[4]))]).distance(Point(pt_)) < 3.0 for dd in L["doors"]): continue
                tc[(i, j)] = pen / G
            eave = set()
            if space == 5 and kind == "exh":                          # main-floor bath: into the eave space, roof cap
                em = g.mask(q.outline(5).buffer(-.5)) & ~g.mask(q.outline(6).buffer(.3))
                eave = {(i, j) for i, j in zip(*np.nonzero(em))}
            if kind == "hood":
                bp = None; best = None
                for c_, pen in tc.items():
                    pt_ = g.pt(c_); dd = fp.distance(Point(pt_))
                    if dd < 1.0 and (best is None or dd < best[0]): best = (dd, pt_)
                if best is None:
                    out["hood"].append(dict(a=p, path=[], cap=None, ducted=False, fl=fl)); continue
                cap = best[1]; ext = g.out.exterior; bp = nearest_points(ext, Point(cap))[0]
                a_ = nearest_points(fp.exterior, Point(cap))[0]
                cap = (bp.x, bp.y) if abs(bp.x - a_.x) < .05 or abs(bp.y - a_.y) < .05 else (bp.x, bp.y)
                out["hood"].append(dict(a=(a_.x, a_.y), path=[(a_.x, a_.y), cap], cap=cap, ducted=True, fl=fl)); caps.append(cap); continue
            own = {i for i, rr in enumerate(L["rooms"]) if (room and rr["no"] == room) or (fp is not None and room_shape(rr).intersects(fp))}
            cm = cost_map(g, fl, own, "exhaust")
            cm[g.capzone] += 20.0                                  # never run along the outside wall
            for c_ in tc: cm[c_] = 50.0
            src = {g.cell(p): 0.0} if fp is None else {(i, j): 0.0 for i, j in zip(*np.nonzero(g.mask(fp.buffer(-.2))))}
            for c_ in src: cm[c_] = 1.0
            goal = set(tc) | eave
            # Dijkstra from the source; target cost added on arrival by seeding from the targets instead
            cells = dijkstra(g, cm, {c_: tc.get(c_, 2.0) for c_ in goal}, set(src))
            if not cells:
                out["problems"].append(f"{kind} in room {room or '?'} (level {fl}): no allowed outside wall reachable"); continue
            cells = list(reversed(cells))
            path = corners(g, cells, p if fp is None else None)
            end = g.pt(cells[-1]); to = "eave" if cells[-1] in eave else "wall"
            if to == "wall":
                bp = nearest_points(g.out.exterior, Point(end))[0]; end = (bp.x, bp.y)
                last = path[-2] if len(path) > 1 else path[0]
                end = (end[0], last[1]) if abs(last[1] - path[-1][1]) < 1e-6 and abs(end[0] - last[0]) > abs(end[1] - last[1]) else (last[0], end[1]) if abs(last[0] - path[-1][0]) < 1e-6 else end
                path[-1] = end
            if fp is not None:
                a_ = nearest_points(fp.exterior, Point(path[1] if len(path) > 1 else path[0]))[0]
                path = snap_end(path, (a_.x, a_.y), 0) if len(path) > 1 else path
            g.occupy(path, r_on=.25, r_near=.45, on=20, near=2)
            caps.append(path[-1])
            rec = dict(a=path[0], path=path, cap=path[-1], to=to, fl=fl, room=room)
            if kind == "dry":
                Ld = sum(math.dist(a, c) for a, c in zip(path[:-1], path[1:])); bends = max(0, len(path) - 2) + 2
                rec["eq"] = Ld + 2.0 + 5.0 * bends; rec["bends"] = bends; rec["len"] = Ld
                rec["ventless"] = False
                if rec["eq"] > 35: out["problems"].append(f"dryer vent level {fl}: {rec['eq']:.0f} ft equivalent, over 35")
                out["dry"].append(rec)
            else:
                out["exh"].append(rec)
    for fl in LEVELS[space]:
        if fl in TSTAT:
            x, y, n = TSTAT[fl]
            if not e.solid(fl).buffer(.05).contains(Point(x - n[0] * .15, y - n[1] * .15)): out["problems"].append(f"thermostat level {fl} is not on a wall")
            if e.gaps(fl).contains(Point(x, y)) or swings(fl).contains(Point(x + n[0] * .3, y + n[1] * .3)): out["problems"].append(f"thermostat level {fl} is in a door opening or swing")
    if space == 4:                                                    # the upper flat's stair hall: electric wall heater
        (px, py), n = e.snap(4, 27.5, 26.9); out["heater"].append(dict(p=(px, py), n=n, fl=4))
    # ---- checks: ducts crossing in the same joist space
    lines = []
    for rg in out["regs"]:
        if len(rg.get("path", [])) > 1: lines.append((f"branch {rg['room']}", LineString(rg["path"])))
    for rt in out["rets"]:
        if len(rt["path"]) > 1 and math.dist(rt["path"][0], rt["path"][-1]) > .1: lines.append((rt["name"], LineString(rt["path"])))
    for x_ in out["exh"] + out["dry"]:
        if x_["fl"] != 6 and len(x_["path"]) > 1: lines.append((f"exhaust {x_.get('room') or 'dryer'}", LineString(x_["path"])))
    for i in range(len(lines)):
        for j in range(i + 1, len(lines)):
            a, c = lines[i][1], lines[j][1]
            x = a.intersection(c)
            if not x.is_empty and x.length < 1e-6:
                ends = [Point(p) for p in (a.coords[0], a.coords[-1], c.coords[0], c.coords[-1])]
                pts = list(x.geoms) if hasattr(x, "geoms") else [x]
                pts = [p for p in pts if p.geom_type == "Point" and min(p.distance(en) for en in ends) > .3]
                if pts: out["problems"].append(f"{lines[i][0]} crosses {lines[j][0]} at ({pts[0].x:.1f}, {pts[0].y:.1f}): one passes under in the joist bay; check depth")
            elif not x.is_empty and x.length > .2:
                out["problems"].append(f"{lines[i][0]} runs on top of {lines[j][0]} for {x.length:.1f} ft")
        if not lines[i][0].startswith("branch") and lines[i][1].intersects(g.trunk_shape):
            out["problems"].append(f"{lines[i][0]} crosses the trunk")
    return out


def level(fl):
    """The parts of a space's layout drawn on level fl's plan."""
    D = layout(SPACE[fl]); out = {}
    for kk, v in D.items():
        out[kk] = [x for x in v if not isinstance(x, dict) or x.get("fl", fl) == fl] if kk not in ("problems", "items") else v
    return out


if __name__ == "__main__":
    import time
    for sp in (3, 4, 5):
        t = time.time(); D = layout(sp)
        print(f"space {sp}: {time.time() - t:.1f}s  regs {len(D['regs'])} rets {len(D['rets'])} jumps {len(D['jumps'])} exh {len(D['exh'])} dry {len(D['dry'])} hood {len(D['hood'])} vent {len(D['vent'])} ls {len(D['ls'])}")
        for pr in D["problems"]: print("   PROBLEM:", pr)
        for rg in D["regs"]: print(f"   reg L{rg['fl']} {rg['room']} {rg['cfm']:.0f} at ({rg['p'][0]:.2f}, {rg['p'][1]:.2f}) path {[(round(a, 1), round(c, 1)) for a, c in rg.get('path', [])]}")
        for x in D["exh"] + D["dry"]: print(f"   exh L{x['fl']} {x.get('room')} to {x['to']} {[(round(a, 1), round(c, 1)) for a, c in x['path']]} eq {x.get('eq', '')}")
        for x in D["rets"]: print(f"   ret {x['name']} at {tuple(round(v, 2) for v in x['p'])} path {[(round(a, 1), round(c, 1)) for a, c in x['path']]}")
        for x in D["vent"] + D["ls"]: print(f"   {x['what']} L{x['fl']} {[(round(a, 1), round(c, 1)) for a, c in x['path']]}")
        for x in D["jumps"]: print(f"   jump L{x['fl']} {x['room']} {x['kind']} {tuple(round(v, 2) for v in x['a'])} {tuple(round(v, 2) for v in x['b'])}")
        for x in D["hood"]: print(f"   hood L{x['fl']} ducted {x['ducted']} {x['path']}")
