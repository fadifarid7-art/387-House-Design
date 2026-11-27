"""390 Forest Ave builder set: ELECTRICAL sheets E-001 and E-101 to E-104 (power, lighting, life safety).
The house is gutted to the studs: every circuit, box, device, fixture and panel shown is new. Design intent only; NEC 2020 dwelling rules are the layout guide,
to be confirmed by the licensed electrician.
Receptacles, counter and appliance outlets, lights and bedroom alarms are placed from the plan model (b.LV, b.RANGE_FUEL);
switches, hall alarms and the outlets in the mechanical closets are hand-placed points that snap to the nearest wall."""
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
FLAT = {"A": dict(name="Lower flat", lv=3, amps=100, rec=125, sf=790, ac=18, mech="109", beds=[("103", "Bedroom 1"), ("104", "Bedroom 2")], baths=[("105", "Bath 1"), ("106", "Bath 2")]),
        "B": dict(name="Middle flat", lv=4, amps=100, rec=125, sf=870, ac=18, mech="208", beds=[("203", "Bedroom 1"), ("204", "Bedroom 2")], baths=[("205", "Bath 1"), ("206", "Bath 2")]),
        "C": dict(name="Upper flat + attic", lv=5, amps=125, rec=0, sf=1450, ac=22, mech="307", beds=[("303", "Bedroom 3"), ("304", "Bedroom 4"), ("401", "Attic bedroom 1"), ("402", "Attic bedroom 2")],
                  baths=[("305", "Bath 1"), ("403", "Attic bath A"), ("404", "Attic bath B")])}


def circuits(k):
    """Branch circuits of one flat: (key, breaker, wire, what it serves). AF = arc-fault, GF = ground-fault, DF = both in one breaker."""
    f = FLAT[k]; el = b.RANGE_FUEL[f["lv"]] == "electric"
    c = [("SA1", "20 A 1P DF", "12-2", "Kitchen counter receptacles A"), ("SA2", "20 A 1P DF", "12-2", "Kitchen counter B + wall recepts"), ("REF", "20 A 1P AF", "12-2", "Refrigerator"),
         ("RNG", "50 A 2P GF", "6-3", "Electric range, 240 V recept (14-50R)") if el else ("RNG", "20 A 1P AF", "12-2", "Gas range, 120 V receptacle"),
         ("MW", "20 A 1P AF", "12-2", "Range hood / microwave"), ("DW", "15 A 1P DF", "14-2", "Dishwasher, recept in sink cabinet")]
    c += [("B" + n, "20 A 1P GF", "12-2", f"{nm}: vanity receptacle") for n, nm in f["baths"]]
    c += [("LAU", "20 A 1P DF", "12-2", "Laundry: washer receptacle"), ("DRY", "30 A 2P GF", "10-3", "Dryer, 240 V receptacle (14-30R)"), ("FUR", "15 A 1P AF", "14-2", "Gas furnace, switch at the unit"),
          ("WH", "20 A 1P AF", "12-2", "Water heater vent + service recepts"), ("AC", "30 A 2P", "10-2", "AC condenser, disconnect at the unit")]
    c += [("R" + n, "15 A 1P AF", "14-2", f"{nm}: receptacles") for n, nm in f["beds"]]
    c += [("LIV", "20 A 1P AF", "12-2", "Living room + hall receptacles"), ("LT1", "15 A 1P AF", "14-2", "Lights: living/kitchen/halls + alarms"),
          ("LT2", "15 A 1P AF", "14-2", "Lights + fans: beds, baths, closets")]
    return c + ([("LT3", "15 A 1P AF", "14-2", "Attic: lights and fans")] if k == "C" else [])


CK = {k: circuits(k) for k in FLAT}
CN = {k: {c[0]: i + 1 for i, c in enumerate(CK[k])} for k in FLAT}


def cn(fl, key, no=""):
    """Circuit tag for a device. Room 213 (stair hall on the middle-flat level) belongs to the upper flat: tags C.."""
    return f"C{CN['C'][key]}" if no == "213" else str(CN[PANEL_OF[fl]][key])


