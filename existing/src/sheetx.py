"""Sheet frame and plan drawing for the existing-house scan clean-up (390 Forest Ave and 441 Baird St)."""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))
import numpy as np  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402
from shapely.geometry import LineString, Point, Polygon  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

import common as c  # noqa: E402
from common import ACCENT, BLUE, GREY, INK, LIGHT, PAPER, ftin, line, plt, poly, txt  # noqa: E402

W, H, TB, MG = 17.0, 11.0, 3.3, 0.35
FIX = "#b3261e"       # fixes made
OPEN = "#b9770e"      # still open: check on site
ISSUE = "SCAN CLEAN-UP · 27 NOV 2026"


def sheet(number, title, house, sub, notes=None):
    fig = plt.figure(figsize=(W, H), facecolor=PAPER)
    bg = fig.add_axes([0, 0, 1, 1]); bg.set_xlim(0, W); bg.set_ylim(0, H); bg.axis("off")
    bg.add_patch(Rectangle((MG, MG), W - 2 * MG, H - 2 * MG, fill=False, lw=1.6, ec=INK))
    x0 = W - MG - TB
    bg.plot([x0, x0], [MG, H - MG], color=INK, lw=1.0)
    tx, top = x0 + 0.16, H - MG
    bg.text(tx, top - 0.38, house.upper(), fontsize=15, fontweight="bold", color=INK, va="center")
    bg.text(tx, top - 0.66, "MORGANTOWN, WV", fontsize=8.5, color=INK, va="center")
    bg.text(tx, top - 0.88, sub, fontsize=7.2, color=GREY, va="center")
    bg.plot([x0, W - MG], [top - 1.08, top - 1.08], color=INK, lw=0.6)
    bg.text(tx, top - 1.30, "EXISTING HOUSE AS SCANNED", fontsize=7.6, color=INK, va="center")
    bg.text(tx, top - 1.48, "BEFORE / AFTER THE SCAN FIXES", fontsize=7.6, color=INK, va="center")
    bg.plot([x0, W - MG], [top - 1.68, top - 1.68], color=INK, lw=0.6)
    y = top - 1.93
    for head, lines in (notes or []):
        bg.text(tx, y, head.upper(), fontsize=7.0, fontweight="bold", color=INK, va="top"); y -= 0.19
        for ln in lines:
            col = FIX if ln.startswith("F") and ln[1:2].isdigit() else OPEN if ln.startswith("U") and ln[1:2].isdigit() else INK
            bg.text(tx, y, ln, fontsize=6.3, color=col, va="top", linespacing=1.25)
            y -= 0.142 * (ln.count("\n") + 1) + 0.035
        y -= 0.1
    by = MG
    bg.plot([x0, W - MG], [by + 2.35, by + 2.35], color=INK, lw=0.6)
    bg.add_patch(Rectangle((x0 + 0.12, by + 1.5), TB - 0.24, 0.75, fill=False, ec=ACCENT, lw=1.1))
    bg.text(x0 + TB / 2, by + 2.02, "FROM A PHONE SCAN · VERIFY ON SITE", fontsize=7.0, fontweight="bold", color=ACCENT, ha="center", va="center")
    bg.text(x0 + TB / 2, by + 1.74, "Not a survey. Sizes are good to about 2 in. per room.\nNothing inside walls, floors or ceilings is known.", fontsize=5.6,
            color=ACCENT, ha="center", va="center", linespacing=1.25)
    bg.plot([x0, W - MG], [by + 1.40, by + 1.40], color=INK, lw=0.6)
    bg.text(tx, by + 1.22, "SHEET TITLE", fontsize=5.6, color=GREY, va="center")
    import textwrap
    tl = textwrap.wrap(title.upper(), 30)[:2]
    for i, t in enumerate(tl):
        bg.text(tx, by + (0.98 if len(tl) == 1 else 1.05 - 0.16 * i), t, fontsize=9.2 if len(tl) == 1 else 8.2, fontweight="bold", color=INK, va="center")
    bg.text(tx, by + 0.66, "Red tags F = fixes made · amber tags U = still open", fontsize=5.8, color=INK, va="center")
    bg.text(tx, by + 0.30, ISSUE, fontsize=6.2, color=GREY, va="center")
    bg.text(W - MG - 0.14, by + 0.42, number, fontsize=20, fontweight="bold", color=INK, ha="right", va="center")
    return fig, bg


