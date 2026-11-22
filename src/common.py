"""Shared geometry, site data and drafting helpers for the 387 Baird St concept set.

Plan coordinates are FEET. Origin = south-west front lot corner.
+X runs east along the Baird Street front lot line, +Y runs north into the lot.
"""
import json
import math
import os

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Arc, Polygon as MPoly, Rectangle
from PIL import Image
from pyproj import Transformer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
FT = 0.3048006096  # metres per US survey foot

for f in font_manager.findSystemFonts():
    if "Inter" in os.path.basename(f) and "Display" not in f:
        font_manager.fontManager.addfont(f)
plt.rcParams["font.family"] = ["Inter", "DejaVu Sans"]
plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["hatch.linewidth"] = 0.4

INK = "#111418"
GREY = "#6b7178"
LIGHT = "#c9cdd2"
PALE = "#eef0f2"
ACCENT = "#b3261e"   # property line / zoning limits
BLUE = "#1f5fa8"     # proposed work call-outs
EARTH = "#8a6f52"
PAPER = "#ffffff"

# ----------------------------------------------------------------------------
# Site data (public GIS) -> plan coordinates
# ----------------------------------------------------------------------------
_T = Transformer.from_crs(4326, 26917, always_xy=True)
_parcels = json.load(open(os.path.join(DATA, "parcels_wgs84.json")))["features"]
SUBJECT_ID = "31130029008400000000"
_subj = [f for f in _parcels if f["attributes"]["CleanParcelID"] == SUBJECT_ID][0]
_ring = [_T.transform(x, y) for x, y in _subj["geometry"]["rings"][0]]
_SE = np.array(_ring[1])
_SW = np.array(_ring[4])
_ex = (_SE - _SW) / np.hypot(*(_SE - _SW))
_ey = np.array([-_ex[1], _ex[0]])
Y_AXIS_AZIMUTH = math.degrees(math.atan2(_ey[0], _ey[1]))  # deg east of true north


def to_site(E, N):
    v = (np.array([E, N]) - _SW) / FT
    return float(v @ _ex), float(v @ _ey)


def to_utm(X, Y):
    return _SW + (X * _ex + Y * _ey) * FT


_bd = [float(v) for v in open(os.path.join(DATA, "lidar_dem_bbox_utm17n.txt")).read().strip().split(",")]
_z = np.array(Image.open(os.path.join(DATA, "lidar_dem_1m_utm17n.tif"))).astype(float) / FT


def elev(X, Y):
    """Existing ground elevation (ft, NAVD88) from the 1 m state LiDAR DEM."""
    E, N = to_utm(X, Y)
    c = (E - _bd[0]) - 0.5
    r = (_bd[3] - N) - 0.5
    c0, r0 = int(math.floor(c)), int(math.floor(r))
    fx, fy = c - c0, r - r0
    z = _z
    return float(z[r0, c0] * (1 - fx) * (1 - fy) + z[r0, c0 + 1] * fx * (1 - fy)
                 + z[r0 + 1, c0] * (1 - fx) * fy + z[r0 + 1, c0 + 1] * fx * fy)


def elev_grid(x0, x1, y0, y1, step=1.0):
    xs = np.arange(x0, x1 + step, step)
    ys = np.arange(y0, y1 + step, step)
    Z = np.array([[elev(x, y) for x in xs] for y in ys])
    return xs, ys, Z


def neighbour_parcels():
    out = []
    for f in _parcels:
        a = f["attributes"]
        ring = [to_site(*_T.transform(x, y)) for x, y in f["geometry"]["rings"][0]]
        out.append(dict(id=a["CleanParcelID"], label=a["Label"], addr=a["FullPhysicalAddress"] or "", ring=ring))
    return out


def building_footprints():
    fp = json.load(open(os.path.join(DATA, "building_footprints_wgs84.json")))["features"]
    return [[to_site(*_T.transform(x, y)) for x, y in f["geometry"]["rings"][0]] for f in fp]


