"""Sheets A-501 (wall, floor and roof assemblies) and A-601 (door, window and finish schedules).

A-501 is the sheet for the insulation, drywall, fire-stopping, siding and roofing trades.
A-601 is the sheet for the window and door supplier, the trim carpenter, the flooring and paint
trades and whoever buys the fixtures and appliances.
Detail axes are in real INCHES (1 1/2 in. = 1 ft means 8 real inches per paper inch).
"""
import math
import os
import re
from collections import Counter

import numpy as np
from matplotlib.patches import Circle, Polygon as MPoly, Rectangle
from shapely.geometry import Polygon as SPoly, box as sbox

import model as m
from common import *  # noqa: F401,F403
from index import TITLE
from plans import *  # noqa: F401,F403

UPI = 8.0                      # real inches per paper inch: 1 1/2" = 1'-0"
X_AREA = SHEET_W - MARGIN - TB_W   # right edge of the drawing area (title block starts here)
CHECK = bool(os.environ.get("A3_CHECK"))

# Sizes the model does not carry (taken from the brief / stated catalogue sizes)
EAVE_REAR = 12.0               # in., rear eave projection
RAKE = 8.0                     # in., side rake projection
DOOR_H = 6 + 8 / 12.0          # all doors 6'-8"
R30_T, R49_T = 9.5, 16.0       # in., R-30 batt and R-49 blown depth
RIGID_R10, RIGID_R15 = 2.0, 2.5    # in., rigid foam for R-10 (XPS) and R-15 (polyiso)

# wall-type colours on the key plan
C_W1, C_W2, C_W2S, C_W3, C_W4, C_W2F = "#3d4349", "#8fb4dc", BLUE, "#2e7d32", ACCENT, "#d97a00"
WCOL = {"W1": C_W1, "W1X": ACCENT, "W2": C_W2, "W2S": C_W2S, "W3": C_W3, "W4": C_W4, "W2F": C_W2F,
        "W5": "#6b7178", "F1": "#5b4a8a", "F2": ACCENT, "F3": "#6b7178", "R1": "#3d4349"}

MAT = {
    "gyp": dict(fc="#f1f1ef", hatch=".....", hc="#a3a9b0"),
    "gypx": dict(fc="#f6cfca", hatch=".....", hc="#c9665e"),
    "osb": dict(fc="#dcc594", hatch="/////", hc="#b0935a"),
    "wood": dict(fc="#f0e2c0"),
    "conc": dict(fc="#dfe1e4", hatch="...", hc="#8d949c"),
    "stone": dict(fc="#f5f5f3", hatch="ooo", hc="#8d949c"),
    "rigid": dict(fc="#d9e8f6", hatch="xxxx", hc="#86add3"),
    "earth": dict(fc="#f5efe6", hatch="\\\\\\\\", hc=EARTH),
    "batt": dict(fc="#fde6ec"),
    "sbatt": dict(fc="#fdf0d0"),
    "mwool": dict(fc="#e3dcb8"),
    "blown": dict(fc="#fbf0d6", hatch="...", hc="#c9a86a"),
    "siding": dict(fc="#9fb0c2"),
    "floor": dict(fc="#b99d74"),
    "board": dict(fc="#bfc5cc", hatch="|||||", hc="#6b7178"),
    "metal": dict(fc="#8d949c"),
}
SQ = {"batt": "#d9799a", "sbatt": "#c99a2e", "mwool": "#7d7340"}


# ----------------------------------------------------------------------------
# small helpers
# ----------------------------------------------------------------------------
def inch(v, feet=True):
    """Real inches as text: 6.5 -> 6 1/2", 20 -> 1'-8", 21.375 -> 1'-9 3/8"."""
    s16 = int(round(v * 16))
    whole, f = divmod(s16, 16)
    frac = ""
    if f:
        g = math.gcd(f, 16)
        frac = f"{f // g}/{16 // g}"
    if feet and whole >= 12:
        ft, i = divmod(whole, 12)
        return f"{ft}'-{i} {frac}\"" if frac else f"{ft}'-{i}\""
    if whole and frac:
        return f"{whole} {frac}\""
    return f"{frac}\"" if frac else f"{whole}\""