def axes(fig, left, bottom, xlim, ylim, fpi):
    ax = c.plan_axes(fig, left, bottom, xlim, ylim, fpi)
    return ax


def tag(ax, x, y, s, color=FIX, r=None, size=5.6):
    fpi = getattr(ax, "fpi", 6.0)
    r = r or 0.13 * fpi
    ax.add_patch(plt.Circle((x, y), r, fc=color, ec="white", lw=0.8, zorder=30))
    ax.text(x, y, s, fontsize=size, color="white", ha="center", va="center", fontweight="bold", zorder=31)


def tag_bg(bg, x, y, s, color=FIX):
    bg.add_patch(plt.Circle((x, y), 0.13, fc=color, ec="white", lw=0.8, zorder=30))
    bg.text(x, y, s, fontsize=5.6, color="white", ha="center", va="center", fontweight="bold", zorder=31)


def picture(fig, path, left, bottom, width, height):
    """Place an image inside a box (inches) keeping its proportions; returns the axes."""
    from PIL import Image
    im = Image.open(path)
    ar = im.width / im.height
    w, h = (width, width / ar) if width / ar <= height else (height * ar, height)
    ax = fig.add_axes([(left + (width - w) / 2) / W, (bottom + (height - h) / 2) / H, w / W, h / H])
    ax.imshow(im); ax.axis("off")
    for s in ax.spines.values():
        s.set_visible(False)
    return ax


def head(bg, x, y, title, sub=None, color=INK):
    bg.text(x, y, title.upper(), fontsize=9, fontweight="bold", color=color, va="bottom")
    if sub:
        bg.text(x, y - 0.06, sub, fontsize=6.0, color=GREY, va="top")


# ---------------------------------------------------------------------------- plan drawing
def draw_floor(ax, F, T, names=None, heights=None, furniture=True, label_size=5.0, dims=True, wall_fc="#2a2e33"):
    """F = one floor from the Polycam JSON; T maps plan inches to drawing feet. names: Polycam name -> (new name, assumed?)."""
    polys = {}
    for r in F["rooms"]:
        p = [T(q) for q in r["pts"]]
        polys[r["name"]] = Polygon(p).buffer(0)
        poly(ax, p, fc="#f7f8f9", ec="none", z=1)
    if furniture:
        for key, col in (("furniture", "#c9cdd2"), ("appliances", "#9aa1a9"), ("fixtures", "#7d8792")):
            for o in F[key]:
                if len(o["pts"]) >= 2:
                    q = [T(t) for t in o["pts"]]
                    ax.plot([a[0] for a in q], [a[1] for a in q], color=col, lw=0.35, zorder=2)
    for w in F["walls"]:
        poly(ax, [T(q) for q in w["pts"]], fc=wall_fc, ec=wall_fc, lw=0.3, z=5)
    for o in F["openings"] + F["doors"]:
        if len(o["pts"]) >= 4:
            poly(ax, [T(q) for q in o["pts"]], fc=PAPER, ec="#8d949c", lw=0.4, z=6)
        else:
            q = [T(t) for t in o["pts"]]
            ax.plot([a[0] for a in q], [a[1] for a in q], color="#5b6470", lw=0.6, zorder=7)
    for a_ in F.get("door_arcs", []):
        cx, cy = a_["center"]; mx, my = a_["major"]
        rr = math.hypot(mx, my); a0 = math.atan2(my, mx)
        ts = np.linspace(a_["start"], a_["end"], 24)
        pts = [T((cx + rr * math.cos(a0 + t), cy + rr * a_["ratio"] * math.sin(a0 + t))) for t in ts]
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color="#5b6470", lw=0.45, zorder=7)
    for o in F["windows"]:
        if len(o["pts"]) >= 4:
            poly(ax, [T(q) for q in o["pts"]], fc="#cfe3f7", ec=BLUE, lw=0.6, z=8)
    for r in F["rooms"]:
        p = polys[r["name"]]
        if p.is_empty:
            continue
        c0 = p.representative_point() if not p.contains(p.centroid) else p.centroid
        nm, assumed = (names or {}).get(r["name"], (r["name"], False))
        mr = p.minimum_rotated_rectangle
        x0, y0, x1, y1 = p.bounds
        big = p.area >= 45
        t1 = nm.upper() + (" ?" if assumed else "")
        ax.text(c0.x, c0.y + (0.55 if big else 0), t1, fontsize=label_size if big else label_size - 1.3, fontweight="bold", ha="center", va="center",
                color=OPEN if assumed else INK, zorder=12, bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.85))
        if big and dims:
            # clear size = the largest axis-aligned rectangle through the centre point (good for near-rectangular rooms)
            ww, dd = _clear_size(p, c0)
            ht = (heights or {}).get(r["name"])
            s2 = f"{ftin(ww)} x {ftin(dd)} · {p.area:.0f} sf"
            ax.text(c0.x, c0.y - 0.35, s2, fontsize=label_size - 1.0, ha="center", va="center", color=INK, zorder=12, bbox=dict(fc="white", ec="none", pad=0.5, alpha=0.85))
            if ht:
                ax.text(c0.x, c0.y - 1.15, f"ceiling {ht}", fontsize=label_size - 1.2, ha="center", va="center", color=FIX, zorder=12,
                        bbox=dict(fc="white", ec="none", pad=0.5, alpha=0.85))
    return polys


