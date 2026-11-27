"""390 Forest Ave builder set: plumbing and gas sheets P-001 (notes, schedules, risers) and P-101 to P-104 (one per level).
The house is gutted to the studs: every pipe, fixture and water heater here is new. Every position is worked out from the plan
model in build390 (rooms, fixtures, stack, range fuel); only small offsets are typed here.
Design intent only, IPC / IFGC used as the layout guide: to be confirmed by the licensed plumber and gas fitter."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from matplotlib.patches import Rectangle, Polygon as MPoly  # noqa: E402

import build390 as b  # noqa: E402
from common import INK, GREY, table, plt  # noqa: E402

DRC, VTC, CWC, HWC, GSC = "#2a2f36", "#2e7d32", "#1565c0", "#c62828", "#a8760a"
COL = dict(D=DRC, V=VTC, C=CWC, H=HWC, G=GSC, P="#6a4c93", E=GREY, K=INK)
DASH = dict(V=(3, 2), H=(7, 2), G=(6, 2, 1.2, 2), P=(1.3, 1.6))          # dash patterns in points; D and C are solid
LWD = {"3": 2.1, "2": 1.4, "1.5": 1.0, "1": 1.9, "3/4": 1.5, "1/2": 0.8, "v": 0.9, "pd": 0.8}
DV = {"x+": (1, 0), "x-": (-1, 0), "y+": (0, 1), "y-": (0, -1)}
TUBEND = {3: ("x+", "y+"), 4: ("y+", "y+"), 5: ("x+",), 6: ("y-", "x+")}      # valve end of each tub in L["fx"] order
GASCAP = {40: (81, 170, 320), 50: (72, 151, 284), 70: (60, 126, 237)}        # IFGC Table 402.4(2): cfh for 1/2, 3/4, 1 in. Sch. 40 pipe, 0.5 in. w.c. drop
GASRUN = {3: ("Lower", 40, 40), 4: ("Middle", 50, 40), 5: ("Upper", 70, 60)}  # kitchen level: (flat, ASSUMED longest run in ft, furnace input in 1000 Btu/h)


def gas(fl):
    """Gas pipe sections of one flat: (name, load cfh, size, table capacity). Longest-run method; the main is never under 3/4 in."""
    _, run, furn = GASRUN[fl]; rng = 65 if b.RANGE_FUEL[fl] == "gas" else 0; out = []
    for j, (sec, load) in enumerate([("Meter to closet", furn + 40 + rng), ("Furnace drop", furn), ("Water heater drop", 40)] + ([("Branch to range", rng)] if rng else [])):
        i = max(next(i for i, c in enumerate(GASCAP[run]) if c >= load), 1 if j == 0 else 0)
        out.append((sec, load, ("1/2", "3/4", "1")[i], GASCAP[run][i]))
    return out


def X(v): return ("x", v)
def Y(v): return ("y", v)


def R(p, *mv):
    """Pipe route: start point, then X(to)/Y(to) square moves or plain points."""
    pts = [tuple(p)]
    for m in mv:
        x, y = pts[-1]; pts.append((m[1], y) if m[0] == "x" else (x, m[1]) if m[0] == "y" else tuple(m))
    return pts


def rm(fl, no): return next(r for r in b.LV[fl]["rooms"] if r["no"] == no)["rects"][0]
def fxs(fl, k): return [f for f in b.LV[fl]["fx"] if f[0] == k]
def flange(f): return (f[1] + DV[f[3]][0], f[2] + DV[f[3]][1])            # toilet flange 12 in. off the wall on the bowl axis
def mid(f): return ((f[1] + f[3]) / 2, (f[2] + f[4]) / 2)


def tub(f, end):
    """Valve point (middle of the valve end) and drain point (7 in. in from it) of a tub."""
    (cx, cy), d = mid(f), DV[end]
    v = (f[3] if d[0] > 0 else f[1] if d[0] < 0 else cx, f[4] if d[1] > 0 else f[2] if d[1] < 0 else cy)
    return v, (v[0] - 0.6 * d[0], v[1] - 0.6 * d[1])


# The four new stacks (design intent, set out on site). S1 in the old chimney shaft; S2 in the chase at the tub end of bath 305;
# S3 in the wall behind the toilet of bath 205 (wall lines differ a few inches level to level); S4 where the middle flat's kitchen wall meets the wall below.
S1 = b.STACK; VR0 = (S1[0] - 0.5, S1[1]); RH, RC = (S1[0] - 0.25, S1[1] + 0.75), (S1[0] + 0.05, S1[1] + 0.75)   # vent riser beside S1; attic water risers
S2 = ((fxs(5, "tub")[0][3] + rm(5, "305")[2]) / 2, mid(fxs(5, "tub")[0])[1])
S3 = {fl: (fxs(4, "wc")[1][1] - 0.2, y) for fl, y in ((3, rm(3, "101")[1] - 0.17), (4, rm(4, "205")[1] - 0.17), (5, rm(5, "301")[3] + 0.17))}
S4 = {fl: (x, rm(4, "202")[3] + 0.17) for fl, x in ((3, (rm(3, "102")[2] + rm(3, "104")[0]) / 2), (5, (rm(3, "102")[2] + rm(3, "104")[0]) / 2 + 0.16), (6, (rm(6, "405")[2] + rm(6, "407")[0]) / 2))}
S4[4] = S4[3]


def base(fl):
    """Recorders for one level, the tubs (valve point, drain point, rect), a drain mark at every bath fixture, and the dishwasher's hot line and drain hose."""
    P, S = [], []
    tubs = [tub(f, e) + (f,) for f, e in zip(fxs(fl, "tub"), TUBEND[fl])]
    for (tv, td, f), w, v in zip(tubs, fxs(fl, "wc"), fxs(fl, "van")):
        S.extend([("trap", td[0], td[1], 0.13), ("trap",) + flange(w) + (0.22,), ("trap",) + mid(v) + (0.13,)])
    for d in fxs(fl, "dw"):             # both lines drawn on the room side of the counter, clear of the supply lines at the wall
        a, c, k = mid(d), mid(fxs(fl, "sinkbase")[0]), mid((0,) + next(r for r in b.LV[fl]["rooms"] if r["kind"] == "kitchen")["rects"][0])
        n = math.hypot(c[0] - a[0], c[1] - a[1]); nx, ny = -(c[1] - a[1]) / n, (c[0] - a[0]) / n; sg = 1 if nx * (k[0] - a[0]) + ny * (k[1] - a[1]) > 0 else -1
        for sy, o in (("H", 0.3 * sg), ("D", 0.55 * sg)): P.append((sy, "1/2", [(c[0] + nx * o, c[1] + ny * o), (a[0] + nx * o, a[1] + ny * o)]))
        S.append(("dot", a[0] + nx * 0.3 * sg, a[1] + ny * 0.3 * sg, "H"))
    s = lambda *a: S.append(a)
    return P, S, (lambda sy, z, *a: P.append((sy, z, R(*a)))), s, (lambda x, y, t, c, w="m", ha="center", va="center": s("tag", x, y, t, c, w, ha, va)), tubs


def closet(p, s, fl, IN, feed, G0, gt, ct, tp):
    """Symbols every mechanical closet gets: cold entry + flat shutoff, heater shutoff, expansion tank, relief pipe, pan, gas entry.
    feed: flat valve, heater valve, tank (x, y, tag side). gt, ct: where the gas and cold water notes sit on the enlarged plan. tp: relief pipe direction and its tag."""
    wh = fxs(fl, "wh")[0][1:]
    s("in", IN[0], IN[1], "C"); s("in", G0[0], G0[1], "G"); s("valve", feed[0][0], feed[0][1], "C", feed[0][2][0]); s("valve", feed[1][0], feed[1][1], "C", feed[1][2][0]); s("et", feed[2][0], feed[2][1]); s("pan", *wh)
    p("P", "pd", (wh[0] + 0.92 * tp[0], wh[1] + 0.92 * tp[1]), (wh[0] + 1.1 * tp[0], wh[1] + 1.1 * tp[1])); s("tag", tp[2], tp[3], "T&P relief pipe\nto 6\" above pan", "P", "i", tp[4], tp[5])
    s("lead", IN[0], IN[1], ct[0], ct[1], "new 3/4\" CW in from the\nservice: route to be found", "C", "i", "left")
    s("lead", G0[0], G0[1], gt[0], gt[1], "new " + gas(fl)[0][2] + "\" gas in from the flat's\nmeter: route to be found", "G", "i", "left")
    for (x, y, o), t in zip(feed, ("flat SOV", "SOV", "ET")):                # tag side: h above, hb below, v right, vl left
        dx, dy, ha, va = {"h": (0, 0.2, "center", "bottom"), "hb": (0, -0.22, "center", "top"), "v": (0.22, 0, "left", "center"), "vl": (-0.22, 0, "right", "center")}[o]
        s("tag", x + dx, y + dy, t, "C", "i", ha, va)


KSTAG = "Sink: 1-1/2\" trap, 2\" drain %s;\nvent to the stack vent above, or an AAV.\nDW: hot off the sink stop; drain to the sink\ntailpiece with a high loop."
MCTAG = "Mechanical closet %s: see the enlarged plan.\nNew 3/4\" CW and %s\" gas arrive here: the meters\nexist, but where they are is not recorded"


