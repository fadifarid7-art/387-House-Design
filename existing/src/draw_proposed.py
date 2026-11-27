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


FIXC = "#b9770e"


def fixw_v(ax, x, y0, y1):
    """Wall the scan missed, drawn in to close the outline (amber edge = confirm on site)."""
    ax.add_patch(Rectangle((x - T2, min(y0, y1)), 2 * T2, abs(y1 - y0), fc="#8a9099", ec=FIXC, lw=0.7, zorder=6.9))


def fixw_h(ax, y, x0, x1):
    ax.add_patch(Rectangle((min(x0, x1), y - T2), abs(x1 - x0), 2 * T2, fc="#8a9099", ec=FIXC, lw=0.7, zorder=6.9))


def bed(ax, hx, hy, face, name="KING"):
    """King bed 6'-4" x 6'-8". (hx, hy) = middle of the headboard on the wall; face = way the bed points."""
    Wd, L = 6.33, 6.67
    dx, dy = {"x+": (1, 0), "x-": (-1, 0), "y+": (0, 1), "y-": (0, -1)}[face]
    if dx:
        x0, y0, w, h = (hx if dx > 0 else hx - L), hy - Wd / 2, L, Wd
    else:
        x0, y0, w, h = hx - Wd / 2, (hy if dy > 0 else hy - L), Wd, L
    ax.add_patch(Rectangle((x0, y0), w, h, fc="#fbf3e6", ec="#7a5a2a", lw=0.7, zorder=7.2))
    for s in (-1, 1):                                   # pillows
        if dx:
            ax.add_patch(Rectangle((hx + dx * 0.25 - (0 if dx > 0 else 1.5), hy + s * 1.6 - 1.25), 1.5, 2.5, fc="white", ec="#7a5a2a", lw=0.4, zorder=7.3))
        else:
            ax.add_patch(Rectangle((hx + s * 1.6 - 1.25, hy + dy * 0.25 - (0 if dy > 0 else 1.5)), 2.5, 1.5, fc="white", ec="#7a5a2a", lw=0.4, zorder=7.3))
    ax.text(x0 + w / 2 + dx * 0.6, y0 + h / 2 + dy * 0.6, name + "\n6'-4\" x 6'-8\"", fontsize=3.6, color="#7a5a2a", ha="center", va="center", zorder=7.4, linespacing=1.2)


def couch(ax, x0, y0, x1, y1, back):
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc="#eef0f2", ec="#5b6470", lw=0.7, zorder=7.2))
    b = 0.7
    r = {"x-": (x0, y0, b, y1 - y0), "x+": (x1 - b, y0, b, y1 - y0), "y-": (x0, y0, x1 - x0, b), "y+": (x0, y1 - b, x1 - x0, b)}[back]
    ax.add_patch(Rectangle(r[:2], r[2], r[3], fc="#d5d9de", ec="#5b6470", lw=0.5, zorder=7.3))
    ax.text((x0 + x1) / 2, (y0 + y1) / 2, "COUCH", fontsize=3.4, color="#5b6470", ha="center", va="center", zorder=7.4, rotation=90 if (y1 - y0) > (x1 - x0) else 0)


def box(ax, x0, y0, x1, y1, name, col="#5b6470"):
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc="white", ec=col, lw=0.7, zorder=7.2))
    ax.text((x0 + x1) / 2, (y0 + y1) / 2, name, fontsize=3.2, color=col, ha="center", va="center", zorder=7.4)


def mech(ax, ahx, ahy, whx, why, wd=None):
    """Air handler 24 x 24 in. and 50 gal water heater 24 in. across; optional stacked washer/dryer 27 x 30 in."""
    ax.add_patch(Rectangle((ahx - 1, ahy - 1), 2, 2, fc="#f3e9f7", ec="#6a2c91", lw=0.8, zorder=7.2))
    ax.plot([ahx - 1, ahx + 1], [ahy - 1, ahy + 1], color="#6a2c91", lw=0.4, zorder=7.3); ax.plot([ahx - 1, ahx + 1], [ahy + 1, ahy - 1], color="#6a2c91", lw=0.4, zorder=7.3)
    ax.text(ahx, ahy, "AH", fontsize=3.6, color="#6a2c91", ha="center", va="center", fontweight="bold", zorder=7.5, bbox=dict(fc="#f3e9f7", ec="none", pad=0.3))
    ax.add_patch(plt.Circle((whx, why), 1.0, fc="#f3e9f7", ec="#6a2c91", lw=0.8, zorder=7.2))
    ax.text(whx, why, "WH", fontsize=3.6, color="#6a2c91", ha="center", va="center", fontweight="bold", zorder=7.5)
    if wd:
        box(ax, wd[0], wd[1], wd[0] + 2.25, wd[1] + 2.5, "W/D", "#6a2c91")


