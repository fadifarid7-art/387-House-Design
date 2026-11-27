"""390 Forest Ave: existing plan as checked against the 3D scan (left) and the proposed layout with the added bedroom and bathrooms (right).
Run: python3 existing/src/draw_proposed.py   Coordinates: building frame, feet. x runs north, y runs west (see the north arrow)."""
import math
import os

import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Arc, Ellipse, Rectangle

import draw_existing as de
import sheetx as sx
from sheetx import FIX, OPEN, CHECK, HERE, W, MG, TB, sheet, tag, picture, head, draw_floor, north, save
from common import INK, GREY, LIGHT, PAPER, ftin, table, plt

NEW = "#b3261e"; FXC = "#1f5fa8"; T2 = 1 / 6.0          # T2 = half of a 4 in. wall
EV = os.path.join(HERE, "data", "evidence")
FPI = 7.0


# ------------------------------------------------------------------ drawing helpers (all in feet)
def wall_v(ax, x, y0, y1):
    ax.add_patch(Rectangle((x - T2, min(y0, y1)), 2 * T2, abs(y1 - y0), fc=NEW, ec=NEW, lw=0.3, zorder=7))


def wall_h(ax, y, x0, x1):
    ax.add_patch(Rectangle((min(x0, x1), y - T2), abs(x1 - x0), 2 * T2, fc=NEW, ec=NEW, lw=0.3, zorder=7))


def erase(ax, x0, y0, x1, y1, show=True):
    """Take out an existing wall or door: white patch, dashed red outline."""
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc="#f7f8f9", ec="none", zorder=6.5))
    if show:
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, ec=NEW, lw=0.5, ls=(0, (2, 1.5)), zorder=6.6))


def door(ax, axis, w0, a0, a1, hinge, swing):
    """Door in a wall. axis 'h': wall runs along x at y=w0, opening from x=a0 to a1. hinge 'lo'/'hi' end; swing +1/-1 = side it opens to."""
    wd = a1 - a0; hp = a0 if hinge == "lo" else a1; d = 1 if hinge == "lo" else -1
    if axis == "h":
        ax.add_patch(Rectangle((a0, w0 - 0.22), wd, 0.44, fc=PAPER, ec="none", zorder=7.5))
        ax.plot([hp, hp], [w0, w0 + swing * wd], color=NEW, lw=0.9, zorder=8)
        t0 = 90 if swing > 0 else 270
        th = (t0 - 90, t0) if (d * swing) > 0 else (t0, t0 + 90)
        ax.add_patch(Arc((hp, w0), 2 * wd, 2 * wd, theta1=th[0], theta2=th[1], color=NEW, lw=0.5, zorder=8))
    else:
        ax.add_patch(Rectangle((w0 - 0.22, a0), 0.44, wd, fc=PAPER, ec="none", zorder=7.5))
        ax.plot([w0, w0 + swing * wd], [hp, hp], color=NEW, lw=0.9, zorder=8)
        t0 = 0 if swing > 0 else 180
        th = (t0, t0 + 90) if (d * swing) > 0 else (t0 - 90, t0)
        ax.add_patch(Arc((w0, hp), 2 * wd, 2 * wd, theta1=th[0], theta2=th[1], color=NEW, lw=0.5, zorder=8))


def tub(ax, x0, y0, x1, y1):
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc="white", ec=FXC, lw=0.8, zorder=8))
    ax.add_patch(Rectangle((x0 + 0.2, y0 + 0.2), x1 - x0 - 0.4, y1 - y0 - 0.4, fc="#eaf2fb", ec=FXC, lw=0.5, zorder=8.1))


def shower(ax, x0, y0, x1, y1):
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc="#eaf2fb", ec=FXC, lw=0.8, zorder=8))
    ax.plot([x0, x1], [y0, y1], color=FXC, lw=0.4, zorder=8.1); ax.plot([x0, x1], [y1, y0], color=FXC, lw=0.4, zorder=8.1)


def wc(ax, x, y, face):
    """Toilet centred on (x, y) at the wall; face = direction the bowl points: 'x+','x-','y+','y-'."""
    dx, dy = {"x+": (1, 0), "x-": (-1, 0), "y+": (0, 1), "y-": (0, -1)}[face]
    tx, ty = (0.67, 1.6) if dx else (1.6, 0.67)
    ax.add_patch(Rectangle((x - (0 if dx > 0 else tx if dx < 0 else tx / 2), y - (0 if dy > 0 else ty if dy < 0 else ty / 2)), tx, ty, fc="white", ec=FXC, lw=0.7, zorder=8))
    ax.add_patch(Ellipse((x + dx * 1.45, y + dy * 1.45), 1.5 if dx else 1.2, 1.2 if dx else 1.5, fc="white", ec=FXC, lw=0.7, zorder=8))


def lav(ax, x0, y0, x1, y1):
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc="white", ec=FXC, lw=0.7, zorder=8))
    ax.add_patch(Ellipse(((x0 + x1) / 2, (y0 + y1) / 2), (x1 - x0) * 0.6, (y1 - y0) * 0.6, fc="#eaf2fb", ec=FXC, lw=0.5, zorder=8.1))


def stack(ax, x, y):
    ax.add_patch(plt.Circle((x, y), 0.3, fc="white", ec=FXC, lw=1.0, zorder=9)); ax.text(x, y, "S", fontsize=4.2, color=FXC, ha="center", va="center", fontweight="bold", zorder=9.1)


