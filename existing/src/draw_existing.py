"""Before / after sheets for the scan clean-up of 390 Forest Ave and 441 Baird St."""
import json
import math
import os
import sys
import warnings

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402
from shapely.geometry import Polygon  # noqa: E402

import sheetx as sx  # noqa: E402
from sheetx import FIX, OPEN, HERE, W, H, TB, MG, sheet, tag, tag_bg, picture, head, draw_floor, north, save  # noqa: E402
from common import INK, GREY, LIGHT, BLUE, PAPER, ftin, line, poly, txt, table, plt  # noqa: E402
from xform import IN, FT, load_reg, plan_to_scan  # noqa: E402

D = os.path.join(HERE, "data")
P390 = json.load(open(os.path.join(D, "390_polycam_plan.json")))
P441 = json.load(open(os.path.join(D, "441_polycam_plan.json")))
FX = json.load(open(os.path.join(D, "390_fixed.json")))
REG = load_reg()
FPI = 16 / 3.0
DY2 = 782.45     # Polycam page offset between its 'Floor 2' and Floor 4 (their wall lines then coincide)
LEVEL = {2: "Polycam 'Floor 2' (not a level)", 3: "Lower flat", 4: "Middle flat", 5: "Upper flat", 6: "Attic (part of the upper flat)"}
Z = {3: -7.08, 4: -4.23, 5: -1.56, 6: 1.35, "top": 4.08}

# ---- Polycam name -> (name used here, assumed?) ----
N390 = {
    3: {"Laundry 1 (1)": ("Laundry", False), "Laundry 1 (2)": ("Laundry closet", False), "Bedroom 4": ("Bedroom 1", False),
        "Other 4": ("Bedroom 2", True), "Hallway 3": ("Hall", False), "Kitchen 2": ("Kitchen", False), "Living Room 2": ("Living room", False),
        "Bathroom 2": ("Bath", False), "Closet 2": ("Closet", False), "Closet 3": ("Closet", False), "Other 10": ("Closet", True),
        "Other 12": ("Closet", True), "Other 13": ("Chase", True)},
    4: {"Other 2 (1)": ("Living room / kitchen", False), "Other 2 (2)": ("Bath", False), "Bedroom 3": ("Bedroom 1", False),
        "Bedroom 5": ("Bedroom 2", False), "Other 6": ("Hall", False), "Closet 1": ("Closet", False), "Other 7": ("Stair hall", False),
        "Other 8": ("Stair", False), "Other 11": ("Closet", True)},
    5: {"Living Room 1": ("Living room", False), "Kitchen 1": ("Kitchen", False), "Bathroom 1": ("Bath", False), "Laundry 2": ("Laundry", False),
        "Hallway 1": ("Hall, stair to attic", False), "Hallway 4": ("Closet", True), "Other 3": ("Room A (bedroom)", True),
        "Other 5": ("Room B (bedroom)", True), "Other 9": ("Stair landing", False), "Other 14": ("Chase", True), "Other 15": ("Chase", True)},
    6: {"Bedroom 1": ("Attic bedroom 1", False), "Bedroom 2": ("Attic bedroom 2", False), "Hallway 2": ("Stair hall", False)},
    2: {"Other 1": ("Not a room: outline of the house", False)},
}
N441 = {
    1: {"Basement": ("Basement (half the footprint)", False)},
    2: {"Bedroom 2": ("Bedroom 1", False), "Bedroom 4": ("Bedroom 2", False), "Living Room 2": ("Living room", False), "Kitchen 2": ("Kitchen", False),
        "Bathroom 2": ("Bath", False), "Laundry 1": ("Laundry", False), "Closet 3": ("Closet", False), "Closet 4": ("Closet", False),
        "Other 2": ("Storage", True), "Other 3": ("Hall", False), "Other 5": ("Closet", True), "Other 6": ("Entry", True), "Other 8": ("Closet", True)},
    3: {"Bedroom 1": ("Bedroom 1", False), "Bedroom 3": ("Bedroom 2", False), "Living Room 1": ("Living room", False), "Kitchen 1": ("Kitchen", False),
        "Bathroom 1": ("Bath", False), "Closet 1": ("Closet", False), "Closet 2": ("Closet", False), "Closet 5": ("Closet", False),
        "Laundry 2": ("Laundry", False), "Other 4": ("Hall", False), "Other 7": ("Closet", True)},
}


def R(a, p):
    return (p[0] * math.cos(a) - p[1] * math.sin(a), p[0] * math.sin(a) + p[1] * math.cos(a))


_T390 = {}
TWIST = {}


def _square(fl):
    """Scan-based position of a level, then turned by exactly the angle that makes its own walls square."""
    th5 = math.radians(FX["th5_deg"]); org = np.array(FX["origin_scan_m"])
    Ts = plan_to_scan(REG[fl])
    S = lambda p: (np.array(R(-th5, Ts(p))) - org) / FT          # noqa: E731
    pts = np.array([S(q) for w in P390[str(fl)]["walls"] for q in w["pts"]])
    c = pts.mean(0)
    sx_ = sy_ = 0.0
    for w in P390[str(fl)]["walls"]:
        q = [S(p) for p in w["pts"]]
        for u, v in zip(q, q[1:]):
            L = math.dist(u, v)
            if L > 1.5:
                t = 4 * math.atan2(v[1] - u[1], v[0] - u[0])
                sx_ += L * math.cos(t); sy_ += L * math.sin(t)
    phi = math.atan2(sy_, sx_) / 4                               # walls sit phi off square, in (-45, 45] degrees
    TWIST[fl] = -math.degrees(phi)
    return S, c, -phi


def T390(fl):
    """Plan inches -> building frame feet (all floors stacked), as fixed."""
    if fl in _T390:
        return _T390[fl]
    S, c, a = _square(fl)
    f0 = lambda p: np.array(R(a, S(p) - c)) + c                  # noqa: E731
    sh = np.zeros(2)
    if fl == 3:
        B = np.array([f0(q) for w in P390["3"]["walls"] for q in w["pts"]])
        T5 = T390(5)
        B5 = np.array([T5(q) for w in P390["5"]["walls"] for q in w["pts"]])
        sh = (B5.min(0) + B5.max(0)) / 2 - (B.min(0) + B.max(0)) / 2
    f = lambda p: tuple((f0(p) + sh).tolist())                   # noqa: E731
    _T390[fl] = f
    return f