def closet(ax, x0, y0, x1, y1, front, ends=(True, True), name="CLO."):
    """New closet: front wall with folding doors on side `front`, optional end walls, rod shown dashed."""
    if front in ("y+", "y-"):
        yf = y1 if front == "y+" else y0
        a, b = x0 + 0.12 * (x1 - x0), x1 - 0.12 * (x1 - x0)
        wall_h(ax, yf, x0 - T2, a); wall_h(ax, yf, b, x1 + T2)
        n = 4; xs = np.linspace(a, b, n + 1); s = 0.45 * (1 if front == "y+" else -1)
        ax.plot(xs, [yf + (s if i % 2 else 0) for i in range(n + 1)], color=NEW, lw=0.7, zorder=8)
        if ends[0]: wall_v(ax, x0 - T2, y0, y1)
        if ends[1]: wall_v(ax, x1 + T2, y0, y1)
        ax.plot([x0 + 0.2, x1 - 0.2], [(y0 + y1) / 2] * 2, color=NEW, lw=0.4, ls=(0, (3, 2)), zorder=7.4)
    else:
        xf = x1 if front == "x+" else x0
        a, b = y0 + 0.12 * (y1 - y0), y1 - 0.12 * (y1 - y0)
        wall_v(ax, xf, y0 - T2, a); wall_v(ax, xf, b, y1 + T2)
        n = 4; ys = np.linspace(a, b, n + 1); s = 0.45 * (1 if front == "x+" else -1)
        ax.plot([xf + (s if i % 2 else 0) for i in range(n + 1)], ys, color=NEW, lw=0.7, zorder=8)
        if ends[0]: wall_h(ax, y0 - T2, x0, x1)
        if ends[1]: wall_h(ax, y1 + T2, x0, x1)
        ax.plot([(x0 + x1) / 2] * 2, [y0 + 0.2, y1 - 0.2], color=NEW, lw=0.4, ls=(0, (3, 2)), zorder=7.4)
    ax.text((x0 + x1) / 2, (y0 + y1) / 2, name, fontsize=3.4, color=NEW, ha="center", va="center", fontweight="bold", zorder=7.6, bbox=dict(fc="white", ec="none", pad=0.2, alpha=0.8))


def dim(ax, x0, y0, x1, y1, off=0.0):
    """Dimension between two points on a horizontal or vertical line, text = distance."""
    L = abs(x1 - x0) + abs(y1 - y0); t = ftin(round(L * 12) / 12)
    ax.plot([x0, x1], [y0, y1], color="#444", lw=0.35, zorder=9.5)
    for (px_, py_) in ((x0, y0), (x1, y1)):
        ax.plot([px_ - 0.18, px_ + 0.18], [py_ - 0.18, py_ + 0.18], color="#444", lw=0.5, zorder=9.5)
    hz = abs(x1 - x0) > abs(y1 - y0)
    ax.text((x0 + x1) / 2 + (0 if hz else off), (y0 + y1) / 2 + (off if hz else 0), t, fontsize=3.6, color="#222", ha="center", va="center", rotation=0 if hz else 90, zorder=9.6,
            bbox=dict(fc="white", ec="none", pad=0.25, alpha=0.9))


def level_sheet(pdf, number, title, fl, sub, view, notes, checks, news, opens, existing_extra, proposed):
    sx.KIND[:] = ["PROPOSED INTERIOR CHANGES", "8 BEDROOMS · 7 BATHS · ISSUE 3"]
    sx.LEGEND[:] = ["C = checked in the scan · N = new work · U = confirm on site"]
    fig, bg = sheet(number, title, "390 Forest Ave", sub, notes)
    G, _ = sx.regularize(de.P390[str(fl)], de.T390(fl))
    (vx, vy) = view
    fL = max(9.0, (vx[1] - vx[0]) / 4.35); fR = max(5.35, (vx[1] - vx[0]) / 7.35)
    hL = (vy[1] - vy[0]) / fL; hR = (vy[1] - vy[0]) / fR
    head(bg, 0.6, 10.2, "Existing, as checked", "Compared with the 3D scan · brown hatch = chimney", color=CHECK)
    head(bg, 5.35, 10.2, "Proposed plan", "Red = new walls, doors, closets · red dashes = taken out · blue = new bath fixtures · purple = mechanical · amber edge = wall the scan missed, drawn in · grey = stays", color=FIX)
    axL = sx.axes(fig, 0.5, 9.9 - hL, vx, vy, fL)
    draw_floor(axL, G, sx.IDENT, names=de.N390[fl], heights=de.heights390(fl), label_size=3.5)
    axR = sx.axes(fig, 5.3, 9.9 - hR, vx, vy, fR)
    for r in G["rooms"]:
        axR.fill([p[0] for p in r["pts"]], [p[1] for p in r["pts"]], fc="#f7f8f9", ec="none", zorder=1)
    draw_floor(axR, dict(G, rooms=[], furniture=[]), sx.IDENT, furniture=True, wall_fc="#8a9099")
    nv = de.FX["north_in_building_frame"]
    north(axR, vx[1] - 2.0, vy[1] - 2.2, nv, 1.2); sx.scale_bar(axR, vx[0] + 0.8, vy[0] + 0.7, 12, 4)
    existing_extra(axL); proposed(axR)
    for (t, p, _s) in checks:
        if p: tag(axL, p[0], p[1], t, CHECK, size=4.6)
    for (t, p, _s) in opens:
        if p: tag(axR, p[0], p[1], t, OPEN, size=4.6, r=0.75)
    for (t, p, _s) in news:
        if p: tag(axR, p[0], p[1], t, FIX, size=4.6, r=0.75)
    y1 = items(bg, 0.55, 9.9 - hL - 0.3, [(t, CHECK, s) for (t, _p, s) in checks], 4.25, fs=5.6)
    items(bg, 0.55, y1 - 0.05, [(t, OPEN, s) for (t, _p, s) in opens], 4.25, fs=5.6)
    yb = 9.9 - hR - 0.15
    bg.plot([5.3, W - MG - TB - 0.2], [yb, yb], color=LIGHT, lw=0.6)
    half = (len(news) + 1) // 2
    items(bg, 5.35, yb - 0.22, [(t, FIX, s) for (t, _p, s) in news[:half]], 3.75, fs=5.6)
    items(bg, 9.3, yb - 0.22, [(t, FIX, s) for (t, _p, s) in news[half:]], 3.75, fs=5.6)
    save(fig, number, pdf)


