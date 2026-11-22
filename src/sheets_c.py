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
FTG_IN = 1.0                                # footing toe toward the garage (as S-101)
FTG_OUT = m.FTG_W - m.CONC - FTG_IN         # footing heel outside the wall face, toward the soil: 2'-0" (as S-101)
WORK = 2.0                                  # working space outside the footing heel
EXC_OFF = FTG_OUT + WORK                    # face of the excavation: 4'-0" outside the wall face
EL_EXC = m.EL_FTG_TOP - m.FTG_T             # bottom of footing = bottom of the excavation at the walls
EL_SUBGR = m.EL_GAR - 1.0                   # bottom of the 6 in. stone under the garage slab
Y_EXC_S = m.YF - 1.5                        # south edge of the deep dig (front footing edge, as S-101)
Y_EXC_N = m.Y_GR_O + EXC_OFF


def xw_exc(y):
    return m.xw_o(y) - EXC_OFF / _CW


EXC = [(xw_exc(Y_EXC_S), Y_EXC_S), (m.XE + EXC_OFF, Y_EXC_S), (m.XE + EXC_OFF, Y_EXC_N), (xw_exc(Y_EXC_N), Y_EXC_N)]
_IN = FTG_IN + m.CONC                       # inside edge of the footing, from the outside wall face
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
FD_OFF = 0.75                               # French drain centre line: 9 in. outside the wall face, on the footing heel (as S-102)
_fdw = lambda y: m.xw_o(y) - FD_OFF / _CW   # noqa: E731
FD = [(_fdw(m.YF), m.YF), (_fdw(m.Y_GR_O + FD_OFF), m.Y_GR_O + FD_OFF), (m.XE + FD_OFF, m.Y_GR_O + FD_OFF), (m.XE + FD_OFF, m.YF)]
TD_Y = m.YF - 0.6                           # trench drain line (brief)
J1 = (46.83, m.YF - 2.6)                    # junction cleanout: trench drain and storm line join the solid outlet pipe
PIT_R = 0.75                                # 18 in. meter pit
TAIL = [FD[3], J1, (J1[0], 2.2), (m.WATER_METERS[0][0] - PIT_R - 0.5, 0.3),
        (m.WATER_METERS[0][0] - PIT_R - 0.5, m.WATER_METERS[0][1] - 1.9), m.DRAIN_OUT]     # solid pipe, jogs round the meter pit


def _cum(pts):
    out = [0.0]
    for a, b in zip(pts, pts[1:]):
        out.append(out[-1] + math.dist(a, b))
    return out


FD_RUN = FD + [J1]
FD_STA = _cum(FD + [m.DRAIN_OUT])           # stationing as S-102: corners, then straight to the outlet
FD_LEN = FD_STA[-1]
FD_SLOPE = (m.EL_DRAIN_HI - m.EL_DRAIN_OUT) / FD_LEN


def fd_inv(i):
    """Invert at cleanout i (0 to 3 = CO-1 to CO-4, 4 = junction J-1)."""
    if i == 4:
        return m.EL_DRAIN_HI - FD_SLOPE * (FD_STA[3] + math.dist(FD[3], J1))
    return m.EL_DRAIN_HI - FD_SLOPE * FD_STA[i]


EL_TD = m.EL_GAR - (m.Y_GR_I - (m.YF - 0.6)) / 8 / 12     # slab at the trench drain: 1/8 in./ft down from the rear wall (as S-103)


EL_TD_OUT = EL_TD - 1.0                     # trench drain outlet invert: 12 in. below the grate (assumed channel depth)
X_S1 = 46.65                                # storm line S1 down the east side yard (solid)
UD_OFF = 1.0                                # upper drain behind the rear stem wall
UD_DEPTH = 3.0                              # its invert below finish grade (at the stem footing)
S1 = [rear_pt(m.REAR_WALL_LEN + 1.0, UD_OFF), (X_S1, rear_pt(m.REAR_WALL_LEN + 1.0, UD_OFF)[1] - 1.0), (X_S1, J1[1] + 1.6), J1]
# downspouts: assumed at the four roof corners until A-105 fixes them
DS = {"NW": (m.OUT_U[3][0] + 0.6, m.OUT_U[3][1] - 0.2), "NE": (m.XE, m.yr_o(m.XE) - 0.1), "SW": (m.xw_o(m.YF), m.YF), "SE": (m.XE, m.YF)}
RL_OFF = 3.4                                # west roof leader: from the west wall face
RL_W = [(m.xw_o(40.0) - RL_OFF / _CW, 40.0), (m.xw_o(m.YF) - RL_OFF / _CW, m.YF), (4.2, 1.0), (7.5, PAVE_N + 0.6)]

# ---- water service route (two 1 in. lines, 8 in. apart) ----
X_WA, X_WB = 47.4, m.WATER_METERS[1][0]
WATER_A = [m.WATER_METERS[0], (m.WATER_METERS[0][0], m.WATER_METERS[0][1] + PIT_R), (X_WA, 0.6), (X_WA, m.WATER_ENTRY[1]), m.WATER_ENTRY]
WATER_B = [m.WATER_METERS[1], (m.WATER_METERS[1][0], m.WATER_METERS[1][1] + PIT_R), (X_WB, 0.6), (X_WB, m.WATER_ENTRY[1] + 0.67), (m.XE, m.WATER_ENTRY[1] + 0.67)]
X_ET, X_TEL = 46.25, 45.9                                  # electric and telecom conduits

# ---- trash bay: what four carts need (catalogue 96 gal cart, 26 x 34 in.) ----
CART_W, CART_D = 26 / 12.0, 34 / 12.0
BAY_NEED = (4 * CART_W + 2 / 12.0, CART_D + 4 / 12.0)              # carts side by side with 2 in. slack, 4 in. to the gate
BAY_OK = (m.TRASH[2] - m.TRASH[0]) >= BAY_NEED[0] - 0.01 and (m.TRASH[3] - m.TRASH[1]) >= BAY_NEED[1] - 0.01
BAY = m.TRASH if BAY_OK else (m.TRASH[2] - BAY_NEED[0], m.TRASH[1], m.TRASH[2], m.TRASH[1] + BAY_NEED[1])

