"""General sheets of the Rev E set: G-001 cover, G-002 code analysis, G-003 variance request, G-004 trade packages.

Every number printed on these sheets is computed here from model.py, common.py (lot, LiDAR, county GIS)
or index.py. Text is wrapped by measuring it, so nothing runs out of its column.
"""
import functools
import math
import os
import re

import numpy as np
from matplotlib.font_manager import FontProperties, findfont, get_font
from matplotlib.ft2font import LOAD_NO_HINTING
from pyproj import Transformer
from shapely.geometry import LineString, Polygon, box
from shapely.ops import nearest_points, unary_union

import index
import model as m
from common import *  # noqa: F401,F403

X_TB = SHEET_W - MARGIN - TB_W          # left edge of the title block
LEFT = MARGIN + 0.30                    # left edge of the drawing area used for text
RIGHT = X_TB - 0.30                     # right edge of the drawing area used for text
TOP = SHEET_H - MARGIN
TINT = "#f3c9c4"
NB_FILL = "#d7dade"


# ----------------------------------------------------------------------------
# Text that is measured before it is placed
# ----------------------------------------------------------------------------
_FONTS = {}


def tw(s, fs, bold=False):
    """Width of a string in inches (Inter, as drawn)."""
    if bold not in _FONTS:
        _FONTS[bold] = get_font(findfont(FontProperties(family="Inter", weight="bold" if bold else "normal")))
    f = _FONTS[bold]
    f.set_size(fs, 72)
    f.set_text(s, 0.0, flags=LOAD_NO_HINTING)
    return f.get_width_height()[0] / 64.0 / 72.0


def wrap(s, width, fs, bold=False):
    out = []
    for para in str(s).split("\n"):
        cur = ""
        for word in para.split(" "):
            trial = word if not cur else cur + " " + word
            if cur and tw(trial, fs, bold) > width:
                out.append(cur)
                cur = word
            else:
                cur = trial
        out.append(cur)
    return out


def ftin_dn(v):
    """Feet and whole inches rounded down: a clear height must not be overstated."""
    total = int(math.floor(v * 12 + 1e-6))
    return f"{total // 12}'-{total % 12}\""


def frac_in(v, den=16):
    """Inches as a builder's fraction: 7.333 -> 7 5/16."""
    whole, num = divmod(round(v * den), den)
    if num == 0:
        return f"{whole}"
    g = math.gcd(num, den)
    return f"{whole} {num // g}/{den // g}"


class Flow:
    """A column of headings and wrapped paragraphs that keeps track of where it is."""

    def __init__(self, bg, x, y, w, fs=6.4, bottom=MARGIN + 0.25, name=""):
        self.bg, self.x, self.y, self.w, self.fs, self.bottom, self.name = bg, x, y, w, fs, bottom, name

    def pitch(self, fs=None):
        return (fs or self.fs) * 1.36 / 72

    def _lines(self, lines, x, fs, color, weight):
        p = self.pitch(fs)
        for i, ln in enumerate(lines):
            self.bg.text(x, self.y - (i + 0.5) * p, ln, fontsize=fs, color=color, va="center", fontweight=weight)
        self.y -= len(lines) * p

    def head(self, s, sub=None, color=INK, rule=True, fs=None):
        fs = fs or self.fs + 1.3
        self._lines(wrap(s.upper(), self.w, fs, True), self.x, fs, color, "bold")
        if sub:
            self.y -= 0.01
            self._lines(wrap(sub, self.w, self.fs - 0.6), self.x, self.fs - 0.6, GREY, "normal")
        self.y -= 0.045
        if rule:
            self.bg.plot([self.x, self.x + self.w], [self.y, self.y], color=color, lw=0.6)
        self.y -= 0.075

    def p(self, s, lead=None, indent=0.0, color=INK, weight="normal", after=0.06, fs=None):
        fs = fs or self.fs
        if lead is not None:
            self.bg.text(self.x, self.y - 0.5 * self.pitch(fs), lead, fontsize=fs, color=color, va="center",
                         fontweight="bold")
        self._lines(wrap(s, self.w - indent, fs, weight == "bold"), self.x + indent, fs, color, weight)
        self.y -= after

    def gap(self, h=0.12):
        self.y -= h

    def end(self):
        if self.y < self.bottom:
            print(f"   !! text column '{self.name}' runs {self.bottom - self.y:.2f} in. past its limit")
        return self.y


def wtable(bg, x, y, widths, rows, fs=6.0, head=True, zebra=True, pad=0.06, vpad=0.05):
    """Ruled table like common.table(), but every cell wraps inside its column and rows grow to fit.
    A cell is a string or (string, {"color": ..., "weight": ...})."""
    W = sum(widths)
    pitch = fs * 1.34 / 72
    y0 = y
    for r, row in enumerate(rows):
        cells = []
        for wd, cell in zip(widths, row):
            s, kw = (cell, {}) if isinstance(cell, str) else cell
            bold = (head and r == 0) or kw.get("weight") == "bold"
            cells.append((wrap(s, wd - 2 * pad, fs, bold), kw, bold))
        rh = max(len(c[0]) for c in cells) * pitch + 2 * vpad
        if head and r == 0:
            bg.add_patch(Rectangle((x, y - rh), W, rh, fc="#e3e6ea", ec="none"))
        elif zebra and r % 2 == 0:
            bg.add_patch(Rectangle((x, y - rh), W, rh, fc="#f6f7f8", ec="none"))
        cx = x
        for wd, (lines, kw, bold) in zip(widths, cells):
            for i, ln in enumerate(lines):
                bg.text(cx + pad, y - vpad - (i + 0.5) * pitch, ln, fontsize=fs, va="center",
                        color=kw.get("color", INK), fontweight="bold" if bold else "normal")
            cx += wd
        y -= rh
        bg.plot([x, x + W], [y, y], color=LIGHT, lw=0.4)
    bg.add_patch(Rectangle((x, y), W, y0 - y, fill=False, ec=INK, lw=0.6))
    return y


def tb_notes(blocks, fs=6.6):
    """Title-block notes: wrap each paragraph to the column and warn if the column would overflow."""
    out, used = [], 0.0
    for head, paras in blocks:
        lines = []
        for p_ in paras:
            wl = wrap(p_, TB_W - 0.34, fs)
            hang = "  " if p_[:2] in ("· ", "- ") else ""
            lines.append("\n".join([wl[0]] + [hang + w_ for w_ in wl[1:]]))
            used += 0.148 * len(wl) + 0.035
        out.append((head, lines))
        used += 0.19 + 0.12
    room = (TOP - 1.95) - (MARGIN + 2.62)
    if used > room:
        print(f"   !! title-block notes are {used - room:.2f} in. too long")
    return out


def audit(fig, number):
    """Review aid (AUDIT=1): report text that leaves the sheet, crosses the title block line or overlaps."""
    r = fig.canvas.get_renderer()
    d = fig.dpi
    items = []
    for ax in fig.axes:
        for t in ax.texts:
            if not t.get_text().strip():
                continue
            b = t.get_window_extent(r)
            items.append((b.x0 / d, b.y0 / d, b.x1 / d, b.y1 / d, t.get_text().replace("\n", " / ")[:40]))
    for (x0, y0, x1, y1, s) in items:
        if x0 < MARGIN + 0.04 or x1 > SHEET_W - MARGIN - 0.04 or y0 < MARGIN + 0.04 or y1 > TOP - 0.04:
            print(f"   {number} off sheet: {s!r}")
        elif x0 < X_TB - 0.02 < x1 or x0 < X_TB + 0.02 < x1:
            print(f"   {number} crosses title block: {s!r}")
    for i, a in enumerate(items):
        for b_ in items[i + 1:]:
            ox = min(a[2], b_[2]) - max(a[0], b_[0])
            oy = min(a[3], b_[3]) - max(a[1], b_[1])
            if ox > 0.03 and oy > 0.03 and a[0] < X_TB:
                print(f"   {number} overlap: {a[4]!r} / {b_[4]!r}")


def finish(fig, number, pdf):
    if os.environ.get("AUDIT"):
        audit(fig, number)
    save(fig, number, pdf)


# ----------------------------------------------------------------------------
# Numbers shared by the four sheets (all computed)
# ----------------------------------------------------------------------------
_CR = math.cos(math.atan(abs(REAR_SLOPE)))
_CW = math.cos(WEST_LEAN)
PARCELS = neighbour_parcels()
FOOTPRINTS = [Polygon(f) for f in building_footprints()]
LOT_P = Polygon(LOT)
OUT_P = Polygon(m.OUT_U)
L_REAR = LineString([LOT_NE, LOT_NW])
L_WEST = LineString([LOT_SW, LOT_NW])
L_EAST = LineString([LOT_SE, LOT_NE])
L_FRONT = LineString([LOT_SW, LOT_SE])
EXISTING = [b for b in FOOTPRINTS if b.representative_point().within(LOT_P.buffer(3))][0]   # the 1929 house (county GIS)


def envelope(rear, front=m.SB_FRONT, side=m.SB_SIDE):
    """Area left on the lot by the front and side setbacks and a given rear setback."""
    big = 300.0
    t, k = math.tan(WEST_LEAN), side / _CW
    c = rear / _CR
    p_ = LOT_P.intersection(box(-big, front, 50.0 - side, big))
    p_ = p_.intersection(Polygon([(k, 0), (k + big * t, big), (big, big), (big, 0)]))
    p_ = p_.intersection(Polygon([(-big, rear_y(-big) - c), (big, rear_y(big) - c), (big, -big), (-big, -big)]))
    return p_


def _parcel(label):
    return Polygon([p_ for p_ in PARCELS if p_["label"] == label][0]["ring"]).buffer(0)


def _neighbour(label, shared):
    par = _parcel(label)
    blds = [b for b in FOOTPRINTS if par.buffer(3).contains(b.representative_point())]
    near = min(blds, key=lambda b: b.distance(LOT_P))
    a, b = nearest_points(near, shared)
    return dict(parcel=par, bldg=near, to_line=near.distance(shared), to_bldg=near.distance(OUT_P),
                pts=(a.coords[0], b.coords[0]), cover=100 * sum(b_.area for b_ in blds) / par.area)


