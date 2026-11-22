"""Plumbing sheets, Rev E: P-101 garage level and under-slab, P-102 Unit A, P-103 Unit B,
P-201 risers and schedules. PRELIMINARY: 2018 IPC, sizes for the plumber and engineer to confirm.

Every pipe is drawn to a real position taken from model.py (fixtures, stacks, chases, utility room,
water entry, sewer exit, drain outlet). Run lengths and inverts are computed here from those points.
"""
import math

from matplotlib.patches import Circle, Rectangle

from common import *  # noqa: F401,F403
import model as m
from plans import *  # noqa: F401,F403

SAN, VENT, CW, HW, STORM, APC = "#2e7d32", "#2e7d32", "#1f5fa8", "#c0392b", "#0e8f9c", "#7b3fa0"
DASH_V = (0, (2.2, 1.6))        # vents
DASH_H = (0, (5, 1.8))          # hot water
DASH_OH = (0, (1.2, 1.4))       # overhead (in the soffit)
DASH_UP = (0, (4, 2))           # pipe above (in the floor trusses over the garage)
DASH_FR = (0, (6, 2, 1, 2))     # French drain (perforated)
_cw = math.cos(WEST_LEAN)


def fth(v):
    """Feet-inches to the nearest 1/2 in."""
    half = round(abs(v) * 24)
    f, r = divmod(half, 24)
    i, h = divmod(r, 2)
    return f"{f}'-{i}{' 1/2' if h else ''}\""


