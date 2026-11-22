"""Sheets A-101..A-103 (floor plans), A-201 (street elevation), A-301 (section), A-401 (options)."""
import math

import numpy as np

from common import *  # noqa: F401,F403

FPI = 16 / 3.0          # 3/16" = 1'-0"
VIEW_X = (-5, 55)
VIEW_Y = (-10.5, 38.5)
POCHE = "#1b1e22"
CONC = "#a9aeb4"
FURN = "#8d949c"
WOOD = "#f4f1ea"


def plan_frame(fig, title, sub):
    left = MARGIN + (SHEET_W - 2 * MARGIN - TB_W - (VIEW_X[1] - VIEW_X[0]) / FPI) / 2
    ax = plan_axes(fig, left, 0.72, VIEW_X, VIEW_Y, FPI)
    # lot lines within view
    rear_pts = [(x, rear_y(x)) for x in (LOT_NW[0], 50)]
    line(ax, [LOT_NW, LOT_SW, LOT_SE, LOT_NE, LOT_NW], color=ACCENT, lw=1.1, ls=(0, (9, 2.5, 1.5, 2.5)), z=2)
    txt(ax, 51.2, 13.0, "LOT LINE", size=5.0, color=ACCENT, rot=90)
    txt(ax, 44, -1.0, "FRONT LOT LINE / BAIRD ST R.O.W.", size=5.0, color=ACCENT)
    txt(ax, 41.5, 37.6, "REAR LOT LINE", size=5.0, color=ACCENT, rot=math.degrees(math.atan(REAR_SLOPE)))
    # street edge
    line(ax, [(VIEW_X[0], PAVE_N), (VIEW_X[1], PAVE_N)], color=GREY, lw=0.6, z=2)
    rect(ax, VIEW_X[0], VIEW_Y[0], VIEW_X[1], PAVE_N, fc="#e6e8eb", ec="none", z=1)
    txt(ax, 46.5, -8.9, "BAIRD STREET  (±14' pavement)", size=6.0, color=GREY, weight="bold")
    north_arrow(ax, 51.2, 33.6, 1.9, 6.5)
    scale_bar(ax, -3.5, -9.6, 16, 4, 0.42, size=5.2)
    view_title(ax, -4.4, 36.6, "1", title, sub, 9)
    return ax


def shell(ax, t_front, t_other, fc):
    rect(ax, BX0, BY0, BX1, BY1, fc=fc, ec=INK, lw=0.9, z=3)
    rect(ax, BX0 + t_other, BY0 + t_front, BX1 - t_other, BY1 - t_other, fc=PAPER, ec=INK, lw=0.6, z=4)


def wall(ax, x0, y0, x1, y1, fc=POCHE):
    rect(ax, x0, y0, x1, y1, fc=fc, ec=INK, lw=0.4, z=5)


def stair(ax, x0, x1, ys, ye, n=15, mode="both", split=19.0, label_up="UP 16R", label_dn="DN 16R"):
    """Straight stair rising from ys (south) to ye (north).
    mode: "up" = lower flight only (cut at split), "both" = up flight + down flight below,
    "down" = arriving flight seen from the top floor."""
    step = (ye - ys) / n
    xm = (x0 + x1) / 2
    arrow = dict(arrowstyle="-|>", lw=0.6, color=INK)
    for i in range(n + 1):
        y = ys + i * step
        if mode == "up" and y > split + 0.6:
            line(ax, [(x0, y), (x1, y)], lw=0.3, color=GREY, ls=(0, (3, 2)), z=6)
        else:
            line(ax, [(x0, y), (x1, y)], lw=0.4, color=INK, z=6)
    if mode in ("up", "both"):
        line(ax, [(x0, split - 0.5), (x1, split + 0.5)], lw=0.9, z=8)
        line(ax, [(x0, split - 0.05), (x1, split + 0.95)], lw=0.9, z=8)
        ax.annotate("", xy=(xm, split - 0.9), xytext=(xm, ys + 0.3), arrowprops=arrow, zorder=8)
        txt(ax, xm, ys - 0.7, label_up, size=5.2, weight="bold")
    if mode == "both":
        ax.annotate("", xy=(xm, split + 1.6), xytext=(xm, ye - 0.3), arrowprops=arrow, zorder=8)
        txt(ax, xm, ye + 0.7, label_dn, size=5.2, weight="bold")
    if mode == "down":
        ax.annotate("", xy=(xm, ys + 0.5), xytext=(xm, ye - 0.3), arrowprops=arrow, zorder=8)
        txt(ax, xm, ye + 0.7, label_dn, size=5.2, weight="bold")


def car(ax, x0, y0, w=6.3, l=16.5, label=None):
    from matplotlib.patches import FancyBboxPatch
    ax.add_patch(FancyBboxPatch((x0 + 0.5, y0 + 0.5), w - 1, l - 1, boxstyle="round,pad=0.5,rounding_size=1.1",
                                fc="#f2f3f5", ec=FURN, lw=0.6, zorder=6))
    rect(ax, x0 + 0.7, y0 + 3.4, x0 + w - 0.7, y0 + 5.2, fc="none", ec=FURN, lw=0.4, z=6)
    rect(ax, x0 + 0.7, y0 + l - 5.6, x0 + w - 0.7, y0 + l - 3.6, fc="none", ec=FURN, lw=0.4, z=6)
    if label:
        txt(ax, x0 + w / 2, y0 + l / 2, label, size=5.4, color=GREY)


def room(ax, x, y, name, size=None, extra=None, fs=6.6):
    txt(ax, x, y, name, size=fs, weight="bold", z=9, box=True)
    if size:
        txt(ax, x, y - 1.05, size, size=5.4, z=9, box=True)
    if extra:
        txt(ax, x, y - 2.0, extra, size=5.0, color=GREY, z=9, box=True)


def entry_steps(ax, solid=True):
    c = INK if solid else GREY
    ls = "-" if solid else "--"
    rect(ax, 5.5, 2.5, 9, 21, fc=PAPER if solid else "none", ec=c, lw=0.6, z=3, ls=ls)
    for y in list(np.arange(2.5, 7.6, 1.0)) + list(np.arange(10.5, 14.6, 1.0)):
        line(ax, [(5.5, y), (9, y)], lw=0.35, color=c, z=4, ls=ls)


