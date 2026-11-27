"""390 Forest Ave electrical: design inputs, NEC load calculations (sheet E-002) and lighting calculations (sheet E-003).

Every number on the two sheets is computed here from the plan model in build390.py and the inputs at the top of this file,
so the sheets show their own arithmetic. Change an input (a nameplate, an area rule, a target) and rebuild.
"""
import math
import os
import sys

import numpy as np
from shapely.geometry import box, Point, Polygon
from shapely.ops import unary_union

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build390 as b  # noqa: E402
from common import INK, GREY, table  # noqa: E402

V = 240                                     # 120/240 V single phase, 3-wire
CODE = "NEC 2020 (confirm the edition Morgantown enforces)"

# ---------------------------------------------------------------------------------------------- equipment assumed per flat
# Nameplates are typical values for the class of appliance; the electrician confirms them against what is bought.
APPL = dict(range=("Electric range, 30 in. freestanding", 12000), dryer=("Electric clothes dryer", 5500), dw=("Dishwasher", 1200),
            mw=("Over-range microwave with vented hood", 1650), fridge=("Refrigerator (own circuit)", 720),
            fan=("Bath exhaust fan, 80 cfm, humidity sensing", 50), mirror=("LED mirror, built-in light and anti-fog pad", 60),
            whv=("Gas water heater, power-vent fan", 200))
# Gas furnace with a split air conditioner (outdoor condenser + coil on the furnace). MCA = minimum circuit ampacity on the
# condenser nameplate (125 % of the compressor current + the fan); MOCP = largest breaker it allows. Blower = furnace fan current.
AC = {"A": dict(ton=1.5, mca=10.0, mocp=15, blower=5.0), "B": dict(ton=2.0, mca=12.0, mocp=20, blower=6.0), "C": dict(ton=3.0, mca=18.0, mocp=30, blower=7.6)}
FLATS = {"A": dict(name="Lower flat", short="lower", levels=(3,), sa=3, baths=2, beds=2),
         "B": dict(name="Middle flat", short="middle", levels=(4,), sa=4, baths=2, beds=2),
         "C": dict(name="Upper flat (main floor, attic and its entrance stair hall)", short="upper", levels=(5, 6), sa=4, baths=3, beds=4)}
STAIR_HALL_C = (19.6, 20.9, 31.5, 27.8)       # on the middle flat's level, but part of the upper flat


# ---------------------------------------------------------------------------------------------- floor areas (NEC 220.12: outside dimensions)
def outline(fl):
    """Outer outline of a level: walls and rooms merged, holes filled."""
    g = b.geom(fl); L = b.LV[fl]
    parts = [g["walls"]] + [b.wshape(r) for r in L["new"] + L["fix"]] + [box(*q) for r in L["rooms"] for q in r["rects"]]
    u = unary_union(parts).buffer(0.25).buffer(-0.25)
    return Polygon(max((list(u.geoms) if hasattr(u, "geoms") else [u]), key=lambda p: p.area).exterior)


def areas():
    o = {fl: outline(fl).area for fl in (3, 4, 5, 6)}
    sh = outline(4).intersection(box(*STAIR_HALL_C)).area
    raw = {"A": o[3], "B": o[4] - sh, "C": o[5] + o[6] + sh}
    how = {"A": f"lower level {o[3]:.0f} sf", "B": f"middle level {o[4]:.0f} sf less the upper flat's stair hall {sh:.0f} sf",
           "C": f"main floor {o[5]:.0f} + attic {o[6]:.0f} + stair hall {sh:.0f} sf"}
    return {k: int(round(v / 10.0)) * 10 for k, v in raw.items()}, how


AREA, AREA_HOW = areas()


# ---------------------------------------------------------------------------------------------- per-flat loads
def ac_va(k):
    a = AC[k]; return a["mca"] * V + a["blower"] * 120


def heat_va(k):
    return (AC[k]["blower"] + 1.0) * 120          # gas furnace: blower + inducer and igniter (about 1 A)


def fixed_items(k):
    f = FLATS[k]
    return [("Dishwasher", APPL["dw"][1]), ("Microwave / hood", APPL["mw"][1]), ("Water heater vent fan", APPL["whv"][1]),
            (f"Bath fans x {f['baths']}", APPL["fan"][1] * f["baths"]), (f"LED anti-fog mirrors x {f['baths']}", APPL["mirror"][1] * f["baths"])]