def Traw390(fl):
    """Plan inches -> feet in the 3D scan's own frame turned to the page (no fixes): shows the twist."""
    th5 = math.radians(FX["th5_deg"]); org = np.array(FX["origin_scan_m"])
    Ts = plan_to_scan(REG[fl])
    return lambda p: tuple(((np.array(R(-th5, Ts(p))) - org) / FT).tolist())


def Tsimple(F, origin=None):
    xs = [q[0] for w in F["walls"] for q in w["pts"]]; ys = [q[1] for w in F["walls"] for q in w["pts"]]
    ox, oy = origin if origin else (min(xs), min(ys))
    return lambda p: ((p[0] - ox) / 12, (p[1] - oy) / 12)


def _inch(ft_):
    return ftin(round(ft_ * 12) / 12)


def heights390(fl):
    out = {}
    for r in FX["floors"][str(fl)]["rooms"]:
        if r.get("ceil_ft") and r.get("cells", 0) >= 12:
            t = _inch(r["ceil_ft"])
            if r.get("second_ft") and r.get("share_second", 0) >= 0.2:
                t += f", part {_inch(r['second_ft'])}"
            out[r["name"]] = t
        elif r.get("ceil_max_ft"):
            out[r["name"]] = f"{_inch(r['ceil_min_ft'])} to {_inch(r['ceil_max_ft'])}"
    return out


def height_range(fl):
    v = [r["ceil_ft"] for r in FX["floors"][str(fl)]["rooms"] if r.get("ceil_ft") and r.get("cells", 0) >= 40]
    if not v:
        r = FX["floors"][str(fl)]["rooms"]
        return f"{_inch(min(q['ceil_min_ft'] for q in r))} to {_inch(max(q['ceil_max_ft'] for q in r))}"
    return f"{_inch(min(v))} to {_inch(max(v))}, by room"


def f5_text(fl):
    big = [r for r in FX["floors"][str(fl)]["rooms"] if r.get("ceil_ft") and r.get("cells", 0) >= 40]
    big.sort(key=lambda r: r["ceil_ft"])
    parts = ", ".join(f"{N390[fl].get(r['name'], (r['name'],))[0]} {_inch(r['ceil_ft'])}" for r in big)
    sp = max((r.get("spread_in") or 0) for r in big) if big else 0
    return (f"Ceiling heights re-measured in the 3D scan on a 10 in. grid. Inside any one room the height holds within about {max(2, round(sp))} in. "
            f"The rooms themselves differ: {parts}.")


def centre(F, name, off=34.0):
    r = [r for r in F["rooms"] if r["name"] == name][0]
    p = Polygon(r["pts"]).buffer(0)
    c = p.centroid if p.contains(p.centroid) else p.representative_point()
    return (c.x, c.y + off)


def px(house, p):
    """Plan inches -> pixel on Polycam's own page image (100 px per metre)."""
    hpx = 4455 if house == "390" else 2498
    return (2.54 * (p[0] + 65.3), hpx - 2.54 * (p[1] + 60))


CROPS = {"390": {5: (480, 130, 1560, 1130), 3: (800, 1750, 2120, 3080), 4: (2330, 1230, 3520, 2200), 6: (2330, 130, 3420, 1080), 2: (2330, 3200, 3520, 4200)},
         "441": {3: (90, 150, 1100, 1190), 1: (90, 1310, 1100, 1900), 2: (1230, 1310, 2240, 2360)}}


def before_panel(fig, bg, house, fl, box, tags):
    l, b, w, h = box
    axp = picture(fig, os.path.join(D, "before", f"{house}_f{fl}.png"), l, b, w, h)
    cb = CROPS[house][fl]
    for (t, p, col) in tags:
        qx, qy = px(house, p)
        axp.add_patch(plt.Circle((qx - cb[0], qy - cb[1]), 26, fc=col, ec="white", lw=0.8, zorder=30))
        axp.text(qx - cb[0], qy - cb[1], t, fontsize=5.4, color="white", ha="center", va="center", fontweight="bold", zorder=31)
    return axp


def fix_list(bg, x, y, items, width=6.2, fs=6.2):
    """items: (tag, colour, text). Returns the y reached."""
    import textwrap
    for t, col, s in items:
        tag_bg(bg, x + 0.13, y - 0.02, t, col)
        lines = textwrap.wrap(s, int(width * 15.5))
        for i, ln in enumerate(lines):
            bg.text(x + 0.36, y - i * 0.135, ln, fontsize=fs, va="center", color=INK)
        y -= 0.135 * len(lines) + 0.11
    return y


