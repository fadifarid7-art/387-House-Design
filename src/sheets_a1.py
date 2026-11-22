"""Architectural plan sheets, Rev E: A-101 garage level, A-102 Unit A, A-103 Unit B, A-104 furniture
and clearances, A-105 roof, A-401 enlarged kitchen and baths.

Everything is drawn and dimensioned from model.py. Nothing here retypes a model number.
"""
import math

from matplotlib.patches import Rectangle
from shapely.geometry import Polygon as SPoly

from common import *  # noqa: F401,F403
import model as m
from plans import *  # noqa: F401,F403
import plans

IN = m.IN
T_R = math.atan(abs(REAR_SLOPE))                 # plan skew of the rear wall
U_R = (math.cos(T_R), -math.sin(T_R))            # along the rear wall, west -> east
N_R = (math.sin(T_R), math.cos(T_R))             # outward normal of the rear wall
U_W = (math.sin(WEST_LEAN), math.cos(WEST_LEAN))   # along the west wall, south -> north
N_W = (-math.cos(WEST_LEAN), math.sin(WEST_LEAN))  # outward normal of the west wall
VIEW_A = ((-12.0, 57.0), (-3.0, 50.0))           # unit plans: room for dimension strings and a notes strip
VIEW_G = ((-12.0, 57.0), (-10.0, 43.0))          # garage level with the apron and the street
SLAB = "#e9f0f7"
SWING = "#f6d9a8"
BAND = "#cfe3f5"


# ----------------------------------------------------------------------------
# local drafting helpers
# ----------------------------------------------------------------------------
def fi(v):
    """Feet and inches to the nearest 1/2 in. (ftin() rounds to the inch)."""
    h = round(abs(v) * 24)
    f, r = divmod(h, 24)
    i, half = divmod(r, 2)
    s = f"{f}'-{i}" + (" 1/2" if half else "") + '"'
    return ("-" if v < 0 else "") + s


def inch(v):
    """Small sizes in inches to the nearest 1/4 in."""
    q = round(v * 48)
    i, r = divmod(q, 4)
    return f"{i}" + {0: "", 1: " 1/4", 2: " 1/2", 3: " 3/4"}[r] + '"'


def D(ax, p0, p1, off=0.0, label=None, size=5.0, color=INK, ext=True, side=1, at=0.5, box=False, push=0.0, weight="normal"):
    """Dimension p0 -> p1, offset `off` ft to the left. `at` moves the text along the line (0..1, or
    outside), `push` moves it further off the line (ft), ext=False draws no extension lines."""
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -uy, ux
    fpi = ax.fpi
    tick = 0.065 * fpi
    toff = (0.032 + size / 72 * 0.62) * fpi + push
    a = (x0 + nx * off, y0 + ny * off)
    b = (x1 + nx * off, y1 + ny * off)
    line(ax, [a, b], color=color, lw=0.4, z=8)
    for (px, py), (qx, qy) in ((p0, a), (p1, b)):
        if ext and abs(off) > 1e-6:
            s = (0.05 if off > 0 else -0.05) * fpi
            line(ax, [(px + nx * s, py + ny * s), (qx + nx * s * 0.8, qy + ny * s * 0.8)], color=color, lw=0.25, z=8)
        line(ax, [(qx - (ux + nx) * tick / 2, qy - (uy + ny) * tick / 2),
                  (qx + (ux + nx) * tick / 2, qy + (uy + ny) * tick / 2)], color=color, lw=0.8, z=8)
    ang = math.degrees(math.atan2(uy, ux))
    if ang > 90.01 or ang <= -89.99:
        ang += 180
    mx = a[0] + (b[0] - a[0]) * at + nx * toff * side
    my = a[1] + (b[1] - a[1]) * at + ny * toff * side
    txt(ax, mx, my, label if label is not None else fi(L), size=size, color=color, rot=ang, box=box, z=9.5, weight=weight)
    return L


def chain(ax, pts, off, labels=None, size=4.8, color=INK, side=1, box=False, stub=0.09, min_len=None, ends=True):
    """Chain of dimensions through collinear points. Segments too short for their text stay unlabelled
    (they are wall thicknesses, given in the notes) unless a label is forced with labels[i]."""
    fpi = ax.fpi
    (x0, y0), (x1, y1) = pts[0], pts[-1]
    L = math.hypot(x1 - x0, y1 - y0)
    nx, ny = -(y1 - y0) / L, (x1 - x0) / L
    for i in range(len(pts) - 1):
        p, q = pts[i], pts[i + 1]
        d = math.dist(p, q)
        if d < 1e-4:
            continue
        lab = labels[i] if labels and labels[i] is not None else fi(d)
        need = (len(lab) * size * 0.50 / 72) * fpi if min_len is None else min_len
        show = lab if (d >= need or (labels and labels[i] is not None)) else ""
        D(ax, p, q, off, show, size=size, color=color, ext=False, side=side, box=box and bool(show))
    s = 1 if off > 0 else -1
    for i, (px, py) in enumerate(pts):
        qx, qy = px + nx * off, py + ny * off
        if ends and i in (0, len(pts) - 1):
            g = 0.05 * fpi * s
            line(ax, [(px + nx * g, py + ny * g), (qx + nx * g * 0.8, qy + ny * g * 0.8)], color=color, lw=0.25, z=8)
        else:
            g = stub * fpi * s
            line(ax, [(qx - nx * g, qy - ny * g), (qx + nx * g * 0.4, qy + ny * g * 0.4)], color=color, lw=0.25, z=8)


