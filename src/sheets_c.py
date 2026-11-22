"""Civil / site sheets C-101 to C-107 (Rev E).

Everything is drawn from model.py (the building), common.py (lot, LiDAR ground, street) and the
numbers computed in section 1 below (excavation, apron surface, swale, drain inverts, wall heights).
Site-only assumptions that the model does not hold are named constants in section 1 and are listed
on the sheets as preliminary.
"""
import math
import textwrap
from functools import lru_cache

import numpy as np
from matplotlib.patches import Circle, Rectangle
from matplotlib.path import Path
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

import common as C
import model as m
from common import *  # noqa: F401,F403
from index import TITLE
from plans import *  # noqa: F401,F403

# ----------------------------------------------------------------------------
# 1. Site numbers computed from the model and the LiDAR ground
# ----------------------------------------------------------------------------
WATER = BLUE
SEWER = "#7a4a9c"
POWER = "#c05a00"
STORM = "#0f7b6c"
SHORE = "#b3261e"
CUT = "#8a6f52"
SEED = "#e3efd9"
GRAVEL = "#ece7dc"

_CW = math.cos(WEST_LEAN)
_SWL = math.sin(WEST_LEAN)
T_R = math.atan(abs(REAR_SLOPE))
N_R = (math.sin(T_R), math.cos(T_R))        # unit normal of the rear wall, toward the rear lot line
U_R = (math.cos(T_R), -math.sin(T_R))       # along the rear wall, west to east
N_W = (-_CW, _SWL)                          # unit normal of the west wall, toward the west lot line
YARD = SB_SIDE + m.M                        # 5'-2": every wall face to its lot line (side and rear)

PARCELS = neighbour_parcels()
FOOTPRINTS = [Polygon(fp).buffer(0) for fp in building_footprints()]
_LOTP = Polygon(LOT)
OLD_HOUSE = [g for g in FOOTPRINTS if g.representative_point().within(_LOTP.buffer(3))][0]
NB_W = min((g for g in FOOTPRINTS if g.centroid.x < 0 and g.distance(_LOTP) < 5), key=lambda g: g.distance(_LOTP))
NB_E = min((g for g in FOOTPRINTS if g.centroid.x > 50 and g.centroid.y < 40), key=lambda g: g.distance(_LOTP))
NB_N = min((g for g in FOOTPRINTS if g.centroid.y > 55 and 0 < g.centroid.x < 50), key=lambda g: g.distance(_LOTP))
GAP_W, GAP_E, GAP_N = (g.distance(_LOTP) for g in (NB_W, NB_E, NB_N))


def elev_v(X, Y):
    """Vector form of common.elev (same bilinear read of the 1 m DEM)."""
    X, Y = np.asarray(X, float), np.asarray(Y, float)
    E = C._SW[0] + (X * C._ex[0] + Y * C._ey[0]) * FT
    N = C._SW[1] + (X * C._ex[1] + Y * C._ey[1]) * FT
    c = (E - C._bd[0]) - 0.5
    r = (C._bd[3] - N) - 0.5
    c0, r0 = np.floor(c).astype(int), np.floor(r).astype(int)
    fx, fy = c - c0, r - r0
    z = C._z
    return (z[r0, c0] * (1 - fx) * (1 - fy) + z[r0, c0 + 1] * fx * (1 - fy)
            + z[r0 + 1, c0] * (1 - fx) * fy + z[r0 + 1, c0 + 1] * fx * fy)


# ---- apron surface: garage floor at the opening line, street level at the pavement edge ----
APRON_LEN = m.YF - PAVE_N


def apron_edges(y):
    """West and east edge of the apron at depth y (PAVE_N <= y <= YF)."""
    if y >= 0:
        return m.apron_x(y, 0), m.apron_x(y, 1)
    t = y / PAVE_N
    return m.OPEN[0] + 1.5 - 2.0 * t, m.OPEN[1] - 1.5 + 2.0 * t


def apron_el(x, y):
    """Finish surface: straight grade from EL_GAR at the opening to the pavement edge at the same fan line."""
    xw, xe = apron_edges(y)
    f = min(1.0, max(0.0, (x - xw) / (xe - xw)))
    xp = (m.OPEN[0] - 0.5) + f * (m.OPEN_W + 1.0)
    return m.EL_GAR + (street_el(xp) - m.EL_GAR) * (m.YF - y) / APRON_LEN


APRON_STA = [("West edge", m.OPEN[0], m.OPEN[0] - 0.5), ("Middle", (m.OPEN[0] + m.OPEN[1]) / 2, (m.OPEN[0] + m.OPEN[1]) / 2),
             ("East edge", m.OPEN[1], m.OPEN[1] + 0.5)]            # name, x at the opening, x at the pavement
APRON_SLOPE = [(n, xo, xp, street_el(xp), 100 * (street_el(xp) - m.EL_GAR) / APRON_LEN) for n, xo, xp in APRON_STA]

# ---- excavation for the garage box ----
FTG_TOE = (m.FTG_W - m.CONC) / 2            # footing shown centred under the 12 in. wall: 1'-6" each side
WORK = 2.0                                  # working space outside the footing toe
EXC_OFF = FTG_TOE + WORK                    # face of the excavation: 3'-6" outside the wall face
EL_EXC = m.EL_FTG_TOP - m.FTG_T             # bottom of footing = bottom of the excavation at the walls
EL_SUBGR = m.EL_GAR - 1.0                   # bottom of the 6 in. stone under the garage slab
Y_EXC_S = m.YF - FTG_TOE                    # south edge of the deep dig (front footing toe)
Y_EXC_N = m.Y_GR_O + EXC_OFF


def xw_exc(y):
    return m.xw_o(y) - EXC_OFF / _CW


EXC = [(xw_exc(Y_EXC_S), Y_EXC_S), (m.XE + EXC_OFF, Y_EXC_S), (m.XE + EXC_OFF, Y_EXC_N), (xw_exc(Y_EXC_N), Y_EXC_N)]
_IN = FTG_TOE + m.CONC                      # inside edge of the footing, from the outside wall face
EXC_IN = [(m.xw_o(m.YF + _IN) + _IN / _CW, m.YF + _IN), (m.XE - _IN, m.YF + _IN),
          (m.XE - _IN, m.Y_GR_O - _IN), (m.xw_o(m.Y_GR_O - _IN) + _IN / _CW, m.Y_GR_O - _IN)]
EL_SOG_SUBGR = m.EL_SLAB_A - (5 + 2 + 4) / 12.0     # Unit A slab 5 in. + R-10 (2 in.) + 4 in. stone
EL_LAND_SUBGR = m.EL_GAR - (4 + 6) / 12.0           # landing and trash bay: 4 in. slab on 6 in. stone
LAND_POLY = unary_union([Polygon(m.WALK), box(m.TRASH[0], m.TRASH[1], m.TRASH[2], m.TRASH[3])])


def _grid_in(poly_pts, step=0.25):
    xs0, ys0 = zip(*poly_pts)
    xs = np.arange(min(xs0) + step / 2, max(xs0), step)
    ys = np.arange(min(ys0) + step / 2, max(ys0), step)
    X, Y = np.meshgrid(xs, ys)
    inside = Path(poly_pts).contains_points(np.c_[X.ravel(), Y.ravel()])
    return X.ravel()[inside], Y.ravel()[inside], step * step


@lru_cache(maxsize=None)
def quantities():
    """Bank volumes (cubic yards) with neat vertical (shored) sides, from the 1 m LiDAR DEM."""
    q = {}
    X, Y, dA = _grid_in(EXC)
    Z = elev_v(X, Y)
    inner = Path(EXC_IN).contains_points(np.c_[X, Y])
    q["box"] = float(np.clip(Z - EL_SUBGR, 0, None).sum() * dA) / 27                     # everything down to slab subgrade
    q["ftg"] = float((np.clip(Z - EL_EXC, 0, None) - np.clip(Z - EL_SUBGR, 0, None))[~inner].sum() * dA) / 27
    q["box_area"] = poly_area(EXC)
    q["box_mean"] = float(np.clip(Z - EL_EXC, 0, None)[~inner].mean())
    # apron (6 in. concrete on 6 in. stone), outside the deep dig
    X, Y, dA = _grid_in(m.APRON)
    keep = Y < Y_EXC_S
    X, Y = X[keep], Y[keep]
    bot = np.array([apron_el(x, y) for x, y in zip(X, Y)]) - 1.0
    q["apron"] = float(np.clip(elev_v(X, Y) - bot, 0, None).sum() * dA) / 27
    # landing and trash bay
    pts = list(LAND_POLY.exterior.coords)
    X, Y, dA = _grid_in(pts)
    keep = Y < Y_EXC_S
    q["land"] = float(np.clip(elev_v(X[keep], Y[keep]) - EL_LAND_SUBGR, 0, None).sum() * dA) / 27
    # Unit A slab on grade north of the deep dig: cut to subgrade
    X, Y, dA = _grid_in(m.SOG)
    keep = Y > Y_EXC_N
    q["sog"] = float(np.clip(elev_v(X[keep], Y[keep]) - EL_SOG_SUBGR, 0, None).sum() * dA) / 27
    # stem-wall trenches (2'-6" wide, to 36 in. below finish grade) below that subgrade, outside the deep dig
    vol = 0.0
    for a, b in ((STEM_W[0], STEM_W[1]), (STEM_N[0], STEM_N[1])):
        L = math.dist(a, b)
        for i in range(int(L / 0.5)):
            t = (i + 0.5) * 0.5 / L
            x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            if y < Y_EXC_N:
                continue
            top = min(elev(x, y), EL_SOG_SUBGR)
            vol += max(0.0, top - stem_ftg_bottom(x, y)) * 2.5 * 0.5
    q["stem"] = vol / 27
    q["total"] = q["box"] + q["ftg"] + q["apron"] + q["land"] + q["sog"] + q["stem"]
    return q