# ----------------------------------------------------------------------------
def sheet_a101(pdf):
    gar_w, gar_d = 31 - 10, 29 - (BY0 + 0.67)
    notes = [
        ("Lower level", [
            f"Finished slab EL {EL_GAR:.1f} (level with the street",
            "at the west jamb, ±3 ft above it at the",
            "loading door).",
            "Gross 792 sf · clear span, no interior",
            "bearing walls, so the car/storage split",
            "can change (see A-401).",
            "Garage 21'-0\" x 20'-4\"  = 427 sf",
            "Storage 8'-8\" x 20'-4\"  = 177 sf",
        ]),
        ("Parking shown", [
            "2 cars side by side behind one 16' x 8'",
            "door. Meets the 2 spaces required for a",
            "single-family dwelling (Table 1365.04).",
            "Apron is 15 ft long but only ±8 ft of it",
            "is on the lot: no legal parking on it.",
        ]),
        ("Structure (for engineer)", [
            "Rear and side walls are retaining walls,",
            "±7.5 to 10.5 ft of soil at the rear. Needs",
            "geotechnical report, engineered design,",
            "waterproofing, footing drains to daylight.",
            "±250 to 300 cu yd of excavation.",
            "Shoring / underpinning review for 441",
            "and 442 Baird, both close to the lines.",
        ]),
        ("Driveway (for civil/City Engineer)", [
            "Street falls ±1.8 ft across the 16' door.",
            "Apron must warp: ±0 % at the west jamb,",
            "±12 % at the east. Trench drain at door.",
            "Driveway permit; max 22 ft at R.O.W.",
        ]),
    ]
    fig, bg = new_sheet("A-101", "Lower level: garage + storage", "3/16\" = 1'-0\"", notes)
    ax = plan_frame(fig, "Lower level plan", f"Garage / storage · slab EL {EL_GAR:.1f} · concrete retaining walls shown grey")
    # site work
    apron = [(12.5, BY0), (28.5, BY0), (30.2, PAVE_N), (10.3, PAVE_N)]
    poly(ax, apron, fc="#d5dbe2", ec=INK, lw=0.6, z=2)
    pad = [(33, BY0), (39, BY0), (39.6, PAVE_N), (32.4, PAVE_N)]
    poly(ax, pad, fc="#e2e6eb", ec=INK, lw=0.5, z=2)
    txt(ax, 20.5, 1.6, "CONCRETE APRON", size=6.0, weight="bold")
    txt(ax, 20.5, 0.4, "warped: ±0 % (west) to ±12 % (east)", size=5.0)
    ax.annotate("", xy=(20.5, -6.2), xytext=(20.5, -1.2), arrowprops=dict(arrowstyle="-|>", lw=0.6, color=INK), zorder=8)
    txt(ax, 22.4, -4.0, "DN", size=5.0)
    txt(ax, 36, 2.4, "LOADING\nPAD", size=5.4, weight="bold")
    txt(ax, 36, -0.4, "level, ±EL 913", size=4.8)
    txt(ax, 36, -3.4, "floor is ±2'-6\"\nabove pad =\ntruck-bed height", size=4.8, color=GREY)
    line(ax, [(12.5, 7.55), (28.5, 7.55)], lw=1.4, color=BLUE, z=6)
    txt(ax, 10.2, 6.5, "TRENCH\nDRAIN", size=4.6, color=BLUE)
    for xw in ((10.3, 12.5), (30.2, 28.5), (32.4, 33), (39.6, 39)):
        line(ax, [(xw[0], PAVE_N + 4), (xw[1], BY0)], lw=1.6, color=CONC, z=3)
    txt(ax, 31.3, -3.4, "CHEEK WALLS", size=4.4, color=GREY, rot=90)
    entry_steps(ax, solid=False)
    txt(ax, -2.3, 14.0, "ENTRY STEPS\nON GRADE\n(TO MAIN\nLEVEL)", size=4.8, color=GREY)
    line(ax, [(-0.2, 14.0), (5.4, 14.0)], lw=0.3, color=GREY)
    rect(ax, 9, 4, 35, BY0, fc="none", ec=GREY, lw=0.5, z=6, ls="--")
    txt(ax, 6.2, -1.6, "PORCH ABOVE\n(DASHED)", size=4.6, color=GREY)
    line(ax, [(8.6, -0.9), (10.5, 4.0)], lw=0.3, color=GREY)
    for px in (9.7, 31.4):
        rect(ax, px - 0.35, 4.0, px + 0.35, 4.7, fc=POCHE, z=7)
    # shell
    shell(ax, 0.67, 1.0, CONC)
    opening(ax, 12.5, BY0 - 0.02, 28.5, BY0 + 0.69)
    line(ax, [(12.5, BY0 + 0.2), (28.5, BY0 + 0.2)], lw=0.5, ls=(0, (5, 2)), z=7)
    line(ax, [(12.5, BY0 + 0.45), (28.5, BY0 + 0.45)], lw=0.5, ls=(0, (5, 2)), z=7)
    txt(ax, 20.5, 9.9, "16'-0\" x 8'-0\" OVERHEAD DOOR", size=5.2)
    opening(ax, 33, BY0 - 0.02, 39, BY0 + 0.69)
    line(ax, [(33, BY0 + 0.33), (39, BY0 + 0.33)], lw=0.5, ls=(0, (5, 2)), z=7)
    txt(ax, 36, 9.9, "6' x 7' LOADING DOOR", size=4.8)
    # partition + door
    wall(ax, 31, BY0 + 0.67, 31.5, 29)
    opening(ax, 30.98, 10.2, 31.52, 13.2)
    door(ax, (31.25, 13.2), 3.0, 180, 90)
    # stair
    wall(ax, 40.2, 13, 40.5, 29)
    opening(ax, 40.18, 25.9, 40.52, 28.4)
    door(ax, (40.35, 25.9), 2.5, 90, 90)
    stair(ax, 40.5, 44, 13, 25.5, mode="up", split=18.6)
    rect(ax, 40.5, 19.6, 44, 29, fc="none", ec="none", z=6)
    txt(ax, 42.25, 27.3, "MECH", size=5.4, weight="bold")
    txt(ax, 42.25, 26.4, "under stair", size=4.6, color=GREY)
    # cars + shelving
    car(ax, 13.3, 10.6)
    car(ax, 21.4, 10.6)
    txt(ax, 16.45, 13.0, "CAR 1", size=5.4, color=GREY)
    txt(ax, 24.55, 13.0, "CAR 2", size=5.4, color=GREY)
    rect(ax, 10, 27.5, 31, 29, fc=WOOD, ec=FURN, lw=0.5, z=5, ls="--")
    txt(ax, 20.5, 28.25, "FULL-WIDTH SHELVING / WORKBENCH (18\" DEEP)", size=4.8, color=GREY)
    rect(ax, 38.2, 14.5, 40.2, 25, fc=WOOD, ec=FURN, lw=0.5, z=5, ls="--")
    rect(ax, 31.5, 27, 38.2, 29, fc=WOOD, ec=FURN, lw=0.5, z=5, ls="--")
    txt(ax, 39.2, 19.7, "RACKING", size=4.6, color=GREY, rot=90)
    txt(ax, 34.9, 28.0, "RACKING", size=4.6, color=GREY)
    room(ax, 20.5, 21.2, "2-CAR GARAGE", f"{ftin(gar_w)} x {ftin(gar_d)}  ·  427 sf", f"slab EL {EL_GAR:.1f}  ·  9'-0\" clear")
    room(ax, 35.0, 21.2, "STORAGE /", None)
    txt(ax, 35.0, 20.2, "WORKSHOP", size=6.6, weight="bold")
    txt(ax, 35.0, 19.1, "8'-8\" x 20'-4\"", size=5.4)
    txt(ax, 35.0, 18.2, "177 sf", size=5.4)
    # retaining notes
    txt(ax, 27, 31.4, "12\" REINFORCED CONCRETE RETAINING WALL · retains ±7.5 ft (east) to ±10.5 ft (west) · waterproofing + footing drain",
        size=4.9, color=INK)
    # dims
    dim(ax, (BX0, BY1), (BX1, BY1), 3.4, "36'-0\"")
    dim(ax, (BX1, BY0), (BX1, BY1), -7.6, "22'-0\"", side=-1)
    dim(ax, (10, 14.5), (31, 14.5), 0, "21'-0\"", ext=False, size=5.4)
    dim(ax, (11.6, BY0 + 0.67), (11.6, 29), 0, "20'-4\"", ext=False, size=5.4)
    dim(ax, (12.5, BY0), (28.5, BY0), -3.2, "16'-0\"", side=-1, size=5.4)
    dim(ax, (46.2, 0), (46.2, BY0), 0, "8'-0\"", ext=False, size=5.2, color=ACCENT)
    dim(ax, (BX1, 20), (50, 20), 0, "5'-0\"", ext=False, size=5.2, color=ACCENT)
    dim(ax, (west_x(27), 27), (BX0, 27), 0, f"{ftin(perp_to_west(BX0, 27))}", ext=False, size=5.2, color=ACCENT)
    save(fig, "A-101", pdf)


# ----------------------------------------------------------------------------
def frame_shell(ax):
    shell(ax, 0.5, 0.5, POCHE)


def fixture_wc(ax, x, y, rot=0):
    from matplotlib.patches import Ellipse
    if rot == 0:      # tank on north wall
        rect(ax, x - 0.8, y - 0.65, x + 0.8, y, fc=PAPER, ec=FURN, lw=0.5, z=6)
        ax.add_patch(Ellipse((x, y - 1.55), 1.3, 1.8, fc=PAPER, ec=FURN, lw=0.5, zorder=6))
    else:             # tank on south wall
        rect(ax, x - 0.8, y, x + 0.8, y + 0.65, fc=PAPER, ec=FURN, lw=0.5, z=6)
        ax.add_patch(Ellipse((x, y + 1.55), 1.3, 1.8, fc=PAPER, ec=FURN, lw=0.5, zorder=6))


def fixture_lav(ax, x0, y0, x1, y1):
    from matplotlib.patches import Ellipse
    rect(ax, x0, y0, x1, y1, fc=PAPER, ec=FURN, lw=0.5, z=6)
    ax.add_patch(Ellipse(((x0 + x1) / 2, (y0 + y1) / 2), min(1.4, (x1 - x0) * 0.6), min(1.1, (y1 - y0) * 0.6), fc=PAPER, ec=FURN, lw=0.5, zorder=6))