# Hand-placed items per level, as points about 0.3 ft off the wall inside the room; snap() puts them on the wall face.
# P panel (x, y, slide of the clear floor box along the wall) · AC point just outside the nearest outside wall · SW (room or group, x, y, type)
# RX (symbol, x, y, circuit[, room, free angle]): water heater and service receptacles in the mechanical closets, odd walls · FIX lights that replace the automatic ones (c = small) · LS alarms (in a bedroom: replaces the automatic one)
# KN keynote positions (x, y[, leader to x, y])
X = {3: dict(P=(22.8, 10.2, 0), AC=(31.0, 14.5),
             SW=[("101", 1.4, 18.0, "S3"), ("101", 12.3, 13.42, "S3"), ("102", 15.8, 15.4, "2S"), ("103", 12.4, 12.5, "S"), ("112", 7.4, 10.0, "S"), ("104", 22.8, 13.4, "S"), ("111", 25.8, 15.6, "S"),
                 ("105", 18.45, 9.3, "2S"), ("106", 16.4, 9.0, "2S"), ("107", 16.5, 9.9, "S3"), ("107", 22.9, 12.5, "S3"), ("108", 26.6, 12.5, "S"), ("109", 20.4, 12.5, "S"), ("110", 27.0, 3.9, "S")],
             RX=[("D", 20.5, 15.3, "WH"), ("G", 20.4, 13.4, "WH")],
             FIX={"109": [("c", 18.37, 14.3)], "108": [("C", 28.4, 7.6)], "106": [("F", 14.2, 5.2)], "105": [("F", 20.9, 7.2)], "107": [("C", 15.9, 11.2), ("C", 22.3, 11.2)], "110": [("c", 27.7, 3.14)]},
             LS=[("SC", 24.5, 11.5)], KN=[(25.4, 10.6, 23.4, 10.0), (14.3, 13.5, 16.3, 13.5), (33.3, 16.3), (15.9, 19.9)]),
     4: dict(P=(16.5, 12.4, -.35), AC=(16.4, 28.1),
             SW=[("201", 34.3, 9.65, "S3"), ("201", 21.7, 11.15, "S3"), ("202", 20.1, 17.8, "2S"), ("203", 14.85, 18.4, "S"), ("204", 10.1, 12.3, "S"), ("211", 10.1, 3.5, "S"), ("205", 12.0, 17.0, "2S"),
                 ("206", 14.0, 8.2, "2S"), ("207", 15.8, 13.0, "S"), ("210", 19.2, 17.1, "S3"), ("210", 15.4, 17.1, "S3"), ("208", 19.2, 18.0, "S"), ("209", 22.55, 12.8, "S"), ("213", 30.75, 22.1, "S3")],
             RX=[("D", 18.6, 21.0, "WH"), ("G", 19.25, 20.45, "WH"), ("R", 27.5, 21.35, "LIV", "213"), ("R", 32.4, 11.5, "LIV", "", True)],
             FIX={"205": [("F", 9.0, 15.3)], "206": [("F", 15.1, 6.8)], "207": [("C", 13.8, 10.3)], "210": [("C", 13.9, 15.5)], "208": [("c", 17.5, 18.1)], "209": [("C", 19.55, 12.6)],
                  "213": [("C", 29.0, 25.0), ("C", 18.9, 25.9)]},
             LS=[("SC", 18.2, 15.2), ("SC", 15.6, 11.3), ("SD", 26.4, 25.9)],
             KN=[(16.4, 14.5, 16.95, 12.9), (13.2, 21.6, 15.5, 20.8), (14.2, 28.8), (27.3, 16.0), (23.0, 22.3)]),
     5: dict(P=(11.5, 16.85, 0), AC=(17.9, -.5),
             SW=[("301", 11.6, 12.8, "S"), ("311", 15.0, 4.2, "S"), ("302", 6.9, 13.72, "2S"), ("308", 9.55, 17.6, "S"), ("303", 23.25, 12.4, "S"), ("309", 18.6, 4.55, "S"), ("304", 24.15, 18.5, "S"),
                 ("305", 16.15, 17.78, "2S"), ("306", 12.9, 16.87, "S3"), ("306", 23.25, 18.3, "S3"), ("ST1", 17.2, 18.9, "S3"), ("ST2", 23.25, 19.3, "S3"), ("307", 15.5, 13.72, "S")],
             RX=[("D", 19.95, 10.8, "WH"), ("G", 17.7, 10.65, "WH")],
             FIX={"306": [("C", 13.5, 15.3), ("C", 20.5, 15.3)], "312": [], "ST1": [("C", 18.4, 18.5)], "ST2": [("C", 21.9, 19.7)], "307": [("c", 17.72, 12.4)], "308": [("C", 8.82, 17.2)], "309": [("c", 16.8, 5.1)]},
             LS=[("SC", 20.2, 16.5)], KN=[(12.0, 15.2, 11.5, 17.0), (14.4, 11.6, 15.7, 11.6), (15.7, -1.6), (5.6, 21.65), (17.0, 8.0), (28.7, 25.4, 27.6, 25.4)]),
     6: dict(SW=[("401", 16.0, 13.5, "S"), ("406", 13.75, 12.8, "S"), ("403", 9.9, 16.5, "2S"), ("402", 20.65, 16.7, "S"), ("407", 24.2, 20.1, "S"), ("404", 22.5, 8.4, "2S"), ("405", 17.45, 16.2, "S3")],
             RX=[], FIX={"403": [("F", 13.5, 17.8)], "404": [("F", 19.6, 8.95)], "405": [("C", 18.6, 15.2), ("C", 18.6, 22.3)]},
             LS=[("SC", 19.3, 14.0), ("SD", 8.2, 13.9)], KN=[(15.45, 9.55, 17.3, 8.9), (23.3, 9.6), (5.0, 13.6), (2.0, 9.4)])}


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
    if "P" in X[fl]:      # nothing else in the wall at the panel, on either face
        x, y = X[fl]["P"][:2]; out.append((x - 1.1, y - 1.1, x + 1.1, y + 1.1))
    return unary_union([box(*q) for q in out]).difference(unary_union([box(*q).buffer(.05) for q in L["fix"]] or [Point(0, -99)]))      # a wall the scan missed closes an opening


def clear_depth(fl, p, n, t, s):
    """Least clear depth (ft) in front of a panel, across its 30 in. working width, to the first wall on the plan."""
    S = solid(fl)
    return min(next((d for d in np.arange(.1, 6, .05) if S.contains(Point(p[0] + t[0] * (e + s) + n[0] * d, p[1] + t[1] * (e + s) + n[1] * d))), 6) for e in np.linspace(-1.2, 1.2, 9))


