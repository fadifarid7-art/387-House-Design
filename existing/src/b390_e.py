"""390 Forest Ave builder set: ELECTRICAL sheets E-001 and E-101 to E-104 (power, lighting, life safety).
Design intent only. NEC 2020 dwelling rules are the layout guide; everything is to be confirmed by the licensed electrician.
Receptacles, appliance outlets, lights and bedroom alarms are placed from the plan model; switches and a few closet devices are hand-placed and snapped to the wall."""
import math
import os
import sys
from functools import lru_cache

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, Polygon as MPoly, Rectangle  # noqa: E402
from matplotlib.patheffects import withStroke  # noqa: E402
from shapely.geometry import Point, box  # noqa: E402
from shapely.geometry.polygon import orient  # noqa: E402
from shapely.ops import nearest_points, unary_union  # noqa: E402

import build390 as b  # noqa: E402
from common import GREY, INK, table  # noqa: E402

PW, LT, LS = "#1d4e89", "#c45a00", "#b3261e"      # power (blue), lighting (orange), life safety (red)
HALO = [withStroke(linewidth=1.3, foreground="white")]
PANEL_OF = {3: "A", 4: "B", 5: "C", 6: "C"}
FLAT = {"A": dict(name="Lower flat", amps=100, sf=790, ac=18, sp=24, mech="109", beds=[("103", "Bedroom 1"), ("104", "Bedroom 2")], baths=[("105", "Bath 1"), ("106", "Bath 2")]),
        "B": dict(name="Middle flat", amps=100, sf=870, ac=18, sp=24, mech="208", beds=[("203", "Bedroom 1"), ("204", "Bedroom 2")], baths=[("205", "Bath 1"), ("206", "Bath 2")]),
        "C": dict(name="Upper flat + attic", amps=125, sf=1450, ac=22, sp=30, mech="307", beds=[("303", "Bedroom 3"), ("304", "Bedroom 4"), ("401", "Attic bedroom 1"), ("402", "Attic bedroom 2")],
                  baths=[("305", "Bath 1"), ("403", "Attic bath A"), ("404", "Attic bath B")])}


def circuits(k):
    """Branch circuits of one flat: (key, breaker, wire, what it serves). AF = arc-fault, GF = ground-fault, DF = both in one breaker."""
    f = FLAT[k]
    c = [("SA1", "20 A 1P DF", "12-2", "Kitchen counter receptacles A"), ("SA2", "20 A 1P DF", "12-2", "Kitchen counter B + wall recepts"), ("REF", "20 A 1P AF", "12-2", "Refrigerator"),
         ("RNG", "20 A 1P AF", "12-2", "Gas range, 120 V receptacle"), ("MW", "20 A 1P AF", "12-2", "Range hood / microwave")]
    c += [("B" + n, "20 A 1P GF", "12-2", f"{nm}: vanity receptacle") for n, nm in f["baths"]]
    c += [("LAU", "20 A 1P DF", "12-2", "Laundry: washer receptacle"), ("DRY", "30 A 2P GF", "10-3", "Dryer, 240 V receptacle (14-30R)"), ("FUR", "15 A 1P", "14-2", "Gas furnace, switch at the unit"),
          ("WH", "20 A 1P", "12-2", "Water heater vent + service recepts"), ("AC", "30 A 2P", "10-2", "AC condenser, disconnect at unit")]
    c += [("R" + n, "15 A 1P AF", "14-2", f"{nm}: receptacles") for n, nm in f["beds"]]
    c += [("LIV", "20 A 1P AF", "12-2", "Living room + hall receptacles"), ("LT1", "15 A 1P AF", "14-2", "Lights: living/kitchen/halls + alarms"),
          ("LT2", "15 A 1P AF", "14-2", "Lights + fans: beds, baths, closets")]
    return c + ([("LT3", "15 A 1P AF", "14-2", "Attic: lights and fans")] if k == "C" else [])


CK = {k: circuits(k) for k in FLAT}
CN = {k: {c[0]: i + 1 for i, c in enumerate(CK[k])} for k in FLAT}


def cn(fl, key, no=""):
    """Circuit tag for a device. Room 213 (stair hall on the middle-flat level) belongs to the upper flat: tags C.."""
    return f"C{CN['C'][key]}" if no == "213" else str(CN[PANEL_OF[fl]][key])


def ltkey(fl, r):
    return "LT3" if fl == 6 else "LT2" if r["kind"] in ("bed", "bath", "closet") else "LT1"