HOW = ("How to read", ["KING = king bed 6'-4\" x 6'-8\", drawn to scale.", "AH = air handler 24 x 24 in.", "WH = 50 gal water heater.", "S = new drain stack in the old chimney shaft.",
                       "Sizes are clear, wall face to wall face.", "New walls: 2x4 at 16 in., 4 1/2 in. finished.", "Wet walls behind toilets and tubs: 2x6."])
MECHNOTE = ("Mechanical, assumed", ["One electric air handler (heat pump) and", "one 50 gal electric water heater per flat.", "Outdoor units sit outside; not drawn.", "The scan shows no furnace or boiler, so",
                                    "tell me what heats the house now and I", "will size the rooms to that equipment."])


# ================================================================== lower flat
def lower(pdf):
    def ex(ax):
        chimney(ax, 16.4, 6.5, 18.0, 9.5)
        ax.add_patch(Rectangle((0.9, 12.95), 20.0, 14.0, fill=False, ec=CHECK, lw=0.7, ls=(0, (3, 1.5)), zorder=9))

    def pr(ax):
        fixw_h(ax, 26.94, 19.0, 21.1); fixw_v(ax, 20.94, 26.2, 26.94); erase(ax, 7.3, 26.0, 8.3, 26.75, show=False)
        fixw_h(ax, 12.95, 20.94, 22.0); fixw_h(ax, 12.95, 24.67, 26.3); door(ax, "h", 12.95, 22.0, 24.67, "lo", 1)
        # bath 2: closets and chimney base out, bedroom wall moved 9 in.
        erase(ax, 13.3, 6.15, 16.45, 6.55, show=False); erase(ax, 16.05, 6.35, 16.45, 9.3, show=False); erase(ax, 16.0, 3.3, 18.3, 6.6, show=False)
        erase(ax, 12.9, 0.95, 13.3, 9.28); chimney(ax, 16.4, 6.5, 18.0, 9.5, removed=True)
        wall_v(ax, 12.34, 0.61, 9.62); wall_h(ax, 0.78, 12.17, 13.3); wall_v(ax, 17.68, 0.95, 9.45)
        erase(ax, 12.6, 9.25, 17.5, 9.65, show=False); wall_h(ax, 9.45, 12.17, 13.3); wall_h(ax, 9.45, 15.8, 17.85)
        door(ax, "h", 9.45, 13.3, 15.8, "lo", -1)
        tub(ax, 12.51, 0.95, 17.51, 3.45); wc(ax, 17.51, 5.0, "x-"); lav(ax, 15.93, 6.4, 17.51, 8.4); stack(ax, 17.68, 9.0)
        dim(ax, 12.51, 4.0, 15.6, 4.0, 0.0)
        # bedrooms
        closet(ax, 1.62, 10.6, 7.6, 12.78, "y-", ends=(False, True)); bed(ax, 6.8, 0.95, "y+")
        bed(ax, 21.1, 21.2, "x+"); label(ax, 28.3, 14.5, "Closet", None, GREY, 3.6)
        # laundry / mechanical room
        mech(ax, 25.8, 7.9, 25.8, 5.6, wd=(27.95, 10.25)); label(ax, 28.0, 8.6, "Laundry /\nmechanical", None, "#6a2c91", 3.8); label(ax, 27.7, 3.1, "Storage", None, GREY, 3.4)
        couch(ax, 1.4, 14.3, 4.4, 21.3, "x-"); box(ax, 9.0, 16.5, 9.6, 21.0, "TV")
        label(ax, 14.2, 7.6, "Bath 2", "5'-0\" x 8'-4\"", NEW, 4.0)
        label(ax, 6.9, 9.6, "Bedroom 1", "10'-7\" x 11'-10\"", NEW, 4.6); label(ax, 25.7, 17.0, "Bedroom 2", "9'-2\" x 9'-9\" + alcove", GREY, 4.6); label(ax, 21.1, 6.0, "Bath 1", "existing", GREY, 4.0)
        label(ax, 7.0, 23.5, "Living room", "11'-11\" x 14'-0\"", GREY, 4.6); label(ax, 17.0, 22.0, "Kitchen", "existing cabinets", GREY, 4.4)
    level_sheet(pdf, "PR-101", "390 Forest: lower flat, 2 bedrooms 2 baths", 3, "Rear building · lower flat", ((-3, 36), (-3, 30)),
                [("This flat", ["Now: 2 bedrooms, 1 bath.", "Proposed: 2 bedrooms, 2 baths, both with tubs.", "A king bed fits each bedroom.", "Mechanical moves into the laundry room."]), HOW, MECHNOTE],
                [("C1", (10.5, 20.5), "Two floor levels: the living room and kitchen are 1'-5\" lower than the bedrooms, bath, laundry and hall. Two or three steps that the scan plan does not show."),
                 ("C2", (17.2, 8.0), "Closed box beside the bath = base of the chimney."),
                 ("C3", (29.6, 5.8), "Outside doors: laundry, bedroom 2, and a 2'-10\" opening in the living room. No stair to the flats above."),
                 ("C4", (14.6, 7.8), "Hall closet: a round tank-sized object, probably the water heater."),
                 ("C5", (25.7, 20.0), "Ceilings: living 7'-6\", kitchen 6'-10\", bedroom 1 6'-10\", bedroom 2 7'-1\", bath 7'-0\", laundry 6'-10\".")],
                [("N1", (19.0, 10.9), "Chimney base out with the rest of the chimney. New 3 in. drain stack S lands here beside both baths."),
                 ("N2", (15.0, 2.2), "Bath 2, 5'-0\" x 8'-4\": 60 in. tub across the end, toilet and 24 in. vanity on the wall shared with bath 1, 2'-6\" door from the hall."),
                 ("N3", (12.3, 5.0), "Bedroom 1's wall moves 9 in. into the bedroom for 8'-8\" so the bath is a full 5 ft wide. Bedroom 1 becomes 10'-7\" x 11'-10\"."),
                 ("N4", (4.6, 11.7), "New closet for bedroom 1, 2'-2\" x 6'-0\" with folding doors (its old closet becomes bath 2). King bed shown with 2'-0\" and 2'-2\" at the sides, 2'-10\" at the foot."),
                 ("N5", (26.9, 6.8), "Laundry becomes the laundry / mechanical room: air handler and water heater on the bath wall, stacked washer and dryer in the corner, 3'-5\" clear to the outside door."),
                 ("N6", (23.3, 14.0), "Bedroom 2: a 2'-8\" door is framed in its doorway. King bed fits with 1'-8\" on the window side and 2'-6\" at the foot; a queen leaves 2'-4\"."),
                 ("N7", (20.0, 25.6), "Amber-edged walls were missed by the scan and are drawn in to close the outline: confirm them.")],
                [("U18", (5.0, 3.0), "Bedroom 1 shows NO window in the scan. A bedroom needs one you can climb out of. Check."),
                 ("U3", (21.5, 1.0), "This flat is placed under the others to about 12 in. Set out the stack on site."),
                 ("U20", (10.0, 16.0), "Ceilings of 6'-10\" to 7'-1\" are existing; mention them to the code office.")],
                ex, pr)


