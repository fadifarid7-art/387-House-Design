"""Rev E sheets A-201, A-202, A-301, A-402: elevations, building sections, stair and porch details.

Every view is drawn to scale from model.py. A view is a 2-D axes whose horizontal axis is a
true length (plan station, or distance along a skewed wall) and whose vertical axis is the
elevation in feet (NAVD88). Numbers the model does not hold are collected in section 0 below
with the reason for each, and are reported to the set's editor.
"""
import math
import re

import numpy as np
from matplotlib.patches import FancyBboxPatch

from common import *  # noqa: F401,F403
import model as m
from index import TITLE

IN = m.IN

# ----------------------------------------------------------------------------
# 0. Numbers derived from the model, and the few the model does not hold
# ----------------------------------------------------------------------------
P = m.ROOF_PITCH
EAVE = m.EL_PLATE + m.HEEL                 # top of the roof truss at the outside wall face
T_CONC = m.EL_B1_TOP                       # top of the garage walls = bearing of the Unit A floor trusses
Z_B1_BOT = m.EL_B1_TOP - m.B1_DEPTH        # underside of beam B1
A_T0 = m.EL_A - 0.75 * IN - m.TRUSS_A      # underside of the Unit A floor trusses
B_T1 = m.EL_B - 0.75 * IN                  # top / underside of the Unit B floor trusses
B_T0 = B_T1 - m.TRUSS_B
Z_CLG_GAR = m.EL_GAR + m.CLG_GAR
Z_CLG_A = m.EL_A + m.CLG_A
Z_CLG_B = m.EL_B + m.CLG_B
OH_F, OH_R, OH_S = 4.0, 1.0, 8 * IN        # roof overhangs from the brief: front, rear, side rakes
GUARD = 3.0                                # 36 in. porch and stair guards (IRC R312.1.2 minimum)
CLEAR8 = 8 * IN                            # concrete carried 8 in. above finish grade (IRC R317.1)
DOOR_H = 6 + 8 * IN                        # 6'-8" doors (door D1 note in the model)
FASCIA = 0.5                               # ASSUMED: 2x6 sub-fascia behind a 1x8 fascia board
W3_SILL = 3.5                              # ASSUMED: the model gives no sill for W3; head set level with W1/W2
SWALE_CUT = 0.5                            # ASSUMED: finish grade at the rear wall face is 6 in. below existing
WALL_SITE_FREEBOARD = 0.5                  # ASSUMED: site walls stop 6 in. above the ground they retain
SLAB_GAR, STONE_GAR = 0.5, 0.5             # garage slab 6 in. on 6 in. stone (brief)
SLAB_A, STONE_A, RIGID = 5 * IN, 4 * IN, 2 * IN     # Unit A slab 5 in. on 4 in. stone, R-10 = 2 in. XPS (brief)
STEM, STEM_FTG_W, STEM_FTG_T = 8 * IN, 20 * IN, 10 * IN   # stem wall and its footing (brief)
FROST = 3.0                                # 36 in. frost depth (brief)
HP_H = 2.5                                 # ASSUMED: side-discharge heat pump 30 in. high (38 x 15 in. plan is the model's)
METER_W, METER_H, METER_CL = 2.33, 2.5, 5.0   # ASSUMED: 2-position meter stack 28 x 30 in., meters 5'-0" above grade
WH_H = 5.0                                 # 80 gal heater 60 in. high (m.SIZES)
TUB_H = 16 * IN                            # ASSUMED: 60 x 30 tub, 16 in. rim
CAR_H = 4.75                               # ASSUMED: design car 57 in. high (the model gives 6'-2" x 16'-0" in plan)
STAIR_GAP = 4 * IN                         # well between the two flights (plans.u_stair)
LAND = 3.25                                # floor landing, 3'-3" (plans.unit_shell)
XS1, XS2 = 14.8, 42.0                      # section stations ("about X = 15" and "about X = 41")

_t = math.atan(abs(REAR_SLOPE))
CT, ST = math.cos(_t), math.sin(_t)
CL, SL = math.cos(WEST_LEAN), math.sin(WEST_LEAN)
X0 = m.OUT_U[0][0]                         # south-west building corner
NE, NW = m.OUT_U[2], m.OUT_U[3]

EARTH_FC = "#efe9e1"
CONC_FC = "#b9bdc2"
SIDING = "#fbfaf7"
BEYOND = "#f1f1ee"
GLASS = "#dfe7ee"
ROOF_FC = "#c9cdd2"
WOODC = "#e9e4d9"
SHADE = "#e9ebee"
STEEL = BLUE
POCHE = "#1b1e22"
INSUL = "#f6dfe4"
STONE_FC = "#e1ddd4"
DASH = (0, (4, 2.5))
CHAIN = (0, (9, 2.5, 1.5, 2.5))
SCALE8 = "1/8\" = 1'-0\""
SCALE316 = "3/16\" = 1'-0\""


def fi(v, q=4):
    """Feet-inches to the nearest 1/q in. (common.ftin rounds to the inch)."""
    tot = int(round(abs(v) * 12 * q))
    f, r = divmod(tot, 12 * q)
    i, n = divmod(r, q)
    g = math.gcd(n, q) if n else 1
    frac = f" {n // g}/{q // g}" if n else ""
    return f"{'-' if v < 0 else ''}{f}'-{i}{frac}\""


def inch(v, q=16):
    tot = int(round(v * q))
    i, n = divmod(tot, q)
    g = math.gcd(n, q) if n else 1
    return f"{i} {n // g}/{q // g}" if n else f"{i}"


def wtype(tag):
    """(width, height, sill) of a window type, read from the model's schedule text."""
    s = m.WINDOW_TYPES[tag]
    a = re.search(r"(\d+)'-(\d+)\" x (\d+)'-(\d+)\"", s)
    b = re.search(r"sill (\d+) in", s)
    return int(a[1]) + int(a[2]) / 12, int(a[3]) + int(a[4]) / 12, (int(b[1]) / 12 if b else W3_SILL)


# ---- roof: two planes that meet on the skewed ridge (m.ridge_y), cut by the two gable walls ----
def x_west(y, off=0.0):
    return m.xw_o(y) - off / CL


def y_rear(x, off=0.0):
    return m.yr_o(x) + off / CT


def _fix(f, y=30.0):
    for _ in range(80):
        y = f(y)
    return y


def roof_z(x, y):
    """Top of the roof framing at plan point (x, y)."""
    return min(EAVE + (y - m.YF) * P, EAVE + (m.yr_o(x) - y) * P)