def plan3():
    P, S, p, s, T, tubs = base(3); B2, B1, HA, MC, LA = (rm(3, n) for n in ("106", "105", "107", "109", "108"))
    (TV, TD, t2), (TV1, TD1, t1) = tubs; (f2, f1), w1 = [flange(w) for w in fxs(3, "wc")], fxs(3, "wc")[1]; l2, l1 = [mid(v) for v in fxs(3, "van")]
    wh, fu, rg, wa, ls, sk, dw = fxs(3, "wh")[0][1:], fxs(3, "furnace")[0], fxs(3, "range")[0], fxs(3, "washer")[0], fxs(3, "lsink")[0], fxs(3, "sinkbase")[0], fxs(3, "dw")[0]
    ww = (B2[2] + B1[0]) / 2; SX, SY = ww, S1[1]; xm, xm1 = B2[2] - 0.26, B1[0] + 0.26; vr = (ww, SY - 0.62)      # 2x6 wet wall centre line; S1 stands in it here
    xsp, ywb, yld, ks, s4 = wa[1] + 0.67, mid(wa)[1], HA[1] + 0.9, mid(sk), S4[3]
    # drains and vents. Baths 2 and 1 back to back on the wet wall, to S1; kitchen to S4; laundry to the building drain
    p("D", "3", f2, X(xm), Y(SY), X(SX)); p("D", "2", TD, X(xm), Y(f2[1])); p("D", "1.5", l2, X(ww)); p("V", "v", (xm, TD[1]), X(ww), Y(vr[1]))
    p("D", "3", f1, X(xm1), Y(SY), X(SX)); p("D", "2", TD1, X(xm1)); p("D", "1.5", l1, X(ww)); p("D", "3", (SX, SY), Y(HA[1] + 0.75)); s("arrow", SX, HA[1] + 0.75, SX, HA[1] + 1.25, "D")
    p("D", "2", ks, X(s4[0]), Y(s4[1])); p("D", "2", (xsp, ywb), Y(yld), X(LA[0] - 0.5)); p("D", "2", mid(ls), Y(yld), X(xsp)); s("arrow", LA[0] - 0.5, yld, LA[0] - 1.05, yld, "D")
    for q in ((ww, TD[1]), (ww, (l1[1] + l2[1]) / 2), (s4[0], ks[1]), (wa[1] - 0.17, ywb + 0.35), (mid(ls)[0], ls[4] + 0.17)): s("vup", *q)
    for q in (ks, mid(ls), (xsp, ywb)): s("trap", q[0], q[1], 0.13)
    for q in ((SX, SY), S2, S3[3], s4): s("stk", *q); s("co", q[0] - 0.45, q[1] + 0.3)
    s("vr", *vr)
    # water: heater in the closet, trunks along the hall ceiling, down the bath 1 side of the wet wall
    xc, xh, yc, yh, x1c, x1h = MC[2] - 0.22, MC[2] - 0.47, HA[3] - 0.53, HA[3] - 0.28, B1[0] + 0.6, B1[0] + 0.82
    IN = (wh[0] - 0.6, MC[3] - 0.22); xwc, xwh, xls, ys = wa[1] + 0.12, wa[1] + 0.34, ls[1] + 0.4, ks[1]
    p("C", "3/4", IN, X(xc), Y(yc), X(x1c), Y(l2[1] - 0.2)); p("C", "1/2", (x1c, l2[1] - 0.2), Y(TV[1] + 0.22), X(ww - 0.1)); p("C", "3/4", (xc, wh[1] + 0.25), X(wh[0] + 0.25))
    p("C", "3/4", (xc, yc), X(xwc)); p("C", "1/2", (xwc, yc), X(xls)); p("C", "1/2", (xwc, yc), Y(ywb)); p("C", "1/2", (xc, IN[1]), Y(ys + 0.15))
    p("C", "1/2", (x1c, l2[1] + 0.45), X(B2[2] + 0.08)); p("C", "1/2", (x1c, f2[1] + 0.5), X(B2[2] + 0.08)); p("C", "1/2", (TV1[0] - 0.18, yc), Y(TV1[1] + 0.2))
    p("H", "3/4", (wh[0], wh[1] - 0.3), X(xh), Y(yh), X(x1h), Y(l2[1] - 0.4)); p("H", "1/2", (x1h, l2[1] - 0.4), Y(TV[1] - 0.03), X(ww - 0.1))
    p("H", "3/4", (xh, yh), X(xwh)); p("H", "1/2", (xwh, yh), X(xls)); p("H", "1/2", (xwh, yh), Y(ywb)); p("H", "1/2", (xh, wh[1] - 0.3), Y(ys - 0.15))
    p("H", "1/2", (x1h, l2[1] + 0.7), X(B2[2] + 0.08)); p("H", "1/2", (TV1[0] + 0.08, yh), Y(TV1[1] + 0.2))
    for q in ((x1c, l1[1] - 0.6, "C"), (x1h, l1[1] - 0.6, "H"), (x1c, w1[2] - 0.35, "C"), (xls, yc, "C"), (xls, yh, "H"), (xc, ys + 0.15, "C"), (xh, ys - 0.15, "H"), (xwc, ywb, "C"), (xwh, ywb, "H"),
              (B2[2] + 0.08, l2[1] + 0.45, "C"), (B2[2] + 0.08, l2[1] + 0.7, "H"), (B2[2] + 0.08, f2[1] + 0.5, "C"), (TV1[0] - 0.18, TV1[1] + 0.2, "C"), (TV1[0] + 0.08, TV1[1] + 0.2, "H")):
        s("dot", *q)
    s("tv", ww - 0.12, TV[1] + 0.1); s("ap", B1[0], TV[1] + 0.75, "v"); s("tv", TV1[0] - 0.05, TV1[1] + 0.17); s("ap", TV1[0] + 0.6, HA[1] + 0.28, "h")
    pd = (fu[3] + 0.35, MC[1] + 0.3); p("P", "pd", (wh[0] - 0.9, wh[1] - 0.63), pd); s("up", pd[0], pd[1], "P")
    s("lead", pd[0], pd[1], MC[0] - 0.4, MC[1] - 0.6, "1\" pan drain down\nto the crawl space:\nroute to be found", "P", "i", "left")
    # gas: enters at the closet; furnace and water heater, and the range only if it is gas
    gz = gas(3); G0 = (fu[3] + 0.14, MC[3] - 0.17); xr = fu[3] - 0.11
    p("G", gz[1][2], G0, X(mid(fu)[0]), Y(fu[4] - 0.3)); p("G", gz[2][2], G0, Y(wh[1] - 0.5), X(wh[0] - 0.77)); s("gv", mid(fu)[0] + 0.42, G0[1], "h"); s("gv", G0[0], wh[1] + 0.3, "v")
    if len(gz) > 3: p("G", gz[3][2], G0, Y(MC[3] + 0.17), X(xr), Y(mid(rg)[1]), X(rg[1] + 0.9)); s("gv", rg[1] - 0.3, mid(rg)[1], "h")
    else: T(rg[1] - 0.15, mid(rg)[1], "electric range:\nno gas", "E", "m", "right")
    closet(p, s, 3, IN, (((IN[0] + xc) / 2, IN[1], "h"), (xc - 0.35, wh[1] + 0.25, "h"), (wh[0] + 0.25, wh[1] + 0.25, "hb")), G0,
           (MC[0] - 0.4, MC[3] + 0.7), (fu[3] + 0.3, MC[3] + 0.75), (0.25, -0.97, wh[0] - 0.3, MC[1] - 0.05, "center", "top"))
    T(xm - 0.12, (f2[1] + SY) / 2 - 0.55, "3\"", "D", "m", "right"); T(xm - 0.12, (TD[1] + f2[1]) / 2 + 0.3, "2\"", "D", "m", "right"); T(l2[0] - 0.1, l2[1] + 0.42, "1-1/2\"", "D")
    T(TD[0] - 0.25, TD[1], "tub trap 1-1/2\"", "D", "m", "right"); T(f2[0] - 0.3, f2[1] - 0.75, "WC 3\"", "D", "m", "right"); T(xm - 0.2, vr[1] + 0.02, "VR 2\"", "V", "m", "right"); T(xm - 0.2, SY + 0.12, "S1 3\", CO at base", "D", "m", "right")
    T((xm1 + TD1[0]) / 2 + 0.9, TD1[1] - 0.12, "2\" tub arm", "D", "m", "center", "top"); T(f1[0] + 0.3, f1[1] - 0.75, "WC 3\"", "D", "m", "left")
    s("lead", ww, f2[1] + 0.95, B2[0] + 0.15, f2[1] + 0.95, "1-1/2\" vents up in the wet\nwall, across at 42\" min to VR", "V", "m", "left")
    s("lead", SX, HA[1] + 1.0, HA[0] + 0.2, HA[1] + 1.55, "3\" on to the new 4\" building drain, probably\nin the crawl space (door stuck): find the route", "D", "m", "left")
    s("lead", S2[0], S2[1], MC[0] - 3.0, S2[1] - 1.5, "S2 3\" down from above, boxed at the wall;\nCO at base, on to the building drain", "D", "m", "left")
    s("lead", S3[3][0], S3[3][1], S3[3][0] - 0.3, S3[3][1] + 1.5, "S3 3\" down from above in this wall;\nCO at base, on to the building drain", "D", "m", "center")
    s("lead", s4[0], s4[1], s4[0] + 0.6, s4[1] - 1.3, "S4 2\" in this wall, from above;\nCO at base, on to the building drain", "D", "m", "left")
    T((x1c + xc) / 2 - 0.3, yh + 0.02, "3/4\" H", "H", "m", "center", "bottom"); T((x1c + xc) / 2 - 0.3, yc - 0.02, "3/4\" C", "C", "m", "center", "top")
    T((xc + xwc) / 2 + 0.3, yh + 0.02, "3/4\" H", "H", "m", "center", "bottom"); T((xc + xwc) / 2 + 0.3, yc - 0.02, "3/4\" C", "C", "m", "center", "top")
    T(x1h + 0.15, (HA[1] + l2[1]) / 2 + 0.9, "3/4\"\nH+C", "C", "m", "left"); T(x1h + 0.15, (TV[1] + f2[1]) / 2 + 0.6, "1/2\"", "C", "m", "left"); T(B1[0] + 0.12, TV[1] + 1.3, "AP", "K", "m", "left", "bottom")
    T(xsp + 0.2, ywb + 1.9, "washer box: 1/2\" H+C, HA;\n2\" standpipe; vent or AAV", "C", "m", "left"); T(mid(ls)[0] - 0.2, ls[2] - 0.1, "laundry sink: 1/2\" H+C;\n1-1/2\" trap; vent or AAV", "C", "m", "right", "top")
    T(xsp + 0.2, yld - 0.15, "2\" down to the building drain in the crawl space", "D", "m", "left", "top"); T(TV1[0] + 1.15, HA[1] + 0.42, "AP", "K", "m", "left", "bottom")
    T(xh - 0.25, fxs(3, "fridge")[0][4] - 0.6, "1/2\" H+C to\nkitchen sink", "C", "m", "right"); T(dw[1] - 0.15, dw[4] - 0.2, KSTAG % "in the wall to S4", "D", "m", "right", "top")
    s("lead", MC[0] + 0.3, MC[3] - 0.1, MC[0] - 0.4, MC[3] + 1.3, MCTAG % ("109", gz[0][2]), "K", "m", "right")
    T(mid(fu)[0] + 0.42, G0[1] - 0.2, "GV+DL", "G", "i", "center", "top"); T(G0[0] - 0.15, wh[1] + 0.3, "GV+DL", "G", "i", "right")
    T(xh - 0.12, MC[3] + 1.3, "1/2\" H+C to\nkitchen sink", "C", "i", "right"); T(xc + 0.4, yh + 0.12, "3/4\" H", "H", "i", "center", "bottom"); T(xc + 0.4, yc - 0.12, "3/4\" C", "C", "i", "center", "top")
    return P, S