@functools.lru_cache(None)
def facts():
    f = dict(m.summary())
    f["lot"] = LOT_AREA_CALC
    f["avg"] = m.avg_grade()
    f["eave"] = m.EL_PLATE + m.HEEL                                   # top of roof at the wall line
    f["h_mean"] = (f["eave"] + m.EL_RIDGE_HI) / 2 - f["avg"]          # zoning height: mean roof height, highest ridge
    f["h_ridge"] = m.EL_RIDGE_HI - f["avg"]
    f["below"] = 100 * (f["avg"] - m.EL_GAR) / (m.EL_A - m.EL_GAR)    # share of the garage storey below average grade
    f["a_above"] = m.EL_A - f["avg"]
    f["porch_pct"] = 100 * (m.PORCH[2] - m.PORCH[0]) / m.FACADE_W
    f["porch_out"] = m.PORCH[3] - m.PORCH[1]
    f["hp_side"] = min((hx - m.HP_SIZE[1] / 2 - west_x(hy)) * _CW for hx, hy in m.HP)
    f["hp_behind"] = min(hy for _, hy in m.HP) - m.YF
    f["d_front"] = m.YF
    f["d_side"] = 50.0 - m.XE
    f["d_west"] = OUT_P.distance(L_WEST)
    f["d_rear"] = OUT_P.distance(L_REAR)
    f["depth_e"] = m.yr_o(m.XE) - m.YF
    f["depth_w"] = m.OUT_U[3][1] - m.YF
    f["env"] = {d: envelope(d) for d in (20.0, 10.0, 5.0)}
    f["rear_len"] = math.dist(LOT_NE, LOT_NW)
    f["w442"] = _neighbour("29-85", L_WEST)
    f["e441"] = _neighbour("29-83", L_EAST)
    f["n386"] = _neighbour("29-87", L_REAR)
    f["ex_rear"] = EXISTING.distance(L_REAR)
    f["ex_front"] = EXISTING.distance(L_FRONT)
    f["cut_rear_e"] = perp_to_rear(m.XE, m.Y_GR_O)                    # garage excavation to the rear line, east end
    f["cut_rear_w"] = perp_to_rear(m.xw_o(m.Y_GR_O), m.Y_GR_O)        # and west end
    f["cut_side"] = (50.0 - m.XE) + f["e441"]["to_line"]              # garage wall to the east neighbour's house
    xs = np.linspace(m.OUT_U[3][0] + 1, m.XE - 1, 12)
    f["g_line"] = float(np.mean([elev(x, rear_y(x)) for x in xs]))    # ground along the rear lot line
    wall = [p_ for p_ in f["n386"]["bldg"].exterior.coords if p_[1] < 67 and 12 < p_[0] < 47]
    f["g_house"] = float(np.mean([elev(x, y - 0.5) for x, y in wall]))  # ground at the rear neighbour's near wall
    f["eave_edge"] = f["eave"] - 1.0 * m.ROOF_PITCH                   # top of the rear eave, 12 in. out
    f["street_out"] = street_el(m.DRAIN_OUT[0])
    f["win"] = _glazing()
    return f

_WIN_FT = {}
for _k, _v in m.WINDOW_TYPES.items():
    _a = [int(v) for v in re.match(r"(\d+)'-(\d+)\" x (\d+)'-(\d+)\"", _v).groups()]
    _WIN_FT[_k] = ((_a[0] + _a[1] / 12) * (_a[2] + _a[3] / 12),
                   0.0 if "fixed" in _v else 0.5 if ("slider" in _v or "hung" in _v) else 1.0)


def _glazing():
    """IRC R303: window area and openable area as a share of floor area, by nominal window size."""
    rooms = {"BEDROOM 1": "Bedroom 1", "BEDROOM 2": "Bedroom 2", "BEDROOM 3": "Bedroom 3", "LIVING / KITCHEN": "Living"}
    out = {}
    for room, key in rooms.items():
        ws = [_WIN_FT[t] for (t, _w, _s0, _s1, note) in m.WINDOWS if note.startswith(key)]
        out[room] = (100 * sum(a for a, _ in ws) / m.area(room), 100 * sum(a * o for a, o in ws) / m.area(room))
    return out


@functools.lru_cache(None)
def noon_shadow(decl, n=48):
    """Estimate: how far the building's shadow reaches past the rear lot line at solar noon.
    Marches from points on the rear eave and the ridge toward true north over the LiDAR ground."""
    lon, lat = Transformer.from_crs(26917, 4326, always_xy=True).transform(*to_utm(25.0, 20.0))
    alt = 90.0 - lat + decl
    t = math.tan(math.radians(alt))
    az = math.radians(Y_AXIS_AZIMUTH)
    nx, ny = -math.sin(az), math.cos(az)
    tips = []
    for x in np.linspace(m.OUT_U[3][0], m.XE, n):
        for kind, (sx, sy, sz) in (("eave", (x, m.yr_o(x) + 1.0 / _CR, m.EL_PLATE + m.HEEL - m.ROOF_PITCH)),
                                   ("ridge", (x, m.ridge_y(x), m.ridge_el(x)))):
            d = 0.0
            while d < 150 and sz - d * t > elev(sx + nx * d, sy + ny * d):
                d += 0.25
            px, py = sx + nx * d, sy + ny * d
            tips.append((-perp_to_rear(px, py), px, py, sx, sy, sz, kind))
    return alt, tips


def shadow_reach(decl):
    alt, tips = noon_shadow(decl)
    return alt, max(t[0] for t in tips)


# ----------------------------------------------------------------------------
# Site drawing pieces
# ----------------------------------------------------------------------------
def draw_geom(ax, g, **kw):
    for q in ([g] if g.geom_type == "Polygon" else list(getattr(g, "geoms", []))):
        if q.geom_type == "Polygon" and q.area > 60:
            poly(ax, list(q.exterior.coords), **kw)


def site_base(ax, view, lot_lw=1.4):
    """Street pavement, neighbouring parcels and buildings (county GIS) and the lot outline."""
    x0, y0, x1, y1 = view
    vb = box(x0 - 6, y0 - 6, x1 + 6, y1 + 6)
    pars = [Polygon(p_["ring"]).buffer(0) for p_ in PARCELS if p_["id"] != SUBJECT_ID]
    pars = [p_ for p_ in pars if p_.intersects(vb)]
    row = vb.difference(unary_union([p_.buffer(0.3) for p_ in pars] + [LOT_P.buffer(0.3)]))
    draw_geom(ax, row.buffer(-7.5).buffer(1.5).buffer(-1.5), fc="#e3e5e8", ec="none", z=1)
    for p_ in pars:                      # county GIS lines, trimmed where they stray inside the tax-map lot
        draw_geom(ax, p_.difference(LOT_P.buffer(0.05)), fc="none", ec=GREY, lw=0.5, z=2)
    for b in FOOTPRINTS:
        if b.intersects(vb) and b is not EXISTING:
            poly(ax, list(b.exterior.coords), fc=NB_FILL, ec=GREY, lw=0.5, z=3)
    poly(ax, LOT, fc="none", ec=ACCENT, lw=lot_lw, z=7, ls=(0, (9, 2.5, 1.5, 2.5)))


def setback_lines(ax, rear=m.SB_REAR_CODE, lw=0.5):
    """The four R-2 minimum setback lines, drawn across the lot."""
    ls = (0, (4, 3))
    c = rear / _CR
    k = m.SB_SIDE / _CW
    line(ax, [(west_x(m.SB_FRONT), m.SB_FRONT), (50, m.SB_FRONT)], color=ACCENT, lw=lw, ls=ls, z=6)
    line(ax, [(50 - m.SB_SIDE, 0), (50 - m.SB_SIDE, rear_y(50 - m.SB_SIDE))], color=ACCENT, lw=lw, ls=ls, z=6)
    line(ax, [(k, 0), (west_x(46.0) + k, 46.0)], color=ACCENT, lw=lw, ls=ls, z=6)
    line(ax, [(LOT_NW[0], LOT_NW[1] - c), (50, LOT_NE[1] - c)], color=ACCENT, lw=lw, ls=ls, z=6)


def leader(ax, tip, at, s, size=5.4, color=INK, ha="left", va="center", weight="normal"):
    ax.annotate("", xy=tip, xytext=at, arrowprops=dict(arrowstyle="-|>", lw=0.5, color=color, shrinkA=0, shrinkB=0,
                                                       mutation_scale=5), zorder=12)
    off = 0.6 if ha == "left" else -0.6 if ha == "right" else 0.0
    txt(ax, at[0] + off, at[1], s, size=size, color=color, ha=ha, va=va, weight=weight, z=13, box=True)


# ----------------------------------------------------------------------------
# G-001  Cover sheet and summary
# ----------------------------------------------------------------------------
DISCIPLINES = [("G", "General"), ("C", "Civil and site"), ("A", "Architectural"), ("S", "Structural"),
               ("P", "Plumbing"), ("M", "Mechanical: heating and cooling"), ("E", "Electrical")]
INDEX_COLUMNS = [["G", "C"], ["A"], ["S"], ["P", "M"], ["E"]]


def key_plan(fig, left, bottom, fpi=30):
    f = facts()
    view = (-36.0, -22.0, 87.0, 62.0)
    ax = plan_axes(fig, left, bottom, (view[0], view[2]), (view[1], view[3]), fpi)
    site_base(ax, view, lot_lw=1.2)
    poly(ax, m.APRON, fc="#cfd6de", ec=INK, lw=0.4, z=4)
    poly(ax, m.OUT_U, fc=PAPER, ec=INK, lw=1.3, z=8)
    txt(ax, 27.0, 23.5, f"NEW BUILDING\n{m.FOOTPRINT:,.0f} sf footprint", size=5.2, weight="bold", z=9)
    dim(ax, LOT_SE, LOT_SW, 3.2, "50'-0\" front", size=5.0, color=ACCENT)
    txt(ax, 47.6, 19.0, "34'-0\"", size=5.0, color=ACCENT, rot=90, z=9)
    txt(ax, west_x(27.0) + 2.5, 27.0, "48'-0\"", size=5.0, color=ACCENT, rot=90 - math.degrees(WEST_LEAN), z=9)
    cx = f["w442"]["bldg"].centroid
    txt(ax, cx.x, cx.y, "442\nBAIRD", size=5.0, color=GREY)
    cx = f["e441"]["bldg"].centroid
    txt(ax, cx.x, cx.y, "441\nBAIRD", size=5.0, color=GREY)
    txt(ax, 30.0, 58.0, "386 FOREST AVE", size=5.0, color=GREY, box=True)
    txt(ax, 48.0, -14.0, "BAIRD STREET", size=5.6, color=GREY, weight="bold")
    north_arrow(ax, 78.0, -13.5, 4.6, 6.5)
    scale_bar(ax, -30.0, -17.5, 30, 10, 1.3, size=5.0)
    return ax