def chimney(ax, x0, y0, x1, y1, removed=False):
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc="none" if removed else "#e9d8c8", ec=NEW if removed else "#7a4b2a", lw=0.8, ls=(0, (2, 1.5)) if removed else "-", hatch=None if removed else "xxx", zorder=6.8))


def label(ax, x, y, name, size=None, col=INK, fs=5.0):
    ax.text(x, y + (0.42 if size else 0), name.upper(), fontsize=fs, fontweight="bold", ha="center", va="center", color=col, zorder=12, bbox=dict(fc="white", ec="none", pad=0.5, alpha=0.85))
    if size:
        ax.text(x, y - 0.42, size, fontsize=fs - 0.9, ha="center", va="center", color=col, zorder=12, bbox=dict(fc="white", ec="none", pad=0.4, alpha=0.85))


def sz(w, d):
    return f"{ftin(round(w * 12) / 12)} x {ftin(round(d * 12) / 12)} · {w * d:.0f} sf"


def items(bg, x, y, rows, width, fs=5.9):
    import textwrap
    for t, col, s in rows:
        sx.tag_bg(bg, x + 0.13, y - 0.02, t, col)
        lines = textwrap.wrap(s, int(width * 16.5))
        for i, ln in enumerate(lines):
            bg.text(x + 0.36, y - i * 0.128, ln, fontsize=fs, va="center", color=INK)
        y -= 0.128 * len(lines) + 0.09
    return y


def level_sheet(pdf, number, title, fl, sub, view, notes, checks, news, opens, existing_extra, proposed):
    sx.KIND[:] = ["PROPOSED INTERIOR CHANGES", "EXISTING (CHECKED) / PROPOSED"]
    sx.LEGEND[:] = ["C = checked in the 3D scan · N = new work · U = confirm on site"]
    fig, bg = sheet(number, title, "390 Forest Ave", sub, notes)
    G, _ = sx.regularize(de.P390[str(fl)], de.T390(fl))
    (vx, vy) = view; fpi = max(FPI, (vx[1] - vx[0]) / 6.1)
    wplan = (vx[1] - vx[0]) / fpi; hplan = (vy[1] - vy[0]) / fpi
    head(bg, 0.6, 10.2, "Existing, checked against the 3D scan", "Walls, doors, windows and stairs compared with the scan slice and photo model · heights from each room's own floor", color=CHECK)
    head(bg, 6.95, 10.2, "Proposed layout", "Red = new walls and doors · red dashes = taken out · blue = new bathroom fixtures · grey = existing to remain", color=FIX)
    axL = sx.axes(fig, 0.55, 9.85 - hplan, vx, vy, fpi)
    draw_floor(axL, G, sx.IDENT, names=de.N390[fl], heights=de.heights390(fl), label_size=4.6)
    axR = sx.axes(fig, 6.9, 9.85 - hplan, vx, vy, fpi)
    for r in G["rooms"]:
        axR.fill([p[0] for p in r["pts"]], [p[1] for p in r["pts"]], fc="#f7f8f9", ec="none", zorder=1)
    draw_floor(axR, dict(G, rooms=[]), sx.IDENT, furniture=False, wall_fc="#8a9099")
    nv = de.FX["north_in_building_frame"]
    north(axL, vx[1] - 2.0, vy[1] - 2.2, nv, 1.2); sx.scale_bar(axL, vx[0] + 0.8, vy[0] + 0.7, 12, 4)
    existing_extra(axL); proposed(axR)
    for (t, p, _s) in checks:
        if p: tag(axL, p[0], p[1], t, CHECK, size=5.0)
    for (t, p, _s) in opens:
        if p: tag(axL if p[2:] != ("R",) else axR, p[0], p[1], t, OPEN, size=5.0)
    for (t, p, _s) in news:
        if p: tag(axR, p[0], p[1], t, FIX, size=5.0)
    yb = 9.85 - hplan - 0.25
    bg.plot([0.55, W - MG - TB - 0.2], [yb, yb], color=LIGHT, lw=0.6)
    y1 = items(bg, 0.6, yb - 0.25, [(t, CHECK, s) for (t, _p, s) in checks], 5.7)
    items(bg, 0.6, y1 - 0.05, [(t, OPEN, s) for (t, _p, s) in opens], 5.7)
    items(bg, 6.95, yb - 0.25, [(t, FIX, s) for (t, _p, s) in news], 5.9)
    save(fig, number, pdf)


HOW = ("How to read", ["Left: the house as it is, with every wall,", "door, window and stair checked in the scan.", "Right: the same level with the new work.",
                       "S = new drain stack, one line through all", "levels in the old chimney shaft.", "Sizes are clear, wall face to wall face.",
                       "Beams, joists and pipe sizes come later", "with the structural and plumbing design."])