# ---- rear swale, finish grade at the rear wall, stem wall ----
SWALE_OFF = 2.5                             # swale centre line from the rear wall face
SWALE_CUT = 0.5                             # invert below existing grade on the centre line
STEM_UP = 8 / 12.0                          # top of concrete above finish grade
STEM_N = (m.OUT_U[3], m.OUT_U[2])           # rear wall, west to east
STEM_W = (m.SOG[0], m.OUT_U[3])             # west wall north of the garage box


def rear_pt(s, off=0.0):
    """Point at distance s along the rear wall from the NW building corner, `off` ft toward the rear line."""
    a = m.OUT_U[3]
    return (a[0] + U_R[0] * s + N_R[0] * off, a[1] + U_R[1] * s + N_R[1] * off)


def swale_inv(s):
    return elev(*rear_pt(s, SWALE_OFF)) - SWALE_CUT


def fg_rear(s):
    """Finish grade at the rear wall: 5 % up from the swale invert."""
    return swale_inv(s) + 0.05 * SWALE_OFF


def stem_ftg_bottom(x, y):
    """Bottom of the stem-wall footing: 36 in. below finish grade, and at least 18 in. below the Unit A floor."""
    return min(elev(x, y) - 3.0, m.EL_SLAB_A - 1.5)


# ---- drains ----
FD_OFF = FTG_TOE + 0.5                      # French drain centre line: beside the footing toe, 2'-0" from the wall face
_fdw = lambda y: m.xw_o(y) - FD_OFF / _CW   # noqa: E731
FD = [(_fdw(m.YF), m.YF), (_fdw(m.Y_GR_O + FD_OFF), m.Y_GR_O + FD_OFF), (m.XE + FD_OFF, m.Y_GR_O + FD_OFF), (m.XE + FD_OFF, m.YF)]
J1 = (m.XE + FD_OFF, m.YF - 1.2)            # junction cleanout: trench drain and storm line join the solid outlet pipe
PIT_R = 0.75                                # 18 in. meter pit
TAIL = [FD[3], J1, (m.XE + FD_OFF, 2.2), (m.WATER_METERS[0][0] - PIT_R - 0.5, 0.3),
        (m.WATER_METERS[0][0] - PIT_R - 0.5, m.WATER_METERS[0][1] - 1.9), m.DRAIN_OUT]     # solid pipe, jogs round the meter pit


def _cum(pts):
    out = [0.0]
    for a, b in zip(pts, pts[1:]):
        out.append(out[-1] + math.dist(a, b))
    return out


FD_RUN = FD + TAIL[1:]
FD_STA = _cum(FD_RUN)
FD_LEN = FD_STA[-1]
FD_SLOPE = (m.EL_DRAIN_HI - m.EL_DRAIN_OUT) / FD_LEN


def fd_inv(i):
    return m.EL_DRAIN_HI - FD_SLOPE * FD_STA[i]


TD_Y = m.YF - 0.6                           # trench drain line (brief)
EL_TD_OUT = m.EL_GAR - 1.0                  # trench drain outlet invert: 12 in. below the grate (assumed channel depth)
X_S1 = 49.1                                 # storm line S1 down the east side yard (solid)
UD_OFF = 1.0                                # upper drain behind the rear stem wall
UD_DEPTH = 3.0                              # its invert below finish grade (at the stem footing)
S1 = [rear_pt(m.REAR_WALL_LEN + 1.0, UD_OFF), (X_S1, rear_pt(m.REAR_WALL_LEN + 1.0, UD_OFF)[1] - 1.5), (X_S1, J1[1] + 1.6), J1]
# downspouts: assumed at the four roof corners until A-105 fixes them
DS = {"NW": (m.OUT_U[3][0] + 0.6, m.OUT_U[3][1] - 0.2), "NE": (m.XE, m.yr_o(m.XE) - 0.1), "SW": (m.xw_o(m.YF), m.YF), "SE": (m.XE, m.YF)}
RL_OFF = 3.4                                # west roof leader: from the west wall face
RL_W = [(m.xw_o(40.0) - RL_OFF / _CW, 40.0), (m.xw_o(m.YF) - RL_OFF / _CW, m.YF), (4.2, 1.0), (7.5, PAVE_N + 0.6)]

# ---- water service route (two 1 in. lines, 8 in. apart) ----
X_WA, X_WB = 47.6, 48.3
WATER_A = [m.WATER_METERS[0], (m.WATER_METERS[0][0], m.WATER_METERS[0][1] + PIT_R), (X_WA, 1.0), (X_WA, m.WATER_ENTRY[1]), m.WATER_ENTRY]
WATER_B = [m.WATER_METERS[1], (m.WATER_METERS[1][0], m.WATER_METERS[1][1] + PIT_R), (X_WB, 1.0), (X_WB, m.WATER_ENTRY[1] + 0.67), (m.XE, m.WATER_ENTRY[1] + 0.67)]
X_ET = 45.75                                # electric and telecom conduits

# ---- trash bay: what four carts need (catalogue 96 gal cart, 26 x 34 in.) ----
CART_W, CART_D = 26 / 12.0, 34 / 12.0
BAY_NEED = (4 * CART_W + 5 * 2 / 12.0, CART_D + 4 / 12.0)          # 2 in. between carts, 4 in. to the gate
BAY_OK = (m.TRASH[2] - m.TRASH[0]) >= BAY_NEED[0] - 0.01 and (m.TRASH[3] - m.TRASH[1]) >= BAY_NEED[1] - 0.01
BAY = m.TRASH if BAY_OK else (m.TRASH[2] - BAY_NEED[0], m.TRASH[1], m.TRASH[2], m.TRASH[1] + BAY_NEED[1])

FENCE_H = 6.0
MEAN_ROOF = ((m.EL_PLATE + m.HEEL) + m.EL_RIDGE_HI) / 2             # mid-height of the roof, highest ridge
BLDG_H = MEAN_ROOF - m.avg_grade()
PORCH_W = m.PORCH[2] - m.PORCH[0]
HP_CLEAR = min((hx - m.HP_SIZE[1] / 2 - west_x(hy)) * _CW for hx, hy in m.HP)


# ----------------------------------------------------------------------------
# 2. Drafting helpers
# ----------------------------------------------------------------------------
def notes(blocks, width=47):
    """Wrap title-block notes to the column width and warn when the column overflows."""
    out, used = [], 0.0
    for head, items in blocks:
        lines = []
        for it in items:
            lines += textwrap.wrap(it, width, subsequent_indent="    " if it[:2] in ("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.") else "")
        out.append((head, lines))
        used += 0.19 + 0.183 * len(lines) + 0.12
    if used > 5.72:
        print(f"   !! title-block notes overflow by {(used - 5.72) / 0.183:.1f} lines")
    return out


def block(bg, x, y, w, head, items, fs=5.9, color=INK, hang="   ", gap=0.035, rule=True):
    """Heading + wrapped paragraphs on the sheet (inches). Returns the y below the block."""
    cpl = max(12, int(w / (fs * 0.0074)))
    lh = fs * 0.0139 * 1.3
    if head:
        bg.text(x, y, head.upper(), fontsize=fs + 1.1, fontweight="bold", color=color, va="top")
        y -= (fs + 1.1) * 0.0139 * 1.45
        if rule:
            bg.plot([x, x + w], [y + 0.02, y + 0.02], color=color, lw=0.5)
            y -= 0.05
    for it in items:
        for ln in textwrap.wrap(it, cpl, subsequent_indent=hang):
            bg.text(x, y, ln, fontsize=fs, color=color, va="top")
            y -= lh
        y -= gap
    return y - 0.08


