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
BRG = 5.5 * IN                                # truss bearing ledge on the concrete walls (2x6 PT sill)
RIM = 1.5 * IN
YS_P = m.PORCH[1]                             # outer edge of the porch cantilever
YN_A = m.Y_GR_I + BRG                         # north end of the Unit A trusses (on the ledge)
EL_BRG_A = m.EL_B1_TOP                        # underside of the Unit A trusses = top of B1 = top of ledge
EL_TOP_A = m.EL_A - 0.75 * IN                 # top of the Unit A trusses
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
    return new_sheet(number, title, scale_txt, notes)


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
            f"north-south, bear at EL {EL_BRG_A:.2f} on steel",
            "beam B1 and on a 5 1/2 in. ledge on the",
            "concrete rear wall, and cantilever 4'-0\"",
            "past the front wall to carry the porch.",
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
                   f"Top of subfloor EL {m.EL_A:.1f} · truss bearing EL {EL_BRG_A:.2f} · garage walls below grey · trusses brown · steel blue · preliminary")
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
    txt(ax, xc, m.B1_Y + 1.05, f"B1  W14x34 (PRELIM.) DROPPED BELOW THE TRUSSES · TOP OF STEEL EL {m.EL_B1_TOP:.2f} · SEE S-104",
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
    lead(ax, (X_LOBBY, 21.6), (32.6, 22.3), "RIM-L ON THE LOBBY\nWALL: carries the stair\nwall, fire-blocks the\ntruss space", size=4.3, color=TR, ha="center")
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
    dimb(ax, (xd, m.B1_Y), (xd, m.Y_GR_I + BRG / 2), 0, f"{ftin(span_a)} SPAN, centre of B1 to centre of ledge", size=4.7, ext=False, side=-1)
    dimb(ax, (xd, YS_P), (xd, m.B1_Y), 0, ftin(cant), size=4.5, ext=False, side=-1)
    dimb(ax, (35.0, m.YF), (35.0, YS_P), 0, "4'-0\"", size=4.5, ext=False, side=1)
    # bearing key in the empty corner
    txt(ax, 30.0, 42.4, "LEVELS", size=5.8, weight="bold", ha="left")
    for i, (s, e) in enumerate((("Top of subfloor = top of slab on grade", m.EL_A), ("Top of trusses", EL_TOP_A),
                                ("Truss bearing: top of B1 and wall ledges", EL_BRG_A), ("Underside of B1", m.EL_B1_TOP - m.B1_DEPTH),
                                ("Garage slab", m.EL_GAR))):
        txt(ax, 30.0, 41.4 - i * 0.82, s, size=4.9, ha="left")
        txt(ax, 46.4, 41.4 - i * 0.82, f"EL {e:.2f}", size=4.9, ha="right", weight="bold")
    txt(ax, 30.0, 37.3, "If a 2x nailer or sill plate goes under the trusses, the steel\nand the ledges go 1 1/2 in. lower: engineer to decide.", size=4.5, ha="left", color=GREY, va="top")
    # ---- strip: schedule and key
    y = SHEET_H - MARGIN - 0.3
    y = strip_head(bg, y, "Unit A floor truss schedule (preliminary)")
    rows = [("MARK", "QTY", "LENGTH", "WHERE / BEARING")]
    rows += [("FT-A1", len(a1), ftin(a1[0]["y1"] - a1[0]["y0"]), "Garage: B1 to rear ledge + porch"),
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
            "Rear: 12 in. overhang. Rakes: 8 in.",
        ]),
        ("Sheathing and ties", [
            "7/16 in. OSB with H-clips, 8d at 6 in.",
            "edges and 12 in. field (prelim.).",
            "Hurricane tie at every truss, both walls.",
            "Permanent bracing exactly as shown on",
            "the sealed truss drawings (BCSI).",
            "Gable-end trusses braced back to the",
            "roof and ceiling planes.",
            "Attic access 22 x 30 in. in the hall.",
        ]),
        ("Not in the attic", [
            "No ducts, no air handler, no water pipe.",
            "Bottom chords carry the ceiling and R-49.",
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
    txt(ax, 27.0, m.ridge_y(27.0) + 0.75, f"RIDGE · skewed {abs(rang):.1f}° in plan · rises {ftin8(S24 * s_abs / 2 * P)} per truss going west", size=5.0, weight="bold", rot=rang, box=True, z=12)
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
    lead(ax, (acc[2], 25.1), (24.0, 22.0), "ATTIC ACCESS 22 x 30 in.\nin the hall ceiling, between\ntrusses, gasketed + R-49 lid", size=4.4, color=ACCENT, dot=False)
    # labels
    txt(ax, 27.2, 13.6, f"T1 - T{len(ROOF_FULL)} · COMMON ROOF TRUSSES @ 24 in. O.C. · 4:12 · 12 in. RAISED HEEL", size=5.4, weight="bold", box=True, z=12)
    txt(ax, 27.2, 12.55, "bear on the front and rear walls (tan) · red dot = hurricane tie at every truss, each wall", size=4.6, box=True, z=12)
    txt(ax, 26.0, 8.15, "4'-0\" FRONT OVERHANG OVER THE UNIT B PORCH · cantilevered truss tails (dashed) · level soffit return to the wall",
        size=4.5, color=TR, box=True, z=12)
    lead(ax, (30.0, eave_r(30.0)), (31.0, 39.2), f"REAR EAVE: 12 in. overhang measured square to the wall\n({ftin8(OH_REAR / CR)} along the truss) · 1-hour soffit, see A-501 and S-301", size=4.5, color=TR)
    xe = m.XE + 1.5
    lead(ax, (m.XE - 0.06, 14.0), (xe, 13.2), f"GE: GABLE-END TRUSS on\nthe east wall, {ftin(depth_oo(m.XE))} span,\nstudded at 16 in. for\nsheathing and siding", size=4.4, color=TR)
    lead(ax, (m.XE + RAKE, 26.5), (xe, 27.5), "8 in. RAKE: 2x4 ladder\nat 24 in. on the gable truss", size=4.4, color=TR)
    gy = 20.0

    def west(p, y, s, color=TR):
        lead(ax, p, (rake_w(y) - 0.9, y), s, size=4.4, color=color, ha="right")

    west((m.xw_o(31.0) + 0.06, 31.0), 33.4, f"GW: GABLE-END TRUSS along\nthe leaning west wall,\n{ftin(m.WEST_WALL_LEN)} span, top chords\n{12 * P * CW:.2f}:12 front and\n{12 * P * (CW + s_abs * math.sin(WEST_LEAN)):.2f}:12 rear along its length")
    c1 = ROOF_CLIP[0]
    west((c1, 15.5), 17.2, f"C1, C2: common-truss\nprofile cut off at the west\ngable, hung from GW\n({ftin(y_on(m.xw_o, ROOF_CLIP[0]) - m.YF)} and {ftin(y_on(m.xw_o, ROOF_CLIP[-1]) - m.YF)} from\nthe front wall)")
    west((rake_w(26.0), 26.0), 26.0, "8 in. RAKE, square\nto the wall")
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
    # eave levels
    txt(ax, 33.0, 42.9, "LEVELS (top of truss, add sheathing and shingles)", size=5.2, weight="bold", ha="left")
    for i, (s, e) in enumerate(((f"Ridge, west wall face / east wall face", f"EL {m.ridge_el(RIDGE_W[0]):.2f} / {m.ridge_el(m.XE):.2f}"),
                                ("Heel: top of truss at the outside face of both walls", f"EL {EL_HEEL:.2f}"),
                                ("Rear eave (level, parallel to the rear wall)", f"EL {EL_EAVE_R:.2f}"),
                                ("Front eave, 4'-0\" out (level)", f"EL {EL_EAVE_F:.2f}"),
                                ("Top of wall plates, Unit B", f"EL {m.EL_PLATE:.2f}"))):
        txt(ax, 33.0, 42.0 - i * 0.8, s, size=4.7, ha="left")
        txt(ax, 50.6, 42.0 - i * 0.8, e, size=4.7, ha="right", weight="bold")
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
    why_roof_key(fig, bg, STRIP_X, 0.5)
    save(fig, "S-203", pdf)


SHEETS = [("S-201", sheet_s201), ("S-202", sheet_s202), ("S-203", sheet_s203)]