def sheet_a102(pdf):
    notes = [
        ("Main level", [
            f"Finished floor EL {EL_MAIN:.1f}, 10'-0\" above",
            "the garage slab. Gross 792 sf.",
            "Open living / dining / kitchen facing",
            "south over the street and valley.",
            "Powder room, laundry + mechanical.",
            "Rear door walks out at grade to the",
            "back patio (rear grade ±EL 923 to 926).",
        ]),
        ("Entry", [
            "On-grade steps climb the west side yard",
            "from the sidewalk (±EL 919.5) to a side",
            "stoop: ±6 ft of rise, ±10 risers.",
            "Steps, walls and terraces may sit in",
            "required yards (1337.05(C)).",
        ]),
        ("Front porch", [
            "26' x 4' covered, unenclosed porch over",
            "the garage door. The R-2 standards call",
            "for a substantial street-facing porch;",
            "an unenclosed porch may project half",
            "the front setback depth and does not",
            "count toward lot coverage.",
        ]),
        ("Fire separation (for architect)", [
            "East wall is 5'-0\" from the lot line and",
            "the NE corner ±5'-4\" from the rear line.",
            "Check IRC R302.1 wall rating and",
            "opening limits at these distances.",
        ]),
    ]
    fig, bg = new_sheet("A-102", "Main level: living", "3/16\" = 1'-0\"", notes)
    ax = plan_frame(fig, "Main level plan", f"Living / dining / kitchen · finished floor EL {EL_MAIN:.1f}")
    # site elements
    rect(ax, 14, BY1, 30, 37, fc="#f3f4f5", ec=GREY, lw=0.5, z=2, ls="--")
    txt(ax, 22, 34.3, "REAR PATIO AT GRADE", size=5.6, weight="bold", color=GREY)
    txt(ax, 22, 33.3, "±EL 925.5", size=5.0, color=GREY)
    entry_steps(ax, solid=True)
    txt(ax, 7.25, 18.0, "STOOP", size=4.8, rot=90)
    ax.annotate("", xy=(7.25, 14.2), xytext=(7.25, 3.0), arrowprops=dict(arrowstyle="-|>", lw=0.6, color=INK), zorder=8)
    txt(ax, -2.0, 7.0, "ENTRY STEPS\nUP ±10R\nFROM\nSIDEWALK", size=4.8)
    line(ax, [(0.1, 7.0), (5.4, 7.0)], lw=0.3, color=GREY)
    # porch
    rect(ax, 9, 4, 35, BY0, fc=WOOD, ec=INK, lw=0.7, z=3)
    for x in np.arange(9.5, 35, 0.5):
        line(ax, [(x, 4), (x, BY0)], lw=0.15, color=LIGHT, z=3)
    line(ax, [(9.2, 4.2), (34.8, 4.2), (34.8, BY0)], lw=1.0, color=INK, z=6)
    line(ax, [(9.2, 4.2), (9.2, BY0)], lw=1.0, color=INK, z=6)
    for px in (9.7, 18.2, 26.6, 34.4):
        rect(ax, px - 0.3, 4.05, px + 0.3, 4.65, fc=POCHE, z=7)
    txt(ax, 22, 6.2, "COVERED FRONT PORCH   26'-0\" x 4'-0\"", size=5.6, weight="bold", box=True)
    txt(ax, 20.5, 1.4, "driveway apron below", size=4.8, color=GREY)
    txt(ax, 36, 1.4, "loading pad below", size=4.8, color=GREY)
    # shell + openings
    frame_shell(ax)
    window_h(ax, 13, 21, BY0, BY0 + 0.5)       # living slider
    window_h(ax, 28, 34, BY0, BY0 + 0.5)       # dining slider
    window_h(ax, 36.5, 39.5, BY0, BY0 + 0.5)
    window_v(ax, 10.5, 13.5, BX0, BX0 + 0.5)
    window_h(ax, 30, 34, BY1 - 0.5, BY1)
    window_h(ax, 11, 13, BY1 - 0.5, BY1)
    window_v(ax, 17.5, 20.5, BX1 - 0.5, BX1)
    opening(ax, BX0 - 0.02, 17, BX0 + 0.52, 20)
    door(ax, (BX0 + 0.5, 17), 3.0, 0, 90)
    opening(ax, 21.6, BY1 - 0.52, 24.6, BY1 + 0.02)
    door(ax, (21.6, BY1 - 0.5), 3.0, 270, 90)
    # service block
    wall(ax, 9.5, 23.5, 21.375, 23.875)
    wall(ax, 14.5, 23.875, 14.875, 29.5)
    wall(ax, 21, 23.5, 21.375, 29.5)
    opening(ax, 11.3, 23.48, 13.8, 23.9)
    door(ax, (11.3, 23.5), 2.5, 0, -90)
    opening(ax, 16.6, 23.48, 19.4, 23.9)
    door(ax, (16.6, 23.5), 2.8, 0, -90)
    fixture_wc(ax, 12.4, 29.5)
    fixture_lav(ax, 9.5, 24.6, 11.1, 26.6)
    rect(ax, 15.1, 26.9, 17.6, 29.4, fc=PAPER, ec=FURN, lw=0.5, z=6)
    rect(ax, 17.8, 26.9, 20.3, 29.4, fc=PAPER, ec=FURN, lw=0.5, z=6)
    txt(ax, 16.35, 28.15, "W", size=5, color=GREY)
    txt(ax, 19.05, 28.15, "D", size=5, color=GREY)
    ax.add_patch(plt.Circle((20.1, 25.2), 0.75, fc=PAPER, ec=FURN, lw=0.5, zorder=6))
    txt(ax, 20.1, 25.2, "WH", size=4.2, color=GREY)
    txt(ax, 12.9, 25.3, "POWDER", size=5.0, weight="bold")
    txt(ax, 17.0, 25.3, "LAUNDRY /\nMECH", size=5.0, weight="bold")
    # coat closet
    wall(ax, 9.5, 13.8, 11.9, 14.1)
    wall(ax, 9.5, 16.5, 11.9, 16.8)
    line(ax, [(11.75, 14.1), (11.75, 16.5)], lw=0.5, ls="--", z=6)
    txt(ax, 10.7, 15.3, "COATS", size=4.4, color=GREY, rot=90)
    # stair
    wall(ax, 40.67, 13, 41, 25.5)
    stair(ax, 41, 44.5, 13, 25.5, mode="both")
    txt(ax, 42.75, 10.4, "LANDING", size=4.6, color=GREY)
    txt(ax, 42.75, 28.3, "LANDING", size=4.6, color=GREY)
    # kitchen
    rect(ax, 25, 27.5, 40.5, 29.5, fc=WOOD, ec=FURN, lw=0.6, z=5)
    rect(ax, 25, 26.9, 28, 29.5, fc=PAPER, ec=FURN, lw=0.6, z=6)
    txt(ax, 26.5, 28.2, "REF", size=4.6, color=GREY)
    fixture_lav(ax, 30.6, 27.7, 33.4, 29.3)
    rect(ax, 36, 27.6, 38.5, 29.4, fc=PAPER, ec=FURN, lw=0.6, z=6)
    for cx in (36.65, 37.85):
        for cy in (28.1, 28.95):
            ax.add_patch(plt.Circle((cx, cy), 0.3, fc="none", ec=FURN, lw=0.4, zorder=7))
    rect(ax, 27, 21.6, 35, 24.6, fc=WOOD, ec=FURN, lw=0.6, z=5)
    txt(ax, 31, 23.1, "ISLAND 8' x 3'", size=4.8, color=GREY)
    for sx in (28.5, 31, 33.5):
        ax.add_patch(plt.Circle((sx, 20.8), 0.55, fc=PAPER, ec=FURN, lw=0.4, zorder=6))
    # furniture
    rect(ax, 13.6, 16.6, 20.6, 19.6, fc="#f2f3f5", ec=FURN, lw=0.5, z=5)
    rect(ax, 13.6, 18.9, 20.6, 19.6, fc="#e4e6e9", ec=FURN, lw=0.4, z=6)
    rect(ax, 15.1, 13.2, 19.1, 15.0, fc="#f2f3f5", ec=FURN, lw=0.5, z=5)
    rect(ax, 29.5, 11.6, 36, 15.1, fc="#f2f3f5", ec=FURN, lw=0.5, z=5)
    for cx in (30.6, 32.75, 34.9):
        for cy in (10.8, 15.9):
            rect(ax, cx - 0.7, cy - 0.55, cx + 0.7, cy + 0.55, fc=PAPER, ec=FURN, lw=0.4, z=5)
    room(ax, 17.2, 11.6, "LIVING", "15'-6\" x 14'-0\"")
    room(ax, 32.7, 18.6, "DINING", "15'-0\" x 10'-6\"")
    room(ax, 37.6, 25.6, "KITCHEN", None, fs=6.2)
    txt(ax, 37.6, 24.6, "19' x 9'-6\"", size=5.2)
    txt(ax, 11.4, 21.7, "ENTRY", size=5.2, weight="bold")
    txt(ax, 17, 8.95, "8' SLIDING DOOR", size=4.4, color=GREY)
    txt(ax, 31, 8.95, "6' SLIDING DOOR", size=4.4, color=GREY)
    # dims
    dim(ax, (BX0, BY1), (BX1, BY1), 7.4, "36'-0\"")
    dim(ax, (BX1, BY0), (BX1, BY1), -7.6, "22'-0\"", side=-1)
    dim(ax, (46.2, 0), (46.2, BY0), 0, "8'-0\"", ext=False, size=5.2, color=ACCENT)
    dim(ax, (37.5, 4), (37.5, BY0), 0, "4'-0\"", ext=False, size=5.0)
    dim(ax, (BX1, 23), (50, 23), 0, "5'-0\"", ext=False, size=5.2, color=ACCENT)
    xr = BX1
    d = perp_to_rear(xr, BY1)
    s = math.atan(REAR_SLOPE)
    line(ax, [(xr, BY1), (xr - d * math.sin(s), BY1 + d * math.cos(s))], color=ACCENT, lw=0.6, z=9)
    txt(ax, xr + 2.6, BY1 + 2.0, f"{ftin(d)}\nTO REAR LINE", size=4.8, color=ACCENT)
    save(fig, "A-102", pdf)


