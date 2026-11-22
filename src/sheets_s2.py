"""Structural framing sheets S-201 .. S-204 and S-301 (Rev E).

Geometry (where every truss, wall and opening is, spans and lengths) is computed from model.py.
Member sizes are PRELIMINARY assumptions for the WV structural engineer and the truss supplier.
"""
import math

import numpy as np

from common import *  # noqa: F401,F403
import model as m
from plans import *  # noqa: F401,F403

TR = "#7a5c2e"        # wood trusses
TR2 = "#b08a4f"       # truss tails / secondary
STEEL = BLUE
SVC = "#0e8f9c"       # service zone, pipes
SOIL = "#efe9e1"
CONC_F = "#b9bec4"
WOODF = "#e9dfc9"
INSUL = "#f6dfe4"

IN = m.IN
CW, TW = math.cos(WEST_LEAN), math.tan(WEST_LEAN)
SKEW = math.atan(abs(REAR_SLOPE))            # rear wall skew in plan (radians)
CR = math.cos(SKEW)
S16, S12, S24 = 16 * IN, 1.0, 2.0
BRG = 5.5 * IN                                # truss bearing on the PT 2x6 sill
LEDGE = 6 * IN                                # truss ledge on the concrete walls (S-101 / S-102)
RIM = 1.5 * IN
YS_P = m.PORCH[1]                             # outer edge of the porch cantilever
YN_A = m.Y_GR_I + BRG                         # north end of the Unit A trusses (on the ledge)
EL_TOP_A = m.EL_A - 0.75 * IN                 # top of the Unit A trusses
EL_BRG_A = EL_TOP_A - m.TRUSS_A               # underside of the Unit A trusses (top of the nailer on B1 / sill on the ledges)
NAILER = EL_BRG_A - m.EL_B1_TOP               # 1 1/2 in. wood nailer on B1 (model)
EL_TOC_A = EL_BRG_A - 1.5 * IN                # top of concrete at the truss ledges, under a 1 1/2 in. PT sill
EL_TOP_B = m.EL_B - 0.75 * IN
EL_BRG_B = EL_TOP_B - m.TRUSS_B               # underside of the Unit B trusses = top of Unit A wall plates
LAND_Y = m.SHAFT_U[2] + 3.25                  # north edge of the stair landing at each floor
WALL_H_B = m.EL_PLATE - m.EL_B                # framed wall height, Unit B
WALL_H_A = EL_BRG_B - m.EL_A


def y_on(xfun, x):
    """Y at which a west-wall line xfun(y) reaches plan station x."""
    return (x - xfun(0.0)) / TW


def span_cc(x):
    """Unit B floor / roof: distance between the centres of the front and rear wall plates at station x."""
    return m.yr_o(x) - m.YF - m.EXT / 2 - m.EXT / 2 / CR


def depth_oo(x):
    """Building depth at station x, outside face of framing to outside face of framing."""
    return m.yr_o(x) - m.YF


def grid(x0, step, lo, hi):
    n = math.ceil((lo - x0) / step - 1e-9)
    xs = []
    x = x0 + n * step
    while x <= hi + 1e-9:
        xs.append(x)
        x += step
    return xs


def ftin8(v):
    """Feet-inches to the nearest 1/8 in. (truss schedules)."""
    e = round(abs(v) * 96)
    f, r = divmod(e, 96)
    i, k = divmod(r, 8)
    frac = {0: "", 1: " 1/8", 2: " 1/4", 3: " 3/8", 4: " 1/2", 5: " 5/8", 6: " 3/4", 7: " 7/8"}[k]
    return f"{f}'-{i}{frac}\""


# ----------------------------------------------------------------------------
# drafting helpers local to these sheets
# ----------------------------------------------------------------------------
PV = ((0.5, 51.0), (0.0, 46.0))               # plan view used on S-201 .. S-203
PLAN_L, PLAN_B = 0.5, 0.62
STRIP_X = PLAN_L + (PV[0][1] - PV[0][0]) / FPI + 0.12
STRIP_W = SHEET_W - MARGIN - TB_W - 0.15 - STRIP_X


def sheet(number, title, scale_txt, notes):
    """new_sheet with a check that the title-block notes stay above the PRELIMINARY box."""
    h = sum(0.31 + sum(0.148 * (ln.count("\n") + 1) + 0.035 for ln in lines) for _, lines in notes)
    if h > 5.72:
        print(f"WARNING {number}: title-block notes are {h:.2f} in. tall (limit 5.72)")
    fig, bg = new_sheet(number, title, scale_txt, notes)
    return fig, bg


def plan_view(fig, bg, title, sub, view=PV, left=PLAN_L, bottom=PLAN_B, arrow=(47.6, 42.3), bar=(33.0, 44.4)):
    ax = plan_axes(fig, left, bottom, view[0], view[1], FPI)
    top = bottom + (view[1][1] - view[1][0]) / FPI
    bg.text(left, top + 0.42, title.upper(), fontsize=10.5, fontweight="bold", color=INK, va="center")
    bg.text(left, top + 0.2, sub, fontsize=6.4, color=GREY, va="center")
    if arrow:
        north_arrow(ax, arrow[0], arrow[1], 1.6, 6.5)
    if bar:
        scale_bar(ax, bar[0], bar[1], 12, 4, 0.38, size=5.0)
    return ax


def lead(ax, p, t, s, size=4.8, color=INK, ha="left", va="center", dot=True, weight="normal", z=11):
    line(ax, [p, t], lw=0.3, color=color, z=z - 1)
    if dot:
        r = 0.022 * getattr(ax, "fpi", FPI)
        ax.add_patch(plt.Circle(p, r, fc=color, ec="none", zorder=z))
    d = 0.03 * getattr(ax, "fpi", FPI)
    dx = d if ha == "left" else (-d if ha == "right" else 0)
    txt(ax, t[0] + dx, t[1], s, size=size, color=color, ha=ha, va=va, box=True, z=z, weight=weight)


def dimb(ax, p0, p1, off, label=None, size=5.0, color=INK, ext=True, side=1, box=True):
    """Dimension with a white box behind the text (for strings that cross framing lines)."""
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0)
    if not box:
        return dim(ax, p0, p1, off, label, size=size, color=color, ext=ext, side=side)
    dim(ax, p0, p1, off, "", size=size, color=color, ext=ext, side=side)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -uy, ux
    toff = 0.085 * getattr(ax, "fpi", FPI) * side
    ang = math.degrees(math.atan2(uy, ux))
    if ang > 90 or ang <= -90:
        ang += 180
    txt(ax, (x0 + x1) / 2 + nx * (off + toff), (y0 + y1) / 2 + ny * (off + toff), label if label is not None else ftin(L),
        size=size, color=color, rot=ang, box=True, z=12)


def mark(ax, x, y, s, color=TR, size=4.8, z=13):
    """Member mark in a lozenge."""
    w = 0.03 * len(s) * getattr(ax, "fpi", FPI) * size / 4.8 + 0.06 * getattr(ax, "fpi", FPI)
    h = 0.075 * getattr(ax, "fpi", FPI) * size / 4.8
    poly(ax, [(x - w, y), (x - w + h, y + h), (x + w - h, y + h), (x + w, y), (x + w - h, y - h), (x - w + h, y - h)],
         fc=PAPER, ec=color, lw=0.6, z=z)
    txt(ax, x, y, s, size=size, color=color, weight="bold", z=z + 1)


def el_tag(ax, x, y, s, size=5.0, ha="left", color=INK, length=None):
    """Level marker for sections: a short line with a triangle and the elevation."""
    f = getattr(ax, "fpi", 4.0)
    L = (0.5 * f) if length is None else length
    sgn = 1 if ha == "left" else -1
    line(ax, [(x, y), (x + sgn * L, y)], lw=0.4, color=color, z=12)
    t = 0.06 * f
    poly(ax, [(x + sgn * t, y), (x + sgn * 2.4 * t, y + 1.2 * t), (x + sgn * 3.8 * t, y)], fc=color, ec=color, lw=0.3, z=12)
    txt(ax, x + sgn * (L + 0.04 * f), y, s, size=size, color=color, ha=ha, z=12)


def strip_head(bg, y, s, x=None):
    x = STRIP_X if x is None else x
    bg.text(x, y, s.upper(), fontsize=7.0, fontweight="bold", color=INK, va="top")
    return y - 0.17


def strip_lines(bg, y, lines, fs=5.7, x=None, color=INK, lh=0.142):
    x = STRIP_X if x is None else x
    for ln in lines:
        bg.text(x, y, ln, fontsize=fs, color=color, va="top", linespacing=1.22)
        y -= lh * (ln.count("\n") + 1) + 0.02
    return y


def truss_band(ax, x0, x1, z0, z1, color=TR, panel=None, lw=0.35, z=6, fc=WOODF, chord=1.5 * IN):
    """Open-web truss seen from the side: two chords and a zig-zag of webs between x0 and x1."""
    rect(ax, x0, z0, x1, z1, fc=PAPER, ec="none", z=z - 0.2)
    rect(ax, x0, z0, x1, z0 + chord, fc=fc, ec=color, lw=lw, z=z)
    rect(ax, x0, z1 - chord, x1, z1, fc=fc, ec=color, lw=lw, z=z)
    d = z1 - z0 - 2 * chord
    panel = panel or d * 1.15
    n = max(2, int(round((x1 - x0) / panel)))
    p = (x1 - x0) / n
    pts = []
    for i in range(n + 1):
        pts.append((x0 + i * p, z0 + chord if i % 2 == 0 else z1 - chord))
    line(ax, pts, lw=lw + 0.25, color=color, z=z)
    for xx in (x0, x1):
        line(ax, [(xx, z0), (xx, z1)], lw=lw + 0.2, color=color, z=z)


# ----------------------------------------------------------------------------
# truss lay-outs (all from the model)
# ----------------------------------------------------------------------------
GRID_A = m.STACK_1[0] + 8 * IN        # Unit A 16 in. grid: stack 1 sits in the middle of a bay
GRID_B = m.STACK_2[0] + 8 * IN        # Unit B 16 in. grid (and the stair bay on both floors): stacks 2 and 3 clear
GRID_B12 = m.STACK_1[0] + 6 * IN      # Unit B 12 in. grid at the long spans: stack 1 in the middle of a bay
ST_BAY = [x for x in grid(GRID_B, S16, m.SHAFT_X0 + 0.3, m.XEI - 0.2)]      # trusses in the stair bay, both floors
X_RIM_E = m.XE - 0.25                 # rim / end truss on the east wall
X_LOBBY = (m.GAR_X1 + m.SHAFT_X0) / 2  # rim truss on the lobby wall (garage level)
X_GT = m.X_ST + 1.75 * IN             # Unit B girder truss beside the stair opening (over the stair wall)
Y_HDR_S = LAND_Y - 1.75 * IN          # header at the landing edge
Y_HDR_N = m.SHAFT_U[3] + m.RATED / 2  # header / rim over the stair north wall
X_PE = m.PORCH[0] + 1.0 * IN          # porch-end truss


def wh_pair(xs):
    """The two trusses either side of the water heater centre (to be doubled)."""
    x = m.WH_UNIT[0]
    return max(v for v in xs if v <= x), min(v for v in xs if v > x)


def draw_wh(ax, pair, y0, y1, label_at, mark_):
    for x in pair:
        line(ax, [(x, y0), (x, y1)], lw=1.7, color=TR, z=7.6)
    ax.add_patch(plt.Circle(m.WH_UNIT, m.WH_PAN_R, fc=PAPER, ec=ACCENT, lw=0.9, zorder=9.2))
    txt(ax, m.WH_UNIT[0], m.WH_UNIT[1], "WH", size=4.0, color=ACCENT, weight="bold", z=12)
    lead(ax, (m.WH_UNIT[0] + m.WH_PAN_R * 0.7, m.WH_UNIT[1] - m.WH_PAN_R * 0.7), label_at,
         f"80 gal WATER HEATER above (about 900 lb full):\nDOUBLE the two {mark_} trusses under it (heavy lines)\n+ solid blocking at 16 in. under the pan", size=4.3, color=ACCENT, dot=False)


def trusses_a():
    """Unit A floor trusses over the garage. Returns list of dict(x, y0, y1, mark)."""
    out = []
    y_front = m.YF + RIM
    for x in grid(GRID_A, S16, m.xw_gi(m.YF) + 0.4, m.GAR_X1 - 0.15):
        if x > m.PORCH[0]:
            out.append(dict(x=x, y0=YS_P + RIM, y1=YN_A, mark="A1"))
        elif x > m.xw_gi(m.Y_GR_I) + 0.1:
            out.append(dict(x=x, y0=y_front, y1=YN_A, mark="A2"))
        else:
            out.append(dict(x=x, y0=y_front, y1=y_on(m.xw_gi, x + BRG / 2 / CW), mark="A3"))
    out.append(dict(x=X_PE, y0=YS_P + RIM, y1=YN_A, mark="A1"))
    for x in ST_BAY:
        out.append(dict(x=x, y0=YS_P + RIM, y1=Y_HDR_S - 1.75 * IN, mark="A4"))
        out.append(dict(x=x, y0=m.UTIL[2] - 4 * IN, y1=YN_A, mark="A5"))
    return sorted(out, key=lambda t: -t["x"])


X28 = m.XE - (28.0 + m.EXT / 2 + m.EXT / 2 / CR + m.YF - m.Y_GR_O) / abs(REAR_SLOPE)   # station where span_cc = 28 ft
X12_START = max(x for x in grid(GRID_B12, S12, 6.0, 30.0) if x <= X28 + 0.5)             # first truss of the 12 in. zone


def trusses_b():
    """Unit B floor trusses. Returns list of dict(x, y0, y1, mark, oc)."""
    out = []
    y_front = m.YF + RIM
    x_full = m.IN_U[3][0]                      # west of this the truss runs into the leaning west wall

    def north(x):
        return m.yr_o(x) - RIM / CR

    for x in ST_BAY:
        out.append(dict(x=x, y0=YS_P + RIM, y1=Y_HDR_S - 1.75 * IN, mark="B6", oc=16))
        out.append(dict(x=x, y0=Y_HDR_N + 1.75 * IN, y1=north(x), mark="B5", oc=16))
    for x in grid(GRID_B, S16, X12_START + 0.9, m.X_ST - 0.6):
        out.append(dict(x=x, y0=YS_P + RIM, y1=north(x), mark="B1", oc=16))
    for x in grid(GRID_B12, S12, m.xw_i(m.YFI) + 0.2, X12_START + 0.01):
        if x > m.PORCH[0]:
            out.append(dict(x=x, y0=YS_P + RIM, y1=north(x), mark="B2", oc=12))
        elif x > x_full:
            out.append(dict(x=x, y0=y_front, y1=north(x), mark="B3", oc=12))
        else:
            yw = y_on(m.xw_o, x - m.EXT / 2 / CW)
            if yw - y_front > 4.0:
                out.append(dict(x=x, y0=y_front, y1=min(yw, north(x)), mark="B4", oc=12))
    out.append(dict(x=X_PE, y0=YS_P + RIM, y1=north(X_PE), mark="B2", oc=12))
    return sorted(out, key=lambda t: -t["x"])


ROOF_X = [m.XE - S24 * k for k in range(1, 40) if m.XE - S24 * k > m.xw_o(m.YF) + 0.3]
EAVE_F = m.YF - 4.0                    # front eave line (over the porch)
RAKE = 8 * IN
OH_REAR = 1.0                          # rear overhang, measured square to the wall


def eave_r(x):
    return m.yr_o(x) + OH_REAR / CR


def rake_w(y):
    return m.xw_o(y) - RAKE / CW


def _x_of_rear(fy, xfun):
    """Intersection of a rear line fy(x) with a west line xfun(y)."""
    y = 35.0
    for _ in range(60):
        y = fy(xfun(y))
    return (xfun(y), y)


ROOF = [(rake_w(EAVE_F), EAVE_F), (m.XE + RAKE, EAVE_F), (m.XE + RAKE, eave_r(m.XE + RAKE)), _x_of_rear(eave_r, rake_w)]
RIDGE_W = _x_of_rear(m.ridge_y, m.xw_o)                      # ridge over the west wall face
RIDGE_WR = _x_of_rear(m.ridge_y, rake_w)                     # ridge at the west rake edge


def corner_angles():
    """Interior plan angles of the four outside corners (deg): SW, SE, NE, NW."""
    P = m.OUT_U
    res = []
    for i in range(4):
        a, b, c = P[i - 1], P[i], P[(i + 1) % 4]
        v1 = (a[0] - b[0], a[1] - b[1])
        v2 = (c[0] - b[0], c[1] - b[1])
        cosang = (v1[0] * v2[0] + v1[1] * v2[1]) / (math.hypot(*v1) * math.hypot(*v2))
        res.append(math.degrees(math.acos(cosang)))
    return res


PRELIM = ("Preliminary", [
    "Sizes are assumptions, not a design. A WV",
    "structural engineer designs and seals the",
    "framing; the truss supplier designs and",
    "seals every truss. Geometry is from the",
    "building model: verify in the field.",
])


