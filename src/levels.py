"""Base floor plans (Rev B). `mode="arch"` draws the full architectural plan; `mode="bg"` draws a
muted background for structural / plumbing / mechanical / electrical overlays."""
import math

import numpy as np
from matplotlib.patches import Ellipse, FancyBboxPatch

from common import *  # noqa: F401,F403

FPI = 16 / 3.0          # 3/16" = 1'-0"
VIEW_X = (-5, 55)
VIEW_Y = (-10.5, 38.5)
POCHE = "#1b1e22"
CONC = "#a9aeb4"
FURN = "#8d949c"
WOOD = "#f4f1ea"
BG_WALL = "#d3d7dc"
BG_EDGE = "#9aa1a9"
RATED = "#b3261e"


class Style:
    def __init__(self, mode):
        self.bg = mode == "bg"
        self.frame = BG_WALL if self.bg else POCHE
        self.conc = BG_WALL if self.bg else CONC
        self.edge = BG_EDGE if self.bg else INK
        self.furn = "#c3c8ce" if self.bg else FURN
        self.text = "#8a9199" if self.bg else INK


def plan_frame(fig, title, sub, street=True, north=True):
    left = MARGIN + (SHEET_W - 2 * MARGIN - TB_W - (VIEW_X[1] - VIEW_X[0]) / FPI) / 2
    ax = plan_axes(fig, left, 0.72, VIEW_X, VIEW_Y, FPI)
    line(ax, [LOT_NW, LOT_SW, LOT_SE, LOT_NE, LOT_NW], color=ACCENT, lw=1.0, ls=(0, (9, 2.5, 1.5, 2.5)), z=2)
    txt(ax, 51.2, 14.0, "LOT LINE", size=5.0, color=ACCENT, rot=90)
    txt(ax, 46.0, -1.0, "FRONT LOT LINE = R.O.W. LINE", size=5.0, color=ACCENT)
    if street:
        line(ax, [(VIEW_X[0], PAVE_N), (VIEW_X[1], PAVE_N)], color=GREY, lw=0.6, z=2)
        rect(ax, VIEW_X[0], VIEW_Y[0], VIEW_X[1], PAVE_N, fc="#e6e8eb", ec="none", z=1)
        txt(ax, 46.5, -8.9, "BAIRD STREET  (±14' pavement)", size=6.0, color=GREY, weight="bold")
    if north:
        north_arrow(ax, 51.6, 34.2, 1.8, 6.5)
    scale_bar(ax, -3.5, -9.6, 16, 4, 0.42, size=5.2)
    view_title(ax, -4.4, 36.6, "1", title, sub, 9)
    return ax


def wall(ax, x0, y0, x1, y1, st, fc=None, z=5):
    rect(ax, x0, y0, x1, y1, fc=fc or st.frame, ec=st.edge, lw=0.4, z=z)


def car(ax, x0, y0, w=6.3, l=16.5, label=None, color=FURN):
    ax.add_patch(FancyBboxPatch((x0 + 0.5, y0 + 0.5), w - 1, l - 1, boxstyle="round,pad=0.5,rounding_size=1.1",
                                fc="#f2f3f5", ec=color, lw=0.6, zorder=6))
    rect(ax, x0 + 0.7, y0 + 3.4, x0 + w - 0.7, y0 + 5.2, fc="none", ec=color, lw=0.4, z=6)
    rect(ax, x0 + 0.7, y0 + l - 5.6, x0 + w - 0.7, y0 + l - 3.6, fc="none", ec=color, lw=0.4, z=6)
    if label:
        txt(ax, x0 + w / 2, y0 + l / 2, label, size=5.4, color=GREY)


def u_stair(ax, shaft, st, n=8, tread=10 / 12, up=True, dn=True, gap=0.3):
    """Switchback stair in shaft (x0, x1, y0, y1). Floor landing at the south end, mid landing at the north."""
    x0, x1, y0, y1 = shaft
    w = (x1 - x0 - gap) / 2
    ys = y0 + 3.25
    ye = ys + n * tread
    for i in range(n + 1):
        y = ys + i * tread
        line(ax, [(x0, y), (x0 + w, y)], lw=0.35, color=st.edge, z=6)
        line(ax, [(x1 - w, y), (x1, y)], lw=0.35, color=st.edge, z=6)
    rect(ax, x0 + w, ys, x1 - w, ye, fc=PAPER, ec=st.edge, lw=0.5, z=6)
    if st.bg:
        return
    arrow = dict(arrowstyle="-|>", lw=0.6, color=INK)
    if up:
        ax.annotate("", xy=(x1 - w / 2, ye - 0.4), xytext=(x1 - w / 2, ys + 0.2), arrowprops=arrow, zorder=8)
        txt(ax, x1 - w / 2, ys - 0.55, "UP", size=5.0, weight="bold")
    if dn:
        ax.annotate("", xy=(x0 + w / 2, ye - 0.4), xytext=(x0 + w / 2, ys + 0.2), arrowprops=arrow, zorder=8)
        txt(ax, x0 + w / 2, ys - 0.55, "DN", size=5.0, weight="bold")