def plan4():
    P, S, p, s, T, tubs = base(4); B2, B1, HL, MC, PS, KT = (rm(4, n) for n in ("206", "205", "207", "208", "210", "202"))
    (TV, TD, t2), (TV1, TD1, t1) = tubs; (f2, f1), w1 = [flange(w) for w in fxs(4, "wc")], fxs(4, "wc")[1]; v2, v1 = fxs(4, "van"); l2, l1 = mid(v2), mid(v1); wy = (B2[3] + HL[1]) / 2
    wh, fu, rg, wa, sk, dw = fxs(4, "wh")[0][1:], fxs(4, "furnace")[0], fxs(4, "range")[0], fxs(4, "washer")[0], fxs(4, "sinkbase")[0], fxs(4, "dw")[0]
    xm, yl, s3, s4, ks, xb, yw1 = t2[1] - 0.33, B2[1] - 0.11, S3[4], S4[4], mid(sk), wa[1] + 0.42, B1[3] + 0.06
    # drains and vents. Bath 2 and the washer to S1; bath 1 to S3 behind its toilet; kitchen along the wall to S4. Each bath is a wet-vented group
    p("D", "3", f2, X(xm), Y(TD[1]), X(S1[0]), Y(S1[1])); p("D", "2", (l2[0], yl), (l2[0] + f2[1] - yl, f2[1]), X(f2[0])); p("D", "1.5", l2, Y(yl)); p("D", "2", TD, X(S1[0]))
    p("V", "v", (l2[0], yl - 0.06), X(xm - 0.4), Y(B2[3] + 0.12), X(VR0[0]), Y(VR0[1])); p("D", "2", (xb, wa[2] + 0.1), Y(S1[1] + 0.5), S1); p("V", "v", (xb - 0.25, wa[2] - 0.03), X(VR0[0]), Y(VR0[1]))
    p("D", "3", f1, X(s3[0]), Y(s3[1])); p("D", "2", (l1[0], yw1), (l1[0] - 0.9, yw1 - 0.9), Y(f1[1]), X(f1[0])); p("D", "1.5", l1, Y(yw1)); p("D", "2", TD1, X(l1[0] - yw1 + TD1[1]))
    p("V", "v", (l1[0], yw1 + 0.1), X(w1[1] + 0.55), Y(s3[1]), X(s3[0])); p("D", "2", ks, Y(s4[1]), X(s4[0]))
    for q in ((l2[0], yl - 0.06), (xb - 0.25, wa[2] - 0.03), (l1[0], yw1 + 0.1), (ks[0], s4[1] + 0.1)): s("vup", *q)
    for q in (S1, S2, s3, s4): s("stk", *q)
    s("vr", *VR0); s("co", xm, f2[1]); s("trap", ks[0], ks[1], 0.13); s("trap", xb, wa[2] + 0.1, 0.13)
    # water
    xh, xc, yci, ykh = MC[2] - 0.47, MC[2] - 0.22, wh[1] + 1.2, wh[1] + 0.55; ykc = ykh + 0.25; IN = (wh[0] - 0.75, yci)
    yct, yht, xc2, xh2, yce, yhe = PS[1] + 1.01, PS[1] + 1.26, HL[2] - 0.33, HL[2] - 0.58, HL[1] + 0.21, HL[1] + 0.43; xtv = S1[0] + 0.7; xac, xah = v2[3] + 0.65, v2[3] + 0.42
    xbc, xbh, xr, ybc, ybh = PS[0] + 0.33, PS[0] + 0.58, v1[3] + 0.35, B1[3] - 1.56, B1[3] - 1.31
    p("C", "3/4", IN, X(xc), Y(yct), X(xc2), Y(yce)); p("C", "3/4", (wh[0] + 0.25, yci), Y(wh[1])); p("C", "1/2", (xc, ykc), X(ks[0] - 0.15)); p("C", "1/2", (xb + 0.35, yct), Y(wa[2] + 0.15))
    p("C", "1/2", (xc2, yce), X(xtv - 0.1), Y(wy)); p("C", "1/2", (xc2, yce), X(xac), Y(B2[1] + 0.19), X(l2[0] + 0.2)); p("C", "1/2", (xac, B2[1] + 0.19), X(f2[0] - 0.5))
    p("C", "1/2", (xc2, yct), X(xbc), Y(ybc), X(xr), Y(w1[2] + 0.36), X(w1[1] + 0.8)); p("C", "1/2", (xr, ybc), X(v1[3] - 0.1)); p("C", "1/2", (xr, ybc), Y(B1[3] + 0.17), X(TV1[0] + 0.12))
    p("H", "3/4", (wh[0] - 0.5, wh[1]), Y(ykh), X(xh), Y(yht), X(xh2), Y(yhe)); p("H", "1/2", (xh, ykh), X(ks[0] + 0.15)); p("H", "1/2", (xb + 0.57, yht), Y(wa[2] + 0.15))
    p("H", "1/2", (xh2, yhe), X(xtv + 0.12), Y(wy)); p("H", "1/2", (xh2, yhe), X(xah), Y(B2[1] + 0.44), X(l2[0] - 0.2))
    p("H", "1/2", (xh2, yht), X(xbh), Y(ybh), X(v1[3] - 0.1)); p("H", "1/2", (xr + 0.22, ybh), Y(B1[3] + 0.32), X(TV1[0] - 0.12))
    for q in ((ks[0] - 0.15, ykc, "C"), (ks[0] + 0.15, ykh, "H"), (xb + 0.35, wa[2] + 0.15, "C"), (xb + 0.57, wa[2] + 0.15, "H"), (l2[0] + 0.2, B2[1] + 0.19, "C"), (l2[0] - 0.2, B2[1] + 0.44, "H"), (f2[0] - 0.5, B2[1] + 0.19, "C"),
              (w1[1] + 0.8, w1[2] + 0.36, "C"), (v1[3] - 0.1, ybc, "C"), (v1[3] - 0.1, ybh, "H"), (TV1[0] + 0.12, B1[3] + 0.17, "C"), (TV1[0] - 0.12, B1[3] + 0.32, "H")):
        s("dot", *q)
    s("tv", xtv, wy); s("ap", xtv, HL[1], "h"); s("ap", TV1[0], B1[3] + 0.42, "h")
    pd = (xh2 - 0.25, S1[1]); p("P", "pd", (wh[0] - 0.4, wh[1] - 1.03), Y(MC[1] + 0.15), X(pd[0]), Y(pd[1])); s("up", pd[0], pd[1], "P")
    # gas: furnace and water heater, and the range only if it is gas
    gz = gas(4); G0 = ((fu[3] + wh[0] - 0.92) / 2, MC[3] - 0.54)
    p("G", gz[1][2], G0, X(mid(fu)[0]), Y(fu[4] - 0.3)); p("G", gz[2][2], G0, Y(wh[1]), X(wh[0] - 0.92)); s("gv", mid(fu)[0] + 0.5, G0[1], "h"); s("gv", G0[0], wh[1] + 0.7, "v")
    if len(gz) > 3: p("G", gz[3][2], G0, Y(MC[3] - 0.24), X(MC[2] + 0.17), Y(KT[3] - 0.17), X(rg[3] - 0.26), Y(rg[4] - 0.3)); s("gv", rg[3] - 0.26, rg[4] + 0.5, "v")
    else: T(rg[1] - 0.15, mid(rg)[1], "electric range:\nno gas", "E", "m", "right")
    closet(p, s, 4, IN, ((IN[0] + 0.5, yci, "h"), (wh[0] + 0.25, wh[1] + 0.88, "vl"), (wh[0] + 0.25, wh[1] + 0.22, "vl")), G0,
           (MC[0] - 0.5, MC[3] + 0.75), (IN[0] - 0.1, MC[3] + 0.75), (-0.7, -0.7, wh[0] - 0.95, wh[1] - 0.95, "right", "top"))
    T((f2[0] + xm) / 2 + 0.1, f2[1] - 0.3, "3\"", "D", "m", "center", "top"); T(xm + 0.15, (f2[1] + TD[1]) / 2, "3\"", "D", "m", "left"); T(l2[0] + 0.75, f2[1] - 0.2, "2\" wet vent", "D", "m", "left", "top")
    T(l2[0] - 0.15, l2[1] + 0.2, "1-1/2\"", "D", "m", "right"); T(xm - 0.3, f2[1] + 0.45, "CO", "D", "m", "right"); T(TD[0] + 0.2, TD[1] - 0.3, "tub trap 1-1/2\",\n2\" arm", "D", "m", "left", "top")
    s("lead", l2[0] + 1.2, yl - 0.06, B2[0] + 0.3, B2[1] - 1.5, "1-1/2\" vent up in the lavatory wall,\nacross in the ceiling to VR", "V", "m", "left")
    s("lead", VR0[0], VR0[1], B2[0] + 0.25, B2[3] - 0.9, "VR 2\" vent riser\nfrom below, on up", "V", "m", "left"); s("lead", S1[0], S1[1], HL[2] + 1.3, HL[1] + 0.95, "S1 3\"", "D", "m", "left")
    s("lead", s3[0], s3[1], s3[0] - 0.4, s3[1] - 1.3, "S3 3\" stack in this wall;\non up as a 2\" vent", "D", "m", "right"); T(l1[0] - 1.05, (f1[1] + TD1[1]) / 2, "2\" wet\nvent", "D", "m", "right"); T(w1[1] + 0.7, f1[1] + 1.3, "1-1/2\" V\nto S3", "V", "m", "left")
    s("lead", s4[0], s4[1], s4[0] + 0.4, s4[1] + 1.3, "S4 2\" stack in this wall;\non up as a vent", "D", "m", "left"); s("lead", S2[0], S2[1], S2[0] + 0.6, S2[1] - 0.75, "S2 3\" passes down,\nboxed in the corner", "D", "m", "left")
    T(xh - 0.45, (yht + MC[1]) / 2, "3/4\" H+C", "C", "m", "right"); T((xbh + xh2) / 2, yct - 0.12, "1/2\" H+C to bath 1", "C", "m", "center", "top"); T(pd[0] - 0.15, HL[3] - 0.9, "3/4\"\nH+C", "C", "m", "right")
    T((xac + xc2) / 2 - 0.2, yhe + 0.12, "1/2\" H+C", "C", "m", "center", "bottom"); T(xac + 0.15, (B2[1] + B2[3]) / 2 + 0.9, "1/2\"\nH+C", "C", "m", "left"); T(xtv + 0.45, HL[1] + 0.2, "AP; valve 6\" off\ncentre to clear S1", "K", "m", "left", "bottom")
    T((xh + dw[1]) / 2 - 0.6, ykh - 0.15, "1/2\" H+C to kitchen sink", "C", "m", "center", "top"); T(pd[0] - 0.15, HL[1] + 1.3, "PD 1\" pan drain\ndown beside S1", "P", "m", "right")
    T(wa[3] + 0.2, mid(wa)[1], "washer box: 1/2\" H+C, HA;\n2\" standpipe to S1,\nvent to VR", "C", "m", "left"); T(min(dw[1], sk[1]) + 0.1, dw[2] - 0.2, KSTAG % "in the wall to S4", "D", "m", "left", "top")
    T(TV1[0] + 0.6, B1[3] + 0.55, "AP", "K", "m", "left", "bottom"); s("lead", MC[0] + 0.3, MC[3] - 0.15, MC[0] - 1.2, MC[3] + 1.6, MCTAG % ("208", gz[0][2]), "K", "m", "center")
    T(mid(fu)[0] + 0.5, G0[1] - 0.2, "GV+DL", "G", "i", "center", "top"); T(G0[0] - 0.15, wh[1] + 0.7, "GV+DL", "G", "i", "right"); T(xh - 0.38, MC[1] - 0.25, "3/4\" H", "H", "i", "right"); T(xc + 0.1, MC[1] - 0.25, "3/4\" C", "C", "i", "left")
    s("lead", pd[0], MC[1] - 0.45, MC[0] - 0.5, MC[1] - 0.9, "1\" pan drain: on in the floor,\ndown beside S1: find the route", "P", "i", "left")
    return P, S


