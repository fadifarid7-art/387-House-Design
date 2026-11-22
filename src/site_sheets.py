"""Sheets C-101 (existing conditions) and C-102 (zoning envelope + proposed site plan)."""
import math

import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from common import *  # noqa: F401,F403

PARCELS = neighbour_parcels()
FOOTPRINTS = building_footprints()

LABELS = {
    "29-85": ("442 BAIRD ST", "PARCEL 85"),
    "29-83": ("441 BAIRD ST", "PARCEL 83"),
    "29-87": ("386 FOREST AVE", "PARCEL 87"),
    "29-86": ("382 FOREST AVE", "PARCEL 86"),
    "29-57": ("VACANT LOT", "PARCEL 57"),
    "29-58": ("392 BAIRD ST", "PARCEL 58"),
    "29-56": ("437 BAIRD ST", "PARCEL 56"),
    "29-55": ("439-441 BAIRD ST", "PARCEL 55"),
    "29-59": ("396 BAIRD ST", "PARCEL 59"),
}


def street_geometry(view):
    """Right-of-way = everything not inside a tax parcel; pavement approximated as R/W shrunk 7.5 ft."""
    polys = [Polygon(p["ring"]).buffer(0.3) for p in PARCELS if p["id"] != SUBJECT_ID]
    polys.append(Polygon(LOT).buffer(0.3))
    row = box(*view).difference(unary_union(polys))
    pave = row.buffer(-7.5).buffer(1.5).buffer(-1.5)
    return row, pave


def draw_geom(ax, g, **kw):
    geoms = [g] if g.geom_type == "Polygon" else list(g.geoms)
    for q in geoms:
        if q.geom_type == "Polygon" and q.area > 60:
            poly(ax, list(q.exterior.coords), **kw)


def base_site(ax, view, contour_alpha=1.0, labels=None):
    x0, y0, x1, y1 = view
    xs, ys, Z = elev_grid(x0 - 2, x1 + 2, y0 - 2, y1 + 2, 1.5)
    lv1 = np.arange(math.floor(Z.min()), Z.max(), 1)
    lv5 = np.arange(math.floor(Z.min() / 5) * 5, Z.max(), 5)
    row, pave = street_geometry((x0 - 5, y0 - 5, x1 + 5, y1 + 5))
    draw_geom(ax, pave, fc="#e3e5e8", ec="none", z=1)
    ax.contour(xs, ys, Z, levels=lv1, colors=EARTH, linewidths=0.25, alpha=0.55 * contour_alpha, zorder=2)
    c5 = ax.contour(xs, ys, Z, levels=lv5, colors=EARTH, linewidths=0.7, alpha=0.9 * contour_alpha, zorder=2)
    ax.clabel(c5, fmt="%d", fontsize=5.5, colors=EARTH)
    for p in PARCELS:
        if p["id"] == SUBJECT_ID:
            continue
        line(ax, p["ring"], color=GREY, lw=0.55, z=3)
    for key, (lx, ly) in (labels or {}).items():
        a, b = LABELS[key]
        txt(ax, lx, ly, f"{a}\n{b}", size=5.6, color=GREY, z=6)
    return row, pave


def existing_buildings(ax, hatch_subject=True):
    lot = Polygon(LOT).buffer(3)
    for fp in FOOTPRINTS:
        g = Polygon(fp)
        on_subject = g.representative_point().within(lot)
        poly(ax, fp, fc="#d7dade" if not on_subject else "none", ec=GREY, lw=0.5, z=3,
             hatch="////" if (on_subject and hatch_subject) else None, ls="-" if not on_subject else "--")


