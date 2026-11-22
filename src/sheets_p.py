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
INV_SLEEVE = 924.2                                   # Unit A bath 2 drain through the 6 in. upstand on the garage rear wall (approx.)
FLOOR_DRAIN = (m.CHASE_3[0] + 0.2, (m.UTIL[2] + m.UTIL[3]) / 2)

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
EL_HB = m.EL_A - 0.75 * m.IN - m.TRUSS_A / 2
_EY = m.WATER_ENTRY[1]
BOARD_A = (_EY - 1.75, _EY - 0.35)                   # shutoff + PRV boards on the utility room east wall (y0, y1)
BOARD_B = (_EY + 0.35, _EY + 1.75)
RISE_A = (m.XE_GI - 0.3, BOARD_A[0] - 0.22)          # Unit A's cold riser goes up through the ceiling here
RISE_B = (m.STACK_3[0] - 1.3, m.B3_Y1 + m.PART + 0.55)           # Unit B's cold riser goes up the bath 3 pipe space
HB = (m.XE, RISE_A[1])                               # frost-proof hose bibb, east wall, in Unit A's floor rim

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
    """Utility room at 3/8 in. scale: service entries, shutoffs, risers, floor drain, stack 3."""
    fpi = 12 / 4.5
    view = ((m.UTIL[0] - 1.25, m.XE + 0.55), (m.UTIL[2] - 0.75, m.Y_GR_O + 0.45))
    ax = plan_axes(fig, left, bottom, view[0], view[1], fpi)
    lower_plan(ax, "bg", cars=False)
    strip_texts(ax)
    x0, x1, y0, y1 = m.UTIL
    # sanitary: stack 3, branch, floor drain
    pipe(ax, [S3B, WYE], SAN, 2.2)
    stack_dot(ax, S3B, SAN, r=0.05)
    cleanout(ax, S3B[0] + 0.62, S3B[1])
    fdx, fdy = FLOOR_DRAIN
    jx = S3B[0] - (S3B[1] - fdy)
    pipe(ax, [(fdx, fdy), (jx, fdy)], SAN, 1.3)
    rect(ax, fdx - 0.25, fdy - 0.25, fdx + 0.25, fdy + 0.25, fc=PAPER, ec=SAN, lw=1.0, z=12)
    line(ax, [(fdx - 0.25, fdy - 0.25), (fdx + 0.25, fdy + 0.25)], color=SAN, lw=0.6, z=13)
    line(ax, [(fdx - 0.25, fdy + 0.25), (fdx + 0.25, fdy - 0.25)], color=SAN, lw=0.6, z=13)
    # services in; one board per flat on the east wall (main shutoff, PRV, gauge)
    xb = x1 - 0.32
    for dy, (b0, b1), nm in ((-0.11, BOARD_A, "A"), (0.11, BOARD_B, "B")):
        pipe(ax, [(view[0][1], _EY + dy), (xb - 0.2, _EY + dy), (xb - 0.2, b1 if nm == "A" else b0)], CW, 1.5)
        rect(ax, xb - 0.38, b0, x1, b1, fc="#e9eef6", ec=CW, lw=0.9, z=11)
        txt(ax, xb - 0.03, (b0 + b1) / 2, f"BOARD {nm}", size=4.0, color=CW, weight="bold", z=12, rot=90)
    # risers: A up through the ceiling, B overhead along the north wall to the pipe space
    pipe(ax, [(xb - 0.2, BOARD_A[0]), (xb - 0.2, RISE_A[1])], CW, 1.5)
    ax.add_patch(Circle((xb - 0.2, RISE_A[1]), 0.2, fc=PAPER, ec=CW, lw=1.0, zorder=12))
    txt(ax, xb - 0.2, RISE_A[1], "A", size=4.2, color=CW, weight="bold", z=13)
    rb = (RISE_B[0], y1 - 0.26)
    pipe(ax, [(xb - 0.2, BOARD_B[1]), (xb - 0.2, y1 - 0.26), rb], CW, 1.5, DASH_UP)
    ax.add_patch(Circle(rb, 0.2, fc=PAPER, ec=CW, lw=1.0, zorder=12))
    txt(ax, rb[0], rb[1], "B", size=4.2, color=CW, weight="bold", z=13)
    # hose bibb feed and trap primer, both off board A
    pipe(ax, [(x1 - 0.1, BOARD_A[0]), (x1 - 0.1, RISE_A[1]), (m.XE + 0.25, RISE_A[1])], CW, 0.9)
    ax.add_patch(Circle((m.XE + 0.25, RISE_A[1]), 0.14, fc=PAPER, ec=CW, lw=0.9, zorder=12))
    pipe(ax, [(xb - 0.38, BOARD_A[0] + 0.5), (fdx + 0.25, fdy - 0.1)], CW, 0.8, (0, (1, 1)))
    # pan drains from the two water heaters above
    pipe(ax, [(fdx + 0.15, y1 - 0.15), (fdx + 0.1, fdy + 0.28)], SAN, 0.9, (0, (4, 1.5, 1, 1.5)))
    pipe(ax, [(fdx - 0.5, y1 - 0.9), (fdx - 0.12, fdy + 0.28)], SAN, 0.9, (0, (4, 1.5, 1, 1.5)))
    # keys
    keynote(ax, x1 + 0.3, _EY + 0.5, 1, CW)
    keynote(ax, xb - 0.75, (BOARD_A[0] + BOARD_A[1]) / 2 + 0.2, 2, CW)
    keynote(ax, xb - 0.75, (BOARD_B[0] + BOARD_B[1]) / 2, 2, CW)
    keynote(ax, xb - 0.85, RISE_A[1] + 0.02, 3, CW)
    keynote(ax, rb[0] - 0.55, rb[1] - 0.1, 4, CW)
    keynote(ax, m.XE + 0.3, RISE_A[1] - 0.45, 5, CW)
    keynote(ax, fdx - 0.62, fdy - 0.1, 6, SAN)
    keynote(ax, S3B[0] + 0.62, S3B[1] - 0.5, 7, SAN)
    keynote(ax, fdx - 0.95, y1 - 1.2, 8, SAN)
    txt(ax, x0 + 1.45, y0 + 0.75, "NO WATER HEATERS HERE:\neach is in its own flat", size=4.4, color=GREY, z=8)
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
            "through the east wall, into the heated",
            "utility room: shutoff and PRV per flat.",
            "The water heaters are up in the flats.",
        ]),
        ("Storm: gravity only", [
            "NO SUMP PUMP. French drain and trench",
            "drain run by gravity to one outlet at the",
            "street edge. The outlet is only about",
            f"{(m.EL_DRAIN_OUT - street_el(m.DRAIN_OUT[0])) * 12:.0f} in. above the pavement: the survey",
            "must confirm it before the footings go in.",
        ]),
    ]
    fig, bg = new_sheet("P-101", title, "3/16\" = 1'-0\"", notes)
    L = MARGIN + 0.2
    heading(bg, L, 10.2, "Garage level and under-slab plumbing", "3/16\" = 1'-0\" · sizes and inverts preliminary · true north: see arrow", 8.6)

    view = ((2.5, 53.5), (-8.5, 42.6))
    ax = frame(fig, view, 4.07, 0.5, north=(51.0, 39.4), bar=(5.0, -7.9), street_label=(26.0, -7.75))
    poly(ax, m.SOG, fc="#f7f3ec", ec=BG_EDGE, lw=0.5, z=1.5, ls=(0, (4, 2)))
    site_work(ax, bg=True)
    n0 = len(ax.texts)
    lower_plan(ax, "bg", cars=False)
    strip_texts(ax, n0)
    txt(ax, 22.0, 13.0, "OPEN GARAGE  (unheated, slab EL 914.5)", size=5.0, color="#8a9199", z=4)
    txt(ax, 40.6, 14.0, "STAIR", size=4.4, color="#8a9199", z=4)
    txt(ax, 51.1, 16.0, "LOT LINE", size=4.6, color=ACCENT, rot=90)
    txt(ax, 21.0, -0.75, "FRONT LOT LINE = RIGHT-OF-WAY LINE", size=4.6, color=ACCENT)
    txt(ax, 13.6, 33.6, "UNIT A SLAB ON GRADE ABOVE\n(EL 925.5; earth below it)", size=4.4, color=EARTH, z=4)

    # ---------------- storm ----------------
    pipe(ax, FD_PATH[:4], STORM, 1.3, DASH_FR)
    pipe(ax, FD_PATH[3:], STORM, 1.3)
    pipe(ax, [(m.OPEN[0], TRENCH_Y), (m.OPEN[1], TRENCH_Y)], STORM, 2.6)
    pipe(ax, TRENCH_OUT, STORM, 1.3)
    ox, oy = m.DRAIN_OUT
    poly(ax, [(ox - 0.75, oy), (ox + 0.75, oy), (ox, oy - 1.3)], fc=STORM, ec=STORM, z=12)
    cleanout(ax, *FD_SW, STORM)
    lab(ax, FD_SW[0] - 0.2, FD_SW[1] - 1.5, f"INV {fd_inv(0):.2f}\nhigh point", STORM, size=4.4)
    cleanout(ax, *FD_NW, STORM)
    lab(ax, FD_NW[0] + 1.0, FD_NW[1] + 1.0, f"INV {fd_inv(1):.2f}", STORM, size=4.4, ha="left")
    cleanout(ax, *FD_NE, STORM)
    note(ax, 50.5, FD_NE[1] + 0.6, f"INV {fd_inv(2):.2f}", to=(FD_NE[0] + 0.4, FD_NE[1] + 0.1), color=STORM, size=4.4, weight="bold")
    cleanout(ax, *FD_SE, STORM)
    note(ax, 50.5, FD_SE[1] + 0.9, f"INV {fd_inv(3):.2f}", to=(FD_SE[0] + 0.4, FD_SE[1] + 0.1), color=STORM, size=4.4, weight="bold")
    note(ax, 25.0, 32.35, "FRENCH DRAIN at the footing of the three buried walls (S-102): 4 in. perforated pipe\nin washed stone and filter fabric. CO = cleanout riser to grade at each corner",
         color=STORM, size=4.4)
    note(ax, 13.6, 7.7, f"TRENCH DRAIN across the opening, {ftin(m.OPEN_W)}, traffic-rated grate,\nfalls east. 4 in. outlet at the east end, in solid pipe to the outlet",
         color=STORM, size=4.4)
    note(ax, 38.5, 6.6, "4 in. SOLID from the French\ndrain to the outlet, clear of\nthe meter pits", to=(FD_SE[0], 6.6), color=STORM, size=4.4, frm=(43.6, 6.6))
    note(ax, 37.6, -4.3, f"GRAVITY OUTLET at the street edge\nINV {m.EL_DRAIN_OUT:.1f} (pavement about {street_el(ox):.1f}).\nNO SUMP PUMP.",
         to=(ox - 0.6, oy - 0.3), color=STORM, size=4.6, weight="bold", frm=(43.4, -4.9))

    # ---------------- water ----------------
    for i, (mx, my) in enumerate(m.WATER_METERS):
        rect(ax, mx - 0.5, my - 0.5, mx + 0.5, my + 0.5, fc=PAPER, ec=CW, lw=1.0, z=11)
        txt(ax, mx, my, "AB"[i], size=3.6, color=CW, weight="bold", z=12)
        pipe(ax, [(mx, my - 0.5), (mx, PAVE_N - 0.6)], CW, 1.0, (0, (2, 1.5)))
        ey = m.WATER_ENTRY[1] + (-0.11, 0.11)[i]
        pipe(ax, [(mx, my + 0.5), (mx, 0.2), (SERV_X[i], 1.2), (SERV_X[i], ey), (m.XE_GI - 0.2, ey)], CW, 1.3, (0, (6, 2)))
    note(ax, 49.4, -3.7, "2 METER PITS\n(MUB), one\nper flat", color=CW, size=4.4, ha="left")
    note(ax, 51.5, 23.0, f"TWO 1 in.\nSERVICES,\nburied 42 in.\nmin. (C-106).\nEnter at\nEL {m.EL_WATER_ENTRY:.1f},\n{elev(m.XE + 1, m.WATER_ENTRY[1]) - m.EL_WATER_ENTRY:.1f} ft below\ngrade, sleeved\nand sealed", color=CW, size=4.4, ha="center")
    ax.add_patch(Circle((HB[0] + 0.3, HB[1]), 0.3, fc=PAPER, ec=CW, lw=1.0, zorder=12))
    lab(ax, HB[0] + 1.6, HB[1] - 0.2, "HB", CW, size=4.6)
    lab(ax, 22.0, 15.6, "NO WATER PIPING IN THE OPEN GARAGE", CW, size=6.4)
    txt(ax, 22.0, 14.55, "It is unheated. Every water line is in the heated utility room or inside the flats.", size=4.6, color=CW, z=14)

    # ---------------- sanitary ----------------
    for st_, base in ((m.STACK_1, A1), (m.STACK_3, S3B)):
        pipe(ax, [st_, base], SAN, 1.2, DASH_UP)
        stack_dot(ax, st_, SAN, fill=False)
    s2 = m.STACK_2
    wcf = (m.WCS[1][0], m.WCS[1][1] - 1.0)
    tubd = ((m.TUBS[1][0] + m.TUBS[1][2]) / 2, m.TUBS[1][1] + 0.7)
    lavx = (m.LAVS[1][0] + m.LAVS[1][2]) / 2
    for p_ in ([wcf, s2], [tubd, (lavx, tubd[1]), (lavx, wcf[1] + (wcf[0] - lavx) * (s2[1] - wcf[1]) / (wcf[0] - s2[0]))]):
        pipe(ax, p_, SAN, 0.9)
    pipe(ax, [s2, A2], SAN, 1.6)
    rect(ax, s2[0] - 0.3, m.Y_GR_I, s2[0] + 0.3, m.Y_GR_O, fc=PAPER, ec=SAN, lw=0.8, z=11)       # sleeve
    stack_dot(ax, s2, SAN, fill=False)
    for c in (A1, A2):
        rect(ax, c[0] - 0.75, m.Y_GR_I - 1.17, c[0] + 0.75, m.Y_GR_I, fc="#e4efe4", ec=SAN, lw=0.7, z=8)
    pipe(ax, [A1, A2, TURN, WYE, BLDG, CO2], SAN, 2.4)
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
    for k, dx, dy, ha in (("A", -2.1, 0.0, "right"), ("B", 1.2, -1.35, "left"), ("C", 1.2, -1.2, "left"), ("D", 0.8, -0.75, "left"),
                          ("E", -0.9, 0.9, "right"), ("F", -1.1, 0.0, "right")):
        d = INV[k]
        lab(ax, d["p"][0] + dx, d["p"][1] + dy, f"{k}  INV {d['inv']:.2f}", SAN, size=4.5, ha=ha)
    xw = m.xw_gi(YM)
    yd = YM - 4.1
    for a_, b_ in ((xw, A1[0]), (A1[0], A2[0]), (A2[0], TURN[0]), (TURN[0], m.GAR_X1)):
        dim(ax, (a_, yd), (b_, yd), 0.0, fth(b_ - a_), size=4.8, color=SAN, ext=False)
    for a_, b_ in ((YM, WYE[1]), (WYE[1], m.YF), (m.YF, CO2[1])):
        dim(ax, (TURN[0] - 2.6, a_), (TURN[0] - 2.6, b_), 0.0, fth(a_ - b_), size=4.8, color=SAN, ext=False)
    for x in (xw, A1[0], A2[0], TURN[0], m.GAR_X1):
        line(ax, [(x, yd - 0.35), (x, yd + 0.35)], color=SAN, lw=0.3, z=8)
    lab(ax, (A2[0] + TURN[0]) / 2, YM, "4 in. BUILDING DRAIN UNDER THE SLAB, 1/4 in./ft", SAN, size=4.5)
    lab(ax, TURN[0], 16.4, "4 in.", SAN, size=4.5, rot=90)
    lab(ax, 35.2, 23.34, "4 in.", SAN, size=4.5, rot=45)
    # callouts
    note(ax, 10.6, 19.4, "CHASES 1 AND 2 on the rear wall (the garage is open and\nunheated): 16 x 12 in. clear, 3 in. stack, R-13 around the pipe,\n2 layers 5/8 in. Type X (1-hour), cleanout tee 18 in. above the\nslab behind a rated 12 x 12 in. access door",
         to=[(A1[0] + 0.3, m.Y_GR_I - 1.17), (A2[0] - 0.5, m.Y_GR_I - 1.17)], color=SAN, size=4.5, frm=(17.6, 20.4))
    note(ax, 10.2, 26.3, "STACK 1 above (3 in.)\noffsets to chase 1 in\nUnit A's floor trusses", to=(m.STACK_1[0] - 0.15, m.STACK_1[1]), color=SAN, size=4.4,
         frm=(14.0, 26.3))
    note(ax, 26.6, 37.25, f"UNIT A BATH 2 is on the slab on grade: its drains run\nUNDER THAT SLAB (in and tested before the pour, P-102).\n3 in. from stack 2 passes through the 6 in. concrete\nupstand in a sleeve, sealed, INV about {INV_SLEEVE:.1f}, then\nbetween two trusses over the ledge and down chase 2",
         to=[(s2[0] + 0.3, m.Y_GR_O - 0.3)], color=SAN, size=4.5, frm=(26.5, 36.2))
    note(ax, 37.2, 34.1, "STACK 3 above (3 in.) offsets 1'-6\" in\nUnit A's floor trusses, over the truss\nledge of the concrete wall, into the\nutility room. See the enlarged plan", to=(m.STACK_3[0], m.STACK_3[1] + 0.1), color=SAN, size=4.4, frm=(40.4, 33.0))
    note(ax, 22.6, 22.6, "FLOOR CLEANOUT at the turn,\nflush, traffic-rated cover", to=(TURN[0] + 1.0, YM - 0.35), color=SAN, size=4.4, frm=(29.3, 22.9))
    note(ax, 34.4, 18.2, f"4 in. branch from\nstack 3, {fth(BR3_LEN)},\nunder the block\nwall footing in\na sleeve", to=(m.GAR_X1 + 0.3, S3B[1] - (S3B[0] - m.GAR_X1 - 0.3)), color=SAN, size=4.2, frm=(35.8, 19.9))
    note(ax, 21.2, 11.4, "Drain passes 12 in. or more below the trench drain", to=(BLDG[0], TRENCH_Y), color=SAN, size=4.4, frm=(31.2, 11.2))
    cov = apron_el(*CO2) - INV["F"]["inv"] - 0.375
    note(ax, 14.9, 4.3, f"TWO-WAY CLEANOUT in the apron, traffic-rated box, flush.\nOnly about {cov * 12:.0f} in. of cover over the pipe here (apron about EL {apron_el(*CO2):.1f}):\ncast iron or encased PVC under the apron, or lower the whole run\nif the main is deep enough",
         to=(CO2[0] - 0.4, CO2[1] - 0.3), color=SAN, size=4.4, frm=(28.9, 3.4))
    note(ax, 21.4, -4.2, "4 in. LATERAL TO THE MUB MAIN IN BAIRD ST.\nMain location and depth UNKNOWN: locate before\nsetting any invert on this sheet", to=(CO2[0], -4.2), color=SAN, size=4.4, weight="bold", frm=(31.0, -4.2))

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

    def s_hb(b, x, y):
        b.add_patch(Circle((x, y), 0.055, fc=PAPER, ec=CW, lw=1.0))

    legend(bg, L, 9.74, [
        ("line", SAN, 2.4, "-", "Sanitary drain under the garage slab (size shown)"),
        ("line", SAN, 1.2, DASH_UP, "Sanitary above: offset in Unit A's floor trusses"),
        ("line", SAN, 0.9, "-", "Sanitary under Unit A's slab on grade"),
        ("sym", s_st, "Stack at the slab  /  stack position in the flats"),
        ("sym", s_ch, "Insulated 1-hour chase on the garage rear wall"),
        ("sym", s_co, "Cleanout (2W = two-way)"),
        ("line", CW, 1.3, (0, (6, 2)), "Water service, buried 42 in. min."),
        ("sym", s_hb, f"HB: frost-proof hose bibb in Unit A's floor rim, EL {EL_HB:.1f}"),
        ("line", STORM, 1.3, DASH_FR, "French drain, 4 in. perforated"),
        ("line", STORM, 1.3, "-", "Storm, 4 in. solid  (thick = trench drain)"),
        ("sym", s_cos, "French drain cleanout riser to grade"),
    ], dy=0.152, fs=5.2)

    x0, x1, y0, y1 = m.UTIL
    heading(bg, L, 7.6, "Utility room, enlarged", f"3/8\" = 1'-0\" · heated, {fth(x1 - x0)} x {fth(y1 - y0)} clear · blue dashed = at the ceiling", 7.6)
    utility_enlarged(fig, bg, L, 4.93)
    keys = [
        "*1  Two 1 in. services in through the east wall, sleeved and",
        f"    sealed, EL {m.EL_WATER_ENTRY:.1f} ({ftin(m.EL_WATER_ENTRY - m.EL_GAR)} above the floor).",
        "*2  Board A, board B (one per flat) on the east wall: main",
        "    shutoff, pressure-reducing valve (set 60 psi), gauge,",
        "    drain valve. Label each board with its flat.",
        "*3  Unit A: 3/4 in. cold riser up through the ceiling into",
        "    Unit A's floor trusses (above the R-30), to its heater.",
        "*4  Unit B: 3/4 in. cold riser at the ceiling to the north",
        "    wall, then up the pipe space behind bath 3, to its heater.",
        "*5  1/2 in. to the hose bibb (HB) in the floor rim, with its",
        "    own shutoff and drain-down valve on board A.",
        "*6  Floor drain, 2 in., with trap primer (dotted, off Unit A's",
        "    cold). It also takes the two heater pan drains.",
        "*7  Stack 3 (3 in.), cleanout at the base. No chase here.",
        "*8  1 in. pan drains from the two water heaters above, ending",
        "    over the floor drain with an air gap.",
        "    The 500 W wall heater (E-101) keeps this room above 40 F.",
    ]
    small_lines(bg, L, 4.84, keys, fs=4.9, dy=0.112)

    rows = [["Pt", "Sanitary: where", "Run ft", "Invert", "Below slab"]]
    for k in "ABCDEF":
        d = INV[k]
        rows.append([k, d["name"], f"{d['sta']:.1f}", f"{d['inv']:.2f}", f"{(m.EL_GAR - d['inv']) * 12:.0f} in."])
    d = INV["S3"]
    rows.append(["", d["name"], f"{d['sta']:.1f} to D", f"{d['inv']:.2f}", f"{(m.EL_GAR - d['inv']) * 12:.0f} in."])
    bg.text(L, 2.78, "BUILDING DRAIN INVERTS  (4 in. at 1/4 in./ft, slab EL 914.5)", fontsize=6.0, fontweight="bold", va="center")
    yb = table(bg, L, 2.67, [0.22, 1.62, 0.5, 0.5, 0.6], rows, fs=5.0, rh=0.16)
    small_lines(bg, L, yb - 0.07, [
        f"Run measured along the pipe from A. Total fall A to F: {(INV['A']['inv'] - INV['F']['inv']) * 12:.1f} in.",
        f"French drain: {FD_LEN:.0f} ft from the high point to the outlet, {(m.EL_DRAIN_HI - m.EL_DRAIN_OUT) * 12:.0f} in. of fall",
        f"({FD_FALL * 100:.1f} %). Inverts at the cleanout risers are on the plan.",
    ], fs=4.9, dy=0.12)
    save(fig, "P-101", pdf)