R_SW = (x_west(m.YF - OH_F, OH_S), m.YF - OH_F)
R_SE = (m.XE + OH_S, m.YF - OH_F)
R_NE = (m.XE + OH_S, y_rear(m.XE + OH_S, OH_R))
_y = _fix(lambda y: y_rear(x_west(y, OH_S), OH_R), 40.0)
R_NW = (x_west(_y, OH_S), _y)
RG_E = (m.XE + OH_S, m.ridge_y(m.XE + OH_S))
_y = _fix(lambda y: m.ridge_y(x_west(y, OH_S)), 25.0)
RG_W = (x_west(_y, OH_S), _y)
_y = _fix(lambda y: m.ridge_y(m.xw_o(y)), 25.0)
RG_WW = (m.xw_o(_y), _y)                   # ridge at the west wall face
Z_EAVE_F = EAVE - OH_F * P                 # top of framing at the front fascia
Z_EAVE_R = EAVE - OH_R * P                 # top of framing at the rear fascia
Z_SOFFIT_F = Z_EAVE_F - FASCIA             # level soffit over the Unit B porch
Z_SOFFIT_R = Z_EAVE_R - FASCIA


# ---- view projections: plan point -> horizontal station of the view ----
def h_rear(x, y):
    """True length along the rear wall, 0 at the north-east corner, + toward the west."""
    return (m.XE - x) * CT + (y - NE[1]) * ST


def h_west(x, y):
    """True length along the west wall, 0 at the south-west corner, - toward the rear (front is on the right)."""
    return -((x - X0) * SL + (y - m.YF) * CL)


# ---- grades ----
def fg_rear(x):
    return elev(x, m.yr_o(x)) - SWALE_CUT


def fg_west(y):
    r = min(1.0, max(0.0, (y - (m.Y_GR_O - 4.0)) / 4.0))
    return elev(m.xw_o(y), y) - SWALE_CUT * r


def ct_rear(x):
    return max(m.EL_A, fg_rear(x) + CLEAR8)


def ct_west(y):
    return max(T_CONC, fg_west(y) + CLEAR8)


def apron_el(x, y):
    """Apron surface: straight grade from the pavement edge to the trench drain at the opening."""
    y1 = m.YF - 0.6
    t = max(0.0, min(1.0, (y1 - y) / (y1 - PAVE_N)))
    return m.EL_GAR + (street_el(x) - m.EL_GAR) * t


# stair geometry used by the section and the details (one geometry for all three levels)
ST_Y0 = m.SHAFT_U[2] + LAND                                 # nosing line at the floor landings
ST_LO_RUN = m.STAIR_LO["treads_per_flight"] * m.STAIR_LO["tread_in"] * IN
ST_UP_RUN = m.STAIR_UP["treads_per_flight"] * m.STAIR_UP["tread_in"] * IN
ST_LO_MID = m.EL_GAR + m.STAIR_LO["rise_total"] / 2         # mid landing, lower stair
ST_UP_MID = m.EL_A + m.STAIR_UP["rise_total"] / 2
FLIGHT_U = (m.SHAFT_U[1] - m.SHAFT_U[0] - STAIR_GAP) / 2    # flight width on the unit floors
FLIGHT_L = (m.SHAFT_L[1] - m.SHAFT_L[0] - STAIR_GAP) / 2    # flight width between the concrete walls


# ----------------------------------------------------------------------------
# 1. Drafting helpers
# ----------------------------------------------------------------------------
def K(ax):
    """Size factor: 1.0 on a 1/8 in. view."""
    return ax.fpi / 8.0


def clipped_lines(ax, patch, ys, x0, x1, color=LIGHT, lw=0.15, z=3.1):
    for yy in ys:
        ln, = ax.plot([x0, x1], [yy, yy], color=color, lw=lw, zorder=z, solid_capstyle="butt")
        ln.set_clip_path(patch)


def siding(ax, pts, step=0.5, fc=SIDING, ec=INK, lw=0.8, z=3, lc=LIGHT):
    p = poly(ax, pts, fc=fc, ec=ec, lw=lw, z=z)
    xs, ys = [q[0] for q in pts], [q[1] for q in pts]
    z0 = math.floor(min(ys) / step) * step
    clipped_lines(ax, p, np.arange(z0, max(ys), step), min(xs), max(xs), color=lc, z=z + 0.05)
    return p


def earth(ax, pts, bottom, z=6, lw=1.3, hatch=True):
    """Ground in elevation or section: fill below the line `pts`, heavy line on top."""
    poly(ax, list(pts) + [(pts[-1][0], bottom), (pts[0][0], bottom)], fc=EARTH_FC, ec="none", z=z)
    line(ax, pts, lw=lw, z=z + 1)


def note(ax, p, t, s, size=4.8, ha="left", va="center", color=INK, dot=True, box=True):
    """Call-out: leader from the thing at p to the text at t."""
    line(ax, [p, t], lw=0.3, color=color, z=11)
    if dot:
        ax.plot([p[0]], [p[1]], marker="o", ms=1.4, color=color, zorder=11)
    d = 0.12 * ax.fpi * (1 if ha == "left" else -1 if ha == "right" else 0)
    txt(ax, t[0] + d, t[1], s, size=size, ha=ha, va=va, color=color, box=box, z=12)


def lvl(ax, x, el, name, ha="left", size=4.6, el_txt=None, line_to=None):
    """Level mark: triangle on the level, name above the line and elevation below."""
    k = K(ax)
    if line_to is not None:
        line(ax, [(x, el), (line_to, el)], lw=0.3, color=GREY, ls=(0, (8, 3, 2, 3)), z=8)
    poly(ax, [(x, el), (x - 0.42 * k, el + 0.7 * k), (x + 0.42 * k, el + 0.7 * k)], fc=INK, lw=0.3, z=10)
    tx = x + (0.75 * k if ha == "left" else -0.75 * k)
    txt(ax, tx, el + 0.52 * k, name, size=size, ha=ha, weight="bold", z=10)
    txt(ax, tx, el - 0.5 * k, el_txt or f"EL {el:.1f}", size=size - 0.3, ha=ha, color=GREY, z=10)


def window(ax, h0, h1, z0, z1, kind="", fc=GLASS, ec=INK, lw=0.6, z=4):
    rect(ax, h0, z0, h1, z1, fc=fc, ec=ec, lw=lw, z=z)
    hm, zm = (h0 + h1) / 2, (z0 + z1) / 2
    if "slider" in kind:
        line(ax, [(hm, z0), (hm, z1)], lw=0.4, color=ec, z=z + 0.1)
    elif "single-hung" in kind:
        line(ax, [(h0, zm), (h1, zm)], lw=0.4, color=ec, z=z + 0.1)
    elif "casement" in kind:
        line(ax, [(h0, z0), (h1, zm), (h0, z1)], lw=0.2, color=GREY, z=z + 0.1)
    elif "awning" in kind:
        line(ax, [(h0, z0), (hm, z1), (h1, z0)], lw=0.2, color=GREY, z=z + 0.1)


