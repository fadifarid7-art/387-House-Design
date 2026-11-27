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
        # bath 2 at the chimney column: clear 5'-0" x 8'-0"
        erase(ax, 18.14 - 0.2, 0.33, 18.14 + 0.2, 13.1)            # old strip wall and closet door
        erase(ax, 15.45 - 0.2, 0.4, 15.45 + 0.2, 3.67, show=False)  # living-room closet opening closed
        wall_v(ax, 15.45, 0.33, 3.8)
        chimney(ax, 15.7, 6.2, 18.0, 9.2, removed=True)
        wall_v(ax, 20.78, 0.33, 13.1); wall_h(ax, 4.94, 15.62, 20.62)
        erase(ax, 20.6, 13.27 - 0.2, 23.5, 13.27 + 0.2, show=False); wall_h(ax, 13.27, 20.6, 21.1); wall_h(ax, 13.27, 23.6, 23.7)
        door(ax, "h", 13.27, 21.1, 23.6, "hi", -1)                  # bedroom 3 door, moved 5 in.
        erase(ax, 17.9, 13.27 - 0.2, 20.4, 13.27 + 0.2, show=False); door(ax, "h", 13.27, 17.9, 20.4, "hi", -1)
        tub(ax, 15.62, 5.11, 20.62, 7.61); wc(ax, 15.62, 9.0, "x+"); lav(ax, 15.62, 10.85, 17.2, 12.35); stack(ax, 15.45, 8.0)
        door(ax, "v", 20.78, 1.0, 3.5, "lo", 1)                     # closet door from bedroom 3
        # closet for bedroom 4, taken from the old Room A
        wall_h(ax, 10.94, 23.7, 31.35); wall_v(ax, 23.7, 10.94, 13.27)
        erase(ax, 25.3, 13.27 - 0.2, 30.3, 13.27 + 0.2)
        ax.plot([25.3, 26.55, 27.8, 29.05, 30.3], [13.27, 13.9, 13.27, 13.9, 13.27], color=NEW, lw=0.7, zorder=8)
        door(ax, "v", 23.7, 15.42, 17.75, "lo", 1)                  # door hung in the existing opening
        label(ax, 18.1, 10.2, "Bath 2", "5'-0\" x 8'-0\"", NEW, 4.4); label(ax, 18.1, 2.6, "Closet", "5'-0\" x 4'-5\"", NEW, 4.2)
        label(ax, 26.2, 5.6, "Bedroom 3", sz(10.4, 10.44) + "\nplus entry 2'-7\" x 2'-4\"", NEW, 4.8)
        label(ax, 27.6, 20.2, "Bedroom 4", sz(7.82 - 0.33, 13.76 - 0.33), NEW, 4.8); label(ax, 27.5, 12.1, "Closet 2'-0\" x 7'-6\"", None, NEW, 3.8)
        label(ax, 7.8, 6.7, "Living room", "15'-0\" x 12'-9\"", GREY, 4.6); label(ax, 3.9, 20.2, "Kitchen", None, GREY, 4.6); label(ax, 13.3, 22.3, "Bath 1", "existing", GREY, 4.4)
        label(ax, 20.2, 15.3, "Hall", None, GREY, 4.2)
    level_sheet(pdf, "PR-103", "390 Forest: upper flat, bedroom 4 and bath 2", 5, "Rear building · upper flat main floor", ((-3, 36), (-3, 30)),
                [("This flat", ["Now: 3 bedrooms (Room A + two in the attic),", "1 bath.", "Proposed: 4 bedrooms, 3 baths.", "N1-N6 on this floor, N7-N9 in the attic."]), HOW],
                [("C1", (18.4, 22.0), "Stair confirmed. This flat's own stair comes up from the middle level under the attic stair and arrives in the hall facing the bath door. The attic stair starts beside it, turns at a landing and runs back over it. It is steep: about 1 ft up per 1 ft forward."),
                 ("C2", (16.8, 10.6), "Old U5 answered. The 2'-8\" strip is two closets with a chimney between them: an open closet off the living room, a closed closet door from Room A, and a chimney about 2'-4\" x 3'-0\" that also shows on the three other levels and on the roof (PR-105)."),
                 ("C3", (27.6, 23.5), "Room B checked as a bedroom: 7'-6\" x 13'-5\" clear (108 sf to wall centres), ceiling 7'-2\", one window. It meets the size rules today. It has a cased opening and no door. It cannot be made wider: the outside wall is on one side and the stair hall on the other."),
                 ("C4", (6.0, 25.6), "Walls, doors and windows: every wall on the plan matches a wall surface in the scan within 3 in. Eight windows confirmed. No wall is missing or extra on this level."),
                 ("C5", (13.3, 19.0), "Ceilings from the true floor: living room 8'-2\", Room A 8'-1\", bath 8'-3\"; kitchen, hall and Room B 7'-2\" to 7'-5\" (dropped ceilings). My earlier figures for this flat were 1'-2\" to 1'-5\" too tall.")],
                [("N1", (16.9, 7.6), "Take out the chimney from the roof down (confirm first that nothing still vents into it). Its shaft becomes the pipe space for one new drain stack serving the new baths on all levels."),
                 ("N2", (19.0, 8.6), "Bath 2, 5'-0\" x 8'-0\": 60 in. tub, toilet and sink, door from the hall. Built from the closet strip plus 2'-8\" of Room A."),
                 ("N3", (26.2, 2.4), "Bedroom 3 (old Room A) becomes 10'-5\" x 10'-5\" with a 5'-0\" x 4'-5\" closet. Both windows stay. Door moves 5 in."),
                 ("N4", (27.6, 17.2), "Bedroom 4 (old Room B): keeps its full 7'-6\" x 13'-5\". A door is hung in the existing opening."),
                 ("N5", (29.4, 12.1), "New closet for bedroom 4, 2'-0\" x 7'-6\" with a 5 ft folding door, taken from Room A's side so bedroom 4 loses no floor."),
                 ("N6", (14.6, 2.0), "The living-room closet opening is closed; that space becomes bedroom 3's closet.")],
                [("U2", (30.6, 20.5), "Bedroom 4's window scans at about 27 x 65 in. It must open at least 5.7 sf clear for escape; measure it. Bedroom 3's two windows the same."),
                 ("U13", (16.8, 4.9), "The middle 9 ft of the strip was never scanned. Open the closet door in Room A and look: chimney size, any flue or pipe still in use.")],
                ex, pr)