def leader(ax, tip, at, s, size=4.6, color=INK, ha=None, va="center", box=False, weight="normal", arrow=True):
    """Note with a leader line from the text position `at` to the thing at `tip`."""
    if arrow:
        ax.annotate("", xy=tip, xytext=at, zorder=9,
                    arrowprops=dict(arrowstyle="-|>", lw=0.35, color=color, mutation_scale=4.5, shrinkA=0, shrinkB=0))
    else:
        line(ax, [tip, at], lw=0.35, color=color, z=9)
    if ha is None:
        ha = "left" if at[0] >= tip[0] else "right"
    dx = 0.045 * ax.fpi * (1 if ha == "left" else -1 if ha == "right" else 0)
    txt(ax, at[0] + dx, at[1], s, size=size, color=color, ha=ha, va=va, box=box, weight=weight, z=9.6)


def ax_in(ax, x, y):
    """Plan point -> sheet inches."""
    b = ax.get_position()
    (x0, x1), (y0, y1) = ax.get_xlim(), ax.get_ylim()
    return (b.x0 * SHEET_W + (x - x0) / ax.fpi, b.y0 * SHEET_H + (y - y0) / ax.fpi)


def block(bg, x, y, head, lines, fs=5.6, lh=0.132, color=INK):
    """Small text block on the sheet (inches); returns the y below it."""
    if head:
        bg.text(x, y, head.upper(), fontsize=fs + 0.6, fontweight="bold", color=color, va="top")
        y -= lh * 1.35
    for ln in lines:
        bg.text(x, y, ln, fontsize=fs, color=color, va="top", linespacing=1.2)
        y -= lh * (ln.count("\n") + 1)
    return y - lh * 0.7


def crop_texts(ax):
    """Texts are not clipped by matplotlib: drop those a base-plan helper put outside this view."""
    (x0, x1), (y0, y1) = ax.get_xlim(), ax.get_ylim()
    for t in list(ax.texts):
        x, y = t.get_position()
        if not (x0 <= x <= x1 and y0 <= y <= y1):
            t.remove()


def rear_pt(x):
    """Point on the outside face of the rear wall square to the inside face at station x."""
    return (x + N_R[0] * m.EXT, m.yr_i(x) + N_R[1] * m.EXT)


def west_pt(y):
    """Point on the outside face of the west wall square to the inside face at station y."""
    return (m.xw_i(y) + N_W[0] * m.EXT, y + N_W[1] * m.EXT)


def lot_labels(ax):
    txt(ax, 30.0, rear_y(30.0) + 0.75, "REAR LOT LINE", size=5.0, color=ACCENT, rot=-math.degrees(T_R))
    yy = 3.6
    txt(ax, west_x(yy) - 0.75, yy, "WEST LOT LINE", size=5.0, color=ACCENT, rot=90 - math.degrees(WEST_LEAN))


def clr(v):
    """Clear heights: rounded DOWN to the inch."""
    t = math.floor(v * 12 + 1e-6)
    return f"{t // 12}'-{t % 12}\""


def setbacks(ax, front_x=48.6, east="ne", rear="nw", rear_tag="", size=5.0):
    """Wall face to lot line, in red, at the corners (clear of the black strings)."""
    D(ax, (front_x, 0.0), (front_x, m.YF), 0, ftin(m.YF), color=ACCENT, ext=False, size=size)
    if front_x > m.XE:
        line(ax, [(m.XE + 0.3, m.YF), (front_x + 0.5, m.YF)], color=ACCENT, lw=0.25, z=8)
    if east == "ne":
        ne = m.OUT_U[2]
        D(ax, ne, (50.0, ne[1]), 1.5, ftin(50.0 - m.XE), color=ACCENT, size=size)
    else:
        se = m.OUT_U[1]
        D(ax, se, (50.0, se[1]), -1.5, ftin(50.0 - m.XE), color=ACCENT, size=size, side=-1)
    sw = m.OUT_U[0]
    foot = (sw[0] + N_W[0] * perp_to_west(*sw), sw[1] + N_W[1] * perp_to_west(*sw))
    D(ax, foot, sw, -1.3, ftin(perp_to_west(*sw)), color=ACCENT, size=size, side=-1)
    c = m.OUT_U[3] if rear == "nw" else m.OUT_U[2]
    d = perp_to_rear(*c)
    D(ax, c, (c[0] + N_R[0] * d, c[1] + N_R[1] * d), 1.5 if rear == "nw" else -3.2, ftin(d) + rear_tag, color=ACCENT, size=size,
      side=1 if rear == "nw" else -1)