# ================================================================== middle flat
def middle(pdf):
    def ex(ax):
        chimney(ax, 15.7, 6.2, 18.4, 9.3)
        ax.annotate("", xy=(20.6, 26.2), xytext=(24.6, 26.2), arrowprops=dict(arrowstyle="->", color=CHECK, lw=0.7), zorder=9)

    def pr(ax):
        erase(ax, 31.7, 0.56, 33.6, 3.8, show=False); fixw_v(ax, 34.76, 0.2, 4.75); fixw_h(ax, 0.37, 32.2, 34.93)
        fixw_h(ax, 26.0, 6.2, 15.45); erase(ax, 6.2, 25.3, 8.3, 25.8, show=False)
        erase(ax, 10.75, 6.25, 15.6, 6.7, show=False); erase(ax, 15.2, 6.4, 15.65, 9.75, show=False); erase(ax, 15.3, 9.4, 17.2, 9.8, show=False)
        chimney(ax, 15.7, 6.2, 18.4, 9.3, removed=True)
        wall_h(ax, 8.77, 10.76, 18.73)
        erase(ax, 10.59 - 0.2, 7.82, 10.59 + 0.2, 12.75, show=False); wall_v(ax, 10.59, 7.82, 9.3); wall_v(ax, 10.59, 11.8, 12.75)
        door(ax, "v", 10.59, 9.3, 11.8, "lo", -1); door(ax, "h", 8.77, 11.0, 13.5, "lo", -1)
        tub(ax, 16.23, 3.61, 18.73, 8.61); wc(ax, 14.6, 3.61, "y+"); lav(ax, 11.2, 3.61, 13.2, 5.36); stack(ax, 15.6, 8.77)
        dim(ax, 10.76, 8.0, 16.23, 8.0, 0.0)
        bed(ax, 0.05, 6.67, "x+"); label(ax, 13.3, 1.9, "Closet", None, GREY, 3.6)
        bed(ax, 6.17, 25.83, "y-"); closet(ax, 0.05, 13.64, 5.8, 15.64, "y+", ends=(False, False))
        mech(ax, 18.3, 19.6, 16.55, 19.6); label(ax, 17.5, 20.95, "Mechanical", None, "#6a2c91", 3.4)
        ax.plot([15.9, 16.7, 17.5, 18.3, 19.1], [17.53, 17.1, 17.53, 17.1, 17.53], color="#6a2c91", lw=0.7, zorder=8)
        couch(ax, 20.2, 0.9, 27.2, 3.9, "y-"); box(ax, 21.5, 9.6, 26.0, 10.2, "TV")
        label(ax, 13.3, 6.8, "Bath 2", "8'-0\" x 5'-0\"", NEW, 4.0); label(ax, 13.8, 11.2, "Hall", "6'-3\" x 4'-4\"", NEW, 4.0)
        label(ax, 5.6, 11.6, "Bedroom 2", "10'-4\" x 12'-9\"", GREY, 4.6); label(ax, 11.6, 21.2, "Bedroom 1", "15'-0\" x 7'-0\" + 5'-9\" x 5'-2\"", GREY, 4.4); label(ax, 9.2, 16.0, "Bath 1", "existing", GREY, 4.0)
        label(ax, 27.5, 7.0, "Living room / kitchen", "15'-2\" x 20'-6\" · existing cabinets", GREY, 4.6); label(ax, 25.5, 24.3, "Stair hall of the upper flat", None, GREY, 4.0)
    level_sheet(pdf, "PR-102", "390 Forest: middle flat, 2 bedrooms 2 baths", 4, "Rear building · middle flat", ((-3, 37.6), (-3, 30)),
                [("This flat", ["Now: 2 bedrooms, 1 bath.", "Proposed: 2 bedrooms, 2 baths, both with tubs.", "A king bed fits each bedroom.", "Mechanical goes in the closet by the kitchen."]), HOW, MECHNOTE],
                [("C1", (22.5, 26.2), "The stair hall on this level is the upper flat's entrance, not this flat's. Stair rises along the outside wall to a landing 4'-5\" up, turns and goes on."),
                 ("C2", (17.0, 5.0), "Closed-in space 3'-4\" x 6'-2\" between hall and living room: the chimney, plus dead space."),
                 ("C3", (31.9, 18.5), "Two outside doors on the porch side. The bay and its angled window are real."),
                 ("C4", (5.2, 3.0), "Ceilings: living room / kitchen and bedroom 2 8'-8\" (dropped part 7'-4\" to 7'-8\"); bedroom 1 7'-8\"; bath 7'-4\".")],
                [("N1", (17.0, 7.3), "Chimney out through this level. New drain stack S in its place serves this bath and the attic bath above."),
                 ("N2", (13.4, 5.0), "Bath 2, 8'-0\" x 5'-0\": 60 in. tub across the far end, toilet and 24 in. vanity on the closet wall, 2'-6\" door from the hall."),
                 ("N3", (9.4, 10.5), "Bedroom 2's 4'-11\" opening becomes a 2'-6\" door clear of the new bath wall. King bed shown with 3 ft each side."),
                 ("N4", (2.9, 16.6), "New closet for bedroom 1, 2'-0\" x 5'-9\". King bed goes on the long wall; you walk round its foot through the corner by the closet. A queen is easier here."),
                 ("N5", (17.5, 18.4), "Mechanical closet, 4'-1\" x 3'-7\": air handler and water heater, doors to the kitchen passage. This closet exists; confirm what is in it now."),
                 ("N6", (33.4, 2.6), "Amber-edged walls (living room corner, bedroom 1 outside wall) were missed by the scan and are drawn in: confirm them.")],
                [("U16", (17.0, 9.9), "What else is in the closed-in space is unknown. Cut an inspection hole first."),
                 ("U17", (18.6, 11.4), "Two short angled pieces at the hall / living room corner are unexplained. Photo please.")],
                ex, pr)