def plan5():
    P, S, p, s, T, tubs = base(5); B1, HL, MC, C9, KT, LR = (rm(5, n) for n in ("305", "306", "307", "309", "302", "301"))
    (TV1, TD1, t1), = tubs; w1, v1 = fxs(5, "wc")[0], fxs(5, "van")[0]; f1, l1 = flange(w1), mid(v1); yA = rm(6, "403")[3]; xd = (f1[0] + TD1[0]) / 2
    wh, fu, rg, wa, sk, dw = fxs(5, "wh")[0][1:], fxs(5, "furnace")[0], fxs(5, "range")[0], fxs(5, "washer")[0], fxs(5, "sinkbase")[0], fxs(5, "dw")[0]
    xw, xsp, ywb, yk, xk2, ks, s3, s4 = B1[0] - 0.11, B1[0] - 0.27, mid(wa)[1], t1[2] - 0.17, B1[0] + 0.77, mid(sk), S3[5], S4[5]
    # drains and vents, all to S2 in the chase: bath 1 (wet-vented group), kitchen sink + dishwasher + washer on one 2 in. branch, attic bath A through the ceiling
    p("D", "3", f1, Y(S2[1] - 0.5), X(S2[0]), Y(S2[1])); p("D", "2", (xw, l1[1]), (xw + 1.2, l1[1] + 1.2), X(f1[0])); p("D", "1.5", l1, X(xw)); p("D", "2", TD1, Y(S2[1] - 0.5), X(f1[0]))
    p("D", "2", ks, Y(yk), X(xk2), Y(S2[1] + 0.63), X(S2[0]), Y(S2[1])); p("D", "2", (xsp, ywb), Y(yk)); p("D", "3", (xd, yA), Y(S2[1]), X(S2[0]))
    for q in ((xw, l1[1]), (xsp, ywb + 0.35), (ks[0], sk[4] + 0.1)): s("vup", *q)
    for q in (ks, (xsp, ywb)): s("trap", q[0], q[1], 0.13)
    for q in (S1, S2): s("stk", *q)
    for q in (VR0, s3, s4): s("vr", *q)
    s("up", RH[0], RH[1], "H"); s("up", RC[0], RC[1], "C")
    # water: heater in closet 307 serves this floor and, through risers beside S1, the attic
    xg, xcm, ysc, ysh, xeh, xec, yH, yC = fu[3] + 0.24, fu[3] + 0.59, MC[1] + 0.15, MC[1] + 0.35, MC[2] - 0.13, MC[2] + 0.12, HL[1] + 0.26, HL[1] + 0.51
    IN = (xcm, MC[3] - 0.45); xwh, xwc, ykh, ykc, xnh, xnc = B1[0] + 0.17, B1[0] + 0.42, t1[2] + 0.16, t1[2] + 0.36, B1[2] - 0.47, B1[2] - 0.22
    p("C", "3/4", IN, Y(ysc), X(xec), Y(yC), X(xwc), Y(ywb)); p("C", "3/4", (xcm, ysc), Y(RC[1]), X(RC[0])); p("C", "3/4", (xcm, wh[1]), X(wh[0] - 0.25))
    p("C", "1/2", (xwc, ywb), Y(ykc), X(ks[0] + 0.15)); p("C", "1/2", (xwc, ywb + 0.15), X(B1[0] - 0.05)); p("C", "1/2", (xnc, yC), Y(TV1[1] + 0.05), X(TV1[0] + 0.15))
    p("H", "3/4", (wh[0] + 0.25, wh[1]), Y(ysh), X(xeh), Y(yH), X(xwh), Y(ywb)); p("H", "3/4", (wh[0] + 0.25, ysh), X(RH[0]), Y(RH[1]))
    p("H", "1/2", (xwh, ywb), Y(ykh), X(ks[0] - 0.15)); p("H", "1/2", (xwh, ywb - 0.1), X(B1[0] - 0.05)); p("H", "1/2", (xnh, yH), Y(TV1[1] - 0.2), X(TV1[0] + 0.15))
    for q in ((ks[0] + 0.15, ykc, "C"), (ks[0] - 0.15, ykh, "H"), (B1[0] - 0.05, ywb + 0.15, "C"), (B1[0] - 0.05, ywb - 0.1, "H"), (xwc, l1[1] + 0.5, "C"), (xwh, l1[1] + 0.5, "H"), (xnc, w1[2], "C"),
              (TV1[0] + 0.15, TV1[1] + 0.05, "C"), (TV1[0] + 0.15, TV1[1] - 0.2, "H")):
        s("dot", *q)
    s("ap", S2[0] + 0.3, t1[2] + 0.08, "h"); pd = (VR0[0] - 0.45, S1[1]); p("P", "pd", (wh[0] - 0.78, wh[1] - 0.78), (wh[0] - 1.0, MC[1] - 0.17), X(pd[0]), Y(pd[1])); s("up", pd[0], pd[1], "P")
    # gas: the upper flat has the only gas range, and the long run to it
    gz = gas(5); G0 = (xg, LR[3] - 0.2); xk = KT[0] + 0.42
    p("G", gz[1][2], (mid(fu)[0], G0[1]), Y(fu[4] - 0.5)); p("G", gz[2][2], G0, Y(wh[1] - 0.55), X(wh[0] - 0.74)); s("gv", mid(fu)[0], G0[1] - 0.28, "v"); s("gv", xg, wh[1] - 0.15, "v")
    if len(gz) > 3:
        p("G", gz[3][2], G0, X(xk), Y(rg[2] + 0.5)); s("gv", xk, rg[2] - 0.5, "v"); T(xk + 0.15, (KT[1] + rg[2]) / 2 + 0.6, gz[3][2] + "\" G", "G", "m", "left")
        T((G0[0] + xk) / 2, G0[1] - 0.12, gz[3][2] + "\" G to the gas range, 65,000 Btu/h, in the ceiling framing; shutoff in the cabinet beside the range", "G", "m", "center", "top")
    closet(p, s, 5, IN, ((xcm, IN[1] - 0.38, "v"), (xcm + 0.28, wh[1], "hb"), (wh[0] - 0.55, wh[1], "hb")), G0,
           (MC[0] - 0.3, MC[3] + 1.95), (xcm + 0.1, MC[3] + 1.95), (0.6, 0.8, wh[0] + 0.2, wh[1] + 0.42, "center", "center"))
    s("lead", xd, yA + 1.6, B1[0] + 2.4, yA + 0.55, "3\" from attic bath A, in the\nceiling framing or a soffit", "D", "m", "center"); T(f1[0] + 0.1, f1[1] + 1.7, "3\"", "D", "m", "left")
    s("lead", S2[0], S2[1], S2[0] + 1.4, S2[1] + 0.45, "S2 3\" stack in the chase: bath 1, kitchen, washer and\nattic bath A; on up as a 3\" vent through the roof", "D", "m", "left")
    s("lead", S1[0], S1[1], C9[0] - 0.5, S1[1] - 1.6, "S1 3\" stack, VR 2\" vent riser and the 1\" pan\ndrain pass through the closet, boxed in:\nno fixtures here, firestop at the floor", "D", "m", "right")
    s("lead", RH[0], RH[1], C9[0] - 0.5, RH[1] + 0.2, "3/4\" H+C up to the attic", "C", "m", "right"); s("lead", s3[0], s3[1], s3[0] + 0.9, s3[1] + 1.25, "S3 2\" vent up\nin this wall", "V", "m", "left")
    s("lead", s4[0], s4[1], s4[0] - 0.5, s4[1] - 1.9, "S4 2\" vent up in\nthe stair wall", "V", "m", "center"); T((xw + f1[0]) / 2 + 0.3, l1[1] + 1.32, "2\" wet vent", "D", "m", "center", "bottom")
    T(xk2 + 0.2, yk - 0.12, "2\" sink + DW + washer,\nbelow the floor to S2", "D", "m", "left", "top"); T(xsp - 0.2, l1[1] + 0.5, "vents up in this wall\nto the eave space,\njoin the S2 vent", "V", "m", "right")
    T((xeh + xnh) / 2 + 1.2, yC + 0.12, "3/4\" H+C", "C", "m", "center", "bottom"); T((xwc + xnh) / 2, yC + 0.12, "3/4\" H+C", "C", "m", "center", "bottom"); T(xwc + 0.15, (HL[3] + ywb) / 2, "3/4\"", "C", "m", "left")
    T(xnc + 0.1, (B1[1] + w1[2]) / 2, "1/2\"", "C", "m", "left"); T(xsp - 0.2, ywb - 0.1, "washer box: 1/2\" H+C,\nHA; 2\" standpipe", "C", "m", "right"); T(S2[0] + 0.85, t1[2] + 0.02, "AP", "K", "m", "left", "top")
    T(dw[1] + 0.5, yk - 0.4, "1/2\" H+C up through the cabinet floor.\n" + KSTAG % "below the floor", "D", "m", "left", "top"); s("lead", MC[2] - 0.3, MC[1] + 0.2, MC[2] + 1.9, MC[1] - 1.3, MCTAG % ("307", gz[0][2]), "K", "m", "left")
    T(mid(fu)[0] - 0.15, G0[1] - 0.28, "GV+DL", "G", "i", "right"); T(xg - 0.15, wh[1] - 0.15, "GV+DL", "G", "i", "right"); T(xeh - 0.12, MC[3] + 0.25, "3/4\" H+C", "C", "i", "right")
    T(RC[0] + 0.25, RC[1] - 0.2, "3/4\" H+C\nup to attic", "C", "i", "left", "top"); T(pd[0] - 0.15, RC[1] + 0.05, "PD 1\" down\nbeside S1", "P", "i", "right"); T(S1[0] + 0.35, S1[1], "S1", "D", "i", "left"); T(VR0[0], VR0[1] - 0.25, "VR", "V", "i", "center", "top")
    return P, S