KIT = {3: ("v", 16.9, 17.6, 25.4), 4: ("h", 17.5, 21.6, 28.0), 5: ("v", 3.9, 15.2, 23.2)}      # recessed row over the kitchen aisle: axis, line, from, to
# Hand-placed items per level, as points about 0.3 ft off the wall inside the room; snap() puts them on the wall face.
# P panel (x, y, slide of the clear floor box) · AC point outside the nearest outside wall · SW (room or group, x, y, type) · RX (symbol, x, y, circuit[, room])
# FIX lights that replace the automatic ones (c = small) · LS alarms outside the bedrooms · KN keynote positions
X = {3: dict(P=(21.75, 12.5, 0.0), AC=(31.0, 14.5),
             SW=[("101", 1.4, 18.0, "S3"), ("101", 12.3, 13.42, "S3"), ("102", 16.9, 16.6, "2S"), ("103", 12.4, 12.5, "S"), ("112", 7.4, 10.0, "S"), ("104", 22.8, 13.4, "S"), ("111", 25.8, 15.6, "S"),
                 ("105", 18.45, 9.3, "2S"), ("106", 16.4, 9.0, "2S"), ("107", 16.5, 9.9, "S3"), ("107", 22.6, 10.15, "S3"), ("108", 26.6, 12.5, "S"), ("109", 20.4, 12.5, "S"), ("110", 27.0, 3.9, "S")],
             RX=[("X", 16.7, 14.5, "FUR"), ("D", 20.5, 15.3, "WH"), ("G", 20.4, 13.4, "WH"), ("G", 19.7, 26.5, "SA1")],
             FIX={"109": [("c", 18.37, 14.3)], "108": [("C", 28.4, 7.6)], "106": [("F", 14.2, 5.2)], "105": [("F", 20.9, 7.2)], "107": [("C", 15.9, 11.2), ("C", 22.3, 11.2)], "110": [("c", 27.7, 3.14)]},
             LS=[("SC", 24.0, 11.3)], KN=[(21.75, 10.6), (18.4, 16.9), (33.3, 16.3), (19.6, 19.0)]),
     4: dict(P=(16.2, 13.9, -0.25), AC=(16.4, 28.1),
             SW=[("201", 34.3, 9.65, "S3"), ("201", 21.0, 11.15, "S3"), ("202", 20.1, 17.8, "2S"), ("203", 14.85, 18.4, "S"), ("204", 10.1, 12.3, "S"), ("211", 10.1, 3.5, "S"), ("205", 12.0, 17.0, "2S"),
                 ("206", 14.0, 8.2, "2S"), ("207", 16.55, 12.6, "S"), ("210", 19.2, 17.1, "S3"), ("210", 15.4, 17.1, "S3"), ("208", 19.2, 18.0, "S"), ("209", 22.55, 12.8, "S"), ("213", 25.3, 21.35, "S3")],
             RX=[("X", 15.7, 19.2, "FUR"), ("D", 18.6, 21.0, "WH"), ("G", 19.25, 20.7, "WH"), ("R", 27.5, 21.35, "LIV", "213")],
             FIX={"205": [("F", 9.0, 15.3)], "206": [("F", 15.1, 6.8)], "207": [("C", 13.8, 10.3)], "210": [("C", 13.9, 15.5)], "208": [("c", 17.5, 18.1)], "209": [("C", 19.55, 12.6)],
                  "213": [("C", 28.0, 25.2), ("C", 18.9, 25.9)]},
             LS=[("SC", 17.6, 15.6), ("SC", 15.6, 11.4), ("SD", 29.6, 22.4)], KN=[(16.0, 14.6), (16.4, 20.9), (14.2, 28.8), (29.9, 14.0)]),
     5: dict(P=(23.25, 14.3, 0.39), AC=(17.9, -0.5),
             SW=[("301", 11.6, 12.8, "S"), ("311", 15.0, 4.2, "S"), ("302", 6.9, 13.72, "2S"), ("308", 9.55, 17.6, "S"), ("303", 23.25, 12.4, "S"), ("309", 18.6, 4.55, "S"), ("304", 24.15, 18.5, "S"),
                 ("305", 16.15, 17.78, "2S"), ("306", 11.1, 13.72, "S3"), ("306", 23.25, 18.3, "S3"), ("ST1", 17.2, 18.9, "S3"), ("ST2", 23.25, 19.3, "S3"), ("307", 15.5, 13.72, "S")],
             RX=[("X", 15.9, 11.7, "FUR"), ("D", 19.4, 10.65, "WH"), ("G", 17.7, 10.65, "WH")],
             FIX={"306": [("C", 13.5, 15.3), ("C", 18.2, 15.6)], "ST1": [("C", 18.4, 18.5)], "ST2": [("C", 21.9, 19.3)], "307": [("c", 17.72, 12.4)], "308": [("C", 8.82, 17.2)], "309": [("c", 16.8, 5.1)]},
             LS=[("SC", 20.2, 16.4)], KN=[(22.0, 14.9), (17.0, 11.2), (15.7, -1.6), (3.3, 21.6)]),
     6: dict(SW=[("401", 16.0, 13.5, "S"), ("406", 13.75, 12.8, "S"), ("403", 9.9, 16.5, "2S"), ("402", 20.65, 16.7, "S"), ("407", 24.2, 20.1, "S"), ("404", 22.5, 8.4, "2S"), ("405", 17.45, 16.2, "S3")],
             RX=[], FIX={"403": [("F", 13.5, 17.8)], "404": [("F", 19.6, 8.95)], "405": [("C", 18.6, 15.2), ("C", 18.6, 22.3)]}, LS=[("SC", 19.3, 14.0)], KN=[])}


# ---------------------------------------------------------------------------------------------- geometry helpers
@lru_cache(None)
def solid(fl):
    L = b.LV[fl]
    return unary_union([b.geom(fl)["walls"]] + [box(*q) for q in L["new"] + L["fix"]])