def ztable(bg, x, y, widths, rows, fs=5.7, rh=0.2, flag=()):
    """Ruled table (inches). rows[0] is the header; rows whose index is in `flag` are printed red and bold."""
    W = sum(widths)
    for r, row in enumerate(rows):
        yy = y - r * rh
        red = r in flag
        if r == 0:
            bg.add_patch(Rectangle((x, yy - rh), W, rh, fc="#e3e6ea", ec="none"))
        elif red:
            bg.add_patch(Rectangle((x, yy - rh), W, rh, fc="#fbe3e0", ec="none"))
        elif r % 2 == 0:
            bg.add_patch(Rectangle((x, yy - rh), W, rh, fc="#f6f7f8", ec="none"))
        cx = x
        for wd, cell in zip(widths, row):
            bg.text(cx + 0.05, yy - rh / 2, str(cell), fontsize=fs, va="center", color=ACCENT if red else INK,
                    fontweight="bold" if (r == 0 or red) else "normal")
            cx += wd
        bg.plot([x, x + W], [yy - rh, yy - rh], color=LIGHT, lw=0.4)
    bg.add_patch(Rectangle((x, y - len(rows) * rh), W, len(rows) * rh, fill=False, ec=INK, lw=0.6))
    return y - len(rows) * rh


def lead(ax, tip, at, s, size=5.2, color=INK, ha="left", va="center", weight="normal", head="-|>", box=True, z=12):
    ax.annotate(s, xy=tip, xytext=at, fontsize=size, color=color, ha=ha, va=va, fontweight=weight, zorder=z, linespacing=1.2,
                arrowprops=dict(arrowstyle=head, lw=0.45, color=color, shrinkA=1.5, shrinkB=0, mutation_scale=5),
                bbox=dict(fc=PAPER, ec="none", pad=0.6) if box else None)


def key(ax, x, y, n, color=BLUE, tip=None):
    r = 0.105 * ax.fpi
    if tip is not None:
        line(ax, [(x, y), tip], color=color, lw=0.45, z=12)
        ax.add_patch(Circle(tip, 0.022 * ax.fpi, fc=color, ec=color, lw=0.3, zorder=12))
    ax.add_patch(Circle((x, y), r, fc=PAPER, ec=color, lw=0.8, zorder=13))
    txt(ax, x, y, str(n), size=5.4, weight="bold", color=color, z=14)


def arrow(ax, a, b, color=BLUE, lw=0.8, z=11, scale=6, ls="-"):
    ax.annotate("", xy=b, xytext=a, zorder=z,
                arrowprops=dict(arrowstyle="-|>", lw=lw, color=color, shrinkA=0, shrinkB=0, mutation_scale=scale, ls=ls))


def spot(ax, x, y, dx=1.0, dy=1.0, size=5.0, color=EARTH, val=None, pre="", z=10):
    v = elev(x, y) if val is None else val
    s = 0.045 * ax.fpi
    line(ax, [(x - s, y - s), (x + s, y + s)], lw=0.5, color=color, z=z)
    line(ax, [(x - s, y + s), (x + s, y - s)], lw=0.5, color=color, z=z)
    txt(ax, x + dx, y + dy, f"{pre}{v:.1f}", size=size, color=color, ha="left" if dx >= 0 else "right", box=True, z=z)


def frame(fig, view, fpi, left=None, bottom=0.55):
    x0, y0, x1, y1 = view
    ax = plan_axes(fig, MARGIN + 0.25 if left is None else left, bottom, (x0, x1), (y0, y1), fpi)
    ax.view = view
    return ax


@lru_cache(maxsize=None)
def _zgrid(x0, y0, x1, y1, step):
    xs = np.arange(x0, x1 + step, step)
    ys = np.arange(y0, y1 + step, step)
    X, Y = np.meshgrid(xs, ys)
    return xs, ys, elev_v(X, Y)


def contours(ax, alpha=1.0, labels=True, clip=None):
    x0, y0, x1, y1 = ax.view
    xs, ys, Z = _zgrid(x0 - 2, y0 - 2, x1 + 2, y1 + 2, 1.0)
    lv1 = np.arange(math.floor(Z.min()), Z.max(), 1)
    lv5 = np.arange(math.floor(Z.min() / 5) * 5, Z.max(), 5)
    c1 = ax.contour(xs, ys, Z, levels=lv1, colors=EARTH, linewidths=0.25, alpha=0.55 * alpha, zorder=2)
    c5 = ax.contour(xs, ys, Z, levels=lv5, colors=EARTH, linewidths=0.7, alpha=0.9 * alpha, zorder=2)
    if labels:
        ax.clabel(c5, fmt="%d", fontsize=5.2, colors=EARTH)
    return c1, c5


@lru_cache(maxsize=None)
def _pavement(view):
    """Pavement = the band 7 to 21 ft off the north side of the Baird St right-of-way (follows the bend at the west)."""
    x0, y0, x1, y1 = view
    vb = box(x0 - 30, y0 - 30, x1 + 30, y1 + 30)
    allp, north = [], [_LOTP]
    for p in PARCELS:
        g = Polygon(p["ring"]).buffer(0)
        if not g.intersects(vb):
            continue
        if p["id"] == SUBJECT_ID:
            g = _LOTP
        allp.append(g.buffer(0.4))
        if g.centroid.y > -20:
            north.append(g.buffer(0.4))
    north = unary_union(north)
    row = vb.difference(unary_union(allp))
    band = north.buffer(-PAVE_S).difference(north.buffer(-PAVE_N))
    return band.intersection(row.buffer(0.5)).intersection(box(x0 - 1, y0 - 1, x1 + 1, min(y1, 12)))


def _draw_geom(ax, g, min_area=20, **kw):
    for q in ([g] if g.geom_type == "Polygon" else list(getattr(g, "geoms", []))):
        if q.geom_type == "Polygon" and q.area > min_area:
            poly(ax, list(q.exterior.coords), **kw)


NB_TEXT = {"W": "442 BAIRD ST", "E": "441 BAIRD ST", "N": "386 FOREST AVE"}


def site_base(ax, cont="faint", old_house=None, row_tint=True, nb=None, clabels=True, street_label=None, lot_lw=1.3):
    """The common site base: street, existing contours, neighbours, lot outline."""
    x0, y0, x1, y1 = ax.view
    _draw_geom(ax, _pavement(ax.view), fc="#e4e6e9", ec="none", z=1)
    if row_tint:
        rect(ax, max(x0, -6), PAVE_N, min(x1, 56), 0, fc="#fbe9e7", ec="none", z=1.1, alpha=0.75)
    if cont:
        contours(ax, alpha=1.0 if cont == "full" else 0.45, labels=clabels)
    for p in PARCELS:
        if p["id"] != SUBJECT_ID:
            line(ax, p["ring"], color=GREY, lw=0.5, z=3)
    for g in FOOTPRINTS:
        if g is OLD_HOUSE:
            continue
        if g.intersects(box(x0, y0, x1, y1)):
            poly(ax, list(g.exterior.coords), fc="#d9dce0", ec=GREY, lw=0.5, z=3)
    if old_house == "remove":
        poly(ax, list(OLD_HOUSE.exterior.coords), fc="#fff5f4", ec=ACCENT, lw=0.8, z=3.5, hatch="////", ls="--")
    for k, (lx, ly, extra) in (nb or {}).items():
        txt(ax, lx, ly, NB_TEXT[k] + (f"\n{extra}" if extra else ""), size=5.4, color=GREY, z=6, weight="bold" if not extra else "normal")
    poly(ax, LOT, fc="none", ec=ACCENT, lw=lot_lw, z=7, ls=(0, (9, 2.5, 1.5, 2.5)))
    if street_label:
        sx, sy = street_label
        txt(ax, sx, sy, "B A I R D   S T R E E T", size=7.6, weight="bold", color=GREY, z=6)
        txt(ax, sx, sy - 0.4 * ax.fpi * 0.72, "one lane, about 14 ft of pavement in a 30 ft right-of-way · falls 11.4 % to the east",
            size=5.0, color=GREY, z=6)


def lot_dims(ax, off=3.2, size=5.8, front_off=None):
    dim(ax, LOT_SE, LOT_SW, off if front_off is None else front_off, "50.0'  FRONT (RECORD)", color=ACCENT, size=size)
    dim(ax, LOT_NE, LOT_SE, off, "34.0'  EAST", color=ACCENT, size=size)
    dim(ax, LOT_SW, LOT_NW, off, "48.0'  WEST", color=ACCENT, size=size)
    dim(ax, LOT_NW, LOT_NE, off, f"±{math.dist(LOT_NW, LOT_NE):.1f}'  REAR (COMPUTED)", color=ACCENT, size=size)


def title(ax, text, sub, dx=0.6, dy=1.7, size=9, clear=None):
    x0, y0, x1, y1 = ax.view
    k = ax.fpi / FPI
    if clear:
        rect(ax, x0, y1 - clear[1], x0 + clear[0], y1, fc=PAPER, ec="none", z=8)
    txt(ax, x0 + dx * k, y1 - dy * k, text.upper(), size=size, weight="bold", ha="left", va="bottom", z=9)
    txt(ax, x0 + dx * k, y1 - (dy + 0.3) * k, sub, size=size - 3.2, color=GREY, ha="left", va="top", z=9)