def standard(k):
    """NEC 220 Part III, one dwelling unit (sizes the flat's own feeder and panel)."""
    f = FLATS[k]; A = AREA[k]; rows = []
    lt = 3 * A; sa = 1500 * f["sa"]; ld = 1500; s = lt + sa + ld
    d1 = min(s, 3000) + 0.35 * max(0, s - 3000)
    rows += [("General lighting and receptacles, 220.12", f"3 VA x {A:,} sf", lt, None),
             ("Small-appliance circuits, 220.52(A)", f"1,500 VA x {f['sa']} kitchen counter circuits", sa, None),
             ("Laundry circuit, 220.52(B)", "1,500 VA x 1", ld, None),
             ("  Subtotal, demand by Table 220.42", f"3,000 at 100 % + {s - 3000:,} at 35 %", s, d1)]
    fx = fixed_items(k); sfx = sum(v for _n, v in fx); dfx = 0.75 * sfx if len(fx) >= 4 else sfx
    rows += [("Fixed appliances, 220.53 (4 or more: 75 %)", ", ".join(f"{n} {v:,}" for n, v in fx), sfx, dfx),
             ("Clothes dryer, 220.54", f"nameplate {APPL['dryer'][1]:,} VA (at least 5,000)", APPL["dryer"][1], max(5000, APPL["dryer"][1])),
             ("Range, Table 220.55 Column C", "one range, 12 kW or less: 8 kW", APPL["range"][1], 8000)]
    c, h = ac_va(k), heat_va(k)
    rows.append(("Cooling or heating, larger only, 220.60", f"cooling {c:,.0f} (condenser MCA {AC[k]['mca']:g} A x 240 + blower {AC[k]['blower']:g} A x 120) vs gas heat {h:,.0f}", c, max(c, h)))
    tot = d1 + dfx + max(5000, APPL["dryer"][1]) + 8000 + max(c, h)
    return rows, tot


def optional(k):
    """NEC 220.82, one dwelling unit (the method normally used for a dwelling feeder)."""
    f = FLATS[k]; A = AREA[k]
    items = [("3 VA per sf, 220.82(B)(1)", f"3 x {A:,} sf", 3 * A),
             ("Small-appliance and laundry circuits, (B)(2)", f"1,500 x ({f['sa']} + 1)", 1500 * (f["sa"] + 1)),
             ("Range, (B)(3) nameplate", APPL["range"][0], APPL["range"][1]), ("Dryer, (B)(3)", APPL["dryer"][0], APPL["dryer"][1]),
             ("Refrigerator on its own circuit, (B)(3)", "nameplate", APPL["fridge"][1])] + [(n + ", (B)(3)", "nameplate", v) for n, v in fixed_items(k)]
    g = sum(v for _n, _h, v in items); dg = min(g, 10000) + 0.4 * max(0, g - 10000)
    c = ac_va(k)
    return items, g, dg, c, dg + c


def service():
    """NEC 220.84, optional method for a multifamily dwelling: 3 or more units, each with electric cooking and air conditioning."""
    per = {}
    for k in FLATS:
        f = FLATS[k]
        per[k] = [("3 VA per sf", 3 * AREA[k]), ("Small-appliance and laundry circuits", 1500 * (f["sa"] + 1)), ("Range", APPL["range"][1]),
                  ("Dryer", APPL["dryer"][1]), ("Refrigerator", APPL["fridge"][1])] + fixed_items(k) + [("Air conditioning (larger than gas heat)", ac_va(k))]
    conn = {k: sum(v for _n, v in it) for k, it in per.items()}
    tot = sum(conn.values()); dem = 0.45 * tot
    return per, conn, tot, dem


def service_standard():
    """For comparison: NEC 220 Part III applied to the whole building."""
    s = sum(3 * AREA[k] + 1500 * FLATS[k]["sa"] + 1500 for k in FLATS); d1 = 3000 + 0.35 * (s - 3000)
    fx = sum(v for k in FLATS for _n, v in fixed_items(k)); dfx = 0.75 * fx
    dry = 3 * max(5000, APPL["dryer"][1]); rng = 14000; c = sum(ac_va(k) for k in FLATS)
    rows = [("Lighting, small-appliance and laundry, Table 220.42", s, d1), ("Fixed appliances at 75 %", fx, dfx), ("Dryers, Table 220.54 (3 dryers: 100 %)", dry, dry),
            ("Ranges, Table 220.55 Column C (3 ranges: 14 kW)", 3 * APPL["range"][1], rng), ("Air conditioning, 100 %", c, c)]
    return rows, d1 + dfx + dry + rng + c