# ================================================================== attic
def attic(pdf):
    def ex(ax):
        chimney(ax, 15.9, 6.3, 18.3, 8.5)
        ax.annotate("", xy=(18.6, 17.3), xytext=(18.6, 23.5), arrowprops=dict(arrowstyle="->", color=CHECK, lw=0.7), zorder=9)
        ax.text(18.6, 24.6, "UP from\nupper flat", fontsize=3.8, color=CHECK, ha="center", va="center", zorder=12)

    def pr(ax):
        chimney(ax, 15.9, 6.3, 18.3, 8.5, removed=True)
        wall_v(ax, 9.43, 12.4, 21.0); wall_h(ax, 12.4, 9.43, 16.55); wall_h(ax, 15.73, 9.43, 16.7)
        door(ax, "v", 9.43, 12.75, 15.25, "lo", -1)                 # bedroom 1 door
        door(ax, "h", 15.73, 9.9, 12.2, "hi", 1)                    # bath door
        tub(ax, 14.1, 15.9, 16.6, 20.9); wc(ax, 12.85, 21.0, "y-"); lav(ax, 9.6, 18.4, 11.35, 20.4); stack(ax, 16.3, 21.6)
        label(ax, 12.3, 17.4, "Bath 3", "7'-0\" x 5'-1\"", NEW, 4.2); label(ax, 13.1, 14.1, "Landing 3'-0\" wide", None, NEW, 3.8)
        label(ax, 4.9, 15.0, "Attic bedroom 1", sz(8.67, 12.8) + "\nplus dormer bay 5'-8\" x 5'-9\"", NEW, 4.8); label(ax, 13.0, 10.3, "Closet alcove", "7'-0\" x 3'-7\"", NEW, 4.0)
        label(ax, 25.5, 14.5, "Attic bedroom 2", "unchanged · 216 sf", GREY, 4.8)
    level_sheet(pdf, "PR-104", "390 Forest: attic, bath 3", 6, "Rear building · attic of the upper flat", ((-3, 36), (-3, 30)),
                [("This level", ["Two bedrooms stay. A bath is added beside", "the stair so neither bedroom is a way", "through to it.", "It sits over the upper flat's existing bath,", "so its drain drops into that bath's wall."]), HOW],
                [("C1", (18.6, 19.5), "Attic stair confirmed in the scan: it arrives at a landing between the two bedroom doors."),
                 ("C2", (17.1, 7.4), "The boxed-out corner between the two dormers is the chimney on its way to the roof. Nobody scanned inside it."),
                 ("C3", (5.0, 18.5), "Headroom from the true floor: flat ceiling 7'-8\" to 8'-0\" across both rooms, below 7 ft only in the last 1 to 2 ft by the knee walls. Corrected: I gave 7'-11\" to 9'-4\" before."),
                 ("C4", (25.5, 4.2), "Five windows confirmed: one in each dormer, one in each end wall, one on the stair. The small door in bedroom 2 leads into the roof space behind the knee wall.")],
                [("N7", (12.3, 19.6), "Bath 3, 7'-0\" x 5'-1\": 60 in. tub against the stair wall, toilet at the knee wall, sink. Ceiling over the tub's shower end is 7'-8\"."),
                 ("N8", (7.9, 13.9), "New wall and door for bedroom 1, set back so a 3'-0\" landing leads from the stair to both the bedroom and the bath."),
                 ("N9", (13.0, 8.9), "The corner left behind the landing becomes bedroom 1's closet alcove. With the chimney gone it gains about 2 ft.")],
                [("U14", (16.9, 14.2), "Bedroom 1's doorway off the landing reads as about 2 ft wide in the scan. Measure it; the new landing needs 3 ft."),
                 ("U15", (15.4, 20.3), "Headroom drops to about 6'-6\" in the last foot by the knee wall, where the toilet tank goes. Fine for a toilet; confirm on site.")],
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
                [("N1", (17.0, 7.6), "Chimney taken out through this level (see PR-103). The new drain stack S comes down here from the upper flat's bath 2 and carries this bath too."),
                 ("N10", (13.4, 5.2), "Bath 2, 8'-0\" x 5'-0\": 60 in. tub across the far end, toilet and sink on the closet wall, door from the hall. Uses the south half of the hall and the closed-in space."),
                 ("N11", (9.4, 10.5), "Bedroom 2's 4'-11\" opening becomes a normal 2'-6\" door, moved clear of the new bath wall."),
                 ("N12", (15.9, 12.4), "The hall that is left, 6'-3\" x 4'-4\", still links the living room, bedroom 2 and the new bath. The old door across the hall and the short walls behind it go.")],
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
                [("N1", (19.3, 10.9), "Chimney base taken out with the rest of the chimney. The new drain stack S from the two baths above lands here, next to both baths of this flat."),
                 ("N13", (15.3, 2.4), "Bath 2, 4'-3\" x 8'-4\": 3 ft x 4'-3\" shower, toilet and sink on the wall shared with the existing bath, door from the hall. Replaces the hall closet and the closet behind it."),
                 ("N14", (14.7, 11.2), "The door is on the hall so both bedrooms can use it. It could open from bedroom 1 instead if you want a private bath.")],
                [("U18", (5.0, 3.0), "Bedroom 1 shows NO window in the scan. A bedroom needs a window you can climb out of. Check; a window may have been hidden by a curtain."),
                 ("U19", (15.3, 4.2), "If the round object in the closet is the water heater, it needs a new home (the laundry is the natural place) before this bath can be built."),
                 ("U3", (23.0, 1.2), "This flat's position under the others is good to about 12 in., so the stack line must be set out on site."),
                 ("U20", (24.5, 11.4), "Ceilings of 6'-10\" to 7'-1\" are existing. A new bath needs 6'-8\" at the fixtures, so it works, but mention it to the code office.")],
                ex, pr)