# ================================================================== upper flat, main floor
def upper(pdf):
    def ex(ax):
        chimney(ax, 15.7, 6.2, 18.0, 9.2)
        ax.add_patch(Rectangle((16.9, 19.6), 2.95, 5.0, fill=False, ec=CHECK, lw=0.7, ls=(0, (3, 1.5)), zorder=9))

    def pr(ax):
        chimney(ax, 15.7, 6.2, 18.0, 9.2, removed=True)
        # closet strip re-used: bedroom 4 closet, bedroom 3 closet, mechanical closet
        erase(ax, 15.25, 0.4, 15.65, 5.6, show=False); wall_v(ax, 15.45, 0.16, 0.9); wall_v(ax, 15.45, 5.5, 6.2)
        ax.plot([15.45, 15.0, 15.45, 15.0, 15.45], [0.9, 2.05, 3.2, 4.35, 5.5], color=NEW, lw=0.7, zorder=8)
        wall_h(ax, 6.03, 15.62, 17.97); label(ax, 16.8, 3.2, "Clo.\nBR 4", None, NEW, 3.4)
        erase(ax, 17.94, 6.5, 18.34, 9.9, show=False); ax.plot([18.14, 18.6, 18.14, 18.6, 18.14], [6.5, 7.35, 8.2, 9.05, 9.9], color=NEW, lw=0.7, zorder=8)
        label(ax, 16.8, 8.4, "Clo.\nBR 3", None, NEW, 3.4); stack(ax, 16.05, 6.6)
        erase(ax, 17.94, 10.37, 18.34, 13.1); wall_h(ax, 10.2, 15.62, 20.57); wall_v(ax, 20.4, 10.03, 13.27)
        erase(ax, 16.0, 13.07, 20.0, 13.47, show=False); ax.plot([16.0, 17.0, 18.0, 19.0, 20.0], [13.27, 13.75, 13.27, 13.75, 13.27], color="#6a2c91", lw=0.7, zorder=8)
        mech(ax, 19.1, 11.7, 16.8, 11.7)
        # bedroom 4 = present living room
        erase(ax, 12.0, 13.07, 15.1, 13.47, show=False); wall_h(ax, 13.27, 12.0, 12.2); wall_h(ax, 13.27, 14.87, 15.1); door(ax, "h", 13.27, 12.2, 14.87, "lo", -1)
        bed(ax, 0.33, 6.67, "x+"); bed(ax, 31.35, 6.5, "x-")
        # living room = Room B, opening widened to 6 ft
        erase(ax, 23.5, 14.0, 23.9, 20.0); couch(ax, 28.35, 14.5, 31.35, 21.5, "x+"); box(ax, 24.0, 21.3, 24.6, 25.3, "TV")
        label(ax, 8.2, 11.4, "Bedroom 4", "15'-0\" x 12'-9\" · 191 sf", NEW, 4.6); label(ax, 24.3, 11.5, "Bedroom 3", "13'-0\" x 12'-9\" · 160 sf", NEW, 4.6)
        label(ax, 27.0, 24.0, "Living room", "7'-6\" x 13'-5\" · 101 sf", NEW, 4.6); label(ax, 3.9, 20.2, "Kitchen", "existing cabinets", GREY, 4.4); label(ax, 13.3, 22.3, "Bath 1", "existing, tub", GREY, 4.0)
        label(ax, 20.2, 15.3, "Hall", None, GREY, 4.0); label(ax, 18.0, 14.3, "Mechanical 4'-7\" x 2'-9\"", None, "#6a2c91", 3.2)
    level_sheet(pdf, "PR-103", "390 Forest: upper flat main floor, bedrooms 3 and 4", 5, "Rear building · upper flat main floor", ((-3, 36), (-3, 30)),
                [("This flat", ["Now: 3 bedrooms, 1 bath.", "Proposed: 4 bedrooms, 3 baths.", "This floor: bedrooms 3 and 4, bath 1.", "Attic: bedrooms 1 and 2, each with a", "private bath (PR-104)."]),
                 ("Why bedroom 4 moved", ["A king bed needs a room about 10'-4\" wide.", "Room B is 7'-6\" and cannot be widened:", "outside wall on one side, the way to the", "attic stair on the other.",
                                           "So bedroom 4 takes the present living", "room, where a king fits easily, and Room B", "becomes the living room.", "No bearing wall is moved on this floor."]), HOW, MECHNOTE],
                [("C1", (18.4, 22.0), "This flat's own stair comes up from the middle level under the attic stair and arrives in the hall. The attic stair starts beside Room B's wall."),
                 ("C2", (16.8, 10.6), "The 2'-8\" strip: two closets with the chimney between them (PR-105)."),
                 ("C3", (27.6, 23.5), "Room B: 7'-6\" x 13'-5\", ceiling 7'-2\", one window, 2'-4\" opening with no door."),
                 ("C4", (13.3, 19.0), "Ceilings: living room 8'-2\", Room A 8'-1\", bath 8'-3\"; kitchen, hall and Room B 7'-2\" to 7'-5\".")],
                [("N1", (19.7, 8.3), "Chimney out from the roof down. Stack S runs in its shaft, boxed in the corner of bedroom 3's closet."),
                 ("N2", (8.0, 3.0), "Bedroom 4 = the present living room, 15'-0\" x 12'-9\". A 2'-8\" door is hung in its opening. King bed shown with over 3 ft each side."),
                 ("N3", (14.4, 3.2), "Bedroom 4's closet: the existing closet at the end of the strip, lengthened to 5'-6\" with 4'-7\" folding doors."),
                 ("N4", (24.6, 3.0), "Bedroom 3 = Room A, 13'-0\" x 12'-9\", door and windows unchanged. Its closet is the middle of the strip, 2'-4\" x 3'-11\", with folding doors."),
                 ("N5", (21.6, 11.9), "Mechanical closet, 4'-7\" x 2'-9\", opening to the hall with a pair of doors: air handler and water heater, next to the stack. It takes a 2'-3\" x 3'-0\" corner of Room A."),
                 ("N6", (25.0, 17.0), "Living room = Room B. Its opening is widened from 2'-4\" to 6'-0\" so it reads with the hall; a header goes over it. Couch and TV shown.")],
                [("U2", (30.4, 3.0), "Measure the bedroom windows: each must open at least 5.7 sf clear for escape."),
                 ("U13", (19.7, 4.6), "Open the closet door in Room A and look inside the strip before pricing."),
                 ("U23", (22.0, 18.0), "If you would rather keep the big living room, Room B can only be a bedroom for a queen or smaller bed. Say which you want.")],
                ex, pr)