def wall_windows(ax, wall_, hfun, light=False, tags=True, floors=(m.EL_A, m.EL_B)):
    """Windows of one exterior wall on both unit floors; hfun maps a station on the wall to the view."""
    out = []
    for (tag, w_, s0, s1, _n) in m.WINDOWS:
        if w_ != wall_:
            continue
        w, hgt, sill = wtype(tag)
        hc = hfun((s0 + s1) / 2)
        d = abs(hfun(s1) - hfun(s0)) / 2 if light else w / 2
        for fl in floors:
            window(ax, hc - d, hc + d, fl + sill, fl + sill + hgt, m.WINDOW_TYPES[tag],
                   fc="#e9eef2" if light else GLASS, ec=GREY if light else INK, lw=0.4 if light else 0.6)
            if tags and not light:
                k = K(ax)
                poly(ax, [(hc - 0.75 * k, fl + sill - 0.85 * k), (hc, fl + sill - 0.3 * k), (hc + 0.75 * k, fl + sill - 0.85 * k),
                          (hc, fl + sill - 1.4 * k)], fc=PAPER, ec=INK, lw=0.35, z=10)
                txt(ax, hc, fl + sill - 0.85 * k, tag[1:], size=3.8, z=11)
            out.append((tag, hc, w, fl + sill, fl + sill + hgt))
    return out


def guard(ax, h0, h1, z, posts=None, bal=4.5 * IN, color=INK, z_=5.5, lw=0.7):
    """36 in. guard in elevation: top and bottom rails, posts, balusters at 4 1/2 in. centres."""
    line(ax, [(h0, z + GUARD), (h1, z + GUARD)], lw=lw + 0.2, color=color, z=z_)
    line(ax, [(h0, z + 0.29), (h1, z + 0.29)], lw=lw * 0.6, color=color, z=z_)
    n = max(1, int(math.ceil((h1 - h0) / 6.0))) if posts is None else posts
    for i in range(n + 1):
        hp = h0 + (h1 - h0) * i / n
        line(ax, [(hp, z), (hp, z + GUARD)], lw=lw + 0.3, color=color, z=z_)
    for hb in np.arange(h0 + bal, h1 - bal / 2, bal):
        line(ax, [(hb, z + 0.29), (hb, z + GUARD)], lw=0.13, color=GREY, z=z_ - 0.1)


def truss_band(ax, y0, y1, z0, z1, z=5, fc=WOODC, web=2.0, lw=0.6):
    """Open-web floor truss seen from the side (section along its span)."""
    rect(ax, y0, z0, y1, z1, fc=fc, ec=INK, lw=lw, z=z)
    c = 0.29                                                   # 3 1/2 in. chords (4x2 flat)
    line(ax, [(y0, z0 + c), (y1, z0 + c)], lw=0.25, color=GREY, z=z + 0.1)
    line(ax, [(y0, z1 - c), (y1, z1 - c)], lw=0.25, color=GREY, z=z + 0.1)
    n = max(1, int(round((y1 - y0) / web)))
    w = (y1 - y0) / n
    pts = []
    for i in range(n):
        pts += [(y0 + i * w, z0 + c), (y0 + (i + 0.5) * w, z1 - c)]
    pts.append((y1, z0 + c))
    line(ax, pts, lw=0.25, color=GREY, z=z + 0.1)


def break_mark(ax, x, z0, z1, color=GREY):
    zm, k = (z0 + z1) / 2, K(ax)
    line(ax, [(x, z0), (x, zm - 0.4 * k), (x - 0.35 * k, zm - 0.15 * k), (x + 0.35 * k, zm + 0.15 * k), (x, zm + 0.4 * k), (x, z1)],
         lw=0.5, color=color, z=9)


def title_under(fig_bg, ax_pos, num, title, sub):
    """View title under a view; ax_pos = (left_in, bottom_in)."""
    x, y = ax_pos
    fig_bg.add_patch(plt.Circle((x + 0.16, y - 0.21), 0.14, fc=PAPER, ec=INK, lw=0.8))
    fig_bg.text(x + 0.16, y - 0.215, str(num), fontsize=7.5, fontweight="bold", ha="center", va="center")
    fig_bg.text(x + 0.38, y - 0.13, title.upper(), fontsize=8.0, fontweight="bold", va="center")
    fig_bg.text(x + 0.38, y - 0.30, sub, fontsize=5.6, color=GREY, va="center")


def lot_line(ax, h, z0, z1, label=None, ha="center", size=4.6, lab_z=None):
    line(ax, [(h, z0), (h, z1)], color=ACCENT, lw=0.8, ls=CHAIN, z=12)
    if label:
        txt(ax, h, (z1 + 0.7 * K(ax)) if lab_z is None else lab_z, label, size=size, color=ACCENT, ha=ha, z=12)


# ----------------------------------------------------------------------------
# 2. A-201: front and rear elevations
# ----------------------------------------------------------------------------
def porch_front(ax, x0, x1, z_top, depth):
    rect(ax, x0, z_top - depth, x1, z_top, fc=WOODC, ec=INK, lw=0.7, z=5)
    line(ax, [(x0, z_top - 0.125), (x1, z_top - 0.125)], lw=0.3, z=5.1)
    guard(ax, x0 + 0.2, x1 - 0.2, z_top)