# ================================================================== summary + chimney evidence
def summary(pdf):
    sx.KIND[:] = ["PROPOSED INTERIOR CHANGES", "CHECK RESULTS AND SUMMARY"]
    sx.LEGEND[:] = ["C = checked in the 3D scan · N = new work · U = confirm on site"]
    fig, bg = sheet("PR-001", "390 Forest: check results and what is proposed", "390 Forest Ave", "Rear building · all levels", [
        ("Result", ["Lower flat   2 bed 1 bath -> 2 bed 2 bath", "Middle flat  2 bed 1 bath -> 2 bed 2 bath", "Upper flat   3 bed 1 bath -> 4 bed 3 bath", "Whole house  7 bed 3 bath -> 8 bed 6 bath"]),
        ("One idea ties it together", ["The chimney runs up the middle of the", "house through all four levels. Taking it", "out frees its shaft for one new drain", "stack, and three of the four new baths", "sit right against that shaft.",
                                       "The attic bath sits over the upper flat's", "existing bath and uses its drain."]),
        ("Not done yet", ["Beams, joists, bearing walls, pipe sizes,", "vents, electrical, fire separation between", "flats, permits. 441 Baird St plans."]),
        ("Sheets", ["PR-101 lower flat", "PR-102 middle flat", "PR-103 upper flat", "PR-104 attic", "PR-105 chimney evidence"])])
    head(bg, 0.6, 10.2, "What the check found", "Every level compared with the 3D scan slice, the photo model and your aerial photo", color=CHECK)
    rows = [["Item", "Result", "Sheet"],
            ["Inside walls", "All four levels match the scan within about 3 in. No missing or extra walls. Three spots still unexplained (U16, U17, lower flat closet).", "all"],
            ["Stairs", "One inside stair: from the porch-level stair hall (middle level) up to the upper flat, then on to the attic, one flight over the other. The lower and middle flats have no inside stair.", "102-104"],
            ["Chimney", "One, in the middle of the house, about 2'-4\" x 3'-0\". Closed in on every level; seen on the roof in your aerial photo.", "105"],
            ["Old U5 strip", "Two closets with the chimney between them. Not a stair.", "103, 105"],
            ["Windows", "390 lower flat 3, middle flat 5, upper flat 8, attic 5: all confirmed. Lower flat bedroom 1 shows none (U18).", "all"],
            ["Doors", "All confirmed. Upper flat Room B has an opening with no door. Middle flat bedroom 2 has a 4'-11\" opening.", "all"],
            ["Floor levels", "Lower flat has two floor levels 1'-5\" apart. Floor to floor: 9'-5\", 10'-1\", 9'-4\"; attic ceiling 7'-9\".", "101"],
            ["Ceiling heights", "CORRECTED. Upper flat and attic were 1'-2\" to 1'-5\" too tall in my last set: I had measured from the ceiling of the flat below. Now from each room's own floor.", "all"]]
    y = table(bg, 0.6, 9.8, [1.15, 9.3, 0.85], rows, fs=6.0, rh=0.34)
    head(bg, 0.6, y - 0.4, "Rooms after the changes", "Clear sizes. Grey rows are unchanged rooms", color=FIX)
    r2 = [["Flat", "Room", "Now", "Proposed", "Ceiling"],
          ["Lower", "Bath 2 (new)", "two closets", "4'-3\" x 8'-4\", shower", "about 7'-0\""],
          ["Middle", "Bath 2 (new)", "half of the hall + closed space", "8'-0\" x 5'-0\", tub", "about 8'-0\""],
          ["Middle", "Hall", "8'-4\" x 10'-0\"", "6'-3\" x 4'-4\"", ""],
          ["Upper", "Bedroom 3 (Room A)", "13'-1\" x 12'-9\", 175 sf", "10'-5\" x 10'-5\" + closet 5'-0\" x 4'-5\"", "8'-1\""],
          ["Upper", "Bedroom 4 (Room B)", "7'-6\" x 13'-5\", no door, no closet", "7'-6\" x 13'-5\" + door + closet 2'-0\" x 7'-6\"", "7'-2\""],
          ["Upper", "Bath 2 (new)", "closet strip + chimney", "5'-0\" x 8'-0\", tub", "8'-1\""],
          ["Attic", "Bath 3 (new)", "corner of bedroom 1", "7'-0\" x 5'-1\", tub", "7'-8\""],
          ["Attic", "Bedroom 1", "257 sf", "8'-8\" x 12'-10\" + dormer bay + closet alcove, about 170 sf", "7'-9\""],
          ["Attic", "Bedroom 2", "216 sf", "unchanged", "7'-10\""]]
    y2 = table(bg, 0.6, y - 0.8, [0.8, 2.0, 3.2, 4.2, 1.1], r2, fs=6.0, rh=0.215)
    bg.text(0.6, y2 - 0.3, "Bedroom 4 cannot be made wider: an outside wall is on one side and the stair hall on the other. It is already a legal bedroom size, so the changes are a door and a closet.\n"
            "If you would rather have a bigger bedroom 4 and a smaller bedroom 3, the wall between them can move instead of building the closet there; say so and I will redraw it.", fontsize=6.2, va="top", color=INK, linespacing=1.4)
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
    out = os.path.join(HERE, "drawings", "390-Forest_Proposed-Bedroom-and-Baths.pdf")
    with PdfPages(out) as pdf:
        summary(pdf); lower(pdf); middle(pdf); upper(pdf); attic(pdf); evidence(pdf)
    print("wrote", out)