# ---------------------------------------------------------------------------------------------- conductor sizing tables (copper / aluminium, 75 C column of Table 310.16)
T31016 = [("8", 50, None), ("6", 65, 50), ("4", 85, 65), ("3", 100, 75), ("2", 115, 90), ("1", 130, 100), ("1/0", 150, 120), ("2/0", 175, 135), ("3/0", 200, 155),
          ("4/0", 230, 180), ("250 kcmil", 255, 205), ("300 kcmil", 285, 230), ("350 kcmil", 310, 250), ("400 kcmil", 335, 270), ("500 kcmil", 380, 310)]
T31012 = {100: ("4", "2"), 110: ("3", "1"), 125: ("2", "1/0"), 150: ("1", "2/0"), 175: ("1/0", "3/0"), 200: ("2/0", "4/0"), 225: ("3/0", "250 kcmil")}


def smallest(amps, al=False):
    for s, cu, a in T31016:
        amp = a if al else cu
        if amp and amp >= amps: return s, amp
    return None, None


def next_rating(a, ratings=(100, 110, 125, 150, 175, 200, 225, 250, 300, 350, 400)):
    return next(r for r in ratings if r >= a)


# ---------------------------------------------------------------------------------------------- lighting: lumen method
FIXT = {"R6": ("6 in. LED wafer downlight, 3000 K, dimmable", 900, 12), "R6W": ("6 in. LED wafer, wet-location rated (over a tub)", 900, 12),
        "C": ("LED flush ceiling fixture, damp rated", 1600, 20), "CL": ("LED closet fixture with motion sensor", 800, 10)}
MIRROR_LM, MIRROR_CREDIT = 1600, 0.5          # LED mirror light; half counted, since it faces the user rather than the floor
LLF = 0.80                                    # LED lumen depreciation x dirt: maintained light
CU_TAB = [(0, 0.95), (1, 0.88), (2, 0.79), (3, 0.71), (4, 0.64), (5, 0.58), (6, 0.52), (7, 0.47), (8, 0.43), (9, 0.39), (10, 0.36)]
TARGET = {"living": (15, 2.5, "R6"), "bed": (10, 2.5, "R6"), "kitchen": (20, 3.0, "R6"), "bath": (20, 2.5, "C"), "hall": (10, 0.0, "R6"), "stair": (10, 0.0, "R6"),
          "mech": (20, 3.0, "C"), "laundry": (30, 3.0, "R6"), "laundrymech": (30, 3.0, "C"), "closet": (10, 0.0, "CL")}
DEF_CEIL = {3: 7.0, 4: 7.33, 5: 7.42, 6: 7.75}
CAB = ("base", "dw", "sinkbase", "range", "fridge", "washer", "dryer")


def kind(r):
    return "laundrymech" if (r["kind"] == "mech" and "laundry" in r["name"].lower()) else r["kind"]


def ceil_ft(fl, r):
    s = r["ceil"]
    if not s: return DEF_CEIL[fl]
    f, i = s.replace('"', "").split("'-"); return int(f) + int(i) / 12


def cu(rcr):
    for (a, ua), (c_, uc) in zip(CU_TAB[:-1], CU_TAB[1:]):
        if rcr <= c_: return ua + (uc - ua) * (rcr - a) / (c_ - a)
    return CU_TAB[-1][1]


def skip(r):
    return r["name"].upper() == "CHASE"


def lit_rooms(fl):
    return [r for r in b.LV[fl]["rooms"] if not skip(r) and kind(r) in TARGET]


def geo(fl, r):
    P = unary_union([box(*q) for q in r["rects"]]); A = P.area
    E, wp, ft = TARGET[kind(r)]; h = max(1.0, ceil_ft(fl, r) - wp); rcr = 2.5 * h * P.length / A; u = cu(rcr)
    return dict(area=A, h=h, rcr=rcr, cu=u, E=E, ft=ft, need=E * A / (u * LLF))


