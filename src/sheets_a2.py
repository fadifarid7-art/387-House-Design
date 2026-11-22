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
T_CONC = m.EL_B1_TOP                       # top of the garage walls: 1 1/2 in. sill plate under the trusses, like the nailer on B1
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


def ftd(v):
    """Feet-inches rounded DOWN to the inch (clear heights)."""
    tot = int(math.floor(v * 12 + 1e-6))
    return f"{tot // 12}'-{tot % 12}\""


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
            if not (ax.get_ylim()[0] < fl + sill + hgt and fl + sill < ax.get_ylim()[1]):
                continue
            window(ax, hc - d, hc + d, fl + sill, fl + sill + hgt, m.WINDOW_TYPES[tag],
                   fc="#e9eef2" if light else GLASS, ec=GREY if light else INK, lw=0.4 if light else 0.6)
            if tags and not light and fl + sill - 1.5 * K(ax) > ax.get_ylim()[0] and fl + sill < ax.get_ylim()[1]:
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
    rect(ax, m.COL_X[0] - 0.25, m.EL_B1_TOP, m.SHAFT_X0, A_T0, fc=WOODC, ec=INK, lw=0.3, z=4)
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
    note(ax, (XE + OH_S, m.ridge_el(XE)), (XE - 3.0, 951.0), f"RIDGE (EAST) EL {m.EL_RIDGE_LO:.1f}", size=4.2, ha="right")
    # zoning height: mean roof level (midway between the eave and the highest ridge) above average grade
    zm = ag + m.zoning_height()
    line(ax, [(X0 - 1, ag + 35), (XE + 4.4, ag + 35)], color=ACCENT, lw=0.7, ls=(0, (4, 3)), z=12)
    txt(ax, (X0 + XE) / 2, ag + 35.75, f"35 FT ZONING HEIGHT LIMIT = EL {ag + 35:.1f}  (average existing grade at the four corners EL {ag:.1f} + 35 ft)",
        size=4.4, color=ACCENT)
    line(ax, [(XE - 9, zm), (XE + 4.4, zm)], color=ACCENT, lw=0.5, ls=(0, (4, 3)), z=12)
    txt(ax, XE - 0.5, zm + 0.5, f"MEAN ROOF LEVEL EL {zm:.1f}", size=3.7, color=ACCENT, ha="right", z=12)
    dim(ax, (XE + 3.7, ag), (XE + 3.7, zm), 0, f"ZONING HEIGHT {ftin(m.zoning_height())} (avg. grade to mean roof)", ext=False, size=4.0, color=ACCENT, side=-1)
    dim(ax, (XE + 3.7, zm), (XE + 3.7, ag + 35), 0, f"{ftin(35 - m.zoning_height())} SPARE", ext=False, size=4.0, color=ACCENT, side=-1)
    line(ax, [(XE - 4, ag), (XE + 4.4, ag)], color=ACCENT, lw=0.5, ls=(0, (4, 3)), z=12)
    txt(ax, XE + 0.3, ag - 0.6, f"AVG. GRADE EL {ag:.1f}", size=3.7, color=ACCENT, ha="left", z=12)
    # widths
    dim(ax, (X0, 953.2), (XE, 953.2), 0, f"FACADE {ftin(m.FACADE_W)}", ext=False, size=4.6)
    dim(ax, (0, 953.2), (X0, 953.2), 0, ftin(X0), ext=False, size=4.2, color=ACCENT)
    dim(ax, (XE, 953.2), (50, 953.2), 0, ftin(50 - XE), ext=False, size=4.2, color=ACCENT)
    # heights on the east side of the facade
    xd = 46.3
    dim(ax, (xd, m.EL_GAR), (xd, m.EL_A), 0, fi(m.EL_A - m.EL_GAR), ext=False, size=4.2, side=-1)
    dim(ax, (xd, m.EL_A), (xd, m.EL_B), 0, fi(m.EL_B - m.EL_A), ext=False, size=4.2, side=-1)
    dim(ax, (xd, m.EL_B), (xd, m.EL_PLATE), 0, fi(m.EL_PLATE - m.EL_B, 8), ext=False, size=4.2, side=-1)
    for el in (m.EL_GAR, m.EL_A, m.EL_B, m.EL_PLATE):
        line(ax, [(XE + 0.2, el), (xd + 0.5, el)], lw=0.25, color=GREY, z=8)
    # call-outs
    txt(ax, 20.0, Z_B1_BOT + 0.58, "STEEL BEAM B1, DROPPED UNDER THE FLOOR TRUSSES", size=3.6, color=PAPER, z=9)
    txt(ax, 19.6, 920.9, f"OPEN GARAGE, NO DOORS · {ftin(m.OPEN_W)} x {ftin(m.OPEN_CLEAR_H)} CLEAR", size=4.2, weight="bold", z=9)
    note(ax, (m.COL_X[1], 919.2), (29.6, 918.6), "HSS 6x6\nPOST", size=3.8, ha="left")
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
    txt(ax, 17.0, 940.6, "FIBRE-CEMENT OR VINYL LAP SIDING", size=3.8, z=9, box=True)
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
    w5 = [q for q in wins if q[0] == "W5" and q[3] < m.EL_B][0]
    w1 = [q for q in wins if q[0] == "W1" and q[3] < m.EL_B][0]
    note(ax, (w5[1] - 1.5, w5[3] + 0.1), (29.0, 934.1), f"W5 SILL EL {w5[3]:.1f}: 54 in. above the Unit A\nfloor, clear of the stem wall and ground", size=3.8, ha="right")
    note(ax, (w1[1] + 1.17, w1[3] + 2), (12.3, 931.6), f"W1 ESCAPE WINDOW\nSILL EL {w1[3]:.1f}", size=3.8, ha="left")
    note(ax, (24.0, np.interp(24.0, [c[0] for c in ct], [c[1] for c in ct]) - 0.25), (16.5, 923.2),
         "CONCRETE STEM WALL carried to 8 in.\nabove finish grade, siding starts there", size=3.8, ha="center")
    note(ax, (20.5, np.interp(20.5, [c[0] for c in ll], [c[1] for c in ll])), (14.0, 937.6),
         "EXISTING GROUND AT THE REAR LOT LINE (dotted red)\n5'-2\" in front of this wall; 6 ft fence on the line not drawn", size=3.8, ha="center", color=ACCENT)
    txt(ax, 13.0, 918.6, "dashed brown: existing ground at the wall · solid: finish grade, cut 6 in. for the swale that falls east",
        size=3.7, color=EARTH, z=12)
    txt(ax, 18.3, 916.6, "dashed grey: bottom of the stem-wall footing, 36 in. min. below finish grade (S-101)", size=3.7, color=GREY, z=12)
    txt(ax, L - 0.4, m.EL_A - 0.55, "UNIT A FLOOR EL 925.5 (below ground here)", size=3.6, color=GREY, ha="right", z=12, box=True)
    # the neighbour's view of the building
    yard = 931.0
    line(ax, [(L - 2.6, yard), (L + 3.2, yard)], lw=0.5, color=GREY, ls=(0, (6, 2)), z=12)
    dim(ax, (L - 1.5, yard), (L - 1.5, m.EL_PLATE), 0, f"{ftin(m.EL_PLATE - yard)}", ext=False, size=4.0)
    note(ax, (L - 1.5, 937.6), (29.0, 937.6), f"EAVE {ftin(m.EL_PLATE - yard)} ABOVE THE YARD OF 386 FOREST AVE\n(±EL 931, 10 ft beyond the lot line at the west half)", size=3.8, ha="right", dot=False)
    txt(ax, 6.5, Z_EAVE_R - FASCIA / 2, "12 in. EAVE, 1-HOUR SOFFIT, GUTTER", size=3.5, z=11)
    txt(ax, 17.0, 947.0, "ASPHALT SHINGLES, 4:12", size=4.2, z=11)
    txt(ax, 4.2, 941.6, "< EAST (441 Baird side)", size=4.0, color=GREY)
    txt(ax, 24.5, 941.6, "WEST (442 Baird side) >", size=4.0, color=GREY)
    note(ax, (-3.0, 930.5), (-3.2, 956.6), "EAST WALL AND PORCH ENDS\nseen at an angle beyond the corner", size=3.7, ha="center", color=GREY)
    he = -(50 - m.XE) / CT
    lot_line(ax, he, yl[0] + 0.6, 918.0)
    txt(ax, he + 0.4, 913.2, "EAST LOT LINE\n5'-2\" from the wall", size=3.8, color=ACCENT, ha="left")
    txt(ax, L + 3.3, 913.2, "WEST LOT LINE\n5'-2\" beyond\nthe corner  >", size=3.8, color=ACCENT, ha="right")