# ================================================================== attic
def attic(pdf):
    def ex(ax):
        chimney(ax, 15.9, 6.3, 18.3, 8.5)
        ax.annotate("", xy=(18.6, 17.3), xytext=(18.6, 23.5), arrowprops=dict(arrowstyle="->", color=CHECK, lw=0.7), zorder=9)

    def pr(ax):
        fixw_v(ax, 24.0, 23.0, 27.4)
        erase(ax, 15.5, 6.0, 18.6, 8.8, show=False); chimney(ax, 15.9, 6.3, 18.3, 8.5, removed=True)
        # bath A (bedroom 1)
        wall_v(ax, 9.43, 15.56, 21.0); wall_h(ax, 15.73, 9.43, 16.7); door(ax, "h", 15.73, 9.9, 12.2, "hi", 1)
        tub(ax, 14.1, 15.9, 16.6, 20.9); wc(ax, 12.85, 21.0, "y-"); lav(ax, 9.6, 18.4, 11.35, 20.4)
        dim(ax, 9.6, 17.2, 14.1, 17.2, 0.35); dim(ax, 13.6, 15.9, 13.6, 21.0)
        # bath B (bedroom 2) in the chimney space
        wall_v(ax, 16.7, 5.53, 8.8); wall_h(ax, 6.2, 15.53, 16.87); wall_h(ax, 5.7, 16.53, 18.5); wall_h(ax, 5.7, 19.8, 22.21)
        wall_v(ax, 22.04, 5.53, 13.37); wall_h(ax, 13.2, 20.03, 22.21)
        erase(ax, 16.95, 13.0, 19.7, 13.4, show=False); wall_h(ax, 13.2, 16.87, 19.8)
        erase(ax, 20.0, 13.7, 20.4, 16.2, show=False); door(ax, "v", 20.2, 13.7, 16.2, "lo", 1)
        door(ax, "v", 22.04, 8.9, 11.2, "hi", -1)
        tub(ax, 16.87, 5.87, 21.87, 8.37); wc(ax, 16.87, 10.0, "x+"); lav(ax, 19.2, 11.53, 21.2, 13.03); stack(ax, 17.3, 8.75)
        dim(ax, 16.87, 9.0, 21.87, 9.0, -0.35); dim(ax, 21.4, 5.87, 21.4, 13.03)
        bed(ax, 0.59, 14.37, "x+"); closet(ax, 14.2, 8.77, 16.53, 12.9, "x-")
        bed(ax, 31.6, 13.2, "x-"); closet(ax, 20.37, 20.77, 23.83, 22.98, "y-", ends=(False, False))
        label(ax, 11.8, 16.6, "Bath A", None, NEW, 4.0); label(ax, 20.3, 10.3, "Bath B", None, NEW, 4.0)
        label(ax, 8.0, 10.0, "Attic bedroom 1", "15'-11\" x 7'-4\" + 8'-8\" x 5'-5\" + bay", NEW, 4.4); label(ax, 27.0, 18.6, "Attic bedroom 2", "9'-5\" x 13'-2\" + bay", NEW, 4.4)
    level_sheet(pdf, "PR-104", "390 Forest: attic, bedrooms 1 and 2 with private baths", 6, "Rear building · attic of the upper flat", ((-3, 36), (-3, 30)),
                [("This level", ["Two bedrooms, each with its own bath", "entered only from that bedroom.", "Both baths have a 60 in. tub."]),
                 ("No new dormer", ["Both baths fit under the existing ceiling,", "which is flat at 7'-8\" to 8'-0\".", "Bath A: the tub stands against the stair", "wall under the full-height ceiling; only",
                                    "the toilet tank is under the slope.", "Bath B: the tub's shower end is toward the", "dormer, where the ceiling is 8'-0\". The", "far corner is about 6'-8\": check it."]), HOW],
                [("C1", (18.6, 19.5), "Attic stair arrives at a landing between the two bedroom doors."),
                 ("C2", (17.1, 7.4), "Boxed corner between the dormers = the chimney."),
                 ("C3", (5.0, 18.5), "Headroom from the true floor: flat ceiling 7'-8\" to 8'-0\", under 7 ft only in the last 1 to 2 ft by the knee walls."),
                 ("C4", (25.5, 4.2), "Five windows confirmed. The small door in bedroom 2 leads to the roof space behind the knee wall.")],
                [("N1", (17.6, 7.2), "Chimney out. Its space and the corner beside it become bath B; stack S starts here."),
                 ("N2", (12.2, 19.6), "Bath A, private to bedroom 1, 7'-0\" x 5'-1\": 60 in. tub on the stair wall, toilet at the knee wall, 21 in. vanity. Drains into the wall of bath 1 below."),
                 ("N3", (19.4, 11.0), "Bath B, private to bedroom 2, 5'-0\" x 7'-2\": 60 in. tub across the end, toilet, 24 in. vanity, 2'-4\" door from the bedroom."),
                 ("N4", (21.6, 15.0), "Bedroom 2's door moves 3 ft round the corner of the landing; the old doorway is walled up because it would open into bath B."),
                 ("N5", (15.3, 10.8), "New closets: bedroom 1, 2'-4\" x 4'-2\" by its door; bedroom 2, the 3'-5\" x 2'-2\" recess by the stair gets doors."),
                 ("N6", (4.0, 12.5), "King beds: bedroom 1 on the end wall with 3 ft each side and 2 ft to the bath wall; bedroom 2 on the end wall under the window with 2'-8\" at the foot."),
                 ("N7", (25.0, 25.0), "Heating and cooling for the attic comes from the upper flat's air handler, ducts run in the knee-wall space; or one ductless unit per bedroom. To be designed.")],
                [("U14", (16.9, 14.4), "Bedroom 1's doorway reads about 2 ft wide in the scan. Measure it."),
                 ("U22", (20.9, 17.6), "New bedroom 2 door: check the stair's top landing is at least 3 ft deep there."),
                 ("U15", (15.0, 21.8), "Headroom is about 6'-6\" in the last foot by the knee wall (bath A toilet tank) and about 6'-8\" at the back corner of bath B's tub.")],
                ex, pr)