# ----------------------------------------------------------------------------
# A-101  Garage level plan
# ----------------------------------------------------------------------------
def sheet_a101(pdf):
    util_w, util_d = m.UTIL[1] - m.UTIL[0], m.UTIL[3] - m.UTIL[2]
    lo = m.STAIR_LO
    x0, x1, y0, y1 = m.SHAFT_L
    land = 3.25
    run = lo["treads_per_flight"] * lo["tread_in"] / 12
    flight = (x1 - x0 - 4 * IN) / 2
    notes = [
        ("Open garage", [
            f"Slab EL {m.EL_GAR:.1f}, broom finish, sealed (S-103).",
            f"Open front {ftin(m.OPEN_W)} wide. NO doors, NO operators.",
            f"Clear {clr(m.OPEN_CLEAR_H)} under beam B1, {clr(m.CLG_GAR)} to ceiling.",
            f"Opening = {m.GARAGE_PCT:.0f} % of the {ftin(m.FACADE_W)} front (65 max).",
            f"3 design cars {ftin(m.CAR_W)} x {ftin(m.CAR_L)}. Stalls are",
            "painted lines only. One steel post, on a line.",
        ]),
        ("Because it is open", [
            "The garage is at outdoor temperature: NO",
            "water pipe in it. Both services enter the",
            "heated utility room below grade (P-101).",
            "Drains cross in the insulated truss space",
            "and drop in 1-hour chases on the rear wall.",
            "Ceiling 5/8 in. Type X, R-30 above (A-501).",
        ]),
        ("Utility room and stair", [
            f"Utility: heated, {fi(util_w)} x {fi(util_d)}, with",
            "both 80 gal water heaters. Its 2'-8\" door",
            "swings INTO the room, never toward a car.",
            f"Stair to Unit A: {lo['risers']} risers at {lo['riser_in']:.2f} in.,",
            f"{lo['tread_in']} in. treads, flights {fi(flight)} wide between",
            "the concrete walls, 1-hour enclosure (A-402).",
        ]),
        ("Outside", [
            "Bike hooks on the west wall at the back.",
            "Trash bay: 4 carts, screened, on the lot.",
            "Nothing in the right-of-way but the apron.",
        ]),
        ("To confirm", [
            "Wall, footing and beam sizes: engineer.",
            "Lot lines and all setbacks: survey.",
        ]),
    ]
    fig, bg = new_sheet("A-101", "Garage level plan", "3/16\" = 1'-0\"", notes)
    ax = plan_frame(fig, "Garage level plan", f"Open 3-car garage · slab EL {m.EL_GAR:.1f} · concrete shown grey",
                    view=VIEW_G, street=True, bottom=0.5)
    lot_labels(ax)
    # unexcavated ground under Unit A's slab on grade, and the floors above
    poly(ax, m.SOG, fc="#f6f1ea", ec=EARTH, lw=0.0, z=1.2, hatch="////", alpha=0.75)
    line(ax, m.OUT_U + [m.OUT_U[0]], color=GREY, lw=0.7, ls=(0, (5, 3)), z=7)
    txt(ax, 20.5, 34.0, "UNEXCAVATED\nUnit A slab on grade above (S-103)", size=4.8, color=EARTH, box=True, weight="bold")
    leader(ax, (26.0, m.yr_o(26.0)), (28.5, 38.9), "LINE OF UNIT A AND B WALLS ABOVE (dashed)", size=4.4, color=GREY)
    site_work(ax)
    rect(ax, *m.PORCH[:2], *m.PORCH[2:], fc="none", ec=GREY, lw=0.5, z=6.5, ls=(0, (5, 3)))
    lower_plan(ax, "arch")
    line(ax, [(m.COL_X[0], m.B1_Y), (m.COL_X[2], m.B1_Y)], color=BLUE, lw=0.6, ls=(0, (8, 2, 2, 2)), z=7.5)
    # drain chases on the rear wall (coordination with P-101)
    for i, (cx, cy) in enumerate((m.CHASE_1, m.CHASE_2)):
        rect(ax, cx - 0.67, cy - 0.67, cx + 0.67, m.Y_GR_I, fc=PAPER, ec=RATED, lw=0.6, z=6.6)
        txt(ax, cx, (cy - 0.67 + m.Y_GR_I) / 2, f"C{i + 1}", size=3.8, color=RATED, z=9)

    # ---- inside dimensions ----
    yf_in = m.YF + m.CONC
    D(ax, (m.xw_gi(yf_in + 0.55), yf_in + 0.55), (m.GAR_X1, yf_in + 0.55), 0, None, ext=False, at=0.075, size=4.8)
    y = m.CAR_Y0 + 6.4
    pts = [(m.xw_gi(y), y)]
    for c in m.CARS:
        pts += [(c, y), (c + m.CAR_W, y)]
    pts.append((m.GAR_X1, y))
    chain(ax, pts, 0.0, size=4.6, color=BLUE, labels=[None, None, None, None, None, None, ""], ends=False, box=True)
    xg = (m.CARS[2] + m.CAR_W + m.GAR_X1) / 2
    leader(ax, (xg, y), (xg - 0.9, y + 1.6), fi(m.GAR_X1 - m.CARS[2] - m.CAR_W), size=4.6, color=BLUE, ha="center", va="bottom", arrow=False)
    y = m.CAR_Y0 + 12.9
    pts = [(m.xw_gi(y), y)] + [(sx, y) for sx in m.STALL_LINES] + [(m.GAR_X1, y)]
    chain(ax, pts, 0.0, size=4.6, labels=[f"STALL 1  {fi(pts[1][0] - pts[0][0])}", f"STALL 2  {fi(pts[2][0] - pts[1][0])}",
                                         f"STALL 3  {fi(pts[3][0] - pts[2][0])}"], ends=False, box=True)
    x = 11.0
    chain(ax, [(x, m.YF), (x, m.CAR_Y0), (x, m.CAR_Y0 + m.CAR_L), (x, m.Y_GR_I)], 0.0, size=4.4, color=BLUE, ends=False,
          labels=[fi(m.CAR_Y0 - m.YF), fi(m.CAR_L) + " CAR", ""])
    leader(ax, (x, m.Y_GR_I - 0.5), (x + 0.5, m.Y_GR_I - 1.9), fi(m.Y_GR_I - m.CAR_Y0 - m.CAR_L), size=4.4, color=BLUE,
           ha="center", va="top", arrow=False)
    D(ax, (xg, m.YF), (xg, m.Y_GR_I), 0, fi(m.Y_GR_I - m.YF) + " DEEP", ext=False, size=4.8, at=0.3)
    # stair shaft
    D(ax, (x0, y1 - 0.75), (x1, y1 - 0.75), 0, fi(x1 - x0), ext=False, size=4.6)
    txt(ax, (x0 + x1) / 2, y1 - 1.85, "MID LANDING", size=3.8, color=GREY)

    # ---- strings outside the walls ----
    yy = m.YF - 1.75
    chain(ax, [(m.xw_o(m.YF), m.YF), (m.OPEN[0], m.YF), (m.OPEN[1], m.YF), (m.ENTRY[0], m.YF), (m.ENTRY[1], m.YF), (m.XE, m.YF)],
          yy - m.YF, size=4.8, labels=[fi(m.OPEN[0] - m.xw_o(m.YF)) + " PIER", fi(m.OPEN_W) + " CLEAR OPENING, NO DOORS", None,
                                       fi(m.ENTRY[1] - m.ENTRY[0]) + " DOOR", None])
    chain(ax, [(m.OPEN[0], m.YF), (m.COL_X[1], m.YF), (m.OPEN[1], m.YF)], yy - 1.2 - m.YF, size=4.6,
          labels=[fi(m.COL_X[1] - m.OPEN[0]) + " TO CENTRE OF POST", None], ends=False)
    D(ax, (m.xw_o(m.YF), m.YF), (m.XE, m.YF), yy - 3.3 - m.YF, ftin(m.FACADE_W) + " FRONT OF BUILDING", size=4.8, at=0.3)
    # rear: inside widths and wall thicknesses, read over the hatch
    yr = m.Y_GR_O
    chain(ax, [(m.xw_o(yr), yr), (m.xw_gi(m.Y_GR_I), yr), (m.GAR_X1, yr), (m.SHAFT_X0, yr), (m.XE_GI, yr), (m.XE, yr)], 1.2, size=4.6,
          labels=[inch(m.CONC), fi(m.GAR_X1 - m.xw_gi(m.Y_GR_I)) + " INSIDE AT REAR WALL", inch(m.CMU),
                  fi(util_w) + " UTILITY", inch(m.CONC)], box=True)
    D(ax, (m.xw_o(yr), yr), (m.XE, yr), 2.5, fi(m.XE - m.xw_o(yr)) + " OUTSIDE AT REAR WALL", size=4.8, box=True, at=0.6)
    # east: stair and utility room
    xe = m.XE
    chain(ax, [(xe, m.YF), (xe, y0), (xe, y0 + land), (xe, y0 + land + run), (xe, y1), (xe, m.UTIL[2]), (xe, m.Y_GR_I), (xe, m.Y_GR_O)], -1.4,
          size=4.4, labels=["", fi(land), fi(run), fi(y1 - y0 - land - run), "", fi(util_d), ""])
    D(ax, (xe, m.YF), (xe, m.Y_GR_O), -2.7, fi(m.Y_GR_O - m.YF), size=4.8)
    # west wall along its own direction
    D(ax, m.OUT_L[0], m.OUT_L[3], 2.9, fi(math.dist(m.OUT_L[0], m.OUT_L[3])) + " ALONG WALL", size=4.8)
    setbacks(ax, front_x=8.6, east="se", rear="ne")

    # ---- notes on the plan ----
    T = dict(size=4.5)
    txt(ax, 24.0, 27.25, f"CEILING {clr(m.CLG_GAR)} CLEAR", size=4.6, weight="bold", box=True)
    leader(ax, (16.5, m.B1_Y), (13.4, m.YF + 1.3), f"STEEL BEAM B1 OVER (S-104): {clr(m.OPEN_CLEAR_H)} CLEAR UNDER IT", size=4.4, color=BLUE,
           ha="left", arrow=False)
    leader(ax, (m.COL_X[1] + 0.25, m.YF + 0.33), (29.6, m.YF + 1.3), "STEEL POST (S-104)", size=4.4, color=BLUE, arrow=False)
    leader(ax, (m.xw_gi(27.0), 27.0), (3.2, 30.6), "BIKE HOOKS ON THIS WALL,\nAT THE BACK", ha="right", **T)
    leader(ax, (m.xw_o(15.0) + 0.5, 15.0), (2.0, 16.6), f"{inch(m.CONC)} CONCRETE RETAINING\nWALL ON 3 SIDES (S-102)", ha="right", **T)
    leader(ax, (m.HP[1][0] - 0.4, m.HP[1][1]), (2.6, 25.4), "HEAT-PUMP PADS\nA AND B (M-101)", ha="right", **T)
    line(ax, [(m.HP[0][0] - 0.4, m.HP[0][1]), (4.3, 23.9)], lw=0.3, z=9)
    txt(ax, (m.CHASE_1[0] + m.CHASE_2[0]) / 2, 26.55, "C1, C2: DRAIN CHASES, 1-HOUR,\nINSULATED, 16 x 16 in. (P-101)", size=3.9, color=RATED, box=True)
    leader(ax, (m.XE, 27.0), (50.9, 27.0), f"UTILITY ROOM (heated)\n{fi(util_w)} x {fi(util_d)} clear\nDoor swings in.\nWH A, WH B: 80 gal", arrow=False, **T)
    leader(ax, (m.XE_GI - 0.6, m.UTIL[2] - m.CMU / 2), (50.9, 23.2), f"{inch(m.CMU)} CONCRETE OR\nGROUTED BLOCK:\nlobby wall and stair /\nutility wall (S-101)", **T)
    leader(ax, (m.XE, 15.5), (50.9, 15.5), f"COMMON STAIR\nflights {fi(flight)} wide\n{lo['risers']} risers to Unit A", arrow=False, **T)
    leader(ax, (m.XE - 1.0, 1.9), (46.3, 4.6), "TRASH BAY, 4 CARTS,\nSCREENED (C-107)", **T)
    txt(ax, 40.9, 4.4, f"ENTRY LANDING\nEL {m.EL_GAR:.1f}, level", size=4.2)
    leader(ax, (14.5, m.YF - 0.6), (3.0, 12.9), "TRENCH DRAIN ACROSS\nTHE OPENING (C-105)", ha="right", color=BLUE, **T)
    leader(ax, ((m.WING_W[0][0] + m.WING_W[1][0]) / 2, 5.3), (7.6, 3.3), "WING WALL RETAINS\nTHE FRONT YARD (C-107)", ha="right", **T)
    txt(ax, 24.3, 3.0, "CONCRETE APRON (C-107)", size=5.4, weight="bold")
    D(ax, m.APRON[5], m.APRON[2], 0.0, fi(m.APRON_W_ROW) + " AT THE RIGHT-OF-WAY LINE", ext=False, size=4.6)
    txt(ax, 24.3, -3.6, "CITY RIGHT-OF-WAY: APRON ONLY. NO WALLS, STEPS OR POSTS.", size=4.8, color=ACCENT)
    txt(ax, 22.0, m.PORCH[1] + 0.45, "PORCHES ABOVE CANTILEVER 4'-0\" (dashed): NO POSTS", size=4.2, color=GREY, box=True)
    txt(ax, 4.6, 7.2, "FRONT YARD STAYS\nAT NATURAL GRADE", size=4.2, color=GREY)
    save(fig, "A-101", pdf)