def plan6():
    P, S, p, s, T, tubs = base(6); BA, BB = rm(6, "403"), rm(6, "404")
    (TVA, TDA, tA), (TVB, TDB, tB) = tubs; (wA, wB), (vA, vB) = fxs(6, "wc"), fxs(6, "van"); fA, fB, lA, lB = flange(wA), flange(wB), mid(vA), mid(vB)
    xd = (flange(fxs(5, "wc")[0])[0] + tub(fxs(5, "tub")[0], "x+")[1][0]) / 2; yv = BB[3] + 0.17; xa = BA[0] - 0.08; v3 = (xa - 0.09, BA[1] - 0.17)
    # bath B on S1; bath A through the floor framing to S2 over bath 305. Bath A vents with S3 in its own wall, bath B to VR
    p("D", "3", fB, Y(S1[1]), X(S1[0])); p("D", "2", (lB[0], yv - 0.07), Y(S1[1]), X(fB[0])); p("D", "1.5", lB, Y(yv - 0.07)); p("D", "2", TDB, Y(S1[1]), X(lB[0]))
    p("D", "3", fA, X(xd), Y(BA[3])); p("D", "2", (xa, lA[1]), (xa + fA[1] - lA[1], fA[1]), X(fA[0])); p("D", "1.5", lA, X(xa)); p("D", "2", TDA, Y(fA[1]), X(xd))
    p("V", "v", (xa - 0.09, lA[1]), Y(v3[1])); p("V", "v", S3[5], v3); p("V", "v", (lB[0], yv), X(VR0[0]), Y(VR0[1]))
    for q in (v3, VR0, S4[6]): s("vr", *q)
    s("vup", xa - 0.09, lA[1]); s("vup", lB[0], yv); s("stk", *S1); s("arrow", xd, BA[3] - 0.1, xd, BA[3] + 0.45, "D"); s("up", RH[0], RH[1], "H"); s("up", RC[0], RC[1], "C")
    yb_c, yb_h, xb_c, xb_h, ya_c, ya_h, xw_c, xw_h = BB[3] - 0.43, BB[3] - 0.18, BB[2] - 0.47, BB[2] - 0.22, BA[1] - 0.6, BA[1] - 0.85, tA[1] - 0.35, tA[1] - 0.6
    p("C", "3/4", RC, Y(ya_c), X(xw_c)); p("C", "1/2", (RC[0], yb_c), X(xb_c), Y(TVB[1] + 0.18), X(BB[2] - 0.07)); p("C", "1/2", (TVA[0] + 0.1, ya_c), Y(BA[1] - 0.1))
    p("C", "1/2", (xw_c, ya_c), Y(wA[2] - 0.5), X(wA[1] + 0.8)); p("C", "1/2", (xw_c, vA[2] - 0.3), X(lA[0] + 0.2), Y(vA[2] + 0.2))
    p("H", "3/4", RH, Y(ya_h), X(xw_h)); p("H", "1/2", (RH[0], yb_h), X(xb_h), Y(TVB[1] - 0.17), X(BB[2] - 0.07)); p("H", "1/2", (TVA[0] - 0.15, ya_h), Y(BA[1] - 0.1))
    p("H", "1/2", (xw_h, ya_h), Y(vA[2] - 0.55), X(lA[0] - 0.2), Y(vA[2] + 0.2))
    for q in ((lB[0] + 0.2, yb_c, "C"), (lB[0] - 0.2, yb_h, "H"), (RC[0], wB[2], "C"), (wA[1] + 0.8, wA[2] - 0.5, "C"), (lA[0] + 0.2, vA[2] + 0.2, "C"), (lA[0] - 0.2, vA[2] + 0.2, "H")):
        s("dot", *q)
    s("tv", TVA[0], BA[1] - 0.17); s("ap", TVA[0], BA[1] - 0.44, "h"); s("tv", BB[2] + 0.17, TVB[1]); s("ap", BB[2] + 0.44, TVB[1], "v")
    T((fA[0] + xd) / 2, fA[1] + 0.15, "3\"", "D", "m", "center", "bottom"); T((xa + fA[0]) / 2 + 0.2, fA[1] + 0.15, "2\" wet vent", "D", "m", "center", "bottom"); T(TDA[0] + 0.15, (TDA[1] + fA[1]) / 2, "2\" tub arm", "D", "m", "left")
    T((lB[0] + fB[0]) / 2, S1[1] + 0.15, "2\" wet vent", "D", "m", "center", "bottom"); T(lB[0] - 0.15, (lB[1] + S1[1]) / 2 - 0.5, "2\"", "D", "m", "right"); T(TDB[0] + 0.12, S1[1] - 0.6, "2\"", "D", "m", "left")
    T(fB[0] + 0.15, fB[1] - 0.55, "3\"", "D", "m", "left")
    s("lead", xd, BA[3] + 0.3, BA[2] - 3.4, BA[3] + 1.5, "3\" on in the floor framing under the eave to S2: see P-103.\nS2 goes up through the roof there as a 3\" vent.", "D", "m", "center")
    s("lead", S1[0], S1[1], BA[0] + 1.3, S1[1] - 2.6, "S1: 3\" drain to below the floor; on up as a\n3\" vent through the roof at the old chimney\nopening. Box it in beside the tub.", "D", "m", "center")
    s("lead", VR0[0], VR0[1] + 0.25, BA[0] + 1.3, S1[1] + 0.4, "VR 2\" vent riser in the wall: takes the vents of\nthe lower and middle flat baths and of bath B,\njoins S1 6\" min above the flood rims", "V", "m", "center")
    s("lead", v3[0], v3[1], BA[0] - 2.4, BA[1] - 2.0, "S3 2\" vent: comes over in the floor from\nbelow, up in this wall with the bath A\nvent (1-1/2\"), through the roof", "V", "m", "center")
    s("lead", S4[6][0], S4[6][1], S4[6][0] + 2.2, S4[6][1] - 1.9, "S4 2\" vent: offset in the floor from\nbelow, up in this wall, through the roof", "V", "m", "left"); T((lB[0] + VR0[0]) / 2, yv + 0.2, "1-1/2\" vent to VR", "V", "m", "center", "bottom")
    T(BB[0] - 0.5, RH[1] + 0.6, "3/4\" H+C\nrisers from\nbelow", "C", "m", "right"); T((RC[0] + xw_c) / 2 + 0.3, ya_h - 0.12, "3/4\" H+C", "C", "m", "center", "top"); T((RC[0] + xb_c) / 2 + 0.6, yb_c - 0.12, "1/2\" H+C", "C", "m", "center", "top")
    T(xb_c - 0.15, (TVB[1] + yb_c) / 2, "1/2\"", "C", "m", "right"); T(xw_h - 0.15, (BA[1] + vA[2]) / 2, "1/2\"", "C", "m", "right"); T(TVA[0] + 0.5, BA[1] - 0.5, "AP", "K", "m", "left", "top")
    T(BB[2] + 0.55, TVB[1] - 0.55, "AP", "K", "m", "left", "top"); T(wA[1] + 0.9, wA[2] - 0.15, "floor supply", "C", "m", "left", "top")
    return P, S