# ================================================================== upper flat, main floor
def upper(pdf):
    def ex(ax):
        chimney(ax, 15.7, 6.2, 18.0, 9.2)
        ax.add_patch(Rectangle((16.9, 19.6), 2.95, 5.0, fill=False, ec=CHECK, lw=0.7, ls=(0, (3, 1.5)), zorder=9))
        ax.annotate("", xy=(18.4, 20.0), xytext=(18.4, 24.2), arrowprops=dict(arrowstyle="->", color=CHECK, lw=0.7), zorder=9)
        ax.text(18.4, 25.2, "UP from\nmiddle level", fontsize=3.8, color=CHECK, ha="center", va="center", zorder=12)

    def pr(ax):
        erase(ax, 18.14 - 0.2, 0.33, 18.14 + 0.2, 13.1)             # strip wall and closet door out
        erase(ax, 15.45 - 0.2, 0.4, 15.45 + 0.2, 3.67, show=False); wall_v(ax, 15.45, 0.33, 3.8)   # living-room closet opening closed
        chimney(ax, 15.7, 6.2, 18.0, 9.2, removed=True)
        # bedroom 4 = Room B carried 4 ft into the old Room A
        wall_h(ax, 8.94, 20.61, 31.35); wall_v(ax, 20.78, 8.77, 13.1)
        erase(ax, 20.6, 13.27 - 0.2, 23.5, 13.27 + 0.2, show=False); wall_h(ax, 13.27, 20.6, 23.7)   # old Room A door walled up
        erase(ax, 23.87, 13.27 - 0.2, 31.35, 13.27 + 0.2)           # wall between Room B and Room A out: beam over
        wall_h(ax, 13.27, 23.53, 23.9)
        ax.plot([23.1, 23.55, 23.1, 23.55, 23.1], [9.3, 10.2, 11.1, 12.0, 12.9], color=NEW, lw=0.7, zorder=8)       # closet folding door
        wall_v(ax, 23.1, 9.1, 9.3); wall_v(ax, 23.1, 12.9, 13.1)
        door(ax, "v", 23.7, 15.42, 17.75, "lo", 1)                  # door hung in the existing opening
        # bedroom 3 = rest of Room A + the old strip; entry and closet where the strip met the hall
        erase(ax, 18.0, 13.27 - 0.2, 20.5, 13.27 + 0.2, show=False); door(ax, "h", 13.27, 18.0, 20.5, "hi", -1)
        wall_v(ax, 17.79, 6.83, 9.0); wall_v(ax, 17.79, 12.6, 13.1); wall_h(ax, 6.83, 15.62, 17.96)
        ax.plot([17.79, 18.25, 17.79, 18.25, 17.79], [9.0, 9.9, 10.8, 11.7, 12.6], color=NEW, lw=0.7, zorder=8)
        stack(ax, 16.3, 7.6)
        label(ax, 27.6, 19.5, "Bedroom 4", "7'-6\" x 17'-9\" · 133 sf", NEW, 4.8); label(ax, 22.0, 11.1, "Clo.", None, NEW, 3.6)
        label(ax, 24.5, 4.6, "Bedroom 3", "15'-9\" x 8'-5\" · 133 sf\nplus entry 2'-8\" x 4'-4\"", NEW, 4.8); label(ax, 16.7, 10.3, "Clo.", None, NEW, 3.6)
        label(ax, 7.8, 6.7, "Living room", "15'-0\" x 12'-9\"", GREY, 4.6); label(ax, 3.9, 20.2, "Kitchen", None, GREY, 4.6); label(ax, 13.3, 22.3, "Bath 1", "existing", GREY, 4.4)
        label(ax, 20.2, 15.3, "Hall", None, GREY, 4.2)
    level_sheet(pdf, "PR-103", "390 Forest: upper flat, bedrooms 3 and 4", 5, "Rear building · upper flat main floor", ((-3, 36), (-3, 30)),
                [("This flat", ["Now: 3 bedrooms (Room A + two in the attic),", "1 bath.", "Proposed: 4 bedrooms, 3 baths:", "2 bedrooms + the existing bath here,", "2 bedrooms each with a private bath in", "the attic (PR-104)."]),
                 ("Bedroom 4, plainly", ["Room B cannot be made WIDER. One side is", "the outside wall; the other is the 3'-8\"", "passage to the attic stair.", "So it is made LONGER: 4 ft is taken from",
                                          "Room A, and the old closet strip is given", "back to Room A in exchange."]), HOW],
                [("C1", (18.4, 22.0), "Stair confirmed. This flat's own stair comes up from the middle level under the attic stair and arrives in the hall facing the bath door. The attic stair starts beside Room B's wall, turns at a platform under the window and runs back over the lower stair."),
                 ("C2", (16.8, 10.6), "Old U5: the 2'-8\" strip is two closets with a chimney between them (PR-105)."),
                 ("C3", (27.6, 23.5), "Room B today: 7'-6\" x 13'-5\" clear, ceiling 7'-2\", one window, a cased opening with no door."),
                 ("C4", (6.0, 25.6), "Every wall on the plan matches a wall surface in the scan within 3 in. Eight windows confirmed."),
                 ("C5", (13.3, 19.0), "Ceilings from the true floor: living room 8'-2\", Room A 8'-1\", bath 8'-3\"; kitchen, hall and Room B 7'-2\" to 7'-5\" (dropped ceilings).")],
                [("N1", (16.9, 7.9), "Chimney taken out from the roof down (confirm first that nothing vents into it). Its shaft carries one new drain stack S from the attic to the lower flat; on this floor it is boxed inside bedroom 3's closet."),
                 ("N2", (27.6, 13.3), "Wall between Room B and Room A removed for 7'-6\". A beam is needed here; size it with the structural design. This wall may carry the attic floor."),
                 ("N3", (27.6, 10.6), "Bedroom 4 grows from 7'-6\" x 13'-5\" (101 sf) to 7'-6\" x 17'-9\" (133 sf) and gains a 2 ft x 4 ft closet. A door is hung in its existing opening."),
                 ("N4", (26.0, 8.0), "New wall, 10'-7\" long, between bedroom 3 and bedroom 4."),
                 ("N5", (24.5, 2.2), "Bedroom 3 (old Room A): 13'-1\" x 12'-9\" becomes 15'-9\" x 8'-5\" (133 sf) because the closet strip and chimney space are added to it. Both windows stay."),
                 ("N6", (19.3, 7.4), "Bedroom 3's new door, 2'-6\", from the hall where the strip ended, with a 2 ft x 6 ft closet beside it. The old Room A door is walled up."),
                 ("N7", (14.3, 2.0), "The living-room closet opening is closed. The living room, kitchen and bath 1 are not touched.")],
                [("U2", (30.6, 20.5), "Bedroom 4's window scans at about 27 x 65 in. It must open at least 5.7 sf clear for escape; measure it. Bedroom 3's two windows the same."),
                 ("U13", (16.8, 4.9), "The middle 9 ft of the strip was never scanned. Open the closet door in Room A and look before pricing."),
                 ("U21", (30.2, 15.0), "Bedrooms 3 and 4 share bath 1 on this floor. A second bath here would cost bedroom 3 another 5 ft; say if you want it.")],
                ex, pr)