# ----------------------------------------------------------------------------
def sheet_a103(pdf):
    notes = [
        ("Upper level", [
            f"Finished floor EL {EL_UP:.1f}, 10'-0\" above",
            "the main floor. Gross 792 sf.",
            "2 bedrooms + study, 2 baths, laundry",
            "closet. 8'-1\" ceilings, 6:12 gable roof",
            "with the ridge parallel to the street.",
        ]),
        ("Area summary (gross)", [
            "Lower level (garage/storage)    792 sf",
            "Main level                                   792 sf",
            "Upper level                                 792 sf",
            "Conditioned living area          1,584 sf",
            "Total enclosed                         2,376 sf",
            "Front porch (unenclosed)          104 sf",
        ]),
        ("Storey count (for planner)", [
            "R-2 allows 2.5 storeys / 35 ft. A",
            "'basement' (half or more of its height",
            "below average adjoining grade) is not",
            "a storey. The garage level is borderline",
            "(±51 % buried on a perimeter average).",
            "If it is ruled a storey, either get a",
            "height variance or rebuild this level",
            "as a half-storey under the roof.",
        ]),
        ("Height in feet", [
            f"Mean roof EL {EL_MEAN_ROOF:.1f} minus reference",
            f"grade EL {EL_REF:.1f} = {EL_MEAN_ROOF - EL_REF:.1f} ft (35 ft max).",
        ]),
    ]
    fig, bg = new_sheet("A-103", "Upper level: bedrooms", "3/16\" = 1'-0\"", notes)
    ax = plan_frame(fig, "Upper level plan", f"Bedrooms · finished floor EL {EL_UP:.1f}")
    # roofs below
    rect(ax, 8.6, 3.6, 35.4, BY0, fc="#eceef0", ec=GREY, lw=0.6, z=2)
    for y in np.arange(4.2, BY0, 0.6):
        line(ax, [(8.6, y), (35.4, y)], lw=0.15, color=LIGHT, z=2)
    txt(ax, 22, 5.8, "PORCH ROOF BELOW", size=5.2, color=GREY, box=True)
    rect(ax, BX0 - 1, BY0 - 1, BX1 + 1, BY1 + 1, fc="none", ec=GREY, lw=0.5, z=2, ls=(0, (6, 3)))
    txt(ax, 47.3, 13, "ROOF EAVE ABOVE (1' OVERHANG)", size=4.4, color=GREY, rot=90)
    frame_shell(ax)
    # windows
    window_h(ax, 13, 19, BY0, BY0 + 0.5)
    window_h(ax, 26, 31, BY0, BY0 + 0.5)
    window_h(ax, 36, 39, BY0, BY0 + 0.5)
    window_v(ax, 12, 15, BX0, BX0 + 0.5)
    window_h(ax, 19.5, 21.5, BY1 - 0.5, BY1)
    window_h(ax, 33.4, 35.4, BY1 - 0.5, BY1)
    window_h(ax, 41.8, 43.8, BY1 - 0.5, BY1)
    window_v(ax, 17.5, 20.5, BX1 - 0.5, BX1)
    # partitions
    wall(ax, 9.5, 20, 40.67, 20.375)                 # bedrooms / hall
    wall(ax, 16, 23.875, 37.875, 24.25)              # hall / rear rooms
    wall(ax, 16, 20.375, 16.375, 29.5)               # WIC east wall
    wall(ax, 25.5, 24.25, 25.875, 29.5)              # bath 1 / laundry
    wall(ax, 31, 24.25, 31.375, 29.5)                # laundry / bath 2
    wall(ax, 37.5, 23.875, 37.875, 29.5)             # bath 2 east
    wall(ax, 23, 8.5, 23.375, 20)                    # primary / BR2
    wall(ax, 34, 8.5, 34.375, 20)                    # BR2 / study
    wall(ax, 40.67, 8.5, 41, 25.5)                   # stair wall
    wall(ax, 41, 13, 44.5, 13.3)                     # closet over landing
    # doors
    opening(ax, 11.2, 19.98, 13.7, 20.4)             # primary -> WIC
    door(ax, (11.2, 20.375), 2.5, 0, 90)
    opening(ax, 19.2, 19.98, 21.87, 20.4)            # hall -> primary
    door(ax, (21.87, 20.0), 2.67, 180, 90)
    opening(ax, 24.3, 19.98, 26.97, 20.4)            # hall -> BR2
    door(ax, (24.3, 20.0), 2.67, 270, 90)
    opening(ax, 36.0, 19.98, 38.67, 20.4)            # hall -> study
    door(ax, (36.0, 20.0), 2.67, 270, 90)
    opening(ax, 17.2, 23.86, 19.7, 24.27)            # bath 1
    door(ax, (17.2, 24.25), 2.5, 0, 90)
    opening(ax, 27.0, 23.86, 30.0, 24.27)            # laundry (bifold)
    line(ax, [(27.0, 24.06), (27.75, 23.5), (28.5, 24.06), (29.25, 23.5), (30.0, 24.06)], lw=0.6, z=7)
    opening(ax, 37.48, 25.0, 37.9, 27.4)             # bath 2
    door(ax, (37.5, 25.0), 2.4, 90, 90)
    opening(ax, 40.65, 9.3, 41.02, 11.8)             # closet
    door(ax, (41.0, 9.3), 2.5, 0, 90)
    # stair (arrives at north landing)
    stair(ax, 41, 44.5, 13.3, 25.5, mode="down")
    # fixtures
    rect(ax, 22.9, 24.3, 25.45, 29.45, fc=PAPER, ec=FURN, lw=0.6, z=6)       # tub bath 1
    rect(ax, 23.2, 24.6, 25.15, 29.15, fc=PAPER, ec=FURN, lw=0.4, z=6)
    fixture_wc(ax, 21.2, 29.5)
    fixture_lav(ax, 16.5, 27.3, 18.3, 29.4)
    rect(ax, 26.0, 26.9, 28.4, 29.4, fc=PAPER, ec=FURN, lw=0.5, z=6)
    rect(ax, 28.55, 26.9, 30.95, 29.4, fc=PAPER, ec=FURN, lw=0.5, z=6)
    txt(ax, 27.2, 28.15, "W", size=5, color=GREY)
    txt(ax, 29.75, 28.15, "D", size=5, color=GREY)
    rect(ax, 31.45, 24.3, 34.4, 27.2, fc=PAPER, ec=FURN, lw=0.6, z=6)        # shower bath 2
    line(ax, [(31.45, 24.3), (34.4, 27.2)], lw=0.3, color=FURN, z=6)
    line(ax, [(31.45, 27.2), (34.4, 24.3)], lw=0.3, color=FURN, z=6)
    fixture_wc(ax, 32.6, 29.5)
    fixture_lav(ax, 35.4, 27.6, 37.4, 29.4)
    # WIC rods
    line(ax, [(9.9, 21), (9.9, 29)], lw=0.5, ls="--", color=FURN, z=6)
    line(ax, [(15.6, 23.6), (15.6, 29)], lw=0.5, ls="--", color=FURN, z=6)
    # beds
    rect(ax, 13.2, 9.2, 19.2, 15.9, fc="#f2f3f5", ec=FURN, lw=0.5, z=5)
    rect(ax, 13.2, 9.2, 19.2, 10.8, fc="#e4e6e9", ec=FURN, lw=0.4, z=6)
    rect(ax, 26.2, 9.2, 31.2, 15.9, fc="#f2f3f5", ec=FURN, lw=0.5, z=5)
    rect(ax, 26.2, 9.2, 31.2, 10.8, fc="#e4e6e9", ec=FURN, lw=0.4, z=6)
    rect(ax, 35, 9.0, 40, 11.2, fc="#f2f3f5", ec=FURN, lw=0.5, z=5)
    room(ax, 16.2, 18.6, "PRIMARY BEDROOM", "13'-6\" x 11'-6\"")
    room(ax, 28.7, 18.6, "BEDROOM 2", "10'-7\" x 11'-6\"")
    room(ax, 37.5, 15.2, "STUDY", "6'-4\" x 11'-6\"", fs=6.0)
    txt(ax, 12.75, 26.0, "WALK-IN\nCLOSET", size=5.2, weight="bold")
    txt(ax, 19.6, 25.6, "BATH 1", size=5.2, weight="bold")
    txt(ax, 28.5, 25.5, "LAUNDRY", size=5.0, weight="bold")
    txt(ax, 35.9, 25.4, "BATH 2", size=5.0, weight="bold", rot=0)
    txt(ax, 29, 22.1, "HALL", size=5.4, weight="bold")
    txt(ax, 42.75, 10.6, "CLOSET", size=4.6, color=GREY)
    dim(ax, (BX0, BY1), (BX1, BY1), 3.4, "36'-0\"")
    dim(ax, (BX1, BY0), (BX1, BY1), -7.6, "22'-0\"", side=-1)
    save(fig, "A-103", pdf)


