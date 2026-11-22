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
    c = st.furn
    if facing == "N":
        rect(ax, x - 0.8, y, x + 0.8, y + 0.65, fc=PAPER, ec=c, lw=0.5, z=6)
        ax.add_patch(Ellipse((x, y + 1.55), 1.3, 1.8, fc=PAPER, ec=c, lw=0.5, zorder=6))
    elif facing == "S":
        rect(ax, x - 0.8, y - 0.65, x + 0.8, y, fc=PAPER, ec=c, lw=0.5, z=6)
        ax.add_patch(Ellipse((x, y - 1.55), 1.3, 1.8, fc=PAPER, ec=c, lw=0.5, zorder=6))
    elif facing == "W":
        rect(ax, x - 0.65, y - 0.8, x, y + 0.8, fc=PAPER, ec=c, lw=0.5, z=6)
        ax.add_patch(Ellipse((x - 1.55, y), 1.8, 1.3, fc=PAPER, ec=c, lw=0.5, zorder=6))


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
    st = Style(mode)
    poly(ax, OUT, fc=st.conc, ec=st.edge, lw=0.9, z=3)
    poly(ax, IN_L, fc=PAPER, ec=st.edge, lw=0.6, z=4)
    # front wall openings
    for a, b in (DOOR_A, DOOR_B):
        opening(ax, a, BY0 - 0.02, b, BY0 + 0.69)
        line(ax, [(a, BY0 + 0.2), (b, BY0 + 0.2)], lw=0.5, ls=(0, (5, 2)), z=7, color=st.edge)
        line(ax, [(a, BY0 + 0.45), (b, BY0 + 0.45)], lw=0.5, ls=(0, (5, 2)), z=7, color=st.edge)
    opening(ax, ENTRY[0], BY0 - 0.02, ENTRY[1], BY0 + 0.69)
    door(ax, (ENTRY[0], BY0 + 0.67), 3.0, 0, 90, color=st.edge)
    # stair shaft + mech room (rated enclosure)
    x0, x1, y0, y1 = SHAFT_L
    wall(ax, x0 - 0.33, y0, x0, 29.0, st, fc=st.conc)
    wall(ax, x0, y1, x1, y1 + 0.33, st, fc=st.conc)
    opening(ax, x0 - 0.35, 9.3, x0 + 0.02, 12.3)                 # lobby -> garage (20-min door)
    door(ax, (x0 - 0.33, 9.3), 3.0, 90, 90, color=st.edge)
    opening(ax, x0 - 0.35, 24.0, x0 + 0.02, 27.0)                # mech room door
    door(ax, (x0 - 0.33, 27.0), 3.0, 180, 90, color=st.edge)
    u_stair(ax, SHAFT_L, st, n=8, dn=False)
    # conditioned storage room partition (insulated)
    wall(ax, 10.5, STORE_Y, 27.5, STORE_Y + 0.33, st)
    wall(ax, 27.5, STORE_Y, 27.83, 29.0, st)
    opening(ax, 12.5, STORE_Y - 0.02, 17.5, STORE_Y + 0.35)
    door(ax, (12.5, STORE_Y), 2.5, 270, 90, color=st.edge)
    door(ax, (17.5, STORE_Y), 2.5, 270, -90, color=st.edge)
    opening(ax, 24.0, STORE_Y - 0.02, 27.0, STORE_Y + 0.35)
    door(ax, (27.0, STORE_Y), 3.0, 270, -90, color=st.edge)
    # mech room equipment
    for cx, lab in ((39.0, "WH-A"), (41.4, "WH-B")):
        ax.add_patch(plt.Circle((cx, 27.6), 1.0, fc=PAPER, ec=st.furn, lw=0.6, zorder=6))
        if not st.bg:
            txt(ax, cx, 27.6, lab, size=4.0, color=GREY)
    if cars:
        for i, (a, b) in enumerate(STALLS):
            car(ax, (a + b) / 2 - 3.15, 10.4, label=None if st.bg else f"CAR {i + 1}", color=st.furn)
        for a, b in STALLS[:-1]:
            line(ax, [(b, 9.2), (b, 27.2)], lw=0.4, color=st.furn, ls=(0, (6, 4)), z=5)
    if st.bg:
        room(ax, 23.8, 24.5, "GARAGE", st=st)
        room(ax, 19.0, 31.3, "STORAGE (CONDITIONED)", st=st)
        room(ax, 40.8, 10.3, "LOBBY", st=st)
        room(ax, 40.8, 25.0, "MECH", st=st)
        return st
    rect(ax, 10.6, 32.5, 27.4, 33.9, fc=WOOD, ec=FURN, lw=0.5, z=5, ls="--")
    txt(ax, 19.0, 33.2, "16 FT RACK FOR TRIM, LUMBER, SHEET GOODS ON EDGE", size=4.6, color=GREY)
    room(ax, 23.8, 25.2, "3-CAR GARAGE", "26'-8\" x 19'-4\" to 20'-4\"", f"slab EL {EL_GAR:.1f}  ·  9'-2\" clear")
    room(ax, 19.0, 31.0, "OWNER STORAGE (CONDITIONED)", "17'-0\" x 5'-8\"  ·  96 sf", fs=5.8)
    txt(ax, 40.75, 10.2, "LOBBY", size=5.2, weight="bold")
    txt(ax, 40.75, 25.4, "MECH /\nMETERS", size=5.0, weight="bold")
    return st