# ----------------------------------------------------------------------------
# P-102 / P-103  Unit plans
# ----------------------------------------------------------------------------
YH = m.Y4 + 0.18                      # hot home-runs: just north of the bath 1 plumbing wall, in the floor trusses
YC = YH + 0.32                        # cold home-runs beside them
MAN_X = m.X_C1 - 0.1                  # PEX manifolds on the mechanical closet east wall, above the heater
MAN_Y = (m.WH_UNIT[1] - 0.8, m.HALL_Y1 - 0.12)
RISER_X = m.X_C1 + m.PART / 2         # the 3/4 in. cold riser comes up inside that wall
MAN_H = 5.5                           # manifolds 5'-6" above the floor
LAV1_X = (m.LAVS[0][0] + m.LAVS[0][2]) / 2
GAL_HALF = 0.0092                     # gal per ft of 1/2 in. PEX (SDR 9)


def hot_runs():
    """Hot-water run lengths (ft) from the hot manifold at the heater, along the routes drawn."""
    base = MAN_H + 0.9 + (MAN_Y[0] - YH)                       # down the wall into the floor trusses
    tx1 = (m.TUBS[0][0] + m.TUBS[0][2]) / 2
    tx3 = (m.TUBS[2][0] + m.TUBS[2][2]) / 2
    lx2 = (m.LAVS[1][0] + m.LAVS[1][2]) / 2
    lx3 = (m.LAVS[2][0] + m.LAVS[2][2]) / 2
    xk = m.ISL_SINK[2] - 0.15
    return {
        "bath 1 lavatory": base + (MAN_X - LAV1_X) + 0.2 + 0.9 + 1.75,
        "tub 1": base + (MAN_X - tx1) + 0.2 + 0.9 + 2.5,
        "bath 2 lavatory": (7.0 - MAN_H) + (MAN_X - lx2) + 0.8 + (7.0 - 1.75),
        "bath 3 lavatory": base + (lx3 - MAN_X) + 1.0 + 0.9 + 1.75,
        "tub 3": base + (tx3 - MAN_X) + (m.B3_Y1 - YH) + 0.9 + 2.5,
        "kitchen sink": base + (xk - MAN_X) + (YH - m.ISL_SINK[3] + 0.45) + 0.9 + 1.5,
    }