def front_elev(ax, xl, yl, big=False):
    k = K(ax)
    XE = m.XE
    # --- frame walls with lap siding
    siding(ax, [(X0, T_CONC), (XE, T_CONC), (XE, Z_SOFFIT_F), (X0, Z_SOFFIT_F)])
    line(ax, [(X0, B_T0), (m.OPEN[0], B_T0)], lw=0.3, color=GREY, z=3.2)
    # --- garage level: concrete return pier, opening, lobby wall, beam and post
    rect(ax, X0, yl[0], m.OPEN[0], T_CONC, fc=CONC_FC, lw=0.8, z=3)
    rect(ax, m.GAR_X1, m.EL_GAR, XE, T_CONC, fc=CONC_FC, lw=0.8, z=3)
    rect(ax, m.OPEN[0], m.EL_GAR, m.OPEN[1], Z_B1_BOT, fc=SHADE, ec=INK, lw=0.7, z=2.5)
    for c in m.CARS:
        ax.add_patch(FancyBboxPatch((c + 0.35, m.EL_GAR + 0.75), m.CAR_W - 0.7, CAR_H - 0.75 - 0.35,
                                    boxstyle="round,pad=0.35,rounding_size=0.9", fc="#f6f7f8", ec="#a4abb3", lw=0.5, zorder=2.6))
        for wx in (c + 0.35, c + m.CAR_W - 1.05):
            rect(ax, wx, m.EL_GAR, wx + 0.7, m.EL_GAR + 0.9, fc="#a4abb3", ec="none", z=2.55)
    rect(ax, m.COL_X[0] - 0.25, Z_B1_BOT, m.SHAFT_X0, m.EL_B1_TOP, fc=STEEL, ec=INK, lw=0.5, z=4)
    cx = m.COL_X[1]
    rect(ax, cx - 0.25, m.EL_GAR, cx + 0.25, Z_B1_BOT, fc=STEEL, ec=INK, lw=0.4, z=4)
    rect(ax, m.ENTRY[0], m.EL_GAR, m.ENTRY[1], m.EL_GAR + DOOR_H, fc="#d6dbe0", ec=INK, lw=0.7, z=4)
    rect(ax, m.ENTRY[0] + 0.5, m.EL_GAR + 3.4, m.ENTRY[1] - 0.5, m.EL_GAR + DOOR_H - 0.5, fc=GLASS, ec=INK, lw=0.3, z=4.1)
    # --- windows and the porch door on the front wall, both flats
    wins = wall_windows(ax, "S", lambda s: s, tags=True)
    d14 = [d for d in m.DOORS if d["tag"] == "D14"][0]
    for fl in (m.EL_A, m.EL_B):
        rect(ax, d14["s0"], fl, d14["s1"], fl + DOOR_H, fc=GLASS, ec=INK, lw=0.7, z=4)
        rect(ax, d14["s0"] + 0.35, fl + 0.5, d14["s1"] - 0.35, fl + DOOR_H - 0.35, fc=GLASS, ec=INK, lw=0.3, z=4.1)
    # --- cantilevered porches
    porch_front(ax, m.PORCH[0], m.PORCH[2], m.EL_A, m.EL_A - A_T0)
    porch_front(ax, m.PORCH[0], m.PORCH[2], m.EL_B, m.EL_B - B_T0)
    # --- roof: front slope from the fascia up to the skewed ridge
    ridge = [(x, m.ridge_el(x)) for x in np.linspace(RG_W[0], RG_E[0], 24)]
    rp = poly(ax, [(R_SW[0], Z_EAVE_F), (R_SE[0], Z_EAVE_F)] + ridge[::-1], fc=ROOF_FC, ec=INK, lw=0.9, z=5)
    clipped_lines(ax, rp, np.arange(Z_EAVE_F + 0.6, 951, 0.6), R_SW[0], R_SE[0], color="#9aa1a9", z=5.1)
    rect(ax, R_SW[0], Z_SOFFIT_F, R_SE[0], Z_EAVE_F, fc=PAPER, ec=INK, lw=0.7, z=5.2)
    # --- ground: existing along the front wall, finish (cut for the garage and landing), pavement in front
    xw = list(np.linspace(xl[0], m.OPEN[0], 14))
    xe = list(np.linspace(m.WING_E[1][0], xl[1], 8))
    fin = [(x, elev(x, m.YF)) for x in xw] + [(m.OPEN[0], m.EL_GAR), (m.WING_E[1][0], m.EL_GAR)] + [(x, elev(x, m.YF)) for x in xe]
    earth(ax, fin, yl[0])
    line(ax, [(x, elev(x, m.YF)) for x in np.linspace(m.OPEN[0], m.WING_E[1][0], 16)], lw=0.8, color=EARTH, ls=DASH, z=8)
    line(ax, [(x, street_el(x)) for x in (xl[0], xl[1])], lw=0.8, color=BLUE, ls=(0, (6, 3)), z=8)
    # wing walls: west one seen at an angle (it runs from the opening jamb toward the street), east one end-on
    (wx0, wy0), (wx1, wy1) = m.WING_W
    poly(ax, [(wx0, m.EL_GAR), (wx1, apron_el(wx1, wy1)), (wx1, elev(wx1 - 0.7, wy1) + WALL_SITE_FREEBOARD),
              (wx0, elev(wx0, wy0) + WALL_SITE_FREEBOARD)], fc=CONC_FC, ec=INK, lw=0.6, z=8.2)
    ex = m.WING_E[1][0]
    rect(ax, ex - CLEAR8, m.EL_GAR, ex, elev(ex, m.YF) + WALL_SITE_FREEBOARD, fc=CONC_FC, ec=INK, lw=0.6, z=8.2)
    # hidden below grade: return pier and west retaining wall down to the footing
    line(ax, [(X0, elev(X0, m.YF)), (X0, m.EL_FTG_TOP), (m.OPEN[0], m.EL_FTG_TOP)], lw=0.5, color=GREY, ls=DASH, z=8)
    # trash screen in front of the lobby wall (drawn in outline so the street door stays visible)
    tx0, tx1 = m.TRASH[0], m.TRASH[2]
    line(ax, [(tx0, m.EL_GAR), (tx0, m.EL_GAR + 5.0), (tx1, m.EL_GAR + 5.0)], lw=0.5, color=GREY, ls=(0, (2, 2)), z=8)
    return wins