# ----------------------------------------------------------------------------
# Record lot (county tax map 09-0029 dimensions: 50' front, 34' east, 48' west)
# ----------------------------------------------------------------------------
WEST_LEAN = math.radians(6.5)          # west line leans east going north (from GIS bearings)
LOT_SW = (0.0, 0.0)
LOT_SE = (50.0, 0.0)
LOT_NE = (50.0, 34.0)
LOT_NW = (48.0 * math.sin(WEST_LEAN), 48.0 * math.cos(WEST_LEAN))
LOT = [LOT_SW, LOT_SE, LOT_NE, LOT_NW]
REAR_SLOPE = (LOT_NE[1] - LOT_NW[1]) / (LOT_NE[0] - LOT_NW[0])


def rear_y(x):
    return LOT_NW[1] + REAR_SLOPE * (x - LOT_NW[0])


def west_x(y):
    return y * math.tan(WEST_LEAN)


def poly_area(pts):
    return abs(sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
                   for i in range(len(pts)))) / 2


LOT_AREA_CALC = poly_area(LOT)
LOT_AREA_DEED = 0.0471 * 43560

# R-2 district standards (Morgantown P&Z Code Art. 1337)
SB_FRONT, SB_SIDE, SB_REAR = 10.0, 5.0, 20.0
_cr = math.cos(math.atan(abs(REAR_SLOPE)))


def rear_setback_y(x, d=SB_REAR):
    return rear_y(x) - d / _cr


def west_setback_x(y, d=SB_SIDE):
    return west_x(y) + d / math.cos(WEST_LEAN)


def byright_envelope():
    a = (west_setback_x(SB_FRONT), SB_FRONT)
    b = (50 - SB_SIDE, SB_FRONT)
    c = (50 - SB_SIDE, rear_setback_y(50 - SB_SIDE))
    t = math.tan(WEST_LEAN)
    k = SB_SIDE / math.cos(WEST_LEAN)
    y0 = LOT_NW[1] - REAR_SLOPE * LOT_NW[0] - SB_REAR / _cr
    y = (y0 + REAR_SLOPE * k) / (1 - REAR_SLOPE * t)
    d = (t * y + k, y)
    return [a, b, c, d]


# ----------------------------------------------------------------------------
# Proposed concept, Rev B: two-family dwelling (stacked flats) over a 3-car garage
# ----------------------------------------------------------------------------
BX0, BX1, BY0, BY1 = 9.5, 45.0, 8.0, 30.0       # main block, 35'-6" x 22'-0"
WX1, WY1 = 28.5, 35.0                           # rear wing (west 19'-0"), 5'-0" deeper
OUT = [(BX0, BY0), (BX1, BY0), (BX1, BY1), (WX1, BY1), (WX1, WY1), (BX0, WY1)]
IN_L = [(10.5, 8.67), (44.0, 8.67), (44.0, 29.0), (27.5, 29.0), (27.5, 34.0), (10.5, 34.0)]   # inside of concrete
IN_U = [(10.0, 8.5), (44.5, 8.5), (44.5, 29.5), (28.0, 29.5), (28.0, 34.5), (10.0, 34.5)]     # inside of 2x6 walls
FOOTPRINT = (BX1 - BX0) * (BY1 - BY0) + (WX1 - BX0) * (WY1 - BY1)
EL_GAR, EL_MAIN, EL_UP = 914.5, 925.5, 935.5    # finished floors (11'-0" and 10'-0" floor to floor)
EL_PLATE = EL_UP + 8.1
EL_RIDGE = EL_PLATE + (BY1 - BY0) / 2 * 0.5      # 6:12 gable, ridge parallel to street
EL_MEAN_ROOF = (EL_PLATE + EL_RIDGE) / 2
EL_REF = (914.5 + 927.0) / 2                     # mid-point of lowest/highest grade at footprint
PAVE_N, PAVE_S = -7.0, -21.0                     # approx. pavement edges (LiDAR profile)
# garage level
STALLS = [(10.5, 19.39), (19.39, 28.28), (28.28, 37.17)]
DOOR_A = (11.4, 27.4)                            # 16'-0" x 8'-0" overhead door, stalls 1-2
DOOR_B = (28.9, 36.9)                            # 8'-0" x 8'-0" overhead door, stall 3
ENTRY = (40.9, 43.9)                             # 3'-0" common entry door
SHAFT_L = (37.5, 44.0, 8.67, 22.3)               # stair shaft, lower level (x0, x1, y0, y1)
SHAFT_U = (37.5, 44.5, 8.5, 22.2)                # stair shaft, unit levels
STORE_Y = 28.0                                   # south face of conditioned storage room partition
APRON = [(DOOR_A[0], BY0), (DOOR_B[1], BY0), (37.7, PAVE_N), (10.6, PAVE_N)]
REV = "B"