# ================================================================== attic
def attic(pdf):
    def ex(ax):
        chimney(ax, 15.9, 6.3, 18.3, 8.5)
        ax.annotate("", xy=(18.6, 17.3), xytext=(18.6, 23.5), arrowprops=dict(arrowstyle="->", color=CHECK, lw=0.7), zorder=9)
        ax.text(18.6, 24.6, "UP from\nupper flat", fontsize=3.8, color=CHECK, ha="center", va="center", zorder=12)

    def pr(ax):
        erase(ax, 15.5, 6.0, 18.6, 8.8, show=False); chimney(ax, 15.9, 6.3, 18.3, 8.5, removed=True)
        # private bath for bedroom 1, over the upper flat's bath 1
        wall_v(ax, 9.43, 15.56, 21.0); wall_h(ax, 15.73, 9.43, 16.7)
        door(ax, "h", 15.73, 9.9, 12.2, "hi", 1)
        tub(ax, 14.1, 15.9, 16.6, 20.9); wc(ax, 12.85, 21.0, "y-"); lav(ax, 9.6, 18.4, 11.35, 20.4)
        # private bath for bedroom 2, where the chimney was
        wall_v(ax, 16.7, 5.7, 8.8); wall_h(ax, 5.7, 15.7, 18.5); wall_h(ax, 6.2, 15.53, 16.87); wall_v(ax, 19.9, 5.53, 8.77)
        wall_h(ax, 8.6, 19.73, 22.34); wall_v(ax, 22.17, 8.43, 13.37); wall_h(ax, 13.2, 20.03, 22.34)
        erase(ax, 16.95, 13.0, 19.7, 13.4, show=False); wall_h(ax, 13.2, 16.87, 19.8)        # old bedroom 2 door walled up
        erase(ax, 20.0, 13.7, 20.4, 16.2, show=False); door(ax, "v", 20.2, 13.7, 16.2, "lo", 1)   # new bedroom 2 door off the landing
        door(ax, "v", 22.17, 9.1, 11.4, "lo", -1)
        shower(ax, 16.87, 5.87, 19.73, 8.5); wc(ax, 16.87, 11.75, "x+"); lav(ax, 19.5, 11.53, 21.3, 13.03); stack(ax, 17.2, 9.4)
        label(ax, 12.2, 17.0, "Bath A", "7'-0\" x 5'-1\"", NEW, 4.2); label(ax, 20.5, 10.0, "Bath B", None, NEW, 4.2)
        label(ax, 5.2, 13.5, "Attic bedroom 1", "16'-3\" x 7'-5\" + 8'-8\" x 5'-3\"\nplus dormer bay · 215 sf", NEW, 4.8)
        label(ax, 26.6, 14.8, "Attic bedroom 2", "11'-5\" x 11'-9\" plus\ndormer bay · 185 sf", NEW, 4.8)
    level_sheet(pdf, "PR-104", "390 Forest: attic, a private bath for each bedroom", 6, "Rear building · attic of the upper flat", ((-3, 36), (-3, 30)),
                [("This level", ["Two bedrooms stay. Each gets its own bath,", "entered only from that bedroom.", "Bath A sits over the upper flat's bath, so", "its drain drops into that bath's wall.",
                                 "Bath B sits where the chimney was, on the", "new stack S."]), HOW],
                [("C1", (18.6, 19.5), "Attic stair confirmed in the scan: it arrives at a landing between the two bedroom doors."),
                 ("C2", (17.1, 7.4), "The boxed-out corner between the two dormers is the chimney on its way to the roof."),
                 ("C3", (5.0, 18.5), "Headroom from the true floor: flat ceiling 7'-8\" to 8'-0\" across both rooms, below 7 ft only in the last 1 to 2 ft by the knee walls."),
                 ("C4", (25.5, 4.2), "Five windows confirmed: one in each dormer, one in each end wall, one on the stair. The small door in bedroom 2 leads into the roof space behind the knee wall.")],
                [("N8", (12.3, 19.4), "Bath A, private to bedroom 1, 7'-0\" x 5'-1\": 60 in. tub against the stair wall, toilet at the knee wall, sink. Door from inside bedroom 1."),
                 ("N9", (18.3, 7.2), "Bath B, private to bedroom 2: toilet and sink in a 5'-1\" x 4'-3\" room, with a 2'-10\" x 2'-8\" shower in the space the chimney leaves. Door from inside bedroom 2."),
                 ("N10", (21.6, 15.0), "Bedroom 2's door moves 3 ft round the corner of the landing, because the old doorway would open into bath B. The old doorway is walled up."),
                 ("N11", (16.2, 9.8), "The wall between the two bedrooms is carried on across the old chimney space.")],
                [("U14", (16.9, 14.4), "Bedroom 1's doorway off the landing reads as about 2 ft wide in the scan. Measure it."),
                 ("U15", (14.6, 21.6), "Headroom drops to about 6'-6\" in the last foot by the knee wall, where bath A's toilet tank goes, and to about 6'-8\" at the back of bath B's shower. Confirm both on site."),
                 ("U22", (20.9, 17.6), "The new bedroom 2 door is cut through the wall beside the stair's top landing. Check that the landing is at least 3 ft deep there.")],
                ex, pr)