def sym(ax, r, k=1.0, ins=False):
    """One symbol or tag. k scales the symbol (1 on plans in feet, 0.25 to 0.3 on the sheet in inches)."""
    kind, x, y = r[0], r[1], r[2]; z = 26
    circ = lambda rad, **kw: ax.add_patch(plt.Circle((x, y), rad * k, zorder=kw.pop("zorder", z), **kw))
    if kind == "stk": circ(0.27, fc="white", ec=DRC, lw=1.6); circ(0.1, fc=DRC, ec=DRC, lw=0.3, zorder=z + 1)
    elif kind == "vr": circ(0.17, fc="white", ec=VTC, lw=1.1)
    elif kind == "trap": circ(r[3], fc="white", ec=DRC, lw=0.9)
    elif kind == "vup": circ(0.11, fc=VTC, ec="white", lw=0.4)
    elif kind == "dot": circ(0.085, fc=COL[r[3]], ec="white", lw=0.3)
    elif kind == "up": circ(0.15, fc="white", ec=COL[r[3]], lw=1.0); circ(0.05, fc=COL[r[3]], ec=COL[r[3]], lw=0.2, zorder=z + 1)
    elif kind == "in": circ(0.17, fc=COL[r[3]], ec="white", lw=0.5); circ(0.06, fc="white", ec="white", lw=0.2, zorder=z + 1)
    elif kind == "et": circ(0.17, fc="white", ec=CWC, lw=0.9)
    elif kind == "tv": circ(0.14, fc="white", ec=HWC, lw=0.9); ax.plot([x - 0.14 * k, x + 0.14 * k], [y, y], color=CWC, lw=0.7, zorder=z + 1)
    elif kind == "pan": circ(1.1, fill=False, ec=COL["P"], lw=0.7, ls=(0, (2.5, 1.5)), zorder=20)
    elif kind == "co": circ(0.15, fc=DRC, ec="white", lw=0.4); ax.plot([x - 0.08 * k, x + 0.08 * k], [y, y], color="white", lw=0.6, zorder=z + 1)
    elif kind in ("valve", "gv"):
        c = GSC if kind == "gv" else COL[r[3]]; h = (r[3] if kind == "gv" else r[4] if len(r) > 4 else "h") == "h"; a, w = 0.17 * k, 0.1 * k
        ax.add_patch(MPoly([(x + (u if h else v), y + (v if h else u)) for u, v in [(-a, -w), (-a, w), (a, -w), (a, w)]], closed=True, fc="white", ec=c, lw=0.8, zorder=z))
        if kind == "gv": ax.plot([x, x + (0 if h else 0.24 * k)], [y, y - (0.24 * k if h else 0)], color=c, lw=1.4, zorder=z - 1, solid_capstyle="butt")
    elif kind == "ap":
        w, h = (0.9, 0.16) if r[3] == "h" else (0.16, 0.9)
        ax.add_patch(Rectangle((x - w * k / 2, y - h * k / 2), w * k, h * k, fc="#ffd54f", ec=INK, lw=0.6, zorder=z))
    elif kind == "arrow":
        ax.annotate("", xy=(r[3], r[4]), xytext=(x, y), arrowprops=dict(arrowstyle="-|>", color=COL[r[5]], lw=1.6, mutation_scale=7), zorder=z)
    elif kind == "tag" and r[5] in ("", "i" if ins else "m"):
        ax.text(x, y, r[3], fontsize=4.6 if ins else 3.7, color=COL[r[4]], ha=r[6], va=r[7], zorder=32, linespacing=1.12, clip_on=ins, bbox=dict(fc="white", ec="none", pad=0.25, alpha=0.88))
    elif kind == "lead" and r[7] in ("", "i" if ins else "m"):
        ax.annotate(r[5], xy=(x, y), xytext=(r[3], r[4]), fontsize=4.6 if ins else 3.7, color=COL[r[6]], ha=r[8], va="center", zorder=32, linespacing=1.12, annotation_clip=False,
                    bbox=dict(fc="white", ec="none", pad=0.25, alpha=0.9), arrowprops=dict(arrowstyle="-", color=COL[r[6]], lw=0.45, shrinkA=1, shrinkB=0))


def pipes(ax, P, ins=False):
    for i, (sy, z, pts) in enumerate(P):
        lw = LWD[z] * (1.25 if ins else 1.0); ds = DASH.get(sy)
        ax.plot([q[0] for q in pts], [q[1] for q in pts], color=COL[sy], lw=lw, ls=(0, tuple(v / lw for v in ds)) if ds else "-", zorder=14 + "DPVGCH".index(sy) + i * 1e-3,
                solid_capstyle="round", solid_joinstyle="round", dash_capstyle="butt")


LEG = [("D", "3", "Drain / waste, PVC. Size in inches;\nslope 1/4 in. per ft"), ("V", "v", "Vent: in wall or ceiling, 42 in. min\nabove the floor before it turns"),
       ("C", "3/4", "Cold water, PEX (thick 3/4, thin 1/2 in.)"), ("H", "3/4", "Hot water, PEX (thick 3/4, thin 1/2 in.)"), ("G", "3/4", "Gas, black steel or CSST. Size shown"),
       ("P", "pd", "Pan drain (PD) and T&P relief pipe")]
LSYM = [(("stk", 0, 0), "S1 to S4  drain stack"), (("vr", 0, 0), "VR vent riser, or a stack going on\nup as a vent"), (("trap", 0, 0, 0.18), "Fixture drain: toilet flange 12 in. off\nthe wall; trap of tub, sink, standpipe"),
        (("vup", 0, 0), "Vent goes up in this wall"), (("dot", 0, 0, "C"), "Fixture stop / connection"), (("valve", 0, 0, "C"), "Shutoff valve (SOV)"), (("gv", 0, 0, "h"), "GV+DL  gas cock and drip leg"),
        (("tv", 0, 0), "Tub valve, pressure-balance"), (("ap", 0, 0, "h"), "AP  access panel 12 x 12 in. behind"), (("co", 0, 0), "CO  cleanout"), (("up", 0, 0, "C"), "Riser: goes on up or down"),
        (("in", 0, 0, "C"), "Supply arrives (route to be found)")]


def legend(bg, y=9.9):
    bg.text(10.6, y, "LEGEND", fontsize=7, fontweight="bold", color=INK, va="center"); y -= 0.22
    for sy, z, t in LEG:
        pipes(bg, [(sy, z, [(10.6, y), (10.98, y)])])
        for i, ln in enumerate(t.split("\n")): bg.text(11.08, y - i * 0.115, ln, fontsize=5.2, color=INK, va="center")
        y -= 0.16 + 0.115 * t.count("\n")
    for r, t in LSYM:
        sym(bg, (r[0], 10.79, y) + r[3:], 0.25)
        for i, ln in enumerate(t.split("\n")): bg.text(11.08, y - i * 0.115, ln, fontsize=5.2, color=INK, va="center")
        y -= 0.16 + 0.115 * t.count("\n")
    for ln in ("HA hammer arrestor · ET expansion tank · DW dishwasher", "T&P relief valve · CW cold water · AAV air admittance valve", "All piping, fixtures and heaters are new. Pipes are drawn", "beside walls so they read; run them in the wall or joists."):
        bg.text(10.6, y, ln, fontsize=5.0, color=INK, va="center"); y -= 0.125
    return y


PLAN = {3: plan3, 4: plan4, 5: plan5, 6: plan6}
MECH = {3: "109", 4: "208", 5: "307"}; MECHV = {3: (1.25, 1.6), 4: (1.3, 1.1), 5: (2.0, 2.3)}      # closet room; margin of the enlarged plan below / above it
TITLE = {3: "Lower flat: plumbing and gas", 4: "Middle flat: plumbing and gas", 5: "Upper flat main floor: plumbing and gas", 6: "Attic: plumbing"}
COMMON = ("All levels", ["Design intent, to be confirmed by the", "licensed plumber and gas fitter. Joists:", "direction unknown. A 3 in. drain runs with", "them or in a furred ceiling; never notch.", "Schedules, risers, gas table: P-001."])
KITCH = ("Sinks and heater", ["Each sink: P-trap, and a vent or an air", "admittance valve (AAV). Dishwasher: drain", "to the sink tailpiece with a high loop.", "Heater: new 40 gal power vent, in a pan."])
NOTES = {
    3: [("This level", ["Everything is new. Baths 1 and 2 back onto", "the 2x6 wet wall and drain to stack S1 in", "it. Bath 2: tub and lavatory dry-vented,", "toilet wet-vented. Bath 1: a wet-vented",
                        "group on the common lavatory vent.", "Kitchen sink and dishwasher to S4 in the", "wall behind the range. Washer and laundry", "sink: 2 in. down to the building drain.",
                        "S2 (boxed at the kitchen wall) and S3 pass", "down from above. Cleanout at the base of", "each stack; all join a new 4 in. building", "drain, probably in the crawl space (access",
                        "door stuck): route to the sewer unknown.", "If this floor is a slab, saw-cut and trench.", "Bath 2 tub valve: the back of the wall is", "the bath 1 corner by the toilet. Panel high",
                        "on that wall or a front-serviced valve.", "Range is electric: no gas to it."]), KITCH, COMMON],
    4: [("This level", ["Everything is new.", "Bath 2 (206): a wet-vented group to S1:", "lavatory vent in its wall, 2 in. wet vent", "to the toilet, 3 in. on. Washer: 2 in. to S1.",
                        "S1 is in the 2x6 wall right behind the tub", "centre line: set the tub valve 6 in. off", "centre, or move S1 8 in. west.", "The toilet is 5 ft from S1: part of the 3",
                        "in. branch crosses joists whichever way", "they run. Fur the ceiling below or move", "the toilet: verify before framing.", "Bath 1 (205): a wet-vented group to S3 in",
                        "the wall behind its toilet.", "Kitchen sink and dishwasher: 2 in. in the", "wall to S4 behind the refrigerator.", "S2 passes down, boxed, in the stair corner.",
                        "Pan drain: 1 in., down beside S1 to the", "crawl space, then daylight or a floor drain.", "Range is electric: no gas to it."]), KITCH, COMMON],
    5: [("This level", ["Everything is new.", "Bath 1 (305): a wet-vented group to S2 in", "the chase at the tub end.", "Kitchen sink, dishwasher and washer: one",
                        "2 in. branch below the floor to S2. It is", "14 ft long: check the fall against the", "joist depth.", "Attic bath A joins S2 through the ceiling",
                        "framing (or a soffit) over bath 1.", "S1 and vent riser VR pass through closet", "309, boxed. S3 and S4 pass up as vents.", "Firestop at floor and ceiling.",
                        "One heater serves this floor and the attic.", "Pan drain: 1 in., down beside S1.", "Gas: 1 in. to the closet, 3/4 in. to the", "gas range (long run): table on P-001.",
                        "Kitchen sink is on an outside wall: bring", "its lines up through the cabinet floor."]), KITCH, COMMON],
    6: [("This level", ["Two new baths. No gas in the attic.", "Bath B (404): wet-vented group on S1.", "Bath A (403): wet-vented group, drains", "through the floor framing to S2 over bath",
                        "1 below: see P-103.", "Vents through the roof: S1 (3 in.) at the", "old chimney opening, with VR joined in;", "S2 in the eave over bath 1; S3 with the",
                        "bath A vent in the bath A wall; S4 in the", "wall by closet 407.", "S1 stands 5 in. off the wall between tub", "and toilet: box it in. The box leaves",
                        "about 10 in. beside the toilet centre", "line (15 in. wanted): jog S1 into the", "wall below the floor if it can be done.", "Bath A toilet is on the eave wall: use a",
                        "floor supply, no water in that wall.", "Hot and cold come up beside S1 and run in", "the attic floor. Insulate them where the", "floor is over the eaves.",
                        "Tub valves in the 2x6 walls, access", "panel on the bedroom side of each."]), COMMON],
}


