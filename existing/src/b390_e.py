"""390 Forest Ave builder set: electrical. Sheets E-001 (notes, legend), E-002 / E-003 (calculations, from b390_eq), E-004 (service and
feeders), E-005 (panel schedules) and E-101 to E-104 (power and lighting plans, one per level).

The house is gutted: every panel, circuit, box, device and fixture is new. Devices are placed from the plan model in build390.py:
general receptacles by the 6 ft rule along each unbroken wall (NEC 210.52(A)), counter receptacles by the 2 ft rule (210.52(C)),
lights from the lumen-method layout in b390_eq.py, switches at the latch side of each room's door.
"""
import math
import os
import sys
from functools import lru_cache

import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch, Polygon as MPoly, Rectangle
from matplotlib.patheffects import withStroke
from shapely.geometry import LineString, Point, box
from shapely.geometry.polygon import orient
from shapely.ops import nearest_points, unary_union

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build390 as b  # noqa: E402
import b390_eq as q  # noqa: E402
from common import INK, GREY, table  # noqa: E402

PW, LT, LS, HV, FD = "#1d4e9e", "#c25e00", "#b3261e", "#6a2c91", "#111111"
HALO = [withStroke(linewidth=1.4, foreground="white")]
FLAT_OF = {3: "A", 4: "B", 5: "C", 6: "C"}
VIEW = {3: ((-3.5, 36.1), (-5.2, 30.0)), 4: ((-2.5, 37.1), (-3.0, 30.0)), 5: ((-3.5, 36.1), (-3.0, 30.0)), 6: ((-3.5, 36.1), (-0.5, 32.5))}


def flat_of(fl, r):
    return "C" if (fl == 4 and r["no"] == "213") else FLAT_OF[fl]


# ---------------------------------------------------------------------------------------------- geometry helpers
@lru_cache(None)
def solid(fl):
    L = b.LV[fl]
    return unary_union([b.geom(fl)["walls"]] + [b.wshape(r) for r in L["new"] + L["fix"]])


def _door_boxes(fl, m=0.3):
    L = b.LV[fl]; out = []
    for d in L["doors"] + L["bifolds"]:
        w, a0, a1 = d[2:5]; out.append((a0 - m, w - .6, a1 + m, w + .6) if d[1] == "h" else (w - .6, a0 - m, w + .6, a1 + m))
    for o in b.geom(fl)["doors"]:
        if len(o["pts"]) >= 4:
            (x0, y0), (x1, y1) = np.min(o["pts"], 0), np.max(o["pts"], 0)
            if max(x1 - x0, y1 - y0) > 1.2:
                out.append((x0 - m, y0 - .5, x1 + m, y1 + .5) if x1 - x0 > y1 - y0 else (x0 - .5, y0 - m, x1 + .5, y1 + m))
    for f in L["fx"]:
        if f[0] == "panel":
            x0, y0, x1, y1 = f[1:5]; out.append((min(x0, x1) - 1.0, min(y0, y1) - 1.0, max(x0, x1) + 1.0, max(y0, y1) + 1.0))
    for c in L.get("cut", []):
        out.append((c[0] - .2, c[1] - .2, c[2] + .2, c[3] + .2))
    return out


@lru_cache(None)
def gaps(fl):
    """Door, closet and wall openings (new and existing) plus the panels: no receptacle or switch lands in them."""
    return unary_union([box(*q_) for q_ in _door_boxes(fl)])


@lru_cache(None)
def fxboxes(fl):
    return unary_union([box(*f[1:5]).buffer(.12) for f in b.LV[fl]["fx"] if len(f) >= 5 and not isinstance(f[3], str) and f[0] not in ("xequip", "panel")])


def snap(fl, x, y):
    """Nearest wall face to a point inside a room: (point on the face, unit normal back into the room)."""
    p = nearest_points(solid(fl).boundary, Point(x, y))[0]; dx, dy = x - p.x, y - p.y
    return (p.x, p.y), ((1 if dx > 0 else -1, 0) if abs(dx) > abs(dy) else (0, 1 if dy > 0 else -1))


def wall_runs(fl, r):
    """Unbroken wall space of a room (NEC 210.52(A)(2): measured around corners, broken by doors, openings and fixed cabinets).
    Runs of samples (x, y, nx, ny) every 0.1 ft, n pointing into the room."""
    U = unary_union([box(*q_) for q_ in r["rects"]]).buffer(.12, join_style=2).buffer(-.12, join_style=2)
    S, G, F = solid(fl), gaps(fl), fxboxes(fl); allruns = []
    for P in (U.geoms if hasattr(U, "geoms") else [U]):
        P = orient(P, 1.0); c = list(P.exterior.coords); runs, cur, first = [], [], None
        for (x0, y0), (x1, y1) in zip(c[:-1], c[1:]):
            d = math.hypot(x1 - x0, y1 - y0)
            if d < 1e-6: continue
            ux, uy = (x1 - x0) / d, (y1 - y0) / d; nx, ny = -uy, ux
            for t in np.arange(.05, d, .1):
                x, y = x0 + ux * t, y0 + uy * t
                ok = S.distance(Point(x - nx * .2, y - ny * .2)) < .3 and not G.contains(Point(x, y)) and not F.contains(Point(x + nx * .25, y + ny * .25))
                first = ok if first is None else first
                if ok: cur.append((x, y, nx, ny))
                elif cur: runs.append(cur); cur = []
        if cur:
            if first and runs: runs[0] = cur + runs[0]
            else: runs.append(cur)
        allruns += runs
    return allruns


def place(run, spacing):
    """Receptacles along one run so no point is more than spacing/2 from one; kept 0.6 ft or more off corners."""
    n = len(run); k = max(1, math.ceil(n * .1 / spacing)); out = []
    for i in range(k):
        j = int((i + .5) * n / k)
        for s in (0, 7, -7, 14, -14, 21, -21):
            qq = j + s
            if 0 <= qq < n and all(run[min(max(qq + e, 0), n - 1)][2:] == run[qq][2:] for e in (-6, 6)):
                j = qq; break
        out.append(run[j])
    return out


def back(box_, rect):
    """Which side of a room rectangle a cabinet or appliance backs onto: (wall coordinate, normal into the room, axis along the wall)."""
    x0, y0, x1, y1 = box_; X0, Y0, X1, Y1 = rect
    c = [(abs(x0 - X0), (x0, (1, 0), 1)), (abs(X1 - x1), (x1, (-1, 0), 1)), (abs(y0 - Y0), (y0, (0, 1), 0)), (abs(Y1 - y1), (y1, (0, -1), 0))]
    return min(c, key=lambda t: t[0])[1]


def room_of(fl, x, y):
    return min(b.LV[fl]["rooms"], key=lambda r: min(box(*q_).distance(Point(x, y)) for q_ in r["rects"]))


def ext_face(fl, x=None, y=None, side="y-"):
    """Outside face of the exterior wall crossing the vertical line x (side y-, east) or horizontal line y (side x+, north / x-, south)."""
    S = solid(fl)
    if side == "y-":
        g = S.intersection(LineString([(x, -6), (x, 10)])); return min(p[1] for p in (g.geoms if hasattr(g, "geoms") else [g]) for p in p.coords)
    g = S.intersection(LineString([(-6, y), (40, y)])); pts = [p[0] for p in (g.geoms if hasattr(g, "geoms") else [g]) for p in p.coords]
    return max(pts) if side == "x+" else min(pts)


# ---------------------------------------------------------------------------------------------- design data per level
# Switches: room -> ("door", tag) for the latch side of that door, inside the room it opens into; or a point inside the room near the wall
# wanted (snapped to the nearest wall face). Extra gangs: "EX" exterior light, "UC" under-cabinet LEDs, "LD" laundry lights.
SW = {3: {"101": [("door", "100", ("EX",))], "102": [((15.2, 16.75), ("UC",))], "107": [((15.75, 15.6), ()), ((23.95, 12.4), ())],
          "103": [("door", "107", ())], "104": [("door", "102", ())], "106": [("door", "101", ())], "108": [("door", "106", ())], "105": [("door", "103", ())]},
      4: {"201": [("door", "200", ("EX",))], "202": [((20.1, 17.9), ("UC",))], "207": [((10.6, 13.2), ())], "210": [((19.1, 17.3), ())], "209": [((17.5, 14.6), ())],
          "208": [((12.6, 10.15), ())], "203": [("door", "206", ())], "204": [("door", "201", ())], "205": [("door", "205", ())], "206": [("door", "202", ())],
          "213": [("door", "208", ("EX",))]},
      5: {"301": [((11.3, 17.4), ("KT", "UC", "LD"))], "306": [((16.95, 19.0), ("ST",)), ((23.4, 14.2), ())], "312": [((23.5, 20.6), ())],
          "303": [("door", "305", ())], "304": [("door", "301", ())], "305": [("door", "306", ())], "307": [((20.6, 14.05), ())]},
      6: {"401": [("door", "404", ())], "402": [("door", "403", ())], "403": [("door", "401", ())], "404": [("door", "402", ())], "405": [((17.3, 17.9), ())]}}
THREE_WAY = {(3, "107"), (4, "207"), (4, "210"), (5, "306"), (4, "213"), (5, "312"), (6, "405")}
GROUP = {(4, "210"): (4, "207"), (5, "302"): (5, "301"), (5, "308"): (5, "301")}          # lights switched from another room's switch
EXT = {3: [("100", "EX"), ("100", "WP")], 4: [("200", "EX"), ("200", "WP"), ("208", "EX"), ("208", "WP")]}
SMOKE = {3: [("SD", "103"), ("SD", "104"), ("SC", "107")], 4: [("SD", "203"), ("SD", "204"), ("SC", "207"), ("SC", "210"), ("SD", "213")],
         5: [("SD", "303"), ("SD", "304"), ("SC", "306")], 6: [("SD", "401"), ("SD", "402"), ("SC", "405")]}
DATA = {3: ["101", "103", "104"], 4: ["201", "203", "204"], 5: ["301", "303", "304"], 6: ["401", "402"]}
SPACING = {"bed": 10.0, "living": 10.0}


def dev(k, x, y, n=(0, 1), flat="A", ckt="", **kw):
    d = dict(k=k, x=x, y=y, n=n, flat=flat, ckt=ckt); d.update(kw); return d


def door_switch(fl, tag):
    d = next(d for d in b.LV[fl]["doors"] if d[0] == tag)
    _t, axis, w, a0, a1, hinge, swing = d[:7]
    for along in ((a1 + .5) if hinge == "lo" else (a0 - .5), (a1 + .8) if hinge == "lo" else (a0 - .8), (a0 - .5) if hinge == "lo" else (a1 + .5)):
        x, y = ((along, w + swing * .55) if axis == "h" else (w + swing * .55, along))
        (px, py), n = snap(fl, x, y)
        if not gaps(fl).contains(Point(px + n[0] * .1, py + n[1] * .1)) and math.dist((px, py), (x, y)) < 1.0:
            return (px, py), n
    return snap(fl, x, y)


