"""Base floor plans drawn from model.py. `mode="arch"` is the full architectural plan; `mode="bg"` is a
muted background for the trade overlays (structure, plumbing, mechanical, electrical ...)."""
import math

import numpy as np
from matplotlib.patches import Arc, Ellipse, FancyBboxPatch

import model as m
from common import *  # noqa: F401,F403

FPI = 16 / 3.0          # 3/16" = 1'-0"
VIEW_UNIT = ((0.0, 54.0), (2.5, 49.5))       # unit floors
VIEW_GAR = ((0.0, 54.0), (-8.5, 42.5))       # garage level with the apron and street
POCHE = "#1b1e22"
CONC = "#a9aeb4"
FURN = "#8d949c"
WOOD = "#f4f1ea"
BG_WALL = "#d3d7dc"
BG_EDGE = "#9aa1a9"
RATED = "#b3261e"
YELLOW = "#c9a400"


class Style:
    def __init__(self, mode):
        self.bg = mode == "bg"
        self.frame = BG_WALL if self.bg else POCHE
        self.conc = BG_WALL if self.bg else CONC
        self.edge = BG_EDGE if self.bg else INK
        self.furn = "#c3c8ce" if self.bg else FURN
        self.text = "#8a9199" if self.bg else INK
        self.fill = "#f6f7f8" if self.bg else "#f2f3f5"


def plan_frame(fig, title, sub, view=VIEW_UNIT, street=False, north=True, fpi=FPI, bottom=0.72, lot=True):
    (vx, vy) = view
    left = MARGIN + (SHEET_W - 2 * MARGIN - TB_W - (vx[1] - vx[0]) / fpi) / 2
    ax = plan_axes(fig, left, bottom, vx, vy, fpi)
    if lot:
        line(ax, [LOT_NW, LOT_SW, LOT_SE, LOT_NE, LOT_NW], color=ACCENT, lw=1.0, ls=(0, (9, 2.5, 1.5, 2.5)), z=5.25)
        txt(ax, 51.0, 20.0, "LOT LINE", size=5.0, color=ACCENT, rot=90)
        if vy[0] < 0:
            txt(ax, 46.0, -1.0, "FRONT LOT LINE = R.O.W. LINE", size=5.0, color=ACCENT)
    if street and vy[0] < PAVE_N:
        line(ax, [(vx[0], PAVE_N), (vx[1], PAVE_N)], color=GREY, lw=0.6, z=2)
        rect(ax, vx[0], vy[0], vx[1], PAVE_N, fc="#e6e8eb", ec="none", z=1)
        txt(ax, 44.0, PAVE_N - 0.8, "BAIRD STREET  (±14' pavement)", size=5.6, color=GREY, weight="bold")
    if north:
        north_arrow(ax, vx[1] - 3.0, vy[1] - 4.2, 1.8, 6.5)
    scale_bar(ax, vx[0] + 1.5, vy[0] + 1.0, 16, 4, 0.42, size=5.2)
    view_title(ax, vx[0] + 0.6, vy[1] - 1.6, "1", title, sub, 9)
    return ax


# ----------------------------------------------------------------------------
# symbols
# ----------------------------------------------------------------------------
def wall(ax, x0, y0, x1, y1, st, fc=None, z=5):
    rect(ax, x0, y0, x1, y1, fc=fc or st.frame, ec=st.edge, lw=0.4, z=z)


def car(ax, x0, y0, w=m.CAR_W, l=m.CAR_L, color=FURN):
    ax.add_patch(FancyBboxPatch((x0 + 0.5, y0 + 0.5), w - 1, l - 1, boxstyle="round,pad=0.5,rounding_size=1.1",
                                fc="#f2f3f5", ec=color, lw=0.6, zorder=6))
    rect(ax, x0 + 0.7, y0 + 3.4, x0 + w - 0.7, y0 + 5.2, fc="none", ec=color, lw=0.4, z=6)
    rect(ax, x0 + 0.7, y0 + l - 5.6, x0 + w - 0.7, y0 + l - 3.6, fc="none", ec=color, lw=0.4, z=6)


