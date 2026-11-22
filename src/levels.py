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
    ys = y0 + 3.5
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
    if facing == "S":
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
        room(ax, 40.8, 24.5, "MECH", st=st)
        return st
    rect(ax, 10.6, 32.5, 27.4, 33.9, fc=WOOD, ec=FURN, lw=0.5, z=5, ls="--")
    txt(ax, 19.0, 33.2, "16 FT RACK FOR TRIM, LUMBER, SHEET GOODS ON EDGE", size=4.6, color=GREY)
    room(ax, 23.8, 25.2, "3-CAR GARAGE", "26'-8\" x 19'-4\" to 20'-4\"", f"slab EL {EL_GAR:.1f}  ·  9'-2\" clear")
    room(ax, 19.0, 31.0, "OWNER STORAGE (CONDITIONED)", "17'-0\" x 5'-8\"  ·  96 sf", fs=5.8)
    txt(ax, 40.75, 10.2, "LOBBY", size=5.2, weight="bold")
    txt(ax, 40.75, 25.4, "MECH /\nMETERS", size=5.0, weight="bold")
    return st


# ----------------------------------------------------------------------------
def unit_plan(ax, mode="arch", unit="A"):
    st = Style(mode)
    poly(ax, OUT, fc=st.frame, ec=st.edge, lw=0.9, z=3)
    poly(ax, IN_U, fc=PAPER, ec=st.edge, lw=0.6, z=4)
    # exterior openings
    window_h(ax, 12, 20, BY0, BY0 + 0.5)            # living sliding door
    window_h(ax, 25, 30, BY0, BY0 + 0.5)            # dining window
    window_h(ax, 39.5, 43, BY0, BY0 + 0.5)          # stair window
    window_v(ax, 12, 15, BX0, BX0 + 0.5)            # living west
    window_v(ax, 24, 27, BX0, BX0 + 0.5)            # bedroom 1 west
    window_h(ax, 13, 17, WY1 - 0.5, WY1)            # bedroom 1 north (egress)
    window_h(ax, 37.5, 41.5, BY1 - 0.5, BY1)        # bedroom 2 north (egress)
    window_v(ax, 24.5, 27.5, BX1 - 0.5, BX1)        # bedroom 2 east
    # stair enclosure (1-hour)
    x0, x1, y0, y1 = SHAFT_U
    wall(ax, x0 - 0.5, y0, x0, y1 + 0.5, st)
    wall(ax, x0, y1, x1, y1 + 0.5, st)
    opening(ax, x0 - 0.52, 9.0, x0 + 0.02, 12.0)    # unit entry
    door(ax, (x0 - 0.5, 9.0), 3.0, 90, 90, color=st.edge)
    u_stair(ax, SHAFT_U, st, n=8, up=(unit == "A"), dn=True)
    # partitions
    wall(ax, 10, 20, 37, 20.375, st)                # living / rear rooms
    wall(ax, 22, 20.375, 22.375, 34.5, st)          # bedroom 1 east
    wall(ax, 26, 20.375, 26.375, 29.5, st)          # hall / bath
    wall(ax, 31.6, 20.375, 32.0, 29.5, st)          # bath / bedroom 2 (wet wall)
    wall(ax, 22.375, 26.5, 26, 26.875, st)          # laundry closet
    wall(ax, 22.375, 29.5, 28, 29.9, st)            # closet / hall-bath line
    opening(ax, 22.7, 19.98, 25.7, 20.4)            # cased opening to hall
    opening(ax, 33.4, 19.98, 36.1, 20.4)            # bedroom 2 door
    door(ax, (33.4, 20.375), 2.7, 0, 90, color=st.edge)
    opening(ax, 21.98, 21.0, 22.4, 23.7)            # bedroom 1 door
    door(ax, (22.0, 23.7), 2.7, 180, 90, color=st.edge)
    opening(ax, 25.98, 21.0, 26.4, 23.5)            # bath door
    door(ax, (26.375, 21.0), 2.5, 0, 90, color=st.edge)
    opening(ax, 21.98, 30.6, 22.4, 33.1)            # closet door
    door(ax, (22.375, 30.6), 2.5, 0, 90, color=st.edge)
    opening(ax, 22.8, 26.48, 25.6, 26.9)            # laundry bifold
    line(ax, [(22.8, 26.5), (23.5, 25.9), (24.2, 26.5), (24.9, 25.9), (25.6, 26.5)], lw=0.5, z=7, color=st.edge)
    # fixtures
    f = st.furn
    rect(ax, 26.45, 26.95, 31.55, 29.45, fc=PAPER, ec=f, lw=0.6, z=6)             # tub
    rect(ax, 26.75, 27.2, 31.25, 29.2, fc=PAPER, ec=f, lw=0.4, z=6)
    wc(ax, 31.6, 25.3, st, facing="W")
    lav(ax, 29.4, 20.5, 31.5, 22.5, st)
    rect(ax, 22.9, 27.0, 25.5, 29.4, fc=PAPER, ec=f, lw=0.5, z=6)                 # stacked W/D
    rect(ax, 26.0, 18.0, 36.6, 20.0, fc=WOOD if not st.bg else PAPER, ec=f, lw=0.6, z=5)   # kitchen run
    rect(ax, 34.0, 17.4, 36.8, 20.0, fc=PAPER, ec=f, lw=0.6, z=6)                 # refrigerator
    rect(ax, 31.3, 18.05, 33.8, 19.95, fc=PAPER, ec=f, lw=0.6, z=6)               # range
    for cx in (31.95, 33.15):
        for cy in (18.5, 19.45):
            ax.add_patch(plt.Circle((cx, cy), 0.3, fc="none", ec=f, lw=0.4, zorder=7))
    lav(ax, 28.3, 18.15, 30.9, 19.85, st)                                         # kitchen sink
    rect(ax, 26.1, 18.05, 28.1, 19.95, fc=PAPER, ec=f, lw=0.5, z=6)               # dishwasher
    rect(ax, 27, 13.2, 33, 15.7, fc=WOOD if not st.bg else PAPER, ec=f, lw=0.6, z=5)       # island
    if st.bg:
        for x, y, n in ((16, 14, "LIVING"), (30, 11, "DINING"), (31, 16.6, "KITCHEN"), (16, 27, "BEDROOM 1"),
                        (38.5, 26, "BEDROOM 2"), (29, 24, "BATH"), (24.2, 23, "HALL"), (25.2, 32.2, "CLOSET"), (24.2, 28.2, "W/D")):
            room(ax, x, y, n, st=st)
        return st
    txt(ax, 26.6, 19.0, "DW", size=4.2, color=GREY, z=8)
    txt(ax, 35.4, 18.7, "REF", size=4.4, color=GREY, z=8)
    txt(ax, 24.2, 28.2, "W/D", size=4.6, color=GREY, z=8)
    for sx in (28.2, 30, 31.8):
        ax.add_patch(plt.Circle((sx, 12.4), 0.55, fc=PAPER, ec=f, lw=0.4, zorder=6))
    rect(ax, 11.5, 16.4, 18.5, 19.4, fc="#f2f3f5", ec=f, lw=0.5, z=5)             # sofa
    rect(ax, 11.5, 18.7, 18.5, 19.4, fc="#e4e6e9", ec=f, lw=0.4, z=6)
    rect(ax, 13.0, 12.8, 17.0, 14.6, fc="#f2f3f5", ec=f, lw=0.5, z=5)
    rect(ax, 12.5, 26.5, 18.5, 33.2, fc="#f2f3f5", ec=f, lw=0.5, z=5)             # bed 1
    rect(ax, 12.5, 31.6, 18.5, 33.2, fc="#e4e6e9", ec=f, lw=0.4, z=6)
    rect(ax, 38.3, 23.2, 43.3, 29.3, fc="#f2f3f5", ec=f, lw=0.5, z=5)             # bed 2
    rect(ax, 38.3, 27.7, 43.3, 29.3, fc="#e4e6e9", ec=f, lw=0.4, z=6)
    line(ax, [(22.8, 34.0), (27.6, 34.0)], lw=0.5, ls="--", color=f, z=6)
    room(ax, 16.0, 10.9, "LIVING", "12'-0\" x 11'-6\"")
    room(ax, 23.5, 16.4, "DINING", None, fs=5.8)
    room(ax, 31.0, 16.9, "KITCHEN", None, fs=5.8)
    room(ax, 16.0, 24.4, "BEDROOM 1", "12'-0\" x 14'-1\"")
    room(ax, 35.0, 22.2, "BEDROOM 2", None, fs=5.8)
    txt(ax, 35.0, 21.25, "12'-6\" x 7'-0\" + 5' x 9'", size=4.8, box=True)
    txt(ax, 28.6, 24.6, "BATH", size=5.2, weight="bold")
    txt(ax, 24.2, 24.6, "HALL", size=5.0, weight="bold")
    txt(ax, 25.2, 32.3, "WALK-IN\nCLOSET", size=5.0, weight="bold")
    txt(ax, 41.0, 10.3, "COMMON\nSTAIR", size=4.8, color=GREY)
    return st


def porch(ax, level="A", bg=False):
    c = BG_EDGE if bg else INK
    rect(ax, 9.5, 4, 35.5, BY0, fc=PAPER if bg else WOOD, ec=c, lw=0.7, z=3)
    if not bg:
        for x in np.arange(10.0, 35.5, 0.5):
            line(ax, [(x, 4), (x, BY0)], lw=0.15, color=LIGHT, z=3)
    line(ax, [(9.7, BY0), (9.7, 4.2), (35.3, 4.2), (35.3, BY0)], lw=1.0, color=c, z=6)