def legend(ax, x, y, items, dy=None, size=5.0, w=None):
    """items: (kind, style-dict, label); kind 'line' or 'patch'."""
    dy = 0.2 * ax.fpi if dy is None else dy
    w = 0.42 * ax.fpi if w is None else w
    for i, (kind, st, lab) in enumerate(items):
        yy = y - i * dy
        if kind == "line":
            line(ax, [(x, yy), (x + w, yy)], z=12, **st)
        else:
            rect(ax, x, yy - dy * 0.3, x + w, yy + dy * 0.3, z=12, **st)
        txt(ax, x + w + 0.08 * ax.fpi, yy, lab, size=size, ha="left", z=12)


def bg_legend(bg, x, y, items, dy=0.2, fs=5.6, w=0.42):
    """Legend on the sheet (inches): ('line'|'patch'|'mark', style, label)."""
    for i, (kind, st, lab) in enumerate(items):
        yy = y - i * dy
        if kind == "line":
            bg.plot([x, x + w], [yy, yy], solid_capstyle="butt", **st)
        elif kind == "patch":
            bg.add_patch(Rectangle((x, yy - 0.06), w, 0.12, **st))
        else:
            bg.plot([x + w / 2 - 0.05, x + w / 2 + 0.05], [yy - 0.05, yy + 0.05], lw=0.6, **st)
            bg.plot([x + w / 2 - 0.05, x + w / 2 + 0.05], [yy + 0.05, yy - 0.05], lw=0.6, **st)
        bg.text(x + w + 0.1, yy, lab, fontsize=fs, va="center", color=INK)
    return y - len(items) * dy


def new_building(ax, lw=1.8, fill=PAPER, garage_line=True, z=8):
    poly(ax, m.OUT_U, fc=fill, ec=INK, lw=lw, z=z)
    if garage_line:
        line(ax, [m.OUT_L[3], m.OUT_L[2]], color=GREY, lw=0.6, ls=(0, (4, 2)), z=z + 0.2)


def sheet(number, scale_txt, blocks):
    return new_sheet(number, TITLE[number], scale_txt, notes(blocks))


# ----------------------------------------------------------------------------
# C-101  Existing site and demolition
# ----------------------------------------------------------------------------
def sheet_c101(pdf):
    out_fall = m.EL_DRAIN_OUT - street_el(m.DRAIN_OUT[0])
    fig, bg = sheet("C-101", "1\" = 10'-0\"", [
        ("Existing house: remove", [
            "Built 1929. Two-storey stucco dwelling, 24 x 16 ft plus a 6 x 12 ft porch (assessor record), 768 sf, "
            "2 bedrooms, 1 bath. No basement.",
            "It sits at or very near the front lot line.",
        ]),
        ("Working on this street", [
            "Baird St is one lane, about 14 ft wide, on an 11.4 % grade. Use small trucks, a flagger, "
            "and haul downhill (east). Nothing is stored in the right-of-way. Sweep the street daily.",
        ]),
        ("Basis and accuracy", [
            "Lot lines: county tax map 09-0029 record dimensions placed on the GIS frontage.",
            "Neighbours, buildings, street: public GIS, about ±3 to 5 ft.",
            "Ground: WV 1 m LiDAR, NAVD88 ft.",
            "NOT A BOUNDARY SURVEY.",
        ]),
    ])
    view = (-36, -33, 63, 66)
    ax = frame(fig, view, 10.0, left=0.6)
    site_base(ax, cont="full", old_house="remove", row_tint=False, lot_lw=1.6,
              nb={"W": (-17, 36, "house and lot owned by this owner"), "N": (37, 63.2, "rear neighbour, uphill")},
              street_label=None)
    txt(ax, 57.2, 18, "441 BAIRD ST", size=5.4, color=GREY, weight="bold", rot=90)
    lot_dims(ax, off=3.4)
    for (x, y, dx, dy) in [(0, 0, -1.2, -1.7), (50, 0, 1.2, -1.7), (50, 34, 1.5, 1.2), (LOT_NW[0], LOT_NW[1], -1.5, 1.4)]:
        spot(ax, x, y, dx, dy, size=5.4, color=INK)
    for x in (0, 25, 50):
        spot(ax, x, PAVE_N - 1.5, 0.9, -1.6, color=GREY, val=street_el(x), size=5.0)
    txt(ax, 24, -14.5, "B A I R D   S T R E E T", size=8.5, weight="bold", color=GREY)
    txt(ax, 24, -17.6, "30 ft right-of-way · about 14 ft of pavement · one lane", size=5.6, color=GREY)
    arrow(ax, (6, -24.6), (46, -24.6), color=INK)
    txt(ax, 25, -26.6, f"STREET FALLS 11.4 % TO THE EAST  ({street_el(0) - street_el(50):.1f} ft across the frontage)", size=5.6, box=True)
    # existing house
    hx0, hy0, hx1, hy1 = OLD_HOUSE.bounds
    txt(ax, (hx0 + hx1) / 2, (hy0 + hy1) / 2 + 1.0, "EXISTING HOUSE (1929)", size=6.4, weight="bold", box=True, color=ACCENT)
    txt(ax, (hx0 + hx1) / 2, (hy0 + hy1) / 2 - 1.6, "REMOVE", size=9, weight="bold", box=True, color=ACCENT)
    txt(ax, 21, 36.5, "REAR YARD", size=5.4, color=GREY)
    arrow(ax, (31, 27), (31, 41.5), color=EARTH, ls="--")
    txt(ax, 37.4, 33.6, "lot rises 8 to 12 ft\nfrom street to rear", size=5.0, color=EARTH, box=True)
    # neighbours' clearances
    lead(ax, (west_x(31) - GAP_W / 2, 31), (-13, 25.5), f"house wall about 1 ft from\nthe shared line (GIS {GAP_W:.1f} ft)", ha="center", size=5.0)
    lead(ax, (50 + GAP_E / 2, 21), (58.5, 7.5), f"house wall about 1 ft\nfrom the line\n(GIS {GAP_E:.1f} ft)", ha="center", size=5.0)
    pn = NB_N.exterior.interpolate(NB_N.exterior.project(Point(27, 40)))
    foot = LineString([LOT_NW, LOT_NE]).interpolate(LineString([LOT_NW, LOT_NE]).project(pn))
    dim(ax, (foot.x, foot.y), (pn.x, pn.y), 0, "", ext=False, color=GREY)
    txt(ax, (foot.x + pn.x) / 2 + 5.2, (foot.y + pn.y) / 2 + 2.0, f"house ±{GAP_N:.0f} ft\nfrom the rear line", size=5.0, color=GREY, box=True)
    # keyed notes
    key(ax, 14, 31.5, 1, color=ACCENT, tip=(17, 23.5))
    key(ax, 37.5, 3.2, 2, color=ACCENT, tip=(34, 6.6))
    key(ax, 12, 2.7, 3, color=ACCENT, tip=(12, 0))
    key(ax, 44.5, 2.7, 4, color=ACCENT, tip=(44.5, 0))
    key(ax, -4.5, 14, 5, color=ACCENT, tip=(west_x(14) - 0.6, 14))
    key(ax, 54.5, 28, 6, color=ACCENT, tip=(50.5, 28))
    key(ax, 14, 52, 7, color=ACCENT, tip=(17, 44.2))
    key(ax, 5.5, -5.2, 8, color=ACCENT, tip=(8, -1.0))
    north_arrow(ax, 55, 58.5, 3.6, 7.5)
    scale_bar(ax, -32, -30, 30, 10, 0.9)
    title(ax, "Existing site and demolition plan",
          "Existing contours at 1 ft (5 ft heavy), WV 1 m LiDAR · parcels and buildings from county GIS", dx=1.5, dy=1.9,
          clear=(58, 7.0))
    # right column
    x = 0.6 + 9.9 + 0.22
    w = SHEET_W - MARGIN - TB_W - 0.18 - x
    y = SHEET_H - MARGIN - 0.3
    y = block(bg, x, y, w, "Keyed demolition notes", [
        "1  Remove the house complete. The outline shown is the GIS footprint (about "
        f"{OLD_HOUSE.area:.0f} sf); the survey fixes its true position.",
        "2  Remove all foundations, footings, slabs, steps and walks on the lot to full depth. The new "
        "excavation goes 5 to 14 ft below this ground (C-104): leave nothing buried.",
        "3  Water and sewer: MUB shuts off. Cap both services at the street side of the front lot line. "
        "Service positions are not known: locate them first and record the capped ends for C-106.",
        "4  Electric and telecom: the utility removes the service drop and meter before work starts. "
        "Gas, if found: the gas company cuts and caps at the main. The new building is all-electric.",
        "5  442 Baird St (west): hand demolition within 5 ft of the shared line. No machine swing over the line.",
        "6  441 Baird St (east): same protection as note 5.",
        "7  386 Forest Ave (rear, uphill): leave the rear bank standing. Do not undercut it.",
        "8  Leave the lot graded to drain to the street. Silt fence on the street side and the east side "
        "until excavation starts (C-105).",
    ], fs=5.7, color=INK)
    y = block(bg, x, y - 0.05, w, "Boundary and topographic survey must deliver", [
        "a  All four corners found or set; bearings and distances; the record dimensions checked "
        "(50.0, 34.0 and 48.0 ft; the rear line computes to "
        f"{math.dist(LOT_NW, LOT_NE):.1f} ft).",
        f"b  Lot area. Deed says {LOT_AREA_DEED:,.0f} sf, the record dimensions give {LOT_AREA_CALC:,.0f} sf, "
        "the GIS polygon 1,911 sf. Zoning coverage depends on it.",
        "c  Front line = right-of-way line: R.O.W. width, both pavement edges, centre line.",
        "d  Walls, eaves, steps and footings of 441 and 442 Baird St within 10 ft of the side lines, to 0.1 ft, "
        "and anything that crosses a line. Rear house at 386 Forest Ave.",
        "e  Easements and encroachments of record (deed book 1246, page 78).",
        "f  1 ft contours on NAVD88 and a benchmark on site. Spot levels at lot corners, at the new building "
        "corners (C-102) and every 10 ft along both side lines.",
        f"g  Street profile along the frontage. Pavement edge level at X = {m.DRAIN_OUT[0]:.1f} ft (drain outlet): "
        f"the EL {m.EL_DRAIN_OUT:.1f} gravity outlet has only about {out_fall * 12:.0f} in. of fall there. NO SUMP PUMP is allowed, "
        "so this level decides the garage floor.",
        "h  Sewer main (position, size, invert), water main, existing taps, poles, overhead wires, gas, storm inlets.",
        "i  Walls, steps, fences and trees over 6 in. on or near the lot.",
    ], fs=5.7)
    y = block(bg, x, y - 0.05, w, "Before any demolition", [
        "1  Boundary survey done and the four lot corners staked.",
        "2  Asbestos and lead-paint survey by a licensed inspector (1929 house). Abate what is found first.",
        "3  Demolition permit from the City. Written utility disconnects: MUB water and sewer, power, telecom, gas if any.",
        "4  Call 811 at least two working days ahead.",
        "5  Photo and crack survey of 441 and 442 Baird St, inside and out, signed by both owners.",
        "6  Hold demolition until the variance and the building permit are granted: the old house's "
        "setbacks are lost once it is gone (zoning 1373.06).",
    ], fs=5.7)
    bg_legend(bg, x, y - 0.1, [
        ("line", dict(color=ACCENT, lw=1.4, ls=(0, (9, 2.5, 1.5, 2.5))), "Lot line (record dimensions, not surveyed)"),
        ("patch", dict(fc="#fff5f4", ec=ACCENT, lw=0.7, hatch="////", ls="--"), "Existing house: remove with its foundations"),
        ("patch", dict(fc="#d9dce0", ec=GREY, lw=0.5), "Neighbouring building (GIS)"),
        ("line", dict(color=EARTH, lw=0.8), "Existing contour, 5 ft (1 ft light)"),
        ("mark", dict(color=INK), "Existing spot level (LiDAR, NAVD88 ft)"),
    ])
    save(fig, "C-101", pdf)