@lru_cache(None)
def gaps(fl, m=0.3):
    """Door and closet openings (new and existing) as boxes, with a margin along the wall so nothing lands on the trim."""
    L = b.LV[fl]; out = []
    for d in L["doors"] + L["bifolds"]:
        w, a0, a1 = d[2:5]; out.append((a0 - m, w - .6, a1 + m, w + .6) if d[1] == "h" else (w - .6, a0 - m, w + .6, a1 + m))
    for o in b.geom(fl)["doors"]:
        if len(o["pts"]) >= 4:
            (x0, y0), (x1, y1) = np.min(o["pts"], 0), np.max(o["pts"], 0)
            if max(x1 - x0, y1 - y0) > 1.2:
                out.append((x0 - m, y0 - .5, x1 + m, y1 + .5) if x1 - x0 > y1 - y0 else (x0 - .5, y0 - m, x1 + .5, y1 + m))
    return unary_union([box(*q) for q in out])


@lru_cache(None)
def fxboxes(fl):
    return unary_union([box(*f[1:5]).buffer(.12) for f in b.LV[fl]["fx"] if len(f) >= 5 and not isinstance(f[3], str)])


def snap(fl, x, y):
    """Nearest wall face to a point just inside a room: (point on the face, unit normal pointing back into the room)."""
    p = nearest_points(solid(fl).boundary, Point(x, y))[0]; dx, dy = x - p.x, y - p.y
    return (p.x, p.y), ((1 if dx > 0 else -1, 0) if abs(dx) > abs(dy) else (0, 1 if dy > 0 else -1))


def room_at(fl, x, y):
    return min(b.LV[fl]["rooms"], key=lambda r: min(box(*q).distance(Point(x, y)) for q in r["rects"]))


def wall_runs(fl, r):
    """Unbroken wall space of a room (NEC 210.52: measured around corners, broken by doors, openings and fixed cabinets).
    Returns runs of samples (x, y, nx, ny) every 0.1 ft; n points into the room."""
    P = orient(unary_union([box(*q) for q in r["rects"]]), 1.0); S, G, F = solid(fl), gaps(fl), fxboxes(fl)
    c = list(P.exterior.coords); runs, cur, first = [], [], None
    for (x0, y0), (x1, y1) in zip(c[:-1], c[1:]):
        d = math.hypot(x1 - x0, y1 - y0); ux, uy = (x1 - x0) / d, (y1 - y0) / d; nx, ny = -uy, ux
        for t in np.arange(.05, d, .1):
            x, y = x0 + ux * t, y0 + uy * t
            ok = S.distance(Point(x - nx * .2, y - ny * .2)) < .25 and not G.contains(Point(x, y)) and not F.contains(Point(x + nx * .25, y + ny * .25))
            first = ok if first is None else first
            if ok: cur.append((x, y, nx, ny))
            elif cur: runs.append(cur); cur = []
    if cur:
        if first and runs: runs[0] = cur + runs[0]
        else: runs.append(cur)
    return runs


def place(run, spacing=12.0):
    """Receptacles along one wall run so no point is more than spacing/2 from one; nudged 0.6 ft or more off corners."""
    n = len(run); k = max(1, math.ceil(n * .1 / spacing)); out = []
    for i in range(k):
        j = int((i + .5) * n / k)
        for s in (0, 7, -7, 14, -14):
            q = j + s
            if 0 <= q < n and all(run[min(max(q + e, 0), n - 1)][2:] == run[q][2:] for e in (-6, 6)):
                j = q; break
        out.append(run[j])
    return out


def back(fl, bx, r):
    """The wall a cabinet, appliance or vanity backs onto: (point on the wall at the middle of the box, normal into the room, half length along the wall)."""
    x0, y0, x1, y1 = bx; cand = []
    for q in r["rects"]:
        for gap_, pt, n, half in ((abs(x0 - q[0]), (q[0], (y0 + y1) / 2), (1, 0), (y1 - y0) / 2), (abs(x1 - q[2]), (q[2], (y0 + y1) / 2), (-1, 0), (y1 - y0) / 2),
                                  (abs(y0 - q[1]), ((x0 + x1) / 2, q[1]), (0, 1), (x1 - x0) / 2), (abs(y1 - q[3]), ((x0 + x1) / 2, q[3]), (0, -1), (x1 - x0) / 2)):
            cand.append((gap_ > .2, gaps(fl).contains(Point(pt)), -half, gap_, pt, n, half))
    _, _, _, _, pt, n, half = min(cand)
    return snap(fl, pt[0] + n[0] * .4, pt[1] + n[1] * .4)[0], n, half