def floor_sheet(pdf, number, house, title, plan, fl, T, names, heights, fixes, opens, view, notes, sub, north_vec=None, extra=None, fpi=FPI, flags=True):
    """One level: Polycam's export on the left, the corrected plan on the right, tagged."""
    F = plan[str(fl)]
    fig, bg = sheet(number, title, "390 Forest Ave" if house == "390" else "441 Baird St", sub, notes)
    left_w = 4.9
    head(bg, 0.6, 10.2, "Before: what the scan export shows", "Polycam floor plan as exported, unchanged")
    head(bg, 0.6 + left_w + 0.35, 10.2, "After: with the fixes", "Same geometry, squared, stacked, renamed, re-measured · feet and inches", color=FIX)
    tags_b = [(t, p, FIX) for (t, p, _s) in fixes if p] + [(t, p, OPEN) for (t, p, _s) in opens if p]
    before_panel(fig, bg, house, fl, (0.55, 4.25, left_w, 5.55), tags_b)
    (vx, vy) = view
    fpi = max(fpi, (vx[1] - vx[0]) / 7.3, (vy[1] - vy[0]) / 5.5)
    wplan = (vx[1] - vx[0]) / fpi
    hplan = (vy[1] - vy[0]) / fpi
    ax = sx.axes(fig, 0.6 + left_w + 0.35 + max(0, (7.35 - wplan) / 2), 4.25 + max(0, (5.55 - hplan) / 2), vx, vy, fpi)
    G, st = sx.regularize(F, T)
    draw_floor(ax, G, sx.IDENT, names=names, heights=heights)
    for run in (sx.uncaptured_exterior(G, sx.IDENT) if flags else []):
        ax.plot([p[0] for p in run], [p[1] for p in run], color=OPEN, lw=1.6, ls=(0, (3, 2)), zorder=9)
    fixes = list(fixes) + [("F12", None, f"Walls straightened: {st['n_square'] // 2} wall runs set exactly square and lined up on {st['lines']} common lines, corners closed. "
                            f"No wall moved more than {max(st['max_move_in'], 0.5):.1f} in." + (f" Walls were up to {st['max_skew']:.1f} degrees out of square in the scan." if st['max_skew'] > 0.3 else ""))]
    big_diag = [d_ for d_ in st["diag"] if d_[2] >= 1.0] if flags else []
    if big_diag:
        opens = list(opens) + [("U10", None, f"{len(big_diag) // 2 or 1} short angled wall piece(s), {ftin(min(d_[2] for d_ in big_diag))} to {ftin(max(d_[2] for d_ in big_diag))} long, are kept as scanned. "
                                "Some are real (a bay, a cut corner); some may be the scan rounding a corner. Circled in amber.")]
        seen = []
        for d_ in big_diag:
            if all(math.dist(d_[:2], q) > 0.5 for q in seen):
                seen.append(d_[:2])
                ax.add_patch(plt.Circle(d_[:2], max(0.9, d_[2] * 0.6), fc="none", ec=OPEN, lw=0.9, ls=(0, (2, 1.5)), zorder=15))
    for (t, p, _s) in fixes:
        if p:
            q = T(p); tag(ax, q[0], q[1], t, FIX)
    for (t, p, _s) in opens:
        if p:
            q = T(p); tag(ax, q[0], q[1], t, OPEN)
    if north_vec is not None:
        north(ax, vx[1] - 2.2, vy[1] - 2.4, north_vec, 1.3)
    sx.scale_bar(ax, vx[0] + 0.8, vy[0] + 0.9, 12, 4)
    if extra:
        extra(ax, bg, fig)
    bg.plot([0.55, W - MG - TB - 0.2], [4.05, 4.05], color=LIGHT, lw=0.6)
    y = fix_list(bg, 0.6, 3.82, [(t, FIX, s) for (t, _p, s) in fixes], width=6.0)
    fix_list(bg, 7.0, 3.82, [(t, OPEN, s) for (t, _p, s) in opens], width=5.6)
    save(fig, number, pdf)