def wc(ax, x, y, st, facing="S"):
    """Water closet; (x, y) is the centre of the tank's wall side, `facing` is the direction the bowl points."""
    c = st.furn
    dx, dy = {"N": (0, 1), "S": (0, -1), "E": (1, 0), "W": (-1, 0)}[facing]
    if dx == 0:
        rect(ax, x - 0.8, min(y, y + 0.65 * dy), x + 0.8, max(y, y + 0.65 * dy), fc=PAPER, ec=c, lw=0.5, z=6)
        ax.add_patch(Ellipse((x, y + 1.55 * dy), 1.3, 1.8, fc=PAPER, ec=c, lw=0.5, zorder=6))
    else:
        rect(ax, min(x, x + 0.65 * dx), y - 0.8, max(x, x + 0.65 * dx), y + 0.8, fc=PAPER, ec=c, lw=0.5, z=6)
        ax.add_patch(Ellipse((x + 1.55 * dx, y), 1.8, 1.3, fc=PAPER, ec=c, lw=0.5, zorder=6))


def lav(ax, x0, y0, x1, y1, st):
    rect(ax, x0, y0, x1, y1, fc=PAPER, ec=st.furn, lw=0.5, z=6)
    ax.add_patch(Ellipse(((x0 + x1) / 2, (y0 + y1) / 2), min(1.4, (x1 - x0) * 0.6), min(1.1, (y1 - y0) * 0.6),
                         fc=PAPER, ec=st.furn, lw=0.5, zorder=6))


def room(ax, x, y, name, size=None, extra=None, fs=6.4, st=None):
    if st is not None and st.bg:
        txt(ax, x, y, name, size=4.6, color=st.text, z=4)
        return
    txt(ax, x, y, name, size=fs, weight="bold", z=9, box=True)
    if size:
        txt(ax, x, y - 1.05, size, size=5.3, z=9, box=True)
    if extra:
        txt(ax, x, y - 2.0, extra, size=4.9, color=GREY, z=9, box=True)


# ----------------------------------------------------------------------------
def lower_plan(ax, mode="arch", cars=True):
    """Garage level: open front, three stalls, lobby + stair, small utility closet. No storage room."""
    st = Style(mode)
    poly(ax, OUT_L, fc=st.conc, ec=st.edge, lw=0.9, z=3)
    poly(ax, IN_L, fc=PAPER, ec=st.edge, lw=0.6, z=4)
    for a, b in (DOOR_A, DOOR_B):                         # open bays, no doors
        opening(ax, a, BY0 - 0.02, b, BY0 + 0.69)
        line(ax, [(a, BY0), (b, BY0)], lw=0.5, ls=(0, (2, 3)), z=7, color=st.edge)
    rect(ax, DOOR_A[1], BY0 + 0.08, DOOR_B[0], BY0 + 0.58, fc=st.conc if st.bg else "#1f5fa8", ec=st.edge, lw=0.4, z=7)   # centre post
    opening(ax, ENTRY[0], BY0 - 0.02, ENTRY[1], BY0 + 0.69)
    door(ax, (ENTRY[0], BY0 + 0.67), 3.0, 0, 90, color=st.edge)
    x0, x1, y0, y1 = SHAFT_L
    wall(ax, x0 - 0.33, y0, x0, 29.0, st, fc=st.conc)
    wall(ax, x0, y1, x1, y1 + 0.33, st, fc=st.conc)
    opening(ax, x0 - 0.35, 9.3, x0 + 0.02, 12.3)          # lobby <-> garage (20-min, tenant key)
    door(ax, (x0 - 0.33, 9.3), 3.0, 90, 90, color=st.edge)
    opening(ax, x0 - 0.35, 24.0, x0 + 0.02, 27.0)         # utility / bike closet
    door(ax, (x0 - 0.33, 27.0), 3.0, 180, 90, color=st.edge)
    u_stair(ax, SHAFT_L, st, n=8, dn=False)
    if cars:
        for i, cx in enumerate(CARS):
            car(ax, cx - 0.05, 10.4, w=6.3, label=None, color=st.furn)
        for a, b in STALLS[:-1]:
            line(ax, [(b, 9.0), (b, 27.4)], lw=0.9 if not st.bg else 0.5, color="#c9a400" if not st.bg else st.furn, z=5)
    if st.bg:
        room(ax, 23.8, 24.5, "OPEN GARAGE", st=st)
        room(ax, 40.8, 10.3, "LOBBY", st=st)
        room(ax, 40.8, 25.4, "UTILITY", st=st)
        return st
    for i, (a, b) in enumerate(STALLS):
        txt(ax, (a + b) / 2 + (0.6 if i == 0 else 0), 18.7, f"{i + 1}", size=11, weight="bold", color="#c9a400", z=7)
    room(ax, 23.8, 27.9, "OPEN 3-CAR GARAGE", None, fs=6.2)
    txt(ax, 40.75, 10.2, "LOBBY", size=5.2, weight="bold")
    txt(ax, 40.75, 25.6, "BIKES /\nUTILITY", size=5.0, weight="bold")
    return st


