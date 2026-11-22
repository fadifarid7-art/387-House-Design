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


def sheet_c102(pdf):
    env = byright_envelope()
    env_area = poly_area(env)
    bldg = [(BX0, BY0), (BX1, BY0), (BX1, BY1), (BX0, BY1)]
    fp_area = (BX1 - BX0) * (BY1 - BY0)
    r_ne = perp_to_rear(BX1, BY1)
    r_nw = perp_to_rear(BX0, BY1)
    w_n = perp_to_west(BX0, BY1)
    w_s = perp_to_west(BX0, BY0)
    notes = [
        ("Zoning: R-2 district", [
            "Single and Two-Family Residential",
            "(city zoning layer; no overlay district).",
            "Min. lot 5,000 sf / 40 ft frontage",
            "Setbacks: front 10 to 20, side 5, rear 20",
            "Max. lot coverage 50 %",
            "Max. height 2.5 storeys or 35 ft",
            "Parking: 2 spaces per 1-family dwelling",
        ]),
        ("What the lot allows by right", [
            f"Lot ±{LOT_AREA_CALC:,.0f} to {LOT_AREA_DEED:,.0f} sf = legal",
            "nonconforming lot (under 5,000 sf).",
            f"Setbacks leave a wedge of ±{env_area:,.0f} sf,",
            f"{rear_setback_y(45) - 10:.1f} ft deep at the east end and",
            f"{env[3][1] - 10:.1f} ft at the west. Too shallow for a",
            "house or a car, so a variance is needed.",
        ]),
        ("Concept shown (needs BZA relief)", [
            f"Footprint 36' x 22' = {fp_area:,.0f} sf",
            f"Coverage {fp_area / LOT_AREA_DEED * 100:.0f} % of deeded area (50 % max)",
            "Front setback 8.0 ft (10 required, or",
            "block-average rule 1363.02(C))",
            f"Rear setback {r_ne:.1f} to {r_nw:.1f} ft (20 required)",
            f"Side setbacks 5.0 ft east, {w_n:.1f} to {w_s:.1f} ft west",
        ]),
        ("Demolition warning", [
            "Voluntary demolition ends the existing",
            "house's grandfathered setbacks",
            "(1373.06). Secure variances BEFORE",
            "demolishing or closing without a",
            "zoning contingency.",
        ]),
    ]
    fig, bg = new_sheet("C-102", "Zoning envelope and site plan", "1/8\" = 1'-0\"", notes)
    view = (-16, -27, 74, 54)
    ax = plan_axes(fig, 1.45, 0.44, (view[0], view[2]), (view[1], view[3]), 8)
    base_site(ax, view, contour_alpha=0.55, labels={"29-85": (-8, 30), "29-83": (63, 22), "29-87": (36, 47)})
    existing_buildings(ax, hatch_subject=False)
    lot_outline(ax, dims=False, lw=1.8)
    # by-right envelope
    poly(ax, env, fc="#f3c9c4", ec=ACCENT, lw=0.8, z=9, alpha=0.75)
    txt(ax, 29, 12.3, f"BY-RIGHT BUILDABLE AREA  ±{env_area:,.0f} SF", size=5.6, color=ACCENT, weight="bold", z=12, rot=0)
    # setback lines
    line(ax, [(west_x(SB_FRONT), SB_FRONT), (50, SB_FRONT)], color=ACCENT, lw=0.5, ls=(0, (4, 3)), z=6)
    line(ax, [(LOT_NW[0], rear_setback_y(LOT_NW[0])), (50, rear_setback_y(50))], color=ACCENT, lw=0.5, ls=(0, (4, 3)), z=6)
    line(ax, [(45, 0), (45, 34)], color=ACCENT, lw=0.5, ls=(0, (4, 3)), z=6)
    line(ax, [(west_setback_x(0), 0), (west_setback_x(46), 46)], color=ACCENT, lw=0.5, ls=(0, (4, 3)), z=6)
    txt(ax, 53.5, 10, "10' FRONT\nSETBACK", size=5.0, color=ACCENT, ha="left")
    txt(ax, 53.5, rear_setback_y(50) - 0.2, "20' REAR\nSETBACK", size=5.0, color=ACCENT, ha="left")
    # proposed building
    poly(ax, bldg, fc="#ffffff", ec=INK, lw=2.0, z=8)
    poly(ax, bldg, fc="none", ec=INK, lw=2.0, z=10)
    txt(ax, 27, 27.0, "PROPOSED DWELLING", size=7.4, weight="bold", z=12)
    txt(ax, 27, 24.9, f"36' x 22'  ·  {fp_area:,.0f} sf footprint  ·  2 storeys over garage", size=5.8, z=12)
    txt(ax, 27, 23.2, f"Garage slab EL {EL_GAR:.1f} · Main floor EL {EL_MAIN:.1f}", size=5.8, z=12)
    # porch, apron, steps, pads
    rect(ax, 9, 4, 35, 8, fc="none", ec=BLUE, lw=0.8, z=9, ls="--")
    txt(ax, 22, 6.0, "FRONT PORCH OVER (4' DEEP, MAIN LEVEL)", size=4.9, color=BLUE, z=12, box=True)
    apron = [(12.5, 8), (28.5, 8), (30.2, PAVE_N), (10.3, PAVE_N)]
    poly(ax, apron, fc="#cfd6de", ec=BLUE, lw=0.8, z=5)
    txt(ax, 20.3, -2.6, "DRIVEWAY APRON\n16' door · 15' long\n0 to 12 % (warped)", size=5.0, color=BLUE, z=12)
    pad = [(33, 8), (39, 8), (39.6, PAVE_N), (32.4, PAVE_N)]
    poly(ax, pad, fc="#dfe4ea", ec=BLUE, lw=0.6, z=5)
    txt(ax, 36, -2.6, "LOADING\nPAD", size=4.8, color=BLUE, z=12)
    for i in range(11):
        yy = 2 + i * 1.1 if i < 5 else 9.5 + (i - 6) * 1.1
        if i == 5:
            continue
        line(ax, [(5.4, yy), (9, yy)], lw=0.4, color=BLUE, z=9)
    rect(ax, 5.4, 2, 9, 21, fc="none", ec=BLUE, lw=0.7, z=9)
    txt(ax, -3.2, 12, "ENTRY STEPS\nON GRADE\n(UP TO MAIN\nLEVEL DOOR)", size=4.9, color=BLUE, box=True)
    ax.annotate("", xy=(5.6, 12), xytext=(0.8, 12), arrowprops=dict(arrowstyle="-", lw=0.4, color=BLUE), zorder=9)
    rect(ax, 14, 30, 30, 38, fc="none", ec=BLUE, lw=0.6, z=6, ls=":")
    txt(ax, 22, 34, "REAR PATIO AT GRADE\n(±EL 925.5)", size=5.0, color=BLUE, z=12, box=True)
    # dims for proposed
    dim(ax, (BX0, BY1), (BX1, BY1), 1.3, "36'-0\"", size=5.6)
    dim(ax, (BX1, BY0), (BX1, BY1), -1.3, "22'-0\"", size=5.6, side=-1)
    dim(ax, (30.5, 0), (30.5, BY0), -1.2, "8.0'", size=5.2, color=BLUE, side=-1, ext=False)
    dim(ax, (BX1, 17), (50, 17), 0.0, "5.0'", size=5.2, color=BLUE, ext=False)
    dim(ax, (west_x(26), 26), (BX0, 26), 0.0, f"{perp_to_west(BX0, 26):.1f}'", size=5.2, color=BLUE, ext=False)
    # rear setback call-outs
    for (x, y) in ((BX1, BY1), (BX0, BY1)):
        d = perp_to_rear(x, y)
        s = math.atan(REAR_SLOPE)
        fx, fy = x - d * math.sin(s), y + d * math.cos(s)
        line(ax, [(x, y), (fx, fy)], color=BLUE, lw=0.6, z=9)
        txt(ax, (x + fx) / 2 + (1.9 if x > 30 else -2.2), (y + fy) / 2 + 0.3, f"{d:.1f}'", size=5.4, color=BLUE, box=True)
    # lot dims
    dim(ax, LOT_SE, LOT_SW, 24.0, "50.0'  LOT FRONTAGE", color=ACCENT, size=5.8)
    dim(ax, LOT_NE, LOT_SE, 4.0, "34.0'", color=ACCENT, size=5.8)
    dim(ax, LOT_SW, LOT_NW, 10.5, "48.0'", color=ACCENT, size=5.8)
    # spot grades
    for (x, y, dx, dy) in [(BX0, BY0, -1.0, -1.4), (BX1, BY0, 1.0, -1.4), (BX1, BY1, 1.0, 1.2), (BX0, BY1, -1.0, 1.2)]:
        spot(ax, x, y, dx, dy, size=4.9, color=EARTH)
    for x in (12.5, 28.5, 36):
        spot(ax, x, -9.5, 0.7, -1.3, size=4.9, color=GREY, val=street_el(x))
    txt(ax, 60, -14, "B A I R D   S T R E E T", size=8, weight="bold", color=GREY)
    txt(ax, 60, -17, "±14' pavement in a 30' R/W", size=5.6, color=GREY)
    north_arrow(ax, 67, 47, 3.4, 7.5)
    scale_bar(ax, 28, -24.5, 20, 5, 0.7)
    rect(ax, -15.6, 47.6, 33, 53.4, fc=PAPER, ec="none", z=8)
    view_title(ax, -15, 50.6, "1", "Site plan: zoning envelope and concept footprint",
               "Red tint = area left by R-2 setbacks · heavy outline = concept footprint · brown x = existing grade (LiDAR)", 8.6)
    # legend
    lx, ly = -15, -18.5
    for i, (c, ls, lab) in enumerate([(ACCENT, (0, (9, 2.5, 1.5, 2.5)), "Lot line (tax-map record dims)"),
                                      (ACCENT, (0, (4, 3)), "R-2 minimum setback lines"),
                                      (INK, "-", "Proposed building footprint"),
                                      (BLUE, "--", "Proposed porch / site work"),
                                      (GREY, "--", "Existing building (to be removed)")]):
        line(ax, [(lx, ly - i * 1.7), (lx + 5, ly - i * 1.7)], color=c, lw=1.2 if i in (0, 2) else 0.8, ls=ls, z=9)
        txt(ax, lx + 6, ly - i * 1.7, lab, size=5.2, ha="left")
    save(fig, "C-102", pdf)
    return dict(env_area=env_area, fp_area=fp_area, r_ne=r_ne, r_nw=r_nw, w_n=w_n, w_s=w_s)