def grid(z, n):
    """n or a few more points in an even grid over rectangle z, cells as square as possible."""
    x0, y0, x1, y1 = z; W, H = x1 - x0, y1 - y0; best = None
    for c in range(1, n + 1):
        r_ = math.ceil(n / c); asp = (W / c) / (H / r_); key = 0.6 * (c * r_ - n) + abs(math.log(asp))
        if best is None or key < best[0]: best = (key, c, r_)
    _k, c, r_ = best
    return [(x0 + W * (i + 0.5) / c, y0 + H * (j + 0.5) / r_) for j in range(r_) for i in range(c)]


def aisle(fl, r):
    """A kitchen's open floor: its rectangle less the cabinet and appliance strips along its walls."""
    x0, y0, x1, y1 = r["rects"][0]; fx = [f for f in b.LV[fl]["fx"] if f[0] in CAB and box(*f[1:5]).intersects(box(x0, y0, x1, y1))]
    z = [x0, y0, x1, y1]
    for side, ax_, lo in ((0, 0, True), (2, 0, False), (1, 1, True), (3, 1, False)):
        edge = z[side]; on = [f for f in fx if abs((f[1 + ax_] if lo else f[3 + ax_]) - edge) < 0.4]
        cover = sum((f[4 - ax_] - f[2 - ax_]) if ax_ == 0 else (f[3] - f[1]) for f in on); span = (y1 - y0) if ax_ == 0 else (x1 - x0)
        if on and cover / span >= 0.3:
            z[side] = max(f[3 + ax_] for f in on) if lo else min(f[1 + ax_] for f in on)
    return tuple(z)


def layout(fl, r):
    """Ceiling fixtures drawn in a room: list of (type, x, y), plus lumens credited from an LED mirror. The calc and the plans both use this."""
    g = geo(fl, r); k = kind(r); ft = g["ft"]; lm = FIXT[ft][1]; main = r["rects"][0]
    if k == "bath":
        tub = next((f for f in b.LV[fl]["fx"] if f[0] == "tub" and any(box(*f[1:5]).intersects(box(*q).buffer(-0.1)) for q in r["rects"])), None)
        z = list(main)
        if tub and box(*tub[1:5]).intersects(box(*main).buffer(-0.1)):
            along_y = (tub[3] - tub[1]) < (tub[4] - tub[2])             # long side runs in y: the tub sits against an x side
            if along_y:
                if abs(tub[1] - main[0]) < abs(main[2] - tub[3]): z[0] = tub[3]
                else: z[2] = tub[1]
            else:
                if abs(tub[2] - main[1]) < abs(main[3] - tub[4]): z[1] = tub[4]
                else: z[3] = tub[2]
        out = [("C", (z[0] + z[2]) / 2, (z[1] + z[3]) / 2)]; credit = MIRROR_LM * MIRROR_CREDIT
        while sum(FIXT[t][1] for t, _x, _y in out) + credit < g["need"] and tub:
            out.append(("R6W", (tub[1] + tub[3]) / 2, (tub[2] + tub[4]) / 2)); break
        return out, credit
    nmin = max(1, math.ceil(g["need"] / lm - 0.02))
    if k == "closet":
        return [("CL", (main[0] + main[2]) / 2, (main[1] + main[3]) / 2)], 0
    if k == "kitchen":
        return [(ft, x, y) for x, y in grid(aisle(fl, r), nmin)], 0
    if k in ("hall", "stair", "bed", "living") and len(r["rects"]) > 1:
        lim = 12 if k in ("hall", "stair") else 30
        big = [q for q in r["rects"] if (q[2] - q[0]) * (q[3] - q[1]) >= lim]; A = sum((q[2] - q[0]) * (q[3] - q[1]) for q in big); out = []
        for q in big:
            a = (q[2] - q[0]) * (q[3] - q[1])
            out += [(ft, x, y) for x, y in grid(q, max(1, round(nmin * a / A)))]
        while sum(1 for _ in out) * lm * g["cu"] * LLF / g["area"] < g["E"] * 0.97:      # rounding left it short: one more in the main part
            out += [(ft, x, y) for x, y in grid(big[0], sum(1 for o in out if box(*big[0]).contains(Point(o[1], o[2]))) + 1)][-1:]
            break
        return out, 0
    return [(ft, x, y) for x, y in grid(main, nmin)], 0