def street_el(x):
    """Approx. pavement elevation opposite plan station x (LiDAR, ~11.4 % grade)."""
    return 916.9 - 0.114 * x


def perp_to_rear(x, y):
    return (rear_y(x) - y) * _cr


def perp_to_west(x, y):
    return (x - west_x(y)) * math.cos(WEST_LEAN)


# ----------------------------------------------------------------------------
# Drafting helpers
# ----------------------------------------------------------------------------
SHEET_W, SHEET_H = 17.0, 11.0
TB_W = 2.9
MARGIN = 0.35
PROJECT = "387 BAIRD STREET"
ISSUE = "REV B · HEAD-START SET · 22 NOV 2026"


def ftin(v, zero_in=True):
    sign = "-" if v < 0 else ""
    v = abs(v)
    total = round(v * 12)
    f, i = divmod(total, 12)
    if i == 0 and not zero_in:
        return f"{sign}{f}'"
    return f"{sign}{f}'-{i}\""


def new_sheet(number, title, scale_txt, notes=None):
    fig = plt.figure(figsize=(SHEET_W, SHEET_H), facecolor=PAPER)
    bg = fig.add_axes([0, 0, 1, 1])
    bg.set_xlim(0, SHEET_W)
    bg.set_ylim(0, SHEET_H)
    bg.axis("off")
    bg.add_patch(Rectangle((MARGIN, MARGIN), SHEET_W - 2 * MARGIN, SHEET_H - 2 * MARGIN, fill=False, lw=1.6, ec=INK))
    x0 = SHEET_W - MARGIN - TB_W
    bg.plot([x0, x0], [MARGIN, SHEET_H - MARGIN], color=INK, lw=1.0)
    tx = x0 + 0.16
    top = SHEET_H - MARGIN
    bg.text(tx, top - 0.38, PROJECT, fontsize=15, fontweight="bold", color=INK, va="center")
    bg.text(tx, top - 0.66, "MORGANTOWN, WV 26505", fontsize=8.5, color=INK, va="center")
    bg.text(tx, top - 0.88, "Tax Dist. 13 · Map 29 · Parcel 84", fontsize=7.5, color=GREY, va="center")
    bg.plot([x0, SHEET_W - MARGIN], [top - 1.08, top - 1.08], color=INK, lw=0.6)
    bg.text(tx, top - 1.30, "TWO-FAMILY DWELLING OVER", fontsize=7.6, color=INK, va="center")
    bg.text(tx, top - 1.48, "3-CAR GARAGE + OWNER STORAGE", fontsize=7.6, color=INK, va="center")
    bg.plot([x0, SHEET_W - MARGIN], [top - 1.68, top - 1.68], color=INK, lw=0.6)
    # notes
    y = top - 1.95
    if notes:
        for head, lines in notes:
            bg.text(tx, y, head.upper(), fontsize=7.2, fontweight="bold", color=INK, va="top")
            y -= 0.19
            for ln in lines:
                bg.text(tx, y, ln, fontsize=6.6, color=INK, va="top", linespacing=1.25)
                y -= 0.148 * (ln.count("\n") + 1) + 0.035
            y -= 0.12
    # stamp + sheet id
    by = MARGIN
    bg.plot([x0, SHEET_W - MARGIN], [by + 2.55, by + 2.55], color=INK, lw=0.6)
    bg.add_patch(Rectangle((x0 + 0.12, by + 1.52), TB_W - 0.24, 0.92, fill=False, ec=ACCENT, lw=1.1))
    bg.text(x0 + TB_W / 2, by + 2.12, "PRELIMINARY · NOT FOR CONSTRUCTION", fontsize=7.2, fontweight="bold",
            color=ACCENT, ha="center", va="center")
    bg.text(x0 + TB_W / 2, by + 1.80,
            "Head-start draft, not engineered. No licence, survey,\nsoil report or site visit behind it. For review and\nredesign by the licensed professionals of record.",
            fontsize=5.6, color=ACCENT, ha="center", va="center", linespacing=1.25)
    bg.plot([x0, SHEET_W - MARGIN], [by + 1.40, by + 1.40], color=INK, lw=0.6)
    bg.text(tx, by + 1.22, "SHEET TITLE", fontsize=5.6, color=GREY, va="center")
    bg.text(tx, by + 0.98, title.upper(), fontsize=9.6, fontweight="bold", color=INK, va="center")
    bg.text(tx, by + 0.72, f"SCALE  {scale_txt}", fontsize=6.6, color=INK, va="center")
    bg.text(tx, by + 0.54, "(when printed at 11 x 17 in, 100 %)", fontsize=5.6, color=GREY, va="center")
    bg.text(tx, by + 0.30, ISSUE, fontsize=6.2, color=GREY, va="center")
    bg.text(SHEET_W - MARGIN - 0.14, by + 0.42, number, fontsize=21, fontweight="bold", color=INK, ha="right", va="center")
    return fig, bg