def sheet_g001(pdf):
    f = facts()
    notes = tb_notes([
        ("Property record", [
            "Owner of record: R & L RENTALS LLC",
            "Deed Book 1246, Page 78",
            "Parcel 31-13-0029-0084-0000",
            "Zoned R-2 (city zoning layer)",
            "Existing: 1929 house, 768 sf, to be removed",
            "Flood risk: low, no mapped flood zone",
        ]),
        ("Owner's fixed requirements", [
            "· All electric. No gas.",
            "· Two electric meters only, one per flat. Common loads are on Unit A's panel.",
            "· Everything separate per flat: panel, water meter, water heater, heat pump, air handler, washer and dryer.",
            "· Ducted central air. No mini-splits.",
            "· No sump pump: foundation water leaves by gravity.",
            "· No water pipe in the open garage.",
            "· No garage doors, door operators, cameras or heat cable.",
            "· Nothing built in the street right-of-way except the driveway apron and the buried drain outlet.",
            "· Rental-grade, durable finishes.",
        ]),
        ("Start here", [
            "G-002  codes and notes for every trade",
            "G-003  the one variance and the case for it",
            "G-004  which sheets each company gets",
        ]),
    ])
    fig, bg = new_sheet("G-001", index.TITLE["G-001"], "As noted", notes)
    L, R = MARGIN + 0.45, X_TB - 0.4
    bg.text(L, TOP - 0.62, PROJECT, fontsize=30, fontweight="bold", va="center")
    bg.text(L, TOP - 1.08, "Two-family dwelling: two stacked 3-bedroom / 3-bath flats over an open 3-car garage · "
            f"head-start drawing set, Rev {REV}", fontsize=11.5, va="center", color=INK)
    bg.text(L, TOP - 1.38, "Morgantown, Monongalia County, West Virginia 26505 · Tax District 13 (5th Ward), Map 29, "
            "Parcel 84 · Zoned R-2", fontsize=8, va="center", color=GREY)
    bg.plot([L, R], [TOP - 1.58, TOP - 1.58], color=INK, lw=1.0)
    ytop = TOP - 1.82
    gap = 0.34
    w1, w3 = 3.75, 4.12
    w2 = (R - L) - w1 - w3 - 2 * gap
    c1, c2, c3 = L, L + w1 + gap, L + w1 + gap + w2 + gap
    # column 1: what the set is
    fl = Flow(bg, c1, ytop, w1, fs=7.2, bottom=4.15, name="G-001 what this set is")
    fl.head("What this set is")
    fl.p("A coordinated head start for licensed professionals. Every discipline is drawn to the same "
         "dimensioned building model, so the architect and engineers who take the project over begin from a "
         "worked-out scheme instead of a blank page, and each trade can see its own scope early.")
    fl.gap(0.1)
    fl.head("What it is not", color=ACCENT)
    fl.p("Not engineered. Not stamped. Not for construction.", weight="bold", color=ACCENT)
    fl.p("No boundary survey, soil report or site visit is behind it. Lot lines come from tax-map dimensions "
         "and ground levels from aerial LiDAR. Every member size is a preliminary assumption. Each licensed "
         "professional must review, recalculate and take responsibility for their own sheets before anything "
         "is priced as final, permitted or built.")
    fl.gap(0.1)
    fl.head("Data behind it")
    for s in ("County tax map 09-0029: lot dimensions.",
              "County assessor record: owner, existing house, values.",
              "State 1 m LiDAR: ground levels (NAVD88 ft).",
              "County GIS parcels and building outlines: neighbours, accurate to about 3 to 5 ft.",
              "City of Morgantown Planning and Zoning Code, 2019 edition, and the city zoning layer."):
        fl.p(s, lead="·", indent=0.12, after=0.03)
    fl.end()
    # column 2: at a glance
    bg.text(c2, ytop - 0.07, "AT A GLANCE", fontsize=8.0, fontweight="bold", va="center")
    br = [f"BR{i} {ftin(m.room_dims(k)[0])} x {ftin(m.room_dims(k)[1])} clear, {m.area(k):.0f} sf"
          for i, k in enumerate(("BEDROOM 1", "BEDROOM 2", "BEDROOM 3"), 1)]
    rows = [
        ("Lot", f"50 ft on Baird St, 34 ft deep (east) to 48 ft (west), diagonal rear line. About "
                f"{f['lot']:,.0f} sf by tax-map dimensions ({LOT_AREA_DEED:,.0f} sf by deed)."),
        ("Footprint", f"{m.FOOTPRINT:,.0f} sf wedge: {ftin(m.FACADE_W)} wide at the street, "
                      f"{ftin(f['depth_e'])} deep (east) to {ftin(f['depth_w'])} (west)."),
        ("Lot coverage", f"{f['coverage']:.1f} % (50 % allowed)."),
        ("Height", f"{f['h_mean']:.1f} ft mean roof height above average grade EL {f['avg']:.1f} (35 ft allowed). "
                   f"Ridge {f['h_ridge']:.1f} ft. Two storeys over a basement garage."),
        ("Floor levels", f"Garage EL {m.EL_GAR:.1f} · Unit A EL {m.EL_A:.1f} · Unit B EL {m.EL_B:.1f}"),
        ("Each flat", f"{m.net_area():,.0f} sf net inside the walls, stair excluded. 3 bedrooms, 3 baths with "
                      f"60 in. tubs, living room and kitchen with island. Ceiling {ftin_dn(m.CLG_A)} (A), {ftin_dn(m.CLG_B)} (B)."),
        ("Bedrooms", "\n".join(br)),
        ("Parking", f"{len(m.CARS)} cars in the open garage ({len(m.CARS)} required). Opening "
                    f"{ftin(m.OPEN_W)} wide, {ftin_dn(m.OPEN_CLEAR_H)} clear, no doors."),
        ("Services", "All electric. One meter, panel, heat pump, water heater, washer and dryer per flat."),
        ("Variance", ("One only: rear setback 20 ft to 5 ft (G-003). Everything else meets the R-2 rules as drawn.",
                      {"color": ACCENT, "weight": "bold"})),
    ]
    yb = wtable(bg, c2, ytop - 0.22, [0.95, w2 - 0.95], [((k, {"weight": "bold"}), v) for k, v in rows],
                fs=6.8, head=False)
    if yb < 4.15:
        print(f"   !! G-001 at-a-glance table is {4.15 - yb:.2f} in. too tall")
    # column 3: key plan and the "measured" box
    bg.text(c3, ytop - 0.07, "KEY PLAN", fontsize=8.0, fontweight="bold", va="center")
    bg.text(c3 + w3, ytop - 0.07, "1\" = 30'-0\" · lot from tax map, neighbours from county GIS", fontsize=5.4,
            color=GREY, va="center", ha="right")
    key_plan(fig, c3 + 0.01, ytop - 0.24 - 2.8)
    by1 = ytop - 0.24 - 2.8 - 0.16
    box_ = Flow(bg, c3 + 0.12, by1 - 0.12, w3 - 0.24, fs=7.0, bottom=4.15, name="G-001 measured box")
    box_.head("How this set stays measured", color=BLUE, rule=False)
    box_.p("Every plan in the set is generated from one dimensioned model of the building (src/model.py). "
           "Its checks stop the build if furniture, doors, fixtures or setbacks do not fit, so a sheet cannot "
           "show something that was only drawn in.", after=0.0)
    by0 = box_.end() - 0.1
    bg.add_patch(Rectangle((c3, by0), w3, by1 - by0, fill=False, ec=BLUE, lw=1.0))
    # sheet index
    yi = 3.92
    bg.plot([L, R], [yi + 0.14, yi + 0.14], color=INK, lw=1.0)
    bg.text(L, yi - 0.06, f"SHEET INDEX · {len(index.INDEX)} SHEETS", fontsize=8.0, fontweight="bold", va="center")
    bg.text(R, yi - 0.06, "Each trade's own package of sheets is listed on G-004", fontsize=6.0, color=GREY,
            va="center", ha="right")
    fs, pitch, numw = 6.4, 0.176, 0.52
    names = dict(DISCIPLINES)
    need = []
    for grp in INDEX_COLUMNS:
        ws = [tw(t, fs) for n, t, _ in index.INDEX if n[0] in grp] + [tw(names[g].upper(), fs + 0.6, True) - numw for g in grp]
        need.append(numw + max(ws))
    spare = ((R - L) - sum(need)) / (len(need) - 1)
    if spare < 0.12:
        print("   !! G-001 sheet index columns are too wide")
    x = L
    for grp, wd in zip(INDEX_COLUMNS, need):
        y = yi - 0.36
        for g in grp:
            bg.text(x, y, names[g].upper(), fontsize=fs + 0.6, fontweight="bold", va="center")
            bg.plot([x, x + wd], [y - 0.095, y - 0.095], color=INK, lw=0.5)
            y -= pitch * 1.25
            for n, t, _ in index.INDEX:
                if n[0] == g:
                    bg.text(x, y, n, fontsize=fs, fontweight="bold", va="center")
                    bg.text(x + numw, y, t, fontsize=fs, va="center")
                    y -= pitch
            y -= pitch * 0.75
        if y < MARGIN + 0.2:
            print("   !! G-001 sheet index runs off the sheet")
        x += wd + spare
    finish(fig, "G-001", pdf)


# ----------------------------------------------------------------------------
# G-002  Code analysis and general notes
# ----------------------------------------------------------------------------
OK = ("OK", {"weight": "bold"})
VAR = ("VARIANCE", {"weight": "bold", "color": ACCENT})
CONF = ("CONFIRM", {"weight": "bold", "color": BLUE})