# ----------------------------------------------------------------------------
# A-102 / A-103  Unit plans
# ----------------------------------------------------------------------------
def room_size(name):
    """Clear size text for the room list (all from the model)."""
    if name in ("BEDROOM 1", "BEDROOM 2", "BEDROOM 3", "LIVING / KITCHEN"):
        w, d = m.room_dims(name)
        return f"{fi(w)} x {fi(d)}"
    if name == "CLOSET 3":
        return f"{fi(m.C3_X - m.X_B3)} x {fi(m.yr_i(m.C3_X) - m.C3_Y - m.PART)} min."
    xs = [p[0] for p in m.ROOMS[name]]
    ys = [p[1] for p in m.ROOMS[name]]
    if name == "BATH 2":
        return f"{fi(max(xs) - min(xs))} x {fi(m.B2_Y1 - m.B2_Y0)}"
    return f"{fi(max(xs) - min(xs))} x {fi(max(ys) - min(ys))}"


def room_table(bg, x, y, fs=5.0, rh=0.152):
    rows = [("ROOM", "CLEAR SIZE", "AREA")]
    for k in m.ROOMS:
        rows.append((k.title().replace("W/D", "Washer / dryer").replace(" / K", " / k"), room_size(k), f"{m.area(k):.0f} sf"))
    rows.append(("NET, inside the walls", "less the stair", f"{m.net_area():.0f} sf"))
    return table(bg, x, y, [0.86, 0.86, 0.40], rows, fs=fs, rh=rh)