def lot_outline(ax, dims=True, lw=1.6):
    poly(ax, LOT, fc="none", ec=ACCENT, lw=lw, z=7, ls=(0, (9, 2.5, 1.5, 2.5)))
    if dims:
        dim(ax, LOT_SE, LOT_SW, 3.2, "50.0'  (FRONT, TAX MAP)", color=ACCENT, size=6.2)
        dim(ax, LOT_NE, LOT_SE, 3.2, "34.0'", color=ACCENT, size=6.2)
        dim(ax, LOT_SW, LOT_NW, 3.2, "48.0'", color=ACCENT, size=6.2)
        L = math.hypot(LOT_NE[0] - LOT_NW[0], LOT_NE[1] - LOT_NW[1])
        dim(ax, LOT_NW, LOT_NE, 3.2, f"±{L:.1f}' (CALC.)", color=ACCENT, size=6.2)


def spot(ax, x, y, dx=1.2, dy=1.2, size=5.4, color=INK, val=None):
    v = elev(x, y) if val is None else val
    line(ax, [(x - 0.5, y - 0.5), (x + 0.5, y + 0.5)], lw=0.5, color=color, z=8)
    line(ax, [(x - 0.5, y + 0.5), (x + 0.5, y - 0.5)], lw=0.5, color=color, z=8)
    txt(ax, x + dx, y + dy, f"{v:.1f}", size=size, color=color, ha="left" if dx >= 0 else "right", box=True)


def sheet_c101(pdf):
    notes = [
        ("Property record", [
            "Owner of record: R & L RENTALS LLC",
            "3025 Greystone Dr, Morgantown WV 26508",
            "Deed Book 1246, Page 78",
            "Legal: Block I, part of Lot 2",
            f"Deeded area 0.0471 ac ({LOT_AREA_DEED:,.0f} sf)",
            f"Tax-map dims compute to ±{LOT_AREA_CALC:,.0f} sf",
            "County GIS polygon: 1,911 sf",
            "Flood risk: low (no mapped flood zone)",
        ]),
        ("Existing building", [
            "2-storey stucco dwelling, built 1929",
            "24' x 16' footprint + 6' x 12' porch",
            "768 sf living area, 2 bed / 1 bath",
            "No basement. Assessor grade D.",
            "Sits at or very near the front lot line.",
        ]),
        ("Terrain (1 m state LiDAR)", [
            "Street rises east to west at about 11 %",
            "(±911 at SE corner to ±917 at SW).",
            "Lot rises ±8 to 12 ft from street to rear",
            "line; a bank of ±3 to 5 ft separates the",
            "pavement from the house terrace.",
        ]),
        ("Basis and accuracy", [
            "Lot lines: county tax map 09-0029",
            "dimensions placed on the GIS frontage.",
            "Neighbours, buildings, street: public GIS,",
            "accuracy about ±3 to 5 ft. Elevations are",
            "NAVD88 ft. NOT A BOUNDARY SURVEY.",
        ]),
    ]
    fig, bg = new_sheet("C-101", "Existing site conditions", "1\" = 10'-0\"", notes)
    view = (-38, -36, 92, 64)
    ax = plan_axes(fig, 0.55, 0.52, (view[0], view[2]), (view[1], view[3]), 10)
    base_site(ax, view, labels={"29-85": (-17, 30), "29-83": (68, 22), "29-87": (30, 53), "29-58": (48, -31.5)})
    existing_buildings(ax)
    lot_outline(ax)
    for (x, y, dx, dy) in [(0, 0, -1.2, -1.6), (50, 0, 1.2, -1.6), (50, 34, 1.4, 1.0), (LOT_NW[0], LOT_NW[1], -1.4, 1.2)]:
        spot(ax, x, y, dx, dy)
    for x in (0, 25, 50):
        spot(ax, x, -13, 0.9, -1.5, color=GREY)
    txt(ax, 24, 19.5, "EXISTING DWELLING\n(TO BE REMOVED)", size=6.0, weight="bold", box=True)
    txt(ax, 16, 36, "REAR YARD", size=5.6, color=GREY)
    txt(ax, 62, -14, "B A I R D   S T R E E T", size=8.5, weight="bold", color=GREY, rot=0)
    txt(ax, 62, -17.6, "30' right-of-way · ±14' pavement · one lane", size=5.8, color=GREY)
    ax.annotate("", xy=(4, -24.5), xytext=(46, -24.5), arrowprops=dict(arrowstyle="-|>", lw=0.8, color=INK), zorder=9)
    txt(ax, 25, -26.6, "STREET CLIMBS ±11 %  (±5.7 ft across the frontage)", size=6.0, box=True)
    ax.annotate("", xy=(30, 42), xytext=(30, 6), arrowprops=dict(arrowstyle="-|>", lw=0.8, color=EARTH, ls="--"), zorder=6)
    txt(ax, 36.5, 30.5, "LOT RISES\n±20 to 28 %", size=5.6, color=EARTH, box=True)
    txt(ax, -25, -3.5, "Baird St continues uphill and\nturns north to Forest Ave", size=5.4, color=GREY, rot=-33)
    north_arrow(ax, 82, 54, 4.2, 8)
    scale_bar(ax, 58, -32, 30, 10, 0.9)
    view_title(ax, -36, 59.5, "1", "Existing site plan", "Contours at 1 ft (5 ft heavy) from WV 1 m LiDAR DEM · parcels from county GIS", 9)
    save(fig, "C-101", pdf)