# ----------------------------------------------------------------------------
def level_marks(ax, x, levels, left=False, x_line=None):
    for el, name in levels:
        if x_line is not None:
            line(ax, [x_line, (x, el)] if False else [(x_line, el), (x, el)], lw=0.35, color=GREY, ls=(0, (8, 3, 2, 3)), z=2)
        poly(ax, [(x, el), (x + 0.7, el + 0.7), (x + 1.4, el)], fc=INK, lw=0.3, z=8)
        txt(ax, x + 1.9, el + 0.55, f"{name}", size=5.4, ha="left", weight="bold")
        txt(ax, x + 1.9, el - 0.45, f"EL {el:.1f}", size=5.0, ha="left", color=GREY)


def sheet_a201(pdf):
    notes = [
        ("Street (south) elevation", [
            "Viewed from Baird Street looking north.",
            "Uphill (west, 442 Baird) is on the left.",
            "The pavement falls ±4 ft across the",
            "width of the building, so the lower",
            "level reads as a full storey at the east",
            "end and is half buried at the west.",
        ]),
        ("Design standards met (1337.07)", [
            "Garage is 22 ft of the 36 ft facade",
            "= 61 % (65 % max) and does not project",
            "past the main building line.",
            "Cladding: fibre-cement or vinyl siding",
            "over a masonry/concrete base.",
            "Gable roof to match neighbours.",
            "Street-facing porch across 72 % of the",
            "front.",
        ]),
        ("Height", [
            f"Garage slab                 EL {EL_GAR:.1f}",
            f"Main floor                   EL {EL_MAIN:.1f}",
            f"Upper floor                 EL {EL_UP:.1f}",
            f"Top plate                     EL {EL_PLATE:.1f}",
            f"Ridge                           EL {EL_RIDGE:.1f}",
            f"Zoning height {EL_MEAN_ROOF - EL_REF:.1f} ft to mean roof",
            "level (35 ft maximum).",
        ]),
        ("Not shown", [
            "East, west and north elevations are",
            "left for the architect. Neighbouring",
            "buildings are omitted for clarity.",
        ]),
    ]
    fig, bg = new_sheet("A-201", "Street elevation", "3/16\" = 1'-0\"", notes)
    xl, yl = (-6, 58), (903.5, 957.5)
    left = MARGIN + (SHEET_W - 2 * MARGIN - TB_W - (xl[1] - xl[0]) / FPI) / 2
    ax = plan_axes(fig, left, 0.5, xl, yl, FPI)
    # finished grade at the front wall line
    g = [(-6, elev(-6, BY0)), (2, elev(2, BY0)), (5.5, 921.0), (9, 920.6), (12.2, 919.6), (12.2, EL_GAR),
         (28.8, EL_GAR), (30.5, 914.9), (32.4, 913.2), (39.8, 913.0), (39.8, 916.2), (45, 917.0),
         (50, elev(50, BY0)), (58, elev(58, BY0))]
    poly(ax, g + [(58, 903.5), (-6, 903.5)], fc="#efe9e1", ec="none", z=6)
    line(ax, g, lw=1.4, color=INK, z=7)
    ax.fill_between([p[0] for p in g], [p[1] - 1.0 for p in g], [p[1] for p in g], hatch="////", fc="none", ec=EARTH, lw=0, zorder=6, alpha=0.6)
    # street pavement in front (dashed)
    sx = np.linspace(-6, 58, 30)
    line(ax, [(x, street_el(x)) for x in sx], lw=0.8, color=BLUE, ls=(0, (6, 3)), z=8)
    txt(ax, 49.5, street_el(49.5) - 1.3, "BAIRD ST PAVEMENT (IN FRONT) · FALLS ±11 % EASTWARD", size=5.0, color=BLUE, rot=-6.5)
    # lower level wall (masonry base)
    rect(ax, BX0, EL_GAR - 1.5, BX1, EL_MAIN, fc="#d9dcdf", ec=INK, lw=1.0, z=3)
    for y in np.arange(EL_GAR - 1.0, EL_MAIN, 0.667):
        line(ax, [(BX0, y), (BX1, y)], lw=0.15, color=GREY, z=3)
    # garage door
    rect(ax, 12.5, EL_GAR, 28.5, EL_GAR + 8, fc="#f6f6f4", ec=INK, lw=0.9, z=4)
    for y in np.arange(EL_GAR + 2, EL_GAR + 8, 2):
        line(ax, [(12.5, y), (28.5, y)], lw=0.4, z=4)
    for x in np.arange(16.5, 28.5, 4):
        line(ax, [(x, EL_GAR), (x, EL_GAR + 8)], lw=0.2, color=GREY, z=4)
    txt(ax, 20.5, EL_GAR + 4.9, "16' x 8' GARAGE DOOR", size=5.4, z=9)
    # loading door
    rect(ax, 33, EL_GAR, 39, EL_GAR + 7, fc="#f6f6f4", ec=INK, lw=0.9, z=4)
    for y in np.arange(EL_GAR + 1.75, EL_GAR + 7, 1.75):
        line(ax, [(33, y), (39, y)], lw=0.4, z=4)
    txt(ax, 36, EL_GAR + 4.3, "6' x 7'\nLOADING\nDOOR", size=4.8, z=9)
    dim(ax, (40.4, 913.0), (40.4, EL_GAR), 0, "2'-6\"", ext=False, size=4.8, color=BLUE, side=-1)
    # upper walls with lap siding
    rect(ax, BX0, EL_MAIN, BX1, EL_PLATE, fc="#fbfaf7", ec=INK, lw=1.0, z=3)
    for y in np.arange(EL_MAIN + 0.5, EL_PLATE, 0.5):
        line(ax, [(BX0, y), (BX1, y)], lw=0.12, color=LIGHT, z=3)
    line(ax, [(BX0, EL_UP), (BX1, EL_UP)], lw=0.5, z=4)
    # main level openings
    for (a, b) in ((13, 21), (28, 34)):
        rect(ax, a, EL_MAIN, b, EL_MAIN + 6.8, fc="#dfe7ee", ec=INK, lw=0.7, z=4)
        line(ax, [((a + b) / 2, EL_MAIN), ((a + b) / 2, EL_MAIN + 6.8)], lw=0.5, z=4)
    rect(ax, 36.5, EL_MAIN + 2.8, 39.5, EL_MAIN + 6.8, fc="#dfe7ee", ec=INK, lw=0.7, z=4)
    # upper windows
    for (a, b) in ((13, 19), (26, 31), (36, 39)):
        rect(ax, a, EL_UP + 2.6, b, EL_UP + 6.8, fc="#dfe7ee", ec=INK, lw=0.7, z=4)
        line(ax, [((a + b) / 2, EL_UP + 2.6), ((a + b) / 2, EL_UP + 6.8)], lw=0.5, z=4)
        line(ax, [(a, EL_UP + 4.7), (b, EL_UP + 4.7)], lw=0.3, z=4)
    # roof (ridge parallel to street)
    rect(ax, BX0 - 1, EL_PLATE - 0.4, BX1 + 1, EL_RIDGE, fc="#c9cdd2", ec=INK, lw=1.0, z=4)
    for y in np.arange(EL_PLATE, EL_RIDGE, 0.55):
        line(ax, [(BX0 - 1, y), (BX1 + 1, y)], lw=0.15, color=GREY, z=4)
    # porch
    rect(ax, 9, EL_MAIN - 0.9, 35, EL_MAIN, fc="#e9e4d9", ec=INK, lw=0.8, z=10)
    for px in (9.7, 18.2, 26.6, 34.4):
        rect(ax, px - 0.3, EL_MAIN, px + 0.3, EL_UP - 1.4, fc=PAPER, ec=INK, lw=0.6, z=10)
    for px in (9.7, 31.4):
        gy = EL_GAR if 12.2 < px < 29 else (919.9 if px < 12 else 914.3)
        rect(ax, px - 0.35, gy, px + 0.35, EL_MAIN - 0.9, fc=PAPER, ec=INK, lw=0.6, z=5)
    line(ax, [(9, EL_MAIN + 3), (35, EL_MAIN + 3)], lw=0.8, z=10)
    for x in np.arange(9.4, 35, 0.42):
        line(ax, [(x, EL_MAIN + 0.3), (x, EL_MAIN + 3)], lw=0.15, color=GREY, z=9)
    line(ax, [(9, EL_MAIN + 0.3), (35, EL_MAIN + 0.3)], lw=0.4, z=10)
    poly(ax, [(8.5, EL_UP - 1.4), (35.5, EL_UP - 1.4), (35.5, EL_UP - 0.2), (8.5, EL_UP - 0.2)], fc="#c9cdd2", ec=INK, lw=0.8, z=10)
    txt(ax, 22, EL_UP - 0.8, "PORCH ROOF", size=4.6, z=11)
    # entry steps at west side yard
    for i in range(10):
        y = 919.6 + i * 0.6
        rect(ax, 5.5, y, 9, y + 0.6, fc=PAPER, ec=GREY, lw=0.3, z=5 if i < 9 else 5)
    txt(ax, 2.4, 924.6, "ENTRY STEPS\n(BEYOND)", size=4.8, color=GREY)
    # lot lines
    for x in (0, 50):
        line(ax, [(x, 906), (x, 950.6)], color=ACCENT, lw=0.8, ls=(0, (9, 2.5, 1.5, 2.5)), z=12)
    txt(ax, 0.5, 949.6, "LOT LINE\n(SW CORNER)", size=4.8, color=ACCENT, ha="left")
    txt(ax, 49.5, 951.6, "LOT LINE (EAST)", size=4.8, color=ACCENT, ha="right")
    txt(ax, -3.2, 934, "442\nBAIRD ST", size=5.2, color=GREY)
    txt(ax, 54.8, 934, "441\nBAIRD ST", size=5.2, color=GREY)
    # levels
    level_marks(ax, 51.6, [(EL_MAIN, "MAIN FLOOR"), (EL_UP, "UPPER FLOOR"), (EL_PLATE, "TOP PLATE"), (EL_RIDGE, "RIDGE")], x_line=BX1)
    txt(ax, 20.5, EL_GAR - 1.3, f"GARAGE SLAB  EL {EL_GAR:.1f}", size=5.2, weight="bold", box=True, z=12)
    line(ax, [(20, EL_REF + 35), (BX1 + 3, EL_REF + 35)], color=ACCENT, lw=0.6, ls=(0, (4, 3)), z=12)
    txt(ax, 34, EL_REF + 35.8, f"35' ZONING HEIGHT LIMIT  (EL {EL_REF + 35:.1f}, from reference grade EL {EL_REF:.1f})", size=5.0, color=ACCENT)
    dim(ax, (BX0, EL_RIDGE), (BX1, EL_RIDGE), 1.6, "36'-0\"", size=5.4)
    dim(ax, (47.4, EL_GAR), (47.4, EL_MAIN), 0, "10'-0\"", ext=False, size=5.0)
    dim(ax, (47.4, EL_MAIN), (47.4, EL_UP), 0, "10'-0\"", ext=False, size=5.0)
    dim(ax, (47.4, EL_UP), (47.4, EL_PLATE), 0, "8'-1\"", ext=False, size=5.0)
    scale_bar(ax, -4.5, 905.6, 16, 4, 0.42, size=5.2)
    view_title(ax, -5.4, 954.6, "1", "South (Baird Street) elevation", "Looking north · elevations NAVD88 ft from state LiDAR", 9)
    save(fig, "A-201", pdf)