# ----------------------------------------------------------------------------
def shower(ax, x0, y0, x1, y1, st):
    rect(ax, x0, y0, x1, y1, fc=PAPER, ec=st.furn, lw=0.6, z=6)
    line(ax, [(x0, y0), (x1, y1)], lw=0.3, color=st.furn, z=6)
    line(ax, [(x0, y1), (x1, y0)], lw=0.3, color=st.furn, z=6)


def tub(ax, x0, y0, x1, y1, st):
    rect(ax, x0, y0, x1, y1, fc=PAPER, ec=st.furn, lw=0.7, z=6)
    ax.add_patch(FancyBboxPatch((x0 + 0.35, y0 + 0.35), (x1 - x0) - 0.7, (y1 - y0) - 0.7, boxstyle="round,pad=0.1,rounding_size=0.5",
                                fc=PAPER, ec=st.furn, lw=0.5, zorder=6))


def pocket(ax, x0, y0, x1, y1, st):
    """Pocket / sliding door shown as an opening with a thin leaf."""
    opening(ax, x0, y0, x1, y1)
    if x1 - x0 < y1 - y0:
        xm = (x0 + x1) / 2
        line(ax, [(xm, y0), (xm, (y0 + y1) / 2 + 0.3)], lw=0.9, color=st.edge, z=7)
    else:
        ym = (y0 + y1) / 2
        line(ax, [(x0, ym), ((x0 + x1) / 2 + 0.3, ym)], lw=0.9, color=st.edge, z=7)