def u_stair(ax, shaft, st, treads, up=True, dn=True, tread=10 / 12, land=None):
    """Switchback stair in shaft (x0, x1, y0, y1): floor landing at the south end, mid landing at the north."""
    x0, x1, y0, y1 = shaft
    gap = 4 / 12
    w = (x1 - x0 - gap) / 2
    ys = y0 + (land if land else (y1 - y0 - treads * tread) / 2)
    ye = ys + treads * tread
    for i in range(treads + 1):
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
    """Water closet; (x, y) is the centre of the tank's wall side, `facing` the direction the bowl points."""
    c = st.furn
    dx, dy = {"N": (0, 1), "S": (0, -1), "E": (1, 0), "W": (-1, 0)}[facing]
    if dx == 0:
        rect(ax, x - 0.8, min(y, y + 0.65 * dy), x + 0.8, max(y, y + 0.65 * dy), fc=PAPER, ec=c, lw=0.5, z=6)
        ax.add_patch(Ellipse((x, y + 1.5 * dy), 1.25, 1.65, fc=PAPER, ec=c, lw=0.5, zorder=6))
    else:
        rect(ax, min(x, x + 0.65 * dx), y - 0.8, max(x, x + 0.65 * dx), y + 0.8, fc=PAPER, ec=c, lw=0.5, z=6)
        ax.add_patch(Ellipse((x + 1.5 * dx, y), 1.65, 1.25, fc=PAPER, ec=c, lw=0.5, zorder=6))


def lav(ax, x0, y0, x1, y1, st):
    rect(ax, x0, y0, x1, y1, fc=PAPER, ec=st.furn, lw=0.5, z=6)
    ax.add_patch(Ellipse(((x0 + x1) / 2, (y0 + y1) / 2), min(1.3, (x1 - x0) * 0.62), min(1.0, (y1 - y0) * 0.62),
                         fc=PAPER, ec=st.furn, lw=0.5, zorder=6))


def tub(ax, x0, y0, x1, y1, st):
    rect(ax, x0, y0, x1, y1, fc=PAPER, ec=st.furn, lw=0.7, z=6)
    ax.add_patch(FancyBboxPatch((x0 + 0.35, y0 + 0.35), (x1 - x0) - 0.7, (y1 - y0) - 0.7, boxstyle="round,pad=0.1,rounding_size=0.5",
                                fc=PAPER, ec=st.furn, lw=0.5, zorder=6))


def room(ax, x, y, name, size=None, extra=None, fs=6.0, st=None):
    if st is not None and st.bg:
        txt(ax, x, y, name, size=4.4, color=st.text, z=4)
        return
    txt(ax, x, y, name, size=fs, weight="bold", z=9, box=True)
    if size:
        txt(ax, x, y - 0.95, size, size=5.0, z=9, box=True)
    if extra:
        txt(ax, x, y - 1.8, extra, size=4.6, color=GREY, z=9, box=True)


def draw_door(ax, d, st, tag=False):
    x0, y0, x1, y1 = m.door_cut(d)
    opening(ax, x0 - 0.01, y0 - 0.01, x1 + 0.01, y1 + 0.01)
    (hx, hy), (ax_, ay_), (sx, sy) = m.door_hinge(d)
    w = d["w"]
    if d["kind"] == "bifold":
        n = 4
        pts = []
        for i in range(n + 1):
            off = 0.0 if i % 2 == 0 else w / n * 0.8
            pts.append((hx + ax_ * w * i / n + sx * off, hy + ay_ * w * i / n + sy * off))
        line(ax, pts, lw=0.55, color=st.edge, z=7)
    else:
        line(ax, [(hx, hy), (hx + sx * w, hy + sy * w)], lw=1.0, color=st.edge, z=7)
        a0 = math.degrees(math.atan2(ay_, ax_))
        a1 = math.degrees(math.atan2(sy, sx))
        d_ = (a1 - a0 + 180) % 360 - 180
        t1, t2 = (a0, a0 + d_) if d_ > 0 else (a0 + d_, a0)
        ax.add_patch(Arc((hx, hy), 2 * w, 2 * w, theta1=t1, theta2=t2, lw=0.4, color=st.edge, zorder=7))
    # jamb lines
    if d["wall"] == "h":
        for x in (x0, x1):
            line(ax, [(x, y0), (x, y1)], lw=0.5, color=st.edge, z=7)
    else:
        for y in (y0, y1):
            line(ax, [(x0, y), (x1, y)], lw=0.5, color=st.edge, z=7)
    if tag and not st.bg:
        cx, cy = (x0 + x1) / 2 - sx * 0.7, (y0 + y1) / 2 - sy * 0.7
        ax.add_patch(plt.Circle((cx, cy), 0.46, fc=PAPER, ec=INK, lw=0.4, zorder=10))
        txt(ax, cx, cy, d["tag"][1:], size=3.4, z=11)