# ----------------------------------------------------------------------------
def sheet_a301(pdf):
    XS = 20.0
    ry = rear_y(XS)
    notes = [
        ("Section A-A", [
            "Cut north-south through the garage at",
            "plan station X = 20 ft, looking west.",
            "Street on the left, rear lot line right.",
            "Dashed brown = existing ground from",
            "the 1 m LiDAR (it includes the existing",
            "house terrace and bank).",
        ]),
        ("Why the under-garage works", [
            f"Existing ground rises from ±EL {elev(XS, -10):.0f} at",
            f"the pavement to ±EL {elev(XS, BY1):.0f} at the back of",
            "the footprint: 11 ft in 37 ft. Cutting the",
            "garage in at street level leaves the",
            "main floor level with the rear yard.",
        ]),
        ("Cost drivers visible here", [
            "±7 ft average cut over the footprint.",
            "Rear wall retains ±10 ft at this cut.",
            "Temporary shoring toward 386 Forest",
            "Ave, whose lot line is 13 ft behind the",
            "wall here and 5 ft at the NE corner.",
            "Rock depth is unknown: borings needed.",
            "Ask the geotech to check state mine",
            "maps for old workings under the site.",
        ]),
        ("Garage clearances", [
            "20'-4\" clear depth, 9'-0\" clear height,",
            "8'-0\" door. Check your longest vehicle",
            "and any ladder rack against these.",
        ]),
    ]
    fig, bg = new_sheet("A-301", "Building section", "3/16\" = 1'-0\"", notes)
    xl, yl = (-24, 46), (904.5, 958)
    left = MARGIN + (SHEET_W - 2 * MARGIN - TB_W - (xl[1] - xl[0]) / FPI) / 2
    ax = plan_axes(fig, left, 0.42, xl, yl, FPI)
    ys = np.arange(xl[0], xl[1] + 0.5, 1.0)
    eg = [(y, elev(XS, y)) for y in ys]
    # proposed finished grade
    st = street_el(XS)
    fg = [(xl[0], elev(XS, xl[0])), (PAVE_S, elev(XS, PAVE_S)), (PAVE_S, st), (PAVE_N, st), (BY0, EL_GAR), (BY0, EL_GAR - 1.5),
          (BY1, EL_GAR - 1.5), (BY1, EL_MAIN - 0.3)]
    fg += [(y, max(elev(XS, y), EL_MAIN - 0.3)) for y in np.arange(BY1 + 2, xl[1] + 1, 2)]
    poly(ax, fg + [(xl[1], 904.5), (xl[0], 904.5)], fc="#efe9e1", ec="none", z=2)
    line(ax, [(xl[0], elev(XS, xl[0])), (PAVE_S, elev(XS, PAVE_S))], lw=1.2, z=7)
    line(ax, [(PAVE_S, st), (PAVE_N, st)], lw=2.6, color="#3a3f45", z=7)
    line(ax, [(PAVE_N, st), (BY0, EL_GAR)], lw=1.4, z=7)
    line(ax, [(BY1, EL_MAIN - 0.3)] + fg[8:], lw=1.4, z=7)
    line(ax, eg, lw=0.9, color=EARTH, ls=(0, (5, 3)), z=8)
    txt(ax, 39.5, elev(XS, 39.5) + 1.6, "EXISTING GRADE", size=5.0, color=EARTH, rot=14)
    txt(ax, 3.2, elev(XS, 3.2) + 1.5, "EXISTING BANK +\nHOUSE TERRACE\n(REMOVED)", size=4.8, color=EARTH)
    txt(ax, -14, st - 1.2, "BAIRD STREET  ±14' PAVEMENT", size=5.4, weight="bold")
    txt(ax, -14, st - 2.4, f"±EL {st:.1f} at this section", size=4.8, color=GREY)
    txt(ax, 0.2, EL_GAR - 2.3, "APRON ±8 %", size=4.8, color=GREY)
    # slab + footings
    rect(ax, BY0, EL_GAR - 0.5, BY1 - 1, EL_GAR, fc=CONC, ec=INK, lw=0.6, z=5)
    rect(ax, BY0, EL_GAR - 1.0, BY1 - 1, EL_GAR - 0.5, fc="#e1ddd4", ec="none", z=4)
    rect(ax, BY0 - 0.5, EL_GAR - 2.5, BY0 + 1.5, EL_GAR - 1.5, fc=CONC, ec=INK, lw=0.6, z=5)
    rect(ax, BY0, EL_GAR - 1.5, BY0 + 0.67, EL_GAR, fc=CONC, ec=INK, lw=0.6, z=5)
    # rear retaining wall + footing
    rect(ax, BY1 - 1, EL_GAR - 1.5, BY1, EL_MAIN - 1.0, fc=CONC, ec=INK, lw=0.8, z=5)
    rect(ax, BY1 - 5.5, EL_GAR - 2.7, BY1 + 2.0, EL_GAR - 1.5, fc=CONC, ec=INK, lw=0.8, z=5)
    ax.add_patch(plt.Circle((BY1 + 0.6, EL_GAR - 1.1), 0.33, fc=PAPER, ec=BLUE, lw=0.8, zorder=6))
    rect(ax, BY1, EL_GAR - 1.5, BY1 + 1.2, EL_MAIN - 1.6, fc="#dcdfe3", ec="none", z=4, hatch="....")
    txt(ax, 34.6, 916.6, "12\" CONC. RETAINING WALL\n±10' retained · engineered\ndrainage board + footing drain", size=4.8, ha="left")
    line(ax, [(31.3, 917.5), (34.3, 917.2)], lw=0.3)
    # front wall above door, door opening
    rect(ax, BY0, EL_GAR + 8, BY0 + 0.67, EL_MAIN - 1.0, fc=CONC, ec=INK, lw=0.6, z=5)
    line(ax, [(BY0 + 0.33, EL_GAR), (BY0 + 0.33, EL_GAR + 8)], lw=0.6, ls=(0, (4, 2)), z=6)
    txt(ax, BY0 - 2.4, EL_GAR + 4.2, "8' DOOR", size=4.6, color=GREY, rot=90)
    # floors
    for el in (EL_MAIN, EL_UP):
        rect(ax, BY0, el - 1.0, BY1, el, fc="#e9e4d9", ec=INK, lw=0.7, z=5)
        for y in np.arange(BY0 + 1, BY1, 2.0):
            line(ax, [(y - 0.6, el - 1.0), (y, el - 0.5), (y + 0.6, el - 1.0)], lw=0.2, color=GREY, z=6)
    # frame walls
    for el0, el1 in ((EL_MAIN, EL_UP - 1.0), (EL_UP, EL_PLATE)):
        rect(ax, BY0, el0, BY0 + 0.5, el1, fc=POCHE, z=6)
        rect(ax, BY1 - 0.5, el0, BY1, el1, fc=POCHE, z=6)
    # openings in front wall (sliders / windows) shown as breaks
    rect(ax, BY0 - 0.02, EL_MAIN + 0.1, BY0 + 0.52, EL_MAIN + 6.8, fc=PAPER, ec=INK, lw=0.4, z=7)
    rect(ax, BY0 - 0.02, EL_UP + 2.6, BY0 + 0.52, EL_UP + 6.8, fc=PAPER, ec=INK, lw=0.4, z=7)
    rect(ax, BY1 - 0.52, EL_MAIN + 3.4, BY1 + 0.02, EL_MAIN + 6.8, fc=PAPER, ec=INK, lw=0.4, z=7)
    # ceiling + roof
    line(ax, [(BY0, EL_PLATE), (BY1, EL_PLATE)], lw=0.7, z=6)
    ym = (BY0 + BY1) / 2
    roof = [(BY0 - 1.2, EL_PLATE - 0.6), (ym, EL_RIDGE), (BY1 + 1.2, EL_PLATE - 0.6), (BY1 + 1.2, EL_PLATE - 0.1), (ym, EL_RIDGE + 0.6), (BY0 - 1.2, EL_PLATE - 0.1)]
    poly(ax, roof, fc="#c9cdd2", ec=INK, lw=0.8, z=6)
    txt(ax, ym, EL_PLATE + 2.0, "ATTIC / TRUSSES · 6:12", size=4.8, color=GREY)
    # porch
    rect(ax, 4, EL_MAIN - 0.9, BY0, EL_MAIN, fc="#e9e4d9", ec=INK, lw=0.7, z=6)
    rect(ax, 4.05, EL_MAIN, 4.55, EL_UP - 1.5, fc=PAPER, ec=INK, lw=0.5, z=6)
    line(ax, [(4.3, EL_MAIN + 3), (BY0, EL_MAIN + 3)], lw=0.5, z=6)
    poly(ax, [(3.4, EL_UP - 1.6), (BY0, EL_UP - 0.4), (BY0, EL_UP - 0.1), (3.4, EL_UP - 1.3)], fc="#c9cdd2", ec=INK, lw=0.6, z=6)
    txt(ax, 1.0, EL_MAIN + 5.2, "FRONT\nPORCH", size=4.8)
    # car silhouette
    cx = 10.2
    carp = [(cx, EL_GAR + 1.0), (cx + 0.3, EL_GAR + 2.6), (cx + 3.2, EL_GAR + 3.0), (cx + 5.0, EL_GAR + 4.8), (cx + 10.4, EL_GAR + 4.9),
            (cx + 12.6, EL_GAR + 3.3), (cx + 15.6, EL_GAR + 2.9), (cx + 16.2, EL_GAR + 1.0)]
    poly(ax, carp, fc="#f2f3f5", ec=FURN, lw=0.6, z=5)
    for wx in (cx + 3.1, cx + 12.8):
        ax.add_patch(plt.Circle((wx, EL_GAR + 1.05), 1.05, fc=PAPER, ec=FURN, lw=0.6, zorder=6))
    # labels
    txt(ax, 19, EL_GAR + 6.6, "GARAGE / STORAGE", size=6.2, weight="bold")
    txt(ax, 19, EL_MAIN + 4.6, "LIVING · DINING · KITCHEN", size=6.2, weight="bold")
    txt(ax, 19, EL_UP + 4.2, "BEDROOMS", size=6.2, weight="bold")
    txt(ax, 36.6, EL_MAIN + 4.6, "REAR PATIO\nAT GRADE", size=4.8)
    # lot lines
    for y, lab in ((0, "FRONT LOT LINE"), (ry, "REAR LOT LINE")):
        line(ax, [(y, 906), (y, 952.6)], color=ACCENT, lw=0.8, ls=(0, (9, 2.5, 1.5, 2.5)), z=12)
        txt(ax, y, 953.5, lab, size=4.8, color=ACCENT)
    dim(ax, (0, 908.6), (BY0, 908.6), 0, "8'-0\"", ext=False, size=5.0, color=ACCENT)
    dim(ax, (BY0, 908.6), (BY1, 908.6), 0, "22'-0\"", ext=False, size=5.0)
    dim(ax, (BY1, 908.6), (ry, 908.6), 0, f"{ftin(ry - BY1)}", ext=False, size=5.0, color=ACCENT)
    dim(ax, (PAVE_N, 908.6), (0, 908.6), 0, "±7' R.O.W.", ext=False, size=4.8, color=GREY)
    # levels
    level_marks(ax, -23.4, [(EL_GAR, "GARAGE SLAB"), (EL_MAIN, "MAIN FLOOR"), (EL_UP, "UPPER FLOOR"), (EL_PLATE, "TOP PLATE")])
    for el in (EL_GAR, EL_MAIN, EL_UP, EL_PLATE):
        line(ax, [(-22, el), (BY0 - 1.5 if el > EL_GAR else PAVE_N - 0.5, el)], lw=0.3, color=GREY, ls=(0, (8, 3, 2, 3)), z=3)
    line(ax, [(BY0 - 2, EL_REF + 35), (BY1 + 14, EL_REF + 35)], color=ACCENT, lw=0.6, ls=(0, (4, 3)), z=12)
    txt(ax, BY1 + 5, EL_REF + 35.9, f"35' ZONING HEIGHT LIMIT (EL {EL_REF + 35:.1f})", size=4.8, color=ACCENT)
    line(ax, [(BY1 + 3, EL_MEAN_ROOF), (BY1 + 9, EL_MEAN_ROOF)], lw=0.4, color=GREY)
    txt(ax, BY1 + 9.4, EL_MEAN_ROOF, f"MEAN ROOF EL {EL_MEAN_ROOF:.1f}\n= {EL_MEAN_ROOF - EL_REF:.1f} ft height", size=4.8, ha="left", color=GREY)
    dim(ax, (BY1 + 3.4, EL_GAR), (BY1 + 3.4, EL_MAIN), 0, "10'-0\"", ext=False, size=4.8, side=-1)
    dim(ax, (BY1 + 3.4, EL_MAIN), (BY1 + 3.4, EL_UP), 0, "10'-0\"", ext=False, size=4.8, side=-1)
    scale_bar(ax, -22.5, 906.3, 16, 4, 0.42, size=5.2)
    view_title(ax, -23.4, 955.6, "A", "Section A-A", "North-south through the garage, looking west", 9)
    save(fig, "A-301", pdf)