def above_floor(el):
    """Stretches of the rear and west walls where existing ground is above floor level `el`."""
    nw, ne, sw = m.OUT_U[3], m.OUT_U[2], m.OUT_U[0]
    Lr, Lw = math.dist(nw, ne), math.dist(sw, nw)
    r = [s for s in [i * 0.25 for i in range(int(Lr / 0.25) + 1)]
         if elev(nw[0] + U_R[0] * s + N_R[0] * 1.5, nw[1] + U_R[1] * s + N_R[1] * 1.5) > el]
    w = [s for s in [i * 0.25 for i in range(int(Lw / 0.25) + 1)]
         if elev(sw[0] + U_W[0] * s + N_W[0] * 1.5, sw[1] + U_W[1] * s + N_W[1] * 1.5) > el]
    return (max(r) if r else 0.0), (min(w) if w else Lw), Lw


def unit_dims(ax, unit):
    """All dimension strings of a unit plan. Outside: openings / rooms / overall on each wall."""
    o1, o2, o3 = 1.9, 3.1, 4.3
    sw, se, ne, nw = m.OUT_U
    S = dict(size=4.5)
    # front wall (strings below the porch)
    yb = m.PORCH[1]
    f = lambda x: (x, m.YF)
    ops = sorted([(s0, s1) for (t, w_, s0, s1, n) in m.WINDOWS if w_ == "S"] + [(d["s0"], d["s1"]) for d in m.DOORS if d["tag"] == "D14"])
    chain(ax, [sw] + [f(v) for o in ops for v in o] + [se], yb - 0.95 - m.YF, **S)
    chain(ax, [sw, f(m.xw_i(m.YFI)), f(m.E1), f(m.X_H0), f(m.X_ST), f(m.SHAFT_X0), f(m.XEI), se], yb - 2.15 - m.YF, **S)
    D(ax, sw, se, yb - 3.35 - m.YF, fi(m.FACADE_W) + " FRONT WALL", size=5.2, weight="bold")
    # east wall
    e = lambda y: (m.XE, y)
    chain(ax, [se, e(m.YFI), e(m.SHAFT_U[3]), e(m.Y_ST), e(m.B3_Y1), e(m.B3_Y1 + m.PART), ne], -1.5, **S)
    D(ax, se, ne, -2.7, fi(math.dist(se, ne)) + " EAST WALL", size=5.2, weight="bold")
    # rear wall, along its own direction
    ops = sorted((s0, s1) for (t, w_, s0, s1, n) in m.WINDOWS if w_ == "N")
    chain(ax, [nw] + [(v, m.yr_o(v)) for o in ops for v in o] + [ne], o1, **S)
    xs = [m.IN_U[3][0], m.E1, m.X_H0, m.X_C1, m.X_B3, m.C3_X, m.C3_X + m.PART, m.X_ST, m.SHAFT_X0, m.XEI]
    chain(ax, [nw] + [rear_pt(x) for x in xs] + [ne], o2, **S)
    D(ax, nw, ne, o3, fi(m.REAR_WALL_LEN) + " REAR WALL, MEASURED ALONG THE WALL", size=5.2, weight="bold")
    # west wall, along its own direction
    ops = sorted((s0, s1) for (t, w_, s0, s1, n) in m.WINDOWS if w_ == "W")
    chain(ax, [sw] + [(m.xw_o(v), v) for o in ops for v in o] + [nw], o1, **S)
    ys = [m.YFI, m.Y1, m.Y2, m.CL_Y, m.CL_Y + m.PART, m.Y3, m.Y4, m.IN_U[3][1]]
    chain(ax, [sw] + [west_pt(y) for y in ys] + [nw], o2, **S)
    D(ax, sw, nw, o3, fi(m.WEST_WALL_LEN) + " WEST WALL, MEASURED ALONG THE WALL", size=5.2, weight="bold")
    # porch
    D(ax, (m.PORCH[0], m.PORCH[1]), (m.PORCH[0], m.PORCH[3]), 0.7, fi(m.PORCH[3] - m.PORCH[1]), size=4.6)

    # ---- inside the rooms (each line reads true where it is drawn) ----
    I = dict(ext=False, size=4.6)
    y = m.YFI + 0.65
    D(ax, (m.xw_i(y), y), (m.E1, y), 0, **I)                                   # bedroom 1 width at the front wall
    D(ax, (8.75, m.YFI), (8.75, m.Y1), 0, **I)                                 # bedroom 1 depth
    y = 31.15
    D(ax, (m.xw_i(y), y), (m.E1, y), 0, **I)                                   # bedroom 2 width
    D(ax, (16.7, m.Y4), (16.7, m.yr_i(16.7)), 0, **I)                          # bedroom 2 depth
    D(ax, (m.X_B3, 28.3), (m.X_ST, 28.3), 0, **I)                              # bedroom 3 width
    D(ax, (30.4, m.Y2), (30.4, m.yr_i(30.4)), 0, at=0.36, **I)                 # bedroom 3 depth to the rear wall
    y = m.Y1 - 0.45
    D(ax, (m.X_H0, y), (m.X_ST, y), 0, side=-1, **I)                           # living / kitchen width
    D(ax, (30.6, m.YFI), (30.6, m.Y1), 0, at=0.62, **I)                        # living / kitchen depth
    D(ax, (m.KIT_BASE[2], 14.4), (m.ISLAND[0], 14.4), 0, ext=False, size=4.2)  # kitchen aisle
    D(ax, (m.X_H0, 29.62), (m.X_H1, 29.62), 0, side=-1, ext=False, size=4.2)   # hall width
    D(ax, (m.SHAFT_U[0], m.SHAFT_U[3] - 0.8), (m.SHAFT_U[1], m.SHAFT_U[3] - 0.8), 0, **I)   # stair shaft
    for (x0, y0, x1, y1) in m.TUBS:                                            # 5'-0" tub alcoves
        D(ax, (x1 - 0.62, y0), (x1 - 0.62, y1), 0, ext=False, size=4.4, color=BLUE, side=-1)