@lru_cache(None)
def fxboxes(fl):
    return unary_union([box(*f[1:5]).buffer(.12) for f in b.LV[fl]["fx"] if len(f) >= 5 and not isinstance(f[3], str) and f[0] != "xequip"])      # xequip is being removed


def snap(fl, x, y, free=False):
    """Nearest wall face to a point just inside a room: (point on the face, unit normal pointing back into the room). free = wall at an angle."""
    p = nearest_points(solid(fl).boundary, Point(x, y))[0]; dx, dy = x - p.x, y - p.y; d = math.hypot(dx, dy)
    return (p.x, p.y), ((dx / d, dy / d) if free else (1 if dx > 0 else -1, 0) if abs(dx) > abs(dy) else (0, 1 if dy > 0 else -1))


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


def fit(fl, at, half, offs):
    """Slide outlet positions along the wall, inside the width of the appliance, until none sits in a door or window opening."""
    for k in (1, .67, .56):
        for sh in sorted(np.arange(-1.5, 1.51, .05), key=abs):
            o = [v * k + sh for v in offs]
            if all(abs(v) <= half - .25 and not gaps(fl).contains(Point(at(v))) for v in o): return o
    return offs


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


def leg(a, p, q, rad=.22, away=None):
    """Dashed switch leg. away = a point (the room name) the curve should bend away from."""
    if away:
        m = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2); d = (rad * (q[1] - p[1]), -rad * (q[0] - p[0]))
        rad = rad if math.dist((m[0] + d[0], m[1] + d[1]), away) >= math.dist((m[0] - d[0], m[1] - d[1]), away) else -rad
    a.add_patch(FancyArrowPatch(p, q, connectionstyle=f"arc3,rad={rad}", arrowstyle="-", color=LT, lw=.45, ls=(0, (2.4, 1.8)), zorder=10, shrinkA=2.5, shrinkB=2.5))


LEG = [("R", "Duplex receptacle (number = circuit)"), ("G", "GFCI receptacle, 20 A"), ("D", "Dedicated receptacle, one appliance"), ("Q", "240 V receptacle: dryer 30 A, range 50 A"),
       ("X", "Disconnect (D) or junction box (J)"), ("P", "New panel; dashed = 30 x 36 in. clear"), ("S", "Switch; S3 = 3-way pair; 2S = two in a box"),
       ("C", "Ceiling light; small = closet (enclosed)"), ("RL", "Recessed LED light"), ("V", "Vanity light over the basin"), ("F", "Bath exhaust fan with light"),
       ("leg", "Switch leg: switch to its lights"), ("uc", "Under-cabinet LED strip"), ("SD", "Smoke alarm, hardwired, interconnected"), ("SC", "Smoke + CO alarm, hardwired")]


def legend(bg, x, y, items=LEG, fs=5.6, rh=.215):
    for k, txt in items:
        if k == "leg": leg(bg, (x, y - .03), (x + .36, y - .03), .35)
        elif k == "uc": bg.plot([x, x + .34], [y, y], color=LT, lw=1.3)
        elif k in ("C", "RL", "F", "SD", "SC", "P"): sym(bg, k, x + .17, y + (.045 if k == "P" else 0), s=.25)
        else: sym(bg, k, x + .17, y - .08, (0, 1), .25, "S3" if k == "S" else 1.2)
        for i, ln in enumerate(txt.split("\n")):
            bg.text(x + .47, y - i * .13, ln, fontsize=fs, color=INK, va="center")
        y -= rh + .13 * txt.count("\n")
    return y


# ---------------------------------------------------------------------------------------------- devices of one level
def kitchen_row(fl, r):
    """Three recessed lights over the aisle: 1 ft in front of the longest run of cabinets and appliances, kept off the run on the return wall."""
    x0, y0, x1, y1 = r["rects"][0]
    bs = [(f[1:5], back(fl, f[1:5], r)[1]) for f in b.LV[fl]["fx"] if f[0] in ("fridge", "range", "base", "sinkbase", "dw") and room_at(fl, (f[1] + f[3]) / 2, (f[2] + f[4]) / 2) is r]
    tot = {}
    for q, n in bs: tot[n] = tot.get(n, 0) + (q[3] - q[1] if n[0] else q[2] - q[0])
    n = max(tot, key=tot.get); a = 1 if n[0] else 0; own = [q for q, m in bs if m == n]
    c = {(1, 0): max(q[2] for q in own) + 1, (-1, 0): min(q[0] for q in own) - 1, (0, 1): max(q[3] for q in own) + 1, (0, -1): min(q[1] for q in own) - 1}[n]
    lo, hi = min(q[a] for q in own) + 1.2, max(q[a + 2] for q in own) - 1.2; mid = (lo + hi) / 2
    for q, m in bs:
        if m != n: lo, hi = (max(lo, q[a + 2] + .8), hi) if q[a + 2] < mid else (lo, min(hi, q[a] - .8))
    return [("RL", c, v) if n[0] else ("RL", v, c) for v in np.linspace(lo, hi, 3)]


def clear(r, x, y):
    """Move a ceiling item off the room name printed on the base plan."""
    lx, ly = r["lab"]
    return (x, ly + (1.0 if y >= ly else -1.0)) if abs(x - lx) < 1.5 and abs(y - ly) < .8 else (x, y)


