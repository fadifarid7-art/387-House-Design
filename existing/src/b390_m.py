"""390 Forest Ave builder set: HVAC sheets M-001 and M-101 to M-104.
One gas furnace + cooling coil per flat, sheet-metal supply trunk with round branches to a register per room, one central
filter return, bath / range / dryer exhaust and PVC equipment venting. Positions are read from build390.LV (rooms, fixtures,
doors) and the scan geometry; sizes are rule of thumb. Design intent only: Manual J/S/D by the HVAC contractor governs."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402
from shapely.geometry import LineString, Point, Polygon, box  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

import build390 as b  # noqa: E402
from common import INK, GREY, table, plt  # noqa: E402

SUP, SUPF, EXH, EXHF, PVC = b.MECHC, "#eadcf3", "#c2570c", "#fbe3cf", "#0b7a75"   # supply/return purple, exhaust orange, pipes teal
FS = 3.5
FLATS = [("Lower flat", (3,), 790, 1.5, 40), ("Middle flat", (4,), 870, 2.0, 40), ("Upper flat (main floor + attic)", (5, 6), 1450, 3.0, 60)]


# ------------------------------------------------------------------------------------------ sizing (rule of thumb, 0.08 in. w.c. / 100 ft)
def rnd(c): return next(d for cap, d in ((35, 4), (60, 5), (110, 6), (160, 7), (220, 8), (290, 9), (390, 10), (620, 12)) if c <= cap)
def rct(c): return next(w for cap, w in ((210, 8), (310, 10), (410, 12), (510, 14), (620, 16), (710, 18), (810, 20), (910, 22), (1300, 24)) if c <= cap)
def grl(c): return "8x4" if c <= 60 else "10x4" if c <= 110 else "12x6" if c <= 150 else "14x6"


# ------------------------------------------------------------------------------------------ plan model look-ups
def rr(fl, no, i=0): return next(r for r in b.LV[fl]["rooms"] if r["no"] == no)["rects"][i]
def rname(fl, no): return next(r for r in b.LV[fl]["rooms"] if r["no"] == no)["name"]
def area(fl, no): return sum((r[2] - r[0]) * (r[3] - r[1]) for r in next(r for r in b.LV[fl]["rooms"] if r["no"] == no)["rects"])
def fx(fl, k): return next(f for f in b.LV[fl]["fx"] if f[0] == k)[1:5]
def mid(r): return ((r[0] + r[2]) / 2, (r[1] + r[3]) / 2)
def nd(fl, tag): d = next(d for d in b.LV[fl]["doors"] if d[0] == tag); return d[2], d[3], d[4]      # new door: wall line, start, end
def stack(fl): return b.STACK if fl != 3 else (17.68, 8.9)


def fxin(fl, k, r):
    """Tub or vanity of kind k that sits in room rectangle r."""
    return next(f[1:5] for f in b.LV[fl]["fx"] if f[0] == k and r[0] - .3 < (f[1] + f[3]) / 2 < r[2] + .3 and r[1] - .3 < (f[2] + f[4]) / 2 < r[3] + .3)


def bbx(o): p = np.array(o["pts"]); return (p[:, 0].min(), p[:, 1].min(), p[:, 0].max(), p[:, 1].max())
def near(fl, key, r): return min((bbx(o) for o in b.geom(fl)[key] if len(o["pts"]) >= 4), key=lambda q: box(*q).distance(box(*r)))


def wn(fl, r, side):
    """Windows on one side (N, S, E, W = +y, -y, +x, -x on the sheet) of room rectangle r."""
    out = []
    for o in b.geom(fl)["windows"]:
        q = bbx(o); cx, cy = mid(q)
        if box(*q).distance(box(*r)) < 0.8 and {"N": cy > r[3] - .2, "S": cy < r[1] + .2, "E": cx > r[2] - .2, "W": cx < r[0] + .2}[side]:
            out.append(q)
    return sorted(out)


_FOOT = {}


def foot(fl):
    """Floor area of the level (scan room outlines, grown to the wall centres)."""
    if fl not in _FOOT:
        _FOOT[fl] = unary_union([Polygon(r["pts"]).buffer(0.2) for r in b.geom(fl)["rooms"] if len(r["pts"]) >= 3])
    return _FOOT[fl]


def out(fl, p, d, more=0.35):
    """Point just outside the building, going from p in direction d (unit vector along x or y)."""
    s = LineString([p, (p[0] + 60 * d[0], p[1] + 60 * d[1])]).intersection(foot(fl))
    x0, y0, x1, y1 = min(getattr(s, "geoms", [s]), key=lambda q: q.distance(Point(p))).bounds
    return ((x1 + more) if d[0] > 0 else (x0 - more) if d[0] < 0 else p[0], (y1 + more) if d[1] > 0 else (y0 - more) if d[1] < 0 else p[1])


def hood(fl, lo):
    """Range hood: ducted if the range backs on an outside wall, otherwise recirculating."""
    R = fx(fl, "range"); cx, cy = mid(R); fuel = b.RANGE_FUEL[fl]
    for p, d, nm in (((R[0], cy), (-1, 0), "W"), ((R[2], cy), (1, 0), "E"), ((cx, R[1]), (0, -1), "S"), ((cx, R[3]), (0, 1), "N")):
        q = (p[0] + 0.95 * d[0], p[1] + 0.95 * d[1])
        if not foot(fl).contains(Point(q)):
            return (R, [p, q], f"New range hood ({fuel} range):\n6 in. duct out {nm} wall", lo)
    return (R, None, f"New range hood ({fuel}\nrange): recirculating,\nrange on inside wall", lo)


def risers():
    """Supply and return risers: the part of the old chimney shaft that is clear on level 5 (closet 309) and level 6 (west of bath B)."""
    g = box(*b.CHIMNEY).intersection(box(*rr(5, "309"))).difference(unary_union([box(*r) for r in b.LV[6]["new"]] + [box(*rr(6, "404")).buffer(0.2)]))
    x0, y0, x1, y1 = max(getattr(g, "geoms", [g]), key=lambda p: p.area).bounds
    return (x0 + .04, y0 + .05, x1 - .04, y0 + 1.0), (x0 + .04, y1 - 1.0, x1 - .04, y1 - .05), (x0, y0, x1, y1)


def feeds():
    """Attic floor registers fed through the floor from the level 5 ducts: bath A, bath B, bedroom 2 (same x, y on both levels)."""
    ta, vb, H = fxin(6, "tub", rr(6, "403")), fxin(6, "van", rr(6, "404")), rr(5, "306")
    return (ta[0] - 0.8, rr(6, "403")[1] + 0.55), (vb[0] + 0.7, vb[1] - 0.32), (rr(5, "304")[2] - 2.0, H[3] - 0.55)


# ------------------------------------------------------------------------------------------ symbols
def band(ax, pts, w, ec, fc, z=10, **kw):
    b._fill(ax, LineString(pts).buffer(w / 2, cap_style=2, join_style=2), fc=fc, ec=ec, lw=0.5, zorder=z, **kw)


def lab(ax, x, y, s, col=SUP, rot=0, ha="center", va="center", fs=FS, bold=False):
    ax.text(x, y, s, fontsize=fs, color=col, ha=ha, va=va, rotation=rot, zorder=17, linespacing=1.1, fontweight="bold" if bold else "normal",
            bbox=dict(fc="white", ec="none", pad=0.12, alpha=0.88))


def seglab(ax, pts, s, col=SUP):
    i = max(range(len(pts) - 1), key=lambda k: abs(pts[k + 1][0] - pts[k][0]) + abs(pts[k + 1][1] - pts[k][1]))
    (x0, y0), (x1, y1) = pts[i], pts[i + 1]
    lab(ax, (x0 + x1) / 2, (y0 + y1) / 2, s, col, 90 if abs(y1 - y0) > abs(x1 - x0) else 0, bold=True)


def reg(ax, x, y, cfm, lo, vert=False, note=""):
    w, h = (0.5, 1.0) if vert else (1.0, 0.5)
    ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fc="white", ec=SUP, lw=0.8, zorder=13))
    ax.plot([x - w / 2, x + w / 2], [y - h / 2, y + h / 2], color=SUP, lw=0.5, zorder=13.1); ax.plot([x - w / 2, x + w / 2], [y + h / 2, y - h / 2], color=SUP, lw=0.5, zorder=13.1)
    lab(ax, x + lo[0], y + lo[1], f"{cfm} cfm{note}\n{rnd(cfm)} in. dia. · {grl(cfm)}")


def grille(ax, r, s=None, lo=(0, 0), rot=0):
    ax.add_patch(Rectangle((r[0], r[1]), r[2] - r[0], r[3] - r[1], fc="white", ec=SUP, lw=0.8, hatch="//////", zorder=13))
    if s: lab(ax, (r[0] + r[2]) / 2 + lo[0], (r[1] + r[3]) / 2 + lo[1], s, SUP, rot)


def arrow(ax, p, q, col):
    ax.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle="-|>", color=col, lw=0.7, mutation_scale=5), zorder=15)


def out_end(pts, d=0.7):
    (x0, y0), (x1, y1) = pts[-2], pts[-1]; n = max(abs(x1 - x0) + abs(y1 - y0), 1e-6)
    return (x1 + d * (x1 - x0) / n, y1 + d * (y1 - y0) / n)


def exhaust(ax, pts, s, lo, w=0.33, roof=False):
    band(ax, pts, w, EXH, EXHF, 11)
    if roof: bubble(ax, pts[-1][0], pts[-1][1], "R", EXH, 0.3, 3.0)      # roof jack
    else: arrow(ax, pts[-1], out_end(pts), EXH)
    if s: lab(ax, lo[0], lo[1], s, EXH, lo[2] if len(lo) > 2 else 0)


def fan(ax, x, y):
    ax.add_patch(Rectangle((x - 0.4, y - 0.4), 0.8, 0.8, fc="white", ec=EXH, lw=0.8, zorder=13)); ax.add_patch(plt.Circle((x, y), 0.26, fc=EXHF, ec=EXH, lw=0.6, zorder=13.1))
    ax.text(x, y, "EF", fontsize=2.6, color=EXH, ha="center", va="center", zorder=13.2, fontweight="bold")


def bubble(ax, x, y, s, col=INK, r=0.34, fs=3.4):
    ax.add_patch(plt.Circle((x, y), r, fc="white", ec=col, lw=0.8, zorder=18)); ax.text(x, y, s, fontsize=fs, color=col, ha="center", va="center", zorder=18.1, fontweight="bold")


# ------------------------------------------------------------------------------------------ layouts (data only)
def lay3():
    fl = 3; F = fx(fl, "furnace"); px, py = mid(F); H = rr(fl, "107"); hy = mid(H)[1]
    LIV, KIT, B1, B2, BA1, BA2, LAU, MEC = (rr(fl, n) for n in ("101", "102", "103", "104", "105", "106", "108", "109"))
    xw, xe, yn, yr = H[0] + 1.3, H[2] - 0.5, KIT[1] + 4.5, LIV[1] + 2.9
    wl = wn(fl, LIV, "N"); w2 = wn(fl, B2, "N")[0]; t1, t2, Dr, Rg = fxin(fl, "tub", BA1), fxin(fl, "tub", BA2), fx(fl, "dryer"), fx(fl, "range")
    d1 = near(fl, "doors", rr(fl, "103", 1)); w0, a0, a1 = nd(fl, "102"); yv = mid(rr(fl, "111"))[1]; st = stack(fl); xb, xc, yd = B1[2] - 2.6, t1[0] - 0.85, Dr[3] + 0.75
    e2, e1 = (BA2[0] + 1.05, t2[3] + 0.85), (t1[0] - 1.0, BA1[1] + 1.2)
    return dict(
        trunk=[([(px, F[1]), (px, hy)], 600), ([(px, hy), (xw, hy)], 400), ([(px, hy), (xe, hy)], 200), ([(xw, hy), (xw, yn)], 250)], main=[],
        br=[("103", [(xw, hy), (xb, hy), (xb, B1[1] + 1.4)], 100, (1.9, 0)), ("106", [(xw, hy), (xw, BA2[3] - 2.6)], 50, (0.1, -0.75)),
            ("105", [(xc, hy), (xc, BA1[3] - 2.3)], 50, (-0.3, -0.75)), ("108", [(xe, hy), (LAU[0] + 2.6, hy)], 50, (-0.5, 0.75)),
            ("104", [(xe, hy), (xe, B2[3] - 1.5), (mid(w2)[0], B2[3] - 1.5)], 100, (0, -0.8)), ("102", [(xw, yn), (xw, KIT[3] - 1.6)], 80, (2.0, 0)),
            ("101", [(xw, yn), (mid(wl[1])[0], yn), (mid(wl[1])[0], LIV[3] - 1.5)], 85, (-2.0, 0)), ("101", [(xw, yr), (LIV[0] + 1.6, yr)], 85, (0.4, 0.8))],
        ret=[((MEC[0] - 0.56, py - 0.83, MEC[0] - 0.3, py + 0.83), "RA 20x20 filter grille\nlow in closet wall", (-0.1, 1.45), 0)], rduct=[([(MEC[0] - 0.3, py), (F[0], py)], 1.4)],
        tg=[(mid(d1)[0], d1[1] + 0.5, True), (a1 - 0.6, w0, False)],
        ef=[(e2, [e2, out(fl, e2, (0, -1))], "EF 80 cfm, 4 in. out\nS wall (over tub)", (e2[0] + 2.3, mid(t2)[1])),
            (e1, [e1, out(fl, e1, (0, -1))], "EF 80 cfm\n4 in. out S wall", (e1[0] + 1.6, e1[1] - 0.6))],
        dv=([(mid(Dr)[0], Dr[3]), (mid(Dr)[0], yd), out(fl, (mid(Dr)[0], yd), (1, 0))], "Dryer vent 4 in. rigid, about\n11 ft + 2 elbows, out E wall", (LAU[2] - 1.75, yd - 0.8)),
        hood=hood(fl, (Rg[0] - 1.45, mid(Rg)[1])),
        util=[([(F[2], yv), out(fl, (F[2], yv), (1, 0))], "PVC: 2 in. intake + 2 in. flue (furnace), 2 in. flue (WH); line-set LS.\nOut E wall, 12 in. above grade, 4 ft from doors. Slope to furnace.", (25.3, yv + 0.75))],
        cd=([(st[0], F[1]), (st[0], st[1] + 0.35)], (st[0] + 0.55, st[1] + 1.1)), ts=((MEC[2] + a0) / 2 + 0.2, H[3] - 0.42),
        txt=[(mid(LIV)[0], LIV[1] + 6.6, "Existing ducts and ceiling registers are above the dropped\nceilings: reuse where sound, seal, re-balance to this layout.", SUP)])


def lay4():
    fl = 4; F = fx(fl, "furnace"); px, py = mid(F); P = rr(fl, "210"); ys = P[1] + 0.95
    LIV, KIT, B1, B2, BA1, BA2, LAU, H = (rr(fl, n) for n in ("201", "202", "203", "204", "205", "206", "209", "207"))
    t1, t2, Dr, Rg, Wa = fxin(fl, "tub", BA1), fxin(fl, "tub", BA2), fx(fl, "dryer"), fx(fl, "range"), fx(fl, "washer")
    xl, xs, yl, yb, xb, xk = LAU[2] + 1.0, P[0] + 1.3, LIV[3] - 2.4, F[1] + 1.9, B1[2] - 4.1, KIT[2] - 4.5
    w1, a1, b1 = nd(fl, "201"); yh = (a1 + b1) / 2; xt = nd(fl, "202")[1] + 1.0; wb = wn(fl, B1, "N")[0]; gx = px + 1.07; yv, xv = F[3] + 0.55, B1[2] - 2.1
    e1, e2, xd, xc = (t1[2] + 0.5, mid(BA1)[1]), (t2[0] - 0.5, BA2[3] - 1.5), mid(Dr)[0], F[2] + 0.19
    S13 = rr(fl, "213")
    return dict(
        trunk=[([(px, F[1]), (px, ys)], 640), ([(px, ys), (xl, ys)], 390), ([(xl, ys), (xl, yl)], 240), ([(px, ys), (xs, ys)], 250)],
        main=[([(xs, ys), (xs, yh), (xt, yh)], 200), ([(F[0], yb), (xb, yb)], 160)],
        br=[("202", [(xl, ys), (xk, ys), (xk, ys + 2.2)], 150, (0, 0.8)), ("201", [(xl, yl), (xl, LIV[1] + 1.6)], 120, (2.0, 0)), ("201", [(xl, yl), (LIV[2] - 3.4, yl)], 120, (0, 0.8)),
            ("205", [(xs, ys), (BA1[2] - 0.55, ys)], 50, (-0.5, 1.15), True), ("204", [(xt, yh), (B2[0] + 2.2, yh)], 150, (0.3, 0.8)), ("206", [(xt, yh), (xt, BA2[3] - 1.5)], 50, (1.75, 0)),
            ("203", [(xb, yb), (xb, B1[3] - 1.7)], 80, (0.2, 0.8)), ("203", [(xb, yb), (mid(wb)[0], yb), (mid(wb)[0], B1[3] - 1.7)], 80, (0.3, 0.8))],
        ret=[((gx, P[3] - 1.77, gx + 2.08, P[3] - 0.1), "RA 20x25 filter\ngrille in ceiling", (0, 0), 0)], rduct=[([(gx + 1.0, P[3] - 0.1), (gx + 1.0, F[1] + 0.05), (F[2], F[1] + 0.05)], 0.67)],
        tg=[(w1, a1 + 0.42, True)],
        ef=[(e1, [e1, out(fl, e1, (0, 1))], "EF 80 cfm, 4 in. to N wall,\nabout 10 ft (wall: verify)", (e1[0] - 2.1, B1[1] + 2.6)),
            (e2, [e2, out(fl, e2, (0, -1))], "EF 80 cfm, 4 in.\nto S wall", (e2[0] - 1.8, BA2[1] - 1.6))],
        dv=([(xd, Dr[1]), out(fl, (xd, Dr[1]), (0, -1))], "Dryer vent 4 in. rigid to S wall: about 19 ft + 2 elbows\n= 29 ft equivalent (max 35). Long: verify the route.", (xd - 0.75, mid(LIV)[1], 90)),
        hood=hood(fl, (Rg[0] - 1.9, Rg[1] - 0.75)),
        util=[([(F[0], yv), (xv, yv), (xv, max(r[3] for r in b.LV[fl]["fix"]) + 0.35)], "PVC: 2 in. intake + flue (furnace), 2 in. flue (WH);\nline-set LS. Out N wall, 4 ft from the window.", (xv + 0.65, B1[3] - 2.2, 90))],
        cd=([(F[2], F[1] + 0.2), (xc, F[1] + 0.2), (xc, Wa[3])], (xc + 0.3, Wa[3] + 0.3)), ts=(H[0] + 0.85, H[3] - 0.42),
        txt=[(mid(S13)[0], S13[1] + 1.0, "Stair hall 213 is the upper flat's: no middle-flat ducts or grilles here.", GREY),
             (B1[2] + 1.0, B1[3] - 0.4, "No wall or door in the model here:\nverify. If a door goes in, add a TG.", GREY)])


def lay5():
    fl = 5; F = fx(fl, "furnace"); px, py = mid(F); H = rr(fl, "306"); yt = H[3] - 1.05
    LIV, KIT, B3, B4, BA1, C9 = (rr(fl, n) for n in ("301", "302", "303", "304", "305", "309"))
    dl, d3, db = near(fl, "doors", (LIV[2] - 3, LIV[3], LIV[2], LIV[3] + 0.4)), near(fl, "doors", rr(fl, "303", 1)), near(fl, "doors", (BA1[0] + 1, BA1[1] - 0.4, BA1[2], BA1[1]))
    w4, _a4, b4 = nd(fl, "301"); xw, xe, x3 = dl[0] + 0.6, H[2] - 0.9, d3[0] + 0.6
    ws, ww, w3, we = wn(fl, LIV, "S")[0], wn(fl, LIV, "W")[0], wn(fl, B3, "E")[0], wn(fl, B4, "E")[0]; yl, x1 = mid(ww)[1], mid(ws)[0]
    SR, RT, PK = risers(); fa, fb, f2 = feeds(); xs, x4, gx = SR[2] + 0.28, f2[0], px + 1.05
    t1, Dr, Rg, XE, st = fxin(fl, "tub", BA1), fx(fl, "dryer"), fx(fl, "range"), fx(fl, "xequip"), stack(fl)
    e1, xd, xp = (near(fl, "windows", BA1)[0] - 3.4, t1[1] - 0.8), mid(Dr)[0], C9[2] - 0.17
    return dict(
        trunk=[([(px, F[3]), (px, yt)], 840), ([(px, yt), (xw, yt)], 460), ([(px, yt), (xe, yt)], 380)],
        main=[([(xw, yt), (xw, yl), (x1, yl)], 240), ([(xe, yt), (x4, yt)], 220)], pipe=[([(F[2], fb[1]), fb], 50)],
        br=[("301", [(x1, yl), (x1, LIV[1] + 1.9)], 120, (2.0, 0)), ("301", [(x1, yl), (LIV[0] + 2.0, yl)], 120, (0.4, 0.8)), ("302", [(xw, yt), (KIT[2] - 3.0, yt)], 120, (0.3, -0.8)),
            ("305", [(mid(db)[0], yt), (mid(db)[0], BA1[1] + 1.7)], 50, (0, 0.75)), ("303", [(x3, yt), (x3, mid(w3)[1]), (B3[2] - 3.0, mid(w3)[1])], 160, (0, 0.8)),
            ("304", [(x4, yt), (x4, mid(we)[1])], 120, (-1.9, 0))],
        up=[(fa[0], yt, "UP 5 in. to attic bath A\nfloor register, 50 cfm", (0.2, -1.05)), (fb[0], fb[1], "UP 5 in. to attic bath B\nfloor register, 50 cfm", (-0.3, -1.4)),
            (x4, yt, "UP 6 in. to attic bedroom 2\nfloor register, 100 cfm", (-0.2, -0.95))],
        ris=[(SR, "S", [(xs, F[1]), (xs, mid(SR)[1]), (SR[2], mid(SR)[1])], "SR 12x8 supply riser\nup to attic, 310 cfm", (PK[0] - 1.75, mid(SR)[1] - 0.3)),
             (RT, "R", [(mid(RT)[0], RT[3]), (mid(RT)[0], F[1])], "RR 12x8 return riser\ndown from the attic", (PK[0] - 1.75, mid(RT)[1] + 0.5))],
        ret=[((gx, H[1] + 0.12, gx + 2.5, H[1] + 1.79), "RA 30x20 filter\ngrille in ceiling", (0, 0), 0)], rduct=[([(gx + 0.14, H[1] + 0.12), (gx + 0.14, py + 0.3)], 0.67)],
        tg=[(d3[2] - 0.7, mid(d3)[1], False), (w4, b4 - 0.6, True)],
        ef=[(e1, [e1, out(fl, e1, (0, 1))], "EF 80 cfm, 4 in. out N wall\n(over tub), 3 ft from window", (e1[0] - 0.75, e1[1] - 0.85))],
        dv=([(xd, Dr[3]), out(fl, (xd, Dr[3]), (0, 1))], "Dryer vent 4 in. rigid,\nabout 8 ft + 2 elbows,\nout N wall of the recess", (KIT[2] - 2.0, Dr[3] + 0.5)),
        hood=hood(fl, (Rg[2] + 2.2, mid(Rg)[1])),
        util=[([(xp, F[1] + 0.55), out(fl, (xp, F[1] + 0.55), (0, -1))],
               "PVC: 2 in. intake + flue (furnace), 2 in. flue (WH); line-set LS.\nThrough closets 309 and 311, out S wall, 4 ft from windows.", (xp + 1.5, (C9[1] + C9[3]) / 2 - 2.2, 90))],
        cd=([(st[0], F[1]), (st[0], st[1] + 0.35)], (st[0] + 0.02, st[1] + 1.0)), ts=(H[0] + 1.1, H[3] - 0.42),
        txt=[(mid(XE)[0] + 0.9, XE[1] - 0.8, "Old furnace + water heater here move to closet 307:\nremove the old trunk and flue from this room, or re-feed\nsound branches from the new trunk; patch.", SUP)])


def lay6():
    fl = 6; SR, RT, PK = risers(); fa, fb, f2 = feeds(); BY1, BY2, BAa, BAb, C6 = rr(fl, "401", 2), rr(fl, "402", 2), rr(fl, "403"), rr(fl, "404"), rr(fl, "406")
    xs, xr, ye = mid(SR)[0], mid(RT)[0], PK[1] - 1.6; x1 = (BY1[2] + PK[0]) / 2
    ck = LineString([(xs + 0.6, ye), (BY2[0], ye)]).intersection(b.geom(fl)["walls"]); ck = min(getattr(ck, "geoms", [ck]), key=lambda q: q.bounds[0]).bounds   # bay 2 west side wall
    cut = b.LV[fl]["cut"][0]; yd = mid(cut)[1]; w3, _a3, b3 = nd(fl, "403"); va, tb = fxin(fl, "van", BAa), fxin(fl, "tub", BAb)
    ea, eb = (va[2] + 0.45, BAa[1] + 1.4), (BAb[2] - 1.35, tb[3] + 0.7)
    return dict(
        trunk=[], main=[([(xs, ye), (x1, ye)], 210)],
        br=[("401", [(x1, ye), (x1, PK[1] + 0.2)], 105, (0, 0.85), False, " knee wall"), ("401", [(x1, ye), (BY1[2] + 0.17, ye)], 105, (-1.6, 0), True, " bay side"),
            ("402", [(xs, ye), ((ck[0] + ck[2]) / 2, ye)], 100, (1.65, 0), True, " bay side")],
        fr=[("403", [fa], 50, (0, 0.8), False, " floor"), ("404", [fb], 50, (-1.75, 0.95), False, " floor"), ("402", [f2], 100, (-0.2, 0.8), False, " floor")],
        ris=[(SR, "S", [(xs, SR[1]), (xs, ye)], "SR 12x8 supply riser from level 5:\n310 cfm to the ducts in the eave space", (xs - 0.6, ye - 0.9)),
             (RT, "R", [(xr, RT[3]), (xr, yd), (cut[2], yd)], "RR 12x8 return riser\nboxed in closet 406", (C6[0] + 0.75, mid(C6)[1], 90))],
        ret=[((cut[2] + 0.02, cut[1] + 0.1, cut[2] + 0.3, cut[3] - 0.1), "RA 24x10 grille, high,\nover the doorway", (1.5, 0), 0),
             ((xr - 0.45, C6[3] + 0.5, xr + 0.45, C6[3] + 1.0), "RA inlet 14x8\nbedroom 1", (-1.5, 0), 0)],
        tg=[(w3, b3 - 0.6, True)],
        ef=[(ea, [ea, (ea[0], BAa[3] + 1.5)], "EF 80 cfm, 4 in. insulated duct\nto roof jack R, north slope", (ea[0] - 2.2, BAa[3] + 1.5), True),
            (eb, [eb, (eb[0] + 0.95, eb[1])], "EF 80 cfm, 4 in. up\nto roof jack R", (eb[0] - 1.2, mid(tb)[1]), True)],
        txt=[((BY1[2] + ck[0]) / 2, ye - 1.9, "South eave space behind the knee wall: insulated (R-8), sealed ducts.\nThe dormer bays block the run to the east and west ends: verify on site.", SUP),
             (rr(fl, "405")[0] + 1.45, rr(fl, "405")[3] - 0.8, "Stair hall: no register;\nreturn air path", GREY)])


LAY = {3: lay3, 4: lay4, 5: lay5, 6: lay6}


# ------------------------------------------------------------------------------------------ plan sheets
LEG = [("fill", SUPF, "Supply trunk or duct, size in inches"), ("X", SUP, "Supply register: cfm, round neck, grille"),
       ("RA", SUP, "Return grille / duct (hatched)"), ("TG", SUP, "Transfer grille over the bedroom door"), ("fill", EXHF, "Exhaust: bath fan EF, dryer, range hood"),
       ("dash", PVC, "PVC flue + intake pipes, line-set LS"), ("CD", PVC, "Condensate drain, 3/4 in., trapped"), ("T", INK, "Thermostat, 5 ft above floor")]


def draw(ax, fl, D):
    for pts, c in D["trunk"]:
        band(ax, pts, rct(c) / 12, SUP, SUPF, 10)
    for pts, c in D.get("main", []):
        band(ax, pts, rnd(c) / 12, SUP, SUPF, 10.2)
    for pts, c in [(q[1], q[2]) for q in D["br"]] + D.get("pipe", []):
        band(ax, pts, rnd(c) / 12, SUP, "white", 10.4)
    for pts, w in D.get("rduct", []):
        band(ax, pts, w, SUP, "white", 10.6, hatch="//////")
    for r, kind, pts, s, lo in D.get("ris", []):                      # risers in the old chimney shaft
        if pts: band(ax, pts, 0.5, SUP, SUPF if kind == "S" else "white", 10.7, **({} if kind == "S" else dict(hatch="//////")))
        ax.add_patch(Rectangle((r[0], r[1]), r[2] - r[0], r[3] - r[1], fc=SUPF if kind == "S" else "white", ec=SUP, lw=1.1, zorder=14, hatch=None if kind == "S" else "//////"))
        if kind == "S": ax.plot([r[0], r[2]], [r[1], r[3]], color=SUP, lw=0.7, zorder=14.1)
        lab(ax, lo[0], lo[1], s, SUP, lo[2] if len(lo) > 2 else 0)
    for pts, c in D["trunk"]:
        seglab(ax, pts, f"{rct(c)}x8")
    for pts, c in D.get("main", []):
        seglab(ax, pts, f"{rnd(c)} in.")
    for _no, pts, c, lo, *k in D["br"] + D.get("fr", []):
        reg(ax, pts[-1][0], pts[-1][1], c, lo, *k)
    for r, s, lo, rot in D.get("ret", []):
        grille(ax, r, s, lo, rot)
    for x, y, vert in D.get("tg", []):
        grille(ax, (x - 0.2, y - 0.45, x + 0.2, y + 0.45) if vert else (x - 0.45, y - 0.2, x + 0.45, y + 0.2))
        lab(ax, x + (0.6 if vert else 0), y + (0 if vert else 0.5), "TG", SUP, bold=True)
    for p, pts, s, lo, *roof in D.get("ef", []):
        exhaust(ax, pts, s, lo, roof=bool(roof)); fan(ax, *p)
    if D.get("dv"):
        exhaust(ax, *D["dv"])
    if D.get("hood"):
        Rg, pts, s, lo = D["hood"]
        ax.add_patch(Rectangle((Rg[0], Rg[1]), Rg[2] - Rg[0], Rg[3] - Rg[1], fill=False, ec=EXH, lw=0.9, ls=(0, (3, 1.5)), zorder=12))
        if pts: exhaust(ax, pts, None, None, 0.5)
        lab(ax, lo[0], lo[1], s, EXH)
    for pts, s, lo in D.get("util", []):
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color=PVC, lw=1.0, ls=(0, (5, 1.5, 1, 1.5)), zorder=12); arrow(ax, pts[-1], out_end(pts), PVC)
        lab(ax, lo[0], lo[1], s, PVC, lo[2] if len(lo) > 2 else 0)
    if D.get("cd"):
        pts, lo = D["cd"]; ax.plot([p[0] for p in pts], [p[1] for p in pts], color=PVC, lw=0.9, ls=(0, (1, 1.2)), zorder=12); lab(ax, lo[0], lo[1], "CD", PVC, bold=True)
    for x, y, s, lo in D.get("up", []):
        bubble(ax, x, y, "UP", SUP, 0.3, 2.6); lab(ax, x + lo[0], y + lo[1], s)
    for x, y, s, col, *rot in D.get("txt", []):
        lab(ax, x, y, s, col, rot[0] if rot else 0)
    if D.get("ts"):
        bubble(ax, D["ts"][0], D["ts"][1], "T")


ST = ("Status", ["Design intent, to be confirmed by the", "licensed HVAC trade. Manual J/S/D governs.", "See M-001 for basis, schedule, air balance."])
NOTES = {3: [("This level", ["Lower flat, about 790 sf. Furnace 40,000", "Btu/h + 1.5 ton coil in closet 109.", "600 cfm supply, 8 registers, 1 return."]),
             ("MAIN RISK: LOW CEILINGS", ["Ceilings are 6'-10\" to 7'-6\" and are", "dropped / tiled today, with the existing", "ducts and ceiling registers above them.", "A soffit is NOT possible below 7'-0\":",
                                          "every duct here must stay above the", "ceiling, in the joist space. Joist direction", "is NOT known: a duct fits only along the", "joists (about 14 x 8 in. per 2x10 bay).",
                                          "Open the ceiling and confirm on site", "BEFORE ordering. If joists cross the", "route: use another bay, or the crawl space", "under part of the house (access door",
                                          "stuck: open and check), or a small-duct", "or ductless system for this flat."]),
             ("Verify", ["Grade at each wall cap (flat is partly", "below grade): caps 12 in. above grade.", "Bedroom 2 has only a small high window;", "bedroom 1 shows none in the scan."])],
         4: [("This level", ["Middle flat, about 870 sf. Furnace 40,000", "Btu/h + 2 ton coil in closet 208.", "800 cfm supply, 8 registers, 1 return."]),
             ("Ceilings", ["Passage 210 is 7'-4\" and hall 207 is 7'-0\":", "an 8 in. soffit there leaves under 6'-8\".", "Trunk in the joist space there (joists:", "verify), soffit only in the living room and",
                           "bedrooms (8'-8\", 7'-8\")."]),
             ("Verify", ["Closet 208 has no wall beside its door for", "a return grille: the filter grille is in the", "passage ceiling, ducted over the door.", "Dryer is 11 ft from the nearest outside",
                         "wall: vent is near its length limit.", "Kitchen: the range stands in front of the", "east opening (window or door?); keep the", "hood cap 3 ft from it.",
                         "Bedroom 1: no wall to the stair in the", "model, and its north wall is not scanned."])],
         5: [("This level", ["Upper flat (main floor + attic), about", "1,450 sf: ONE furnace, 60,000 Btu/h +", "3 ton coil, in closet 307. 1,200 cfm:", "690 here, 510 to the attic."]),
             ("Existing equipment", ["The flat's furnace and water heater", "stand today in the west end of room 304", "(dashed box). They move to closet 307.", "Remove the old trunk and flue from room",
                                     "304, or re-feed sound branches from the", "new trunk; patch."]),
             ("To the attic", ["Risers SR + RR go up the old chimney", "shaft, through closet 309. The clear", "pocket at the attic floor is only about", "8 x 24 in.: verify. If both do not fit,",
                               "keep SR and bring attic return air down", "the open stair to the hall grille.", "UP = branch through the floor to an", "attic floor register (same joist space)."]),
             ("Verify", ["Hall ceiling is 7'-5\": an 8 in. soffit", "leaves 6'-8\" clear, no more.", "Gas range: hood is ducted outside."])],
         6: [("This level", ["Attic of the upper flat: 2 bedrooms,", "2 baths. 510 cfm from the furnace on", "level 5. No equipment up here."]),
             ("Attic ducts", ["SR feeds insulated ducts in the south", "eave space behind the knee wall, to a", "knee-wall register and bay side-wall", "registers. The two dormer bays block",
                              "the eave run, so the far ends rely on", "throw from the bay sides.", "Both baths and the east end of bedroom", "2 get a floor register fed through the",
                              "floor from level 5 (see M-103).", "If there is space above the 7'-8\" flat", "ceiling, the ducts may run there with", "ceiling registers instead: verify.",
                              "Ducts in the eave: R-8, sealed, inside", "the insulation where possible."]),
             ("Verify", ["Rafters are cut or separated in places", "(inspection report): repair first; no", "roof jack through a damaged rafter.", "One thermostat (level 5) runs both",
                         "floors: set balance dampers; consider", "a 2-zone damper kit."])]}


def plan(pdf, number, fl):
    D = LAY[fl](); L = b.LV[fl]
    fig, bg, ax = b.bsheet(number, f"{L['name']}: HVAC plan", fl, NOTES[fl] + [ST], LEG)
    b.draw_base(ax, fl, "trade"); draw(ax, fl, D)
    y = b.text_block(bg, 10.6, fig._legend_end - 0.15, "All levels", [
        "Supply: sheet-metal trunk, round branches with a", "damper at each take-off. Register tags show cfm,", "round neck and grille size.",
        "Baths: door undercut 3/4 in. for make-up air.", "Bedrooms: transfer grille TG over the door.", "Existing ducts: reuse where sound and the size",
        "matches; seal joints, repair holes and rust.", "Remove old metal flues; patch walls and roof.", "Wall caps: 3 ft from windows and doors (flues:", "4 ft beside, 12 in. above grade or snow)."])
    cf = sum(c for _n, _p, c, *_ in D["br"] + D.get("fr", []))
    b.text_block(bg, 10.6, y - 0.05, "Supply on this sheet", [f"{len(D['br']) + len(D.get('fr', []))} registers, {cf} cfm."] + D.get("sum", []))
    b.save(fig, number, pdf)


SHEETS = [("M-101", "Lower flat: HVAC plan", lambda pdf: plan(pdf, "M-101", 3)), ("M-102", "Middle flat: HVAC plan", lambda pdf: plan(pdf, "M-102", 4)),
          ("M-103", "Upper flat main floor: HVAC plan", lambda pdf: plan(pdf, "M-103", 5)), ("M-104", "Attic: HVAC plan", lambda pdf: plan(pdf, "M-104", 6))]

if __name__ == "__main__":
    from matplotlib.backends.backend_pdf import PdfPages
    with PdfPages(os.path.join(b.HERE, "drawings", "_test_m.pdf")) as pdf:
        for n, t, fn in SHEETS:
            fn(pdf)
    print("ok", [s[0] for s in SHEETS])