# ================================================================== middle flat
def middle(pdf):
    def ex(ax):
        chimney(ax, 15.7, 6.2, 18.4, 9.3)
        ax.add_patch(Rectangle((15.45, 3.6), 3.3, 6.0, fill=False, ec=OPEN, lw=0.7, ls=(0, (3, 1.5)), zorder=9))
        ax.annotate("", xy=(20.6, 26.2), xytext=(24.6, 26.2), arrowprops=dict(arrowstyle="->", color=CHECK, lw=0.7), zorder=9)
        ax.annotate("", xy=(18.4, 21.6), xytext=(18.4, 24.4), arrowprops=dict(arrowstyle="->", color=CHECK, lw=0.7), zorder=9)
        ax.text(26.6, 26.2, "UP", fontsize=4.0, color=CHECK, ha="center", va="center", zorder=12)

    def pr(ax):
        erase(ax, 10.75, 6.25, 15.6, 6.7); erase(ax, 15.2, 6.4, 15.65, 9.75); erase(ax, 15.3, 9.4, 17.2, 9.8)   # old inner hall walls and door
        chimney(ax, 15.7, 6.2, 18.4, 9.3, removed=True)
        wall_h(ax, 8.77, 10.76, 18.73)
        erase(ax, 10.59 - 0.2, 7.82, 10.59 + 0.2, 12.75, show=False); wall_v(ax, 10.59, 7.82, 9.3); wall_v(ax, 10.59, 11.8, 12.75)
        door(ax, "v", 10.59, 9.3, 11.8, "lo", -1)                   # bedroom 2 door re-framed
        door(ax, "h", 8.77, 11.0, 13.5, "lo", -1)                   # bath 2 door
        tub(ax, 16.23, 3.61, 18.73, 8.61); wc(ax, 14.6, 3.61, "y+"); lav(ax, 11.2, 3.61, 13.2, 5.36); stack(ax, 15.6, 8.77)
        label(ax, 13.4, 7.0, "Bath 2", "8'-0\" x 5'-0\"", NEW, 4.4); label(ax, 13.8, 11.2, "Hall", "6'-3\" x 4'-4\"", NEW, 4.2)
        label(ax, 5.2, 7.0, "Bedroom 2", "unchanged", GREY, 4.8); label(ax, 4.5, 21.5, "Bedroom 1", "unchanged", GREY, 4.8); label(ax, 9.2, 16.0, "Bath 1", "existing", GREY, 4.2)
        label(ax, 26.5, 8.0, "Living room / kitchen", "unchanged", GREY, 4.8); label(ax, 25.5, 24.3, "Stair hall of the upper flat", None, GREY, 4.2)
    level_sheet(pdf, "PR-102", "390 Forest: middle flat, bath 2", 4, "Rear building · middle flat", ((-3, 37.6), (-3, 30)),
                [("This flat", ["Now: 2 bedrooms, 1 bath.", "Proposed: 2 bedrooms, 2 baths.", "The new bath takes the dead-end half of", "the hall outside bedroom 2 and the closed-in", "space around the chimney."]), HOW],
                [("C1", (22.5, 26.2), "Stair confirmed, and it is not this flat's: the stair hall on the north side is the upper flat's entrance. From the porch level it climbs along the outside wall to a landing 4'-5\" up, turns and goes on up."),
                 ("C2", (17.0, 5.0), "Closed-in space 3'-4\" x 6'-2\" between the hall and the living room, never scanned. The chimney stands in it (amber box); the rest is dead space or a sealed closet."),
                 ("C3", (31.9, 18.5), "Two outside doors on the porch side: a 4'-4\" wide door from the kitchen end and one in the bay. A porch floor shows outside at this level. The window in the bay's angled wall is confirmed; the bay is real."),
                 ("C4", (13.9, 15.2), "Inside doors confirmed: bath, bedroom 1, bedroom 2 (a 4'-11\" opening), a door across the hall and the closet. All walls match the scan within 3 in. except the items under U."),
                 ("C5", (5.2, 3.0), "Ceilings from the true floor: living room / kitchen and bedroom 2 are 8'-8\" with a dropped part at 7'-4\" to 7'-8\"; bedroom 1 7'-8\"; bath 7'-4\". Earlier I gave 7'-3\" and 8'-3\": the tall parts had been cut off.")],
                [("N1", (17.0, 7.6), "Chimney taken out through this level (see PR-103). The new drain stack S comes down here from the attic bath above and carries this bath too."),
                 ("N12", (13.4, 5.2), "Bath 2, 8'-0\" x 5'-0\": 60 in. tub across the far end, toilet and sink on the closet wall, door from the hall. Uses the south half of the hall and the closed-in space."),
                 ("N13", (9.4, 10.5), "Bedroom 2's 4'-11\" opening becomes a normal 2'-6\" door, moved clear of the new bath wall."),
                 ("N14", (15.9, 12.4), "The hall that is left, 6'-3\" x 4'-4\", still links the living room, bedroom 2 and the new bath. The old door across the hall and the short walls behind it go.")],
                [("U16", (17.0, 9.9), "What is in the closed-in space besides the chimney is unknown. Cut an inspection hole from the hall before pricing."),
                 ("U17", (18.6, 11.4), "Two short angled wall pieces at the hall / living room corner are still unexplained (scan rounding, or boxed pipes). Photo please."),
                 ("U9", (33.8, 2.0), "The outside wall at the south-east corner of the living room was not captured.")],
                ex, pr)