def level(pdf, number, fl):
    fig, bg, ax = b.bsheet(number, TITLE[fl], fl, NOTES[fl], None)
    b.draw_base(ax, fl, "trade"); P, S = PLAN[fl](); pipes(ax, P)
    for r in S: sym(ax, r)
    y = legend(bg)
    if fl in MECH:                      # enlarged plan of the mechanical closet at 1/2 in. = 1 ft
        m = rm(fl, MECH[fl]); cx = (m[0] + m[2]) / 2; y0, y1 = m[1] - MECHV[fl][0], m[3] + MECHV[fl][1]; h = (y1 - y0) / 2.0; top = y - 0.25
        bg.text(10.6, top, f"MECHANICAL CLOSET {MECH[fl]}", fontsize=7, fontweight="bold", color=INK, va="center"); bg.text(13.2, top, "1/2 in. = 1 ft", fontsize=5.4, color=GREY, va="center", ha="right")
        ix = b.sx.axes(fig, 10.55, top - 0.15 - h, (cx - 2.7, cx + 2.7), (y0, y1), 2.0); b.draw_base(ix, fl, "trade"); pipes(ix, P, True)
        for r in S: sym(ix, r, 1.0, True)
        for t in ix.texts:              # keep everything the base plan draws inside the window
            t.set_clip_on(True)
            if getattr(t, "arrow_patch", None): t.set_annotation_clip(True); t.arrow_patch.set_clip_path(ix.patch)
        bg.add_patch(Rectangle((10.55, top - 0.15 - h), 2.7, h, fill=False, ec=INK, lw=0.6))
        ax.add_patch(Rectangle((cx - 2.7, y0), 5.4, y1 - y0, fill=False, ec=GREY, lw=0.5, ls=(0, (4, 2)), zorder=11))
    b.save(fig, number, pdf)


# ---------------------------------------------------------------------------------------------- P-001
FLATS = (("Lower", (3,)), ("Middle", (4,)), ("Upper", (5, 6)))


def riser(bg, x0, y0):
    """Drain and vent riser of the four stacks (not to scale). Fixture boxes are in flow order, the last one nearest its stack."""
    fy = {3: y0 + 0.55, 4: y0 + 1.4, 5: y0 + 2.25, 6: y0 + 3.1}; roof = y0 + 3.95; yb = y0 + 0.12; xs = dict(S1=x0 + 2.05, S2=x0 + 5.6, S3=x0 + 8.3, S4=x0 + 9.0); xv = xs["S1"] + 0.27
    tx = lambda x, y, t, c=DRC, ha="left": bg.text(x, y, t, fontsize=4.5, color=c, ha=ha, va="center", linespacing=1.15)
    for fl, y in list(fy.items()) + [(0, roof)]:
        bg.plot([x0 + 0.58, x0 + 9.15], [y, y], color=GREY, lw=0.9 if not fl else 0.5); bg.text(x0, y + 0.1, b.LV[fl]["name"].split(",")[0].split(" (")[0].upper() if fl else "ROOF", fontsize=5.0, color=GREY, fontweight="bold", va="center")
    for (nm, x), sz, top in zip(xs.items(), "3332", (6, 6, 4, 4)):
        pipes(bg, [("D", sz, [(x, yb), (x, fy[top] - 0.13)]), ("V", "v", [(x, fy[top] - 0.13), (x, roof + 0.25)])]); sym(bg, ("co", x - 0.12, yb + 0.14), 0.3); tx(x, roof + 0.34, f"{nm} {sz} in.", DRC, "center")
    pipes(bg, [("D", "3", [(xs["S1"], yb), (x0 + 9.3, yb)]), ("V", "v", [(xv, fy[3] + 0.55), (xv, fy[6] + 0.7), (xs["S1"], fy[6] + 0.7)])])
    bg.annotate("", xy=(x0 + 9.55, yb), xytext=(x0 + 9.25, yb), arrowprops=dict(arrowstyle="-|>", color=DRC, lw=1.4, mutation_scale=7))

    def grp(fl, name, names, x1, dx, stk, dry=(), vto=None):
        y, xf = fy[fl], [x1 + i * dx for i in range(len(names))]; xk = xs.get(stk, 0); iw = names.index("WC") if "WC" in names else len(names)
        segs = ([("D", "2", [(xf[0], y - 0.13), ((xf + [xk])[iw], y - 0.13)])] if stk else []) + ([("D", "3", [(xf[iw], y - 0.13), (xk, y - 0.13)])] if iw < len(names) else [])
        for x, t in zip(xf, names):
            bg.add_patch(Rectangle((x - 0.18, y + 0.04), 0.36, 0.19, fc="white", ec=DRC, lw=0.6, zorder=3)); bg.text(x, y + 0.135, t, fontsize=4.4, color=DRC, ha="center", va="center", zorder=4)
            segs.append(("D", "3" if t == "WC" else "1.5", [(x, y + 0.04), (x, y - 0.13 if stk else yb)]))
            if t in dry: segs.append(("V", "v", [(x - 0.12 * dx / abs(dx), y + 0.23), (x - 0.12 * dx / abs(dx), y + 0.55)] + ([(vto, y + 0.55)] if vto else [])))
        pipes(bg, segs); bg.text(min(xf) - 0.05, y + 0.37, name, fontsize=4.6, color=INK, va="center", fontweight="bold", bbox=dict(fc="white", ec="none", pad=0.2))
    a, c = x0 + 0.8, 0.44
    grp(6, "Bath B (404)", ("LAV", "TUB", "WC"), a, c, "S1", ("LAV",), xv); grp(4, "Bath 2 (206)", ("LAV", "WC", "TUB"), a, c, "S1", ("LAV",), xv); grp(3, "Bath 2 (106)", ("TUB", "WC", "LAV"), a, c, "S1", ("TUB", "LAV"), xv)
    grp(4, "Washer", ("CW",), x0 + 2.7, -c, "S1", ("CW",), xv); grp(3, "Bath 1 (105)", ("WC", "LAV", "TUB"), x0 + 3.58, -c, "S1", ("LAV",), xv); grp(3, "Laundry", ("LS", "CW"), x0 + 4.25, c, "", ("LS", "CW"))
    grp(5, "Bath 1 (305)", ("LAV", "WC", "TUB"), x0 + 4.3, c, "S2", ("LAV",), xs["S2"]); grp(6, "Bath A (403)", ("LAV", "WC", "TUB"), x0 + 6.9, -c, "S2", ("LAV",)); grp(5, "Kitchen, washer", ("KS", "CW"), x0 + 6.46, -c, "S2", ("KS", "CW"))
    grp(4, "Bath 1 (205)", ("LAV", "WC", "TUB"), x0 + 7.0, c, "S3", ("LAV",), xs["S3"]); grp(4, "Kitchen", ("KS",), x0 + 8.65, c, "S4", ("KS",)); grp(3, "Kitchen", ("KS",), x0 + 8.65, c, "S4", ("KS",))
    for q in ((xv + 0.06, fy[5] + 0.45, "VR 2 in.: bath vents of the\nlower and middle flats and\nbath B; joins S1 above", VTC), (x0 + 0.62, fy[5] + 0.3, "No fixtures on S1 at this level", GREY),
              (a + 0.1, fy[4] - 0.26, "2 in. wet vent"), (a + 0.98, fy[4] - 0.26, "3 in."), (x0 + 6.95, fy[6] - 0.26, "3 in. in the floor framing"), (x0 + 6.3, fy[5] - 0.26, "2 in. branch"),
              (x0 + 7.0, fy[6] + 0.75, "Bath A vent joins the\nS3 vent in its wall", VTC), (x0 + 5.9, fy[3] + 0.3, "S2 passes: boxed", GREY), (x0 + 4.83, fy[3] - 0.25, "2 in. to the\nbuilding drain"),
              (x0 + 8.15, fy[6] + 0.3, "S3, S4: vents only\nabove the middle flat", GREY, "right"), (x0 + 6.72, fy[5] + 0.42, "sink, washer:\nvent or AAV", VTC),
              (x0 + 0.62, y0 - 0.1, "New 4 in. building drain below the lower flat, probably in the crawl space (access door stuck): route to the sewer to be found. Cleanout at the base of every stack. KS = kitchen sink with the"),
              (x0 + 0.62, y0 - 0.23, "dishwasher on its tailpiece; CW = washer standpipe; LS = laundry sink. Each stack goes through the roof full size: S1 at the old chimney opening.")):
        tx(*q)