# ----------------------------------------------------------------------------
# S-201  Unit A floor framing
# ----------------------------------------------------------------------------
def truss_zone_key(fig, bg, left, bottom, depth_in=20, title="TRUSS SPACE OVER THE GARAGE: WHAT GOES WHERE"):
    f = 1.25
    d = depth_in * IN
    ax = plan_axes(fig, left, bottom, (-0.12, STRIP_W * f - 0.12), (-0.5, d + 0.45), f)
    L = 2.05
    rect(ax, 0, d, L, d + 0.75 * IN, fc=WOODF, ec=INK, lw=0.5, z=6)                   # subfloor
    rect(ax, 0, -0.625 * IN, L, 0, fc="#dfe2e6", ec=INK, lw=0.5, z=6)                 # 5/8 X ceiling
    rect(ax, 0, 1.5 * IN, L, 11.0 * IN, fc=INSUL, ec="none", z=3, hatch="////")
    rect(ax, 0, 11.0 * IN, L, d - 1.5 * IN, fc="#e4f3f5", ec="none", z=3)
    truss_band(ax, 0, L, 0, d, panel=0.52, fc=WOODF, z=7)
    line(ax, [(0, 11.0 * IN), (L, 11.0 * IN)], lw=0.5, color=SVC, ls=(0, (4, 2)), z=8)
    for x, r, c in ((0.44, 0.04, SVC), (0.58, 0.04, ACCENT), (1.03, 0.14, GREY), (1.54, 0.075, INK)):
        ax.add_patch(plt.Circle((x, 15.0 * IN), r, fc=PAPER, ec=c, lw=0.8, zorder=9))
    x = L + 0.1
    for y, s, c in ((d + 0.03, "3/4 in. T&G subfloor, glued + nailed", INK),
                    (14.6 * IN, "SERVICE ZONE, top 7 1/2 in.:\nPEX, drains, refrigerant lines,\nfeeders. Warm side of the R-30", SVC),
                    (6.0 * IN, "R-30 batts on the ceiling, 9 1/2 in.\nNo water pipe in or below them", ACCENT),
                    (-0.03, "5/8 in. Type X ceiling (R302.6)", INK)):
        txt(ax, x, y, s, size=4.5, color=c, ha="left")
    txt(ax, 0.0, d + 0.3, f"{depth_in} in. TRUSS, SIDE VIEW", size=4.6, ha="left", weight="bold")
    bg.text(left, bottom + (d + 0.95) / f + 0.06, title, fontsize=6.4, fontweight="bold", va="bottom")
    return ax


def sheet_s201(pdf):
    T = trusses_a()
    a1 = [t for t in T if t["mark"] == "A1"]
    a2 = [t for t in T if t["mark"] == "A2"]
    a3 = [t for t in T if t["mark"] == "A3"]
    a4 = [t for t in T if t["mark"] == "A4"]
    a5 = [t for t in T if t["mark"] == "A5"]
    span_a = (m.Y_GR_I + BRG / 2) - m.B1_Y
    cant = m.B1_Y - YS_P
    notes = [
        ("Unit A floor framing", [
            "Only the floor over the garage is framed.",
            "North of the garage rear wall Unit A is a",
            "slab on grade at the same level (S-103).",
            "20 in. open-web trusses at 16 in. o.c. run",
            f"north-south, bear at EL {EL_BRG_A:.2f} on the nailer",
            "of steel beam B1 and on the sill of a 6 in.",
            "ledge on the concrete rear wall, and run",
            "4'-0\" past the front wall as the porch.",
        ]),
        ("Deck, rims, blocking", [
            "3/4 in. T&G subfloor, glued and nailed.",
            "Rim board or ladder truss on every wall.",
            "2x4 flat blocking at 24 in. under each",
            "partition that runs along the trusses.",
            "Solid blocking over B1 and at the ledge.",
            "Never cut or notch a chord or web.",
        ]),
        ("Sequence", [
            "This floor props the tops of the three",
            "retaining walls: frame, sheath and anchor",
            "it before the walls are backfilled.",
        ]),
        PRELIM,
    ]
    fig, bg = sheet("S-201", "Unit A floor framing", "3/16\" = 1'-0\"", notes)
    ax = plan_view(fig, bg, "Unit A floor framing plan",
                   f"Top of subfloor EL {m.EL_A:.1f} · truss bearing EL {EL_BRG_A:.2f} · top of steel and ledges EL {m.EL_B1_TOP:.2f} · garage walls below grey · trusses brown · steel blue · preliminary")
    lower_plan(ax, "bg", cars=False)
    # Unit A outline above, slab-on-grade part
    poly(ax, m.SOG, fc="#f6f1e7", ec=INK, lw=0.6, z=5.5, hatch="..")
    line(ax, m.OUT_U + [m.OUT_U[0]], lw=0.6, color=GREY, ls=(0, (6, 2)), z=6)
    txt(ax, 21.0, 33.3, "SLAB ON GRADE, SEE S-103", size=6.0, weight="bold", box=True, z=12)
    txt(ax, 21.0, 32.3, f"top of slab EL {m.EL_SLAB_A:.1f} = top of subfloor · no framing here", size=4.8, box=True, z=12)
    # service zone band
    by0, by1 = m.Y_GR_I - 4.5, m.Y_GR_I - 1.5
    band = [(m.xw_gi(by0) + 0.15, by0), (m.XE_GI, by0), (m.XE_GI, by1), (m.xw_gi(by1) + 0.15, by1)]
    poly(ax, band, fc="#e4f3f5", ec=SVC, lw=0.5, z=5.6, ls=(0, (4, 2)))
    rect(ax, m.PORCH[0], YS_P, m.PORCH[2], m.YF, fc="#fbf8f1", ec="none", z=2.5)
    for t in T:
        line(ax, [(t["x"], t["y0"]), (t["x"], t["y1"])], lw=0.55, color=TR, z=7)
    draw_wh(ax, wh_pair([t["x"] for t in a1]), YS_P + RIM, YN_A, (26.6, 22.9), "FT-A1")
    aw = m.EXT / 2 / CW
    line(ax, [(m.xw_o(m.YF) + aw, m.YF), (m.xw_o(m.Y_GR_O) + aw, m.Y_GR_O)], lw=1.3, color=TR, z=7.5)          # west rim on the leaning wall
    line(ax, [(X_RIM_E, YS_P), (X_RIM_E, m.Y_GR_O)], lw=1.3, color=TR, z=7.5)                                   # east rim / end truss
    line(ax, [(m.xw_o(m.YF), m.YF + RIM / 2), (m.PORCH[0], m.YF + RIM / 2)], lw=1.3, color=TR, z=7.5)           # front rim on the return pier
    line(ax, [(m.PORCH[0], YS_P + RIM / 2), (m.XE, YS_P + RIM / 2)], lw=1.5, color=TR, z=7.5)                   # porch rim
    line(ax, [(X_LOBBY, m.YF), (X_LOBBY, m.Y_GR_I)], lw=1.3, color=TR, z=7.5)                                   # rim on the lobby wall
    line(ax, [(m.xw_gi(YN_A), YN_A), (m.XE_GI, YN_A)], lw=0.9, color=TR, z=7.5)                                 # ribbon at the ledge
    line(ax, [(X_LOBBY, Y_HDR_S), (m.XEI, Y_HDR_S)], lw=2.0, color=TR, z=8)                                     # landing header
    line(ax, [(X_LOBBY, Y_HDR_N), (m.XEI, Y_HDR_N)], lw=1.3, color=TR, z=8)                                     # rim on the stair / utility wall
    rect(ax, m.SHAFT_U[0], LAND_Y, m.SHAFT_U[1], m.SHAFT_U[3], fc=PAPER, ec=INK, lw=0.7, z=8.2, hatch="xx")
    xs_ = (m.SHAFT_U[0] + m.SHAFT_U[1]) / 2
    txt(ax, xs_, 19.6, "STAIR\nOPENING", size=5.0, weight="bold", box=True, z=12)
    txt(ax, xs_, 17.9, f"{ftin(m.SHAFT_U[1] - m.SHAFT_U[0])} x {ftin(m.SHAFT_U[3] - LAND_Y)}", size=4.6, box=True, z=12)
    txt(ax, xs_, 12.2, "LANDING", size=4.4, box=True, z=12)
    line(ax, [(m.COL_X[0] - 0.4, m.B1_Y), (m.COL_X[2] + 0.3, m.B1_Y)], lw=3.2, color=STEEL, z=9)
    for cx in m.COL_X:
        rect(ax, cx - 0.3, m.B1_Y - 0.3, cx + 0.3, m.B1_Y + 0.3, fc=PAPER, ec=STEEL, lw=1.2, z=10)
    for i, (cx, cy) in enumerate((m.CHASE_1, m.CHASE_2)):
        rect(ax, cx - 0.67, m.Y_GR_I - 1.33, cx + 0.67, m.Y_GR_I, fc=PAPER, ec=ACCENT, lw=0.9, z=9)
        txt(ax, cx + 0.3, m.Y_GR_I - 0.95, f"C{i + 1}", size=4.0, color=ACCENT, weight="bold", z=12)
    for (sx, sy), (cx, cy) in ((m.STACK_1, m.CHASE_1), (m.STACK_3, m.CHASE_3)):
        line(ax, [(sx, sy), (cx, cy)], lw=1.4, color=SVC, z=9.5)
        ax.add_patch(plt.Circle((sx, sy), 0.17, fc=PAPER, ec=SVC, lw=1.0, zorder=10))
        ax.add_patch(plt.Circle((cx, cy), 0.17, fc=SVC, ec=SVC, lw=1.0, zorder=10))
    # ---- labels
    xc = 25.6
    txt(ax, xc, 19.7, f"FT-A1 · 20 in. OPEN-WEB FLOOR TRUSSES @ 16 in. O.C. · {len(a1)} THUS", size=5.6, weight="bold", box=True, z=12)
    txt(ax, xc, 18.65, f"each {ftin(a1[0]['y1'] - a1[0]['y0'])} long · bear on B1 and on the rear-wall ledge · run over B1 to the porch rim",
        size=4.8, box=True, z=12)
    txt(ax, 24.0, (by0 + by1) / 2 + 0.55, "SERVICE CORRIDOR IN THE TRUSS SPACE (3'-0\" band, above the R-30)", size=4.9, color=SVC, weight="bold", box=True, z=12)
    txt(ax, 24.0, (by0 + by1) / 2 - 0.5, "truss supplier: line up the web openings here, 7 in. clear min. · PEX, drains, refrigerant, feeders",
        size=4.4, color=SVC, box=True, z=12)
    txt(ax, xc, m.B1_Y + 1.05, f"B1  W14x34 (PRELIM.) DROPPED BELOW THE TRUSSES · TOP OF STEEL EL {m.EL_B1_TOP:.2f} + 1 1/2 in. NAILER · SEE S-104",
        size=4.8, color=STEEL, weight="bold", box=True, z=12)
    txt(ax, 24.0, 8.15, "4'-0\" PORCH CANTILEVER · doubled rim · top chord steps down outside the wall (A-402)",
        size=4.5, color=TR, box=True, z=12)
    txt(ax, 22.4, m.Y_GR_I - 0.62, "C1, C2: 16 x 16 in. insulated 1-hour pipe chases in the garage below (P-101)", size=4.3, color=ACCENT, ha="left", box=True, z=12)

    def west(p, y, s, color=TR):
        lead(ax, p, (m.xw_o(y) - 0.9, y), s, size=4.4, color=color, ha="right")

    west((m.xw_o(26.5) + aw, 26.5), 27.3, f"RIM-W follows the leaning\nwall, {ftin((m.Y_GR_O - m.YF) / CW)} (ladder truss\non the concrete wall)")
    west((a3[0]["x"], 20.0), 21.6, f"FT-A3 ({len(a3)}) trimmed,\n{ftin(a3[0]['y1'] - a3[0]['y0'])}: north end bears\non the west wall ledge")
    west((a2[-1]["x"], 15.6), 16.4, f"FT-A2 ({len(a2)}), {ftin(a2[0]['y1'] - a2[0]['y0'])},\nno cantilever: bear on\nthe concrete return")
    lead(ax, (X_PE, 9.2), (m.xw_o(8.6) - 0.9, 8.0), "PORCH-END TRUSS\n(extra FT-A1) at the\nwest jamb of the\ngarage opening", size=4.4, color=TR, ha="right")
    xe = m.XE + 1.0
    lead(ax, (ST_BAY[-1], 8.4), (xe, 7.6), f"FT-A4 ({len(a4)}): landing +\nporch, {ftin(a4[0]['y1'] - a4[0]['y0'])} long.\nBack span only {ftin(a4[0]['y1'] - m.YF - m.CMU / 2)}:\nstrap each one to\nHDR-A (engineer)", size=4.4, color=TR)
    lead(ax, (m.XEI - 0.6, Y_HDR_S), (xe, 13.6), f"HDR-A, landing edge:\n(2) 1 3/4 x 16 LVL\nprelim., {ftin(m.XEI - X_LOBBY)}, lobby\nwall to east wall ledge", size=4.4, color=TR)
    lead(ax, (X_RIM_E, 19.4), (xe, 19.4), f"RIM-E: end truss on\nthe concrete wall,\n{ftin(m.Y_GR_O - YS_P)}, carries the\nUnit A east wall", size=4.4, color=TR)
    lead(ax, (ST_BAY[-1], 26.3), (xe, 25.0), f"FT-A5 ({len(a5)}) over the\nutility room, {ftin(a5[0]['y1'] - a5[0]['y0'])}", size=4.4, color=TR)
    lead(ax, m.STACK_3, (xe, 32.2), "STACK 3 lands on the\noutside face of the\ngarage wall: sleeve it\nthrough the upstand\nabove bearing level,\nthen down inside the\nutility room (P-101)", size=4.4, color=SVC)
    lead(ax, m.STACK_1, (17.3, 23.7), "STACK 1 offsets in the truss\nspace to chase C1", size=4.4, color=SVC)
    lead(ax, (X_LOBBY, 15.6), (33.0, 15.4), "RIM-L ON THE LOBBY\nWALL: carries the stair\nwall, fire-blocks the\ntruss space", size=4.3, color=TR, ha="center")
    # ---- dimensions
    yd = YS_P - 1.45
    dim(ax, (m.xw_o(m.YF), yd), (m.PORCH[0], yd), 0, None, size=4.8, ext=False)
    dim(ax, (m.OPEN[0], yd), (m.OPEN[1], yd), 0, f"{ftin(m.OPEN_W)} GARAGE OPENING BELOW", size=4.8, ext=False)
    dim(ax, (m.OPEN[1], yd), (m.XE, yd), 0, None, size=4.8, ext=False)
    yd2 = YS_P - 2.75
    xa_e, xa_w = max(t["x"] for t in a1), min(t["x"] for t in a1 if t["x"] > X_PE + 0.1)
    dim(ax, (xa_w, yd2), (xa_e, yd2), 0, f"FT-A1: {round((xa_e - xa_w) / S16)} SPACES @ 16 in. = {ftin(xa_e - xa_w)}", size=4.8, ext=False)
    dim(ax, (xa_e, yd2), (m.XE, yd2), 0, f"{ftin(m.XE - xa_e)} SET-OUT", size=4.8, ext=False)
    dim(ax, (m.xw_o(m.YF), yd2), (xa_w, yd2), 0, None, size=4.8, ext=False)
    yd3 = YS_P - 4.05
    dim(ax, (ST_BAY[0], yd3), (ST_BAY[-1], yd3), 0, f"{len(ST_BAY) - 1} @ 16 in.", size=4.6, ext=False)
    dim(ax, (ST_BAY[-1], yd3), (m.XE, yd3), 0, ftin(m.XE - ST_BAY[-1]), size=4.6, ext=False)
    txt(ax, ST_BAY[0] - 0.5, yd3, "STAIR BAY (FT-A4, FT-A5) SET-OUT FROM THE EAST FACE", size=4.4, ha="right")
    xd = (a1[-3]["x"] + a1[-4]["x"]) / 2
    dimb(ax, (xd, m.B1_Y), (xd, m.Y_GR_I + BRG / 2), 0, f"{ftin(span_a)} SPAN, centre of B1 to centre of sill", size=4.7, ext=False, side=-1)
    dimb(ax, (xd, YS_P), (xd, m.B1_Y), 0, ftin(cant), size=4.5, ext=False, side=-1)
    dimb(ax, (35.0, m.YF), (35.0, YS_P), 0, "4'-0\"", size=4.5, ext=False, side=1)
    # bearing key in the empty corner
    txt(ax, 30.0, 42.4, "LEVELS", size=5.8, weight="bold", ha="left")
    for i, (s, e) in enumerate((("Top of subfloor = top of slab on grade", m.EL_A), ("Top of trusses", EL_TOP_A),
                                ("Truss bearing: top of nailer (B1) and sills", EL_BRG_A), ("Top of steel B1 = top of concrete ledges", m.EL_B1_TOP),
                                ("Underside of B1", m.EL_B1_TOP - m.B1_DEPTH),
                                ("Garage slab", m.EL_GAR))):
        txt(ax, 30.0, 41.4 - i * 0.82, s, size=4.9, ha="left")
        txt(ax, 46.4, 41.4 - i * 0.82, f"EL {e:.2f}", size=4.9, ha="right", weight="bold")
    txt(ax, 30.0, 36.5, "", size=4.5)
    # ---- strip: schedule and key
    y = SHEET_H - MARGIN - 0.3
    y = strip_head(bg, y, "Unit A floor truss schedule (preliminary)")
    rows = [("MARK", "QTY", "LENGTH", "WHERE / BEARING")]
    rows += [("FT-A1", len(a1), ftin(a1[0]["y1"] - a1[0]["y0"]), "Garage: B1 to rear ledge + porch"),
             ("FT-A1", "+2", ftin(a1[0]["y1"] - a1[0]["y0"]), "2nd ply under the water heater"),
             ("FT-A2", len(a2), ftin(a2[0]["y1"] - a2[0]["y0"]), "West end: concrete return to ledge"),
             ("FT-A3", len(a3), ftin(a3[0]["y1"] - a3[0]["y0"]), "Trimmed at the leaning west wall"),
             ("FT-A4", len(a4), ftin(a4[0]["y1"] - a4[0]["y0"]), "Stair landing + porch"),
             ("FT-A5", len(a5), ftin(a5[0]["y1"] - a5[0]["y0"]), "Over the utility room"),
             ("RIM-E", 1, ftin(m.Y_GR_O - YS_P), "End truss on the east wall"),
             ("RIM-W", 1, ftin((m.Y_GR_O - m.YF) / CW), "Ladder truss, west wall (6.5° lean)"),
             ("RIM-L", 1, ftin(m.Y_GR_I - m.YF), "Ladder truss on the lobby wall"),
             ("HDR-A", 1, ftin(m.XEI - X_LOBBY), "(2) 1 3/4 x 16 LVL, landing edge")]
    y = table(bg, STRIP_X, y, [0.46, 0.3, 0.5, STRIP_W - 1.26], rows, fs=5.2, rh=0.17)
    y -= 0.08
    y = strip_lines(bg, y, [
        f"All 20 in. deep at 16 in. o.c. FT-A1 design span {ftin(span_a)},",
        f"cantilever {ftin(cant)} beyond the centre of B1 (4'-0\" beyond",
        "the wall face). Truss design loads: S-001; live-load",
        "deflection L/480; porch 60 psf. Lengths are from the",
        "model: supplier to measure the concrete before making.",
    ])
    y -= 0.1
    y = strip_head(bg, y, "Set-out")
    y = strip_lines(bg, y, [
        f"Garage trusses: first one {ftin(m.XE - xa_e)} from the outside face",
        "of the east wall, then 16 in. o.c. westward. That puts",
        "plumbing stack 1 in the middle of a bay. One truss runs",
        "over chase C2: pipes enter that chase beside it.",
        f"Stair bay: first truss {ftin(m.XE - ST_BAY[-1])} from the east face, then",
        "16 in. o.c., the same as the Unit B floor above, so",
        "stack 3 is clear on both floors.",
    ])
    y -= 0.1
    y = strip_head(bg, y, "Stair opening")
    y = strip_lines(bg, y, [
        f"{ftin(m.SHAFT_U[1] - m.SHAFT_U[0])} x {ftin(m.SHAFT_U[3] - LAND_Y)} between the lobby wall, the east wall and",
        "the stair / utility wall (concrete or block up to bearing",
        f"level). One header, HDR-A, {ftin(LAND_Y - m.SHAFT_U[2])} north of the inside",
        "face of the front wall. FT-A4 hang from it and cantilever",
        "to the porch. Their back span is shorter than the",
        "cantilever: anchor HDR-A down to both walls.",
    ])
    y -= 0.1
    y = strip_head(bg, y, "Tie-down and blocking")
    y = strip_lines(bg, y, [
        f"FT-A1: back span {ftin(span_a)} against a {ftin(cant)} cantilever, so",
        "no net uplift is expected at the rear; still strap every",
        "truss to the sill (the floor props the wall) and clip it",
        "to B1. Full-depth blocking between trusses over B1: the",
        "Unit A front wall and all loads above land there.",
    ])
    truss_zone_key(fig, bg, STRIP_X, 0.5)
    save(fig, "S-201", pdf)