def draw_window(ax, wall_, s0, s1, st, tag=None):
    q = m.win_quad(wall_, s0, s1)
    poly(ax, q, fc=PAPER, ec="none", z=5.4 if wall_ == "N" else 5)
    mid0 = ((q[0][0] + q[3][0]) / 2, (q[0][1] + q[3][1]) / 2)
    mid1 = ((q[1][0] + q[2][0]) / 2, (q[1][1] + q[2][1]) / 2)
    for a, b in ((q[0], q[1]), (mid0, mid1), (q[3], q[2])):
        line(ax, [a, b], lw=0.5, color=st.edge, z=6)
    for a, b in ((q[0], q[3]), (q[1], q[2])):
        line(ax, [a, b], lw=0.8, color=st.edge, z=6)
    if tag and not st.bg:
        ox, oy = {"S": (0, -1.0), "N": (0.3, 1.0), "E": (1.0, 0), "W": (-1.0, 0)}[wall_]
        cx, cy = (q[0][0] + q[1][0]) / 2 + ox, (q[0][1] + q[1][1]) / 2 + oy
        poly(ax, [(cx - 0.62, cy), (cx, cy + 0.5), (cx + 0.62, cy), (cx, cy - 0.5)], fc=PAPER, ec=INK, lw=0.4, z=10)
        txt(ax, cx, cy, tag[1:], size=3.4, z=11)


# ----------------------------------------------------------------------------
# garage level
# ----------------------------------------------------------------------------
def lower_plan(ax, mode="arch", cars=True, labels=True):
    st = Style(mode)
    x0, x1, y0, y1 = m.SHAFT_L
    poly(ax, m.OUT_L, fc=st.conc, ec=st.edge, lw=0.9, z=3)
    inside = [(m.xw_gi(m.YF - 0.02), m.YF - 0.02), (m.XE_GI, m.YF - 0.02), (m.XE_GI, m.Y_GR_I), (m.xw_gi(m.Y_GR_I), m.Y_GR_I)]
    poly(ax, inside, fc=PAPER, ec="none", z=4)
    line(ax, [inside[0], inside[3], inside[2], inside[1]], lw=0.6, color=st.edge, z=5)
    # front wall: concrete return at the west, lobby front wall at the east, open between
    poly(ax, [(m.xw_o(m.YF), m.YF), (m.OPEN[0], m.YF), (m.OPEN[0], m.YF + m.CONC), (m.xw_gi(m.YF + m.CONC), m.YF + m.CONC)],
         fc=st.conc, ec=st.edge, lw=0.6, z=5)
    wall(ax, m.GAR_X1, m.YF, m.XE, m.YF + m.CMU, st, fc=st.conc)
    wall(ax, m.GAR_X1, m.YF, m.SHAFT_X0, m.Y_GR_I, st, fc=st.conc)                 # garage / lobby + utility
    wall(ax, m.SHAFT_X0, m.SHAFT_U[3], m.XE_GI, m.UTIL[2], st, fc=st.conc)         # stair / utility
    line(ax, [(m.OPEN[0], m.YF), (m.OPEN[1], m.YF)], lw=0.5, ls=(0, (2, 3)), z=7, color=st.edge)
    cx = m.COL_X[1]
    rect(ax, cx - 0.25, m.B1_Y - 0.25, cx + 0.25, m.B1_Y + 0.25, fc=st.conc if st.bg else BLUE, ec=st.edge, lw=0.4, z=7)   # steel post, on the B1 line
    # entry door (street) and utility door (swings into the room, never toward a car)
    opening(ax, m.ENTRY[0], m.YF - 0.02, m.ENTRY[1], m.YF + m.CMU + 0.02)
    door(ax, (m.ENTRY[0], m.YF + m.CMU), 3.0, 0, 90, color=st.edge)
    opening(ax, m.GAR_X1 - 0.02, m.UTIL_DOOR[0], m.SHAFT_X0 + 0.02, m.UTIL_DOOR[1])
    door(ax, (m.SHAFT_X0, m.UTIL_DOOR[1]), 2.667, 270, 90, color=st.edge)
    u_stair(ax, m.SHAFT_L, st, treads=m.STAIR_LO["treads_per_flight"], dn=False, land=3.25)
    for (wx, wy) in m.WH:
        ax.add_patch(plt.Circle((wx, wy), m.WH_R, fc=PAPER, ec=st.furn, lw=0.6, zorder=6))
    if cars:
        for c in m.CARS:
            car(ax, c, m.CAR_Y0, color=st.furn)
        for sx in m.STALL_LINES:
            line(ax, [(sx, m.YF + 0.4), (sx, m.YF + 18.0)], lw=0.9 if not st.bg else 0.5, color=YELLOW if not st.bg else st.furn, z=5)
    if st.bg or not labels:
        room(ax, 24.0, 27.6, "OPEN GARAGE", st=Style("bg"))
        room(ax, (x0 + x1) / 2, 12.2, "STAIR", st=Style("bg"))
        room(ax, 39.4, 27.0, "UTILITY", st=Style("bg"))
        return st
    for i, c in enumerate(m.CARS):
        txt(ax, c + m.CAR_W / 2, m.CAR_Y0 + 8.3, f"{i + 1}", size=11, weight="bold", color=YELLOW, z=7)
    room(ax, 24.0, 28.1, "OPEN 3-CAR GARAGE", None, fs=6.0)
    txt(ax, (x0 + x1) / 2, 12.3, "COMMON\nSTAIR", size=4.8, color=GREY)
    txt(ax, 40.6, 27.2, "UTILITY (heated)\nwater service entry", size=4.4, weight="bold")
    return st