# =============================================================================== 390 Forest Ave
def sheet_390_stack(pdf):
    notes = [
        ("What was wrong", [
            "The export numbers the levels Floor 1 to 6.",
            "Floor 1 is a stray object and Floor 2 is a",
            "copy of the outside walls: not levels.",
            "The lowest flat is drawn turned 45 degrees.",
            "In the 3D scan itself that flat is twisted",
            "11 degrees against the floors above: the",
            "phone lost its bearings between levels.",
            "The floors sit apart on the page with no",
            "common origin, so walls cannot be stacked.",
        ]),
        ("What I did", [
            "F1 Named the four real levels: lower flat,",
            "   middle flat, upper flat, attic.",
            "F2 Turned the lowest flat square.",
            "F3 Took out the 11 degree twist and seated",
            "   that flat on the common footprint by",
            "   matching its outline (30'-8\" x 26'-10\"",
            "   against 31'-8\" x 27'-6\" above).",
            "F4 Put every level on one origin and",
            "   measured the level heights in the scan.",
            "F10 North from the scan's GPS / compass.",
        ]),
        ("Still open", [
            "U1 Nothing below the lower flat was",
            "   scanned. Basement or crawl space: unknown.",
            "U3 The lower flat is placed by outline",
            "   only: good to about 12 in. sideways.",
        ]),
    ]
    fig, bg = sheet("EX-101", "390 Forest: levels lined up and stacked", "390 Forest Ave", "Rear building · county parcel 31-13-0029-0083", notes)
    head(bg, 0.6, 10.2, "Before 1: the export page", "Six 'floors' scattered on the page; the lowest flat at 45 degrees")
    axp = picture(fig, os.path.join(D, "before", "390_page.png"), 0.55, 5.7, 3.5, 4.2)
    k = 1500 / 4455
    for (t, (qx, qy)) in (("F1", (330, 4150)), ("F2", (1150, 2000))):
        axp.add_patch(plt.Circle((qx * k, qy * k), 48, fc=FIX, ec="white", lw=0.8, zorder=30))
        axp.text(qx * k, qy * k, t, fontsize=5.6, color="white", ha="center", va="center", fontweight="bold", zorder=31)
    head(bg, 4.5, 10.2, "Before 2: the 3D scan, seen from above", "Outlines of the four scanned levels exactly as the scan holds them")
    cols = {3: "#b3261e", 4: "#1f5fa8", 5: "#2e7d32", 6: "#8e24aa"}
    ax = sx.axes(fig, 4.4, 5.75, (-6, 40), (-8, 36), 11.0)
    for fl in (3, 4, 5, 6):
        Tr = Traw390(fl)
        for w in P390[str(fl)]["walls"]:
            q = [Tr(p) for p in w["pts"]]
            ax.plot([a[0] for a in q], [a[1] for a in q], color=cols[fl], lw=0.5)
    tag(ax, 3.5, 30.5, "F3", FIX)
    ax.text(17, -6.4, "red = lower flat: twisted 11 degrees against the others", fontsize=6.0, color=cols[3], ha="center")
    head(bg, 8.9, 10.2, "After: stacked on one origin", "Same four levels after the fixes · origin at the south-west outside corner", color=FIX)
    ax2 = sx.axes(fig, 8.85, 5.75, (-6, 40), (-8, 36), 11.0)
    for fl in (3, 4, 5, 6):
        Tf = T390(fl)
        for w in P390[str(fl)]["walls"]:
            q = [Tf(p) for p in w["pts"]]
            ax2.plot([a[0] for a in q], [a[1] for a in q], color=cols[fl], lw=0.5)
    north(ax2, 36.5, 32.0, FX["north_in_building_frame"], 2.4)
    tag(ax2, 30.5, 32.0, "F10", FIX); tag(ax2, -2.5, -2.5, "F4", FIX)
    ax2.plot([0], [0], marker="+", ms=9, color=INK)
    ax2.text(17, -6.4, "walls of all four levels now fall on the same lines", fontsize=6.0, color=INK, ha="center")
    for i, fl in enumerate((3, 4, 5, 6)):
        bg.plot([4.6 + i * 2.0, 4.9 + i * 2.0], [5.5, 5.5], color=cols[fl], lw=2)
        bg.text(4.97 + i * 2.0, 5.5, LEVEL[fl].split(" (")[0], fontsize=6.2, va="center")
    # level diagram
    head(bg, 0.6, 5.05, "After: level heights measured in the 3D scan", "Floor-to-floor and typical ceiling heights · the export's own heights ran from 6'-8\" to 21 ft")
    axs = fig.add_axes([0.75 / W, 0.6 / H, 6.4 / W, 3.95 / H]); axs.set_xlim(0, 64); axs.set_ylim(-11, 39); axs.axis("off")
    base = Z[3]
    lv = [(3, "LOWER FLAT", "ceilings " + height_range(3)), (4, "MIDDLE FLAT", "ceilings " + height_range(4)), (5, "UPPER FLAT", "ceilings " + height_range(5)), (6, "ATTIC", "ceilings " + height_range(6))]
    tops = [Z[4], Z[5], Z[6], Z["top"]]
    for (fl, nm, ch), ztop in zip(lv, tops):
        y0 = (Z[fl] - base) / FT; y1 = (ztop - base) / FT
        axs.add_patch(plt.Rectangle((14, y0), 30, y1 - y0, fc="#f3f4f6", ec=INK, lw=0.8))
        axs.text(29, (y0 + y1) / 2 + 0.6, nm, fontsize=7, fontweight="bold", ha="center", va="center")
        axs.text(29, (y0 + y1) / 2 - 1.1, ch, fontsize=6, ha="center", va="center", color=FIX)
        axs.plot([44, 47], [y0, y0], color=INK, lw=0.5); axs.text(47.6, y0, f"floor +{ftin(y0)}" if y0 else "floor 0'-0\" (lower flat)", fontsize=5.8, va="center")
        axs.annotate("", xy=(11.5, y1), xytext=(11.5, y0), arrowprops=dict(arrowstyle="<->", lw=0.5, color=INK))
        axs.text(10.6, (y0 + y1) / 2, ftin(y1 - y0), fontsize=6, ha="right", va="center")
    axs.add_patch(plt.Rectangle((14, -9.5), 30, 9.5, fc="#fdf3e3", ec=OPEN, lw=0.8, ls="--"))
    axs.text(29, -4.3, "BELOW THE LOWER FLAT", fontsize=7, fontweight="bold", ha="center", va="center", color=OPEN)
    axs.text(29, -6.2, "not scanned: basement, cellar or crawl space unknown", fontsize=6, ha="center", va="center", color=OPEN)
    axs.text(3.0, 13, "floor\nto\nfloor", fontsize=5.6, ha="center", va="center", color=GREY)
    tag(axs, 46.5, -4.3, "U1", OPEN, r=1.3); tag(axs, 8.0, 34.0, "F4", FIX, r=1.3)
    # footprint table
    rows = [["Level", "Outline in the scan (ft)", "Turned by", "Result"]]
    for fl in (6, 5, 4, 3):
        Tf = T390(fl); B = np.array([Tf(q) for w in P390[str(fl)]["walls"] for q in w["pts"]])
        rows.append([LEVEL[fl].split(" (")[0], f"{ftin(np.ptp(B[:, 0]))} x {ftin(np.ptp(B[:, 1]))}", f"{TWIST[fl]:+.1f} deg", "seated by outline" if fl == 3 else "as scanned"])
    rows.append(["'Floor 2'", "copy of the middle flat's outside walls", "-", "dropped (F13)"])
    head(bg, 7.6, 5.05, "After: footprint check", "Each level's outline once squared: they agree within about 12 in. except where there is a bay or stair")
    table(bg, 7.6, 4.55, [1.3, 1.9, 0.9, 1.5], rows, fs=6.2, rh=0.22)
    bg.text(7.6, 2.95, "The middle flat reads 3'-6\" longer because its stair and bay window project past the main wall line.\nThe attic is narrower because its walls are the knee walls under the roof.", fontsize=6.0, va="top", color=INK, linespacing=1.3)
    save(fig, "EX-101", pdf)