def dimb(ax, p0, p1, off, label=None, size=5.4, color=INK, ext=True, side=1, toff=0.085, z=9.5):
    """common.dim with the label on a white box (readable over hatching and contours)."""
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -uy, ux
    dim(ax, p0, p1, off, "", size=size, color=color, ext=ext)
    t = toff * ax.fpi * side
    ang = math.degrees(math.atan2(uy, ux))
    if ang > 90 or ang <= -90:
        ang += 180
    txt(ax, (x0 + x1) / 2 + nx * (off + t), (y0 + y1) / 2 + ny * (off + t), label if label is not None else ftin(L),
        size=size, color=color, rot=ang, box=True, z=z)


def _meet_west(fy):
    """Point where the line y = fy(x) meets the west lot line."""
    y = 30.0
    for _ in range(50):
        y = fy(west_x(y))
    return (west_x(y), y)


# ----------------------------------------------------------------------------
# C-102  Site plan and zoning
# ----------------------------------------------------------------------------
def sheet_c102(pdf):
    env = byright_envelope()
    env_area = poly_area(env)
    cov = 100 * m.FOOTPRINT / LOT_AREA_CALC
    avg = m.avg_grade()
    fig, bg = sheet("C-102", "1/8\" = 1'-0\"", [
        ("Zoning district R-2", [
            "Single and two-family residential, Morgantown Planning and Zoning Code art. 1337. "
            "No overlay district is mapped on the parcel.",
            "Standards were read from the City's 2019 edition: check later amendments.",
        ]),
        ("One variance is requested", [
            "REAR SETBACK 20 ft reduced to 5 ft.",
            f"The R-2 setbacks leave only {env_area:,.0f} sf of this {LOT_AREA_CALC:,.0f} sf lot (hatched), "
            "a wedge 4'-7\" to 16 ft deep. No usable dwelling fits in it.",
            "Every other standard is met as drawn. All wall faces are held 2 in. inside the setback lines.",
        ]),
        ("Confirm with the planner", [
            "1. Front building line: written confirmation that 10 ft governs under the developed-block "
            "rule, 1363.02(C).",
            "2. Lot area and frontage: existing lot of record, buildable under 1373.04.",
            "3. Garage level counted as a basement, not a storey.",
        ]),
        ("Right-of-way", [
            "Nothing is built in the City right-of-way except the driveway apron, the buried drain outlet "
            "and the MUB meter pits. No walls, steps or posts.",
        ]),
    ])
    view = (-8, -24, 58, 53)
    ax = frame(fig, view, 8.0, left=0.6)
    site_base(ax, cont="faint", street_label=(31, -13.2))
    txt(ax, -3.6, 37, "442 BAIRD ST", size=5.2, color=GREY, weight="bold", rot=83.5)
    txt(ax, 55.2, 18, "441 BAIRD ST", size=5.2, color=GREY, weight="bold", rot=90)
    txt(ax, 34, 49.6, "386 FOREST AVE  (house ±18 ft from the rear line)", size=5.2, color=GREY, weight="bold")
    # setback lines
    sb = dict(color=ACCENT, lw=0.55, ls=(0, (4, 3)), z=6)
    line(ax, [(west_x(SB_FRONT), SB_FRONT), (50, SB_FRONT)], **sb)
    line(ax, [(45, 0), (45, rear_y(45))], **sb)
    wtop = _meet_west(lambda x: rear_y(x))
    line(ax, [(west_setback_x(0), 0), (west_setback_x(wtop[1] - 5.6), wtop[1] - 5.6)], **sb)
    a20 = _meet_west(rear_setback_y)
    line(ax, [a20, (50, rear_setback_y(50))], color=ACCENT, lw=0.9, ls=(0, (4, 3)), z=10.5)
    a5 = _meet_west(lambda x: rear_setback_y(x, m.SB_REAR))
    line(ax, [a5, (50, rear_setback_y(50, m.SB_REAR))], color=BLUE, lw=0.7, ls=(0, (4, 3)), z=6)
    # building
    new_building(ax, lw=1.9)
    poly(ax, env, fc="#fbe3e0", ec=ACCENT, lw=0.8, z=8.5, hatch="////", alpha=0.85)
    poly(ax, m.OUT_U, fc="none", ec=INK, lw=1.9, z=10)
    site_work(ax)
    x0, y0, x1, y1 = m.PORCH
    rect(ax, x0, y0, x1, y1, fc="none", ec=BLUE, lw=0.8, ls="--", z=9)
    txt(ax, 26.2, 31.9, "PROPOSED TWO-FAMILY DWELLING", size=7.0, weight="bold", z=12)
    txt(ax, 26.2, 28.4, f"{m.FOOTPRINT:,.0f} sf footprint · two flats over an open 3-car garage", size=5.2, z=12)
    txt(ax, 26.2, 26.9, f"Garage EL {m.EL_GAR:.1f} · Unit A EL {m.EL_A:.1f} · Unit B EL {m.EL_B:.1f}", size=5.2, z=12)
    txt(ax, 26.2, 25.4, "3 parking stalls in the garage (C-103)", size=5.2, z=12)
    txt(ax, 19.5, 30.75, "garage rear wall below", size=4.3, color=GREY, z=12, ha="center", box=True)
    txt(ax, 22.0, 15.2, f"BY-RIGHT BUILDABLE AREA  {env_area:,.0f} SF", size=5.6, color=ACCENT, weight="bold", z=12, box=True)
    txt(ax, 22.0, 13.6, "front 10 ft, sides 5 ft, rear 20 ft", size=4.8, color=ACCENT, z=12, box=True)
    t20 = (31.5, rear_setback_y(31.5) + 0.9)
    txt(ax, *t20, "20 FT REAR SETBACK LINE (CODE)", size=4.8, color=ACCENT, weight="bold", rot=m.REAR_ANGLE, z=12, box=True)
    t5 = (19.0, rear_setback_y(19.0, m.SB_REAR) + 1.0)
    txt(ax, *t5, "5 FT REAR LINE REQUESTED (VARIANCE)", size=4.6, color=BLUE, weight="bold", rot=m.REAR_ANGLE, z=12, box=True)
    txt(ax, 52.2, 11.4, "10 FT FRONT\nSETBACK", size=4.4, color=ACCENT, ha="left", box=True)
    txt(ax, 45.0, -1.1, "5 FT SIDE", size=4.2, color=ACCENT, box=True)
    # setbacks, dimensioned square to each lot line
    dimb(ax, (9.3, 0), (9.3, m.YF), 0, ftin(m.YF), color=BLUE, ext=False)
    dimb(ax, (m.XE, 23.5), (50, 23.5), 0, ftin(YARD), color=BLUE, ext=False)
    pw = (m.xw_o(27.5), 27.5)
    dimb(ax, (pw[0] + N_W[0] * YARD, pw[1] + N_W[1] * YARD), pw, 0, ftin(YARD), color=BLUE, ext=False)
    pr = (33.5, m.yr_o(33.5))
    dimb(ax, pr, (pr[0] + N_R[0] * YARD, pr[1] + N_R[1] * YARD), 0, ftin(YARD), color=BLUE, ext=False, side=-1)
    q = (40.5, rear_y(40.5))
    dimb(ax, (q[0] - N_R[0] * SB_REAR, q[1] - N_R[1] * SB_REAR), q, 0, "20'-0\" CODE", color=ACCENT, ext=False, side=-1, size=4.8)
    # building sides
    dimb(ax, m.OUT_U[0], m.OUT_U[1], 1.5, None, ext=False)
    dimb(ax, m.OUT_U[1], m.OUT_U[2], 1.5, None, ext=False)
    dimb(ax, m.OUT_U[2], m.OUT_U[3], 1.5, None, ext=False)
    dimb(ax, m.OUT_U[3], m.OUT_U[0], 1.5, None, ext=False)
    dimb(ax, (m.OPEN[0] + 1.5, 0), (m.OPEN[1] - 1.5, 0), -2.3, f"{ftin(m.APRON_W_ROW)} DRIVEWAY AT THE R.O.W. LINE", color=BLUE, side=-1, size=5.0)
    dimb(ax, (m.OPEN[0], m.YF - 4.0), (m.OPEN[1], m.YF - 4.0), -1.3, f"{ftin(m.OPEN_W)} GARAGE OPENING", color=BLUE, side=-1, size=4.8, ext=False)
    dimb(ax, (29.0, m.YF), (29.0, m.YF - 4.0), 0, "4'-0\"", color=BLUE, ext=False, size=4.6)
    lot_dims(ax, off=2.6, size=5.4, front_off=9.6)
    for (x, y), (dx, dy) in zip(m.OUT_U, [(-0.9, -1.3), (0.9, -1.2), (1.1, 1.1), (-0.8, 1.6)]):
        spot(ax, x, y, dx, dy, size=4.8)
    # keys
    key(ax, 24.0, 7.9, 1)
    key(ax, 24.0, 2.6, 2)
    key(ax, 40.4, 7.0, 3)
    key(ax, 41.5, -3.4, 4, tip=(41.5, 1.6))
    key(ax, -1.5, 24.0, 5, tip=(m.HP[0][0] - 0.3, m.HP[0][1] + 2.0))
    key(ax, 7.8, 4.6, 6, tip=(12.6, 4.6))
    key(ax, 53.6, 5.6, 7, tip=(45.3, 5.6))
    key(ax, 53.0, -3.4, 8, tip=(47.5, -1.7))
    key(ax, 28.0, 46.2, 9, tip=(27.6, rear_y(27.6)))
    for (wx, wy) in m.WATER_METERS:
        ax.add_patch(Circle((wx, wy), PIT_R, fc=PAPER, ec=WATER, lw=0.6, zorder=6))
    north_arrow(ax, 52.5, 46.5, 2.9, 7)
    scale_bar(ax, -6, -22, 20, 5, 0.65)
    title(ax, "Site plan and zoning", "Brown x = existing ground (LiDAR) at the building corners · contours 1 ft, existing",
          dx=0.5, dy=1.4, clear=(33, 4.6))
    # ---- right column
    x = 0.6 + 8.25 + 0.3
    w = SHEET_W - MARGIN - TB_W - 0.18 - x
    y = SHEET_H - MARGIN - 0.3
    bg.text(x, y, "ZONING TABLE: R-2 STANDARD AGAINST WHAT IS PROVIDED", fontsize=7.0, fontweight="bold", va="top")
    rows = [
        ("Item", "R-2 standard", "Provided", "Result"),
        ("Use", "1 or 2-family dwelling", "Two-family: 2 stacked flats", "OK"),
        ("Lot area", "5,000 sf min.", f"{LOT_AREA_CALC:,.0f} sf, lot of record", "Existing"),
        ("Frontage", "40 ft min.", "50.0 ft", "OK"),
        ("Front setback", "10 ft min.", ftin(m.YF), "OK (a)"),
        ("Side setback, east", "5 ft min.", ftin(YARD), "OK"),
        ("Side setback, west", "5 ft min.", ftin(YARD), "OK"),
        ("Rear setback", "20 ft min.", ftin(YARD), "VARIANCE"),
        ("Lot coverage", "50 % max.", f"{cov:.1f} %  ({m.FOOTPRINT:,.0f} of {LOT_AREA_CALC:,.0f} sf)", "OK"),
        ("Height", "35 ft max.", f"{BLDG_H:.1f} ft to mid-roof", "OK (b)"),
        ("Storeys", "2.5 max.", "2 over a basement garage", "OK (c)"),
        ("Parking", "1.5 per unit = 3", "3 in the open garage", "OK"),
        ("Garage width", "65 % of the front max.", f"{ftin(m.OPEN_W)} of {ftin(m.FACADE_W)} = {m.GARAGE_PCT:.1f} %", "OK"),
        ("Front porch width", "50 % of the front min.", f"{ftin(PORCH_W)} = {100 * PORCH_W / m.FACADE_W:.0f} %", "OK"),
        ("Porch into front setback", "5 ft max.", ftin(m.PORCH[3] - m.PORCH[1]), "OK"),
        ("Driveway at the R.O.W. line", "22 ft max.", ftin(m.APRON_W_ROW), "OK"),
        ("Heat pump to side line", "2 ft min., 1337.05(D)", ftin(HP_CLEAR), "OK"),
    ]
    y = ztable(bg, x, y - 0.2, [1.32, 1.12, 1.52, 0.56], rows, fs=5.5, rh=0.192, flag=(7,))
    y = block(bg, x, y - 0.14, w, None, [
        "(a) FRONT BUILDING LINE. The 10 ft line is used. The developed-block rule, 1363.02(C), can set the line "
        "from the neighbouring houses instead: get the planner's written confirmation before the engineers start.",
        f"(b) HEIGHT. Average existing ground at the four building corners EL {avg:.1f}. Eave (truss heel at the wall) "
        f"EL {m.EL_PLATE + m.HEEL:.1f}, highest ridge EL {m.EL_RIDGE_HI:.1f}, mid-roof EL {MEAN_ROOF:.1f}: "
        f"{BLDG_H:.1f} ft. The ridge itself is {m.EL_RIDGE_HI - avg:.1f} ft above average ground.",
        f"(c) STOREYS. The Unit A floor is {m.EL_A - avg:.1f} ft above average ground (6 ft test) and "
        f"{m.EL_A - m.EL_GAR:.1f} ft above the apron (12 ft test), so the garage level is a basement by the building-code "
        "tests. The zoning officer rules on the zoning definition.",
        f"LOT AREA. {LOT_AREA_CALC:,.0f} sf is from the record dimensions; the deed says {LOT_AREA_DEED:,.0f} sf "
        f"(coverage {100 * m.FOOTPRINT / LOT_AREA_DEED:.1f} %). The survey settles it.",
    ], fs=5.6, hang="")
    bg.add_patch(Rectangle((x, y - 0.56), w, 0.6, fc="#fbe3e0", ec=ACCENT, lw=1.0))
    bg.text(x + 0.1, y - 0.12, "VARIANCE REQUESTED: REAR SETBACK 5 FT (20 FT REQUIRED)", fontsize=6.6, fontweight="bold", color=ACCENT, va="center")
    bg.text(x + 0.1, y - 0.37, f"The rear wall runs parallel to the rear lot line, {ftin(YARD)} from it along its whole\n"
            f"{ftin(m.REAR_WALL_LEN)} length. See G-003 for the request.", fontsize=5.6, color=ACCENT, va="center", linespacing=1.25)
    y = block(bg, x, y - 0.8, w, "Keyed site work (all on the lot unless noted)", [
        "1  Porches of Units A and B over, cantilevered 4'-0\". No posts.",
        "2  Driveway apron: on the lot and across the right-of-way to the pavement (C-103, C-107).",
        "3  Entry landing, level with the garage floor.",
        "4  Screened trash bay for 4 carts (C-107).",
        "5  Two heat-pump pads (M-101).",
        "6  West wing wall: retains the front yard beside the apron (C-107).",
        "7  Low wall round the landing and trash bay (C-107).",
        "8  MUB water meter pits, in the right-of-way (C-106).",
        "9  6 ft privacy fence on the rear lot line (C-107).",
    ], fs=5.6, gap=0.012)
    bg_legend(bg, x, y - 0.06, [
        ("line", dict(color=ACCENT, lw=1.3, ls=(0, (9, 2.5, 1.5, 2.5))), "Lot line (record dimensions)"),
        ("line", dict(color=ACCENT, lw=0.7, ls=(0, (4, 3))), "R-2 setback lines: front 10, sides 5, rear 20 ft"),
        ("patch", dict(fc="#fbe3e0", ec=ACCENT, lw=0.7, hatch="////"), "Area the R-2 setbacks leave to build on"),
        ("line", dict(color=INK, lw=1.8), "Proposed building, outside face of walls"),
        ("line", dict(color=BLUE, lw=0.8, ls="--"), "Porches over · 5 ft rear line requested"),
    ], dy=0.185)
    save(fig, "C-102", pdf)