# ----------------------------------------------------------------------------
# unit floors
# ----------------------------------------------------------------------------
def unit_shell(ax, st, unit="A", tags=False):
    poly(ax, m.OUT_U, fc=st.frame, ec=st.edge, lw=0.9, z=3)
    poly(ax, m.IN_U, fc=PAPER, ec=st.edge, lw=0.6, z=4)
    for (tag, w_, s0, s1, note) in m.WINDOWS:
        draw_window(ax, w_, s0, s1, st, tag if tags else None)
    for (x0, y0, x1, y1, kind) in m.PARTITIONS:
        wall(ax, x0, y0, x1, y1, st)
    # trim partitions that run past the angled rear wall
    poly(ax, [m.OUT_U[2], m.OUT_U[3], (m.OUT_U[3][0], m.OUT_U[3][1] + 4), (m.OUT_U[2][0], m.OUT_U[3][1] + 4)], fc=PAPER, ec="none", z=5.2)
    inner_n = [m.IN_U[2], m.IN_U[3]]
    poly(ax, [m.OUT_U[2], m.OUT_U[3], m.IN_U[3], m.IN_U[2]], fc=st.frame, ec=st.edge, lw=0.5, z=5.3)
    for (tag, w_, s0, s1, note) in m.WINDOWS:
        if w_ == "N":
            draw_window(ax, w_, s0, s1, st, tag if tags else None)
    for d in m.DOORS:
        draw_door(ax, d, st, tag=tags)
    u_stair(ax, m.SHAFT_U, st, treads=8 if unit == "A" else 7, up=(unit == "A"), dn=True, land=3.25)


