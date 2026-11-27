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
TRUNK = {3: [[(18.9, 3.3), (18.9, 11.95)], [(15.3, 11.95), (22.6, 11.95)], [(15.3, 11.95), (15.3, 16.1), (6.5, 16.1)]],
         4: [[(13.7, 7.35), (12.4, 7.35), (12.4, 13.0)], [(13.7, 7.35), (13.7, 5.55), (22.8, 5.55), (22.8, 15.6)]],
         5: [[(16.45, 11.0), (16.45, 17.0), (4.5, 17.0)], [(16.45, 17.0), (20.6, 17.0)]]}
# Return: filter grille in a wall of one of these rooms, box behind it, duct to the drop beside the furnace (into its return platform).
RET = {3: dict(rooms=("107",), drop=(20.95, 3.33), name="R-A"), 4: dict(rooms=("207", "210"), drop=(13.25, 9.1), name="R-B"),
       5: dict(rooms=("301", "306"), drop=(16.2, 10.5), name="R-C1", through=True)}
RET2 = dict(fl=6, rooms=("405",), name="R-C2", cfm=160, drop=(18.5, 12.4))      # attic: high wall return at the top of the stair, stack down, duct to F-C
VENTLESS = {4: "Heat-pump dryer, ventless: no outside wall the vent may use is within 35 ft equivalent (west route about 51 ft eq.; north windows; east stair)."}
# Vertical shafts: the old chimney becomes the chase; on the middle level the chimney is gone and the pipes rise behind the water heater.
CHASE = {3: (17.4, 6.4, 18.0, 9.38), 4: (16.45, 6.15, 18.7, 8.6), 5: (15.65, 6.2, 17.85, 8.6), 6: (15.7, 5.96, 17.75, 8.4)}
TSTAT = {3: (3.0, 13.12, (0, 1)), 4: (11.3, 13.55, (0, -1)), 5: (23.75, 18.6, (-1, 0))}
# Exhaust caps: which outside walls may take one, with a cost (ft of extra duct it is worth to avoid). None = never.
# West: small caps are fine (owner); nothing big on that side. East: the wood stair and the property line.
# Lower flat north end: below grade. Lower flat south: the rear deck and the condensers under it.
CAPS = {3: dict(N=None, S=8.0, E=0.0, W=0.0), 4: dict(N=0.0, S=0.0, E=6.0, W=0.0), 5: dict(N=0.0, S=0.0, E=6.0, W=0.0)}
BELOW_GRADE = {3: lambda p, s: s in ("N", "W") and p[0] > 21.0}     # lower flat north end (bedroom 2): north and west walls against earth
HOST = {(4, "202"): "201", (5, "302"): "301"}
CHASE_ROOMS = {5: ("314",), 6: ("408",)}
# attic: where the ceiling is too low for a high wall register (the slopes): the bath alcoves under the east slope, and the west slope
ATTIC_LOW = unary_union([box(11.0, 5.5, 22.7, 9.0), box(-1.0, 19.8, 32.0, 22.0)])         # pipe chases: no grille boots in their walls  # kitchens with every wall taken by cabinets, windows or openings: fed from the open living room
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
    if kind in ("supply", "return") and g.space == 5: c = c + np.where(g.attic, 0.0, 3.0)      # under the eave floor: only if it must, R-8 duct
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