HOT = hot_runs()
HOT_MAX = max(HOT.items(), key=lambda kv: kv[1])
HOT_FAUCET = max(((k, v) for k, v in HOT.items() if "tub" not in k), key=lambda kv: kv[1])


def wait_s(ft_, gpm=1.5):
    return ft_ * GAL_HALF / gpm * 60


def unit_plumbing(ax, unit):
    A = unit == "A"
    s1, s2, s3 = m.STACK_1, m.STACK_2, m.STACK_3
    W3, W2, W1 = 2.2, 1.5, 1.0

    def vent(pts):
        pipe(ax, pts, VENT, 0.8, DASH_V, z=9)

    def vdot(p):
        ax.add_patch(Circle(p, u(ax, 0.028), fc=PAPER, ec=VENT, lw=0.8, zorder=12))

    def sz(x, y, s, color=SAN, rot=0, size=4.2):
        txt(ax, x, y, s, size=size, color=color, weight="bold", rot=rot, z=14, box=True)

    # ---------------- bath 1 -> stack 1 ----------------
    wc1 = (m.WCS[0][0], m.WCS[0][1] - 1.0)
    tx1 = (m.TUBS[0][0] + m.TUBS[0][2]) / 2
    yv1 = m.Y3 + 0.40
    pipe(ax, [wc1, s1], SAN, W3)
    pipe(ax, [(LAV1_X, m.Y3 - 0.1), (LAV1_X, m.Y3 - 0.55), (wc1[0], m.Y3 - 0.55)], SAN, W1)
    pipe(ax, [(tx1, m.TUBS[0][3] - 0.7), (tx1, m.Y3 + 0.13), (s1[0], m.Y3 + 0.13)], SAN, W2)
    vent([(LAV1_X, yv1), (s1[0] - 0.15, yv1)])
    vent([(tx1 - 0.7, yv1), (s1[0] + 0.15, yv1)])
    vdot((LAV1_X, yv1))
    vdot((tx1 - 0.7, yv1))
    sz(wc1[0] + 0.5, wc1[1] + 0.05, '3"')
    sz(LAV1_X + 0.95, m.Y3 - 0.85, '1-1/2"')
    sz(tx1 + 0.42, m.Y3 - 0.45, '2"')
    # ---------------- bath 2 -> stack 2 ----------------
    wc2 = (m.WCS[1][0], m.WCS[1][1] - 1.0)
    tx2 = (m.TUBS[1][0] + m.TUBS[1][2]) / 2
    lx2 = (m.LAVS[1][0] + m.LAVS[1][2]) / 2
    yd2 = m.B2_Y0 + 0.7
    yw2 = m.B2_Y0 - m.PART / 2
    yj = wc2[1] + (wc2[0] - lx2) * (s2[1] - wc2[1]) / (wc2[0] - s2[0])
    pipe(ax, [wc2, s2], SAN, W3)
    pipe(ax, [(tx2, yd2), (lx2, yd2), (lx2, yj)], SAN, W2)
    pipe(ax, [(lx2, m.B2_Y0 + 0.05), (lx2, yd2)], SAN, W1)
    xv2 = s2[0] + 0.52
    vent([(tx2 - 0.62, yw2), (xv2, yw2), (xv2, s2[1] - 0.2), s2])
    vdot((lx2, yw2))
    vdot((tx2 - 0.62, yw2))
    sz(wc2[0] - 0.55, wc2[1] + 1.05, '3"')
    sz(lx2 + 0.42, 33.4, '2"')
    sz(tx2 - 1.3, yd2 + 0.32, '2"')
    # ---------------- bath 3 -> stack 3 ----------------
    wc3 = (m.WCS[2][0], m.WCS[2][1] - 1.0)
    tx3 = (m.TUBS[2][0] + m.TUBS[2][2]) / 2
    lx3 = (m.LAVS[2][0] + m.LAVS[2][2]) / 2
    yw3 = m.B3_Y1 + m.PART / 2
    pipe(ax, [wc3, s3], SAN, W3)
    pipe(ax, [(lx3, m.B3_Y1 - 0.1), (lx3, m.B3_Y1 - 0.42), (wc3[0], m.B3_Y1 - 0.42)], SAN, W1)
    pipe(ax, [(tx3, m.B3_Y1 - 0.72), (wc3[0], m.B3_Y1 - 0.72)], SAN, W2)
    vent([(lx3, yw3), (tx3, yw3)])
    vent([(tx3, m.B3_Y1 - 0.72), (tx3, yw3)])
    vent([(s3[0] - 0.42, yw3), (s3[0] - 0.42, s3[1]), s3])
    vdot((lx3, yw3))
    vdot((tx3, yw3))
    sz(wc3[0] - 0.42, wc3[1] + 0.02, '3"')
    sz(tx3 - 1.1, m.B3_Y1 - 1.0, '2"')
    sz(lx3 + 0.9, m.B3_Y1 - 0.14, '1-1/2"', size=3.8)
    # ---------------- kitchen island + washer -> stack 2 ----------------
    sd = ((m.ISL_SINK[0] + m.ISL_SINK[2]) / 2, (m.ISL_SINK[1] + m.ISL_SINK[3]) / 2)
    wbx, wby = m.X_C0 + 0.7, m.Y1 + m.PART / 2
    yend = A2[1] if A else s2[1]
    pipe(ax, [sd, (s2[0], sd[1]), (s2[0], yend)], SAN, W2)
    pipe(ax, [(wbx - 0.3, wby), (s2[0], wby)], SAN, W2)
    yvw = m.Y1 - 0.3
    vent([(wbx + 0.55, wby), (wbx + 0.55, yvw), (xv2, yvw), (xv2, yw2)])
    vdot((wbx + 0.55, wby))
    box_sym(ax, wbx, wby, "WB", SAN)
    poly(ax, [(sd[0] - 0.3, sd[1] + 0.45), (sd[0] + 0.3, sd[1] + 0.45), (sd[0], sd[1] + 0.95)], fc=PAPER, ec=VENT, lw=0.9, z=12)
    stack_dot(ax, sd, SAN, r=0.022)
    sz(23.4, sd[1] + 0.34, '2"')
    sz(s2[0] + 0.42, 23.9, '2"')
    sz(22.0, wby - 0.36, '2"')
    if A:
        pipe(ax, [s2, A2], SAN, W3)
        rect(ax, s2[0] - 0.32, m.Y_GR_I, s2[0] + 0.32, m.Y_GR_O, fc=PAPER, ec=SAN, lw=0.8, z=11)
        ax.add_patch(Rectangle((A2[0] - 0.3, A2[1] - 0.3), 0.6, 0.6, fc=SAN, ec=SAN, zorder=12))
        sz(s2[0] - 0.45, 32.6, '3"')
    # ---------------- stacks ----------------
    for st_ in (s1, s2, s3):
        stack_dot(ax, st_, SAN, r=0.04)

    # ---------------- water ----------------
    WT, WB_ = 1.35, 0.85

    def cold(pts, lw=WB_, ls="-"):
        pipe(ax, pts, CW, lw, ls, z=10.5)

    def hot(pts, lw=WB_, ls=DASH_H):
        pipe(ax, pts, HW, lw, ls, z=10.4)

    # 3/4 in. cold riser from the utility room to the heater and manifolds
    r0 = RISE_A if A else RISE_B
    ym = MAN_Y[0] + 0.15 if A else MAN_Y[1] - 0.15
    pipe(ax, [r0, (RISER_X, r0[1]), (RISER_X, ym), (MAN_X, ym)], CW, 2.2, z=10.6)
    ax.add_patch(Circle(r0, u(ax, 0.05), fc=CW, ec=CW, lw=1.0, zorder=13))
    rect(ax, MAN_X - 0.11, MAN_Y[0], MAN_X + 0.11, MAN_Y[1], fc="#e9eef6", ec=CW, lw=0.9, z=11)
    # home-runs in the floor trusses: west to bath 1 (and washer, ice maker), east to bath 3 (and kitchen)
    xw_c, xw_h = LAV1_X - 0.2, LAV1_X + 0.17
    xe_c, xe_h = tx3 - 0.15, tx3 + 0.15
    cold([(xw_c, YC), (xe_c, YC)], WT)
    hot([(xw_h, YH), (xe_h, YH)], WT)
    cold([(MAN_X - 0.06, YC), (MAN_X - 0.06, MAN_Y[0])], WT)
    hot([(MAN_X + 0.06, YH), (MAN_X + 0.06, MAN_Y[0])], WT, "-")
    for x in (xw_c, m.WCS[0][0] - 0.5, tx1 - 0.15):
        cold([(x, YC), (x, m.Y4)])
        riser(ax, (x, m.Y4 - 0.02), CW)
    for x in (xw_h, tx1 + 0.17):
        hot([(x, YH), (x, m.Y4)], ls="-")
        riser(ax, (x, m.Y4 - 0.02), HW)
    xi, yi = m.E1 + m.PART / 2, m.FRIDGE[3] - 0.5
    cold([(xi, YC), (xi, yi)])
    box_sym(ax, xi, yi, "IM", CW)
    cold([(wbx - 0.13, YC), (wbx - 0.13, m.Y2)])
    hot([(wbx + 0.17, YH), (wbx + 0.17, m.Y2)])
    xk = m.ISL_SINK[2] - 0.45
    yk = m.ISL_SINK[3] - 0.45
    cold([(xk, YC), (xk, yk)])
    hot([(xk + 0.3, YH), (xk + 0.3, yk)])
    riser(ax, (xk, yk), CW)
    riser(ax, (xk + 0.3, yk), HW)
    # bath 3 stubs
    for x, y in ((lx3 - 0.38, m.LAVS[2][1] + 0.4), (m.WCS[2][0] + 0.66, m.B3_Y1 - 0.12), (xe_c, m.B3_Y1 - 0.12)):
        cold([(x, YC), (x, y)])
        riser(ax, (x, y), CW)
    for x, y in ((lx3 - 0.08, m.LAVS[2][1] + 0.4), (xe_h, m.B3_Y1 - 0.12)):
        hot([(x, YH), (x, y)])
        riser(ax, (x, y), HW)
    # bath 2: from the manifolds OVERHEAD in the soffit, dropping in the walls (never under Unit A's slab)
    xbc, xbh = tx2 - 0.17, tx2 + 0.13
    yoc = m.B2_Y0 - m.PART - 0.27
    yoh = yoc - 0.3
    xwc = m.WCS[1][0] + 0.5
    cold([(MAN_X, yoc), (lx2 - 0.18, yoc)], WT, DASH_OH)
    hot([(MAN_X, yoh), (lx2 + 0.17, yoh)], WB_, DASH_OH)
    cold([(xwc, yoc), (xwc, m.B2_Y1 + m.B2_FUR + 0.12)], WB_, DASH_OH)
    for x in (xbc, lx2 - 0.18):
        cold([(x, yoc), (x, yw2)], WB_, DASH_OH)
        riser(ax, (x, yw2), CW)
    for x in (xbh, lx2 + 0.17):
        hot([(x, yoh), (x, yw2)], WB_, DASH_OH)
        riser(ax, (x, yw2), HW)
    riser(ax, (xwc, m.B2_Y1 + m.B2_FUR + 0.12), CW)
    # heater pan drain, 1 in., in the floor trusses to the utility-room floor drain
    yp = m.WH_UNIT[1]
    pend = FLOOR_DRAIN if A else (RISE_B[0] - 0.55, RISE_B[1] + 0.12)
    pipe(ax, [(m.WH_UNIT[0] + m.WH_PAN_R, yp), (m.X_ST + 0.9, yp), pend], SAN, 0.9, (0, (4, 1.5, 1, 1.5)), z=9.5)
    if A:
        rect(ax, pend[0] - 0.25, pend[1] - 0.25, pend[0] + 0.25, pend[1] + 0.25, fc=PAPER, ec=SAN, lw=0.9, z=12)
        cold([(RISE_A[0] + 0.12, RISE_A[1] - 0.12), (m.XE, HB[1] - 0.12)])
        ax.add_patch(Circle((HB[0] + 0.3, HB[1] - 0.12), 0.3, fc=PAPER, ec=CW, lw=1.0, zorder=12))
    else:
        riser(ax, pend, SAN, 0.035)
    # access
    access_panel(ax, tx1, m.Y4 + 0.1)
    access_panel(ax, m.X_ST - 0.1, (m.B3_Y1 + m.PART + m.yr_i(m.X_ST)) / 2 - 0.1, w=1.33, horiz=False)
    return dict(wc1=wc1, wc2=wc2, wc3=wc3, tx1=tx1, tx2=tx2, tx3=tx3, lx2=lx2, lx3=lx3, sd=sd, wb=(wbx, wby), im=(xi, yi),
                xk=xk, yk=yk, xbc=xbc, yoc=yoc, yoh=yoh, xwc=xwc, yw2=yw2, xv2=xv2, yp=yp, pend=pend)