def unit_fixtures(ax, st, labels=True):
    f = st.furn
    for t in m.TUBS:
        tub(ax, *t, st)
    for (cx, cy, fc_) in m.WCS:
        wc(ax, cx, cy, st, facing=fc_)
    for l in m.LAVS:
        lav(ax, *l, st)
    rect(ax, *m.WD[:2], *m.WD[2:], fc=PAPER, ec=f, lw=0.6, z=6)
    ax.add_patch(plt.Circle(((m.WD[0] + m.WD[2]) / 2, (m.WD[1] + m.WD[3]) / 2), 0.8, fc="none", ec=f, lw=0.4, zorder=7))
    rect(ax, *m.AHU[:2], *m.AHU[2:], fc=PAPER, ec=f, lw=0.6, z=6)
    line(ax, [m.AHU[:2], m.AHU[2:]], lw=0.3, color=f, z=7)
    line(ax, [(m.AHU[0], m.AHU[3]), (m.AHU[2], m.AHU[1])], lw=0.3, color=f, z=7)
    wd = WOOD if not st.bg else PAPER
    rect(ax, m.KIT_BASE[0], m.KIT_BASE[1], m.KIT_BASE[2], m.FRIDGE[1], fc=wd, ec=f, lw=0.6, z=5)
    rect(ax, *m.RANGE[:2], *m.RANGE[2:], fc=PAPER, ec=f, lw=0.6, z=6)
    for cy in (m.RANGE[1] + 0.65, m.RANGE[1] + 1.85):
        for cx in (m.RANGE[0] + 0.55, m.RANGE[0] + 1.5):
            ax.add_patch(plt.Circle((cx, cy), 0.3, fc="none", ec=f, lw=0.4, zorder=7))
    rect(ax, *m.FRIDGE[:2], *m.FRIDGE[2:], fc=PAPER, ec=f, lw=0.6, z=6)
    rect(ax, *m.ISLAND_TOP[:2], *m.ISLAND_TOP[2:], fc=wd, ec=f, lw=0.6, z=5)
    line(ax, [(m.ISLAND[2], m.ISLAND[1]), (m.ISLAND[2], m.ISLAND[3])], lw=0.3, color=f, ls=(0, (2, 2)), z=6)
    lav(ax, *m.ISL_SINK, st)
    rect(ax, *m.ISL_DW[:2], *m.ISL_DW[2:], fc=PAPER, ec=f, lw=0.5, z=6)
    rect(ax, *m.PANEL[:2], *m.PANEL[2:], fc=f, ec=f, lw=0.4, z=7)
    ax.add_patch(plt.Circle(m.WH_UNIT, m.WH_PAN_R, fc=PAPER, ec=f, lw=0.3, ls=(0, (2, 2)), zorder=6))
    ax.add_patch(plt.Circle(m.WH_UNIT, m.WH_R, fc=PAPER, ec=f, lw=0.6, zorder=6))
    if labels and not st.bg:
        txt(ax, (m.FRIDGE[0] + m.FRIDGE[2]) / 2, (m.FRIDGE[1] + m.FRIDGE[3]) / 2, "REF", size=4.0, color=GREY, z=8)
        txt(ax, (m.ISL_DW[0] + m.ISL_DW[2]) / 2, (m.ISL_DW[1] + m.ISL_DW[3]) / 2, "DW", size=3.8, color=GREY, z=8)
        txt(ax, (m.WD[0] + m.WD[2]) / 2, (m.WD[1] + m.WD[3]) / 2, "W/D", size=3.8, color=GREY, z=8)
        txt(ax, (m.AHU[0] + m.AHU[2]) / 2, (m.AHU[1] + m.AHU[3]) / 2, "AHU", size=3.4, color=INK, z=8, weight="bold")
        txt(ax, *m.WH_UNIT, "WH", size=3.6, color=INK, z=8, weight="bold")


def unit_furniture(ax, st):
    f = st.furn
    for (rm, kind, pts) in m.FURN:
        poly(ax, pts, fc=st.fill, ec=f, lw=0.5, z=5)
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        if kind == "bed":
            x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
            if m.BED_HEAD[rm] == "W":
                rect(ax, x0, y0, x0 + 1.5, y1, fc="#e4e6e9", ec=f, lw=0.4, z=6)
            else:
                rect(ax, x0, y0, x1, y0 + 1.5, fc="#e4e6e9", ec=f, lw=0.4, z=6)
        if kind == "sofa":
            rect(ax, min(xs), max(ys) - 0.75, max(xs), max(ys), fc="#e4e6e9", ec=f, lw=0.4, z=6)
    for rm, c in m.CHAIRS.items():
        xs, ys = [p[0] for p in c], [p[1] for p in c]
        ax.add_patch(plt.Circle(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2), 0.75, fc=PAPER, ec=f, lw=0.4, zorder=5))
    for (sx, sy) in m.STOOLS:
        ax.add_patch(plt.Circle((sx, sy), 0.55, fc=PAPER, ec=f, lw=0.4, zorder=6))


ROOM_LABELS = {
    "BEDROOM 1": (12.4, 16.6), "BEDROOM 2": (14.0, 32.6), "BEDROOM 3": (32.56, 26.2), "LIVING / KITCHEN": (33.2, 16.2),
    "HALL": (21.42, 25.4), "BATH 1": (18.25, 24.1), "BATH 2": (24.92, 32.83), "BATH 3": (43.04, 26.85),
    "CLOSET 1": (10.4, 22.9), "CLOSET 2": (10.5, 25.3), "CLOSET 3": (28.0, 32.6),
}