# ================================================================== lower flat
def lower(pdf):
    def ex(ax):
        chimney(ax, 16.4, 6.5, 18.0, 9.5)
        ax.add_patch(Rectangle((0.9, 12.95), 20.0, 14.0, fill=False, ec=CHECK, lw=0.7, ls=(0, (3, 1.5)), zorder=9))
        ax.text(10.5, 14.2, "this part of the floor is 1'-5\" lower", fontsize=4.0, color=CHECK, ha="center", zorder=12)

    def pr(ax):
        erase(ax, 13.3, 6.15, 16.45, 6.55); erase(ax, 16.05, 6.35, 16.45, 9.3); erase(ax, 16.0, 3.4, 18.3, 6.5, show=False)   # closet walls and the angled bits
        chimney(ax, 16.4, 6.5, 18.0, 9.5, removed=True)
        wall_v(ax, 17.68, 0.95, 9.45)
        erase(ax, 13.3, 9.45 - 0.2, 17.5, 9.45 + 0.2, show=False); wall_h(ax, 9.45, 13.27, 13.5); wall_h(ax, 9.45, 15.83, 17.85)
        door(ax, "h", 9.45, 13.5, 15.83, "lo", -1)
        shower(ax, 13.27, 0.95, 17.51, 3.95); wc(ax, 17.51, 5.5, "x-"); lav(ax, 16.0, 6.7, 17.51, 8.7); stack(ax, 17.68, 9.0)
        label(ax, 14.9, 5.0, "Bath 2", "4'-3\" x 8'-4\"", NEW, 4.2)
        label(ax, 7.2, 6.8, "Bedroom 1", "unchanged", GREY, 4.8); label(ax, 25.7, 21.0, "Bedroom 2", "unchanged", GREY, 4.8); label(ax, 21.1, 6.0, "Bath 1", "existing", GREY, 4.2)
        label(ax, 27.4, 8.6, "Laundry", "unchanged", GREY, 4.2); label(ax, 7.0, 20.0, "Living room", None, GREY, 4.8); label(ax, 17.0, 21.5, "Kitchen", None, GREY, 4.8)
    level_sheet(pdf, "PR-101", "390 Forest: lower flat, bath 2", 3, "Rear building · lower flat", ((-3, 36), (-3, 30)),
                [("This flat", ["Now: 2 bedrooms, 1 bath.", "Proposed: 2 bedrooms, 2 baths.", "The new bath replaces the two closets", "beside the existing bath, so both baths", "share one wall and the new stack.",
                                "The laundry stays: its outside door is", "the only way to that door, so a bath", "cannot go there after all."]), HOW],
                [("C1", (10.5, 20.5), "Two floor levels confirmed. The living room and kitchen are 1'-5\" lower than the bedrooms, bath, laundry and hall: there are two or three steps between them that the plan does not show."),
                 ("C2", (17.2, 8.0), "The small closed box beside the bath lines up with the chimney on the floors above: this is its base."),
                 ("C3", (29.6, 5.8), "Outside doors found in the scan: one from the laundry, one from bedroom 2, and a 2'-10\" opening in the living room wall. No stair connects this flat to the flats above."),
                 ("C4", (14.6, 7.8), "Closet off the hall: the scan shows a round tank-sized object in it, possibly the water heater."),
                 ("C5", (25.7, 17.5), "Ceilings from each room's own floor: living room 7'-6\", kitchen 6'-10\", bedroom 1 6'-10\", bedroom 2 7'-1\", bath 7'-0\", laundry 6'-10\". Several are under 7 ft.")],
                [("N1", (19.3, 10.9), "Chimney base taken out with the rest of the chimney. The new drain stack S from the baths above lands here, next to both baths of this flat."),
                 ("N15", (15.3, 2.4), "Bath 2, 4'-3\" x 8'-4\": 3 ft x 4'-3\" shower, toilet and sink on the wall shared with the existing bath, door from the hall. Replaces the hall closet and the closet behind it."),
                 ("N16", (14.7, 11.2), "The door is on the hall so both bedrooms can use it. It could open from bedroom 1 instead if you want a private bath.")],
                [("U18", (5.0, 3.0), "Bedroom 1 shows NO window in the scan. A bedroom needs a window you can climb out of. Check; a window may have been hidden by a curtain."),
                 ("U19", (15.3, 4.2), "If the round object in the closet is the water heater, it needs a new home (the laundry is the natural place) before this bath can be built."),
                 ("U3", (23.0, 1.2), "This flat's position under the others is good to about 12 in., so the stack line must be set out on site."),
                 ("U20", (24.5, 11.4), "Ceilings of 6'-10\" to 7'-1\" are existing. A new bath needs 6'-8\" at the fixtures, so it works, but mention it to the code office.")],
                ex, pr)