def counter_runs(fl, r):
    """Kitchen counter runs: [(wall coordinate, normal, axis, s0, s1, sink centre or None)] from the base cabinets, dishwasher and sink base."""
    rect = r["rects"][0]; boxes = [f for f in b.LV[fl]["fx"] if f[0] in ("base", "dw", "sinkbase") and box(*f[1:5]).intersects(box(*rect))]
    groups = {}
    for f in boxes:
        w, n, ax_ = back(f[1:5], rect); key = (round(w, 1), n)
        groups.setdefault(key, []).append(f)
    runs = []
    for (w, n), fs in groups.items():
        ax_ = 1 if n[0] else 0
        iv = sorted((f[1 + ax_], f[3 + ax_], f) for f in fs); cur = None
        for s0, s1, f in iv:
            if cur and s0 <= cur[1] + .05: cur = [cur[0], max(cur[1], s1), cur[2] + [f]]
            else:
                if cur: runs.append((w, n, ax_, cur[0], cur[1], cur[2]))
                cur = [s0, s1, [f]]
        if cur: runs.append((w, n, ax_, cur[0], cur[1], cur[2]))
    out = []
    for w, n, ax_, s0, s1, fs in runs:
        sink = next(((f[1 + ax_] + f[3 + ax_]) / 2 for f in fs if f[0] == "sinkbase"), None)
        out.append((w, n, ax_, s0, s1, sink, fs))
    return out