def unit_names(ax, unit):
    def name(x, y, k, label=None, fs=5.6):
        txt(ax, x, y, label or k, size=fs, weight="bold", box=True)
        w, d = m.room_dims(k)
        txt(ax, x, y - 0.95, f"{fi(w)} x {fi(d)} clear · {m.area(k):.0f} sf", size=4.5, box=True)

    name(13.7, 16.6, "BEDROOM 1")
    name(13.3, 33.9, "BEDROOM 2")
    name(33.4, 25.9, "BEDROOM 3")
    name(34.0, 17.9, "LIVING / KITCHEN")
    txt(ax, 23.7, 11.75, "KITCHEN", size=4.4, weight="bold")
    for i, (x0, y0, x1, y1) in enumerate(m.TUBS):
        txt(ax, x0 + 0.72, (y0 + y1) / 2, f"BATH {i + 1}", size=4.4, weight="bold", rot=90)
    txt(ax, 21.42, 23.6, "HALL", size=4.0, color=GREY, rot=90)
    txt(ax, 10.4, 22.75, f"CLOSET\n{fi(m.CL_Y - m.Y2)} deep", size=3.7, color=GREY)
    txt(ax, 10.5, 25.4, f"CLOSET\n{fi(m.Y3 - m.CL_Y - m.PART)} deep", size=3.7, color=GREY)
    txt(ax, 28.05, 32.3, f"CLOSET\n{fi(m.C3_X - m.X_B3)} wide", size=3.7, color=GREY)
    txt(ax, 24.75, 28.95, "LINEN", size=3.4, color=GREY)
    txt(ax, (m.SHAFT_U[0] + m.SHAFT_U[1]) / 2, 12.2, "COMMON\nSTAIR", size=4.4, color=GREY)