def sheet_g002(pdf):
    f = facts()
    notes = tb_notes([
        ("Who stamps what", [
            "Whether an architect's seal is required for a two-family dwelling depends on state law and on "
            "what the city accepts. Expect at least:",
            "· Structural engineer (PE): all S sheets, retaining walls, steel beam and post, shoring.",
            "· Geotechnical engineer: soil report.",
            "· Surveyor: boundary, topography, stake-out.",
            "· Civil engineer: grading, driveway, drainage, utility connections.",
            "· Architect: recommended for the code package and the zoning hearing.",
            "· Licensed plumber, electrician and HVAC contractor under the trade permits.",
            "Confirm with Morgantown Code Enforcement before hiring.",
        ]),
        ("Words used in this set", [
            "EL 914.5: level in feet (NAVD88).",
            "R.O.W.: street right-of-way, city land.",
            "Unit A: lower flat. Unit B: upper flat.",
            "CL: common-load circuit on Unit A's panel.",
            "1-hour: fire-rated assembly, built exactly as its listing.",
            "Type X: fire-rated gypsum board.",
            "Prelim.: size assumed, engineer to design.",
        ]),
    ])
    fig, bg = new_sheet("G-002", index.TITLE["G-002"], "No scale", notes)
    gap = 0.3
    wl = 6.5
    wr = (RIGHT - LEFT) - wl - gap
    xl, xr = LEFT, LEFT + wl + gap
    ytop = TOP - 0.3
    fs, fn = 6.7, 6.9                     # tables, notes
    # ---- zoning ----
    fl = Flow(bg, xl, ytop, wl, fs=fn, name="G-002 left")
    fl.head("Zoning: R-2 Single and Two-Family Residential", rule=False,
            sub="Morgantown Planning and Zoning Code, Article 1337 (2019 edition as published by the city; check later amendments)")
    w = f["win"]
    zr = [
        ("Standard", "R-2 requires", "This design", "Result"),
        ("Use", "One- and two-family dwellings permitted", "Two-family dwelling: two stacked flats", OK),
        ("Lot area", "5,000 sf min.",
         f"About {f['lot']:,.0f} sf (tax-map dimensions) to {LOT_AREA_DEED:,.0f} sf (deed). Legal non-conforming lot, "
         "buildable under 1373.04.", ("EXISTING LOT", {"weight": "bold"})),
        ("Frontage", "40 ft min.", "50 ft", OK),
        ("Front setback", "10 ft min., 20 ft max.",
         f"{ftin(f['d_front'])}. Planning Division to confirm the front building line (1363.02(C)).", OK),
        ("Side setbacks", "5 ft min.", f"{ftin(f['d_side'])} east, {ftin(f['d_west'])} west", OK),
        ("Rear setback", "20 ft min., 1337.04(A)(4)", (f"{ftin(f['d_rear'])}, wall parallel to the rear line. See G-003.",
                                                      {"weight": "bold", "color": ACCENT}), VAR),
        ("Lot coverage", "50 % max.", f"{f['coverage']:.1f} %: {m.FOOTPRINT:,.0f} sf on {f['lot']:,.0f} sf", OK),
        ("Height", "35 ft max.",
         f"{f['h_mean']:.1f} ft: mean roof height EL {(f['eave'] + m.EL_RIDGE_HI) / 2:.1f} above average grade "
         f"EL {f['avg']:.1f}. Highest ridge {f['h_ridge']:.1f} ft.", OK),
        ("Storeys", "2.5 max.", "2 storeys over a basement garage (see the building code table)", OK),
        ("Parking", "1.5 spaces per unit = 3", f"{len(m.CARS)} in the open garage, each {ftin(m.CAR_W)} x {ftin(m.CAR_L)} design car", OK),
        ("Garage width", "65 % of the facade max.",
         f"{ftin(m.OPEN_W)} opening on a {ftin(m.FACADE_W)} facade = {m.GARAGE_PCT:.1f} %", OK),
        ("Front porch", "At least 50 % of the facade", f"{ftin(m.PORCH[2] - m.PORCH[0])} = {f['porch_pct']:.0f} % of the facade", OK),
        ("Porch in the front setback", "May project 50 % of the setback = 5 ft", f"{ftin(f['porch_out'])}", OK),
        ("Driveway", "22 ft max. at the right-of-way line", f"{ftin(m.APRON_W_ROW)}", OK),
        ("HVAC units", "2 ft min. from a side line; not in the front yard",
         f"West side yard, {ftin(f['hp_side'])} from the side line, {ftin(f['hp_behind'])} or more behind the front wall", OK),
        ("Eaves", "May project 3 ft into a setback; not within 3 ft of a lot line",
         f"Rear eave 12 in. ({ftin(f['d_rear'] - 1.0)} from the line), side rakes 8 in. "
         f"({ftin(f['d_side'] - 8 / 12)}). Front: {ftin(f['porch_out'])} roof over the porch, counted as the porch.", OK),
    ]
    y = wtable(bg, xl, fl.y, [1.02, 1.55, 3.13, 0.8], zr, fs=fs)
    # ---- general notes ----
    y -= 0.2
    gl = Flow(bg, xl, y, wl, fs=fn, name="G-002 general notes")
    gl.head("General notes for all trades", rule=True)
    gnotes = [
        "This set is a preliminary head start. Nobody builds from it. Build only from the permit drawings "
        "issued and sealed by the architect and engineers of record.",
        "Every structural size shown anywhere in the set (footings, walls, steel, trusses, shoring) is a "
        "preliminary assumption for the engineer to check and change.",
        f"Levels are NAVD88 feet from state LiDAR: garage slab EL {m.EL_GAR:.1f}, Unit A floor EL {m.EL_A:.1f}, "
        f"Unit B floor EL {m.EL_B:.1f}. The surveyor sets a site benchmark first; levels may shift with the survey.",
        "Plan dimensions run to finished wall faces inside and to the face of sheathing or concrete outside. "
        "Use the written dimensions, do not scale the drawings. If a dimension is missing, ask.",
        f"Lot lines are from tax-map dimensions, not a survey. Every outside wall face is held {m.MARGIN_IN:.0f} in. "
        "inside its setback line. The surveyor stakes lot lines and building corners before excavation.",
        "Nothing is built in the street right-of-way except the driveway apron, the buried drain outlet and "
        "the utility's own meter pits. No walls, steps or posts there.",
        f"Excavation is beside occupied houses: 441 and 442 Baird stand about {f['e441']['to_line']:.0f} ft outside "
        f"the side lot lines, about {f['cut_side']:.0f} ft from the garage walls. Shoring is designed by an engineer "
        "and no cut is left unsupported. Call 811 before digging.",
        "Fire-rated construction must stay whole: the 1-hour floor between the flats, the 1-hour stair walls, "
        "the 5/8 in. Type X garage ceiling and the 1-hour soffits near the lot lines. Any trade that cuts "
        "through one seals the hole with a listed fire-stop system.",
        "Owner's fixed requirements for every trade: all electric, no gas. No sump pump. No water pipe in the "
        "open garage. Two electric meters only. Everything separate per flat. Ducted central air, no "
        "mini-splits. No garage doors, door operators, cameras or heat cable.",
        "Before starting, each trade reads the sheets everyone gets (G-004) and the sheets of the trades it "
        f"touches. Shared points (plumbing stacks and chases, beam B1, duct soffits at {ftin(m.CLG_SOFFIT)}, panels "
        "and meters) are set once in the model and repeated on each trade's sheet.",
        "Finishes are rental grade and durable: LVP floors, fibreglass tub surrounds, laminate counters, "
        "vinyl windows, fibre-cement or vinyl siding, sealed broom-finished garage slab.",
        "If the site differs from the drawings, stop and tell the owner and the designer before covering the work.",
    ]
    half = 7
    cw = (wl - 0.25) / 2
    ys = gl.y
    ends = []
    for k, part in enumerate((gnotes[:half], gnotes[half:])):
        c = Flow(bg, xl + k * (cw + 0.25), ys, cw, fs=fn, name=f"G-002 notes {k}")
        for i, s in enumerate(part, 1 + k * half):
            c.p(s, lead=f"{i}.", indent=0.22, after=0.06)
        ends.append(c.end())
    # ---- building code ----
    fr = Flow(bg, xr, ytop, wr, fs=fn, name="G-002 right")
    fr.head("Building code: two-family dwelling under the IRC", rule=False,
            sub="West Virginia State Building Code: 2018 IRC, IPC and IMC · 2020 NEC · 2015 IECC, climate zone 5A")
    gmin = min(w.values(), key=lambda v: v[0])
    omin = min(w.values(), key=lambda v: v[1])
    small = min(("BEDROOM 1", "BEDROOM 2", "BEDROOM 3"), key=m.area)
    least = min(min(m.room_dims(k)) for k in ("BEDROOM 1", "BEDROOM 2", "BEDROOM 3"))
    nesc = sum(1 for t in m.WINDOWS if t[0] == "W1")
    flight_w = (m.SHAFT_U[1] - m.SHAFT_U[0] - 4 / 12) / 2
    br = [
        ("Item", "The code asks for", "This design"),
        ("Scope", "IRC: one- and two-family dwellings, 3 storeys or fewer above grade",
         "Two dwelling units, 2 storeys above grade over a basement garage"),
        ("Basement or storey",
         "A basement counts as a storey when the floor above it is more than 6 ft above average grade, or more "
         "than 12 ft above the ground at any point",
         f"Garage floor EL {m.EL_GAR:.1f}, average grade EL {f['avg']:.1f}: {f['below']:.0f} % of the garage level "
         f"is below grade. Unit A's floor is {f['a_above']:.1f} ft above average grade and {m.EL_A - m.EL_GAR:.0f} ft "
         "above the driveway. Basement, not a storey."),
        ("R302.3 between the flats", "1-hour separation between dwelling units",
         "1-hour floor/ceiling between Units A and B; 1-hour stair walls (2x4, 5/8 in. Type X each side)"),
        ("R302.6 garage", "5/8 in. Type X ceiling under habitable rooms",
         "5/8 in. Type X on the whole garage ceiling"),
        ("R302.1 walls near lot lines",
         "Walls under 5 ft from a lot line: 1-hour. Projections 2 to 5 ft from the line: 1-hour underside",
         f"Every wall is {ftin(f['d_side'])} or more from a lot line: no wall rating, windows not limited. Rear eave "
         "and side rakes come inside 5 ft: 1-hour underside."),
        ("R310 escape windows", "Every bedroom: 5.7 sf clear opening, sill 44 in. max.",
         f"{nesc} per flat, one in each bedroom: W1 casement, {m.WINDOW_TYPES['W1'].split(',')[0].replace(' vinyl casement', '')}, sill 30 in."),
        ("R311 stairs and exit", "Riser 7 3/4 in. max., tread 10 in. min., 36 in. wide, 6'-8\" headroom",
         f"Risers {frac_in(m.STAIR_LO['riser_in'])} in. (garage to A, {m.STAIR_LO['risers']}) and {frac_in(m.STAIR_UP['riser_in'])} in. "
         f"(A to B, {m.STAIR_UP['risers']}); {m.STAIR_LO['tread_in']} in. treads; flights {ftin(flight_w)} wide. "
         "Each flat's door opens to the enclosed stair and the street door."),
        ("R303 light and air", "Glass 8 % of the room's floor area, openable 4 %",
         f"Least room: {gmin[0]:.1f} % glass and {omin[1]:.1f} % openable, by nominal window size (A-601)"),
        ("R304 room sizes", "Habitable rooms 70 sf and 7 ft min.",
         f"Smallest bedroom {m.area(small):.0f} sf; least clear width {ftin(least)}"),
        ("R305 ceilings", "7'-0\" min. in habitable rooms",
         f"Unit A {ftin_dn(m.CLG_A)}, Unit B {ftin_dn(m.CLG_B)}, duct soffits {ftin_dn(m.CLG_SOFFIT)}; garage {ftin_dn(m.CLG_GAR)}"),
        ("R314, R315 alarms", "Smoke alarms in and outside bedrooms, CO alarm",
         "Hard-wired, interconnected; see E-105"),
        ("Energy, 2015 IECC", "Zone 5A insulation levels; blower-door test",
         "Walls R-20, attic R-49, floor over the garage R-30, slab R-10, stem walls R-15"),
        ("Design loads (prelim.)", "Set by the engineer",
         "Frost depth 36 in., snow 30 psf, wind 115 mph, seismic category B: all to be confirmed"),
    ]
    y = wtable(bg, xr, fr.y, [1.2, 1.95, wr - 3.15], br, fs=fs)
    # ---- to be confirmed ----
    y -= 0.2
    cf = Flow(bg, xr, y, wr, fs=fn, name="G-002 confirm")
    cf.head("Must be confirmed before design is final", color=BLUE)
    items = [
        ("Boundary and topographic survey.",
         f"Lot lines, corners and area ({f['lot']:,.0f} sf by tax-map dimensions, {LOT_AREA_DEED:,.0f} sf by deed, "
         "1,911 sf on county GIS), ground levels, and the neighbours' walls."),
        ("Soil report.", "Bearing capacity, pressure on the retaining walls, groundwater, rock, shoring."),
        ("Front building line.", "Written determination from the Planning Division under the developed-block "
                                 "rule, 1363.02(C), before the variance is filed."),
        ("Utility locations and depths.", "Sewer main in Baird St, water main and meter pits, power pole and "
                                          "service route. None is known yet."),
        ("Fall at the drain outlet.",
         f"The gravity outlet (invert EL {m.EL_DRAIN_OUT:.1f}) has only about 6 in. to spare above the street edge "
         f"(about EL {f['street_out']:.1f} by LiDAR). If the survey does not confirm it, the garage floor rises. "
         "A pump is not an option."),
        ("Code editions and local amendments.", "With Morgantown Code Enforcement, including any sprinkler "
                                                "amendment for two-family dwellings and the blower-door limit."),
        ("Basement ruling.", "That the zoning code counts the garage level as a basement, as the building code does."),
    ]
    for i, (a, b) in enumerate(items, 1):
        cf.p(a, lead=f"{i}.", indent=0.22, weight="bold", after=0.0)
        cf.p(b, indent=0.22, after=0.07)
    ends.append(cf.end())
    if min(ends) < MARGIN + 0.2:
        print(f"   !! G-002 text is {MARGIN + 0.2 - min(ends):.2f} in. too long")
    finish(fig, "G-002", pdf)