def ex390(pdf):
    nv = FX["north_in_building_frame"]
    gen = lambda fl, extra: [("Level", [f"{LEVEL[fl]}. Scan floor level", f"{ftin((Z[fl] - Z[3]) / FT)} above the lower flat's floor."] + extra)]  # noqa: E731
    how = ("How to read the 'after' plan", ["Dark = walls as scanned (drawn 4 in. thick,", "the real thickness is not known).", "Blue = windows. Grey = furniture and",
                                             "fixtures the scan recognised.", "Red text = ceiling height from the 3D scan.", "Amber name with ? = my guess at the use.",
                                             "Amber dashes = outside wall the scan missed.", "Room size = clear width x depth through", "the middle of the room."])
    F3 = P390["3"]
    floor_sheet(pdf, "EX-102", "390", "390 Forest: lower flat, before and after", P390, 3, T390(3), N390[3], heights390(3), [
        ("F2", centre(F3, "Living Room 2"), "Plan was exported turned 45 degrees. Turned square to the page like the other levels."),
        ("F3", centre(F3, "Kitchen 2"), "This level is twisted 11 degrees in the 3D scan. Twist removed; outline seated on the footprint of the floors above."),
        ("F5", centre(F3, "Bedroom 4"), f5_text(3)),
        ("F7", centre(F3, "Other 4"), "'Other 4' renamed Bedroom 2, because you count this flat as a two-bedroom. 'Other 10/12/13' renamed closet / chase (my guess)."),
        ("F8", None, "All sizes converted from decimal inches to feet and inches, with each room's clear size and area."),
    ], [
        ("U2", (centre(F3, "Other 4")[0] - 70, centre(F3, "Other 4")[1] - 40), "Bedroom 2's window scans at 28 x 33 in. Too small to be an escape window unless it is larger than it reads. Sill heights could not be read from the scan."),
        ("U5", (centre(F3, "Other 4")[0] + 45, centre(F3, "Other 4")[1] + 62), "Bedroom 2 has a 5'-10\" opening to the hall and no door in the scan. Confirm whether a door exists."),
        ("U6", centre(F3, "Laundry 1 (1)"), "No stair shows on this level. How this flat is entered, and whether the laundry door is an outside door, is not known."),
        ("U4", None, "Drain stacks, joist direction and bearing walls cannot be seen in a scan."),
    ], ((-3, 36), (-3, 30)), gen(3, ["One bedroom per the scan, two per the owner.", "Polycam area: 762 sf outside, 689 sf inside."]) + [how], "Rear building · lower flat", nv)

    F4 = P390["4"]

    bath4 = Polygon([r for r in F4["rooms"] if r["name"] == "Other 2 (2)"][0]["pts"]).buffer(0)
    cand = [Polygon(o["pts"]).buffer(0) for o in F4["furniture"] if len(o["pts"]) >= 4]
    cand = [g for g in cand if g.area > 150 and bath4.contains(g.centroid)]
    wc4 = (cand[0].centroid.x, cand[0].centroid.y) if cand else centre(F4, "Other 2 (2)", 0)

    def extra4(ax, bg, fig):
        q = T390(4)(wc4)
        ax.add_patch(plt.matplotlib.patches.Ellipse(q, 2.4, 2.4, fc="none", ec=FIX, lw=1.0, ls=(0, (2, 1.5)), zorder=14))
    floor_sheet(pdf, "EX-103", "390", "390 Forest: middle flat, before and after", P390, 4, T390(4), N390[4], heights390(4), [
        ("F4", None, "Placed on the common origin: this level sits directly over the lower flat and under the upper flat (see EX-101)."),
        ("F5", centre(F4, "Bedroom 5"), f5_text(4) + " Bedroom 2 and the living room each show a second, different height over part of the room: a dropped section or a step."),
        ("F7", centre(F4, "Other 2 (1)"), "'Other 2 (1)' renamed Living room / kitchen, 'Other 2 (2)' Bath, 'Other 6' Hall, 'Other 7/8' Stair hall and Stair."),
        ("F9", (wc4[0] + 30, wc4[1] + 8), "The export shows a tub and a sink in this bath but no toilet, only an unnamed object in the corner. The 3D scan shows something standing there too: circled as the likely toilet. Confirm."),
        ("F8", None, "Sizes in feet and inches; clear size and area per room."),
    ], [
        ("U6", centre(F4, "Other 7"), "The stair and its hall are only partly scanned. Stair width, rise and where it leads are not known."),
        ("U9", (centre(F4, "Other 2 (1)")[0] + 60, centre(F4, "Other 2 (1)")[1] - 95), "Amber dashes: the outside wall at the south-east corner and bay was not captured. Shape assumed from the room outline."),
        ("U2", centre(F4, "Bedroom 3"), "Bedroom window sills and whether they open could not be read. Check each bedroom for an escape window."),
        ("U4", None, "Drain stacks, joist direction and bearing walls cannot be seen in a scan."),
    ], ((-3, 39), (-3, 31)), gen(4, ["Two bedrooms, one bath.", "Polycam area: 887 sf outside, 818 sf inside."]) + [how], "Rear building · middle flat", nv, extra=extra4)

    F5 = P390["5"]
    floor_sheet(pdf, "EX-104", "390", "390 Forest: upper flat, before and after", P390, 5, T390(5), N390[5], heights390(5), [
        ("F4", None, "This level is the reference: every other level is positioned against its outline (31'-8\" x 27'-6\")."),
        ("F5", centre(F5, "Kitchen 1"), f5_text(5) + " The export listed 9'-8\" to 21'-7\" because it read up the open stair."),
        ("F7", centre(F5, "Other 3"), "'Other 3' and 'Other 5' have a door and a window each and no furniture in the scan: named Room A and Room B, likely bedrooms. Tell me which is in use."),
        ("F7b", centre(F5, "Hallway 1"), "'Hallway 1' holds the stair up to the attic; 'Other 9' is its landing. Renamed."),
        ("F8", None, "Sizes in feet and inches; clear size and area per room."),
    ], [
        ("U5", centre(F5, "Hallway 4"), "'Hallway 4' is a strip 2'-4\" wide between the living room and Room A. A closet, or an old stair? Unknown."),
        ("U2", centre(F5, "Other 5"), "Window sills and operation not readable. Room B's window scans at 27 x 65 in."),
        ("U6", centre(F5, "Other 9"), "How this flat is entered from outside is not in the scan."),
        ("U11", centre(F5, "Living Room 1"), "The living room, Room A and the small spaces have too few 3D scan points for a reliable ceiling height."),
        ("U4", None, "Drain stacks, joist direction and bearing walls cannot be seen in a scan."),
    ], ((-3, 36), (-3, 30)), gen(5, ["Main floor of the upper flat.", "Polycam area: 862 sf outside, 785 sf inside."]) + [how], "Rear building · upper flat", nv)

    F6 = P390["6"]

    def extra6(ax, bg, fig):
        T = T390(6); Ts = plan_to_scan(REG[6]); th5 = math.radians(FX["th5_deg"]); org = np.array(FX["origin_scan_m"])
        pts = np.array([R(-th5, Ts(q)) for w in P390["6"]["walls"] for q in w["pts"]]); c = pts.mean(0); a = math.radians(FX["twist_deg"]["6"])
        xs, ys, hs = [], [], []
        for r in FX["floors"]["6"]["rooms"]:
            for (cx, cy, hgt) in r.get("cells", []):
                q = np.array(R(-th5, (cx, cy))) - c; q = np.array(R(a, q)) + c - org
                xs.append(q[0] / FT); ys.append(q[1] / FT); hs.append(hgt / FT)
        hs = np.array(hs)
        low = hs < 7.0
        ax.scatter(np.array(xs)[low], np.array(ys)[low], s=9, marker="s", color=OPEN, alpha=0.55, zorder=3, linewidths=0)
        ax.scatter(np.array(xs)[~low], np.array(ys)[~low], s=9, marker="s", color="#d7ecd9", alpha=0.6, zorder=1.5, linewidths=0)
        ax.text(16, 29.3, "green = ceiling 7 ft or higher · amber = lower than 7 ft (measured cell by cell in the 3D scan)", fontsize=5.6, ha="center", color=INK)
    floor_sheet(pdf, "EX-105", "390", "390 Forest: attic, before and after", P390, 6, T390(6), N390[6], heights390(6), [
        ("F6", centre(F6, "Bedroom 1"), "Headroom measured from the 3D scan on a 10 in. grid. The ceiling is 7 ft or higher over 99 to 100 % of both bedrooms: the scanned rooms stop at the knee walls, so the low roof space is outside them."),
        ("F5", centre(F6, "Bedroom 2"), "Ceiling 7'-11\" to 9'-4\". The export gave one figure, 7'-6\" to 8'-0\"."),
        ("F4", None, "Placed over the upper flat on the common origin: the attic stair hall sits over the stair in the hall below."),
        ("F7", centre(F6, "Hallway 2"), "'Hallway 2' renamed Stair hall. No bathroom on this level."),
        ("F8", None, "Sizes in feet and inches; clear size and area per room."),
    ], [
        ("U2", (centre(F6, "Bedroom 1")[0] - 75, centre(F6, "Bedroom 1")[1]), "Window sills and operation not readable. Each attic bedroom needs one window that opens for escape."),
        ("U7", None, "What is behind the knee walls (roof slope, storage, framing) is not in the scan."),
        ("U4", None, "Drain stacks, joist direction and bearing walls cannot be seen in a scan."),
    ], ((-3, 36), (-3, 30)), gen(6, ["Two bedrooms reached by the stair", "from the upper flat's hall."]) + [how], "Rear building · attic", nv, extra=extra6)

    F2 = P390["2"]
    T4 = T390(4)
    T2 = lambda p: T4((p[0], p[1] + DY2))                        # noqa: E731

    def extra2(ax, bg, fig):
        G4, _ = sx.regularize(P390["4"], T4)
        for w in G4["walls"]:
            q = w["pts"] + [w["pts"][0]]
            ax.plot([a_[0] for a_ in q], [a_[1] for a_ in q], color="#1f5fa8", lw=0.55, zorder=20)
        ax.text(38.6, -2.1, "blue outline = the middle flat's walls (EX-103) · dark = Polycam's 'Floor 2' walls, lying on the same lines", fontsize=5.6, color="#1f5fa8", ha="right")
    c2 = centre(F2, "Other 1", 0)
    floor_sheet(pdf, "EX-106", "390", "390 Forest: Polycam's 'Floor 2' is not a basement", P390, 2, T2, N390[2], {}, [
        ("F13", (c2[0] - 60, c2[1] + 60), "Identified. These six wall pieces are the middle flat's own outside walls drawn a second time: the west wall, south wall, east wall and the corner notch "
                                           "fall on the middle flat's lines within 1/8 in., and the angled piece runs parallel to the side of its bay window, about 1'-6\" inside it. Blue shows the middle flat laid over it."),
        ("F1", None, "Dropped as a level, with the stray 'Floor 1'. My last issue called this sheet Basement and drew a guessed outline in amber dashes: that was wrong and is removed."),
        ("F14", None, "Why Polycam made it: it has no rooms, doors or windows, and its listed height of 16'-6\" is the lower flat's floor to the middle flat's ceiling "
                      "(9'-4\" + 7'-3\"). It is the shell of two storeys saved as if it were one room. The slanted edge of its 777 sf area is only the app closing the shape."),
    ], [
        ("U1", (c2[0] + 60, c2[1] - 80), "Whether the house has a basement, cellar or crawl space is NOT known from these files. The 3D scan holds nothing below the lower flat's floor."),
        ("U12", None, "Outside the lower flat the scan caught ground 1 to 8 ft below that flat's floor, so there is room for a cellar or crawl space under it. "
                      "Tell me what is down there; it decides how new bathroom drains can run."),
    ], ((-3, 39), (-3, 31)), [("What this is", ["Not a floor of the house. It is a leftover", "from the scanning app: the outside walls", "of the lower two storeys, saved as an", "extra 'floor' with one 777 sf 'room'.",
                                               "Nothing on it is new information."]),
                              ("What is needed", ["If there is a basement or cellar: a scan", "or photos of it, showing the stairs, any", "outside door, posts and beams, where the", "drains leave, heaters and panels."]), how],
        "Rear building · Polycam 'Floor 2'", nv, extra=extra2, flags=False)