def site_plan_base(ax, view, contour_alpha=0.55, labels=None, envelope=True):
    base_site(ax, view, contour_alpha=contour_alpha, labels=labels)
    existing_buildings(ax, hatch_subject=False)
    rect(ax, view[0], PAVE_N, view[2], 0, fc="#fbe9e7", ec="none", z=1, alpha=0.7)       # R.O.W. strip in front
    lot_outline(ax, dims=False, lw=1.8)
    poly(ax, OUT, fc="#ffffff", ec=INK, lw=2.0, z=8)
    if envelope:
        poly(ax, byright_envelope(), fc="#f3c9c4", ec=ACCENT, lw=0.8, z=9, alpha=0.75)
    poly(ax, OUT, fc="none", ec=INK, lw=2.0, z=10)
    poly(ax, APRON, fc="#cfd6de", ec=BLUE, lw=0.8, z=5)
    rect(ax, 37.5, 3, 45, BY0, fc="#e2e7ec", ec=BLUE, lw=0.6, z=5)
    line(ax, [(11.2, 7.9), (10.95, 0.5)], lw=2.0, color=GREY, z=6)
    line(ax, [(37.6, 2.8), (45.2, 2.8), (45.2, 7.9)], lw=1.6, color=GREY, z=6)
    rect(ax, 9.5, 4, 35.5, BY0, fc="none", ec=BLUE, lw=0.8, z=9, ls="--")