def plan_axes(fig, left_in, bottom_in, xlim, ylim, ft_per_in):
    w = (xlim[1] - xlim[0]) / ft_per_in
    h = (ylim[1] - ylim[0]) / ft_per_in
    ax = fig.add_axes([left_in / SHEET_W, bottom_in / SHEET_H, w / SHEET_W, h / SHEET_H])
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.fpi = ft_per_in
    return ax


def poly(ax, pts, fc="none", ec=INK, lw=0.8, z=3, **kw):
    p = MPoly(pts, closed=True, fc=fc, ec=ec, lw=lw, zorder=z, **kw)
    ax.add_patch(p)
    return p


def rect(ax, x0, y0, x1, y1, **kw):
    return poly(ax, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], **kw)


def line(ax, pts, color=INK, lw=0.8, ls="-", z=4, **kw):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=color, lw=lw, ls=ls, zorder=z, solid_capstyle="butt", **kw)


def txt(ax, x, y, s, size=6.5, color=INK, ha="center", va="center", weight="normal", rot=0, z=9, box=False, **kw):
    bbox = dict(fc=PAPER, ec="none", pad=0.8) if box else None
    return ax.text(x, y, s, fontsize=size, color=color, ha=ha, va=va, fontweight=weight, rotation=rot,
                   zorder=z, bbox=bbox, linespacing=1.2, **kw)


def dim(ax, p0, p1, off, label=None, size=6.0, color=INK, tick=None, ext=True, side=1):
    """Dimension string between p0 and p1, offset `off` ft to the left of the p0->p1 direction."""
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -uy, ux
    fpi = getattr(ax, "fpi", 5.333)
    tick = 0.075 * fpi if tick is None else tick
    toff = 0.085 * fpi
    a = (x0 + nx * off, y0 + ny * off)
    b = (x1 + nx * off, y1 + ny * off)
    line(ax, [a, b], color=color, lw=0.45, z=8)
    for (px, py), (qx, qy) in ((p0, a), (p1, b)):
        if ext:
            s = (0.06 if off > 0 else -0.06) * fpi
            line(ax, [(px + nx * s, py + ny * s), (qx + nx * s * 0.9, qy + ny * s * 0.9)], color=color, lw=0.3, z=8)
        line(ax, [(qx - (ux + nx) * tick / 2, qy - (uy + ny) * tick / 2),
                  (qx + (ux + nx) * tick / 2, qy + (uy + ny) * tick / 2)], color=color, lw=0.9, z=8)
    ang = math.degrees(math.atan2(uy, ux))
    if ang > 90 or ang <= -90:
        ang += 180
    mx, my = (a[0] + b[0]) / 2 + nx * toff * side, (a[1] + b[1]) / 2 + ny * toff * side
    txt(ax, mx, my, label if label is not None else ftin(L), size=size, color=color, rot=ang)