FENCE_H = 6.0
MEAN_ROOF = ((m.EL_PLATE + m.HEEL) + m.EL_RIDGE_HI) / 2             # mid-height of the roof, highest ridge
BLDG_H = m.zoning_height()
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
        f"excavation goes {elev(*EXC[1]) - EL_EXC:.0f} to {elev(*EXC[3]) - EL_EXC:.0f} ft below this ground (C-104): leave nothing buried.",
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
    txt(ax, 36, 50.6, "386 FOREST AVE  (house ±18 ft from the rear line)", size=5.2, color=GREY, weight="bold", box=True)
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
    txt(ax, 22.0, 17.4, f"BY-RIGHT BUILDABLE AREA  {env_area:,.0f} SF", size=5.6, color=ACCENT, weight="bold", z=12, box=True)
    txt(ax, 22.0, 15.8, "front 10 ft, sides 5 ft, rear 20 ft", size=4.8, color=ACCENT, z=12, box=True)
    t20 = (31.5, rear_setback_y(31.5) + 0.9)
    txt(ax, *t20, "20 FT REAR SETBACK LINE (CODE)", size=4.8, color=ACCENT, weight="bold", rot=m.REAR_ANGLE, z=12, box=True)
    t5 = (19.0, rear_setback_y(19.0, m.SB_REAR) + 1.0)
    txt(ax, *t5, "5 FT REAR LINE REQUESTED (VARIANCE)", size=4.6, color=BLUE, weight="bold", rot=m.REAR_ANGLE, z=12, box=True)
    txt(ax, 52.2, 11.4, "10 FT FRONT\nSETBACK", size=4.4, color=ACCENT, ha="left", box=True)
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
    key(ax, -4.6, 16.5, 5, tip=(m.HP[0][0] - 0.2, m.HP[0][1] - 0.6))
    key(ax, 9.3, -3.6, 6, tip=(13.0, 1.6))
    key(ax, 53.6, 5.6, 7, tip=(45.3, 5.6))
    key(ax, 53.0, -3.4, 8, tip=(47.5, -1.7))
    key(ax, 28.0, 46.2, 9, tip=(27.6, rear_y(27.6)))
    for (wx, wy) in m.WATER_METERS:
        ax.add_patch(Circle((wx, wy), PIT_R, fc=PAPER, ec=WATER, lw=0.6, zorder=6))
    north_arrow(ax, 52.5, -16.0, 2.9, 7)
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
            "9'-2\" clear inside.",
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
    view = (-8, -27, 59, 41)
    ax = frame(fig, view, 8.0, left=0.6)
    site_base(ax, cont="faint", clabels=False, street_label=None)
    txt(ax, -3.4, 30, "442 BAIRD ST", size=5.0, color=GREY, weight="bold", rot=83.5)
    txt(ax, 55.4, 22, "441 BAIRD ST", size=5.0, color=GREY, weight="bold", rot=90)
    poly(ax, m.OUT_U, fc="#f4f5f6", ec=GREY, lw=0.6, ls=(0, (4, 2)), z=2.5)
    site_work(ax)
    lower_plan(ax, "arch", cars=True, labels=False)
    for i, c in enumerate(car_c):
        txt(ax, c, m.CAR_Y0 + 9.2, f"{i + 1}", size=11, weight="bold", color=YELLOW, z=7)
    x0, y0, x1, y1 = m.PORCH
    rect(ax, x0, y0, x1, y1, fc="none", ec=GREY, lw=0.6, ls=(0, (3, 2)), z=9)
    # trucks
    truck(ax, xa1, ya, 270, label="A  TRUCK FOR STALL 1")
    truck(ax, xa3, ya, 270, label="A  TRUCK FOR STALL 3")
    truck(ax, 36.6, -14.0, 0, color=GREEN, fc="#e3f1e7", cab="#bfdcc8", label="B  TRUCK IN THE STREET")
    arrow(ax, (52.0, -20.3), (58.0, -20.3), color=GREEN, lw=1.0)
    txt(ax, 51.4, -20.3, "leave downhill (east)", size=4.8, color=GREEN, ha="right", box=True)
    for xt, cc in ((xa1, car_c[0]), (xa3, car_c[2])):
        line(ax, [(xt, ya), (cc, m.CAR_Y0)], color=AMBER, lw=0.9, ls=(0, (5, 2, 1, 2)), z=13)
    lead(ax, ((xa1 + car_c[0]) / 2, (ya + m.CAR_Y0) / 2), (1.5, 15.5), f"winch line\n{ang1:.0f}° off the\nstall axis", size=4.6, color=AMBER, ha="center")
    # dimensions
    dimb(ax, (m.OPEN[0], m.YF + 21.6), (m.OPEN[1], m.YF + 21.6), 0, f"{ftin(m.OPEN_W)} OPENING, NO DOORS", ext=False, color=BLUE, size=5.0)
    dimb(ax, (m.OPEN[0], 33.6), (post_w, 33.6), 0, f"{ftin(post_w - m.OPEN[0])} CLEAR", ext=False, size=4.6)
    dimb(ax, (post_e, 33.6), (m.OPEN[1], 33.6), 0, f"{ftin(m.OPEN[1] - post_e)} CLEAR", ext=False, size=4.6)
    for xx in (m.OPEN[0], post_w, post_e, m.OPEN[1]):
        line(ax, [(xx, 30.6), (xx, 34.4)], color=GREY, lw=0.3, z=8)
    dimb(ax, (neck_w - (m.WING_W[1][0] - (m.OPEN[0] + 1.5)), 0), (neck_e, 0), -24.6, f"{ftin(m.APRON_W_ROW)} AT THE R.O.W. LINE", color=BLUE, side=-1, size=5.0)
    dimb(ax, (m.OPEN[0] - 0.5, PAVE_N), (m.OPEN[1] + 0.5, PAVE_N), -16.2, f"{ftin(m.OPEN_W + 1.0)} AT THE PAVEMENT", color=BLUE, side=-1, size=5.0)
    xd = -4.2
    dimb(ax, (xd, 0), (xd, m.YF), 0, ftin(m.YF), ext=False, size=4.6, side=-1)
    dimb(ax, (xd, PAVE_N), (xd, 0), 0, ftin(-PAVE_N), ext=False, size=4.6, side=-1)
    dimb(ax, (xd, PAVE_S), (xd, PAVE_N), 0, f"±{ftin(PAVE_N - PAVE_S)} LANE", ext=False, size=4.6, side=-1)
    for yy in (m.YF, 0, PAVE_N, PAVE_S):
        line(ax, [(xd - 0.8, yy), (xd + 2.6, yy)], color=GREY, lw=0.3, z=8)
    # apron levels and slopes
    for (name, xo, xp, zs, sl) in APRON_SLOPE:
        spot(ax, xp, PAVE_N, 0.5 if name != "East edge" else -0.5, -1.2, color=BLUE, val=zs, size=4.6, z=14)
    spot(ax, 19.4, m.YF - 0.05, 0.5, 1.0, color=BLUE, val=m.EL_GAR, size=4.6, pre="EL ", z=14)
    key(ax, 5.0, 6.3, 1, tip=(m.WING_W[1][0] - 0.3, 2.5))
    key(ax, 5.0, 11.2, 2, tip=(m.OPEN[0] - 0.4, m.YF + 0.5))
    key(ax, m.COL_X[1], 6.4, 3, tip=(m.COL_X[1], m.YF + 0.1))
    key(ax, 49.5, 12.5, 4, tip=(41.0, m.YF + 0.3))
    key(ax, 49.5, 2.0, 5, tip=(41.4, 1.9))
    key(ax, 5.2, -3.6, 6, tip=(10.4, -3.6))
    key(ax, 24.3, 7.7, 7, tip=(24.3, m.YF - 0.6))
    txt(ax, 4.6, -12.4, "BAIRD STREET", size=7.0, weight="bold", color=GREY, z=6)
    txt(ax, 4.6, -14.3, "one lane · falls 11.4 %\nto the east", size=4.8, color=GREY, z=6, va="top")
    north_arrow(ax, 54.4, 35.4, 2.6, 6.5)
    scale_bar(ax, 37, -25.2, 20, 5, 0.65)
    title(ax, "Garage level: vehicle access and towing plan", "Amber = truck on the apron (position A) · green = truck in the street (position B) · dashed = Unit A walls over",
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
        f"Street levels are from LiDAR and the slopes are taken from EL {m.EL_GAR:.1f}. S-103 sets the slab at the trench drain "
        f"at EL {EL_TD:.2f}, which changes each slope by about {100 * (m.EL_GAR - EL_TD) / APRON_LEN:.0f} %. The survey and the City "
        "driveway permit fix the final apron grades.",
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


# ----------------------------------------------------------------------------
# C-104  Excavation and shoring
# ----------------------------------------------------------------------------
LAY_BACK = 1.0          # open-cut slope used for the test below (1 horizontal : 1 vertical)


def _cut_pt(pt):
    z = elev(*pt)
    return z, z - EL_EXC, _LOTP.exterior.distance(Point(pt))


def shoring_runs(a, b, n=60):
    """Parts of the cut face a->b where a 1:1 laid-back slope would cross a lot line."""
    runs, cur = [], None
    for i in range(n + 1):
        t = i / n
        pt = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        _, d, gap = _cut_pt(pt)
        if d * LAY_BACK > gap:
            cur = [pt, pt] if cur is None else [cur[0], pt]
        elif cur is not None:
            runs.append(cur)
            cur = None
    if cur is not None:
        runs.append(cur)
    return runs


def piles(ax, a, b, spacing=7.0, color=SHORE):
    L = math.dist(a, b)
    n = max(1, round(L / spacing))
    for i in range(n + 1):
        t = i / n
        ax.add_patch(Rectangle((a[0] + (b[0] - a[0]) * t - 0.3, a[1] + (b[1] - a[1]) * t - 0.3), 0.6, 0.6, fc=color, ec=color, zorder=11))


def strip(bg, cols, x0, y, w_total, fs=5.6):
    """Notes strip under a plan: equal columns of (heading, items)."""
    w = w_total / len(cols)
    for i, (head, items) in enumerate(cols):
        block(bg, x0 + i * w, y, w - 0.2, head, items, fs=fs, gap=0.02)


def sheet_c104(pdf):
    q = quantities()
    face_sw = (m.OPEN[0], Y_EXC_S)
    edges = {"W": (EXC[0], EXC[3]), "N": (EXC[3], EXC[2]), "E": (EXC[2], EXC[1]), "S": (EXC[0], face_sw)}
    runs = {k: shoring_runs(*v) for k, v in edges.items()}
    marks = [
        ("A", EXC[0], "SW corner of the cut", (2.4, 1.6)),
        ("B", (xw_exc(20.0), 20.0), "West face at section A", (2.6, 0.0)),
        ("C", EXC[3], "NW corner", (2.6, -1.6)),
        ("D", (27.0, Y_EXC_N), "Rear face, middle", (0.0, -1.7)),
        ("E", EXC[2], "NE corner", (-2.6, -1.6)),
        ("F", (m.XE + EXC_OFF, 20.0), "East face, middle", (-2.6, 0.0)),
        ("G", EXC[1], "SE corner", (-2.6, 1.6)),
        ("H", face_sw, "Front return at the pier", (0.6, 2.0)),
    ]
    data = [(k, pt, name, off) + _cut_pt(pt) for k, pt, name, off in marks]
    dW = [d[5] for d in data if d[0] in "ABC"]
    dE = [d[5] for d in data if d[0] in "EFG"]
    ret_w = (elev(m.xw_o(m.YF), m.YF) - m.EL_GAR, elev(m.xw_o(m.Y_GR_O), m.Y_GR_O) - m.EL_GAR)
    gap_side = YARD - EXC_OFF
    gap_ne = perp_to_rear(*EXC[2])
    loads = q["total"] * 1.3 / 12
    fig, bg = sheet("C-104", "1/8\" = 1'-0\"  ·  section 1/4\" = 1'-0\"", [
        ("Before any digging", [
            "1. Soil report first: bearing, lateral pressures, groundwater, depth to rock. It decides the shoring type "
            "and whether any face may be laid back.",
            "2. Shoring designed and stamped by an engineer. Soldier piles and lagging are shown; an equal system is acceptable.",
            "3. Call 811. Demolition and utility caps complete (C-101).",
            "4. Crack survey and monitoring points on 441 and 442 Baird St. Read them daily while the cut is open; "
            "stop work if they move.",
        ]),
        ("Rules for the cut", [
            "No excavation, pile, tie-back or slope across any lot line without a written easement.",
            "Nothing stored and no machine parked within 5 ft of the top of the cut.",
            "Fence the open cut. Keep water out: pump from a sump in the cut during construction only.",
        ]),
        ("Haul route", [
            f"About {q['total']:.0f} cy in the bank, {q['total'] * 1.3:.0f} cy loose: near {loads:.0f} loads of 12 cy. "
            "Trucks leave downhill (east) on Baird St. The street is one lane: flagger at all times, sweep daily.",
        ]),
    ])
    view = (-8, -12, 60, 54)
    ax = frame(fig, view, 8.0, left=0.6, bottom=1.8)
    site_base(ax, cont="full", row_tint=False, street_label=None)
    txt(ax, -3.4, 30, "442 BAIRD ST", size=5.0, color=GREY, weight="bold", rot=83.5)
    txt(ax, 56.0, 20, "441 BAIRD ST", size=5.0, color=GREY, weight="bold", rot=90)
    txt(ax, 39.5, 48.6, "386 FOREST AVE", size=5.0, color=GREY, weight="bold", box=True)
    poly(ax, m.OUT_U, fc="none", ec=GREY, lw=0.6, ls=(0, (4, 2)), z=5.5)
    site_work(ax, bg=True)
    lower_plan(ax, "bg", cars=False)
    # the cut
    poly(ax, EXC, fc="#e9dccb", ec=CUT, lw=1.1, z=2.6, alpha=0.75)
    poly(ax, EXC_IN, fc="none", ec=CUT, lw=0.6, ls=(0, (3, 2)), z=6)
    poly(ax, [p for p in m.APRON if p[1] < Y_EXC_S] + [(m.OPEN[1], Y_EXC_S), (m.OPEN[0], Y_EXC_S)][::1], fc="none", ec=CUT, lw=0.0, z=2.7)
    ap = [(m.OPEN[0], Y_EXC_S), (m.OPEN[1], Y_EXC_S)] + m.APRON[2:]
    poly(ax, ap, fc="#f1e8db", ec=CUT, lw=0.8, z=2.7, hatch="...", alpha=0.8)
    poly(ax, [(x, min(y, Y_EXC_S)) for x, y in LAND_POLY.exterior.coords], fc="#f1e8db", ec=CUT, lw=0.8, z=2.7, alpha=0.8)
    for a, b in (STEM_N, STEM_W):
        line(ax, [a, b], color=CUT, lw=3.2, z=5.6, alpha=0.55)
    txt(ax, 24.0, 21.5, f"GARAGE BOX\nsubgrade EL {EL_SUBGR:.1f} under the slab", size=5.4, weight="bold", color=CUT, z=12, box=True)
    txt(ax, 24.0, 17.6, f"footing trench EL {EL_EXC:.1f} inside the dashed line,\nall round ({ftin(FTG_OUT)} footing heel + {ftin(WORK)} working space)",
        size=4.8, color=CUT, z=12, box=True)
    txt(ax, 24.3, 3.0, f"APRON CUT\nto 12 in. below the apron surface", size=4.8, color=CUT, z=12, box=True)
    txt(ax, 19.0, 35.3, f"UNIT A SLAB ON GRADE: cut to EL {EL_SOG_SUBGR:.1f}", size=4.6, color=CUT, z=12, rot=m.REAR_ANGLE, box=True)
    lead(ax, rear_pt(13.0, -0.3), (16.5, 45.0), "stem-wall footing trench,\n36 in. min. below finish grade", size=4.6, color=CUT, ha="center")
    # shoring
    for k, rr in runs.items():
        for a, b in rr:
            line(ax, [a, b], color=SHORE, lw=2.0, z=10.5)
            piles(ax, a, b)
    # cut-depth marks
    for (k, pt, name, off, z, d, gap) in data:
        ax.add_patch(Circle(pt, 0.45, fc=PAPER, ec=INK, lw=0.6, zorder=13))
        txt(ax, pt[0] + off[0], pt[1] + off[1], f"{k}  {d:.1f}'", size=5.2, weight="bold", z=14, box=True)
    # clearances
    pw = (xw_exc(27.0), 27.0)
    lead(ax, (pw[0] - 0.8, pw[1] + 0.1), (-3.6, 13.5), f"cut face {ftin(gap_side)}\nfrom the lot line,\nabout {ftin(gap_side + 1.0)} from\nthe house wall", size=4.6, color=SHORE, ha="center")
    lead(ax, (m.XE + EXC_OFF + 0.8, 27.0), (56.0, 37.6), f"cut face {ftin(gap_side)}\nfrom the lot line,\nabout {ftin(gap_side + 1.0)}\nfrom the house", size=4.6, color=SHORE, ha="center")
    lead(ax, (EXC[2][0] + 0.2, EXC[2][1] + 0.4), (53.5, 44.6), f"corner of the cut is\n{gap_ne * 12:.0f} in. from the rear line", size=4.6, color=SHORE, ha="center")
    pd = (27.0, Y_EXC_N)
    dd = perp_to_rear(*pd)
    dimb(ax, pd, (pd[0] + N_R[0] * dd, pd[1] + N_R[1] * dd), 0, ftin(dd), color=SHORE, ext=False, size=4.8, side=-1)
    pc = EXC[3]
    dc = perp_to_rear(*pc)
    dimb(ax, pc, (pc[0] + N_R[0] * dc, pc[1] + N_R[1] * dc), 0, ftin(dc), color=SHORE, ext=False, size=4.8, side=-1)
    # section mark
    for xx in (-6.0, 15.5):
        line(ax, [(xx, 20.0), (xx + (2.2 if xx < 0 else -2.2), 20.0)], lw=1.4, z=12)
        txt(ax, xx, 21.4, "A", size=7, weight="bold", z=12)
    arrow(ax, (20, -9.6), (44, -9.6), color=INK, lw=1.0)
    txt(ax, 19, -9.6, "HAUL ROUTE: downhill on Baird St", size=5.2, weight="bold", ha="right", box=True)
    north_arrow(ax, -3.4, 47.6, 2.6, 6.5)
    scale_bar(ax, 38, -5.4, 20, 5, 0.6)
    title(ax, "Excavation and shoring plan", "Existing contours 1 ft · brown tint = excavation · red = shoring, piles at about 7 ft (preliminary)",
          dx=6.4, dy=1.4, clear=(52, 4.4))
    # ---- notes strip under the plan
    need = ", ".join({"W": "west", "N": "rear", "E": "east", "S": "front return at the pier"}[k] for k in "WNES" if runs[k])
    n_run = runs["N"]
    n_txt = ("its whole length" if n_run and math.dist(*n_run[0]) > 0.9 * math.dist(*edges["N"]) else
             f"the east {math.dist(*n_run[-1]):.0f} ft" if n_run else "not needed")
    strip(bg, [
        ("Where shoring is needed", [
            f"Test used: would an open cut laid back 1:1 cross a lot line? It would on these faces: {need}.",
            f"WEST: {ftin(YARD)} yard, wall retains {ret_w[0]:.1f} to {ret_w[1]:.1f} ft above the slab, cut {min(dW):.1f} to {max(dW):.1f} ft deep. "
            f"EAST: cut {min(dE):.1f} to {max(dE):.1f} ft deep. REAR: {n_txt}.",
        ]),
        ("What the cut is next to", [
            "The cut goes well below the neighbours' footings (depths not known), about "
            f"{ftin(gap_side + 1.0)} from each house wall. The shoring must hold those houses still: design for it.",
            "442 Baird St belongs to this owner; 441 Baird St and 386 Forest Ave do not. A temporary easement from "
            "386 Forest Ave would allow an open cut at the rear.",
        ]),
        ("For the engineer to decide", [
            f"The footing heel stands {ftin(FTG_OUT)} outside the wall (S-101). With {ftin(WORK)} of working space the cut face is "
            f"{ftin(gap_side)} from the side lot lines and {gap_ne * 12:.0f} in. from the rear line at the NE corner. An L-shaped "
            "footing (no heel) or less working space on those faces moves it back.",
            "Part of the Unit A slab on grade and its stem wall sit on backfill beside the garage wall: use "
            "compacted engineered fill or step the stem footing down to the garage wall (S-101).",
        ]),
    ], 0.6, 1.62, 8.5)

    # ---- right column: section A, schedule, quantities
    xr = 0.6 + 8.5 + 0.28
    wr = SHEET_W - MARGIN - TB_W - 0.15 - xr
    ytop = SHEET_H - MARGIN - 0.3
    bg.text(xr, ytop, "SECTION A: WEST SIDE AT Y = 20 FT, LOOKING NORTH", fontsize=7.0, fontweight="bold", va="top")
    bg.text(xr, ytop - 0.17, "1/4\" = 1'-0\". East side is the mirror image against 441 Baird St.", fontsize=4.9, color=GREY, va="top")
    ys = 20.0
    xl, xo, xe = west_x(ys), m.xw_o(ys), xw_exc(ys)
    xi, xt0, xt1 = xo + m.CONC / _CW, xo - FTG_OUT / _CW, xo + (FTG_IN + m.CONC) / _CW
    xn = xl - 1.0
    sv = (xl - 3.4, EL_EXC - 2.6, xo + 6.8, 930.0)
    sx = plan_axes(fig, xr, ytop - 0.32 - (sv[3] - sv[1]) / 4.0, (sv[0], sv[2]), (sv[1], sv[3]), 4.0)
    g = lambda x: elev(x, ys)  # noqa: E731
    xs = np.linspace(sv[0], xe, 30)
    soil = [(sv[0], sv[1])] + [(x, g(x)) for x in xs] + [(xe, EL_EXC), (xt1, EL_EXC), (xt1, EL_SUBGR), (sv[2], EL_SUBGR), (sv[2], sv[1])]
    poly(sx, soil, fc="#efe6da", ec="none", z=1)
    line(sx, [(x, g(x)) for x in xs], color=EARTH, lw=1.0, z=4)
    xs2 = np.linspace(xe, sv[2], 30)
    line(sx, [(x, g(x)) for x in xs2], color=EARTH, lw=0.6, ls=(0, (4, 2)), z=4)
    poly(sx, [(xe, EL_EXC), (xo, EL_EXC), (xo, g(xo)), (xe, g(xe))], fc="#f7f3ea", ec="none", hatch="...", z=1.5)
    line(sx, [(xe, g(xe)), (xe, EL_EXC), (xt1, EL_EXC), (xt1, EL_SUBGR), (sv[2], EL_SUBGR)], color=CUT, lw=1.0, z=5)
    # neighbour
    rect(sx, xn - 0.67, g(xn) - 0.1, xn, sv[3], fc="#d9dce0", ec=GREY, lw=0.6, z=3)
    rect(sx, xn - 1.3, g(xn) - 2.6, xn + 0.35, g(xn) - 1.8, fc="none", ec=GREY, lw=0.6, ls=(0, (2, 2)), z=3)
    txt(sx, xn - 0.5, g(xn) - 3.4, "footing\ndepth ?", size=4.4, color=GREY)
    txt(sx, xn - 1.5, g(xn) + 3.6, "442 BAIRD ST\nhouse wall", size=4.6, color=GREY, rot=90)
    line(sx, [(xl, sv[1] + 2.2), (xl, sv[3])], color=ACCENT, lw=1.0, ls=(0, (9, 2.5, 1.5, 2.5)), z=6)
    txt(sx, xl + 0.25, sv[3] - 1.0, "LOT LINE", size=4.6, color=ACCENT, ha="left", weight="bold")
    # shoring
    rect(sx, xe - 0.67, sv[1], xe, g(xe) + 0.5, fc="#f3c9c4", ec=SHORE, lw=0.8, z=5)
    line(sx, [(xe, EL_EXC - 0.3), (xe, g(xe) + 0.5)], color=SHORE, lw=1.6, z=6)
    # structure
    rect(sx, xt0, EL_EXC, xt1, m.EL_FTG_TOP, fc=CONC, ec=INK, lw=0.6, z=6)
    top = g(xo) + STEM_UP
    rect(sx, xo, m.EL_FTG_TOP, xi, top, fc=CONC, ec=INK, lw=0.6, z=6)
    rect(sx, xi, m.EL_GAR - 0.5, sv[2], m.EL_GAR, fc=CONC, ec=INK, lw=0.5, z=6)
    rect(sx, xi, m.EL_GAR - 1.0, sv[2], m.EL_GAR - 0.5, fc="#f7f3ea", ec=GREY, lw=0.3, hatch="ooo", z=5)
    rect(sx, xo, m.EL_B1_TOP, sv[2], m.EL_A, fc="#f4f1ea", ec=GREY, lw=0.4, z=5)
    rect(sx, xo, m.EL_A, xo + m.EXT, sv[3], fc="#f4f1ea", ec=GREY, lw=0.4, z=5)
    fdx = xo - FD_OFF / _CW
    zfd = max(m.EL_FTG_TOP, m.EL_DRAIN_HI - FD_SLOPE * (ys - m.YF) / _CW)
    sx.add_patch(Circle((fdx, zfd + 0.17), 0.17, fc=PAPER, ec=BLUE, lw=0.9, zorder=7))
    # 1:1 line
    line(sx, [(xe, EL_EXC), (sv[0], EL_EXC + (xe - sv[0]) / LAY_BACK)], color=GREY, lw=0.6, ls=(0, (5, 3)), z=4.5)
    txt(sx, sv[0] + 0.15, EL_EXC + 2.1, "1:1 open cut would cross\nthe lot line: not allowed", size=4.4, color=GREY, ha="left", rot=45, va="bottom")
    # dimensions
    yb = EL_EXC - 1.3
    for a, b, lab in ((xn, xl, "±1'"), (xl, xe, ftin(gap_side)), (xe, xt0, ftin(WORK)), (xt0, xo, ftin(FTG_OUT)), (xo, xi, "12\"")):
        dimb(sx, (a, yb), (b, yb), 0, lab, ext=False, size=4.4, side=-1)
        line(sx, [(a, yb - 0.3), (a, yb + 0.9)], color=GREY, lw=0.3, z=7)
    line(sx, [(xi, yb - 0.3), (xi, yb + 0.9)], color=GREY, lw=0.3, z=7)
    dimb(sx, (xe + 0.9, EL_EXC), (xe + 0.9, g(xe)), 0, f"CUT {g(xe) - EL_EXC:.1f} ft", ext=False, size=4.8, color=SHORE, side=-1)
    dimb(sx, (xi + 1.2, m.EL_GAR), (xi + 1.2, g(xo)), 0, f"RETAINS {g(xo) - m.EL_GAR:.1f} ft", ext=False, size=4.8, side=-1)
    txt(sx, sv[2] - 0.15, m.EL_GAR + 0.45, f"GARAGE SLAB EL {m.EL_GAR:.1f}", size=4.6, ha="right", weight="bold")
    txt(sx, sv[2] - 0.15, m.EL_A + 0.45, f"UNIT A FLOOR EL {m.EL_A:.1f}", size=4.6, ha="right", weight="bold")
    txt(sx, sv[2] - 0.15, EL_EXC - 0.5, f"bottom of footing EL {EL_EXC:.1f}", size=4.4, ha="right", color=CUT)
    lead(sx, (xe - 0.3, g(xe) - 3.0), (xl - 3.2, 918.3), "SOLDIER PILE AND\nLAGGING or equal,\nengineer-designed", size=4.5, color=SHORE, box=True)
    lead(sx, (fdx + 0.1, zfd + 0.3), (xo + 4.9, 917.0), "French drain on the\nfooting heel (S-102)", size=4.4, color=BLUE, ha="center")
    lead(sx, (xo + 0.5, 921.9), (xo + 4.9, 921.6), "12 in. concrete\nwall (S-102)", size=4.4, ha="center")
    lead(sx, ((xe + xo) / 2, 920.0), (xo + 4.2, 928.3), "free-draining backfill", size=4.4, ha="center")
    txt(sx, xl + 0.2, g(xl) + 0.5, "existing ground", size=4.3, color=EARTH, ha="left")
    # cut-depth schedule
    y = ytop - 0.32 - (sv[3] - sv[1]) / 4.0 - 0.18
    bg.text(xr, y, "CUT DEPTH AT THE FACE (to bottom of footing)", fontsize=6.4, fontweight="bold", va="top")
    rows = [("", "Where", "Ground EL", "Bottom EL", "Cut", "To lot line")]
    for (k, pt, name, off, z, d, gap) in data:
        rows.append((k, name, f"{z:.1f}", f"{EL_EXC:.1f}", f"{d:.1f} ft", ftin(gap)))
    y = ztable(bg, xr, y - 0.17, [0.22, 1.5, 0.66, 0.66, 0.56, 0.62], rows, fs=5.2, rh=0.168)
    bg.text(xr, y - 0.12, "EXCAVATION QUANTITIES (approximate, bank measure)", fontsize=6.4, fontweight="bold", va="top")
    rows = [("Part", "Cubic yards"),
            (f"Garage box to EL {EL_SUBGR:.1f}, {q['box_area']:,.0f} sf, vertical sides", f"{q['box']:.0f}"),
            (f"Footing trenches, EL {EL_SUBGR:.1f} down to {EL_EXC:.1f}", f"{q['ftg']:.0f}"),
            ("Apron, 12 in. below its surface", f"{q['apron']:.0f}"),
            ("Entry landing and trash bay", f"{q['land']:.0f}"),
            (f"Unit A slab on grade, cut to EL {EL_SOG_SUBGR:.1f}", f"{q['sog']:.0f}"),
            ("Stem-wall footing trenches", f"{q['stem']:.0f}"),
            ("TOTAL, in the bank", f"{q['total']:.0f}")]
    y = ztable(bg, xr, y - 0.29, [3.3, 0.92], rows, fs=5.2, rh=0.168, flag=())
    block(bg, xr, y - 0.08, wr, None, [
        "Computed on a 3 in. grid from the 1 m LiDAR ground. Expect ±15 % until the survey is in. Loose volume about 1.3 x. "
        "Wing-wall footings and any laid-back slopes are not included.",
    ], fs=5.0, hang="")
    save(fig, "C-104", pdf)


# ----------------------------------------------------------------------------
# C-105  Grading, drainage and erosion control
# ----------------------------------------------------------------------------
SILT = "#2e7d32"


def pipe(ax, pts, color=STORM, lw=1.1, perf=False, z=10):
    line(ax, pts, color=color, lw=lw, ls=(0, (3, 1.6)) if perf else "-", z=z)


def flow(ax, a, b, color=STORM, t=0.5, scale=5):
    mx, my = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
    L = math.dist(a, b)
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    arrow(ax, (mx - ux * 0.6, my - uy * 0.6), (mx + ux * 0.6, my + uy * 0.6), color=color, lw=0.8, scale=scale, z=11)


def cleanout(ax, pt, color=STORM, r=0.5):
    ax.add_patch(Circle(pt, r, fc=PAPER, ec=color, lw=0.9, zorder=11.5))
    ax.add_patch(Circle(pt, r * 0.4, fc=color, ec=color, lw=0.3, zorder=11.6))


TD_PIPE = [(m.OPEN[1], TD_Y), (m.XE + 0.6, TD_Y), J1]


def storm_lines(ax, color=STORM, lw=1.1, marks=True):
    """French drain, upper drain, trench drain, storm line S1, roof leaders and the outlet (shared by C-105 and C-106)."""
    pipe(ax, FD, color, lw, perf=True)
    pipe(ax, TAIL, color, lw)
    pipe(ax, [rear_pt(0.0, UD_OFF), S1[0]], color, lw * 0.8, perf=True)
    pipe(ax, S1, color, lw * 0.8)
    pipe(ax, TD_PIPE, color, lw * 0.8)
    pipe(ax, RL_W, color, lw * 0.7)
    pipe(ax, [DS["NW"], RL_W[0]], color, lw * 0.7)
    pipe(ax, [DS["SW"], RL_W[1]], color, lw * 0.7)
    pipe(ax, [DS["SE"], (m.XE + 0.2, m.YF - 1.4), J1], color, lw * 0.7)
    if marks:
        for pt in FD + [J1]:
            cleanout(ax, pt, color)
        for pt in DS.values():
            rect(ax, pt[0] - 0.35, pt[1] - 0.35, pt[0] + 0.35, pt[1] + 0.35, fc=color, ec=color, lw=0.3, z=11.5)
        ox, oy = m.DRAIN_OUT
        poly(ax, [(ox - 0.7, oy + 0.5), (ox + 0.7, oy + 0.5), (ox, oy - 0.8)], fc=color, ec=color, lw=0.4, z=11.5)
        ox, oy = RL_W[-1]
        poly(ax, [(ox - 0.5, oy + 0.4), (ox + 0.5, oy + 0.4), (ox, oy - 0.6)], fc=color, ec=color, lw=0.4, z=11.5)


def sheet_c105(pdf):
    L = m.REAR_WALL_LEN
    out_fall = m.EL_DRAIN_OUT - street_el(m.DRAIN_OUT[0])
    slab_rise = (m.EL_GAR - EL_TD) * 12
    ud1, ud2 = fg_rear(0.0) - UD_DEPTH, fg_rear(L) - UD_DEPTH
    ey0, ey1 = elev(47.4, 30.0), elev(47.4, 10.0)
    wy0, wy1 = elev(m.xw_o(40.0) - 2.6, 40.0), elev(m.xw_o(m.YF) - 2.6, m.YF)
    fig, bg = sheet("C-105", "1/8\" = 1'-0\"  ·  section 1/4\" = 1'-0\"", [
        ("Finish grades", [
            f"Garage slab EL {m.EL_GAR:.2f} at the rear wall, falling 1/8 in./ft ({slab_rise:.1f} in.) to EL {EL_TD:.2f} at the "
            "trench drain (S-103).",
            f"Unit A floor EL {m.EL_A:.1f}. Entry landing EL {m.EL_GAR:.1f}, level with the garage floor.",
            "Concrete (stem wall or garage wall) stops 8 in. above finish grade all round; wood framing starts above that.",
            "Side yards follow the existing ground and fall to the street. Slope the ground away from the walls at 5 % "
            "for the first 2'-6\".",
        ]),
        ("Erosion control", [
            "1. Silt fence on the street side and down the east side before any ground is opened.",
            "2. Stone construction entrance on the apron line: 2 to 3 in. stone, 6 in. thick, on fabric.",
            "3. Protect any storm inlet found downhill; none is known on this block. Stone splash pad at both outlets.",
            "4. Seed and mulch bare ground within 7 days of final grade; temporary seed on ground left idle 14 days.",
            "5. Sweep the street daily. Concrete washout on the lot, not in the street.",
        ]),
    ])
    view = (-8, -12, 60, 54)
    ax = frame(fig, view, 8.0, left=0.6, bottom=1.8)
    site_base(ax, cont="faint", clabels=False, street_label=None)
    txt(ax, -3.6, 32, "442 BAIRD ST", size=5.0, color=GREY, weight="bold", rot=83.5)
    txt(ax, 56.0, 20, "441 BAIRD ST", size=5.0, color=GREY, weight="bold", rot=90)
    new_building(ax, lw=1.3, fill="#fbfbfc")
    line(ax, [m.OUT_L[0], m.OUT_L[3]], color=GREY, lw=0.5, z=8.2)
    site_work(ax)
    # floors and slab
    txt(ax, 24.3, 21.5, f"GARAGE SLAB  EL {m.EL_GAR:.2f} at the rear wall", size=5.4, weight="bold", z=12)
    arrow(ax, (24.3, 19.6), (24.3, 13.2), color=BLUE)
    txt(ax, 25.0, 16.6, f"1/8 in./ft to the trench\ndrain, EL {EL_TD:.2f}", size=4.8, color=BLUE, ha="left", z=12)
    txt(ax, 22.0, 34.6, f"UNIT A SLAB ON GRADE  EL {m.EL_A:.1f}", size=4.8, weight="bold", z=12, rot=m.REAR_ANGLE)
    txt(ax, 40.4, 6.7, f"LANDING\nEL {m.EL_GAR:.1f}", size=4.4, z=12)
    # apron grades
    for (name, xo, xp, zs, sl) in APRON_SLOPE:
        xm = (xo + xp) / 2 + (1.6 if name == "West edge" else -1.6 if name == "East edge" else 0)
        a, b = (xm, PAVE_N + 1.2), (xm, m.YF - 2.6)
        if sl > 0:
            arrow(ax, a, b, color=BLUE)
        else:
            arrow(ax, b, a, color=BLUE)
        txt(ax, xm + 0.4, 3.4, f"{abs(sl):.1f} %", size=4.8, color=BLUE, ha="left", z=12, box=True)
        spot(ax, xp, PAVE_N, 0.4, -1.1, color=BLUE, val=zs, size=4.4, z=12)
    # swale
    sw = [rear_pt(sv_, SWALE_OFF) for sv_ in np.linspace(-2.0, L + 2.4, 12)]
    sw_e = [sw[-1], (47.4, sw[-1][1] - 1.6), (47.4, 1.0), (47.6, PAVE_N + 0.6)]
    line(ax, sw + sw_e[1:], color=BLUE, lw=0.9, ls=(0, (6, 2, 1, 2)), z=9.5)
    for t_ in (0.2, 0.5, 0.8):
        i = int(t_ * (len(sw) - 1))
        flow(ax, sw[i], sw[i + 1], color=BLUE)
    for a, b in ((sw_e[1], sw_e[2]),):
        for t_ in (0.3, 0.75):
            flow(ax, a, b, color=BLUE, t=t_)
    for s_, dx, dy in ((0.0, -2.2, 2.2), (L / 2, 1.0, 2.3), (L, 1.4, 2.6)):
        pt = rear_pt(s_, SWALE_OFF)
        spot(ax, pt[0], pt[1], dx, dy, color=BLUE, val=swale_inv(s_), size=4.6, pre="INV ", z=12)
    lead(ax, rear_pt(L * 0.3, SWALE_OFF), (30.5, 46.4), f"REAR SWALE, centre line {ftin(SWALE_OFF)} from the wall,\nfalls east {100 * (swale_inv(0) - swale_inv(L)) / L:.0f} %: "
         "erosion matting and sod", size=4.8, color=BLUE, ha="center")
    for s_, lab in ((1.2, "NW"), (L - 1.2, "NE")):
        pt = rear_pt(s_, -1.6)
        txt(ax, pt[0], pt[1], f"T.O. CONC.\n{fg_rear(s_) + STEM_UP:.1f}", size=4.2, z=12, ha="center", box=True)
    # side yards
    arrow(ax, (47.4 + 1.6, 27.0), (47.4 + 1.6, 22.0), color=BLUE)
    lead(ax, (49.0, 24.5), (55.6, 30.5), f"east yard falls\n{100 * (ey0 - ey1) / 20:.0f} % to the street", size=4.6, color=BLUE, ha="center")
    wa = (m.xw_o(33.0) - 3.9 / _CW, 33.0)
    wb = (m.xw_o(27.0) - 3.9 / _CW, 27.0)
    arrow(ax, wa, wb, color=BLUE)
    lead(ax, ((wa[0] + wb[0]) / 2, 30.0), (-3.4, 40.5), f"west yard falls\n{100 * (wy0 - wy1) / (40.0 - m.YF):.0f} % to the front", size=4.6, color=BLUE, ha="center")
    for (x, y, dx, dy) in [(0, 0, 0.7, 1.2), (50, 0, 0.8, 1.0), (50, 34, 0.9, 1.0), (LOT_NW[0], LOT_NW[1], 0.9, 1.3)]:
        spot(ax, x, y, dx, dy, size=4.4)
    # drains
    storm_lines(ax)
    for a, b in ((FD[0], FD[1]), (FD[1], FD[2]), (FD[2], FD[3])):
        flow(ax, a, b)
    flow(ax, rear_pt(0.0, UD_OFF), S1[0], t=0.45)
    flow(ax, TD_PIPE[0], TD_PIPE[1])
    flow(ax, RL_W[0], RL_W[1])
    labs = [(FD[0], f"CO-1  {fd_inv(0):.2f}", (-3.4, -1.4)), (FD[1], f"CO-2  {fd_inv(1):.2f}", (-3.6, 1.2)),
            (FD[2], f"CO-3  {fd_inv(2):.2f}", (8.6, 4.0)), (FD[3], f"CO-4  {fd_inv(3):.2f}", (7.6, 0.6)),
            (J1, f"J-1  {fd_inv(4):.2f}", (7.6, -0.4))]
    for pt, lab, (dx, dy) in labs:
        lead(ax, pt, (pt[0] + dx, pt[1] + dy), lab, size=4.6, color=STORM, ha="center", weight="bold", head="-")
    lead(ax, m.DRAIN_OUT, (54.5, -9.3), f"OUTLET  INV EL {m.EL_DRAIN_OUT:.1f}\nstone splash pad", size=4.8, color=STORM, ha="center", weight="bold")
    lead(ax, RL_W[-1], (0.5, -9.4), "roof leader outlet", size=4.6, color=STORM, ha="center")
    lead(ax, (18.0, TD_Y), (4.2, 13.0), "TD trench drain,\ngrate flush", size=4.6, color=STORM, ha="center")
    lead(ax, rear_pt(L * 0.72, UD_OFF), (41.0, 42.6), f"UD upper drain behind the stem wall\nINV {ud1:.1f} (west) to {ud2:.1f} (east)", size=4.6, color=STORM, ha="center")
    lead(ax, (X_S1, 18.5), (55.6, 13.6), "S1 solid storm pipe\nFD footing drain", size=4.6, color=STORM, ha="center")
    lead(ax, (RL_W[0][0] + (RL_W[1][0] - RL_W[0][0]) * 0.75, 17.5), (-4.0, 22.5), "RL solid\nroof leader", size=4.6, color=STORM, ha="center")
    # erosion control
    sf = [(-6.0, -1.0), (-3.0, PAVE_N + 0.9), (m.OPEN[0] - 1.6, PAVE_N + 0.9)]
    sf2 = [(m.OPEN[1] + 1.6, PAVE_N + 0.9), (44.4, PAVE_N + 0.9), (49.6, -4.6), (49.6, 33.6)]
    for ln_ in (sf, sf2):
        line(ax, ln_, color=SILT, lw=0.9, z=10)
        cum = _cum(ln_)
        for d in np.arange(1.0, cum[-1], 2.0):
            i = max(j for j in range(len(cum)) if cum[j] <= d)
            i = min(i, len(ln_) - 2)
            t_ = (d - cum[i]) / (cum[i + 1] - cum[i])
            px_, py_ = ln_[i][0] + (ln_[i + 1][0] - ln_[i][0]) * t_, ln_[i][1] + (ln_[i + 1][1] - ln_[i][1]) * t_
            txt(ax, px_, py_, "x", size=4.2, color=SILT, z=10)
    lead(ax, (4.0, PAVE_N + 0.9), (2.6, -3.2), "SILT FENCE", size=4.6, color=SILT, ha="center", weight="bold")
    lead(ax, (49.6, 2.6), (55.6, 2.6), "SILT\nFENCE", size=4.6, color=SILT, ha="center", weight="bold")
    ce = [(m.OPEN[0] + 1.5, 4.6), (m.OPEN[1] - 1.5, 4.6)] + m.APRON[2:5] + [(m.OPEN[0] + 1.5, 0.0)]
    poly(ax, [(m.apron_x(4.6, 0), 4.6), (m.apron_x(4.6, 1), 4.6)] + m.APRON[2:], fc="none", ec=SILT, lw=0.8, hatch="xx", z=4, alpha=0.6)
    txt(ax, 24.3, -4.4, "STONE CONSTRUCTION ENTRANCE (until the apron is poured)", size=4.6, color=SILT, weight="bold", z=12, box=True)
    txt(ax, 22, -9.9, "BAIRD STREET  ·  falls 11.4 % east", size=5.6, weight="bold", color=GREY, z=6)
    north_arrow(ax, -3.6, 47.4, 2.6, 6.5)
    scale_bar(ax, 38, -10.6, 20, 5, 0.6)
    title(ax, "Grading, drainage and erosion control plan", "Blue = finish grades and surface flow · green-blue = drains (inverts in the schedule) · green = erosion control",
          dx=6.4, dy=1.4, clear=(56, 4.4))
    # ---- strip under the plan
    bg.add_patch(Rectangle((0.6, 0.52), 3.1, 1.12, fc="#fbe3e0", ec=ACCENT, lw=1.2))
    bg.text(0.72, 1.46, "NO SUMP PUMP. GRAVITY ONLY.", fontsize=9.5, fontweight="bold", color=ACCENT, va="center")
    bg.text(0.72, 0.98, f"All foundation and surface water leaves by gravity at the\noutlet, INV EL {m.EL_DRAIN_OUT:.1f}. LiDAR puts the pavement "
            f"edge there at\nEL {street_el(m.DRAIN_OUT[0]):.1f}: about {out_fall * 12:.0f} in. of fall. THE SURVEY MUST CONFIRM IT\n"
            "before the garage floor level is fixed.", fontsize=5.6, color=ACCENT, va="center", linespacing=1.3)
    strip(bg, [
        ("Foundation drains", [
            f"FD: 4 in. perforated pipe in washed stone and filter fabric at the footing of the three buried walls, "
            f"{FD_OFF * 12:.0f} in. from the wall face (S-102). One run, CO-1 round the back to the outlet: {FD_LEN:.0f} ft at "
            f"{100 * FD_SLOPE:.2f} %. That is flat: set it with a laser. Solid pipe from CO-4 down.",
            "Cleanout risers to grade at CO-1 to CO-4 and J-1.",
        ]),
        ("Surface and roof water", [
            "TD, S1 and the south-east leader join the solid outlet pipe at J-1, with the wyes pointing downstream. "
            "The engineer sizes the pipe from J-1 down (6 in. assumed).",
            "Roof leaders are solid pipe, never tied into perforated pipe. Downspout positions are assumed at the four "
            "corners: see A-105. Both outlets are in the right-of-way: City Engineer approval.",
        ]),
    ], 3.9, 1.62, 5.2)

    # ---- right column
    xr = 0.6 + 8.5 + 0.28
    wr = SHEET_W - MARGIN - TB_W - 0.15 - xr
    ytop = SHEET_H - MARGIN - 0.3
    s0 = 8.0
    bg.text(xr, ytop, f"SECTION B: REAR SWALE, {ftin(s0)} EAST OF THE NW CORNER", fontsize=7.0, fontweight="bold", va="top")
    bg.text(xr, ytop - 0.17, "1/4\" = 1'-0\". Cut square to the rear wall, looking west.", fontsize=4.9, color=GREY, va="top")
    fg0, inv0 = fg_rear(s0), swale_inv(s0)
    zl = elev(*rear_pt(s0, YARD))
    ge = lambda t: elev(*rear_pt(s0, t))  # noqa: E731
    fb = stem_ftg_bottom(*rear_pt(s0, 0.0))
    sv = (-8.6, fb - 1.6, 8.0, zl + FENCE_H + 1.0)
    hh = (sv[3] - sv[1]) / 4.0
    sx = plan_axes(fig, xr, ytop - 0.32 - hh, (sv[0], sv[2]), (sv[1], sv[3]), 4.0)
    fin = [(0, fg0), (SWALE_OFF, inv0), (YARD, zl)] + [(t, ge(t)) for t in np.linspace(YARD, sv[2], 6)]
    poly(sx, [(0, sv[1])] + fin + [(sv[2], sv[1])], fc="#efe6da", ec="none", z=1)
    poly(sx, [(sv[0], sv[1]), (sv[0], m.EL_A - 0.42), (-m.CMU, m.EL_A - 0.42), (-m.CMU, sv[1])], fc="#efe6da", ec="none", z=1)
    line(sx, fin, color=BLUE, lw=1.1, z=5)
    line(sx, [(t, ge(t)) for t in np.linspace(sv[0], sv[2], 30)], color=EARTH, lw=0.6, ls=(0, (4, 2)), z=4)
    rect(sx, -m.CMU, fb + 10 / 12.0, 0, fg0 + STEM_UP, fc=CONC, ec=INK, lw=0.6, z=6)
    rect(sx, -m.CMU - 0.5, fb, 0.5, fb + 10 / 12.0, fc=CONC, ec=INK, lw=0.6, z=6)
    rect(sx, sv[0], m.EL_A - 5 / 12.0, -m.CMU, m.EL_A, fc=CONC, ec=INK, lw=0.5, z=6)
    rect(sx, sv[0], m.EL_A - 11 / 12.0, -m.CMU, m.EL_A - 5 / 12.0, fc="#f7f3ea", ec=GREY, lw=0.3, hatch="ooo", z=5)
    rect(sx, -m.EXT, fg0 + STEM_UP, 0, sv[3], fc="#f4f1ea", ec=GREY, lw=0.5, z=5)
    sx.add_patch(Circle((UD_OFF, fg0 - UD_DEPTH + 0.17), 0.17, fc=PAPER, ec=STORM, lw=0.9, zorder=7))
    rect(sx, 0.02, fg0 - UD_DEPTH - 0.2, 1.7, fg0 - 0.5, fc="none", ec=STORM, lw=0.4, hatch="...", z=4)
    line(sx, [(YARD, sv[1] + 0.6), (YARD, zl)], color=ACCENT, lw=1.0, ls=(0, (9, 2.5, 1.5, 2.5)), z=6)
    rect(sx, YARD - 0.12, zl, YARD + 0.12, zl + FENCE_H, fc="#c8b89a", ec=EARTH, lw=0.5, z=6)
    dimb(sx, (YARD + 0.9, zl), (YARD + 0.9, zl + FENCE_H), 0, "6'-0\" FENCE", ext=False, size=4.4, side=-1)
    dimb(sx, (0, sv[1] + 0.75), (SWALE_OFF, sv[1] + 0.75), 0, ftin(SWALE_OFF), ext=False, size=4.4)
    dimb(sx, (SWALE_OFF, sv[1] + 0.75), (YARD, sv[1] + 0.75), 0, ftin(YARD - SWALE_OFF), ext=False, size=4.4)
    dimb(sx, (-1.6, fg0), (-1.6, fg0 + STEM_UP), 0, "8\"", ext=False, size=4.4)
    txt(sx, sv[0] + 0.2, m.EL_A + 0.5, f"UNIT A SLAB EL {m.EL_A:.1f}", size=4.6, weight="bold", ha="left", box=True)
    lead(sx, (-m.CMU / 2, fg0 + STEM_UP), (-4.6, fg0 + STEM_UP + 2.4), f"TOP OF CONCRETE EL {fg0 + STEM_UP:.1f}\n8 in. above finish grade", size=4.5, ha="center")
    lead(sx, (SWALE_OFF, inv0), (3.4, inv0 + 3.4), f"SWALE INV EL {inv0:.1f}", size=4.5, color=BLUE, ha="center", weight="bold")
    lead(sx, (0.9, fg0 - 0.1), (4.1, fg0 - 1.5), "5 % to the swale", size=4.4, color=BLUE, ha="center")
    lead(sx, (UD_OFF + 0.15, fg0 - UD_DEPTH + 0.2), (3.4, fg0 - UD_DEPTH + 0.4), f"UD 4 in. perforated,\nINV EL {fg0 - UD_DEPTH:.1f}", size=4.4, color=STORM, ha="center")
    lead(sx, (-m.CMU / 2, fb + 1.6), (-5.0, fb + 0.2), "8 in. stem wall on a\n20 x 10 in. footing (S-101)", size=4.4, ha="center")
    txt(sx, YARD + 0.25, sv[1] + 0.9, "REAR\nLOT LINE", size=4.3, color=ACCENT, ha="left", weight="bold")
    txt(sx, sv[2] - 0.2, ge(sv[2] - 0.6) + 0.55, "existing", size=4.2, color=EARTH, ha="right")
    # drain schedule
    y = ytop - 0.32 - hh - 0.16
    bg.text(xr, y, "DRAIN SCHEDULE (preliminary inverts)", fontsize=6.4, fontweight="bold", va="top")
    gnd = lambda p: elev(*p)  # noqa: E731
    rows = [("Mark", "What and where", "Invert EL", "Ground EL")]
    for i, nm in enumerate(("CO-1  SW corner, high point", "CO-2  NW corner", "CO-3  NE corner", "CO-4  SE corner, solid from here", "J-1   junction cleanout")):
        rows.append((nm[:4].strip(), nm[6:], f"{fd_inv(i):.2f}", f"{gnd(FD_RUN[i]):.1f}"))
    rows += [
        ("OUT", "Outlet at the street edge", f"{m.EL_DRAIN_OUT:.2f}", f"{gnd(m.DRAIN_OUT):.1f}"),
        ("TD", f"Trench drain: grate {EL_TD:.2f}, outlet", f"{EL_TD_OUT:.1f}", "-"),
        ("UD-1", "Upper drain, NW corner", f"{ud1:.1f}", f"{gnd(rear_pt(0, UD_OFF)):.1f}"),
        ("UD-2", "Upper drain, NE corner, solid S1 from here", f"{ud2:.1f}", f"{gnd(S1[0]):.1f}"),
        ("S1", "Storm pipe, east yard, 18 in. cover min.", "to J-1", "-"),
        ("RL", "West roof leader, 18 in. cover min.", "1 % min.", "-"),
    ]
    y = ztable(bg, xr, y - 0.17, [0.42, 2.45, 0.67, 0.68], rows, fs=5.2, rh=0.168)
    block(bg, xr, y - 0.1, wr, None, [
        f"The outlet invert EL {m.EL_DRAIN_OUT:.1f} is at the LiDAR ground level there: it daylights in the bank at the pavement edge. "
        "MUB meter pit A sits on the straight line to the outlet, so the pipe is shown jogged round it: MUB fixes the pit positions.",
        f"East yard falls {100 * (ey0 - ey1) / 20:.0f} %, west yard {100 * (wy0 - wy1) / (40.0 - m.YF):.0f} %: loose gravel will move. "
        "See C-107 for the surface.",
    ], fs=5.0, hang="")
    save(fig, "C-105", pdf)


# ----------------------------------------------------------------------------
# C-106  Site utilities
# ----------------------------------------------------------------------------
def sheet_c106(pdf):
    st_x = street_el(m.SEWER_OUT_X)
    ye = m.WATER_ENTRY[1]
    cover_wall = elev(m.XE, ye) - m.EL_WATER_ENTRY
    fig, bg = sheet("C-106", "3/16\" = 1'-0\"  ·  profile 1/8\"  ·  section 3/8\"", [
        ("Locate before design", [
            "Not known and not shown: the sewer main (position, size, invert), the water main, the utility pole and "
            "any overhead wires. The survey and each utility locate them; this sheet is then redrawn.",
        ]),
        ("Water: nothing may freeze", [
            f"Two 1 in. services, one per flat, each with its own MUB meter pit. Buried {m.WATER_DEPTH * 12:.0f} in. to the top of "
            "the pipe, below the 36 in. frost line, from the pits to the heated utility room.",
            "No water pipe anywhere in the open garage.",
        ]),
        ("Sewer: gravity only", [
            f"The building drain leaves under the garage slab (EL {m.EL_GAR:.1f}). The street beside it is EL {st_x:.1f}. "
            "The main must be deep enough for a lateral at 1/4 in./ft. No sewage pump is planned: find the main's "
            "invert before the garage floor level is fixed.",
        ]),
        ("Electric", [
            "All-electric building, no gas service. Two meters only. Underground service; no overhead drop to the building.",
        ]),
    ])
    view = (20, -18, 62, 34)
    ax = frame(fig, view, FPI, left=0.6, bottom=0.6)
    site_base(ax, cont="faint", clabels=False, street_label=None)
    txt(ax, 57.6, 3.0, "441 BAIRD ST", size=5.4, color=GREY, weight="bold")
    poly(ax, m.OUT_U, fc="none", ec=GREY, lw=0.6, ls=(0, (4, 2)), z=5.5)
    site_work(ax, bg=True)
    lower_plan(ax, "bg", cars=False)
    storm_lines(ax, color="#a9c4bf", lw=0.9, marks=False)
    ox, oy = m.DRAIN_OUT
    poly(ax, [(ox - 0.6, oy + 0.45), (ox + 0.6, oy + 0.45), (ox, oy - 0.7)], fc=STORM, ec=STORM, lw=0.4, z=11.5)
    lead(ax, (ox, oy - 0.2), (55.0, -9.6), f"STORM OUTLET  INV EL {m.EL_DRAIN_OUT:.1f}\nfooting, trench and roof drains (C-105)", size=4.8, color=STORM, ha="center")
    lead(ax, (X_S1 + 0.25, 17.0), (55.5, 16.6), "storm pipes, grey:\nsee C-105", size=4.6, color=STORM, ha="center")
    # water
    for i, (wx, wy) in enumerate(m.WATER_METERS):
        ax.add_patch(Circle((wx, wy), PIT_R, fc=PAPER, ec=WATER, lw=1.0, zorder=11))
        txt(ax, wx, wy, "AB"[i], size=4.6, weight="bold", color=WATER, z=12)
        line(ax, [(wx, wy - PIT_R), (wx + (i - 0.5) * 0.6, -10.5)], color=WATER, lw=0.9, ls=(0, (2, 2)), z=10)
    txt(ax, 47.3, -11.6, "to the water main\n(position not known)", size=4.6, color=WATER, z=12, box=True)
    line(ax, WATER_A[1:], color=WATER, lw=1.3, z=10.5)
    line(ax, WATER_B[1:], color=WATER, lw=1.3, z=10.5)
    rect(ax, m.XE - 1.0, ye - 0.3, m.XE, ye + 0.97, fc=WATER, ec=WATER, lw=0.3, z=11)
    lead(ax, (48.6, -1.6), (55.5, -3.4), "MUB METER PITS A, B\n(utility-owned, in the R.O.W.)", size=4.8, color=WATER, ha="center", weight="bold")
    lead(ax, (X_WB, 20.0), (55.5, 21.6), f"W-A, W-B: two 1 in. water\nservices, {m.WATER_DEPTH * 12:.0f} in. cover,\n7 in. apart in one trench", size=4.8, color=WATER, ha="center")
    lead(ax, (m.XE - 0.5, ye + 0.6), (56.2, 28.6), f"WATER ENTRY, EL {m.EL_WATER_ENTRY:.1f}:\ntwo sleeved cores through the\n12 in. wall, sealed both faces,\n"
         f"{ftin(m.Y_GR_O - ye)} south of the rear wall face.\nGround cover here {cover_wall:.1f} ft. Main\nshut-offs and pressure-reducing\nvalves inside (P-101).",
         size=4.6, color=WATER, ha="center")
    dimb(ax, (m.XE, 24.0), (X_WA, 24.0), 0, ftin(X_WA - m.XE), ext=False, size=4.4, color=WATER)
    dimb(ax, (X_WB, 15.0), (50.0, 15.0), 0, ftin(50.0 - X_WB), ext=False, size=4.4, color=WATER)
    # sewer
    sxx = m.SEWER_OUT_X
    line(ax, [(sxx, 15.5), (sxx, m.YF)], color=SEWER, lw=1.2, ls=(0, (3, 1.6)), z=10)
    line(ax, [(sxx, m.YF), m.SEWER_CO], color=SEWER, lw=1.5, z=10.5)
    line(ax, [m.SEWER_CO, (sxx, -13.5)], color=SEWER, lw=1.2, ls=(0, (5, 2)), z=10)
    arrow(ax, (sxx, -12.0), (sxx, -14.0), color=SEWER, lw=1.0)
    for r_ in (0.62, 0.3):
        ax.add_patch(Circle(m.SEWER_CO, r_, fc=PAPER if r_ > 0.5 else SEWER, ec=SEWER, lw=1.0, zorder=11.5))
    lead(ax, (sxx, 13.6), (25.0, 16.8), "4 in. building drain\nunder the slab (P-101)", size=4.6, color=SEWER, ha="center")
    lead(ax, (m.SEWER_CO[0] - 0.6, m.SEWER_CO[1]), (25.0, 5.2), "TWO-WAY CLEANOUT\nin the apron: traffic-rated\ncover, flush", size=4.6, color=SEWER, ha="center", weight="bold")
    lead(ax, (sxx, -3.6), (25.2, -3.6), "4 in. lateral, 1/4 in./ft min.\n(2 %), cleanout to the main", size=4.6, color=SEWER, ha="center")
    txt(ax, sxx, -15.6, "to the sewer main in Baird St:\nposition and depth NOT KNOWN", size=4.8, color=SEWER, weight="bold", z=12, box=True)
    dimb(ax, (sxx, 0.0), m.SEWER_CO, -1.3, ftin(m.SEWER_CO[1]), ext=False, size=4.4, color=SEWER, side=-1)
    dimb(ax, (sxx, 12.3), (m.OPEN[1], 12.3), 0, ftin(m.OPEN[1] - sxx), ext=False, size=4.4, color=SEWER)
    # electric and telecom
    ex, ey = m.E_METER
    rect(ax, ex, ey - 1.0, ex + 0.5, ey + 1.0, fc=POWER, ec=POWER, lw=0.4, z=11)
    rect(ax, ex, ey - 2.1, ex + 0.35, ey - 1.4, fc=PAPER, ec=POWER, lw=0.8, z=11)
    line(ax, [(ex + 0.5, ey - 0.4), (X_ET, ey - 0.9), (X_ET, 3.6)], color=POWER, lw=1.3, z=10.6)
    line(ax, [(ex + 0.35, ey - 1.8), (X_TEL, ey - 2.2), (X_TEL, 3.6)], color=POWER, lw=0.8, ls=(0, (4, 1.5)), z=10.6)
    for xx in (X_ET, X_TEL):
        line(ax, [(xx - 0.3, 3.45), (xx + 0.3, 3.75)], color=POWER, lw=0.8, z=10.7)
    lead(ax, (ex + 0.5, ey + 0.5), (55.5, 11.6), "2-POSITION METER STACK\non the east wall (E-101)", size=4.8, color=POWER, ha="center", weight="bold")
    lead(ax, (X_ET + 0.15, 6.4), (55.5, 6.9), "E: service lateral in conduit\nT: telecom conduit (dashed)\nBoth continue to the utility pole:\nPOLE POSITION NOT KNOWN", size=4.6, color=POWER, ha="center")
    # section and profile marks
    for xx in (43.2, 51.6):
        line(ax, [(xx, 11.5), (xx + (1.2 if xx < 45 else -1.2), 11.5)], lw=1.4, z=12)
        txt(ax, xx, 12.4, "B", size=6.5, weight="bold", z=12)
    txt(ax, 26.5, -9.4, "BAIRD STREET", size=7.0, weight="bold", color=GREY, z=6)
    txt(ax, 26.5, -10.9, "one lane · falls 11.4 % east", size=4.8, color=GREY, z=6)
    txt(ax, 28.5, 24.5, "OPEN GARAGE\nno water piping here", size=4.6, color=GREY, z=6)
    north_arrow(ax, 58.6, -14.4, 1.8, 6.5)
    scale_bar(ax, 21.5, -16.6, 12, 4, 0.42, size=5.2)
    title(ax, "Site utilities plan (east half of the lot)", "Blue = water · purple = sewer · orange = electric and telecom · grey-green = storm (C-105)",
          dx=0.6, dy=0.9, size=8.6, clear=(34, 2.5))
    # ---- right column
    xr = 0.6 + (view[2] - view[0]) / FPI + 0.3
    wr = SHEET_W - MARGIN - TB_W - 0.15 - xr
    ytop = SHEET_H - MARGIN - 0.3
    bg.text(xr, ytop, "WATER SERVICE PROFILE: METER PIT A TO THE UTILITY ROOM", fontsize=7.0, fontweight="bold", va="top")
    bg.text(xr, ytop - 0.17, "1/8\" = 1'-0\", no vertical exaggeration. Ground from LiDAR along the pipe route. Service B is the same.", fontsize=4.9, color=GREY, va="top")
    route = WATER_A
    cum = _cum(route)
    S, G, Pz = [], [], []
    for i in range(len(route) - 1):
        n = max(2, int((cum[i + 1] - cum[i]) / 0.5))
        for j in range(n + (1 if i == len(route) - 2 else 0)):
            t_ = j / n
            pt = (route[i][0] + (route[i + 1][0] - route[i][0]) * t_, route[i][1] + (route[i + 1][1] - route[i][1]) * t_)
            S.append(cum[i] + (cum[i + 1] - cum[i]) * t_)
            G.append(elev(*pt))
            if i < len(route) - 2:
                Pz.append(G[-1] - m.WATER_DEPTH)
            else:
                z0 = elev(*route[i]) - m.WATER_DEPTH
                Pz.append(min(G[-1] - m.WATER_DEPTH, z0 + (m.EL_WATER_ENTRY - z0) * t_))
    min_cover = min(g_ - p_ for g_, p_ in zip(G, Pz))
    pv = (-3.0, 908.6, cum[-1] + 3.4, 925.0)
    hh = (pv[3] - pv[1]) / 8.0
    px = plan_axes(fig, xr, ytop - 0.36 - hh, (pv[0], pv[2]), (pv[1], pv[3]), 8.0)
    g0 = G[0]
    poly(px, [(pv[0], pv[1]), (pv[0], g0 - 0.4)] + list(zip(S, G)) + [(cum[-1], pv[1])], fc="#efe6da", ec="none", z=1)
    line(px, [(pv[0], g0 - 0.4)] + list(zip(S, G)), color=EARTH, lw=1.0, z=4)
    line(px, list(zip(S, [g_ - 3.0 for g_ in G])), color=GREY, lw=0.5, ls=(0, (3, 2)), z=3)
    line(px, list(zip(S, Pz)), color=WATER, lw=1.6, z=6)
    rect(px, -PIT_R, Pz[0] - 0.3, PIT_R, g0, fc=PAPER, ec=WATER, lw=0.9, z=5)
    rect(px, cum[-1], m.EL_FTG_TOP, cum[-1] + m.CONC, pv[3], fc=CONC, ec=INK, lw=0.5, z=6)
    rect(px, cum[-1] + m.CONC, m.EL_GAR - 0.5, pv[2], m.EL_GAR, fc=CONC, ec=INK, lw=0.5, z=6)
    s_lot = cum[1] + (0.0 - route[1][1]) / (route[2][1] - route[1][1]) * (cum[2] - cum[1])
    line(px, [(s_lot, pv[1] + 0.4), (s_lot, pv[3] - 0.3)], color=ACCENT, lw=0.8, ls=(0, (9, 2.5, 1.5, 2.5)), z=6)
    txt(px, s_lot + 0.4, pv[3] - 1.0, "LOT LINE", size=4.2, color=ACCENT, ha="left")
    txt(px, 0, g0 + 0.9, "PIT A", size=4.6, color=WATER, weight="bold")
    for s_ in (9.0, 21.0):
        k = min(range(len(S)), key=lambda i: abs(S[i] - s_))
        dimb(px, (S[k], Pz[k]), (S[k], G[k]), 0, f"{m.WATER_DEPTH * 12:.0f}\" COVER", ext=False, size=4.4, color=WATER, side=-1)
    txt(px, 15.0, Pz[min(range(len(S)), key=lambda i: abs(S[i] - 15.0))] - 1.2, "1 in. service, follows the ground", size=4.6, color=WATER)
    txt(px, 14.0, G[min(range(len(S)), key=lambda i: abs(S[i] - 14.0))] + 0.9, "ground", size=4.4, color=EARTH)
    lead(px, (26.5, G[min(range(len(S)), key=lambda i: abs(S[i] - 26.5))] - 3.0), (22.5, 913.0), "frost line, 36 in.", size=4.3, color=GREY, ha="center")
    lead(px, (cum[-1], m.EL_WATER_ENTRY), (cum[-1] - 6.0, 911.4), f"enters at EL {m.EL_WATER_ENTRY:.1f}\n({cover_wall:.1f} ft of cover at the wall)", size=4.5, color=WATER, ha="center")
    txt(px, cum[-1] - 0.4, 924.2, f"utility room wall; slab EL {m.EL_GAR:.1f}", size=4.2, ha="right")
    # section B
    y = ytop - 0.36 - hh - 0.22
    bg.text(xr, y, "SECTION B: EAST SIDE YARD AT Y = 11'-6\", LOOKING NORTH", fontsize=7.0, fontweight="bold", va="top")
    bg.text(xr, y - 0.17, "3/8\" = 1'-0\". Seven lines share the 5'-2\" yard: lay them deepest first.", fontsize=4.9, color=GREY, va="top")
    yc = 11.5
    g = lambda x: elev(x, yc)  # noqa: E731
    f_ = 8 / 3.0
    sv = (43.0, 910.6, 52.2, 920.6)
    hs = (sv[3] - sv[1]) / f_
    sx = plan_axes(fig, xr, y - 0.36 - hs, (sv[0], sv[2]), (sv[1], sv[3]), f_)
    xs = np.linspace(m.XE, sv[2], 30)
    poly(sx, [(m.XE, sv[1])] + [(x, g(x)) for x in xs] + [(sv[2], sv[1])], fc="#efe6da", ec="none", z=1)
    line(sx, [(x, g(x)) for x in xs], color=EARTH, lw=1.0, z=4)
    rect(sx, m.XE - m.CONC, m.EL_FTG_TOP, m.XE, sv[3], fc=CONC, ec=INK, lw=0.6, z=6)
    rect(sx, m.XE - m.CONC - FTG_IN, EL_EXC, m.XE + FTG_OUT, m.EL_FTG_TOP, fc=CONC, ec=INK, lw=0.6, z=6)
    rect(sx, sv[0], m.EL_GAR - 0.5, m.XE - m.CONC, m.EL_GAR, fc=CONC, ec=INK, lw=0.5, z=6)
    xface = m.XE + EXC_OFF
    line(sx, [(xface, EL_EXC), (xface, g(xface))], color=SHORE, lw=1.2, ls=(0, (4, 2)), z=5)
    line(sx, [(50.0, sv[1] + 0.9), (50.0, sv[3])], color=ACCENT, lw=1.0, ls=(0, (9, 2.5, 1.5, 2.5)), z=6)
    rect(sx, 50.0 + 1.0, g(51.0) - 0.1, 50.0 + 1.67, sv[3], fc="#d9dce0", ec=GREY, lw=0.6, z=3)
    k4 = (yc - m.YF) / (FD[2][1] - m.YF)
    zfd = fd_inv(3) + (fd_inv(2) - fd_inv(3)) * k4
    items = [(m.XE + FD_OFF, max(zfd, m.EL_FTG_TOP) + 0.17, 0.17, STORM, "FD"), (X_TEL, g(X_TEL) - 2.0, 0.08, POWER, "T"),
             (X_ET, g(X_ET) - 2.5, 0.13, POWER, "E"), (X_S1, g(X_S1) - 2.0, 0.25, STORM, "S1"),
             (X_WA, g(X_WA) - m.WATER_DEPTH - 0.05, 0.07, WATER, "W-A"), (X_WB, g(X_WB) - m.WATER_DEPTH - 0.05, 0.07, WATER, "W-B")]
    for (x_, z_, r_, c_, lab) in items:
        sx.add_patch(Circle((x_, z_), r_, fc=PAPER if r_ > 0.1 else c_, ec=c_, lw=0.9, zorder=8))
        line(sx, [(x_, z_ + r_), (x_, g(x_))], color=c_, lw=0.3, ls=(0, (2, 2)), z=5)
    ytag = sv[3] - 0.45
    for (x_, z_, r_, c_, lab), dx in zip(items, (-0.3, -0.25, 0.0, 0.15, 0.35, 0.45)):
        txt(sx, x_ + dx, ytag, lab, size=4.6, color=c_, weight="bold", box=True)
        line(sx, [(x_, g(x_)), (x_ + dx, ytag - 0.25)], color=c_, lw=0.3, z=5)
    yb = sv[1] + 0.45
    for a, b in ((m.XE, X_WA), (X_WA, X_WB), (X_WB, 50.0)):
        dimb(sx, (a, yb), (b, yb), 0, ftin(b - a), ext=False, size=4.3, side=-1)
    txt(sx, 50.0 - 0.1, sv[1] + 1.25, "LOT LINE", size=4.3, color=ACCENT, ha="right", weight="bold")
    txt(sx, 51.35, 919.4, "441 BAIRD ST", size=4.3, color=GREY, rot=90)
    txt(sx, sv[0] + 0.1, m.EL_GAR + 0.3, f"EL {m.EL_GAR:.1f}", size=4.4, ha="left", va="bottom")
    txt(sx, xface + 0.12, 913.4, "shoring face\n(C-104)", size=4.0, color=SHORE, ha="left")
    # depth list beside the section
    xt = xr + (sv[2] - sv[0]) / f_ + 0.12
    block(bg, xt, y - 0.42, SHEET_W - MARGIN - TB_W - 0.12 - xt, "Depth to the pipe", [
        f"FD footing drain, 4 in.: INV EL {zfd:.2f}, at the footing heel (S-102), {(FD_OFF) * 12:.0f} in. from the wall.",
        f"T telecom conduit: 24 in., {(X_TEL - m.XE) * 12:.0f} in. from the wall.",
        f"E electric conduit: 30 in. or the power company's standard, {(X_ET - m.XE) * 12:.0f} in. from the wall.",
        f"S1 storm, 6 in. solid: 24 in. here, 18 in. min., {(X_S1 - m.XE) * 12:.0f} in. from the wall.",
        f"W-A, W-B water, 1 in.: {m.WATER_DEPTH * 12:.0f} in. to the top of the pipe.",
        "Keep 12 in. between water and electric. All of it sits in the backfill inside the shoring face.",
    ], fs=5.0, hang="", gap=0.03, rule=False)
    # who does what
    y = y - 0.36 - hs - 0.2
    bg.text(xr, y, "WHO DOES WHAT (confirm with each utility)", fontsize=6.6, fontweight="bold", va="top")
    rows = [("Work", "By"),
            ("Water main taps, meter pits A and B, meters", "MUB"),
            ("Water services from the pits to the utility room", "Owner's plumber; MUB inspects"),
            ("Sewer tap at the main", "MUB"),
            ("Building sewer, cleanout and lateral to the tap", "Owner's plumber; MUB inspects"),
            ("Service conductors and the two meters", "Power company"),
            ("Trench, conduits, meter stack, grounding", "Owner's electrician"),
            ("Telecom conduit and pull string", "Owner's electrician; provider pulls"),
            ("Storm drains and the outlet in the right-of-way", "Owner's site contractor; City Engineer")]
    ztable(bg, xr, y - 0.17, [2.55, 2.2], rows, fs=5.1, rh=0.165)
    print(f"   C-106: min water cover along the route {min_cover:.2f} ft")
    save(fig, "C-106", pdf)


# ----------------------------------------------------------------------------
# C-107  Paving, site walls, fence and trash bay
# ----------------------------------------------------------------------------
def _wall_w(t):
    """West wing wall at fraction t from the pier: point, existing ground behind it, apron surface in front."""
    (ax_, ay_), (bx_, by_) = m.WING_W
    x, y = ax_ + (bx_ - ax_) * t, ay_ + (by_ - ay_) * t
    return (x, y), elev(x - 0.6, y), apron_el(x + 0.4, y)


def _wall_e(s):
    """Low wall round the bay and landing at developed distance s from its west end: point, ground outside."""
    a, b, c = m.WING_E
    L1 = math.dist(a, b)
    if s <= L1:
        x, y = a[0] + (b[0] - a[0]) * s / L1, a[1]
        return (x, y), elev(x, y - 0.6)
    y = b[1] + (s - L1)
    return (b[0], y), elev(b[0] + 0.6, y)


def sheet_c107(pdf):
    Lw = math.dist(*m.WING_W)
    hw0, hw1 = _wall_w(0)[1] - _wall_w(0)[2], _wall_w(1)[1] - _wall_w(1)[2]
    L1 = math.dist(m.WING_E[0], m.WING_E[1])
    Le = L1 + math.dist(m.WING_E[1], m.WING_E[2])
    he = [(_wall_e(s)[1] - m.EL_GAR) for s in (0.0, L1, Le)]
    step = m.EL_GAR - apron_el(m.apron_x(m.LAND_Y0, 1) - 0.2, m.LAND_Y0)
    fence_L = math.dist(LOT_NW, LOT_NE)
    bank_w = (elev(m.WING_W[1][0] - 1.0, -0.5) - apron_el(m.OPEN[0] + 1.6, -0.5))
    fig, bg = sheet("C-107", "1/8\" = 1'-0\"  ·  details as noted", [
        ("Apron", [
            "6 in. concrete, 4,000 psi, air-entrained, on 6 in. of compacted stone. No. 4 bars at 12 in. each way "
            "(preliminary). Broom finish across the slope.",
            "Control joints as drawn, 8'-8\" apart at most, cut 1 1/2 in. deep. Isolation joint at the trench drain "
            "and at the lot line, so the City can replace its part.",
            "The part in the right-of-way needs the City driveway permit.",
        ]),
        ("Site walls", [
            "Cast concrete, engineer-designed (the west wall retains over 4 ft). Footings 36 in. below finish grade. "
            "Drain stone and weep holes behind; waterproof the back.",
            "Both walls stop 6 in. inside the front lot line. Nothing in the right-of-way.",
        ]),
        ("Planting", [
            "4 in. of topsoil, seed and straw mulch on all green areas. Erosion matting in the rear swale and on the "
            "2:1 banks.",
        ]),
    ])
    view = (-8, -12, 60, 54)
    ax = frame(fig, view, 8.0, left=0.6, bottom=1.8)
    site_base(ax, cont="faint", clabels=False, street_label=None)
    txt(ax, -3.6, 32, "442 BAIRD ST", size=5.0, color=GREY, weight="bold", rot=83.5)
    txt(ax, 56.0, 20, "441 BAIRD ST", size=5.0, color=GREY, weight="bold", rot=90)
    txt(ax, 39.5, 48.6, "386 FOREST AVE", size=5.0, color=GREY, weight="bold")
    # surfaces
    foot_w = (m.OUT_U[3][0] + N_W[0] * YARD, m.OUT_U[3][1] + N_W[1] * YARD)
    p2 = (m.OUT_U[2][0] + N_R[0] * YARD, m.OUT_U[2][1] + N_R[1] * YARD)
    west_yard = [(west_x(m.YF), m.YF), m.OUT_U[0], m.OUT_U[3], foot_w]
    east_yard = [(m.WING_E[1][0], m.WING_E[1][1]), (50.0, m.WING_E[1][1]), LOT_NE, p2, m.OUT_U[2], (m.XE, m.YF), (m.WING_E[1][0], m.YF)]
    rear_yard = [foot_w, m.OUT_U[3], m.OUT_U[2], p2, LOT_NE, LOT_NW]
    front_yard = [LOT_SW, (m.apron_x(0, 0), 0.0), m.WING_W[1], m.WING_W[0], m.OUT_U[0], (west_x(m.YF), m.YF)]
    bank_wst = [(-5.0, 0.0), (m.apron_x(0, 0), 0.0), (m.OPEN[0] - 0.5, PAVE_N), (-5.0, PAVE_N)]
    bank_est = [(m.OPEN[1] - 1.5, 0.0), (50.0, 0.0), (50.0, PAVE_N), (m.OPEN[1] + 0.5, PAVE_N)]
    for pg in (west_yard, east_yard):
        poly(ax, pg, fc=GRAVEL, ec="none", z=2.2, hatch="....")
    for pg in (rear_yard, front_yard, bank_wst, bank_est):
        poly(ax, pg, fc=SEED, ec="none", z=2.1)
    new_building(ax, lw=1.3, fill="#fbfbfc")
    site_work(ax)
    if not BAY_OK:
        rect(ax, BAY[0], BAY[1], BAY[2], BAY[3], fc="none", ec=ACCENT, lw=0.9, ls=(0, (3, 2)), z=6)
    # bank ticks, 2:1
    for i in range(6):
        yy = -0.8 - i * 1.1
        xw_, xe_ = apron_edges(yy)
        hw_ = max(0.0, elev(xw_ - 3.0, yy) - apron_el(xw_ + 0.2, yy))
        he_ = max(0.0, elev(xe_ + 3.0, yy) - apron_el(xe_ - 0.2, yy))
        line(ax, [(xw_, yy), (xw_ - 2 * hw_, yy)], color="#5d8a4a", lw=0.5, z=4)
        line(ax, [(xe_, yy), (xe_ + 2 * he_, yy)], color="#5d8a4a", lw=0.5, z=4)
    # apron joints
    jc = dict(color=INK, lw=0.45, ls=(0, (6, 2)), z=5)
    for k in (1, 2):
        f = k / 3.0
        line(ax, [(m.OPEN[0] + m.OPEN_W * f, TD_Y), (m.OPEN[0] + 1.5 + m.APRON_W_ROW * f, 0.0), (m.OPEN[0] - 0.5 + (m.OPEN_W + 1.0) * f, PAVE_N)], **jc)
    line(ax, [(m.apron_x(5.0, 0), 5.0), (m.apron_x(5.0, 1), 5.0)], **jc)
    line(ax, [(m.apron_x(0, 0), 0.0), (m.apron_x(0, 1), 0.0)], color=INK, lw=1.0, z=7.5)
    for (name, xo, xp, zs, sl) in APRON_SLOPE:
        xm = (xo + xp) / 2 + (2.0 if name == "West edge" else -2.0 if name == "East edge" else 0)
        a, b = (xm, PAVE_N + 1.0), (xm, PAVE_N + 4.4)
        arrow(ax, a, b, color=BLUE) if sl > 0 else arrow(ax, b, a, color=BLUE)
        txt(ax, xm, PAVE_N + 5.4, f"{abs(sl):.1f} %", size=4.6, color=BLUE, z=12, box=True)
    # fence
    line(ax, [LOT_NW, LOT_NE], color=EARTH, lw=1.6, z=7.4)
    npost = math.ceil(fence_L / 8.0)
    for i in range(npost + 1):
        t_ = i / npost
        fx, fy = LOT_NW[0] + (LOT_NE[0] - LOT_NW[0]) * t_, LOT_NW[1] + (LOT_NE[1] - LOT_NW[1]) * t_
        rect(ax, fx - 0.4, fy - 0.4, fx + 0.4, fy + 0.4, fc=EARTH, ec=EARTH, lw=0.3, z=7.6)
    # heat pumps
    hx, hy = m.HP[0]
    hp_w = (hx - m.HP_SIZE[1] / 2 * _CW, hy + m.HP_SIZE[1] / 2 * _SWL)
    dimb(ax, (hp_w[0] + N_W[0] * HP_CLEAR, hp_w[1] + N_W[1] * HP_CLEAR), hp_w, 0, ftin(HP_CLEAR), ext=False, size=4.4, color=BLUE)
    # labels and keys
    txt(ax, 24.3, 24.0, "BUILDING\n(see A and S sheets)", size=5.2, color=GREY, z=12)
    lead(ax, _wall_w(0.08)[0], (4.6, 13.4), f"{ftin(hw0)} retained\nat the pier", size=4.6, ha="center", color=INK)
    lead(ax, _wall_w(0.97)[0], (5.2, 2.6), f"{ftin(hw1)} retained\nat the south end", size=4.6, ha="center", color=INK)
    lead(ax, (m.WING_E[2][0], m.YF - 0.6), (55.4, 12.6), f"{ftin(he[2])} retained\nat the building", size=4.6, ha="center")
    lead(ax, (m.WING_E[1][0], 1.0), (55.4, 5.2), f"{ftin(he[1])} retained\nat the corner", size=4.6, ha="center")
    key(ax, 24.3, 7.4, 1)
    key(ax, 24.3, -3.8, 2)
    key(ax, 8.0, 7.2, 3, tip=_wall_w(0.5)[0])
    key(ax, 40.2, 7.4, 4)
    key(ax, 42.0, -3.6, 5, tip=(41.5, 1.8))
    key(ax, 53.6, -1.6, 6, tip=(45.2, 0.5))
    key(ax, -3.6, 21.0, 7, tip=(m.HP[0][0] - 0.4, m.HP[0][1]))
    key(ax, 25.0, 46.8, 8, tip=(26.0, rear_y(26.0)))
    key(ax, 53.6, 26.0, 9, tip=(47.5, 26.0))
    key(ax, 2.0, 30.0, 9, tip=(m.xw_o(30.0) - 2.6, 30.0))
    key(ax, 24.0, 40.3, 10)
    key(ax, 6.0, 4.6, 10)
    key(ax, 3.0, -3.6, 11)
    key(ax, 47.6, -4.6, 11)
    txt(ax, 20, -9.9, "BAIRD STREET  ·  falls 11.4 % east", size=5.6, weight="bold", color=GREY, z=6)
    north_arrow(ax, -3.6, 47.4, 2.6, 6.5)
    scale_bar(ax, 38, -10.6, 20, 5, 0.6)
    title(ax, "Paving, site walls, fence and planting plan", "Dotted buff = gravel · green = topsoil and seed · numbers refer to the keyed notes below",
          dx=6.4, dy=1.4, clear=(56, 4.4))
    strip(bg, [
        ("Keyed notes", [
            f"1  APRON on the lot: {ftin(m.OPEN_W)} wide at the opening, {ftin(m.APRON_W_ROW)} at the lot line. Surface is warped: "
            f"west edge {abs(APRON_SLOPE[0][4]):.1f} % up to the street, east edge {abs(APRON_SLOPE[2][4]):.1f} % down (C-103).",
            f"2  APRON in the right-of-way, flaring to {ftin(m.OPEN_W + 1.0)} at the pavement. Apron only: no walls, steps or posts.",
            f"3  WEST WING WALL, {ftin(Lw)} long, 10 in. concrete (prelim.). Top 6 in. above the yard it retains.",
            f"4  ENTRY LANDING, 4 in. concrete on 6 in. stone, broom finish, level at EL {m.EL_GAR:.1f}. Its west edge stands "
            f"up to {step * 12:.0f} in. above the apron at the south end: form it as a kerb, flush at the opening.",
        ]),
        ("", [
            "5  TRASH BAY for 4 carts: see the detail.",
            f"6  LOW WALL round the bay and landing, {ftin(Le)} long in two legs, 8 in. concrete (prelim.).",
            f"7  HEAT-PUMP PADS, 2 no., precast or 4 in. concrete, level, for side-discharge units {m.HP_SIZE[0] * 12:.0f} x "
            f"{m.HP_SIZE[1] * 12:.0f} in. Unit {ftin(HP_CLEAR)} from the side line (2 ft min., zoning 1337.05(D)). Pad size on M-101.",
            f"8  PRIVACY FENCE, 6 ft, {ftin(fence_L)} along the rear lot line, {npost + 1} posts at 8 ft max. set 36 in. in concrete; "
            "panels stepped with the ground. On the line only with the rear owner's written agreement, otherwise 6 in. inside.",
        ]),
        ("", [
            "9  SIDE YARDS: 3 in. of angular crushed stone on geotextile. The yards fall 20 to 25 %: add a timber or stone "
            "check across the yard every 8 ft so the stone stays put.",
            "10  TOPSOIL AND SEED: rear yard and swale, and the front yard west of the apron (left at its natural level).",
            f"11  BANKS in the right-of-way graded 2:1 and seeded. At the end of the west wall the bank is about {bank_w:.1f} ft "
            f"high and runs out about {2 * bank_w:.0f} ft: confirm with the City Engineer.",
        ]),
    ], 0.6, 1.62, 8.5, fs=5.3)

    # ---- right column: trash bay, wall elevations
    xr = 0.6 + 8.5 + 0.28
    wr = SHEET_W - MARGIN - TB_W - 0.15 - xr
    ytop = SHEET_H - MARGIN - 0.3
    bw, bd = BAY[2] - BAY[0], BAY[3] - BAY[1]
    bg.text(xr, ytop, "TRASH BAY, 4 CARTS: PLAN", fontsize=7.0, fontweight="bold", va="top")
    bg.text(xr, ytop - 0.17, "1/4\" = 1'-0\". 96 gal carts, 26 x 34 in. each. All on the lot.", fontsize=4.9, color=GREY, va="top")
    dv = (BAY[0] - 2.6, -1.9, m.XE + 2.4, BAY[3] + 5.4)
    hd = (dv[3] - dv[1]) / 4.0
    dx_ = plan_axes(fig, xr, ytop - 0.34 - hd, (dv[0], dv[2]), (dv[1], dv[3]), 4.0)
    rect(dx_, dv[0], dv[1], dv[2], 0.0, fc="#fbe9e7", ec="none", z=1)
    poly(dx_, [(m.apron_x(dv[3], 1), dv[3]), (dv[0], dv[3]), (dv[0], 0.0), (m.apron_x(0.0, 1), 0.0)], fc="#d5dbe2", ec=INK, lw=0.5, z=2)
    rect(dx_, m.apron_x(BAY[3], 1), BAY[3], m.XE, dv[3], fc="#e7eaee", ec=INK, lw=0.5, z=2)
    rect(dx_, BAY[0], BAY[1], BAY[2], BAY[3], fc="#eef1e6", ec=INK, lw=0.6, z=3)
    line(dx_, m.WING_E, color=CONC, lw=5.0, z=4)
    line(dx_, [(dv[0], 0.0), (dv[2], 0.0)], color=ACCENT, lw=1.0, ls=(0, (9, 2.5, 1.5, 2.5)), z=6)
    txt(dx_, dv[0] + 0.2, -0.55, "FRONT LOT LINE · right-of-way below", size=4.4, color=ACCENT, ha="left")
    slack = (bw - 4 * CART_W) / 5
    for i in range(4):
        cx0 = BAY[0] + slack + i * (CART_W + slack)
        rect(dx_, cx0, BAY[1] + 0.08, cx0 + CART_W, BAY[1] + 0.08 + CART_D, fc=PAPER, ec=GREY, lw=0.6, z=5)
        txt(dx_, cx0 + CART_W / 2, BAY[1] + 0.08 + CART_D / 2, f"{i + 1}", size=5.2, color=GREY, z=6)
    # screen and gates
    line(dx_, [(BAY[0], BAY[3]), (BAY[0], BAY[1])], color=EARTH, lw=2.0, z=6)
    gw = bw / 2
    for hxg, sgn in ((BAY[0], 1), (BAY[2], -1)):
        door(dx_, (hxg, BAY[3]), gw, 0 if sgn > 0 else 180, 75 * sgn, color=EARTH)
    if not BAY_OK:
        rect(dx_, m.TRASH[0], m.TRASH[1], m.TRASH[2], m.TRASH[3], fc="none", ec=ACCENT, lw=0.9, ls=(0, (3, 2)), z=7)
        lead(dx_, (m.TRASH[0], m.TRASH[3] - 0.3), (BAY[0] + 1.6, BAY[3] + 4.7),
             f"red dashed = bay in the model,\n{ftin(m.TRASH[2] - m.TRASH[0])} x {ftin(m.TRASH[3] - m.TRASH[1])}: too small", size=4.4, color=ACCENT, ha="center")
    dimb(dx_, (BAY[0], BAY[1]), (BAY[2], BAY[1]), -1.25, f"{ftin(bw)} INSIDE", size=4.6, side=-1)
    dimb(dx_, (BAY[2], BAY[1]), (BAY[2], BAY[3]), -1.5, ftin(bd), size=4.6, side=-1)
    txt(dx_, (BAY[0] + BAY[2]) / 2 + 1.0, BAY[3] + 3.3, f"ENTRY LANDING  EL {m.EL_GAR:.1f}", size=4.8, weight="bold")
    txt(dx_, (BAY[0] + BAY[2]) / 2 + 1.0, BAY[3] + 2.6, "two gates swing onto the landing", size=4.4, color=EARTH)
    txt(dx_, dv[0] + 0.2, 2.4, "APRON", size=4.6, ha="left", color=GREY)
    y = ytop - 0.34 - hd - 0.08
    y = block(bg, xr, y, wr, None, [
        "Floor: 4 in. concrete, level with the landing, falling 1/8 in./ft to the gates. Screen: 6 ft solid board or "
        "composite panels on steel posts, on the west side and on top of the low wall (south and east). Two framed gates "
        "with a drop rod, hasp and padlock. Carts roll north along the landing to the flush end at the opening, then down the apron."
        + ("" if BAY_OK else f" THE MODEL'S BAY ({ftin(m.TRASH[2] - m.TRASH[0])} x {ftin(m.TRASH[3] - m.TRASH[1])}) DOES NOT HOLD FOUR "
           f"26 x 34 in. CARTS: {ftin(BAY_NEED[0])} x {ftin(BAY_NEED[1])} is needed and is drawn here; the landing loses "
           f"{(BAY[3] - m.TRASH[3]) * 12:.0f} in. of depth. Smaller 64 gal carts (24 x 27 in.) would fit the bay as modelled."),
    ], fs=5.0, hang="")
    # west wall elevation
    bg.text(xr, y - 0.02, f"WEST WING WALL: ELEVATION FROM THE APRON  (3/16\" = 1'-0\")", fontsize=6.6, fontweight="bold", va="top")
    ts = np.linspace(0, 1, 21)
    ex_ = [_wall_w(t)[1] for t in ts]
    ap_ = [_wall_w(t)[2] for t in ts]
    wv = (-4.6, min(ap_) - 4.2, Lw + 6.2, max(ex_) + 1.6)
    hw_in = (wv[3] - wv[1]) / FPI
    wx = plan_axes(fig, xr, y - 0.22 - hw_in, (wv[0], wv[2]), (wv[1], wv[3]), FPI)
    S_ = [t * Lw for t in ts]
    top_ = [e + 0.5 for e in ex_]
    bot_ = [a - 3.0 for a in ap_]
    poly(wx, list(zip(S_, top_)) + list(zip(S_[::-1], bot_[::-1])), fc="#e4e6e9", ec=INK, lw=0.6, z=3)
    line(wx, list(zip(S_, ex_)), color=EARTH, lw=0.7, ls=(0, (4, 2)), z=5)
    line(wx, [(wv[0], ap_[0])] + list(zip(S_, ap_)) + [(wv[2], ap_[-1] + (ap_[-1] - ap_[0]) / Lw * (wv[2] - Lw))], color=BLUE, lw=1.1, z=6)
    rect(wx, wv[0] + 2.8, ap_[0] - 3.0, 0, max(ex_) + 1.6, fc=CONC, ec=INK, lw=0.5, z=4)
    txt(wx, wv[0] + 3.7, ap_[0] + 4.2, "garage\nreturn pier", size=4.2, rot=90)
    dimb(wx, (0.9, ap_[0]), (0.9, ex_[0]), 0, ftin(hw0), ext=False, size=4.6, side=-1)
    dimb(wx, (Lw - 0.7, ap_[-1]), (Lw - 0.7, ex_[-1]), 0, ftin(hw1), ext=False, size=4.6)
    dimb(wx, (0, bot_[0] - 0.2), (Lw, bot_[0] - 0.2), -0.7, f"{ftin(Lw)} LONG", ext=False, size=4.6, side=-1)
    line(wx, [(Lw + 1.2, wv[1] + 0.6), (Lw + 1.2, wv[3])], color=ACCENT, lw=0.8, ls=(0, (9, 2.5, 1.5, 2.5)), z=6)
    txt(wx, Lw + 1.5, wv[3] - 0.8, "LOT LINE\n6 in. past the wall", size=4.2, color=ACCENT, ha="left", va="top")
    txt(wx, Lw * 0.5, (ex_[10] + ap_[10]) / 2, f"front yard behind:\nEL {ex_[0]:.1f} to {ex_[-1]:.1f}", size=4.4, color=EARTH, z=7)
    txt(wx, Lw + 1.5, ap_[-1] - 0.9, f"apron EL {ap_[0]:.1f}\nto {ap_[-1]:.1f}", size=4.4, color=BLUE, ha="left", va="top")
    txt(wx, Lw * 0.5, bot_[10] + 0.9, "footing 36 in. below the apron", size=4.2, color=GREY, z=7)
    # east wall elevation
    y2 = y - 0.22 - hw_in - 0.16
    bg.text(xr, y2, "LOW WALL ROUND THE BAY AND LANDING: DEVELOPED ELEVATION  (3/16\")", fontsize=6.6, fontweight="bold", va="top")
    ss = np.linspace(0, Le, 31)
    ge_ = [_wall_e(s_)[1] for s_ in ss]
    ev = (-1.4, m.EL_GAR - 3.9, Le + 1.4, max(ge_) + 2.3)
    he_in = (ev[3] - ev[1]) / FPI
    exx = plan_axes(fig, xr, y2 - 0.2 - he_in, (ev[0], ev[2]), (ev[1], ev[3]), FPI)
    poly(exx, [(s_, max(g_, m.EL_GAR) + 0.5) for s_, g_ in zip(ss, ge_)] + [(Le, m.EL_GAR - 3.0), (0, m.EL_GAR - 3.0)], fc="#e4e6e9", ec=INK, lw=0.6, z=3)
    line(exx, list(zip(ss, ge_)), color=EARTH, lw=0.7, ls=(0, (4, 2)), z=5)
    line(exx, [(0, m.EL_GAR), (Le, m.EL_GAR)], color=BLUE, lw=1.1, z=6)
    line(exx, [(L1, ev[1] + 0.3), (L1, ev[3] - 0.2)], color=GREY, lw=0.4, ls=(0, (2, 2)), z=6)
    txt(exx, L1 / 2, ev[3] - 0.5, f"SOUTH LEG {ftin(L1)}", size=4.4, weight="bold")
    txt(exx, L1 + (Le - L1) / 2, ev[3] - 0.5, f"EAST LEG {ftin(Le - L1)}", size=4.4, weight="bold")
    for s_, sd in ((0.6, -1), (L1 - 0.7, 1), (Le - 0.6, 1)):
        h_ = _wall_e(s_)[1] - m.EL_GAR
        dimb(exx, (s_, m.EL_GAR), (s_, m.EL_GAR + h_), 0, ftin(h_), ext=False, size=4.4, side=sd)
    txt(exx, L1 / 2, m.EL_GAR - 0.7, f"bay floor and landing EL {m.EL_GAR:.1f}", size=4.4, color=BLUE, z=7)
    txt(exx, L1 + (Le - L1) / 2, m.EL_GAR - 1.9, "footing 36 in. down", size=4.2, color=GREY, z=7)
    block(bg, xr, y2 - 0.2 - he_in - 0.06, wr, None, [
        "Dashed brown = existing ground outside the wall (LiDAR). Heights are ground minus the finish surface inside; the survey "
        "will change them. The 6 ft trash screen stands on the south leg and the first part of the east leg.",
    ], fs=5.0, hang="")
    save(fig, "C-107", pdf)


SHEETS = [
    ("C-101", sheet_c101),
    ("C-102", sheet_c102),
    ("C-103", sheet_c103),
    ("C-104", sheet_c104),
    ("C-105", sheet_c105),
    ("C-106", sheet_c106),
    ("C-107", sheet_c107),
]