def plen(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


# ----------------------------------------------------------------------------
# Design numbers (all from the model)
# ----------------------------------------------------------------------------
SLOPE = 0.25 / 12                                    # 1/4 in. per ft
A1, A2, S3B = m.CHASE_1, m.CHASE_2, m.CHASE_3        # stack bases at the garage slab
YM = A1[1]                                           # building drain runs along this line under the slab
TURN = (m.SEWER_OUT_X, YM)                           # turns south here (floor cleanout)
WYE = (m.SEWER_OUT_X, S3B[1] - (S3B[0] - m.SEWER_OUT_X))   # stack 3 branch joins at 45 deg
BLDG = (m.SEWER_OUT_X, m.YF)                         # building line, under the garage opening
CO2 = m.SEWER_CO                                     # two-way cleanout on the lot
INV_START = m.EL_GAR - 1.0                           # 12 in. below the slab at the far end
_runs = [("A", "Base of chase 1 (stack 1)", A1), ("B", "Base of chase 2 (stack 2)", A2),
         ("C", "Turn south, floor cleanout", TURN), ("D", "Wye: branch from stack 3", WYE),
         ("E", "Building line, under opening", BLDG), ("F", "Two-way cleanout on the lot", CO2)]
INV = {}
_sta, _prev = 0.0, A1
for _k, _name, _p in _runs:
    _sta += math.dist(_prev, _p)
    INV[_k] = dict(name=_name, p=_p, sta=_sta, inv=INV_START - _sta * SLOPE)
    _prev = _p
BR3_LEN = math.dist(S3B, WYE)
INV["S3"] = dict(name="Base of stack 3 (utility room)", p=S3B, sta=BR3_LEN, inv=INV["D"]["inv"] + BR3_LEN * SLOPE)
INV_SLEEVE = 923.0                                   # Unit A bath 2 drain through the garage rear wall (approx.)
FLOOR_DRAIN = (m.CHASE_3[0] + 0.2, (m.WH[0][1] + m.WH[1][1]) / 2)

# storm
OFFD = 1.0                                           # French drain drawn 12 in. off the wall face (position per S-102)
FD_SW = (m.xw_o(m.YF) - OFFD / _cw, m.YF)
FD_NW = (m.xw_o(m.Y_GR_O + OFFD) - OFFD / _cw, m.Y_GR_O + OFFD)
FD_NE = (m.XE + OFFD, m.Y_GR_O + OFFD)
FD_SE = (m.XE + OFFD, m.YF)
FD_BEND = (m.XE + OFFD, -2.6)
FD_PATH = [FD_SW, FD_NW, FD_NE, FD_SE, FD_BEND, m.DRAIN_OUT]
FD_LEN = plen(FD_PATH)
FD_FALL = (m.EL_DRAIN_HI - m.EL_DRAIN_OUT) / FD_LEN


def fd_inv(i):
    return m.EL_DRAIN_HI - plen(FD_PATH[:i + 1]) * FD_FALL


TRENCH_Y = m.YF - 0.6
TRENCH_OUT = [(m.OPEN[1], TRENCH_Y), (m.OPEN[1] + 0.6, TRENCH_Y - 0.6), (m.OPEN[1] + 0.6, 0.0), (m.DRAIN_OUT[0] - 0.9, m.DRAIN_OUT[1] + 0.75)]
EL_OPEN = m.EL_GAR - (m.Y_GR_I - m.YF) / 8 / 12      # slab at the opening (1/8 in./ft fall to the trench drain)


def apron_el(x, y):
    """Approx. apron surface: straight grade from the garage opening to the street edge (C-105 governs)."""
    t = (TRENCH_Y - y) / (TRENCH_Y - PAVE_N)
    return EL_OPEN + (street_el(x) - EL_OPEN) * t


# water
SERV_X = (47.4, 48.4)                                # the two services in the east side yard (A, B)
SERV_LEN = [abs(m.WATER_METERS[i][0] - SERV_X[i]) + (m.WATER_ENTRY[1] - m.WATER_METERS[i][1]) + (SERV_X[i] - m.XE) for i in (0, 1)]
HB = (m.XE, m.UTIL[2] + 0.6)                         # frost-proof hose bibb, east wall, in Unit A's floor rim
EL_HB = m.EL_A - 0.75 * m.IN - m.TRUSS_A / 2
BOARD_B = (m.UTIL[0] + 0.25, m.UTIL[0] + 2.05)       # manifold boards on the utility room south wall (x0, x1)
BOARD_A = (m.UTIL[0] + 2.25, m.UTIL[0] + 4.05)
RISE_A = ((BOARD_A[0] + BOARD_A[1]) / 2, m.UTIL[2] + 0.55)       # Unit A lines go up through the ceiling here
RISE_B = (m.STACK_3[0] - 1.3, m.B3_Y1 + m.PART + 0.55)           # Unit B lines rise in the bath 3 pipe space

# fixture units (2018 IPC Table 709.1 and Table E103.3(2))
DFU = dict(bath=5, sink=2, dw=2, cw=2, fd=2)
DFU_FLAT = 3 * DFU["bath"] + DFU["sink"] + DFU["dw"] + DFU["cw"]
DFU_S1 = 2 * DFU["bath"]
DFU_S2 = 2 * (DFU["bath"] + DFU["sink"] + DFU["dw"] + DFU["cw"])
DFU_S3 = 2 * DFU["bath"]
DFU_BLDG = 2 * DFU_FLAT + DFU["fd"]
WSFU = dict(bath=3.6, sink=1.4, dw=1.4, cw=1.4, hb=2.5)
WSFU_B = 3 * WSFU["bath"] + WSFU["sink"] + WSFU["dw"] + WSFU["cw"]
WSFU_A = WSFU_B + WSFU["hb"]
GPM_A, GPM_B = 18.6, 17.5                            # IPC Table E103.3(3), flush-tank column, interpolated


# ----------------------------------------------------------------------------
# Drawing helpers
# ----------------------------------------------------------------------------
def u(ax, inches):
    """Paper inches -> axes units (plan feet on a plan, inches on the sheet background)."""
    return inches * getattr(ax, "fpi", 1.0)


def pipe(ax, pts, color, lw=1.3, ls="-", z=10):
    line(ax, pts, color=color, lw=lw, ls=ls, z=z)


def lab(ax, x, y, s, color=INK, size=4.8, weight="bold", box=True, **kw):
    return txt(ax, x, y, s, size=size, color=color, weight=weight, box=box, z=14, **kw)


def lead(ax, p0, p1, color=INK, dot=True):
    line(ax, [p0, p1], color=color, lw=0.35, z=13)
    if dot:
        ax.add_patch(Circle(p1, u(ax, 0.012), fc=color, ec=color, lw=0.3, zorder=13))


def note(ax, x, y, s, to=None, color=INK, size=4.8, ha="left", va="center", weight="normal", frm=None):
    """Text with an optional leader to a point (or list of points). `frm` = where the leader leaves the text."""
    t = txt(ax, x, y, s, size=size, color=color, ha=ha, va=va, weight=weight, box=True, z=14)
    if to is not None:
        for p in (to if isinstance(to, list) else [to]):
            lead(ax, frm or (x, y), p, color)
    return t


def stack_dot(ax, p, color=SAN, fill=True, r=0.034):
    ax.add_patch(Circle(p, u(ax, r), fc=color if fill else PAPER, ec=color, lw=1.0, zorder=12))


def cleanout(ax, x, y, color=SAN, s="CO", r=0.062):
    k = u(ax, r)
    ax.add_patch(Rectangle((x - k, y - k), 2 * k, 2 * k, fc=PAPER, ec=color, lw=1.0, zorder=12))
    txt(ax, x, y, s, size=3.3, color=color, weight="bold", z=13)


def keynote(ax, x, y, n, color=INK, r=0.075):
    k = u(ax, r)
    pts = [(x + k * math.cos(math.radians(a)), y + k * math.sin(math.radians(a))) for a in range(0, 360, 60)]
    poly(ax, pts, fc=PAPER, ec=color, lw=0.8, z=15)
    txt(ax, x, y, str(n), size=4.6, color=color, weight="bold", z=16)


def valve(ax, x, y, color=CW, r=0.045, rot=0):
    k = u(ax, r)
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    for sg in (-1, 1):
        pts = [(0, 0), (sg * k, 0.6 * k), (sg * k, -0.6 * k)]
        poly(ax, [(x + px * c - py * s, y + px * s + py * c) for px, py in pts], fc=PAPER, ec=color, lw=0.8, z=13)


def access_panel(ax, x, y, w=1.17, d=0.3, horiz=True, tag=None, dx=0.0, dy=0.0):
    """Access panel in a wall face: a purple bar the real width of the panel (14 in. default)."""
    if horiz:
        rect(ax, x - w / 2, y - d / 2, x + w / 2, y + d / 2, fc=APC, ec=APC, lw=0.5, z=12)
    else:
        rect(ax, x - d / 2, y - w / 2, x + d / 2, y + w / 2, fc=APC, ec=APC, lw=0.5, z=12)
    if tag:
        lab(ax, x + dx, y + dy, tag, APC, size=4.4)


def box_sym(ax, x, y, s, color, r=0.06):
    """Small lettered box: washer box (WB), ice-maker box (IM), floor drain (FD) ..."""
    k = u(ax, r)
    ax.add_patch(Rectangle((x - k * 1.25, y - k), 2.5 * k, 2 * k, fc=PAPER, ec=color, lw=0.9, zorder=12))
    txt(ax, x, y, s, size=3.4, color=color, weight="bold", z=13)


def riser(ax, p, color, r=0.03):
    """Riser / drop in a wall: a small filled dot on the line."""
    ax.add_patch(Circle(p, u(ax, r), fc=color, ec=color, lw=0.4, zorder=12))


def fit_title(fig, bg, title, maxw=TB_W - 0.34):
    """common.new_sheet prints the title on one line: shrink it when it is wider than the title block."""
    r = fig.canvas.get_renderer()
    for t in bg.texts:
        if t.get_text() == title.upper():
            while t.get_window_extent(r).width / fig.dpi > maxw and t.get_fontsize() > 5.5:
                t.set_fontsize(t.get_fontsize() - 0.2)


def frame(fig, view, left, bottom, fpi=FPI, street=True, lot=True, north=None, bar=None, street_label=None):
    """Plan axes like plans.plan_frame, but placed where the sheet layout needs it."""
    vx, vy = view
    ax = plan_axes(fig, left, bottom, vx, vy, fpi)
    if lot:
        line(ax, [LOT_NW, LOT_SW, LOT_SE, LOT_NE, LOT_NW], color=ACCENT, lw=0.9, ls=(0, (9, 2.5, 1.5, 2.5)), z=5.25)
    if street and vy[0] < PAVE_N:
        rect(ax, vx[0], vy[0], vx[1], PAVE_N, fc="#e6e8eb", ec="none", z=1)
        line(ax, [(vx[0], PAVE_N), (vx[1], PAVE_N)], color=GREY, lw=0.6, z=2)
        if street_label:
            txt(ax, street_label[0], street_label[1], "BAIRD STREET  (±14' pavement)", size=5.4, color=GREY, weight="bold")
    if north:
        north_arrow(ax, north[0], north[1], 1.8 * fpi / FPI, 6.5)
    if bar:
        scale_bar(ax, bar[0], bar[1], 16, 4, 0.42 * fpi / FPI, size=5.2)
    return ax


def strip_texts(ax, n0=0):
    for t in list(ax.texts)[n0:]:
        t.remove()


def legend(bg, x, y, rows, title="LEGEND", dy=0.168, fs=5.4, lw_=0.55):
    """rows: ("line", color, lw, ls, label) or ("sym", fn, label); fn(bg, cx, cy) draws the symbol."""
    bg.text(x, y, title, fontsize=6.6, fontweight="bold", color=INK, va="center")
    y -= 0.21
    for row in rows:
        if row[0] == "line":
            _, color, lw, ls, label = row
            bg.plot([x, x + lw_], [y, y], color=color, lw=lw, ls=ls, solid_capstyle="butt")
        else:
            _, fn, label = row
            fn(bg, x + lw_ / 2, y)
        bg.text(x + lw_ + 0.1, y, label, fontsize=fs, color=INK, va="center")
        y -= dy
    return y


def heading(bg, x, y, s, sub=None, size=9.0):
    bg.text(x, y, s.upper(), fontsize=size, fontweight="bold", color=INK, va="bottom")
    if sub:
        bg.text(x, y - 0.05, sub, fontsize=size - 3.2, color=GREY, va="top")


def small_lines(bg, x, y, lines, fs=5.4, dy=0.135, color=INK):
    for ln in lines:
        bold = ln.startswith("*")
        bg.text(x, y, ln.lstrip("*"), fontsize=fs, color=color, va="top", fontweight="bold" if bold else "normal")
        y -= dy * (ln.count("\n") + 1)
    return y


# ----------------------------------------------------------------------------
# P-101  Garage level and under-slab
# ----------------------------------------------------------------------------
def utility_enlarged(fig, bg, left, bottom):
    """Utility room at 3/8 in. scale: where each piece of equipment stands."""
    fpi = 12 / 4.5
    view = ((m.UTIL[0] - 1.25, m.XE + 1.0), (m.UTIL[2] - 0.75, m.Y_GR_O + 0.45))
    ax = plan_axes(fig, left, bottom, view[0], view[1], fpi)
    lower_plan(ax, "bg", cars=False)
    strip_texts(ax)
    for t in ax.patches:
        t.set_clip_on(True)
    x0, x1, y0, y1 = m.UTIL
    # shared pan under both heaters, heaters
    pan = (m.WH[0][0] - m.WH_R - 0.1, y0 + 0.03, x1 - 0.02, m.WH[1][1] + m.WH_R + 0.1)
    rect(ax, pan[0], pan[1], pan[2], pan[3], fc="#fbf6e9", ec=GREY, lw=0.6, z=5.5, ls=(0, (3, 1.5)))
    for i, (wx, wy) in enumerate(m.WH):
        ax.add_patch(Circle((wx, wy), m.WH_R, fc=PAPER, ec=INK, lw=0.8, zorder=6))
        txt(ax, wx, wy + 0.12, f"WH-{'AB'[i]}", size=5.0, weight="bold", z=8)
        txt(ax, wx, wy - 0.3, "80 gal", size=4.2, color=GREY, z=8)
        ax.add_patch(Circle((wx - 0.55, wy + (0.62 if i else -0.62)), 0.3, fc=PAPER, ec=CW, lw=0.8, zorder=9))   # expansion tank
        txt(ax, wx - 0.55, wy + (0.62 if i else -0.62), "ET", size=3.4, color=CW, weight="bold", z=10)
    # sanitary: stack 3, branch, floor drain
    pipe(ax, [S3B, WYE], SAN, 2.2)
    stack_dot(ax, S3B, SAN, r=0.05)
    cleanout(ax, S3B[0] + 0.62, S3B[1] + 0.05)
    fdx, fdy = FLOOR_DRAIN
    jx = S3B[0] - (S3B[1] - fdy)
    pipe(ax, [(fdx, fdy), (jx, fdy)], SAN, 1.3)
    rect(ax, fdx - 0.25, fdy - 0.25, fdx + 0.25, fdy + 0.25, fc=PAPER, ec=SAN, lw=1.0, z=12)
    line(ax, [(fdx - 0.25, fdy - 0.25), (fdx + 0.25, fdy + 0.25)], color=SAN, lw=0.6, z=13)
    line(ax, [(fdx - 0.25, fdy + 0.25), (fdx + 0.25, fdy - 0.25)], color=SAN, lw=0.6, z=13)
    # T&P relief lines to the floor drain
    for (wx, wy) in m.WH:
        pipe(ax, [(wx - m.WH_R * 0.8, wy + (-0.45 if wy > fdy else 0.45)), (fdx + 0.32, fdy + (0.12 if wy > fdy else -0.12))], HW, 0.7, (0, (1, 1)))
    # services in, up in the corner behind the heaters, overhead to the boards
    ey = m.WATER_ENTRY[1]
    for i, dy in enumerate((-0.11, 0.11)):
        pipe(ax, [(view[0][1], ey + dy), (x1 - 0.22, ey + dy)], CW, 1.5)
        riser(ax, (x1 - 0.22, ey + dy), CW, 0.022)
    bx = (BOARD_A, BOARD_B)
    pipe(ax, [(x1 - 0.22, ey - 0.11), (m.WH[0][0] - 1.25, ey - 0.11), (BOARD_A[1] - 0.2, y0 + 0.5), (BOARD_A[1] - 0.2, y0 + 0.3)], CW, 1.0, DASH_UP)
    pipe(ax, [(x1 - 0.22, ey + 0.11), (m.WH[0][0] - 1.25, ey + 0.11), (BOARD_B[1] - 0.2, ey + 0.11), (BOARD_B[1] - 0.2, y0 + 0.3)], CW, 1.0, DASH_UP)
    # boards
    for (b0, b1), nm in ((BOARD_A, "A"), (BOARD_B, "B")):
        rect(ax, b0, y0, b1, y0 + 0.3, fc="#e9eef6", ec=CW, lw=0.9, z=11)
        txt(ax, (b0 + b1) / 2, y0 + 0.15, f"BOARD {nm}", size=4.0, color=CW, weight="bold", z=12)
    # heater connections (overhead): cold to the heater, hot back to the board
    a_c = [(BOARD_A[1] - 0.45, y0 + 0.3), (BOARD_A[1] - 0.45, y0 + 0.78), (m.WH[0][0] - 0.75, y0 + 0.78)]
    a_h = [(BOARD_A[1] - 0.7, y0 + 0.3), (BOARD_A[1] - 0.7, y0 + 1.0), (m.WH[0][0] - 0.55, y0 + 1.0), (m.WH[0][0] - 0.2, m.WH[0][1])]
    pipe(ax, a_c, CW, 0.9)
    pipe(ax, a_h, HW, 0.9, DASH_H)
    by = m.WH[1][1] + 0.55
    b_c = [(BOARD_B[0] + 0.75, y0 + 0.3), (BOARD_B[0] + 0.75, by + 0.12), (m.WH[1][0] - 0.8, by + 0.12)]
    b_h = [(BOARD_B[0] + 0.5, y0 + 0.3), (BOARD_B[0] + 0.5, by - 0.12), (m.WH[1][0] - 0.75, by - 0.12), (m.WH[1][0] - 0.25, m.WH[1][1])]
    pipe(ax, b_c, CW, 0.9)
    pipe(ax, b_h, HW, 0.9, DASH_H)
    # home-runs leaving the room
    for p, c in ((RISE_A, "A"),):
        ax.add_patch(Circle(p, 0.2, fc=PAPER, ec=CW, lw=1.0, zorder=12))
        txt(ax, p[0], p[1], c, size=4.2, color=CW, weight="bold", z=13)
    rb = (BOARD_B[0] + 0.2, y1 - 0.25)
    pipe(ax, [(BOARD_B[0] + 0.2, y0 + 0.3), rb], CW, 0.9)
    pipe(ax, [(BOARD_B[0] + 0.36, y0 + 0.3), (rb[0] + 0.16, rb[1])], HW, 0.9, DASH_H)
    ax.add_patch(Circle((rb[0] + 0.08, rb[1]), 0.2, fc=PAPER, ec=CW, lw=1.0, zorder=12))
    txt(ax, rb[0] + 0.08, rb[1], "B", size=4.2, color=CW, weight="bold", z=13)
    # keys
    keynote(ax, x1 + 0.55, ey + 0.55, 1, CW)
    keynote(ax, (BOARD_A[0] + BOARD_A[1]) / 2 + 0.45, y0 - 0.35, 2, CW)
    keynote(ax, (BOARD_B[0] + BOARD_B[1]) / 2, y0 - 0.35, 2, CW)
    keynote(ax, RISE_A[0] - 0.45, RISE_A[1] + 0.05, 3, CW)
    keynote(ax, rb[0] + 0.62, rb[1] - 0.05, 4, CW)
    keynote(ax, m.WH[0][0] + 0.5, m.WH[0][1] - 0.45, 5)
    keynote(ax, m.WH[1][0] + 0.5, m.WH[1][1] + 0.45, 5)
    keynote(ax, fdx - 0.15, fdy - 0.62, 6, SAN)
    keynote(ax, S3B[0] + 0.62, S3B[1] - 0.52, 7, SAN)
    keynote(ax, pan[0] + 0.25, pan[3] - 0.22, 8, GREY)
    # room dimensions
    dim(ax, (x0, y0 - 0.02), (x1, y0 - 0.02), -0.62 * 0 - 0.0001, fth(x1 - x0), size=4.6) if False else None
    txt(ax, (x0 + x1) / 2 - 0.9, (y0 + y1) / 2 + 0.55, f"UTILITY ROOM (heated)\n{fth(x1 - x0)} x {fth(y1 - y0)}", size=4.4, color=GREY, z=8)
    return ax


def sheet_p101(pdf):
    title = "Plumbing: garage level and under-slab"
    notes = [
        ("Basis", [
            "2018 IPC. Sizes, slopes and inverts are",
            "PRELIMINARY: the plumber and the",
            "engineer confirm them. Elevations are",
            "from LiDAR, not a survey.",
        ]),
        ("Sanitary", [
            "4 in. building drain under the garage",
            "slab at 1/4 in. per ft, PVC schedule 40",
            "DWV, bedded in the stone under the slab.",
            "Cleanout at the base of every stack, at",
            "the turn, and a two-way cleanout outside.",
            "No traps and no fixtures in the open",
            "garage: nothing there holds water.",
        ]),
        ("Water", [
            "NO WATER PIPING IN THE OPEN GARAGE.",
            "The two 1 in. services come in buried,",
            "through the east wall, straight into the",
            "heated utility room. Everything after",
            "that is inside heated space (P-102, P-103).",
        ]),
        ("Storm: gravity only", [
            "NO SUMP PUMP. French drain and trench",
            "drain run by gravity to one outlet at the",
            "street edge. The outlet is only about",
            f"{(m.EL_DRAIN_OUT - street_el(m.DRAIN_OUT[0])) * 12:.0f} in. above the pavement: the survey",
            "must confirm it before the footings go in.",
        ]),
        ("Find out first", [
            "MUB: sewer main location and depth,",
            "tap, static water pressure, meter pits.",
            "City Engineer: storm outlet at the street.",
        ]),
    ]
    fig, bg = new_sheet("P-101", title, "3/16\" = 1'-0\"", notes)
    fit_title(fig, bg, title)
    L = MARGIN + 0.2
    heading(bg, L, 10.2, "Garage level and under-slab plumbing", "3/16\" = 1'-0\" · sizes and inverts preliminary · north is up the page (true north: see arrow)", 8.6)

    view = ((2.5, 53.5), (-8.5, 42.6))
    ax = frame(fig, view, 4.07, 0.5, north=(51.0, 39.4), bar=(5.0, -7.9), street_label=(26.0, -7.75))
    poly(ax, m.SOG, fc="#f7f3ec", ec=BG_EDGE, lw=0.5, z=1.5, ls=(0, (4, 2)))
    site_work(ax, bg=True)
    n0 = len(ax.texts)
    lower_plan(ax, "bg", cars=False)
    strip_texts(ax, n0)
    txt(ax, 22.0, 13.2, "OPEN GARAGE  (unheated, EL 914.5)", size=5.0, color="#8a9199", z=4)
    txt(ax, 40.6, 14.0, "STAIR", size=4.4, color="#8a9199", z=4)
    txt(ax, 51.1, 14.0, "LOT LINE", size=4.6, color=ACCENT, rot=90)
    txt(ax, 21.0, -0.75, "FRONT LOT LINE = RIGHT-OF-WAY LINE", size=4.6, color=ACCENT)
    txt(ax, 13.2, 33.4, "UNIT A SLAB ON GRADE ABOVE\n(EL 925.5; earth below it)", size=4.4, color=EARTH, z=4)

    # ---------------- storm ----------------
    pipe(ax, FD_PATH[:4], STORM, 1.3, DASH_FR)
    pipe(ax, FD_PATH[3:], STORM, 1.3)
    pipe(ax, [(m.OPEN[0], TRENCH_Y), (m.OPEN[1], TRENCH_Y)], STORM, 2.6)
    pipe(ax, TRENCH_OUT, STORM, 1.3)
    ox, oy = m.DRAIN_OUT
    poly(ax, [(ox - 0.75, oy), (ox + 0.75, oy), (ox, oy - 1.3)], fc=STORM, ec=STORM, z=12)
    for i, (p, nm, dx, dy, ha) in enumerate(((FD_SW, "high point", -0.2, -1.5, "center"), (FD_NW, "", 1.2, 1.15, "left"),
                                             (FD_NE, "", 0.9, 1.15, "left"), (FD_SE, "", 1.0, 0.0, "left"))):
        cleanout(ax, p[0], p[1], STORM)
        lab(ax, p[0] + dx, p[1] + dy, f"INV {fd_inv(i):.2f}" + (f"\n{nm}" if nm else ""), STORM, size=4.4, ha=ha)
    note(ax, 3.0, 22.6, "FRENCH DRAIN\n4 in. perforated,\nstone + fabric,\nat the footing\n(S-102).\nCO = cleanout\nriser to grade\nat each corner", color=STORM, size=4.4)
    note(ax, 13.6, 7.7, f"TRENCH DRAIN across the opening, {ftin(m.OPEN_W)}, traffic-rated grate,\nfalls east. 4 in. outlet at the east end, in solid pipe to the outlet",
         color=STORM, size=4.4)
    note(ax, 48.0, 5.6, "4 in. SOLID\nfrom the\nFrench drain\nto the outlet", to=(FD_SE[0], 5.6), color=STORM, size=4.4, frm=(47.9, 5.6))
    note(ax, 38.6, -4.4, f"GRAVITY OUTLET at the street edge\nINV {m.EL_DRAIN_OUT:.1f} (pavement about {street_el(ox):.1f}).\nNO SUMP PUMP.",
         to=(ox - 0.5, oy - 0.2), color=STORM, size=4.6, weight="bold", frm=(44.3, -4.9))

    # ---------------- water ----------------
    for i, (mx, my) in enumerate(m.WATER_METERS):
        rect(ax, mx - 0.5, my - 0.5, mx + 0.5, my + 0.5, fc=PAPER, ec=CW, lw=1.0, z=11)
        txt(ax, mx, my, "AB"[i], size=3.6, color=CW, weight="bold", z=12)
        pipe(ax, [(mx, my - 0.5), (mx, PAVE_N - 0.6)], CW, 1.0, (0, (2, 1.5)))
        ey = m.WATER_ENTRY[1] + (-0.11, 0.11)[i]
        pipe(ax, [(mx, my + 0.5), (mx, 0.2), (SERV_X[i], 1.2), (SERV_X[i], ey), (m.XE_GI - 0.2, ey)], CW, 1.3, (0, (6, 2)))
    note(ax, 49.4, -3.7, "2 METER PITS\n(MUB), one\nper flat", color=CW, size=4.4, ha="left")
    note(ax, 51.4, 24.0, f"TWO 1 in.\nSERVICES,\nburied 42 in.\nmin. (C-106).\nEnter at\nEL {m.EL_WATER_ENTRY:.1f},\n{elev(m.XE + 1, m.WATER_ENTRY[1]) - m.EL_WATER_ENTRY:.1f} ft below\ngrade, sleeved\nand sealed", color=CW, size=4.4, ha="center")
    ax.add_patch(Circle((HB[0] + 0.3, HB[1]), 0.3, fc=PAPER, ec=CW, lw=1.0, zorder=12))
    note(ax, 46.0, 33.3, f"FROST-PROOF HOSE BIBB in Unit A's\nfloor rim, EL {EL_HB:.1f} (about {EL_HB - elev(m.XE + 1, HB[1]):.0f} ft above\ngrade). Fed from Unit A, see P-102",
         to=(HB[0] + 0.45, HB[1] + 0.25), color=CW, size=4.4, ha="left", frm=(46.2, 32.5))
    lab(ax, 22.0, 15.6, "NO WATER PIPING IN THE OPEN GARAGE", CW, size=6.4)
    txt(ax, 22.0, 14.55, "It is unheated. Every water line is in the heated utility room or inside the flats.", size=4.6, color=CW, z=14)

    # ---------------- sanitary ----------------
    # stacks above and their offsets
    for st_, base in ((m.STACK_1, A1), (m.STACK_3, S3B)):
        pipe(ax, [st_, base], SAN, 1.2, DASH_UP)
        stack_dot(ax, st_, SAN, fill=False)
    # Unit A bath 2 under its slab on grade, through the wall in a sleeve
    s2 = m.STACK_2
    wcf = (m.WCS[1][0], m.WCS[1][1] - 1.0)
    tubd = ((m.TUBS[1][0] + m.TUBS[1][2]) / 2, m.TUBS[1][1] + 0.7)
    lavd = ((m.LAVS[1][0] + m.LAVS[1][2]) / 2, tubd[1])
    for p_ in ([wcf, s2], [tubd, lavd, (lavd[0] + 0.45, lavd[1]), (lavd[0] + 0.45, wcf[1] + 0.4)]):
        pipe(ax, p_, SAN, 0.9)
    pipe(ax, [s2, (s2[0], m.Y_GR_O)], SAN, 1.6)
    rect(ax, s2[0] - 0.3, m.Y_GR_I, s2[0] + 0.3, m.Y_GR_O, fc=PAPER, ec=SAN, lw=0.8, z=9)       # sleeve
    pipe(ax, [(s2[0], m.Y_GR_O), A2], SAN, 1.6)
    stack_dot(ax, s2, SAN, fill=False)
    # chases
    for c in (A1, A2):
        rect(ax, c[0] - 0.75, m.Y_GR_I - 1.17, c[0] + 0.75, m.Y_GR_I, fc="#e4efe4", ec=SAN, lw=0.7, z=8)
    # building drain
    main = [A1, A2, TURN, WYE, BLDG, CO2]
    pipe(ax, main, SAN, 2.4)
    pipe(ax, [S3B, WYE], SAN, 2.0)
    pipe(ax, [CO2, (CO2[0], -8.5)], SAN, 2.0, (0, (4, 2)))
    for c in (A1, A2, S3B):
        stack_dot(ax, c, SAN)
    fdx, fdy = FLOOR_DRAIN
    pipe(ax, [(fdx, fdy), (S3B[0] - (S3B[1] - fdy), fdy)], SAN, 1.0)
    rect(ax, fdx - 0.25, fdy - 0.25, fdx + 0.25, fdy + 0.25, fc=PAPER, ec=SAN, lw=0.8, z=12)
    cleanout(ax, A1[0] - 1.3, YM)
    pipe(ax, [(A1[0] - 0.9, YM), A1], SAN, 1.2)
    cleanout(ax, A2[0], YM - 1.35)
    pipe(ax, [(A2[0], YM - 0.95), A2], SAN, 1.2)
    cleanout(ax, TURN[0] + 1.2, YM)
    pipe(ax, [TURN, (TURN[0] + 0.8, YM)], SAN, 1.2)
    cleanout(ax, CO2[0], CO2[1], SAN, "2W", r=0.07)
    # point letters and inverts
    for k, dx, dy, ha in (("A", -1.3, -1.3, "center"), ("B", 1.2, -1.35, "left"), ("C", 1.2, -1.2, "left"), ("D", -0.9, 0.0, "right"),
                          ("E", -0.9, 0.9, "right"), ("F", -1.1, 0.0, "right")):
        d = INV[k]
        lab(ax, d["p"][0] + dx, d["p"][1] + dy, f"{k}  INV {d['inv']:.2f}", SAN, size=4.5, ha=ha)
    # dimensions
    xw = m.xw_gi(YM)
    yd = YM - 3.2
    for a, b in ((xw, A1[0]), (A1[0], A2[0]), (A2[0], TURN[0]), (TURN[0], m.GAR_X1)):
        dim(ax, (a, yd), (b, yd), 0.0, fth(b - a), size=4.8, color=SAN, ext=False)
    for a, b in ((YM, WYE[1]), (WYE[1], m.YF), (m.YF, CO2[1])):
        dim(ax, (TURN[0] - 2.6, a), (TURN[0] - 2.6, b), 0.0, fth(a - b), size=4.8, color=SAN, ext=False)
    for x in (xw, A1[0], A2[0], TURN[0], m.GAR_X1):
        line(ax, [(x, yd - 0.35), (x, yd + 0.35)], color=SAN, lw=0.3, z=8)
    mid = ((S3B[0] + WYE[0]) / 2, (S3B[1] + WYE[1]) / 2)
    lab(ax, mid[0] - 0.35, mid[1] + 0.35, f"4 in.  {fth(BR3_LEN)}", SAN, size=4.5, rot=45)
    lab(ax, (A2[0] + TURN[0]) / 2, YM + 0.0, "4 in. BUILDING DRAIN UNDER THE SLAB, 1/4 in./ft", SAN, size=4.5)
    lab(ax, TURN[0], 16.4, "4 in.", SAN, size=4.5, rot=90)
    # callouts
    note(ax, 10.6, 21.4, "CHASES 1 AND 2 on the rear wall (the garage is open and\nunheated): 16 x 12 in. clear, 3 in. stack, R-13 around the pipe,\n2 layers 5/8 in. Type X (1-hour), cleanout tee 18 in. above the\nslab behind a rated 12 x 12 in. access door",
         to=[(A1[0], m.Y_GR_I - 1.17), (A2[0] - 0.4, m.Y_GR_I - 1.17)], color=SAN, size=4.5, frm=(16.2, 22.4))
    note(ax, 10.2, 26.9, "STACK 1 above (3 in.)\noffsets to chase 1 in\nUnit A's floor trusses", to=(m.STACK_1[0] - 0.15, m.STACK_1[1]), color=SAN, size=4.4,
         frm=(14.0, 26.9))
    note(ax, 22.0, 38.6, f"UNIT A BATH 2 is on the slab on grade: its drains run UNDER THAT SLAB (in before the pour, P-102).\n3 in. from stack 2 passes through the 12 in. concrete wall in a 6 in. sleeve, sealed both faces,\nINV about {INV_SLEEVE:.1f}, then drops in chase 2. Engineer to place the sleeve",
         to=[(s2[0] + 0.3, m.Y_GR_O - 0.4)], color=SAN, size=4.5, frm=(24.0, 37.6))
    note(ax, 36.0, 34.3, "STACK 3 above (3 in.) offsets 1'-6\"\nin Unit A's floor trusses, over the\ntop of the concrete wall, into\nthe utility room. See the\nenlarged plan", to=(m.STACK_3[0], m.STACK_3[1] + 0.1), color=SAN, size=4.4, frm=(40.4, 32.5), ha="left")
    note(ax, 23.2, 25.2, "FLOOR CLEANOUT at the turn,\nflush, traffic-rated cover", to=(TURN[0] + 1.2, YM - 0.35), color=SAN, size=4.4, frm=(29.9, 25.3))
    note(ax, 34.6, 18.6, "Branch passes\nunder the block\nwall footing\nin a sleeve", to=(m.GAR_X1 + 0.3, S3B[1] - (S3B[0] - m.GAR_X1 - 0.3)), color=SAN, size=4.2, frm=(35.8, 20.4), ha="left")
    note(ax, 21.2, 11.4, "Drain passes 12 in. or more below the trench drain", to=(BLDG[0], TRENCH_Y), color=SAN, size=4.4, frm=(31.2, 11.2))
    cov = apron_el(*CO2) - INV["F"]["inv"] - 0.375
    note(ax, 17.6, 4.3, f"TWO-WAY CLEANOUT in the apron, traffic-rated box, flush.\nOnly about {cov * 12:.0f} in. of cover over the pipe here (apron about EL {apron_el(*CO2):.1f}):\ncast iron or encased PVC under the apron, or lower the whole run\nif the main is deep enough",
         to=(CO2[0] - 0.4, CO2[1]), color=SAN, size=4.4, frm=(31.6, 3.4))
    note(ax, 22.4, -4.2, "4 in. LATERAL TO THE MUB MAIN IN BAIRD ST.\nMain location and depth UNKNOWN: locate before\nsetting any invert on this sheet", to=(CO2[0], -4.2), color=SAN, size=4.4, weight="bold", frm=(32.0, -4.2))

    # ---------------- left column: legend, enlarged utility room, inverts ----------------
    def s_co(b, x, y):
        cleanout(b, x, y, SAN)

    def s_cos(b, x, y):
        cleanout(b, x, y, STORM)

    def s_st(b, x, y):
        stack_dot(b, (x - 0.12, y), SAN)
        stack_dot(b, (x + 0.12, y), SAN, fill=False)

    def s_ch(b, x, y):
        b.add_patch(Rectangle((x - 0.14, y - 0.055), 0.28, 0.11, fc="#e4efe4", ec=SAN, lw=0.7))

    yl = legend(bg, L, 9.72, [
        ("line", SAN, 2.4, "-", "Sanitary drain under the garage slab (size shown)"),
        ("line", SAN, 1.2, DASH_UP, "Sanitary above: offset in Unit A's floor trusses"),
        ("line", SAN, 0.9, "-", "Sanitary under Unit A's slab on grade"),
        ("sym", s_st, "Stack at the slab  /  stack position in the flats"),
        ("sym", s_ch, "Insulated 1-hour chase on the garage rear wall"),
        ("sym", s_co, "Cleanout (2W = two-way)"),
        ("line", CW, 1.3, (0, (6, 2)), "Water service, buried 42 in. min."),
        ("line", STORM, 1.3, DASH_FR, "French drain, 4 in. perforated"),
        ("line", STORM, 1.3, "-", "Storm, 4 in. solid  (thick = trench drain)"),
        ("sym", s_cos, "French drain cleanout riser to grade"),
    ], dy=0.158, fs=5.2)

    heading(bg, L, 7.62, "Utility room, enlarged", "3/8\" = 1'-0\" · heated room · dashed = overhead, above the heaters", 7.6)
    ua = utility_enlarged(fig, bg, L, 4.95)
    keys = [
        "*1  Two 1 in. services in through the east wall, sleeved and",
        f"    sealed, EL {m.EL_WATER_ENTRY:.1f} ({ftin(m.EL_WATER_ENTRY - m.EL_GAR)} above the floor). Up the wall",
        "    in the corner, then overhead to the boards.",
        "*2  Board A, board B (one per flat) on the south wall: main",
        "    shutoff, pressure-reducing valve (set 60 psi), gauge,",
        "    3/4 in. cold manifold and hot manifold with a valve per line.",
        "*3  Unit A's PEX lines go up through the ceiling into Unit A's",
        "    floor trusses, above the R-30.",
        "*4  Unit B's PEX lines cross the ceiling, then rise in the",
        "    pipe space behind bath 3.",
        "*5  WH-A, WH-B: 80 gal, 4.5 kW electric. ET = expansion tank.",
        "    T&P relief, 3/4 in., to 6 in. above the floor drain.",
        "*6  Floor drain, 2 in., with trap primer (off Unit A's cold).",
        "*7  Stack 3 (3 in.), cleanout at the base. No chase here.",
        f"*8  One shared pan, {ftin(m.WH_R * 2 + 0.2)} x {ftin(m.WH[1][1] - m.WH[0][1] + 2 * m.WH_R + 0.2)}, 1 in. drain to the floor drain.",
    ]
    yk = small_lines(bg, L, 4.86, keys, fs=4.9, dy=0.118)

    # invert schedule
    rows = [["Pt", "Sanitary: where", "Run ft", "Invert", "Below slab"]]
    for k in "ABCDEF":
        d = INV[k]
        rows.append([k, d["name"], f"{d['sta']:.1f}", f"{d['inv']:.2f}", f"{(m.EL_GAR - d['inv']) * 12:.0f} in."])
    d = INV["S3"]
    rows.append(["", d["name"], f"{d['sta']:.1f} to D", f"{d['inv']:.2f}", f"{(m.EL_GAR - d['inv']) * 12:.0f} in."])
    bg.text(L, 2.93, "BUILDING DRAIN INVERTS  (4 in. at 1/4 in./ft, slab EL 914.5)", fontsize=6.0, fontweight="bold", va="center")
    yb = table(bg, L, 2.82, [0.22, 1.62, 0.5, 0.5, 0.6], rows, fs=5.0, rh=0.165)
    small_lines(bg, L, yb - 0.07, [
        f"Run measured along the pipe from A. Total fall A to F: {(INV['A']['inv'] - INV['F']['inv']) * 12:.1f} in.",
        f"French drain: {FD_LEN:.0f} ft from the high point to the outlet, {(m.EL_DRAIN_HI - m.EL_DRAIN_OUT) * 12:.0f} in. of fall",
        f"({FD_FALL * 100:.1f} %). Inverts at the cleanout risers are on the plan.",
    ], fs=4.9, dy=0.12)
    save(fig, "P-101", pdf)


SHEETS = [("P-101", sheet_p101)]