# ---------------------------------------------------------------------------------------------- symbols (s = 1 on a plan in feet, 0.25 on the sheet in inches)
def sym(a, k, x, y, n=(0, 1), s=1.0, arg=None, z=12):
    nx, ny = n; tx, ty = -ny, nx; cx, cy = x + nx * .32 * s, y + ny * .32 * s
    if k in ("R", "G", "D"):
        a.add_patch(Circle((cx, cy), .27 * s, fc=PW if k == "D" else "white", ec=PW, lw=.7, zorder=z))
        if k == "G": a.text(cx, cy - .01 * s, "G", fontsize=3.5, color=PW, ha="center", va="center", fontweight="bold", zorder=z + 1)
        for e in ((-.1, .1) if k == "R" else ()):
            a.plot([x + tx * e * s, x + tx * e * s + nx * .68 * s], [y + ty * e * s, y + ty * e * s + ny * .68 * s], color=PW, lw=.55, zorder=z + .5, solid_capstyle="butt")
    elif k == "Q":
        a.add_patch(MPoly([(x + tx * .33 * s, y + ty * .33 * s), (x - tx * .33 * s, y - ty * .33 * s), (x + nx * .62 * s, y + ny * .62 * s)], closed=True, fc=PW, ec=PW, lw=.5, zorder=z))
    elif k in ("X", "J"):
        a.add_patch(Rectangle((cx - .25 * s, cy - .25 * s), .5 * s, .5 * s, fc="white", ec=PW, lw=.7, zorder=z))
        a.text(cx, cy - .01 * s, "D" if k == "X" else "J", fontsize=3.4, color=PW, ha="center", va="center", fontweight="bold", zorder=z + 1)
    elif k == "P":
        a.add_patch(MPoly([(x + tx * e * s - nx * d * s, y + ty * e * s - ny * d * s) for e, d in ((-.6, 0), (.6, 0), (.6, .34), (-.6, .34))], closed=True, fc=PW, ec=PW, lw=.5, zorder=z))
    elif k == "S":
        a.text(cx, cy, arg or "S", fontsize=4.4, color=LT, ha="center", va="center", fontweight="bold", zorder=z + 1, path_effects=HALO)
    elif k in ("C", "c"):
        r = (.3 if k == "C" else .22) * s
        for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            a.plot([x + dx * r, x + dx * r * 1.55], [y + dy * r, y + dy * r * 1.55], color=LT, lw=.6, zorder=z)
        a.add_patch(Circle((x, y), r, fc="white", ec=LT, lw=.75, zorder=z))
    elif k == "RL":
        a.add_patch(Circle((x, y), .2 * s, fc="white", ec=LT, lw=.7, zorder=z)); a.add_patch(Circle((x, y), .07 * s, fc=LT, ec=LT, lw=.3, zorder=z + .1))
    elif k == "V":
        h = (arg or 1.4) / 2 * s
        a.add_patch(MPoly([(x + tx * e + nx * d * s, y + ty * e + ny * d * s) for e, d in ((-h, .05), (h, .05), (h, .25), (-h, .25))], closed=True, fc="#f7c79a", ec=LT, lw=.6, zorder=z))
    elif k == "F":
        a.add_patch(Rectangle((x - .36 * s, y - .36 * s), .72 * s, .72 * s, fc="white", ec=LT, lw=.75, zorder=z)); a.add_patch(Circle((x, y), .25 * s, fc="none", ec=LT, lw=.6, zorder=z + .1))
        a.text(x, y - .01 * s, "F", fontsize=3.4, color=LT, ha="center", va="center", fontweight="bold", zorder=z + 1)
    elif k in ("SD", "SC"):
        w = (.42 if k == "SD" else .62) * s
        a.add_patch(Rectangle((x - w, y - .3 * s), 2 * w, .6 * s, fc="white", ec=LS, lw=.8, zorder=z + 2))
        a.text(x, y - .01 * s, "SD" if k == "SD" else "SD/CO", fontsize=3.5, color=LS, ha="center", va="center", fontweight="bold", zorder=z + 3)


def tag(a, x, y, t, col=PW):
    a.text(x, y, t, fontsize=3.5, color=col, ha="center", va="center", fontweight="bold", zorder=14, path_effects=HALO)


def leg(a, p, q, rad=.22):
    a.add_patch(FancyArrowPatch(p, q, connectionstyle=f"arc3,rad={rad}", arrowstyle="-", color=LT, lw=.45, ls=(0, (2.4, 1.8)), zorder=10, shrinkA=2.5, shrinkB=2.5))


LEG = [("R", "Duplex receptacle, tamper-resistant.\nBlue number beside it = circuit"), ("G", "GFCI receptacle, 20 A"), ("D", "Dedicated receptacle: one appliance"), ("Q", "30 A 240 V dryer receptacle"),
       ("X", "Disconnect / switch at equipment\n(J in the box = junction box)"), ("P", "New panel flush in the wall; dashed\nbox = 30 x 36 in. clear floor"),
       ("S", "Switch. S3 = 3-way pair,\n2S = two switches in one box"), ("C", "Ceiling light, LED. Small = closet\nor mechanical, enclosed"), ("RL", "Recessed LED light"),
       ("V", "Vanity light over the basin"), ("F", "Bath exhaust fan with light"), ("leg", "Switch leg: switch to its lights"), ("uc", "Under-cabinet LED strip"),
       ("SD", "Smoke alarm, hardwired, interconnected"), ("SC", "Smoke + CO alarm, hardwired")]


def legend(bg, x, y, items=LEG, fs=5.6):
    for k, txt in items:
        if k == "leg": leg(bg, (x, y - .03), (x + .36, y - .03), .35)
        elif k == "uc": bg.plot([x, x + .34], [y, y], color=LT, lw=1.3)
        elif k in ("C", "RL", "F", "SD", "SC"): sym(bg, k, x + .17, y, s=.25)
        else: sym(bg, k, x + .17, y - .08, (0, 1), .25, "S3" if k == "S" else 1.2)
        for i, ln in enumerate(txt.split("\n")):
            bg.text(x + .47, y - i * .13, ln, fontsize=fs, color=INK, va="center")
        y -= .215 + .13 * txt.count("\n")
    return y