@lru_cache(None)
def wall_faces(fl, no):
    """Wall faces around a room's open floor (walls inside the room's outline too, such as a pantry or laundry alcove), sampled every
    3 in.: dicts with edge id, face point p, inward normal n, along-wall u, what is behind (interior / exterior / demising / none),
    the room behind and the wall thickness."""
    from shapely.prepared import prep
    from shapely.geometry.polygon import orient
    r = room_of(fl, no); R = room_shape(r); Sg = e.solid(fl); S_ = prep(Sg); P_ = prep(q.outline(fl)); out = []
    L = b.LV[fl]; k = mq.flat_of(fl, r); others = [(rr, prep(room_shape(rr))) for rr in L["rooms"] if rr is not r]
    inner = [room_shape(rr) for rr in L["rooms"] if rr is not r and R.buffer(.05).contains(room_shape(rr))]
    free = R.buffer(.12, join_style="mitre").difference(Sg)
    for sh in inner: free = free.difference(sh.buffer(.12, join_style="mitre"))
    polys = [p_ for p_ in (free.geoms if hasattr(free, "geoms") else [free]) if p_.area > 1.0]
    for pi, P in enumerate(polys):
        P = orient(P, 1.0)
        for ri, ring in enumerate([P.exterior] + list(P.interiors)):
            c = list(ring.coords)
            for si, (a_, b_) in enumerate(zip(c[:-1], c[1:])):
                d = math.dist(a_, b_)
                if d < .5: continue
                u = ((b_[0] - a_[0]) / d, (b_[1] - a_[1]) / d); n_out = (u[1], -u[0])
                for t in np.arange(.125, d - .1, .25):
                    p = (a_[0] + u[0] * t, a_[1] + u[1] * t)
                    if not R.buffer(.15).contains(Point(p)): continue
                    f0 = next((dd for dd in np.arange(-.05, .3, .05) if S_.contains(Point(p[0] + n_out[0] * dd, p[1] + n_out[1] * dd))), None)
                    if f0 is None: continue
                    th = next((dd for dd in np.arange(f0 + .05, 2.5, .05) if not S_.contains(Point(p[0] + n_out[0] * dd, p[1] + n_out[1] * dd))), 2.5) - f0
                    face = (p[0] + n_out[0] * f0, p[1] + n_out[1] * f0)
                    bp = Point(face[0] + n_out[0] * (th + .3), face[1] + n_out[1] * (th + .3))
                    if not P_.contains(bp): back, bno = "exterior", None
                    else:
                        rr = next((rr for rr, pr in others if pr.contains(bp)), None)
                        if rr is None: back, bno = "none", None
                        elif mq.flat_of(fl, rr) != k: back, bno = "demising", rr["no"]
                        else: back, bno = "interior", rr["no"]
                    out.append(dict(eid=(pi, ri, si), t=t, p=face, n=(-n_out[0], -n_out[1]), u=u, back=back, bno=bno, th=th))
    return out


# what may not be in front of (below) a high wall grille: cabinets with uppers, tall appliances, the tub, the vanity mirror, equipment
WALL_BAD = ("fridge", "base", "sinkbase", "dw", "range", "wdstack", "washer", "dryer", "tub", "van", "furnace", "wh", "panel")


@lru_cache(None)
def wall_blockers(fl):
    L = b.LV[fl]; shp = [b._fx_geom(f) for f in L["fx"] if (f[0] in WALL_BAD or (fl == 6 and f[0] == "wc")) and f[0] != "panel"]
    shp += [box(*b.panel_box(f)) for f in L["fx"] if f[0] == "panel"]
    return unary_union(shp)


def wall_place(fl, r, w, backs=("interior", "exterior", "none")):
    """Places on the walls of room r for a grille w ft wide: solid wall the whole width plus 2 in. each side, no door or opening,
    nothing tall or wet below it, the wall behind of an allowed kind. Each: dict(p, n, u, back, bno, th, front)."""
    rows = wall_faces(fl, r["no"]); gp = e.gaps(fl); bl = wall_blockers(fl); out = []
    by = {}
    for rw in rows:                                                 # samples on one wall line, whatever polygon segment they came from
        n = rw["n"]; key = (round(n[0], 2), round(n[1], 2), round((rw["p"][0] * n[0] + rw["p"][1] * n[1]) / .15))
        by.setdefault(key, []).append(rw)
    half = w / 2 + .17
    for key, rs in by.items():
        u_ = (-key[1], key[0]); tt = lambda rw: rw["p"][0] * u_[0] + rw["p"][1] * u_[1]
        rs.sort(key=tt); ts = np.array([tt(rw) for rw in rs])
        for i, rw in enumerate(rs):
            if rw["back"] not in backs or rw["bno"] in CHASE_ROOMS.get(fl, ()): continue
            if fl == 6 and ATTIC_LOW.contains(Point(rw["p"])): continue
            idx = np.nonzero(np.abs(ts - ts[i]) <= half)[0]
            if len(idx) < int(2 * half / .25) or (len(idx) > 1 and np.max(np.diff(ts[idx])) > .32): continue
            span = [rs[j] for j in idx]
            if any(sp["back"] != rw["back"] or sp["bno"] != rw["bno"] for sp in span): continue
            if any(gp.contains(Point(sp["p"])) for sp in span): continue
            c = dict(p=rw["p"], n=rw["n"], u=rw["u"], back=rw["back"], bno=rw["bno"], th=rw["th"])
            c["front"] = rect(c, w, .9)
            if c["front"].intersects(bl): continue
            out.append(c)
    return out