def summary(pdf):
    sx.KIND[:] = ["PROPOSED INTERIOR CHANGES", "8 BEDROOMS · 7 BATHS · ISSUE 3"]
    sx.LEGEND[:] = ["C = checked in the scan · N = new work · U = confirm on site"]
    fig, bg = sheet("PR-001", "390 Forest: 8 bedrooms, 7 baths, summary", "390 Forest Ave", "Rear building · all levels · issue 3", [
        ("Result", ["Lower flat   2 bed 2 bath", "Middle flat  2 bed 2 bath", "Upper flat   4 bed 3 bath", "Whole house  8 bed 7 bath", "Every bath has a 60 in. tub.", "Every bedroom has a closet."]),
        ("Changed since issue 2", ["Tubs in all seven baths.", "King beds drawn in every bedroom.", "Closets added. Mechanical rooms added.", "Couches, TVs, existing cabinets drawn.", "Open corners in the scan closed.",
                                   "Upper flat: bedroom 4 moved to the present", "living room; Room B becomes the living", "room. No beam between Room A and B now."]),
        ("No new dormer", ["Both attic baths fit under the existing", "ceiling. See PR-104."]),
        ("Not done yet", ["Beams and headers, joists, pipe and duct", "sizes, electrical, fire separation between", "flats, permits. 441 Baird St plans."]),
        ("Sheets", ["PR-101 lower flat", "PR-102 middle flat", "PR-103 upper flat", "PR-104 attic", "PR-105 chimney evidence"])])
    head(bg, 0.6, 10.2, "Bedrooms: size and king-bed fit", "King bed = 6'-4\" x 6'-8\". Clearances are what is left beside and beyond the bed as drawn", color=FIX)
    r1 = [["Flat", "Bedroom", "Clear size", "King bed: sides / foot", "Closet", "Ceiling"],
          ["Lower", "1", "10'-7\" x 11'-10\"", "2'-0\" and 2'-2\" / 2'-10\"", "new, 2'-2\" x 6'-0\"", "6'-10\""],
          ["Lower", "2", "9'-2\" x 9'-9\" + alcove", "1'-8\" and 1'-9\" / 2'-6\"  (tight; queen is better)", "existing", "7'-1\""],
          ["Middle", "1", "15'-0\" x 7'-0\" + 5'-9\" x 5'-2\"", "3'-0\" and 5'-9\" / walk round through the corner  (queen is better)", "new, 2'-0\" x 5'-9\"", "7'-8\""],
          ["Middle", "2", "10'-4\" x 12'-9\"", "3'-0\" and 3'-5\" / 3'-8\"", "existing", "8'-8\""],
          ["Upper", "3 (Room A)", "13'-0\" x 12'-9\"", "3'-0\" and 3'-5\" / 6'-4\"", "2'-4\" x 3'-11\" in the strip", "8'-1\""],
          ["Upper", "4 (was living room)", "15'-0\" x 12'-9\"", "3'-2\" and 3'-3\" / 8'-3\"", "2'-4\" x 5'-6\" in the strip", "8'-2\""],
          ["Attic", "1", "15'-11\" x 7'-4\" + 8'-8\" x 5'-5\" + bay", "3'-0\" and 3'-6\" / 2'-0\"", "new, 2'-4\" x 4'-2\"", "7'-9\""],
          ["Attic", "2", "9'-5\" x 13'-2\" + bay", "2'-10\" and 4'-0\" / 2'-8\"", "recess 3'-5\" x 2'-2\", doors added", "7'-10\""]]
    y = table(bg, 0.6, 9.8, [0.7, 1.5, 2.6, 3.9, 1.9, 0.75], r1, fs=5.9, rh=0.215)
    head(bg, 0.6, y - 0.4, "Baths", "All seven have a 60 in. tub, a toilet and a vanity", color=FIX)
    r2 = [["Flat", "Bath", "Clear size", "Where", "Drain"],
          ["Lower", "1 existing", "6'-9\" x 7'-6\"", "off the hall", "existing"],
          ["Lower", "2 NEW", "5'-0\" x 8'-4\"", "old closets + chimney base, door from the hall", "new stack S"],
          ["Middle", "1 existing", "6'-6\" x 5'-3\"", "off the kitchen passage", "existing"],
          ["Middle", "2 NEW", "8'-0\" x 5'-0\"", "half of the hall + chimney space, door from the hall", "new stack S"],
          ["Upper", "1 existing", "6'-9\" x 10'-0\"", "off the hall; shared by bedrooms 3 and 4", "existing"],
          ["Attic", "A NEW", "7'-0\" x 5'-1\"", "private to bedroom 1, over bath 1", "into bath 1's wall"],
          ["Attic", "B NEW", "5'-0\" x 7'-2\"", "private to bedroom 2, in the chimney space", "new stack S"]]
    y2 = table(bg, 0.6, y - 0.8, [0.7, 1.3, 1.6, 5.1, 2.65], r2, fs=5.9, rh=0.215)
    head(bg, 0.6, y2 - 0.4, "Mechanical rooms", "Assumed: one electric air handler and one 50 gal electric water heater per flat. Tell me what is there now", color="#6a2c91")
    r3 = [["Flat", "Room", "Clear size", "Holds"],
          ["Lower", "Laundry / mechanical room (existing laundry)", "5'-7\" x 8'-4\"", "air handler, water heater, stacked washer/dryer; outside door for service"],
          ["Middle", "Closet by the kitchen passage (existing)", "4'-1\" x 3'-7\"", "air handler, water heater"],
          ["Upper + attic", "New closet off the hall", "4'-7\" x 2'-9\"", "air handler, water heater; washer/dryer stay in the kitchen recess"]]
    y3 = table(bg, 0.6, y2 - 0.8, [1.1, 3.9, 1.5, 4.85], r3, fs=5.9, rh=0.215)
    bg.text(0.6, y3 - 0.25, "King beds fit every bedroom, but two are tight: lower flat bedroom 2 and middle flat bedroom 1. Making those roomier means moving a closet or a bath wall; say if you want that.\n"
            "Before pricing: open the chimney strip, confirm the amber-edged walls, find the existing heating equipment and water heaters, and check for a window in the lower flat's bedroom 1.", fontsize=6.1, va="top", color=INK, linespacing=1.4)
    save(fig, "PR-001", pdf)


def evidence(pdf):
    sx.KIND[:] = ["PROPOSED INTERIOR CHANGES", "EVIDENCE FOR THE CHIMNEY"]
    fig, bg = sheet("PR-105", "390 Forest: the U5 strip is a chimney between two closets", "390 Forest Ave", "Rear building · chimney", [
        ("Answer", ["The strip between the upper flat's living", "room and Room A is two closets with a", "chimney standing between them."]),
        ("Why I think so", ["1 The same closed-in spot, about 2'-4\" x", "  3'-0\", shows on all four levels, one", "  above the other.", "2 On the roof a box sits right above it,",
                            "  between the two dormers.", "3 Both room faces of the strip are flat", "  plaster with a closet door: nothing was", "  scanned inside the middle 9 ft."]),
        ("How sure", ["Confirmed: the owner has a photo showing", "the roof box is a chimney."]),
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