# ----------------------------------------------------------------------------
# S-202  Unit B floor framing
# ----------------------------------------------------------------------------
def _rng(vals, f=ftin):
    a, b = min(vals), max(vals)
    return f(a) if abs(a - b) < 0.04 else f"{f(a)} to {f(b)}"


def sheet_s202(pdf):
    T = trusses_b()
    g = {k: [t for t in T if t["mark"] == k] for k in ("B1", "B2", "B3", "B4", "B5", "B6")}
    notes = [
        ("Unit B floor framing", [
            "24 in. open-web trusses run north-south",
            "and clear-span from the front wall to the",
            "skewed rear wall of Unit A. No interior",
            "wall of Unit A is load-bearing.",
            "Every truss has its own length and a rear",
            f"end cut {abs(m.REAR_ANGLE):.1f}° off square.",
            f"16 in. o.c.; 12 in. o.c. where the span",
            "passes 28 ft (west part, tinted).",
            "Trusses run over the front wall and",
            "cantilever 4'-0\" for the Unit B porch.",
        ]),
        ("1-hour floor between the flats", [
            "This floor is the fire separation (IRC",
            "R302.3, assembly on A-501). No holes in",
            "the ceiling membrane except pipes, ducts",
            "and boxes fire-stopped to a listed system.",
            "No recessed lights. Stair walls 1-hour.",
        ]),
        ("Deck and edges", [
            "3/4 in. T&G subfloor, glued and nailed.",
            "Rim board all round; solid blocking over",
            "the front wall between the trusses.",
        ]),
        PRELIM,
    ]
    fig, bg = sheet("S-202", "Unit B floor framing", "3/16\" = 1'-0\"", notes)
    ax = plan_view(fig, bg, "Unit B floor framing plan",
                   f"Top of subfloor EL {m.EL_B:.1f} · truss bearing (top of Unit A wall plates) EL {EL_BRG_B:.2f} · Unit A walls below grey · preliminary")
    porch(ax, bg=True)
    unit_shell(ax, Style("bg"), "A")
    # 12 in. zone tint
    xz = X12_START + 0.5
    zone = [(m.xw_i(m.YFI), m.YFI), (xz, m.YFI), (xz, m.yr_i(xz)), m.IN_U[3]]
    poly(ax, zone, fc="#f3e7cf", ec="none", z=4.4, alpha=0.75)
    for t in T:
        line(ax, [(t["x"], t["y0"]), (t["x"], t["y1"])], lw=0.55, color=TR, z=7)
    whp = wh_pair([t["x"] for t in g["B1"]])
    draw_wh(ax, whp, YS_P + RIM, m.yr_o(whp[0]) - 0.2, (27.3, 26.3), "FT-B1")
    aw = m.EXT / 2 / CW
    line(ax, [(m.xw_o(m.YF) + aw, m.YF), (m.OUT_U[3][0] + aw, m.OUT_U[3][1] - 0.2)], lw=1.3, color=TR, z=7.5)   # west rim
    line(ax, [(X_RIM_E, YS_P), (X_RIM_E, m.yr_o(X_RIM_E))], lw=1.3, color=TR, z=7.5)                            # east end truss
    line(ax, [(m.xw_o(m.YF), m.YF + RIM / 2), (m.PORCH[0], m.YF + RIM / 2)], lw=1.3, color=TR, z=7.5)
    line(ax, [(m.PORCH[0], YS_P + RIM / 2), (m.XE, YS_P + RIM / 2)], lw=1.5, color=TR, z=7.5)
    line(ax, [(m.OUT_U[3][0] + 0.1, m.yr_o(m.OUT_U[3][0] + 0.1) - RIM / 2), (m.XE, m.yr_o(m.XE) - RIM / 2)], lw=1.3, color=TR, z=7.5)   # rear rim (skew)
    line(ax, [(X_GT, YS_P), (X_GT, m.yr_o(X_GT))], lw=2.2, color=TR, z=8)                                        # girder truss
    line(ax, [(X_GT, Y_HDR_S), (m.XEI, Y_HDR_S)], lw=2.0, color=TR, z=8)
    line(ax, [(X_GT, Y_HDR_N), (m.XEI, Y_HDR_N)], lw=2.0, color=TR, z=8)
    rect(ax, m.SHAFT_U[0], LAND_Y, m.SHAFT_U[1], m.SHAFT_U[3], fc=PAPER, ec=INK, lw=0.7, z=8.2, hatch="xx")
    xs_ = (m.SHAFT_U[0] + m.SHAFT_U[1]) / 2
    txt(ax, xs_, 19.6, "STAIR\nOPENING", size=5.0, weight="bold", box=True, z=12)
    txt(ax, xs_, 17.9, f"{ftin(m.SHAFT_U[1] - m.SHAFT_U[0])} x {ftin(m.SHAFT_U[3] - LAND_Y)}", size=4.6, box=True, z=12)
    txt(ax, xs_, 12.2, "LANDING", size=4.4, box=True, z=12)
    for i, (sx, sy) in enumerate((m.STACK_1, m.STACK_2, m.STACK_3)):
        ax.add_patch(plt.Circle((sx, sy), 0.19, fc=PAPER, ec=SVC, lw=1.1, zorder=10))
    # span limit line
    line(ax, [(X28, m.YF - 0.6), (X28, m.yr_o(X28) + 0.9)], lw=0.7, color=ACCENT, ls=(0, (5, 2, 1, 2)), z=9)
    txt(ax, X28 - 0.3, m.yr_o(X28) + 1.9, f"SPAN = 28'-0\" HERE\n({ftin(m.XE - X28)} from the east face)", size=4.5, color=ACCENT, ha="center")
    # labels
    b1 = g["B1"]
    txt(ax, 27.6, 17.0, f"FT-B1 · 24 in. OPEN-WEB FLOOR TRUSSES\n@ 16 in. O.C. · {len(b1)} THUS", size=5.4, weight="bold", box=True, z=12)
    txt(ax, 27.6, 15.35, f"spans {ftin(span_cc(b1[0]['x']))} (east) to {ftin(span_cc(b1[-1]['x']))} (west), + 4'-0\" porch", size=4.7, box=True, z=12)
    b2 = g["B2"]
    txt(ax, 13.3, 19.0, f"FT-B2 · 24 in. TRUSSES\n@ 12 in. O.C. · {len(b2)} THUS", size=5.0, weight="bold", box=True, z=12)
    txt(ax, 13.3, 17.6, f"spans {ftin(min(span_cc(t['x']) for t in b2))} to {ftin(max(span_cc(t['x']) for t in b2))}", size=4.6, box=True, z=12)
    txt(ax, 24.6, 8.15, "4'-0\" PORCH CANTILEVER (UNIT B PORCH) · doubled rim · no posts down to the Unit A porch", size=4.5, color=TR, box=True, z=12)
    # rear ends
    xr = 28.0
    lead(ax, (xr, m.yr_o(xr) - 0.1), (30.0, 38.6), f"REAR ENDS: each truss is cut {abs(m.REAR_ANGLE):.1f}° off square to sit on the\nskewed wall plate (or square-cut with a bevelled rim: supplier).\nEach truss is {ftin8(S16 * abs(REAR_SLOPE))} longer than its east neighbour at 16 in. o.c.,\n{ftin8(S12 * abs(REAR_SLOPE))} at 12 in. o.c.", size=4.5, color=TR)

    def west(p, y, s, color=TR):
        lead(ax, p, (m.xw_o(y) - 0.9, y), s, size=4.4, color=color, ha="right")

    b4 = g["B4"]
    west((m.xw_o(30.0) + aw, 30.0), 31.0, "RIM-W on the leaning\nwest wall plate")
    west((b4[-1]["x"], 17.0), 22.0, f"FT-B4 ({len(b4)}) trimmed:\nnorth ends bear on\nthe west wall, {_rng([t['y1'] - t['y0'] for t in b4])}")
    b3 = g["B3"]
    west((b3[0]["x"], 13.2), 14.6, f"FT-B3 ({len(b3)}), {ftin(b3[0]['y1'] - b3[0]['y0'])}: full\nspan, no cantilever\n(west of the porch)")
    lead(ax, (X_PE, 9.2), (m.xw_o(8.6) - 0.9, 8.0), "PORCH-END TRUSS\n(extra FT-B2) in line\nwith the porch end", size=4.4, color=TR, ha="right")
    xe = m.XE + 1.0
    b5, b6 = g["B5"], g["B6"]
    lead(ax, (ST_BAY[-1], 8.4), (xe, 7.4), f"FT-B6 ({len(b6)}): landing +\nporch, {ftin(b6[0]['y1'] - b6[0]['y0'])}. Back\nspan {ftin(b6[0]['y1'] - m.YF - m.EXT / 2)}: strap\neach one to HDR-S", size=4.4, color=TR)
    lead(ax, (m.XEI - 0.6, Y_HDR_S), (xe, 13.2), f"HDR-S and HDR-N:\n(2) 1 3/4 x 18 LVL\nprelim., {ftin(m.XEI - X_GT)}, from\nGT-B to a post in\nthe east wall", size=4.4, color=TR)
    lead(ax, (X_RIM_E, 20.6), (xe, 20.6), f"END TRUSS on the\neast wall, {ftin(m.yr_o(X_RIM_E) - YS_P)}", size=4.4, color=TR)
    lead(ax, (ST_BAY[-1], 27.0), (xe, 25.4), f"FT-B5 ({len(b5)}): HDR-N\nto the rear wall,\n{_rng([t['y1'] - t['y0'] for t in b5])}", size=4.4, color=TR)
    lead(ax, m.STACK_3, (xe, 31.6), "STACKS 1, 2, 3 (circles)\nfall between trusses:\nkeep this set-out", size=4.4, color=SVC)
    lead(ax, (X_GT, 21.5), (32.4, 22.6), f"GT-B: 2-ply girder truss\nover the stair wall,\n{ftin(m.yr_o(X_GT) - YS_P)} long, carries\nboth headers", size=4.4, color=TR, ha="center")
    # dimensions
    yd = YS_P - 1.45
    x16e, x16w = max(t["x"] for t in b1), min(t["x"] for t in b1)
    x12e = max(t["x"] for t in b2)
    x12w = min(t["x"] for t in T if t["oc"] == 12)
    dim(ax, (x16w, yd), (x16e, yd), 0, f"FT-B1: {round((x16e - x16w) / S16)} SPACES @ 16 in. = {ftin(x16e - x16w)}", size=4.8, ext=False)
    dim(ax, (x16e, yd), (X_GT, yd), 0, ftin(X_GT - x16e), size=4.4, ext=False)
    dim(ax, (X_GT, yd), (ST_BAY[0], yd), 0, "", size=4.4, ext=False)
    dim(ax, (ST_BAY[0], yd), (ST_BAY[-1], yd), 0, f"{len(ST_BAY) - 1} @ 16 in.", size=4.6, ext=False)
    dim(ax, (ST_BAY[-1], yd), (m.XE, yd), 0, ftin(m.XE - ST_BAY[-1]), size=4.6, ext=False)
    dim(ax, (x12e, yd), (x16w, yd), 0, ftin(x16w - x12e), size=4.4, ext=False)
    dim(ax, (x12w, yd), (x12e, yd), 0, f"{round(x12e - x12w)} SPACES @ 12 in.", size=4.6, ext=False)
    yd2 = YS_P - 2.75
    dim(ax, (m.xw_o(m.YF), yd2), (m.PORCH[0], yd2), 0, None, size=4.8, ext=False)
    dim(ax, (m.PORCH[0], yd2), (m.XE, yd2), 0, f"{ftin(m.XE - m.PORCH[0])} PORCH (TRUSSES CANTILEVER)", size=4.8, ext=False)
    yd3 = YS_P - 4.05
    dim(ax, (x16e, yd3), (m.XE, yd3), 0, f"{ftin(m.XE - x16e)} SET-OUT", size=4.6, ext=False)
    dim(ax, (X28, yd3), (x16e, yd3), 0, "SPAN UNDER 28 ft: 16 in. O.C.", size=4.6, ext=False)
    dim(ax, (m.xw_o(m.YF), yd3), (X28, yd3), 0, f"SPAN OVER 28 ft: 12 in. O.C.", size=4.6, ext=False, color=ACCENT)
    dimb(ax, (35.0, m.YF), (35.0, YS_P), 0, "4'-0\"", size=4.5, ext=False, side=1)
    # a few real spans on the plan
    for x_, sd in ((b1[0]["x"], 1), (b1[-1]["x"], 1), (g["B3"][0]["x"], 1)):
        xm = x_ + S16 / 2 if x_ > 12 else x_ + 0.5
        dimb(ax, (xm, m.YF + m.EXT / 2), (xm, m.yr_o(xm) - m.EXT / 2 / CR), 0, f"{ftin(span_cc(x_))} SPAN", size=4.5, ext=False, side=-1)
    # ---- strip
    y = SHEET_H - MARGIN - 0.3
    y = strip_head(bg, y, "Unit B floor truss schedule, east to west (prelim.)")
    rows = [("MARK", "QTY", "FROM E. FACE", "O.C.", "SPAN c/c", "LENGTH")]

    def row(mk, ts, span=True):
        xs = [t["x"] for t in ts]
        return (mk, len(ts), _rng([m.XE - x for x in xs]), f"{ts[0]['oc']}\"", _rng([span_cc(x) for x in xs]) if span else "-",
                _rng([t["y1"] - t["y0"] for t in ts]))

    rows.append(row("FT-B6", b6, span=False))
    rows.append(row("FT-B5", b5, span=False))
    rows.append(("GT-B", "1", ftin(m.XE - X_GT), "2-ply", ftin(span_cc(X_GT)), ftin(m.yr_o(X_GT) - YS_P)))
    n = len(b1)
    cuts = [0, (n + 2) // 3, (2 * n + 2) // 3, n]
    for i in range(3):
        rows.append(row(f"FT-B1{'abc'[i]}", b1[cuts[i]:cuts[i + 1]]))
    rows.append(("FT-B1", "+2", _rng([m.XE - x for x in whp]), "2nd ply", "under the water heater", ""))
    rows.append(row("FT-B2", b2))
    rows.append(row("FT-B3", g["B3"]))
    rows.append(row("FT-B4", b4, span=False))
    y = table(bg, STRIP_X, y, [0.46, 0.26, 0.9, 0.32, 0.9, STRIP_W - 2.84], rows, fs=4.7, rh=0.17)
    y -= 0.08
    y = strip_lines(bg, y, [
        "FROM E. FACE = distance of the truss centre from the",
        "outside face of the east wall framing. SPAN c/c = centre",
        "of the front wall plate to centre of the rear wall plate.",
        "LENGTH = overall, including the 4'-0\" porch cantilever",
        "where there is one. FT-B4, B5, B6 are short pieces.",
        f"Rims: east end truss {ftin(m.yr_o(X_RIM_E) - YS_P)}; west rim {ftin(m.WEST_WALL_LEN)} along the",
        f"lean; rear rim {ftin(m.REAR_WALL_LEN)} along the skew.",
    ], fs=5.6)
    y -= 0.1
    y = strip_head(bg, y, "Spans and spacing")
    y = strip_lines(bg, y, [
        f"Building depth, outside to outside of framing, is {ftin(depth_oo(m.XE))}",
        f"at the east wall and {ftin(depth_oo(m.OUT_U[3][0]))} at the north-west corner:",
        f"it grows {ftin8(abs(REAR_SLOPE))} for every foot you go west.",
        f"The span passes 28 ft at {ftin(m.XE - X28)} from the east face.",
        "From the next truss west, spacing is 12 in. o.c. to the",
        "west wall. Truss supplier may propose 16 in. o.c. with",
        "a stiffer truss: the engineer decides. L/480 live load;",
        "check floor vibration at the long spans.",
    ], fs=5.6)
    y -= 0.1
    y = strip_head(bg, y, "Stair opening")
    y = strip_lines(bg, y, [
        f"Opening {ftin(m.SHAFT_U[1] - m.SHAFT_U[0])} x {ftin(m.SHAFT_U[3] - LAND_Y)}. West side: 2-ply girder truss GT-B",
        "over the stair wall. North and south sides: LVL headers",
        "from GT-B to a built-up post in the east wall. FT-B5 hang",
        "from HDR-N; FT-B6 (landing and porch) from HDR-S.",
        "The stair walls below stand on block walls and could",
        "carry these headers instead: engineer's choice.",
    ], fs=5.6)
    y -= 0.1
    y = strip_head(bg, y, "Loads the west wall sees")
    y = strip_lines(bg, y, [
        "The trimmed trusses FT-B4 land on the leaning west",
        "wall, so that wall carries a strip of floor up to",
        f"{ftin(b3[0]['x'] - m.xw_i(m.YFI))} wide at the front. Everywhere else the east",
        "and west walls carry only themselves.",
    ], fs=5.6)
    y -= 0.1
    y = strip_head(bg, y, "Levels")
    for s, e in (("Top of subfloor, Unit B", m.EL_B), ("Top of trusses", EL_TOP_B), ("Truss bearing = top of Unit A wall plates", EL_BRG_B),
                 ("Unit A ceiling (finished)", m.EL_A + m.CLG_A)):
        bg.text(STRIP_X, y, s, fontsize=5.6, va="top")
        bg.text(STRIP_X + STRIP_W - 0.05, y, f"EL {e:.2f}", fontsize=5.6, va="top", ha="right", fontweight="bold")
        y -= 0.16
    save(fig, "S-202", pdf)


# ----------------------------------------------------------------------------
# S-203  Roof framing
# ----------------------------------------------------------------------------
P = m.ROOF_PITCH
EL_HEEL = m.EL_PLATE + m.HEEL                     # top of truss at the outside face of the bearing walls
EL_EAVE_F = EL_HEEL - 4.0 * P                     # top of truss at the front eave (4'-0" out)
EL_EAVE_R = EL_HEEL - OH_REAR / CR * P            # top of truss at the rear eave
ROOF_FULL = [x for x in ROOF_X if x > m.OUT_U[3][0] + 0.05]
ROOF_CLIP = [x for x in ROOF_X if x <= m.OUT_U[3][0] + 0.05]
GW_END = _x_of_rear(eave_r, m.xw_o)               # west gable truss meets the rear eave


def why_roof_key(fig, bg, left, bottom):
    """Shortest and longest common truss drawn over each other from the front wall."""
    f = 12.0
    w = STRIP_W * f
    ax = plan_axes(fig, left, bottom, (-5.0, w - 5.0), (-2.2, 9.4), f)
    xa, xb = ROOF_FULL[0], ROOF_FULL[-1]
    for x, c, lw in ((xb, TR, 1.0), (xa, STEEL, 1.0)):
        L = depth_oo(x)
        h = m.HEEL + L / 2 * P
        pts = [(-4.0, m.HEEL - 4.0 * P), (L / 2, h), (L + OH_REAR / CR, m.HEEL - OH_REAR / CR * P)]
        line(ax, pts, lw=lw, color=c, z=6)
        line(ax, [(0, 0), (L, 0), (L, m.HEEL), (L, 0)], lw=lw * 0.8, color=c, z=5)
        line(ax, [(0, 0), (0, m.HEEL)], lw=lw * 0.8, color=c, z=5)
        line(ax, [(L / 2, 0), (L / 2, h)], lw=0.3, color=c, ls=(0, (3, 2)), z=5)
        txt(ax, L / 2, h + 0.75, f"{m.ridge_el(x):.2f}", size=4.4, color=c, weight="bold")
        txt(ax, L, -0.9, ftin(L), size=4.4, color=c, ha="right")
    line(ax, [(-5.0, 0), (w - 5.0, 0)], lw=0.3, color=GREY, z=3)
    txt(ax, -4.9, -0.9, "FRONT WALL", size=4.0, color=GREY, ha="left")
    txt(ax, -4.9, 6.2, f"T1 (blue) and T{len(ROOF_FULL)} (brown)\nstart from the same heel\nand rise at the same 4:12", size=4.3, ha="left", va="top")
    bg.text(left, bottom + 11.6 / f + 0.06, "WHY THE ROOF IS TWO FLAT PLANES", fontsize=6.4, fontweight="bold", va="bottom")


def sheet_s203(pdf):
    s_abs = abs(REAR_SLOPE)
    true_pitch = 12 * P * math.sqrt(1 + s_abs ** 2)
    notes = [
        ("Roof framing", [
            "Common trusses at 24 in. o.c. run north-",
            "south and bear on the front and rear",
            "walls of Unit B. 4:12, 12 in. raised heel.",
            "Each is a symmetric gable truss, so its",
            "peak is at mid-span. Spans grow from",
            f"{ftin(depth_oo(m.XE))} (east) to {ftin(depth_oo(ROOF_FULL[-1]))} (west): the ridge",
            "is skewed in plan and climbs westward.",
            "Front: 4'-0\" cantilevered tails over the",
            "porch with a level soffit return.",
            "Rear: 12 in. Rakes: 8 in. (1-hour under).",
        ]),
        ("Sheathing and ties", [
            "7/16 in. OSB with H-clips, 8d at 6 in.",
            "edges and 12 in. field (prelim.).",
            "Hurricane tie at every truss, both walls.",
            "Permanent bracing exactly as shown on",
            "the sealed truss drawings (BCSI).",
            "Brace gable-end trusses to the roof plane.",
            "Attic access 22 x 30 in. in the hall.",
            "Attic vents: front soffit and ridge only.",
        ]),
        ("Not in the attic", [
            "No ducts, air handler or water pipe.",
        ]),
        PRELIM,
    ]
    fig, bg = sheet("S-203", "Roof framing", "3/16\" = 1'-0\"", notes)
    ax = plan_view(fig, bg, "Roof framing plan",
                   f"Top of wall plates EL {m.EL_PLATE:.2f} · trusses at 24 in. o.c. · Unit B walls below grey · preliminary", bar=(33.0, 44.6))
    unit_shell(ax, Style("bg"), "B")
    poly(ax, ROOF, fc="none", ec=INK, lw=1.0, z=8)
    # bearing walls
    line(ax, [(m.xw_o(m.YF), m.YF + m.EXT / 2), (m.XE, m.YF + m.EXT / 2)], lw=2.4, color="#d9c8a6", z=5.5)
    line(ax, [(m.OUT_U[3][0], m.OUT_U[3][1] - m.EXT / 2 / CR), (m.XE, m.Y_GR_O - m.EXT / 2 / CR)], lw=2.4, color="#d9c8a6", z=5.5)
    for i, x in enumerate(ROOF_FULL):
        line(ax, [(x, m.YF), (x, eave_r(x))], lw=0.6, color=TR, z=7)
        line(ax, [(x, EAVE_F), (x, m.YF)], lw=0.6, color=TR, z=7, ls=(0, (4, 1.5)))
        for yy in (m.YF + m.EXT / 2, m.yr_o(x) - m.EXT / 2 / CR):
            ax.add_patch(plt.Circle((x, yy), 0.16, fc=ACCENT, ec="none", zorder=9))
        txt(ax, x, EAVE_F - 0.75, f"T{i + 1}", size=4.2, color=TR, rot=90, weight="bold")
    for i, x in enumerate(ROOF_CLIP):
        yw = y_on(m.xw_o, x)
        line(ax, [(x, m.YF), (x, yw)], lw=0.6, color=TR, z=7)
        line(ax, [(x, EAVE_F), (x, m.YF)], lw=0.6, color=TR, z=7, ls=(0, (4, 1.5)))
        ax.add_patch(plt.Circle((x, m.YF + m.EXT / 2), 0.16, fc=ACCENT, ec="none", zorder=9))
        txt(ax, x, EAVE_F - 0.75, f"C{i + 1}", size=4.2, color=TR, rot=90, weight="bold")
    # gable-end trusses and rake ladders
    line(ax, [(m.XE - 0.06, EAVE_F), (m.XE - 0.06, eave_r(m.XE))], lw=1.5, color=TR, z=7.5)
    line(ax, [(m.xw_o(EAVE_F) + 0.06, EAVE_F), (GW_END[0] + 0.06, GW_END[1])], lw=1.5, color=TR, z=7.5)
    for y in np.arange(EAVE_F + 1.0, eave_r(m.XE), 2.0):
        line(ax, [(m.XE, y), (m.XE + RAKE, y)], lw=0.4, color=TR, z=7)
    for y in np.arange(EAVE_F + 1.0, GW_END[1], 2.0):
        line(ax, [(m.xw_o(y), y), (rake_w(y), y - RAKE * TW)], lw=0.4, color=TR, z=7)
    txt(ax, m.XE - 0.06, EAVE_F - 0.75, "GE", size=4.2, color=TR, rot=90, weight="bold")
    txt(ax, m.xw_o(EAVE_F) - 0.2, EAVE_F - 0.75, "GW", size=4.2, color=TR, rot=90, weight="bold")
    # ridge
    r_e = (m.XE + RAKE, m.ridge_y(m.XE + RAKE))
    line(ax, [RIDGE_WR, r_e], lw=1.8, color=INK, z=9)
    rang = math.degrees(math.atan2(r_e[1] - RIDGE_WR[1], r_e[0] - RIDGE_WR[0]))
    txt(ax, 31.0, m.ridge_y(31.0) + 0.75, f"RIDGE · skewed {abs(rang):.1f}° in plan · rises {ftin8(S24 * s_abs / 2 * P)} per truss going west", size=5.0, weight="bold", rot=rang, box=True, z=12)
    lead(ax, (m.XE, m.ridge_y(m.XE)), (m.XE + 1.6, m.ridge_y(m.XE) + 1.6), f"RIDGE EL {m.ridge_el(m.XE):.2f}\nat the east wall face,\n{ftin(depth_oo(m.XE) / 2)} from the front wall", size=4.6, weight="bold")
    lead(ax, RIDGE_W, (RIDGE_W[0] - 1.6, RIDGE_W[1] + 1.2), f"RIDGE EL {m.ridge_el(RIDGE_W[0]):.2f}\nat the west wall face,\n{ftin(RIDGE_W[1] - m.YF)} from the front wall", size=4.6, weight="bold", ha="right")
    # slope arrows
    arrow = dict(arrowstyle="-|>", lw=0.8, color=INK)
    for x in (17.8, 33.8):
        ry = m.ridge_y(x)
        ax.annotate("", xy=(x, ry - 5.6), xytext=(x, ry - 2.2), arrowprops=arrow, zorder=11)
        txt(ax, x, ry - 6.3, "4:12", size=5.4, weight="bold", box=True, z=12)
        ax.annotate("", xy=(x, ry + 5.2), xytext=(x, ry + 1.8), arrowprops=arrow, zorder=11)
        txt(ax, x, ry + 5.9, "4:12", size=5.4, weight="bold", box=True, z=12)
    # attic access
    acc = (20.95, 23.9, 22.72, 26.4)
    rect(ax, *acc[:2], *acc[2:], fc=PAPER, ec=ACCENT, lw=0.8, z=9)
    line(ax, [acc[:2], acc[2:]], lw=0.4, color=ACCENT, z=9.5)
    lead(ax, (acc[2], 24.3), (23.6, 19.6), "ATTIC ACCESS 22 x 30 in.\nin the hall ceiling, between\ntrusses, gasketed + R-49 lid", size=4.4, color=ACCENT, dot=False)
    # labels
    txt(ax, 27.2, 13.6, f"T1 - T{len(ROOF_FULL)} · COMMON ROOF TRUSSES @ 24 in. O.C. · 4:12 · 12 in. RAISED HEEL", size=5.4, weight="bold", box=True, z=12)
    txt(ax, 27.2, 12.55, "bear on the front and rear walls (tan) · red dot = hurricane tie at every truss, each wall", size=4.6, box=True, z=12)
    txt(ax, 26.0, 8.15, "4'-0\" FRONT OVERHANG OVER THE UNIT B PORCH · cantilevered truss tails (dashed) · level soffit return to the wall",
        size=4.5, color=TR, box=True, z=12)
    lead(ax, (30.0, eave_r(30.0)), (31.0, 39.2), f"REAR EAVE: 12 in. overhang measured square to the wall\n({ftin8(OH_REAR / CR)} along the truss) · 1-hour soffit, no vents: see A-501 and S-301", size=4.5, color=TR)
    xe = m.XE + 1.5
    lead(ax, (m.XE - 0.06, 14.0), (xe, 13.2), f"GE: GABLE-END TRUSS on\nthe east wall, {ftin(depth_oo(m.XE))} span,\nstudded at 16 in. for\nsheathing and siding", size=4.4, color=TR)
    lead(ax, (m.XE + RAKE, 26.5), (xe, 27.5), "8 in. RAKE: 2x4 ladder at\n24 in. on the gable truss,\n1-hour underside (A-501)", size=4.4, color=TR)
    gy = 20.0

    def west(p, y, s, color=TR):
        lead(ax, p, (rake_w(y) - 0.9, y), s, size=4.4, color=color, ha="right")

    west((m.xw_o(31.0) + 0.06, 31.0), 33.4, f"GW: GABLE-END TRUSS along\nthe leaning west wall,\n{ftin(m.WEST_WALL_LEN)} span, top chords\n{12 * P * CW:.2f}:12 front and\n{12 * P * (CW + s_abs * math.sin(WEST_LEAN)):.2f}:12 rear along its length")
    c1 = ROOF_CLIP[0]
    west((c1, 15.5), 17.2, f"C1, C2: common-truss\nprofile cut off at the west\ngable, hung from GW\n({ftin(y_on(m.xw_o, ROOF_CLIP[0]) - m.YF)} and {ftin(y_on(m.xw_o, ROOF_CLIP[-1]) - m.YF)} from\nthe front wall)")
    west((rake_w(21.6), 21.6), 21.6, "8 in. RAKE, square to the\nwall, 1-hour underside")
    # dimensions
    yd = EAVE_F - 2.3
    dim(ax, (ROOF_FULL[-1], yd), (ROOF_FULL[0], yd), 0, f"{len(ROOF_FULL) - 1} SPACES @ 24 in. = {ftin(ROOF_FULL[0] - ROOF_FULL[-1])}", size=4.8, ext=False)
    dim(ax, (ROOF_FULL[0], yd), (m.XE, yd), 0, ftin(m.XE - ROOF_FULL[0]), size=4.6, ext=False)
    dim(ax, (m.xw_o(m.YF), yd), (ROOF_FULL[-1], yd), 0, None, size=4.6, ext=False)
    yd2 = EAVE_F - 3.6
    dim(ax, (m.xw_o(m.YF), yd2), (m.XE, yd2), 0, f"{ftin(m.FACADE_W)} FRONT WALL, OUTSIDE OF FRAMING", size=4.8, ext=False)
    dim(ax, (m.XE, yd2), (m.XE + RAKE, yd2), 0, "8\"", size=4.4, ext=False)
    dim(ax, (ROOF[0][0], yd2), (m.xw_o(m.YF), yd2), 0, "8\"", size=4.4, ext=False)
    xr = m.XE + RAKE
    dim(ax, (xr, EAVE_F), (xr, m.YF), -1.0, "4'-0\"", size=4.6, side=-1)
    dim(ax, (xr, m.YF), (xr, m.Y_GR_O), -1.0, ftin(m.Y_GR_O - m.YF), size=4.6, side=-1)
    dim(ax, (xr, m.Y_GR_O), (xr, eave_r(m.XE)), -1.0, ftin(OH_REAR / CR), size=4.4, side=-1)
    for x_ in (ROOF_FULL[0], ROOF_FULL[len(ROOF_FULL) // 2], ROOF_FULL[-1]):
        xm = x_ + 1.0
        dimb(ax, (xm, m.YF), (xm, m.yr_o(xm)), 0, "", size=4.5, ext=False, side=-1)
        txt(ax, xm, m.YF + 5.6 if x_ < 40 else m.YF + 13.0, f"T{ROOF_FULL.index(x_) + 1}: {ftin(depth_oo(x_))}", size=4.5, rot=90, box=True, z=12)
    # ---- strip: truss schedule
    y = SHEET_H - MARGIN - 0.3
    y = strip_head(bg, y, "Roof truss schedule (preliminary)")
    rows = [("MARK", "FROM E. FACE", "SPAN", "RIDGE EL", "RISE", "NOTE")]
    rows.append(("GE", "0", ftin8(depth_oo(m.XE)), f"{m.ridge_el(m.XE):.2f}", ftin8(m.ridge_el(m.XE) - m.EL_PLATE), "gable end"))
    for i, x in enumerate(ROOF_FULL):
        rows.append((f"T{i + 1}", ftin(m.XE - x), ftin8(depth_oo(x)), f"{m.ridge_el(x):.2f}", ftin8(m.ridge_el(x) - m.EL_PLATE),
                     "attic access bay" if abs(x - 21.8) < 1.1 and x > 21.8 else ""))
    for i, x in enumerate(ROOF_CLIP):
        yw = y_on(m.xw_o, x)
        top = m.ridge_el(x) if yw > m.ridge_y(x) else EL_HEEL + (yw - m.YF) * P
        rows.append((f"C{i + 1}", ftin(m.XE - x), ftin8(yw - m.YF), f"{top:.2f}", ftin8(top - m.EL_PLATE), "clipped at GW"))
    rows.append(("GW", "west wall", ftin8(m.WEST_WALL_LEN), f"{m.ridge_el(RIDGE_W[0]):.2f}", ftin8(m.ridge_el(RIDGE_W[0]) - m.EL_PLATE), "gable, on the lean"))
    y = table(bg, STRIP_X, y, [0.36, 0.7, 0.72, 0.56, 0.52, STRIP_W - 2.86], rows, fs=4.7, rh=0.148)
    y -= 0.08
    y = strip_lines(bg, y, [
        "FROM E. FACE: truss centre from the outside face of the",
        "east wall framing. SPAN: outside to outside of the wall",
        "framing at that truss (C1, C2: front wall to the cut end).",
        "RISE: top of truss at the peak above the wall plates.",
        f"Each truss is {ftin8(S24 * s_abs)} longer and {ftin8(S24 * s_abs / 2 * P)} taller than the",
        "one east of it. Tails: 4'-0\" front, 12 in. rear (square).",
        "Supplier to verify every span on the framed walls.",
    ], fs=5.5)
    y -= 0.1
    y = strip_head(bg, y, "Why this works")
    y = strip_lines(bg, y, [
        "Every truss starts at the front wall with the same heel",
        "and the same 4:12 top chord, so the front slope is one",
        "flat plane. Every rear top chord is also 4:12 and ends",
        "at the same heel height on the rear wall, which is a",
        "straight line, so the rear slope is one flat plane too",
        f"(it measures {true_pitch:.2f}:12 square to the skewed eave).",
        "Two flat planes meet in a straight line: the ridge. It",
        "is straight but not level and not parallel to the street.",
        "Sheathing lies flat; both eaves are level; no hips,",
        "valleys or girder trusses are needed.",
    ], fs=5.5)
    y -= 0.1
    y = strip_head(bg, y, "Levels (top of truss; add sheathing + shingles)")
    for s_, e in (("Ridge at the west / east wall face", f"EL {m.ridge_el(RIDGE_W[0]):.2f} / {m.ridge_el(m.XE):.2f}"),
                  ("Heel: top of truss at the outside face of both walls", f"EL {EL_HEEL:.2f}"),
                  ("Rear eave (level, parallel to the rear wall)", f"EL {EL_EAVE_R:.2f}"),
                  ("Front eave, 4'-0\" out (level)", f"EL {EL_EAVE_F:.2f}"),
                  ("Top of wall plates, Unit B", f"EL {m.EL_PLATE:.2f}")):
        bg.text(STRIP_X, y, s_, fontsize=5.5, va="top")
        bg.text(STRIP_X + STRIP_W - 0.05, y, e, fontsize=5.5, va="top", ha="right", fontweight="bold")
        y -= 0.155
    why_roof_key(fig, bg, STRIP_X, 0.5)
    save(fig, "S-203", pdf)


# ----------------------------------------------------------------------------
# S-204  Wall framing, shear walls and porch
# ----------------------------------------------------------------------------
def _open_list(wall):
    o = [(s0, s1, tag, note) for (tag, w_, s0, s1, note) in m.WINDOWS if w_ == wall]
    if wall == "S":
        o += [(d["s0"], d["s1"], d["tag"], d["note"]) for d in m.DOORS if d["wall"] == "h" and abs(d["at"][0] - m.YF) < 1e-6]
    return sorted(o)


def wall_pt(wall, s, off=0.0):
    """Point on the outside face of an exterior wall at station s, moved `off` ft outward (negative = inward)."""
    if wall == "S":
        return (s, m.YF - off)
    if wall == "E":
        return (m.XE + off, s)
    if wall == "N":
        return (s + off * math.sin(SKEW), m.yr_o(s) + off * math.cos(SKEW))
    return (m.xw_o(s) - off * CW, s + off * math.sin(WEST_LEAN))


WALL_SPAN = {"S": (m.xw_o(m.YF), m.XE), "E": (m.YF, m.Y_GR_O), "N": (m.OUT_U[3][0], m.XE), "W": (m.YF, m.OUT_U[3][1])}
WALL_FAC = {"S": 1.0, "E": 1.0, "N": 1 / CR, "W": 1 / CW}
WALL_NAME = {"S": "Front", "E": "East", "N": "Rear", "W": "West"}


def shear_segments():
    res = []
    for w in "SENW":
        lo, hi = WALL_SPAN[w]
        a, k = lo, 0
        for s0, s1, tag, _ in _open_list(w) + [(hi, hi, None, None)]:
            if s0 - a > 0.5:
                k += 1
                L = (s0 - a) * WALL_FAC[w]
                res.append(dict(wall=w, mark=f"{w}{k}", s0=a, s1=s0, L=L, ratio=WALL_H_B / L))
            a = s1
    return res


def header_for(width):
    """Preliminary header by opening width: (mark, Unit A size, Unit B size)."""
    if width <= 3.01:
        return ("H1", "(2) 2x10, 2 trimmers", "(2) 2x8, 1 trimmer")
    return ("H2", "(2) 1 3/4 x 9 1/4 LVL, 2 trimmers", "(2) 2x10, 2 trim.")


def porch_posts():
    """Guard post centres along the porch front edge: equal bays of 5 ft or less."""
    L = m.PORCH[2] - m.PORCH[0] - 2 * 0.15
    n = math.ceil(L / 5.0)
    return [m.PORCH[0] + 0.15 + i * L / n for i in range(n + 1)], L / n


def porch_plan(fig, bg, left, bottom):
    f = 4.0
    vx, vy = (9.6, 47.4), (4.5, 12.0)
    ax = plan_axes(fig, left, bottom, vx, vy, f)
    x0, y0, x1, y1 = m.PORCH
    rect(ax, m.xw_o(m.YF), m.YF, m.XE, m.YFI, fc=BG_WALL, ec=BG_EDGE, lw=0.5, z=3)
    rect(ax, m.xw_o(m.YF), m.YFI, m.XE, vy[1], fc="#f6f7f8", ec="none", z=2)
    for s0, s1, tag, _ in _open_list("S"):
        rect(ax, s0, m.YF - 0.01, s1, m.YFI + 0.01, fc=PAPER, ec=BG_EDGE, lw=0.4, z=4)
        if s0 > vx[0] + 1:
            txt(ax, (s0 + s1) / 2, m.YFI + 0.62, "PORCH DOOR D14" if tag == "D14" else f"WINDOW {tag}", size=4.2, color=GREY, box=True, z=9)
    rect(ax, x0, y0, x1, y1, fc="#fbf8f1", ec="none", z=2)
    for y in np.arange(y0 + 5.5 * IN, y1 - 0.05, 5.625 * IN):
        line(ax, [(x0, y), (x1, y)], lw=0.2, color=LIGHT, z=3)
    xs = sorted([t["x"] for t in trusses_a() if t["mark"] in ("A1", "A4")])
    for x in xs:
        line(ax, [(x, y0 + 2 * RIM), (x, m.YFI + 0.9)], lw=0.7, color=TR, z=6)
    for x in (X_RIM_E,):
        line(ax, [(x, y0), (x, m.YFI + 0.9)], lw=1.4, color=TR, z=6)
    line(ax, [(x0, y0 + RIM / 2), (x1, y0 + RIM / 2)], lw=1.2, color=TR, z=6)
    line(ax, [(x0, y0 + RIM * 1.5), (x1, y0 + RIM * 1.5)], lw=1.2, color=TR, z=6)
    line(ax, [(m.COL_X[0], m.B1_Y), (m.COL_X[2], m.B1_Y)], lw=1.6, color=STEEL, ls=(0, (6, 2)), z=5)
    line(ax, [(x0, m.YF + m.EXT / 2), (x1, m.YF + m.EXT / 2)], lw=0.5, color=TR, ls=(0, (2, 1.5)), z=6.5)
    posts, bay = porch_posts()
    ps = 3.5 * IN
    for px in posts:
        rect(ax, px - ps / 2, y0 - ps + 0.02, px + ps / 2, y0 + 0.02, fc=INK, ec=INK, lw=0.3, z=8)
    for px in (x0 + 0.15, x1 - 0.15):
        rect(ax, px - ps / 2, y1 - ps - 0.05, px + ps / 2, y1 - 0.05, fc=INK, ec=INK, lw=0.3, z=8)
    line(ax, [(x0 + 0.15, y1 - 0.2), (x0 + 0.15, y0 - ps / 2), (x1 - 0.15, y0 - ps / 2), (x1 - 0.15, y1 - 0.2)], lw=0.5, color=INK, ls=(0, (1, 1)), z=7)
    # dims
    yd = y0 - 0.75
    for a, b in zip(posts[:-1], posts[1:]):
        dim(ax, (a, yd), (b, yd), 0, ftin8(bay), size=4.4, ext=False)
    dim(ax, (x0, yd - 0.72), (x1, yd - 0.72), 0, f"{ftin(x1 - x0)} PORCH, OUT TO OUT OF RIMS", size=4.6, ext=False)
    dim(ax, (x0, y0), (x0, y1), 0.8, "4'-0\"", size=4.6)
    k = len(xs) // 2
    dimb(ax, (xs[k], 9.55), (xs[k + 1], 9.55), 0, "16\"", size=4.2, ext=False)
    # labels
    lead(ax, (15.2, y0 + RIM), (10.0, 8.9), "DOUBLED RIM\n(2) 1 1/2 x 11 7/8\nLVL, PT or wrapped", size=4.3, color=TR, ha="left", va="center") if False else None
    txt(ax, 21.6, 8.75, "5/4 x 6 COMPOSITE OR PT DECKING, BOARDS EAST-WEST ACROSS THE TRUSS TAILS, 1/8 in. GAPS", size=4.5, box=True, z=9)
    txt(ax, 21.6, 7.95, "truss tails at 16 in. o.c. = the floor trusses run out 4'-0\" (FT-A1, FT-A4); top chord stepped down for the deck", size=4.2, color=TR, box=True, z=9)
    txt(ax, 21.6, 7.15, f"black squares = 4x4 PT guard posts, {len(posts) - 1} equal bays (5'-0\" max.), bolted to the DOUBLED RIM; guard 36 in. min. above the deck",
        size=4.2, box=True, z=9)
    lead(ax, (m.COL_X[1] + 3.0, m.B1_Y), (33.4, 9.55), "B1 BELOW (dashed blue): full-depth blocking between trusses over it", size=4.2, color=STEEL)
    lead(ax, (posts[2], y0 - ps / 2), (posts[2] + 0.5, 5.05), "4x4 PT GUARD POST, 36 in. MIN. ABOVE THE DECK, (2) 1/2 in. THROUGH-BOLTS TO THE DOUBLED RIM + BLOCKING. 200 lb AT THE TOP, ANY DIRECTION.", size=4.2) if False else None
    txt(ax, x1 + 0.3, 9.0, "END TRUSS\n= porch end,\nguard returns\nto the wall", size=4.0, color=TR, ha="left")
    bg.text(left, bottom + (vy[1] - vy[0]) / f + 0.07, "PORCH FRAMING PLAN (UNIT A SHOWN, UNIT B THE SAME ON ITS OWN TRUSSES)   1/4\" = 1'-0\"", fontsize=7.0, fontweight="bold", va="bottom")
    return ax


def sheet_s204(pdf):
    segs = shear_segments()
    ang = corner_angles()                       # SW, SE, NE, NW
    notes = [
        ("Wall framing", [
            "Exterior walls: 2x6 at 16 in. o.c., 7/16",
            "in. OSB, double top plate (A-501).",
            "Front and rear walls are bearing: they",
            "carry the roof and the Unit B floor.",
            "East and west walls carry themselves",
            "(west: also the trimmed truss ends).",
            "All interior partitions are non-bearing.",
            "Stair walls: 2x4 + 5/8 Type X, 1-hour.",
        ]),
        ("Shear walls (red)", [
            "Full-height wall between openings, both",
            "storeys alike. Lengths are from the",
            "model. Prelim.: 8d at 4 in. edges, 12 in.",
            "field, all edges blocked; hold-down at",
            "each segment end; strap Unit B studs to",
            "Unit A studs across the floor.",
        ]),
        ("Open garage front", [
            "At garage level the front line has only",
            "the concrete return (west) and the lobby",
            "wall (east). Engineer to verify them or",
            "make B1 and its post a moment frame.",
        ]),
        PRELIM,
    ]
    fig, bg = sheet("S-204", "Wall framing, shear walls and porch", "3/16\" = 1'-0\"; porch 1/4\"", notes)
    view = ((0.5, 51.0), (4.3, 45.3))
    PB = 2.82
    ax = plan_axes(fig, PLAN_L, PB, view[0], view[1], FPI)
    txt(ax, 27.0, 44.3, "WALL FRAMING AND SHEAR WALL PLAN", size=10.5, weight="bold", ha="left")
    txt(ax, 27.0, 43.3, "Typical flat (Units A and B alike) · 3/16\" = 1'-0\" · preliminary", size=6.2, color=GREY, ha="left")
    north_arrow(ax, 48.6, 39.6, 1.5, 6.5)
    porch(ax, bg=True)
    unit_shell(ax, Style("bg"), "A")
    # bearing walls tinted
    BEAR = "#e2c98f"
    for w, (lo, hi) in (("S", WALL_SPAN["S"]), ("N", WALL_SPAN["N"])):
        a = lo
        for s0, s1, tag, _ in _open_list(w) + [(hi, hi, None, None)]:
            if s0 - a > 0.05:
                q = m.win_quad(w, a, s0)
                poly(ax, q, fc=BEAR, ec=BG_EDGE, lw=0.4, z=5.6)
            a = s1
    # headers
    hrows = [("MARK", "OPENING", "WIDTH", "UNIT A HEADER", "UNIT B HEADER")]
    for w in "SNW":
        for s0, s1, tag, note in _open_list(w):
            width = (s1 - s0)
            mk, ha_, hb_ = header_for(width)
            q = m.win_quad(w, s0, s1)
            c0 = ((q[0][0] + q[3][0]) / 2, (q[0][1] + q[3][1]) / 2)
            c1 = ((q[1][0] + q[2][0]) / 2, (q[1][1] + q[2][1]) / 2)
            line(ax, [c0, c1], lw=2.4, color=STEEL, z=9)
            px, py = wall_pt(w, (s0 + s1) / 2, -1.55)
            mark(ax, px, py, mk, color=STEEL, size=4.4)
            hrows.append((mk, f"{tag} {WALL_NAME[w].lower()}: {note.split(',')[0].replace(' escape window', '')}", ftin(width), ha_, hb_))
    # shear segments
    OFF = {"S": 5.0, "E": 1.7, "N": 1.6, "W": 1.6}
    srows = [("MARK", "WALL", "LENGTH", "h / L", "USE")]
    for sg in segs:
        w = sg["wall"]
        ok = sg["ratio"] <= 3.5
        full = sg["ratio"] <= 2.0
        p0, p1 = wall_pt(w, sg["s0"], 0.3), wall_pt(w, sg["s1"], 0.3)
        line(ax, [p0, p1], lw=2.6 if ok else 1.2, color=ACCENT, z=9, ls="-" if ok else (0, (1.5, 1.5)))
        if ok:
            for p in (p0, p1):
                rect(ax, p[0] - 0.24, p[1] - 0.24, p[0] + 0.24, p[1] + 0.24, fc=INK, ec=INK, lw=0.3, z=10)
        f0, f1 = wall_pt(w, sg["s0"]), wall_pt(w, sg["s1"])
        off = OFF[w] if w in "NW" else -OFF[w]
        dim(ax, f0, f1, off, f"SW-{sg['mark']}  {ftin(sg['L'])}", size=4.6, color=ACCENT, side=1 if w in "NW" else -1)
        srows.append((f"SW-{sg['mark']}", WALL_NAME[w], ftin(sg["L"]), f"{sg['ratio']:.1f}",
                      "full" if full else ("reduced (narrow)" if ok else "too narrow: not counted")))
    # corner angles
    names = ("SW", "SE", "NE", "NW")
    for i, (cx, cy) in enumerate(m.OUT_U):
        a_prev, a_next = m.OUT_U[i - 1], m.OUT_U[(i + 1) % 4]
        t1 = math.degrees(math.atan2(a_prev[1] - cy, a_prev[0] - cx)) % 360
        t2 = math.degrees(math.atan2(a_next[1] - cy, a_next[0] - cx)) % 360
        lo_, hi_ = (t2, t1) if (t1 - t2) % 360 < 180 else (t1, t2)
        ax.add_patch(Arc((cx, cy), 5.0, 5.0, theta1=lo_, theta2=hi_, lw=0.8, color=INK, zorder=11))
        mid = math.radians(lo_ + ((hi_ - lo_) % 360) / 2)
        txt(ax, cx + 3.5 * math.cos(mid), cy + 3.5 * math.sin(mid), f"{ang[i]:.1f}°", size=5.6, weight="bold", box=True, z=12)
    # wall notes
    txt(ax, 25.0, m.YFI + 3.3, "FRONT WALL: BEARING · carries roof, Unit B floor and both porch cantilevers · sits over beam B1", size=4.7, weight="bold", box=True, z=12)
    px, py = wall_pt("N", 25.0, -3.4)
    txt(ax, px, py, "REAR WALL: BEARING · carries roof and Unit B floor · on the stem wall (S-101)", size=4.7, weight="bold", box=True, z=12, rot=m.REAR_ANGLE)
    txt(ax, m.XEI - 0.9, 27.0, "EAST WALL: NON-BEARING", size=4.4, rot=90, box=True, z=12) if False else None
    lead(ax, (m.XE - 0.27, 16.5), (m.XE + 3.4, 12.4), "EAST WALL:\nnon-bearing gable\nwall, no openings,\non the concrete\nwall below", size=4.4, va="center")
    lead(ax, wall_pt("W", 26.0, -0.27), (2.2, 29.6), "WEST WALL:\nnon-bearing gable wall\n(carries the trimmed\nfloor truss ends)", size=4.4, ha="left", va="center") if False else None
    px, py = wall_pt("W", 23.0, -0.27)
    line(ax, [(px, py), (px - 3.6, py + 3.0)], lw=0.3, z=10)
    txt(ax, px - 3.7, py + 3.0, "WEST WALL: non-bearing\ngable wall (carries the\ntrimmed truss ends)", size=4.4, ha="right", box=True, z=12)
    txt(ax, 30.0, 23.3, "ALL INTERIOR PARTITIONS NON-BEARING\n2x4 @ 16 in. · plumbing walls 2x6", size=4.6, box=True, z=12)
    lead(ax, (m.SHAFT_X0 - 0.2, 18.0), (33.4, 19.6), "STAIR WALLS: 2x4 + 5/8 X each\nside, 1-hour, non-bearing here", size=4.4, color=ACCENT, ha="right")
    # legend
    lx, ly = 30.6, 41.6
    items = [("bear", "Bearing wall, 2x6 @ 16 in. (front and rear)"), ("sw", "Shear wall segment, full height, both storeys"),
             ("hd", "Hold-down at the end of a segment (engineer)"), ("hdr", "Header over an opening (H1, H2: schedule)"),
             ("nb", "Non-bearing exterior wall, 2x6 @ 16 in.")]
    for i, (k, s) in enumerate(items):
        y = ly - i * 0.85
        if k == "bear":
            rect(ax, lx, y - 0.2, lx + 1.6, y + 0.2, fc=BEAR, ec=BG_EDGE, lw=0.4, z=9)
        elif k == "nb":
            rect(ax, lx, y - 0.2, lx + 1.6, y + 0.2, fc=BG_WALL, ec=BG_EDGE, lw=0.4, z=9)
        elif k == "sw":
            line(ax, [(lx, y), (lx + 1.6, y)], lw=2.6, color=ACCENT, z=9)
        elif k == "hd":
            rect(ax, lx + 0.56, y - 0.24, lx + 1.04, y + 0.24, fc=INK, ec=INK, z=9)
        else:
            line(ax, [(lx, y), (lx + 1.6, y)], lw=2.4, color=STEEL, z=9)
        txt(ax, lx + 2.1, y, s, size=4.7, ha="left")
    porch_plan(fig, bg, PLAN_L + 0.1, 0.5)
    # ---- strip
    y = SHEET_H - MARGIN - 0.3
    y = strip_head(bg, y, "Shear wall segments (preliminary)")
    y = table(bg, STRIP_X, y, [0.52, 0.48, 0.55, 0.42, STRIP_W - 1.97], srows, fs=4.9, rh=0.152)
    y -= 0.07
    y = strip_lines(bg, y, [
        f"h = {ftin(WALL_H_B)} framed wall height. Lengths are between the",
        "edges of the openings in the model, measured along",
        "the wall. Full: h/L 2.0 or less. Reduced: up to 3.5.",
        "The east wall and the garage-level walls on three",
        "sides (concrete) are the stiff lines; the front is not.",
    ], fs=5.4)
    y -= 0.08
    y = strip_head(bg, y, "Header schedule (preliminary, by width)")
    y = table(bg, STRIP_X, y, [0.27, 0.9, 0.33, 1.14, STRIP_W - 2.64], hrows, fs=4.3, rh=0.152)
    y -= 0.07
    y = strip_lines(bg, y, [
        "Unit A headers carry the Unit B floor and porch; the",
        "roof comes down the trimmers beside the opening",
        "above (openings stack). Unit B headers carry the roof.",
        "Front-wall trimmers land on the trusses over B1.",
    ], fs=5.4)
    y -= 0.08
    y = strip_head(bg, y, "Corners that are not square")
    y = strip_lines(bg, y, [
        f"Inside angles: SW {ang[0]:.1f}°, SE {ang[1]:.1f}°, NE {ang[2]:.1f}°, NW {ang[3]:.1f}°.",
        f"The rear wall runs {abs(m.REAR_ANGLE):.1f}° off the street line; the west",
        f"wall leans {math.degrees(WEST_LEAN):.1f}° off square.",
        "Snap the four wall lines on the deck from the model",
        "corners, then build each wall straight on its line.",
        f"Plates: at each skew corner one wall runs through; cut",
        f"the other wall's plates to the corner angle (rear wall",
        f"ends {abs(m.REAR_ANGLE):.1f}° off square, west wall ends {math.degrees(WEST_LEAN):.1f}°); lap the",
        "double top plates over the joint. Corner studs: rip",
        "one stud to the bevel so sheathing and drywall both",
        "have nailing. Studs stay plumb and square to the plate.",
    ], fs=5.4)
    y -= 0.08
    y = strip_head(bg, y, "Hold-downs and straps")
    y = strip_lines(bg, y, [
        "Unit B to Unit A: strap studs across the 24 in. floor at",
        "each segment end. Unit A to structure: front wall to B1",
        "(welded tab) or to the concrete return and lobby wall;",
        "east and west walls to the concrete walls; rear wall",
        "to the stem wall. Sizes by the engineer.",
    ], fs=5.4)
    y -= 0.08
    y = strip_head(bg, y, "Porches: no posts")
    y = strip_lines(bg, y, [
        "Both porches hang on the 4'-0\" truss cantilevers.",
        "No posts between the porches and none down to the",
        "apron. Guard 36 in. min. above the deck, 4x4 PT posts",
        "through-bolted to the doubled rim with blocking, for",
        "200 lb at the top any way. Details: A-402, S-301.",
    ], fs=5.4)
    save(fig, "S-204", pdf)


# ----------------------------------------------------------------------------
# S-301  Structural sections and details
# ----------------------------------------------------------------------------
XS = 15.0                                   # station of the section (ft east of the SW lot corner)
PORCH_STEP = 3.5 * IN                       # truss top chord drops this much outside the wall line (prelim., A-402)
DECK_T = 1.0 * IN                           # 5/4 decking
FRAME = "#d6c39a"                           # framed wall in section
STONE = "#e3ded3"
W14 = dict(d=m.B1_DEPTH, bf=6.75 * IN, tf=0.455 * IN, tw=0.285 * IN)      # W14x34 catalogue size


def i_beam(ax, yc, ztop, z=8, color=STEEL):
    d, bf, tf, tw = W14["d"], W14["bf"], W14["tf"], W14["tw"]
    for a, b, c, e in ((yc - bf / 2, ztop - tf, yc + bf / 2, ztop), (yc - bf / 2, ztop - d, yc + bf / 2, ztop - d + tf),
                       (yc - tw / 2, ztop - d + tf, yc + tw / 2, ztop - tf)):
        rect(ax, a, b, c, e, fc=color, ec=color, lw=0.4, z=z)


def bubble(ax, y, z, n, r=1.7):
    ax.add_patch(plt.Circle((y, z), r, fc="none", ec=ACCENT, lw=0.8, ls=(0, (4, 2)), zorder=13))
    a = math.radians(40)
    cx, cy = y + (r + 0.75) * math.cos(a), z + (r + 0.75) * math.sin(a)
    ax.add_patch(plt.Circle((cx, cy), 0.75, fc=PAPER, ec=ACCENT, lw=0.8, zorder=14))
    txt(ax, cx, cy, str(n), size=5.6, color=ACCENT, weight="bold", z=15)


def roof_top(y, yr):
    return min(EL_HEEL + (y - m.YF) * P, EL_HEEL + (yr - y) * P)


def detail_title(bg, x, y, n, s, scale="1/2\" = 1'-0\""):
    bg.add_patch(plt.Circle((x + 0.11, y + 0.05), 0.11, fc=PAPER, ec=ACCENT, lw=0.9))
    bg.text(x + 0.11, y + 0.045, str(n), fontsize=6.6, fontweight="bold", color=ACCENT, ha="center", va="center")
    bg.text(x + 0.3, y + 0.05, s.upper(), fontsize=6.6, fontweight="bold", va="center")
    bg.text(x + 0.3, y - 0.1, scale, fontsize=5.0, color=GREY, va="center")


def section_main(fig, bg):
    yr, yri = m.yr_o(XS), m.yr_i(XS)
    tS = 8 * IN / CR                                   # stem wall as cut by the section (skew)
    ZB, ZT = 911.3, 951.3
    ax = plan_axes(fig, 0.5, 2.95, (0.0, 46.0), (ZB, ZT), FPI)
    g_rear = elev(XS, yr)
    stem_top = g_rear + 8 * IN
    y_td = m.YF - 0.6

    def apron(y):
        return m.EL_GAR + (street_el(XS) - m.EL_GAR) * max(0.0, y_td - y) / (y_td - PAVE_N)

    # ---- ground
    ys = list(np.arange(yr, 46.01, 0.5))
    soil = [(0, ZB), (0, apron(0) - 1.0), (m.YF, m.EL_GAR - 1.0), (m.Y_GR_O, m.EL_GAR - 1.0), (m.Y_GR_O, m.EL_A - 0.75), (yr, m.EL_A - 0.75)]
    soil += [(y, elev(XS, y)) for y in ys] + [(46, ZB)]
    poly(ax, soil, fc=SOIL, ec="none", z=1)
    line(ax, [(y, elev(XS, y)) for y in ys], lw=0.9, color=EARTH, z=3)
    ex = [(y, elev(XS, y)) for y in np.arange(0, yr + 0.3, 0.5)]
    line(ax, ex, lw=0.8, color=EARTH, ls=(0, (5, 3)), z=7.5)
    # stone layers
    poly(ax, [(0, apron(0) - 1.0), (m.YF, m.EL_GAR - 1.0), (m.Y_GR_I, m.EL_GAR - 1.0), (m.Y_GR_I, m.EL_GAR - 0.5), (m.YF, m.EL_GAR - 0.5), (0, apron(0) - 0.5)],
         fc=STONE, ec="none", z=2, hatch="...")
    rect(ax, m.Y_GR_O, m.EL_A - 0.75, yr - tS, m.EL_A - 5 * IN, fc=STONE, ec="none", z=2, hatch="...")
    # ---- concrete
    rect(ax, m.Y_GR_I - 1.5, m.EL_FTG_TOP - m.FTG_T, m.Y_GR_O + 1.5, m.EL_FTG_TOP, fc=CONC_F, ec=INK, lw=0.7, z=4)          # retaining-wall footing
    poly(ax, [(m.Y_GR_I, m.EL_FTG_TOP), (m.Y_GR_O, m.EL_FTG_TOP), (m.Y_GR_O, m.EL_A - 5 * IN), (m.Y_GR_I + BRG, m.EL_A - 5 * IN),
              (m.Y_GR_I + BRG, EL_BRG_A), (m.Y_GR_I, EL_BRG_A)], fc=CONC_F, ec=INK, lw=0.8, z=5)                             # wall + upstand
    rect(ax, m.YF - 0.0, m.EL_GAR - 0.5, m.Y_GR_I, m.EL_GAR, fc=CONC_F, ec=INK, lw=0.6, z=4)                                 # garage slab
    poly(ax, [(0, apron(0) - 0.5), (0, apron(0)), (y_td, m.EL_GAR), (m.YF, m.EL_GAR), (m.YF, m.EL_GAR - 0.5)], fc="#d0d4d9", ec=INK, lw=0.5, z=4)   # apron
    rect(ax, y_td - 0.25, m.EL_GAR - 0.6, y_td + 0.25, m.EL_GAR, fc=PAPER, ec=BLUE, lw=0.9, z=6)                             # trench drain
    rect(ax, m.Y_GR_I + BRG, m.EL_A - 5 * IN, yr - tS, m.EL_A, fc=CONC_F, ec=INK, lw=0.6, z=6)                               # slab on grade
    line(ax, [(m.Y_GR_O, m.EL_A - 5 * IN - 0.06), (yr - tS, m.EL_A - 5 * IN - 0.06)], lw=1.2, color="#d9607a", z=6)          # R-10 under the slab
    ft_top = m.EL_A - 1.5
    rect(ax, yr - tS / 2 - 10 * IN / CR, ft_top - 10 * IN, yr - tS / 2 + 10 * IN / CR, ft_top, fc=CONC_F, ec=INK, lw=0.6, z=4)   # stem-wall footing
    rect(ax, yr - tS, ft_top, yr, stem_top, fc=CONC_F, ec=INK, lw=0.8, z=5)                                                  # stem wall
    line(ax, [(m.Y_GR_O + 0.07, m.EL_FTG_TOP), (m.Y_GR_O + 0.07, m.EL_A - 0.8)], lw=1.2, color=BLUE, z=6)                    # membrane + drainage board
    ax.add_patch(plt.Circle((m.Y_GR_O + 0.75, m.EL_FTG_TOP + 0.3), 0.22, fc=PAPER, ec=BLUE, lw=1.0, zorder=7))               # French drain
    # ---- things beyond (west of the section) and the post (east of it)
    rect(ax, m.YF, m.EL_GAR, m.YF + m.CONC, EL_BRG_A, fc="#eceef1", ec=GREY, lw=0.5, z=3.5)
    rect(ax, m.B1_Y - 0.25, m.EL_GAR, m.B1_Y + 0.25, m.EL_B1_TOP - m.B1_DEPTH, fc="none", ec=STEEL, lw=0.7, ls=(0, (3, 2)), z=7)
    i_beam(ax, m.B1_Y, m.EL_B1_TOP)
    # ---- Unit A floor (20 in. trusses) and porch
    truss_band(ax, m.YF, YN_A, EL_BRG_A, EL_TOP_A, panel=2.0)
    truss_band(ax, YS_P + 2 * RIM, m.YF, EL_BRG_A, EL_TOP_A - PORCH_STEP, panel=2.0)
    rect(ax, m.B1_Y + 0.3, EL_BRG_A + 1.5 * IN, m.Y_GR_I, EL_BRG_A + 11 * IN, fc=INSUL, ec="none", z=5.9, alpha=0.9)
    rect(ax, m.YF, EL_TOP_A, m.Y_GR_I + BRG, m.EL_A, fc=WOODF, ec=INK, lw=0.4, z=7)
    rect(ax, m.B1_Y + 0.3, EL_BRG_A - 0.625 * IN, m.Y_GR_I, EL_BRG_A, fc="#dfe2e6", ec=INK, lw=0.3, z=7)
    for el_top, el_fl in ((EL_TOP_A, m.EL_A), (EL_TOP_B, m.EL_B)):
        dk = el_top - PORCH_STEP + DECK_T
        rect(ax, YS_P, el_top - PORCH_STEP - 0.9, YS_P + 2 * RIM, el_top - PORCH_STEP, fc=WOODF, ec=TR, lw=0.4, z=7)            # doubled rim
        rect(ax, YS_P - 0.08, dk - DECK_T, m.YF, dk, fc="#c9b28a", ec=INK, lw=0.3, z=7)                                         # decking
        rect(ax, YS_P - 0.29, dk - 1.0, YS_P, dk + 3.0, fc=PAPER, ec=INK, lw=0.6, z=8)                                          # guard post
        for zz in (dk + 3.0 - 0.08, dk + 0.3):
            line(ax, [(YS_P, zz), (m.YF, zz)], lw=0.6, color=GREY, z=6)
        for yy in np.arange(YS_P + 0.4, m.YF - 0.1, 0.4):
            line(ax, [(yy, dk + 0.3), (yy, dk + 3.0 - 0.08)], lw=0.2, color=LIGHT, z=5.5)
    # ---- Unit A walls
    top_a = EL_BRG_B
    rect(ax, m.YF, m.EL_A, m.YFI, top_a, fc=FRAME, ec=INK, lw=0.6, z=6)
    rect(ax, yri, stem_top, yr, top_a, fc=FRAME, ec=INK, lw=0.6, z=6)
    for (a, b) in ((m.Y1, m.Y2), (m.Y3, m.Y4)):
        rect(ax, a, m.EL_A, b, m.EL_A + m.CLG_A, fc="#eceef1", ec=GREY, lw=0.4, z=5)
        rect(ax, a, m.EL_B, b, m.EL_B + m.CLG_B, fc="#eceef1", ec=GREY, lw=0.4, z=5)
    # ---- Unit B floor (24 in. trusses)
    truss_band(ax, m.YF, yr - RIM / CR, EL_BRG_B, EL_TOP_B, panel=2.4)
    truss_band(ax, YS_P + 2 * RIM, m.YF, EL_BRG_B, EL_TOP_B - PORCH_STEP, panel=2.0)
    rect(ax, m.YF, EL_TOP_B, yr, m.EL_B, fc=WOODF, ec=INK, lw=0.4, z=7)
    rect(ax, m.YFI, EL_BRG_B - 1.25 * IN, yri, EL_BRG_B, fc="#f0b9b3", ec=ACCENT, lw=0.4, z=7)                                 # rated ceiling membrane
    # ---- Unit B walls and roof
    rect(ax, m.YF, m.EL_B, m.YFI, m.EL_PLATE, fc=FRAME, ec=INK, lw=0.6, z=6)
    rect(ax, yri, m.EL_B, yr, m.EL_PLATE, fc=FRAME, ec=INK, lw=0.6, z=6)
    rect(ax, m.YFI, m.EL_B + m.CLG_B, yri, m.EL_PLATE, fc="#dfe2e6", ec=INK, lw=0.3, z=6)
    rect(ax, m.YFI, m.EL_PLATE + 0.29, yri, m.EL_PLATE + 1.25, fc=INSUL, ec="none", z=4, alpha=0.9)
    ye_r = yr + OH_REAR / CR
    yrd = m.ridge_y(XS)
    top = [(EAVE_F, EL_EAVE_F), (yrd, m.ridge_el(XS)), (ye_r, EL_EAVE_R)]
    ch = 0.31
    poly(ax, top + [(ye_r, EL_EAVE_R - ch), (yrd, m.ridge_el(XS) - ch), (EAVE_F, EL_EAVE_F - ch)], fc=WOODF, ec=TR, lw=0.5, z=8)
    rect(ax, m.YF, m.EL_PLATE, yr, m.EL_PLATE + 0.29, fc=WOODF, ec=TR, lw=0.5, z=8)
    L = yr - m.YF
    for (yb, yt) in ((1 / 3, 1 / 4), (1 / 3, 1 / 2), (2 / 3, 1 / 2), (2 / 3, 3 / 4), (1 / 6, 1 / 8), (1 / 6, 1 / 4), (5 / 6, 7 / 8), (5 / 6, 3 / 4)):
        ya, yb_ = m.YF + yb * L, m.YF + yt * L
        line(ax, [(ya, m.EL_PLATE + 0.29), (yb_, roof_top(yb_, yr) - ch)], lw=0.6, color=TR, z=7.5)
    for yy in (m.YF + 0.15, yr - 0.15):
        line(ax, [(yy, m.EL_PLATE + 0.29), (yy, roof_top(yy, yr) - ch)], lw=1.4, color=TR, z=7.5)
    line(ax, [(a, b + 0.09) for a, b in top], lw=1.3, color=INK, z=9)                                                          # sheathing + shingles
    sof_f, sof_r = EL_EAVE_F - 0.62, EL_EAVE_R - 0.62
    line(ax, [(EAVE_F, EL_EAVE_F + 0.09), (EAVE_F, sof_f), (m.YF, sof_f)], lw=0.9, color=INK, z=9)
    line(ax, [(ye_r, EL_EAVE_R + 0.09), (ye_r, sof_r), (yr, sof_r)], lw=0.9, color=ACCENT, z=9)
    # ---- lot lines
    yl = rear_y(XS)
    line(ax, [(yl, 926.5), (yl, 936.5)], lw=0.9, color=ACCENT, ls=(0, (9, 2.5, 1.5, 2.5)), z=8)
    txt(ax, yl - 0.45, 934.4, "REAR LOT LINE", size=4.4, color=ACCENT, rot=90)
    dimb(ax, (yr, 930.3), (yl, 930.3), 0, ftin(yl - yr), size=4.4, ext=False, color=ACCENT)
    # ---- room names
    for y_, z_, s in ((20.0, 919.3, "OPEN GARAGE"), (15.8, 929.6, "UNIT A · BEDROOM 1"), (24.1, 929.0, "BATH 1"), (30.6, 931.3, "BEDROOM 2"),
                      (15.8, 939.6, "UNIT B · BEDROOM 1"), (24.1, 939.0, "BATH 1"), (33.0, 939.6, "BEDROOM 2")):
        txt(ax, y_, z_, s, size=5.0 if "GARAGE" in s or "UNIT" in s else 4.4, color=GREY, weight="bold")
    # ---- level lines at the left
    for z_, s in ((m.EL_PLATE, "TOP OF B PLATES"), (m.EL_B, "UNIT B FLOOR"), (EL_BRG_B, "TOP OF A PLATES"), (m.EL_A, "UNIT A FLOOR"),
                  (EL_BRG_A, "TOP OF B1 + LEDGES"), (m.EL_B1_TOP - m.B1_DEPTH, "UNDERSIDE OF B1")):
        line(ax, [(0.2, z_), (YS_P - 0.5, z_)], lw=0.35, color=INK, z=10)
        txt(ax, 0.25, z_ + 0.42, f"EL {z_:.2f}  {s}", size=4.3, ha="left", z=12)
    lead(ax, (13.0, m.EL_GAR), (12.6, 915.55), f"EL {m.EL_GAR:.2f}  GARAGE SLAB, 6 in. on 6 in. stone, slopes 1/8 in./ft to the trench drain (S-103)", size=4.4, dot=False)
    lead(ax, (m.Y_GR_O + 1.3, m.EL_FTG_TOP), (33.2, 914.6), f"EL {m.EL_FTG_TOP:.2f}  TOP OF FOOTING\n{ftin(m.FTG_W)} x {round(m.FTG_T * 12)} in. (S-101)", size=4.4)
    lead(ax, (m.Y_GR_O + 0.75, m.EL_FTG_TOP + 0.3), (33.2, 916.9), "4 in. FRENCH DRAIN in stone,\ngravity to the street, no sump (S-102)", size=4.4, color=BLUE)
    lead(ax, (m.Y_GR_O + 0.07, 919.5), (33.2, 919.6), "MEMBRANE + DRAINAGE BOARD,\nbackfill in lifts only after the\nUnit A floor is on (S-102)", size=4.4, color=BLUE)
    lead(ax, (m.Y_GR_I + 0.5, 921.3), (27.9, 921.6), "12 in. CONCRETE\nRETAINING WALL\n(S-102)", size=4.4, ha="right")
    lead(ax, (m.B1_Y + 0.3, m.EL_B1_TOP - 0.6), (12.6, 921.9), "B1  W14x34 (prelim.)", size=4.6, color=STEEL, weight="bold")
    lead(ax, (m.B1_Y + 0.25, 917.4), (12.6, 917.5), f"HSS 6x6 POST: {ftin(m.COL_X[1] - XS)} east of this\nsection, dashed for reference (S-104)", size=4.3, color=STEEL, dot=False)
    lead(ax, (m.YF + 0.5, 920.4), (12.6, 920.3), "CONCRETE RETURN BEYOND\n(west end of B1 sits on it)", size=4.3, color=GREY, dot=False)
    txt(ax, 20.2, 922.85, f"20 in. FLOOR TRUSSES FT-A1 @ 16 in. · span {ftin((m.Y_GR_I + BRG / 2) - m.B1_Y)} · R-30 + 5/8 in. Type X below", size=4.5, weight="bold", box=True, z=12)
    txt(ax, 22.6, 932.5, f"24 in. FLOOR TRUSSES FT-B2 @ 12 in. here · span {ftin(span_cc(XS))} · 1-hour floor / ceiling (A-501)", size=4.5, weight="bold", box=True, z=12)
    txt(ax, yrd, 945.75, f"ROOF TRUSS T15 · span {ftin(depth_oo(XS))} · 4:12 · 12 in. raised heel · 24 in. o.c. · R-49 on the ceiling", size=4.5, weight="bold", box=True, z=12)
    lead(ax, (yrd, m.ridge_el(XS) + 0.1), (yrd + 1.5, 950.6), f"RIDGE EL {m.ridge_el(XS):.2f} at this section ({m.ridge_el(m.XE):.2f} east end, {m.ridge_el(RIDGE_W[0]):.2f} west end)", size=4.5, weight="bold")
    lead(ax, (EAVE_F + 0.6, EL_EAVE_F + 0.25), (0.3, 947.0), f"FRONT EAVE EL {EL_EAVE_F:.2f}:\n4'-0\" cantilevered tails,\nlevel soffit return", size=4.4, va="center")
    lead(ax, (ye_r, EL_EAVE_R), (ye_r + 0.4, 948.3), f"REAR EAVE EL {EL_EAVE_R:.2f},\n12 in., 1-hour soffit", size=4.4, color=ACCENT)
    lead(ax, (yr - tS + 0.05, stem_top - 0.6), (38.2, 929.4), f"8 in. CONCRETE STEM WALL up to 8 in.\nabove grade (top EL {stem_top:.1f} here); the\n2x6 wall starts on top of it. Footing\n20 x 10 in., 36 in. min. below grade (S-101)", size=4.3, ha="right")
    lead(ax, (32.6, m.EL_A - 0.2), (31.0, 926.75), "5 in. SLAB ON GRADE on R-10, vapour barrier, 4 in. stone (S-103)", size=4.3)
    txt(ax, 0.3, 919.0, "EXISTING GRADE (LiDAR),\ndashed: cut away for the\napron and garage (C-104)", size=4.2, color=EARTH, ha="left", va="top")
    txt(ax, 3.4, 913.7, "APRON (C-107)", size=4.2, ha="center", box=True)
    lead(ax, (y_td, m.EL_GAR + 0.05), (0.3, 916.5), "TRENCH DRAIN (S-103)", size=4.2, color=BLUE, dot=False)
    txt(ax, 42.3, elev(XS, 42.3) - 3.4, f"EXISTING GRADE\nEL {g_rear:.1f} at the wall;\nfinished grade and\nswale: C-105", size=4.2, color=EARTH)
    lead(ax, (YS_P - 0.15, m.EL_A + 2.2), (0.3, 928.9), "36 in. GUARD,\nposts bolted to\nthe doubled rim", size=4.3, va="center")
    txt(ax, (YS_P + m.YF) / 2, m.EL_A + 4.6, "PORCH A", size=4.2, color=GREY)
    txt(ax, (YS_P + m.YF) / 2, m.EL_B + 4.6, "PORCH B", size=4.2, color=GREY)
    txt(ax, 3.0, 937.6, "NO POSTS between\nthe porches or down\nto the apron", size=4.3, color=ACCENT)
    # ---- dimensions
    yv = 12.1
    dimb(ax, (yv, m.EL_GAR), (yv, m.EL_GAR + m.CLG_GAR), 0, f"{ftin8(m.CLG_GAR)} CLEAR", size=4.4, ext=False, side=-1)
    dimb(ax, (yv, m.EL_A), (yv, m.EL_A + m.CLG_A), 0, f"{ftin8(m.CLG_A)}", size=4.4, ext=False, side=-1)
    dimb(ax, (yv, m.EL_B), (yv, m.EL_B + m.CLG_B), 0, f"{ftin8(m.CLG_B)}", size=4.4, ext=False, side=-1)
    dimb(ax, (9.2, m.EL_GAR), (9.2, m.EL_B1_TOP - m.B1_DEPTH), 0, f"{ftin8(m.OPEN_CLEAR_H)} UNDER B1", size=4.3, ext=False, side=1)
    yv2 = 45.55
    dimb(ax, (yv2, m.EL_GAR), (yv2, m.EL_A), 0, ftin(m.EL_A - m.EL_GAR), size=4.4, ext=False, side=1)
    dimb(ax, (yv2, m.EL_A), (yv2, m.EL_B), 0, ftin(m.EL_B - m.EL_A), size=4.4, ext=False, side=1)
    dimb(ax, (yv2, m.EL_B), (yv2, m.EL_PLATE), 0, ftin8(m.EL_PLATE - m.EL_B), size=4.4, ext=False, side=1)
    dimb(ax, (yv2, m.EL_PLATE), (yv2, m.ridge_el(XS)), 0, ftin8(m.ridge_el(XS) - m.EL_PLATE), size=4.4, ext=False, side=1)
    for z_ in (m.EL_GAR, m.EL_A, m.EL_B, m.EL_PLATE, m.ridge_el(XS)):
        line(ax, [(yv2 - 0.8, z_), (yv2 + 0.3, z_)], lw=0.3, z=11)
    zd = 911.85
    dimb(ax, (YS_P, zd), (m.YF, zd), 0, "4'-0\"", size=4.4, ext=False)
    dimb(ax, (m.YF, zd), (m.Y_GR_O, zd), 0, f"{ftin(m.Y_GR_O - m.YF)} GARAGE, OUT TO OUT", size=4.4, ext=False)
    dimb(ax, (m.Y_GR_O, zd), (yr, zd), 0, f"{ftin(yr - m.Y_GR_O)} SLAB ON GRADE", size=4.4, ext=False)
    # ---- detail bubbles
    bubble(ax, m.Y_GR_I + 0.5, m.EL_A - 0.9, 1, r=1.5)
    bubble(ax, m.B1_Y - 0.6, m.EL_A - 1.0, 2, r=1.6)
    bubble(ax, yr - 0.3, m.EL_B - 1.0, 3, r=1.6)
    bubble(ax, yr + 0.2, EL_HEEL - 0.4, 4, r=1.5)
    # title
    txt(ax, 10.6, 950.6, "", size=4)
    bg.add_patch(plt.Circle((0.63, 10.47), 0.12, fc=PAPER, ec=INK, lw=0.9))
    bg.text(0.63, 10.465, "A", fontsize=7.4, fontweight="bold", ha="center", va="center")
    bg.text(0.84, 10.47, f"NORTH-SOUTH STRUCTURAL SECTION {ftin(XS)} EAST OF THE SW LOT CORNER, LOOKING WEST", fontsize=7.6, fontweight="bold", va="center")
    bg.text(0.84, 10.31, "3/16\" = 1'-0\" · street on the left · cuts floor truss FT-A1, FT-B2 and roof truss T15 · numbered circles = details", fontsize=5.4, color=GREY, va="center")
    return ax


def detail_1(fig, bg, left, bottom, width):
    """Truss bearing on the garage rear retaining wall, with the slab-on-grade edge on the wall upstand."""
    f = 2.0
    vy = (m.Y_GR_I - 8.2, m.Y_GR_I - 8.2 + width * f)
    vz = (922.75, 926.75)
    ax = plan_axes(fig, left, bottom, vy, vz, f)
    yi, yo = m.Y_GR_I, m.Y_GR_O
    yl, yrr = yi - 2.6, yo + 2.7                      # drawn extent
    us = yi + BRG                                     # south face of the upstand
    slab_b = m.EL_A - 5 * IN
    rect(ax, yo, vz[0], yrr, slab_b - 4 * IN, fc=SOIL, ec="none", z=1)
    rect(ax, yo, slab_b - 4 * IN, yrr, slab_b, fc=STONE, ec="none", z=2, hatch="...")
    poly(ax, [(yi, vz[0]), (yo, vz[0]), (yo, slab_b), (us, slab_b), (us, EL_BRG_A), (yi, EL_BRG_A)], fc=CONC_F, ec=INK, lw=0.8, z=5)
    rect(ax, us, slab_b, yrr, m.EL_A, fc="#c9ced4", ec=INK, lw=0.7, z=6)
    line(ax, [(yo, slab_b - 0.05), (yrr, slab_b - 0.05)], lw=1.6, color="#d9607a", z=6.5)
    line(ax, [(yo + 0.06, vz[0]), (yo + 0.06, slab_b - 0.1)], lw=1.4, color=BLUE, z=6.5)
    line(ax, [(us + 0.25, EL_BRG_A - 0.7), (us + 0.25, slab_b + 0.22), (us + 1.6, slab_b + 0.22)], lw=1.0, color=ACCENT, z=7)          # dowel
    truss_band(ax, yl, us, EL_BRG_A, EL_TOP_A, panel=1.5, lw=0.5, z=6)
    rect(ax, yl, EL_BRG_A + 1.5 * IN, yi, EL_BRG_A + 11 * IN, fc=INSUL, ec="none", z=5.5, hatch="////")
    rect(ax, yl, EL_TOP_A, us, m.EL_A, fc=WOODF, ec=INK, lw=0.5, z=7)
    rect(ax, yl, EL_BRG_A - 0.625 * IN, yi, EL_BRG_A, fc="#dfe2e6", ec=INK, lw=0.4, z=7)
    line(ax, [(yi + 0.02, EL_BRG_A + 0.015), (us - 0.02, EL_BRG_A + 0.015)], lw=1.6, color="#5d6b3a", z=8)                             # sill / bearing
    line(ax, [(yi + 0.25, EL_BRG_A - 0.55), (yi + 0.25, EL_BRG_A + 0.22)], lw=1.2, color=ACCENT, z=8.5)                               # anchor bolt
    line(ax, [(yi + 0.1, EL_BRG_A + 0.05), (yi + 0.1, EL_BRG_A + 0.75)], lw=1.6, color=ACCENT, z=8.5)                                 # strap
    line(ax, [(yl, vz[0] + 0.3), (yl, vz[1] - 0.2)], lw=0.4, color=GREY, ls=(0, (6, 2, 1, 2)), z=3)
    line(ax, [(yrr, vz[0] + 0.3), (yrr, vz[1] - 0.2)], lw=0.4, color=GREY, ls=(0, (6, 2, 1, 2)), z=3)
    xl = yl - 0.35
    for z_, s, c in ((m.EL_A + 0.0, f"EL {m.EL_A:.2f}: top of 3/4 in. T&G subfloor = top of slab", INK),
                     (EL_BRG_A + 1.28, "20 in. FLOOR TRUSS FT-A1 @ 16 in. o.c. End blocking between trusses", TR),
                     (EL_BRG_A + 0.72, "TRUSS STRAPPED TO THE SILL (red): the floor props the wall top", ACCENT),
                     (EL_BRG_A + 0.16, f"EL {EL_BRG_A:.2f}: 5 1/2 in. BEARING LEDGE, PT 2x6 sill, 1/2 in. anchor bolts", INK),
                     (EL_BRG_A - 0.4, "R-30 in the bottom of the trusses + 5/8 in. Type X garage ceiling", INK)):
        txt(ax, xl, z_, s, size=4.4, color=c, ha="right")
        line(ax, [(xl + 0.08, z_), (yl - 0.02 if z_ > EL_BRG_A else yi - 0.3, z_)], lw=0.3, color=c, z=9)
    xr_ = yrr + 0.35
    for z_, s, c, px in ((m.EL_A - 0.2, "5 in. SLAB ON GRADE (S-103) runs over the upstand to the subfloor edge", INK, yrr - 0.4),
                         (slab_b - 0.05 - 0.38, "R-10 + 15-mil vapour barrier under the slab, 4 in. stone", "#b23a56", yrr - 0.4),
                         (EL_BRG_A + 0.1, "6 1/2 in. CONCRETE UPSTAND (stem) cast with the wall: carries the slab\nedge and closes the truss space. #4 dowels at 24 in. (prelim.)", INK, us + 0.3),
                         (EL_BRG_A - 0.72, "12 in. RETAINING WALL (S-102). Membrane + drainage board (blue)", BLUE, yo + 0.1)):
        txt(ax, xr_, z_, s, size=4.4, color=c, ha="left")
        line(ax, [(xr_ - 0.08, z_), (px, z_ if px > yo + 0.2 else z_)], lw=0.3, color=c, z=9)
    dim(ax, (yi, vz[0] + 0.28), (us, vz[0] + 0.28), 0, "5 1/2\"", size=4.2, ext=False, side=-1)
    dim(ax, (us, vz[0] + 0.28), (yo, vz[0] + 0.28), 0, "6 1/2\"", size=4.2, ext=False, side=-1)
    detail_title(bg, left, bottom + (vz[1] - vz[0]) / f + 0.08, 1, "Truss bearing on the garage rear wall, slab-on-grade edge on the upstand")
    return ax


def detail_2(fig, bg, left, bottom, width, height):
    """Trusses over beam B1 with the porch cantilever."""
    f = 2.0
    vy = (4.75, 4.75 + width * f)
    vz = (921.75, 921.75 + height * f)
    ax = plan_axes(fig, left, bottom, vy, vz, f)
    yend = vy[1] - 0.5
    tail_top = EL_TOP_A - PORCH_STEP
    dk = tail_top + DECK_T
    i_beam(ax, m.B1_Y, m.EL_B1_TOP)
    truss_band(ax, m.YF, yend, EL_BRG_A, EL_TOP_A, panel=1.5, lw=0.5)
    truss_band(ax, YS_P + 2 * RIM, m.YF, EL_BRG_A, tail_top, panel=1.3, lw=0.5)
    rect(ax, YS_P, EL_BRG_A, YS_P + RIM, tail_top, fc=WOODF, ec=TR, lw=0.6, z=7)
    rect(ax, YS_P + RIM, EL_BRG_A, YS_P + 2 * RIM, tail_top, fc=WOODF, ec=TR, lw=0.6, z=7)
    rect(ax, YS_P - 0.1, tail_top, m.YF, dk, fc="#c9b28a", ec=INK, lw=0.4, z=7)
    for yy in np.arange(YS_P - 0.1 + 5.625 * IN, m.YF, 5.625 * IN):
        line(ax, [(yy, tail_top), (yy, dk)], lw=0.3, z=7.5)
    rect(ax, YS_P - 3.5 * IN, EL_BRG_A + 0.15, YS_P, vz[1] - 0.25, fc=PAPER, ec=INK, lw=0.7, z=8)                      # guard post
    for zz in (EL_BRG_A + 0.45, tail_top - 0.3):
        line(ax, [(YS_P - 3.5 * IN - 0.1, zz), (YS_P + 2 * RIM + 0.1, zz)], lw=1.3, color=ACCENT, z=9)                # through-bolts
    rect(ax, m.B1_Y - 1.75 * IN, EL_BRG_A, m.B1_Y + 1.75 * IN, EL_TOP_A, fc="#efe3c6", ec=TR, lw=0.5, z=6.6)           # blocking over B1
    line(ax, [(m.B1_Y - 1.75 * IN, EL_BRG_A), (m.B1_Y + 1.75 * IN, EL_TOP_A)], lw=0.4, color=TR, z=6.7)
    line(ax, [(m.B1_Y - 1.75 * IN, EL_TOP_A), (m.B1_Y + 1.75 * IN, EL_BRG_A)], lw=0.4, color=TR, z=6.7)
    rect(ax, m.YF, EL_TOP_A, yend, m.EL_A, fc=WOODF, ec=INK, lw=0.5, z=7)
    rect(ax, m.YF, m.EL_A, m.YFI, vz[1] - 0.25, fc=FRAME, ec=INK, lw=0.6, z=6)
    line(ax, [(m.YF, m.EL_A + 1.5 * IN), (m.YFI, m.EL_A + 1.5 * IN)], lw=0.4, z=7)
    rect(ax, m.B1_Y + W14["bf"] / 2, EL_BRG_A + 1.5 * IN, yend, EL_BRG_A + 11 * IN, fc=INSUL, ec="none", z=5.5, hatch="////")
    rect(ax, m.B1_Y + W14["bf"] / 2, EL_BRG_A - 0.625 * IN, yend, EL_BRG_A, fc="#dfe2e6", ec=INK, lw=0.4, z=7)
    line(ax, [(m.B1_Y - 0.2, EL_BRG_A + 0.02), (m.B1_Y - 0.2, EL_BRG_A + 0.6)], lw=1.6, color=ACCENT, z=9)             # clip
    line(ax, [(yend, vz[0] + 0.2), (yend, vz[1] - 0.2)], lw=0.4, color=GREY, ls=(0, (6, 2, 1, 2)), z=3)
    # labels
    lead(ax, (m.B1_Y, m.EL_B1_TOP - 0.7), (11.2, 922.45), f"B1 W14x34 (prelim.)\ntop of steel EL {m.EL_B1_TOP:.2f}\ntrusses clipped to it\n(bearing: engineer)", size=4.3, color=STEEL)
    lead(ax, (m.B1_Y + 0.05, EL_BRG_A + 1.0), (11.25, 923.3), "FULL-DEPTH BLOCKING between\ntrusses over B1 (X)", size=4.3, color=TR, va="center") if False else None
    lead(ax, (12.2, EL_BRG_A + 0.9), (11.6, 923.05), "20 in. TRUSS FT-A1 runs over B1; R-30 + 5/8 X ceiling", size=4.3, color=TR, dot=False) if False else None
    txt(ax, 12.15, EL_BRG_A + 0.9, "20 in. TRUSS FT-A1", size=4.3, color=TR, box=True, z=12)
    lead(ax, (m.B1_Y + 0.1, EL_TOP_A - 0.35), (11.3, 926.6), "FULL-DEPTH BLOCKING (X)\nbetween trusses over B1", size=4.3, color=TR)
    lead(ax, (m.YF + 0.27, m.EL_A + 0.7), (11.3, 927.35), "UNIT A FRONT WALL 2x6 (bearing)\nlands on the trusses over B1", size=4.3)
    lead(ax, (8.3, dk), (6.4, 926.6), f"5/4 DECKING, deck ±{round((m.EL_A - dk) * 12 * 4) / 4:g} in.\nbelow the floor (A-402)", size=4.3, va="center")
    lead(ax, (8.3, tail_top - 0.5), (7.1, 922.9), "TRUSS TAIL: 4'-0\" cantilever,\ntop chord stepped down", size=4.3, color=TR, va="center")
    lead(ax, (YS_P + RIM, EL_BRG_A + 0.25), (5.0, 922.15), "DOUBLED RIM + blocking,\n(2) 1/2 in. through-bolts per post", size=4.3, color=ACCENT, va="center", dot=False)
    txt(ax, YS_P - 0.5, 927.2, "4x4 PT GUARD POST,\n36 in. above the deck", size=4.2, ha="right")
    dimb(ax, (YS_P, 924.55), (m.YF, 924.55), 0, "4'-0\"", size=4.3, ext=False)
    dim(ax, (m.YF, vz[0] + 0.3), (m.B1_Y, vz[0] + 0.3), 0, "6\"", size=4.2, ext=False, side=-1)
    detail_title(bg, left, bottom + height + 0.08, 2, "Trusses over beam B1, porch cantilever")
    return ax


def detail_3(fig, bg, left, bottom, width, height):
    """Unit B floor truss bearing on the Unit A rear wall, rated ceiling."""
    f = 2.0
    yr, yri = m.yr_o(XS), m.yr_i(XS)
    vy = (yr - 4.9, yr - 4.9 + width * f)
    vz = (931.6, 931.6 + height * f)
    ax = plan_axes(fig, left, bottom, vy, vz, f)
    yl = vy[0] + 0.5
    rim = RIM / CR
    rect(ax, yri, vz[0] + 0.25, yr, EL_BRG_B, fc=FRAME, ec=INK, lw=0.6, z=6)
    for k in (1, 2):
        line(ax, [(yri, EL_BRG_B - k * 1.5 * IN), (yr, EL_BRG_B - k * 1.5 * IN)], lw=0.4, z=7)
    truss_band(ax, yl, yr - rim, EL_BRG_B, EL_TOP_B, panel=1.7, lw=0.5)
    rect(ax, yr - rim, EL_BRG_B, yr, EL_TOP_B, fc=WOODF, ec=TR, lw=0.6, z=7)
    rect(ax, yl, EL_TOP_B, yr, m.EL_B, fc=WOODF, ec=INK, lw=0.5, z=7)
    rect(ax, yri, m.EL_B, yr, vz[1] - 0.25, fc=FRAME, ec=INK, lw=0.6, z=6)
    line(ax, [(yri, m.EL_B + 1.5 * IN), (yr, m.EL_B + 1.5 * IN)], lw=0.4, z=7)
    rect(ax, yl, EL_BRG_B + 1.5 * IN, yri, EL_BRG_B + 5.0 * IN, fc=INSUL, ec="none", z=5.5, hatch="////")
    rect(ax, yl, EL_BRG_B - 0.5 * IN, yri, EL_BRG_B, fc=PAPER, ec=GREY, lw=0.3, z=7)                                   # resilient channel
    rect(ax, yl, EL_BRG_B - 1.25 * IN, yri, EL_BRG_B - 0.5 * IN, fc="#f0b9b3", ec=ACCENT, lw=0.5, z=7)                 # 5/8 X
    rect(ax, yri - 0.5 * IN, vz[0] + 0.25, yri, EL_BRG_B - 1.25 * IN, fc="#dfe2e6", ec=INK, lw=0.3, z=7)
    rect(ax, yri - 0.5 * IN, m.EL_B, yri, vz[1] - 0.25, fc="#dfe2e6", ec=INK, lw=0.3, z=7)
    line(ax, [(yr + 0.04, vz[0] + 0.25), (yr + 0.04, vz[1] - 0.25)], lw=1.0, color=TR2, z=7)                           # OSB
    line(ax, [(yr + 0.1, EL_BRG_B - 1.0), (yr + 0.1, m.EL_B + 1.0)], lw=1.8, color=ACCENT, z=8)                        # strap
    line(ax, [(yl, vz[0] + 0.2), (yl, vz[1] - 0.2)], lw=0.4, color=GREY, ls=(0, (6, 2, 1, 2)), z=3)
    xr_ = yr + 0.5
    lead(ax, (yr + 0.1, m.EL_B + 0.6), (xr_, 937.0), "STRAP Unit B studs to\nUnit A studs across the\nfloor at shear-wall ends", size=4.3, color=ACCENT, va="center", dot=False)
    lead(ax, (yr - rim / 2, EL_TOP_B - 0.5), (xr_, 935.6), "1 1/4 in. RIM BOARD\nfollows the skewed wall", size=4.3, color=TR, va="center")
    lead(ax, (yr - 0.25, EL_BRG_B + 0.05), (xr_, 934.2), f"TRUSS END cut {abs(m.REAR_ANGLE):.1f}° off\nsquare, bears 5 1/2 in. on the\ndouble 2x6 top plate,\nEL {EL_BRG_B:.2f}", size=4.3, va="center")
    lead(ax, (yr - 0.25, 932.3), (xr_, 932.3), "UNIT A REAR WALL 2x6\n@ 16 in. (bearing)", size=4.3, va="center")
    txt(ax, yl + 0.1, m.EL_B + 0.9, f"EL {m.EL_B:.2f} UNIT B FLOOR\n3/4 in. T&G subfloor (+ sound mat, A-501)", size=4.3, ha="left")
    txt(ax, yl + 1.6, EL_BRG_B + 1.1, "24 in. FLOOR TRUSS", size=4.3, color=TR, box=True, z=12, ha="left")
    lead(ax, (yl + 1.2, EL_BRG_B - 0.07), (yl + 0.1, 932.55), "1-HOUR CEILING MEMBRANE (A-501): 5/8 in.\nType X on resilient channel, batts above.\nNo holes except fire-stopped pipes, ducts, boxes.", size=4.3, color=ACCENT, va="center", dot=False)
    detail_title(bg, left, bottom + height + 0.08, 3, "Unit B floor truss on the Unit A wall, rated ceiling")
    return ax


def detail_4(fig, bg, left, bottom, width, height):
    """Roof truss heel at the rear wall: raised heel, hurricane tie, 1-hour soffit."""
    f = 2.0
    yr, yri = m.yr_o(XS), m.yr_i(XS)
    vy = (yr - 4.9, yr - 4.9 + width * f)
    vz = (942.0, 942.0 + height * f)
    ax = plan_axes(fig, left, bottom, vy, vz, f)
    yl = vy[0] + 0.5
    ye = yr + OH_REAR / CR
    ch = 3.5 * IN / math.cos(math.atan(P))

    def zt(y):
        return EL_HEEL + (yr - y) * P

    rect(ax, yri, vz[0] + 0.25, yr, m.EL_PLATE, fc=FRAME, ec=INK, lw=0.6, z=6)
    for k in (1, 2):
        line(ax, [(yri, m.EL_PLATE - k * 1.5 * IN), (yr, m.EL_PLATE - k * 1.5 * IN)], lw=0.4, z=7)
    rect(ax, yl, m.EL_B + m.CLG_B, yri, m.EL_PLATE, fc="#dfe2e6", ec=INK, lw=0.4, z=7)                                 # ceiling
    rect(ax, yri - 0.5 * IN, vz[0] + 0.25, yri, m.EL_B + m.CLG_B, fc="#dfe2e6", ec=INK, lw=0.3, z=7)
    poly(ax, [(yl, m.EL_PLATE + 3.5 * IN), (yr - 3.5 * IN, m.EL_PLATE + 3.5 * IN), (yr - 3.5 * IN, zt(yr - 3.5 * IN) - ch), (yl + 0.9, m.EL_PLATE + 1.17 + 3.5 * IN),
              (yl, m.EL_PLATE + 1.17 + 3.5 * IN)], fc=INSUL, ec="none", z=4, hatch="////")
    rect(ax, yl, m.EL_PLATE, yr, m.EL_PLATE + 3.5 * IN, fc=WOODF, ec=TR, lw=0.6, z=8)                                  # bottom chord
    poly(ax, [(yl, zt(yl)), (ye, zt(ye)), (ye, zt(ye) - ch), (yl, zt(yl) - ch)], fc=WOODF, ec=TR, lw=0.6, z=8)         # top chord + tail
    rect(ax, yr - 3.5 * IN, m.EL_PLATE + 3.5 * IN, yr, zt(yr - 1.75 * IN) - ch, fc=WOODF, ec=TR, lw=0.6, z=8)          # heel post
    line(ax, [(yl, zt(yl) + 0.06), (ye + 0.12, zt(ye + 0.12) + 0.06)], lw=1.6, color=INK, z=9)                         # sheathing + shingles
    rect(ax, ye, zt(ye) - ch - 0.2, ye + 1.5 * IN, zt(ye) + 0.02, fc=WOODF, ec=TR, lw=0.6, z=8)                        # sub-fascia
    sof = zt(ye) - ch - 0.2
    rect(ax, yr + 0.05, sof - 1.1 * IN, ye + 1.5 * IN, sof, fc="#f0b9b3", ec=ACCENT, lw=0.6, z=8)                      # rated soffit
    line(ax, [(yr + 0.04, vz[0] + 0.25), (yr + 0.04, zt(yr) - ch)], lw=1.0, color=TR2, z=7)                            # wall OSB up to the roof deck
    poly(ax, [(yr - 0.02, m.EL_PLATE - 0.45), (yr + 0.09, m.EL_PLATE - 0.45), (yr + 0.09, m.EL_PLATE + 0.75), (yr - 0.02, m.EL_PLATE + 0.75)],
         fc=ACCENT, ec=ACCENT, lw=0.3, z=10)                                                                           # hurricane tie
    line(ax, [(yl, vz[0] + 0.2), (yl, vz[1] - 0.2)], lw=0.4, color=GREY, ls=(0, (6, 2, 1, 2)), z=3)
    # pitch symbol
    px, pz = yl + 1.5, zt(yl + 1.5) + 0.45
    line(ax, [(px, pz), (px + 1.5, pz), (px + 1.5, pz - 0.5), (px, pz)], lw=0.5, z=10)
    txt(ax, px + 0.75, pz + 0.2, "12", size=4.2)
    txt(ax, px + 1.72, pz - 0.25, "4", size=4.2)
    dim(ax, (yr, m.EL_PLATE), (yr, EL_HEEL), -0.95, "12\" HEEL", size=4.2, side=-1) if False else None
    xr_ = ye + 0.55
    lead(ax, (ye + 0.1, zt(ye) + 0.08), (xr_, 946.0), f"7/16 in. OSB + H-clips,\nshingles. REAR EAVE\nEL {EL_EAVE_R:.2f} (top of truss)", size=4.3, va="center")
    lead(ax, (yr + 0.09, m.EL_PLATE + 0.5), (xr_, 944.6), "HURRICANE TIE at\nevery truss, both\nwalls (red)", size=4.3, color=ACCENT, va="center", dot=False)
    lead(ax, (ye - 0.3, sof - 0.05), (xr_, 943.35), "1-HOUR SOFFIT (within 5 ft\nof the lot line): 5/8 in. Type X\nexterior gypsum + fibre-\ncement, no vents (A-501)", size=4.3, color=ACCENT, va="center", dot=False)
    lead(ax, (yr - 0.25, 942.6), (xr_, 942.35), "UNIT B REAR WALL 2x6", size=4.3, va="center")
    txt(ax, yl + 0.1, 947.6, f"ROOF TRUSS @ 24 in., 4:12 · 12 in. RAISED HEEL:\ntop of truss EL {EL_HEEL:.2f} at the outside face of the wall", size=4.3, ha="left")
    lead(ax, (yr - 0.6, m.EL_PLATE + 0.9), (yl + 0.1, 942.9), f"R-49 full depth over the plate. Heel blocking\nwith OSB up to the roof deck (shear + wind-wash).\nPlates EL {m.EL_PLATE:.2f}; ceiling EL {m.EL_B + m.CLG_B:.2f}", size=4.3, va="center", dot=False)
    dimb(ax, (yr, zt(yr) + 0.55), (ye, zt(yr) + 0.55), 0, ftin8(OH_REAR / CR).replace("1'-0", "12"), size=4.2, ext=False)
    dimb(ax, (yr - 0.75, m.EL_PLATE), (yr - 0.75, EL_HEEL), 0, "12\"", size=4.2, ext=False, side=1)
    detail_title(bg, left, bottom + height + 0.08, 4, "Roof truss heel at the rear wall, 1-hour soffit")
    return ax


def sheet_s301(pdf):
    notes = [
        ("Section A", [
            f"Cut {ftin(XS)} east of the SW lot corner,",
            "through the garage, both flats and the",
            "roof, looking west. Ground is the state",
            "LiDAR surface: the survey replaces it.",
            "At this cut the garage is 20'-0\" deep",
            f"and the flats are {ftin(depth_oo(XS))} deep: the rear",
            f"{ftin(m.yr_o(XS) - m.Y_GR_O)} of Unit A is a slab on grade.",
        ]),
        ("Load path", [
            "Roof and Unit B floor: front and rear",
            "walls only. Front wall line: down the",
            "Unit A wall to the trusses over B1, to",
            "the post, the concrete return and the",
            "lobby wall. Rear wall line: down to the",
            "stem wall (or the garage wall, east end).",
            "Unit A floor: B1 and the rear-wall ledge.",
        ]),
        ("Sequence that matters", [
            "Footings, walls, drains, garage slab,",
            "steel, Unit A floor anchored to the walls,",
            "THEN backfill, stem wall and rear slab.",
        ]),
        PRELIM,
    ]
    fig, bg = sheet("S-301", "Structural sections and details", "3/16\" and 1/2\" = 1'-0\"", notes)
    section_main(fig, bg)
    detail_1(fig, bg, 0.5, 0.5, 8.62)
    xr_ = 9.33
    w = SHEET_W - MARGIN - TB_W - 0.1 - xr_
    detail_2(fig, bg, xr_, 7.3, w, 3.0)
    detail_3(fig, bg, xr_, 3.9, w, 3.0)
    detail_4(fig, bg, xr_, 0.5, w, 3.0)
    save(fig, "S-301", pdf)


SHEETS = [("S-201", sheet_s201), ("S-202", sheet_s202), ("S-203", sheet_s203), ("S-204", sheet_s204), ("S-301", sheet_s301)]