# ----------------------------------------------------------------------------
# G-003  Variance request
# ----------------------------------------------------------------------------
def variance_plan(fig, left, bottom, fpi=20):
    f = facts()
    view = (-36.0, -22.0, 88.0, 80.0)
    ax = plan_axes(fig, left, bottom, (view[0], view[2]), (view[1], view[3]), fpi)
    site_base(ax, view)
    poly(ax, m.APRON, fc="#e9edf1", ec=GREY, lw=0.4, z=4)
    poly(ax, m.OUT_U, fc=PAPER, ec="none", z=5)
    env = f["env"][20.0]
    poly(ax, list(env.exterior.coords), fc=TINT, ec=ACCENT, lw=0.7, z=6, alpha=0.8)
    setback_lines(ax)
    poly(ax, m.OUT_U, fc="none", ec=INK, lw=1.8, z=10)
    rot = m.REAR_ANGLE
    s = math.radians(rot)
    ux, uy = math.cos(s), math.sin(s)          # along the rear line, eastward
    px, py = -uy, ux                           # square to it, toward the rear

    def on_line(d, x):                         # point x along a line d ft inside the rear lot line
        return (x, rear_y(x) - d / _CR)
    # 10 ft line: the fallback
    a10, b10 = on_line(10.0, m.xw_o(36.0)), on_line(10.0, m.XE)
    line(ax, [a10, b10], color=BLUE, lw=0.6, ls=(0, (1.5, 2)), z=11)
    c = on_line(20.0, 27.5)
    txt(ax, c[0] + px * 1.3, c[1] + py * 1.3, "20 ft: REAR SETBACK IN THE CODE", size=5.0, color=ACCENT, rot=rot, z=12, weight="bold")
    c = on_line(10.0, 29.5)
    txt(ax, c[0] + px * 1.25, c[1] + py * 1.25, "10 ft line: the fallback", size=5.0, color=BLUE, rot=rot, z=12)
    c = on_line(15.0, 27.0)
    txt(ax, c[0] - px * 0.2, c[1] - py * 0.2, f"PROPOSED BUILDING · {m.FOOTPRINT:,.0f} SF", size=6.2, weight="bold", rot=rot, z=12)
    ec = env.centroid
    txt(ax, ec.x + 1.5, ec.y - 1.2, f"BUILDABLE BY RIGHT\n{env.area:,.0f} SF", size=5.6, color=ACCENT, weight="bold", z=12)
    # proposed setbacks
    dim(ax, (31.0, 0.0), (31.0, m.YF), 0, f"{ftin(m.YF)}", size=5.2, color=BLUE, ext=False, side=-1)
    dim(ax, (m.XE, 21.5), (50.0, 21.5), 0, f"{ftin(f['d_side'])}", size=5.2, color=BLUE, ext=False)
    yw = 31.0
    dim(ax, (west_x(yw), yw), (m.xw_o(yw), yw - (m.xw_o(yw) - west_x(yw)) * math.tan(WEST_LEAN)), 0, f"{ftin(f['d_west'])}",
        size=5.2, color=BLUE, ext=False)
    # rear neighbour: house to line, line to proposed wall, on one string square to the rear line
    (hx, hy), (lx, ly) = f["n386"]["pts"]
    wx, wy = lx - px * f["d_rear"], ly - py * f["d_rear"]
    dim(ax, (lx, ly), (hx, hy), 0, f"±{f['n386']['to_line']:.0f}'", size=5.6, color=BLUE, ext=False, side=-1)
    dim(ax, (wx, wy), (lx, ly), 0, "", size=5.2, color=BLUE, ext=False)
    leader(ax, ((wx + lx) / 2, (wy + ly) / 2), (-6.0, 53.5), f"{ftin(f['d_rear'])} requested\n(20 ft in the code)", size=5.2,
           color=BLUE, ha="right", weight="bold")
    txt(ax, hx + 12.5, hy - 5.4, f"±{f['n386']['to_bldg']:.0f} ft building to building", size=5.4, color=BLUE, z=12, box=True)
    # labels of the neighbours
    c = f["n386"]["bldg"].centroid
    txt(ax, c.x + 1, 73.0, "386 FOREST AVE\nrear neighbour, uphill\n(owned by the seller's affiliate)", size=5.4, color=INK, z=9)
    c = f["w442"]["bldg"].centroid
    txt(ax, c.x - 1.5, c.y + 2, "442 BAIRD ST\nthe applicant's\nown property", size=5.4, color=INK, z=9)
    txt(ax, c.x - 1.5, c.y - 6.5, f"house ±{f['w442']['to_line']:.0f} ft\nfrom the shared line\ncovers ±{round(f['w442']['cover'], -1):.0f} % of its lot",
        size=5.0, color=GREY, z=9)
    c = f["e441"]["bldg"].centroid
    txt(ax, c.x + 2, c.y + 3, "441 BAIRD ST", size=5.4, color=INK, z=9)
    txt(ax, c.x + 2, c.y - 2, f"house ±{f['e441']['to_line']:.0f} ft\nfrom the shared line", size=5.0, color=GREY, z=9)
    # heat pumps, fence, driveway
    t = -WEST_LEAN
    w_, d_ = m.HP_SIZE
    for (qx, qy) in m.HP:
        pp = [(-d_ / 2, -w_ / 2), (d_ / 2, -w_ / 2), (d_ / 2, w_ / 2), (-d_ / 2, w_ / 2)]
        poly(ax, [(qx + a * math.cos(t) - b * math.sin(t), qy + a * math.sin(t) + b * math.cos(t)) for a, b in pp],
             fc=PAPER, ec=BLUE, lw=0.6, z=9)
    leader(ax, (m.HP[0][0] - 0.2, m.HP[0][1] - 1.9), (-3.0, 9.0), "heat pumps", size=5.0, color=BLUE, ha="right")
    c = (36.0, rear_y(36.0))
    txt(ax, c[0] + px * 1.5, c[1] + py * 1.5, "6 ft privacy fence offered", size=5.0, color=INK, rot=rot, z=12)
    txt(ax, (m.OPEN[0] + m.OPEN[1]) / 2, 4.2, f"driveway {ftin(m.APRON_W_ROW)}\n{len(m.CARS)} cars park inside", size=5.0, color=INK, z=12)
    dim(ax, LOT_SE, LOT_SW, 3.4, "50'-0\" LOT FRONT", size=5.4, color=ACCENT)
    dim(ax, LOT_NE, LOT_SE, 2.6, "34'-0\"", size=5.4, color=ACCENT)
    dim(ax, LOT_SW, LOT_NW, 2.6, "48'-0\"", size=5.4, color=ACCENT, side=-1)
    txt(ax, 58.0, -14.0, "B A I R D   S T R E E T", size=7.0, weight="bold", color=GREY)
    txt(ax, 58.0, -17.0, "one lane, ±14 ft of pavement", size=5.2, color=GREY)
    north_arrow(ax, 80.0, 71.0, 4.0, 7)
    scale_bar(ax, -32.0, -18.5, 30, 10, 0.9, size=5.2)
    return ax