def calc(fl, r):
    g = geo(fl, r); items, credit = layout(fl, r)
    cnt = {}
    for t, _x, _y in items: cnt[t] = cnt.get(t, 0) + 1
    lm = sum(FIXT[t][1] for t, _x, _y in items) + credit
    g.update(items=items, cnt=cnt, credit=credit, lm=lm, ach=lm * g["cu"] * LLF / g["area"], w=sum(FIXT[t][2] for t, _x, _y in items) + (40 if credit else 0),
             desc=" + ".join(f"{n} {t}" for t, n in cnt.items()) + (" + mirror" if credit else ""))
    return g


# ---------------------------------------------------------------------------------------------- sheets
def _flat_block(bg, x, y, k):
    """One flat: both methods side by side, item by item, with the arithmetic written out."""
    f = FLATS[k]; A = AREA[k]; rows, tot = standard(k); items, g, dg, c, ot = optional(k)
    lt, sa, ld = 3 * A, 1500 * f["sa"], 1500; s3 = lt + sa + ld; d3 = min(s3, 3000) + 0.35 * max(0, s3 - 3000)
    fx = fixed_items(k); sfx = sum(v for _n, v in fx); dfx = 0.75 * sfx
    short = {"Dishwasher": "DW", "Microwave / hood": "MW/hood", "Water heater vent fan": "WH fan"}
    fxt = " + ".join((f"{short[n]} {v:,}" if n in short else (f"{f['baths']} fans {v:,}" if "fans" in n else f"{f['baths']} mirrors {v:,}")) for n, v in fx)
    bg.text(x, y, f"PANEL {k} · {f['name'].upper()} · {A:,} sf ({AREA_HOW[k]})", fontsize=6.4, fontweight="bold", color=INK, va="center"); y -= .17
    T = [["Item", "Rule and arithmetic", "Std. load", "Std. demand", "Optional"],
         ["General lighting and receptacles", f"3 VA x {A:,} sf (220.12; 220.82(B)(1))", f"{lt:,}", "", f"{lt:,}"],
         ["Kitchen small-appliance circuits", f"1,500 VA x {f['sa']} counter circuits (220.52(A); (B)(2))", f"{sa:,}", "", f"{sa:,}"],
         ["Laundry circuit", "1,500 VA x 1 (220.52(B); (B)(2))", f"{ld:,}", "", f"{ld:,}"],
         ["  Lines 1 to 3, Table 220.42", f"{s3:,}: first 3,000 at 100 % + {s3 - 3000:,} at 35 %", "", f"{d3:,.0f}", ""],
         ["Range (electric)", "Table 220.55 Col. C: one range up to 12 kW = 8 kW; optional: nameplate", f"{APPL['range'][1]:,}", "8,000", f"{APPL['range'][1]:,}"],
         ["Clothes dryer (electric)", f"220.54: nameplate {APPL['dryer'][1]:,}, not less than 5,000", f"{APPL['dryer'][1]:,}", f"{max(5000, APPL['dryer'][1]):,}", f"{APPL['dryer'][1]:,}"],
         ["Fixed appliances", fxt + f" = {sfx:,}; 75 % (220.53)", f"{sfx:,}", f"{dfx:,.0f}", f"{sfx:,}"],
         ["Refrigerator, own circuit", "standard: not counted (220.52(A) Exc.); optional: nameplate", "", "", f"{APPL['fridge'][1]:,}"],
         ["  Optional general load", f"{g:,.0f}: first 10,000 at 100 % + {max(0, g - 10000):,.0f} at 40 % (220.82(B))", "", "", f"{dg:,.0f}"],
         ["Cooling (larger than gas heat)", f"MCA {AC[k]['mca']:g} A x 240 + blower {AC[k]['blower']:g} A x 120, {AC[k]['ton']:g} ton (220.60; 220.82(C))", f"{ac_va(k):,.0f}", f"{max(ac_va(k), heat_va(k)):,.0f}", f"{c:,.0f}"],
         ["TOTAL", "VA / 240 V", "", f"{tot:,.0f} = {tot / V:,.0f} A", f"{ot:,.0f} = {ot / V:,.0f} A"]]
    y = table(bg, x, y, [1.6, 3.75, .55, .78, .78], T, fs=5.0, rh=.158) - .02
    bg.text(x, y - .08, f"Panel {k} needs {ot / V:,.0f} A by the optional method ({tot / V:,.0f} A standard): a 125 A panel and feeder, with room for students' appliances.",
            fontsize=5.1, color=INK, va="center", fontweight="bold"); return y - .3


