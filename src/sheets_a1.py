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
    if h < 24:
        return f"{h // 2}" + (" 1/2" if h % 2 else "") + '"'
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
        need = max((len(lab) * size * 0.50 / 72) * fpi, 1.0) if min_len is None else min_len
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
    txt(ax, 42.5, rear_y(42.5) + 0.75, "REAR LOT LINE", size=5.0, color=ACCENT, rot=-math.degrees(T_R))
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
            f"Clear {ftin(m.OPEN_CLEAR_H)} under beam B1, {clr(m.CLG_GAR)} to ceiling.",
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
            f"Utility: heated, {fi(util_w)} x {fi(util_d)}: water",
            "service entry and shut-offs for both flats.",
            "No water heaters here (one in each flat).",
            "Its 2'-8\" door swings INTO the room.",
            f"Stair to Unit A: {lo['risers']} risers at {lo['riser_in']:.2f} in.,",
            f"{lo['tread_in']} in. treads, flights {fi(flight)} wide between",
            "the concrete walls, 1-hour enclosure (A-402).",
        ]),
        ("Outside", [
            "Bike hooks on the west wall at the back.",
            "Trash bay: 4 carts, screened, on the lot.",
        ]),
        ("To confirm", [
            "Wall, footing, beam sizes: engineer.",
            "Lot lines and setbacks: survey.",
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
        txt(ax, cx, (cy - 0.67 + m.Y_GR_I) / 2, f"C{i + 1}", size=4.2, color=RATED, z=9)

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
    txt(ax, (x0 + x1) / 2, y1 - 1.85, "MID LANDING", size=4.2, color=GREY)

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
    leader(ax, (16.5, m.B1_Y), (13.4, m.YF + 1.3), f"STEEL BEAM B1 OVER (S-104): {ftin(m.OPEN_CLEAR_H)} CLEAR UNDER IT", size=4.4, color=BLUE,
           ha="left", arrow=False)
    leader(ax, (m.COL_X[1] + 0.25, m.YF + 0.33), (29.6, m.YF + 1.3), "STEEL POST (S-104)", size=4.4, color=BLUE, arrow=False)
    leader(ax, (m.xw_gi(27.0), 27.0), (2.8, 30.6), "BIKE HOOKS ON THIS WALL,\nAT THE BACK", ha="right", **T)
    leader(ax, (m.xw_o(15.0) + 0.5, 15.0), (1.2, 16.6), f"{inch(m.CONC)} CONCRETE RETAINING\nWALL ON 3 SIDES (S-102)", ha="right", **T)
    leader(ax, (m.HP[1][0] - 0.4, m.HP[1][1]), (2.2, 25.4), "HEAT-PUMP PADS\nA AND B (M-101)", ha="right", **T)
    txt(ax, (m.CHASE_1[0] + m.CHASE_2[0]) / 2, 26.55, "C1, C2: DRAIN CHASES, 1-HOUR,\nINSULATED, 16 x 16 in. (P-101)", size=4.2, color=RATED, box=True)
    leader(ax, (m.XE, 27.0), (50.9, 27.0), f"UTILITY ROOM (heated)\n{fi(util_w)} x {fi(util_d)} clear\nDoor swings in.\nBoth water services\nenter here (P-101)", arrow=False, **T)
    leader(ax, (m.XE_GI - 0.6, m.UTIL[2] - m.CMU / 2), (50.9, 23.2), f"{inch(m.CMU)} CONCRETE OR\nGROUTED BLOCK:\nlobby wall and stair /\nutility wall (S-101)", **T)
    leader(ax, (m.XE, 15.5), (50.9, 15.5), f"COMMON STAIR\nflights {fi(flight)} wide\n{lo['risers']} risers to Unit A", arrow=False, **T)
    leader(ax, (m.XE - 1.0, 1.9), (46.4, 4.9), "TRASH BAY,\n4 CARTS,\nSCREENED\n(C-107)", **T)
    txt(ax, 40.9, 4.4, f"ENTRY LANDING\nEL {m.EL_GAR:.1f}, level", size=4.2)
    leader(ax, (14.5, m.YF - 0.6), (0.7, 12.9), "TRENCH DRAIN ACROSS\nTHE OPENING (C-105)", ha="right", color=BLUE, **T)
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
        nm = {"W/D": "Washer / dryer", "AIR HANDLER": "Mech. closet, AHU", "WATER HEATER": "Mech. closet, WH",
              "LIVING / KITCHEN": "Living / kitchen"}.get(k, k.title())
        rows.append((nm, room_size(k), f"{m.area(k):.0f} sf"))
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


def rear_windows(ax):
    """plans.unit_shell paints the rear wall over the white of its windows: put the white back."""
    for (t, w_, s0, s1, n) in m.WINDOWS:
        if w_ == "N":
            poly(ax, m.win_quad(w_, s0, s1), fc=PAPER, ec="none", z=5.6)


def unit_dims(ax, unit):
    """All dimension strings of a unit plan. Outside: openings / rooms / overall on each wall."""
    o1, o2, o3 = 1.8, 2.9, 4.0
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
    D(ax, (16.7, m.Y4), (16.7, m.yr_i(16.7)), 0, at=0.8, **I)                          # bedroom 2 depth
    D(ax, (m.X_B3, 28.3), (m.X_ST, 28.3), 0, **I)                              # bedroom 3 width
    D(ax, (30.4, m.Y2), (30.4, m.yr_i(30.4)), 0, at=0.36, **I)                 # bedroom 3 depth to the rear wall
    y = m.Y1 - 0.45
    D(ax, (m.X_H0, y), (m.X_ST, y), 0, side=-1, at=0.3, **I)                           # living / kitchen width
    D(ax, (30.6, m.YFI), (30.6, m.Y1), 0, at=0.62, **I)                        # living / kitchen depth
    D(ax, (m.KIT_BASE[2], 14.4), (m.ISLAND[0], 14.4), 0, ext=False, size=4.2)  # kitchen aisle
    yh = (m.Y1 + m.Y2) / 2
    D(ax, (m.X_H0, yh), (m.X_H1, yh), 0, at=0.3, ext=False, size=4.2)          # hall width, at the cased opening
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
    txt(ax, 21.42, 23.6, "HALL", size=4.2, color=GREY, rot=90)
    txt(ax, 10.45, 23.35, f"CL. {fi(m.CL_Y - m.Y2)} deep", size=4.2, color=GREY)
    txt(ax, 10.6, 24.75, f"CL. {fi(m.Y3 - m.CL_Y - m.PART)} deep", size=4.2, color=GREY)
    txt(ax, 28.05, 32.3, f"CLOSET\n{fi(m.C3_X - m.X_B3)} wide", size=4.2, color=GREY)
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
    rear_windows(ax)
    if A:
        yl = m.Y_GR_O
        line(ax, [(m.xw_o(yl) - 1.0, yl), (m.XE + 0.8, yl)], color=BLUE, lw=0.8, ls=(0, (6, 2.5)), z=7.6)
        txt(ax, 13.2, yl + 0.42, "SLAB ON GRADE THIS SIDE (S-103)", size=4.2, color=BLUE, box=True)
        txt(ax, 13.2, yl - 0.45, "FLOOR TRUSSES THIS SIDE (S-201)", size=4.2, color=BLUE, box=True)
        txt(ax, 33.4, yl + 0.42, "SLAB ON GRADE", size=4.2, color=BLUE, box=True)
        txt(ax, 33.4, yl - 0.45, "FLOOR TRUSSES", size=4.2, color=BLUE, box=True)
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
        txt(ax, hx + 11 * IN, 26.0, "ATTIC ACCESS\n22 x 30 in.", size=4.2, color=BLUE, rot=90, z=9.5)
    unit_dims(ax, unit)
    unit_names(ax, unit)
    cover = "ROOF OVERHANG ABOVE" if not A else "UNIT B PORCH ABOVE"
    txt(ax, 28.3, m.PORCH[1] + 1.55, f"COVERED PORCH  {fi(m.PORCH[2] - m.PORCH[0])} x {fi(m.PORCH[3] - m.PORCH[1])}", size=5.0, weight="bold", box=True)
    txt(ax, 28.3, m.PORCH[1] + 0.75, f"cantilevered floor trusses, no posts · {cover.lower()} · guard 36 in. (A-402)", size=4.2, box=True)
    setbacks(ax)

    # ---- notes strip at the left ----
    xl, yt = ax_in(ax, -11.5, 46.2)
    yb = room_table(bg, xl, yt)
    amps = m.PANEL_A_AMPS if A else m.PANEL_B_AMPS
    yb = block(bg, xl, yb - 0.16, "This flat's own equipment", [
        f"Electric meter and {amps} A panel (hall wall).",
        "Water meter and 1 in. service (shut-off in the",
        "garage-level utility room).",
        f"Mechanical closet off the hall, {fi(m.HALL_Y1 - m.AH_Y0)} x {fi(m.X_C1 - m.X_C0)},",
        "pair of 2'-0\" doors D12 + D13: air handler and",
        "80 gal electric water heater on a 26 in. pan.",
        "2-ton heat pump on the west side yard,",
        "ducted air handler (M-10" + ("2" if A else "3") + ").",
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


# ----------------------------------------------------------------------------
# A-104  Furniture and clearance plan
# ----------------------------------------------------------------------------
FURN_NAME = {"bed": "QUEEN BED", "desk": "DESK", "dresser": "DRESSER", "sofa": "SOFA", "tv": "TV STAND"}


def furn_size(kind, pts):
    """Real size of a furniture polygon in inches, as (text, angle of its long side)."""
    a, b = math.dist(pts[0], pts[1]), math.dist(pts[1], pts[2])
    long_edge = (pts[0], pts[1]) if a >= b else (pts[1], pts[2])
    ang = math.degrees(math.atan2(long_edge[1][1] - long_edge[0][1], long_edge[1][0] - long_edge[0][0]))
    if ang > 90.01 or ang <= -89.99:
        ang += 180
    lo, hi = sorted((round(a * 12), round(b * 12)))
    return (f"{lo} x {hi}" if kind == "bed" else f"{hi} x {lo}"), ang


def bed_zones(room, pts):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    if m.BED_HEAD[room] == "W":
        return [((x0, y0 - 2.0, x1, y0), "y"), ((x0, y1, x1, y1 + 2.0), "y"), ((x1, y0, x1 + 2.0, y1), "x")]
    return [((x0 - 2.0, y0, x0, y1), "x"), ((x1, y0, x1 + 2.0, y1), "x"), ((x0, y1, x1, y1 + 2.0), "y")]


def clearance_overlays(ax, wc_dims=True, size=4.2):
    """Door swings, bed bands and toilet clearances drawn from the same shapes model.check() tests."""
    for d in m.DOORS:
        poly(ax, list(m.door_sector(d).exterior.coords)[:-1], fc=SWING, ec="none", z=4.4, alpha=0.9)
    for (room, kind, pts) in m.FURN:
        if kind != "bed":
            continue
        for (x0, y0, x1, y1), axis in bed_zones(room, pts):
            rect(ax, x0, y0, x1, y1, fc=BAND, ec=BLUE, lw=0.3, z=4.3, alpha=0.85)
            if axis == "y":
                D(ax, ((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1), 0, fi(y1 - y0), ext=False, size=size, color=BLUE)
            else:
                D(ax, (x0, (y0 + y1) / 2), (x1, (y0 + y1) / 2), 0, fi(x1 - x0), ext=False, size=size, color=BLUE)
    for (cx, cy, f) in m.WCS:
        yf = cy - m.WC_D
        rect(ax, cx - m.WC_W / 2, yf - 1.75, cx + m.WC_W / 2, cy, fc="none", ec=BLUE, lw=0.5, ls=(0, (3, 2)), z=7.2)
        if wc_dims:
            chain(ax, [(cx - 1.25, yf - 1.75), (cx, yf - 1.75), (cx + 1.25, yf - 1.75)], 0.0, size=size, color=BLUE, ends=False,
                  labels=[inch(1.25), inch(1.25)])
            D(ax, (cx - 1.25, yf - 1.75), (cx - 1.25, yf), 0, inch(1.75), ext=False, size=size, color=BLUE, side=-1)


def sheet_a104(pdf):
    notes = [
        ("What this sheet proves", [
            "Every piece is drawn at its real size and",
            "sits where the model puts it. The model",
            "then tests each piece against the walls,",
            "the other pieces and every door swing.",
            "Furniture is by the tenant: the plan only",
            "shows that standard pieces fit.",
        ]),
        ("Rules held (model.check)", [
            "Queen bed in every bedroom with 24 in.",
            "clear on both sides and at the foot.",
            "No furniture, fixture or cabinet inside a",
            "door swing (orange). Bifolds: half a leaf.",
            "Toilet: 15 in. from centre to each side,",
            "21 in. clear in front (IRC R307).",
            f"Kitchen aisle {fi(m.ISLAND[0] - m.KIT_BASE[2])} (42 in. min.); path north",
            f"of the island {fi(m.Y1 - m.ISLAND_TOP[3])} (30 in. min.).",
            "Bedrooms: 100 sf and 8'-6\" x 10'-0\" clear",
            "rectangle or better (code: 70 sf, 7 ft).",
        ]),
        ("For the trim carpenter", [
            "Hang doors on the hinge side shown.",
            "Do not move a door or reverse a swing",
            "without checking it against this sheet.",
            "Closets are framed rooms with bifold",
            "doors; shelf and rod by owner (A-601).",
        ]),
    ]
    fig, bg = new_sheet("A-104", "Furniture and clearance plan", "3/16\" = 1'-0\"", notes)
    fpi = plans.FPI
    xlim, ylim = (4.6, 46.6), (8.4, 42.0)
    left, bottom = 0.62, 3.5
    ax = plan_axes(fig, left, bottom, xlim, ylim, fpi)
    top = bottom + (ylim[1] - ylim[0]) / fpi
    bg.text(left, 10.36, "FURNITURE AND CLEARANCE PLAN", fontsize=9, fontweight="bold", color=INK, va="center")
    bg.text(left, 10.14, "Unit A shown; Unit B is the same · 3/16\" = 1'-0\" · every size below is a real catalogue size",
            fontsize=6.2, color=GREY, va="center")
    st = unit_plan(ax, "arch", "A", furniture=True, labels=False)
    rear_windows(ax)
    clearance_overlays(ax)
    # furniture, labelled with its real size
    for (room, kind, pts) in m.FURN:
        s, ang = furn_size(kind, pts)
        cx, cy = sum(p[0] for p in pts) / 4, sum(p[1] for p in pts) / 4
        if kind == "bed":
            dx = 0.6 if m.BED_HEAD[room] == "W" else 0.0
            dy = 0.0 if m.BED_HEAD[room] == "W" else 0.55
            txt(ax, cx + dx, cy + dy + 0.55, room, size=5.0, weight="bold")
            txt(ax, cx + dx, cy + dy - 0.45, f"QUEEN BED\n{s} in.", size=4.4)
        elif kind == "sofa":
            txt(ax, cx, cy - 0.35, f"SOFA {s} in.", size=4.4)
        else:
            txt(ax, cx, cy, f"{FURN_NAME[kind]}\n{s}", size=4.2, rot=ang, z=9.6)
    for room, c in m.CHAIRS.items():
        poly(ax, c, fc="none", ec=GREY, lw=0.4, ls=(0, (2, 2)), z=6.5)
    txt(ax, m.STOOLS[1][0] + 1.25, m.STOOLS[1][1], f"{len(m.STOOLS)} STOOLS", size=4.2, rot=90)
    txt(ax, 34.4, 16.0, "LIVING / KITCHEN", size=5.0, weight="bold")
    txt(ax, 23.7, 11.75, "KITCHEN", size=4.4, weight="bold")
    txt(ax, (m.SHAFT_U[0] + m.SHAFT_U[1]) / 2, 12.2, "COMMON\nSTAIR", size=4.4, color=GREY)
    txt(ax, m.ISLAND[2] + 0.5, (m.ISLAND[1] + m.ISLAND[3]) / 2, f"ISLAND {round((m.ISLAND_TOP[3] - m.ISLAND_TOP[1]) * 12)} x {round((m.ISLAND_TOP[2] - m.ISLAND_TOP[0]) * 12)} TOP", size=4.2, color=GREY, rot=90, z=9)
    txt(ax, *m.WH_UNIT, "WH", size=4.2, z=8, weight="bold")
    txt(ax, (m.FRIDGE[0] + m.FRIDGE[2]) / 2, (m.FRIDGE[1] + m.FRIDGE[3]) / 2, "REF\n36 in.", size=4.2, color=GREY, z=8)
    txt(ax, (m.WD[0] + m.WD[2]) / 2, (m.WD[1] + m.WD[3]) / 2, "W/D", size=4.2, color=GREY, z=8)
    txt(ax, (m.AHU[0] + m.AHU[2]) / 2, (m.AHU[1] + m.AHU[3]) / 2, "AHU", size=4.2, z=8, weight="bold")
    for i, (x0, y0, x1, y1) in enumerate(m.TUBS):
        txt(ax, (x0 + x1) / 2, (y0 + y1) / 2, f"BATH {i + 1} · TUB 60 x 30", size=4.2, rot=90)
    # kitchen and living clearances
    K = dict(ext=False, size=4.2, color=BLUE)
    D(ax, (m.KIT_BASE[2], 14.3), (m.ISLAND[0], 14.3), 0, **K)
    D(ax, (m.FRIDGE[2], 17.3), (m.ISLAND[0], 17.3), 0, **K)
    D(ax, (27.0, m.ISLAND_TOP[3]), (27.0, m.Y1), 0, **K)
    D(ax, (27.9, m.YFI), (27.9, m.ISLAND[1]), 0, **K)
    tv = [p for (r, k, p) in m.FURN if k == "tv"][0]
    sofa = [p for (r, k, p) in m.FURN if k == "sofa"][0]
    D(ax, (32.9, max(p[1] for p in tv)), (32.9, min(p[1] for p in sofa)), 0, **K)
    D(ax, (m.X_H0, 22.6), (m.X_H1, 22.6), 0, fi(m.X_H1 - m.X_H0), ext=False, size=4.2, color=BLUE)
    sb = plan_axes(fig, 9.0, 0.5, (0.0, 20.0), (0.0, 2.0), fpi)
    scale_bar(sb, 1.0, 1.1, 16, 4, 0.42, size=5.2)
    north_arrow(ax, xlim[1] - 3.2, ylim[1] - 3.6, 1.6, 6.0)

    # ---- right column: standard sizes ----
    xr = left + (xlim[1] - xlim[0]) / fpi + 0.35
    bg.text(xr, 10.36, "STANDARD SIZES USED (model.SIZES)", fontsize=7.0, fontweight="bold", color=INK, va="center")
    rows = [("ITEM", "SIZE DRAWN")] + [(k, v) for k, v in m.SIZES.items()]
    wrapped = []
    for k, v in rows:
        if len(v) > 58:
            cut = v.rfind(", ", 0, 58)
            cut = cut + 1 if cut > 0 else v.rfind(" ", 0, 58)
            v = v[:cut].rstrip() + "\n" + v[cut:].strip()
        wrapped.append((k, v))
    y = 10.2
    W = [0.82, 13.62 - xr - 0.82]
    for r, (k, v) in enumerate(wrapped):
        rh = 0.165 * (v.count("\n") + 1) + 0.035
        if r == 0:
            bg.add_patch(Rectangle((xr, y - rh), sum(W), rh, fc="#e3e6ea", ec="none"))
        elif r % 2 == 0:
            bg.add_patch(Rectangle((xr, y - rh), sum(W), rh, fc="#f6f7f8", ec="none"))
        bg.text(xr + 0.05, y - rh / 2, k, fontsize=5.4, va="center", color=INK, fontweight="bold" if r == 0 else "normal")
        bg.text(xr + W[0] + 0.05, y - rh / 2, v, fontsize=5.4, va="center", color=INK, fontweight="bold" if r == 0 else "normal", linespacing=1.2)
        bg.plot([xr, xr + sum(W)], [y - rh, y - rh], color=LIGHT, lw=0.4)
        y -= rh
    bg.add_patch(Rectangle((xr, y), sum(W), 10.2 - y, fill=False, ec=INK, lw=0.6))
    # legend
    y -= 0.3
    bg.text(xr, y, "LEGEND", fontsize=7.0, fontweight="bold", color=INK, va="center")
    items = [
        (dict(fc=SWING, ec="none"), "Floor swept by a door (must stay empty)"),
        (dict(fc=BAND, ec=BLUE, lw=0.4), "24 in. clear band beside and at the foot of a bed"),
        (dict(fc="none", ec=BLUE, lw=0.6, ls=(0, (3, 2))), "Toilet clearance: 30 in. wide, 21 in. in front of the bowl"),
        (dict(fc="none", ec=GREY, lw=0.5, ls=(0, (2, 2))), "Desk chair pulled out (may overlap a bed band)"),
        (dict(fc="#f2f3f5", ec=plans.FURN, lw=0.5), "Furniture at real size (inches)"),
    ]
    for kw, s in items:
        y -= 0.21
        bg.add_patch(Rectangle((xr, y - 0.065), 0.3, 0.13, **kw))
        bg.text(xr + 0.4, y, s, fontsize=5.6, va="center", color=INK)
    y -= 0.2
    block(bg, xr, y - 0.1, "The build checks this sheet", [
        "model.check() runs before any sheet is drawn and",
        "stops the build if any item overlaps another item,",
        "a door swing or a wall, if a bed loses its 24 in.",
        "bands, if a toilet loses its clearance, or if the",
        "kitchen aisle drops under 42 in. Nothing on this",
        "plan is placed by eye.",
    ], fs=5.8, lh=0.145)

    # ---- under the plan: every piece, its size and what is left around it ----
    rows = [("ROOM", "PIECE", "SIZE (in.)", "ROOM", "PIECE", "SIZE (in.)")]
    flat = []
    for (room, kind, pts) in m.FURN:
        flat.append((room.title().replace(" / K", " / k"), FURN_NAME[kind].capitalize().replace("Tv", "TV"), furn_size(kind, pts)[0]))
    for room, c in m.CHAIRS.items():
        a, b = math.dist(c[0], c[1]), math.dist(c[1], c[2])
        flat.append((room.title(), "Desk chair space", f"{round(a * 12)} x {round(b * 12)}"))
    flat.append(("Living / kitchen", f"{len(m.STOOLS)} stools at the island", f"{inch(m.STOOLS[1][1] - m.STOOLS[0][1])} centre to centre"))
    half = (len(flat) + 1) // 2
    for i in range(half):
        r2 = flat[i + half] if i + half < len(flat) else ("", "", "")
        rows.append(flat[i] + r2)
    bg.text(left, 3.17, "FURNITURE SHOWN (model.FURN, CHAIRS, STOOLS)", fontsize=7.0, fontweight="bold", color=INK, va="center")
    table(bg, left, 3.05, [1.05, 1.25, 1.2, 1.05, 1.25, 1.2], rows, fs=5.4, rh=0.165)
    save(fig, "A-104", pdf)


# ----------------------------------------------------------------------------
# A-105  Roof plan
# ----------------------------------------------------------------------------
OH_REAR, OH_RAKE, OH_FRONT = 1.0, 8 * IN, 4.0          # overhangs, square to each wall
ICE_IN = 2.0                                           # ice barrier: 24 in. inside the wall line


def roof_geometry():
    yf = m.YF - OH_FRONT
    xe = m.XE + OH_RAKE
    xwr = lambda y: m.xw_o(y) - OH_RAKE / math.cos(WEST_LEAN)        # west rake edge
    yre = lambda x: m.yr_o(x) + OH_REAR / math.cos(T_R)              # rear eave edge
    y = 40.0
    for _ in range(60):
        y = yre(xwr(y))
    nw = (xwr(y), y)
    x = 9.0
    for _ in range(60):
        x = xwr(m.ridge_y(x))
    ridge_w = (x, m.ridge_y(x))
    ridge_e = (xe, m.ridge_y(xe))
    out = [(xwr(yf), yf), (xe, yf), (xe, yre(xe)), nw]
    return dict(out=out, ridge=(ridge_w, ridge_e), xwr=xwr, yre=yre, yf=yf, xe=xe)


def sheet_a105(pdf):
    g = roof_geometry()
    out, (rw, re_) = g["out"], g["ridge"]
    sw, se, ne, nw = out
    p = m.ROOF_PITCH
    f_front = math.sqrt(1 + p * p)
    g_rear = p * math.sqrt(1 + REAR_SLOPE ** 2)                       # true fall of the rear plane, square to its eave
    f_rear = math.sqrt(1 + g_rear ** 2)
    a_front = poly_area([sw, se, re_, rw]) * f_front
    a_rear = poly_area([rw, re_, ne, nw]) * f_rear
    squares = (a_front + a_rear) / 100
    x_hi = m.OUT_U[3][0] + 0.5                                         # station of m.EL_RIDGE_HI
    side_gap = perp_to_west(*m.OUT_U[0]) - OH_RAKE
    notes = [
        ("Roof", [
            "Common trusses run north-south at 24 in.,",
            f"4:12, {inch(m.HEEL)} raised heel (S-203).",
            f"Top of wall plate EL {m.EL_PLATE:.2f}.",
            "The front and rear walls are not parallel,",
            "so spans grow to the west and the ridge",
            f"climbs from EL {m.EL_RIDGE_LO:.1f} to EL {m.EL_RIDGE_HI:.2f}.",
            "Both eaves stay level.",
        ]),
        ("Roofing", [
            "Architectural asphalt shingles over",
            "synthetic underlayment.",
            "Ice barrier (self-adhered) from each eave",
            "edge to 24 in. inside the wall line.",
            "Metal drip edge on eaves and rakes.",
            "Pipe flashing at the 3 vents (VTR 1-3,",
            "above the plumbing stacks, P-201).",
            "Step flashing: none (no wall above roof).",
            f"About {squares:.1f} squares on the slope + waste.",
        ]),
        ("Venting and fire rating", [
            "Attic vents: ridge vent full length and",
            "the front soffit only.",
            "Rear eave and both side rakes are within",
            "5 ft of a lot line: SOLID soffit, no vents,",
            "1-hour underside (IRC Table R302.1(1)).",
        ]),
        ("Gutters", [
            "Gutter on the front and rear eaves, a",
            "downspout at each of the 4 corners, piped",
            "to the site drains (C-105). Sizes prelim.",
        ]),
    ]
    fig, bg = new_sheet("A-105", "Roof plan", "3/16\" = 1'-0\"", notes)
    ax = plan_frame(fig, "Roof plan", f"4:12 asphalt shingles · plate EL {m.EL_PLATE:.2f} · ridge EL {m.EL_RIDGE_LO:.1f} to {m.EL_RIDGE_HI:.2f}",
                    view=VIEW_A, bottom=0.5)
    lot_labels(ax)
    poly(ax, out, fc="#eceff2", ec=INK, lw=1.0, z=3)
    # trusses at 24 in. from the east end wall
    x = m.XE - 2.0
    while x > sw[0] + 0.05:
        y1 = g["yre"](x) if x >= nw[0] else (x - g["xwr"](0.0)) / math.tan(WEST_LEAN)
        line(ax, [(x, g["yf"]), (x, y1)], color="#c4c9cf", lw=0.3, z=3.2)
        x -= 2.0
    line(ax, m.OUT_U + [m.OUT_U[0]], color=GREY, lw=0.6, ls=(0, (5, 3)), z=4)
    # ice barrier limits
    yi_f = m.YFI + ICE_IN
    line(ax, [(g["xwr"](yi_f) + 0.1, yi_f), (g["xe"] - 0.1, yi_f)], color=BLUE, lw=0.6, ls=(0, (2, 2)), z=5)
    a = (m.OUT_U[3][0] + 1.6, m.yr_i(m.OUT_U[3][0] + 1.6) - ICE_IN / math.cos(T_R))
    b = (g["xe"] - 0.1, m.yr_i(g["xe"] - 0.1) - ICE_IN / math.cos(T_R))
    line(ax, [a, b], color=BLUE, lw=0.6, ls=(0, (2, 2)), z=5)
    # ridge, gutters, downspouts
    line(ax, [rw, re_], color=INK, lw=2.2, z=6)
    line(ax, [rw, re_], color=PAPER, lw=0.5, ls=(0, (4, 3)), z=6.1)
    off = 0.22
    line(ax, [(sw[0], sw[1] - off), (se[0], se[1] - off)], color=BLUE, lw=1.6, z=6)
    line(ax, [(nw[0] + N_R[0] * off, nw[1] + N_R[1] * off), (ne[0] + N_R[0] * off, ne[1] + N_R[1] * off)], color=BLUE, lw=1.6, z=6)
    ds = [(sw[0] + 0.5, sw[1] - off), (se[0] - 0.5, se[1] - off), (ne[0] - 0.5, ne[1] + 0.4), (nw[0] + 0.75, nw[1] + 0.05)]
    for (dx, dy) in ds:
        ax.add_patch(plt.Circle((dx, dy), 0.38, fc=PAPER, ec=BLUE, lw=0.9, zorder=7))
        txt(ax, dx, dy, "DS", size=4.2, color=BLUE, z=9, weight="bold")
    # plumbing vents and attic access
    for i, (vx, vy) in enumerate((m.STACK_1, m.STACK_2, m.STACK_3)):
        ax.add_patch(plt.Circle((vx, vy), 0.3, fc=PAPER, ec=INK, lw=0.8, zorder=7))
        ax.add_patch(plt.Circle((vx, vy), 0.1, fc=INK, ec=INK, lw=0.4, zorder=7.1))
        txt(ax, vx + 0.5, vy - 0.1, f"VTR {i + 1}", size=4.6, weight="bold", ha="left")
    hx = m.X_H0 + (m.X_H1 - m.X_H0 - 22 * IN) / 2
    rect(ax, hx, 24.75, hx + 22 * IN, 24.75 + 30 * IN, fc="none", ec=GREY, lw=0.6, ls=(0, (3, 2)), z=6)
    leader(ax, (hx + 22 * IN, 25.4), (24.8, 20.6), "ATTIC ACCESS 22 x 30 in.\nin Unit B's hall ceiling (below)", size=4.4, color=GREY, va="top", ha="left")
    # slope arrows
    arrow = dict(arrowstyle="-|>", lw=0.9, color=INK, mutation_scale=9)
    for xa in (16.5, 37.0):
        yr = m.ridge_y(xa)
        ax.annotate("", xy=(xa, yr - 6.3), xytext=(xa, yr - 2.6), arrowprops=arrow, zorder=8)
        txt(ax, xa + 0.3, yr - 4.4, "4:12\nDOWN", size=5.0, weight="bold", ha="left")
    for xa, d0, d1 in ((14.0, 2.6, 6.3), (37.0, 2.0, 5.2)):
        yr = m.ridge_y(xa)
        ax.annotate("", xy=(xa, yr + d1), xytext=(xa, yr + d0), arrowprops=arrow, zorder=8)
        txt(ax, xa + 0.3, yr + (d0 + d1) / 2, "4:12\nDOWN", size=5.0, weight="bold", ha="left")
    txt(ax, 27.0, m.ridge_y(27.0) + 5.3, f"along the trusses; {g_rear * 12:.1f}:12 square to the rear eave", size=4.2, color=GREY,
        rot=-math.degrees(T_R))
    txt(ax, 25.0, 15.0, "ROOF TRUSSES AT 24 in. O.C., SPAN NORTH-SOUTH (grey lines; layout S-203)", size=4.4, color=GREY, box=True)
    # ridge elevations
    ang = math.degrees(math.atan2(re_[1] - rw[1], re_[0] - rw[0]))
    txt(ax, 27.0, m.ridge_y(27.0) + 0.75, "RIDGE, WITH CONTINUOUS RIDGE VENT", size=5.0, weight="bold", rot=ang)
    for xs, el, lab, pos, ha in ((m.XE, m.EL_RIDGE_LO, "RIDGE LOW END\nat the east wall", (51.0, 22.2), "left"),
                                 (x_hi, m.EL_RIDGE_HI, "RIDGE HIGH END\n(over the NW corner)", (11.5, 21.3), "left")):
        ax.add_patch(plt.Circle((xs, m.ridge_y(xs)), 0.3, fc=ACCENT, ec=ACCENT, zorder=8))
        leader(ax, (xs, m.ridge_y(xs)), pos, f"EL {el:.2f}\n{lab}", size=4.8, color=ACCENT, ha=ha, weight="bold")

    # ---- dimensions ----
    S = dict(size=4.8)
    D(ax, sw, se, -1.4, fi(math.dist(sw, se)) + " FRONT EAVE", **S)
    D(ax, se, ne, -3.0, fi(math.dist(se, ne)) + " EAST RAKE", **S)
    D(ax, nw, ne, 1.5, fi(math.dist(nw, ne)) + " REAR EAVE, ALONG THE EAVE", **S)
    D(ax, sw, nw, 1.5, fi(math.dist(sw, nw)) + " WEST RAKE, ALONG THE RAKE", **S)
    # overhangs
    D(ax, (41.0, g["yf"]), (41.0, m.YF), 0, fi(OH_FRONT) + " OVERHANG", ext=False, size=4.4, at=0.5)
    D(ax, (m.XE, 14.0), (g["xe"], 14.0), 0, inch(OH_RAKE), ext=False, size=4.4, at=2.6)
    c = (31.0, m.yr_o(31.0))
    D(ax, c, (c[0] + N_R[0] * OH_REAR, c[1] + N_R[1] * OH_REAR), 0, inch(OH_REAR), ext=False, size=4.4, at=2.4)
    c = (m.xw_o(16.0), 16.0)
    D(ax, (c[0] + N_W[0] * OH_RAKE, c[1] + N_W[1] * OH_RAKE), c, 0, inch(OH_RAKE), ext=False, size=4.4, at=-1.8)
    # ridge position and truss span at each end
    for xs, dxl in ((m.XE - 1.6, 0), (x_hi, 0)):
        yr, yb = m.ridge_y(xs), m.yr_o(xs)
        chain(ax, [(xs, m.YF), (xs, yr), (xs, yb)], 0.0, size=4.4, ends=False, labels=[fi(yr - m.YF), fi(yb - yr)])
    txt(ax, m.XE - 4.1, 13.9, f"TRUSS SPAN\n{fi(m.yr_o(m.XE - 1.6) - m.YF)}\nhere", size=4.4, weight="bold")
    txt(ax, x_hi + 2.6, 13.9, f"TRUSS SPAN\n{fi(m.yr_o(x_hi) - m.YF)}\nhere", size=4.4, weight="bold")
    # ice barrier widths
    D(ax, (33.5, g["yf"]), (33.5, yi_f), 0, fi(yi_f - g["yf"]) + " ICE BARRIER", ext=False, size=4.4, color=BLUE)
    c = (25.5, m.yr_i(25.5) - ICE_IN / math.cos(T_R))
    wr = OH_REAR + m.EXT + ICE_IN
    D(ax, c, (c[0] + N_R[0] * wr, c[1] + N_R[1] * wr), 0, fi(wr), ext=False, size=4.4, color=BLUE, side=-1)
    txt(ax, 32.0, m.yr_i(32.0) - ICE_IN / math.cos(T_R) - 0.45, "ICE BARRIER TO THIS LINE (24 in. inside the wall)", size=4.2, color=BLUE,
        rot=-math.degrees(T_R))
    # notes with leaders
    T = dict(size=4.5)
    leader(ax, (30.0, g["yf"] - off), (30.0, 2.6), "GUTTER, FRONT EAVE · FRONT SOFFIT VENTED (continuous strip vent)", color=BLUE, ha="center", va="top", **T)
    leader(ax, (36.0 + N_R[0] * 0.3, g["yre"](36.0) + N_R[1] * 0.3), (39.5, 39.6),
           "GUTTER, REAR EAVE · REAR SOFFIT SOLID, NO VENTS,\n1-HOUR UNDERSIDE (within 5 ft of the lot line)", color=BLUE, ha="left", **T)
    leader(ax, (ds[0][0] + 0.2, ds[0][1] - 0.35), (8.0, 2.4), "DOWNSPOUT AT EACH CORNER (4),\nTO THE SITE DRAINS (C-105)", color=BLUE, **T)
    leader(ax, (m.XE - 0.2, 26.0), (51.0, 27.2), "WALL LINE BELOW\n(dashed)", color=GREY, **T)
    leader(ax, (g["xe"], 12.5), (51.0, 12.5), f"RAKE, {inch(OH_RAKE)} OVERHANG,\n1-HOUR UNDERSIDE,\nno vents, {fi(side_gap)} from\nthe side lot line", arrow=False, **T)
    leader(ax, (m.xw_o(33.0) - OH_RAKE, 33.0), (2.6, 36.2), f"WEST RAKE, {inch(OH_RAKE)} OVERHANG,\n1-HOUR UNDERSIDE, no vents", ha="right", **T)
    txt(ax, 25.0, 8.2, "FRONT OVERHANG COVERS UNIT B'S PORCH", size=4.6, weight="bold", box=True)
    # roof edge to lot line (fire separation of the overhangs), in red
    R = dict(color=ACCENT, size=4.8)
    D(ax, (47.3, 0.0), (47.3, g["yf"]), 0, fi(g["yf"]), ext=False, **R)
    line(ax, [(se[0] + 0.3, se[1]), (47.8, se[1])], color=ACCENT, lw=0.25, z=8)
    D(ax, ne, (50.0, ne[1]), 1.3, fi(50.0 - ne[0]), **R)
    foot = (sw[0] + N_W[0] * perp_to_west(*sw), sw[1] + N_W[1] * perp_to_west(*sw))
    D(ax, foot, sw, -1.2, fi(perp_to_west(*sw)), side=-1, **R)
    c = (17.0, g["yre"](17.0))
    d = perp_to_rear(*c)
    D(ax, c, (c[0] + N_R[0] * d, c[1] + N_R[1] * d), 0, fi(d) + " EAVE TO LOT LINE", ext=False, at=1.9, **R)

    # ---- strip at the left: slope and area table ----
    xl, yt = ax_in(ax, -11.5, 46.2)
    rows = [("ROOF PLANE", "PLAN AREA", "ON SLOPE"),
            ("Front (4:12)", f"{poly_area([sw, se, re_, rw]):,.0f} sf", f"{a_front:,.0f} sf"),
            (f"Rear ({g_rear * 12:.1f}:12 true)", f"{poly_area([rw, re_, ne, nw]):,.0f} sf", f"{a_rear:,.0f} sf"),
            ("Total", f"{poly_area(out):,.0f} sf", f"{a_front + a_rear:,.0f} sf")]
    yb = table(bg, xl, yt, [0.92, 0.6, 0.6], rows, fs=5.0, rh=0.152)
    yb = block(bg, xl, yb - 0.16, "Key heights", [
        f"Top of wall plate          EL {m.EL_PLATE:.2f}",
        f"Ridge, east wall           EL {m.EL_RIDGE_LO:.2f}",
        f"Ridge, north-west corner   EL {m.EL_RIDGE_HI:.2f}",
        f"Ridge rises {inch(m.EL_RIDGE_HI - m.EL_RIDGE_LO)} over its length.",
        f"Unit B floor               EL {m.EL_B:.1f}",
    ])
    block(bg, xl, yb, "For the roofer", [
        "1. Both eaves are level; only the ridge",
        "   climbs. Shingle courses run parallel to",
        "   each eave, so front and rear courses do",
        "   not meet square at the ridge: cut to the",
        "   ridge line and cap.",
        "2. The rear plane is slightly steeper than",
        "   4:12 measured square to its eave. Both",
        "   planes are above the 4:12 minimum for",
        "   standard shingle application.",
        "3. Ice barrier strip is wider at the front",
        "   because of the 4'-0\" overhang.",
        "4. The west rake leans with the lot line:",
        "   rake trim follows the wall, not the",
        "   trusses (S-203).",
        "5. Rear eave and side rakes are within 5 ft",
        "   of the lot lines: no vents in them and a",
        "   1-hour underside (5/8 in. Type X or as",
        "   detailed on A-501).",
        "6. No roof-mounted equipment. Nothing but",
        "   the 3 plumbing vents and the ridge vent",
        "   penetrates the roof.",
        "7. Truss layout, bracing, sheathing and",
        "   nailing: S-203. This sheet is the",
        "   roofer's sheet.",
    ])
    save(fig, "A-105", pdf)


# ----------------------------------------------------------------------------
# A-401  Kitchen and bath enlarged plans (1/2 in. = 1 ft)
# ----------------------------------------------------------------------------
BLOCK = "#d9730d"
FPI_E = 2.0


def enlarged(fig, bg, left, bottom, xlim, ylim, title, sub):
    ax = plan_axes(fig, left, bottom, xlim, ylim, FPI_E)
    st = plans.Style("arch")
    unit_shell(ax, st, "A")
    unit_fixtures(ax, st, labels=False)
    rear_windows(ax)
    crop_texts(ax)
    w, h = (xlim[1] - xlim[0]) / FPI_E, (ylim[1] - ylim[0]) / FPI_E
    bg.add_patch(Rectangle((left, bottom), w, h, fill=False, ec=LIGHT, lw=0.6))
    bg.text(left, bottom + h + 0.19, title.upper(), fontsize=8.5, fontweight="bold", color=INK, va="center")
    bg.text(left, bottom + h + 0.06, sub, fontsize=5.6, color=GREY, va="center")
    return ax


def blocking(ax, a, b, off=0.1):
    """Grab-bar blocking inside a wall: orange dashes just behind the finished face a -> b."""
    (x0, y0), (x1, y1) = a, b
    L = math.hypot(x1 - x0, y1 - y0)
    nx, ny = -(y1 - y0) / L * off, (x1 - x0) / L * off
    line(ax, [(x0 + nx, y0 + ny), (x1 + nx, y1 + ny)], color=BLOCK, lw=2.0, ls=(0, (2.2, 1.2)), z=7.8)


def bath_view(fig, bg, i, left, bottom, xlim, ylim):
    name = f"BATH {i + 1}"
    tub, (cx, cy, _), lav = m.TUBS[i], m.WCS[i], m.LAVS[i]
    door = [d for d in m.DOORS if d["tag"] == ("D5", "D6", "D7")[i]][0]
    xs, ys = [p[0] for p in m.ROOMS[name]], [p[1] for p in m.ROOMS[name]]
    bx0, bx1, by0 = min(xs), max(xs), min(ys)
    by1 = tub[3]
    off_room = ("bedroom 1", "bedroom 2", "bedroom 3")[i]
    ax = enlarged(fig, bg, left, bottom, xlim, ylim, f"{name} (opens off {off_room})",
                  f"1/2\" = 1'-0\" · {fi(bx1 - bx0)} x {fi(by1 - by0)} clear · {m.area(name):.0f} sf")
    poly(ax, list(m.door_sector(door).exterior.coords)[:-1], fc=SWING, ec="none", z=4.4, alpha=0.9)
    yf = cy - m.WC_D
    S = dict(size=5.0, min_len=0.12)
    # toilet centre line and its clearance box
    line(ax, [(cx, cy + 0.25), (cx, yf - 2.0)], color=BLUE, lw=0.5, ls=(0, (8, 2, 2, 2)), z=7.5)
    rect(ax, cx - m.WC_W / 2, yf - 1.75, cx + m.WC_W / 2, cy, fc="none", ec=BLUE, lw=0.6, ls=(0, (3, 2)), z=7.4)
    # string 1: fixtures along the toilet wall
    if i == 1:
        y = yf - 0.55
        chain(ax, [(bx0, y), (cx, y), (tub[0], y)], 0.0, ends=False, color=BLUE,
              labels=[fi(cx - bx0), fi(tub[0] - cx)], box=True, **S)
        ys_ = m.HALL_Y1                                                  # vanity string, outside the south wall
        chain(ax, [(bx0, ys_), (lav[0], ys_), (lav[2], ys_), (tub[0], ys_), (bx1, ys_)], -0.45,
              labels=[None, fi(lav[2] - lav[0]) + " VANITY", fi(tub[0] - lav[2]), fi(bx1 - tub[0])], side=-1, **S)
    else:
        yn = by1 + (m.WET if i == 0 else m.PART)                         # far face of the wall behind the toilet
        lx = lav[2]
        labs = [fi(lx - bx0) + (" VANITY" if i == 0 else " LAV"), fi(cx - lx), fi(tub[0] - cx), fi(bx1 - tub[0]) + " TUB"]
        n = 5 if i == 0 else 4                                           # bath 3: the skewed rear wall closes the pipe space
        chain(ax, [(bx0, yn), (lx, yn), (cx, yn), (tub[0], yn), (bx1, yn)][:n], 0.38, labels=labs[:n - 1], **S)
    # toilet: clear in front, 15 in. each side
    front_to = lav[3] if i == 1 else by0
    xf = cx + 0.62
    D(ax, (xf, front_to), (xf, yf), 0, f"{fi(yf - front_to)} CLEAR", ext=False, size=4.6, color=BLUE, side=-1)
    if i == 1:
        line(ax, [(lav[2], front_to), (xf + 0.15, front_to)], color=BLUE, lw=0.3, z=8)
    txt(ax, cx - 0.4, yf - 1.75 + (0.14 if i != 1 else 0.42), "30 x 21 in. MIN. CLEAR", size=4.2, color=BLUE, z=9.5, box=True)
    txt(ax, cx + 0.07, cy + 0.2, "CL", size=4.2, color=BLUE, ha="left", z=9.5)
    # tub alcove
    xc = (tub[0] + tub[2]) / 2
    D(ax, (xc + 0.35, tub[1]), (xc + 0.35, tub[3]), 0, fi(tub[3] - tub[1]) + " ALCOVE, FINISHED WALL TO WALL", ext=False, size=4.6,
      color=BLUE, side=-1)
    txt(ax, xc - 0.45, (tub[1] + tub[3]) / 2, "TUB 60 x 30 in.\nfibreglass surround", size=4.6, rot=90, z=9.5)
    # door string, outside the door wall
    tag = door["tag"]
    if door["wall"] == "h":
        yd = door["at"][0]
        chain(ax, [(bx0, yd), (door["s0"], yd), (door["s1"], yd), (bx1, yd)], -0.38, side=-1,
              labels=[None, f"{fi(door['w'])} DOOR {tag}", None], **S)
    else:
        xd = door["at"][0]
        top = max(ys)
        chain(ax, [(xd, by0), (xd, door["s0"]), (xd, door["s1"]), (xd, top)], 0.42,
              labels=[None, f"{fi(door['w'])} DOOR {tag}", None], **S)
    # vanity / lavatory label
    w_in, d_in = round((lav[2] - lav[0]) * 12), round((lav[3] - lav[1]) * 12)
    kind = ("VANITY", "VANITY", "WALL-HUNG LAV")[i]
    lx, ly = (lav[0] + lav[2]) / 2, (lav[1] - 0.22 if i != 1 else (lav[1] + lav[3]) / 2)
    txt(ax, lx, ly, f"{kind} {w_in} x {d_in}", size=4.2, z=9.5, box=True)
    # grab-bar blocking: three tub walls, and behind / beside the toilet
    blocking(ax, (tub[2], tub[1]), (tub[2], tub[3]), off=-0.12)
    blocking(ax, (tub[0], tub[1]), (tub[2], tub[1]), off=-0.12)
    blocking(ax, (tub[0], tub[3]), (tub[2], tub[3]), off=0.12)
    blocking(ax, (cx - 1.25, cy), (cx + 1.25, cy), off=0.12)
    # exhaust fan (ceiling)
    fan = (xc, tub[1] + 0.72)
    rect(ax, fan[0] - 0.4, fan[1] - 0.4, fan[0] + 0.4, fan[1] + 0.4, fc=PAPER, ec=INK, lw=0.7, ls=(0, (3, 1.5)), z=8)
    txt(ax, fan[0], fan[1], "EF", size=4.6, weight="bold", z=9.5)
    return ax


def sheet_a401(pdf):
    notes = [
        ("Scope", [
            "Unit A is drawn; Unit B is identical and",
            "stacks directly above. Build both from",
            "this sheet. Sizes are standard catalogue",
            "sizes (model.SIZES); rental grade.",
        ]),
        ("Blocking (framer)", [
            "Orange dashes: 2x8 flat blocking between",
            "studs, 33 to 36 in. above the floor, on",
            "the three walls of each tub and behind",
            "each toilet, for grab bars now or later.",
            "Also block for vanities, the wall-hung",
            "lavatory, towel bars and wall cabinets.",
        ]),
        ("Exhaust fans", [
            "EF: ceiling fan, 80 cfm, over the end of",
            "each tub (listed for a tub location),",
            "ducted outside: bath 1 to the west wall,",
            "baths 2 and 3 to the rear wall (M-102).",
        ]),
        ("Tubs and toilets", [
            "60 x 30 alcove tub: frame each alcove",
            "5'-0\" between finished walls. Check the",
            "tub maker's rough-in before framing.",
            "Toilet centre line 15 in. from the tub",
            "and 15 in. min. from the other side;",
            "21 in. min. clear in front (IRC R307).",
        ]),
    ]
    fig, bg = new_sheet("A-401", "Kitchen and bath enlarged plans", "1/2\" = 1'-0\"", notes)
    bh = 3.7
    b0 = 0.5
    # ---- three baths along the bottom ----
    bath_view(fig, bg, 0, 0.5, b0, (11.9, 20.5), (20.48, 20.48 + bh * FPI_E))
    bath_view(fig, bg, 1, 5.0, b0, (18.7, 26.7), (29.15, 29.15 + bh * FPI_E))
    bath_view(fig, bg, 2, 9.2, b0, (36.2, 45.0), (23.4, 23.4 + bh * FPI_E))

    # ---- kitchen ----
    kb = b0 + bh + 0.45
    xlim, ylim = (19.2, 31.6), (10.3, 21.5)
    ax = enlarged(fig, bg, 0.5, kb, xlim, ylim, "Kitchen",
                  f"1/2\" = 1'-0\" · west wall run and island · aisle {fi(m.ISLAND[0] - m.KIT_BASE[2])}")
    for (sx, sy) in m.STOOLS:
        ax.add_patch(plt.Circle((sx, sy), 0.55, fc=PAPER, ec=plans.FURN, lw=0.5, zorder=6))
    for d in m.DOORS:
        if d["tag"] in ("D2", "D14"):
            poly(ax, list(m.door_sector(d).exterior.coords)[:-1], fc=SWING, ec="none", z=4.4, alpha=0.9)
    S = dict(size=5.0, min_len=0.12)
    kx = m.KIT_BASE[2]
    # west wall run
    xr_ = m.FRIDGE[2] + 0.35
    chain(ax, [(xr_, m.YFI), (xr_, m.RANGE[1]), (xr_, m.FRIDGE[1]), (xr_, m.FRIDGE[3]), (xr_, m.Y1)], 0.0, ends=False, side=-1,
          labels=[fi(m.RANGE[1] - m.YFI), fi(m.FRIDGE[1] - m.RANGE[1]), fi(m.FRIDGE[3] - m.FRIDGE[1]), fi(m.Y1 - m.FRIDGE[3])], **S)
    cxb = (m.KIT_BASE[0] + kx) / 2
    txt(ax, cxb, m.YFI + 1.25, "BASE\n24 in.", size=4.6, z=9.5)
    D(ax, (m.KIT_BASE[0], m.YFI + 0.4), (kx, m.YFI + 0.4), 0, fi(kx - m.KIT_BASE[0]), ext=False, size=4.4)
    txt(ax, cxb, (m.RANGE[1] + m.RANGE[3]) / 2, "RANGE 30 in.\nhood over", size=4.4, z=9.5, box=True)
    txt(ax, (m.FRIDGE[0] + m.FRIDGE[2]) / 2, m.FRIDGE[1] + 2.0, "REFRIGERATOR\nSPACE 36 in.", size=4.6, z=9.5)
    D(ax, (m.FRIDGE[0], m.FRIDGE[1] + 0.75), (m.FRIDGE[2], m.FRIDGE[1] + 0.75), 0, fi(m.FRIDGE[2] - m.FRIDGE[0]) + " DEEP", ext=False, size=4.4)
    # aisles
    A = dict(ext=False, size=5.0, color=BLUE, weight="bold")
    D(ax, (kx, 14.35), (m.ISLAND[0], 14.35), 0, fi(m.ISLAND[0] - kx) + " AISLE", at=0.56, **A)
    D(ax, (m.FRIDGE[2], 17.9), (m.ISLAND[0], 17.9), 0, fi(m.ISLAND[0] - m.FRIDGE[2]), at=0.6, **A)
    D(ax, (26.9, m.ISLAND_TOP[3]), (26.9, m.Y1), 0, fi(m.Y1 - m.ISLAND_TOP[3]) + " PATH", **A)
    D(ax, (29.3, m.YFI), (29.3, m.ISLAND[1]), 0, fi(m.ISLAND[1] - m.YFI), **A)
    # island
    xi = m.ISLAND[0] - 0.4
    chain(ax, [(xi, m.ISLAND[1]), (xi, m.ISL_DW[1]), (xi, m.ISL_DW[3]), (xi, m.ISLAND[3])], 0.0, ends=False,
          labels=[inch(m.ISL_DW[1] - m.ISLAND[1]), fi(m.ISL_DW[3] - m.ISL_DW[1]), fi(m.ISLAND[3] - m.ISL_DW[3])], **S)
    line(ax, [(m.ISLAND[0], m.ISL_DW[3]), (m.ISLAND[2], m.ISL_DW[3])], lw=0.4, color=plans.FURN, z=6.5)
    yi = m.ISLAND[1]
    chain(ax, [(m.ISLAND[0], yi), (m.ISLAND[2], yi), (m.ISLAND_TOP[2], yi)], -0.42, side=-1,
          labels=[fi(m.ISLAND[2] - m.ISLAND[0]) + " CABINET", inch(m.ISLAND_TOP[2] - m.ISLAND[2]) + " OVERHANG"], **S)
    D(ax, (m.ISLAND_TOP[2], m.ISLAND[1]), (m.ISLAND_TOP[2], m.ISLAND[3]), -2.5, fi(m.ISLAND[3] - m.ISLAND[1]) + " ISLAND TOP", side=-1, size=5.0)
    xs_ = m.STOOLS[0][0] + 0.85
    chain(ax, [(xs_, sy) for (sx, sy) in m.STOOLS], 0.0, ends=False, side=-1, size=4.4,
          labels=[inch(m.STOOLS[1][1] - m.STOOLS[0][1])] * 2)
    txt(ax, (m.ISL_DW[0] + m.ISL_DW[2]) / 2, (m.ISL_DW[1] + m.ISL_DW[3]) / 2, "DISHWASHER\n24 in.", size=4.4, z=9.5)
    txt(ax, (m.ISLAND[0] + m.ISLAND[2]) / 2, m.ISLAND[3] - 0.38, "SINK BASE 33 in.", size=4.2, z=9.5)
    txt(ax, m.ISLAND[2] + 0.5, m.ISLAND[1] + 3.3, "12 in. SEATING OVERHANG", size=4.2, rot=90, z=9.5)
    txt(ax, m.STOOLS[1][0], m.STOOLS[1][1], "STOOL", size=4.2, color=GREY, z=9.5)
    # notes in the view
    txt(ax, 20.2, 19.75, "DOOR D2 TO BEDROOM 1", size=4.4, color=GREY, rot=90)
    txt(ax, 28.2, 11.05, "PORCH DOOR D14", size=4.4, color=GREY)
    txt(ax, 24.4, 11.0, "WINDOW W2 (A-601)", size=4.4, color=GREY)
    txt(ax, 30.2, 20.6, "LIVING ROOM", size=5.0, weight="bold")
    scale_bar(ax, 29.2, 19.6, 2, 1, 0.12, size=4.6)

    # ---- notes and sizes beside the kitchen ----
    xn = 0.5 + (xlim[1] - xlim[0]) / FPI_E + 0.35
    yt = kb + (ylim[1] - ylim[0]) / FPI_E + 0.2
    y1_ = block(bg, xn, yt, "Kitchen: for the cabinet installer", [
        "WEST WALL RUN, from the front wall going north:",
        f"  {fi(m.RANGE[1] - m.YFI)} base cabinet, {fi(m.RANGE[3] - m.RANGE[1])} freestanding range,",
        f"  {fi(m.FRIDGE[3] - m.FRIDGE[1])} refrigerator space ({fi(m.FRIDGE[2] - m.FRIDGE[0])} deep, no cabinet).",
        f"  Then {fi(m.Y1 - m.FRIDGE[3])} of clear floor to the bedroom 1 door.",
        "  Base cabinets 24 in. deep, laminate counter 25 in.",
        "  deep at 36 in. high. Range hood over the range,",
        "  ducted to the front wall (M-102).",
        "ISLAND, fixed to the floor:",
        f"  Cabinet body {fi(m.ISLAND[3] - m.ISLAND[1])} x {fi(m.ISLAND[2] - m.ISLAND[0])}: from the south end,",
        f"  {inch(m.ISL_DW[1] - m.ISLAND[1])} filler, 24 in. dishwasher, 33 in. sink base.",
        f"  Top {fi(m.ISLAND_TOP[3] - m.ISLAND_TOP[1])} x {fi(m.ISLAND_TOP[2] - m.ISLAND_TOP[0])}: 12 in. seating overhang on the",
        "  living-room side, on brackets by the supplier.",
        f"  {len(m.STOOLS)} stools at {inch(m.STOOLS[1][1] - m.STOOLS[0][1])} centres (by tenant).",
        "  Sink drain, water and the island receptacle come",
        "  up through the floor inside the sink base: cut",
        "  the cabinet floor after the plumber marks it.",
        "  Finished end panels on both ends and the back.",
    ], fs=5.6, lh=0.138)
    xn2 = xn + 3.3
    y2_ = block(bg, xn2, yt, "Clearances held", [
        f"Counter to island: {fi(m.ISLAND[0] - kx)} (42 in. min.).",
        f"Refrigerator to island: {fi(m.ISLAND[0] - m.FRIDGE[2])}.",
        f"Island to the front wall: {fi(m.ISLAND[1] - m.YFI)}.",
        f"Island to the hall wall: {fi(m.Y1 - m.ISLAND_TOP[3])} (30 in. min.).",
        "Orange = floor swept by a door: keep clear.",
    ], fs=5.6, lh=0.138)
    y2_ = block(bg, xn2, y2_, "Baths: for plumber and tile", [
        "Fixtures back onto the 2x6 plumbing wall",
        "(bath 1), the furred pipe space (bath 2)",
        "and the pipe space behind bath 3.",
        "Vanity tops: laminate with drop-in bowl.",
        "Floors LVP; tub surrounds fibreglass, no tile.",
        "Bath 2: the rear wall is skewed. Fur a square",
        "end wall across the north end of the tub.",
        "Bath 2 in Unit A sits on the slab on grade:",
        "its drains go in before the slab (P-101).",
    ], fs=5.6, lh=0.138)
    block(bg, xn2, y2_, "Legend", [
        "Blue dashed box: toilet clearance.",
        "Blue dash-dot: toilet centre line (CL).",
        "Orange dashes: blocking in the wall.",
        "EF in a dashed square: ceiling exhaust fan.",
    ], fs=5.6, lh=0.138)
    keep = ("Bathtub", "Toilet", "Vanity", "Range", "Refrigerator", "Dishwasher", "Sink base", "Base cabinets", "Island")
    rows = [("ITEM", "STANDARD SIZE (model.SIZES)")] + [(k, m.SIZES[k]) for k in keep]
    table(bg, xn, kb + 10 * 0.152 + 0.02, [0.95, 13.62 - xn - 0.95], rows, fs=5.2, rh=0.152)
    save(fig, "A-401", pdf)


SHEETS = [
    ("A-101", sheet_a101),
    ("A-102", sheet_a102),
    ("A-103", sheet_a103),
    ("A-104", sheet_a104),
    ("A-105", sheet_a105),
    ("A-401", sheet_a401),
]