def front_labels(ax, xl, yl):
    """Call-outs, level marks and dimensions of the 1/8 in. front elevation."""
    XE = m.XE
    ag = m.avg_grade()
    lot_line(ax, 0.0, yl[0] + 1.0, 955.5)
    lot_line(ax, 50.0, yl[0] + 1.0, 955.5)
    txt(ax, -0.45, 951.0, "WEST LOT LINE", size=4.4, color=ACCENT, rot=90)
    txt(ax, 50.5, 951.0, "EAST LOT LINE", size=4.4, color=ACCENT, rot=90)
    for xn, nm, ha in ((west_x(m.YF) - 1.0, "442\nBAIRD", "left"), (51.0, "441\nBAIRD", "right")):
        g = elev(xn, m.YF)
        line(ax, [(xn, g), (xn, g + 14)], lw=0.6, color=GREY, ls=DASH, z=8)
        break_mark(ax, xn, g + 13, g + 15.5)
    txt(ax, -1.2, elev(-1, m.YF) + 17.4, "442 BAIRD\nhouse wall\n±1 ft beyond\nthe lot line", size=3.9, color=GREY, ha="left")
    txt(ax, 53.1, elev(51, m.YF) + 17.4, "441 BAIRD\nhouse wall\n±1 ft beyond\nthe lot line", size=3.9, color=GREY, ha="right")
    # level marks between the west lot line and the building
    for el, nm, et in ((m.EL_A, "UNIT A FLOOR", None), (m.EL_B, "UNIT B FLOOR", None), (m.EL_PLATE, "TOP PLATE", None),
                       (m.EL_RIDGE_HI, "RIDGE (WEST)", f"EL {m.EL_RIDGE_HI:.2f}")):
        lvl(ax, 4.75, el, nm, ha="right", size=4.3, el_txt=et, line_to=X0 if el < m.EL_PLATE else 5.3)
    txt(ax, (m.OPEN[0] + m.OPEN[1]) / 2, m.EL_GAR - 1.0, f"GARAGE SLAB AND ENTRY LANDING  EL {m.EL_GAR:.1f}", size=4.6, weight="bold", z=12)
    note(ax, (XE + OH_S, m.ridge_el(XE)), (XE + 1.4, 950.6), f"RIDGE (EAST) EL {m.EL_RIDGE_LO:.1f}", size=4.2, ha="center")
    # zoning height
    line(ax, [(X0 - 1, ag + 35), (XE + 2.5, ag + 35)], color=ACCENT, lw=0.7, ls=(0, (4, 3)), z=12)
    txt(ax, (X0 + XE) / 2, ag + 35.75, f"35 FT ZONING HEIGHT LIMIT = EL {ag + 35:.1f}  (average existing grade at the four corners EL {ag:.1f} + 35 ft)",
        size=4.4, color=ACCENT)
    line(ax, [(X0 - 2.4, ag), (X0 + 3, ag)], color=ACCENT, lw=0.5, ls=(0, (4, 3)), z=12)
    dim(ax, (XE + 2.0, ag), (XE + 2.0, m.EL_RIDGE_HI), 0, f"{ftin(m.EL_RIDGE_HI - ag)} TO RIDGE", ext=False, size=4.2, color=ACCENT, side=-1)
    dim(ax, (XE + 2.0, m.EL_RIDGE_HI), (XE + 2.0, ag + 35), 0, f"{ftin(ag + 35 - m.EL_RIDGE_HI)} SPARE", ext=False, size=4.2, color=ACCENT, side=-1)
    line(ax, [(XE - 4, ag), (XE + 2.6, ag)], color=ACCENT, lw=0.5, ls=(0, (4, 3)), z=12)
    txt(ax, XE + 2.7, ag - 0.75, f"AVG. GRADE\nEL {ag:.1f}", size=3.9, color=ACCENT, ha="center", va="top", z=12)
    # widths
    dim(ax, (X0, 953.2), (XE, 953.2), 0, f"FACADE {ftin(m.FACADE_W)}", ext=False, size=4.6)
    dim(ax, (0, 953.2), (X0, 953.2), 0, ftin(X0), ext=False, size=4.2, color=ACCENT)
    dim(ax, (XE, 953.2), (50, 953.2), 0, ftin(50 - XE), ext=False, size=4.2, color=ACCENT)
    txt(ax, X0 / 2, 954.5, "5'-2\" square\nto the line", size=3.6, color=ACCENT)
    # heights on the east side of the facade
    xd = 47.3
    dim(ax, (xd, m.EL_GAR), (xd, m.EL_A), 0, fi(m.EL_A - m.EL_GAR), ext=False, size=4.2, side=-1)
    dim(ax, (xd, m.EL_A), (xd, m.EL_B), 0, fi(m.EL_B - m.EL_A), ext=False, size=4.2, side=-1)
    dim(ax, (xd, m.EL_B), (xd, m.EL_PLATE), 0, fi(m.EL_PLATE - m.EL_B, 8), ext=False, size=4.2, side=-1)
    for el in (m.EL_GAR, m.EL_A, m.EL_B, m.EL_PLATE):
        line(ax, [(XE + 0.2, el), (xd + 0.5, el)], lw=0.25, color=GREY, z=8)
    # call-outs
    note(ax, (20.0, Z_B1_BOT + 0.5), (15.5, 918.9), "STEEL BEAM B1 (W14x34 prelim.)\ndropped under the trusses", size=4.0, ha="center")
    txt(ax, 22.6, 916.9, "OPEN GARAGE, NO DOORS", size=4.4, weight="bold", z=9)
    txt(ax, 33.3, 918.9, f"{ftin(m.OPEN_W)} x {fi(m.OPEN_CLEAR_H)}\nCLEAR OPENING", size=4.0, z=9)
    note(ax, (m.COL_X[1], 919.2), (30.3, 921.3), "HSS 6x6\nPOST", size=3.8, ha="left")
    txt(ax, (m.ENTRY[0] + m.ENTRY[1]) / 2, m.EL_GAR + 2.0, "STREET\nDOOR", size=3.6, z=9)
    note(ax, (m.TRASH[0], m.EL_GAR + 4.2), (41.0, 911.9), "TRASH SCREEN IN FRONT OF THE\nLOBBY WALL (dotted, see C-107)", size=3.8, ha="center")
    note(ax, (9.0, 923.0), (2.0, 918.0), "CONCRETE\nRETURN PIER\n(buried below\nthe front yard)", size=3.8, ha="center")
    note(ax, (12.6, 918.6), (7.2, 913.2), "WING WALL beside the apron\nretains the front yard (C-107)", size=3.8, ha="center")
    note(ax, (XE - 0.3, 916.5), (48.0, 914.0), "LOW WALL\nat the landing", size=3.8, ha="left")
    note(ax, (25.0, elev(25.0, m.YF)), (22.0, 912.2), "EXISTING GROUND AT THE FRONT WALL\n(removed for the garage and landing)", size=3.8, ha="center", color=EARTH)
    txt(ax, 3.0, street_el(3.0) - 1.0, "BAIRD ST PAVEMENT (in front), falls 11.4 % east", size=3.9, color=BLUE, rot=-6.5, ha="left", z=12)
    txt(ax, 34.5, m.EL_A - 0.95, "UNIT A PORCH, CANTILEVERED 4'-0\", 36 in. GUARD", size=3.8, z=11)
    txt(ax, 34.5, m.EL_B - 1.1, "UNIT B PORCH, CANTILEVERED 4'-0\", 36 in. GUARD", size=3.8, z=11)
    txt(ax, 27.0, Z_EAVE_F - FASCIA / 2, "FASCIA + GUTTER: ROOF OVERHANGS THE FRONT WALL 4'-0\"", size=3.5, z=11)
    txt(ax, 27.0, 946.2, "ASPHALT SHINGLES, 4:12", size=4.2, z=11)
    txt(ax, 16.6, 940.6, "FIBRE-CEMENT OR VINYL LAP SIDING", size=4.0, z=9, box=True)
    txt(ax, 34.0, 930.2, "D14 PORCH DOOR\n3'-0\" x 6'-8\"", size=3.6, z=9, box=True)