def existing_inset(fig, left, bottom, fpi=30):
    f = facts()
    ax = plan_axes(fig, left, bottom, (-5.0, 55.0), (-6.5, 51.5), fpi)
    poly(ax, LOT, fc="none", ec=ACCENT, lw=1.1, z=7, ls=(0, (9, 2.5, 1.5, 2.5)))
    poly(ax, list(f["env"][20.0].exterior.coords), fc=TINT, ec="none", z=2, alpha=0.8)
    setback_lines(ax, lw=0.4)
    poly(ax, list(EXISTING.exterior.coords), fc="none", ec=INK, lw=0.9, z=5, hatch="////")
    a, b = nearest_points(EXISTING, L_REAR)
    dim(ax, a.coords[0], b.coords[0], 0, f"±{f['ex_rear']:.0f}'", size=5.4, color=BLUE, ext=False, side=-1)
    a, b = nearest_points(EXISTING, L_FRONT)
    dim(ax, b.coords[0], a.coords[0], 0, f"±{f['ex_front']:.0f}'", size=5.4, color=BLUE, ext=False, side=-1)
    c = EXISTING.centroid
    txt(ax, c.x, c.y, "1929 HOUSE", size=5.2, weight="bold", box=True, z=9)
    txt(ax, 25.0, -3.6, "BAIRD ST", size=5.0, color=GREY)
    return ax


def variance_section(fig, left, bottom, xs=30.0, fpi=20):
    """Massing section through the lot and the rear neighbour's yard at plan station X = xs, looking west."""
    f = facts()
    Y0, Y1, Z0, Z1 = -18.0, 67.0, 907.0, 956.0
    ax = plan_axes(fig, left, bottom, (Y0, Y1), (Z0, Z1), fpi)
    ys = np.arange(Y0, Y1 + 0.25, 0.5)
    g = np.array([elev(xs, y) for y in ys])
    ax.fill_between(ys, Z0, g, color="#efe9e1", zorder=1, lw=0)
    yf, yr, ygi, ygo = m.YF, m.yr_o(xs), m.Y_GR_I, m.Y_GR_O
    und_a = m.EL_A - m.TRUSS_A - 0.0625
    T = f["eave"]
    grey = "#b9bec4"
    rect(ax, yf, m.EL_GAR - 0.5, yr, m.EL_PLATE, fc=PAPER, ec="none", z=2)                 # the building, cut
    rect(ax, yf, m.EL_GAR - 0.5, ygi, m.EL_GAR, fc=grey, ec=INK, lw=0.4, z=4)              # garage slab
    rect(ax, ygi, m.EL_FTG_TOP, ygo, und_a, fc=grey, ec=INK, lw=0.4, z=4)                  # rear retaining wall
    poly(ax, [(ygo, m.EL_GAR - 0.5), (yr, m.EL_GAR - 0.5), (yr, m.EL_A - 5 / 12), (ygo, m.EL_A - 5 / 12)], fc="#efe9e1", ec="none", z=3)
    rect(ax, ygo, m.EL_A - 5 / 12, yr, m.EL_A, fc=grey, ec=INK, lw=0.4, z=4)               # Unit A slab on grade
    rect(ax, yr - 8 / 12, m.EL_A - 3.6, yr, m.EL_A + 0.67, fc=grey, ec=INK, lw=0.4, z=4)   # rear stem wall (prelim.)
    rect(ax, yf - 4.0, und_a, ygo, m.EL_A, fc="#e6e8eb", ec=INK, lw=0.4, z=4)              # Unit A floor trusses + porch
    rect(ax, yf - 4.0, m.EL_B - m.TRUSS_B - 0.0625, yr, m.EL_B, fc="#e6e8eb", ec=INK, lw=0.4, z=4)
    rect(ax, yf, m.EL_A, yf + m.EXT, m.EL_PLATE, fc=INK, ec=INK, lw=0.3, z=5)
    rect(ax, yr - m.EXT, m.EL_A + 0.67, yr, m.EL_PLATE, fc=INK, ec=INK, lw=0.3, z=5)
    rect(ax, yf, m.EL_B1_TOP - m.B1_DEPTH, yf + 0.9, m.EL_B1_TOP, fc=BLUE, ec=BLUE, lw=0.3, z=6)   # beam B1
    ey = yr + 1.0 / _CR
    roof = [(yf - 4.0, T - 4.0 * m.ROOF_PITCH), (m.ridge_y(xs), m.ridge_el(xs)), (ey, T - m.ROOF_PITCH),
            (ey, T - m.ROOF_PITCH - 0.6), (yr, m.EL_PLATE), (yf, m.EL_PLATE), (yf - 4.0, T - 4.0 * m.ROOF_PITCH - 0.6)]
    poly(ax, roof, fc="#f2f3f5", ec=INK, lw=0.8, z=5)
    line(ax, list(zip(ys, g)), color=EARTH, lw=0.9, ls=(0, (4, 2)), z=7)                   # existing ground
    # lot lines and the code line
    yl = rear_y(xs)
    for y_, lab in ((0.0, "FRONT LOT LINE"), (yl, "REAR LOT LINE")):
        line(ax, [(y_, Z0 + 1.0), (y_, Z1 - 3.2)], color=ACCENT, lw=1.0, ls=(0, (9, 2.5, 1.5, 2.5)), z=8)
        txt(ax, y_, Z1 - 2.2, lab, size=5.0, color=ACCENT, weight="bold")
    y20 = yl - 20.0 / _CR
    line(ax, [(y20, m.EL_A), (y20, Z1 - 6.6)], color=ACCENT, lw=0.5, ls=(0, (4, 3)), z=8)
    txt(ax, y20, Z1 - 5.7, "20 ft code line", size=4.8, color=ACCENT)
    # neighbour's wall
    hit = LineString([(xs, yl + 1), (xs, 140)]).intersection(f["n386"]["bldg"])
    ywall = hit.bounds[1]
    gw = elev(xs, ywall - 0.5)
    line(ax, [(ywall, gw), (ywall, gw + 17.0)], color=GREY, lw=1.0, ls=(0, (5, 2)), z=8)
    txt(ax, ywall - 0.8, gw + 19.6, "386 FOREST AVE\nhouse wall\n(height not measured)", size=4.8, color=GREY, ha="center")
    # levels
    for el, lab in ((m.EL_GAR, "OPEN GARAGE"), (m.EL_A, "UNIT A"), (m.EL_B, "UNIT B")):
        txt(ax, yf + 1.4, el + 1.5, f"{lab}  EL {el:.1f}", size=5.0, ha="left", z=9, weight="bold")
    txt(ax, yf - 13.0, m.street_el(xs) if hasattr(m, "street_el") else street_el(xs) - 2.6, "BAIRD ST", size=5.0, color=GREY)
    txt(ax, m.ridge_y(xs), m.ridge_el(xs) + 1.5, f"ridge EL {m.ridge_el(xs):.1f}", size=5.0, z=9)
    # heights seen from the neighbour's side
    ge = elev(xs, yl)
    dim(ax, (yl + 4.0, ge), (yl + 4.0, f["eave_edge"]), 0, f"{f['eave_edge'] - ge:.0f}' at the line", size=5.0, color=BLUE,
        ext=False, side=-1)
    line(ax, [(ey, f["eave_edge"]), (ywall, f["eave_edge"])], color=BLUE, lw=0.3, ls=(0, (2, 2)), z=8)
    dim(ax, (ywall - 2.2, gw), (ywall - 2.2, f["eave_edge"]), 0, f"{f['eave_edge'] - gw:.0f}' at the house", size=5.0,
        color=BLUE, ext=False, side=1)
    # noon sun, midwinter and equinox (estimate)
    for decl, lab, col in ((-23.44, "noon sun, 21 Dec", "#b07a00"), (0.0, "noon, 21 Mar / 21 Sep", "#b07a00")):
        alt, tips = noon_shadow(decl)
        tip = min((t_ for t_ in tips if t_[6] == "eave"), key=lambda t_: abs(t_[1] - xs))
        zt = elev(tip[1], tip[2])
        up = (tip[4] - 9.0, tip[5] + 9.0 * (tip[5] - zt) / max(tip[2] - tip[4], 0.1))
        line(ax, [(tip[2], zt), (tip[4], tip[5])], color=col, lw=0.6, ls=(0, (6, 2)), z=9)
        ax.plot([tip[2]], [zt], marker="v", ms=3.2, color=col, zorder=10)
        txt(ax, tip[2] + 0.5, zt - 1.6, lab, size=4.8, color=col, ha="center", z=10)
    txt(ax, Y0 + 0.5, g[0] - 3.4, "existing ground (LiDAR), dashed", size=4.8, color=EARTH, ha="left")
    return ax