def sheet_c102(pdf):
    env = byright_envelope()
    env_area = poly_area(env)
    r_ne, r_w = perp_to_rear(BX1, BY1), perp_to_rear(WX1, WY1)
    r_nw = perp_to_rear(BX0, WY1)
    w_n, w_s = perp_to_west(BX0, WY1), perp_to_west(BX0, BY0)
    cov = FOOTPRINT / LOT_AREA_DEED * 100
    notes = [
        ("Zoning: R-2 district", [
            "Two-family dwelling: permitted use.",
            "Min. lot 5,000 sf / 40 ft frontage",
            "Setbacks: front 10 to 20, side 5, rear 20",
            "Max. coverage 50 % · 2.5 storeys / 35 ft",
            "Parking: 1.5 per unit = 3 spaces",
        ]),
        ("Meets the code as drawn", [
            f"Side setbacks 5.0 ft east, {w_n:.1f} to {w_s:.1f} ft west",
            f"Coverage {cov:.0f} % ({FOOTPRINT:,.0f} sf footprint)",
            f"Height {EL_MEAN_ROOF - EL_REF:.1f} ft, 2 storeys over basement",
            "Parking 3 spaces, all enclosed",
            "Porch 73 % of the front (50 % min.)",
            "Nothing but the apron in the R.O.W.",
        ]),
        ("Cannot meet: needs approval", [
            f"1. Rear setback {r_ne:.1f} ft min. (20 req.). The",
            f"   setbacks leave only ±{env_area:,.0f} sf, so no",
            "   building fits without this variance.",
            "2. Front setback 8 ft (10 req.) unless",
            "   block averaging 1363.02(C) governs.",
            "3. Garage 78 % of the front (65 % max).",
            "   Two cars would comply, but a duplex",
            "   needs three spaces.",
            "4. Apron 26 ft wide at the R.O.W. line",
            "   (22 ft): City Engineer approval.",
            "5. Sidewalk waiver (1337.07(E)).",
        ]),
        ("Do not demolish first", [
            "It forfeits the old house's grandfathered",
            "setbacks (1373.06).",
        ]),
    ]
    fig, bg = new_sheet("C-102", "Site plan and zoning", "1/8\" = 1'-0\"", notes)
    view = (-16, -27, 74, 54)
    ax = plan_axes(fig, 1.45, 0.44, (view[0], view[2]), (view[1], view[3]), 8)
    site_plan_base(ax, view, labels={"29-85": (-8, 30), "29-83": (63, 22), "29-87": (38, 47.5)})
    txt(ax, 30, 12.2, f"BY-RIGHT BUILDABLE AREA  ±{env_area:,.0f} SF", size=5.4, color=ACCENT, weight="bold", z=12)
    line(ax, [(west_x(SB_FRONT), SB_FRONT), (50, SB_FRONT)], color=ACCENT, lw=0.5, ls=(0, (4, 3)), z=6)
    line(ax, [(LOT_NW[0], rear_setback_y(LOT_NW[0])), (50, rear_setback_y(50))], color=ACCENT, lw=0.5, ls=(0, (4, 3)), z=6)
    line(ax, [(45, 0), (45, 34)], color=ACCENT, lw=0.5, ls=(0, (4, 3)), z=6)
    line(ax, [(west_setback_x(0), 0), (west_setback_x(46), 46)], color=ACCENT, lw=0.5, ls=(0, (4, 3)), z=6)
    txt(ax, 53.5, 10, "10' FRONT\nSETBACK", size=5.0, color=ACCENT, ha="left")
    txt(ax, 53.5, rear_setback_y(50) - 0.2, "20' REAR\nSETBACK", size=5.0, color=ACCENT, ha="left")
    txt(ax, 27, 27.4, "PROPOSED TWO-FAMILY DWELLING", size=7.0, weight="bold", z=12)
    txt(ax, 27, 25.4, f"{FOOTPRINT:,.0f} sf footprint · 2 storeys over a 3-car garage", size=5.6, z=12)
    txt(ax, 27, 23.7, f"Garage slab EL {EL_GAR:.1f} · Unit A EL {EL_MAIN:.1f} · Unit B EL {EL_UP:.1f}", size=5.4, z=12)
    txt(ax, 19, 32.6, "REAR WING 19' x 5'", size=5.0, z=12)
    txt(ax, 22.5, 6.0, "PORCHES OVER (CANTILEVERED 4')", size=4.7, color=BLUE, z=12, box=True)
    txt(ax, 24, 1.6, "DRIVEWAY APRON", size=5.4, color=BLUE, z=12, weight="bold")
    txt(ax, 41.2, 5.4, "ENTRY\nLANDING", size=4.6, color=BLUE, z=12)
    txt(ax, 62, -3.5, "CITY RIGHT-OF-WAY (tinted):\ndriveway apron only", size=5.0, color=ACCENT)
    txt(ax, -6, -3.5, "bank graded\nback 2:1,\nno wall", size=4.6, color=ACCENT)
    for x in (31.5, 35.5, 39.5):
        rect(ax, x - 1.5, 31.2, x + 1.5, 33.4, fc=PAPER, ec=BLUE, lw=0.6, z=9)
    txt(ax, 35.5, 34.6, "HEAT-PUMP PADS", size=4.4, color=BLUE, z=12)
    dim(ax, (BX0, WY1), (WX1, WY1), 1.3, "19'-0\"", size=5.2)
    dim(ax, (BX1, BY0), (BX1, BY1), -1.3, "22'-0\"", size=5.2, side=-1)
    dim(ax, (BX0, 36.9), (BX1, 36.9), 0, "35'-6\"", size=5.2, ext=False)
    dim(ax, (33, 0), (33, BY0), 0, "8.0'", size=5.0, color=BLUE, side=-1, ext=False)
    dim(ax, (BX1, 17), (50, 17), 0, "5.0'", size=5.0, color=BLUE, ext=False)
    dim(ax, (west_x(26), 26), (BX0, 26), 0, f"{perp_to_west(BX0, 26):.1f}'", size=5.0, color=BLUE, ext=False)
    s = math.atan(REAR_SLOPE)
    for (x, y, dx) in ((BX1, BY1, 2.0), (WX1, WY1, 2.2), (BX0, WY1, -2.4)):
        d = perp_to_rear(x, y)
        fx, fy = x - d * math.sin(s), y + d * math.cos(s)
        line(ax, [(x, y), (fx, fy)], color=BLUE, lw=0.6, z=11)
        txt(ax, (x + fx) / 2 + dx, (y + fy) / 2 + 0.3, f"{d:.1f}'", size=5.2, color=BLUE, box=True, z=12)
    dim(ax, LOT_SE, LOT_SW, 24.0, "50.0'  LOT FRONTAGE", color=ACCENT, size=5.8)
    dim(ax, LOT_NE, LOT_SE, 4.0, "34.0'", color=ACCENT, size=5.8)
    dim(ax, LOT_SW, LOT_NW, 10.5, "48.0'", color=ACCENT, size=5.8)
    for (x, y, dx, dy) in [(BX0, BY0, -1.0, -1.4), (BX1, BY0, 1.0, -1.4), (BX1, BY1, 1.0, 1.2), (BX0, WY1, -1.0, 1.2)]:
        spot(ax, x, y, dx, dy, size=4.9, color=EARTH)
    for x in (11.4, 27.4, 36.9):
        spot(ax, x, -9.5, 0.7, -1.3, size=4.9, color=GREY, val=street_el(x))
    txt(ax, 60, -14, "B A I R D   S T R E E T", size=8, weight="bold", color=GREY)
    txt(ax, 60, -17, "±14' pavement in a 30' R/W · one lane", size=5.6, color=GREY)
    north_arrow(ax, 67, 47, 3.4, 7.5)
    scale_bar(ax, 28, -24.5, 20, 5, 0.7)
    rect(ax, -15.6, 47.6, 33, 53.4, fc=PAPER, ec="none", z=8)
    view_title(ax, -15, 50.6, "1", "Site plan: zoning envelope and proposed footprint",
               "Red tint on lot = area left by R-2 setbacks · heavy outline = proposed · brown x = existing grade (LiDAR)", 8.6)
    lx, ly = -15, -18.5
    for i, (c, ls, lab) in enumerate([(ACCENT, (0, (9, 2.5, 1.5, 2.5)), "Lot line (tax-map record dims)"),
                                      (ACCENT, (0, (4, 3)), "R-2 minimum setback lines"),
                                      (INK, "-", "Proposed building footprint"),
                                      (BLUE, "--", "Porches over / site work on lot"),
                                      (GREY, "--", "Existing building (to be removed)")]):
        line(ax, [(lx, ly - i * 1.7), (lx + 5, ly - i * 1.7)], color=c, lw=1.2 if i in (0, 2) else 0.8, ls=ls, z=9)
        txt(ax, lx + 6, ly - i * 1.7, lab, size=5.2, ha="left")
    save(fig, "C-102", pdf)
    return dict(env_area=env_area, r_ne=r_ne, r_w=r_w, r_nw=r_nw, w_n=w_n, w_s=w_s, cov=cov)