# =============================================================================== 441 Baird St
def ex441(pdf):
    how = ("How to read the 'after' plan", ["Dark = walls as scanned (drawn 4 in. thick).", "Blue = windows. Grey = furniture and fixtures.", "Amber name with ? = my guess at the use.",
                                             "Amber dashes = outside wall the scan missed.", "No 3D scan exists for this house, so", "nothing here is re-measured: heights are", "the export's own and are not checked."])
    o3 = (7.68, 486.78); o2 = (453.32, 30.31); o1 = (7.68, 203.78 - (359.42 - 185.95))
    notes = [
        ("What was wrong", ["Both exports carry the address 390 Forest", "Ave. This is the front building; the county", "lists it as 441 Baird St.",
                            "Levels are numbered Floor 1 to 3 and sit", "apart on the page.", "No stairs were captured at all.",
                            "The basement outline covers half the", "footprint. Only 2 of 4 sinks were found."]),
        ("What I did", ["F1 Named the levels: basement, first-floor", "   flat, second-floor flat.", "F4 Stacked the two flats on one origin: their",
                        "   outlines are identical, 30'-11\" x 29'-11\".", "F7 Named the rooms. F8 Feet and inches.", "F11 Corrected the address label."]),
        ("Still open", ["U7 No 3D scan: heights and stacking are", "   not checked.", "U8 No stairs anywhere: how the upper flat", "   is reached is unknown.",
                        "U9 Basement: which half it is under is a", "   guess (drawn under the north half)."]),
    ]
    fig, bg = sheet("EX-201", "441 Baird: levels named and stacked", "441 Baird St", "Front building · county parcel 31-13-0029-0083", notes)
    head(bg, 0.6, 10.2, "Before: the export page", "Three 'floors' apart on the page, labelled 390 Forest Ave")
    picture(fig, os.path.join(D, "before", "441_page.png"), 0.55, 5.6, 4.3, 4.3)
    tag_bg(bg, 2.6, 9.72, "F11"); tag_bg(bg, 1.1, 8.6, "F1")
    head(bg, 5.3, 10.2, "After: the two flats and the basement on one origin", "Blue = first-floor flat · green = second-floor flat · amber dashed = basement outline", color=FIX)
    ax = sx.axes(fig, 5.6, 5.5, (-4, 36), (-4, 34), 8.6)
    for fl, org, col in ((2, o2, "#1f5fa8"), (3, o3, "#2e7d32")):
        Tf = Tsimple(P441[str(fl)], org)
        for w in P441[str(fl)]["walls"]:
            q = [Tf(p) for p in w["pts"]]; ax.plot([a[0] for a in q], [a[1] for a in q], color=col, lw=0.5)
    Tb = Tsimple(P441["1"], o1)
    for w in P441["1"]["walls"]:
        q = [Tb(p) for p in w["pts"]]; ax.plot([a[0] for a in q], [a[1] for a in q], color=OPEN, lw=0.6, ls=(0, (3, 2)))
    tag(ax, -2, -2, "F4", FIX); tag(ax, 15.5, 22, "U9", OPEN); tag(ax, 33.5, 15, "U8", OPEN)
    ax.plot([0], [0], marker="+", ms=9, color=INK)
    rows = [["Level", "Export name", "Outline", "Inside area", "Ceiling in the export"],
            ["Second-floor flat", "Floor 3", "30'-11\" x 29'-11\"", "797 sf", "7'-7\" to 8'-10\" (not checked)"],
            ["First-floor flat", "Floor 2", "30'-11\" x 29'-11\"", "767 sf", "4'-7\" to 9'-3\" (not reliable)"],
            ["Basement", "Floor 1", "30'-11\" x 15'-6\"", "449 sf", "7'-7\" (not checked)"]]
    head(bg, 0.6, 5.0, "Levels", "From the export table: 2,198 sf outside in total")
    table(bg, 0.6, 4.6, [1.6, 1.1, 1.7, 1.1, 2.6], rows, fs=6.2, rh=0.22)
    fix_list(bg, 0.6, 3.25, [("F1", FIX, "Levels renamed: Floor 1 = Basement, Floor 2 = First-floor flat, Floor 3 = Second-floor flat."),
                             ("F4", FIX, "The two flats have the same outline to the inch, so they are stacked corner on corner."),
                             ("F11", FIX, "Address corrected from '390 Forest Ave' to 441 Baird St (county record). Tell me if you use another address.")], width=5.6)
    fix_list(bg, 7.0, 3.25, [("U7", OPEN, "No 3D scan was exported for this house. Send one (the .laz file) and I can check heights and stacking as for 390."),
                             ("U8", OPEN, "No stair appears on any level. The second-floor flat must have one, inside or outside."),
                             ("U9", OPEN, "The basement outline is half the footprint. Which half, and whether the rest is crawl space, is unknown.")], width=5.4)
    save(fig, "EX-201", pdf)

    F2 = P441["2"]
    floor_sheet(pdf, "EX-202", "441", "441 Baird: first-floor flat, before and after", P441, 2, Tsimple(F2, o2), N441[2], {}, [
        ("F4", None, "Placed on the common origin, directly under the second-floor flat."),
        ("F7", centre(F2, "Bedroom 2"), "Bedrooms renumbered 1 and 2 for this flat. 'Other 3' renamed Hall; 'Other 2/5/6/8' named by my guess (amber)."),
        ("F8", None, "Sizes in feet and inches; clear size and area per room."),
    ], [
        ("U5", centre(F2, "Other 6"), "A 2 ft gap in the north wall between the bedrooms, labelled 'Other 6'. An entry, or a missed wall? Unknown."),
        ("U8", centre(F2, "Other 3"), "No stair to the flat above or to the basement is shown."),
        ("U9", (centre(F2, "Laundry 1")[0] + 70, centre(F2, "Laundry 1")[1]), "The east wall steps in and out by the laundry and closet. It may be real (a porch or bump-out) or a scan error."),
        ("U7", None, "Ceiling heights in the export run from 4'-7\" to 9'-3\" on this level: not usable. No 3D scan to check them."),
    ], ((-3, 35), (-3, 33)), [("Level", ["First-floor flat: 2 bedrooms, living room,", "kitchen, bath, laundry.", "Polycam area: 849 sf outside, 767 sf inside."]), how], "Front building · first-floor flat")

    F3 = P441["3"]
    floor_sheet(pdf, "EX-203", "441", "441 Baird: second-floor flat, before and after", P441, 3, Tsimple(F3, o3), N441[3], {}, [
        ("F4", None, "Placed on the common origin, directly over the first-floor flat."),
        ("F7", centre(F3, "Bedroom 3"), "Bedrooms renumbered 1 and 2 for this flat. 'Other 4' renamed Hall, 'Other 7' closet (my guess)."),
        ("F8", None, "Sizes in feet and inches; clear size and area per room."),
    ], [
        ("U8", centre(F3, "Other 4"), "No stair is shown. How this flat is reached is unknown: the door at the south wall may lead to an outside stair."),
        ("U2", centre(F3, "Bedroom 1"), "Window sills and operation not readable from a floor plan."),
        ("U7", None, "Ceiling heights (7'-7\" and 8'-10\") are the export's own and are not checked."),
    ], ((-3, 35), (-3, 33)), [("Level", ["Second-floor flat: 2 bedrooms, living room,", "kitchen, bath, laundry.", "Polycam area: 869 sf outside, 797 sf inside."]), how], "Front building · second-floor flat")

    def base_extra(ax, bg, fig):
        pass
    F1 = P441["1"]
    floor_sheet(pdf, "EX-204", "441", "441 Baird: basement, before and after", P441, 1, Tsimple(F1, o1), N441[1], {}, [
        ("F1", None, "'Floor 1' renamed Basement."),
        ("F8", None, "Sizes in feet and inches."),
    ], [
        ("U9", centre(F1, "Basement"), "Only 30'-11\" x 15'-6\" was scanned, half the footprint of the flats. Drawn under the north half as a guess."),
        ("U8", None, "No stair, no outside door and no windows are shown. Water heaters, panels and drains are not shown."),
        ("U7", None, "Ceiling height 7'-7\" is the export's own and is not checked."),
    ], ((-3, 35), (-3, 33)), [("Level", ["Basement, about 449 sf scanned.", "Needs a scan or tape measure of the rest."]), how], "Front building · basement")