def water(bg, x0, y0, flat, groups):
    """Water riser sketch of one flat (not to scale): service, shutoffs, heater, trunks and the fixture groups."""
    yc, yh = y0 + 1.0, y0 + 0.15; xw = x0 + 0.62
    pipes(bg, [("C", "3/4", [(x0, yc), (x0 + 3.75, yc)]), ("C", "3/4", [(xw, yc), (xw, y0 + 0.73)]), ("H", "3/4", [(xw, y0 + 0.45), (xw, yh), (x0 + 3.75, yh)])])
    bg.add_patch(plt.Circle((xw, y0 + 0.59), 0.15, fc="#f3e9f7", ec=b.MECHC, lw=0.8, zorder=30)); bg.text(xw, y0 + 0.59, "WH", fontsize=4.4, color=b.MECHC, ha="center", va="center", zorder=31, fontweight="bold")
    sym(bg, ("in", x0, yc, "C"), 0.3); sym(bg, ("valve", x0 + 0.3, yc, "C"), 0.3); sym(bg, ("valve", xw, y0 + 0.88, "C", "v"), 0.3); sym(bg, ("et", xw + 0.2, y0 + 0.81), 0.3)
    bg.text(x0 - 0.02, yc + 0.13, f"{flat.upper()} FLAT  3/4 in. CW from the service · flat shutoff · heater shutoff · expansion tank (ET)", fontsize=4.6, color=INK, va="center", fontweight="bold")
    bg.text(xw - 0.2, y0 + 0.37, "40 gal, pan,\nT&P pipe", fontsize=4.2, color=b.MECHC, ha="right", va="center", linespacing=1.1); bg.text(xw + 0.3, y0 + 0.85, "ET", fontsize=4.2, color=CWC, va="center")
    for i, t in enumerate(groups):
        x = x0 + 1.25 + i * 0.6
        bg.add_patch(Rectangle((x - 0.27, y0 + 0.4), 0.54, 0.36, fc="white", ec=INK, lw=0.5)); bg.text(x, y0 + 0.58, t, fontsize=4.2, color=INK, ha="center", va="center", linespacing=1.1)
        pipes(bg, [("C", "1/2", [(x - 0.1, yc), (x - 0.1, y0 + 0.76)]), ("H", "1/2", [(x + 0.1, yh), (x + 0.1, y0 + 0.4)])])


def notes_sheet(pdf):
    gen = [("General notes", ["All piping, fixtures and heaters are new;", "all old piping comes out.", "Test before cover, inspector to witness:", "drains 10 ft head of water for 15 min;", "water lines at working pressure 15 min;",
                              "gas at 3 psi min for 10 min.", "Insulate every hot line, and any pipe in an", "outside wall, eave or unheated space.", "Keep water pipes out of outside walls. If", "one must be there, put it on the warm",
                              "side of the insulation.", "Firestop each pipe through a floor or wall", "between flats with a listed system: collar", "on plastic drain, sealant on PEX and steel.",
                              "Holes in joists: middle third of the depth,", "1/3 depth max, 2 in. from the edges. Steel", "plates where a pipe is within 1-1/4 in. of", "a stud face.",
                              "Cleanout at the base of each stack and", "where a branch turns over 45 degrees; a", "toilet or removable trap counts as one.", "Every sink gets a P-trap (no S-traps) and",
                              "a vent, or an air admittance valve where", "a vent cannot be reached.", "PEX: support every 32 in.; metal stubs at", "the heater as its maker requires.",
                              "Gas: shutoff within 6 ft of each appliance,", "drip leg at furnace and heater (not needed", "at a range). CSST: size by its maker's", "table and bond it."])]
    fig, bg, _ = b.bsheet("P-001", "Plumbing and gas notes, schedules, riser diagrams", 0, gen, sub="Rear building · all levels")
    H = lambda x, y, t: bg.text(x, y, t.upper(), fontsize=7, fontweight="bold", color=INK, va="center")
    bg.text(0.5, 10.25, "PLUMBING AND GAS: NOTES, FIXTURE SCHEDULE, RISER DIAGRAMS", fontsize=10, fontweight="bold", color=INK, va="center")

    def row(tag, name, desc, k):
        n = [sum(len(fxs(fl, k)) for fl in lv) for _, lv in FLATS]; return [tag, name, desc] + n + [sum(n), sum(n)]
    rows = [["Tag", "Fixture", "Description and rough-in (all new)", "Lower", "Middle", "Upper", "Total", "New"],
            row("T", "Bathtub", "60 x 30 in. alcove tub, pressure-balance valve; 1-1/2 in. trap, 2 in. drain at the valve end; access panel", "tub"),
            row("WC", "Toilet", "1.28 gal per flush, elongated, 12 in. rough-in; 3 in. drain; 1/2 in. cold", "wc"),
            row("L", "Lavatory", "24 in. vanity, lavatory and faucet; 1-1/4 in. trap, 1-1/2 in. drain; 1/2 in. hot + cold", "van"),
            row("KS", "Kitchen sink", "Sink and faucet; 1-1/2 in. P-trap, 2 in. drain; vent or air admittance valve; 1/2 in. hot + cold", "sinkbase"),
            row("DW", "Dishwasher hookup", "Hot off the sink stop; drain hose to the sink tailpiece above the trap, with a high loop", "dw"),
            row("WB", "Washer box", "Recessed box: 1/2 in. hot + cold with hammer arrestors; 2 in. standpipe and trap, vented", "washer"),
            row("LS", "Laundry sink", "Sink and faucet; 1-1/2 in. P-trap; vent or air admittance valve; 1/2 in. hot + cold", "lsink"),
            row("WH", "Water heater", "40 gal gas, power vent: see the water heater schedule", "wh")]
    H(0.5, 9.82, "Fixture schedule"); y = table(bg, 0.5, 9.66, [0.4, 1.1, 4.75, 0.5, 0.55, 0.5, 0.45, 0.4], rows, fs=5.4, rh=0.18)
    H(0.5, y - 0.19, "Water heater schedule")
    wr = [["Tag", "Where", "Serves", "Heater", "Gas input", "With each"]] + [
        [f"WH-{i + 1}", f"Mech. closet {MECH[lv[0]]}", f"{fl} flat" + (", levels 5 + 6" if len(lv) > 1 else ""), "New 40 gal gas, power vent", "40,000 Btu/h",
         "Pan + 1 in. drain, expansion tank, full-length relief pipe, shutoff"] for i, (fl, lv) in enumerate(FLATS)]
    y = table(bg, 0.5, y - 0.33, [0.5, 1.3, 1.4, 1.65, 0.9, 3.2], wr, fs=5.2, rh=0.18)
    H(0.5, y - 0.2, "Drain and vent riser: stacks S1 to S4 (not to scale)"); riser(bg, 0.5, 2.3)
    H(0.5, 1.93, "Water risers, one per flat (not to scale): each bath = tub + lavatory (hot + cold) + toilet (cold); 1/2 in. branches; upper flat risers to the attic beside S1")
    G = {"Lower": ["BATH 2", "BATH 1", "KITCHEN\nSINK + DW", "WASHER\n+ HA", "LAUNDRY\nSINK"], "Middle": ["BATH 2", "BATH 1", "KITCHEN\nSINK + DW", "WASHER\n+ HA"],
         "Upper": ["BATH 1", "KITCHEN\nSINK + DW", "WASHER\n+ HA", "ATTIC\nBATH A", "ATTIC\nBATH B"]}
    for i, (fl, _) in enumerate(FLATS): water(bg, 0.62 + i * 4.2, 0.55, fl, G[fl])
    gr = [["Flat", "Pipe section", "Load cfh", "Run ft", "Size", "Table cfh"]] + [[GASRUN[fl][0] if j == 0 else "", sec, load, GASRUN[fl][1] if j == 0 else "", sz + " in.", cap] for fl in GASRUN for j, (sec, load, sz, cap) in enumerate(gas(fl))]
    H(9.85, 9.82, "Gas load and pipe sizing (all new)"); yg = table(bg, 9.85, 9.66, [0.5, 1.05, 0.5, 0.42, 0.45, 0.48], gr, fs=5.0, rh=0.165)
    TB = lambda y, t, lines: b.text_block(bg, 9.85, y, t, lines, fs=5.0, lh=0.127)
    yg = TB(yg - 0.2, "How the gas table was made", [
        "Natural gas, one meter per flat, under 2 psi at the meter.", "Longest-run method, IFGC Table 402.4(2): Sch. 40 steel,", "0.5 in. w.c. drop, 1,000 Btu per cu ft. Every section of a",
        "flat is sized at that flat's longest run from the meter.", "Runs are ASSUMED: lower 40 ft, middle 50 ft, upper 70 ft.", "The meters exist but their place is not recorded: measure,",
        "then re-check. Main kept at 3/4 in. minimum.", "Loads: furnace 40,000 (upper 60,000), water heater 40,000.", "Only the upper flat range is gas (65,000 Btu/h); the lower",
        "and middle ranges and all dryers are electric."])
    yg = TB(yg - 0.03, "Basis of design: to confirm", [
        "IPC and IFGC used as the layout guide. Design intent, to be", "confirmed by the licensed plumber and gas fitter.", "Drains: PVC. Four new stacks, each with a cleanout at its",
        "base and a vent through the roof. S1 (old chimney shaft):", "attic bath B, middle bath 2 and washer, lower baths 1 and 2.", "S2 (chase at bath 305): attic bath A, upper bath 1, kitchen",
        "and washer. S3: middle bath 1. S4: middle and lower", "kitchens. Lower washer and laundry sink: building drain.", "Each bath is a wet-vented group (IPC 912). VR, 2 in., beside",
        "S1 takes the bath vents below the attic.", "Water: PEX, 3/4 in. trunks, 1/2 in. to each fixture; each", "flat has its own heater and its own cold shutoff."])
    TB(yg - 0.03, "There now (all to be removed) · not known", [
        "Three 40 gal gas heaters (2017, 2022, 2022) with no pans,", "tanks or full relief pipes; S-traps and wrongly piped", "sinks; dishwasher drains with no high loop; all old water,",
        "drain, vent and gas piping. The meters stay.", "Not known: joist direction and depth; where the meters,", "water service and sewer connection are. Stone foundation", "with a crawl space under part of the house (access door",
        "stuck): the service and building drain are probably there."])
    b.save(fig, "P-001", pdf)


SHEETS = [("P-001", "Plumbing and gas notes, fixture schedule, riser diagrams", notes_sheet)] + [
    (n, TITLE[fl], (lambda pdf, n=n, fl=fl: level(pdf, n, fl))) for n, fl in (("P-101", 3), ("P-102", 4), ("P-103", 5), ("P-104", 6))]

if __name__ == "__main__":
    from matplotlib.backends.backend_pdf import PdfPages
    with PdfPages(os.path.join(b.HERE, "drawings", "_test_plumbing.pdf")) as pdf:
        for n, t, fn in SHEETS:
            if len(sys.argv) < 2 or n in sys.argv[1:]: fn(pdf)
    print("ok")