def load_sheet(pdf):
    per, conn, tot, dem = service(); srows, stot = service_standard()
    sa = dem / V; cu_s, cu_a = smallest(sa); al_s, al_a = smallest(sa, True); rating = next_rating(sa)
    notes = [("What this sheet does", ["Sizes each flat's panel and feeder, and the", "building's service, by the NEC. Every value", "is worked out in the tables: area x rate,", "nameplate, then the code's demand factor."]),
             ("Inputs", ["Areas: measured to the outside faces of", "the walls on the plans (220.12).", "Appliances: electric range, electric dryer,", "dishwasher, over-range microwave, fridge,",
                         "2 or 3 bath fans and LED anti-fog mirrors.", "Gas furnace and gas water heater (only", "their fans are electric). Central air:", "1.5, 2 and 3 ton condensers.",
                         "Nameplates are typical: confirm when the", "equipment is bought, then rebuild."]),
             ("Result", [f"Each flat: 125 A panel and feeder.", f"Building: {dem:,.0f} VA = {sa:,.0f} A calculated.", f"Service conductors: {cu_s} Cu or {al_s} Al", "(Table 310.16, 75 C). See E-004.",
                         "Existing cable: size not readable in the", "photos; replace it (E-004)."])]
    fig, bg, _ = b.bsheet("E-002", "Electrical load calculations", 0, notes, sub="Rear building · all three flats")
    bg.text(0.5, 10.25, "ELECTRICAL LOAD CALCULATIONS · " + CODE + " · 120/240 V single phase", fontsize=9.5, fontweight="bold", color=INK, va="center")
    y = 9.98
    for k in ("A", "B", "C"):
        y = _flat_block(bg, 0.5, y, k)
    # building service, right column of the drawing area
    x = 8.15; yy = 10.0
    bg.text(x, yy, "BUILDING SERVICE · NEC 220.84 (multifamily, optional)", fontsize=6.6, fontweight="bold", color=INK, va="center"); yy -= 0.17
    for t in ("Allowed because the building has 3 units and each", "has electric cooking and air conditioning, 220.84(A)."):
        bg.text(x, yy, t, fontsize=5.0, color=GREY, va="center"); yy -= 0.13
    rows = [["Connected load per flat", "A", "B", "C"]]
    names = [n for n, _v in per["A"]]
    for i, n in enumerate(names):
        rows.append([n.replace("LED anti-fog mirrors", "Anti-fog mirrors"), *[f"{per[k][i][1]:,.0f}" for k in FLATS]])
    rows.append(["Connected load, VA", *[f"{conn[k]:,.0f}" for k in FLATS]])
    yy = table(bg, x, yy - 0.04, [1.75, 0.38, 0.38, 0.38], rows, fs=4.8, rh=0.135) - 0.05
    for t, bold in ((f"Sum of three flats: {tot:,.0f} VA", False), (f"Table 220.84(B), 3 units: 45 % = {dem:,.0f} VA", False),
                    (f"Service load: {dem:,.0f} VA / 240 V = {sa:,.0f} A", True), ("No house loads: everything is on the flats' panels.", False)):
        bg.text(x, yy, t, fontsize=5.4, color=INK, va="center", fontweight="bold" if bold else "normal"); yy -= 0.15
    yy -= 0.05
    bg.text(x, yy, "For comparison: standard method, whole building", fontsize=6.0, fontweight="bold", color=INK, va="center"); yy -= 0.17
    r2 = [["Item", "Load VA", "Demand VA"]] + [[n, f"{v:,.0f}", f"{d:,.0f}"] for n, v, d in srows] + [["Total", "", f"{stot:,.0f} = {stot / V:,.0f} A"]]
    yy = table(bg, x, yy, [1.85, 0.48, 0.7], r2, fs=4.8, rh=0.135) - 0.08
    bg.text(x, yy, "The NEC lets the optional method be used here; it is the", fontsize=5.0, color=GREY, va="center"); yy -= 0.13
    bg.text(x, yy, "one the utility and inspector expect for apartments.", fontsize=5.0, color=GREY, va="center"); yy -= 0.2
    bg.text(x, yy, "CONDUCTORS", fontsize=6.6, fontweight="bold", color=INK, va="center"); yy -= 0.17
    cond = [["Run", "Carries", "Copper", "Aluminium"],
            ["Service: weatherhead to meters", f"{sa:,.0f} A", f"{cu_s} ({cu_a} A)", f"{al_s} ({al_a} A)"],
            ["Feeder to each flat's panel", "125 A", f"{T31012[125][0]} (310.12)", f"{T31012[125][1]} (310.12)"],
            ["Equipment ground in each feeder", "125 A breaker", "6 (250.122)", "4 (250.122)"],
            ["Grounding electrode conductor", "to the rods", "6 (250.66(A))", "-"]]
    yy = table(bg, x, yy, [1.2, 0.55, 0.62, 0.78], cond, fs=4.8, rh=0.135) - 0.06
    for t in ("Service conductors: Table 310.16, 75 C. The 83 % rule of", "310.12 is for one dwelling's own service or feeder, so it", "applies to the three feeders but not to the building service.",
              "Three 125 A meter-main breakers may add to more than the", "service conductors carry: allowed by 230.90(A) Exc. 3 because", "the calculated load is within the conductors' ampacity."):
        bg.text(x, yy, t, fontsize=5.0, color=GREY, va="center"); yy -= 0.13
    b.save(fig, "E-002", pdf)