# ================================================================== summary + chimney evidence
def summary(pdf):
    sx.KIND[:] = ["PROPOSED INTERIOR CHANGES", "8 BEDROOMS · 7 BATHS · SUMMARY"]
    sx.LEGEND[:] = ["C = checked in the 3D scan · N = new work · U = confirm on site"]
    fig, bg = sheet("PR-001", "390 Forest: 8 bedrooms, 7 baths", "390 Forest Ave", "Rear building · all levels · issue 2", [
        ("Result", ["Lower flat   2 bed 1 bath -> 2 bed 2 bath", "Middle flat  2 bed 1 bath -> 2 bed 2 bath", "Upper flat   3 bed 1 bath -> 4 bed 3 bath", "Whole house  7 bed 3 bath -> 8 bed 7 bath"]),
        ("Changed since issue 1", ["Upper flat: no second bath on the main", "floor. Instead each attic bedroom gets a", "private bath.", "Bedroom 4 made 4 ft longer by re-framing", "the wall to Room A."]),
        ("One idea ties it together", ["The chimney runs up the middle of the", "house through all four levels. Taking it", "out frees its shaft for one new drain", "stack. Three of the four new baths sit",
                                       "against that shaft; the fourth sits over", "the upper flat's existing bath."]),
        ("Not done yet", ["Beams, joists, bearing walls, pipe sizes,", "vents, electrical, fire separation between", "flats, permits. 441 Baird St plans."]),
        ("Sheets", ["PR-101 lower flat", "PR-102 middle flat", "PR-103 upper flat", "PR-104 attic", "PR-105 chimney evidence"])])
    head(bg, 0.6, 10.2, "Bedrooms and baths, flat by flat", "Clear sizes, wall face to wall face. NEW = built or re-framed in this proposal", color=FIX)
    r2 = [["Flat", "Room", "Now", "Proposed", "Ceiling"],
          ["Lower", "Bedroom 1", "11'-8\" x 12'-2\", 142 sf", "unchanged", "6'-10\""],
          ["Lower", "Bedroom 2", "9'-6\" x 13'-3\", 113 sf", "unchanged", "7'-1\""],
          ["Lower", "Bath 1", "6'-9\" x 7'-6\", tub", "unchanged", "7'-0\""],
          ["Lower", "Bath 2  NEW", "two closets beside bath 1", "4'-3\" x 8'-4\", shower, door from the hall", "about 7'-0\""],
          ["Middle", "Bedroom 1", "150 sf (L-shaped)", "unchanged", "7'-8\""],
          ["Middle", "Bedroom 2", "10'-8\" x 13'-1\", 140 sf", "unchanged; door narrowed to 2'-6\"", "8'-8\""],
          ["Middle", "Bath 1", "6'-6\" x 5'-3\", tub", "unchanged", "7'-4\""],
          ["Middle", "Bath 2  NEW", "half of the hall + closed-in chimney space", "8'-0\" x 5'-0\", tub, door from the hall", "about 8'-0\""],
          ["Upper", "Bedroom 3 (Room A)  NEW", "13'-1\" x 12'-9\", 167 sf", "15'-9\" x 8'-5\", 133 sf + entry and closet", "8'-1\""],
          ["Upper", "Bedroom 4 (Room B)  NEW", "7'-6\" x 13'-5\", 101 sf, no door, no closet", "7'-6\" x 17'-9\", 133 sf + door + closet", "7'-2\" / 8'-1\""],
          ["Upper", "Bath 1", "6'-9\" x 10'-0\", tub", "unchanged; shared by bedrooms 3 and 4", "8'-3\""],
          ["Attic", "Bedroom 1", "257 sf", "about 215 sf", "7'-9\""],
          ["Attic", "Bath A  NEW", "corner of bedroom 1", "7'-0\" x 5'-1\", tub, private to bedroom 1", "7'-8\""],
          ["Attic", "Bedroom 2", "216 sf", "about 185 sf; door moved 3 ft", "7'-10\""],
          ["Attic", "Bath B  NEW", "chimney space + corner of bedroom 2", "5'-1\" x 4'-3\" + 2'-10\" x 2'-8\" shower, private to bedroom 2", "7'-8\""]]
    y2 = table(bg, 0.6, 9.8, [0.75, 2.2, 3.2, 4.2, 1.0], r2, fs=6.0, rh=0.215)
    head(bg, 0.6, y2 - 0.4, "Framing that changes", "Everything else stays as built", color=FIX)
    r3 = [["Where", "Taken out", "Built"],
          ["All levels", "Chimney, roof to lower flat; floors and roof patched", "One drain stack and vent in its shaft"],
          ["Lower flat", "Walls of the two closets beside bath 1", "Bath 2 walls and door"],
          ["Middle flat", "Door across the hall and the short walls behind it", "Bath 2 wall and door; bedroom 2 door re-framed"],
          ["Upper flat", "Closet-strip wall (13 ft); 7'-6\" of the wall between Room A and Room B, with a new beam; old Room A door", "10'-7\" wall between bedrooms 3 and 4; bedroom 3 door and two closets"],
          ["Attic", "Old bedroom 2 doorway (walled up)", "Bath A and bath B walls; new bedroom 2 door"]]
    y3 = table(bg, 0.6, y2 - 0.8, [1.1, 5.4, 4.85], r3, fs=6.0, rh=0.215)
    bg.text(0.6, y3 - 0.28, "Bedroom 4 cannot be made wider than 7'-6\": the outside wall is on one side and the 3'-8\" passage to the attic stair on the other. Making it wider means rebuilding that stair.\n"
            "Still to confirm before pricing: what is inside the chimney strip, whether the lower flat's hall closet holds the water heater, and a window in the lower flat's bedroom 1.", fontsize=6.2, va="top", color=INK, linespacing=1.4)
    save(fig, "PR-001", pdf)