def unit_sheet(pdf, number, unit):
    A = unit == "A"
    el = m.EL_A if A else m.EL_B
    clg = m.CLG_A if A else m.CLG_B
    st_ = m.STAIR_LO if A else m.STAIR_UP
    walls = ("Walls (finished thickness)", [
        f"Exterior 2x6: {inch(m.EXT)}. Partitions 2x4: {inch(m.PART)}.",
        f"Plumbing walls 2x6: {inch(m.WET)}. Stair walls 2x4",
        f"with 5/8 in. Type X each side: {inch(m.RATED)}, 1-hour.",
        "No interior wall carries the floor above.",
    ])
    if A:
        r_len, w_from, w_len = above_floor(m.EL_A)
        notes = [
            ("Unit A (lower flat)", [
                f"Finished floor EL {m.EL_A:.1f}, {ftin(m.EL_A - m.EL_GAR)} above the",
                f"garage slab. Ceiling {clr(clg)}; duct soffits at",
                f"{clr(m.CLG_SOFFIT)} (M-102). 3 bedrooms, 3 baths.",
                f"{m.net_area():.0f} sf inside the walls, less the stair.",
            ]),
            ("Two kinds of floor, one level", [
                "South of the dashed blue line: 20 in.",
                "open-web floor trusses over the garage",
                "(S-201). North of it (tinted): 5 in. slab on",
                "grade with R-10 under and at the edge",
                "(S-103). The line is the outside face of",
                "the garage rear wall below.",
            ]),
            ("Ground above the floor", [
                "Brown band: existing ground outside is",
                f"above this floor, up to {max(elev(*m.OUT_U[3]) - m.EL_A, 0):.1f} ft at the north-",
                "west corner. There the concrete stem wall",
                "rises to 8 in. above finished grade and",
                "the frame wall starts on top of it (S-101).",
                "Rear yard is cut to a swale (C-105).",
            ]),
            ("Escape windows", [
                "One W1 casement in each bedroom: 5.7 sf",
                "clear opening, sill 30 in. (IRC R310).",
                "Grade must stay below those sills.",
            ]),
            walls,
        ]
    else:
        notes = [
            ("Unit B (upper flat)", [
                f"Finished floor EL {m.EL_B:.1f}, {ftin(m.EL_B - m.EL_A)} above Unit A.",
                f"Ceiling {clr(clg)}; duct soffits at {clr(m.CLG_SOFFIT)} (M-103).",
                f"3 bedrooms, 3 baths. {m.net_area():.0f} sf inside the",
                "walls, less the stair.",
            ]),
            ("What differs from Unit A", [
                "Same walls, doors and fixtures, so baths,",
                "kitchens and closets stack. Differences:",
                "1. Whole floor is on 24 in. open-web",
                "   trusses, front wall to rear wall (S-202).",
                f"2. Stair ends here: {st_['risers']} risers at {st_['riser_in']:.1f} in.",
                "   from Unit A, no flight up.",
                "3. Attic access 22 x 30 in. in the hall",
                "   ceiling, insulated and gasketed.",
                "4. Porch is covered by the roof overhang.",
                "5. Supply ducts stay in the soffits:",
                "   nothing in the attic.",
                f"6. {m.PANEL_B_AMPS} A panel (Unit A: {m.PANEL_A_AMPS} A, it also",
                "   carries the common loads).",
            ]),
            ("Fire separation", [
                "Floor/ceiling to Unit A: 1-hour (R302.3).",
                "Stair walls 1-hour, to the roof deck.",
                "Unit door D1: 20-minute, self-closing.",
            ]),
            walls,
        ]
    fig, bg = new_sheet(number, f"Unit {unit} plan", "3/16\" = 1'-0\"", notes)
    ax = plan_frame(fig, f"Unit {unit} floor plan", f"Finished floor EL {el:.1f} · ceiling {clr(clg)} · {m.net_area():.0f} sf net",
                    view=VIEW_A, bottom=0.5)
    lot_labels(ax)
    st = plans.Style("arch")
    plans.porch(ax)
    if A:
        tint = SPoly(m.SOG).intersection(SPoly(m.IN_U))
        poly(ax, list(tint.exterior.coords)[:-1], fc=SLAB, ec="none", z=4.3)
    unit_shell(ax, st, unit, tags=True)
    unit_fixtures(ax, st, labels=True)
    if A:
        yl = m.Y_GR_O
        line(ax, [(m.xw_o(yl) - 1.0, yl), (m.XE + 0.8, yl)], color=BLUE, lw=0.8, ls=(0, (6, 2.5)), z=7.6)
        txt(ax, 13.2, yl + 0.42, "SLAB ON GRADE THIS SIDE (S-103)", size=4.0, color=BLUE, box=True)
        txt(ax, 13.2, yl - 0.45, "FLOOR TRUSSES THIS SIDE (S-201)", size=4.0, color=BLUE, box=True)
        txt(ax, 33.4, yl + 0.42, "SLAB ON GRADE", size=4.0, color=BLUE, box=True)
        txt(ax, 33.4, yl - 0.45, "FLOOR TRUSSES", size=4.0, color=BLUE, box=True)
        # where the ground is above this floor
        nw, sw = m.OUT_U[3], m.OUT_U[0]
        a, b = 0.14, 0.42
        P = lambda s, o: (nw[0] + U_R[0] * s + N_R[0] * o, nw[1] + U_R[1] * s + N_R[1] * o)
        poly(ax, [P(-b * 0.2, a), P(r_len, a), P(r_len, b), P(-b * 0.2, b)], fc=EARTH, ec="none", z=6, alpha=0.75)
        Q = lambda s, o: (sw[0] + U_W[0] * s + N_W[0] * o, sw[1] + U_W[1] * s + N_W[1] * o)
        poly(ax, [Q(w_from, a), Q(w_len + b * 0.2, a), Q(w_len + b * 0.2, b), Q(w_from, b)], fc=EARTH, ec="none", z=6, alpha=0.75)
        leader(ax, P(6.2, b), (16.5, 47.0), "GROUND IS ABOVE THIS FLOOR ALONG THE BROWN BAND:\nCONCRETE STEM WALL TO 8 in. ABOVE GRADE (S-101)",
               size=4.4, color=EARTH, ha="left")
    else:
        hx = m.X_H0 + (m.X_H1 - m.X_H0 - 22 * IN) / 2
        rect(ax, hx, 24.75, hx + 22 * IN, 24.75 + 30 * IN, fc="none", ec=BLUE, lw=0.6, ls=(0, (3, 2)), z=8)
        txt(ax, hx + 11 * IN, 26.0, "ATTIC ACCESS\n22 x 30 in.", size=3.3, color=BLUE, rot=90, z=9.5)
    unit_dims(ax, unit)
    unit_names(ax, unit)
    cover = "ROOF OVERHANG ABOVE" if not A else "UNIT B PORCH ABOVE"
    txt(ax, 28.3, m.PORCH[1] + 1.55, f"COVERED PORCH  {fi(m.PORCH[2] - m.PORCH[0])} x {fi(m.PORCH[3] - m.PORCH[1])}", size=5.0, weight="bold", box=True)
    txt(ax, 28.3, m.PORCH[1] + 0.75, f"cantilevered floor trusses, no posts · {cover.lower()} · guard 36 in. (A-402)", size=4.0, box=True)
    setbacks(ax)

    # ---- notes strip at the left ----
    xl, yt = ax_in(ax, -11.5, 46.2)
    yb = room_table(bg, xl, yt)
    amps = m.PANEL_A_AMPS if A else m.PANEL_B_AMPS
    yb = block(bg, xl, yb - 0.16, "This flat's own equipment", [
        f"Electric meter and {amps} A panel (hall wall).",
        "Water meter and 1 in. service; 80 gal electric",
        "water heater in the garage-level utility room.",
        "2-ton heat pump on the west side yard, air",
        "handler in the AHU closet, ducted (M-10" + ("2" if A else "3") + ").",
        "Stacked washer / dryer, 27 x 31 in.",
        "30 in. range, refrigerator, dishwasher.",
        "All electric. Tenant pays own utilities.",
    ])
    block(bg, xl, yb, "Reading the dimensions", [
        "Three strings outside each wall: openings,",
        "rooms, then the overall wall length.",
        f"The rear wall is skewed {abs(m.REAR_ANGLE):.1f}° and the west",
        f"wall leans {math.degrees(WEST_LEAN):.1f}°; their strings are measured",
        "ALONG the wall, square to it.",
        "Short unlabelled spaces are wall thicknesses",
        "(see WALLS at the right).",
        "Inside lines read true where they are drawn.",
        "Rooms on the two angled walls are not",
        "square: the size under the room name is the",
        "clear rectangle that fits inside.",
        "Blue 5'-0\" = tub alcove, finished wall to",
        "finished wall, for a standard 60 x 30 tub.",
        "Red = wall face to lot line (2 in. inside",
        "each setback line).",
        "Circle = door tag, diamond = window tag:",
        "see A-601. Enlarged kitchen and baths: A-401.",
    ])
    save(fig, number, pdf)


def sheet_a102(pdf):
    unit_sheet(pdf, "A-102", "A")


def sheet_a103(pdf):
    unit_sheet(pdf, "A-103", "B")


SHEETS = [
    ("A-101", sheet_a101),
    ("A-102", sheet_a102),
    ("A-103", sheet_a103),
]