# ----------------------------------------------------------------------------
def mini_lower(ax, ox, oy, doors, cars, storage, title, lines, verdict, vcolor):
    k = ax.fpi / 8.0

    def R(x0, y0, x1, y1, **kw):
        rect(ax, ox + x0, oy + y0, ox + x1, oy + y1, **kw)
    R(0, 0, 36, 22, fc=CONC, ec=INK, lw=0.8, z=3)
    R(1, 0.67, 35, 21, fc=PAPER, ec=INK, lw=0.5, z=4)
    R(31.5, 5, 35, 21, fc="#eceef0", ec=GREY, lw=0.4, z=5)
    txt(ax, ox + 33.25, oy + 13, "STAIR", size=4.4, color=GREY, rot=90)
    for (a, b, lab) in doors:
        R(a, -0.05, b, 0.72, fc=PAPER, ec="none", z=5)
        line(ax, [(ox + a, oy + 0.33), (ox + b, oy + 0.33)], lw=0.6, ls=(0, (4, 2)), z=6)
        txt(ax, ox + (a + b) / 2, oy - 1.5 * k, lab, size=4.8)
    for (sx0, sy0, sx1, sy1, lab) in storage:
        R(sx0, sy0, sx1, sy1, fc="#f1e7d2", ec=FURN, lw=0.5, z=5, hatch="///")
        txt(ax, ox + (sx0 + sx1) / 2, oy + (sy0 + sy1) / 2, lab, size=4.8, weight="bold", box=True)
    for i, cx in enumerate(cars):
        car(ax, ox + cx, oy + 2.2, label=f"{i + 1}")
    txt(ax, ox, oy + 22 + 5.4 * k, title, size=7.4, weight="bold", ha="left")
    txt(ax, ox, oy + 22 + 3.0 * k, verdict, size=5.8, weight="bold", ha="left", color=vcolor)
    for i, ln in enumerate(lines):
        txt(ax, ox, oy - (4.6 + i * 1.8) * k, ln, size=5.5, ha="left")