def level_devices(fl):
    """Everything electrical drawn on one level: devices, switch groups (switch -> lights), smoke alarms, data outlets."""
    L = b.LV[fl]; D = []; legs = []
    rooms = {r["no"]: r for r in L["rooms"]}
    # -------------------------------------------------- ceiling lights (lumen-method layout) and bath fan / mirror
    lights = {}
    for r in q.lit_rooms(fl):
        fa = flat_of(fl, r); items, credit = q.layout(fl, r); lights[r["no"]] = []
        for t, x, y in items:
            d = dev(t, x, y, flat=fa, ckt=lt_key(fl, r), room=r["no"]); D.append(d); lights[r["no"]].append(d)
        if r["kind"] == "bath":
            van = next(f for f in L["fx"] if f[0] == "van" and any(box(*f[1:5]).intersects(box(*q_)) for q_ in r["rects"]))
            rect = next(q_ for q_ in r["rects"] if box(*van[1:5]).intersects(box(*q_)))
            w, n, ax_ = back(van[1:5], rect); c = ((van[1] + van[3]) / 2, (van[2] + van[4]) / 2)
            mp = (w, c[1]) if ax_ == 1 else (c[0], w); half = ((van[4] - van[2]) if ax_ == 1 else (van[3] - van[1])) / 2
            md = dev("M", *mp, n=n, flat=fa, ckt="BA-" + r["no"], room=r["no"], half=half); D.append(md)
            tub = next((f for f in L["fx"] if f[0] == "tub" and any(box(*f[1:5]).intersects(box(*q_)) for q_ in r["rects"])), None)
            wc = next((f for f in L["fx"] if f[0] == "wc" and any(box(f[1] - .3, f[2] - .3, f[1] + .3, f[2] + .3).intersects(box(*q_).buffer(.2)) for q_ in r["rects"])), None)
            cl = next(d for d in lights[r["no"]] if d["k"] == "C")
            if tub and wc:
                tc = ((tub[1] + tub[3]) / 2, (tub[2] + tub[4]) / 2); wx, wy = wc[1], wc[2]
                fx_, fy = (tc[0] + wx) / 2, (tc[1] + wy) / 2
            else:
                fx_, fy = cl["x"] + 1.4, cl["y"]
            if math.dist((fx_, fy), (cl["x"], cl["y"])) < 1.3:
                ang = math.atan2(fy - cl["y"], fx_ - cl["x"]) if (fx_, fy) != (cl["x"], cl["y"]) else 0
                fx_, fy = cl["x"] + 1.4 * math.cos(ang), cl["y"] + 1.4 * math.sin(ang)
            fd = dev("F", fx_, fy, flat=fa, ckt="BA-" + r["no"], room=r["no"]); D.append(fd)
            # GFCI receptacle beside the vanity, within 3 ft of the basin (210.52(D))
            best = None
            for sgn in (1, -1):
                t = (c[1] if ax_ == 1 else c[0]) + sgn * (half + .45)
                p = (w, t) if ax_ == 1 else (t, w)
                inside = any(box(*q_).buffer(.05).contains(Point(p[0] + n[0] * .3, p[1] + n[1] * .3)) for q_ in r["rects"])
                clear = not fxboxes(fl).contains(Point(p[0] + n[0] * .3, p[1] + n[1] * .3)) and not gaps(fl).contains(Point(*p))
                if inside and clear: best = p; break
            if best is None:
                for sgn in (-1, 1):
                    t = (c[1] if ax_ == 1 else c[0]) + sgn * (half - .2); p = (w, t) if ax_ == 1 else (t, w)
                    if not gaps(fl).contains(Point(*p)): best = p; break
                if best is None: best = (w, c[1] - half + .2) if ax_ == 1 else (c[0] - half + .2, w)
            D.append(dev("G", *best, n=n, flat=fa, ckt="BA-" + r["no"], room=r["no"]))
    # -------------------------------------------------- switches and legs
    for no, specs in SW.get(fl, {}).items():
        r = rooms[no]; fa = flat_of(fl, r)
        grp = [no] + [k_[1] for k_, v in GROUP.items() if v == (fl, no)]
        three = (fl, no) in THREE_WAY or (fl, no) in [v for k_, v in GROUP.items() if k_ in THREE_WAY]
        for spec in specs:
            if spec[0] == "door": (px, py), n = door_switch(fl, spec[1]); extra = spec[2]
            else: (px, py), n = snap(fl, *spec[0]); extra = spec[1]
            gang = ["S3" if three else ("DIM" if r["kind"] in ("bed", "living") else "S")]
            if r["kind"] == "bath": gang = ["S", "S", "FT"]
            gang += [{"EX": "S", "UC": "S", "LD": "S", "KT": "DIM", "ST": "S3"}[e] for e in extra]
            sd = dev("S", px, py, n=n, flat=fa, ckt=lt_key(fl, r), room=no, gang=gang); D.append(sd)
            tgt = [d for g_ in grp for d in lights.get(g_, [])] + ([d for d in lights.get("302", [])] if fl == 5 and no == "301" else [])
            if fl == 5 and no == "312":
                tgt = lights.get("312", [])
            if tgt:
                near = min(tgt, key=lambda d: math.dist((d["x"], d["y"]), (px, py))); legs.append(((px, py), (near["x"], near["y"]), no))
    # chain the lights of each room (and its grouped rooms) together
    for no, ls in lights.items():
        if len(ls) < 2: continue
        rest = ls[:]; cur = rest.pop(0)
        while rest:
            nx_ = min(rest, key=lambda d: math.dist((d["x"], d["y"]), (cur["x"], cur["y"]))); rest.remove(nx_)
            legs.append(((cur["x"], cur["y"]), (nx_["x"], nx_["y"]), no)); cur = nx_
    # -------------------------------------------------- general receptacles (210.52(A)), hall receptacle (210.52(H))
    for r in L["rooms"]:
        fa = flat_of(fl, r); k = r["kind"]
        if k in SPACING:
            for run in wall_runs(fl, r):
                if len(run) < 20: continue                              # wall space under 2 ft needs no receptacle
                for x, y, nx, ny in place(run, SPACING[k]):
                    D.append(dev("R", x, y, n=(nx, ny), flat=fa, ckt=("BR-" + r["no"]) if k == "bed" else "LIV", room=r["no"]))
        if k in ("hall", "stair") and sum((q_[2] - q_[0]) * (q_[3] - q_[1]) for q_ in r["rects"]) >= 30 and r["no"] not in ("312", "405"):
            runs = sorted(wall_runs(fl, r), key=len, reverse=True)
            if runs and len(runs[0]) >= 20:
                x, y, nx, ny = runs[0][len(runs[0]) // 2]
                D.append(dev("R", x, y, n=(nx, ny), flat=fa, ckt="LIV" if fa != "C" or fl == 5 else "LT2", room=r["no"]))
    # -------------------------------------------------- kitchen: counters, fridge, range, microwave-hood, dishwasher
    for r in L["rooms"]:
        if r["kind"] != "kitchen": continue
        fa = flat_of(fl, r); rect = r["rects"][0]; n_sa = q.FLATS[fa]["sa"]; ct = 0; pts = []
        for w, n, ax_, s0, s1, sink, fs in counter_runs(fl, r):
            ln = s1 - s0
            if ln < 1.0: continue
            k = max(1, math.ceil(ln / 4.0)); ts = [s0 + (i + .5) * ln / k for i in range(k)]
            if sink is not None:
                ts = [(sink - 1.0 if t < sink else sink + 1.0) if abs(t - sink) < 1.0 else t for t in ts]
                ts = [min(max(t, s0 + .35), s1 - .35) for t in ts]
            for t in ts: pts.append(((w, t) if ax_ == 1 else (t, w), n))
        pts.sort(key=lambda p: (p[0][0], p[0][1]))
        for p, n in pts:
            D.append(dev("G", *p, n=n, flat=fa, ckt=f"CT{ct % n_sa + 1}", room=r["no"])); ct += 1
        if fl == 3:     # a fourth small-appliance outlet for an appliance cart: the free wall beside the fridge
            (px, py), n = snap(fl, 13.9, 16.7); D.append(dev("G", px, py, n=n, flat=fa, ckt=f"CT{ct % n_sa + 1}", room=r["no"]))
        for f in L["fx"]:
            if f[0] not in ("fridge", "range", "sinkbase") or not box(*f[1:5]).intersects(box(*rect)): continue
            w, n, ax_ = back(f[1:5], rect); c = ((f[1] + f[3]) / 2, (f[2] + f[4]) / 2); p = (w, c[1]) if ax_ == 1 else (c[0], w)
            if f[0] == "fridge": D.append(dev("D", *p, n=n, flat=fa, ckt="FR", room=r["no"], lab="REF"))
            if f[0] == "range":
                D.append(dev("Q", *p, n=n, flat=fa, ckt="RNG", room=r["no"], lab="50A"))
                o = .75; p2 = (w, c[1] + o) if ax_ == 1 else (c[0] + o, w)
                D.append(dev("D", *p2, n=n, flat=fa, ckt="MW", room=r["no"], lab="MW", high=True))
        for f in L["fx"]:
            if f[0] != "dw" or not box(*f[1:5]).intersects(box(*rect)): continue
            w, n, ax_ = back(f[1:5], rect); sk = next((g_ for g_ in L["fx"] if g_[0] == "sinkbase" and box(*g_[1:5]).intersects(box(*rect))), None)
            lo, hi = (f[2], f[4]) if ax_ == 1 else (f[1], f[3]); sc = (((sk[2] + sk[4]) / 2) if ax_ == 1 else ((sk[1] + sk[3]) / 2)) if sk else hi + 1
            t = hi + .5 if sc > (lo + hi) / 2 else lo - .5; p3 = (w, t) if ax_ == 1 else (t, w)
            D.append(dev("D", *p3, n=n, flat=fa, ckt="DW", room=r["no"], lab="DW"))
    # -------------------------------------------------- laundry, mechanical
    for f in L["fx"]:
        k = f[0]
        if k not in ("washer", "dryer", "wdstack", "furnace", "wh"): continue
        if k == "wh":
            r = room_of(fl, f[1], f[2]); (px, py), n = snap(fl, f[1], f[2]); fa = flat_of(fl, r)
            D.append(dev("D", px, py, n=n, flat=fa, ckt="MECH", room=r["no"], lab="WH")); continue
        cx, cy = (f[1] + f[3]) / 2, (f[2] + f[4]) / 2; r = room_of(fl, cx, cy); fa = flat_of(fl, r)
        rect = next((q_ for q_ in r["rects"] if box(*f[1:5]).intersects(box(*q_))), r["rects"][0])
        w, n, ax_ = back(f[1:5], rect); p = (w, cy) if ax_ == 1 else (cx, w)
        if k == "washer": D.append(dev("D", *p, n=n, flat=fa, ckt="WSH", room=r["no"], lab="W"))
        if k == "dryer": D.append(dev("Q", *p, n=n, flat=fa, ckt="DRY", room=r["no"], lab="30A"))
        if k == "wdstack":
            o = .55; D.append(dev("D", *((w, cy - o) if ax_ == 1 else (cx - o, w)), n=n, flat=fa, ckt="WSH", room=r["no"], lab="W"))
            D.append(dev("Q", *((w, cy + o) if ax_ == 1 else (cx + o, w)), n=n, flat=fa, ckt="DRY", room=r["no"], lab="30A"))
        if k == "furnace":
            lx = (f[3] - f[1]) > (f[4] - f[2]); D.append(dev("J", cx + (.75 if lx else 0), cy + (0 if lx else .75), flat=fa, ckt="FUR", room=r["no"], lab="FURN"))
    # -------------------------------------------------- panels
    for f in L["fx"]:
        if f[0] == "panel":
            x0, y0, x1, y1 = f[1:5]; n = (f[5], 0) if x0 == x1 else (0, f[5]); r = room_of(fl, (x0 + x1) / 2 + n[0], (y0 + y1) / 2 + n[1])
            D.append(dev("P", (x0 + x1) / 2, (y0 + y1) / 2, n=n, flat=FLAT_OF[fl], ckt="", room=r["no"], half=max(abs(x1 - x0), abs(y1 - y0)) / 2))
    # -------------------------------------------------- exterior lights and receptacles at the entrances
    for tag, k in EXT.get(fl, []):
        d = next(d_ for d_ in L["doors"] if d_[0] == tag); _t, axis, w, a0, a1, hinge, swing = d[:7]
        fa = "C" if (fl == 4 and tag == "208") else FLAT_OF[fl]
        along = (a1 + .7 if hinge == "lo" else a0 - .7) if k == "EX" else (a0 - 1.3 if hinge == "lo" else a1 + 1.3)
        x, y = (w - swing * 1.2, along) if axis == "v" else (along, w - swing * 1.2)
        (px, py), n = snap(fl, x, y)
        D.append(dev(k, px, py, n=n, flat=fa, ckt=("LT" if fa != "C" else "LT2") if k == "EX" else "EXT", room="ext"))
    # -------------------------------------------------- smoke / CO alarms and data outlets
    for k, no in SMOKE.get(fl, []):
        r = rooms[no]; fa = flat_of(fl, r); x0, y0, x1, y1 = r["rects"][0]; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        occupied = [(d["x"], d["y"]) for d in D if d.get("room") == no and d["k"] in ("R6", "C", "R6W")]
        cand = [(cx, cy)] + [(cx + dx, cy + dy) for dx, dy in ((1.3, 0), (-1.3, 0), (0, 1.3), (0, -1.3), (1.0, 1.0), (-1.0, -1.0))]
        p = max(cand, key=lambda c_: min([math.dist(c_, o) for o in occupied] or [9]))
        D.append(dev(k, *p, flat=fa, ckt=lt_key(fl, r), room=no))
    for no in DATA.get(fl, []):
        r = rooms[no]; fa = flat_of(fl, r)
        fz = [f for f in L["furn"] if f[0] in ("desk", "tv") and any(box(*f[1:5]).intersects(box(*q_)) for q_ in r["rects"])]
        if fz: f = fz[0]; tx, ty = (f[1] + f[3]) / 2, (f[2] + f[4]) / 2
        else: tx, ty = r["lab"]
        (px, py), n = snap(fl, tx, ty)
        px += (n[1] * .9); py += (n[0] * .9)
        D.append(dev("T", px, py, n=n, flat=fa, ckt="", room=no))
    return D, legs


def lt_key(fl, r):
    fa = flat_of(fl, r)
    if fa == "C": return "LT2" if (fl == 6 or r["no"] in ("213", "312")) else "LT1"
    return "LT"


# ---------------------------------------------------------------------------------------------- circuits and panel schedules
PROT = {"basement": "A"}         # the lower flat is partly below grade: basement GFCI rule 210.8(A)(5) for its receptacles


def room_name(no):
    for fl in (3, 4, 5, 6):
        for r in b.LV[fl]["rooms"]:
            if r["no"] == no: return r["name"].split(" (")[0]
    return no


def circuit_def(fa, key, devs):
    """(description, load VA, breaker A, poles, wire, protection) for one circuit key."""
    ac = q.AC[fa]; f = q.FLATS[fa]; base = fa == "A"
    nrec = sum(1 for d in devs if d["k"] in ("R", "G", "D", "WP"))
    W = sum(q.FIXT[d["k"]][2] for d in devs if d["k"] in q.FIXT) + sum(60 for d in devs if d["k"] == "M") + sum(50 for d in devs if d["k"] == "F") + \
        sum(15 for d in devs if d["k"] in ("EX",)) + sum(5 for d in devs if d["k"] in ("SD", "SC"))
    if key == "RNG": return ("Range, 240 V receptacle (NEMA 14-50)", q.APPL["range"][1], 50, 2, "6/3 NM-B Cu", "GFCI")
    if key == "DRY": return ("Dryer, 240 V receptacle (NEMA 14-30)", q.APPL["dryer"][1], 30, 2, "10/3 NM-B Cu", "GFCI")
    if key == "AC": return (f"Air conditioner {ac['ton']:g} ton, MCA {ac['mca']:g} A", ac["mca"] * q.V, ac["mocp"], 2, {15: "14", 20: "12", 30: "10"}[ac["mocp"]] + " Cu, conduit outdoors", "GFCI *")
    if key.startswith("CT"): return (f"Kitchen counter receptacles {key[2]} of {f['sa']}", 1500, 20, 1, "12/2 NM-B", "DF")
    if key == "FR": return ("Refrigerator", q.APPL["fridge"][1], 20, 1, "12/2 NM-B", "DF")
    if key == "DW": return ("Dishwasher", q.APPL["dw"][1], 20, 1, "12/2 NM-B", "DF")
    if key == "MW": return ("Microwave / hood over the range", q.APPL["mw"][1], 20, 1, "12/2 NM-B", "DF")
    if key == "WSH": return ("Washer", 1500, 20, 1, "12/2 NM-B", "DF")
    if key.startswith("BA-"): return (f"{room_name(key[3:])} ({key[3:]}): recept., light, mirror, fan", 1500, 20, 1, "12/2 NM-B", "GFCI")
    if key.startswith("BR-"): return (f"{room_name(key[3:])} ({key[3:]}) receptacles", 180 * nrec, 20, 1, "12/2 NM-B", "DF" if base else "AFCI")
    if key == "LIV": return ("Living room and hall receptacles", 180 * nrec, 20, 1, "12/2 NM-B", "DF" if base else "AFCI")
    if key in ("LT", "LT1", "LT2"):
        what = {"LT": "Lighting, smoke / CO alarms, entrance light", "LT1": "Lighting main floor, smoke / CO alarms", "LT2": "Lighting attic, stairs, entrance hall, smoke"}[key]
        return (what, W + (180 * nrec), 15, 1, "14/2 NM-B", "DF" if base else "AFCI")
    if key == "FUR": return ("Gas furnace (service switch at the unit)", (ac["blower"] + 1.0) * 120, 15, 1, "14/2 NM-B", "AFCI")
    if key == "MECH": return ("Water heater vent fan, service receptacle", q.APPL["whv"][1] + 180, 20, 1, "12/2 NM-B", "DF" if base else "AFCI")
    if key == "EXT": return ("Outdoor receptacles" + (", HVAC service receptacle" if fa == "A" else ""), 180 * max(1, nrec), 20, 1, "12/2 NM-B / UF", "GFCI")
    return (key, 0, 20, 1, "12/2", "")


ORDER = ["RNG", "DRY", "AC", "CT1", "CT2", "CT3", "CT4", "FR", "DW", "MW", "WSH"]


@lru_cache(None)
def all_devices():
    return {fl: level_devices(fl) for fl in (3, 4, 5, 6)}


def extra_devices():
    """Devices outside the plans' rooms: condensers, their disconnects, the HVAC service receptacle (drawn on E-101 and E-004)."""
    return [dev("AC", 0, 0, flat=k, ckt="AC") for k in q.FLATS] + [dev("WP", 0, 0, flat="A", ckt="EXT", room="hvac")]


@lru_cache(None)
def schedules():
    """Panel schedules: {flat: [(position(s), key, desc, VA, breaker, poles, wire, prot, phase VA (A, B))]}."""
    by = {k: {} for k in q.FLATS}
    for fl, (D, _l) in all_devices().items():
        for d in D:
            if d["ckt"]: by[d["flat"]].setdefault(d["ckt"], []).append(d)
    for d in extra_devices(): by[d["flat"]].setdefault(d["ckt"], []).append(d)
    for k in q.FLATS:
        for key in ("RNG", "DRY", "AC", "FR", "DW", "MW", "WSH", "FUR", "MECH", "EXT"): by[k].setdefault(key, [])
    out = {}
    for k, cs in by.items():
        keys = sorted(cs, key=lambda c: (ORDER.index(c) if c in ORDER else 50, c))
        two = [c for c in keys if circuit_def(k, c, cs[c])[3] == 2]; one = [c for c in keys if c not in two]
        rows, pos, ph = [], 1, [0.0, 0.0]
        for c in two:
            dsc, va, br, po, wi, pr = circuit_def(k, c, cs[c]); rows.append((f"{pos},{pos + 2}", c, dsc, va, br, po, wi, pr)); ph[0] += va / 2; ph[1] += va / 2; pos += 4
        free = sorted(set(range(2, 61, 2)) | set(range(pos, 61, 2)))
        for c in sorted(one, key=lambda c: -circuit_def(k, c, cs[c])[1]):
            dsc, va, br, po, wi, pr = circuit_def(k, c, cs[c])
            want = 0 if ph[0] <= ph[1] else 1
            p_ = next((p for p in free if ((p - 1) // 2) % 2 == want), free[0]); free.remove(p_)
            ph[((p_ - 1) // 2) % 2] += va; rows.append((str(p_), c, dsc, va, br, po, wi, pr))
        rows.sort(key=lambda r_: int(r_[0].split(",")[0]))
        out[k] = (rows, ph)
    return out


def ckt_no(flat, key):
    rows, _ph = schedules()[flat]
    for r in rows:
        if r[1] == key: return f"{flat}{r[0].split(',')[0]}" if "," not in r[0] else f"{flat}{r[0].replace(',', '/')}"
    return flat + "?"


# ---------------------------------------------------------------------------------------------- symbols (s = 1 on a plan in feet; 0.25 on the sheet in inches)
def sym(a, d, s=1.0, z=12):
    k, x, y = d["k"], d["x"], d["y"]; nx, ny = d["n"]; tx, ty = -ny, nx; cx, cy = x + nx * .32 * s, y + ny * .32 * s
    if k in ("R", "G", "D", "WP"):
        a.add_patch(Circle((cx, cy), .27 * s, fc=PW if k == "D" else "white", ec=PW, lw=.7, zorder=z))
        if k in ("G", "WP"): a.text(cx, cy - .01 * s, "G" if k == "G" else "W", fontsize=3.4 * (s if s < 1 else 1) / (.25 if s < 1 else 1) if False else 3.4, color=PW, ha="center", va="center", fontweight="bold", zorder=z + 1)
        for e in ((-.1, .1) if k in ("R",) else ()):
            a.plot([x + tx * e * s, x + tx * e * s + nx * .66 * s], [y + ty * e * s, y + ty * e * s + ny * .66 * s], color=PW, lw=.55, zorder=z + .5, solid_capstyle="butt")
        if k == "WP": a.add_patch(Rectangle((cx - .36 * s, cy - .36 * s), .72 * s, .72 * s, fill=False, ec=PW, lw=.5, zorder=z))
    elif k == "Q":
        a.add_patch(MPoly([(x + tx * .26 * s, y + ty * .26 * s), (x - tx * .26 * s, y - ty * .26 * s), (x + nx * .5 * s, y + ny * .5 * s)], closed=True, fc=PW, ec=PW, lw=.5, zorder=z))
    elif k == "J":
        a.add_patch(Rectangle((x - .26 * s, y - .26 * s), .52 * s, .52 * s, fc="white", ec=HV, lw=.8, zorder=z))
        a.text(x, y - .01 * s, "J", fontsize=3.4, color=HV, ha="center", va="center", fontweight="bold", zorder=z + 1)
    elif k == "P":
        h = d.get("half", .6)
        a.add_patch(MPoly([(x + tx * e * s - nx * dd * s, y + ty * e * s - ny * dd * s) for e, dd in ((-h, -.05), (h, -.05), (h, .3), (-h, .3))], closed=True, fc=FD, ec=FD, lw=.5, zorder=z))
    elif k == "S":
        g = d.get("gang", ["S"]); lab = "".join(g) if len(g) == 1 else f"{len(g)}G"
        a.add_patch(Circle((cx, cy), .2 * s, fc=LT, ec="white", lw=.3, zorder=z))
        a.text(cx + nx * .55 * s, cy + ny * .55 * s, " ".join(g), fontsize=3.4, color=LT, ha="center", va="center", fontweight="bold", zorder=z + 1, path_effects=HALO)
    elif k in ("R6", "R6W"):
        a.add_patch(Circle((x, y), .24 * s, fc="white", ec=LT, lw=.75, zorder=z)); a.add_patch(Circle((x, y), .08 * s, fc=LT, ec=LT, lw=.3, zorder=z + .1))
        if k == "R6W": a.add_patch(Circle((x, y), .36 * s, fc="none", ec=LT, lw=.4, ls=(0, (1.5, 1)), zorder=z))
    elif k in ("C", "CL"):
        r_ = (.32 if k == "C" else .22) * s
        for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            a.plot([x + dx * r_, x + dx * r_ * 1.5], [y + dy * r_, y + dy * r_ * 1.5], color=LT, lw=.6, zorder=z)
        a.add_patch(Circle((x, y), r_, fc="white", ec=LT, lw=.75, zorder=z))
        if k == "CL": a.text(x, y, "M", fontsize=2.8, color=LT, ha="center", va="center", fontweight="bold", zorder=z + 1)
    elif k == "M":
        h = d.get("half", .9) * .72
        a.add_patch(MPoly([(x + tx * e * s + nx * dd * s, y + ty * e * s + ny * dd * s) for e, dd in ((-h, .04), (h, .04), (h, .2), (-h, .2))], closed=True, fc="#fde3c4", ec=LT, lw=.7, zorder=z))
        a.text(x + nx * .48 * s, y + ny * .48 * s, "LED MIRROR", fontsize=2.9, color=LT, ha="center", va="center", zorder=z + 1, rotation=0 if nx == 0 else 90, path_effects=HALO)
    elif k == "F":
        a.add_patch(Rectangle((x - .36 * s, y - .36 * s), .72 * s, .72 * s, fc="white", ec=HV, lw=.75, zorder=z))
        for e in (-.18, 0, .18): a.plot([x - .24 * s, x + .24 * s], [y + e * s, y + e * s], color=HV, lw=.4, zorder=z + .1)
    elif k == "EX":
        a.add_patch(MPoly([(x + tx * .3 * s, y + ty * .3 * s), (x - tx * .3 * s, y - ty * .3 * s), (x - tx * .3 * s + nx * .3 * s, y - ty * .3 * s + ny * .3 * s),
                           (x + tx * .3 * s + nx * .3 * s, y + ty * .3 * s + ny * .3 * s)], closed=True, fc="white", ec=LT, lw=.75, zorder=z))
        a.add_patch(Circle((x + nx * .3 * s, y + ny * .3 * s), .14 * s, fc=LT, ec=LT, zorder=z + .1))
    elif k in ("SD", "SC"):
        w = (.42 if k == "SD" else .62) * s
        a.add_patch(Rectangle((x - w, y - .27 * s), 2 * w, .54 * s, fc="white", ec=LS, lw=.8, zorder=z + 2))
        a.text(x, y - .01 * s, "SD" if k == "SD" else "SD/CO", fontsize=3.3, color=LS, ha="center", va="center", fontweight="bold", zorder=z + 3)
    elif k == "T":
        a.add_patch(MPoly([(x - .27 * s, y + .22 * s), (x + .27 * s, y + .22 * s), (x, y - .25 * s)], closed=True, fc="white", ec="#444", lw=.7, zorder=z))
    elif k == "AC":
        a.add_patch(Rectangle((x - 1.25 * s, y - 1.25 * s), 2.5 * s, 2.5 * s, fc="#f3e9f7", ec=HV, lw=.8, zorder=z))
        a.add_patch(Circle((x, y), .9 * s, fc="none", ec=HV, lw=.5, zorder=z + .1))
    elif k == "X":
        a.add_patch(Rectangle((x - .3 * s, y - .3 * s), .6 * s, .6 * s, fc="white", ec=HV, lw=.8, zorder=z))
        a.text(x, y - .01 * s, "D", fontsize=3.4, color=HV, ha="center", va="center", fontweight="bold", zorder=z + 1)
    elif k == "MTR":
        for i in range(3):
            a.add_patch(Rectangle((x - 1.5 * s + i * s, y - .3 * s), s, .6 * s, fc="white", ec=FD, lw=.7, zorder=z))
            a.add_patch(Circle((x - 1.0 * s + i * s, y), .22 * s, fc="none", ec=FD, lw=.5, zorder=z + .1))


def leg(a, p, q_, rad=.22):
    a.add_patch(FancyArrowPatch(p, q_, connectionstyle=f"arc3,rad={rad}", arrowstyle="-", color=LT, lw=.45, ls=(0, (2.4, 1.8)), zorder=10, shrinkA=2.0, shrinkB=2.0))


LEG = [("R", "Duplex receptacle, 20 A (number = circuit)"), ("G", "GFCI receptacle, 20 A"), ("D", "Dedicated receptacle, one appliance"), ("WP", "Outdoor GFCI receptacle, in-use cover"),
       ("Q", "240 V receptacle: range 50 A, dryer 30 A"), ("J", "Hardwired: furnace (service switch at it)"), ("X", "A/C disconnect, outdoors"), ("P", "Panel (125 A main breaker)"),
       ("S", "Switch: S single, S3 3-way, DIM dimmer,\nFT bath fan timer / humidity control"), ("R6", "6 in. LED downlight"), ("R6W", "6 in. LED downlight, wet rated, over tub"),
       ("C", "LED flush ceiling fixture"), ("CL", "Closet LED, motion sensor (no switch)"), ("M", "LED mirror with anti-fog, hardwired"), ("F", "Bath exhaust fan, ducted outside"),
       ("EX", "Exterior wall light, dusk to dawn"), ("SD", "Smoke alarm, hardwired, interconnected"), ("SC", "Smoke and CO alarm, combined"), ("T", "Data / TV outlet (Cat 6 + coax)"),
       ("leg", "Switch leg: switch to its lights"), ("uc", "Under-cabinet LED strip")]


def legend(bg, x, y, fs=5.3, rh=.19):
    for k, txt in LEG:
        if k == "leg": leg(bg, (x, y - .02), (x + .36, y - .02), .35)
        elif k == "uc": bg.plot([x, x + .34], [y, y], color=LT, lw=1.6)
        else:
            d = dict(k=k, x=x + .17, y=y - (.07 if k in ("R", "G", "D", "WP", "Q", "EX", "M") else 0), n=(0, 1) if k != "S" else (1, 0), gang=["S3"], half=.9)
            if k == "S": d["x"] = x + .05
            sym(bg, d, s=.25)
        for i, ln in enumerate(txt.split("\n")):
            bg.text(x + .47, y - i * .12, ln, fontsize=fs, color=INK, va="center")
        y -= rh + .12 * txt.count("\n")
    return y


# ---------------------------------------------------------------------------------------------- plan sheets
def tag_positions(D, ax, fl, pre=()):
    """A circuit number beside each receptacle and one per room's lights, moved off other tags, symbols and texts already drawn."""
    placed = list(pre); out = []
    def free(x, y, w=.5, h=.26):
        bb = box(x - w / 2, y - h / 2, x + w / 2, y + h / 2)
        return not any(bb.intersects(p) for p in placed)
    for d in D:
        if d["k"] in ("R", "G", "D", "Q", "WP", "J", "X"):
            placed.append(Point(d["x"] + d["n"][0] * .32, d["y"] + d["n"][1] * .32).buffer(.3))
        elif d["k"] in ("R6", "R6W", "C", "CL", "F", "SD", "SC", "T", "S"):
            placed.append(Point(d["x"], d["y"]).buffer(.32))
    done_rooms = set()
    for d in D:
        k = d["k"]
        if k in ("R", "G", "D", "Q", "WP", "J"):
            t = ckt_no(d["flat"], d["ckt"]) + (f" {d['lab']}" if d.get("lab") else "")
            nx, ny = d["n"]; tx, ty = -ny, nx; w = .14 * len(t) + .1
            for off, side in ((1.05, 0), (1.05, .55), (1.05, -.55), (1.5, 0), (1.05, .95), (1.05, -.95), (1.9, 0), (1.5, .8), (1.5, -.8)):
                x, y = d["x"] + nx * off + tx * side, d["y"] + ny * off + ty * side
                if free(x, y, w):
                    placed.append(box(x - w / 2, y - .13, x + w / 2, y + .13)); out.append((x, y, t, PW)); break
        elif k in ("R6", "R6W", "C") and (d["room"], d["flat"]) not in done_rooms and d["ckt"]:
            done_rooms.add((d["room"], d["flat"])); t = ckt_no(d["flat"], d["ckt"]); w = .14 * len(t) + .1
            for dx, dy in ((0, -.6), (0, .6), (.65, 0), (-.65, 0), (.6, -.6), (-.6, .6)):
                x, y = d["x"] + dx, d["y"] + dy
                if free(x, y, w):
                    placed.append(box(x - w / 2, y - .13, x + w / 2, y + .13)); out.append((x, y, t, LT)); break
    return out, placed


def room_labels(fl, ax, placed):
    for r in b.LV[fl]["rooms"]:
        if r["kind"] == "closet" or q.skip(r): continue
        x0, y0, x1, y1 = r["rects"][0]; t = f"{r['name'].split(' (')[0]}  {r['no']}"; w = .135 * len(t) + .2
        cand = [r["lab"]] + [((x0 + x1) / 2 + dx * (x1 - x0) / 4, (y0 + y1) / 2 + dy * (y1 - y0) / 4) for dx in (0, -1, 1) for dy in (0, -1, 1, -1.5, 1.5)]
        for x, y in cand:
            bb = box(x - w / 2, y - .2, x + w / 2, y + .2)
            if not any(bb.intersects(p) for p in placed) and box(x0, y0, x1, y1).buffer(.2).contains(bb):
                ax.text(x, y, t, fontsize=3.6, color="#7a818a", ha="center", va="center", zorder=11, fontweight="bold"); placed.append(bb); break


def feeder_route(fl):
    """Feeder routes on each level, as polylines in plan feet (drawn heavy dashed): in the ceiling, or in the chase."""
    if fl == 3:
        mx, my = meter_pos(); fy = 2.95
        return [([(mx, my + .3), (mx, fy), (22.2, fy), (22.2, 2.55)], "A"), ([(22.2, fy), (21.0, fy), (21.0, 9.1), (18.35, 9.1)], "BC")]
    if fl == 4:
        return [([(16.7, 8.0), (16.7, 10.3), (16.3, 10.3), (16.3, 12.42)], "B"), ([(17.4, 7.2), (17.4, 6.4)], "C")]
    if fl == 5:
        return [([(16.4, 7.0), (16.4, 2.35), (15.45, 2.35)], "C")]
    return []


PANEL_NOTE = {3: ("PANEL A", (22.2, 3.25)), 4: ("PANEL B", (14.9, 12.4)), 5: ("PANEL C", (14.2, 2.35))}


def meter_pos():
    """Meter stack on the east wall, north end (the left side seen from Forest Ave): plan point outside the wall on level 3."""
    x = 29.4; return x, ext_face(3, x=x) - .55


def condensers():
    y0 = ext_face(3, x=21.0) - 2.4
    return {"A": (19.0, y0), "B": (22.0, y0), "C": (25.0, y0)}


KEYN = {3: [("Meter stack, 3 positions with a 125 A main breaker each, on the east wall at the north end (the left side seen from Forest Ave), where the meters are today. See E-004.", (29.4, -3.6)),
            ("Air conditioner condensers on pads, 12 in. off the wall: A lower, B middle, C upper flat. Disconnect (D) within sight of each; GFCI receptacle within 25 ft (210.63).", (22.0, -4.6)),
            ("Lower flat is partly below grade: its receptacles are GFCI protected as a basement (210.8(A)(5)); dual-function breakers.", (8.0, 8.4)),
            ("Old electrical panel in the old laundry: removed. Its cables are not reused.", (27.8, 10.3)),
            ("Feeders in the lower flat's ceiling: A to panel A; B and C to the point marked, under the chase, then up it (E-004).", (21.0, 10.6), (18.35, 9.1))],
        4: [("Feeder B rises in the old chimney chase and runs in the hall ceiling to panel B. Firestop the chase at every floor.", (18.6, 9.0)),
            ("Stair hall 213 belongs to the upper flat: its lights, receptacle and alarm are on panel C. 3-way at the door and at the top of the stair.", (25.0, 25.2)),
            ("Laundry recess: the washer and dryer receptacles stay open to the passage; no doors.", (21.2, 15.4))],
        5: [("Panel C on the living room wall. Feeder C comes up the chase and down the closet wall. Keep 30 x 36 in. clear in front; no furniture.", (12.6, 4.2)),
            ("Open kitchen / living / hall: one switch bank at the bath wall for living, kitchen, under-cabinet and laundry lights.", (11.6, 15.0)),
            ("Stair to the attic: 3-way switches at the bottom (here) and at the top (E-104); stair lights over the treads.", (22.6, 22.6))],
        6: [("Attic circuits are on panel C (main floor): cables come up the chase. Bath fans ducted to the outside through the gable or roof, not into the eave.", (17.3, 4.4)),
            ("Baths: LED anti-fog mirror on the vanity wall, light and fan on the ceiling; 3-gang switch at the door (light, mirror, fan timer).", (9.0, 13.0))]}


def plan_sheet(pdf, number, fl):
    L = b.LV[fl]; D, legs = all_devices()[fl]; fa = FLAT_OF[fl]
    title = {3: "Lower flat: power and lighting plan", 4: "Middle flat: power and lighting plan", 5: "Upper flat main floor: power and lighting plan", 6: "Attic: power and lighting plan"}[fl]
    notes = [("This sheet", [f"All devices, circuits and fixtures for {L['name'].lower()}." if fl < 5 else "Upper flat: all on panel C (main floor).",
                             "Number by each outlet = its circuit; one", "number per room for its lights. Schedules", "on E-005, loads on E-002, light on E-003.",
                             "Mounting: receptacles 16 in., counters 44 in.,", "switches 48 in. to the centre, panels 6 ft", "to the top breaker, alarms on the ceiling."]),
             ("Rules used", ["Receptacles: no point on a wall more than", "6 ft from one (210.52(A)); counters 2 ft", "(210.52(C)); bath within 3 ft of the basin.",
                             "Every kitchen counter outlet on its own", "20 A circuit in turn: two air fryers and a", "kettle can run at once.",
                             "AFCI / GFCI as in the schedules (E-005)."])]
    fig, bg, ax = b.bsheet(number, title, fl, notes, sub=f"Rear building · {L['name'].lower()}", view=VIEW[fl])
    b.draw_base(ax, fl, "trade", labels=False)
    for d in D: sym(ax, d)
    for p, q_, _no in legs: leg(ax, p, q_)
    # under-cabinet LED strips along the counter runs
    for r in L["rooms"]:
        if r["kind"] != "kitchen": continue
        for w, n, ax_, s0, s1, sink, fs in counter_runs(fl, r):
            d_ = 1.75
            if ax_ == 1: ax.plot([w + n[0] * d_] * 2, [s0 + .2, s1 - .2], color=LT, lw=1.4, zorder=9, solid_capstyle="butt")
            else: ax.plot([s0 + .2, s1 - .2], [w + n[1] * d_] * 2, color=LT, lw=1.4, zorder=9, solid_capstyle="butt")
    # exterior equipment on the lower flat sheet
    placed_extra = []
    if fl == 3:
        mx, my = meter_pos(); sym(ax, dict(k="MTR", x=mx, y=my, n=(0, -1)))
        ax.add_patch(Rectangle((mx - 1.5, my - 3.3), 3.0, 3.0, fill=False, ec=FD, lw=.5, ls=(0, (3, 2)), zorder=9))
        ax.text(mx, my - 2.0, "METERS\n3 x 125 A", fontsize=3.4, color=FD, ha="center", va="center", zorder=12, linespacing=1.1, fontweight="bold")
        for k, (cx, cy) in condensers().items():
            sym(ax, dict(k="AC", x=cx, y=cy, n=(0, 1))); ax.text(cx, cy, f"A/C {k}\n{q.AC[k]['ton']:g} ton", fontsize=3.2, color=HV, ha="center", va="center", zorder=13, linespacing=1.1)
            sym(ax, dict(k="X", x=cx - .9, y=cy + 1.75, n=(0, 1)))
            ax.text(cx + .4, cy + 1.75, ckt_no(k, "AC"), fontsize=3.4, color=PW, ha="center", va="center", fontweight="bold", zorder=14, path_effects=HALO)
        hx, hy = 26.9, ext_face(3, x=26.9); sym(ax, dict(k="WP", x=hx, y=hy, n=(0, -1)))
        ax.text(hx, hy - 1.05, ckt_no("A", "EXT"), fontsize=3.4, color=PW, ha="center", va="center", fontweight="bold", zorder=14, path_effects=HALO)
    for pts, lab in feeder_route(fl):
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color=FD, lw=1.6, ls=(0, (4, 1.6)), zorder=9.5, solid_capstyle="butt")
    if fl in PANEL_NOTE:
        t, (x, y) = PANEL_NOTE[fl]; ax.text(x, y, t, fontsize=4.0, color=FD, ha="center", va="center", fontweight="bold", zorder=14, path_effects=HALO)
    if fl in (4, 5):
        c = b.CHIMNEY
        ax.add_patch(Rectangle((c[0], c[1]), c[2] - c[0], c[3] - c[1], fill=False, ec=FD, lw=.6, ls=(0, (1.5, 1.5)), zorder=9.4))
    if fl == 3:                                    # feeders B and C turn up into the chase over the wet wall
        ax.add_patch(Circle((18.35, 9.1), .2, fc=FD, ec=FD, zorder=9.6))
    fig.canvas.draw(); rend = fig.canvas.get_renderer(); inv = ax.transData.inverted(); pre = []
    for t in ax.texts:
        bb = t.get_window_extent(rend); (u0, v0), (u1, v1) = inv.transform((bb.x0, bb.y0)), inv.transform((bb.x1, bb.y1))
        pre.append(box(min(u0, u1), min(v0, v1), max(u0, u1), max(v0, v1)))
    tags, placed = tag_positions(D, ax, fl, pre)
    for x, y, t, col in tags:
        ax.text(x, y, t, fontsize=3.5, color=col, ha="center", va="center", fontweight="bold", zorder=14, path_effects=HALO)
    room_labels(fl, ax, placed)
    for i, kn in enumerate(KEYN.get(fl, [])):
        b.keynote(ax, i + 1, *kn[1], col=FD, to=kn[2] if len(kn) > 2 else None)
    # right strip: legend, keynotes
    y = legend(bg, 10.6, 9.95) - .1
    bg.text(10.6, y, "KEYNOTES", fontsize=6.6, fontweight="bold", color=INK, va="center"); y -= .2
    for i, kn in enumerate(KEYN.get(fl, [])):
        t = kn[0]
        bg.text(10.68, y, str(i + 1), fontsize=5.4, color=FD, fontweight="bold", va="center", ha="center")
        for j, ln in enumerate(b.wrap(t, 56)):
            bg.text(10.85, y - j * .12, ln, fontsize=5.2, color=INK, va="center")
        y -= .12 * len(b.wrap(t, 56)) + .07
    bad = b.clarity(fig, ax, None, bg)
    print(number, "text clashes:", len(bad))
    for m in bad[:12]: print("   ", m)
    b.save(fig, number, pdf)


# ---------------------------------------------------------------------------------------------- schedules sheet
def sched_sheet(pdf):
    S = schedules()
    notes = [("Panels", ["Each flat: 125 A main-breaker load centre,", "120/240 V 1-phase 3-wire, copper bus, 30", "spaces (A, B) or 40 (C), Type 2 surge", "protector (230.67). Fed from its 125 A",
                         "meter-main at the stack. Neutral bar isolated", "from the can, ground bar bonded (250.24).", "Typed directory on the door (408.4)."]),
             ("Protection", ["AFCI: combination type (210.12).", "GFCI (210.8): baths, kitchen counters and", "within 6 ft of a sink, laundry incl. the", "dryer, dishwasher (210.8(D)), outdoors.",
                             "DF = dual function AFCI + GFCI breaker:", "used on all kitchen and laundry circuits.", "Lower flat treated as a basement (partly", "below grade): all its receptacles GFCI.",
                             "* A/C: 210.8(F) outdoor GFCI unless the", "inspector accepts an exception."]),
             ("Wire (copper)", ["14 AWG on 15 A, 12 on 20 A, 10 on 30 A,", "6 on the 50 A range. NM-B indoors; in", "conduit or UF outdoors."])]
    fig, bg, _ = b.bsheet("E-005", "Panel schedules", 0, notes, sub="Rear building · panels A, B, C")
    bg.text(.5, 10.25, "PANEL SCHEDULES · odd circuits on the left, even on the right; rows alternate legs A and B", fontsize=9.0, fontweight="bold", color=INK, va="center")
    wid = [.24, 1.78, .55, .4, .26, .4, .55, 1.78, .24]
    for k, (xx, yy) in (("A", (.5, 9.95)), ("B", (.5, 4.95)), ("C", (6.85, 9.95))):
        rows, ph = S[k]; f = q.FLATS[k]; nsp = 40 if k == "C" else 30
        info = {}
        for r in rows:
            ps = [int(p_) for p_ in r[0].split(",")]
            for j, p_ in enumerate(ps): info[p_] = (r, j)
        def cell(p_):
            if p_ not in info: return ["", "spare" if p_ <= nsp else "", "", ""]
            r, j = info[p_]
            if j: return [str(p_), "  (2nd pole)", "", f"{r[3] / 2:,.0f}"]
            return [str(p_), r[2][:46], f"{r[4]}A {r[5]}P {r[7]}".replace(" 1P", "").strip(), f"{r[3] / (2 if r[5] == 2 else 1):,.0f}"]
        T = [["Ckt", "Serves", "Breaker", "VA", "Leg", "VA", "Breaker", "Serves", "Ckt"]]
        for i in range(nsp // 2):
            L_ = cell(2 * i + 1); R_ = cell(2 * i + 2)
            T.append([L_[0], L_[1], L_[2], L_[3], "A" if i % 2 == 0 else "B", R_[3], R_[2], R_[1], R_[0]])
        dem = q.optional(k)[4]
        bg.text(xx, yy, f"PANEL {k} · {f['name'].split(' (')[0].upper()} · 125 A main breaker · {nsp} spaces · 120/240 V", fontsize=6.4, fontweight="bold", color=INK, va="center")
        y2 = table(bg, xx, yy - .12, wid, T, fs=4.5, rh=.142)
        bg.text(xx, y2 - .14, f"Connected: leg A {ph[0]:,.0f} VA, leg B {ph[1]:,.0f} VA, total {sum(ph):,.0f} VA.  Calculated load (E-002, 220.82): {dem:,.0f} VA = {dem / q.V:,.0f} A on a 125 A main.",
                fontsize=5.0, color=INK, va="center")
        bg.text(xx, y2 - .28, f"Spares: {nsp - sum(len(r[0].split(',')) for r in rows)} spaces.  Feeder: {q.T31012[125][0]} Cu or {q.T31012[125][1]} Al + 6 Cu ground, 125 A (310.12), from the meter stack (E-004).",
                fontsize=5.0, color=INK, va="center")
    bad = b.clarity(fig, None, None, bg); print("E-005 text clashes:", len(bad)); [print("   ", m) for m in bad[:8]]
    b.save(fig, "E-005", pdf)


# ---------------------------------------------------------------------------------------------- service, meters and feeders
def service_sheet(pdf):
    per, conn, tot, dem = q.service(); sa = dem / q.V
    cu_s, cu_a = q.smallest(sa); al_s, al_a = "300 kcmil", 230                     # aluminium chosen to match copper's 230 A, not the 205 A minimum
    notes = [("Existing (inspection 9 Oct 2026)", ["Overhead drop, one service cable down the", "east wall to an old 3-meter socket on the", "stone foundation, north end. Cable not",
                                                    "strapped; ground rod top exposed; three", "100 A panels inside."]),
             ("Is the old cable big enough?", ["Its size cannot be read in the photos.", "A socket like this is normally fed by 4/0", "aluminium SE cable: 180 A at 75 C.",
                                               f"The building needs {sa:,.0f} A (E-002), so it is", "NOT big enough. The socket also has no", "main breakers. Replace the whole service",
                                               "entrance in the same place, as drawn."]),
             ("Utility", ["Mon Power (FirstEnergy) sets the drop,", "meters and meter height. Apply for the", "upgrade first; their rules govern where", "they differ from this sheet."])]
    fig, bg, _ = b.bsheet("E-004", "Service, meters, feeders and grounding", 0, notes, sub="Rear building · east wall, north end")
    bg.text(.5, 10.25, "SERVICE ENTRANCE, METERS, FEEDERS AND GROUNDING · " + q.CODE, fontsize=9.0, fontweight="bold", color=INK, va="center")
    # ================================================================ elevation, 1 in. = 5 ft
    S = .2; X0, Y0 = .62, 2.75; Ex = lambda x: X0 + (x - 13.0) * S; Ez = lambda z: Y0 + z * S       # x = plan x (north to the right), z = ft above grade
    bg.text(.5, 9.95, "ELEVATION: EAST WALL, NORTH END, AS NEW", fontsize=6.6, fontweight="bold", color=INK, va="center")
    bg.text(.5, 9.8, "looking west · Forest Ave is to the right · 1 in. = 5 ft · heights approximate", fontsize=4.8, color=GREY, va="center")
    def R(x0, z0, x1, z1, **kw): bg.add_patch(Rectangle((Ex(x0), Ez(z0)), (x1 - x0) * S, (z1 - z0) * S, **kw))
    def Ln(pts, **kw): bg.plot([Ex(p[0]) for p in pts], [Ez(p[1]) for p in pts], **kw)
    xs, xe, ft, eave = 13.6, 31.6, 6.9, 30.0
    R(xs, 0, xe, ft, fc="#ebe6dc", ec="#8a8172", lw=.6, hatch="...", zorder=1)                     # stone foundation (stuccoed)
    R(xs, ft, xe, eave, fc="#f4f6f8", ec="#8a9099", lw=.6, zorder=1)                                # siding
    for z in np.arange(ft + .45, eave, .45): Ln([(xs, z), (xe, z)], color="#dde2e7", lw=.3, zorder=1.1)
    R(xs - .6, eave, xe + .6, eave + .7, fc="#d9dde2", ec=INK, lw=.6, zorder=2)                     # eave and gutter
    bg.add_patch(MPoly([(Ex(xs - .6), Ez(eave + .7)), (Ex(xe + .6), Ez(eave + .7)), (Ex(xe + .6), Ez(eave + 3.6)), (Ex(xs - .6), Ez(eave + 3.6))], closed=True, fc="#c9ced4", ec="#8a9099", lw=.5, zorder=1.5))
    bg.text(Ex((xs + xe) / 2), Ez(eave + 2.2), "roof", fontsize=4.4, color=GREY, ha="center", va="center", zorder=3)
    Ln([(xs, -.02), (xs, eave + .7)], color=INK, lw=.5, ls=(0, (6, 2, 1, 2)), zorder=2)              # break line: the wall continues south
    R(21.95, 21.0, 24.95, 25.6, fc="#cfe3f7", ec="#1f5fa8", lw=.6, zorder=3)                         # upper flat window on this face
    Ln([(12.6, 0), (34.6, 0)], color=INK, lw=1.0, zorder=4)
    for i in np.arange(12.6, 34.6, .7): Ln([(i, 0), (i - .5, -.5)], color=GREY, lw=.3, zorder=4)
    for lv, z in {"lower flat floor": -1.5, "middle flat floor": 7.9, "upper flat floor": 18.0, "attic floor": 27.4}.items():
        Ln([(xs, z), (xe, z)], color="#9aa0a8", lw=.4, ls=(0, (3, 2)), zorder=1.2)
        bg.text(Ex(xs + .3), Ez(z) + .05, lv, fontsize=4.0, color=GREY, ha="left", va="bottom", zorder=3)
    mx = q_mx = meter_pos()[0]; mz0, mz1 = 2.8, 6.3; hx = mx + 1.0; att = eave - 1.3; head = eave - .5
    # meter stack, three meters, three 125 A breakers
    R(mx - 1.6, mz0, mx + 1.6, mz1, fc="white", ec=FD, lw=1.0, zorder=6)
    for i, k in enumerate("ABC"):
        xm = mx - 1.07 + i * 1.07
        bg.add_patch(Circle((Ex(xm), Ez(mz0 + 2.55)), .38 * S, fc="#eef4fb", ec=FD, lw=.6, zorder=7))
        R(xm - .25, mz0 + .35, xm + .25, mz0 + 1.45, fc="#d9dde2", ec=FD, lw=.5, zorder=7)
        bg.text(Ex(xm), Ez(mz0 + .9), k, fontsize=4.0, color=FD, ha="center", va="center", fontweight="bold", zorder=8)
    # service mast and head
    Ln([(hx, mz1), (hx, head)], color=FD, lw=2.4, zorder=5, solid_capstyle="butt")
    bg.add_patch(MPoly([(Ex(hx) - .05, Ez(head)), (Ex(hx) + .05, Ez(head)), (Ex(hx) + .09, Ez(head + .55)), (Ex(hx) - .09, Ez(head + .55))], closed=True, fc=FD, zorder=6))
    straps = [mz1 + 2.5] + list(np.arange(mz1 + 7.5, head - 2.5, 5.0)) + [head - 1.5]
    for z in straps: Ln([(hx - .35, z), (hx + .35, z)], color=INK, lw=1.3, zorder=6)
    bg.add_patch(Circle((Ex(hx - .6), Ez(att)), .03, fc=INK, zorder=7)); Ln([(hx, att), (hx - .6, att)], color=INK, lw=.6, zorder=6)
    Ln([(hx - .1, head + .55), (hx - .75, head - .5), (hx - .6, att)], color=INK, lw=.6, zorder=6)           # drip loop
    Ln([(hx - .6, att), (34.2, att + 2.6)], color=INK, lw=1.0, zorder=6)                                     # drop
    # feeders out of the top of the stack into the rim joist
    for i, xf in enumerate((mx - 1.15, mx - .7, mx - .25)):
        Ln([(xf, mz1), (xf, 7.25)], color=FD, lw=1.1, zorder=5)
        R(xf - .17, 7.1, xf + .17, 7.55, fc="white", ec=FD, lw=.5, zorder=6)
    # working space
    R(mx - 1.6, 0, mx + 1.6, 6.5, fill=False, ec=FD, lw=.5, ls=(0, (3, 2)), zorder=5.5)
    # grounding
    gx = mx + 1.9; Ln([(mx + 1.6, mz0 + .4), (gx, mz0 + .4), (gx, 0)], color="#2f7d32", lw=.9, zorder=6)
    for rx in (gx, gx - 6.4):
        Ln([(rx, 0), (rx, -8.0)], color="#2f7d32", lw=1.4, zorder=6)
    Ln([(gx, -.4), (gx - 6.4, -.4)], color="#2f7d32", lw=.8, ls=(0, (2, 1)), zorder=6)
    # condensers, disconnects, service receptacle
    for k, (ux, _uy) in condensers().items():
        R(ux - 1.25, 0, ux + 1.25, 2.9, fc="#f3e9f7", ec=HV, lw=.7, zorder=6)
        bg.text(Ex(ux), Ez(1.45), f"A/C {k}", fontsize=4.0, color=HV, ha="center", va="center", zorder=7)
        R(ux - .35, 3.7, ux + .35, 4.7, fc="white", ec=HV, lw=.6, zorder=6); Ln([(ux, 2.9), (ux, 3.7)], color=HV, lw=.6, zorder=6)
    R(26.6, 1.3, 27.2, 1.9, fc="white", ec=PW, lw=.6, zorder=6)
    # numbered callouts on the elevation
    marks = [(1, (33.0, att + 2.1), (33.2, 34.0)), (2, (hx - .6, att), (hx - 3.6, att - 2.2)), (3, (hx, head + .3), (hx - 3.6, head + 2.4)),
             (4, (hx, 17.0), (hx + 2.4, 17.0)), (5, (hx, straps[1]), (hx + 2.4, straps[1] + 1.4)), (6, (mx, mz0 + 2.0), (mx - 4.2, mz0 + 2.0)),
             (7, (mx - 1.6, 1.0), (mx - 4.2, -1.6)), (8, (mx - .7, 7.3), (mx - 4.2, 9.3)), (9, (gx - 6.4, -6.0), (gx - 9.6, -6.0)), (10, (22.0, 2.9), (22.0, 6.2))]
    for n, (px, pz), (tx, tz) in marks:
        Ln([(px, pz), (tx, tz)], color=GREY, lw=.35, zorder=8)
        bg.add_patch(Circle((Ex(tx), Ez(tz)), .085, fc="white", ec=FD, lw=.7, zorder=9))
        bg.text(Ex(tx), Ez(tz), str(n), fontsize=4.6, color=FD, ha="center", va="center", fontweight="bold", zorder=10)
    items = [f"Service drop: Mon Power's conductors from their pole (pole position not known: verify). Mon Power decides if the drop is upsized for the {sa:,.0f} A load.",
             "Point of attachment for the drop: at least 10 ft above grade (230.26), 3 ft or more from any window that opens (230.9).",
             "Service head above the point of attachment, with drip loops (230.54(C), (F)).",
             f"Service conductors: 3 x {cu_s} Cu THWN-2 ({cu_a} A) or 3 x {al_s} Al XHHW-2 ({al_a} A), neutral full size, in 2 in. (Cu) or 2-1/2 in. (Al) Sch 80 PVC. "
             f"Load {sa:,.0f} A by 220.84; ampacity from Table 310.16 at 75 C. {q.smallest(sa, True)[0]} Al ({q.smallest(sa, True)[1]} A) is the bare minimum: not used.",
             "Straps within 3 ft of the head, every fitting and the stack, then at most 5 ft apart (Table 352.30). The old cable was found loose.",
             "Meter stack, ringless, 3 positions, a 125 A meter-main breaker under each meter: these are the 3 service disconnects (230.71), marked LOWER, MIDDLE, UPPER FLAT (230.70(B)). "
             "Neutral bonded here (main bonding jumper, 250.28). Meter height per Mon Power (about 4 to 6 ft to the meter centre).",
             "Working space kept clear in front: 36 in. deep, 30 in. or the stack's width, 6.5 ft high (110.26).",
             f"Feeders A, B and C: out of the top of the stack in three 1-1/4 in. conduits with LB fittings, through the rim joist into the floor framing above the lower flat. "
             f"Each {q.T31012[125][0]} Cu or {q.T31012[125][1]} Al, 2 hots + neutral, + 6 Cu ground (125 A, 310.12). Route: see the section.",
             "Grounding: two 5/8 in. x 8 ft rods, 6 ft or more apart, tops at or below grade (the old rod is exposed); 6 AWG Cu to the rods (250.66(A)). Metal water pipe (if any) bonded with "
             "4 AWG Cu within 5 ft of where it enters. Gas pipe bonded (250.104(B)). Bonding bar for phone and cable at the stack (250.94).",
             "Condensers A, B, C on pads, 12 in. off the wall; a disconnect in sight of each (440.14); GFCI service receptacle within 25 ft (210.63). Each A/C circuit comes from its own flat's panel."]
    y = 9.95; cx0 = 5.25
    bg.text(cx0, y, "NOTES TO THE ELEVATION", fontsize=6.6, fontweight="bold", color=INK, va="center"); y -= .2
    for n, t in enumerate(items, 1):
        bg.add_patch(Circle((cx0 + .07, y), .075, fc="white", ec=FD, lw=.6)); bg.text(cx0 + .07, y, str(n), fontsize=4.4, color=FD, ha="center", va="center", fontweight="bold")
        ls_ = b.wrap(t, 58)
        for j, ln in enumerate(ls_): bg.text(cx0 + .22, y - j * .122, ln, fontsize=4.9, color=INK, va="center")
        y -= .122 * len(ls_) + .07
    y -= .1
    bg.text(cx0, y, "OLD SERVICE CABLE: IS IT BIG ENOUGH?", fontsize=6.4, fontweight="bold", color=INK, va="center"); y -= .16
    chk = [["", "Ampacity at 75 C", "Needed", "OK?"], ["Old cable, if 4/0 Al SE (typical)", "180 A", f"{sa:,.0f} A", "No"], ["Old cable, if 2/0 Cu SE", "175 A", f"{sa:,.0f} A", "No"],
           [f"New: {cu_s} Cu", f"{cu_a} A", f"{sa:,.0f} A", "Yes"], [f"New: {al_s} Al", f"{al_a} A", f"{sa:,.0f} A", "Yes"]]
    table(bg, cx0, y, [1.35, .7, .5, .35], chk, fs=4.9, rh=.15)
    # ================================================================ riser diagram
    rx = 8.45
    bg.text(rx, 9.95, "RISER DIAGRAM", fontsize=6.6, fontweight="bold", color=INK, va="center")
    def boxl(x, y, w, h, t, col=FD, fs=4.6):
        bg.add_patch(Rectangle((x, y), w, h, fc="white", ec=col, lw=.8, zorder=5))
        ls_ = t.split("\n")
        for j, ln in enumerate(ls_): bg.text(x + w / 2, y + h / 2 + (len(ls_) - 1) * .06 - j * .12, ln, fontsize=fs, color=col, ha="center", va="center", zorder=6)
    boxl(9.85, 9.45, 1.6, .36, "Mon Power drop and meters")
    bg.plot([10.65, 10.65], [9.45, 9.05], color=FD, lw=1.5); bg.text(10.72, 9.25, f"{cu_s} Cu or {al_s} Al, {sa:,.0f} A load", fontsize=4.5, color=FD, va="center")
    bg.add_patch(Rectangle((9.2, 8.2), 2.9, .85, fc="white", ec=FD, lw=.9, zorder=5))
    bg.text(10.65, 8.95, "METER STACK (outdoors)", fontsize=4.7, color=FD, ha="center", va="center", fontweight="bold", zorder=6)
    for i, k in enumerate("ABC"):
        bx = 9.45 + i * .9
        bg.add_patch(Circle((bx + .2, 8.62), .12, fc="#eef4fb", ec=FD, lw=.6, zorder=6)); bg.add_patch(Rectangle((bx + .07, 8.26), .26, .16, fc="#d9dde2", ec=FD, lw=.5, zorder=6))
        bg.text(bx + .52, 8.45, f"125 A\n{k}", fontsize=4.2, color=FD, va="center", zorder=6, linespacing=1.0)
    for i, (k, t, ln_) in enumerate((("A", "PANEL A, lower flat\n125 A main, 30 sp.\nmech. room wall", "about 15 ft"), ("B", "PANEL B, middle flat\n125 A main, 30 sp.\nhall wall", "about 40 ft"),
                                     ("C", "PANEL C, upper flat\n125 A main, 40 sp.\nliving room wall", "about 55 ft"))):
        bx = 9.65 + i * .9
        bg.plot([bx, bx], [8.2, 7.25], color=FD, lw=1.2, ls=(0, (4, 1.5)))
        bg.text(bx + .05, 7.72, f"{ln_}", fontsize=4.0, color=FD, va="center", rotation=90)
        boxl(bx - .45 if i else bx - .55, 6.6, .9, .62, t, fs=3.95)
    bg.text(rx, 6.42, f"Each feeder: {q.T31012[125][0]} Cu or {q.T31012[125][1]} Al + 6 Cu ground, 1-1/4 in. conduit (or 1/0 Al SER cable inside the building).", fontsize=4.6, color=INK, va="center")
    bg.plot([12.1, 12.55, 12.55], [8.5, 8.5, 7.95], color="#2f7d32", lw=.9)
    bg.text(12.6, 7.9, "6 Cu to\n2 rods;\nwater and\ngas bonded", fontsize=4.0, color="#2f7d32", va="top", linespacing=1.05)
    # ================================================================ schematic section: where the feeders go
    sx0, sy0 = 8.45, 3.55
    bg.text(rx, 6.15, "WHERE THE FEEDERS GO: SECTION THROUGH THE HOUSE (schematic, looking north)", fontsize=6.0, fontweight="bold", color=INK, va="center")
    Xs = lambda yy: sx0 + 4.4 - (yy + 3.0) * .135; Zs = lambda z: sy0 + (z + 1.5) * .068          # east on the right
    for z0, z1, lab in ((-1.5, 7.9, "LOWER FLAT"), (7.9, 18.0, "MIDDLE FLAT"), (18.0, 27.4, "UPPER FLAT"), (27.4, 35.0, "ATTIC (upper flat)")):
        bg.add_patch(Rectangle((Xs(27.5), Zs(z0)), Xs(0.3) - Xs(27.5), Zs(z1) - Zs(z0), fc="#f7f8f9", ec="#8a9099", lw=.6, zorder=2))
        bg.text(Xs(24.0), Zs(z0) + .1, lab, fontsize=4.0, color=GREY, va="bottom", zorder=3)
    bg.plot([Xs(30), Xs(-4)], [Zs(0)] * 2, color=INK, lw=.8, zorder=3)
    bg.add_patch(Rectangle((Xs(8.5), Zs(-1.5)), Xs(6.1) - Xs(8.5), Zs(35.0) - Zs(-1.5), fc="none", ec=FD, lw=.6, ls=(0, (2, 1.5)), zorder=4, hatch="////", alpha=.5))
    bg.text(Xs(7.3), Zs(34.0), "chase", fontsize=4.0, color=FD, ha="center", va="center", zorder=5)
    bg.add_patch(Rectangle((Xs(-.6) - .05, Zs(2.8)), .2, Zs(6.3) - Zs(2.8), fc="white", ec=FD, lw=.8, zorder=6))
    bg.text(Xs(-.6) + .18, Zs(4.5), "meters", fontsize=4.0, color=FD, va="center", zorder=6)
    fz = 6.9; pa, pb, pc = (2.4, 4.5), (12.4, 13.5), (2.35, 23.0)
    def fl_(pts, lab=None, **kw): bg.plot([Xs(p[0]) for p in pts], [Zs(p[1]) for p in pts], color=FD, lw=1.3, ls=(0, (4, 1.4)), zorder=7, **kw)
    fl_([(-.6, 6.3), (-.6, fz), (pa[0], fz), (pa[0], pa[1] + .6)])
    fl_([(pa[0], fz + .25), (7.3, fz + .25), (7.3, 17.0), (pb[0], 17.0), (pb[0], pb[1] + .6)])
    fl_([(7.0, fz + .5), (7.0, 18.6), (pc[0] + .3, 18.6), (pc[0] + .3, pc[1] - .6)])
    for (yy, zz), k in ((pa, "A"), (pb, "B"), (pc, "C")):
        bg.add_patch(Rectangle((Xs(yy) - .07, Zs(zz - .6)), .14, Zs(zz + .6) - Zs(zz - .6), fc=FD, ec=FD, zorder=8))
        bg.text(Xs(yy) - .12, Zs(zz), f"panel {k}", fontsize=4.2, color=FD, ha="right", va="center", fontweight="bold", zorder=8)
    bg.text(Xs(-.4), Zs(-1.5) - .12, "east wall", fontsize=4.0, color=GREY, ha="center", va="top")
    bg.text(Xs(27.0), Zs(-1.5) - .12, "west wall", fontsize=4.0, color=GREY, ha="center", va="top")
    for t, yy in (("A: 15 ft in the lower flat's ceiling to panel A.", 3.25), ("B, C: in the same ceiling to the old chimney chase, then up it. B leaves at the", 3.12),
                  ("middle flat's ceiling for panel B; C at the upper flat's floor for panel C.", 2.99), ("Firestop at every floor and the floors between flats.", 2.86)):
        bg.text(rx, yy, t, fontsize=4.6, color=INK, va="center")
    # ================================================================ key plan
    kx, ky, ks = 9.35, .75, .047
    bg.text(rx, 2.62, "KEY PLAN", fontsize=6.0, fontweight="bold", color=INK, va="center")
    P = q.outline(4); xs_, ys_ = P.exterior.xy
    bg.add_patch(MPoly([(kx + (27.5 - y_) * ks, ky + x_ * ks) for x_, y_ in zip(xs_, ys_)], closed=True, fc="#f4f6f8", ec=INK, lw=.7))
    bg.plot([kx - 2 * ks, kx + 30 * ks], [ky + 36.2 * ks] * 2, color=INK, lw=1.0)
    bg.text(kx + 13.5 * ks, ky + 37.4 * ks, "FOREST AVE", fontsize=5.2, color=INK, ha="center", va="center", fontweight="bold")
    mxp, myp = meter_pos()
    bg.add_patch(Rectangle((kx + (27.5 - myp) * ks - .01, ky + (mxp - 1.6) * ks), .09, 3.2 * ks, fc=FD, ec=FD))
    bg.annotate("meters: east wall, north end\n= LEFT side seen from Forest Ave", xy=(kx + (27.5 - myp) * ks + .1, ky + mxp * ks), xytext=(kx + 1.75, ky + 1.35),
                fontsize=4.6, color=FD, arrowprops=dict(arrowstyle="->", color=FD, lw=.6), va="center")
    for k, (cx_, cy_) in condensers().items():
        bg.add_patch(Rectangle((kx + (27.5 - cy_) * ks - .07, ky + cx_ * ks - .07), .14, .14, fc="#f3e9f7", ec=HV, lw=.5))
    bg.text(kx + 1.75, ky + .6, "A/C condensers along the east wall\n(pads: verify the space on site)", fontsize=4.5, color=HV, va="center")
    bg.text(kx + 13.5 * ks, ky + 14 * ks, "390 FOREST\n(rear building)", fontsize=4.4, color=GREY, ha="center", va="center")
    bad = b.clarity(fig, None, None, bg); print("E-004 text clashes:", len(bad)); [print("   ", m) for m in bad[:10]]
    b.save(fig, "E-004", pdf)


# ---------------------------------------------------------------------------------------------- general notes sheet
GEN = ["Scope: full gut. Every panel, circuit, box, device, fixture and the service entrance are new; nothing existing is reused. Design intent "
       "to NEC 2020 (confirm the edition Morgantown enforces) and Mon Power's rules; the licensed electrician confirms, pulls the permit and adjusts to the inspector.",
       "Service: replace the service entrance in its present place, east wall north end (left side seen from Forest Ave): new conductors, "
       "3-position meter stack with a 125 A meter-main for each flat, new grounding. Mon Power to set the drop and meters. See E-004.",
       "Panels: one 125 A main-breaker load centre in each flat (A lower, B middle, C upper incl. the attic and its stair hall), Type 2 surge "
       "protector in each. Panel directories typed and filled in. Working space 30 x 36 in. kept clear, 6.5 ft high.",
       "Wiring: copper NM-B in walls and floors of each flat; feeders in conduit (E-004). Cables between flats only in the chase. Boxes in the "
       "fire-rated walls and floors between flats: listed, putty pads where boxes are back to back, firestop every penetration.",
       "Kitchens: 3 or 4 counter circuits per flat, 20 A each, counter receptacles alternating between them so high-wattage appliances "
       "(air fryers, kettles, toasters) are spread out; refrigerator, dishwasher and microwave-hood each on their own 20 A circuit; range 50 A, 240 V.",
       "Laundry: washer 20 A circuit of its own; dryer 30 A, 240 V, 4-wire receptacle; dryer vent ducted outside.",
       "Baths: one 20 A GFCI circuit per bath for its receptacle, ceiling light, LED anti-fog mirror and exhaust fan. Mirror hardwired from a box "
       "behind it (centred, 60 in. to the box); fan 80 cfm, humidity-sensing, ducted to the outside; wet-rated light over a tub.",
       "Heating and cooling: gas furnace on its own 15 A circuit with a service switch at the unit; condenser on a 2-pole circuit sized to its "
       "nameplate MOCP, disconnect within sight outdoors; condensate pump (if needed) on the mechanical circuit.",
       "Lighting: LED throughout, counts from the lumen-method calculation (E-003). Dimmers in living rooms and bedrooms. Closets: motion-sensor "
       "fixtures. Exterior: dusk-to-dawn light at each entrance on the flat's own lighting circuit.",
       "Smoke and CO alarms: hardwired with battery backup, interconnected within each flat; smoke in every bedroom, combined smoke/CO outside each "
       "sleeping area and on every level (gas appliances in each flat).",
       "Low voltage: data / TV outlet (Cat 6 and RG6) in each bedroom and living room, home-run to a structured-wiring box next to each panel; "
       "doorbell at each entrance.",
       "Mounting heights to the centre: receptacles 16 in., counters 44 in., switches 48 in., outdoor receptacles 18 in. above grade or deck. "
       "Receptacles tamper resistant (406.12); outdoor ones weather resistant with in-use covers (406.9).",
       "Gas appliances: the furnace and water heater need power only for their blower, inducer, igniter and vent fan. Boxes for the furnace "
       "and water heater placed so the gas pipe, flue and ducts can run clear of them (see the HVAC and plumbing sheets)."]


def notes_sheet(pdf):
    notes = [("Read with", ["E-002 load calculations, E-003 lighting", "calculations, E-004 service and feeders,", "E-005 panel schedules, E-101 to E-104", "plans. Architecture: A-101 to A-104."]),
             ("Owner's choices built in", ["Electric ranges and dryers; gas furnaces", "and gas water heaters; central air.", "Students: 3 or 4 kitchen counter circuits,", "a data outlet in each bedroom, USB-C",
                                         "combination receptacle at each desk.", "Every bath: LED anti-fog mirror, ceiling", "light and exhaust fan."])]
    fig, bg, _ = b.bsheet("E-001", "Electrical general notes and legend", 0, notes, sub="Rear building · all flats")
    bg.text(.5, 10.25, "ELECTRICAL GENERAL NOTES AND LEGEND", fontsize=9.5, fontweight="bold", color=INK, va="center")
    y = 9.95
    for i, t in enumerate(GEN):
        bg.text(.55, y, f"{i + 1}.", fontsize=5.9, color=INK, va="center", fontweight="bold")
        for j, ln in enumerate(b.wrap(t, 104)):
            bg.text(.8, y - j * .145, ln, fontsize=5.9, color=INK, va="center")
        y -= .145 * len(b.wrap(t, 104)) + .09
    bg.text(7.3, 9.95, "LEGEND", fontsize=7.0, fontweight="bold", color=INK, va="center")
    yl = legend(bg, 7.35, 9.68, fs=5.6, rh=.205)
    bg.plot([7.35, 7.71], [yl - .02, yl - .02], color=FD, lw=1.6, ls=(0, (4, 1.6))); bg.text(7.82, yl - .02, "Feeder (heavy dashed)", fontsize=5.6, color=INK, va="center")
    bg.add_patch(Rectangle((7.4, yl - .3), .26, .16, fill=False, ec=FD, lw=.6, ls=(0, (1.5, 1.5)))); bg.text(7.82, yl - .22, "Old chimney: chase for feeders and pipes", fontsize=5.6, color=INK, va="center")
    S = schedules(); yy = yl - .55
    bg.text(7.3, yy, "CIRCUIT COUNT", fontsize=7.0, fontweight="bold", color=INK, va="center"); yy -= .2
    rows = [["Panel", "Flat", "Circuits", "2-pole", "Counter"]] + [[k, q.FLATS[k]["name"].split(" (")[0], f"{len(S[k][0])}", f"{sum(1 for r in S[k][0] if r[5] == 2)}", f"{q.FLATS[k]['sa']}"] for k in q.FLATS]
    table(bg, 7.3, yy, [.45, 1.15, .55, .5, .55], rows, fs=5.5, rh=.18)
    bad = b.clarity(fig, None, None, bg); print("E-001 text clashes:", len(bad)); [print("   ", m) for m in bad[:8]]
    b.save(fig, "E-001", pdf)


SHEETS = [("E-001", "Electrical general notes and legend", notes_sheet), ("E-002", "Electrical load calculations", q.load_sheet),
          ("E-003", "Lighting calculations", q.light_sheet), ("E-004", "Service, meters, feeders and grounding", service_sheet),
          ("E-005", "Panel schedules", sched_sheet)] + [
          (n, t, (lambda fl_, n_: (lambda pdf: plan_sheet(pdf, n_, fl_)))(fl, n)) for n, t, fl in
          (("E-101", "Lower flat: power and lighting", 3), ("E-102", "Middle flat: power and lighting", 4),
           ("E-103", "Upper flat main floor: power and lighting", 5), ("E-104", "Attic: power and lighting", 6))]

if __name__ == "__main__":
    from matplotlib.backends.backend_pdf import PdfPages
    out = os.path.join(b.HERE, "drawings", "390-Forest_Electrical_Rev1.pdf")
    with PdfPages(out) as pdf:
        for n, _t, fn in SHEETS:
            fn(pdf)
    print("wrote", out)