def _clear_size(p, c0):
    hx = LineString([(c0.x - 200, c0.y), (c0.x + 200, c0.y)]).intersection(p)
    hy = LineString([(c0.x, c0.y - 200), (c0.x, c0.y + 200)]).intersection(p)

    def seg_len(g):
        if g.is_empty:
            return 0.0
        parts = list(g.geoms) if hasattr(g, "geoms") else [g]
        best = 0.0
        for s in parts:
            if s.distance(c0) < 0.05:
                best = max(best, s.length)
        return best or max(s.length for s in parts)
    return seg_len(hx), seg_len(hy)


def uncaptured_exterior(F, T):
    """Stretches of the floor's outer boundary with no wall, door or window drawn by Polycam (as line segments in feet)."""
    rooms = [Polygon([T(q) for q in r["pts"]]).buffer(0) for r in F["rooms"]]
    if not rooms:
        return []
    u = unary_union([r.buffer(0.35) for r in rooms]).buffer(-0.35)
    solid = unary_union([Polygon([T(q) for q in w["pts"]]).buffer(0) for w in F["walls"] if len(w["pts"]) >= 4]
                        + [Polygon([T(q) for q in w["pts"]]).buffer(0) for w in F["windows"] + F["doors"] + F["openings"] if len(w["pts"]) >= 4])
    out = []
    geoms = list(u.geoms) if hasattr(u, "geoms") else [u]
    for g in geoms:
        ring = g.exterior
        n = max(int(ring.length / 0.25), 8)
        pts = [ring.interpolate(i / n, normalized=True) for i in range(n + 1)]
        run = []
        for pt in pts:
            if solid.distance(pt) > 0.6:
                run.append((pt.x, pt.y))
            else:
                if len(run) >= 8:
                    out.append(run)
                run = []
        if len(run) >= 8:
            out.append(run)
    return out


def north(ax, x, y, vec, r=1.6):
    dx, dy = vec
    n = math.hypot(dx, dy); dx, dy = dx / n, dy / n
    ax.add_patch(plt.Circle((x, y), r, fill=False, lw=0.6, ec=INK, zorder=20))
    ax.annotate("", xy=(x + dx * r * 0.9, y + dy * r * 0.9), xytext=(x - dx * r * 0.7, y - dy * r * 0.7), arrowprops=dict(arrowstyle="-|>", lw=1.0, color=INK), zorder=21)
    ax.text(x + dx * (r + 0.7), y + dy * (r + 0.7), "N", fontsize=6.5, fontweight="bold", ha="center", va="center", zorder=21)


def scale_bar(ax, x, y, total=12, step=4):
    c.scale_bar(ax, x, y, total, step, 0.35, size=5.0)


def save(fig, number, pdf):
    fig.savefig(os.path.join(HERE, "drawings", "png", f"{number}.png"), dpi=200, facecolor=PAPER)
    pdf.savefig(fig, facecolor=PAPER)
    plt.close(fig)