def sheet_a401(pdf):
    notes = [
        ("How many cars?", [
            "On this lot, parking is only possible",
            "inside the building. The front yard is",
            "8 ft deep and the street is one lane",
            "(±14 ft) with no room to park on it, so",
            "there is no legal surface space.",
            "Realistic answer: 2 cars (as drawn),",
            "3 if storage is given up, 1 if storage",
            "is the priority.",
        ]),
        ("Zoning parking minimums", [
            "Single-family dwelling: 2 spaces.",
            "Two-family: 1.5 per unit (3 total).",
            "Stall size 8.5 ft x 18 ft.",
            "Option B needs a parking variance.",
            "A parking variance was requested for",
            "the adjoining 442 Baird St in 2024",
            "(VAR24-191), so the Board knows this",
            "block's constraints.",
        ]),
        ("Storage use: check first", [
            "R-2 allows storage that is accessory",
            "to the dwelling, indoors. A 'private",
            "garage' is defined as housing the",
            "occupants' automobiles, 'not",
            "commercial vehicles'. Stocking",
            "materials for other rental properties",
            "may be read as a contractor or",
            "warehouse use, which R-2 may not",
            "allow. Get the Planning Division's",
            "position in writing before buying.",
        ]),
    ]
    fig, bg = new_sheet("A-401", "Parking and storage options", "3/32\" = 1'-0\"", notes)
    fpi = 32 / 3.0
    xl, yl = (-4, 136), (0, 106)
    left = MARGIN + (SHEET_W - 2 * MARGIN - TB_W - (xl[1] - xl[0]) / fpi) / 2
    ax = plan_axes(fig, left, 0.48, xl, yl, fpi)
    view_title(ax, 0, 99, "1", "Lower-level options (same 36' x 22' shell)",
               "The level is a clear span, so the split between cars and storage can change without changing the building", 9)
    y0 = 58
    mini_lower(ax, 0, y0, [(3.5, 19.5, "16' door"), (24, 30, "6' loading door")], [4.3, 12.4],
               [(22.5, 0.9, 31.3, 20.8, "STORAGE\n177 sf")],
               "A · 2 CARS + STORAGE ROOM (as drawn)",
               ["2 cars side by side · 177 sf storage room", "+ 21 ft of shelving behind the cars", "Truck-bed-height loading door on the low side",
                "Meets the 2-space minimum for one dwelling"],
               "Recommended base scheme", "#1c6b3a")
    mini_lower(ax, 48, y0, [(3.5, 12.5, "9' door"), (17, 27, "10' loading door")], [4.6],
               [(13.5, 0.9, 31.3, 20.8, "STORAGE / WORKSHOP\n±370 sf")],
               "B · 1 CAR + LARGE STORAGE",
               ["1 car · ±370 sf storage / workshop", "Wide loading door, room for pallet racking", "1 space short of the 2 required",
                "Needs a parking variance from the BZA"],
               "Only with a parking variance", "#9a5b00")
    mini_lower(ax, 96, y0, [(2.5, 18.5, "16' door"), (20.5, 29.5, "9' door")], [3.3, 11.4, 21.9],
               [(1.2, 19.3, 31.3, 20.8, "SHELVING ONLY")],
               "C · 3 CARS, MINIMAL STORAGE",
               ["3 cars · storage limited to wall shelving", "Slab must drop ±1 ft (to ±EL 914.5) so the", "east door meets the falling street",
                "Garage fills the whole front: exceeds the", "65 % facade limit, needs relief"],
               "Possible, most zoning friction", "#9a5b00")
    ty = 24.0
    cols = [0, 40, 57, 76, 97]
    heads = ["", "Cars inside", "Storage floor", "Parking rule", "Extra approvals beyond setbacks"]
    rows = [("A · 2 cars + storage room", "2", "±177 sf + shelving", "Meets (2 required)", "None expected"),
            ("B · 1 car + large storage", "1", "±370 sf", "1 short", "Parking variance"),
            ("C · 3 cars", "3", "Shelving only", "Meets", "Garage-width relief; steeper apron")]
    line(ax, [(0, ty + 1.8), (134, ty + 1.8)], lw=0.8)
    for c, h in zip(cols, heads):
        txt(ax, c, ty + 3.6, h, size=6.0, weight="bold", ha="left")
    for i, r in enumerate(rows):
        yy = ty - i * 3.6
        for c, v in zip(cols, r):
            txt(ax, c, yy, v, size=6.0, ha="left", weight="bold" if c == 0 else "normal")
        line(ax, [(0, yy - 1.8), (134, yy - 1.8)], lw=0.3, color=LIGHT)
    txt(ax, 0, ty - 13.0, "All three options need the same rear-setback variance and the same front-setback determination. Surface or on-street parking: none available.",
        size=5.8, ha="left", color=GREY)
    save(fig, "A-401", pdf)