def rect(c, w, depth):
    """Rectangle w wide on the wall face at c, depth into the room."""
    p, n, u = c["p"], c["n"], c["u"]
    pts = [(p[0] - u[0] * w / 2, p[1] - u[1] * w / 2), (p[0] + u[0] * w / 2, p[1] + u[1] * w / 2)]
    pts += [(pts[1][0] + n[0] * depth, pts[1][1] + n[1] * depth), (pts[0][0] + n[0] * depth, pts[0][1] + n[1] * depth)]
    return Polygon(pts)


def wall_symbol(c, w, depth=.28):
    return rect(c, w, depth)


def cavity(c, w):
    """The stud bays the grille's boot or box takes, for keeping grilles on the two faces of one wall apart."""
    return rect(c, w + .7, -(c["th"] + .05))


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

    reach_cache = {}

    def reach(fl, p):
        """Duct length (ft) from the trunk to a point by the cheapest square route through this joist space."""
        if fl not in reach_cache:
            cm = cost_map(g, fl, set(), "supply"); cm = np.where(np.isinf(cm), np.inf, 1.0 + np.where(g.wall[fl], 1.0, 0.0))
            dist = np.full(cm.shape, np.inf); hp = []
            for i, j in zip(*np.nonzero(g.centre)): dist[i, j] = 0.0; heapq.heappush(hp, (0.0, i, j))
            while hp:
                d0, i, j = heapq.heappop(hp)
                if d0 > dist[i, j]: continue
                for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    a_, b_ = i + di, j + dj
                    if 0 <= a_ < g.nx and 0 <= b_ < g.ny and cm[a_, b_] < np.inf and d0 + cm[a_, b_] < dist[a_, b_]:
                        dist[a_, b_] = d0 + cm[a_, b_]; heapq.heappush(hp, (dist[a_, b_], a_, b_))
            reach_cache[fl] = dist
        i, j = g.cell(p); best = min((reach_cache[fl][a_, b_] for a_ in range(i - 2, i + 3) for b_ in range(j - 2, j + 3) if 0 <= a_ < g.nx and 0 <= b_ < g.ny), default=np.inf)
        return best * G if best < np.inf else 99.0

    # ---- return grilles: in walls, 14 in. wide (one stud bay), with a sealed box behind
    def place_return(fl, rooms, cfm, drop, high=True, need_back=None):
        sz = mq.wall_return(cfm); w = 14 / 12; best = None
        for no in rooms:
            r = room_of(fl, no)
            for c in wall_place(fl, r, w):
                if need_back and not need_back(c): continue
                if not clear_of_items(c["front"], fl, .1) or not clear_of_items(cavity(c, w), fl, .02): continue
                inner = (c["p"][0] - c["n"][0] * c["th"] / 2, c["p"][1] - c["n"][1] * c["th"] / 2)
                sc = math.dist(c["p"], drop) * .5 + (1.0 if c["front"].intersects(swings(fl)) else 0.0) + \
                    (12.0 if LineString([inner, (inner[0], drop[1]), drop]).intersects(g.trunk_shape) and LineString([inner, (drop[0], inner[1]), drop]).intersects(g.trunk_shape) else 0.0)
                if best is None or sc < best[0]: best = (sc, c, no)
        if best is None:
            out["problems"].append(f"no wall for return grille in rooms {rooms} (level {fl})"); return None
        c = best[1]; shp = wall_symbol(c, w)
        items.append((shp, fl)); items.append((c["front"], fl)); items.append((cavity(c, w), fl))
        return dict(fl=fl, p=c["p"], n=c["n"], u=c["u"], w=w, size=sz, cfm=cfm, kind="wall", high=high, shape=shp, back=c["back"], bno=c["bno"], th=c["th"], room=best[2])

    def mech_or_thick(fl):
        mechs = {rr["no"] for rr in b.LV[fl]["rooms"] if rr["kind"] in ("mech", "closet", "laundry")}
        return lambda c: (c["back"] == "interior" and c["bno"] in mechs) or c["th"] >= .7

    for fl_ in LEVELS[space]:                                       # no grille within 2 ft of the thermostat
        if fl_ in TSTAT: items.append((Point(TSTAT[fl_][:2]).buffer(2.0), fl_))
    rinfo = RET[space]; rcfm = S["cfm"] - (RET2["cfm"] if space == 5 else 0)
    rt = place_return(space, rinfo["rooms"], rcfm, rinfo["drop"], need_back=mech_or_thick(space))
    if rt: rt.update(name=rinfo["name"], drop=rinfo["drop"], through=rinfo.get("through", False)); out["rets"].append(rt)
    if space == 5:
        r2 = place_return(6, RET2["rooms"], RET2["cfm"], RET2["drop"])
        if r2: r2.update(name=RET2["name"], drop=RET2["drop"], through=False); out["rets"].append(r2)
    # ---- transfer grilles: through the wall beside each bedroom door, high on the bedroom side, low on the hall side
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
            x_ = next((xx for xx in S["served"] if xx["fl"] == fl and xx["r"]["no"] == bed["no"]), None)
            if x_ is None or hall is None: continue
            best = None; Wsh = e.solid(fl)
            for t in list(np.arange(a1 + .35, a1 + 3.0, .1)) + list(np.arange(a0 - .35, a0 - 3.0, -.1)):
                seg = LineString([P(t - .62, w0), P(t + .62, w0)])
                if not Wsh.buffer(.02).contains(seg): continue
                if not room_shape(bed).buffer(.12).contains(Point(P(t, w0 + sgn * .35))) or not room_shape(hall).buffer(.12).contains(Point(P(t, w0 - sgn * .35))): continue
                fa = box(*seg.buffer(.45, cap_style="flat").bounds)
                if not clear_of_items(fa, fl, .05): continue
                sc = abs(t - cmid) + (1.0 if seg.buffer(.3).intersects(sw) else 0.0)
                if best is None or sc < best[0]: best = (sc, t)
            if best is None:
                ce = mq.ceil_ft(fl, bed)
                if ce >= 7.6:                                        # above the door: 12 in. of wall over the header
                    t = cmid; th = 0.2
                    a_ = P(t, w0 + sgn * th); b_ = P(t, w0 - sgn * th)
                    out["jumps"].append(dict(a=a_, b=b_, room=bed["no"], fl=fl, kind="wall", axis=axis, size="14x6", cfm=x_["cfm"], over_door=True))
                    continue
                # jump duct: high wall grille in the bedroom and one in the hall, joined through the ceiling framing
                jd = mq.jump(x_["cfm"]); lists = []
                for rm, sg in ((bed, sgn), (hall, -sgn)):
                    cands = [c for c in wall_place(fl, rm, 14 / 12, backs=("interior", "none")) if clear_of_items(c["front"], fl, .2) and clear_of_items(cavity(c, 14 / 12), fl, .02)]
                    cands.sort(key=lambda c: math.dist(c["p"], P(cmid, w0))); lists.append(cands[:40])
                pick = [None, None]
                if all(lists):                                       # the pair with the shortest duct between them, near the door
                    man = lambda a_, b_: abs(a_[0] - b_[0]) + abs(a_[1] - b_[1])
                    ca, cb = min(((ca, cb) for ca in lists[0] for cb in lists[1] if man(ca["p"], cb["p"]) > .8),
                                 key=lambda t_: man(t_[0]["p"], t_[1]["p"]) + .3 * (math.dist(t_[0]["p"], P(cmid, w0)) + math.dist(t_[1]["p"], P(cmid, w0))))
                    pick = [ca, cb]
                if None in pick:
                    out["problems"].append(f"no wall for the jump duct of bedroom {bed['no']}"); continue
                ins = [(c["p"][0] - c["n"][0] * c["th"] / 2, c["p"][1] - c["n"][1] * c["th"] / 2) for c in pick]
                cm = cost_map(g, fl, {i for i, rr in enumerate(L["rooms"]) if rr["no"] in (bed["no"], hall["no"])}, "return")
                for c_ in ins: cm[g.cell(c_)] = 1.0
                cells = dijkstra(g, cm, {g.cell(ins[0]): 0.0}, {g.cell(ins[1])})
                path = corners(g, cells, ins[0], ins[1]) if cells else [ins[0], ins[1]]
                g.occupy(path, r_on=.35, r_near=.6, on=30, near=3)
                for c in pick: items.append((wall_symbol(c, 14 / 12), fl)); items.append((c["front"], fl)); items.append((cavity(c, 14 / 12), fl))
                out["jumps"].append(dict(a=pick[0]["p"], b=pick[1]["p"], ca=pick[0], cb=pick[1], path=path, d=jd, room=bed["no"], fl=fl, kind="jump", cfm=x_["cfm"], size="14x6"))
                continue
            t = best[1]; th = 0.2
            a_ = P(t, w0 + sgn * th); b_ = P(t, w0 - sgn * th)
            out["jumps"].append(dict(a=a_, b=b_, room=bed["no"], fl=fl, kind="wall", axis=axis, size="14x8" if x_["cfm"] > 110 else "14x6", cfm=x_["cfm"]))
            items.append((LineString([a_, b_]).buffer(.6), fl))
    # ---- supply registers: high on an inside wall (top 8 in. below the ceiling), throwing across the room toward the outside wall
    ATTIC = q.outline(6).buffer(-0.35) if space == 5 else None
    fans = {}
    for fl in LEVELS[space]:
        for d in e.all_devices()[fl][0]:
            if d["k"] == "F": fans.setdefault((fl, d["room"]), []).append((d["x"], d["y"]))
    plan = sorted([x for x in S["served"] if SPACE[x["fl"]] == space], key=lambda x: -x["cfm"])
    tags = {}
    for x in plan:
        fl = x["fl"]; r = x["r"]; n = mq.n_registers(r, x["cfm"]); c_ = x["cfm"] / n; sz, stack = mq.sidewall(c_); w = int(sz.split("x")[0]) / 12
        R = room_shape(r); got = []
        rets_here = [rt_["p"] for rt_ in out["rets"] if rt_["fl"] == fl and rt_["room"] == r["no"]]
        host = room_of(fl, HOST[(fl, r["no"])]) if (fl, r["no"]) in HOST else None
        for pi in range(n):
            best = None
            for rm, ok_back, pen in ((r, ("interior",), 0.0), (r, ("interior", "exterior", "none"), 4.0)) + (((host, ("interior", "none"), 1.0),) if host else ()):
                Rm = room_shape(rm).union(R)
                for c in wall_place(fl, rm, w, backs=ok_back):
                    p = c["p"]
                    if any(math.dist(p, gp) < 4.0 for gp in got): continue
                    if not clear_of_items(c["front"], fl, .2) or not clear_of_items(cavity(c, w), fl, .02): continue
                    eave = space == 5 and fl == 5 and not ATTIC.contains(Point(p[0] - c["n"][0] * .3, p[1] - c["n"][1] * .3))
                    ray = LineString([p, (p[0] + c["n"][0] * 40, p[1] + c["n"][1] * 40)]).intersection(Rm.buffer(.3))
                    seg = ray if ray.geom_type == "LineString" else max(ray.geoms, key=lambda gg: gg.length) if not ray.is_empty and hasattr(ray, "geoms") else ray
                    throw = seg.length if not seg.is_empty else 0
                    ex = seg.coords[-1] if not seg.is_empty else p
                    exitp = Point(ex[0] + c["n"][0] * .9, ex[1] + c["n"][1] * .9)
                    ext = not q.outline(fl).contains(exitp)
                    win = any(math.dist(ex, (wx, wy)) < ww / 2 + 1.5 for wx, wy, ww in windows_near(fl)) if ext else False
                    if rm is not r:                                              # from the host room: the air stream (3 ft wide) must sweep this room
                        jet = LineString([p, (p[0] + c["n"][0] * max(throw, 1), p[1] + c["n"][1] * max(throw, 1))]).buffer(1.5, cap_style="flat")
                        if jet.intersection(R).area < 6.0: continue
                    sc = 0.3 * reach(fl, p) + (max(0, 5 - throw) * 2 + max(0, throw - 16) * .5) - 3 * ext - 1.5 * win + pen + 3.0 * eave
                    sc += sum(3.0 for rp in rets_here if math.dist(rp, p) < 6)
                    sc += sum(2.0 for f_ in fans.get((fl, r["no"]), []) if math.dist(f_, p) < 2.0)
                    if best is None or sc < best[0]: best = (sc, c, throw, ext, win)
                if best: break
            if best is None:
                out["problems"].append(f"no wall for a register in room {r['no']} (level {fl})"); continue
            _s, c, throw, ext, win = best; got.append(c["p"]); shp = wall_symbol(c, w); items.append((cavity(c, w), fl))
            in_host = host is not None and not R.buffer(.3).contains(Point(c["p"][0] + c["n"][0] * .3, c["p"][1] + c["n"][1] * .3))
            items.append((shp, fl)); items.append((c["front"], fl))
            tags[FLAT[fl]] = tags.get(FLAT[fl], 0) + 1
            out["regs"].append(dict(p=c["p"], n=c["n"], u=c["u"], w=w, th=c["th"], cfm=c_, d=mq.round_duct(c_), g=sz, stack=stack, room=r["no"], flat=k, fl=fl,
                                    floor=False, kind="wall", shape=shp, throw=throw, faces_out=ext, back=c["back"], tag=f"S-{FLAT[fl]}{tags[FLAT[fl]]}",
                                    feed="stack up from the floor framing" if fl == 6 else "boot down through the top plate", host=host["no"] if in_host else None))
    # ---- return ducts (after the exhaust, which has the tighter length limits)
    for rt in out["rets"]:
        fl = rt["fl"]; inner = (rt["p"][0] - rt["n"][0] * rt["th"] / 2, rt["p"][1] - rt["n"][1] * rt["th"] / 2); drop = rt["drop"]
        if rt["through"]: rt["path"] = [inner, drop]; continue
        own = {i for i, rr in enumerate(b.LV[fl]["rooms"]) if rr["kind"] in ("hall", "mech", "laundry") or rr["no"] == rt["room"]}
        cm = cost_map(g, fl, own, "return"); gi = g.cell(inner); cm[gi] = 1.0
        cells = dijkstra(g, cm, {g.cell(drop): 0.0}, {gi})
        rt["path"] = list(reversed(corners(g, cells, drop, inner))) if cells else [inner, drop]
        if not cells: out["problems"].append(f"return {rt['name']}: no route")
        g.occupy(rt["path"], r_on=0.6, r_near=0.95, on=60, near=6)
    # ---- branches: farthest first
    for rg in sorted(out["regs"], key=lambda rg: g.trunk_shape.distance(Point(rg["p"]))):
        fl = rg["fl"]; own = {i for i, rr in enumerate(b.LV[fl]["rooms"]) if rr["no"] == rg["room"]}
        cm = cost_map(g, fl, own, "supply"); tip = (rg["p"][0] - rg["n"][0] * .12, rg["p"][1] - rg["n"][1] * .12); gc = g.cell(tip)
        cm[gc] = 1.0
        src = {(i, j): 0.0 for i, j in zip(*np.nonzero(g.centre))}
        cells = dijkstra(g, cm, src, {gc})
        if not cells:
            out["problems"].append(f"branch to room {rg['room']} (level {fl}): no route"); rg["path"] = [rg["p"]]; continue
        a = nearest_points(LineString(g.trunk_lines[0]) if len(g.trunk_lines) == 1 else unary_union([LineString(t) for t in g.trunk_lines]), Point(g.pt(cells[0])))[0]
        path = corners(g, cells, (a.x, a.y), tip)
        rg["path"] = path; g.occupy(path)
    for rg in out["regs"]:
        g.occ[g.mask(cavity(rg, rg["w"]).buffer(.8))] += 60.0
    for rt in out["rets"]:
        g.occ[g.mask(cavity(rt, rt["w"]).buffer(.35))] += 60.0
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
                if pen is None or (fl in BELOW_GRADE and BELOW_GRADE[fl](pt_, s)): continue
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
            cells = dijkstra(g, cm, {c_: tc.get(c_, 10.0 / G) for c_ in goal}, set(src))
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
        print(f"space {sp}: {time.time() - t:.1f}s  regs {len(D['regs'])} rets {len(D['rets'])} tg {len(D['jumps'])} exh {len(D['exh'])} dry {len(D['dry'])}")
        for pr in D["problems"]: print("   PROBLEM:", pr)
        for rg in D["regs"]: print(f"   {rg['tag']} L{rg['fl']} {rg['room']} {rg['cfm']:.0f} {rg['g']} at ({rg['p'][0]:.1f}, {rg['p'][1]:.1f}) n {rg['n']} back {rg['back']} throw {rg['throw']:.1f} out {rg['faces_out']} len {LineString(rg['path']).length if len(rg.get('path', [])) > 1 else 0:.1f}")
        for x in D["rets"]: print(f"   {x['name']} {x['size']} at {tuple(round(v, 2) for v in x['p'])} back {x['back']} {x['bno']} th {x['th']:.2f} path {[(round(a, 1), round(c, 1)) for a, c in x['path']]}")
        for x in D["jumps"]: print(f"   TG L{x['fl']} {x['room']} {tuple(round(v, 2) for v in x['a'])}")
        for x in D["exh"] + D["dry"]: print(f"   exh L{x['fl']} {x.get('room')} to {x['to']} {[(round(a, 1), round(c, 1)) for a, c in x['path']]} eq {x.get('eq', '')}")