def B(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def dax(fig, left, bottom, w_in, h_in, upi=UPI, x0=0.0, y0=0.0):
    """Detail axes in real inches."""
    ax = fig.add_axes([left / SHEET_W, bottom / SHEET_H, w_in / SHEET_W, h_in / SHEET_H])
    ax.set_xlim(x0, x0 + w_in * upi)
    ax.set_ylim(y0, y0 + h_in * upi)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.fpi = upi
    return ax


def mat(ax, pts, kind, z=3.0, lw=0.45, ec=INK):
    s = MAT[kind]
    if s.get("hatch"):
        ax.add_patch(MPoly(pts, closed=True, fc=s["fc"], ec=s["hc"], lw=0, hatch=s["hatch"], zorder=z))
        ax.add_patch(MPoly(pts, closed=True, fc="none", ec=ec, lw=lw, zorder=z + 0.05))
    else:
        ax.add_patch(MPoly(pts, closed=True, fc=s["fc"], ec=ec, lw=lw, zorder=z))


def squiggle(ax, x0, y0, x1, y1, kind, z=3.2, lw=0.45):
    """Batt insulation symbol: a wave filling the long direction of the box."""
    w, h = x1 - x0, y1 - y0
    if w >= h:
        n = max(2, int(round(w / (h * 0.5))))
        t = np.linspace(0, 1, n * 16 + 1)
        ax.plot(x0 + t * w, (y0 + y1) / 2 + 0.38 * h * np.sin(t * n * math.pi), color=SQ[kind], lw=lw, zorder=z)
    else:
        n = max(2, int(round(h / (w * 0.5))))
        t = np.linspace(0, 1, n * 16 + 1)
        ax.plot((x0 + x1) / 2 + 0.38 * w * np.sin(t * n * math.pi), y0 + t * h, color=SQ[kind], lw=lw, zorder=z)


def cavity(ax, x0, y0, x1, y1, kind, z=3.0):
    mat(ax, B(x0, y0, x1, y1), kind, z=z)
    squiggle(ax, x0, y0, x1, y1, kind, z=z + 0.2)


def cut_wood(ax, x0, y0, x1, y1, z=4.0):
    """Framing member cut across the grain (fill + X)."""
    mat(ax, B(x0, y0, x1, y1), "wood", z=z)
    line(ax, [(x0, y0), (x1, y1)], lw=0.3, z=z + 0.1)
    line(ax, [(x0, y1), (x1, y0)], lw=0.3, z=z + 0.1)


def ddim(ax, p0, p1, off, label, size=5.0, **kw):
    dim(ax, p0, p1, off, label, size=size, **kw)


def callouts(ax, xt, ytop, items, fs=5.4, gap=0.45, ha="left", land=0.9, color=INK, align=False, ybot=None):
    """Stack of leader notes. items: [((x, y) anchor or None, text)]. With align=True each note sits level with
    its anchor where there is room; ybot keeps the stack above that line. Returns the y below the last note."""
    k = ax.fpi / UPI
    lh = fs * 1.2 / 72 * ax.fpi
    hs = [(t.count("\n") + 1) * lh for _, t in items]
    ys, y = [], ytop
    for (pt, t), h in zip(items, hs):
        if align and pt is not None:
            y = min(y, pt[1] + 0.55 * lh)
        ys.append(y)
        y -= h + gap * k
    if ybot is not None:
        lim = ybot
        for i in reversed(range(len(items))):
            if ys[i] - hs[i] < lim:
                ys[i] = lim + hs[i]
            lim = ys[i] + gap * k
    s = -1 if ha == "left" else 1
    for (pt, t), y in zip(items, ys):
        txt(ax, xt, y, t, size=fs, ha=ha, va="top", color=color)
        if pt is not None:
            ym = y - 0.52 * fs / 72 * ax.fpi
            x1 = xt + s * 0.3 * k
            line(ax, [pt, (x1 + s * land * k, ym), (x1, ym)], lw=0.35, color=color, z=8)
            ax.add_patch(Circle(pt, 0.16 * k, fc=color, ec="none", zorder=8))
    return ys[-1] - hs[-1] - gap * k


def dtitle(ax, x, y, tag, title, sub=None, color=INK):
    """Detail title: coloured tag box + name + grey sub-line. (x, y) = top-left, in axes units."""
    k = ax.fpi / UPI
    w = (0.6 + 0.62 * len(tag)) * k
    ax.add_patch(Rectangle((x, y - 1.5 * k), w, 1.5 * k, fc=color, ec="none", zorder=9))
    txt(ax, x + w / 2, y - 0.78 * k, tag, size=6.8, color=PAPER, weight="bold", z=10)
    txt(ax, x + w + 0.5 * k, y - 0.04 * k, title.upper(), size=6.6, weight="bold", ha="left", va="top")
    if sub:
        txt(ax, x + w + 0.5 * k, y - 1.0 * k, sub, size=4.8, color=GREY, ha="left", va="top")


def wall_slice(ax, x0, y0, L, layers, studs=(2.0, 18.0), fill="batt"):
    """Plan cut through a wall, room side at the bottom. layers = [(thickness in., kind)].
    Returns [(y_low, y_high)] for each layer."""
    y, out = y0, []
    for t, kind in layers:
        if kind == "stud":
            if fill:
                cavity(ax, x0, y, x0 + L, y + t, fill)
            else:
                rect(ax, x0, y, x0 + L, y + t, fc=PAPER, ec=INK, lw=0.45, z=3)
            for s in studs:
                cut_wood(ax, x0 + s - 0.75, y, x0 + s + 0.75, y + t)
        elif kind == "furr":
            for s in studs:
                cut_wood(ax, x0 + s - 1.25, y, x0 + s + 1.25, y + t)
            line(ax, [(x0, y), (x0, y + t)], lw=0.45)
            line(ax, [(x0 + L, y), (x0 + L, y + t)], lw=0.45)
        elif kind == "wrap":
            line(ax, [(x0, y + t / 2), (x0 + L, y + t / 2)], lw=0.9, color=BLUE, ls=(0, (4, 1.5)), z=5)
        elif kind == "membrane":
            rect(ax, x0, y, x0 + L, y + t, fc=INK, ec=INK, lw=0.3, z=5)
        else:
            mat(ax, B(x0, y, x0 + L, y + t), kind)
        out.append((y, y + t))
        y += t
    return out


def mid(band):
    return (band[0] + band[1]) / 2


def tbl(fig, bg, x, y, widths, rows, fs=6.0, rh=0.19, title=None, sub=None):
    """common.table with a title; prints any cell that overruns its column when A3_CHECK is set."""
    if title:
        bg.text(x, y + 0.07, title, fontsize=7.8, fontweight="bold", color=INK, va="bottom")
        if sub:
            bg.text(x + sum(widths), y + 0.07, sub, fontsize=5.4, color=GREY, va="bottom", ha="right")
    n0 = len(bg.texts)
    yb = table(bg, x, y, widths, rows, fs=fs, rh=rh)
    if CHECK:
        r = fig.canvas.get_renderer()
        cells = [(i, j) for i, row in enumerate(rows) for j, _ in enumerate(row[:len(widths)])]
        for (i, j), t in zip(cells, bg.texts[n0:]):
            w = t.get_window_extent(r).width / fig.dpi
            if w > widths[j] - 0.07:
                print(f"  cell overrun {title} r{i} c{j}: {w:.2f} > {widths[j]:.2f}  {t.get_text()!r}")
        if x + sum(widths) > X_AREA - 0.05:
            print(f"  table {title} runs to {x + sum(widths):.2f} (limit {X_AREA:.2f})")
    return yb


def note_lines(bg, x, y, lines, fs=5.6, lh=0.112, color=INK):
    for ln in lines:
        bg.text(x, y, ln, fontsize=fs, color=color, va="top")
        y -= lh
    return y


# ----------------------------------------------------------------------------
# A-501: key plan
# ----------------------------------------------------------------------------
def wall_type(i):
    """Type tag of partition i of m.PARTITIONS. 2x4 partitions get sound batts (W2S) when they touch a
    bath, or separate a bedroom from anything but its own closet."""
    x0, y0, x1, y1, kind = m.PARTITIONS[i]
    if kind == "r":
        return "W4"
    if kind == "w":
        return "W3"
    if kind == "f":
        return "W2F"
    near = sbox(x0, y0, x1, y1).buffer(0.15)
    touch = [k for k, p in m.ROOMS.items() if near.intersection(SPoly(p)).area > 0.08]
    if any(k.startswith("BATH") for k in touch):
        return "W2S"
    if any(k.startswith("BEDROOM") for k in touch) and any(not k.startswith(("BEDROOM", "CLOSET")) for k in touch):
        return "W2S"
    if sum(k.startswith("BEDROOM") for k in touch) > 1:
        return "W2S"
    return "W2"


def wtag(ax, x, y, t):
    ax.text(x, y, t, fontsize=4.6, fontweight="bold", color=WCOL[t], ha="center", va="center", zorder=12,
            bbox=dict(fc=PAPER, ec=WCOL[t], lw=0.4, pad=0.7))


# where each partition's tag sits on the key plan: partition index -> (x, y) ft
TAG_AT = {0: (15.0, 20.2), 1: (31.0, 20.2), 2: (14.0, 28.1), 3: (18.0, 13.6), 4: (18.0, 36.0), 5: (13.9, 22.6),
          10: (28.1, 24.6), 11: (29.2, 29.3), 13: (35.5, 15.5), 14: (41.0, 22.9), 16: (22.6, 38.7)}


def key_plan_walls(fig, left, bottom):
    vx, vy = (5.8, 45.4), (6.0, 42.4)
    ax = plan_axes(fig, left, bottom, vx, vy, 8.0)                 # 1/8" = 1'-0"
    st = unit_plan(ax, "bg", "A", furniture=False, labels=True)
    # exterior wall W1: ring between the outside and inside faces
    poly(ax, m.OUT_U, fc=C_W1, ec=C_W1, lw=0.6, z=3.5)
    poly(ax, [m.OUT_U[2], m.OUT_U[3], m.IN_U[3], m.IN_U[2]], fc=C_W1, ec=C_W1, lw=0.4, z=5.35)
    for (tag, w_, s0, s1, note) in m.WINDOWS:
        if w_ == "N":
            poly(ax, m.win_quad(w_, s0, s1), fc=PAPER, ec="none", z=5.4)
    # partitions by type
    types = [wall_type(i) for i in range(len(m.PARTITIONS))]
    for (x0, y0, x1, y1, kind), t in zip(m.PARTITIONS, types):
        rect(ax, x0, y0, x1, y1, fc=WCOL[t], ec=WCOL[t], lw=0.3, z=5.1)
    for d in m.DOORS:
        x0, y0, x1, y1 = m.door_cut(d)
        if d["at"] != (m.YF, m.YFI):
            rect(ax, x0, y0, x1, y1, fc=PAPER, ec="none", z=5.15)
    # 5/8 Type X on the room side of the exterior walls of the stair
    o = 0.16
    line(ax, [(m.SHAFT_X0, m.YFI + o), (m.XEI - o, m.YFI + o), (m.XEI - o, m.SHAFT_U[3])], color=ACCENT, lw=1.3, z=6.6)
    # stacks through the rated floors
    for (sx, sy) in (m.STACK_1, m.STACK_2, m.STACK_3):
        ax.add_patch(Circle((sx, sy), 0.42, fc=PAPER, ec=ACCENT, lw=1.0, zorder=8))
        ax.add_patch(Circle((sx, sy), 0.16, fc=ACCENT, ec="none", zorder=8.1))
    # tags
    for i, ((x0, y0, x1, y1, kind), t) in enumerate(zip(m.PARTITIONS, types)):
        if i not in TAG_AT:
            continue
        x, y = TAG_AT[i]
        wtag(ax, x, y, t)
        if t == "W2F":
            line(ax, [(x, y - 0.6), ((x0 + x1) / 2, y1)], lw=0.35, color=WCOL[t], z=11)
    wtag(ax, 26.5, 37.9, "W1")
    wtag(ax, 20.0, 9.3, "W1")
    wtag(ax, 42.4, 12.0, "W1X")
    return ax, types


def sheet_a501(pdf):
    eave_face = m.SB_REAR + m.M - EAVE_REAR / 12
    rake_face = m.SB_SIDE + m.M - RAKE / 12
    notes = [
        ("Where the ratings are", [
            "W4 stair walls and F2 floor between the\n"
            "flats: 1 hour. F1 garage ceiling: 5/8 in.\n"
            "Type X (IRC R302.6). Roof edges: the rear\n"
            f"eave ({ftin(eave_face)} from the lot line) and the\n"
            f"{inch(RAKE)} side rakes ({ftin(rake_face)}) are both under 5 ft:\n"
            "1-hour underside on all three, no vents.\n"
            "Attic vents: front soffit and ridge only.",
        ]),
        ("Fire-stopping", [
            "Every pipe, duct, cable and box through a\n"
            "rated wall, floor or ceiling gets a listed\n"
            "fire-stop system (ASTM E814 / UL 1479)\n"
            "matched to the pipe material and hole size.\n"
            "Keep the data sheets for the inspector.\n"
            "Plastic drain stacks: intumescent collar\n"
            "or wrap at the F1 and F2 ceilings.\n"
            "Boxes in W4: steel, 16 sq in. max, 24 in.\n"
            "apart on opposite faces, or putty pads.\n"
            "Unit A: hang the F2 ceiling first, then\n"
            "frame the 7'-0\" duct soffits below it. No\n"
            "duct, fan or recessed light may go through\n"
            "the rated ceiling.",
        ]),
        ("Fire-blocking, draft-stopping", [
            "Fire-block (IRC R302.11) at every floor and\n"
            "ceiling line in the stud walls, at the\n"
            "duct soffits, at the stair stringers and\n"
            "around each pipe and wire hole in plates.\n"
            f"Each floor is {m.FOOTPRINT:,.0f} sf, under the 1,000 sf\n"
            "limit of R302.12: no draft-stop is needed\n"
            "by area. Close the truss space solid at\n"
            "the stair walls so W4 is unbroken from\n"
            "the garage slab to the roof deck.",
        ]),
        ("Preliminary", [
            "UL numbers are generic examples. The\n"
            "architect picks the listed designs; build\n"
            "to those listings exactly.",
        ]),
    ]
    fig, bg = new_sheet("A-501", TITLE["A-501"], "As noted", notes)

    # ---------------- key plan (top left) ----------------
    PX, PY = 0.5, 5.9
    ax, types = key_plan_walls(fig, PX, PY)
    txt(ax, 13.0, 41.75, "KEY PLAN: WALL TYPES", size=8.0, weight="bold", ha="left", va="bottom")
    txt(ax, 13.0, 41.6, "Units A and B (same plan) · 1/8\" = 1'-0\"", size=5.0, color=GREY, ha="left", va="top")
    north_arrow(ax, 7.5, 7.5, 1.0, 4.8)
    leg = [("W1", "Exterior wall, 2x6, R-20"),
           ("W1X", "W1 with 5/8 Type X inside (stair)"),
           ("W2", "2x4 partition, empty cavity"),
           ("W2S", "2x4 partition with sound batts"),
           ("W3", "2x6 plumbing wall, sound batts"),
           ("W4", "1-hour wall, 5/8 Type X both sides"),
           ("W2F", "Furred 2x4, board on bath side only"),
           ("FS", "Drain stack: fire-stop at each floor")]
    lx, ly = 31.6, 41.9
    for i, (t, s) in enumerate(leg):
        y = ly - i * 0.84
        if t == "FS":
            ax.add_patch(Circle((lx + 0.75, y), 0.34, fc=PAPER, ec=ACCENT, lw=0.9, zorder=8))
            ax.add_patch(Circle((lx + 0.75, y), 0.13, fc=ACCENT, ec="none", zorder=8.1))
        elif t == "W1X":
            rect(ax, lx, y - 0.2, lx + 1.5, y + 0.2, fc=C_W1, ec=C_W1, lw=0.3, z=8)
            line(ax, [(lx, y - 0.3), (lx + 1.5, y - 0.3)], color=ACCENT, lw=1.3, z=9)
        else:
            rect(ax, lx, y - 0.2, lx + 1.5, y + 0.2, fc=WCOL[t], ec=WCOL[t], lw=0.3, z=8)
        txt(ax, lx + 1.9, y, t, size=4.8, weight="bold", ha="left", color=ACCENT if t in ("FS", "W1X") else WCOL[t])
        txt(ax, lx + 3.85, y, s, size=4.8, ha="left")

    # ---------------- W1-W4 wall types (bottom left) ----------------
    wx = dax(fig, 0.5, 0.48, 4.95, 5.3)
    X0, L, XT = 3.0, 20.0, 24.4
    top = 5.3 * UPI
    osb_t = m.EXT * 12 - 6.0

    def stud_dim(y):
        ddim(wx, (X0 + 2.0, y), (X0 + 18.0, y), -1.1, "16\" o.c.", size=4.8)

    # W1
    y = top
    dtitle(wx, 0, y, "W1", "Exterior wall", "Plan cut · outside at the top · 1 1/2\" = 1'-0\"", WCOL["W1"])
    layers = [(0.5, "gyp"), (5.5, "stud"), (osb_t, "osb"), (0.22, "wrap"), (5 / 16, "siding")]
    yb = y - 2.6 - sum(t for t, _ in layers)
    b = wall_slice(wx, X0, yb, L, layers)
    ddim(wx, (X0, b[0][0]), (X0, b[2][1]), 1.2, inch(m.EXT * 12))
    stud_dim(yb)
    ax_ = X0 + L - 1.0
    ynext = callouts(wx, XT, b[-1][1] + 0.5, [
        ((ax_, mid(b[4])), "Fibre-cement lap or vinyl siding"),
        ((ax_ - 1.2, mid(b[3])), "Housewrap, seams taped; flash every\nwindow and door into it"),
        ((ax_ - 2.4, mid(b[2])), "7/16 in. OSB sheathing (nailing: S-204)"),
        ((X0 + 18.0, mid(b[1]) + 1.2), "2x6 studs @ 16 in. o.c."),
        ((X0 + 13.0, mid(b[1]) - 0.4), "R-20 kraft-faced batts, full depth, cut\ntight around boxes and pipes"),
        ((ax_ - 3.0, mid(b[0])), "1/2 in. gypsum board. W1X = 5/8 in. Type X:\nat the stair; and on the Unit A front and\nrear walls, which carry the 1-hour floor\n(IRC R302.3.1, architect to confirm)"),
    ])
    # W2
    y = min(yb - 2.6, ynext) - 0.7
    dtitle(wx, 0, y, "W2", "Partition, 2x4", "W2S = with sound batts", WCOL["W2S"])
    layers = [(0.5, "gyp"), (m.PART * 12 - 1.0, "stud"), (0.5, "gyp")]
    yb = y - 2.4 - sum(t for t, _ in layers)
    b = wall_slice(wx, X0, yb, L, layers, fill="sbatt")
    ddim(wx, (X0, b[0][0]), (X0, b[2][1]), 1.2, inch(m.PART * 12))
    ynext = callouts(wx, XT, b[-1][1] + 0.5, [
        ((ax_, mid(b[2])), "1/2 in. gypsum board each side;\nmoisture-resistant board in baths"),
        ((X0 + 18.0, mid(b[1]) + 0.6), "2x4 studs @ 16 in. o.c."),
        ((X0 + 13.0, mid(b[1])), "W2S: 3 1/2 in. sound batts (walls around\nbaths and bedrooms). W2: empty (closets)"),
    ])
    # W3
    y = min(yb, ynext) - 0.9
    dtitle(wx, 0, y, "W3", "Plumbing wall, 2x6", "Behind bath 1", WCOL["W3"])
    layers = [(0.5, "gyp"), (m.WET * 12 - 1.0, "stud"), (0.5, "gyp")]
    yb = y - 2.4 - sum(t for t, _ in layers)
    b = wall_slice(wx, X0, yb, L, layers, fill="sbatt")
    px, py = X0 + 9.0, mid(b[1])
    wx.add_patch(Circle((px, py), 1.75, fc=PAPER, ec=INK, lw=0.7, zorder=5))
    wx.add_patch(Circle((px, py), 1.5, fc=PAPER, ec=INK, lw=0.35, zorder=5))
    ddim(wx, (X0, b[0][0]), (X0, b[2][1]), 1.2, inch(m.WET * 12))
    ynext = callouts(wx, XT, b[-1][1] + 0.5, [
        ((ax_, mid(b[2])), "1/2 in. moisture-resistant gypsum board"),
        ((X0 + 18.0, mid(b[1]) + 1.0), "2x6 studs @ 16 in. o.c.: room for the\n3 in. stack and vents (P-102, P-103)"),
        ((px + 1.75, py), "Sound batts around the pipes; nail plates\nwhere a pipe is within 1 1/4 in. of a face"),
    ])
    # W4
    y = min(yb, ynext) - 0.9
    dtitle(wx, 0, y, "W4", "1-hour stair enclosure wall", "2x4, Type X each side", WCOL["W4"])
    layers = [(0.625, "gypx"), (m.RATED * 12 - 1.25, "stud"), (0.625, "gypx")]
    yb = y - 2.4 - sum(t for t, _ in layers)
    b = wall_slice(wx, X0, yb, L, layers, fill="mwool")
    ddim(wx, (X0, b[0][0]), (X0, b[2][1]), 1.2, inch(m.RATED * 12))
    callouts(wx, XT, b[-1][1] + 0.5, [
        ((ax_, mid(b[2])), "5/8 in. Type X gypsum each side, full\nheight, taped, fasteners per the listing"),
        ((X0 + 18.0, mid(b[1]) + 0.6), "2x4 studs @ 16 in. o.c."),
        ((X0 + 13.0, mid(b[1])), "3 1/2 in. mineral wool batts, friction fit"),
        (None, "1-hour, generic design UL U305. Architect\nconfirms the listing; build exactly to it"),
    ])

    # ---------------- middle column: F2, F3, W5 ----------------
    CX, CW = 5.65, 3.9
    SX, SL, ST = 2.7, 19.0, 22.9          # slice left, slice length, text left (in.)

    # F2
    tot = 0.25 + 0.75 + m.TRUSS_B * 12 + 0.5 + 1.25
    h_in = (2.5 + 1.3 + tot + 1.9) / UPI
    fx = dax(fig, CX, 10.45 - h_in, CW, h_in)
    top = h_in * UPI
    dtitle(fx, 0, top, "F2", "1-hour floor between the flats", "Cut along a truss · 1 1/2\" = 1'-0\"", WCOL["F2"])
    y0 = 1.9
    b = [(y0, y0 + 0.625), (y0 + 0.625, y0 + 1.25), (y0 + 1.25, y0 + 1.75)]
    yt0 = y0 + 1.75
    mat(fx, B(SX, b[0][0], SX + SL, b[0][1]), "gypx")
    mat(fx, B(SX, b[1][0], SX + SL, b[1][1]), "gypx")
    for c in (1.5, 17.5):                                           # resilient channels @ 16 in.
        mat(fx, [(SX + c - 1.25, yt0), (SX + c + 0.75, yt0), (SX + c + 0.35, yt0 - 0.5), (SX + c - 0.75, yt0 - 0.5)], "metal", z=4)
    cavity(fx, SX, yt0, SX + SL, yt0 + 3.5, "sbatt", z=2.5)
    truss_elev(fx, SX, yt0, SL, m.TRUSS_B * 12)
    ytt = yt0 + m.TRUSS_B * 12
    mat(fx, B(SX, ytt, SX + SL, ytt + 0.75), "osb")
    mat(fx, B(SX, ytt + 0.75, SX + SL, ytt + 1.0), "floor")
    ddim(fx, (SX, yt0), (SX, ytt), 0.9, inch(m.TRUSS_B * 12))
    ddim(fx, (SX, y0), (SX, ytt + 1.0), 2.0, inch(tot))
    ddim(fx, (SX + 1.5, y0), (SX + 17.5, y0), -1.2, "16\" o.c.", size=4.8)
    txt(fx, SX + SL / 2, ytt + 1.75, "UNIT B", size=5.4, weight="bold", color=GREY)
    xa = SX + SL - 1.2
    callouts(fx, ST, ytt + 1.2, [
        ((xa, ytt + 0.88), "LVP on acoustic underlay\n(A-601)"),
        ((xa - 1.0, ytt + 0.38), "3/4 in. T&G subfloor,\nglued and screwed"),
        ((xa - 0.3, ytt - 0.75), "24 in. open-web floor\ntrusses @ 16 in. o.c.\n(S-202)"),
        ((xa - 2.0, yt0 + 2.6), "Sound batts, 3 1/2 in.\nmin., on the channels"),
        ((SX + 17.9, yt0 - 0.25), "Resilient channels across\nthe trusses @ 16 in. o.c.\nmax.; screws must miss\nthe trusses"),
        ((xa, mid(b[0]) + 0.3), "Two layers 5/8 in. Type X\ngypsum, joints staggered,\nface layer taped"),
        (None, "1-hour, generic designs:\nUL L521 / L528 family.\nArchitect confirms the\nlisting; build exactly to it"),
        (None, f"Unit A ceiling below:\n{ftin(m.CLG_A)} less 1/2 in. for\nthe channels"),
    ], fs=5.3, gap=0.7, align=True, ybot=0.2)

    # F3
    yF2 = 10.45 - h_in
    depth = 0.25 + 5.0 + RIGID_R10 + 4.0 + 2.0
    h_in = (2.5 + 3.3 + depth + 3.0) / UPI
    sx = dax(fig, CX, yF2 - 0.08 - h_in, CW, h_in)
    top = h_in * UPI
    dtitle(sx, 0, top, "F3", "Unit A slab on grade (rear)", "Section at the stem wall · 1 1/2\" = 1'-0\"", WCOL["F3"])
    yS = top - 2.5 - 3.3                    # top of slab
    xw1, xf1, xr = SX + m.CMU * 12, SX + m.CMU * 12 + RIGID_R10, SX + SL
    ybot = yS - (5.0 + RIGID_R10 + 4.0 + 2.0)
    mat(sx, B(SX, ybot, xw1, yS), "conc")                                    # stem wall
    mat(sx, B(xw1, yS - 5.0 - RIGID_R10, xf1, yS), "rigid")                  # edge strip
    mat(sx, B(xf1, yS - 5.0, xr, yS), "conc")                                # slab
    mat(sx, B(xf1, yS - 5.0 - RIGID_R10, xr, yS - 5.0), "rigid")
    line(sx, [(xr, yS - 5.0), (xf1, yS - 5.0), (xf1, yS)], color=BLUE, lw=1.0, z=6)   # vapour barrier
    mat(sx, B(xw1, yS - 5.0 - RIGID_R10 - 4.0, xr, yS - 5.0 - RIGID_R10), "stone")
    mat(sx, B(xw1, ybot, xr, yS - 5.0 - RIGID_R10 - 4.0), "earth")
    mat(sx, B(SX + m.EXT * 12, yS, xr, yS + 0.25), "floor")
    # W1 above (sill plate, sheathing, gypsum)
    cut_wood(sx, SX + osb_t, yS, SX + osb_t + 5.5, yS + 1.5)
    mat(sx, B(SX, yS, SX + osb_t, yS + 3.0), "osb")
    mat(sx, B(SX + osb_t, yS + 1.5, SX + osb_t + 5.5, yS + 3.0), "batt")
    mat(sx, B(SX + 6.0, yS + 0.25, SX + 6.5, yS + 3.0), "gyp")
    txt(sx, SX + 7.3, yS + 2.2, "W1 above", size=5.0, weight="bold", color=WCOL["W1"], ha="left")
    txt(sx, SX + 15.5, yS + 1.1, "UNIT A", size=5.4, weight="bold", color=GREY)
    ddim(sx, (SX, ybot), (xw1, ybot), -1.0, inch(m.CMU * 12), size=4.8)
    ddim(sx, (SX, yS - 5.0), (SX, yS), 1.0, "5\"", size=4.8)
    xa = xr - 1.2
    callouts(sx, ST, yS + 2.6, [
        ((xa, yS + 0.12), "LVP floor finish"),
        ((xa - 1.0, yS - 2.2), "5 in. concrete slab\n(S-103)"),
        ((xa - 2.2, yS - 5.0), "15-mil vapour barrier,\nseams taped"),
        ((xa - 3.4, yS - 6.0), "2 in. rigid foam, R-10,\nunder the whole slab"),
        ((xa - 1.0, yS - 9.0), "4 in. washed stone on\ncompacted subgrade"),
    ], fs=5.3, gap=0.4, align=True, ybot=ybot - 0.2)
    callouts(sx, SX + 11.5, ybot - 0.55, [
        (((xw1 + xf1) / 2, yS - 6.0), "R-10 edge strip, full slab depth. Stem wall (S-101):\nwhere it rises above the floor (rear-west corner),\nline it inside like W5, R-15"),
    ], fs=5.0, ha="left", land=0.0)

    # W5
    yF3 = yF2 - 0.08 - h_in
    layers = [(0.5, "gyp"), (0.75, "furr"), (RIGID_R15, "rigid"), (m.CONC * 12, "conc"), (0.18, "membrane"), (0.5, "board"), (2.0, "stone")]
    tot = sum(t for t, _ in layers)
    h_in = (2.5 + 0.4 + tot + 1.5) / UPI
    cx = dax(fig, CX, yF3 - 0.08 - h_in, CW, h_in)
    top = h_in * UPI
    dtitle(cx, 0, top, "W5", "Concrete retaining wall", "Plan cut · soil at the top · 1 1/2\" = 1'-0\"", WCOL["W5"])
    yb = 1.5
    b = wall_slice(cx, SX, yb, SL, layers, studs=(1.5, 17.5))
    ddim(cx, (SX, b[3][0]), (SX, b[3][1]), 1.0, inch(m.CONC * 12))
    ddim(cx, (SX, b[0][0]), (SX, b[2][1]), 1.0, inch(0.5 + 0.75 + RIGID_R15), size=4.6)
    ddim(cx, (SX + 1.5, yb), (SX + 17.5, yb), -1.0, "16\" o.c.", size=4.8)
    xa = SX + SL - 1.2
    callouts(cx, ST, b[-1][1] + 0.2, [
        ((xa, mid(b[6])), "Backfill: washed stone\n(S-102)"),
        ((xa - 1.2, mid(b[5])), "Drainage board, full\nheight, to the French drain"),
        ((xa - 2.4, mid(b[4])), "Sheet membrane on the\nconcrete, full height"),
        ((xa, mid(b[3])), "12 in. concrete wall,\nwest, north and east\n(S-102)"),
        ((xa - 1.0, mid(b[2])), "UTILITY ROOM ONLY:\n2 1/2 in. rigid foam,\nR-15 min., joints taped"),
        ((SX + 17.5, mid(b[1])), "1x3 furring @ 16 in. and\n1/2 in. moisture-resistant\ngypsum. Open garage\nside: bare concrete"),
    ], fs=5.3, gap=0.38, align=True, ybot=0.1)

    # ---------------- right column: R1, F1, energy table, air sealing ----------------
    RX = 9.7
    roof_eave(fig, RX, 7.25, CW, 3.2, eave_face)

    tot = 0.25 + 0.75 + m.TRUSS_A * 12 + 0.625
    h_in = (2.5 + 1.3 + tot + 1.4) / UPI
    gx = dax(fig, RX, 7.1 - h_in, CW, h_in)
    top = h_in * UPI
    dtitle(gx, 0, top, "F1", "Garage ceiling / Unit A floor", "Cut along a truss · 1 1/2\" = 1'-0\"", WCOL["F1"])
    y0 = 1.4
    mat(gx, B(SX, y0, SX + SL, y0 + 0.625), "gypx")
    yt0 = y0 + 0.625
    cavity(gx, SX, yt0, SX + SL, yt0 + R30_T, "batt", z=2.5)
    truss_elev(gx, SX, yt0, SL, m.TRUSS_A * 12)
    ytt = yt0 + m.TRUSS_A * 12
    mat(gx, B(SX, ytt, SX + SL, ytt + 0.75), "osb")
    mat(gx, B(SX, ytt + 0.75, SX + SL, ytt + 1.0), "floor")
    pipes = [(SX + 5.2, yt0 + 14.2, 1.19, BLUE), (SX + 13.0, yt0 + 15.6, 0.56, BLUE), (SX + 14.8, yt0 + 15.6, 0.56, ACCENT)]
    for (px, py, r, c) in pipes:
        gx.add_patch(Circle((px, py), r, fc=PAPER, ec=c, lw=0.9, zorder=6))
    ddim(gx, (SX, yt0), (SX, ytt), 0.9, inch(m.TRUSS_A * 12))
    ddim(gx, (SX, y0), (SX, ytt + 1.0), 2.0, inch(tot))
    txt(gx, SX + SL / 2, ytt + 1.75, "UNIT A (heated)", size=5.4, weight="bold", color=GREY)
    clr = math.floor(m.CLG_GAR * 12) / 12
    txt(gx, SX + SL / 2, 0.55, f"OPEN GARAGE (unheated) · {ftin(clr)} clear", size=4.8, weight="bold", color=GREY)
    xa = SX + SL - 1.2
    callouts(gx, ST, ytt + 1.2, [
        ((xa, ytt + 0.88), "LVP floor finish (A-601)"),
        ((xa - 1.0, ytt + 0.38), "3/4 in. T&G subfloor,\nglued and screwed"),
        ((xa - 0.3, ytt - 0.75), "20 in. open-web floor\ntrusses @ 16 in. o.c.\n(S-201)"),
        ((SX + 15.36, yt0 + 15.6), "Water, drain and other\nlines stay ABOVE the\ninsulation, on the warm\nside. Nothing below it"),
        ((xa - 1.5, yt0 + 6.5), "R-30 batts laid on the\nceiling board; R-20 on\nthe rim, full depth"),
        ((xa, y0 + 0.31), "5/8 in. Type X gypsum,\nscrews 6 in. o.c., taped\nand painted (IRC R302.6)"),
    ], fs=5.3, gap=0.42, align=True, ybot=0.2)

    # energy table + air-sealing notes
    yF1 = 7.1 - h_in
    rows = [["PART", "2015 IECC, 5A", "THIS SET"],
            ["Ceiling", "R-49", f"R1: R-49 blown, {inch(m.HEEL * 12)} raised heel"],
            ["Frame wall", "R-20 or 13+5", "W1: R-20 batts in 2x6"],
            ["Floor over garage", "R-30", "F1: R-30 batts + R-20 rim"],
            ["Slab on grade", "R-10, 2 ft", "F3: R-10 under all + edge"],
            ["Utility room wall", "R-15 cont.", "W5: R-15 rigid foam"],
            ["Windows, doors", "U 0.32 max", "See A-601"],
            ["Air leakage", "3 ACH50", "Blower-door test"]]
    yt = tbl(fig, bg, RX, yF1 - 0.42, [1.0, 0.95, 1.9], rows, fs=5.8, rh=0.175, title="ENERGY CODE VALUES")
    bg.text(RX, yt - 0.2, "AIR SEALING AND INSULATION", fontsize=7.0, fontweight="bold", va="top")
    note_lines(bg, RX, yt - 0.38, [
        "Seal before insulating: sill and top plates, window and door rough",
        "openings, the rim of each floor, and every hole to the attic or garage.",
        "The garage ceiling board and the Unit B ceiling board are the air",
        "barriers: tape every joint, seal or gasket every box.",
        "F1 is insulated at the bottom so the truss space is inside the heated",
        "envelope (2015 IECC R402.2.8): rim R-20 full depth, no gaps at the walls.",
        "Class I or II vapour retarder on the room side of W1 (kraft facing).",
        "Blower-door test 3 ACH50 max; confirm with the code official.",
    ], fs=5.5, lh=0.118)
    save(fig, "A-501", pdf)


def truss_elev(ax, x0, y0, L, depth, z=4.0):
    """Open-web floor truss in elevation: 1 1/2 in. deep flat chords and one V of webs."""
    mat(ax, B(x0, y0, x0 + L, y0 + 1.5), "wood", z=z)
    mat(ax, B(x0, y0 + depth - 1.5, x0 + L, y0 + depth), "wood", z=z)
    yb, yt = y0 + 1.5, y0 + depth - 1.5
    w, xm = 1.9, x0 + L / 2
    mat(ax, [(x0 + 0.4, yb), (x0 + 0.4 + w, yb), (xm + w / 2, yt), (xm - w / 2, yt)], "wood", z=z - 0.1)
    mat(ax, [(xm - w / 2, yt), (xm + w / 2, yt), (x0 + L - 0.4, yb), (x0 + L - 0.4 - w, yb)], "wood", z=z - 0.1)


def roof_eave(fig, left, bottom, w_in, h_in, eave_face):
    """R1: rear eave section at 1 in. = 1 ft (12 real inches per paper inch)."""
    upi = 12.0
    ax = dax(fig, left, bottom, w_in, h_in, upi=upi, x0=-21.0, y0=-12.6)
    top = -12.6 + h_in * upi
    dtitle(ax, -21.0, top, "R1", "Roof, rear eave and rakes", "Section at the rear wall · 1\" = 1'-0\"", WCOL["R1"])
    p = m.ROOF_PITCH
    rake_face = m.SB_SIDE + m.M - RAKE / 12
    heel = m.HEEL * 12
    osb_t = m.EXT * 12 - 6.0
    xi = m.EXT * 12
    Rr = 22.0
    dv = 3.5 / math.cos(math.atan(p))

    def yt(x):
        return heel + p * x

    # wall W1 below the plate
    mat(ax, B(0, -12.6, osb_t, yt(0) - dv), "osb", z=4)
    cavity(ax, osb_t, -12.6, osb_t + 5.5, -3.0, "batt")
    cut_wood(ax, osb_t, -3.0, osb_t + 5.5, -1.5)
    cut_wood(ax, osb_t, -1.5, osb_t + 5.5, 0.0)
    mat(ax, B(osb_t + 5.5, -12.6, xi, -0.625), "gyp")
    mat(ax, B(-0.45, -12.6, -0.12, 1.6), "siding")
    # ceiling and insulation
    mat(ax, B(xi, -0.625, Rr, 0.0), "gyp")
    x16 = (R49_T - heel) / p
    mat(ax, [(osb_t, 0), (Rr, 0), (Rr, R49_T), (x16, R49_T), (osb_t, yt(osb_t))], "blown", z=2.5, lw=0.3)
    # truss
    mat(ax, B(osb_t, 0, Rr, 3.5), "wood", z=4)
    mat(ax, [(osb_t, 3.5), (osb_t + 3.5, 3.5), (osb_t + 3.5, yt(osb_t + 3.5) - dv), (osb_t, yt(osb_t) - dv)], "wood", z=4)
    mat(ax, [(-EAVE_REAR, yt(-EAVE_REAR)), (Rr, yt(Rr)), (Rr, yt(Rr) - dv), (-EAVE_REAR, yt(-EAVE_REAR) - dv)], "wood", z=4.2)
    # roof deck and shingles
    xo = -EAVE_REAR - 0.75
    mat(ax, [(xo, yt(xo)), (Rr, yt(Rr)), (Rr, yt(Rr) + 0.47), (xo, yt(xo) + 0.47)], "osb", z=4.3)
    line(ax, [(xo - 0.6, yt(xo - 0.6) + 0.72), (Rr, yt(Rr) + 0.72)], lw=1.6, color="#3a3f45", z=5)
    # sub-fascia, fascia, soffit
    ye = yt(-EAVE_REAR)
    cut_wood(ax, -EAVE_REAR, ye - 5.5, -EAVE_REAR + 1.5, ye, z=4.4)
    mat(ax, B(xo, ye - 6.5, -EAVE_REAR, ye), "siding", z=4.4)
    ys = ye - 5.5
    mat(ax, B(-EAVE_REAR + 1.5, ys, -0.12, ys + 1.5), "wood", z=4)
    mat(ax, B(-EAVE_REAR, ys - 0.625, -0.45, ys), "gypx", z=4.4)
    mat(ax, B(xo, ys - 0.95, -0.45, ys - 0.625), "siding", z=4.4)
    line(ax, [(xo, ye - 0.6), (xo - 5.0, ye - 0.6), (xo - 5.0, ye - 2.4), (xo - 3.6, ye - 4.2), (xo, ye - 4.2)], lw=0.9, color=GREY, z=5)
    line(ax, [(Rr, -0.625), (Rr, yt(Rr) + 0.72)], lw=0.4, color=GREY, ls=(0, (3, 2)), z=6)
    # dimensions
    ddim(ax, (0, 0), (0, heel), -9.2, f"{inch(heel)} heel", size=4.8)
    ddim(ax, (-EAVE_REAR, ys - 0.95), (0, ys - 0.95), -1.5, inch(EAVE_REAR), size=4.8)
    # pitch mark
    xa, ya = 13.0, yt(19.0) + 1.6
    line(ax, [(xa, ya), (xa + 6, ya), (xa + 6, ya + 2), (xa, ya)], lw=0.5, z=7)
    txt(ax, xa + 3, ya - 0.7, "12", size=4.6)
    txt(ax, xa + 6.8, ya + 1.0, f"{p * 12:.0f}", size=4.6)
    # notes
    txt(ax, 14.6, 9.4, f"R-49 BLOWN INSULATION\nabout {R49_T:.0f} in. deep", size=5.0, weight="bold", box=True, z=9)
    txt(ax, 15.2, -6.2, "UNIT B", size=5.4, weight="bold", color=GREY)
    callouts(ax, -5.4, top - 3.1, [
        ((7.0, yt(7.0) + 0.75), "Asphalt shingles, synthetic underlay,\nice barrier at the eave (A-105)"),
        ((3.0, yt(3.0) + 0.25), "7/16 in. OSB with H-clips (S-203)"),
        ((-5.0, yt(-5.0) - dv / 2), "Roof trusses @ 24 in. o.c. (S-203)"),
        ((xo - 2.5, ye - 0.6), "Drip edge, fascia, gutter (A-105)"),
    ], fs=5.1, gap=0.5, ha="right", land=0.8)
    callouts(ax, -20.8, ys - 4.2, [
        ((-6.5, ys - 0.31), "REAR EAVE AND SIDE RAKES: 5/8 in.\nType X exterior gypsum soffit board,\nNO vents. 1 hour from below, IRC\nTable R302.1(1): rear eave edge is\n"
                            f"{ftin(eave_face)}, {inch(RAKE)} rakes {ftin(rake_face)} from the lot line"),
    ], fs=5.1, land=0.0)
    callouts(ax, 8.6, -2.0, [
        ((11.0, -0.31), "5/8 in. gypsum ceiling, taped\n(air barrier); seal top plates"),
    ], fs=5.1, land=0.0)
    txt(ax, 8.6, -9.2, "W1 wall: sheathing runs\nup over the heel", size=5.1, ha="left", va="top")
    line(ax, [(8.3, -9.8), (osb_t / 2, 2.0)], lw=0.35, z=8)
    return ax


# ----------------------------------------------------------------------------
# A-601
# ----------------------------------------------------------------------------
def opening_tags(ax):
    """Door tags (circles) and window tags (diamonds), placed as plans.draw_door / draw_window place them."""
    for d in m.DOORS:
        x0, y0, x1, y1 = m.door_cut(d)
        (hx, hy), (ax_, ay_), (sx, sy) = m.door_hinge(d)
        cx, cy = (x0 + x1) / 2 - sx * 0.95, (y0 + y1) / 2 - sy * 0.95
        ax.add_patch(Circle((cx, cy), 0.62, fc=PAPER, ec=INK, lw=0.5, zorder=10))
        txt(ax, cx, cy, d["tag"], size=4.4, weight="bold", z=11)
    for (tag, w_, s0, s1, note) in m.WINDOWS:
        q = m.win_quad(w_, s0, s1)
        ox, oy = {"S": (0, -1.25), "N": (0.38, 1.25), "E": (1.5, 0), "W": (-1.5, 0)}[w_]
        cx, cy = (q[0][0] + q[1][0]) / 2 + ox, (q[0][1] + q[1][1]) / 2 + oy
        poly(ax, [(cx - 0.95, cy), (cx, cy + 0.62), (cx + 0.95, cy), (cx, cy - 0.62)], fc=PAPER, ec=INK, lw=0.5, z=10)
        txt(ax, cx, cy, tag, size=4.4, weight="bold", z=11)


def door_rows():
    rows = [["TAG", "LOCATION", "W x H", "TYPE", "DOOR", "HARDWARE"]]
    h = ftin(DOOR_H)
    for d in m.DOORS:
        tag, loc = d["tag"], d["note"].split(",")[0]
        w = ftin(round(d["w"] * 12) / 12)
        low = d["note"].lower()
        if "20-min" in low:
            door_, hw = "Solid core, 20-min. rated", "Closer, keyed, deadbolt"
        elif "glass" in low:
            door_, hw = "Full-glass insulated, tempered", "Keyed lever, deadbolt"
        elif d["kind"] == "bifold":
            door_, hw = "Hollow-core flush bifold", "Pulls, track"
        else:
            door_ = "Hollow-core flush"
            hw = "Privacy lever" if ("bedroom" in low or "bath" in low) else "Passage lever"
            if "grille" in low:
                door_ += ", return grille"
            if "pair" in low:
                hw = "Pull, ball catch"
        typ = "Bifold" if d["kind"] == "bifold" else ("Pair leaf" if "pair" in low else "Swing")
        rows.append([tag, loc, f"{w} x {h}", typ, door_, hw])
    rows.append(["G1", "Street door to the stair", f"{ftin(m.ENTRY[1] - m.ENTRY[0])} x {h}", "Swing",
                 "Insulated steel, steel frame", "Closer, keyed lock"])
    rows.append(["G2", "Utility room (garage level)", f"{ftin(round((m.UTIL_DOOR[1] - m.UTIL_DOOR[0]) * 12) / 12)} x {h}", "Swing",
                 "Insulated steel, steel frame", "Keyed lock, swings in"])
    return rows


def window_rows():
    per = Counter(t for t, *_ in m.WINDOWS)
    where = {}
    for (t, w_, s0, s1, note) in m.WINDOWS:
        where.setdefault(t, []).append(note)
    rows = [["TAG", "PER FLAT", "BLDG", "W x H", "TYPE", "SILL", "WHERE AND REMARKS"]]
    d14 = [d for d in m.DOORS if d["tag"] == "D14"][0]
    for tag, desc in m.WINDOW_TYPES.items():
        size, rest = desc.split(" vinyl ")
        typ = rest.split(",")[0].capitalize()
        s = re.search(r"sill (\d+) in\.", desc)
        notes_ = where[tag]
        if len(notes_) > 1:
            nums = ", ".join(re.search(r"(\d)", n).group(1) for n in notes_)
            rem = f"Bedrooms {nums}: escape, note 1"
        else:
            rem = notes_[0].split(",")[0]
        temp = "tempered" in desc
        for (t, w_, s0, s1, note) in m.WINDOWS:          # within 24 in. of the porch door: tempered (IRC R308.4.2)
            if t == tag and w_ == "S" and d14["wall"] == "h" and min(abs(d14["s0"] - s1), abs(s0 - d14["s1"])) < 2.0:
                temp = True
        if temp:
            rem += "; tempered"
        rows.append([tag, per[tag], per[tag] * 2, size, typ, f"{s.group(1)} in." if s else "See A-201", rem])
    rows.append(["", sum(per.values()), sum(per.values()) * 2, "", "", "", "All: vinyl frame, U 0.32 max"])
    return rows


def sheet_a601(pdf):
    d14 = [d for d in m.DOORS if d["tag"] == "D14"][0]
    w2 = [w for w in m.WINDOWS if w[0] == "W2"][0]
    gap_in = (d14["s0"] - w2[3]) * 12
    notes = [
        ("Doors", [
            f"All doors {ftin(DOOR_H)} high. Interior doors:\n"
            "hollow-core flush, pre-hung, 1 3/8 in.,\n"
            "painted, lever handles.\n"
            "D1 unit entries are in the 1-hour stair\n"
            "wall: 20-minute rated, self-closing,\n"
            "latching, smoke gasket.\n"
            "D14, G1, G2: exterior grade, weather-\n"
            "stripped, U 0.32 max, sill pan flashing.\n"
            "No door swings toward a car: G2 swings\n"
            "into the utility room.",
        ]),
        ("Windows", [
            "Vinyl, double glazed, low-E, U 0.32 max\n"
            "(2015 IECC zone 5A). Screens on all\n"
            "operable sash.\n"
            "Tempered glass (IRC R308.4): W3 at the\n"
            f"stair, door D14, and W2 ({gap_in:.0f} in. from\n"
            "door D14, under the 24 in. rule).\n"
            "Sills are 24 in. or more above the floor,\n"
            "so no fall guards are needed (R312.2).\n"
            "Flash every opening into the housewrap,\n"
            "see A-501 W1.",
        ]),
        ("Finishes", [
            "Rental grade: durable, easy to repair,\n"
            "not top of the line. Owner picks colours.\n"
            "Gypsum: level 4 finish, primer + 2 coats.\n"
            "Rated boards and insulation: A-501.",
        ]),
        ("Preliminary", [
            "Check sizes against the framing before\n"
            "ordering. Architect confirms ratings.",
        ]),
    ]
    fig, bg = new_sheet("A-601", TITLE["A-601"], "3/16\" = 1'-0\"", notes)

    # ---------------- key plan ----------------
    vx, vy = (5.0, 46.0), (5.8, 42.3)
    ax = plan_axes(fig, 0.5, 3.62, vx, vy, FPI)
    unit_plan(ax, "arch", "A", furniture=False, labels=False, tags=False)
    opening_tags(ax)
    for k, (x, y) in ROOM_LABELS.items():
        rot = 90 if k.startswith("BATH") or k == "HALL" else 0
        name = k.replace("CLOSET ", "CL ")
        if k == "CLOSET 1":                  # keep clear of door tags D8 and D9
            x, y = (m.CL_X0 + m.CL_X1) / 2, m.CL_Y - 0.42
        if k == "CLOSET 2":
            x, y = (m.CL_X0 + m.CL_X1) / 2, m.CL_Y + m.PART + 0.42
        txt(ax, x, y, name, size=4.8, color=GREY, rot=rot, z=8)
    txt(ax, (m.SHAFT_U[0] + m.SHAFT_U[1]) / 2, 12.2, "COMMON\nSTAIR", size=4.6, color=GREY)
    txt(ax, 28.0, 8.0, "PORCH", size=4.8, color=GREY)
    txt(ax, 31.0, 41.9, "KEY PLAN: DOOR AND WINDOW TAGS", size=8.5, weight="bold", ha="left", va="bottom")
    txt(ax, 31.0, 41.75, "Unit A shown; Unit B is the same · 3/16\" = 1'-0\"", size=5.4, color=GREY, ha="left", va="top")
    ax.add_patch(Circle((31.9, 39.9), 0.62, fc=PAPER, ec=INK, lw=0.5, zorder=10))
    txt(ax, 31.9, 39.9, "D1", size=4.4, weight="bold", z=11)
    txt(ax, 33.2, 39.9, "Door tag, see the door schedule", size=5.4, ha="left")
    poly(ax, [(31.9 - 0.95, 38.4), (31.9, 39.02), (31.9 + 0.95, 38.4), (31.9, 37.78)], fc=PAPER, ec=INK, lw=0.5, z=10)
    txt(ax, 31.9, 38.4, "W1", size=4.4, weight="bold", z=11)
    txt(ax, 33.2, 38.4, "Window tag, see the window schedule", size=5.4, ha="left")
    txt(ax, 33.2, 37.2, "G1, G2: garage-level doors, see A-101", size=5.4, ha="left")
    north_arrow(ax, 43.9, 35.0, 1.2, 5.5)
    scale_bar(ax, 32.0, 35.6, 8, 4, 0.36, size=4.8)

    # ---------------- schedules, right column ----------------
    TX = 8.4
    yb = tbl(fig, bg, TX, 10.22, [0.34, 1.2, 0.78, 0.44, 1.38, 1.06], door_rows(), fs=6.0, rh=0.176,
             title="DOOR SCHEDULE", sub=f"all doors {ftin(DOOR_H)} high")
    yb = note_lines(bg, TX, yb - 0.06, [
        f"D1 to D{len(m.DOORS)} occur in each flat ({2 * len(m.DOORS)} doors in all). G1 and G2 occur once, at the garage level (A-101).",
        "D12 + D13 are the two leaves of one 4'-0\" pair on the mechanical closet (air handler and water heater): both must open",
        "fully for service. Return grille in leaf D12 and transfer grilles over the bedroom doors: M-102, M-103.",
    ], fs=5.4)
    yb = tbl(fig, bg, TX, yb - 0.3, [0.34, 0.54, 0.4, 0.8, 0.74, 0.62, 1.76], window_rows(), fs=6.0, rh=0.176,
             title="WINDOW SCHEDULE", sub="frame sizes; rough openings by the window maker")
    yb = note_lines(bg, TX, yb - 0.06, [
        "1. Escape windows (IRC R310): 5.7 sf clear opening, 20 in. min. clear width, 24 in. min. clear height,",
        "    sill 44 in. max above the floor. Order W1 as an egress casement and check the maker's",
        "    clear-opening table before ordering.",
        "2. W3 is in the common stair, one at each flat level. Its sill height is set on the elevations.",
    ], fs=5.4)
    yb = tbl(fig, bg, TX, yb - 0.3, [0.98, 0.52, 0.4, 3.3], fixture_rows(), fs=5.8, rh=0.176,
             title="FIXTURE AND APPLIANCE SCHEDULE", sub="all electric, no gas")
    note_lines(bg, TX, yb - 0.06, [
        "Each flat has its own of everything in this table. Circuits: E-201. Piping: P-201. Equipment: M-201.",
    ], fs=5.4)

    # ---------------- room finish schedule, under the plan ----------------
    yb = tbl(fig, bg, 0.5, 3.3, [1.32, 1.72, 0.74, 1.5, 1.32, 1.1], finish_rows(), fs=6.0, rh=0.185,
             title="ROOM FINISH SCHEDULE", sub="both flats unless noted")
    note_lines(bg, 0.5, yb - 0.06, [
        "LVP = luxury vinyl plank, 12-mil wear layer min. MR = moisture-resistant gypsum board. Baths: caulk the floor edge to the tub and the base.",
        "Kitchen: laminate counters and island top, 25 in. deep, on 24 in. base cabinets (A-401). Garage: 4 in. painted yellow stall lines and numbers 1 to 3 (A-101).",
    ], fs=5.4)
    save(fig, "A-601", pdf)


def fixture_rows():
    S = m.SIZES
    hp = f"{m.HP_SIZE[0] * 12:.0f} x {m.HP_SIZE[1] * 12:.0f} in."
    nt, nw, nl = len(m.TUBS), len(m.WCS), len(m.LAVS)
    items = [
        ("Range", 1, f"{S['Range']} electric, freestanding, with anti-tip bracket"),
        ("Range hood", 1, f"{S['Range']} wide, ducted to the front wall"),
        ("Refrigerator", 1, S["Refrigerator"]),
        ("Dishwasher", 1, f"{S['Dishwasher']} built-in, in the island"),
        ("Kitchen sink", 1, f"Stainless steel, in a {S['Sink base']} base in the island"),
        ("Washer / dryer", 1, f"{S['Washer/dryer'][0].upper()}{S['Washer/dryer'][1:]}; electric dryer"),
        ("Tub / shower", nt, f"{S['Bathtub'].split(',')[0]}, one-piece fibreglass tub/shower unit"),
        ("Toilet", nw, S["Toilet"][0].upper() + S["Toilet"][1:]),
        ("Lavatory", nl, S["Vanity"]),
        ("Water heater", 1, S["Water heater"].replace(" of its own flat", "")),
        ("Air handler", 1, f"{S['Air handler'][0].upper()}{S['Air handler'][1:]}"),
        ("Heat pump", 1, f"Outdoor unit, side discharge, {hp}, on a pad in the west side yard"),
    ]
    return [["ITEM", "PER FLAT", "BLDG", "SIZE AND TYPE"]] + [[a, n, 2 * n, t] for a, n, t in items]


def finish_rows():
    g, gc = "Gypsum, painted", "Gypsum, flat white"
    return [
        ["ROOM", "FLOOR", "BASE", "WALLS", "CEILING", "REMARKS"],
        ["Living / kitchen", "LVP", "Vinyl, 4 in.", g, gc, "Laminate counters"],
        ["Hall", "LVP", "Vinyl, 4 in.", g, gc, "Duct soffit at 7'-0\""],
        ["Bedrooms 1, 2, 3", "LVP", "Vinyl, 4 in.", g, gc, ""],
        ["Closets", "LVP", "Vinyl, 4 in.", g, gc, "Shelf and rod"],
        ["W/D, mechanical closet", "LVP", "Vinyl, 4 in.", "MR gypsum, painted", gc, "Water heater on a pan"],
        ["Baths 1, 2, 3", "Sheet vinyl or LVP", "Vinyl, caulked", "MR gypsum, semi-gloss", "MR gypsum, semi-gloss", "Fibreglass tub unit"],
        ["Common stair", "Vinyl treads and landings", "Vinyl, 4 in.", "5/8 Type X, painted", "5/8 Type X, painted", "See A-402"],
        ["Open garage", "Concrete, broom finish, sealed", "None", "Bare concrete", "5/8 Type X, painted", "Stall lines, numbers"],
        ["Utility room", "Concrete, sealed, floor drain", "None", "MR gypsum, painted", "5/8 Type X, painted", "Walls: A-501 W5"],
    ]


SHEETS = [("A-501", sheet_a501), ("A-601", sheet_a601)]