def sheet_g003(pdf):
    f = facts()
    e20, e10, e5 = (f["env"][d].area for d in (20.0, 10.0, 5.0))
    a_dec, s_dec = shadow_reach(-23.44)
    a_eq, s_eq = shadow_reach(0.0)
    n386, w442, e441 = f["n386"], f["w442"], f["e441"]
    notes = tb_notes([
        ("Process", [
            "· The applicant need not own the lot yet: the owner can authorise the application in writing "
            "(1381.02(A)). The purchase can then be made contingent on approval.",
            "· If denied, the same request cannot be filed again for one year (1381.03(J)). Prepare it once, properly.",
            "· An approval lapses if it is not used within 12 months (1381.05).",
            "· The west neighbour, 442 Baird, is the applicant's own property. A no-objection letter from the "
            "rear owner (the seller's affiliate) should be part of the sale.",
            "· Before filing, get the Planning Division's written front building line determination. The "
            "developed-block rule (1363.02(C)) may set it closer than 10 ft. The building would then slide "
            "forward, away from the rear line. It would not grow: lot coverage caps it.",
            "· Do not demolish the old house before the Board decides.",
        ]),
        ("Basis of this sheet", [
            "Lot from tax map 09-0029. Neighbours' buildings and lot lines from county GIS, good to about "
            "3 to 5 ft. Ground from state LiDAR. Distances marked ± are from those sources; the survey will "
            "replace them. Section numbers are from the city's 2019 code edition.",
        ]),
    ])
    fig, bg = new_sheet("G-003", index.TITLE["G-003"], "1\" = 20'-0\"", notes)
    # ---- left: drawings ----
    xl = LEFT - 0.02
    bg.text(xl, TOP - 0.28, "THE LOT, THE SETBACKS AND THE NEIGHBOURS", fontsize=8.6, fontweight="bold", va="center")
    bg.text(xl, TOP - 0.46, "1\" = 20'-0\" · red tint = all that the R-2 setbacks leave to build on · heavy outline = "
            "proposed building · grey = neighbours' buildings (county GIS)", fontsize=5.4, color=GREY, va="center")
    variance_plan(fig, xl, TOP - 0.6 - 5.1)
    ysec = TOP - 0.6 - 5.1 - 0.32
    bg.text(xl, ysec, f"SECTION THROUGH THE LOT AND THE REAR YARD", fontsize=8.0, fontweight="bold", va="center")
    bg.text(xl, ysec - 0.17, "1\" = 20'-0\" · cut 30 ft east of the west front corner, looking west · sun lines are an estimate",
            fontsize=5.4, color=GREY, va="center")
    variance_section(fig, xl, ysec - 0.3 - 2.45)
    xi = xl + 4.25 + 0.2
    bg.text(xi, ysec, "TODAY: THE 1929 HOUSE", fontsize=8.0, fontweight="bold", va="center")
    bg.text(xi, ysec - 0.17, "1\" = 30'-0\" · same setback lines", fontsize=5.4, color=GREY, va="center")
    existing_inset(fig, xi - 0.05, ysec - 0.3 - 1.95)
    cap = Flow(bg, xi, ysec - 0.3 - 1.95 - 0.06, 1.95, fs=5.6, name="G-003 inset caption")
    cap.p(f"About {f['ex_rear']:.0f} ft from the rear line where 20 is required and {f['ex_front']:.0f} ft from the "
          "front line where 10 is required. It already breaks both rules.")
    # legend under the section
    ly = MARGIN + 0.42
    lx = xl + 0.05
    for i, (kind, lab) in enumerate((("lot", "Lot line (tax map)"), ("sb", "R-2 minimum setback lines"),
                                     ("tint", "Buildable by right"), ("out", "Proposed building"))):
        x = lx + i * 1.62 + (0.1 if i > 1 else 0)
        if kind == "lot":
            bg.plot([x, x + 0.42], [ly, ly], color=ACCENT, lw=1.3, ls=(0, (9, 2.5, 1.5, 2.5)))
        elif kind == "sb":
            bg.plot([x, x + 0.42], [ly, ly], color=ACCENT, lw=0.6, ls=(0, (4, 3)))
        elif kind == "tint":
            bg.add_patch(Rectangle((x, ly - 0.06), 0.42, 0.12, fc=TINT, ec=ACCENT, lw=0.6))
        else:
            bg.add_patch(Rectangle((x, ly - 0.06), 0.42, 0.12, fc=PAPER, ec=INK, lw=1.6))
        bg.text(x + 0.5, ly, lab, fontsize=5.6, va="center")
    # ---- right: the case ----
    gap = 0.26
    x1 = xl + 6.2 + 0.32
    cw = (RIGHT - x1 - gap) / 2
    x2 = x1 + cw + gap
    ytop = TOP - 0.2
    fs = 6.2
    # the request
    rq = Flow(bg, x1 + 0.1, ytop - 0.1, cw - 0.2, fs=6.6, name="G-003 request")
    rq.head("The request", color=ACCENT, rule=False)
    rq.p("Relief from Section 1337.04(A)(4), minimum rear setback in the R-2 district: from 20 ft to 5 ft, "
         "for a new two-family dwelling at 387 Baird Street.", weight="bold", after=0.05)
    rq.p("Nothing else is requested. Use, front and side setbacks, lot coverage, height, parking, garage width, "
         "porch and driveway all meet the code as drawn (table on G-002).", after=0.0)
    yb = rq.end() - 0.1
    bg.add_patch(Rectangle((x1, yb), cw, ytop - yb, fill=False, ec=ACCENT, lw=1.2))
    a = Flow(bg, x1, yb - 0.2, cw, fs=fs, name="G-003 column A")
    a.head("What each rear setback leaves", sub="Area inside the setback lines, per floor", rule=False)
    side20 = math.sqrt(e20)
    y = wtable(bg, x1, a.y, [0.78, 0.6, cw - 1.38], [
        ("Rear setback", "Area", "What can be built"),
        ("20 ft (the code)", f"{e20:,.0f} sf", f"A building about {side20:.0f} x {side20:.0f} ft. No two-family dwelling fits."),
        ("10 ft", f"{e10:,.0f} sf", "The fallback: two 2-bedroom flats."),
        (("5 ft (requested)", {"weight": "bold"}), (f"{e5:,.0f} sf", {"weight": "bold"}),
         f"This design: {m.FOOTPRINT:,.0f} sf footprint, walls {m.MARGIN_IN:.0f} in. inside the lines. Two 3-bedroom flats."),
    ], fs=5.9)
    a.y = y - 0.2
    a.head("Findings the Board must make", sub="West Virginia Code 8A-7-11. Attorney to confirm the wording.")
    a.p("No harm to public health, safety or welfare, or to the rights of adjacent owners.", lead="1.", indent=0.16, weight="bold", after=0.02)
    a.p(f"The full 5 ft side yards are kept. Five feet is also the distance at which the building code stops asking "
        f"for fire-rated walls. The rear neighbour's house is about {n386['to_line']:.0f} ft beyond the line, so the two "
        f"buildings stand about {n386['to_bldg']:.0f} ft apart. Their yard is uphill: the ground at their house is about "
        f"{f['g_house'] - m.EL_A:.0f} ft above the first flat's floor, so from there the new building stands about "
        f"{f['eave_edge'] - f['g_house']:.0f} ft to the eave. Gutters and drains carry roof and hillside water to the "
        f"street, not to a neighbour. All {len(m.CARS)} required parking spaces are on the lot.", indent=0.16)
    a.p("Special conditions of the property, not created by the applicant.", lead="2.", indent=0.16, weight="bold", after=0.02)
    a.p(f"The lot is about {round(f['lot'], -1):,.0f} sf where the district minimum is 5,000. It is only 34 ft deep on the "
        f"east side, against {m.SB_FRONT + m.SB_REAR_CODE:.0f} ft of combined front and rear setbacks. The rear line runs "
        "diagonally. The lot was platted long before the zoning code.", indent=0.16)
    a.p("Unnecessary hardship; reasonable use of the land.", lead="3.", indent=0.16, weight="bold", after=0.02)
    a.p(f"The code setbacks leave {e20:,.0f} sf, a building about {side20:.0f} x {side20:.0f} ft. The district permits a "
        "two-family dwelling here, but none can be built on what the setbacks leave.", indent=0.16)
    a.p("The spirit of the ordinance is kept.", lead="4.", indent=0.16, weight="bold", after=0.02)
    a.p(f"The use is permitted. Coverage is {f['coverage']:.0f} % (50 allowed), height {f['h_mean']:.0f} ft (35 allowed), "
        f"parking is met. The request follows the pattern of the block: every neighbouring building sits within "
        f"about 1 ft of a lot line, and 442 Baird covers about {round(w442['cover'], -1):.0f} % of its lot.", indent=0.16)
    ya = a.end()
    b = Flow(bg, x2, ytop, cw, fs=fs, name="G-003 column B")
    b.head("Likely questions")
    qa = [
        ("Why not keep the old house?",
         f"It breaks the same rules: about {f['ex_rear']:.0f} ft from the rear line and {f['ex_front']:.0f} ft from the "
         "front line. The county values the building at \\$12,600."),
        ("Is this the minimum that works?",
         f"At 10 ft the building is {e10:,.0f} sf per floor. That is the fallback: two-bedroom flats. Three bedrooms "
         "per flat need the 5 ft line."),
        ("Parking and traffic?",
         f"Two households. {len(m.CARS)} spaces inside the building, the number the code requires, so no car is added "
         f"to the one-lane street. The driveway is {ftin(m.APRON_W_ROW)} at the right-of-way line, the code limit."),
        ("Excavation near the rear yard?",
         f"The part of the building nearest the rear line is a slab on grade and is not dug out. The garage cut "
         f"stays {f['cut_rear_e']:.0f} ft from the rear line at the east corner and {f['cut_rear_w']:.0f} ft at the west, "
         "held by shoring designed by an engineer."),
        ("Shade?",
         f"Estimate from the ground model: at noon in midwinter the shadow reaches about {s_dec:.0f} ft past the "
         f"line, about the foot of the neighbour's wall. At the equinox about {s_eq:.0f} ft, and less all summer, "
         "so for most of the year it stays in the first 10 ft of their yard."),
        ("Privacy?",
         "A 6 ft privacy fence on the rear line is offered. The neighbour's yard is higher than the first "
         f"flat's floor. Each flat has {sum(1 for t in m.WINDOWS if t[1] == 'N')} windows in the rear wall."),
        ("Noise?",
         "The two heat pumps stand in the west side yard, facing the applicant's own house at 442 Baird."),
        ("A rooming house?",
         "No. Two dwelling units, one lease each."),
    ]
    for q, ans in qa:
        b.p(q, weight="bold", after=0.02)
        b.p(ans, after=0.1)
    yb2 = b.end()
    if min(ya, yb2) < MARGIN + 0.2:
        print(f"   !! G-003 text is {MARGIN + 0.2 - min(ya, yb2):.2f} in. too long")
    finish(fig, "G-003", pdf)