def rear_elev(ax, xl, yl):
    L = m.REAR_WALL_LEN
    xs = np.linspace(m.XE, NW[0], 36)
    hs = [h_rear(x, m.yr_o(x)) for x in xs]
    ct = [(h, ct_rear(x)) for h, x in zip(hs, xs)]
    # --- east wall, seen at an angle beyond the north-east corner (the rear wall is skewed 17.1 deg)
    he0, hr_ = h_rear(m.XE, m.YF), h_rear(m.XE, m.ridge_y(m.XE))
    siding(ax, [(he0, T_CONC), (0, T_CONC), (0, EAVE), (hr_, m.ridge_el(m.XE)), (he0, EAVE)], fc=BEYOND, ec=GREY, lw=0.5, z=2)
    rect(ax, he0, yl[0], 0, T_CONC, fc="#d3d6da", ec=GREY, lw=0.5, z=2)
    hp = h_rear(m.XE, m.PORCH[1])
    for fl, bot in ((m.EL_A, A_T0), (m.EL_B, B_T0)):
        rect(ax, hp, bot, he0, fl, fc=WOODC, ec=GREY, lw=0.5, z=2)
        line(ax, [(hp, fl), (hp, fl + GUARD), (he0, fl + GUARD)], lw=0.5, color=GREY, z=2)
    # --- rear wall: concrete stem wall to 8 in. above finish grade, frame wall above
    siding(ax, ct + [(L, Z_SOFFIT_R), (0, Z_SOFFIT_R)])
    poly(ax, [(0, yl[0])] + ct + [(L, yl[0])], fc=CONC_FC, ec=INK, lw=0.8, z=3.3)
    line(ax, [(0, B_T1), (L, B_T1)], lw=0.3, color=GREY, z=3.2)
    wins = wall_windows(ax, "N", lambda s: h_rear(s, m.yr_o(s)))
    # --- roof: rear slope, 12 in. eave, and the east rake running away toward the street
    pts = [(h_rear(*p), roof_z(*p)) for p in (R_NE, R_NW, RG_W, RG_E)]
    rp = poly(ax, pts, fc=ROOF_FC, ec=INK, lw=0.9, z=5)
    clipped_lines(ax, rp, np.arange(Z_EAVE_R + 0.6, 951, 0.6), -9, L + 3, color="#9aa1a9", z=5.1)
    rect(ax, pts[0][0], Z_SOFFIT_R, pts[1][0], Z_EAVE_R, fc=PAPER, ec=INK, lw=0.7, z=5.2)
    se = (h_rear(*R_SE), roof_z(*R_SE))
    poly(ax, [pts[3], se, (se[0], se[1] - FASCIA), (pts[3][0], pts[3][1] - FASCIA)], fc=PAPER, ec=GREY, lw=0.5, z=4.5)
    # --- ground
    xg = list(np.linspace(m.XE, NW[0] - 4.0, 44))
    fin = [(h_rear(m.XE, y), elev(m.XE, y)) for y in np.linspace(-3.0, m.YF + 16, 8)]
    fin += [(h_rear(x, m.yr_o(x)), fg_rear(x)) for x in xg]
    earth(ax, fin, yl[0])
    line(ax, [(h_rear(x, m.yr_o(x)), elev(x, m.yr_o(x))) for x in xg], lw=0.8, color=EARTH, ls=DASH, z=8)
    d = m.SB_REAR + m.M
    ll = [(h_rear(x, m.yr_o(x)), elev(x + d * ST, m.yr_o(x) + d * CT)) for x in xg]
    line(ax, ll, lw=0.7, color=ACCENT, ls=(0, (1.5, 2)), z=8)
    # hidden: stem-wall footing and the Unit A floor where it is below ground
    line(ax, [(h_rear(x, m.yr_o(x)), min(fg_rear(x) - FROST, m.EL_A - 2.0)) for x in xs], lw=0.5, color=GREY, ls=DASH, z=8)
    hx = [h for h, x in zip(hs, xs) if fg_rear(x) > m.EL_A]
    if hx:
        line(ax, [(min(hx), m.EL_A), (L, m.EL_A)], lw=0.5, color=GREY, ls=DASH, z=8)
    return wins, ct, ll