def light_sheet(pdf):
    """Every room: the fixtures counted are the ones drawn on the plans (both come from layout())."""
    notes = [("Method", ["Lumen method, average maintained", "illuminance on the work plane:", "  E = N x lumens x CU x LLF / area",
                         "so  N = E x area / (lumens x CU x LLF).", "RCR = 2.5 x cavity height x perimeter /", "  area. CU from the table below.",
                         f"LLF = {LLF:.2f} (LED depreciation x dirt).", "Cavity height = ceiling minus work plane."]),
             ("Targets", ["Residential values from the IES Lighting", "Handbook ranges: living 15 fc, kitchen 20 fc", "general + counters by under-cabinet LEDs,", "bath 20 fc + the LED mirror at the vanity,",
                          "bedroom 10 fc + a desk lamp, hall and", "stair 10 fc at the floor, laundry 30 fc,", "mechanical 20 fc, closet 10 fc."]),
             ("Confirm", ["CU values are typical for a wide-beam LED", "downlight in a white room (80/50/20 %).", "Check against the chosen fixture's", "photometric file before ordering."])]
    fig, bg, _ = b.bsheet("E-003", "Lighting calculations", 0, notes, sub="Rear building · all rooms")
    bg.text(0.5, 10.25, "LIGHTING CALCULATIONS · lumen method, every room", fontsize=9.5, fontweight="bold", color=INK, va="center")
    head = ["Room", "Area sf", "Ceiling", "Cavity", "RCR", "CU", "Target fc", "lm needed", "Fixtures drawn", "lm drawn", "Gives fc", "W", "W/sf"]
    wid = [1.55, 0.42, 0.42, 0.42, 0.33, 0.33, 0.46, 0.52, 1.05, 0.5, 0.48, 0.3, 0.36]
    rows = [head]
    for fl in (3, 4, 5, 6):
        for r in lit_rooms(fl):
            c = calc(fl, r); ok = c["ach"] >= c["E"] * 0.97
            rows.append([f"{r['no']} {r['name'].split(' (')[0][:22]}", f"{c['area']:.0f}", b.ftin(round(ceil_ft(fl, r) * 12) / 12), f"{c['h']:.1f} ft", f"{c['rcr']:.1f}", f"{c['cu']:.2f}",
                         f"{c['E']}", f"{c['need']:,.0f}", c["desc"], f"{c['lm']:,.0f}", f"{c['ach']:.0f}" + ("" if ok else " !"), f"{c['w']}", f"{c['w'] / c['area']:.2f}"])
    half = (len(rows) + 1) // 2
    y = table(bg, 0.5, 9.95, wid, rows[:half], fs=4.6, rh=0.16)
    if len(rows) > half:
        table(bg, 0.5, y - 0.15, wid, [head] + rows[half:], fs=4.6, rh=0.16)
    # fixture and CU tables in the free strip
    x = 10.6; yy = 9.95
    bg.text(x, yy, "FIXTURES", fontsize=6.8, fontweight="bold", color=INK, va="center"); yy -= 0.2
    yy = table(bg, x, yy, [0.32, 1.65, 0.33, 0.25], [["Type", "Description", "lm", "W"]] + [[k, d, f"{lm}", f"{w}"] for k, (d, lm, w) in FIXT.items()], fs=4.6, rh=0.15) - 0.15
    bg.text(x, yy, "COEFFICIENT OF UTILISATION", fontsize=6.8, fontweight="bold", color=INK, va="center"); yy -= 0.2
    yy = table(bg, x, yy, [0.5, 0.5], [["RCR", "CU"]] + [[f"{a}", f"{u:.2f}"] for a, u in CU_TAB], fs=4.6, rh=0.14) - 0.15
    for t in ("Baths: the LED mirror (about 1,600 lm) is counted", "at half, since it faces the user. Not counted:", "under-cabinet LEDs (counters), range-hood light,", "exterior lights: they add task light where needed.",
              "", "Switching: dimmers in living rooms and", "bedrooms; closet fixtures switch on by motion.", "! = below target: none should appear."):
        bg.text(x, yy, t, fontsize=5.0, color=GREY, va="center"); yy -= 0.13
    yy -= .15; xw = 7.85
    bg.text(xw, 9.95, "WORKED EXAMPLES", fontsize=6.8, fontweight="bold", color=INK, va="center"); y3 = 9.72
    for fl, no in ((3, "101"), (6, "403")):
        r = next(r_ for r_ in b.LV[fl]["rooms"] if r_["no"] == no); c = calc(fl, r); P = unary_union([box(*q_) for q_ in r["rects"]])
        E, wp, ft = TARGET[kind(r)]
        lines = [f"{no} {r['name'].split(' (')[0]}, target {E} fc", f"Area {c['area']:.0f} sf, perimeter {P.length:.1f} ft", f"Cavity = {ceil_ft(fl, r):.2f} - {wp} = {c['h']:.2f} ft",
                 f"RCR = 2.5 x {c['h']:.2f} x {P.length:.1f} / {c['area']:.0f} = {c['rcr']:.1f}", f"CU from the table: {c['cu']:.2f}",
                 f"Lumens needed = {E} x {c['area']:.0f} / ({c['cu']:.2f} x {LLF:.2f})", f"  = {c['need']:,.0f} lm"]
        if c["credit"]:
            lines += [f"Drawn: {c['desc']}", f"  = {c['lm'] - c['credit']:,.0f} + mirror {c['credit']:,.0f} (half of 1,600)", f"  = {c['lm']:,.0f} lm"]
        else:
            lines += [f"Drawn: {c['desc']} x {FIXT[ft][1]} lm = {c['lm']:,.0f} lm"]
        lines += [f"Result = {c['lm']:,.0f} x {c['cu']:.2f} x {LLF:.2f} / {c['area']:.0f}", f"  = {c['ach']:.1f} fc (target {E}): OK"]
        for ln in lines:
            bg.text(xw, y3, ln, fontsize=5.0, color=INK, va="center"); y3 -= .13
        y3 -= .15
    b.save(fig, "E-003", pdf)


if __name__ == "__main__":
    for k in FLATS:
        rows, tot = standard(k); items, g, dg, c, ot = optional(k)
        print(k, FLATS[k]["name"], "area", AREA[k], "|", AREA_HOW[k], "| standard", round(tot), round(tot / V), "A | optional", round(ot), round(ot / V), "A")
    per, conn, tot, dem = service(); srows, stot = service_standard()
    print("220.84 connected", {k: round(v) for k, v in conn.items()}, "total", round(tot), "x45% =", round(dem), "VA =", round(dem / V), "A")
    print("standard building", round(stot), round(stot / V), "A")
    print("service conductors:", smallest(dem / V), smallest(dem / V, True))
    for fl in (3, 4, 5, 6):
        for r in lit_rooms(fl):
            c = calc(fl, r); print(f"  L{fl} {r['no']} {r['name'][:20]:20s} A {c['area']:5.0f} RCR {c['rcr']:4.1f} CU {c['cu']:.2f} need {c['need']:5.0f} drawn {c['desc']:18s} {c['ach']:4.0f} fc of {c['E']}")