# ----------------------------------------------------------------------------
# G-004  Trade packages
# ----------------------------------------------------------------------------
def scopes():
    f = facts()
    return {
        "Surveyor": "Boundary and topographic survey. Stakes the lot lines, building corners and floor levels. "
                    "Confirms the fall at the drain outlet.",
        "Demolition": "Removes the 1929 house and its foundation after the utilities are disconnected. Not before "
                      "the variance is granted.",
        "Excavation and shoring": f"Engineered shoring; cuts the hill for the garage down to footing level "
                                  f"(top of footing EL {m.EL_FTG_TOP:.1f}); rear swale; backfill.",
        "Concrete: footings and retaining walls": "Footings, the three 12 in. garage retaining walls and the return "
                                                  "pier, the 8 in. lobby and utility walls, stem walls for the rear slab.",
        "Waterproofing and foundation drains": "Membrane and drainage board on the three buried walls; French drain "
                                               "to the gravity outlet at the street edge; cleanout risers. No sump pump.",
        "Concrete flatwork: slabs, apron, walks": "Garage slab sloped to the trench drain, Unit A slab on grade over "
                                                  "insulation, driveway apron, entry landing.",
        "Structural steel": f"Beam B1 over the {ftin(m.OPEN_W)} garage opening, its steel post, bearing plates and anchors.",
        "Framing and trusses": f"{m.TRUSS_A * 12:.0f} in. and {m.TRUSS_B * 12:.0f} in. floor trusses, 2x6 outside walls, "
                               "partitions, roof trusses, sheathing, the two cantilevered porches.",
        "Roofing and gutters": "Asphalt shingles, underlayment, flashing, gutters and downspouts.",
        "Windows and exterior doors": f"Vinyl windows ({len(m.WINDOWS)} per flat, {sum(1 for t in m.WINDOWS if t[0] == 'W1')} "
                                      "of them escape windows), porch doors, street door.",
        "Siding and exterior trim": "Fibre-cement or vinyl siding, trim, and the 1-hour soffits near the lot lines.",
        "Plumbing": "Drain under the garage slab, three stacks, water lines kept inside the heated building, "
                    "two 80 gal electric water heaters, fixtures, cleanouts.",
        "Heating and cooling": f"One ducted heat pump and air handler per flat, ducts in the {ftin(m.CLG_SOFFIT)} soffits, "
                               "bath fans, range hood and dryer vents.",
        "Electrical": f"Two-meter service, {m.PANEL_A_AMPS} A and {m.PANEL_B_AMPS} A panels, wiring, automatic garage and "
                      "stair lights, smoke and CO alarms.",
        "Insulation and air sealing": "Walls R-20, attic R-49, floor over the garage R-30, slab R-10, stem walls R-15; "
                                      "air sealing for the blower-door test.",
        "Drywall and fire-rated assemblies": "5/8 in. Type X garage ceiling, 1-hour floor between the flats, 1-hour "
                                             "stair walls and chases, all other gypsum board.",
        "Cabinets and countertops": "Kitchen cabinets and island, laminate counters, bath vanities, in both flats.",
        "Interior doors, trim and closets": f"{len(m.DOORS) - 2} interior doors per flat, casing and base, closet "
                                            "shelves and rods.",
        "Flooring, tile and paint": "LVP floors, bath floors, paint.",
        "Stairs and railings": f"Common stair ({m.STAIR_LO['risers']} risers garage to Unit A, {m.STAIR_UP['risers']} "
                               "A to B), handrails, porch guards.",
        "Site utilities: water, sewer, power": f"Two 1 in. water services buried {m.WATER_DEPTH * 12:.0f} in. deep, sewer "
                                               "lateral and two-way cleanout, electric service to the meters.",
        "Paving, site walls, fence, landscape": "Wing walls beside the driveway, trash bay, 6 ft rear fence, final "
                                                "grading and seeding.",
        "Zoning and permit reviewers": "Not a builder: the sheets for the Planning Division, the Board of Zoning "
                                       "Appeals and Code Enforcement.",
    }


ORDER = [
    ("Survey and soil report", "Boundary and topographic survey; geotechnical borings."),
    ("Variance", "Front building line determination, then the Board of Zoning Appeals (G-003)."),
    ("Design by licensed professionals", "Architect and engineers take over this set and seal their own."),
    ("Permits", "Building, demolition, right-of-way and trade permits; utility applications."),
    ("Demolition", "Only after the variance is granted and the utilities are disconnected."),
    ("Shoring and excavation", "Protect the neighbours' houses first."),
    ("Footings and retaining walls", ""),
    ("Waterproofing and drains", "Inspect and photograph before anything is covered."),
    ("Backfill", "Only when the engineer says the walls can take it."),
    ("Slabs", "Under-slab plumbing and conduit first."),
    ("Steel", "Beam B1 and its post."),
    ("Framing", "Unit A floor, walls, Unit B floor, walls."),
    ("Roof", "Trusses, sheathing, shingles: dry in."),
    ("Windows", "And exterior doors."),
    ("Rough-ins", "Plumbing, heating and cooling, electrical; fire-stopping; inspections."),
    ("Insulation", "And air sealing."),
    ("Drywall", "Fire-rated assemblies inspected before finishing."),
    ("Finishes", "Cabinets, doors and trim, flooring, paint, fixtures."),
    ("Site work", "Utilities connected, apron, walls, fence, final grading."),
]


def sheet_g004(pdf):
    sc = scopes()
    missing = [t for t, _ in index.PACKAGES if t not in sc]
    if missing:
        raise SystemExit(f"G-004: no scope statement for {missing}")
    notes = tb_notes([
        ("How to use this sheet", [
            "Hand each company the sheets on its row plus the eight sheets everyone gets. The row is that "
            "company's own work; the shared sheets show what it has to fit around.",
            "A sheet can be in more than one package. Where two trades meet (a pipe through a rated floor, "
            "a duct in a soffit), both get the sheet.",
            "A scope line says what the company builds. It is not a contract scope: the contract and the "
            "sealed permit drawings govern.",
        ]),
        ("Pricing from this set", [
            "Use it for budget prices and for questions only. Sizes marked preliminary will change when the "
            "engineers design them.",
        ]),
    ])
    fig, bg = new_sheet("G-004", index.TITLE["G-004"], "No scale", notes)
    ytop = TOP - 0.3
    wo = 3.05                                  # order-of-work column
    gap = 0.3
    wt = (RIGHT - LEFT) - wo - gap
    xt, xo = LEFT, LEFT + wt + gap
    fl = Flow(bg, xt, ytop, wt, fs=7.0, name="G-004 head")
    fl.head("Trade packages: who gets which sheets", rule=False,
            sub=f"{len(index.PACKAGES)} packages. Every package also gets the {len(index.EVERYONE)} sheets in the blue box.")
    # everyone strip
    ev = [f"{n}  {index.TITLE[n]}" for n in index.EVERYONE]
    h = 0.66
    bg.add_patch(Rectangle((xt, fl.y - h), wt, h, fc="#eef3f9", ec=BLUE, lw=0.9))
    bg.text(xt + 0.1, fl.y - h / 2, "EVERYONE\nGETS", fontsize=7.0, fontweight="bold", color=BLUE, va="center", linespacing=1.3)
    ncol = 4
    cw = (wt - 1.0) / ncol
    for i, s in enumerate(ev):
        cx = xt + 0.95 + (i % ncol) * cw
        cy = fl.y - 0.21 - (i // ncol) * 0.24
        n, t = s.split("  ", 1)
        bg.text(cx, cy, n, fontsize=6.6, fontweight="bold", va="center")
        bg.text(cx + 0.46, cy, t, fontsize=6.6, va="center")
        if cx + 0.46 + tw(t, 6.6) > xt + wt - 0.05 or (i % ncol < ncol - 1 and 0.46 + tw(t, 6.6) > cw - 0.05):
            print(f"   !! G-004 everyone strip: '{t}' does not fit its cell")
    y = fl.y - h - 0.14
    rows = [("No.", "Trade package", "What that company builds", "Its own sheets")]
    for i, (trade, sheets) in enumerate(index.PACKAGES, 1):
        bad = [s for s in sheets if s not in index.TITLE]
        if bad:
            raise SystemExit(f"G-004: unknown sheets {bad}")
        rows.append((f"{i}", (trade, {"weight": "bold"}), sc[trade], "  ".join(sheets)))
    wn, wtr, wsh = 0.36, 2.05, 2.05
    yb = wtable(bg, xt, y, [wn, wtr, wt - wn - wtr - wsh, wsh], rows, fs=6.6, vpad=0.052)
    if yb < MARGIN + 0.2:
        print(f"   !! G-004 table is {MARGIN + 0.2 - yb:.2f} in. too tall")
    o = Flow(bg, xo, ytop, wo, fs=7.0, name="G-004 order")
    o.head("Suggested order of work", sub="A sequence to plan by, not a schedule. The contractor sets the schedule.")
    o.gap(0.05)
    for i, (step, note) in enumerate(ORDER, 1):
        y0 = o.y
        o.p(step, indent=0.34, weight="bold", after=0.0, fs=7.0)
        if note:
            o.p(note, indent=0.34, after=0.0, fs=6.3)
        o.y = min(o.y, y0 - 0.27) - 0.12
        bg.add_patch(plt.Circle((xo + 0.12, y0 - 0.085), 0.12, fill=False, ec=INK, lw=0.6))
        bg.text(xo + 0.12, y0 - 0.088, f"{i}", fontsize=6.6, fontweight="bold", ha="center", va="center")
    o.end()
    finish(fig, "G-004", pdf)


SHEETS = [("G-001", sheet_g001), ("G-002", sheet_g002), ("G-003", sheet_g003), ("G-004", sheet_g004)]