# ----------------------------------------------------------------------------
def shower(ax, x0, y0, x1, y1, st):
    rect(ax, x0, y0, x1, y1, fc=PAPER, ec=st.furn, lw=0.6, z=6)
    line(ax, [(x0, y0), (x1, y1)], lw=0.3, color=st.furn, z=6)
    line(ax, [(x0, y1), (x1, y0)], lw=0.3, color=st.furn, z=6)


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
    """3-bedroom / 3-bath flat. Bedrooms across the rear, each with its own entry hall and bath."""
    st = Style(mode)
    poly(ax, OUT, fc=st.frame, ec=st.edge, lw=0.9, z=3)
    poly(ax, IN_U, fc=PAPER, ec=st.edge, lw=0.6, z=4)
    # exterior openings
    window_h(ax, 12, 17, BY0, BY0 + 0.5)            # kitchen window
    window_h(ax, 22, 30, BY0, BY0 + 0.5)            # living sliding door
    window_h(ax, 39.5, 43, BY0, BY0 + 0.5)          # stair window
    window_v(ax, 10.5, 13.5, BX0, BX0 + 0.5)        # kitchen west
    window_v(ax, 27, 30, BX0, BX0 + 0.5)            # bedroom 1 west
    window_h(ax, 12, 16, WY1 - 0.5, WY1)            # bedroom 1 north (escape)
    window_h(ax, 22, 26, WY1 - 0.5, WY1)            # bedroom 2 north (escape)
    window_h(ax, 39, 43, BY1 - 0.5, BY1)            # bedroom 3 north (escape)
    window_v(ax, 24, 27, BX1 - 0.5, BX1)            # bedroom 3 east
    # stair enclosure (1-hour)
    x0, x1, y0, y1 = SHAFT_U
    wall(ax, x0 - 0.5, y0, x0, y1 + 0.5, st)
    wall(ax, x0, y1, x1, y1 + 0.5, st)
    opening(ax, x0 - 0.52, 9.0, x0 + 0.02, 12.0)    # unit entry
    door(ax, (x0 - 0.5, 9.0), 3.0, 90, 90, color=st.edge)
    u_stair(ax, SHAFT_U, st, n=8, up=(unit == "A"), dn=True)
    # partitions
    wall(ax, 10, 18.5, 37, 18.9, st)                # living / bedroom suites (wet wall)
    wall(ax, 10, 23.5, 33.2, 23.9, st)              # baths / bedrooms
    wall(ax, 16.4, 18.9, 16.8, 23.5, st)            # bath 1 / hall 1
    wall(ax, 20, 18.9, 20.4, 34.5, st)              # suite 1 / suite 2
    wall(ax, 23.6, 18.9, 24, 23.5, st)              # hall 2 / bath 2
    wall(ax, 30, 18.9, 30.4, 23.5, st)              # bath 2 / laundry
    wall(ax, 33.2, 18.9, 33.6, 29.5, st)            # laundry + bath 3 / suite 3
    wall(ax, 28, 23.9, 28.4, 29.5, st)              # bedroom 2 / bath 3
    for a, b in ((17.1, 19.8), (20.7, 23.4), (33.9, 36.6)):          # suite entry doors
        opening(ax, a, 18.48, b, 18.92)
        door(ax, (a, 18.9), b - a, 0, 90, color=st.edge)
    opening(ax, 30.6, 18.48, 33.0, 18.92)           # laundry bifold
    line(ax, [(30.6, 18.5), (31.2, 17.9), (31.8, 18.5), (32.4, 17.9), (33.0, 18.5)], lw=0.5, z=7, color=st.edge)
    opening(ax, 17.1, 23.48, 19.8, 23.92)           # hall 1 -> bedroom 1 (open)
    opening(ax, 20.7, 23.48, 23.4, 23.92)           # hall 2 -> bedroom 2 (open)
    pocket(ax, 16.38, 19.7, 16.82, 22.1, st)        # bath 1
    pocket(ax, 23.58, 19.7, 24.02, 22.1, st)        # bath 2
    pocket(ax, 33.18, 24.3, 33.62, 26.7, st)        # bath 3
    # bath fixtures
    f = st.furn
    shower(ax, 10.1, 19.0, 13.1, 23.4, st)
    wc(ax, 14.5, 18.9, st, facing="N")
    lav(ax, 13.5, 21.9, 15.7, 23.4, st)
    shower(ax, 27.0, 19.0, 29.9, 23.4, st)
    wc(ax, 25.6, 23.5, st, facing="S")
    lav(ax, 24.4, 19.0, 26.6, 20.5, st)
    shower(ax, 28.5, 26.6, 31.3, 29.4, st)
    wc(ax, 32.3, 29.5, st, facing="S")
    lav(ax, 28.7, 24.0, 30.9, 25.5, st)
    rect(ax, 30.5, 20.9, 33.1, 23.4, fc=PAPER, ec=f, lw=0.5, z=6)                 # stacked W/D
    # kitchen along the west wall + island
    rect(ax, 10.0, 8.9, 12.0, 18.5, fc=WOOD if not st.bg else PAPER, ec=f, lw=0.6, z=5)
    rect(ax, 10.0, 15.9, 12.8, 18.5, fc=PAPER, ec=f, lw=0.6, z=6)                 # refrigerator
    rect(ax, 10.05, 13.3, 11.95, 15.8, fc=PAPER, ec=f, lw=0.6, z=6)               # range
    for cy in (13.9, 15.2):
        for cx in (10.5, 11.45):
            ax.add_patch(plt.Circle((cx, cy), 0.3, fc="none", ec=f, lw=0.4, zorder=7))
    lav(ax, 10.15, 10.7, 11.85, 13.2, st)                                         # kitchen sink
    rect(ax, 10.05, 8.95, 11.95, 10.6, fc=PAPER, ec=f, lw=0.5, z=6)               # dishwasher
    rect(ax, 14.6, 10.3, 17.1, 16.0, fc=WOOD if not st.bg else PAPER, ec=f, lw=0.6, z=5)   # island
    # closets
    for (a, b, c, d) in ((10.1, 23.9, 15.6, 25.8), (24.4, 23.9, 27.9, 25.8), (40.6, 22.2, 44.4, 24.1)):
        rect(ax, a, b, c, d, fc="none", ec=f, lw=0.5, z=5, ls="--")
    if st.bg:
        for x, y, n in ((27, 13, "LIVING"), (13.3, 17.2, "KITCHEN"), (15, 30, "BEDROOM 1"), (24.2, 30, "BEDROOM 2"),
                        (39, 26.5, "BEDROOM 3"), (14.6, 20.6, "BATH 1"), (26.4, 21.6, "BATH 2"), (30.8, 26, "BATH 3"), (31.8, 19.8, "W/D")):
            room(ax, x, y, n, st=st)
        return st
    txt(ax, 11.0, 9.8, "DW", size=4.0, color=GREY, z=8)
    txt(ax, 11.4, 17.2, "REF", size=4.2, color=GREY, z=8)
    txt(ax, 31.8, 22.1, "W/D", size=4.4, color=GREY, z=8)
    for sy in (11.4, 13.2, 15.0):
        ax.add_patch(plt.Circle((18.0, sy), 0.55, fc=PAPER, ec=f, lw=0.4, zorder=6))
    rect(ax, 24.0, 14.6, 31.0, 17.6, fc="#f2f3f5", ec=f, lw=0.5, z=5)             # sofa
    rect(ax, 24.0, 16.9, 31.0, 17.6, fc="#e4e6e9", ec=f, lw=0.4, z=6)
    rect(ax, 25.5, 11.4, 29.5, 13.2, fc="#f2f3f5", ec=f, lw=0.5, z=5)
    for (a, b, c, d, hx0, hy0, hx1, hy1) in ((10.2, 28.6, 16.9, 33.6, 10.2, 28.6, 11.8, 33.6),
                                             (21.6, 27.6, 26.6, 34.2, 21.6, 32.6, 26.6, 34.2),
                                             (39.6, 24.6, 44.3, 29.3, 39.6, 27.7, 44.3, 29.3)):
        rect(ax, a, b, c, d, fc="#f2f3f5", ec=f, lw=0.5, z=5)
        rect(ax, hx0, hy0, hx1, hy1, fc="#e4e6e9", ec=f, lw=0.4, z=6)
    room(ax, 27.0, 10.2, "LIVING", "27'-0\" x 10'-0\" with kitchen")
    txt(ax, 13.3, 17.3, "KITCHEN", size=5.2, weight="bold", z=9)
    room(ax, 15.0, 27.4, "BEDROOM 1", "10'-0\" x 10'-7\"  ·  106 sf", fs=5.8)
    room(ax, 24.2, 26.8, "BEDROOM 2", "7'-7\" x 10'-7\"  ·  81 sf", fs=5.6)
    room(ax, 36.6, 27.6, "BEDROOM 3", None, fs=5.6)
    txt(ax, 36.6, 26.6, "10'-11\" x 7'-4\"", size=5.0, box=True, z=9)
    txt(ax, 36.6, 25.7, "80 sf", size=5.0, box=True, z=9)
    txt(ax, 14.9, 20.4, "BATH 1", size=4.8, weight="bold")
    txt(ax, 25.5, 21.6, "BATH 2", size=4.8, weight="bold")
    txt(ax, 30.8, 26.0, "BATH 3", size=4.8, weight="bold", rot=0)
    txt(ax, 18.4, 21.2, "HALL", size=4.2, color=GREY, rot=90)
    txt(ax, 22.0, 21.2, "HALL", size=4.2, color=GREY, rot=90)
    txt(ax, 35.3, 20.4, "HALL", size=4.2, color=GREY)
    txt(ax, 12.9, 24.8, "CLOSET", size=3.8, color=GREY)
    txt(ax, 26.1, 24.8, "CLOSET", size=3.8, color=GREY)
    txt(ax, 42.5, 23.1, "CLOSET", size=3.8, color=GREY)
    txt(ax, 41.0, 10.2, "COMMON\nSTAIR", size=4.8, color=GREY)
    return st


def porch(ax, level="A", bg=False):
    c = BG_EDGE if bg else INK
    rect(ax, 9.5, 4, 35.5, BY0, fc=PAPER if bg else WOOD, ec=c, lw=0.7, z=3)
    if not bg:
        for x in np.arange(10.0, 35.5, 0.5):
            line(ax, [(x, 4), (x, BY0)], lw=0.15, color=LIGHT, z=3)
    line(ax, [(9.7, BY0), (9.7, 4.2), (35.3, 4.2), (35.3, BY0)], lw=1.0, color=c, z=6)