def unit_plan(ax, mode="arch", unit="A"):
    """3-bedroom / 3-bath flat with tubs. Bedrooms 1 and 2 share a short hall; each bath opens off its own bedroom."""
    st = Style(mode)
    poly(ax, OUT, fc=st.frame, ec=st.edge, lw=0.9, z=3)
    poly(ax, IN_U, fc=PAPER, ec=st.edge, lw=0.6, z=4)
    window_h(ax, 12, 17, BY0, BY0 + 0.5)            # kitchen window
    window_h(ax, 22, 30, BY0, BY0 + 0.5)            # living sliding door
    window_h(ax, 39.5, 43, BY0, BY0 + 0.5)          # stair window
    window_v(ax, 10.5, 13.5, BX0, BX0 + 0.5)        # kitchen west
    window_v(ax, 28.5, 31.5, BX0, BX0 + 0.5)        # bedroom 1 west
    window_h(ax, 12, 16, WY1 - 0.5, WY1)            # bedroom 1 north (escape)
    window_h(ax, 22, 26, WY1 - 0.5, WY1)            # bedroom 2 north (escape)
    window_h(ax, 39, 43, BY1 - 0.5, BY1)            # bedroom 3 north (escape)
    window_v(ax, 24.5, 27.5, BX1 - 0.5, BX1)        # bedroom 3 east
    x0, x1, y0, y1 = SHAFT_U
    wall(ax, x0 - 0.5, y0, x0, y1 + 0.5, st)        # stair enclosure (1-hour)
    wall(ax, x0, y1, x1, y1 + 0.5, st)
    opening(ax, x0 - 0.52, 9.0, x0 + 0.02, 12.0)    # unit entry
    door(ax, (x0 - 0.5, 9.0), 3.0, 90, 90, color=st.edge)
    u_stair(ax, SHAFT_U, st, n=8, up=(unit == "A"), dn=True)
    # partitions
    wall(ax, 10, 18.0, 37, 18.4, st)                # living / suites (wet wall)
    wall(ax, 10, 23.5, 29.8, 23.9, st)              # baths / bedrooms
    wall(ax, 17.6, 18.4, 18.0, 27.3, st)            # bath 1 east + hall west
    wall(ax, 21.4, 18.4, 21.8, 27.3, st)            # hall east + bath 2 west
    wall(ax, 17.6, 26.9, 21.8, 27.3, st)            # hall end
    wall(ax, 19.5, 27.3, 19.9, 34.5, st)            # bedroom 1 / bedroom 2
    wall(ax, 29.4, 18.4, 29.8, 23.9, st)            # bath 2 east
    wall(ax, 29.8, 21.5, 33.5, 21.9, st)            # laundry / bath 3
    wall(ax, 33.5, 18.4, 33.9, 29.5, st)            # laundry + bath 3 / suite 3
    wall(ax, 28.0, 23.9, 28.4, 29.5, st)            # bedroom 2 / bath 3
    for a, b in ((18.3, 21.1), (34.1, 36.8)):       # hall doors from the living room
        opening(ax, a, 17.98, b, 18.42)
        door(ax, (a, 18.4), b - a, 0, 90, color=st.edge)
    opening(ax, 30.2, 17.98, 33.2, 18.42)           # laundry bifold
    line(ax, [(30.2, 18.0), (30.95, 17.4), (31.7, 18.0), (32.45, 17.4), (33.2, 18.0)], lw=0.5, z=7, color=st.edge)
    opening(ax, 18.02, 23.48, 21.38, 23.92)         # hall runs through to the bedroom doors
    opening(ax, 17.58, 24.2, 18.02, 26.7)           # bedroom 1 door
    door(ax, (17.6, 24.2), 2.5, 90, 90, color=st.edge)
    opening(ax, 21.38, 24.2, 21.82, 26.7)           # bedroom 2 door
    door(ax, (21.8, 24.2), 2.5, 90, -90, color=st.edge)
    pocket(ax, 15.0, 23.48, 17.4, 23.92, st)        # bath 1 from bedroom 1
    pocket(ax, 22.0, 23.48, 24.4, 23.92, st)        # bath 2 from bedroom 2
    pocket(ax, 33.48, 24.1, 33.92, 26.5, st)        # bath 3 from bedroom 3
    f = st.furn
    tub(ax, 10.1, 18.5, 12.6, 23.4, st)             # bath 1
    wc(ax, 14.1, 18.4, st, facing="N")
    lav(ax, 15.5, 18.5, 17.5, 20.0, st)
    tub(ax, 26.8, 18.5, 29.3, 23.4, st)             # bath 2
    wc(ax, 25.3, 23.5, st, facing="S")
    lav(ax, 22.0, 18.5, 24.0, 20.0, st)
    tub(ax, 28.5, 27.0, 33.4, 29.4, st)             # bath 3
    wc(ax, 28.4, 25.3, st, facing="E")
    lav(ax, 30.4, 22.0, 32.8, 23.5, st)
    rect(ax, 30.1, 18.6, 33.2, 21.3, fc=PAPER, ec=f, lw=0.5, z=6)                 # stacked W/D
    # water heater closet beside the entry
    wall(ax, 34.0, 12.2, 34.3, 15.5, st)
    wall(ax, 34.0, 15.2, 37, 15.5, st)
    wall(ax, 34.0, 12.2, 37, 12.5, st)
    opening(ax, 33.98, 12.8, 34.32, 14.9)
    ax.add_patch(plt.Circle((35.7, 13.85), 1.05, fc=PAPER, ec=f, lw=0.6, zorder=6))
    # kitchen along the west wall + island
    rect(ax, 10.0, 8.9, 12.0, 18.0, fc=WOOD if not st.bg else PAPER, ec=f, lw=0.6, z=5)
    rect(ax, 10.0, 15.4, 12.8, 18.0, fc=PAPER, ec=f, lw=0.6, z=6)                 # refrigerator
    rect(ax, 10.05, 12.9, 11.95, 15.3, fc=PAPER, ec=f, lw=0.6, z=6)               # range
    for cy in (13.5, 14.7):
        for cx in (10.5, 11.45):
            ax.add_patch(plt.Circle((cx, cy), 0.3, fc="none", ec=f, lw=0.4, zorder=7))
    lav(ax, 10.15, 10.5, 11.85, 12.8, st)                                         # kitchen sink
    rect(ax, 10.05, 8.95, 11.95, 10.4, fc=PAPER, ec=f, lw=0.5, z=6)               # dishwasher
    rect(ax, 14.6, 10.0, 17.1, 15.4, fc=WOOD if not st.bg else PAPER, ec=f, lw=0.6, z=5)   # island
    for (a, b, c, d) in ((10.1, 23.9, 14.8, 25.8), (24.7, 23.9, 27.9, 25.8), (40.6, 22.2, 44.4, 24.1)):   # closets
        rect(ax, a, b, c, d, fc="none", ec=f, lw=0.5, z=5, ls="--")
    if st.bg:
        for x, y, n in ((27, 12.6, "LIVING"), (13.4, 16.6, "KITCHEN"), (14.6, 30.6, "BEDROOM 1"), (24.0, 30.6, "BEDROOM 2"),
                        (39, 26.6, "BEDROOM 3"), (14.6, 21.6, "BATH 1"), (24.6, 21.4, "BATH 2"), (31.0, 25.6, "BATH 3"),
                        (31.6, 20.0, "W/D"), (35.7, 13.85, "WH")):
            room(ax, x, y, n, st=st)
        return st
    txt(ax, 11.0, 9.7, "DW", size=4.0, color=GREY, z=8)
    txt(ax, 11.4, 16.7, "REF", size=4.2, color=GREY, z=8)
    txt(ax, 31.65, 19.95, "W/D", size=4.4, color=GREY, z=8)
    txt(ax, 35.7, 13.85, "WH", size=4.4, color=GREY, z=8)
    for sy in (11.0, 12.7, 14.4):
        ax.add_patch(plt.Circle((18.0, sy), 0.55, fc=PAPER, ec=f, lw=0.4, zorder=6))
    rect(ax, 24.6, 14.2, 31.6, 17.2, fc="#f2f3f5", ec=f, lw=0.5, z=5)             # sofa
    rect(ax, 24.6, 16.5, 31.6, 17.2, fc="#e4e6e9", ec=f, lw=0.4, z=6)
    rect(ax, 26.1, 11.2, 30.1, 13.0, fc="#f2f3f5", ec=f, lw=0.5, z=5)
    for (a, b, c, d, hx0, hy0, hx1, hy1) in ((10.2, 28.6, 16.9, 33.6, 10.2, 28.6, 11.8, 33.6),
                                             (21.4, 28.0, 26.4, 34.2, 21.4, 32.6, 26.4, 34.2),
                                             (39.6, 24.6, 44.3, 29.3, 39.6, 27.7, 44.3, 29.3)):
        rect(ax, a, b, c, d, fc="#f2f3f5", ec=f, lw=0.5, z=5)
        rect(ax, hx0, hy0, hx1, hy1, fc="#e4e6e9", ec=f, lw=0.4, z=6)
    room(ax, 27.0, 10.0, "LIVING", "27'-0\" x 9'-6\" with kitchen")
    txt(ax, 13.4, 16.6, "KITCHEN", size=5.2, weight="bold", z=9)
    room(ax, 14.4, 27.5, "BEDROOM 1", "9'-6\" x 10'-7\"  ·  94 sf", fs=5.6)
    room(ax, 25.0, 27.3, "BEDROOM 2", None, fs=5.4)
    txt(ax, 25.0, 26.5, "8'-1\" x 10'-7\" · 79 sf", size=4.6, box=True, z=9)
    room(ax, 36.6, 27.6, "BEDROOM 3", None, fs=5.6)
    txt(ax, 36.6, 26.6, "10'-7\" x 7'-4\"", size=5.0, box=True, z=9)
    txt(ax, 36.6, 25.7, "77 sf", size=5.0, box=True, z=9)
    txt(ax, 14.6, 21.8, "BATH 1", size=4.8, weight="bold")
    txt(ax, 24.6, 21.4, "BATH 2", size=4.8, weight="bold")
    txt(ax, 31.2, 25.3, "BATH 3", size=4.8, weight="bold")
    txt(ax, 19.7, 21.0, "HALL", size=4.4, color=GREY, rot=90)
    txt(ax, 35.4, 20.4, "HALL", size=4.2, color=GREY)
    for x, y in ((12.4, 24.85), (26.3, 24.85), (42.5, 23.15)):
        txt(ax, x, y, "CLOSET", size=3.8, color=GREY)
    txt(ax, 41.0, 10.2, "COMMON\nSTAIR", size=4.8, color=GREY)
    return st


def porch(ax, level="A", bg=False):
    c = BG_EDGE if bg else INK
    rect(ax, 9.5, 4, 35.5, BY0, fc=PAPER if bg else WOOD, ec=c, lw=0.7, z=3)
    if not bg:
        for x in np.arange(10.0, 35.5, 0.5):
            line(ax, [(x, 4), (x, BY0)], lw=0.15, color=LIGHT, z=3)
    line(ax, [(9.7, BY0), (9.7, 4.2), (35.3, 4.2), (35.3, BY0)], lw=1.0, color=c, z=6)