# =============================================================================== fix log
def sheet_log(pdf):
    fig, bg = sheet("EX-001", "Scan fix log: both houses", "390 Forest + 441 Baird", "Two buildings on county parcel 31-13-0029-0083", [
        ("What this set is", ["The Polycam exports redrawn with every", "fix tagged, so you can see what the scan", "showed and what I changed.",
                              "Nothing new is designed here: no added", "bedroom or bath yet."]),
        ("Tags", ["F = a fix I made. Red.", "U = still open: I could not fix it from the", "    files; it needs a look on site or", "    another scan. Amber."]),
        ("Files used", ["390: floor plan export + 3D scan (.laz).", "441: floor plan export only.", "The .stl and second .laz are copies of the", "same 390 scan and were not needed."]),
        ("Sheets", ["EX-101 to 106  390 Forest Ave", "EX-201 to 204  441 Baird St"]),
    ])
    head(bg, 0.6, 10.2, "Fixes made", "What the scan showed, and what I did", color=FIX)
    rows = [["Tag", "House", "What the scan showed", "What I did", "Sheet"],
            ["F1", "both", "Levels numbered Floor 1 to 6 (390) and 1 to 3 (441); 390's Floor 1 is a stray object", "Named the real levels; dropped Floor 1 and Floor 2", "101, 201"],
            ["F2", "390", "Lowest flat drawn turned 45 degrees", "Turned square", "101, 102"],
            ["F3", "390", "3D scan has the lowest flat twisted 11 degrees against the floors above", "Twist removed; seated on the common footprint by outline", "101, 102"],
            ["F4", "both", "Levels sit apart on the page, no common origin", "Stacked on one origin; 390 level heights measured in the scan", "101, 201"],
            ["F5", "390", "Ceiling heights from 6'-8\" to 21'-7\"", "Re-measured per room on a 10 in. grid: each room steady within about 2 in.", "102 to 105"],
            ["F6", "390", "Attic drawn as flat rooms, no headroom information", "Headroom mapped: 7 ft or more over 99 % of both bedrooms", "105"],
            ["F7", "both", "Rooms without furniture labelled 'Other'", "Named by use; guesses marked with ?", "all"],
            ["F8", "both", "Sizes in decimal inches", "Feet and inches; clear size and area per room", "all"],
            ["F9", "390", "Middle flat bath: tub and sink, no toilet", "Unnamed object in the corner circled as the likely toilet", "103"],
            ["F10", "390", "North shown only as a small compass symbol on the export page", "North arrow added from the geo-referenced scan (phone compass, approximate)", "101"],
            ["F11", "441", "Address reads 390 Forest Ave", "Labelled 441 Baird St (county record)", "201"],
            ["F12", "both", "Walls up to 3 degrees out of square (390 lower flat); small jogs and open corners", "Walls set exactly square, lined up on common lines, corners closed", "all"],
            ["F13", "390", "'Floor 2': six wall pieces and one 777 sf 'room', which I first read as a basement", "Shown to be the middle flat's outside walls drawn twice; not a basement", "106"],
            ["F14", "390", "'Floor 2' listed 16'-6\" high", "Explained: lower flat floor to middle flat ceiling, two storeys saved as one room", "106"]]
    y = table(bg, 0.6, 9.8, [0.45, 0.55, 5.0, 4.9, 1.0], rows, fs=6.1, rh=0.235)
    head(bg, 0.6, y - 0.45, "Still open: could not be fixed from the files", "Each needs a look on site, a tape measure, or another scan", color=OPEN)
    rows2 = [["Tag", "House", "What is missing or doubtful", "What would settle it"],
             ["U1", "390", "Nothing below the lower flat was scanned: basement, cellar or crawl space unknown", "Tell me what is under the lower flat; scan or photos"],
             ["U2", "both", "Window sill heights and whether windows open could not be read (glass and blinds)", "Measure the bedroom windows"],
             ["U3", "both", "Walls are drawn 4 in. thick everywhere; real thickness unknown, so room sizes are good to about 2 in.", "Tape check of a few rooms"],
             ["U4", "both", "Nothing inside walls or floors: drain stacks, joists, bearing walls, wiring", "Look in the basement and attic; open a ceiling"],
             ["U5", "both", "Openings without doors, odd strips and gaps (390 upper flat 'Hallway 4', 441 'Other 6')", "Tell me what they are"],
             ["U6", "390", "Stairs and entrances only partly scanned", "Tell me where each flat's door and stair are"],
             ["U7", "441", "No 3D scan: heights and stacking not checked", "Export the .laz for 441"],
             ["U8", "441", "No stairs captured on any level", "Scan or describe the stairs"],
             ["U9", "both", "Outside walls missed in places (390 middle flat south-east corner, 441 basement)", "Rescan those corners"],
             ["U10", "both", "Short angled wall pieces kept as scanned: real cut corners or the scan rounding a corner", "Look at each circled spot"],
             ["U11", "390", "Upper flat living room and a few small spaces have too few 3D points for a height", "Tape measure"],
             ["U12", "390", "Ground outside is 1 to 8 ft below the lower flat's floor: room for a cellar under it", "Same as U1; it decides how new drains can run"]]
    table(bg, 0.6, y - 0.85, [0.45, 0.55, 6.4, 4.5], rows2, fs=6.1, rh=0.235)
    save(fig, "EX-001", pdf)


if __name__ == "__main__":
    out = os.path.join(HERE, "drawings", "390-Forest_441-Baird_Scan-Fixes.pdf")
    with PdfPages(out) as pdf:
        sheet_log(pdf)
        sheet_390_stack(pdf)
        ex390(pdf)
        ex441(pdf)
    print("wrote", out)