def unit_sheet(pdf, number, unit):
    A = unit == "A"
    title = f"Plumbing: Unit {unit}"
    el = m.EL_A if A else m.EL_B
    trunk = plen([(26.5, 17.33), (m.STACK_2[0], 17.33), (m.STACK_2[0], A2[1] if A else m.STACK_2[1])])
    drains = ("Unit " + unit + " drains", [
        "Bath 1 to stack 1. Bath 2, kitchen and",
        "washer to stack 2. Bath 3 to stack 3.",
        "Toilets 3 in., tubs and washer standpipe",
        "2 in., lavatories 1 1/2 in. All at 1/4 in.",
        "per ft. PVC schedule 40 DWV.",
    ])
    wait = ("Hot water wait", [
        f"Longest hot run: {HOT_MAX[1]:.0f} ft ({HOT_MAX[0]}).",
        f"Longest to a faucet: {HOT_FAUCET[1]:.0f} ft of 1/2 in.",
        f"PEX = {HOT_FAUCET[1] * GAL_HALF:.2f} gal, about {wait_s(HOT_FAUCET[1]):.0f} s at 1.5 gpm.",
        "No recirculation pump.",
    ])
    if A:
        notes = [drains,
                 ("Slab on grade (shaded)", [
                     "North of the garage rear wall the floor",
                     "is a slab on grade. Bath 2's drains are",
                     "UNDER that slab: lay, test and inspect",
                     "them BEFORE the slab is poured. No water",
                     "line goes under the slab: bath 2 is fed",
                     "overhead in the 7'-0\" soffit.",
                 ]),
                 ("Water", [
                     "3/4 in. cold riser from Unit A's shutoff",
                     "and PRV in the utility room, in Unit A's",
                     "own floor trusses ABOVE the R-30, to the",
                     "80 gal heater in the mechanical closet.",
                     "PEX home-runs from the manifolds there:",
                     "1/2 in. to every fixture, stop at each.",
                 ]),
                 wait]
    else:
        notes = [drains,
                 ("Vents through the roof", [
                     "Each stack continues 3 in. through the",
                     "roof (VTR), 12 in. above it, flashed.",
                     "All three come out on the rear slope.",
                     "Unit A's vents join in above Unit B's",
                     "fixtures. No water pipe in the attic.",
                 ]),
                 ("Water", [
                     "3/4 in. cold riser from Unit B's shutoff",
                     "and PRV in the utility room, up the pipe",
                     "space behind bath 3, then in Unit B's own",
                     "floor trusses to the 80 gal heater in the",
                     "mechanical closet. PEX home-runs from",
                     "the manifolds there, 1/2 in. to fixtures.",
                 ]),
                 wait]
    fig, bg = new_sheet(number, title, "1/4\" = 1'-0\"", notes)
    L = MARGIN + 0.2
    heading(bg, L, 10.22, f"Unit {unit} plumbing plan",
            f"1/4\" = 1'-0\" · floor EL {el:.1f} · pipes are in this flat's floor " + ("trusses (or under its slab)" if A else "trusses") + " unless dotted · preliminary", 8.6)
    view = ((5.2, 57.6), (4.6, 44.4))
    ax = frame(fig, view, 0.5, 0.5, fpi=4.0, street=False, lot=False, north=(55.4, 42.4), bar=(6.0, 5.5))
    unit_plan(ax, "bg", unit, furniture=False)
    if A:
        from shapely.geometry import Polygon as SP
        sog = SP(m.SOG).intersection(SP(m.IN_U))
        poly(ax, list(sog.exterior.coords), fc="#f1e4cc", ec="none", z=4.1, alpha=0.75)
        line(ax, [(m.xw_i(m.Y_GR_O), m.Y_GR_O), (m.XEI, m.Y_GR_O)], color=EARTH, lw=0.9, ls=(0, (5, 2)), z=6.6)
    g = unit_plumbing(ax, unit)
    s1, s2, s3 = m.STACK_1, m.STACK_2, m.STACK_3
    vtr = ", VTR" if not A else ""

    # ---------------- labels on the plan ----------------
    note(ax, 13.3, 29.2, f"STACK 1, 3 in.{vtr}\nin the 2x6 wall", to=(s1[0], s1[1] + 0.15), color=SAN, size=4.6, weight="bold", frm=(15.2, 28.7))
    note(ax, 12.2, 37.3, f"STACK 2, 3 in.{vtr}\nin the pipe space behind\nthe furred wall", to=(s2[0] - 0.15, s2[1]), color=SAN, size=4.6, weight="bold", frm=(17.3, 37.0))
    note(ax, 41.6, 32.9, f"STACK 3, 3 in.{vtr}\nin the pipe space behind bath 3", to=(s3[0] + 0.05, s3[1] + 0.15), color=SAN, size=4.6, weight="bold", frm=(42.2, 32.4))
    note(ax, 29.2, 15.6, "ISLAND SINK + DISHWASHER\n2 in. drain down through the floor.\nAAV (air admittance valve) in the\ncabinet, 4 in. min. above the trap arm.\nDishwasher: high loop to the sink\ntailpiece; hot from the sink supply",
         to=(g["sd"][0] + 0.25, g["sd"][1] + 0.7), color=SAN, size=4.4, frm=(29.1, 17.0))
    note(ax, 21.3, 19.6, f"2 in. kitchen + washer drain in the\nfloor trusses to {'chase 2' if A else 'stack 2'}: {trunk:.0f} ft,\nfalls {trunk / 4:.1f} in. at 1/4 in. per ft",
         to=(s2[0], 19.9), color=SAN, size=4.4, frm=(21.2, 19.9))
    note(ax, 28.0, 20.3, "WB: recessed washer box, hot + cold\n1/4-turn valves, 2 in. standpipe and\ntrap in the wall, 1 1/2 in. vent",
         to=(g["wb"][0] + 0.25, g["wb"][1] - 0.2), color=SAN, size=4.4, frm=(27.9, 20.6))
    note(ax, 12.9, 18.9, "IM: recessed ice-maker box behind\nthe refrigerator, 1/2 in. cold\nwith a stop", to=(g["im"][0] - 0.3, g["im"][1]), color=CW, size=4.4, frm=(18.1, 18.3))
    note(ax, 28.3, 23.2, "WATER HEATER, 80 gal, 4.5 kW, on a 26 in. pan.\nExpansion tank on the cold inlet. T&P relief to the pan.\nCold + hot PEX MANIFOLDS on the closet wall above\nthe heater, 5'-6\" up, a labelled valve on every line",
         to=(MAN_X + 0.05, MAN_Y[0] + 0.5), color=CW, size=4.4, frm=(28.2, 23.9))
    txt(ax, 32.3, YC + 0.3, "3/4\" C  +  1/2\" H  to bath 3", size=4.2, color=CW, weight="bold", z=14, box=True)
    txt(ax, 16.4, YC + 0.32, "3/4\" C  +  1/2\" H  to bath 1", size=4.2, color=CW, weight="bold", z=14, box=True)
    txt(ax, 32.3, g["yp"] + 0.3, "1 in. PAN DRAIN in the floor trusses to the utility-room floor drain", size=4.0, color=SAN, weight="bold", z=14, box=True)
    txt(ax, g["xk"] + 0.78, 21.9, "1/2\" C + H", size=3.8, color=CW, weight="bold", rot=90, z=14, box=True)
    txt(ax, g["wb"][0] - 0.5, 23.2, "1/2\" C + H", size=3.8, color=CW, weight="bold", rot=90, z=14, box=True)
    txt(ax, g["xwc"] + 0.4, 33.6, "1/2\" C", size=3.8, color=CW, weight="bold", rot=90, z=14, box=True)
    txt(ax, g["im"][0], 21.0, "1/2\" C", size=3.8, color=CW, weight="bold", rot=90, z=14, box=True)
    lab(ax, g["tx1"], m.Y4 + 0.62, "AP 1", APC, size=4.4)
    note(ax, 35.4, 31.55, "AP 3", to=(m.X_ST - 0.25, 30.75), color=APC, size=4.4, weight="bold", ha="right", frm=(35.5, 31.5))
    note(ax, 27.0, 33.1, "BATH 2 WATER: 3/4\" C + 1/2\" H from the manifolds,\nOVERHEAD in the 7'-0\" soffit (dotted), dropping in\nthe walls" + (". NEVER under the slab" if A else ", same as Unit A below"),
         to=(22.3, g["yoc"]), color=CW, size=4.4, frm=(26.9, 32.6))
    if A:
        txt(ax, (RISER_X + RISE_A[0]) / 2, RISE_A[1] - 0.32, "3/4\" COLD RISER in the floor trusses, from Unit A's shutoff + PRV in the utility room below", size=4.0, color=CW,
            weight="bold", z=14, box=True)
        note(ax, 28.3, 38.3, "SLAB ON GRADE (shaded), EL 925.5. Bath 2's toilet, tub and lavatory drains and the\n3 in. from stack 2 are under it: IN, TESTED AND INSPECTED BEFORE THE SLAB IS POURED.",
             to=(24.6, 34.6), color=EARTH, size=4.6, weight="bold", frm=(28.2, 37.7))
        txt(ax, 33.4, m.Y_GR_O + 0.3, "EDGE OF THE SLAB ON GRADE  (garage rear wall below)", size=3.9, color=EARTH, z=7)
        note(ax, 12.6, 31.6, "3 in. from stack 2 under the slab,\nthrough the 6 in. concrete upstand in\na sleeve, between two trusses,\nthen DOWN IN CHASE 2",
             to=[(s2[0] - 0.32, m.Y_GR_O - 0.5), (A2[0] - 0.3, A2[1])], color=SAN, size=4.4, frm=(18.9, 31.0))
        note(ax, 46.2, 22.3, f"HB: frost-proof hose bibb, 12 in.\nstem, vacuum breaker, in the floor\nrim at EL {EL_HB:.1f}. 1/2 in. cold from\nboard A in the utility room",
             to=(HB[0] + 0.6, HB[1] - 0.25), color=CW, size=4.4, frm=(46.3, 23.3))
        note(ax, 46.2, 26.6, "COLD RISER UP from the\nutility room below",
             to=(RISE_A[0] + 0.2, RISE_A[1] + 0.1), color=CW, size=4.4, frm=(46.1, 26.4))
        note(ax, 46.2, 28.4, "Pan drain DOWN to the\nfloor drain (air gap)", to=(g["pend"][0] + 0.25, g["pend"][1] + 0.1), color=SAN, size=4.4, frm=(46.1, 28.3))
    else:
        txt(ax, 32.3, RISE_B[1] + 0.32, "3/4\" COLD RISER in the floor trusses to the heater", size=4.0, color=CW, weight="bold", z=14, box=True)
        note(ax, 45.6, 33.6, "COLD RISER UP this pipe space from\nUnit B's shutoff + PRV in the utility\nroom, on the room side of the wall\ninsulation. Pan drain goes DOWN it\nto the utility-room floor drain",
             to=(RISE_B[0] + 0.2, RISE_B[1] + 0.1), color=CW, size=4.4, frm=(45.5, 33.0))
        note(ax, 27.0, 39.0, "VTR: each stack continues 3 in. through the roof, 12 in. above it, on the rear slope.\nUnit A's 2 in. vent risers come up beside each stack and join it 42 in. above this floor.",
             color=SAN, size=4.6, weight="bold")

    # ---------------- stack table, legend and keyed notes ----------------
    per = [("Stack 1", "Bath 1: toilet, tub, lavatory", DFU["bath"]),
           ("Stack 2", "Bath 2 + island sink + dishwasher + washer", DFU["bath"] + DFU["sink"] + DFU["dw"] + DFU["cw"]),
           ("Stack 3", "Bath 3: toilet, tub, lavatory", DFU["bath"])]
    rows = [["Stack", f"Unit {unit} fixtures on it", "DFU"]] + [[a_, b_, str(c_)] for a_, b_, c_ in per] + [["", "This flat, total", str(DFU_FLAT)]]
    table(bg, 6.75, 10.47, [0.55, 2.6, 0.4], rows, fs=5.2, rh=0.165)

    def s_v(b, x, y):
        b.add_patch(Circle((x, y), 0.028, fc=PAPER, ec=VENT, lw=0.8))

    def s_st(b, x, y):
        stack_dot(b, (x, y), SAN, r=0.04)

    def s_ap(b, x, y):
        b.add_patch(Rectangle((x - 0.15, y - 0.035), 0.3, 0.07, fc=APC, ec=APC))

    def s_r(b, x, y):
        riser(b, (x - 0.1, y), CW)
        riser(b, (x + 0.1, y), HW)

    def s_aav(b, x, y):
        b.add_patch(MPoly([(x - 0.07, y - 0.05), (x + 0.07, y - 0.05), (x, y + 0.07)], closed=True, fc=PAPER, ec=VENT, lw=0.9))

    def s_sog(b, x, y):
        b.add_patch(Rectangle((x - 0.2, y - 0.055), 0.4, 0.11, fc="#f1e4cc", ec=EARTH, lw=0.5))

    LX = 10.92
    rows_l = [
        ("line", SAN, 2.2, "-", "Drain: 3\" thick, 2\" medium, 1-1/2\" thin"),
        ("sym", s_st, "Stack, 3 in."),
        ("line", VENT, 0.8, DASH_V, "Vent, 1-1/2 in., in the wall or ceiling"),
        ("sym", s_v, "Vent riser in the wall"),
        ("sym", s_aav, "Air admittance valve (island)"),
        ("line", SAN, 0.9, (0, (4, 1.5, 1, 1.5)), "Water heater pan drain, 1 in."),
        ("line", CW, 2.2, "-", "Cold riser 3/4\" (thickest); cold PEX 3/4\", 1/2\""),
        ("line", HW, 0.85, DASH_H, "Hot PEX, 1/2 in."),
        ("line", CW, 1.35, DASH_OH, "Dotted: OVERHEAD in the soffit"),
        ("sym", s_r, "Stub up in the wall or cabinet, 1/2 in."),
        ("sym", s_ap, "Access panel (AP)"),
    ]
    if A:
        rows_l.append(("sym", s_sog, "Slab on grade"))
    yl = legend(bg, LX, 9.42, rows_l, dy=0.15, fs=5.1)
    common_k = [
        "*DRAINS AND VENTS",
        "Each bath: the lavatory drain joins the toilet branch, so",
        "the lavatory vent also vents the toilet (wet vent, IPC 912).",
        "Tub and lavatory each have a 1 1/2 in. vent in the wall.",
        "Vents shown are one workable scheme: the plumber may",
        "propose another that the code official accepts.",
        "Washer vent runs in the ceiling to the bath 2 vent.",
        "Firestop every pipe through the 1-hour floor and walls.",
        "",
        "*WATER",
        "Every home-run is one unbroken PEX line from its",
        "manifold valve: no fittings under the floor except the",
        "ice-maker tee. Stops at every fixture. Flat shutoff: the",
        "valve on the cold riser at the heater; main shutoff on the",
        "flat's board in the utility room.",
        "Heater pan: 1 in. drain by gravity to the utility-room",
        "floor drain. It cannot reach the washer standpipe: the",
        "standpipe inlet is 3 ft above the pan.",
        "",
        "*ACCESS",
        "AP 1: 14 x 14 in., bedroom 2 wall, behind the tub 1 valve.",
        "AP 3: 16 x 24 in. door from bedroom 3 into the pipe space:",
        "stack 3 cleanout and the " + ("Unit B riser." if A else "cold riser."),
        "Tub 2's valve wall is behind the water heater and tub 3's",
        "backs onto a 5 to 10 in. pipe space: no rear panel there.",
        "All tub valves: pressure-balance with integral stops,",
        "serviced from the tub side; glued (not slip-joint) waste",
        "and overflow. Limit 120 deg F.",
        "",
    ]
    if A:
        unit_k = [
            "*UNIT A ONLY",
            "Stack 1 offsets 1'-8\" in the floor trusses to chase 1.",
            "Stack 3 and Unit B's riser pass between two trusses over",
            "the wall's truss ledge; their pipe space stands over the",
            "6 in. upstand: framer and engineer to detail the opening.",
            "Keep every pipe in the trusses ABOVE the R-30 batts.",
        ]
    else:
        unit_k = [
            "*UNIT B ONLY",
            "Pipes cross the trusses through the open webs: keep the",
            "2 in. drain's fall (" + f"{trunk / 4:.1f}" + " in.) inside the 24 in. depth, clear",
            "of the duct soffits. Pipe space behind bath 3 is on an",
            "outside wall: pipes on the room side, R-20 behind them.",
        ]
    small_lines(bg, LX, yl - 0.08, common_k + unit_k, fs=4.9, dy=0.118)
    save(fig, number, pdf)


def sheet_p102(pdf):
    unit_sheet(pdf, "P-102", "A")


def sheet_p103(pdf):
    unit_sheet(pdf, "P-103", "B")


SHEETS = [("P-101", sheet_p101), ("P-102", sheet_p102), ("P-103", sheet_p103)]