# ---------------------------------------------------------------------------------------------- devices of one level
def auto_lights(fl, r):
    x0, y0, x1, y1 = r["rects"][0]; cx, cy, w, h = (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0; k = r["kind"]
    if k == "bed":
        return [("C", cx, cy)] if fl != 6 else [("C", x0 + w * q, cy) if w > h else ("C", cx, y0 + h * q) for q in (.25, .75)]
    if k == "living": return [("RL", x0 + w * i, y0 + h * j) for i in (.25, .75) for j in (.25, .75)]
    if k == "kitchen":
        a, c, lo, hi = KIT[fl]; return [("RL", c, v) if a == "v" else ("RL", v, c) for v in np.linspace(lo, hi, 3)]
    if k == "bath": return [("F", cx, cy)]
    if k == "closet": return [("c", cx, cy)] if min(w, h) >= 2.0 else []
    if k == "hall":
        n = max(1, round(max(w, h) / 7)); return [("C", x0 + w * (i + .5) / n, cy) if w > h else ("C", cx, y0 + h * (i + .5) / n) for i in range(n)]
    return [("C", cx, cy)]


def devices(fl):
    """Everything electrical on one level: D = (symbol, x, y, normal, tag, arg), lights by room or group, legs, under-cabinet strips."""
    L = b.LV[fl]; x_ = X[fl]; D, lights, legs, strips = [], {}, [], []
    for r in L["rooms"]:      # receptacles: 6 ft / 12 ft rule in bedrooms, living rooms and halls; kitchen walls without cabinets on small-appliance circuit B
        key = {"bed": "R" + r["no"], "living": "LIV", "hall": "LIV", "kitchen": "SA2"}.get(r["kind"])
        for run in (wall_runs(fl, r) if key else []):
            if len(run) >= 20:
                for x, y, nx, ny in place(run):
                    p, n = snap(fl, x + nx * .4, y + ny * .4); D.append(("R", *p, n, cn(fl, key), None))
        fx = x_["FIX"].get(r["no"], auto_lights(fl, r))
        if fx: lights[r["no"]] = list(fx)
    lights.update({k: list(v) for k, v in x_["FIX"].items() if k not in lights})
    sa = 0; tubs = unary_union([box(*q[1:5]) for q in L["fx"] if q[0] == "tub"])
    for f in L["fx"]:      # outlets that follow the fixtures and appliances
        k = f[0]
        if k not in ("fridge", "range", "base", "sinkbase", "washer", "dryer", "van"): continue
        bx = f[1:5]; r = room_at(fl, (bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2); (px, py), n, half = back(fl, bx, r); t = (-n[1], n[0])
        at = lambda s: (px + t[0] * s, py + t[1] * s)  # noqa: E731
        if k == "fridge": D.append(("D", *at(0), n, cn(fl, "REF"), None))
        elif k == "range": D += [("D", *at(-.42), n, cn(fl, "RNG"), None), ("D", *at(.42), n, cn(fl, "MW"), None)]
        elif k == "washer": D.append(("D", *at(0), n, cn(fl, "LAU"), None))
        elif k == "dryer": D.append(("Q", *at(0), n, cn(fl, "DRY"), None))
        elif k == "van":
            e = max((-half, half), key=lambda s: tubs.distance(Point(at(s))))
            D += [("G", *at(e), n, cn(fl, "B" + r["no"]), None), ("V", px, py, n, "", half * 1.4)]; lights[r["no"]].append(("V", px + n[0] * .15, py + n[1] * .15))
        if k in ("base", "sinkbase"): strips.append((at(-half + .1), at(half - .1), n))
        if k == "base" and half >= .5:      # counter: no point more than 2 ft from a receptacle, alternating the two small-appliance circuits
            m = math.ceil(half / 2)
            for i in range(m):
                sa += 1; D.append(("G", *at(-half + (i + .5) * 2 * half / m), n, cn(fl, "SA1" if sa % 2 else "SA2"), None))
    for e in x_["RX"]:
        p, n = snap(fl, e[1], e[2]); D.append((e[0], *p, n, "" if e[3] in ("FUR", "WH") else cn(fl, e[3], e[4] if len(e) > 4 else ""), None))
    first = {}
    for tgt, x, y, typ in x_["SW"]:      # switches, each tied to the nearest light of its room; lights of a room chained together
        p, n = snap(fl, x, y); D.append(("S", *p, n, "", typ)); c = (p[0] + n[0] * .32, p[1] + n[1] * .32); first.setdefault(tgt, c)
        q = min(lights[tgt], key=lambda v: math.dist(c, v[1:3])); legs.append((c, q[1:3]))
    for tgt, fx in lights.items():
        todo = list(fx); cur = min(todo, key=lambda v: math.dist(first.get(tgt, v[1:3]), v[1:3])); todo.remove(cur)
        while todo:
            nxt = min(todo, key=lambda v: math.dist(cur[1:3], v[1:3])); legs.append((cur[1:3], nxt[1:3])); todo.remove(nxt); cur = nxt
        D += [(k, x, y, (0, 1), "", None) for k, x, y in fx if k != "V"]
    for r in L["rooms"]:      # smoke alarm in every bedroom, part-way from the middle of the room to the door switch
        if r["kind"] == "bed":
            x0, y0, x1, y1 = r["rects"][0]; c = ((x0 + x1) / 2, (y0 + y1) / 2); s = first.get(r["no"], c)
            D.append(("SD", c[0] + .45 * (s[0] - c[0]), c[1] + .45 * (s[1] - c[1]), (0, 1), "", None))
    D += [(k, x, y, (0, 1), "", None) for k, x, y in x_["LS"]]
    return D, lights, legs, strips


def keynotes(fl):
    p = PANEL_OF[fl]; f = FLAT[p]; c = CN[p]
    if fl == 6:
        return [((17.0, 7.5), "Circuits from panel C (main floor) come up in the old chimney chase. Firestop at the floor."),
                ((23.3, 9.6), "Bath B switches are outside the door: no wall inside is clear of the tub."),
                ((5.0, 13.6), "Keep lights and alarms on the flat 7'-8\" ceiling. Any light in the slope: IC-rated, airtight."),
                ((2.0, 9.4), "Knee walls: check there is depth for a box before cutting in; if not, use a surface box.")]
    k = list(zip(X[fl]["KN"], [f"Panel {p}, {f['amps']} A, flush in the hall wall. Keep the dashed 30 x 36 in. floor clear. Feeder from existing meter: route and size by electrician.",
                               f"Mechanical closet: furnace switch D (ckt {c['FUR']}); water heater receptacle and GFCI service receptacle (ckt {c['WH']}); light and switch.",
                               f"AC condenser outside (place by HVAC): ckt {c['AC']}, 30 A 240 V, weatherproof disconnect at the unit." + (" Run down the outside wall." if fl == 5 else ""),
                               f"Range wall: gas range receptacle (ckt {c['RNG']}); hood / microwave receptacle in the cabinet above (ckt {c['MW']}). Under-cabinet strip on the kitchen switch."]))
    if fl == 3: k += [((22.2, 13.7), "Wall not in the scan (see A-101): confirm it before setting the panel here.")]
    if fl == 4: k += [((23.0, 22.3), f"Stair hall 213 is the upper flat's: fed from panel C (tags C{CN['C']['LT1']}, C{CN['C']['LIV']}). Entry door is not on the plan: add a 3-way switch at it."),
                      ((32.2, 18.2), "Counter in front of an opening: put the counter receptacle below the sill, or use a listed pop-up."),
                      ((18.3, 16.3), "Two doors swing across the panel's clear floor: workable, but verify with the inspector.")]
    if fl == 5: k += [((17.0, 8.0), "Attic circuits rise in the old chimney chase. Firestop at the floor.")]
    return k


def sheet_notes(fl):
    p = PANEL_OF[fl]; f = FLAT[p]
    n = [(f"Panel {p} circuits · {f['amps']} A", [f"{i + 1:>2}  {c[1][:4]} {c[1][5:7]}  {c[3]}" for i, c in enumerate(CK[p])]),
         ("Read with E-001", ["Design intent, to be confirmed by the", "licensed electrician. Existing wiring is", "unknown: sound, grounded devices in the",
                              "right place may stay; new rooms and", "closets are all-new wiring."])]
    return n


def level(pdf, number, fl):
    L = b.LV[fl]; p = PANEL_OF[fl]; x_ = X[fl]
    fig, bg, ax = b.bsheet(number, f"{L['name']}: power, lighting, life safety", fl, sheet_notes(fl))
    b.draw_base(ax, fl, "trade")
    D, lights, legs, strips = devices(fl)
    for a0, a1, n in strips:
        ax.plot([a0[0] + n[0] * .1, a1[0] + n[0] * .1], [a0[1] + n[1] * .1, a1[1] + n[1] * .1], color=LT, lw=1.3, zorder=11, solid_capstyle="butt")
    for a0, a1 in legs: leg(ax, a0, a1)
    for k, x, y, n, t, arg in D:
        sym(ax, k, x, y, n, 1.0, arg)
        if t: tag(ax, x + n[0] * .86, y + n[1] * .86, t)
    for r in L["rooms"]:      # lighting circuit number at one light per room
        if r["no"] in lights:
            k, x, y = lights[r["no"]][0]; tag(ax, x + .52, y - .42, cn(fl, ltkey(fl, r), r["no"]), LT)
    if "P" in x_:
        (px, py), n = snap(fl, *x_["P"][:2]); t = (-n[1], n[0]); s = x_["P"][2]; sym(ax, "P", px, py, n)
        ax.add_patch(MPoly([(px + t[0] * (e + s) + n[0] * d, py + t[1] * (e + s) + n[1] * d) for e, d in ((-1.25, 0), (1.25, 0), (1.25, 3), (-1.25, 3))], closed=True, fill=False, ec=PW, lw=.6,
                           ls=(0, (2.5, 1.8)), zorder=11))
        ax.text(px + n[0] * .45, py + n[1] * .45, f"PANEL {p}", fontsize=3.8, color=PW, ha="center", va="center", fontweight="bold", zorder=14, path_effects=HALO, rotation=90 if n[0] else 0)
        (qx, qy), m = snap(fl, *x_["AC"])
        ax.annotate("", xy=(qx + m[0] * 1.7, qy + m[1] * 1.7), xytext=(qx - m[0] * .5, qy - m[1] * .5), arrowprops=dict(arrowstyle="-|>", color=PW, lw=.9), zorder=12)
        sym(ax, "X", qx + m[0] * .05, qy + m[1] * .05, m)
        ax.text(qx + m[0] * 2.0 + (0 if m[0] else 1.3), qy + m[1] * 2.0 + (.75 if m[0] else 0), f"AC condenser outside\nckt {cn(fl, 'AC')} · 30 A 240 V", fontsize=3.6, color=PW,
                ha="left" if m[0] > 0 else "center", va="center", zorder=14, linespacing=1.2)
    kn = keynotes(fl)
    for i, ((x, y), _t) in enumerate(kn): b.keynote(ax, i + 1, x, y, PW)
    bg.text(10.6, 9.9, "LEGEND", fontsize=7, fontweight="bold", color=INK, va="center")
    y = legend(bg, 10.6, 9.64) - .1
    bg.text(10.6, y, "KEYNOTES", fontsize=7, fontweight="bold", color=INK, va="center"); y -= .22
    for i, (_p, t) in enumerate(kn):
        bg.text(10.68, y, str(i + 1), fontsize=5.6, color=PW, fontweight="bold", va="center", ha="center")
        for j, ln in enumerate(b.wrap(t, 46)): bg.text(10.85, y - j * .125, ln, fontsize=5.3, color=INK, va="center")
        y -= .125 * len(b.wrap(t, 46)) + .07
    b.save(fig, number, pdf)


# ---------------------------------------------------------------------------------------------- E-001
GEN = ["Receptacles in bedrooms, living rooms and halls: no point along a wall is more than 6 ft from one, and every wall 2 ft or longer has one. Placed from the room "
       "sizes, then moved off door openings. All 15 and 20 A receptacles tamper-resistant. 16 in. to centre above the floor; counters 44 in.",
       "AFCI (AF) on every 120 V circuit to living rooms, bedrooms, halls, closets, kitchens and laundries. GFCI (GF) at baths, kitchen counters, laundry, within 6 ft "
       "of a sink, service receptacles and outdoors. DF = one breaker doing both. The 2020 code also asks for GFCI on the dryer and on outdoor equipment: confirm locally.",
       "Kitchens: two 20 A small-appliance circuits; no point of counter more than 2 ft from a GFCI receptacle. Where a window sits over the counter put the receptacle "
       "below the sill or beside it. Own circuits for the refrigerator, the gas range (120 V) and the hood / microwave. No dishwasher or disposal is shown: add circuits if fitted.",
       "Baths: one 20 A GFCI receptacle at each vanity, within 3 ft of the basin, one circuit per bath. Fan/light and vanity light on the lighting circuit. No switch or "
       "receptacle inside the tub or shower space.",
       "Laundry: 20 A washer receptacle; 30 A 240 V 4-wire dryer receptacle (dryers are electric).",
       "Mechanical closets (109, 208, 307): furnace on its own circuit with a switch at the unit; 120 V receptacle for the power-vent gas water heater; GFCI service "
       "receptacle; light and switch. The walls and ceiling are fire-rated board: seal every box and cable hole to keep the rating.",
       "AC condensers are outside and not drawn: 30 A 240 V circuit and a weatherproof disconnect within sight of each unit; size the breaker and wire to the nameplate. "
       "One weatherproof GFCI receptacle within 25 ft of each unit and at each flat's grade-level entry (may be the same one).",
       "Lighting is LED. Recessed lights under a roof or insulation: IC-rated and airtight. Closet lights: enclosed LED, 12 in. clear of shelves (6 in. if recessed). "
       "S3 = 3-way pair at both ends of stairs and long halls. Switches 48 in. up, on the latch side of the door: existing door swings are not known, so check each one.",
       "Alarms: hardwired with battery back-up, interconnected within each flat. Smoke alarm in every bedroom, outside each sleeping area and on each level; combined "
       "smoke + CO outside the bedrooms on every level (gas appliances). Where the plan allows keep them 3 ft from bath doors and supply registers and 10 ft from the range.",
       "Panels: one per flat, flush in a hall wall beside the mechanical closet, not in a closet or bath, 30 in. wide x 36 in. deep x 6 ft 6 in. high clear in front. "
       "Feeder from existing meter: route and size by electrician. Service size, grounding and bonding (water and gas pipe) to be checked and corrected by the electrician.",
       "Upper flat: one panel (C) on the main floor serves the main floor, the attic and stair hall 213 on the middle-flat level. Attic circuits rise in the old chimney "
       "chase next to the 3 in. stack; firestop at each floor. No circuit of one flat may serve another flat.",
       "Existing wiring is unknown. These sheets show the target layout for each whole flat. Existing devices that are grounded, sound and in the right place may be "
       "reused. Rooms 106, 206, 403, 404, 109, 208, 307 and all new closets are all-new wiring. Old ungrounded or knob-and-tube wiring found in opened walls is replaced.",
       "Circuit numbers are schedule references: the electrician assigns the panel spaces. Wire sizes are copper NM-B with ground (12-2 = two 12 AWG + ground). "
       "Device positions are good to about 6 in.; set the final positions on site."]
N001 = [("Basis of design", ["Design intent only, to be confirmed by", "the licensed electrician and the", "inspector. Not a permit drawing.", "Layout guide: NEC 2020 dwelling rules,",
                             "as adopted locally.", "One panel per flat, 120/240 V 1-phase:", "A lower 100 A, B middle 100 A,", "C upper flat + attic 125 A.",
                             "Gas ranges, furnaces and water heaters.", "Electric dryers. One outdoor AC", "condenser per flat."]),
        ("Assumed: confirm", ["Each flat has, or will get, its own", "meter. The service can carry three", "panels of this size.", "AC, furnace and water heater sizes", "(see the mechanical sheets)."]),
        ("Not known: verify on site", ["Where the meters, service and existing", "panels are, and their size.", "Existing wiring type and condition.", "Joist direction; what is below the",
                                       "lower flat. Feeder and cable routes", "are therefore not drawn."])]


def loads():
    rows = [["Load, VA (standard method)", "A lower", "B middle", "C upper"]]; f = [FLAT[k] for k in "ABC"]; lt = [3 * q["sf"] for q in f]; sub = [v + 4500 for v in lt]
    dem = [3000 + .35 * (v - 3000) for v in sub]; ac = [240 * q["ac"] for q in f]; tot = [d + 5000 + 1200 + 1500 + 500 + a * 1.25 for d, a in zip(dem, ac)]
    fm = lambda v: [f"{x:,.0f}" for x in v]  # noqa: E731
    rows += [["Floor area, sf (about)"] + fm([q["sf"] for q in f]), ["General lighting and receptacles, 3 VA/sf"] + fm(lt), ["Two small-appliance circuits, 1,500 each"] + ["3,000"] * 3,
             ["Laundry circuit"] + ["1,500"] * 3, ["After demand: first 3,000 at 100%, rest 35%"] + fm(dem), ["Electric dryer"] + ["5,000"] * 3, ["Furnace blower (assumed 1/2 hp)"] + ["1,200"] * 3,
             ["Hood / microwave"] + ["1,500"] * 3, ["Water heater vent + range ignition"] + ["500"] * 3, [f"AC condenser (assumed {f[0]['ac']} A; C {f[2]['ac']} A at 240 V)"] + fm(ac),
             ["25% of the largest motor (AC)"] + fm([a * .25 for a in ac]), ["Total"] + fm(tot), ["Amps at 240 V"] + [f"{v / 240:.0f} A" for v in tot], ["Panel"] + [f"{q['amps']} A" for q in f]]
    return rows


def notes_sheet(pdf):
    fig, bg, _ = b.bsheet("E-001", "Electrical notes, legend, panel schedules", 0, N001, sub="Rear building · all levels")
    bg.text(.5, 10.25, "ELECTRICAL NOTES, LEGEND, PANEL SCHEDULES", fontsize=10, fontweight="bold", color=INK, va="center")
    for i, k in enumerate("ABC"):
        f = FLAT[k]; x = .5 + i * 4.22
        bg.text(x, 9.9, f"PANEL {k} · {f['name'].upper()} · {f['amps']} A", fontsize=7, fontweight="bold", color=PW, va="center")
        bg.text(x, 9.74, f"120/240 V 1-phase, main breaker, {f['sp']} spaces or more. Flush in the hall by room {f['mech']}.", fontsize=5.2, color=GREY, va="center")
        table(bg, x, 9.62, [.3, .8, .42, 2.53], [["Ckt", "Breaker", "Wire", "Serves"]] + [[j + 1, c[1], c[2], c[3]] for j, c in enumerate(CK[k])], fs=5.3, rh=.158)
    y0 = 9.62 - .158 * (len(CK["C"]) + 1) - .3
    bg.text(.5, y0, "LOAD SUMMARY", fontsize=7, fontweight="bold", color=INK, va="center")
    y = table(bg, .5, y0 - .14, [2.3, .58, .58, .59], loads(), fs=5.3, rh=.15) - .13
    for ln in ["Nameplate figures are assumed: redo with the real units. Gas ranges assumed;", "an electric range or electric heat changes the totals. Lights are LED; the",
               "3 VA/sf figure is the code allowance, not the real lighting load."]:
        bg.text(.5, y, ln, fontsize=5.2, color=GREY, va="center"); y -= .125
    y -= .12; bg.text(.5, y, "SYMBOLS (same on E-101 to E-104)", fontsize=7, fontweight="bold", color=INK, va="center")
    legend(bg, .5, y - .24, LEG[:8], 5.3); legend(bg, 2.62, y - .24, LEG[8:], 5.3)
    bg.text(4.72, y0, "GENERAL NOTES", fontsize=7, fontweight="bold", color=INK, va="center")
    x, y = 4.72, y0 - .24
    for i, t in enumerate(GEN):
        ls = b.wrap(t, 84)
        if y - .128 * len(ls) < .62: x, y = 8.94, y0 - .24
        bg.text(x, y, f"{i + 1}", fontsize=5.5, color=PW, fontweight="bold", va="center")
        for j, ln in enumerate(ls): bg.text(x + .2, y - j * .128, ln, fontsize=5.3, color=INK, va="center")
        y -= .128 * len(ls) + .075
    b.save(fig, "E-001", pdf)


SHEETS = [("E-001", "Electrical notes, legend, panel schedules", notes_sheet)] + [
    (n, f"{b.LV[fl]['name']}: power, lighting, life safety", (lambda pdf, n=n, fl=fl: level(pdf, n, fl))) for n, fl in (("E-101", 3), ("E-102", 4), ("E-103", 5), ("E-104", 6))]

if __name__ == "__main__":
    from matplotlib.backends.backend_pdf import PdfPages
    with PdfPages(os.path.join(b.HERE, "drawings", "_test_e.pdf")) as pdf:
        for _n, _t, fn in SHEETS:
            fn(pdf)
    print("ok", [s[0] for s in SHEETS])