def rear_labels(ax, xl, yl, wins, ct, ll):
    L = m.REAR_WALL_LEN
    ag = m.avg_grade()
    line(ax, [(-3, ag + 35), (L + 1.5, ag + 35)], color=ACCENT, lw=0.7, ls=(0, (4, 3)), z=12)
    txt(ax, L / 2, ag + 35.75, f"35 FT ZONING HEIGHT LIMIT = EL {ag + 35:.1f}", size=4.4, color=ACCENT)
    dim(ax, (0, 953.2), (L, 953.2), 0, f"REAR WALL {ftin(L)} (true length, parallel to the rear lot line)", ext=False, size=4.4)
    for el, nm in ((m.EL_A, "A"), (m.EL_B, "B"), (m.EL_PLATE, "PLATE")):
        line(ax, [(L + 0.2, el), (L + 1.2, el)], lw=0.3, color=GREY, z=8)
        txt(ax, L + 1.35, el, f"{nm}\n{el:.1f}", size=3.9, ha="left", z=10)
    txt(ax, L + 1.35, m.EL_RIDGE_HI + 0.2, f"RIDGE\n{m.EL_RIDGE_HI:.2f}", size=3.9, ha="left", z=10)
    # window stations along the wall (true length from the north-east corner)
    cs = sorted({round(w[1], 3): w for w in wins}.values(), key=lambda w: w[1])
    zb = 920.6
    st = [0.0]
    for w in cs:
        st += [w[1] - w[2] / 2, w[1] + w[2] / 2]
    st.append(L)
    for a, b in zip(st[:-1], st[1:]):
        dim(ax, (a, zb), (b, zb), 0, ftin(b - a), ext=False, size=3.9)
    for a in st[1:-1]:
        line(ax, [(a, zb), (a, zb + 1.2)], lw=0.25, color=GREY, z=8)
    # sill heights against the ground
    for w in cs:
        tag, hc, wd, z0, z1 = [q for q in wins if abs(q[1] - w[1]) < 1e-6 and q[3] < m.EL_B][0]
        x = m.XE - hc / CT * 1.0 if False else None
    w5 = [q for q in wins if q[0] == "W5" and q[3] < m.EL_B][0]
    w1 = [q for q in wins if q[0] == "W1" and q[3] < m.EL_B][0]
    note(ax, (w5[1], w5[3]), (27.2, 932.9), f"W5 SILL EL {w5[3]:.1f}: 54 in. above the Unit A\nfloor, clear of the stem wall and ground", size=3.8, ha="right")
    note(ax, (w1[1] + 0.8, w1[3] + 2), (8.8, 931.2), f"W1 ESCAPE WINDOW\nSILL EL {w1[3]:.1f}", size=3.8, ha="left")
    note(ax, (24.0, np.interp(24.0, [c[0] for c in ct], [c[1] for c in ct]) - 0.25), (16.5, 923.2),
         "CONCRETE STEM WALL carried to 8 in.\nabove finish grade, siding starts there", size=3.8, ha="center")
    note(ax, (31.5, np.interp(31.5, [c[0] for c in ll], [c[1] for c in ll])), (28.0, 937.2),
         "EXISTING GROUND AT THE REAR LOT LINE\n(5'-2\" in front of this wall; 6 ft fence on the line not drawn)", size=3.8, ha="center", color=ACCENT)
    txt(ax, 13.0, 918.6, "dashed brown: existing ground at the wall · solid: finish grade, cut 6 in. for the swale that falls east",
        size=3.7, color=EARTH, z=12)
    txt(ax, 18.3, 916.6, "dashed grey: bottom of the stem-wall footing, 36 in. min. below finish grade (S-101)", size=3.7, color=GREY, z=12)
    txt(ax, L - 0.4, m.EL_A - 0.55, "UNIT A FLOOR EL 925.5 (below ground here)", size=3.6, color=GREY, ha="right", z=12, box=True)
    # the neighbour's view of the building
    yard = 931.0
    line(ax, [(L - 17, yard), (L + 3.2, yard)], lw=0.5, color=GREY, ls=(0, (6, 2)), z=12)
    txt(ax, L - 16.8, yard + 0.55, "386 FOREST AVE YARD ±EL 931 (10 ft beyond the line, west half)", size=3.7, color=GREY, ha="left", z=12)
    dim(ax, (L - 5.5, yard), (L - 5.5, m.EL_PLATE), 0, f"{ftin(m.EL_PLATE - yard)} EAVE", ext=False, size=4.0, side=-1)
    line(ax, [(L - 6.2, m.EL_PLATE), (L - 4.8, m.EL_PLATE)], lw=0.3, z=8)
    txt(ax, 6.5, Z_EAVE_R - FASCIA / 2, "12 in. EAVE, 1-HOUR SOFFIT, GUTTER", size=3.5, z=11)
    txt(ax, 17.0, 947.0, "ASPHALT SHINGLES, 4:12", size=4.2, z=11)
    txt(ax, 3.0, 936.9, "EAST\n(441 Baird\nside)", size=4.0, color=GREY)
    txt(ax, L - 3.0, 940.5, "WEST\n(442 Baird\nside)", size=4.0, color=GREY)
    note(ax, (-3.0, 930.5), (-3.2, 956.6), "EAST WALL AND PORCH ENDS\nseen at an angle beyond the corner", size=3.7, ha="center", color=GREY)
    he = -(50 - m.XE) / CT
    lot_line(ax, he, yl[0] + 0.6, 918.0)
    txt(ax, he + 0.4, 913.2, "EAST LOT LINE\n5'-2\" from the wall", size=3.8, color=ACCENT, ha="left")
    txt(ax, L + 3.3, 913.2, "WEST LOT LINE\n5'-2\" beyond\nthe corner  >", size=3.8, color=ACCENT, ha="right")


def sheet_a201(pdf):
    ag = m.avg_grade()
    notes = [
        ("1 Front (south) elevation", [
            "Seen from Baird Street. 442 Baird (uphill)",
            "is on the left, 441 Baird on the right.",
            f"Garage: one opening {ftin(m.OPEN_W)} wide, {fi(m.OPEN_CLEAR_H)} clear",
            "under steel beam B1, no doors. It is",
            f"{m.GARAGE_PCT:.0f} % of the {ftin(m.FACADE_W)} facade (65 % max).",
            "West of the opening the front yard stays at",
            "natural grade, so the concrete pier and the",
            "west wall are buried below about EL 922.",
        ]),
        ("2 Rear (north) elevation", [
            "Seen from 386 Forest Ave. The rear wall is",
            f"skewed {abs(m.REAR_ANGLE):.1f}° in plan and is drawn at its",
            f"true length, {ftin(m.REAR_WALL_LEN)}. Existing ground at the",
            f"wall runs from EL {elev(m.XE, NE[1]):.1f} (east) to {elev(*NW):.1f}",
            f"(west), up to {elev(*NW) - m.EL_A:.1f} ft above the Unit A floor.",
            f"From the neighbour's yard (±EL 931) the eave",
            f"is {ftin(m.EL_PLATE - 931)} up and the ridge {ftin(m.EL_RIDGE_HI - 931)}.",
        ]),
        ("Heights", [
            f"Garage slab {m.EL_GAR:.1f} · Unit A {m.EL_A:.1f} · Unit B {m.EL_B:.1f}",
            f"Top plate {m.EL_PLATE:.2f} · eave (truss top) {EAVE:.2f}",
            f"Ridge {m.EL_RIDGE_LO:.2f} (east) to {m.EL_RIDGE_HI:.2f} (west)",
            f"Average existing grade, 4 corners: EL {ag:.1f}",
            f"Height to the ridge {ftin(m.EL_RIDGE_HI - ag)}; limit 35'-0\".",
        ]),
        ("Exterior materials (rental grade)", [
            "Walls: fibre-cement or vinyl lap siding on",
            "2x6 framing. Base: exposed concrete.",
            "Roof: asphalt shingles, 4:12, gutters front",
            "and rear. Windows: vinyl. Guards: 36 in.,",
            "balusters under 4 in. apart.",
        ]),
        ("Confirm before pricing", [
            "Ground lines are from 1 m state LiDAR, not",
            "a survey: every grade here is ±0.5 ft.",
            "Window W3 sill, fascia depth, site wall",
            "tops and the trash screen are assumed.",
            "Wall caps for fans, dryer and range hood",
            "are on M-102 and M-103.",
        ]),
    ]
    fig, bg = new_sheet("A-201", TITLE["A-201"], "As noted", notes)
    yl = (910.5, 959.5)
    xl1, xl2 = (-2.6, 53.2), (-8.6, 39.9)
    w1, w2 = (xl1[1] - xl1[0]) / 8, (xl2[1] - xl2[0]) / 8
    gap = (SHEET_W - 2 * MARGIN - TB_W - w1 - w2) / 3
    l1 = MARGIN + gap
    l2 = l1 + w1 + gap
    b1 = 4.42
    ax = plan_axes(fig, l1, b1, xl1, yl, 8.0)
    front_elev(ax, xl1, yl)
    front_labels(ax, xl1, yl)
    title_under(bg, (l1, b1), 1, "Front (south) elevation", f"{SCALE8} · from Baird Street, looking north · elevations NAVD88 ft (LiDAR)")
    ax2 = plan_axes(fig, l2, b1, xl2, yl, 8.0)
    wins, ct, ll = rear_elev(ax2, xl2, yl)
    rear_labels(ax2, xl2, yl, wins, ct, ll)
    title_under(bg, (l2, b1), 2, "Rear (north) elevation", f"{SCALE8} · from 386 Forest Ave, square to the rear wall")
    # --- 3: garage front at 3/16 in.
    xl3, yl3 = (3.6, 48.4), (911.6, 928.4)
    b3 = 0.78
    ax3 = plan_axes(fig, l1, b3, xl3, yl3, 16 / 3)
    front_elev(ax3, xl3, yl3, big=True)
    garage_front_labels(ax3, xl3, yl3)
    title_under(bg, (l1, b3), 3, "Garage front, enlarged", f"{SCALE316} · opening, beam B1 bearings, post and street door")
    # --- opening legend
    rows = [("Mark", "Opening (from A-601)", "Sill", "Head")]
    for tag in sorted(m.WINDOW_TYPES):
        w, h, s = wtype(tag)
        kind = m.WINDOW_TYPES[tag].split("vinyl ")[1].split(",")[0]
        rows.append((tag, f"{fi(w)} x {fi(h)} {kind}", fi(s) + ("*" if tag == "W3" else ""), fi(s + h)))
    rows.append(("D14", "3'-0\" x 6'-8\" full-glass porch door", "floor", "6'-8\""))
    rows.append(("Street", "3'-0\" x 6'-8\" stair door, garage level", "slab", "6'-8\""))
    tx = l1 + (xl3[1] - xl3[0]) / (16 / 3) + 0.3
    bg.text(tx, 3.78, "OPENINGS ON THESE ELEVATIONS", fontsize=7.0, fontweight="bold", va="top")
    y = table(bg, tx, 3.58, [0.42, 2.25, 0.5, 0.5], rows, fs=5.4, rh=0.185)
    bg.text(tx, y - 0.1, "Sill and head are above the finished floor of the flat. Both flats\nhave the same openings.  * W3 sill is assumed: confirm on A-601.\n"
            "Unit A ceiling is 7'-10\": heads at 7'-6\" leave 4 in., so the\nwindow headers must go up into the floor truss rim (S-204).",
            fontsize=5.4, va="top", linespacing=1.3)
    save(fig, "A-201", pdf)