def auto_lights(fl, r):
    x0, y0, x1, y1 = r["rects"][0]; cx, cy, w, h = (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0; k = r["kind"]
    if k == "bed":
        return [("C", cx, cy)] if fl != 6 else [("C", x0 + w * q, cy) if w > h else ("C", cx, y0 + h * q) for q in (.25, .75)]
    if k == "living": return [("RL", x0 + w * i, y0 + h * j) for i in (.25, .75) for j in (.25, .75)]
    if k == "kitchen": return kitchen_row(fl, r)
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
    lights.update({k: list(v) for k, v in x_["FIX"].items() if k not in lights and v})
    tubs = unary_union([box(*q[1:5]) for q in L["fx"] if q[0] == "tub"]); cab, dws, cnt = {}, [], []
    for f in L["fx"]:      # outlets that follow the fixtures and appliances
        k = f[0]
        if k not in ("fridge", "range", "base", "sinkbase", "dw", "washer", "dryer", "van", "furnace"): continue
        bx = f[1:5]; r = room_at(fl, (bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2); (px, py), n, half = back(fl, bx, r); t = (-n[1], n[0])
        at = lambda s, px=px, py=py, t=t: (px + t[0] * s, py + t[1] * s)  # noqa: E731
        if k == "range":      # electric: 50 A 240 V receptacle; gas: 120 V receptacle. Hood / microwave outlet beside it on plan (in the cabinet above)
            o = fit(fl, at, half, [-.42, .42]); D += [("Q" if b.RANGE_FUEL.get(fl) == "electric" else "D", *at(o[0]), n, cn(fl, "RNG"), -1), ("D", *at(o[1]), n, cn(fl, "MW"), 1)]
        elif k in ("fridge", "washer", "dryer"):
            D.append(("Q" if k == "dryer" else "D", *at(fit(fl, at, half, [0])[0]), n, cn(fl, {"fridge": "REF", "washer": "LAU", "dryer": "DRY"}[k]), None))
        elif k == "furnace": D.append(("X", *at(0), n, "", None))
        elif k == "van":
            e = max((-half, half), key=lambda s: tubs.distance(Point(at(s))))
            D += [("G", *at(e), n, cn(fl, "B" + r["no"]), None), ("V", px, py, n, "", half * 1.4)]; lights[r["no"]].append(("V", px + n[0] * .15, py + n[1] * .15))
        else:
            a = px * t[0] + py * t[1]; cab.setdefault((n, round(px * n[0] + py * n[1], 1)), []).append((a - half, a + half, k))
            if k == "dw": dws.append((at, t, n))
    for (n, w), segs in cab.items():      # counters: each run of base cabinet, dishwasher and sink base along a wall; no point more than 2 ft from a GFCI, none behind the bowl
        t = (-n[1], n[0]); segs.sort(); runs = [[segs[0]]]; P = lambda v, n=n, w=w, t=t: (n[0] * w + t[0] * v, n[1] * w + t[1] * v)  # noqa: E731
        for q in segs[1:]: runs[-1].append(q) if q[0] - runs[-1][-1][1] < .2 else runs.append([q])
        for g in runs:
            a0, a1 = g[0][0], g[-1][1]; m = math.ceil((a1 - a0) / 4 - 1e-6); strips.append((P(a0 + .1), P(a1 - .1), n))
            for i in range(m):
                v = a0 + (i + .5) * (a1 - a0) / m
                for s0, s1, k in g:
                    lo, hi = .8 * s0 + .2 * s1 - .3, .2 * s0 + .8 * s1 + .3
                    if k == "sinkbase" and lo < v < hi: v = min((lo, hi), key=lambda q: (not a0 + .29 <= q <= a1 - .29, abs(q - v)))
                if not gaps(fl).contains(Point(P(v))): cnt.append(P(v)); D.append(("G", *P(v), n, cn(fl, "SA2" if len(cnt) % 2 == 0 else "SA1"), None))
    for at, t, n in dws:      # dishwasher outlet: kept clear of the counter receptacles on plan; in fact it goes in the sink cabinet
        q = next((at(s) for s in (0, -.55, .55, -.8, .8) if all(math.dist(at(s), c) >= .62 for c in cnt)), at(0)); g = min(cnt, key=lambda c: math.dist(c, q), default=q)
        D.append(("D", *q, n, cn(fl, "DW"), -1 if (g[0] - q[0]) * t[0] + (g[1] - q[1]) * t[1] > 0 else 1))
    for e in x_["RX"]:
        p, n = snap(fl, e[1], e[2], len(e) > 5); D.append((e[0], *p, n, "" if e[3] in ("FUR", "WH") else cn(fl, e[3], e[4] if len(e) > 4 else ""), None))
    first = {}; lab = {r["no"]: r["lab"] for r in L["rooms"] if r["kind"] != "closet"}
    for tgt, x, y, typ in x_["SW"]:      # switches, each tied to the nearest light of its room; lights of a room chained together
        p, n = snap(fl, x, y); D.append(("S", *p, n, "", typ)); c = (p[0] + n[0] * .32, p[1] + n[1] * .32); first.setdefault(tgt, c)
        q = min(lights[tgt], key=lambda v: math.dist(c, v[1:3])); legs.append((c, q[1:3], lab.get(tgt)))
    for tgt, fx in lights.items():
        todo = list(fx); cur = min(todo, key=lambda v: math.dist(first.get(tgt, v[1:3]), v[1:3])); todo.remove(cur)
        while todo:
            nxt = min(todo, key=lambda v: math.dist(cur[1:3], v[1:3])); legs.append((cur[1:3], nxt[1:3], lab.get(tgt))); todo.remove(nxt); cur = nxt
        D += [(k, x, y, (0, 1), "", None) for k, x, y in fx if k != "V"]
    for r in L["rooms"]:      # smoke alarm in every bedroom, part-way from the middle of the room to the door switch
        if r["kind"] == "bed" and not any(box(*q).contains(Point(e[1:3])) for q in r["rects"] for e in x_["LS"]):
            x0, y0, x1, y1 = r["rects"][0]; c = ((x0 + x1) / 2, (y0 + y1) / 2); s = first.get(r["no"], c)
            D.append(("SD", *clear(r, c[0] + .45 * (s[0] - c[0]), c[1] + .45 * (s[1] - c[1])), (0, 1), "", None))
    D += [(k, x, y, (0, 1), "", None) for k, x, y in x_["LS"]]
    return D, lights, legs, strips


def keynotes(fl):
    p = PANEL_OF[fl]; f = FLAT[p]; c = CN[p]; kn = list(X[fl]["KN"])
    if fl == 6:
        t = ["Circuits from panel C (main floor) come up in the old chimney chase beside the stack. Firestop at the floor.",
             "Bath B switches are outside the door: no wall inside is clear of the tub.",
             "Keep lights and alarms on the flat 7'-8\" ceiling. Any light in the slope: IC-rated, airtight.",
             "Knee walls: check there is depth for a box before cutting in; if not, use a surface box."]
    else:
        rg = next(q for q in b.LV[fl]["fx"] if q[0] == "range"); (px, py), n, _h = back(fl, rg[1:5], room_at(fl, rg[1], rg[2])); d = rg[3] - rg[1] if n[0] else rg[4] - rg[2]
        kn[3] = kn[3] + (px + n[0] * d, py + n[1] * d)      # leader to the front of the range, wherever the model puts it
        (q, m), sl = snap(fl, *X[fl]["P"][:2]), X[fl]["P"][2]; dp = clear_depth(fl, q, m, (abs(m[1]), abs(m[0])), sl)
        t = [f"New panel {p}, {f['amps']} A" + (f" ({f['rec']} A recommended)" if f["rec"] else "") + ", flush in the hall wall. Keep the dashed 30 x 36 in. floor clear. Feeder from the "
             "new meter stack: route and size by electrician. "
             + (f"Clear depth here is only about {dp * 12:.0f} in. on the scan: measure it; if it is under 36 in., use the deeper west end of this hall." if dp < 3 else
                "30 x 36 in. clear floor checks on the plan."),
             f"Mechanical closet: furnace switch D (ckt {c['FUR']}); water heater receptacle and GFCI service receptacle (ckt {c['WH']}); light and switch.",
             f"New AC condenser outside, placed by the mechanical sheets. Ckt {c['AC']}, 30 A 240 V, weatherproof disconnect at the unit."
             + (" Run down the outside wall." if fl == 5 else ""),
             f"Range wall: {'50 A 240 V range receptacle' if b.RANGE_FUEL[fl] == 'electric' else 'gas range, 120 V receptacle'} (ckt {c['RNG']}); hood / microwave outlet in the cabinet "
             f"above ({c['MW']}); dishwasher outlet in the sink cabinet ({c['DW']}). Under-cabinet strip on the kitchen switch."
             + (" The wall behind the range is not in the scan (A-102): confirm it." if fl == 4 else "")]
        if fl == 4: t += [f"Stair hall 213 is the upper flat's: fed from panel C (tags C{CN['C']['LT1']}, C{CN['C']['LIV']}). 3-way switch at the entry door, latch side: verify the swing."]
        if fl == 5: t += ["Attic circuits rise in the old chimney chase. Firestop at the floor.",
                          "The old furnace and water heater here (dashed) are removed; the new ones go in closet 307. Room 304 is wired as a bedroom."]
    return list(zip(kn, t))


def sheet_notes(fl):
    p = PANEL_OF[fl]; f = FLAT[p]
    more = {3: [], 4: ["Tags C.. in stair hall 213 are panel C", "(upper flat), not panel B."], 5: ["Panel C also feeds the attic (E-104) and", "stair hall 213 (E-102)."],
            6: ["No panel up here: the attic is on panel C", "on the main floor (E-103)."]}[fl]
    low = ["One data / coax outlet in each bedroom,", "home runs down the chimney chase."] if fl == 6 else ["One data / coax outlet in each bedroom and", "the living room; doorbell at the entry;",
                                                                                                           "thermostat cable from furnace to hall."]
    return [(f"Panel {p} circuits · {f['amps']} A" + (f" ({f['rec']} A advised)" if f["rec"] else ""), [f"{i + 1:>2}  {c[1][:4]} {c[1][5:7]}  {c[3]}" for i, c in enumerate(CK[p])]),
            ("All new · read with E-001", more + ["Gutted to the studs: every circuit, box,", "device, fixture and the panel is new.", "Design intent, to be confirmed by the", "licensed electrician."]),
            ("Low voltage (not drawn)", low)]


def level(pdf, number, fl):
    L = b.LV[fl]; p = PANEL_OF[fl]; x_ = X[fl]
    fig, bg, ax = b.bsheet(number, f"{L['name']}: power, lighting, life safety", fl, sheet_notes(fl))
    b.draw_base(ax, fl, "trade")
    D, lights, legs, strips = devices(fl)
    for a0, a1, n in strips:
        ax.plot([a0[0] + n[0] * .1, a1[0] + n[0] * .1], [a0[1] + n[1] * .1, a1[1] + n[1] * .1], color=LT, lw=1.3, zorder=11, solid_capstyle="butt")
    for a0, a1, away in legs: leg(ax, a0, a1, away=away)
    used = [(x + n[0] * .32, y + n[1] * .32) for k, x, y, n, t, arg in D if k in ("R", "G", "D", "Q", "X", "S")]      # symbol centres, then tags as they are placed
    names = [(r["lab"], 1.3, .55) for r in L["rooms"] if r["kind"] != "closet"] + [(((f[1] + f[3]) / 2, (f[2] + f[4]) / 2), .5, .3) for f in L["fx"] if f[0] in ("fridge", "dw", "washer", "dryer")]
    for k, x, y, n, t, arg in D:
        sym(ax, k, x, y, n, 1.0, arg)
        if t:      # circuit number: in front of the symbol, or beside it (appliance outlets first try beside), wherever nothing else is
            c = (x + n[0] * .3, y + n[1] * .3); sd = [(c[0] - n[1] * .58 * v, c[1] + n[0] * .58 * v) for v in ((arg or 1), -(arg or 1))]; fr = (x + n[0] * .86, y + n[1] * .86)
            free = lambda q: all(math.dist(q, u) > .45 for u in used if math.dist(u, c) > .1) and not any(abs(q[0] - m[0]) < w and abs(q[1] - m[1]) < h for m, w, h in names)  # noqa: E731
            q = next((q for q in (sd + [fr] if k in ("D", "Q") else [fr] + sd) if free(q)), fr); used.append(q); tag(ax, *q, t)
    kinds = {r["no"]: r["kind"] for r in L["rooms"]}
    for g, fx in lights.items():      # lighting circuit number at one light per room or stair group
        tag(ax, fx[0][1] + .52, fx[0][2] - .42, cn(fl, "LT3" if fl == 6 else "LT2" if kinds.get(g) in ("bed", "bath", "closet") else "LT1", g), LT)
    if "P" in x_:
        (px, py), n = snap(fl, *x_["P"][:2]); t = (abs(n[1]), abs(n[0])); s = x_["P"][2]; sym(ax, "P", px, py, n)
        c = [(px + t[0] * (e + s) + n[0] * d, py + t[1] * (e + s) + n[1] * d) for e, d in ((-1.25, 0), (1.25, 0), (1.25, 3), (-1.25, 3))]
        for (x0, y0), (x1, y1) in zip(c, c[1:] + c[:1]):      # 30 x 36 in. clear floor, dashed, broken where a room name sits
            run = []
            for q in [(x0 + (x1 - x0) * u, y0 + (y1 - y0) * u) for u in np.linspace(0, 1, 61)] + [None]:
                if q and not any(abs(q[0] - r["lab"][0]) < .8 and abs(q[1] - r["lab"][1]) < .45 for r in L["rooms"]): run.append(q); continue
                if len(run) > 1: ax.plot(*zip(*run), color=PW, lw=.6, ls=(0, (2.5, 1.8)), zorder=11)
                run = []
        ax.text(px + n[0] * .45, py + n[1] * .45, f"PANEL {p}", fontsize=3.8, color=PW, ha="center", va="center", fontweight="bold", zorder=14, path_effects=HALO, rotation=90 if n[0] else 0)
        (qx, qy), m = snap(fl, *x_["AC"])
        ax.annotate("", xy=(qx + m[0] * 1.7, qy + m[1] * 1.7), xytext=(qx - m[0] * .5, qy - m[1] * .5), arrowprops=dict(arrowstyle="-|>", color=PW, lw=.9), zorder=12)
        sym(ax, "X", qx + m[0] * .05, qy + m[1] * .05, m)
        ax.text(qx + m[0] * 2.0 + (0 if m[0] else 1.3), qy + m[1] * 2.0 + (.75 if m[0] else 0), f"New AC condenser outside\nckt {cn(fl, 'AC')} · 30 A 240 V", fontsize=3.6, color=PW,
                ha="left" if m[0] > 0 else "center", va="center", zorder=14, linespacing=1.2)
    kn = keynotes(fl)
    for i, (q, _t) in enumerate(kn):
        if len(q) > 2: ax.plot([q[0], q[2]], [q[1], q[3]], color=PW, lw=.5, zorder=19)
        b.keynote(ax, i + 1, q[0], q[1], PW)
    bg.text(10.6, 9.9, "LEGEND", fontsize=7, fontweight="bold", color=INK, va="center")
    y = legend(bg, 10.6, 9.64) - .1
    bg.text(10.6, y, "KEYNOTES", fontsize=7, fontweight="bold", color=INK, va="center"); y -= .22
    for i, (_p, t) in enumerate(kn):
        bg.text(10.68, y, str(i + 1), fontsize=5.6, color=PW, fontweight="bold", va="center", ha="center")
        for j, ln in enumerate(b.wrap(t, 46)): bg.text(10.85, y - j * .125, ln, fontsize=5.3, color=INK, va="center")
        y -= .125 * len(b.wrap(t, 46)) + .07
    b.save(fig, number, pdf)


# ---------------------------------------------------------------------------------------------- E-001
GEN = ["All new: the house is gutted to the studs. All existing wiring, devices, fixtures and panels are removed; every circuit, box, device, fixture and all three "
       "panels on these sheets are new. Nothing existing is reused.",
       "Service: new service entrance and a new 3-meter stack, sized by the electrician and the utility for three panels: A lower flat 100 A, B middle flat 100 A, "
       "C upper flat and attic 125 A. Recommended: 125 A for A and B as well, because cooling and electric ranges stay in (see the load summary). New grounding "
       "electrode system and bonding of water and gas pipe.",
       "Panels: one per flat, flush in a hall wall, not in a closet or bath, with 30 in. wide x 36 in. deep x 6 ft 6 in. high clear in front. Feeder from the new meter "
       "stack: route and size by electrician. No circuit of one flat may serve another flat. Panel C on the main floor also serves the attic and stair hall 213.",
       "Rough-in with the walls open: run cable through holes bored in the middle of the studs, with nail plates wherever a hole is within 1 1/4 in. of the stud face. "
       "Fire-block every stud bay at floor and ceiling lines, and firestop every hole through a floor, ceiling or wall between flats with a listed system. Attic "
       "circuits rise in the old chimney chase next to the 3 in. stack.",
       "Receptacles in bedrooms, living rooms and halls: no point along a wall is more than 6 ft from one, and every wall 2 ft or longer has one. Placed from the room "
       "sizes, then moved off door openings. All 15 and 20 A receptacles tamper-resistant. 16 in. to centre above the floor; counters 44 in.",
       "AFCI (AF) on every 120 V circuit to living rooms, bedrooms, halls, closets, kitchens and laundries. GFCI (GF) at baths, kitchen counters, laundry, within 6 ft "
       "of a sink, service receptacles and outdoors. DF = one breaker doing both. The 2020 code also asks for GFCI on the dryer, the dishwasher, a range receptacle "
       "within 6 ft of a sink and outdoor equipment: confirm locally.",
       "Kitchens: two 20 A small-appliance circuits. Counter receptacles follow the cabinet run (base cabinets, dishwasher, sink base): no point of counter more than "
       "2 ft from a GFCI receptacle, none behind the bowl; where a window is over the counter, below the sill or beside it. Own circuits for the refrigerator, the "
       "range, the hood / microwave and the dishwasher (15 A, receptacle in the sink cabinet). No disposal is shown.",
       "Ranges: electric in the lower and middle flats: 50 A 240 V 4-wire receptacle (14-50R). Gas in the upper flat: 120 V receptacle. If a range changes fuel, "
       "change its circuit and re-run the load.",
       "Baths: one 20 A GFCI receptacle at each vanity, within 3 ft of the basin, one circuit per bath. Fan/light and vanity light on the lighting circuit. No switch or "
       "receptacle inside the tub or shower space.",
       "Laundry: 20 A washer receptacle; 30 A 240 V 4-wire dryer receptacle (dryers are electric).",
       "Mechanical closets (109, 208, 307): furnace on its own circuit with a switch at the unit; 120 V receptacle for the power-vent gas water heater; GFCI service "
       "receptacle; light and switch. The walls and ceiling are fire-rated board: seal every box and cable hole to keep the rating.",
       "Cooling is part of the work: one new condenser per flat, outside (placed on the mechanical sheets). 30 A 240 V circuit and a weatherproof disconnect within "
       "sight of each unit, sized to the nameplate. One weatherproof GFCI receptacle within 25 ft of each unit and at each flat's grade-level entry (may be the same one).",
       "Lighting is LED. Recessed lights under a roof or insulation: IC-rated and airtight. Closet lights: enclosed LED, 12 in. clear of shelves (6 in. if recessed). "
       "S3 = 3-way pair at both ends of stairs and long halls. Switches 48 in. up, on the latch side of the door: check each swing against the A sheets.",
       "Alarms: hardwired with battery back-up, interconnected within each flat. Smoke alarm in every bedroom, outside each sleeping area and on each level; combined "
       "smoke + CO outside the bedrooms on every level (gas appliances). Where the plan allows keep them 3 ft from bath doors and supply registers and 10 ft from the range.",
       "Low voltage (not drawn; a line item on each plan): one data / coax outlet in each bedroom and living room, home runs to a small panel beside each load centre; "
       "doorbell at each flat's entry; thermostat cable from each furnace to its hall. Keep low-voltage cable in its own holes, 2 in. or more from power cable.",
       "Circuit numbers are schedule references: the electrician assigns the panel spaces. A blue number by a receptacle and an orange number by one light in each room "
       "is the circuit in that flat's panel; tags C.. on E-102 are panel C. Breakers: AF arc-fault, GF ground-fault, DF both, 1P / 2P poles. Wire is copper NM-B with "
       "ground (12-2 = two 12 AWG + ground). Device positions are good to about 6 in.: set them on site."]
N001 = [("Basis of design", ["Gutted to the studs: everything on these", "sheets is new. Design intent only, to be", "confirmed by the licensed electrician", "and the inspector. Layout guide: NEC",
                             "2020 dwelling rules, as adopted locally.", "Electric ranges in the lower and middle", "flats, gas in the upper. Gas furnaces", "and water heaters, electric dryers, a",
                             "dishwasher in every kitchen, new cooling."]),
        ("New service", ["New service entrance and a new 3-meter", "stack, sized by the electrician and the", "utility for three panels: 100 A, 100 A", "and 125 A. Recommended: 125 A for the",
                         "lower and middle flats too, because", "cooling and electric ranges stay in."]),
        ("There now (to be removed)", ["Overhead drop; 100 A panels (General", "Electric, Murray); ungrounded, loose", "and painted receptacles; open splices;", "smoke alarms and GFCIs missing or",
                                       "miswired; window units. All of it goes."]),
        ("Not known: verify on site", ["Where the utility wants the meter stack,", "joist direction, what is below the lower", "flat. Feeder and cable routes are", "therefore not drawn."])]


def loads():
    """Feeder load of each flat by the optional method (NEC 220.82), with the standard-method amps for comparison."""
    f = [FLAT[k] for k in "ABC"]; lt = [3 * q["sf"] for q in f]; rng = [12000 if b.RANGE_FUEL[q["lv"]] == "electric" else 0 for q in f]; ac = [240 * q["ac"] for q in f]
    gen = [a + 4500 + 5000 + r + 1200 + 1500 + 1700 for a, r in zip(lt, rng)]; dem = [10000 + .4 * (g - 10000) for g in gen]; tot = [d + a for d, a in zip(dem, ac)]
    std = [(3000 + .35 * (a + 1500) + 5000 + (8000 if r else 0) + .75 * 4400 + 1.25 * c) / 240 for a, r, c in zip(lt, rng, ac)]
    fm = lambda v: [f"{x:,.0f}" if x else "gas" for x in v]  # noqa: E731
    return [["Load, VA (optional method, NEC 220.82)", "A lower", "B middle", "C upper"], ["Floor area, sf (about)"] + fm([q["sf"] for q in f]),
            ["General lighting and receptacles, 3 VA/sf"] + fm(lt), ["Two small-appliance circuits + laundry circuit"] + ["4,500"] * 3, ["Electric dryer"] + ["5,000"] * 3,
            ["Range (electric: 12 kW nameplate assumed)"] + fm(rng), ["Dishwasher"] + ["1,200"] * 3, ["Hood / microwave"] + ["1,500"] * 3, ["Furnace blower + water heater vent"] + ["1,700"] * 3,
            ["Sum"] + fm(gen), ["First 10,000 at 100%, the rest at 40%"] + fm(dem), [f"AC condenser at 100% (assumed {f[0]['ac']} A; C {f[2]['ac']} A)"] + fm(ac), ["Total"] + fm(tot),
            ["Amps at 240 V"] + [f"{v / 240:.0f} A" for v in tot], ["Amps by the standard method (220 Part III)"] + [f"{v:.0f} A" for v in std],
            ["Panel: least"] + [f"{q['amps']} A" for q in f], ["Panel: recommended"] + [f"{q['rec'] or q['amps']} A" for q in f]]


def notes_sheet(pdf):
    fig, bg, _ = b.bsheet("E-001", "Electrical notes, legend, panel schedules", 0, N001, sub="Rear building · all levels")
    bg.text(.5, 10.25, "ELECTRICAL NOTES, LEGEND, PANEL SCHEDULES", fontsize=10, fontweight="bold", color=INK, va="center")
    for i, k in enumerate("ABC"):
        f = FLAT[k]; x = .5 + i * 4.22
        bg.text(x, 9.9, f"PANEL {k} · {f['name'].upper()} · {f['amps']} A" + (f" ({f['rec']} A RECOMMENDED)" if f["rec"] else ""), fontsize=7, fontweight="bold", color=PW, va="center")
        bg.text(x, 9.74, "New panel. 120/240 V 1-phase, main breaker, 30 spaces or more. Flush in a hall wall, fed from the new meter stack.", fontsize=5.2, color=GREY, va="center")
        table(bg, x, 9.62, [.3, .8, .42, 2.53], [["Ckt", "Breaker", "Wire", "Serves"]] + [[j + 1, c[1], c[2], c[3]] for j, c in enumerate(CK[k])], fs=5.3, rh=.15)
    y0 = 9.62 - .15 * (len(CK["C"]) + 1) - .28; rows = loads()
    bg.text(.5, y0, "LOAD SUMMARY", fontsize=7, fontweight="bold", color=INK, va="center")
    y = table(bg, .5, y0 - .14, [2.3, .58, .58, .59], rows, fs=5.3, rh=.145) - .12
    for ln in [f"Nameplates are assumed: redo with the real units. Panels A and B come to {rows[-4][1]} and {rows[-4][2]} by this", f"method and about {rows[-3][1]} by the standard method, so 100 A is the least and has no spare:",
               "125 A is recommended for A and B while cooling and electric ranges stay in.", f"Panel C is 125 A: {len(CK['C'])} circuits, {rows[-4][3]}, room for an electric range later."]:
        bg.text(.5, y, ln, fontsize=5.2, color=GREY, va="center"); y -= .122
    bg.text(.5, y - .13, "SYMBOLS (same on E-101 to E-104)", fontsize=7, fontweight="bold", color=INK, va="center")
    legend(bg, .5, y - .36, LEG[:8], 5.3, .195); legend(bg, 2.6, y - .36, LEG[8:], 5.3, .195)
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