def sheet_a201(pdf):
    ag = m.avg_grade()
    notes = [
        ("1 Front (south) elevation", [
            "From Baird Street. 442 Baird (uphill) is on",
            f"the left. Garage opening {ftin(m.OPEN_W)} x {ftin(m.OPEN_CLEAR_H)}",
            f"clear, no doors: {m.GARAGE_PCT:.0f} % of the {ftin(m.FACADE_W)} facade",
            "(65 % max). The front yard west of the apron",
            "stays at natural grade, so the west pier and",
            "wall are buried below about EL 922.",
        ]),
        ("2 Rear (north) elevation", [
            "From 386 Forest Ave. The wall is skewed",
            f"{abs(m.REAR_ANGLE):.1f}° in plan and drawn at its true length.",
            f"Existing ground at the wall: EL {elev(m.XE, NE[1]):.1f} (east)",
            f"to {elev(*NW):.1f} (west), up to {elev(*NW) - m.EL_A:.1f} ft above the",
            "Unit A floor. From the neighbour's yard",
            f"(±EL 931) the eave is {ftin(m.EL_PLATE - 931)} up and the",
            f"ridge {ftin(m.EL_RIDGE_HI - 931)}.",
        ]),
        ("Heights", [
            f"Slab {m.EL_GAR:.1f} · Unit A {m.EL_A:.1f} · Unit B {m.EL_B:.1f}",
            f"Top plate {m.EL_PLATE:.2f} · truss top at eave {EAVE:.2f}",
            f"Ridge {m.EL_RIDGE_LO:.2f} (east) to {m.EL_RIDGE_HI:.2f} (west)",
            f"Average existing grade at 4 corners {ag:.1f}",
            f"Zoning height (mean roof) {ftin(m.zoning_height())}; limit 35 ft",
        ]),
        ("Confirm before pricing", [
            "Ground is 1 m state LiDAR, not a survey:",
            "every grade here is ±0.5 ft.",
            "Assumed here: W3 sill, 6 in. fascia, site",
            "wall tops, trash screen height.",
            "Side walls are 5'-2\" square to the side lot",
            "lines. Wall caps for fans: M-102, M-103.",
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
    xh = 34.9
    dim(ax, (xh, g), (xh, Z_B1_BOT), 0, f"{ftin(m.OPEN_CLEAR_H)} CLEAR", ext=False, size=4.8)
    dim(ax, (xh, Z_B1_BOT), (xh, m.EL_B1_TOP), 0, "14\"", ext=False, size=4.4)
    dim(ax, (xh, m.EL_B1_TOP), (xh, m.EL_A), 0, inch((m.EL_A - m.EL_B1_TOP) * 12, 4) + "\"", ext=False, size=4.4)
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
    note(ax, (9.4, 922.9), (4.0, 920.4), f"Top of concrete EL {T_CONC:.2f}.\nGround at the front wall is\nabout EL 922 here", size=4.2, ha="left")
    note(ax, (12.5, 919.0), (4.0, 917.2), "Wing wall (C-107):\ntop 6 in. above the\nyard it retains", size=4.2, ha="left")
    txt(ax, (m.ENTRY[0] + m.ENTRY[1]) / 2, g + 1.9, "STREET\nDOOR\n3'-0\" x\n6'-8\"", size=4.2, z=9)
    note(ax, (37.6, g + 4.0), (37.9, g + 8.2), "8 in. concrete or grouted-block lobby wall", size=4.2, ha="left")
    txt(ax, 24.3, m.EL_A - 0.85, "UNIT A PORCH FASCIA (20 in. floor trusses cantilever 4'-0\" over B1, see A-402)", size=4.2, z=11)
    txt(ax, 24.3, g - 0.42, "TRENCH DRAIN ACROSS THE OPENING · SLAB FALLS 1/8 in./ft TO IT · DIMENSIONS ARE TO THE POST CENTRE", size=3.9, color=BLUE, z=12)


# ----------------------------------------------------------------------------
# 3. A-202: side elevations and side-yard sections
# ----------------------------------------------------------------------------
def rake(ax, a, r, b, ec=INK, z=5):
    """Gable rake board and roof edge through eave a, ridge r, eave b."""
    poly(ax, [a, r, b, (b[0], b[1] - FASCIA), (r[0], r[1] - FASCIA * 1.06), (a[0], a[1] - FASCIA)], fc=PAPER, ec=ec, lw=0.7, z=z)
    line(ax, [a, r, b], lw=1.5, color="#5c6269", z=z + 0.1)


def porch_end(ax, h_out, h_wall, fl, bot):
    rect(ax, min(h_out, h_wall), bot, max(h_out, h_wall), fl, fc=WOODC, ec=INK, lw=0.7, z=5)
    d = 0.2 if h_out < h_wall else -0.2
    guard(ax, min(h_out + d, h_wall), max(h_out + d, h_wall), fl, posts=1)


def east_elev(ax, xl, yl):
    XE, y0, y1, yNW = m.XE, m.YF, NE[1], NW[1]
    # --- beyond the north-east corner: the skewed rear wall, its roof slope and the west gable
    xs = np.linspace(XE, NW[0], 24)
    siding(ax, [(y1, m.EL_A), (yNW, m.EL_A), (yNW, Z_SOFFIT_R), (y1, Z_SOFFIT_R)], fc=BEYOND, ec=GREY, lw=0.5, z=2)
    poly(ax, [(y1, yl[0])] + [(m.yr_o(x), ct_rear(x)) for x in xs] + [(yNW, yl[0])], fc="#d6d9dd", ec=GREY, lw=0.5, z=2.1)
    wall_windows(ax, "N", lambda s_: m.yr_o(s_), light=True)
    poly(ax, [(p[1], roof_z(*p)) for p in (RG_E, RG_W, R_NW, R_NE)], fc="#dcdfe3", ec=GREY, lw=0.5, z=2.2)
    rect(ax, R_NE[1], Z_SOFFIT_R, R_NW[1], Z_EAVE_R, fc=PAPER, ec=GREY, lw=0.5, z=2.3)
    # --- east wall: 12 in. concrete garage wall below, frame wall and gable above
    ry, rz = m.ridge_y(XE), m.ridge_el(XE)
    siding(ax, [(y0, T_CONC), (y1, T_CONC), (y1, EAVE), (ry, rz), (y0, EAVE)])
    rect(ax, y0, yl[0], y1, T_CONC, fc=CONC_FC, lw=0.8, z=3)
    line(ax, [(y0, B_T1), (y1, B_T1)], lw=0.3, color=GREY, z=3.2)
    rake(ax, (R_SE[1], Z_EAVE_F), (RG_E[1], roof_z(*RG_E)), (R_NE[1], roof_z(*R_NE)))
    line(ax, [(R_SE[1], Z_SOFFIT_F), (y0, Z_SOFFIT_F)], lw=0.6, z=5)
    porch_end(ax, m.PORCH[1], y0, m.EL_A, A_T0)
    porch_end(ax, m.PORCH[1], y0, m.EL_B, B_T0)
    # --- meter stack
    ym = m.E_METER[1]
    g = elev(XE, ym)
    rect(ax, ym - METER_W / 2, g + METER_CL - METER_H + 1.0, ym + METER_W / 2, g + METER_CL + 1.0, fc="#d6dbe0", ec=INK, lw=0.6, z=5)
    for dy in (-0.55, 0.55):
        ax.add_patch(plt.Circle((ym + dy, g + METER_CL), 0.32, fc=PAPER, ec=INK, lw=0.4, zorder=5.1))
    # --- ground along the east wall (the side yard is not regraded) and the street
    gl = [(y, elev(XE, y)) for y in np.linspace(xl[0], xl[1], 60)]
    earth(ax, gl, yl[0])
    # hidden below grade: garage slab, footing, the entry landing behind the low wall, water entry
    line(ax, [(m.LAND_Y0, m.EL_GAR), (m.Y_GR_I, m.EL_GAR)], lw=0.5, color=GREY, ls=DASH, z=8)
    line(ax, [(m.TRASH[1], m.EL_GAR), (m.TRASH[1], elev(XE, m.TRASH[1]))], lw=0.5, color=GREY, ls=DASH, z=8)
    line(ax, [(y0, elev(XE, y0)), (y0, m.EL_FTG_TOP), (y1, m.EL_FTG_TOP), (y1, elev(XE, y1))], lw=0.5, color=GREY, ls=DASH, z=8)
    ax.add_patch(plt.Circle((m.WATER_ENTRY[1], m.EL_WATER_ENTRY), 0.3, fc=PAPER, ec=BLUE, lw=0.7, zorder=9))
    return gl


def east_labels(ax, xl, yl):
    XE, y0, y1 = m.XE, m.YF, NE[1]
    ry = m.ridge_y(XE)
    lot_line(ax, 0.0, yl[0] + 1.0, 952.0)
    txt(ax, -0.5, 946.0, "FRONT LOT LINE", size=4.4, color=ACCENT, rot=90)
    lot_line(ax, LOT_NE[1], yl[0] + 1.0, 945.0)
    txt(ax, LOT_NE[1] + 0.55, 938.6, "REAR LOT LINE at the lot corner", size=4.2, color=ACCENT, rot=90)
    for el, nm, et in ((m.EL_A, "UNIT A FLOOR", None), (m.EL_B, "UNIT B FLOOR", None), (m.EL_PLATE, "TOP PLATE", None)):
        lvl(ax, -2.0, el, nm, ha="right", size=4.3, el_txt=et, line_to=m.PORCH[1] if el < m.EL_PLATE else R_SE[1])
    note(ax, (ry, m.ridge_el(XE)), (ry - 6.5, 951.6), f"RIDGE AT THE EAST WALL EL {m.EL_RIDGE_LO:.1f}", size=4.2, ha="right")
    note(ax, (RG_W[1], roof_z(*RG_W)), (RG_W[1] + 3.0, 952.6), f"RIDGE AT THE WEST GABLE (beyond) EL {m.EL_RIDGE_HI:.2f}", size=4.0, ha="left", color=GREY)
    zt = 955.6
    dim(ax, (0, zt), (y0, zt), 0, ftin(y0), ext=False, size=4.2, color=ACCENT)
    dim(ax, (y0, zt), (ry, zt), 0, ftin(ry - y0), ext=False, size=4.2)
    dim(ax, (ry, zt), (y1, zt), 0, ftin(y1 - ry), ext=False, size=4.2)
    dim(ax, (y0, zt + 1.5), (y1, zt + 1.5), 0, f"EAST WALL {ftin(y1 - y0)}", ext=False, size=4.6)
    for y in (y0, ry, y1):
        line(ax, [(y, zt - 0.3), (y, zt + 1.8 if y != ry else zt + 0.3)], lw=0.25, color=GREY, z=8)
    txt(ax, ry, zt - 1.0, "ridge at mid-depth", size=3.8, color=GREY)
    dim(ax, (m.PORCH[1], B_T0 - 0.75), (y0, B_T0 - 0.75), 0, "4'-0\"", ext=False, size=4.0)
    dim(ax, (R_SE[1], Z_SOFFIT_F - 0.8), (y0, Z_SOFFIT_F - 0.8), 0, "4'-0\"", ext=False, size=4.0)
    note(ax, (m.PORCH[1] + 1.0, m.EL_B + 1.5), (-3.0, 940.3), "PORCH ENDS: 4'-0\"\ncantilever, 36 in. guard", size=3.9, ha="center")
    note(ax, (R_SE[1] + 0.8, Z_EAVE_F - 0.2), (-3.2, 949.2), "ROOF OVERHANGS\nTHE FRONT 4'-0\"", size=3.9, ha="center")
    yd = 22.5
    dim(ax, (yd, m.EL_GAR), (yd, m.EL_A), 0, fi(m.EL_A - m.EL_GAR), ext=False, size=4.2)
    dim(ax, (yd, m.EL_A), (yd, m.EL_B), 0, fi(m.EL_B - m.EL_A), ext=False, size=4.2)
    dim(ax, (yd, m.EL_B), (yd, m.EL_PLATE), 0, fi(m.EL_PLATE - m.EL_B, 8), ext=False, size=4.2)
    for el in (m.EL_A, m.EL_PLATE):
        line(ax, [(yd - 0.6, el), (yd + 0.6, el)], lw=0.3, z=8)
    g0 = elev(XE, y0 + 1.0)
    dim(ax, (y0 + 0.6, g0), (y0 + 0.6, T_CONC), 0, ftin(T_CONC - g0), ext=False, size=4.0, side=-1)
    note(ax, (y0 + 4.0, 922.8), (y0 + 6.2, 928.2), f"EXPOSED CONCRETE (12 in. garage wall)\ntop EL {T_CONC:.2f}, {ftin(T_CONC - elev(XE, y0))} above ground at the\nfront corner, 8 in. at the rear corner", size=3.9, ha="left")
    ym = m.E_METER[1]
    note(ax, (ym + METER_W / 2, elev(XE, ym) + METER_CL + 0.6), (ym + 3.6, 933.0), "2-POSITION METER STACK\nmeters 5'-0\" above grade (E-101)", size=3.9, ha="left")
    txt(ax, 17.0, 940.2, "NO WINDOWS ON THIS WALL\nlap siding on 2x6 framing", size=4.0, z=9, box=True)
    note(ax, (37.0, 941.0), (37.5, 949.4), "REAR WALL (skewed) AND\nWEST GABLE, BEYOND", size=3.9, ha="center", color=GREY)
    txt(ax, 19.5, m.EL_GAR + 0.55, f"GARAGE SLAB EL {m.EL_GAR:.1f} (hidden: this wall retains the side yard)", size=3.8, color=GREY, z=12)
    txt(ax, 20.0, m.EL_FTG_TOP - 0.6, f"TOP OF FOOTING EL {m.EL_FTG_TOP:.1f}", size=3.8, color=GREY, z=12)
    note(ax, (m.WATER_ENTRY[1], m.EL_WATER_ENTRY), (m.WATER_ENTRY[1] + 2.2, 918.6), f"TWO 1 in. WATER SERVICES ENTER\nBELOW GRADE, EL {m.EL_WATER_ENTRY:.1f} (C-106, P-101)", size=3.8, ha="left", color=BLUE)
    note(ax, (5.5, m.EL_GAR), (3.2, 912.2), "ENTRY LANDING AND TRASH BAY EL 914.5,\nbehind the low wall (C-107)", size=3.8, ha="center", color=GREY)
    txt(ax, -8.8, street_el(XE) + 1.3, "BAIRD ST", size=4.0, color=GREY, ha="left", z=12)
    txt(ax, 38.3, elev(XE, 38.3) - 1.3, "386 FOREST AVE", size=4.0, color=GREY, ha="left", z=12)
    txt(ax, 5.2, 920.6, "EXISTING = FINISH GRADE\nalong the east wall", size=3.8, color=EARTH, z=12)


def west_elev(ax, xl, yl):
    L = m.WEST_WALL_LEN
    hw = lambda y: h_west(m.xw_o(y), y)                        # noqa: E731
    ys = np.linspace(m.YF, NW[1], 40)
    ct = [(hw(y), ct_west(y)) for y in ys]
    siding(ax, ct + [(-L, EAVE), (h_west(*RG_WW), roof_z(*RG_WW)), (0, EAVE)])
    poly(ax, [(0, yl[0])] + ct + [(-L, yl[0])], fc=CONC_FC, ec=INK, lw=0.8, z=3.3)
    line(ax, [(0, B_T1), (-L, B_T1)], lw=0.3, color=GREY, z=3.2)
    wins = wall_windows(ax, "W", hw)
    rake(ax, (h_west(*R_SW), Z_EAVE_F), (h_west(*RG_W), roof_z(*RG_W)), (h_west(*R_NW), roof_z(*R_NW)))
    hp_ = h_west(m.PORCH[0], m.PORCH[1])
    line(ax, [(h_west(*R_SW), Z_SOFFIT_F), (0, Z_SOFFIT_F)], lw=0.6, z=5)
    porch_end(ax, hp_, 0.0, m.EL_A, A_T0)
    porch_end(ax, hp_, 0.0, m.EL_B, B_T0)
    # heat pumps on pads in the side yard (in front of the wall)
    w = m.HP_SIZE[0]
    for (hx, hy) in m.HP:
        hc, g = h_west(hx, hy), elev(hx, hy)
        rect(ax, hc - w / 2 - 0.25, g - 0.05, hc + w / 2 + 0.25, g + 0.33, fc=CONC_FC, ec=INK, lw=0.5, z=8.5)
        rect(ax, hc - w / 2, g + 0.33, hc + w / 2, g + 0.33 + HP_H, fc="#eef0f2", ec=INK, lw=0.7, z=8.5)
        ax.add_patch(plt.Circle((hc - 0.35, g + 0.33 + HP_H / 2), 0.85, fc=PAPER, ec=INK, lw=0.4, zorder=8.6))
    # ground along the wall line, continued to the street and to the rear lot line
    ya = np.linspace(-9.0, 49.0, 70)
    ex = [(hw(y), elev(m.xw_o(y), y)) for y in ya]
    fin = [(hw(y), fg_west(y) if y <= NW[1] else elev(m.xw_o(y), y) - SWALE_CUT * max(0.0, 1 - (y - NW[1]) / 2.5)) for y in ya]
    earth(ax, fin[::-1], yl[0])
    line(ax, ex, lw=0.8, color=EARTH, ls=DASH, z=8)
    # hidden: garage slab, garage rear wall, footing; Unit A floor where it is below ground
    hg = hw(m.Y_GR_O)
    line(ax, [(0, m.EL_GAR), (hw(m.Y_GR_I), m.EL_GAR)], lw=0.5, color=GREY, ls=DASH, z=8)
    line(ax, [(0, elev(X0, m.YF)), (0, m.EL_FTG_TOP), (hg, m.EL_FTG_TOP), (hg, ct_west(m.Y_GR_O))], lw=0.5, color=GREY, ls=DASH, z=8)
    yb = [y for y in ys if fg_west(y) > m.EL_A]
    if yb:
        line(ax, [(hw(min(yb)), m.EL_A), (-L, m.EL_A)], lw=0.5, color=GREY, ls=DASH, z=8)
    return wins, ct


def west_labels(ax, xl, yl, wins, ct):
    L = m.WEST_WALL_LEN
    hw = lambda y: h_west(m.xw_o(y), y)                        # noqa: E731
    hr = h_west(*RG_WW)
    hf = hw(0.0)
    yr = _fix(lambda y: rear_y(m.xw_o(y)), 45.0)
    hb = hw(yr)
    lot_line(ax, hf, yl[0] + 1.0, 952.0)
    txt(ax, hf + 0.5, 946.0, "FRONT LOT LINE", size=4.4, color=ACCENT, rot=90)
    lot_line(ax, hb, yl[0] + 1.0, 952.0)
    txt(ax, hb - 0.5, 946.0, "REAR LOT LINE", size=4.4, color=ACCENT, rot=90)
    for el, nm in ((m.EL_A, "UNIT A FLOOR"), (m.EL_B, "UNIT B FLOOR"), (m.EL_PLATE, "TOP PLATE")):
        lvl(ax, 5.0, el, nm, ha="left", size=4.3, line_to=h_west(m.PORCH[0], m.PORCH[1]) if el < m.EL_PLATE else h_west(*R_SW))
    note(ax, (hr, roof_z(*RG_WW)), (hr + 7.5, 952.0), f"RIDGE AT THE WEST GABLE EL {m.EL_RIDGE_HI:.2f}", size=4.2, ha="left")
    zt = 955.6
    dim(ax, (-L, zt), (hr, zt), 0, ftin(L + hr), ext=False, size=4.2)
    dim(ax, (hr, zt), (0, zt), 0, ftin(-hr), ext=False, size=4.2)
    dim(ax, (0, zt), (hf, zt), 0, ftin(hf), ext=False, size=4.2, color=ACCENT)
    dim(ax, (hb, zt), (-L, zt), 0, ftin(-L - hb), ext=False, size=4.2, color=ACCENT)
    dim(ax, (-L, zt + 1.5), (0, zt + 1.5), 0, f"WEST WALL {fi(L, 2)} (true length, parallel to the west lot line)", ext=False, size=4.6)
    for h in (-L, hr, 0):
        line(ax, [(h, zt - 0.3), (h, zt + 1.8 if h != hr else zt + 0.3)], lw=0.25, color=GREY, z=8)
    txt(ax, hr, zt - 1.0, "ridge at mid-depth", size=3.8, color=GREY)
    # windows: stations from the front corner
    cs = sorted({round(w_[1], 3): w_ for w_ in wins}.values(), key=lambda w_: -w_[1])
    zb = 934.2
    st = [0.0]
    for w_ in cs:
        st += [w_[1] + w_[2] / 2, w_[1] - w_[2] / 2]
    st.append(-L)
    for a, b in zip(st[:-1], st[1:]):
        dim(ax, (b, zb), (a, zb), 0, ftin(a - b), ext=False, size=3.9)
    yd = -11.0
    dim(ax, (yd, m.EL_A), (yd, m.EL_B), 0, fi(m.EL_B - m.EL_A), ext=False, size=4.2)
    dim(ax, (yd, m.EL_B), (yd, m.EL_PLATE), 0, fi(m.EL_PLATE - m.EL_B, 8), ext=False, size=4.2)
    dim(ax, (yd, m.EL_GAR), (yd, m.EL_A), 0, fi(m.EL_A - m.EL_GAR), ext=False, size=4.2)
    for el in (m.EL_A, m.EL_PLATE):
        line(ax, [(yd - 0.6, el), (yd + 0.6, el)], lw=0.3, z=8)
    w1 = [q for q in wins if q[0] == "W1" and q[3] < m.EL_B][0]
    note(ax, (w1[1], w1[3]), (-22.5, 932.6), f"W1 ESCAPE WINDOW, SILL EL {w1[3]:.1f}: only 6 in. above\nexisting ground. Cut the yard to EL {w1[3] - 0.67:.1f} or lower here", size=3.9, ha="left", color=ACCENT)
    note(ax, (-13.5, np.interp(-13.5, [c[0] for c in ct][::-1], [c[1] for c in ct][::-1]) - 0.2), (-12.0, 921.4),
         f"TOP OF CONCRETE: EL {T_CONC:.2f} at the front, then\n8 in. above finish grade, stepped to suit", size=3.9, ha="center")
    for i, (hx, hy) in enumerate(m.HP):
        hc = h_west(hx, hy)
        txt(ax, hc + 0.5, elev(hx, hy) + 0.33 + HP_H + 0.55, f"HP-{'AB'[i]}", size=3.9, weight="bold", z=12)
    note(ax, (h_west(*m.HP[0]) + 1.0, elev(*m.HP[0]) + 1.0), (-3.0, 930.3), "HEAT PUMPS, one per flat,\non pads (M-101)", size=3.9, ha="center")
    txt(ax, -9.3, m.EL_GAR + 0.55, f"GARAGE SLAB EL {m.EL_GAR:.1f} (hidden: the garage is fully below ground on this side)", size=3.8, color=GREY, z=12)
    txt(ax, -9.3, m.EL_FTG_TOP - 0.6, f"TOP OF FOOTING EL {m.EL_FTG_TOP:.1f}", size=3.8, color=GREY, z=12)
    txt(ax, hw(m.Y_GR_O) - 0.4, 917.5, "GARAGE REAR WALL", size=3.6, color=GREY, rot=90, z=12)
    txt(ax, -L + 0.3, m.EL_A - 0.55, "UNIT A FLOOR (below ground)", size=3.6, color=GREY, ha="left", z=12, box=True)
    txt(ax, -25.0, 919.4, "SLAB ON GRADE BEHIND\n(Unit A, north of the garage)", size=3.6, color=GREY, z=12)
    note(ax, (h_west(m.PORCH[0], m.PORCH[1]) - 1.0, m.EL_B + 1.5), (8.0, 931.0), "PORCH ENDS\n(start 5'-5\" east\nof this corner)", size=3.9, ha="center")
    txt(ax, hf - 0.6, elev(m.xw_o(1.5), 1.5) + 1.4, "FRONT YARD AT\nNATURAL GRADE", size=3.8, color=EARTH, ha="right", z=12)
    txt(ax, -29.5, 913.0, "dashed brown: existing ground at the wall\nsolid: finish grade", size=3.7, color=EARTH, z=12)
    txt(ax, -15.5, 946.2, "442 BAIRD (west neighbour) is behind the viewer:\nits wall is ±1 ft beyond the lot line, 6'-2\" from this wall", size=3.9, color=GREY, z=9, box=True)


def side_yard(ax, yc, west, xl, yl):
    """East-west cut through a side yard at plan station y = yc, looking north."""
    xo = m.xw_o(yc) if west else m.XE
    sgn = 1 if west else -1                                    # direction from the wall face into the building
    tw = m.CONC / CL if west else m.CONC
    g = [(x, elev(x, yc)) for x in np.linspace(xl[0], xl[1], 30)]
    top = ct_west(yc) if west else max(T_CONC, elev(xo, yc) + CLEAR8)
    xi = xo + sgn * tw
    # inside: garage slab on stone, Unit A floor
    xin = xl[1] if west else xl[0]
    rect(ax, min(xi, xin), yl[0], max(xi, xin), m.EL_GAR - SLAB_GAR - STONE_GAR, fc=EARTH_FC, ec="none", z=1)
    rect(ax, min(xi, xin), m.EL_GAR - SLAB_GAR - STONE_GAR, max(xi, xin), m.EL_GAR - SLAB_GAR, fc=STONE_FC, ec="none", z=2)
    rect(ax, min(xi, xin), m.EL_GAR - SLAB_GAR, max(xi, xin), m.EL_GAR, fc=CONC_FC, ec=INK, lw=0.6, z=3)
    # outside: ground
    go = [p for p in g if (p[0] <= xo if west else p[0] >= xo)]
    go = (go + [(xo, elev(xo, yc))]) if west else ([(xo, elev(xo, yc))] + go)
    earth(ax, go, yl[0], z=1, lw=1.2)
    # wall, footing, drain
    f0 = xo - sgn * 1.0
    rect(ax, min(f0, f0 + sgn * m.FTG_W), m.EL_FTG_TOP - m.FTG_T, max(f0, f0 + sgn * m.FTG_W), m.EL_FTG_TOP, fc=CONC_FC, ec=INK, lw=0.8, z=4)
    rect(ax, min(xo, xi), m.EL_FTG_TOP, max(xo, xi), T_CONC, fc=CONC_FC, ec=INK, lw=0.9, z=4)
    if top > T_CONC + 0.01:
        rect(ax, min(xo, xo + sgn * 0.5), T_CONC, max(xo, xo + sgn * 0.5), top, fc=CONC_FC, ec=INK, lw=0.9, z=4)
    xf = xo + sgn * m.EXT
    rect(ax, min(xo, xf), max(m.EL_A, top), max(xo, xf), yl[1] + 1, fc=POCHE, ec=INK, lw=0.5, z=4)
    rect(ax, min(xo - sgn * 0.5, xo - sgn * 1.5), m.EL_FTG_TOP, max(xo - sgn * 0.5, xo - sgn * 1.5), elev(xo, yc) - 1.0, fc="#dcdfe3", ec="none", z=2, hatch="....")
    zd = (m.EL_DRAIN_HI if west else (m.EL_DRAIN_HI + m.EL_DRAIN_OUT) / 2) + 0.17
    ax.add_patch(plt.Circle((xo - sgn * 1.0 - sgn * 0.45, zd), 0.17, fc=PAPER, ec=BLUE, lw=0.8, zorder=6))
    return xo, xi, top


def sheet_a202(pdf):
    XE = m.XE
    L = m.WEST_WALL_LEN
    notes = [
        ("1 East elevation", [
            "Seen from 441 Baird, looking west. The east",
            f"wall is square to the street, {ftin(NE[1] - m.YF)} long.",
            "It has no windows: stair and bath 3 are",
            "behind it. Its base is the 12 in. concrete",
            "garage wall, exposed above the side yard.",
        ]),
        ("2 West elevation", [
            "Seen from 442 Baird, looking east. The wall",
            f"leans {math.degrees(WEST_LEAN):.1f}° with the lot line and is drawn",
            f"at its true length, {fi(L, 2)}. Ground rises",
            f"from EL {elev(X0, m.YF):.0f} at the front to {elev(*NW):.0f} at the rear,",
            "so the garage level is fully buried here.",
        ]),
        ("Roof", [
            "Both side walls are gable ends. The 8 in.",
            "rakes and the rear eave are within 5 ft of",
            "a lot line: 1-hour underside (R302.1).",
            "The ridge is at mid-depth of each wall and",
            "is higher at the west (deeper building).",
        ]),
        ("3, 4 Side yards", [
            "Both walls are 5'-2\" from the side lot",
            "lines. The neighbours' houses stand about",
            "1 ft beyond the lines (not surveyed).",
            "Excavation for the garage walls is 6 ft",
            "from those houses: see C-104 for shoring.",
        ]),
        ("Confirm", [
            "Grades are LiDAR ±0.5 ft. Heat pump height",
            "(30 in.) and meter stack size are assumed.",
            "Footing position is per S-102.",
        ]),
    ]
    fig, bg = new_sheet("A-202", TITLE["A-202"], "As noted", notes)
    yl = (910.5, 959.5)
    xl1, xl2 = (-9.2, 43.4), (-38.4, 12.6)
    w1, w2 = (xl1[1] - xl1[0]) / 8, (xl2[1] - xl2[0]) / 8
    gap = (SHEET_W - 2 * MARGIN - TB_W - w1 - w2) / 3
    l1 = MARGIN + gap
    l2 = l1 + w1 + gap
    b1 = 4.48
    ax = plan_axes(fig, l1, b1, xl1, yl, 8.0)
    east_elev(ax, xl1, yl)
    east_labels(ax, xl1, yl)
    title_under(bg, (l1, b1), 1, "East elevation", f"{SCALE8} · from 441 Baird, looking west · street on the left")
    ax2 = plan_axes(fig, l2, b1, xl2, yl, 8.0)
    wins, ct = west_elev(ax2, xl2, yl)
    west_labels(ax2, xl2, yl, wins, ct)
    title_under(bg, (l2, b1), 2, "West elevation", f"{SCALE8} · from 442 Baird, square to the west wall · street on the right")
    # --- 3: west side yard at heat pump A
    f3 = 16 / 3
    yl3 = (910.9, 928.3)
    yc = m.HP[0][1]
    xl3 = (west_x(yc) - 3.2, m.xw_o(yc) + 4.6)
    b3 = 0.72
    ax3 = plan_axes(fig, l1, b3, xl3, yl3, f3)
    xo, xi, top = side_yard(ax3, yc, True, xl3, yl3)
    lx = west_x(yc)
    lot_line(ax3, lx, yl3[0] + 0.4, yl3[1] - 1.5)
    txt(ax3, lx, yl3[1] - 1.0, "LOT LINE", size=4.2, color=ACCENT)
    gn = elev(lx - 1.0, yc)
    line(ax3, [(lx - 1.0, gn - 1.5), (lx - 1.0, yl3[1])], lw=0.7, color=GREY, ls=DASH, z=8)
    txt(ax3, lx - 1.45, 918.5, "442 BAIRD HOUSE WALL (±1 ft)", size=3.8, color=GREY, rot=90, z=12)
    hx = m.HP[0][0]
    d, g = m.HP_SIZE[1], elev(hx, yc)
    rect(ax3, hx - d / 2 - 0.2, g - 0.05, hx + d / 2 + 0.2, g + 0.33, fc=CONC_FC, ec=INK, lw=0.5, z=5)
    rect(ax3, hx - d / 2, g + 0.33, hx + d / 2, g + 0.33 + HP_H, fc="#eef0f2", ec=INK, lw=0.7, z=5)
    zt = g + 0.33 + HP_H + 0.6
    dim(ax3, (lx, zt), (hx - d / 2, zt), 0, ftin((hx - d / 2 - lx) * CL), ext=False, size=4.2)
    dim(ax3, (hx - d / 2, zt), (hx + d / 2, zt), 0, "15\"", ext=False, size=4.0)
    dim(ax3, (lx, 920.2), (xo, 920.2), 0, "5'-2\" WALL TO LOT LINE", ext=False, size=4.2, color=ACCENT)
    txt(ax3, hx, g + 0.33 + HP_H / 2, "HP", size=4.0, weight="bold", z=9)
    truss_a = [(xo + 0.5, A_T0), (xl3[1], A_T0), (xl3[1], m.EL_A), (xo + 0.5, m.EL_A)]
    poly(ax3, truss_a, fc=WOODC, ec=INK, lw=0.6, z=3)
    txt(ax3, xl3[1] - 0.2, m.EL_A + 0.5, f"UNIT A EL {m.EL_A:.1f}", size=4.2, weight="bold", ha="right")
    txt(ax3, xl3[1] - 0.2, m.EL_GAR + 0.5, f"GARAGE EL {m.EL_GAR:.1f}", size=4.2, weight="bold", ha="right")
    txt(ax3, xl3[1] - 0.3, 917.6, "OPEN\nGARAGE", size=4.2, color=GREY, ha="right")
    dim(ax3, (xi + 1.0, m.EL_GAR), (xi + 1.0, elev(xo, yc)), 0, f"{ftin(elev(xo, yc) - m.EL_GAR)} OF EARTH RETAINED", ext=False, size=4.0, side=-1)
    line(ax3, [(xo - 0.3, elev(xo, yc)), (xi + 1.4, elev(xo, yc))], lw=0.25, color=GREY, z=8)
    note(ax3, (xo + 0.25, top - 0.25), (xo + 2.0, 922.0), "concrete curb to\n8 in. above grade", size=3.8, ha="left")
    note(ax3, (xo - 1.45, m.EL_DRAIN_HI + 0.17), (lx - 2.9, 911.6), f"French drain, invert EL {m.EL_DRAIN_HI:.1f} (high end)", size=3.8, ha="left", color=BLUE)
    title_under(bg, (l1, b3), 3, "West side yard at heat pump A", f"{SCALE316} · looking north")
    # --- 4: east side yard at the meter stack
    yc4 = m.E_METER[1]
    xl4 = (XE - 4.4, 53.4)
    l4 = l1 + (xl3[1] - xl3[0]) / f3 + 0.45
    ax4 = plan_axes(fig, l4, b3, xl4, yl3, f3)
    xo, xi, top = side_yard(ax4, yc4, False, xl4, yl3)
    lot_line(ax4, 50.0, yl3[0] + 0.4, yl3[1] - 1.5)
    txt(ax4, 50.0, yl3[1] - 1.0, "LOT LINE", size=4.2, color=ACCENT)
    gn = elev(51.0, yc4)
    line(ax4, [(51.0, gn - 1.5), (51.0, yl3[1])], lw=0.7, color=GREY, ls=DASH, z=8)
    txt(ax4, 51.3, gn + 4.6, "441 BAIRD HOUSE WALL (±1 ft)", size=3.8, color=GREY, rot=90)
    g = elev(XE, yc4)
    rect(ax4, XE, g + METER_CL - METER_H + 1.0, XE + 0.4, g + METER_CL + 1.0, fc="#d6dbe0", ec=INK, lw=0.6, z=5)
    note(ax4, (XE + 0.4, g + METER_CL + 0.3), (XE + 1.2, g + METER_CL + 1.9), "meter stack", size=3.8, ha="left")
    dim(ax4, (XE, g + 2.0), (50.0, g + 2.0), 0, "5'-2\"", ext=False, size=4.4, color=ACCENT)
    dim(ax4, (XE + 0.9, g), (XE + 0.9, g + METER_CL), 0, "5'-0\"", ext=False, size=3.8, side=-1)
    for (wx, _wy) in m.WATER_METERS:
        ax4.add_patch(plt.Circle((wx, elev(wx, yc4) - m.WATER_DEPTH), 0.12, fc=BLUE, ec=BLUE, zorder=6))
    wx = m.WATER_METERS[0][0]
    note(ax4, (wx, elev(wx, yc4) - m.WATER_DEPTH), (XE + 2.0, 911.9), "two 1 in. water services,\n42 in. cover (C-106)", size=3.8, ha="left", color=BLUE)
    txt(ax4, xl4[0] + 0.2, m.EL_GAR + 0.5, f"STAIR EL {m.EL_GAR:.1f}", size=4.2, weight="bold", ha="left")
    dim(ax4, (XE + 2.6, m.EL_GAR), (XE + 2.6, g), 0, f"{ftin(g - m.EL_GAR)} RETAINED", ext=False, size=4.0, side=-1)
    title_under(bg, (l4, b3), 4, "East side yard at the meters", f"{SCALE316} · looking north")
    # --- table: grades and top of concrete along the two walls
    tx = l4 + (xl4[1] - xl4[0]) / f3 + 0.4
    rows = [("Wall", "Station from front", "Existing", "Finish", "Top of conc.", "Exposed")]
    for s_ in (0, 8, 16, 24, L):
        y = m.YF + s_ * CL
        e, f, t = elev(m.xw_o(y), y), fg_west(y), ct_west(y)
        rows.append(("West", ftin(s_), f"{e:.1f}", f"{f:.1f}", f"{t:.2f}", ftin(t - f)))
    for s_ in (0, 5, 10, 15, NE[1] - m.YF):
        y = m.YF + s_
        e = elev(XE, y)
        t = max(T_CONC, e + CLEAR8)
        rows.append(("East", ftin(s_), f"{e:.1f}", f"{e:.1f}", f"{t:.2f}", ftin(t - e)))
    bg.text(tx, 3.78, "GROUND AND TOP OF CONCRETE ALONG THE SIDE WALLS (EL, ft)", fontsize=6.6, fontweight="bold", va="top")
    y = table(bg, tx, 3.58, [0.5, 1.15, 0.72, 0.62, 0.9, 0.7], rows, fs=5.4, rh=0.185)
    bg.text(tx, y - 0.1, "West finish grade north of the garage rear wall is cut 6 in. (assumed, see C-105).\n"
            "Concrete is carried 8 in. above finish grade; the wood floor and wall framing\n"
            "start above it. On the west the curb rises past the Unit A floor trusses: S-102.",
            fontsize=5.4, va="top", linespacing=1.3)
    save(fig, "A-202", pdf)


# ----------------------------------------------------------------------------
# 4. A-301: building sections (north-south cuts, looking west; street on the left)
# ----------------------------------------------------------------------------
def flight(ax, y0, z0, n_r, rise, tread, d=1, cut=True, z=6):
    """Stair flight in section: n_r risers from (y0, z0), rising toward +y (d=1) or -y (d=-1).
    Returns the nosing line (bottom nosing, top nosing)."""
    pts, y, zz = [(y0, z0)], y0, z0
    for i in range(n_r):
        zz += rise
        pts.append((y, zz))
        if i < n_r - 1:
            y += d * tread
            pts.append((y, zz))
    drop = 0.5 * math.hypot(1, rise / tread)                   # 6 in. stringer throat, measured plumb
    und = [(y, zz - rise - drop), (y0 + d * drop * tread / rise, z0)]
    poly(ax, pts + und, fc=WOODC if cut else "none", ec=INK if cut else GREY, lw=0.7 if cut else 0.4, z=z if cut else z - 1)
    return (y0, z0 + rise), (y, zz)


def car_side(ax, y0, g):
    k = m.CAR_L / 16.2
    pr = [(0, 1.0), (0.3, 2.6), (3.2, 3.0), (5.0, CAR_H), (10.4, CAR_H), (12.6, 3.3), (15.6, 2.9), (16.2, 1.0)]
    poly(ax, [(y0 + a * k, g + b) for a, b in pr], fc="#f2f3f5", ec="#8d949c", lw=0.6, z=5)
    for a in (3.1, 12.8):
        ax.add_patch(plt.Circle((y0 + a * k, g + 1.05), 1.05, fc=PAPER, ec="#8d949c", lw=0.6, zorder=5.1))


def i_beam(ax, yc, z_top, depth, bf=6.75 * IN, tf=0.455 * IN, tw=0.285 * IN):
    rect(ax, yc - bf / 2, z_top - tf, yc + bf / 2, z_top, fc=STEEL, ec=STEEL, lw=0.3, z=7)
    rect(ax, yc - bf / 2, z_top - depth, yc + bf / 2, z_top - depth + tf, fc=STEEL, ec=STEEL, lw=0.3, z=7)
    rect(ax, yc - tw / 2, z_top - depth, yc + tw / 2, z_top, fc=STEEL, ec=STEEL, lw=0.3, z=7)


def roof_section(ax, X, y_in0, y_in1):
    """Common roof truss at station X with 12 in. heel, 4'-0" front and 12 in. rear overhangs, R-49 on the ceiling."""
    yf, yR = m.YF, m.yr_o(X)
    ya, yb, yr_ = yf - OH_F, yR + OH_R / CT, m.ridge_y(X)
    za, zb, zr = roof_z(X, ya), roof_z(X, yb), m.ridge_el(X)
    ch = 0.46 * math.hypot(1, P)
    poly(ax, [(ya, za), (yr_, zr), (yb, zb), (yb, zb - ch), (yr_, zr - ch), (ya, za - ch)], fc=WOODC, ec=INK, lw=0.6, z=6)
    line(ax, [(ya - 0.15, za + 0.02), (yr_, zr + 0.14), (yb + 0.15, zb + 0.02)], lw=1.6, color="#5c6269", z=6.2)
    rect(ax, yf, m.EL_PLATE, yR, m.EL_PLATE + 0.29, fc=WOODC, ec=INK, lw=0.5, z=6)
    n = 6
    web = []
    for i in range(n + 1):
        y = yf + (yR - yf) * i / n
        web.append((y, m.EL_PLATE + 0.29) if i % 2 == 0 else (y, roof_z(X, y) - ch))
    line(ax, web, lw=0.35, color=GREY, z=5.9)
    for y in (yf, yR):
        line(ax, [(y, m.EL_PLATE), (y, EAVE)], lw=0.6, z=6.1)
    ins = [(y_in0, m.EL_PLATE + 0.29)]
    for y in np.linspace(y_in0, y_in1, 30):
        ins.append((y, min(m.EL_PLATE + 0.29 + 1.33, roof_z(X, y) - ch - 0.08)))
    ins.append((y_in1, m.EL_PLATE + 0.29))
    poly(ax, ins, fc=INSUL, ec="#c98a98", lw=0.3, z=5.5)
    # soffits and fascias
    rect(ax, ya - 0.08, Z_SOFFIT_F, ya, za, fc=PAPER, ec=INK, lw=0.6, z=6.3)
    line(ax, [(ya, Z_SOFFIT_F), (yf, Z_SOFFIT_F)], lw=0.7, z=6.3)
    rect(ax, yb, Z_SOFFIT_R, yb + 0.08, zb, fc=PAPER, ec=INK, lw=0.6, z=6.3)
    line(ax, [(yR, Z_SOFFIT_R), (yb, Z_SOFFIT_R)], lw=1.2, color=ACCENT, z=6.3)
    return ya, yb, yr_, zr


def opening_in_wall(ax, y0, y1, z0, z1):
    rect(ax, y0 - 0.02, z0, y1 + 0.02, z1, fc=PAPER, ec=INK, lw=0.4, z=7)
    ym = (y0 + y1) / 2
    line(ax, [(ym, z0), (ym, z1)], lw=0.5, z=7.1)


def retaining(ax, X, yl):
    """Garage rear wall, footing, waterproofing and French drain; returns the drain centre."""
    yri, yro = m.Y_GR_I, m.Y_GR_O
    rect(ax, yri - 2.0, m.EL_FTG_TOP - m.FTG_T, yri - 2.0 + m.FTG_W, m.EL_FTG_TOP, fc=CONC_FC, ec=INK, lw=0.8, z=4)
    rect(ax, yri, m.EL_FTG_TOP, yro, T_CONC, fc=CONC_FC, ec=INK, lw=0.8, z=4.1)
    rect(ax, yro + 0.06, m.EL_FTG_TOP, yro + 1.0, m.EL_A - 2.6, fc="#dcdfe3", ec="none", z=2, hatch="....")
    line(ax, [(yro + 0.03, m.EL_FTG_TOP), (yro + 0.03, T_CONC)], lw=1.0, color=BLUE, z=4.2)
    zd = m.EL_DRAIN_HI - (m.EL_DRAIN_HI - m.EL_DRAIN_OUT) * 0.5 * (X - X0) / (m.XE - X0) + 0.17
    ax.add_patch(plt.Circle((yro + 0.55, zd), 0.17, fc=PAPER, ec=BLUE, lw=0.8, zorder=6))
    return (yro + 0.55, zd)


def section(ax, X, xl, yl, stair=False):
    yf, yfi, yri, yro = m.YF, m.YFI, m.Y_GR_I, m.Y_GR_O
    yR = m.yr_o(X)
    yRi = yR - m.EXT / CT
    ry = rear_y(X)
    st = street_el(X)
    g = m.EL_GAR
    sub = g - SLAB_GAR - STONE_GAR
    sog = m.EL_A - SLAB_A - RIGID - STONE_A
    fgw = fg_rear(X)
    ct = ct_rear(X)
    # --- ground: finish profile (fill) and existing (dashed)
    prof = [(xl[0], st), (PAVE_N, st)]
    if stair:
        prof += [(0.2, g - 0.33), (yf, g - 0.33)]
    else:
        prof += [(yf - 0.6, g - SLAB_GAR), (yf - 0.6, sub)]
    prof += [(yf, sub), (yro, sub), (yro, sog), (yR, sog), (yR, fgw), (yR + 2.0, fgw - 2 * IN)]
    prof += [(y, elev(X, y)) for y in np.arange(ry, xl[1] + 1.0, 1.0)]
    poly(ax, prof + [(xl[1], yl[0]), (xl[0], yl[0])], fc=EARTH_FC, ec="none", z=1)
    line(ax, [(xl[0], st), (PAVE_N, st)], lw=2.4, color="#3a3f45", z=7)
    line(ax, prof[-(len(prof) - prof.index((yR, fgw))):], lw=1.3, z=7)
    line(ax, [(y, elev(X, y)) for y in np.arange(xl[0], xl[1] + 0.5, 1.0)], lw=0.8, color=EARTH, ls=DASH, z=8)
    # --- garage slab, apron or landing
    rect(ax, yf - 0.35, sub, yri, g - SLAB_GAR, fc=STONE_FC, ec="none", z=2)
    rect(ax, yf - 0.35, g - SLAB_GAR, yri, g, fc=CONC_FC, ec=INK, lw=0.6, z=4)
    rect(ax, yf - 0.1, g - 0.5 - FROST, yf + 0.9, g - SLAB_GAR, fc="none", ec=GREY, lw=0.5, z=4, ls=DASH)
    if stair:
        rect(ax, m.TRASH[1], g - 0.33, yf, g, fc=CONC_FC, ec=INK, lw=0.6, z=4)
        line(ax, [(PAVE_N, st), (0.2, g - 0.33), (m.TRASH[1], g - 0.33)], lw=1.3, z=7)
        line(ax, [(m.TRASH[1], g), (m.TRASH[1], g + 5.0), (m.TRASH[3], g + 5.0), (m.TRASH[3], g)], lw=0.5, color=GREY, ls=(0, (2, 2)), z=7)
    else:
        ap = [(PAVE_N, st), (yf - 0.85, g)]
        poly(ax, ap + [(yf - 0.85, g - SLAB_GAR), (PAVE_N, st - SLAB_GAR)], fc=CONC_FC, ec=INK, lw=0.6, z=4)
        rect(ax, yf - 0.85, g - 0.5, yf - 0.35, g, fc=PAPER, ec=BLUE, lw=0.9, z=5)
        (wx0, wy0), (wx1, wy1) = m.WING_W
        ww = [(y, elev(wx0 - 0.5, y) + WALL_SITE_FREEBOARD) for y in np.linspace(wy1, wy0, 8)]
        poly(ax, [(wy1, apron_el(X, wy1)), (wy0, g)] + ww[::-1], fc="#dfe2e5", ec=GREY, lw=0.5, z=3)
    drain = retaining(ax, X, yl)
    rect(ax, yri, T_CONC, yri + 0.46, A_T0, fc=WOODC, ec=INK, lw=0.4, z=5)
    # --- Unit A floor: trusses over the garage (R-30 in the bottom, 5/8 Type X below), slab on grade behind
    t0 = (m.SHAFT_U[3] + 0.1) if stair else m.PORCH[1] + 0.12
    truss_band(ax, t0, yri + 0.46, A_T0, m.EL_A - 0.75 * IN)
    line(ax, [(t0, m.EL_A - 0.03), (yri + 0.46, m.EL_A - 0.03)], lw=1.0, z=5.2)
    i0 = (m.UTIL[2]) if stair else yf + 0.6
    rect(ax, i0, A_T0 + 0.02, yri, A_T0 + 0.8, fc=INSUL, ec="#c98a98", lw=0.3, z=5.3)
    line(ax, [(i0, A_T0 - 0.04), (yri, A_T0 - 0.04)], lw=1.3, color=ACCENT, z=6)
    if stair:                                                  # the skewed rear wall lands on a thickened head of the retaining wall
        poly(ax, [(yri + 0.46, T_CONC), (yro, T_CONC), (yro, T_CONC - 1.6), (yR, T_CONC - 0.6), (yR, max(ct, m.EL_A)), (yri + 0.46, m.EL_A)],
             fc=CONC_FC, ec=INK, lw=0.8, z=4.2)
    else:
        rect(ax, yri + 0.46, T_CONC, yro, m.EL_A - SLAB_A, fc=CONC_FC, ec=INK, lw=0.8, z=4.2)
        ys = yR - STEM / CT
        rect(ax, yro, m.EL_A - SLAB_A - RIGID - STONE_A, ys, m.EL_A - SLAB_A - RIGID, fc=STONE_FC, ec="none", z=2)
        rect(ax, yro, m.EL_A - SLAB_A - RIGID, ys, m.EL_A - SLAB_A, fc=INSUL, ec="#c98a98", lw=0.3, z=3)
        rect(ax, yri + 0.46, m.EL_A - SLAB_A, ys, m.EL_A, fc=CONC_FC, ec=INK, lw=0.6, z=4.3)
        fb = min(fgw - FROST, m.EL_A - 2.0)
        yc = (ys + yR) / 2
        rect(ax, yc - STEM_FTG_W / 2, fb, yc + STEM_FTG_W / 2, fb + STEM_FTG_T, fc=CONC_FC, ec=INK, lw=0.8, z=4)
        rect(ax, ys, fb + STEM_FTG_T, yR, ct, fc=CONC_FC, ec=INK, lw=0.8, z=4.1)
        ax.add_patch(plt.Circle((yR + 0.5, fgw - 1.6), 0.17, fc=PAPER, ec=BLUE, lw=0.8, zorder=6))
    # --- front
    if stair:
        rect(ax, yf, g, yf + m.CMU, T_CONC, fc=CONC_FC, ec=INK, lw=0.8, z=4.1)
        rect(ax, yf - 0.02, g, yf + m.CMU + 0.02, g + DOOR_H, fc=PAPER, ec=INK, lw=0.4, z=7)
        line(ax, [(yf + m.CMU, g), (yf + m.CMU, g + DOOR_H)], lw=0.9, z=7.1)
        rect(ax, yf, T_CONC, yfi, m.EL_PLATE, fc=POCHE, ec=INK, lw=0.4, z=6)
        w, hgt, sill = wtype("W3")
        for fl in (m.EL_A, m.EL_B):
            opening_in_wall(ax, yf, yfi, fl + sill, fl + sill + hgt)
    else:
        i_beam(ax, m.B1_Y, m.EL_B1_TOP, m.B1_DEPTH)
        rect(ax, m.B1_Y - 0.28, m.EL_B1_TOP, m.B1_Y + 0.28, A_T0, fc=WOODC, ec=INK, lw=0.4, z=7)
        rect(ax, yf, m.EL_A, yfi, B_T0, fc=POCHE, ec=INK, lw=0.4, z=6)
        rect(ax, yf, m.EL_B, yfi, m.EL_PLATE, fc=POCHE, ec=INK, lw=0.4, z=6)
    # --- Unit B floor trusses (clear span front wall to rear wall, cantilevered 4'-0" for the porch)
    tb0 = (m.SHAFT_U[3]) if stair else m.PORCH[1] + 0.12
    truss_band(ax, tb0, yR - 0.08, B_T0, B_T1)
    line(ax, [(tb0, m.EL_B - 0.03), (yR - 0.08, m.EL_B - 0.03)], lw=1.0, z=5.2)
    line(ax, [(max(tb0, yfi), Z_CLG_A - 0.02), (yRi, Z_CLG_A - 0.02)], lw=1.3, color=ACCENT, z=6)
    line(ax, [(yfi, Z_CLG_B), (yRi, Z_CLG_B)], lw=0.8, z=6)
    # --- rear walls
    rect(ax, yRi, max(ct, m.EL_A), yR, B_T0, fc=POCHE, ec=INK, lw=0.4, z=6)
    rect(ax, yRi, m.EL_B, yR, m.EL_PLATE, fc=POCHE, ec=INK, lw=0.4, z=6)
    for (tag, w_, s0, s1, _n) in m.WINDOWS:
        if w_ == "N" and s0 <= X <= s1:
            w, hgt, sill = wtype(tag)
            for fl in (m.EL_A, m.EL_B):
                opening_in_wall(ax, yRi, yR, fl + sill, fl + sill + hgt)
    # --- porches
    for fl, bot in ((m.EL_A, A_T0), (m.EL_B, B_T0)):
        y0 = m.PORCH[1]
        if stair:
            rect(ax, y0, bot, yf, fl, fc=WOODC, ec=INK, lw=0.6, z=5)
        rect(ax, y0, bot, y0 + 0.12, fl, fc=PAPER, ec=INK, lw=0.6, z=5.3)
        line(ax, [(y0 + 0.2, fl), (y0 + 0.2, fl + GUARD)], lw=1.0, z=6)
        line(ax, [(y0 + 0.2, fl + GUARD), (yf, fl + GUARD)], lw=0.5, color=GREY, z=5)
        line(ax, [(y0 + 0.2, fl + 0.29), (yf, fl + 0.29)], lw=0.3, color=GREY, z=5)
    # --- partitions cut at this station, with any door in them
    for (x0, y0, x1, y1, kind) in m.PARTITIONS:
        if not (x0 <= X <= x1) or y1 - y0 > 1.0:
            continue
        for fl, top in ((m.EL_A, Z_CLG_A), (m.EL_B, Z_CLG_B)):
            rect(ax, y0, fl, y1, top, fc=POCHE, ec=INK, lw=0.3, z=6)
            for d in m.DOORS:
                if d["wall"] == "h" and d["s0"] <= X <= d["s1"] and abs(d["at"][0] - y0) < 0.01:
                    rect(ax, y0 - 0.02, fl, y1 + 0.02, fl + DOOR_H, fc=PAPER, ec=INK, lw=0.4, z=7)
    ya, yb, yr_, zr = roof_section(ax, X, yfi, yRi)
    return dict(yR=yR, yRi=yRi, ry=ry, st=st, fgw=fgw, ct=ct, drain=drain, ya=ya, yb=yb, yr=yr_, zr=zr, sog=sog)


def section1_fit(ax, X, q):
    """What is seen beyond the cut of section 1 and the things standing in it."""
    car_side(ax, m.CAR_Y0, m.EL_GAR)
    w, hgt, sill = wtype("W4")
    s0, s1 = [(a, b) for (t, w_, a, b, _n) in m.WINDOWS if t == "W4"][0]
    for fl in (m.EL_A, m.EL_B):
        rect(ax, s0, fl + sill, s1, fl + sill + hgt, fc="#eef2f5", ec=GREY, lw=0.4, z=3)
        lv = m.LAVS[0]
        rect(ax, lv[1], fl, lv[3], fl + 2.83, fc=PAPER, ec="#8d949c", lw=0.5, z=3)
        line(ax, [(m.Y2, fl + m.CLG_SOFFIT), (m.Y3, fl + m.CLG_SOFFIT)], lw=0.6, color=GREY, ls=DASH, z=5)
    line(ax, [(q["ry"], elev(X, q["ry"])), (q["ry"], elev(X, q["ry"]) + 6.0)], lw=1.0, color="#8d949c", z=7)


def section2_fit(ax, X, q):
    """Stair, utility room and bath 3 in section 2."""
    g = m.EL_GAR
    lo, up = m.STAIR_LO, m.STAIR_UP
    y1 = m.SHAFT_U[3]
    # concrete wall between the stair and the utility room; rated walls above
    rect(ax, y1, g, m.UTIL[2], A_T0, fc=CONC_FC, ec=INK, lw=0.8, z=4.1)
    rect(ax, y1, m.EL_A, m.Y_ST, B_T0, fc=POCHE, ec=ACCENT, lw=0.6, z=6)
    rect(ax, y1, m.EL_B, m.Y_ST, Z_CLG_B, fc=POCHE, ec=ACCENT, lw=0.6, z=6)
    # lower stair: 2 flights; upper stair: 2 flights; the far (west) flights are seen beyond
    for z0, sd, run, zmid, fl_top in ((g, lo, ST_LO_RUN, ST_LO_MID, m.EL_A), (m.EL_A, up, ST_UP_RUN, ST_UP_MID, m.EL_B)):
        n, r, t = sd["risers"] // 2, sd["riser_in"] * IN, sd["tread_in"] * IN
        a, b = flight(ax, ST_Y0, z0, n, r, t, d=1, cut=True)
        line(ax, [(a[0], a[1] + GUARD), (b[0], b[1] + GUARD)], lw=0.9, z=7)
        rect(ax, ST_Y0 + run, zmid - 0.75, y1, zmid, fc=WOODC, ec=INK, lw=0.7, z=6)
        flight(ax, ST_Y0 + run, zmid, n, r, t, d=-1, cut=False)
        rect(ax, m.YFI, fl_top - 0.85, ST_Y0, fl_top, fc=WOODC, ec=INK, lw=0.7, z=6)
        line(ax, [(ST_Y0 + run, zmid + GUARD), (ST_Y0, fl_top + GUARD)], lw=0.4, color=GREY, z=5)
    line(ax, [(ST_Y0, m.EL_B), (ST_Y0, m.EL_B + GUARD)], lw=1.0, z=7)
    # utility room (heated): water services enter through the east wall below grade; floor drain
    ax.add_patch(plt.Circle((m.WATER_ENTRY[1], m.EL_WATER_ENTRY), 0.2, fc=PAPER, ec=BLUE, lw=0.8, zorder=6))
    rect(ax, m.UTIL[2] + 1.6, g - 0.12, m.UTIL[2] + 2.2, g, fc=PAPER, ec=BLUE, lw=0.6, z=6)
    # bath 3 on both floors: tub cut lengthwise, north wall, pipe space with stack 3 beyond
    for fl, top in ((m.EL_A, Z_CLG_A), (m.EL_B, Z_CLG_B)):
        rect(ax, m.Y_ST, fl, m.B3_Y1, fl + TUB_H, fc=PAPER, ec=INK, lw=0.7, z=5)
        line(ax, [(m.Y_ST + 0.25, fl + TUB_H), (m.Y_ST + 0.6, fl + 0.25), (m.B3_Y1 - 0.3, fl + 0.25), (m.B3_Y1 - 0.2, fl + TUB_H)], lw=0.4, color=GREY, z=5.1)
        rect(ax, m.B3_Y1, fl, m.B3_Y1 + m.PART, top, fc=POCHE, ec=INK, lw=0.3, z=6)
        line(ax, [(m.Y_ST, fl + m.CLG_SOFFIT), (m.B3_Y1, fl + m.CLG_SOFFIT)], lw=0.6, color=GREY, ls=DASH, z=5)
    sy, cy = m.STACK_3[1], m.CHASE_3[1]
    line(ax, [(cy, g), (cy, A_T0 + 0.9), (sy, A_T0 + 1.2), (sy, roof_z(X, sy) + 1.0)], lw=1.1, color="#2e7d32", z=6.5)


def sec_levels(ax, x, x_to):
    for el, nm in ((m.EL_A, "UNIT A FLOOR"), (m.EL_B, "UNIT B FLOOR"), (m.EL_PLATE, "TOP PLATE")):
        lvl(ax, x, el, nm, ha="left", size=4.4, line_to=x_to(el))


def section1_labels(ax, X, xl, yl, q):
    g, yf, yri, yro, yR, ry = m.EL_GAR, m.YF, m.Y_GR_I, m.Y_GR_O, q["yR"], q["ry"]
    sec_levels(ax, xl[0] + 0.6, lambda el: (m.PORCH[1] if el > g + 1 else PAVE_N) if el < m.EL_PLATE else q["ya"])
    lot_line(ax, 0.0, yl[0] + 0.8, 947.5, "FRONT LOT LINE", size=4.2)
    lot_line(ax, ry, yl[0] + 0.8, 947.5, "REAR LOT LINE", size=4.2)
    txt(ax, xl[0] + 0.4, q["st"] - 1.1, f"BAIRD ST ±EL {q['st']:.1f}", size=4.2, weight="bold", ha="left", z=12)
    zb = 910.5
    for a, b, c in ((0, yf, ACCENT), (yf, yro, INK), (yro, yR, INK), (yR, ry, ACCENT)):
        dim(ax, (a, zb), (b, zb), 0, ftin(b - a), ext=False, size=4.2, color=c)
    txt(ax, (yf + yro) / 2 - 5.5, zb + 0.55, "garage level", size=3.7, color=GREY, z=12)
    txt(ax, (yro + yR) / 2 + 2.6, zb + 1.4, "slab on grade", size=3.7, color=GREY, z=12)
    txt(ax, ry + 3.6, zb + 0.5, "(5'-2\" square)", size=3.7, color=ACCENT, z=12)
    # rooms
    txt(ax, 21.5, g + 7.3, "OPEN GARAGE", size=5.0, weight="bold", z=9)
    txt(ax, 21.5, g - 1.7, f"GARAGE SLAB EL {g:.1f}", size=4.4, weight="bold", z=12)
    for fl, u in ((m.EL_A, "A"), (m.EL_B, "B")):
        txt(ax, (m.YFI + m.Y1) / 2 + 1.6, fl + 1.9, f"UNIT {u}\nBEDROOM 1", size=4.4, weight="bold", z=9)
        txt(ax, (m.Y2 + m.Y3) / 2, fl + 5.3, "BATH 1", size=3.9, z=9)
        txt(ax, (m.Y4 + q["yRi"]) / 2, fl + 5.6, "BEDROOM 2", size=4.4, weight="bold", z=9)
        txt(ax, (m.PORCH[1] + yf) / 2, fl + 4.3, "PORCH", size=3.6, rot=90, z=9)
    # heights
    dim(ax, (17.6, g), (17.6, Z_CLG_GAR), 0, f"{ftd(m.CLG_GAR)} CLG", ext=False, size=4.0, side=-1)
    dim(ax, (12.2, g), (12.2, Z_B1_BOT), 0, f"{ftin(m.OPEN_CLEAR_H)} UNDER B1", ext=False, size=4.0, side=-1)
    dim(ax, (13.0, m.EL_A), (13.0, Z_CLG_A), 0, ftin(m.CLG_A), ext=False, size=4.0, side=-1)
    dim(ax, (13.0, m.EL_B), (13.0, Z_CLG_B), 0, ftin(m.CLG_B), ext=False, size=4.0, side=-1)
    xd = yR + 2.6
    dim(ax, (xd, m.EL_A), (xd, m.EL_B), 0, fi(m.EL_B - m.EL_A), ext=False, size=4.0, side=-1)
    dim(ax, (xd, m.EL_B), (xd, m.EL_PLATE), 0, fi(m.EL_PLATE - m.EL_B, 8), ext=False, size=4.0, side=-1)
    for el in (m.EL_A, m.EL_B, m.EL_PLATE):
        line(ax, [(yR + 0.2, el), (xd + 0.5, el)], lw=0.25, color=GREY, z=8)
    dim(ax, (3.6, g), (3.6, m.EL_A), 0, fi(m.EL_A - g), ext=False, size=4.0)
    line(ax, [(3.1, g), (4.1, g)], lw=0.25, color=GREY, z=8)
    # assemblies
    txt(ax, 19.6, (A_T0 + m.EL_A) / 2 + 0.25, "20 in. FLOOR TRUSSES · R-30 · 5/8 in. TYPE X GARAGE CEILING", size=3.5, z=9, box=True)
    txt(ax, 24.5, (B_T0 + B_T1) / 2, "24 in. FLOOR TRUSSES, CLEAR SPAN · 1-HOUR FLOOR/CEILING BETWEEN FLATS", size=3.5, z=9, box=True)
    txt(ax, q["yr"], m.EL_PLATE + 2.2, "ROOF TRUSSES @ 24 in., 4:12\n12 in. heel · R-49", size=3.8, z=9)
    note(ax, (q["yr"], q["zr"]), (q["yr"] + 7.0, q["zr"] + 1.2), f"RIDGE EL {q['zr']:.1f} HERE", size=4.0, ha="left")
    note(ax, (m.B1_Y, Z_B1_BOT + 0.5), (4.6, 920.3), "STEEL BEAM B1\nunder the trusses", size=3.8, ha="center")
    note(ax, (yro - 0.5, 919.0), (yro + 4.3, 919.6), "12 in. CONCRETE\nRETAINING WALL", size=3.8, ha="left")
    note(ax, (yR - 0.3, q["ct"] - 0.6), (yR + 3.4, 923.0), "STEM WALL to\n8 in. above grade", size=3.8, ha="left")
    note(ax, (yR + 2.0, q["fgw"] - 0.1), (ry + 0.7, 925.4), "SWALE", size=3.8, ha="left")
    txt(ax, (yf + 2.2), m.EL_PLATE - 0.9, "R-20 WALLS", size=3.5, ha="left", z=9)
    txt(ax, ry + 4.6, elev(X, ry + 4.6) - 1.2, "386 FOREST AVE\nground rises to\n±EL 931", size=3.8, color=GREY, z=12)
    note(ax, (2.5, elev(X, 2.5)), (-4.8, 924.2), "EXISTING GROUND\n(dashed, LiDAR)", size=3.8, ha="center", color=EARTH)
    txt(ax, -3.2, apron_el(X, -3.2) + 0.8, "APRON", size=3.8, z=12)
    txt(ax, (m.PORCH[1] - 2.2), Z_EAVE_F + 0.9, "4'-0\" OVERHANG", size=3.6, z=9)


def section2_labels(ax, X, xl, yl, q):
    g, yf, yri, yro, yR, ry = m.EL_GAR, m.YF, m.Y_GR_I, m.Y_GR_O, q["yR"], q["ry"]
    lo, up = m.STAIR_LO, m.STAIR_UP
    lot_line(ax, ry, yl[0] + 0.8, 947.5, "REAR LOT LINE", size=4.2)
    lot_line(ax, 0.0, yl[0] + 0.8, 947.5, "FRONT LOT LINE", size=4.2, ha="left")
    zb = 910.5
    for a, b, c in ((0, yf, ACCENT), (yf, m.SHAFT_U[3], INK), (m.SHAFT_U[3], yro, INK), (yro, ry, ACCENT)):
        dim(ax, (a, zb), (b, zb), 0, ftin(b - a), ext=False, size=4.0, color=c)
    txt(ax, (yf + m.SHAFT_U[3]) / 2 + 3.0, zb + 0.55, "stair", size=3.7, color=GREY, z=12)
    txt(ax, (m.SHAFT_U[3] + yro) / 2, zb + 1.3, "utility", size=3.7, color=GREY, z=12)
    for el, s_ in ((g, f"SLAB {g:.1f}"), (m.EL_A, f"A {m.EL_A:.1f}"), (m.EL_B, f"B {m.EL_B:.1f}")):
        txt(ax, 3.2, el + 0.5, s_, size=3.9, weight="bold", z=10)
        line(ax, [(0.6, el), (m.PORCH[1] if el > g else 5.6, el)], lw=0.3, color=GREY, ls=(0, (8, 3, 2, 3)), z=8)
    ys = (ST_Y0 + ST_Y0 + ST_LO_RUN) / 2
    txt(ax, ys + 1.2, g + 1.3, f"UP {lo['risers'] // 2} R", size=3.6, z=9)
    txt(ax, 17.0, m.EL_A - 2.6, f"GARAGE TO UNIT A\n{lo['risers']} risers at {inch(lo['riser_in'])} in.", size=3.7, z=9, box=True)
    txt(ax, 17.0, m.EL_B - 2.4, f"UNIT A TO UNIT B\n{up['risers']} risers at {inch(up['riser_in'])} in.", size=3.7, z=9, box=True)
    txt(ax, 17.2, m.EL_B + 5.6, "COMMON STAIR\n1-hour enclosure", size=4.0, weight="bold", z=9)
    txt(ax, (m.UTIL[2] + m.UTIL[3]) / 2, g + 7.3, "UTILITY\n(heated)", size=3.9, weight="bold", z=9)
    note(ax, (m.WATER_ENTRY[1], m.EL_WATER_ENTRY), (yR + 2.2, g + 3.6), "WATER SERVICES IN,\nshutoffs, floor drain.\nWater heaters are\nin the flats", size=3.6, ha="left", color=BLUE)
    for fl in (m.EL_A, m.EL_B):
        txt(ax, (m.Y_ST + m.B3_Y1) / 2, fl + 4.0, "BATH 3", size=3.9, weight="bold", z=9)
    note(ax, (m.STACK_3[1], m.EL_B + 5.0), (yR + 2.0, m.EL_B + 6.2), "PIPE SPACE:\nstack 3 and\nUnit B water\nlines", size=3.6, ha="left")
    note(ax, (yf + 0.3, g + 3.0), (4.4, g + 3.4), "STREET\nDOOR", size=3.6, ha="center")
    note(ax, (m.TRASH[3] - 0.6, g + 5.0), (3.0, g + 6.0), "TRASH BAY SCREEN (C-107)", size=3.4, ha="center", color=GREY)
    note(ax, (yro + 0.4, T_CONC - 0.9), (yR + 2.2, 921.4), "WALL HEAD THICKENED\nunder the skewed rear\nwall (engineer)", size=3.6, ha="left")
    note(ax, (q["yr"], q["zr"]), (q["yr"] + 5.0, q["zr"] + 1.4), f"RIDGE EL {q['zr']:.1f} HERE", size=4.0, ha="left")
    note(ax, (m.PORCH[1] + 2.0, m.EL_A - 0.8), (3.3, m.EL_A - 3.3), "PORCH IN FRONT OF THE STAIR:\nno floor trusses behind it,\nframing by S-204", size=3.5, ha="center", color=ACCENT)
    dim(ax, (yR + 1.6, m.EL_A), (yR + 1.6, m.EL_B), 0, fi(m.EL_B - m.EL_A), ext=False, size=3.9, side=-1)
    dim(ax, (yR + 1.6, g), (yR + 1.6, m.EL_A), 0, fi(m.EL_A - g), ext=False, size=3.9, side=-1)


def section1_lower_labels(ax, X, xl, yl, q):
    g, yf, yri, yro, yR, ry = m.EL_GAR, m.YF, m.Y_GR_I, m.Y_GR_O, q["yR"], q["ry"]
    lot_line(ax, 0.0, yl[0] + 0.5, 929.0, "FRONT LOT LINE = R.O.W. LINE", size=4.4)
    lot_line(ax, ry, yl[0] + 0.5, 918.0)
    txt(ax, ry + 0.3, 916.0, "REAR LOT LINE\n6 ft fence on the line", size=4.4, color=ACCENT, ha="left")
    txt(ax, xl[0] + 0.3, q["st"] + 0.6, f"BAIRD ST PAVEMENT\n±EL {q['st']:.1f} at this cut", size=4.4, weight="bold", ha="left", va="bottom", z=12)
    txt(ax, -3.4, apron_el(X, -3.4) - 1.2, "CONCRETE APRON (C-107)\nfalls to the trench drain", size=4.2, z=12)
    note(ax, (yf - 0.6, g - 0.25), (yf - 4.2, g - 2.3), "TRENCH DRAIN across the\nopening, to the gravity outlet", size=4.2, ha="right", color=BLUE)
    note(ax, (yf + 0.4, g - 2.6), (yf + 2.2, g - 2.9), "FOUNDATION AT THE OPENING to frost depth (36 in.), see S-101", size=4.2, ha="left", color=GREY)
    txt(ax, 21.0, g - 0.25, "6 in. SLAB ON 6 in. STONE · BROOM FINISH, SEALED · FALLS 1/8 in./ft TO THE TRENCH DRAIN", size=3.9, z=12)
    txt(ax, 20.6, g + 0.55, f"GARAGE SLAB EL {g:.1f}", size=4.8, weight="bold", z=12)
    txt(ax, 17.6, g + 5.9, "OPEN GARAGE", size=6.0, weight="bold", z=9)
    txt(ax, m.CAR_Y0 + 8.3, g + 3.1, "design car 16'-0\"", size=4.0, color=GREY, z=9)
    dim(ax, (yri - 0.55, g), (yri - 0.55, Z_CLG_GAR), 0, f"{ftd(m.CLG_GAR)} CLEAR TO CEILING", ext=False, size=4.4)
    dim(ax, (yf + 1.5, g), (yf + 1.5, Z_B1_BOT), 0, f"{ftin(m.OPEN_CLEAR_H)} CLEAR UNDER B1", ext=False, size=4.4, side=-1)
    line(ax, [(m.B1_Y, Z_B1_BOT), (yf + 1.9, Z_B1_BOT)], lw=0.25, color=GREY, z=8)
    dim(ax, (yf, g + 0.9), (yri, g + 0.9), 0, f"{ftin(yri - yf)} CLEAR DEPTH", ext=False, size=4.4)
    note(ax, (m.B1_Y, m.EL_B1_TOP - 0.6), (3.2, 921.0), f"B1 W14x34 (prelim.)\ntop EL {m.EL_B1_TOP:.2f}", size=4.2, ha="center")
    note(ax, (16.0, A_T0 + 0.4), (12.6, 922.3), "R-30 in the bottom of the trusses,\n5/8 in. Type X ceiling below (R302.6)", size=4.2, ha="left")
    note(ax, (4.0, elev(X, 4.0)), (1.2, 924.6), "EXISTING GROUND (LiDAR):\nall of this is excavated", size=4.2, ha="left", color=EARTH)
    note(ax, (5.0, elev(m.WING_W[0][0] - 0.5, 5.0)), (-5.0, 919.8), "WING WALL beyond\n(retains the front yard)", size=4.2, ha="center", color=GREY)
    txt(ax, (m.PORCH[1] + yf) / 2 - 0.1, m.EL_A + 1.6, "PORCH\n4'-0\"", size=4.0, z=9)
    txt(ax, 16.5, m.EL_A + 2.0, "BEDROOM 1", size=4.6, weight="bold", z=9)
    txt(ax, (m.Y2 + m.Y3) / 2, m.EL_A + 4.2, "BATH 1", size=4.0, z=9)
    txt(ax, 33.4, m.EL_A + 3.6, "BEDROOM 2 (on the slab)", size=4.6, weight="bold", z=9)
    txt(ax, 5.4, m.EL_A + 0.6, f"UNIT A FLOOR EL {m.EL_A:.1f}", size=4.6, weight="bold", ha="right", z=12)
    # retaining wall
    note(ax, (yri + 0.5, 921.0), (yri - 1.6, 920.9), "12 in. CONCRETE WALL (prelim.)\nretains 11'-0\" to the Unit A slab", size=4.2, ha="right")
    note(ax, (yro + 0.03, 921.5), (yro + 2.6, 921.9), "sheet membrane + drainage board", size=4.2, ha="left", color=BLUE)
    note(ax, (yro + 0.6, 917.0), (yro + 2.6, 919.9), "free-draining stone in filter fabric", size=4.2, ha="left")
    d = q["drain"]
    note(ax, d, (yro + 2.6, 913.6), f"4 in. PERFORATED FRENCH DRAIN, invert ±EL {d[1] - 0.17:.1f} here\n(EL {m.EL_DRAIN_HI:.1f} high end to {m.EL_DRAIN_OUT:.1f} at the street outlet). NO SUMP.", size=4.2, ha="left", color=BLUE)
    dim(ax, (yri - 2.0, m.EL_FTG_TOP - m.FTG_T - 0.55), (yri + 2.0, m.EL_FTG_TOP - m.FTG_T - 0.55), 0, f"FOOTING {ftin(m.FTG_W)} x 14 in., TOP EL {m.EL_FTG_TOP:.1f}", ext=False, size=4.2, side=-1)
    txt(ax, (yro + yR) / 2 + 0.8, 923.0, "ENGINEERED FILL\nplaced after the Unit A\nfloor props the wall", size=4.0, color=EARTH, z=9)
    note(ax, (yro + 3.0, m.EL_A - 0.2), (yro + 0.6, 927.6), "5 in. SLAB · 15-mil VAPOUR BARRIER · R-10 · 4 in. STONE", size=4.0, ha="left")
    # stem wall and rear yard
    note(ax, (yR - 0.3, q["ct"] - 1.2), (yR + 2.9, 924.2), "8 in. STEM WALL on a 20 x 10 in.\nfooting, R-15 inside, top 8 in.\nabove finish grade", size=4.2, ha="left")
    note(ax, (yR + 0.5, q["fgw"] - 1.6), (yR + 2.9, 921.9), "shallow drain behind the stem wall, runs east", size=4.2, ha="left", color=BLUE)
    note(ax, (yR + 2.0, q["fgw"] - 0.17), (yR + 1.2, 930.2), "SWALE falls east", size=4.2, ha="left")
    dim(ax, (yR, 928.9), (ry, 928.9), 0, f"{ftin(ry - yR)}", ext=False, size=4.2, color=ACCENT)
    txt(ax, ry + 3.7, elev(X, ry + 3.7) - 1.3, "386 FOREST AVE\nexisting ground, not touched", size=4.2, color=GREY, z=12)
    w5 = wtype("W5")
    note(ax, (yR - 0.3, m.EL_A + w5[2] + 0.1), (yR - 1.6, m.EL_A + 4.5), f"W5 sill EL {m.EL_A + w5[2]:.1f}", size=4.0, ha="right")


def sheet_a301(pdf):
    notes = [
        ("1 Section through the garage", [
            f"North-south cut at X = {XS1:.1f} ft, looking west:",
            "apron, stall 1, bedroom 1, bath 1 and",
            "bedroom 2. View 3 is the same cut, larger,",
            "for the concrete and excavation trades.",
        ]),
        ("2 Section through the stair", [
            f"Cut at X = {XS2:.0f} ft: street door, both stairs,",
            "the heated utility room (water entry;",
            "the water heaters are in the flats) and",
            "bath 3 above it on both floors.",
        ]),
        ("Heights", [
            f"Garage {ftd(m.CLG_GAR)} clear, {ftin(m.OPEN_CLEAR_H)} under beam B1",
            f"Unit A ceiling {ftin(m.CLG_A)} · Unit B {ftin(m.CLG_B)}",
            f"Duct soffits {ftin(m.CLG_SOFFIT)} (dashed). Floor to floor",
            "11'-0\" and 10'-0\".",
        ]),
        ("Fire and insulation", [
            "Red lines: 5/8 in. Type X garage ceiling",
            "(R302.6); 1-hour floor/ceiling between the",
            "flats (R302.3); 1-hour rear soffit and",
            "rakes; 1-hour stair walls. R-30 over the",
            "garage, R-49 attic (vents: front soffit",
            "and ridge), R-20 walls, R-10 under slab.",
        ]),
        ("Preliminary", [
            "Wall, footing, beam and truss sizes are",
            "for the engineer. Ground is LiDAR ±0.5 ft.",
            "No sump: drains fall to the street by",
            "gravity; the survey must confirm the fall.",
        ]),
    ]
    fig, bg = new_sheet("A-301", TITLE["A-301"], "As noted", notes)
    yl = (909.8, 951.6)
    xl1, xl2 = (-11.5, 53.5), (0.0, 38.2)
    w1, w2 = (xl1[1] - xl1[0]) / 8, (xl2[1] - xl2[0]) / 8
    gap = (SHEET_W - 2 * MARGIN - TB_W - w1 - w2) / 3
    l1 = MARGIN + gap
    l2 = l1 + w1 + gap
    b1 = 5.08
    ax = plan_axes(fig, l1, b1, xl1, yl, 8.0)
    q = section(ax, XS1, xl1, yl)
    section1_fit(ax, XS1, q)
    section1_labels(ax, XS1, xl1, yl, q)
    break_mark(ax, xl1[0] + 0.25, 913.5, 916.5)
    title_under(bg, (l1, b1), 1, "Section through the garage and bedrooms", f"{SCALE8} · X = {XS1:.1f} ft, looking west")
    ax2 = plan_axes(fig, l2, b1, xl2, yl, 8.0)
    q2 = section(ax2, XS2, (xl2[0] - 12, xl2[1]), yl, stair=True)
    section2_fit(ax2, XS2, q2)
    section2_labels(ax2, XS2, xl2, yl, q2)
    title_under(bg, (l2, b1), 2, "Section through the stair", f"{SCALE8} · X = {XS2:.0f} ft, looking west")
    f3 = 16 / 3
    xl3, yl3 = (-9.6, 52.0), (910.2, 930.6)
    b3 = 0.78
    l3 = MARGIN + (SHEET_W - 2 * MARGIN - TB_W - (xl3[1] - xl3[0]) / f3) / 2
    ax3 = plan_axes(fig, l3, b3, xl3, yl3, f3)
    q3 = section(ax3, XS1, xl3, yl3)
    section1_fit(ax3, XS1, q3)
    section1_lower_labels(ax3, XS1, xl3, yl3, q3)
    title_under(bg, (l3, b3), 3, "Section 1, garage level and foundations", f"{SCALE316} · same cut as 1 · all sizes preliminary, for the engineer")
    save(fig, "A-301", pdf)


# ----------------------------------------------------------------------------
# 5. A-402: stair, guard and porch details
# ----------------------------------------------------------------------------
RATED_EC = ACCENT


def stair_plan(ax, level):
    """Plan of the common stair at one level: "G" garage, "A" Unit A, "B" Unit B."""
    G = level == "G"
    sx0, sx1 = m.SHAFT_X0, (m.SHAFT_L[1] if G else m.SHAFT_U[1])
    sy0, sy1 = (m.SHAFT_L[2] if G else m.SHAFT_U[2]), m.SHAFT_U[3]
    w = FLIGHT_L if G else FLIGHT_U
    t = m.STAIR_LO["tread_in"] * IN
    rect(ax, sx0, sy0, sx1, sy1, fc="#fafaf8", ec="none", z=1)
    if G:
        for (a, b, c, d) in ((m.GAR_X1, m.YF, sx0, m.UTIL[2]), (sx1, m.YF, m.XE, m.UTIL[2]), (m.GAR_X1, m.YF, m.XE, sy0), (sx0, sy1, sx1, m.UTIL[2])):
            rect(ax, a, b, c, d, fc=CONC_FC, ec=INK, lw=0.7, z=3)
        rect(ax, m.ENTRY[0], m.YF - 0.03, m.ENTRY[1], sy0 + 0.03, fc=PAPER, ec="none", z=4)
        door(ax, (m.ENTRY[0], sy0), 3.0, 0, 90)
    else:
        rect(ax, m.X_ST, m.YF, m.XE, m.YFI, fc=POCHE, ec=INK, lw=0.5, z=3)
        rect(ax, m.XEI, m.YF, m.XE, m.Y_ST, fc=POCHE, ec=INK, lw=0.5, z=3)
        rect(ax, m.X_ST, m.YFI, sx0, m.Y_ST, fc="#5a2a27", ec=RATED_EC, lw=0.9, z=3)
        rect(ax, sx0, sy1, m.XEI, m.Y_ST, fc="#5a2a27", ec=RATED_EC, lw=0.9, z=3)
        w3 = [(a, b) for (tg, w_, a, b, _n) in m.WINDOWS if tg == "W3"][0]
        window_h(ax, w3[0], w3[1], m.YF, m.YFI)
        d1 = [d for d in m.DOORS if d["tag"] == "D1"][0]
        rect(ax, m.X_ST - 0.03, d1["s0"], sx0 + 0.03, d1["s1"], fc=PAPER, ec="none", z=4)
        door(ax, (m.X_ST, d1["s0"]), 3.0, 90, 90)
    xe0, xw1 = sx1 - w, sx0 + w
    run_lo, run_up = ST_LO_RUN, ST_UP_RUN
    arrow = dict(arrowstyle="-|>", lw=0.6, color=INK)

    def treads(x0, x1, run, n, ls="-", color=INK):
        for i in range(n + 1):
            line(ax, [(x0, ST_Y0 + i * t), (x1, ST_Y0 + i * t)], lw=0.45, color=color, ls=ls, z=5)
        line(ax, [(x0, ST_Y0), (x0, ST_Y0 + run)], lw=0.45, color=color, z=5) if x0 > sx0 + 0.01 else None
        line(ax, [(x1, ST_Y0), (x1, ST_Y0 + run)], lw=0.45, color=color, z=5) if x1 < sx1 - 0.01 else None

    def up_dn(xc, run, s_):
        ax.annotate("", xy=(xc, ST_Y0 + run - 0.5), xytext=(xc, ST_Y0 + 0.25), arrowprops=arrow, zorder=8)
        txt(ax, xc, ST_Y0 + run / 2, s_, size=4.6, weight="bold", box=True, z=9)

    lo_n, up_n = m.STAIR_LO["treads_per_flight"], m.STAIR_UP["treads_per_flight"]
    if G:
        treads(xe0, sx1, run_lo, lo_n)
        up_dn((xe0 + sx1) / 2, run_lo, f"UP\n{lo_n + 1} R")
        treads(sx0, xw1, run_lo, lo_n, ls=DASH, color=GREY)
        txt(ax, (sx0 + xw1) / 2, ST_Y0 + run_lo / 2, "FLIGHT 2\nOVER.\nSpace\nbelow\nclosed off\n(R302.7)", size=3.8, color=GREY, box=True, z=9)
        txt(ax, (sx0 + sx1) / 2, (ST_Y0 + run_lo + sy1) / 2, f"MID LANDING EL {ST_LO_MID:.1f} (over)", size=3.9, z=9)
        txt(ax, sx0 + 1.2, sy0 + 1.6, f"ENTRY\nLANDING\nEL {m.EL_GAR:.1f}", size=3.9, z=9)
    elif level == "A":
        treads(xe0, sx1, run_up, up_n)
        up_dn((xe0 + sx1) / 2, run_up, f"UP\n{up_n + 1} R")
        treads(sx0, xw1, run_lo, lo_n)
        up_dn((sx0 + xw1) / 2, run_lo, f"DN\n{lo_n + 1} R")
        txt(ax, (sx0 + sx1) / 2, sy1 - 1.0, f"MID LANDINGS\nEL {ST_LO_MID:.1f} (down) · EL {ST_UP_MID:.1f} (up)", size=3.7, z=9)
        txt(ax, (sx0 + sx1) / 2 + 0.4, sy0 + 1.6, f"UNIT A LANDING\nEL {m.EL_A:.1f}", size=3.9, z=9)
    else:
        treads(sx0, xw1, run_up, up_n)
        up_dn((sx0 + xw1) / 2, run_up, f"DN\n{up_n + 1} R")
        treads(xe0, sx1, run_up, up_n, ls=DASH, color=GREY)
        txt(ax, (xe0 + sx1) / 2, ST_Y0 + run_up / 2, "OPEN\nTO\nFLIGHT 3\nBELOW", size=3.8, color=GREY, box=True, z=9)
        line(ax, [(xw1, ST_Y0), (sx1, ST_Y0)], lw=1.6, color=BLUE, z=7)
        line(ax, [(xw1, ST_Y0), (xw1, ST_Y0 + run_up)], lw=1.6, color=BLUE, z=7)
        txt(ax, (sx0 + sx1) / 2, sy1 - 1.2, f"MID LANDING EL {ST_UP_MID:.1f} (below)", size=3.7, z=9)
        txt(ax, (sx0 + sx1) / 2 + 0.4, sy0 + 1.6, f"UNIT B LANDING\nEL {m.EL_B:.1f}", size=3.9, z=9)
    rect(ax, xw1, ST_Y0, xe0, ST_Y0 + (run_lo if level != "B" else run_up), fc=PAPER, ec=INK, lw=0.5, z=5.5)
    for x in (sx0 + 0.12, sx1 - 0.12):                         # handrails on the wall side of each flight
        line(ax, [(x, ST_Y0 - 0.6), (x, ST_Y0 + (run_lo if level != "B" else run_up) + 0.6)], lw=0.9, color=BLUE, z=6)
    # dimensions
    yb = m.YF - 0.95
    dim(ax, (sx0, yb), (xw1, yb), 0, fi(w), ext=False, size=4.2)
    dim(ax, (xw1, yb), (xe0, yb), 0, "4\"", ext=False, size=3.8)
    dim(ax, (xe0, yb), (sx1, yb), 0, fi(w), ext=False, size=4.2)
    dim(ax, (sx0, yb - 1.1), (sx1, yb - 1.1), 0, f"{fi(sx1 - sx0)} CLEAR", ext=False, size=4.4)
    xd = sx0 - (1.75 if G else 1.55)
    run = run_lo if level != "B" else run_up
    dim(ax, (xd, sy0), (xd, ST_Y0), 0, fi(ST_Y0 - sy0), ext=False, size=4.0)
    dim(ax, (xd, ST_Y0), (xd, ST_Y0 + run), 0, f"{fi(run)}", ext=False, size=4.0)
    dim(ax, (xd, ST_Y0 + run), (xd, sy1), 0, fi(sy1 - ST_Y0 - run), ext=False, size=4.0)
    for y in (sy0, ST_Y0, ST_Y0 + run, sy1):
        line(ax, [(xd - 0.15, y), (sx0 - (0.75 if G else 0.5), y)], lw=0.25, color=GREY, z=8)
    xr = m.XE + 0.75
    dim(ax, (xr, sy0), (xr, sy1), 0, f"{fi(sy1 - sy0)} CLEAR", ext=False, size=4.4, side=-1)
    if level == "A":
        dim(ax, (sx1 - 0.55, ST_Y0 + run_up), (sx1 - 0.55, sy1), 0, fi(sy1 - ST_Y0 - run_up), ext=False, size=3.8)


def stair_section(ax, xl, yl):
    """Section through the east flights (X = XS2), looking west."""
    g, yf, yfi, y1 = m.EL_GAR, m.YF, m.YFI, m.SHAFT_U[3]
    lo, up = m.STAIR_LO, m.STAIR_UP
    rect(ax, xl[0], yl[0], xl[1], g - 0.5, fc=EARTH_FC, ec="none", z=1)
    rect(ax, xl[0], g - 0.33, yf, g, fc=CONC_FC, ec=INK, lw=0.6, z=4)
    rect(ax, yf, g - 0.5, xl[1], g, fc=CONC_FC, ec=INK, lw=0.6, z=4)
    # walls: garage level concrete/block, 1-hour framed walls above
    rect(ax, yf, g, yf + m.CMU, A_T0, fc=CONC_FC, ec=INK, lw=0.8, z=4.1)
    rect(ax, yf - 0.02, g, yf + m.CMU + 0.02, g + DOOR_H, fc=PAPER, ec=INK, lw=0.4, z=7)
    line(ax, [(yf + m.CMU, g), (yf + m.CMU, g + DOOR_H)], lw=1.0, z=7.1)
    rect(ax, yf, A_T0, yfi, yl[1], fc=POCHE, ec=INK, lw=0.4, z=6)
    w, hgt, sill = wtype("W3")
    for fl in (m.EL_A, m.EL_B):
        opening_in_wall(ax, yf, yfi, fl + sill, fl + sill + hgt)
    rect(ax, y1, g, m.UTIL[2], A_T0, fc=CONC_FC, ec=INK, lw=0.8, z=4.1)
    rect(ax, y1, A_T0, m.Y_ST, yl[1], fc="#5a2a27", ec=RATED_EC, lw=0.9, z=6)
    truss_band(ax, m.Y_ST, xl[1], A_T0, m.EL_A - 0.75 * IN)
    truss_band(ax, m.Y_ST, xl[1], B_T0, B_T1)
    line(ax, [(yfi, Z_CLG_B), (y1, Z_CLG_B)], lw=1.3, color=ACCENT, z=6)
    # porches in front
    for fl, bot in ((m.EL_A, A_T0), (m.EL_B, B_T0)):
        rect(ax, xl[0], bot, yf, fl, fc=WOODC, ec=INK, lw=0.6, z=5)
    out = []
    k = 1
    for z0, sd, run, zmid, fl_top in ((g, lo, ST_LO_RUN, ST_LO_MID, m.EL_A), (m.EL_A, up, ST_UP_RUN, ST_UP_MID, m.EL_B)):
        n, r, t = sd["risers"] // 2, sd["riser_in"] * IN, sd["tread_in"] * IN
        a, b = flight(ax, ST_Y0, z0, n, r, t, d=1, cut=True)
        line(ax, [(a[0], a[1] + GUARD), (b[0], b[1] + GUARD), (b[0] + 1.0, b[1] + GUARD)], lw=1.1, color=BLUE, z=7)
        rect(ax, ST_Y0 + run, zmid - 0.75, y1, zmid, fc=WOODC, ec=INK, lw=0.7, z=6)
        a2, b2 = flight(ax, ST_Y0 + run, zmid, n, r, t, d=-1, cut=False)
        line(ax, [(a2[0], a2[1] + GUARD), (b2[0], b2[1] + GUARD)], lw=0.5, color="#7fa3cf", z=5)
        rect(ax, yfi, fl_top - 0.85, ST_Y0, fl_top, fc=WOODC, ec=INK, lw=0.7, z=6)
        for (p0, p1) in ((a, b), (a2, b2)):
            cx, cz = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 - 1.55
            ax.add_patch(plt.Circle((cx, cz), 0.55, fc=PAPER, ec=INK, lw=0.6, zorder=10))
            txt(ax, cx, cz, str(k), size=5.4, weight="bold", z=11)
            k += 1
        out.append((a, b, zmid, run))
        # unit entry door D1 in the west wall, beyond
        d1 = [d for d in m.DOORS if d["tag"] == "D1"][0]
        rect(ax, d1["s0"], fl_top, d1["s1"], fl_top + DOOR_H, fc="#f4f4f2", ec=GREY, lw=0.5, z=3)
        txt(ax, (d1["s0"] + d1["s1"]) / 2, fl_top + 4.4, "D1\nunit entry\n20-min.\nself-closing", size=3.8, color=GREY, z=4)
    line(ax, [(ST_Y0, m.EL_B), (ST_Y0, m.EL_B + GUARD)], lw=1.2, color=BLUE, z=7)
    line(ax, [(ST_Y0, m.EL_B + GUARD), (ST_Y0 + 1.6, m.EL_B + GUARD)], lw=0.6, color=BLUE, z=7)
    return out


def stair_section_labels(ax, xl, yl, fl):
    g, yf, yfi, y1 = m.EL_GAR, m.YF, m.YFI, m.SHAFT_U[3]
    (a1, b1, zm1, run1), (a2, b2, zm2, run2) = fl
    for el, nm in ((g, "GARAGE / ENTRY"), (m.EL_A, "UNIT A"), (m.EL_B, "UNIT B")):
        txt(ax, xl[0] + 0.15, el + 0.4, f"{nm}\nEL {el:.1f}", size=4.4, weight="bold", ha="left", va="bottom", z=12)
    for zm in (zm1, zm2):
        txt(ax, (ST_Y0 + (run1 if zm == zm1 else run2) + y1) / 2, zm + 0.45, f"LANDING\nEL {zm:.1f}", size=4.2, weight="bold", va="bottom", z=12)
    xd = y1 + 1.35
    dim(ax, (xd, g), (xd, zm1), 0, fi(zm1 - g), ext=False, size=4.2, side=-1)
    dim(ax, (xd, zm1), (xd, m.EL_A), 0, fi(m.EL_A - zm1), ext=False, size=4.2, side=-1)
    dim(ax, (xd, m.EL_A), (xd, zm2), 0, fi(zm2 - m.EL_A), ext=False, size=4.2, side=-1)
    dim(ax, (xd, zm2), (xd, m.EL_B), 0, fi(m.EL_B - zm2), ext=False, size=4.2, side=-1)
    for el in (g, zm1, m.EL_A, zm2, m.EL_B):
        line(ax, [(y1 + 0.5, el), (xd + 0.3, el)], lw=0.25, color=GREY, z=8)
    zb = g - 1.1
    for a, b in ((yf + m.CMU, ST_Y0), (ST_Y0, ST_Y0 + run1), (ST_Y0 + run1, y1)):
        dim(ax, (a, zb), (b, zb), 0, fi(b - a), ext=False, size=4.2)
    txt(ax, ST_Y0 + run1 / 2, zb - 0.6, f"{m.STAIR_LO['treads_per_flight']} treads at {m.STAIR_LO['tread_in']} in.", size=4.0, z=12)
    zt = m.EL_A - 1.35
    dim(ax, (ST_Y0, zt), (ST_Y0 + run2, zt), 0, f"{fi(run2)} ({m.STAIR_UP['treads_per_flight']} treads)", ext=False, size=4.0)
    line(ax, [(ST_Y0 + run2, zt - 0.2), (ST_Y0 + run2, zm2 - 0.75)], lw=0.25, color=GREY, z=8)
    # handrail and guard heights, headroom
    ym = ST_Y0 + 5 * 10 * IN
    zn = a1[1] + (ym - a1[0]) * (b1[1] - a1[1]) / (b1[0] - a1[0])
    dim(ax, (ym, zn), (ym, zn + GUARD), 0, "36\" (34 to 38)", ext=False, size=4.0)
    note(ax, (ym + 1.2, zn + GUARD + 0.75), (ST_Y0 + 0.4, zn + 6.4), "HANDRAIL on the wall side, 34 to 38 in.\nabove the nosing line, returned to the wall", size=4.0, ha="left", color=BLUE)
    yh = ST_Y0 + run2 + 1.0
    dim(ax, (yh, zm1), (yh, zm2 - 0.75), 0, f"HEADROOM {fi(zm2 - 0.75 - zm1)} (6'-8\" min.)", ext=False, size=4.0, side=-1)
    note(ax, (ST_Y0, m.EL_B + 2.2), (ST_Y0 + 1.8, m.EL_B + 4.6), "GUARD 36 in. min. at the open\nside of the landing and well;\nno opening passes a 4 in. sphere", size=4.0, ha="left", color=BLUE)
    note(ax, (ST_Y0 + 2.6, g + 1.0), (ST_Y0 + 3.4, g + 0.75), "space under the stair closed off,\nnot a storage room", size=3.9, ha="left", color=GREY)
    note(ax, (yf + m.CMU, g + 4.5), (xl[0] + 0.2, g + 5.2), "STREET DOOR\n3'-0\" x 6'-8\"", size=4.0, ha="left")
    txt(ax, y1 + (m.Y_ST - y1) / 2, m.EL_B + 4.3, "1-HOUR WALL: 2x4 + 5/8 in. TYPE X EACH SIDE, TO THE ROOF DECK", size=3.6, rot=90, color=ACCENT, z=12, ha="center")
    txt(ax, (m.UTIL[2] + xl[1]) / 2 + 0.2, g + 4.5, "UTILITY\n(heated)", size=4.0, z=9)
    for fl_ in (m.EL_A, m.EL_B):
        txt(ax, (m.Y_ST + xl[1]) / 2 + 0.2, fl_ + 3.6, "BATH\n3", size=4.0, z=9)
        txt(ax, xl[0] + 0.15, fl_ - 1.0, "PORCH", size=3.8, ha="left", z=9)
        note(ax, (yf + 0.25, fl_ + 5.5), (yfi + 0.5, fl_ + 6.2), "W3 fixed,\ntempered", size=3.8, ha="left")
    txt(ax, (yfi + y1) / 2, Z_CLG_B + 0.4, "5/8 in. TYPE X LID UNDER THE ROOF TRUSSES", size=3.8, color=ACCENT, z=12)


def porch_detail(ax, unit, xl, yl):
    """Section through a porch at the door D14 (X = 28), looking west. unit = "A" or "B"."""
    yf, yfi, y0 = m.YF, m.YFI, m.PORCH[1]
    fl = m.EL_A if unit == "A" else m.EL_B
    bot = A_T0 if unit == "A" else B_T0
    sub = 0.75 * IN
    # floor trusses running out over the support, cantilevered 4'-0"
    truss_band(ax, y0 + 0.125, xl[1] + 1, bot, fl - sub, web=1.667)
    rect(ax, y0, bot - 0.06, y0 + 0.125, fl, fc=PAPER, ec=INK, lw=0.7, z=6)                    # fascia over the truss ends
    rect(ax, yfi, fl - sub, xl[1] + 1, fl, fc="#d8cfbd", ec=INK, lw=0.5, z=6)                  # subfloor inside
    for yb in np.arange(y0 + 0.02, yf - 0.3, 0.479):                                           # 5/4 x 6 decking, gapped
        rect(ax, yb, fl - 1 * IN, yb + 0.458, fl, fc="#d8cfbd", ec=INK, lw=0.4, z=6)
    line(ax, [(y0 + 0.15, fl - 1 * IN - 0.02), (yf, fl - 1 * IN + 0.06), (yf, fl + 0.5)], lw=1.2, color=BLUE, z=6.5)   # membrane, turned up the wall
    line(ax, [(y0 + 0.125, bot - 0.04), (yf if unit == "B" else m.B1_Y - 0.3, bot - 0.04)], lw=1.0, z=6)             # porch soffit
    # guard at the porch edge
    yg = y0 + 0.29
    rect(ax, yg - 0.146, bot + 0.3, yg + 0.146, fl + GUARD, fc=WOODC, ec=INK, lw=0.7, z=7)     # 4x4 post bolted to the rim
    rect(ax, yg - 0.23, fl + GUARD, yg + 0.23, fl + GUARD + 0.125, fc=WOODC, ec=INK, lw=0.7, z=7)
    rect(ax, yg - 0.06, fl + 0.29, yg + 0.06, fl + 0.29 + 0.29, fc=WOODC, ec=INK, lw=0.5, z=7.1)
    line(ax, [(yg + 0.15, fl + GUARD - 0.1), (yf, fl + GUARD - 0.1)], lw=0.4, color=GREY, z=4)
    line(ax, [(yg + 0.15, fl + 0.29), (yf, fl + 0.29)], lw=0.4, color=GREY, z=4)
    for yb in np.arange(yg + 0.6, yf - 0.2, 4.5 * IN):
        line(ax, [(yb, fl + 0.29), (yb, fl + GUARD - 0.1)], lw=0.2, color=LIGHT, z=3.9)
    # front wall and door D14
    rect(ax, yf, fl, yfi, yl[1] + 1, fc=POCHE, ec=INK, lw=0.4, z=5)
    rect(ax, yf - 0.02, fl, yfi + 0.02, min(fl + DOOR_H, yl[1] + 1), fc=PAPER, ec=INK, lw=0.4, z=5.5)
    rect(ax, yf + 0.15, fl, yf + 0.3, min(fl + DOOR_H, yl[1] + 1), fc=GLASS, ec=INK, lw=0.4, z=5.6)
    rect(ax, yf - 0.05, fl, yfi + 0.05, fl + 0.06, fc=GREY, ec=INK, lw=0.3, z=5.7)
    if unit == "A":
        i_beam(ax, m.B1_Y, m.EL_B1_TOP, m.B1_DEPTH)
        rect(ax, m.B1_Y - 0.28, m.EL_B1_TOP, m.B1_Y + 0.28, A_T0, fc=WOODC, ec=INK, lw=0.5, z=7)
        rect(ax, m.B1_Y + 0.3, A_T0 + 0.02, xl[1] + 1, A_T0 + 0.8, fc=INSUL, ec="#c98a98", lw=0.3, z=5.3)
        line(ax, [(m.B1_Y + 0.3, A_T0 - 0.05), (xl[1] + 1, A_T0 - 0.05)], lw=1.5, color=ACCENT, z=6)
    else:
        rect(ax, yf, yl[0] - 1, yfi, B_T0, fc=POCHE, ec=INK, lw=0.4, z=5)                      # Unit A front wall below
        rect(ax, yf - 0.02, yl[0] - 1, yfi + 0.02, m.EL_A + DOOR_H, fc=PAPER, ec=INK, lw=0.4, z=5.5)
        line(ax, [(yfi, Z_CLG_A - 0.03), (xl[1] + 1, Z_CLG_A - 0.03)], lw=1.5, color=ACCENT, z=6)
        # roof truss heel and the 4'-0" overhang above
        ch = 0.46 * math.hypot(1, P)
        ya = yf - OH_F
        top = lambda y: EAVE + (y - yf) * P                                                    # noqa: E731
        poly(ax, [(ya, top(ya)), (xl[1] + 1, top(xl[1] + 1)), (xl[1] + 1, top(xl[1] + 1) - ch), (ya, top(ya) - ch)], fc=WOODC, ec=INK, lw=0.7, z=6)
        line(ax, [(ya - 0.2, top(ya - 0.2) + 0.1), (xl[1] + 1, top(xl[1] + 1) + 0.1)], lw=2.0, color="#5c6269", z=6.2)
        rect(ax, yf, m.EL_PLATE, xl[1] + 1, m.EL_PLATE + 0.29, fc=WOODC, ec=INK, lw=0.6, z=6)
        rect(ax, yf, m.EL_PLATE + 0.29, yf + 0.29, EAVE - ch + 0.03, fc=WOODC, ec=INK, lw=0.6, z=6.1)
        rect(ax, ya - 0.125, Z_SOFFIT_F, ya, top(ya), fc=PAPER, ec=INK, lw=0.7, z=6.3)
        rect(ax, ya - 0.5, Z_EAVE_F - 0.45, ya - 0.125, Z_EAVE_F - 0.05, fc=PAPER, ec=INK, lw=0.6, z=6.3)   # gutter
        line(ax, [(ya, Z_SOFFIT_F), (yf, Z_SOFFIT_F)], lw=1.0, z=6.3)
        ins = [(yfi, m.EL_PLATE + 0.29), (yfi, top(yfi) - ch - 0.08)]
        ins += [(y, min(m.EL_PLATE + 0.29 + 1.33, top(y) - ch - 0.08)) for y in np.linspace(yfi + 0.3, xl[1] + 1, 12)]
        poly(ax, ins + [(xl[1] + 1, m.EL_PLATE + 0.29)], fc=INSUL, ec="#c98a98", lw=0.3, z=5.5)
        line(ax, [(yfi, Z_CLG_B), (xl[1] + 1, Z_CLG_B)], lw=1.0, z=6)


def porch_labels(ax, unit, xl, yl):
    yf, yfi, y0 = m.YF, m.YFI, m.PORCH[1]
    fl = m.EL_A if unit == "A" else m.EL_B
    bot = A_T0 if unit == "A" else B_T0
    yg = y0 + 0.29
    dim(ax, (y0, bot - 0.75), (yf, bot - 0.75), 0, f"{ftin(yf - y0)} CANTILEVER", ext=False, size=4.6)
    for y in (y0, yf):
        line(ax, [(y, bot - 1.0), (y, bot - 0.15)], lw=0.25, color=GREY, z=8)
    dim(ax, (yg + 1.3, fl), (yg + 1.3, fl + GUARD + 0.125), 0, "36\" MIN.", ext=False, size=4.4, side=-1)
    dim(ax, (yg + 0.75, fl), (yg + 0.75, fl + 0.29), 0, "3 1/2\"", ext=False, size=3.8, side=-1)
    txt(ax, xl[1] - 0.1, fl + 0.5, f"UNIT {unit}\nEL {fl:.1f}", size=4.6, weight="bold", ha="right", va="bottom", z=12)
    note(ax, (y0 + 2.2, fl - 0.05), (y0 + 1.75, fl + 1.5), "5/4 x 6 decking on a\nsloped membrane (blue)", size=4.0, ha="left")
    note(ax, (yg, fl + 2.0), (xl[0] + 0.1, fl + 2.6), "4x4 post bolted\nto the rim;\nbalusters under\n4 in. apart", size=4.0, ha="left")
    if unit == "A":
        dim(ax, (yf, bot - 1.65), (m.B1_Y, bot - 1.65), 0, "6\"", ext=False, size=4.0, side=-1)
        line(ax, [(m.B1_Y, bot - 1.9), (m.B1_Y, Z_B1_BOT - 0.05)], lw=0.25, color=GREY, ls=CHAIN, z=8)
        note(ax, (m.B1_Y + 0.25, Z_B1_BOT + 0.5), (m.B1_Y + 0.8, Z_B1_BOT + 0.25), f"B1 W14x34 (prelim.), top EL {m.EL_B1_TOP:.2f},\n1 1/2 in. nailer; trusses run over it", size=4.0, ha="left")
        note(ax, (y0 + 2.0, bot - 0.04), (xl[0] + 0.1, bot - 2.0), "porch soffit (exterior\nboard) to the beam", size=4.0, ha="left")
        note(ax, (xl[1] - 0.6, A_T0 + 0.4), (xl[1] - 0.2, bot - 2.1), "R-30 + 5/8 in. Type X\nover the garage", size=4.0, ha="right")
        dim(ax, (xl[1] - 0.45, bot), (xl[1] - 0.45, fl), 0, "20\" TRUSS + 3/4\"", ext=False, size=3.9)
        txt(ax, yfi + 0.9, fl + 3.0, "D14", size=4.4, weight="bold", z=9)
    else:
        ya = yf - OH_F
        dim(ax, (ya, EAVE + 0.75), (yf, EAVE + 0.75), 0, f"{ftin(OH_F)} ROOF OVERHANG", ext=False, size=4.6)
        for y in (ya, yf):
            line(ax, [(y, EAVE + 1.0), (y, EAVE + 0.1 if y == yf else Z_EAVE_F + 0.2)], lw=0.25, color=GREY, z=8)
        dim(ax, (yf - 1.2, fl), (yf - 1.2, Z_SOFFIT_F), 0, f"{ftin(Z_SOFFIT_F - fl)} TO THE SOFFIT", ext=False, size=4.2)
        dim(ax, (xl[1] - 0.45, m.EL_PLATE), (xl[1] - 0.45, EAVE), 0, "12\" HEEL", ext=False, size=3.9)
        line(ax, [(yf, EAVE), (xl[1] - 0.2, EAVE)], lw=0.25, color=GREY, z=8)
        note(ax, (ya + 1.6, Z_SOFFIT_F), (xl[0] + 0.1, Z_SOFFIT_F - 1.1), "vented soffit\n(attic intake)", size=4.0, ha="left")
        note(ax, (ya - 0.3, Z_EAVE_F - 0.3), (xl[0] + 0.1, Z_EAVE_F + 1.3), "fascia and gutter", size=4.0, ha="left")
        note(ax, (yfi + 1.0, m.EL_PLATE + 1.0), (yfi + 0.5, m.EL_PLATE - 1.0), f"R-49; top plate\nEL {m.EL_PLATE:.2f}", size=4.0, ha="left")
        note(ax, (y0 + 2.4, bot - 0.04), (xl[0] + 0.1, bot - 1.9), "soffit = ceiling of\nthe Unit A porch", size=4.0, ha="left")
        dim(ax, (xl[1] - 0.45, bot), (xl[1] - 0.45, fl), 0, "24\" TRUSS + 3/4\"", ext=False, size=3.9)
        note(ax, (yfi + 0.8, Z_CLG_A - 0.03), (xl[1] - 0.1, bot - 1.9), "2 layers 5/8 in. Type X:\n1-hour floor/ceiling", size=4.0, ha="right", color=ACCENT)
        txt(ax, yfi + 0.9, fl + 3.0, "D14", size=4.4, weight="bold", z=9)


def sheet_a402(pdf):
    lo, up = m.STAIR_LO, m.STAIR_UP
    notes = [
        ("Stair (IRC R311.7)", [
            f"Garage to Unit A: {lo['risers']} risers at {inch(lo['riser_in'])} in.",
            f"Unit A to Unit B: {up['risers']} risers at {inch(up['riser_in'])} in.",
            "Treads 10 in. plus a 1 in. nosing. Risers",
            "within 3/8 in. of each other in a flight.",
            f"Flights {fi(FLIGHT_U)} wide; {fi(FLIGHT_L)} between the",
            "concrete walls of the lower stair (36 in.",
            "min. clear above the handrail).",
            "Headroom 6'-8\" min.: over 9 ft here.",
        ]),
        ("Handrails and guards (R311.7.8, R312)", [
            "Handrail one side of every flight, 34 to",
            "38 in. above the nosings, 1 1/4 to 2 in.",
            "round grip, 1 1/2 in. off the wall.",
            "Guards 36 in. min. at landings and porches;",
            "4 in. sphere rule (4 3/8 in. at stair",
            "sides). Posts resist 200 lb at the top.",
        ]),
        ("Enclosure", [
            "Stair walls: 2x4 + 5/8 in. Type X each",
            "side, 1 hour, to the roof deck. Unit entry",
            "doors D1: 20-minute, self-closing.",
            "Automatic lights: see E-104.",
        ]),
        ("Porches", [
            "Floor trusses cantilever 4'-0\" past beam",
            "B1 (Unit A) and the front wall (Unit B).",
            "Zoning allows 5'-0\" into the front",
            "setback. Truss supplier and engineer to",
            "design the cantilever and its protection.",
        ]),
    ]
    fig, bg = new_sheet("A-402", TITLE["A-402"], "As noted", notes)
    # --- stair plans at 1/4 in.
    f4 = 4.0
    xlp, ylp = (m.GAR_X1 - 2.25, m.XE + 1.65), (m.YF - 2.6, m.SHAFT_U[3] + 1.1)
    wp, hp = (xlp[1] - xlp[0]) / f4, (ylp[1] - ylp[0]) / f4
    bp = SHEET_H - MARGIN - 0.1 - hp
    lp = MARGIN + 0.2
    for i, (lev, nm) in enumerate((("G", "Garage level"), ("A", "Unit A level"), ("B", "Unit B level"))):
        l_ = lp + i * (wp + 0.08)
        ax = plan_axes(fig, l_, bp, xlp, ylp, f4)
        stair_plan(ax, lev)
        title_under(bg, (l_, bp), i + 1, f"Stair plan, {nm}", "1/4\" = 1'-0\" · north up")
    # --- stair section at 1/4 in.
    xls, yls = (m.YF - 2.3, m.SHAFT_U[3] + 2.6), (m.EL_GAR - 2.2, Z_CLG_B + 1.0)
    ws, hs = (xls[1] - xls[0]) / f4, (yls[1] - yls[0]) / f4
    ls_ = SHEET_W - MARGIN - TB_W - 0.15 - ws
    bs = SHEET_H - MARGIN - 0.1 - hs
    axs = plan_axes(fig, ls_, bs, xls, yls, f4)
    fl = stair_section(axs, xls, yls)
    stair_section_labels(axs, xls, yls, fl)
    title_under(bg, (ls_, bs), 4, "Stair section", f"1/4\" = 1'-0\" · X = {XS2:.0f} ft, looking west · flights numbered 1 to 4")
    rows = [("Flight", "From EL", "To EL", "Risers", "Treads", "Run")]
    for i, (z0, z1, sd, run) in enumerate(((m.EL_GAR, ST_LO_MID, lo, ST_LO_RUN), (ST_LO_MID, m.EL_A, lo, ST_LO_RUN),
                                           (m.EL_A, ST_UP_MID, up, ST_UP_RUN), (ST_UP_MID, m.EL_B, up, ST_UP_RUN))):
        rows.append((str(i + 1), f"{z0:.1f}", f"{z1:.1f}", f"{sd['risers'] // 2} at {inch(sd['riser_in'])} in.",
                     f"{sd['treads_per_flight']} at {sd['tread_in']} in.", fi(run)))
    table(bg, ls_, bs - 0.62, [0.5, 0.65, 0.6, 1.05, 0.95, 0.6], rows, fs=5.6, rh=0.19)
    # --- porch details at 3/8 in.
    f8 = 8 / 3
    xlq = (m.PORCH[1] - 1.75, m.YFI + 2.5)
    wq = (xlq[1] - xlq[0]) / f8
    ylb = (B_T0 - 2.6, EAVE + 1.5)
    yla = (Z_B1_BOT - 1.5, m.EL_A + GUARD + 1.0)
    bq = 0.8
    axb = plan_axes(fig, lp, bq, xlq, ylb, f8)
    porch_detail(axb, "B", xlq, ylb)
    porch_labels(axb, "B", xlq, ylb)
    title_under(bg, (lp, bq), 5, "Unit B porch and roof overhang", "3/8\" = 1'-0\" · at door D14, looking west")
    la = lp + wq + 0.35
    axa = plan_axes(fig, la, bq, xlq, yla, f8)
    porch_detail(axa, "A", xlq, yla)
    porch_labels(axa, "A", xlq, yla)
    title_under(bg, (la, bq), 6, "Unit A porch over beam B1", "3/8\" = 1'-0\" · at door D14, looking west")
    ty = bq + (yla[1] - yla[0]) / f8 + 1.55
    bg.text(la, ty, "PORCH NOTES", fontsize=7.0, fontweight="bold", va="top")
    bg.text(la, ty - 0.22,
            "1. Both porches are 4'-0\" deep and run from the garage opening's west\n"
            f"    jamb to the east wall ({ftin(m.PORCH[2] - m.PORCH[0])}). No posts: nothing stands on the apron.\n"
            "2. The porch edge is 6'-2\" from the front lot line (4'-0\" into the 10 ft\n"
            "    setback; 5'-0\" is allowed). The roof overhang lines up with it.\n"
            "3. Guard: 36 in. min., bottom rail 3 1/2 in. above the deck, balusters\n"
            "    under 4 in. apart, 200 lb load at the top rail (IRC R312, R301.5).\n"
            "4. In front of the stair (east 7 ft) there are no floor trusses behind\n"
            "    the porch: framing there is by the engineer (S-204).\n"
            "5. Keep the truss cantilever dry: membrane under the decking, turned\n"
            "    up the wall and over the fascia; closed soffit below.",
            fontsize=5.6, va="top", linespacing=1.32)
    save(fig, "A-402", pdf)


# ---SHEETS---
SHEETS = [("A-201", sheet_a201), ("A-202", sheet_a202), ("A-301", sheet_a301), ("A-402", sheet_a402)]