def door(ax, hinge, width, ang0, sweep=90, lw=0.7, color=INK):
    """Door leaf from hinge at angle ang0+sweep, with swing arc from ang0."""
    hx, hy = hinge
    a1 = math.radians(ang0 + sweep)
    line(ax, [(hx, hy), (hx + width * math.cos(a1), hy + width * math.sin(a1))], lw=lw + 0.3, color=color, z=7)
    t1, t2 = (ang0, ang0 + sweep) if sweep > 0 else (ang0 + sweep, ang0)
    ax.add_patch(Arc((hx, hy), 2 * width, 2 * width, theta1=t1, theta2=t2, lw=0.4, color=color, zorder=7))


def opening(ax, x0, y0, x1, y1):
    rect(ax, x0, y0, x1, y1, fc=PAPER, ec="none", z=5)


def window_h(ax, x0, x1, y0, y1):
    """Window in a horizontal (E-W) wall occupying y0..y1."""
    opening(ax, x0, y0, x1, y1)
    for y in (y0, (y0 + y1) / 2, y1):
        line(ax, [(x0, y), (x1, y)], lw=0.5, z=6)
    for x in (x0, x1):
        line(ax, [(x, y0), (x, y1)], lw=0.8, z=6)


def window_v(ax, y0, y1, x0, x1):
    opening(ax, x0, y0, x1, y1)
    for x in (x0, (x0 + x1) / 2, x1):
        line(ax, [(x, y0), (x, y1)], lw=0.5, z=6)
    for y in (y0, y1):
        line(ax, [(x0, y), (x1, y)], lw=0.8, z=6)


def north_arrow(ax, x, y, r=3.0, label_size=7):
    """True north: +Y axis bears Y_AXIS_AZIMUTH deg east of north."""
    a = math.radians(90 + Y_AXIS_AZIMUTH)
    dx, dy = math.cos(a), math.sin(a)
    px, py = -dy, dx
    ax.add_patch(plt.Circle((x, y), r, fill=False, lw=0.6, ec=INK, zorder=9))
    tip = (x + dx * r * 0.92, y + dy * r * 0.92)
    tail = (x - dx * r * 0.7, y - dy * r * 0.7)
    poly(ax, [tip, (tail[0] + px * r * 0.42, tail[1] + py * r * 0.42), (x - dx * r * 0.25, y - dy * r * 0.25)], fc=INK, lw=0.4, z=9)
    poly(ax, [tip, (tail[0] - px * r * 0.42, tail[1] - py * r * 0.42), (x - dx * r * 0.25, y - dy * r * 0.25)], fc=PAPER, lw=0.4, z=9)
    txt(ax, x + dx * (r + 1.3 * r / 3), y + dy * (r + 1.3 * r / 3), "N", size=label_size, weight="bold")


def scale_bar(ax, x, y, total=20, step=5, h=0.6, size=5.8, unit="ft"):
    n = int(total / step)
    for i in range(n):
        rect(ax, x + i * step, y, x + (i + 1) * step, y + h, fc=INK if i % 2 == 0 else PAPER, ec=INK, lw=0.5, z=9)
        txt(ax, x + i * step, y - h * 1.3, f"{i * step}", size=size)
    txt(ax, x + total, y - h * 1.3, f"{total} {unit}", size=size)


def view_title(ax, x, y, tag, title, scale_txt, size=8.5):
    txt(ax, x, y, title.upper(), size=size, weight="bold", ha="left", va="bottom")
    txt(ax, x, y - 0.25, scale_txt, size=size - 2.8, color=GREY, ha="left", va="top")


def save(fig, number, pdf):
    png = os.path.join(ROOT, "drawings", "png", f"{number}.png")
    fig.savefig(png, dpi=200, facecolor=PAPER)
    pdf.savefig(fig, facecolor=PAPER)
    plt.close(fig)
