"""390 Forest Ave builder set: plumbing and gas sheets P-001 (notes, schedules, risers) and P-101 to P-104 (one per level).
Every position is worked out from the plan model in build390 (rooms, fixtures, stack, range fuel); only small offsets are typed here.
Design intent only, IPC / IFGC used as the layout guide: to be confirmed by the licensed plumber and gas fitter."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from matplotlib.patches import Rectangle, Polygon as MPoly  # noqa: E402

import build390 as b  # noqa: E402
from common import INK, GREY, table, plt  # noqa: E402

DRC, VTC, CWC, HWC, GSC, EXC = "#2a2f36", "#2e7d32", "#1565c0", "#c62828", "#a8760a", "#7d848c"
COL = dict(D=DRC, V=VTC, C=CWC, H=HWC, G=GSC, P="#6a4c93", E=EXC, K=INK)
DASH = dict(V=(3, 2), H=(7, 2), G=(6, 2, 1.2, 2), P=(1.3, 1.6), E=(2, 1.6))          # dash patterns in points; D and C are solid
LWD = {"3": 2.1, "2": 1.4, "1.5": 1.0, "1": 1.9, "3/4": 1.5, "1/2": 0.8, "v": 0.9, "pd": 0.8}
DV = {"x+": (1, 0), "x-": (-1, 0), "y+": (0, 1), "y-": (0, -1)}
S0 = b.STACK; VR0 = (S0[0] - 0.5, S0[1]); RH, RC = (S0[0] - 0.25, S0[1] + 0.75), (S0[0] + 0.05, S0[1] + 0.75)   # stack, vent riser, attic water risers
TUBEND = {3: ("x+", "y+"), 4: ("y+", "y+"), 5: ("x+",), 6: ("y-", "x+")}      # valve end of each tub in L["fx"] order (existing ones assumed: verify)
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


def base(fl):
    """Fixtures of one level, new bath first, plus the recorders used by the plan functions. Existing drains get an E mark; dishwashers get their hot line and drain hose."""
    P, S = [], []
    tubs = [tub(f, e) + (f,) for f, e in zip(fxs(fl, "tub"), TUBEND[fl])]
    for (tv, td, f), w, v in zip(tubs, fxs(fl, "wc"), fxs(fl, "van")):
        for pt, r, new in ((td, 0.13, f[5]), (flange(w), 0.22, w[4]), (mid(v), 0.13, v[5])):
            S.append(("trap", pt[0], pt[1], r) if new else ("ex", pt[0], pt[1]))
    for k in ("sinkbase", "lsink"):
        S.extend(("ex",) + mid(f) for f in fxs(fl, k))
    for d in fxs(fl, "dw"):
        a, c = mid(d), mid(fxs(fl, "sinkbase")[0]); n = math.hypot(c[0] - a[0], c[1] - a[1]); nx, ny = -(c[1] - a[1]) / n * 0.14, (c[0] - a[0]) / n * 0.14
        P.append(("H", "1/2", [(c[0] + nx, c[1] + ny), (a[0] + nx, a[1] + ny)])); P.append(("D", "1/2", [(a[0] - nx, a[1] - ny), (c[0] - nx, c[1] - ny)])); S.append(("dot", a[0] + nx, a[1] + ny, "H"))
    return P, S, (lambda sy, z, *a: P.append((sy, z, R(*a)))), (lambda *a: S.append(a)), tubs


def closet(p, s, fl, IN, feed, G0, gt, ct, tp):
    """Symbols every mechanical closet gets: cold entry + flat shutoff, heater shutoff, expansion tank, relief pipe, pan, gas entry.
    feed: flat valve, heater valve, tank (x, y, tag side). gt, ct: where the gas and cold water notes sit on the enlarged plan. tp: relief pipe direction and its tag."""
    wh = fxs(fl, "wh")[0][1:]
    s("in", IN[0], IN[1], "C"); s("in", G0[0], G0[1], "G"); s("valve", feed[0][0], feed[0][1], "C", feed[0][2][0]); s("valve", feed[1][0], feed[1][1], "C", feed[1][2][0]); s("et", feed[2][0], feed[2][1]); s("pan", *wh)
    p("P", "pd", (wh[0] + 0.92 * tp[0], wh[1] + 0.92 * tp[1]), (wh[0] + 1.1 * tp[0], wh[1] + 1.1 * tp[1])); s("tag", tp[2], tp[3], "T&P relief pipe\nto 6\" above pan", "P", "i", tp[4], tp[5])
    s("lead", IN[0], IN[1], ct[0], ct[1], "3/4\" CW in from existing\nservice: route unknown", "C", "i", "left")
    s("lead", G0[0], G0[1], gt[0], gt[1], gas(fl)[0][2] + "\" gas in from the flat's\nmeter: route unknown, verify", "G", "i", "left")
    for (x, y, o), t in zip(feed, ("flat SOV", "SOV", "ET")):                # tag side: h above, hb below, v right, vl left
        dx, dy, ha, va = {"h": (0, 0.2, "center", "bottom"), "hb": (0, -0.22, "center", "top"), "v": (0.22, 0, "left", "center"), "vl": (-0.22, 0, "right", "center")}[o]
        s("tag", x + dx, y + dy, t, "C", "i", ha, va)


def plan3():
    P, S, p, s, tubs = base(3); B2, B1, HA, MC = rm(3, "106"), rm(3, "105"), rm(3, "107"), rm(3, "109")
    (TV, TD, t2), (TV1, TD1, t1) = tubs; f2, (w1,) = flange(fxs(3, "wc")[0]), fxs(3, "wc")[1:]; l2, l1 = mid(fxs(3, "van")[0]), mid(fxs(3, "van")[1])
    ww = (B2[2] + B1[0]) / 2; SX, SY = ww, S0[1]; xm = B2[2] - 0.26; vr = (ww, SY - 0.62)      # 2x6 wet wall centre line; stack S stands in it here
    T = lambda x, y, t, c, w="m", ha="center", va="center": s("tag", x, y, t, c, w, ha, va)
    # drain, waste, vent: all three fixtures back onto the wet wall; tub and lavatory dry-vented, toilet wet-vented by the tub drain
    p("D", "3", f2, X(xm), Y(SY), X(SX)); p("D", "2", TD, X(xm), Y(f2[1])); p("D", "1.5", l2, X(ww)); p("V", "v", (xm, TD[1]), X(ww), Y(vr[1]))
    p("D", "3", (SX, SY), Y(HA[1] + 0.75)); s("arrow", SX, HA[1] + 0.75, SX, HA[1] + 1.25, "D")
    s("vup", ww, TD[1]); s("vup", ww, l2[1]); s("vr", *vr); s("stk", SX, SY); s("co", SX - 0.5, SY + 0.32)
    # water: heater in the closet, trunks along the hall ceiling, down the bath 1 side of the wet wall
    wh, fu, rg, wa, ls, sk, dw = fxs(3, "wh")[0][1:], fxs(3, "furnace")[0], fxs(3, "range")[0], fxs(3, "washer")[0], fxs(3, "lsink")[0], fxs(3, "sinkbase")[0], fxs(3, "dw")[0]
    xc, xh, yc, yh, x1c, x1h = MC[2] - 0.22, MC[2] - 0.47, HA[3] - 0.53, HA[3] - 0.28, B1[0] + 0.15, B1[0] + 0.37
    IN = (wh[0] - 0.6, MC[3] - 0.22); xwc, xwh, ywb, xls, ys = wa[1] + 0.12, wa[1] + 0.34, mid(wa)[1], ls[1] + 0.4, mid(sk)[1]
    p("C", "3/4", IN, X(xc), Y(yc), X(x1c), Y(l2[1] - 0.2)); p("C", "1/2", (x1c, l2[1] - 0.2), Y(TV[1] + 0.22), X(ww - 0.1)); p("C", "3/4", (xc, wh[1] + 0.25), X(wh[0] + 0.25))
    p("C", "3/4", (xc, yc), X(xwc)); p("C", "1/2", (xwc, yc), X(xls)); p("C", "1/2", (xwc, yc), Y(ywb)); p("C", "1/2", (xc, IN[1]), Y(ys + 0.15))
    p("C", "1/2", (x1c, l2[1] + 0.45), X(B2[2] + 0.08)); p("C", "1/2", (x1c, f2[1] + 0.5), X(B2[2] + 0.08)); p("C", "1/2", (TV1[0] - 0.18, yc), Y(TV1[1] + 0.2))
    p("H", "3/4", (wh[0], wh[1] - 0.3), X(xh), Y(yh), X(x1h), Y(l2[1] - 0.4)); p("H", "1/2", (x1h, l2[1] - 0.4), Y(TV[1] - 0.03), X(ww - 0.1))
    p("H", "3/4", (xh, yh), X(xwh)); p("H", "1/2", (xwh, yh), X(xls)); p("H", "1/2", (xwh, yh), Y(ywb)); p("H", "1/2", (xh, wh[1] - 0.3), Y(ys - 0.15))
    p("H", "1/2", (x1h, l2[1] + 0.7), X(B2[2] + 0.08)); p("H", "1/2", (TV1[0] + 0.08, yh), Y(TV1[1] + 0.2))
    for q in ((x1c, l1[1] - 0.6, "C"), (x1h, l1[1] - 0.6, "H"), (x1c, w1[2] - 0.35, "C"), (xls, yc, "C"), (xls, yh, "H"), (xc, ys + 0.15, "C"), (xh, ys - 0.15, "H"), (xwc, ywb, "C"), (xwh, ywb, "H"),
              (B2[2] + 0.08, l2[1] + 0.45, "C"), (B2[2] + 0.08, l2[1] + 0.7, "H"), (B2[2] + 0.08, f2[1] + 0.5, "C"), (TV1[0] - 0.18, TV1[1] + 0.2, "C"), (TV1[0] + 0.08, TV1[1] + 0.2, "H")):
        s("dot", *q)
    s("tv", ww - 0.12, TV[1] + 0.1); s("ap", B1[0], TV[1] + 0.75, "v"); s("ex", wa[1] + 0.45, wa[4] - 0.4)
    pd = (fu[3] + 0.35, MC[1] + 0.3); p("P", "pd", (wh[0] - 0.9, wh[1] - 0.63), pd); s("up", pd[0], pd[1], "P")
    s("lead", pd[0], pd[1], MC[0] - 0.4, MC[1] - 0.6, "1\" pan drain down\nto the crawl space:\nverify route", "P", "i", "left")
    # gas: enters at the closet; furnace and water heater only (the range here is electric)
    gz = gas(3); G0 = (fu[3] + 0.14, MC[3] - 0.17); xr = fu[3] - 0.11
    p("G", gz[1][2], G0, X(mid(fu)[0]), Y(fu[4] - 0.3)); p("G", gz[2][2], G0, Y(wh[1] - 0.5), X(wh[0] - 0.77)); s("gv", mid(fu)[0] + 0.42, G0[1], "h"); s("gv", G0[0], wh[1] + 0.3, "v")
    if len(gz) > 3: p("G", gz[3][2], G0, Y(MC[3] + 0.17), X(xr), Y(mid(rg)[1]), X(rg[1] + 0.9)); s("gv", rg[1] - 0.3, mid(rg)[1], "h")
    else: T(rg[1] - 0.15, mid(rg)[1], "electric range:\nno gas", "E", "m", "right")
    closet(p, s, 3, IN, (((IN[0] + xc) / 2, IN[1], "h"), (xc - 0.35, wh[1] + 0.25, "h"), (wh[0] + 0.25, wh[1] + 0.25, "hb")), G0,
           (MC[0] - 0.4, MC[3] + 0.7), (fu[3] + 0.3, MC[3] + 0.75), (0.25, -0.97, wh[0] - 0.3, MC[1] - 0.05, "center", "top"))
    T(xm - 0.12, (f2[1] + SY) / 2 - 0.55, "3\"", "D", "m", "right"); T(xm - 0.12, (TD[1] + f2[1]) / 2 + 0.3, "2\"", "D", "m", "right"); T(l2[0] - 0.1, l2[1] + 0.42, "1-1/2\"", "D")
    T(TD[0] - 0.25, TD[1], "tub trap 1-1/2\"", "D", "m", "right"); T(f2[0] - 0.3, f2[1] - 0.75, "WC 3\"", "D", "m", "right"); T(xm - 0.2, vr[1] + 0.02, "VR 2\"", "V", "m", "right"); T(xm - 0.2, SY + 0.12, "S 3\", CO at base", "D", "m", "right")
    s("lead", ww, f2[1] + 0.95, B2[0] + 0.15, f2[1] + 0.95, "1-1/2\" vents up in the wet\nwall, across at 42\" min to VR", "V", "m", "left")
    s("lead", SX, HA[1] + 1.0, HA[0] + 0.2, HA[1] + 1.55, "3\" to the existing building drain: probably\nin the crawl space (door stuck): verify", "D", "m", "left")
    T((x1c + xc) / 2 - 0.3, yh + 0.02, "3/4\" H", "H", "m", "center", "bottom"); T((x1c + xc) / 2 - 0.3, yc - 0.02, "3/4\" C", "C", "m", "center", "top")
    T((xc + xwc) / 2 + 0.3, yh + 0.02, "3/4\" H", "H", "m", "center", "bottom"); T((xc + xwc) / 2 + 0.3, yc - 0.02, "3/4\" C", "C", "m", "center", "top")
    T(x1h + 0.15, (HA[1] + l2[1]) / 2 + 0.4, "3/4\" H+C", "C", "m", "left"); T(x1h + 0.15, (TV[1] + f2[1]) / 2 + 0.6, "1/2\"", "C", "m", "left"); T(B1[0] + 0.12, TV[1] + 0.95, "AP", "K", "m", "left", "bottom")
    T(xwh + 0.15, (ywb + yc) / 2 + 0.6, "1/2\" H+C\nto washer box, HA", "C", "m", "left"); T(ls[3], ls[2] - 0.1, "1/2\" H+C to laundry sink", "C", "m", "right", "top")
    T(TV1[0] + 0.3, (TV1[1] + yc) / 2 + 0.3, "1/2\" to tub valve\n(end assumed: verify)", "C", "m", "left"); T(xh - 0.25, fxs(3, "fridge")[0][4] - 0.6, "1/2\" H+C to\nkitchen sink", "C", "m", "right")
    T(dw[1] - 0.15, dw[4] - 0.2, "DW: hot off the sink stop; drain to the sink\ntailpiece with a high loop. Sink: new P-trap\nand a vent or an air admittance valve (AAV)", "D", "m", "right", "top")
    s("lead", MC[0] + 0.3, MC[3] - 0.1, MC[0] - 0.4, MC[3] + 1.3, "Mechanical closet 109: see the enlarged plan.\n3/4\" CW and 3/4\" gas arrive here: meters exist,\nbut where they are is not recorded", "K", "m", "right")
    T(mid(fu)[0] + 0.42, G0[1] - 0.2, "GV+DL", "G", "i", "center", "top"); T(G0[0] - 0.15, wh[1] + 0.3, "GV+DL", "G", "i", "right")
    T(xh - 0.12, MC[3] + 1.3, "1/2\" H+C to\nkitchen sink", "C", "i", "right"); T(xh - 0.9, yh + 0.12, "3/4\" H", "H", "i", "center", "bottom"); T(xh - 0.9, yc - 0.12, "3/4\" C", "C", "i", "center", "top")
    return P, S


def plan4():
    P, S, p, s, tubs = base(4); B2, B1, HL, MC, PS, KT = (rm(4, n) for n in ("206", "205", "207", "208", "210", "202"))
    (TV, TD, t2), (TV1, TD1, t1) = tubs; f2, w1 = flange(fxs(4, "wc")[0]), fxs(4, "wc")[1]; v2, v1 = fxs(4, "van"); l2 = mid(v2); wy = (B2[3] + HL[1]) / 2
    xm, yl = t2[1] - 0.33, B2[1] - 0.11; T = lambda x, y, t, c, w="m", ha="center", va="center": s("tag", x, y, t, c, w, ha, va)
    # drain, waste, vent: wet-vented bath group. Lavatory dry vent in its wall; 2 in. wet vent to the toilet; 3 in. on to stack S
    p("D", "3", f2, X(xm), Y(TD[1]), X(S0[0]), Y(S0[1])); p("D", "2", (l2[0], yl), (l2[0] + f2[1] - yl, f2[1]), X(f2[0])); p("D", "1.5", l2, Y(yl)); p("D", "2", TD, X(S0[0]))
    p("V", "v", (l2[0], yl - 0.06), X(xm - 0.4), Y(B2[3] + 0.12), X(VR0[0]), Y(VR0[1]))
    s("vup", l2[0], yl - 0.06); s("vr", *VR0); s("stk", *S0); s("co", xm, f2[1])
    # water
    wh, fu, rg, wa, sk, dw = fxs(4, "wh")[0][1:], fxs(4, "furnace")[0], fxs(4, "range")[0], fxs(4, "washer")[0], fxs(4, "sinkbase")[0], fxs(4, "dw")[0]
    xh, xc, yci, ykh = MC[2] - 0.47, MC[2] - 0.22, wh[1] + 1.2, wh[1] + 0.55; ykc = ykh + 0.25; IN = (wh[0] - 0.75, yci)
    yct, yht, xc2, xh2, yce, yhe = PS[1] + 1.01, PS[1] + 1.26, HL[2] - 0.33, HL[2] - 0.58, HL[1] + 0.21, HL[1] + 0.43; xtv = S0[0] + 0.7; xac, xah = v2[3] + 0.65, v2[3] + 0.42
    xbc, xbh, xr, ybc, ybh = PS[0] + 0.33, PS[0] + 0.58, v1[3] + 0.35, B1[3] - 1.56, B1[3] - 1.31
    p("C", "3/4", IN, X(xc), Y(yct), X(xc2), Y(yce)); p("C", "3/4", (wh[0] + 0.25, yci), Y(wh[1])); p("C", "1/2", (xc, ykc), X(mid(sk)[0] - 0.15)); p("C", "1/2", (xc, yct), Y(wa[2] + 0.15))
    p("C", "1/2", (xc2, yce), X(xtv - 0.1), Y(wy)); p("C", "1/2", (xc2, yce), X(xac), Y(B2[1] + 0.19), X(l2[0] + 0.2)); p("C", "1/2", (xac, B2[1] + 0.19), X(f2[0] - 0.5))
    p("C", "1/2", (xc2, yct), X(xbc), Y(ybc), X(xr), Y(w1[2] + 0.36), X(w1[1] + 0.8)); p("C", "1/2", (xr, ybc), X(v1[3] - 0.1)); p("C", "1/2", (xr, ybc), Y(B1[3] + 0.1), X(TV1[0] + 0.12))
    p("H", "3/4", (wh[0] - 0.5, wh[1]), Y(ykh), X(xh), Y(yht), X(xh2), Y(yhe)); p("H", "1/2", (xh, ykh), X(mid(sk)[0] + 0.15)); p("H", "1/2", (xh, yht), Y(wa[2] + 0.15))
    p("H", "1/2", (xh2, yhe), X(xtv + 0.12), Y(wy)); p("H", "1/2", (xh2, yhe), X(xah), Y(B2[1] + 0.44), X(l2[0] - 0.2))
    p("H", "1/2", (xh2, yht), X(xbh), Y(ybh), X(v1[3] - 0.1)); p("H", "1/2", (xr + 0.22, ybh), Y(B1[3] + 0.3), X(TV1[0] - 0.12))
    for q in ((mid(sk)[0] - 0.15, ykc, "C"), (mid(sk)[0] + 0.15, ykh, "H"), (xc, wa[2] + 0.15, "C"), (xh, wa[2] + 0.15, "H"), (l2[0] + 0.2, B2[1] + 0.19, "C"), (l2[0] - 0.2, B2[1] + 0.44, "H"), (f2[0] - 0.5, B2[1] + 0.19, "C"),
              (w1[1] + 0.8, w1[2] + 0.36, "C"), (v1[3] - 0.1, ybc, "C"), (v1[3] - 0.1, ybh, "H"), (TV1[0] + 0.12, B1[3] + 0.1, "C"), (TV1[0] - 0.12, B1[3] + 0.3, "H")):
        s("dot", *q)
    s("tv", xtv, wy); s("ap", xtv, HL[1], "h"); s("ex", wa[1] + 0.4, wa[2] + 0.45)
    pd = (xh2 - 0.25, S0[1]); p("P", "pd", (xh - 0.25, wh[1] - 1.08), Y(yht + 0.25), X(pd[0]), Y(pd[1])); s("up", pd[0], pd[1], "P")
    # gas: furnace and water heater only (the range here is electric)
    gz = gas(4); G0 = ((fu[3] + wh[0] - 0.92) / 2, MC[3] - 0.54)
    p("G", gz[1][2], G0, X(mid(fu)[0]), Y(fu[4] - 0.3)); p("G", gz[2][2], G0, Y(wh[1]), X(wh[0] - 0.92)); s("gv", mid(fu)[0] + 0.5, G0[1], "h"); s("gv", G0[0], wh[1] + 0.7, "v")
    if len(gz) > 3: p("G", gz[3][2], G0, Y(MC[3] - 0.24), X(MC[2] + 0.17), Y(KT[3] - 0.17), X(rg[3] - 0.26), Y(rg[4] - 0.3)); s("gv", rg[3] - 0.26, rg[4] + 0.5, "v")
    else: T(rg[1] - 0.15, mid(rg)[1], "electric range:\nno gas", "E", "m", "right")
    closet(p, s, 4, IN, ((IN[0] + 0.5, yci, "h"), (wh[0] + 0.25, wh[1] + 0.88, "vl"), (wh[0] + 0.25, wh[1] + 0.22, "vl")), G0,
           (MC[0] - 0.5, MC[3] + 0.75), (IN[0] - 0.1, MC[3] + 0.75), (-0.7, -0.7, wh[0] - 0.95, wh[1] - 0.95, "right", "top"))
    T((f2[0] + xm) / 2 + 0.1, f2[1] - 0.3, "3\"", "D", "m", "center", "top"); T(xm + 0.15, (f2[1] + TD[1]) / 2, "3\"", "D", "m", "left"); T(l2[0] + 0.75, f2[1] - 0.2, "2\" wet vent", "D", "m", "left", "top")
    T(l2[0] - 0.15, l2[1] + 0.2, "1-1/2\"", "D", "m", "right"); T(xm - 0.3, f2[1] + 0.45, "CO", "D", "m", "right"); T(TD[0] + 0.2, TD[1] - 0.3, "tub trap 1-1/2\",\n2\" arm", "D", "m", "left", "top")
    s("lead", (l2[0] + xm) / 2 - 0.8, yl - 0.06, B2[0] - 0.5, B2[1] - 1.5, "1-1/2\" vent up in the lavatory wall,\nacross in the ceiling to VR", "V", "m", "right")
    s("lead", VR0[0], VR0[1], HL[0] + 2.3, HL[1] + 2.0, "VR 2\" vent riser\nfrom below, on up", "V", "m", "center"); s("lead", S0[0], S0[1], HL[2] + 0.9, HL[1] + 1.5, "S 3\" stack", "D", "m", "left")
    T(xh - 0.45, (yht + MC[1]) / 2, "3/4\" H+C", "C", "m", "right"); T((xh2 + xh) / 2 + 0.3, yct - 0.12, "3/4\" H+C", "C", "m", "center", "top"); T(pd[0] - 0.15, HL[3] - 0.9, "3/4\"\nH+C", "C", "m", "right")
    T((xbh + xh2) / 2, yct - 0.12, "1/2\" H+C to bath 1", "C", "m", "center", "top"); T((xac + xc2) / 2 - 0.2, yhe + 0.12, "1/2\" H+C", "C", "m", "center", "bottom"); T(xac + 0.15, (B2[1] + B2[3]) / 2 + 0.9, "1/2\"\nH+C", "C", "m", "left")
    T(xtv + 0.45, HL[1] + 0.2, "AP; valve 6\" off\ncentre to clear S", "K", "m", "left", "bottom"); T((xh + dw[1]) / 2 - 0.6, ykh - 0.15, "1/2\" H+C to kitchen sink", "C", "m", "center", "top")
    T(pd[0] - 0.15, HL[1] + 1.3, "PD 1\" pan drain\ndown beside S", "P", "m", "right"); T(xc + 0.15, wa[4] + 0.6, "1/2\" H+C to\nwasher box, HA", "C", "m", "left")
    T(sk[1] - 0.15, dw[2] - 0.2, "DW: hot off the sink stop; drain to the sink\ntailpiece with a high loop. Sink: new P-trap\nand a vent or an air admittance valve (AAV)", "D", "m", "right", "top")
    s("lead", MC[0] + 0.3, MC[3] - 0.15, MC[0] - 1.2, MC[3] + 1.6, "Mechanical closet 208: see the enlarged plan.\n3/4\" CW and 3/4\" gas arrive here: meters exist,\nbut where they are is not recorded", "K", "m", "center")
    T(mid(fu)[0] + 0.5, G0[1] - 0.2, "GV+DL", "G", "i", "center", "top"); T(G0[0] - 0.15, wh[1] + 0.7, "GV+DL", "G", "i", "right"); T(xh - 0.38, MC[1] - 0.25, "3/4\" H", "H", "i", "right"); T(xc + 0.1, MC[1] - 0.25, "3/4\" C", "C", "i", "left")
    s("lead", xh - 0.25, MC[1] - 0.45, MC[0] - 0.5, MC[1] - 0.8, "1\" pan drain: on in the floor,\ndown beside S: verify route", "P", "i", "left")
    return P, S


def plan5():
    P, S, p, s, tubs = base(5); B1, HL, MC, C9, KT, LR = (rm(5, n) for n in ("305", "306", "307", "309", "302", "301"))
    (TV1, TD1, t1), = tubs; w1, v1 = fxs(5, "wc")[0], fxs(5, "van")[0]; yA = rm(6, "403")[3]; xd = (flange(w1)[0] + TD1[0]) / 2; ES = ((t1[3] + B1[2]) / 2, TV1[1] + 0.72)
    T = lambda x, y, t, c, w="m", ha="center", va="center": s("tag", x, y, t, c, w, ha, va)
    p("D", "3", (xd, yA), Y(ES[1]), X(ES[0])); s("es", *ES); s("stk", *S0); s("vr", *VR0); s("up", RH[0], RH[1], "H"); s("up", RC[0], RC[1], "C")
    wh, fu, rg, wa, sk, dw, xe = fxs(5, "wh")[0][1:], fxs(5, "furnace")[0], fxs(5, "range")[0], fxs(5, "washer")[0], fxs(5, "sinkbase")[0], fxs(5, "dw")[0], fxs(5, "xequip")[0]
    xg, xcm, ysc, ysh, xeh, xec, yH, yC = fu[3] + 0.24, fu[3] + 0.59, MC[1] + 0.15, MC[1] + 0.35, MC[2] - 0.13, MC[2] + 0.12, HL[1] + 0.26, HL[1] + 0.51
    IN = (xcm, MC[3] - 0.45); xwh, xwc, ywb, ykh, ykc, xnh, xnc = B1[0] + 0.17, B1[0] + 0.42, mid(wa)[1], t1[2] + 0.16, t1[2] + 0.36, B1[2] - 0.47, B1[2] - 0.22
    p("C", "3/4", IN, Y(ysc), X(xec), Y(yC), X(xwc), Y(ywb)); p("C", "3/4", (xcm, ysc), Y(RC[1]), X(RC[0])); p("C", "3/4", (xcm, wh[1]), X(wh[0] - 0.25))
    p("C", "1/2", (xwc, ywb), Y(ykc), X(mid(sk)[0] + 0.15)); p("C", "1/2", (xwc, ywb + 0.15), X(B1[0] - 0.1)); p("C", "1/2", (xnc, yC), Y(TV1[1] + 0.05), X(TV1[0] + 0.15))
    p("H", "3/4", (wh[0] + 0.25, wh[1]), Y(ysh), X(xeh), Y(yH), X(xwh), Y(ywb)); p("H", "3/4", (wh[0] + 0.25, ysh), X(RH[0]), Y(RH[1]))
    p("H", "1/2", (xwh, ywb), Y(ykh), X(mid(sk)[0] - 0.15)); p("H", "1/2", (xwh, ywb - 0.1), X(B1[0] - 0.1)); p("H", "1/2", (xnh, yH), Y(TV1[1] - 0.2), X(TV1[0] + 0.15))
    for q in ((mid(sk)[0] + 0.15, ykc, "C"), (mid(sk)[0] - 0.15, ykh, "H"), (B1[0] - 0.1, ywb + 0.15, "C"), (B1[0] - 0.1, ywb - 0.1, "H"), (xwc, mid(v1)[1], "C"), (xwh, mid(v1)[1], "H"), (xnc, w1[2], "C"),
              (TV1[0] + 0.15, TV1[1] + 0.05, "C"), (TV1[0] + 0.15, TV1[1] - 0.2, "H")):
        s("dot", *q)
    s("ex", wa[3] - 0.4, wa[4] - 0.45); pd = (VR0[0] - 0.45, S0[1]); p("P", "pd", (wh[0] - 0.78, wh[1] - 0.78), (wh[0] - 1.0, MC[1] - 0.17), X(pd[0]), Y(pd[1])); s("up", pd[0], pd[1], "P")
    # gas: the upper flat has the only gas range, and the long run to it
    gz = gas(5); G0 = (xg, LR[3] - 0.2); xk = KT[0] + 0.42
    p("G", gz[1][2], (mid(fu)[0], G0[1]), Y(fu[4] - 0.5)); p("G", gz[2][2], G0, Y(wh[1] - 0.55), X(wh[0] - 0.74)); s("gv", mid(fu)[0], G0[1] - 0.28, "v"); s("gv", xg, wh[1] - 0.15, "v")
    if len(gz) > 3:
        p("G", gz[3][2], G0, X(xk), Y(rg[2] + 0.5)); s("gv", xk, rg[2] - 0.5, "v"); T(xk + 0.15, (KT[1] + rg[2]) / 2 + 0.6, gz[3][2] + "\" G", "G", "m", "left")
        T((G0[0] + xk) / 2, G0[1] - 0.12, gz[3][2] + "\" G to the gas range, 65,000 Btu/h, in the ceiling framing (reuse the old branch if it is this size and sound)", "G", "m", "center", "top")
    closet(p, s, 5, IN, ((xcm, IN[1] - 0.38, "v"), (xcm + 0.28, wh[1], "hb"), (wh[0] - 0.55, wh[1], "hb")), G0,
           (MC[0] - 0.3, MC[3] + 1.95), (xcm + 0.1, MC[3] + 1.95), (0.6, 0.8, wh[0] + 0.2, wh[1] + 0.42, "center", "center"))
    s("lead", xd, (yA + TV1[1]) / 2 - 0.6, B1[0] + 2.6, yA + 2.0, "3\" from attic bath A, in the\nceiling framing or a soffit,\nto the existing stack", "D", "m", "center")
    s("lead", ES[0], ES[1], B1[2] + 3.6, B1[3] + 1.0, "ES existing stack, assumed in this chase:\nverify place, size (3\" min) and vent", "E", "m", "left")
    s("lead", S0[0], S0[1], C9[0] - 0.5, S0[1] - 1.6, "S 3\" stack, VR 2\" vent riser and the 1\" pan\ndrain pass through the closet, boxed in:\nno fixtures here, firestop at the floor", "D", "m", "right")
    s("lead", RH[0], RH[1], C9[0] - 0.5, RH[1] + 0.2, "3/4\" H+C up to the attic", "C", "m", "right"); T(xe[1], xe[2] - 0.15, "cap the old gas and water lines here", "K", "m", "left", "top")
    T((xeh + xnh) / 2 + 1.2, yC + 0.12, "3/4\" H+C", "C", "m", "center", "bottom"); T((xwc + xnh) / 2, yC + 0.12, "3/4\" H+C", "C", "m", "center", "bottom"); T(xwc + 0.15, (HL[3] + ywb) / 2, "3/4\"", "C", "m", "left")
    T(xnc + 0.1, (B1[1] + w1[2]) / 2, "1/2\"", "C", "m", "left"); T(wa[3] - 0.15, ywb + 0.1, "washer box, HA", "C", "m", "right"); T(TV1[0] - 0.2, TV1[1] - 0.5, "1/2\" H+C to tub valve", "C", "m", "right", "top")
    T(dw[1] + 0.5, dw[2] - 0.2, "1/2\" H+C up through the cabinet floor.\nDW: hot off the sink stop; drain to the\nsink tailpiece with a high loop.\nSink: new P-trap, vent or AAV.", "D", "m", "left", "top")
    s("lead", MC[2] - 0.3, MC[1] + 0.2, MC[2] + 1.9, MC[1] - 1.3, "Mechanical closet 307: see the enlarged plan.\n3/4\" CW and " + gz[0][2] + "\" gas arrive here: meters exist,\nbut where they are is not recorded", "K", "m", "left")
    T(mid(fu)[0] - 0.15, G0[1] - 0.28, "GV+DL", "G", "i", "right"); T(xg - 0.15, wh[1] - 0.15, "GV+DL", "G", "i", "right"); T(xeh - 0.12, MC[3] + 0.25, "3/4\" H+C", "C", "i", "right")
    T(RC[0] + 0.25, RC[1] - 0.2, "3/4\" H+C\nup to attic", "C", "i", "left", "top"); T(pd[0] - 0.15, RC[1] + 0.05, "PD 1\" down\nbeside S", "P", "i", "right")
    return P, S


def plan6():
    P, S, p, s, tubs = base(6); BA, BB = rm(6, "403"), rm(6, "404")
    (TVA, TDA, tA), (TVB, TDB, tB) = tubs; (wA, wB), (vA, vB) = fxs(6, "wc"), fxs(6, "van"); fA, fB, lA, lB = flange(wA), flange(wB), mid(vA), mid(vB)
    w5 = fxs(5, "wc")[0]; xd = (flange(w5)[0] + tub(fxs(5, "tub")[0], "x+")[1][0]) / 2; yv = BB[3] + 0.17; xa = BA[0] - 0.08
    T = lambda x, y, t, c, w="m", ha="center", va="center": s("tag", x, y, t, c, w, ha, va)
    # bath B on stack S; bath A through the floor framing to the existing stack over bath 1 below
    p("D", "3", fB, Y(S0[1]), X(S0[0])); p("D", "2", (lB[0], yv - 0.07), Y(S0[1]), X(fB[0])); p("D", "1.5", lB, Y(yv - 0.07)); p("D", "2", TDB, Y(S0[1]), X(lB[0]))
    p("D", "3", fA, X(xd), Y(BA[3])); p("D", "2", (xa, lA[1]), (xa + fA[1] - lA[1], fA[1]), X(fA[0])); p("D", "1.5", lA, X(xa)); p("D", "2", TDA, Y(fA[1]), X(xd))
    p("V", "v", (xa - 0.09, lA[1]), Y(BA[1] - 0.17), X(VR0[0]), Y(VR0[1])); p("V", "v", (lB[0], yv), X(VR0[0]))
    s("vup", xa - 0.09, lA[1]); s("vup", lB[0], yv); s("vr", *VR0); s("stk", *S0); s("arrow", xd, BA[3] - 0.1, xd, BA[3] + 0.45, "D"); s("up", RH[0], RH[1], "H"); s("up", RC[0], RC[1], "C")
    yb_c, yb_h, xb_c, xb_h, ya_c, ya_h, xw_c, xw_h = BB[3] - 0.43, BB[3] - 0.18, BB[2] - 0.47, BB[2] - 0.22, BA[1] - 0.6, BA[1] - 0.85, tA[1] - 0.35, tA[1] - 0.6
    p("C", "3/4", RC, Y(ya_c), X(xw_c)); p("C", "1/2", (RC[0], yb_c), X(xb_c), Y(TVB[1] + 0.18), X(BB[2] - 0.07)); p("C", "1/2", (TVA[0] + 0.1, ya_c), Y(BA[1] - 0.1))
    p("C", "1/2", (xw_c, ya_c), Y(wA[2] - 0.5), X(wA[1] + 0.8)); p("C", "1/2", (xw_c, vA[2] - 0.3), X(lA[0] + 0.2), Y(vA[2] + 0.2))
    p("H", "3/4", RH, Y(ya_h), X(xw_h)); p("H", "1/2", (RH[0], yb_h), X(xb_h), Y(TVB[1] - 0.17), X(BB[2] - 0.07)); p("H", "1/2", (TVA[0] - 0.15, ya_h), Y(BA[1] - 0.1))
    p("H", "1/2", (xw_h, ya_h), Y(vA[2] - 0.55), X(lA[0] - 0.2), Y(vA[2] + 0.2))
    for q in ((lB[0] + 0.2, yb_c, "C"), (lB[0] - 0.2, yb_h, "H"), (RC[0], wB[2], "C"), (wA[1] + 0.8, wA[2] - 0.5, "C"), (lA[0] + 0.2, vA[2] + 0.2, "C"), (lA[0] - 0.2, vA[2] + 0.2, "H")):
        s("dot", *q)
    s("tv", TVA[0], BA[1] - 0.17); s("ap", TVA[0], BA[1] - 0.44, "h"); s("tv", BB[2] + 0.17, TVB[1]); s("ap", BB[2] + 0.44, TVB[1], "v")
    T((fA[0] + xd) / 2, fA[1] + 0.15, "3\"", "D", "m", "center", "bottom"); T((xa + fA[0]) / 2 + 0.2, fA[1] + 0.15, "2\" wet vent", "D", "m", "center", "bottom"); T(TDA[0] + 0.15, (TDA[1] + fA[1]) / 2, "2\" tub arm", "D", "m", "left")
    T((lB[0] + fB[0]) / 2, S0[1] + 0.15, "2\" wet vent", "D", "m", "center", "bottom"); T(lB[0] - 0.15, (lB[1] + S0[1]) / 2 - 0.5, "2\"", "D", "m", "right"); T(TDB[0] + 0.12, S0[1] - 0.6, "2\"", "D", "m", "left")
    T(fB[0] + 0.15, fB[1] - 0.55, "3\"", "D", "m", "left")
    s("lead", xd, BA[3] + 0.3, BA[2] - 3.4, BA[3] + 1.5, "3\" on in the floor framing under the eave\nto the existing stack: see P-103", "D", "m", "center")
    s("lead", S0[0], S0[1], BA[0] + 1.3, S0[1] - 2.6, "S: 3\" drain to below the floor; on up as a\n3\" vent through the roof at the old chimney\nopening. Box it in beside the tub.", "D", "m", "center")
    s("lead", VR0[0], VR0[1] + 0.25, BA[0] + 1.3, S0[1] + 0.4, "VR 2\" vent riser in the wall: takes the vents of\nthe lower and middle flat baths and of both attic\nbaths, joins S 6\" min above the flood rims", "V", "m", "center")
    s("lead", (xa + VR0[0]) / 2 - 1.6, BA[1] - 0.17, BA[0] - 2.2, BA[1] - 2.2, "1-1/2\" vents up in the wall,\nacross above the ceiling to VR", "V", "m", "center")
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
    elif kind == "es": circ(0.26, fc="white", ec=EXC, lw=1.2, ls=(0, (2, 1.2)))
    elif kind == "trap": circ(r[3], fc="white", ec=DRC, lw=0.9)
    elif kind == "ex":
        circ(0.27, fc="white", ec=EXC, lw=0.7, ls=(0, (2, 1.2)), zorder=12); ax.text(x, y, "E", fontsize=3.4, color=EXC, ha="center", va="center", zorder=13, fontweight="bold", clip_on=ins)
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
        ax.plot([q[0] for q in pts], [q[1] for q in pts], color=COL[sy], lw=lw, ls=(0, tuple(v / lw for v in ds)) if ds else "-", zorder=14 + "EDPVGCH".index(sy) + i * 1e-3,
                solid_capstyle="round", solid_joinstyle="round", dash_capstyle="butt")


LEG = [("D", "3", "Drain / waste, new. Size in inches;\nslope 1/4 in. per ft"), ("V", "v", "Vent, new: in wall or ceiling, 42 in.\nmin above the floor before it turns"),
       ("C", "3/4", "Cold water, PEX (thick 3/4, thin 1/2 in.)"), ("H", "3/4", "Hot water, PEX (thick 3/4, thin 1/2 in.)"), ("G", "3/4", "Gas, black steel or CSST. Size shown"),
       ("P", "pd", "Pan drain (PD) and T&P relief pipe")]
LSYM = [(("stk", 0, 0), "S  new 3 in. stack"), (("vr", 0, 0), "VR  2 in. vent riser beside S"), (("ex", 0, 0), "Existing drain and vent at this fixture\nstay as they are (not surveyed)"),
        (("trap", 0, 0, 0.18), "New fixture drain: toilet flange 12 in.\noff the wall; tub and lavatory trap"), (("vup", 0, 0), "Vent goes up in this wall"), (("dot", 0, 0, "C"), "Fixture stop / connection"),
        (("valve", 0, 0, "C"), "Shutoff valve (SOV)"), (("gv", 0, 0, "h"), "GV+DL  gas cock and drip leg"), (("tv", 0, 0), "Tub valve, pressure-balance"),
        (("ap", 0, 0, "h"), "AP  access panel 12 x 12 in. behind"), (("co", 0, 0), "CO  cleanout"), (("up", 0, 0, "C"), "Riser: goes on up or down"), (("in", 0, 0, "C"), "Supply arrives (route unknown)")]


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
    for ln in ("HA hammer arrestor · ET expansion tank · DW dishwasher", "T&P relief valve · CW cold water · AAV air admittance valve", "Pipes are drawn beside walls so they read;", "run them in the wall or joist space noted."):
        bg.text(10.6, y, ln, fontsize=5.0, color=INK, va="center"); y -= 0.125
    return y


PLAN = {3: plan3, 4: plan4, 5: plan5, 6: plan6}
MECH = {3: "109", 4: "208", 5: "307"}; MECHV = {3: (1.25, 1.6), 4: (1.3, 1.1), 5: (1.15, 2.3)}      # closet room; margin of the enlarged plan below / above it
TITLE = {3: "Lower flat: plumbing and gas", 4: "Middle flat: plumbing and gas", 5: "Upper flat main floor: plumbing and gas", 6: "Attic: plumbing"}
COMMON = ("All levels", ["Design intent, to be confirmed by the", "licensed plumber and gas fitter.", "Joist direction is not known: a 3 in. drain", "runs with the joists or in a furred-down",
                         "ceiling below. Never notch a joist for it.", "Schedules, risers, gas table: P-001."])
KITCH = ("Kitchen and heater", ["Kitchen sink: new P-trap, and a vent or an", "air admittance valve. Dishwasher: drain to", "the sink tailpiece with a high loop.",
                                "Heater: the existing one, reused if sound;", "new pan and drain, expansion tank and", "full-length relief pipe."])
NOTES = {
    3: [("This level", ["Bath 2 (106) is new: tub, toilet and", "lavatory all back onto the 2x6 wet wall.", "Stack S comes down in that wall; cleanout", "at its base, then 3 in. to the existing",
                        "building drain: probably in the crawl", "space (access door stuck): verify.", "If this floor is a slab, saw-cut and", "trench for the bath 2 drains.",
                        "Tub and lavatory each have a dry vent in", "the wet wall; the toilet is wet-vented by", "the tub drain. Vents join VR.", "Tub valve access: the back of the wall is",
                        "the bath 1 corner by the toilet. Panel", "high on that wall, or a valve serviced", "from the front: verify.", "Range is electric: no gas to it."]), KITCH, COMMON],
    4: [("This level", ["Bath 2 (206) is new, a wet-vented group:", "lavatory vent in its wall, 2 in. wet vent", "to the toilet, 3 in. on to stack S.", "Stack S is in the 2x6 wall right behind",
                        "the tub centre line: set the tub valve", "6 in. off centre, or move S 8 in. west.", "The toilet is 5 ft from S: part of the 3", "in. branch crosses joists whichever way",
                        "they run. Fur the ceiling below or move", "the toilet: verify before framing.", "Pan drain: 1 in., on in the floor, then", "down beside S to the crawl space and out",
                        "to daylight or a floor drain: verify.", "Bath 1 tub valve end is assumed.", "Range is electric: no gas to it."]), KITCH, COMMON],
    5: [("This level", ["No new fixtures here. Stack S, vent riser", "VR and the pan drain pass through closet", "309, boxed in. Firestop floor and ceiling.", "Attic bath A drains across the ceiling",
                        "framing of bath 1 to the existing stack,", "assumed in the chase at the tub end.", "Verify its place and size (3 in. min).", "Bath 1 fixtures then need their own",
                        "vents: check what is there.", "The heater moves from room 304 to closet", "307 and serves this floor and the attic.", "Cap the old gas and water in room 304.",
                        "Gas: 1 in. to the closet, 3/4 in. to the", "gas range (long run): table on P-001.", "Kitchen sink is on an outside wall: bring", "its lines up through the cabinet floor."]), KITCH, COMMON],
    6: [("This level", ["Two new baths. No gas in the attic.", "Bath B (404) is a wet-vented group on", "stack S. Bath A (403) is a wet-vented", "group that drains through the floor",
                        "framing to the existing stack over", "bath 1 (305) below: see P-103.", "Above the floor S is a 3 in. vent to the", "roof through the old chimney opening.",
                        "It stands 5 in. off the wall between tub", "and toilet: box it in. The box leaves", "about 10 in. beside the toilet centre", "line (15 in. wanted): jog S into the",
                        "wall below the floor if it can be done.", "Bath A toilet is on the eave wall: use a", "floor supply, no water in that wall.", "Hot and cold come up beside S and run in",
                        "the attic floor. Insulate them where the", "floor is over the eaves.", "Tub valves in the 2x6 walls, access", "panel on the bedroom side of each."]), COMMON],
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
            if hasattr(t, "set_annotation_clip"): t.set_annotation_clip(True)
        bg.add_patch(Rectangle((10.55, top - 0.15 - h), 2.7, h, fill=False, ec=INK, lw=0.6))
        ax.add_patch(Rectangle((cx - 2.7, y0), 5.4, y1 - y0, fill=False, ec=GREY, lw=0.5, ls=(0, (4, 2)), zorder=11))
    b.save(fig, number, pdf)


# ---------------------------------------------------------------------------------------------- P-001
FLATS = (("Lower", (3,)), ("Middle", (4,)), ("Upper", (5, 6)))


def count(k, levels, new=None): return sum(1 for fl in levels for f in fxs(fl, k) if new is None or f[-1] == new)


def riser(bg, x0, y0):
    """Drain and vent riser of stack S (not to scale), with attic bath A on the existing stack. Fixtures are in flow order."""
    fy = {6: y0 + 3.75, 5: y0 + 2.7, 4: y0 + 1.65, 3: y0 + 0.6}; roof = y0 + 4.85; xv, xs, xe = x0 + 2.6, x0 + 2.95, x0 + 3.5
    tx = lambda x, y, t, c=DRC, ha="left": bg.text(x, y, t, fontsize=4.6, color=c, ha=ha, va="center", linespacing=1.15)
    for fl, y in fy.items():
        bg.plot([x0 + 0.62, x0 + 5.0], [y, y], color=GREY, lw=0.5); bg.text(x0, y + 0.12, b.LV[fl]["name"].split(",")[0].split(" (")[0].upper(), fontsize=5.0, color=GREY, fontweight="bold", va="center")
    bg.plot([x0 + 0.62, x0 + 5.0], [roof, roof], color=GREY, lw=0.9); bg.text(x0, roof + 0.1, "ROOF", fontsize=5.0, color=GREY, fontweight="bold", va="center")
    pipes(bg, [("D", "3", [(xs + 0.75, y0 + 0.2), (xs, y0 + 0.2), (xs, fy[6] - 0.14)]), ("V", "v", [(xs, fy[6] - 0.14), (xs, roof + 0.3)]), ("V", "v", [(xv, fy[3] + 0.62), (xv, fy[6] + 0.8), (xs, fy[6] + 0.8)]),
               ("E", "v", [(xe, fy[5] - 0.45), (xe, roof + 0.3)])])
    bg.annotate("", xy=(xs + 1.0, y0 + 0.2), xytext=(xs + 0.7, y0 + 0.2), arrowprops=dict(arrowstyle="-|>", color=DRC, lw=1.4, mutation_scale=7)); sym(bg, ("co", xs - 0.16, y0 + 0.33), 0.3)

    def bath(fl, name, names, xf, xstk, dry, vto):
        y = fy[fl]; iw = names.index("WC"); sg = 1 if xstk > xf[0] else -1
        pipes(bg, [("D", "2", [(xf[0], y - 0.14), (xf[iw], y - 0.14)]), ("D", "3", [(xf[iw], y - 0.14), (xstk, y - 0.14)])])
        for x, t in zip(xf, names):
            bg.add_patch(Rectangle((x - 0.19, y + 0.04), 0.38, 0.2, fc="white", ec=DRC, lw=0.6, zorder=3)); bg.text(x, y + 0.14, t, fontsize=4.6, color=DRC, ha="center", va="center", zorder=4)
            pipes(bg, [("D", "3" if t == "WC" else "1.5", [(x, y + 0.04), (x, y - 0.14)])] + ([("V", "v", [(x - 0.12 * sg, y + 0.24), (x - 0.12 * sg, y + 0.62), (vto, y + 0.62)])] if t in dry else []))
        bg.text(min(xf) + 0.3, y + 0.42, name, fontsize=4.8, color=INK, va="center", fontweight="bold", bbox=dict(fc="white", ec="none", pad=0.3))
    xf = (x0 + 0.95, x0 + 1.5, x0 + 2.05)
    bath(6, "Bath B (404)", ("LAV", "TUB", "WC"), xf, xs, ("LAV",), xv); bath(4, "Bath 2 (206)", ("LAV", "WC", "TUB"), xf, xs, ("LAV",), xv); bath(3, "Bath 2 (106)", ("TUB", "WC", "LAV"), xf, xs, ("TUB", "LAV"), xv)
    bath(6, "Bath A (403)", ("LAV", "WC", "TUB"), (x0 + 4.8, x0 + 4.35, x0 + 3.9), xe, ("LAV",), xs)
    for a in ((xs + 0.08, roof + 0.4, "3 in. vent through the roof at the old chimney opening"), (xs - 0.08, fy[5] + 0.3, "S 3 in.", DRC, "right"), (xv - 0.07, fy[4] + 0.85, "VR 2 in.", VTC, "right"),
              (x0 + 0.75, fy[5] + 0.62, "No fixtures on S at this level (closet 309)", GREY), (xe + 0.08, fy[5] + 0.34, "Existing stack at bath 1 (305):\nplace, size, vent to roof: verify", EXC),
              (xe + 0.08, fy[5] - 0.3, "Bath 1 existing fixtures: they\nneed their own vents", EXC), (xv - 0.07, fy[6] + 0.92, "VR joins S 6 in. min above the flood rims", VTC),
              (xs + 1.05, y0 + 0.2, "3 in. to the existing building drain, probably\nin the crawl space (door stuck): verify"), (x0 + 0.62, y0 - 0.05, "Cleanout at the stack base. The lower flat branch joins the stack above the base, or the drain 30 in. min downstream of it."),
              (xf[0] + 0.12, fy[4] - 0.27, "2 in. wet vent"), (xf[1] + 0.3, fy[4] - 0.27, "3 in."), (xf[0] + 0.12, fy[6] - 0.27, "2 in. wet vent"), (xf[2] + 0.2, fy[6] - 0.27, "3 in."), (xf[0] + 0.12, fy[3] - 0.27, "2 in."),
              (xf[1] + 0.3, fy[3] - 0.27, "3 in."), (xs + 0.1, fy[4] - 0.3, "S offsets 5 in.\nin this floor", GREY), (xe + 0.5, fy[6] - 0.27, "3 in. in the floor framing")):
        tx(*a)


def water(bg, x0, y0, flat, groups):
    """Water riser sketch of one flat (not to scale): service, shutoffs, heater, trunks and the fixture groups."""
    yc, yh = y0 + 1.05, y0 + 0.2; xw = x0 + 0.62
    pipes(bg, [("C", "3/4", [(x0, yc), (x0 + 3.55, yc)]), ("C", "3/4", [(xw, yc), (xw, y0 + 0.78)]), ("H", "3/4", [(xw, y0 + 0.5), (xw, yh), (x0 + 3.55, yh)])])
    bg.add_patch(plt.Circle((xw, y0 + 0.64), 0.15, fc="#f3e9f7", ec=b.MECHC, lw=0.8, zorder=30)); bg.text(xw, y0 + 0.64, "WH", fontsize=4.4, color=b.MECHC, ha="center", va="center", zorder=31, fontweight="bold")
    sym(bg, ("in", x0, yc, "C"), 0.3); sym(bg, ("valve", x0 + 0.3, yc, "C"), 0.3); sym(bg, ("valve", xw, y0 + 0.93, "C", "v"), 0.3); sym(bg, ("et", xw + 0.2, y0 + 0.86), 0.3)
    bg.text(x0 - 0.02, yc + 0.14, f"{flat.upper()} FLAT   3/4 in. CW from existing service (verify) · flat shutoff · heater shutoff · expansion tank (ET)", fontsize=4.7, color=INK, va="center", fontweight="bold")
    bg.text(xw - 0.2, y0 + 0.42, "40 gal, pan,\nT&P pipe", fontsize=4.2, color=b.MECHC, ha="right", va="center", linespacing=1.1); bg.text(xw + 0.3, y0 + 0.9, "ET", fontsize=4.2, color=CWC, va="center")
    for i, t in enumerate(groups):
        x = x0 + 1.22 + i * 0.58
        bg.add_patch(Rectangle((x - 0.26, y0 + 0.45), 0.52, 0.36, fc="white", ec=INK, lw=0.5)); bg.text(x, y0 + 0.63, t, fontsize=4.2, color=INK, ha="center", va="center", linespacing=1.1)
        pipes(bg, [("C", "1/2", [(x - 0.1, yc), (x - 0.1, y0 + 0.81)]), ("H", "1/2", [(x + 0.1, yh), (x + 0.1, y0 + 0.45)])])


def notes_sheet(pdf):
    gen = [("General notes", ["Test before cover, inspector to witness:", "drains 10 ft head of water for 15 min;", "water lines at working pressure 15 min;", "gas at 3 psi min for 10 min.",
                              "Insulate every hot line, and any pipe in an", "outside wall, eave or unheated space.", "Keep water pipes out of outside walls. If", "one must be there, put it on the warm",
                              "side of the insulation.", "Firestop each pipe through a floor or wall", "between flats with a listed system: collar", "on plastic drain, sealant on PEX and steel.",
                              "Holes in joists: middle third of the depth,", "1/3 depth max, 2 in. from the edges. Steel", "plates where a pipe is within 1-1/4 in. of", "a stud face.",
                              "Cleanout at the base of S and where a", "branch turns over 45 degrees; a toilet or", "removable trap counts as one.", "Every sink gets a P-trap (no S-traps) and",
                              "a vent, or an air admittance valve where", "a vent cannot be reached.", "PEX: support every 32 in.; metal stubs at", "the heater as its maker requires.",
                              "Gas: shutoff within 6 ft of each appliance,", "drip leg at furnace and heater (not needed", "at a range). CSST: size by its maker's", "table and bond it."])]
    fig, bg, _ = b.bsheet("P-001", "Plumbing and gas notes, schedules, riser diagrams", 0, gen, sub="Rear building · all levels")
    H = lambda x, y, t: bg.text(x, y, t.upper(), fontsize=7, fontweight="bold", color=INK, va="center")
    bg.text(0.5, 10.25, "PLUMBING AND GAS: NOTES, FIXTURE SCHEDULE, RISER DIAGRAMS", fontsize=10, fontweight="bold", color=INK, va="center")

    def row(tag, name, desc, k, new=None):
        n = [count(k, lv) for _, lv in FLATS]; return [tag, name, desc] + n + [sum(n), sum(count(k, lv, True) for _, lv in FLATS) if new is None else new * sum(n)]
    rows = [["Tag", "Fixture", "Description and rough-in", "Lower", "Middle", "Upper", "Total", "New"],
            row("T", "Bathtub", "60 x 30 in. alcove tub, pressure-balance valve; 1-1/2 in. trap, 2 in. drain at the valve end", "tub"),
            row("WC", "Toilet", "1.28 gal per flush, elongated, 12 in. rough-in; 3 in. drain; 1/2 in. cold", "wc"),
            row("L", "Lavatory", "24 in. vanity, lavatory and faucet; 1-1/4 in. trap, 1-1/2 in. drain; 1/2 in. hot + cold", "van"),
            row("KS", "Kitchen sink", "Existing, stays. New P-trap, and a vent or air admittance valve; 1/2 in. hot + cold re-fed", "sinkbase", 0),
            row("DW", "Dishwasher", "Existing, stays. Hot off the sink stop; drain to the sink tailpiece above the trap, high loop", "dw", 0),
            row("WB", "Washer box", "New recessed box: 1/2 in. hot + cold with hammer arrestors, 2 in. standpipe on the existing drain", "washer", 1),
            row("LS", "Laundry sink", "Existing, stays. P-trap and vent as for the kitchen sink; 1/2 in. hot + cold re-fed", "lsink", 0),
            row("WH", "Water heater", "Existing 40 gal gas heaters, reused if sound: see the water heater schedule", "wh", 0)]
    H(0.5, 9.82, "Fixture schedule"); y = table(bg, 0.5, 9.66, [0.4, 0.95, 4.6, 0.5, 0.55, 0.5, 0.45, 0.4], rows, fs=5.4, rh=0.18)
    H(0.5, y - 0.2, "Water heater schedule")
    wr = [["Tag", "Where", "Serves", "Heater", "Gas input", "Add to each"]] + [
        [f"WH-{i + 1}", f"Mech. closet {MECH[lv[0]]}" + (" (moved from room 304)" if i == 2 else ""), f"{fl} flat" + (", levels 5 + 6" if len(lv) > 1 else ""), "Existing 40 gal gas, reused if sound", "40,000 Btu/h: check plate",
         "Pan + 1 in. drain, expansion tank, full-length relief pipe"] for i, (fl, lv) in enumerate(FLATS)]
    y = table(bg, 0.5, y - 0.35, [0.5, 2.0, 1.25, 1.75, 1.15, 2.7], wr, fs=5.2, rh=0.18)
    for i, ln in enumerate(("The house has three 40 gal gas heaters, made 2017, 2022 and 2022 (inspection report, 9 Oct 2026); which flat has which is not recorded. None has a pan, an expansion",
                            "tank or a full-length relief pipe today. The old chimney is being removed: check how each heater is vented. A draft-hood heater needs a listed flue to the roof (see the",
                            "mechanical sheets) or a new power-vent heater in its place. Pan drains fall by gravity: down to the crawl space, then to daylight 6 to 24 in. above grade or a floor drain.")):
        bg.text(0.5, y - 0.13 - i * 0.125, ln, fontsize=4.9, color=INK, va="center")
    y -= 0.5
    H(0.5, y - 0.22, "Drain and vent riser: stack S and the existing stack (not to scale)"); riser(bg, 0.5, 0.78)
    H(5.9, y - 0.22, "Water risers, one per flat (not to scale)")
    G = {"Lower": ["BATH 2\nnew", "BATH 1", "KITCHEN\nSINK + DW", "WASHER\n+ HA", "LAUNDRY\nSINK"], "Middle": ["BATH 2\nnew", "BATH 1", "KITCHEN\nSINK + DW", "WASHER\n+ HA"],
         "Upper": ["BATH 1", "KITCHEN\nSINK + DW", "WASHER\n+ HA", "ATTIC\nBATH A new", "ATTIC\nBATH B new"]}
    for i, (fl, _) in enumerate(FLATS): water(bg, 5.95, y - 1.7 - i * 1.4, fl, G[fl])
    bg.text(5.9, y - 4.72, "Each bath box = tub (hot + cold), lavatory (hot + cold), toilet (cold only), 1/2 in. branches.\nUpper flat: 3/4 in. hot and cold rise to the attic baths in the old chimney shaft.\nWater service and meter: probably at the crawl space; meters exist but their place is not recorded.",
            fontsize=4.8, color=INK, va="top", linespacing=1.3)
    gr = [["Flat", "Pipe section", "Load cfh", "Run ft", "Size", "Table cfh"]] + [[GASRUN[fl][0] if j == 0 else "", sec, load, GASRUN[fl][1] if j == 0 else "", sz + " in.", cap] for fl in GASRUN for j, (sec, load, sz, cap) in enumerate(gas(fl))]
    H(9.75, 9.82, "Gas load and pipe sizing"); yg = table(bg, 9.75, 9.66, [0.5, 1.05, 0.5, 0.42, 0.45, 0.53], gr, fs=5.0, rh=0.165)
    TB = lambda y, t, lines: b.text_block(bg, 9.75, y, t, lines, fs=5.0, lh=0.127)
    yg = TB(yg - 0.2, "How the gas table was made", [
        "Natural gas, one meter per flat, under 2 psi at the meter.", "Longest-run method, IFGC Table 402.4(2): Sch. 40 steel,", "0.5 in. w.c. drop, 1,000 Btu per cu ft. Every section of a",
        "flat is sized at that flat's longest run from the meter.", "Runs are ASSUMED: lower 40 ft, middle 50 ft, upper 70 ft.", "The meters exist but their place is not recorded: measure,",
        "then re-check. Main kept at 3/4 in. minimum.", "Loads: furnace 40,000 (upper 60,000), water heater 40,000.", "Only the upper flat range is gas (65,000 Btu/h); the lower",
        "and middle ranges and all dryers are electric."])
    yg = TB(yg - 0.03, "Basis of design: assumptions to confirm", [
        "IPC and IFGC used as the layout guide. Design intent, to be", "confirmed by the licensed plumber and gas fitter.", "One new 3 in. stack S in the old chimney shaft takes attic",
        "bath B, middle bath 2 and lower bath 2, then joins the", "existing building drain. It goes on up as a 3 in. vent.", "A 2 in. vent riser VR beside S takes the bath vents.",
        "Each new bath is a wet-vented group (IPC 912).", "Attic bath A drains to the existing stack at bath 1 (305).", "Water is PEX: 3/4 in. trunks, 1/2 in. to each fixture.",
        "Each flat keeps its own heater and gets its own cold", "shutoff. Existing baths and kitchens keep their drains."])
    TB(yg - 0.03, "Not known: verify before pricing", [
        "Joist direction and depth. Stone foundation with a crawl", "space under part of the house (access door stuck): the", "building drain and water service are probably there.",
        "Where the gas and water meters are. Pipe materials in", "place (replace lead, galvanized steel or polybutylene).", "Where the existing stack at bath 1 is, and how the",
        "existing fixtures are vented (S-traps were reported)."])
    b.save(fig, "P-001", pdf)


SHEETS = [("P-001", "Plumbing and gas notes, fixture schedule, riser diagrams", notes_sheet)] + [
    (n, TITLE[fl], (lambda pdf, n=n, fl=fl: level(pdf, n, fl))) for n, fl in (("P-101", 3), ("P-102", 4), ("P-103", 5), ("P-104", 6))]

if __name__ == "__main__":
    from matplotlib.backends.backend_pdf import PdfPages
    with PdfPages(os.path.join(b.HERE, "drawings", "_test_plumbing.pdf")) as pdf:
        for n, t, fn in SHEETS:
            if len(sys.argv) < 2 or n in sys.argv[1:]: fn(pdf)
    print("ok")