def evidence(pdf):
    sx.KIND[:] = ["PROPOSED INTERIOR CHANGES", "EVIDENCE FOR THE CHIMNEY"]
    fig, bg = sheet("PR-105", "390 Forest: the U5 strip is a chimney between two closets", "390 Forest Ave", "Rear building · chimney", [
        ("Answer", ["The strip between the upper flat's living", "room and Room A is two closets with a", "chimney standing between them."]),
        ("Why I think so", ["1 The same closed-in spot, about 2'-4\" x", "  3'-0\", shows on all four levels, one", "  above the other.", "2 On the roof a box sits right above it,",
                            "  between the two dormers.", "3 Both room faces of the strip are flat", "  plaster with a closet door: nothing was", "  scanned inside the middle 9 ft."]),
        ("How sure", ["Likely, not proven. The roof box could be", "a capped chimney or a roof hatch. Opening", "the closet door in Room A settles it."]),
        ("If it is removed", ["Take it down from the top. Check first", "that no furnace, water heater or dryer", "still vents into it. The floors need", "patching where it passed through."])])
    head(bg, 0.6, 10.2, "1. Your aerial photo", "The box on 390's roof between the two dormers (circled)", color=CHECK)
    a = picture(fig, os.path.join(EV, "aerial_390.png"), 0.55, 6.2, 3.9, 3.75)
    a.add_patch(plt.Circle((338, 336), 44, fill=False, ec=NEW, lw=1.4)); a.text(338, 262, "box on roof", color=NEW, fontsize=6.5, ha="center", fontweight="bold")
    head(bg, 4.75, 10.2, "2. Room A's wall, from the photo model", "Flat plaster, a closed closet door at the left, a dresser. No fireplace or chimney breast shows in the room", color=CHECK)
    picture(fig, os.path.join(EV, "roomA_wall.png"), 4.7, 6.2, 4.3, 3.75)
    head(bg, 9.3, 10.2, "3. Upper flat from above (photo model)", "White gap between living room and Room A = never scanned", color=CHECK)
    b = picture(fig, os.path.join(EV, "top_upper.png"), 9.25, 6.2, 4.1, 3.75)
    b.add_patch(Rectangle((530, 470), 78, 300, fill=False, ec=NEW, lw=1.2))
    head(bg, 0.6, 5.75, "4. The same spot on every level", "3D scan sliced about 3 ft above each floor · red lines = Polycam's walls · coloured dots = scanned surfaces · the closed-in spot is at x 16 to 18, y 6 to 9 on each", color=CHECK)
    for i, (f, nm) in enumerate((("slice_lower.png", "Lower flat: closed box beside the bath"), ("slice_middle.png", "Middle flat: closed space between hall and living room"),
                                 ("slice_upper.png", "Upper flat: middle of the closet strip"), ("slice_attic.png", "Attic: boxed corner between the dormers"))):
        ax = picture(fig, os.path.join(EV, f), 0.55 + i * 3.2, 0.75, 3.05, 4.3)
        bg.text(0.55 + i * 3.2 + 1.52, 5.2, nm, fontsize=6.0, ha="center", color=INK, fontweight="bold")
        # the column, in picture pixels: x 9..25 ft over 840 px, y -2..16 ft over 945 px (axes inset roughly 30 px)
        fx = lambda v: 30 + (v - 9) / 16 * 790; fy = lambda v: 915 - (v + 2) / 18 * 880  # noqa: E731
        ax.add_patch(Rectangle((fx(15.7), fy(9.4)), fx(18.3) - fx(15.7), fy(6.2) - fy(9.4), fill=False, ec=OPEN, lw=1.3, ls=(0, (3, 1.5))))
    save(fig, "PR-105", pdf)


if __name__ == "__main__":
    out = os.path.join(HERE, "drawings", "390-Forest_8-Bed-7-Bath_Proposed.pdf")
    with PdfPages(out) as pdf:
        summary(pdf); lower(pdf); middle(pdf); upper(pdf); attic(pdf); evidence(pdf)
    print("wrote", out)