# ----------------------------------------------------------------------------
# C-103  Vehicle access and towing
# ----------------------------------------------------------------------------
TRUCK_W, TRUCK_L = 8.0, 22.0
AMBER, GREEN = "#b9770e", "#1c6b3a"


def truck(ax, x, y, ang, color=AMBER, label=None, fc="#fbeed5", cab="#f3d9a4"):
    """8 x 22 ft tow truck: REAR (winch end) centred at (x, y), body running in direction ang (deg)."""
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    px, py = -uy, ux

    def P(d, o):
        return (x + ux * d + px * o, y + uy * d + py * o)
    W, L = TRUCK_W, TRUCK_L
    poly(ax, [P(0, -W / 2), P(L, -W / 2), P(L, W / 2), P(0, W / 2)], fc=fc, ec=color, lw=1.1, z=12, alpha=0.9)
    poly(ax, [P(L - 6, -W / 2), P(L, -W / 2), P(L, W / 2), P(L - 6, W / 2)], fc=cab, ec=color, lw=0.7, z=12.5)
    if label:
        txt(ax, *P(L * 0.38, 0), label, size=5.0, weight="bold", color=color, z=14, rot=ang if abs(ang) < 90 else (ang + 180) % 360 - 0)


def sheet_c103(pdf):
    car_c = [c + m.CAR_W / 2 for c in m.CARS]
    post_w, post_e = m.COL_X[1] - 0.25, m.COL_X[1] + 0.25
    neck_w, neck_e = m.WING_W[1][0], m.OPEN[1] - 1.5
    xa1 = neck_w + 1.0 + TRUCK_W / 2                    # truck for stall 1: 1 ft clear of the wing wall end
    xa3 = neck_e - 0.5 - TRUCK_W / 2                    # truck for stall 3: 6 in. inside the apron edge
    ya = 4.0                                            # rear of the truck on the apron
    ang1 = math.degrees(math.atan2(abs(xa1 - car_c[0]), m.CAR_Y0 - ya))
    ang3 = math.degrees(math.atan2(abs(xa3 - car_c[2]), m.CAR_Y0 - ya))
    clip1 = neck_w - m.CARS[0]
    clip3 = (m.CARS[2] + m.CAR_W) - neck_e
    fig, bg = sheet("C-103", "1/8\" = 1'-0\"", [
        ("How the garage is used", [
            "Three stalls side by side, each one move from the street. No tandem parking, no doors, "
            "no kerbs or wheel stops.",
            f"Opening {ftin(m.OPEN_W)} wide, {ftin(m.OPEN_CLEAR_H)} clear under the steel beam; "
            f"{ftin(m.CLG_GAR)} clear inside.",
            "One steel post, on the line between stalls 2 and 3. No wall or column stands in front of any stall.",
            f"Cars back out across the {ftin(APRON_LEN)} apron into the lane: {ftin(m.YF - PAVE_S)} from the opening "
            "to the far pavement edge.",
        ]),
        ("Towing a car out", [
            "A flatbed or wheel-lift truck, about 8 x 22 ft, backs up the apron (position A) or stands in the "
            "street (position B) and winches the car straight out of its stall.",
            f"The truck is longer than the apron: in position A its nose stands in the lane, so the street is "
            "blocked for the few minutes of the pull. Cones or a flagger; leave downhill (east).",
            "The street is steep: chock the truck.",
        ]),
        ("Right-of-way", [
            "Nothing is built in the right-of-way except the apron. No walls, posts, steps or parking there. "
            "The banks beside the apron are graded 2:1.",
        ]),
    ])
    view = (-8, -27, 59, 44)
    ax = frame(fig, view, 8.0, left=0.6)
    site_base(ax, cont="faint", clabels=False, street_label=None)
    txt(ax, -3.4, 30, "442 BAIRD ST", size=5.0, color=GREY, weight="bold", rot=83.5)
    txt(ax, 55.4, 22, "441 BAIRD ST", size=5.0, color=GREY, weight="bold", rot=90)
    poly(ax, m.OUT_U, fc="#f4f5f6", ec=GREY, lw=0.6, ls=(0, (4, 2)), z=2.5)
    txt(ax, 21, 34.2, "Unit A floor over: slab on grade, not excavated", size=4.4, color=GREY, rot=m.REAR_ANGLE, z=6)
    site_work(ax)
    lower_plan(ax, "arch", cars=True, labels=False)
    for i, c in enumerate(car_c):
        txt(ax, c, m.CAR_Y0 + 9.2, f"{i + 1}", size=11, weight="bold", color=YELLOW, z=7)
    x0, y0, x1, y1 = m.PORCH
    rect(ax, x0, y0, x1, y1, fc="none", ec=GREY, lw=0.6, ls=(0, (3, 2)), z=9)
    # trucks
    truck(ax, xa1, ya, 270, label="A  TRUCK FOR STALL 1")
    truck(ax, xa3, ya, 270, label="A  TRUCK FOR STALL 3")
    truck(ax, 38.5, -14.0, 0, color=GREEN, fc="#e3f1e7", cab="#bfdcc8", label="B  TRUCK IN THE STREET")
    arrow(ax, (52.0, -20.3), (58.0, -20.3), color=GREEN, lw=1.0)
    txt(ax, 51.4, -20.3, "leave downhill (east)", size=4.8, color=GREEN, ha="right", box=True)
    for xt, cc in ((xa1, car_c[0]), (xa3, car_c[2])):
        line(ax, [(xt, ya), (cc, m.CAR_Y0)], color=AMBER, lw=0.9, ls=(0, (5, 2, 1, 2)), z=13)
    line(ax, [(38.5, -14.0), (car_c[1], -1.0), (car_c[1], m.CAR_Y0)], color=GREEN, lw=0.9, ls=(0, (5, 2, 1, 2)), z=13)
    lead(ax, ((xa1 + car_c[0]) / 2, (ya + m.CAR_Y0) / 2), (1.5, 15.5), f"winch line\n{ang1:.0f}° off the\nstall axis", size=4.6, color=AMBER, ha="center")
    # dimensions
    dimb(ax, (m.OPEN[0], m.YF + 21.6), (m.OPEN[1], m.YF + 21.6), 0, f"{ftin(m.OPEN_W)} OPENING, NO DOORS", ext=False, color=BLUE, size=5.0)
    dimb(ax, (m.OPEN[0], 33.6), (post_w, 33.6), 0, f"{ftin(post_w - m.OPEN[0])} CLEAR", ext=False, size=4.6)
    dimb(ax, (post_e, 33.6), (m.OPEN[1], 33.6), 0, f"{ftin(m.OPEN[1] - post_e)} CLEAR", ext=False, size=4.6)
    for xx in (m.OPEN[0], post_w, post_e, m.OPEN[1]):
        line(ax, [(xx, 30.6), (xx, 34.4)], color=GREY, lw=0.3, z=8)
    dimb(ax, (neck_w - (m.WING_W[1][0] - (m.OPEN[0] + 1.5)), 0), (neck_e, 0), -24.6, f"{ftin(m.APRON_W_ROW)} AT THE R.O.W. LINE", color=BLUE, side=-1, size=5.0)
    dimb(ax, (m.OPEN[0] - 0.5, PAVE_N), (m.OPEN[1] + 0.5, PAVE_N), -16.2, f"{ftin(m.OPEN_W + 1.0)} AT THE PAVEMENT", color=BLUE, side=-1, size=5.0)
    xd = 44.6
    dimb(ax, (xd, 0), (xd, m.YF), 0, ftin(m.YF), ext=False, size=4.6, side=-1)
    dimb(ax, (xd, PAVE_N), (xd, 0), 0, ftin(-PAVE_N), ext=False, size=4.6, side=-1)
    dimb(ax, (xd, PAVE_S), (xd, PAVE_N), 0, f"±{ftin(PAVE_N - PAVE_S)} LANE", ext=False, size=4.6, side=-1)
    for yy in (m.YF, 0, PAVE_N, PAVE_S):
        line(ax, [(xd - 6.5, yy), (xd + 1.0, yy)], color=GREY, lw=0.3, z=8)
    # apron levels and slopes
    for (name, xo, xp, zs, sl) in APRON_SLOPE:
        spot(ax, xp, PAVE_N, 0.5 if name != "East edge" else -0.5, -1.2, color=BLUE, val=zs, size=4.6, z=14)
    spot(ax, 24.3, m.YF - 0.05, 0.6, 1.0, color=BLUE, val=m.EL_GAR, size=4.6, pre="EL ", z=14)
    key(ax, 5.0, 6.3, 1, tip=(m.WING_W[1][0] - 0.3, 2.5))
    key(ax, 5.0, 11.2, 2, tip=(m.OPEN[0] - 0.4, m.YF + 0.5))
    key(ax, m.COL_X[1], 6.4, 3, tip=(m.COL_X[1], m.YF + 0.1))
    key(ax, 49.5, 12.5, 4, tip=(41.0, m.YF + 0.3))
    key(ax, 49.5, 2.0, 5, tip=(41.4, 1.9))
    key(ax, 3.2, -3.6, 6, tip=(9.6, -3.6))
    key(ax, 24.3, m.YF - 0.6 + 1.9, 7, tip=(22.6, m.YF - 0.6))
    txt(ax, 14, -23.4, "B A I R D   S T R E E T", size=7.6, weight="bold", color=GREY, z=6, box=True)
    txt(ax, 14, -25.3, "one lane · falls 11.4 % to the east", size=5.0, color=GREY, z=6, box=True)
    north_arrow(ax, 53.5, 38.5, 2.9, 7)
    scale_bar(ax, 36, -25.2, 20, 5, 0.65)
    title(ax, "Garage level: vehicle access and towing plan", "Amber = truck on the apron (position A) · green = truck in the street (position B)",
          dx=0.5, dy=1.4, clear=(42, 4.4))

    # ---- right column: apron profiles
    xr = 0.6 + (view[2] - view[0]) / 8.0 + 0.28
    wr = SHEET_W - MARGIN - TB_W - 0.15 - xr
    ytop = SHEET_H - MARGIN - 0.3
    bg.text(xr, ytop, "APRON PROFILES: STREET TO GARAGE", fontsize=7.0, fontweight="bold", va="top")
    bg.text(xr, ytop - 0.17, "1/8\" = 1'-0\", no vertical exaggeration. Looking west. Dashed brown = existing ground.", fontsize=4.9, color=GREY, va="top")
    pv = (PAVE_S - 0.6, 910.6, 12.6, 926.4)
    ph = (pv[3] - pv[1]) / 8.0
    yb = ytop - 0.42
    for k, (name, xo, xp, zs, sl) in enumerate(APRON_SLOPE):
        yb -= ph + 0.1
        px = plan_axes(fig, xr, yb, (pv[0], pv[2]), (pv[1], pv[3]), 8.0)
        ys = np.linspace(pv[0], pv[2], 80)
        xs = [xp if y <= PAVE_N else (xo if y >= m.YF else xp + (xo - xp) * (y - PAVE_N) / APRON_LEN) for y in ys]
        line(px, list(zip(ys, [elev(x, y) for x, y in zip(xs, ys)])), color=EARTH, lw=0.6, ls=(0, (4, 2)), z=3)
        rect(px, PAVE_S, zs - 0.5, PAVE_N, zs, fc="#c9cdd2", ec=GREY, lw=0.4, z=4)
        poly(px, [(PAVE_N, zs), (m.YF, m.EL_GAR), (m.YF, m.EL_GAR - 0.5), (PAVE_N, zs - 0.5)], fc="#d5dbe2", ec=BLUE, lw=0.7, z=5)
        rect(px, m.YF, m.EL_GAR - 0.5, pv[2], m.EL_GAR, fc=CONC, ec=INK, lw=0.5, z=5)
        rect(px, m.B1_Y - 0.28, m.EL_B1_TOP - m.B1_DEPTH, m.B1_Y + 0.28, m.EL_B1_TOP, fc=BLUE, ec=INK, lw=0.4, z=6)
        rect(px, m.YF - 4.0, m.EL_B1_TOP, pv[2], m.EL_A, fc="#f4f1ea", ec=GREY, lw=0.4, z=4)
        line(px, [(0, pv[1] + 0.3), (0, pv[3] - 0.2)], color=ACCENT, lw=0.7, ls=(0, (9, 2.5, 1.5, 2.5)), z=7)
        txt(px, 0.3, pv[3] - 0.9, "LOT LINE", size=4.2, color=ACCENT, ha="left")
        txt(px, (PAVE_S + PAVE_N) / 2, zs - 1.3, f"street EL {zs:.1f}", size=4.6, color=GREY)
        txt(px, m.YF + 1.3, m.EL_GAR - 1.3, f"EL {m.EL_GAR:.1f}", size=4.6)
        way = "UP to the street" if sl > 0 else "down to the street"
        txt(px, (PAVE_N + m.YF) / 2, (zs + m.EL_GAR) / 2 + 1.5, f"{abs(sl):.1f} % {way}", size=5.2, color=BLUE, weight="bold", box=True)
        dimb(px, (m.YF + 1.6, m.EL_GAR), (m.YF + 1.6, m.EL_B1_TOP - m.B1_DEPTH), 0, ftin(m.OPEN_CLEAR_H), ext=False, size=4.6, side=-1)
        txt(px, m.YF - 2.0, m.EL_A - 0.85, "porch over", size=4.2, color=GREY)
        txt(px, pv[0] + 0.2, pv[3] - 0.9, f"{name.upper()}  (X = {xo:.1f} ft at the opening)", size=5.4, weight="bold", ha="left")
    rows = [("Apron line", "Street EL", "Garage EL", "Rise (+) / fall (-)", "Slope")]
    for (name, xo, xp, zs, sl) in APRON_SLOPE:
        rows.append((name, f"{zs:.1f}", f"{m.EL_GAR:.1f}", f"{zs - m.EL_GAR:+.2f} ft in {ftin(APRON_LEN)}", f"{sl:+.1f} %"))
    y = ztable(bg, xr, yb - 0.15, [0.85, 0.7, 0.75, 1.3, 0.6], rows, fs=5.5, rh=0.19)
    y = block(bg, xr, y - 0.1, wr, None, [
        f"The street falls 11.4 % along the frontage, so the apron is a warped surface. At the west edge the street is "
        f"{APRON_SLOPE[0][3] - m.EL_GAR:.1f} ft ABOVE the garage floor and that side of the apron drains TOWARD the building: "
        "the trench drain across the opening (key 7) must take it. See C-105.",
        "Street levels are from LiDAR. The survey and the City driveway permit fix the final apron grades.",
    ], fs=5.5, hang="")
    y = block(bg, xr, y, wr, "Keyed notes", [
        f"1  West wing wall. The apron necks from {ftin(m.OPEN_W)} at the opening to {ftin(m.APRON_W_ROW)} at the lot line "
        f"(zoning limit), so the straight path of stall 1 is cut by {clip1 * 12:.0f} in. at the wall end: steer toward the middle.",
        "2  Concrete return pier, west end of the opening.",
        "3  Steel post HSS 6x6 (prelim.) on the line between stalls 2 and 3.",
        "4  Street door to the common stair. 5  Trash bay.",
        "6  Bank in the right-of-way graded 2:1. No wall.",
        "7  Trench drain across the opening, grate flush.",
        f"A  Truck on the apron, tail 1 ft clear of the walls. Stall 2: square to the stall. Stalls 1 and 3: the truck sits "
        f"{ftin(abs(xa1 - car_c[0]))} and {ftin(abs(xa3 - car_c[2]))} off the stall axis; the winch line starts {ang1:.0f}° and {ang3:.0f}° off "
        "and straightens as the car comes out.",
        "B  Truck in the street, pointing downhill. The car is winched straight out onto the apron, then hooked up.",
    ], fs=5.5, gap=0.012)
    save(fig, "C-103", pdf)


SHEETS = [
    ("C-101", sheet_c101),
    ("C-102", sheet_c102),
    ("C-103", sheet_c103),
]