def truck(ax, x, y, ang, length=21.0, width=8.0, color="#b9770e", label=None):
    """Rectangle with its REAR at (x, y), body extending `length` along direction ang (deg)."""
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    px, py = -uy, ux
    def P(d, o):
        return (x + ux * d + px * o, y + uy * d + py * o)
    poly(ax, [P(0, -width / 2), P(length, -width / 2), P(length, width / 2), P(0, width / 2)], fc="#fbeed5", ec=color, lw=1.2, z=12)
    poly(ax, [P(length - 6, -width / 2), P(length, -width / 2), P(length, width / 2), P(length - 6, width / 2)], fc="#f3d9a4", ec=color, lw=0.8, z=13)
    line(ax, [P(-3.0, 0), P(0, 0)], lw=2.2, color=color, z=13)
    if label:
        txt(ax, *P(length * 0.4, 0), label, size=5.0, weight="bold", color=color, z=14, rot=ang if abs(ang) < 90 else ang - 180)


def sheet_c103(pdf):
    notes = [
        ("Why towing is tight here", [
            "The garage is cut into the hill and the",
            "only way out is the front. Baird St is one",
            "lane, ±14 ft wide, on an 11 % grade.",
            "Door to far pavement edge is 29 ft. A",
            "wheel-lift wrecker is ±21 ft and a car",
            "±16 ft, so truck plus car cannot pull",
            "straight out: the tow takes two moves.",
        ]),
        ("Built in to make it easy", [
            "1. Every car is one move from a door:",
            "    no tandem, no stackers.",
            "2. No posts, steps or walls in the apron",
            "    (porches are cantilevered).",
            "3. Flush threshold: slab, drain grate and",
            "    apron at one level, so dollies roll.",
            "4. 16 ft door, no centre post, stalls 1-2:",
            "    a car can be swung out.",
            "5. 9'-2\" ceiling and 8 ft doors clear a",
            "    wheel-lift boom.",
            "6. 2 to 3 ft behind each car to winch it",
            "    back. No kerbs or wheel stops.",
            "7. Light and an outlet at each stall.",
        ]),
        ("Rules for the tow company", [
            "Wheel-lift wrecker with dollies. A",
            "rollback (28 ft+) cannot load inside: it",
            "loads in the street after step 1.",
            "The street is blocked for several",
            "minutes. Leave downhill (east).",
            "Post tow-away signs as state and city",
            "rules require.",
        ]),
    ]
    fig, bg = new_sheet("C-103", "Vehicle access and towing", "1/8\" = 1'-0\"", notes)
    view = (-16, -27, 74, 54)
    ax = plan_axes(fig, 1.45, 0.44, (view[0], view[2]), (view[1], view[3]), 8)
    site_plan_base(ax, view, contour_alpha=0.25, labels={"29-85": (-8, 30), "29-83": (63, 26)}, envelope=False)
    # garage interior simplified
    poly(ax, IN_L, fc="#f7f8f9", ec=GREY, lw=0.5, z=9)
    for i, (a, b) in enumerate(STALLS):
        cx = (a + b) / 2
        rect(ax, cx - 3.1, 10.2, cx + 3.1, 26.6, fc="#e9ecef" if i != 1 else "#fdf0d5", ec=GREY if i != 1 else "#b9770e", lw=0.7, z=11)
        txt(ax, cx, 21.5, f"{i + 1}", size=7, weight="bold", color=GREY, z=13)
    rect(ax, 10.5, 28.33, 27.5, 34, fc="#eef1f4", ec=GREY, lw=0.4, z=10)
    txt(ax, 19, 31.2, "storage", size=4.6, color=GREY, z=12)
    rect(ax, 37.5, 8.67, 44, 29, fc="#eef1f4", ec=GREY, lw=0.4, z=10)
    txt(ax, 40.75, 18.5, "stair +\nmech", size=4.4, color=GREY, z=12)
    for a, b in (DOOR_A, DOOR_B):
        line(ax, [(a, BY0 + 0.3), (b, BY0 + 0.3)], lw=1.6, color=BLUE, z=12)
    # step 1: hook-up position, backed to stall 2
    cx2 = (STALLS[1][0] + STALLS[1][1]) / 2
    truck(ax, cx2, 7.2, 270, label="STEP 1  HOOK UP")
    txt(ax, cx2 + 9.5, -8.0, "truck nose sits 6 ft into the lane:\nstreet is blocked while hooking", size=4.8, color="#b9770e", ha="left", z=14, box=True)
    # step 2: truck in street heading east with car in tow
    truck(ax, 34, -14.2, 0, label="STEP 2  TOW AWAY", color="#1c6b3a")
    rect(ax, 16, -17.3, 31, -11.1, fc="#fdf0d5", ec="#b9770e", lw=0.9, z=12)
    txt(ax, 23.5, -14.2, "car 2", size=4.8, color="#b9770e", z=14)
    ax.annotate("", xy=(66, -14.2), xytext=(57, -14.2), arrowprops=dict(arrowstyle="-|>", lw=1.2, color="#1c6b3a"), zorder=14)
    txt(ax, 64, -19.6, "DOWNHILL (EAST)", size=5.0, color="#1c6b3a", weight="bold")
    # swing arc for the car leaving the door
    from matplotlib.patches import Arc as _Arc
    ax.add_patch(_Arc((cx2 + 9, 2.0), 30, 30, theta1=180, theta2=270, lw=0.9, color="#b9770e", ls=(0, (4, 3)), zorder=13))
    txt(ax, 3.5, -3.6, "car is drawn out on dollies\nand swung onto the street", size=4.8, color="#b9770e", z=14, box=True)
    # dims
    dim(ax, (46.6, PAVE_N), (46.6, BY0), 0, "15' APRON", ext=False, size=5.0, color=BLUE, side=-1)
    dim(ax, (46.6, PAVE_S), (46.6, PAVE_N), 0, "±14' LANE", ext=False, size=5.0, color=GREY, side=-1)
    dim(ax, (52.5, PAVE_S), (52.5, BY0), 0, "29' DOOR TO FAR EDGE", ext=False, size=5.0, side=-1)
    dim(ax, (DOOR_A[0], 9.6), (DOOR_A[1], 9.6), 0, "16' CLEAR", ext=False, size=4.8, color=BLUE)
    dim(ax, (DOOR_B[0], 9.6), (DOOR_B[1], 9.6), 0, "8'", ext=False, size=4.8, color=BLUE)
    txt(ax, 62, -3.5, "CITY RIGHT-OF-WAY (tinted):\nno parking, nothing built", size=5.0, color=ACCENT)
    txt(ax, 60, -23.5, "B A I R D   S T R E E T  ·  one lane, ±11 % grade", size=6.4, weight="bold", color=GREY)
    txt(ax, -15, -13.5, "DAILY USE: cars back out across\nthe 15 ft apron into the lane.\n29 ft of back-up depth (24 ft is\nthe usual aisle), onto a one-lane\nstreet on a grade: fit a convex\nmirror and good door lighting.", size=4.8, ha="left", z=12, box=True)
    north_arrow(ax, 67, 47, 3.4, 7.5)
    scale_bar(ax, -14, -24.5, 20, 5, 0.7)
    rect(ax, -15.6, 47.6, 30, 53.4, fc=PAPER, ec="none", z=8)
    view_title(ax, -15, 50.6, "1", "Vehicle access and tow-truck plan",
               "Amber = wheel-lift wrecker hooking up to stall 2 · green = leaving with the car in tow", 8.6)
    save(fig, "C-103", pdf)