def garage_front_labels(ax, xl, yl):
    XE = m.XE
    g = m.EL_GAR
    zb = g - 1.55
    st = [X0, m.OPEN[0], m.COL_X[1], m.OPEN[1], m.ENTRY[0], m.ENTRY[1], XE]
    for a, b in zip(st[:-1], st[1:]):
        dim(ax, (a, zb), (b, zb), 0, fi(b - a, 2), ext=False, size=4.8)
    for a in st:
        line(ax, [(a, zb), (a, g - 0.15)], lw=0.25, color=GREY, z=9)
    dim(ax, (m.OPEN[0], zb - 1.0), (m.OPEN[1], zb - 1.0), 0, f"GARAGE OPENING {ftin(m.OPEN_W)}", ext=False, size=5.2)
    txt(ax, (m.COL_X[1] + m.OPEN[0]) / 2, zb + 0.75, "to the post centre", size=4.0, color=GREY, z=12)
    xh = 34.9
    dim(ax, (xh, g), (xh, Z_B1_BOT), 0, f"{fi(m.OPEN_CLEAR_H)} CLEAR", ext=False, size=4.8)
    dim(ax, (xh, Z_B1_BOT), (xh, m.EL_B1_TOP), 0, "14\"", ext=False, size=4.4)
    dim(ax, (xh, m.EL_B1_TOP), (xh, m.EL_A), 0, "20 3/4\"", ext=False, size=4.4)
    dim(ax, (XE + 1.9, g), (XE + 1.9, m.EL_A), 0, fi(m.EL_A - g), ext=False, size=4.8, side=-1)
    for el in (g, m.EL_A):
        line(ax, [(XE + 0.2, el), (XE + 2.3, el)], lw=0.25, color=GREY, z=9)
    txt(ax, XE + 3.4, m.EL_A + 0.45, f"UNIT A\nEL {m.EL_A:.1f}", size=4.4, weight="bold", ha="right", va="bottom", z=12)
    txt(ax, XE + 3.4, g - 0.3, f"SLAB\nEL {g:.1f}", size=4.4, weight="bold", ha="right", va="top", z=12)
    for i, c in enumerate(m.CARS):
        txt(ax, c + m.CAR_W / 2, g + 2.6, f"STALL {i + 1}\n{fi(m.CAR_W)} car", size=4.4, color=GREY, z=9)
    note(ax, (17.0, (Z_B1_BOT + m.EL_B1_TOP) / 2), (19.0, g + 6.4),
         f"B1: W14x34 (prelim.), top EL {m.EL_B1_TOP:.2f}, underside EL {Z_B1_BOT:.2f}", size=4.6, ha="left")
    note(ax, (m.COL_X[0], m.EL_B1_TOP - 0.3), (6.2, 926.6), "B1 bears on the concrete\nreturn pier", size=4.4, ha="left")
    note(ax, (m.COL_X[2], m.EL_B1_TOP - 0.3), (39.2, 926.6), "B1 bears on the lobby\nwall pier", size=4.4, ha="left")
    note(ax, (m.COL_X[1] + 0.25, g + 5.3), (29.6, g + 5.0), "HSS 6x6 post\n(prelim.) on its\nown footing", size=4.4, ha="left")
    note(ax, (9.4, 922.9), (4.0, 920.4), "Top of concrete EL 923.77.\nGround at the front wall is\nabout EL 922 here", size=4.2, ha="left")
    note(ax, (12.5, 919.0), (4.0, 917.2), "Wing wall (C-107):\ntop 6 in. above the\nyard it retains", size=4.2, ha="left")
    txt(ax, (m.ENTRY[0] + m.ENTRY[1]) / 2, g + 1.9, "STREET\nDOOR\n3'-0\" x\n6'-8\"", size=4.2, z=9)
    note(ax, (37.6, g + 4.0), (37.9, g + 8.2), "8 in. concrete or grouted-block lobby wall", size=4.2, ha="left")
    txt(ax, 24.3, m.EL_A - 0.85, "UNIT A PORCH FASCIA (20 in. floor trusses cantilever 4'-0\" over B1, see A-402)", size=4.2, z=11)
    note(ax, (30.0, g), (22.0, g - 0.75), "Trench drain across the opening, slab falls 1/8 in./ft to it", size=4.2, ha="left", color=BLUE)


# ---SHEETS---
SHEETS = [("A-201", sheet_a201)]