def unit_labels(ax, st, sizes=True):
    if st.bg:
        for k, (x, y) in ROOM_LABELS.items():
            rot = 90 if k.startswith("BATH") or k == "HALL" else 0
            txt(ax, x, y, k.replace("LIVING / KITCHEN", "LIVING").replace("CLOSET ", "CL "), size=4.2, color=st.text, z=6.5, rot=rot)
        return
    for k in ("BEDROOM 1", "BEDROOM 2", "BEDROOM 3"):
        x, y = ROOM_LABELS[k]
        w, d = m.room_dims(k)
        room(ax, x, y, k, f"{ftin(w)} x {ftin(d)}" if sizes else None, f"{m.area(k):.0f} sf" if sizes else None, fs=5.4)
    x, y = ROOM_LABELS["LIVING / KITCHEN"]
    w, d = m.room_dims("LIVING / KITCHEN")
    room(ax, x, y, "LIVING", f"{ftin(w)} x {ftin(d)} with kitchen" if sizes else None, f"{m.area('LIVING / KITCHEN'):.0f} sf" if sizes else None, fs=5.4)
    txt(ax, 23.7, 11.7, "KITCHEN", size=4.4, weight="bold", z=9)
    for k in ("BATH 1", "BATH 2", "BATH 3"):
        txt(ax, *ROOM_LABELS[k], k, size=4.2, weight="bold", z=9, rot=90)
    txt(ax, *ROOM_LABELS["HALL"], "HALL", size=4.0, color=GREY, rot=90)
    for k in ("CLOSET 1", "CLOSET 2", "CLOSET 3"):
        txt(ax, *ROOM_LABELS[k], "CLOSET", size=3.6, color=GREY)
    txt(ax, (m.SHAFT_U[0] + m.SHAFT_U[1]) / 2, 12.2, "COMMON\nSTAIR", size=4.4, color=GREY)


def porch(ax, bg=False):
    c = BG_EDGE if bg else INK
    x0, y0, x1, y1 = m.PORCH
    rect(ax, x0, y0, x1, y1, fc=PAPER if bg else WOOD, ec=c, lw=0.7, z=3)
    if not bg:
        for x in np.arange(x0 + 0.5, x1, 0.5):
            line(ax, [(x, y0), (x, y1)], lw=0.15, color=LIGHT, z=3)
    line(ax, [(x0 + 0.2, y1), (x0 + 0.2, y0 + 0.2), (x1 - 0.2, y0 + 0.2), (x1 - 0.2, y1)], lw=1.0, color=c, z=6)


def unit_plan(ax, mode="arch", unit="A", furniture=True, labels=True, tags=False, sizes=True, with_porch=True):
    st = Style(mode)
    if with_porch:
        porch(ax, bg=st.bg)
    unit_shell(ax, st, unit, tags=tags)
    unit_fixtures(ax, st, labels=labels)
    if furniture:
        unit_furniture(ax, st)
    if labels:
        unit_labels(ax, st, sizes=sizes)
    return st


def site_work(ax, bg=False, labels=False):
    """Apron, entry landing, trash bay, wing walls, trench drain and heat-pump pads."""
    c = BG_EDGE if bg else INK
    poly(ax, m.APRON, fc="#d5dbe2" if not bg else "#eceef1", ec=c, lw=0.6, z=2)
    poly(ax, m.WALK, fc="#e7eaee" if not bg else "#f3f4f6", ec=c, lw=0.5, z=2)
    rect(ax, *m.TRASH[:2], *m.TRASH[2:], fc="#dfe3d6" if not bg else "#f3f4f6", ec=c, lw=0.6, z=3)
    if not bg:
        for i in range(4):
            rect(ax, m.TRASH[0] + 0.25 + i * 1.62, m.TRASH[1] + 0.15, m.TRASH[0] + 1.55 + i * 1.62, m.TRASH[3] - 0.25,
                 fc=PAPER, ec=GREY, lw=0.4, z=4)
    line(ax, m.WING_W, lw=2.2, color=CONC if not bg else BG_WALL, z=3)
    line(ax, m.WING_E, lw=1.8, color=CONC if not bg else BG_WALL, z=3)
    line(ax, [(m.OPEN[0], m.YF - 0.6), (m.OPEN[1], m.YF - 0.6)], lw=1.4, color=BLUE if not bg else BG_EDGE, z=6)     # trench drain
    t = -WEST_LEAN
    w, d = m.HP_SIZE
    for (hx, hy) in m.HP:
        p_ = [(-d / 2, -w / 2), (d / 2, -w / 2), (d / 2, w / 2), (-d / 2, w / 2)]
        poly(ax, [(hx + px * math.cos(t) - py * math.sin(t), hy + px * math.sin(t) + py * math.cos(t)) for px, py in p_],
             fc=PAPER, ec=c, lw=0.6, z=4)
