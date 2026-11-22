"""Plumbing, mechanical and electrical sheets, one per floor. PRELIMINARY layouts on the architectural background."""
import math

import numpy as np

from common import *  # noqa: F401,F403
from levels import *  # noqa: F401,F403
from struct_sheets import text_columns

CW, HW, SAN, VENT, STORM = "#1f5fa8", "#c0392b", "#2e7d32", "#2e7d32", "#0e8f9c"
PWR, LIT, OR, EX = "#6a1b9a", "#b9770e", "#d35400", "#6a1b9a"
S1 = (12.8, 18.7)             # stack 1: kitchen + bath 1, in the living / bath wet wall
S2 = (30.2, 23.7)             # stack 2: bath 2, bath 3, laundry
S1_DROP = (10.9, 18.7)        # where stack 1 comes down on the garage west wall
S2_DROP = (38.3, 23.0)        # where stack 2 comes down in the mech room
PADS = [(30.6, "HP-A"), (33.6, "HP-B"), (36.6, "HP-S")]
LVL = {"A": ("Unit A", "main level", EL_MAIN), "B": ("Unit B", "upper level", EL_UP)}


def tag(ax, x, y, s, color=INK, size=4.4, box=True, weight="bold", **kw):
    txt(ax, x, y, s, size=size, color=color, weight=weight, box=box, z=12, **kw)


def pipe(ax, pts, color, lw=1.2, ls="-"):
    line(ax, pts, color=color, lw=lw, ls=ls, z=10)


def dot(ax, x, y, color, r=0.28, fill=True):
    ax.add_patch(plt.Circle((x, y), r, fc=color if fill else PAPER, ec=color, lw=1.0, zorder=11))


def garage_bg(ax):
    poly(ax, APRON, fc="#f1f3f5", ec=BG_EDGE, lw=0.5, z=2)
    rect(ax, 37.5, 3, 45, BY0, fc="#f6f7f8", ec=BG_EDGE, lw=0.4, z=2)
    lower_plan(ax, "bg", cars=False)


# ---------------------------------------------------------------------------- plumbing
def sheet_p101(pdf):
    notes = [
        ("Garage level plumbing", [
            "Water: 1-1/4 in. service to the mech",
            "room, then a sub-meter and shutoff per",
            "unit plus a house line (hose bibbs).",
            "WH-A and WH-B: 80 gal electric water",
            "heaters, one per unit (three showers",
            "each), on that unit's panel. Pan, drain",
            "and expansion tank at each.",
        ]),
        ("Sanitary", [
            "Two 3 in. soil stacks come down from",
            "the units. Stack S-1 (kitchens, bath 1)",
            "drops on the west wall. Stack S-2",
            "(baths 2 and 3, laundry) offsets in the",
            "ceiling to the mech room.",
            "Both join a 4 in. building drain under",
            "the slab at 1/4 in. per ft. Two-way",
            "cleanout on the lot before the lot line.",
            "Sewer depth in Baird St is unknown: if",
            "the main is shallow, an ejector is",
            "needed. Ask MUB for the tap card.",
        ]),
        ("Storm and groundwater", [
            "Trench drain and sump discharge are",
            "storm water and may not enter the",
            "sanitary sewer. Outlet location is a",
            "City Engineer decision.",
        ]),
        ("Code basis", [
            "2018 IPC / IRC Part VII as adopted by",
            "West Virginia. Preliminary sizes.",
        ]),
    ]
    fig, bg = new_sheet("P-101", "Plumbing: garage level", "3/16\" = 1'-0\"", notes)
    ax = plan_frame(fig, "Garage level plumbing plan", "Water blue · hot water red dashed · sanitary green · storm teal · preliminary")
    garage_bg(ax)
    pipe(ax, [(42.9, PAVE_N - 2.5), (42.9, 23.6)], CW, 1.6)
    tag(ax, 47.6, -4.6, "1-1/4\" WATER SERVICE\nfrom MUB main\n(location TBC)", CW)
    line(ax, [(45.0, -4.6), (43.1, -4.6)], lw=0.3, color=CW)
    for y in (23.9, 24.9, 25.9):
        rect(ax, 43.0, y - 0.3, 43.8, y + 0.3, fc=PAPER, ec=CW, lw=0.9, z=11)
    tag(ax, 48.4, 25.0, "SUB-METERS A, B,\nHOUSE + PRV +\nBACKFLOW", CW)
    line(ax, [(45.8, 25.0), (43.9, 25.0)], lw=0.3, color=CW)
    pipe(ax, [(43.0, 24.9), (41.4, 24.9), (41.4, 26.6)], CW, 1.0)
    pipe(ax, [(43.0, 23.9), (39.0, 23.9), (39.0, 26.6)], CW, 1.0)
    pipe(ax, [(39.6, 27.0), (40.2, 27.0), (40.2, 28.6), (38.6, 28.6)], HW, 1.0, (0, (4, 2)))
    tag(ax, 40.2, 31.4, "CW + HW RISERS UP TO UNITS A AND B (at each stack)", HW, size=4.2)
    line(ax, [(38.6, 28.6), (38.6, 30.6)], lw=0.3, color=HW)
    for x, y in ((37.3, 7.7), (27.2, 27.7)):
        dot(ax, x, y, CW, 0.3, fill=False)
    tag(ax, 36.0, 6.2, "HB frost-free\n(house)", CW, size=4.0)
    tag(ax, 29.6, 26.6, "HB", CW, size=4.0)
    pipe(ax, [(43.0, 25.9), (37.6, 25.9), (37.6, 8.2), (37.3, 7.9)], CW, 0.8)
    # stack 2: offset to mech room
    pipe(ax, [S2, (S2[0], 23.0), S2_DROP], SAN, 1.6, (0, (5, 2)))
    dot(ax, *S2, SAN, 0.38, fill=False)
    tag(ax, 28.0, 25.2, "S-2  3\" FROM\nUNITS ABOVE", SAN, size=4.2)
    tag(ax, 33.6, 21.4, "3\" OFFSET IN CEILING\n(boxed, 5/8\" Type X)", SAN, size=4.0)
    dot(ax, *S2_DROP, SAN, 0.38)
    # stack 1: drop on west wall, under-slab run to the main drain
    pipe(ax, [S1, S1_DROP], SAN, 1.6, (0, (5, 2)))
    dot(ax, *S1, SAN, 0.38, fill=False)
    dot(ax, *S1_DROP, SAN, 0.38)
    tag(ax, 15.6, 20.0, "S-1  3\" FROM UNITS ABOVE,\ndrops on west wall (boxed)", SAN, size=4.2)
    pipe(ax, [S1_DROP, (10.9, 11.0), (12.0, 10.2), (38.3, 10.2)], SAN, 2.0)
    tag(ax, 24, 11.6, "4\" BRANCH UNDER SLAB, 1/4\"/FT, FROM S-1", SAN, size=4.2)
    pipe(ax, [S2_DROP, (38.3, 9.0), (39.6, 7.0), (39.6, PAVE_N - 2.5)], SAN, 2.2)
    tag(ax, 34.4, 15.4, "4\" BUILDING DRAIN\nUNDER SLAB", SAN, size=4.2)
    line(ax, [(36.6, 15.4), (38.2, 15.4)], lw=0.3, color=SAN)
    dot(ax, 39.6, 1.2, SAN, 0.34, fill=False)
    tag(ax, 43.4, 1.0, "CO two-way cleanout\non lot", SAN, size=4.0)
    line(ax, [(41.2, 1.1), (40.0, 1.2)], lw=0.3, color=SAN)
    tag(ax, 35.2, -5.6, "4\" SEWER TO\nMUB MAIN", SAN, size=4.2)
    line(ax, [(37.2, -5.6), (39.5, -5.6)], lw=0.3, color=SAN)
    rect(ax, 40.2, 22.6, 40.9, 23.3, fc=PAPER, ec=SAN, lw=0.9, z=11)
    tag(ax, 41.5, 22.9, "FD", SAN, size=4.0, box=False)
    pipe(ax, [(40.2, 22.95), (38.5, 22.95)], SAN, 1.0)
    # storm
    pipe(ax, [(DOOR_A[0], 7.55), (DOOR_B[1], 7.55)], STORM, 2.0)
    tag(ax, 20, 5.8, "TRENCH DRAIN, TRAFFIC-RATED GRATE, 4\" OUTLET", STORM, size=4.2)
    pipe(ax, [(DOOR_B[1], 7.55), (37.4, 6.6), (37.4, 1.0)], STORM, 1.2, (0, (3, 2)))
    ax.add_patch(plt.Circle((43.0, 27.8), 0.8, fc=PAPER, ec=STORM, lw=1.0, zorder=11))
    tag(ax, 43.0, 27.8, "SP", STORM, size=4.0, box=False)
    pipe(ax, [(43.0, 27.0), (44.4, 27.0)], STORM, 1.0, (0, (3, 2)))
    tag(ax, 31.6, 2.4, "STORM OUTLET (TD + SUMP):\nlocation by City Engineer", STORM, size=4.0)
    line(ax, [(35.0, 2.0), (37.3, 1.4)], lw=0.3, color=STORM)
    tag(ax, 48.6, 29.2, "SUMP PIT +\nPUMP, footing\ndrain", STORM, size=4.0)
    line(ax, [(46.4, 28.6), (43.9, 28.0)], lw=0.3, color=STORM)
    tag(ax, 19, 30.8, "NO PLUMBING IN STORAGE ROOM · dehumidifier condensate pumped to mech-room floor drain", GREY, size=4.0, weight="normal")
    save(fig, "P-101", pdf)


def unit_plumbing(ax, unit):
    for (sx, sy), lab, lx, ly in ((S1, "S-1", 14.6, 17.2), (S2, "S-2", 31.6, 25.0)):
        dot(ax, sx, sy, SAN, 0.42, fill=False)
        tag(ax, lx, ly, f"{lab} 3\"", SAN, size=4.4)
    # waste, stack 1
    for p in ([(11.0, 11.9), (10.4, 11.9), (10.4, 18.7), S1], [(11.0, 9.8), (10.4, 9.8), (10.4, 11.9)],
              [(11.6, 21.2), (12.8, 21.2), S1], [(14.5, 20.2), (12.8, 20.2)], [(14.6, 22.6), (13.4, 22.6), (13.4, 20.2)]):
        pipe(ax, p, SAN, 1.3)
    # waste, stack 2
    for p in ([(28.4, 21.2), (28.4, 23.7), S2], [(25.6, 22.2), (25.6, 23.7), (28.4, 23.7)], [(25.5, 19.8), (26.8, 19.8), (26.8, 23.7)],
              [(31.8, 22.6), (31.8, 23.7), S2], [(32.3, 28.2), (32.3, 24.3), (30.2, 24.3), S2], [(29.9, 28.0), (29.9, 24.3)],
              [(29.8, 24.8), (30.2, 24.8)]):
        pipe(ax, p, SAN, 1.3)
    # vents
    for p in ([(10.4, 11.9), (10.2, 13.0)], [(13.4, 22.6), (13.4, 23.3)], [(26.8, 19.8), (27.3, 19.2)], [(31.8, 22.6), (32.6, 22.6)]):
        pipe(ax, p, VENT, 0.9, (0, (3, 2)))
    # water risers and branches
    risers = ((13.9, 18.7), (31.2, 23.7))
    for rx, ry in risers:
        dot(ax, rx, ry, CW, 0.24)
        dot(ax, rx + 0.6, ry, HW, 0.24)
    cw = [[(13.9, 18.7), (13.9, 19.6), (11.6, 19.6)], [(13.9, 19.6), (15.4, 19.6), (15.4, 22.2)], [(13.9, 18.7), (13.9, 18.1), (12.3, 18.1), (12.3, 12.2), (11.6, 12.2)],
          [(12.3, 17.0), (11.8, 17.0)], [(31.2, 23.7), (31.2, 23.1), (27.6, 23.1), (27.6, 21.6)], [(27.6, 23.1), (25.0, 23.1)], [(25.0, 23.1), (25.0, 20.2)],
          [(31.2, 23.1), (32.4, 23.1)], [(31.2, 23.7), (31.2, 26.9), (30.6, 26.9)], [(31.2, 26.9), (32.0, 26.9), (32.0, 28.4)], [(31.2, 25.2), (30.4, 25.2)]]
    for p in cw:
        pipe(ax, p, CW, 0.8)
    hw = [[(14.5, 18.7), (14.5, 19.3), (11.9, 19.3)], [(14.5, 19.3), (15.7, 19.3), (15.7, 22.2)], [(14.5, 18.7), (14.5, 17.8), (12.6, 17.8), (12.6, 12.5), (11.6, 12.5)],
          [(12.6, 10.2), (12.6, 12.5)], [(12.6, 10.2), (11.9, 10.2)], [(31.8, 23.7), (31.8, 23.35), (27.9, 23.35), (27.9, 21.9)], [(27.9, 23.35), (25.3, 23.35), (25.3, 20.2)],
          [(31.8, 23.7), (31.8, 26.6), (30.6, 26.6)], [(31.5, 25.5), (30.4, 25.5)]]
    for p in hw:
        pipe(ax, p, HW, 0.8, (0, (4, 2)))
    for x, y, s in ((17.0, 12.0, "KS + DW 2\""), (11.6, 24.4, "SHOWER 2\""), (26.6, 17.6, "BATH 2\nWET VENT 2\""), (35.6, 22.8, "WASHER BOX\n2\" STANDPIPE"),
                    (35.8, 27.8, "BATH 3")):
        tag(ax, x, y, s, SAN, size=3.9)
    line(ax, [(15.0, 12.0), (11.4, 12.0)], lw=0.3, color=SAN)
    line(ax, [(34.0, 22.8), (32.2, 22.7)], lw=0.3, color=SAN)
    tag(ax, 17.6, 16.2, "ICE-MAKER", CW, size=3.8)
    line(ax, [(15.9, 16.6), (12.0, 17.0)], lw=0.3, color=CW)
    if unit == "B":
        tag(ax, 16.4, 14.4, "S-1 AND S-2 CONTINUE UP AS 3\" VENTS THROUGH THE ROOF", VENT, size=4.2)
    else:
        tag(ax, 16.4, 14.4, "S-1 AND S-2 PASS THROUGH FROM UNIT B: FIRESTOP AT THE FLOOR ABOVE", SAN, size=4.2)
    rect(ax, 20.5, 36.0, 49.5, 38.2, fc=PAPER, ec="none", z=11)
    tag(ax, 35, 37.1, "Pipes are drawn beside each other for clarity. They run in the 2x6 wet walls and the floor-truss space.", GREY, size=4.4, weight="normal", box=False)


def unit_plumbing_sheet(pdf, number, unit):
    name, lev, el = LVL[unit]
    notes = [
        (f"{name} plumbing ({lev})", [
            "Three baths, kitchen and laundry on",
            "two stacks, so no drain runs more than",
            "about 8 ft in the floor.",
            "S-1: kitchen sink, dishwasher, bath 1.",
            "S-2: baths 2 and 3, clothes washer.",
            "Units A and B stack exactly.",
        ]),
        ("Water", [
            "3/4 in. cold and hot risers beside each",
            "stack; 1/2 in. branches. Shutoff for the",
            "unit inside the unit.",
            "Insulate hot water to R-3 (IECC).",
            "Pressure-balance valve at each shower.",
        ]),
        ("Drain, waste, vent", [
            "3 in. stack at each group. Showers and",
            "lavatories 2 in., wet-vented where the",
            "code allows. Kitchen sink and washer",
            "individually vented.",
            ("3 in. vents through the roof here, 10 ft\nfrom any window." if unit == "B" else
             "Stacks continue down to the garage\nceiling offset (see P-101)."),
        ]),
        ("Fire-stopping", [
            "Every pipe through the 1-hour floor",
            "between units gets a listed firestop",
            "system. Cast-iron stacks recommended",
            "between units for noise.",
            "No plastic pipe in the stair enclosure.",
        ]),
    ]
    fig, bg = new_sheet(number, f"Plumbing: {name}", "3/16\" = 1'-0\"", notes)
    ax = plan_frame(fig, f"{name} plumbing plan", f"{lev.capitalize()} · EL {el:.1f} · cold blue · hot red dashed · waste green · vent green dashed · preliminary", street=False)
    unit_plan(ax, "bg", unit)
    unit_plumbing(ax, unit)
    save(fig, number, pdf)


def sheet_p201(pdf):
    fig, bg = new_sheet("P-201", "Plumbing riser and schedules", "No scale", [
        ("Reading the riser", [
            "Schematic, not to scale. Unit B is",
            "above Unit A. Two stacks serve both",
            "units and meet under the garage slab.",
        ]),
        ("Open items for the plumber", [
            "MUB sewer and water main locations,",
            "depths and tap fees.",
            "Whether the city wants two sewer",
            "laterals for a two-family dwelling.",
            "Static water pressure (PRV setting).",
            "Water service size by fixture-unit",
            "calculation (six showers).",
            "Gas: none shown; all-electric. Hope",
            "Gas is in the area if wanted.",
            "Sprinklers: confirm whether the state",
            "amendments require them for a",
            "two-family dwelling.",
        ]),
    ])
    ax = fig.add_axes([0.55 / SHEET_W, 0.6 / SHEET_H, 7.6 / SHEET_W, 9.6 / SHEET_H])
    ax.set_xlim(0, 76)
    ax.set_ylim(0, 96)
    ax.axis("off")
    txt(ax, 0, 93.5, "SANITARY AND VENT RISER DIAGRAM", size=10, weight="bold", ha="left")
    lv = {"ROOF": 84, "UNIT B": 62, "UNIT A": 40, "GARAGE": 16}
    for name, y in lv.items():
        line(ax, [(1, y), (75, y)], lw=0.5, color=GREY, ls=(0, (8, 3)))
        txt(ax, 1, y + 1.4, name + (" FLOOR" if "UNIT" in name else (" SLAB" if name == "GARAGE" else "")), size=6.0, weight="bold", ha="left")
    X1, X2 = 22, 60
    for X, lab in ((X1, "S-1"), (X2, "S-2")):
        line(ax, [(X, 88), (X, 26)], color=SAN, lw=2.6)
        txt(ax, X + 1.2, 87.6, f"{lab}  3\" VTR", size=5.4, color=SAN, ha="left", weight="bold")
    for name in ("UNIT B", "UNIT A"):
        y = lv[name]
        g1 = [(4, "KS+DW"), (10, "SH 1"), (16, "LAV 1"), (28, "WC 1")]
        g2 = [(36, "LAV 2"), (42, "SH 2"), (48, "WC 2"), (54, "CW"), (66, "WC 3"), (71.5, "SH/LAV 3")]
        line(ax, [(4, y - 3), (28, y - 3)], color=SAN, lw=1.8)
        line(ax, [(36, y - 3), (71.5, y - 3)], color=SAN, lw=1.8)
        for x, n in g1 + g2:
            line(ax, [(x, y - 3), (x, y + 3)], color=SAN, lw=1.2)
            rect(ax, x - 2.7, y + 3, x + 2.7, y + 6.2, fc=PAPER, ec=SAN, lw=0.8, z=6)
            txt(ax, x, y + 4.6, n, size=4.6, weight="bold", z=7)
        line(ax, [(4, y + 6.2), (4, y + 11), (X1, y + 11)], color=VENT, lw=0.9, ls=(0, (4, 2)))
        line(ax, [(16, y + 6.2), (16, y + 11)], color=VENT, lw=0.9, ls=(0, (4, 2)))
        line(ax, [(36, y + 6.2), (36, y + 11), (X2, y + 11)], color=VENT, lw=0.9, ls=(0, (4, 2)))
        line(ax, [(54, y + 6.2), (54, y + 11)], color=VENT, lw=0.9, ls=(0, (4, 2)))
        line(ax, [(71.5, y + 6.2), (71.5, y + 11), (X2, y + 11)], color=VENT, lw=0.9, ls=(0, (4, 2)))
        txt(ax, 11, y + 12.3, "9 DFU", size=5.0, color=SAN, weight="bold")
        txt(ax, 45, y + 12.3, "12 DFU", size=5.0, color=SAN, weight="bold")
    line(ax, [(X1, 26), (X1, 9), (48, 9)], color=SAN, lw=2.6)
    line(ax, [(X2, 26), (48, 26), (48, 9)], color=SAN, lw=2.6)
    txt(ax, 54, 27.6, "S-2 OFFSET IN GARAGE CEILING", size=4.8, color=SAN)
    txt(ax, 12, 22, "S-1 DROPS ON\nWEST WALL", size=4.8, color=SAN)
    txt(ax, 34, 10.8, "4\" UNDER SLAB", size=4.8, color=SAN)
    line(ax, [(48, 9), (70, 5)], color=SAN, lw=3.2)
    txt(ax, 60, 10.4, "4\" BUILDING DRAIN\n1/4\"/FT · 42 DFU", size=4.8, color=SAN)
    ax.add_patch(plt.Circle((66, 5.7), 1.0, fc=PAPER, ec=SAN, lw=1.2, zorder=6))
    txt(ax, 66, 2.6, "CO", size=5.0, color=SAN, weight="bold")
    txt(ax, 75, 2.6, "TO SEWER", size=5.0, color=SAN, ha="right")
    L = 8.55
    cols = [(L, 4.8, [
        ("Fixture schedule (per unit)", [
            ("Water closets (3)", "1.28 gpf, 3 in. waste · 3 DFU each"),
            ("Lavatories (3)", "1-1/4 in. trap · 1 DFU each"),
            ("Showers (3)", "2 in. waste, pressure-balance · 2 DFU each"),
            ("Kitchen sink + DW", "2 in. waste · 2 + 2 DFU"),
            ("Clothes washer", "2 in. standpipe 18 to 42 in. · 2 DFU"),
            ("Total per unit", "±21 DFU waste, ±15 WSFU water"),
        ]),
        ("Water heaters", [
            ("WH-A, WH-B", "80 gal electric, 4.5 kW, 240 V, 30 A, in\nthe mech room, with pan and drain"),
            ("Why 80 gal", "Three showers per unit can run close\ntogether; 50 gal is short"),
            ("Option", "Heat-pump water heaters cut energy use\nbut need 700 cu ft of air or ducting"),
        ]),
        ("Pipe sizes (preliminary)", [
            ("Water service", "1-1/4 in. copper or CTS PE"),
            ("To each unit", "3/4 in. cold, 3/4 in. hot"),
            ("Soil stacks", "3 in. each (S-1 18 DFU, S-2 24 DFU)"),
            ("Building drain", "4 in. at 1/4 in. per ft"),
            ("Vents through roof", "3 in. at each stack"),
            ("Trench drain outlet", "4 in. to storm, not sanitary"),
        ]),
        ("Materials", [
            ("DWV", "PVC schedule 40; cast iron stacks\nbetween units for noise"),
            ("Water", "PEX-A with copper stub-outs, or type L\ncopper"),
        ]),
    ])]
    text_columns(bg, cols, top=SHEET_H - MARGIN - 0.75, fs=6.3)
    save(fig, "P-201", pdf)


# ---------------------------------------------------------------------------- mechanical
def sheet_m101(pdf):
    notes = [
        ("Garage level HVAC", [
            "Owner storage: HP-S, a 9,000 Btu/h",
            "ductless heat pump with one wall",
            "head, plus a dehumidifier set to 50 %",
            "RH. Both on the house meter.",
            "Mech room: inside the insulated",
            "envelope, kept above freezing by the",
            "water heaters and a 1 kW heater.",
            "Lobby and stair: 1.5 kW wall heater.",
        ]),
        ("Garage", [
            "Unheated. A private garage for three",
            "cars needs no mechanical exhaust by",
            "code. Because this one is buried on",
            "three sides, a CO-sensor exhaust fan",
            "(EF-G, ±300 cfm, rear high to a front",
            "wall louver) is recommended.",
        ]),
        ("Outdoor units", [
            "HP-A, HP-B and HP-S sit on pads in the",
            "rear yard at Unit A floor level, shown",
            "dashed. At least 2 ft from a side lot",
            "line and not in the front yard",
            "(1337.05(D)). Line sets run down the",
            "rear wall to this level for HP-S.",
        ]),
        ("Envelope", [
            "Insulate the storage room and mech",
            "room walls and slab; weather-strip the",
            "storage doors.",
        ]),
    ]
    fig, bg = new_sheet("M-101", "Mechanical: garage level", "3/16\" = 1'-0\"", notes)
    ax = plan_frame(fig, "Garage level HVAC and ventilation plan", "Heat pump orange · exhaust purple · preliminary")
    garage_bg(ax)
    rect(ax, 26.6, 30.0, 27.4, 33.0, fc=OR, ec=OR, z=11)
    tag(ax, 23.6, 31.5, "HP-S HEAD\n9k Btu/h", OR)
    rect(ax, 11.2, 29.0, 13.2, 30.6, fc=PAPER, ec=OR, lw=1.0, z=11)
    tag(ax, 15.6, 29.8, "DEHUMID.", OR, size=4.0)
    for x, lab in PADS:
        rect(ax, x - 1.2, 31.2, x + 1.2, 33.4, fc=PAPER, ec=OR, lw=1.0, z=11, ls="--")
        tag(ax, x, 32.3, lab, OR, size=4.0, box=False)
    tag(ax, 37.5, 35.2, "OUTDOOR UNITS ON PADS ABOVE (rear yard, ±EL 923 to 925)", OR, size=4.2)
    line(ax, [(27.4, 31.5), (28.2, 31.5), (36.6, 31.5)], color=OR, lw=0.8, ls=(0, (2, 2)), z=10)
    rect(ax, 43.2, 9.6, 43.9, 11.6, fc=OR, ec=OR, z=11)
    tag(ax, 41.0, 13.0, "1.5 kW WALL\nHEATER", OR, size=3.8)
    rect(ax, 43.2, 22.6, 43.9, 23.8, fc=OR, ec=OR, z=11)
    tag(ax, 47.6, 22.0, "1 kW HEATER", OR, size=3.8)
    line(ax, [(45.6, 22.4), (44.0, 23.0)], lw=0.3, color=OR)
    rect(ax, 22.6, 26.4, 24.4, 27.6, fc=PAPER, ec=EX, lw=1.2, z=11)
    line(ax, [(22.6, 26.4), (24.4, 27.6)], color=EX, lw=0.8, z=12)
    tag(ax, 23.5, 25.2, "EF-G (recommended)", EX, size=4.0)
    line(ax, [(23.5, 26.4), (23.5, 9.2)], color=EX, lw=1.2, ls=(0, (4, 2)), z=10)
    rect(ax, 22.4, 8.0, 24.6, 8.67, fc=EX, ec=EX, z=11)
    tag(ax, 23.5, 6.6, "LOUVER ABOVE DOOR", EX, size=4.0)
    tag(ax, 19, 14.5, "GARAGE: UNHEATED", GREY, size=5.0, weight="normal")
    save(fig, "M-101", pdf)


def unit_hvac(ax, unit):
    heads = [((25.5, 17.7, 28.5, 18.5), "AH-1\n12k", (27.0, 16.2)), ((19.2, 29.5, 20.0, 32.5), "AH-2\n6k", (17.2, 31.0)),
             ((20.4, 29.5, 21.2, 32.5), "AH-3\n6k", (23.2, 31.0)), ((38.0, 22.2, 41.0, 23.0), "AH-4\n6k", (39.5, 24.6))]
    for (x0, y0, x1, y1), lab, (tx, ty) in heads:
        rect(ax, x0, y0, x1, y1, fc=OR, ec=OR, z=11)
        tag(ax, tx, ty, lab, OR, size=4.2)
    for x, lab in PADS:
        rect(ax, x - 1.2, 31.2, x + 1.2, 33.4, fc=PAPER, ec=OR, lw=1.2, z=11)
        tag(ax, x, 32.3, lab, OR, size=4.0, box=False)
    tag(ax, 37.5, 35.2, "OUTDOOR UNITS ON PADS, REAR YARD" + (" (lines rise up the rear wall)" if unit == "B" else ""), OR, size=4.2)
    hp = 30.6 if unit == "A" else 33.6
    for p in ([(27.0, 18.5), (27.0, 18.7), (33.4, 18.7), (33.4, 29.8), (hp, 29.8), (hp, 31.2)],
              [(19.6, 32.5), (19.6, 34.2), (28.2, 34.2), (28.2, 29.8), (hp, 29.8)], [(20.8, 32.5), (20.8, 34.2)], [(39.5, 23.0), (39.5, 29.8), (hp, 29.8)]):
        line(ax, p, color=OR, lw=0.8, ls=(0, (2, 2)), z=10)
    tag(ax, 24.2, 35.4, "refrigerant line sets in wall / truss space", OR, size=3.8, weight="normal")
    # exhaust
    fans = [((13.9, 20.4), "EF-1", [(13.3, 21.0), (9.4, 21.0)], (9.2, 21.0, "W")), ((26.2, 21.6), "EF-2", [(26.8, 22.2), (29.2, 22.2), (29.2, 30.2)], (29.2, 30.3, "N")),
            ((31.0, 27.4), "EF-3", [(31.0, 28.0), (31.0, 30.2)], (31.0, 30.3, "N"))]
    for (x, y), lab, duct, (tx, ty, d) in fans:
        rect(ax, x - 0.6, y - 0.6, x + 0.6, y + 0.6, fc=PAPER, ec=EX, lw=1.1, z=11)
        line(ax, [(x - 0.6, y - 0.6), (x + 0.6, y + 0.6)], color=EX, lw=0.7, z=12)
        line(ax, duct, color=EX, lw=1.3, z=10)
        term(ax, tx, ty, d)
    tag(ax, 15.6, 20.2, "EF-1", EX, size=3.8)
    tag(ax, 26.2, 20.4, "EF-2", EX, size=3.8)
    tag(ax, 32.3, 26.4, "EF-3", EX, size=3.8)
    rect(ax, 10.05, 13.3, 12.2, 15.8, fc="none", ec=EX, lw=1.2, z=11)
    line(ax, [(10.05, 14.5), (9.4, 14.5)], color=EX, lw=1.3, z=10)
    term(ax, 9.2, 14.5, "W")
    tag(ax, 6.0, 14.5, "RH-1 6\"", EX, size=3.8)
    tag(ax, 6.0, 21.0, "EF-1 4\"", EX, size=3.8)
    line(ax, [(32.4, 22.2), (32.4, 30.2)], color=EX, lw=1.3, z=10)
    term(ax, 32.4, 30.3, "N")
    tag(ax, 30.8, 36.6, "EF-2, EF-3, DV-1 (dryer 4\") TERMINATE AT REAR WALL, 3 FT+ FROM OPENINGS", EX, size=3.8)
    tag(ax, 22, 12.6, "T", OR, size=5.0)
    tag(ax, 27, 12.2, "3/4\" door undercuts return air\nfrom each suite to the living room", GREY, size=4.0, weight="normal")


def term(ax, x, y, d):
    pts = [(x, y - 0.5), (x, y + 0.5), (x - 0.8, y)] if d == "W" else [(x - 0.5, y), (x + 0.5, y), (x, y + 0.8)]
    poly(ax, pts, fc=EX, ec=EX, z=12)


def unit_hvac_sheet(pdf, number, unit):
    name, lev, el = LVL[unit]
    notes = [
        (f"{name} heating and cooling", [
            "One cold-climate ductless heat pump",
            f"(HP-{unit}), about 30,000 Btu/h, with four",
            "wall heads: living 12k and one 6k head",
            "in each bedroom, so each suite sets",
            "its own temperature.",
            "No gas, no flues, no ducts through",
            "the rated floor.",
            "Manual J/S by the HVAC designer.",
        ]),
        ("Ventilation (IRC M1505)", [
            "A bath fan in each of the three baths,",
            "50 cfm each. EF-2 runs continuously at",
            "30 cfm for whole-unit ventilation.",
            "Range hood RH-1: 150 cfm min., straight",
            "out the west wall.",
            "Dryer DV-1: 4 in. rigid duct, about 8 ft,",
            "to the rear wall.",
            "Terminations 3 ft from lot lines and",
            "from windows and doors.",
        ]),
        ("Coordination", [
            "EF-2 and the dryer duct cross above",
            "bath 3 in the truss space.",
            ("Unit B line sets rise up the rear wall\nfrom the pads in a covered chase." if unit == "B" else
             "Unit A line sets enter through the\nrear wall just above floor level."),
            "Condensate from each head to the",
            "nearest bath or laundry drain.",
        ]),
    ]
    fig, bg = new_sheet(number, f"Mechanical: {name}", "3/16\" = 1'-0\"", notes)
    ax = plan_frame(fig, f"{name} HVAC and ventilation plan", f"{lev.capitalize()} · EL {el:.1f} · heat-pump heads orange · exhaust purple · preliminary", street=False)
    rect(ax, 29.2, BY1, 44, 34.2, fc="#f6f7f8", ec=BG_EDGE, lw=0.5, z=2, ls="--")
    unit_plan(ax, "bg", unit)
    unit_hvac(ax, unit)
    save(fig, number, pdf)


# ---------------------------------------------------------------------------- electrical
def recept(ax, x, y, kind="R"):
    c = PWR
    ax.add_patch(plt.Circle((x, y), 0.3, fc=c if kind == "2" else PAPER, ec=c, lw=0.9, zorder=11))
    if kind in ("G", "W"):
        txt(ax, x, y, kind, size=3.4, color=c, weight="bold", z=12)


def light(ax, x, y, kind="C"):
    if kind == "S":
        rect(ax, x - 2, y - 0.25, x + 2, y + 0.25, fc=PAPER, ec=LIT, lw=0.9, z=11)
    else:
        ax.add_patch(plt.Circle((x, y), 0.42, fc=PAPER, ec=LIT, lw=0.9, zorder=11))
        line(ax, [(x - 0.3, y - 0.3), (x + 0.3, y + 0.3)], color=LIT, lw=0.6, z=12)
        line(ax, [(x - 0.3, y + 0.3), (x + 0.3, y - 0.3)], color=LIT, lw=0.6, z=12)


def alarm(ax, x, y, s="SD"):
    rect(ax, x - 0.5, y - 0.4, x + 0.5, y + 0.4, fc=PAPER, ec=ACCENT, lw=0.9, z=11)
    txt(ax, x, y, s, size=3.4, color=ACCENT, weight="bold", z=12)


def panel(ax, x0, y0, x1, y1, lab, tx, ty):
    rect(ax, x0, y0, x1, y1, fc=PWR, ec=PWR, z=11)
    tag(ax, tx, ty, lab, PWR, size=4.4)


def e_legend(ax, x, y):
    items = [("R", "Duplex receptacle, 20 A, tamper-resistant"), ("G", "GFCI-protected receptacle"), ("W", "Weatherproof GFCI receptacle"),
             ("2", "240 V outlet or equipment connection"), ("L", "Ceiling or wall light"), ("A", "Smoke (SD) / smoke + CO (SC) alarm")]
    for i, (k, s) in enumerate(items):
        yy = y - i * 1.15
        if k == "L":
            light(ax, x, yy)
        elif k == "A":
            alarm(ax, x, yy)
        else:
            recept(ax, x, yy, k)
        txt(ax, x + 1.1, yy, s, size=4.2, ha="left", box=True)


def sheet_e101(pdf):
    notes = [
        ("Garage level power", [
            "Meter stack on the east wall: Unit A,",
            "Unit B and House. House panel PH in",
            "the mech room feeds everything on",
            "this level so common loads are not on",
            "a tenant's meter.",
            "All garage and exterior receptacles",
            "GFCI (NEC 210.8). One receptacle per",
            "stall. Door operators on ceiling outlets.",
        ]),
        ("EV-ready", [
            "One 1 in. conduit with pull string from",
            "PH to each stall for a future 40 A,",
            "240 V charger. Three chargers exceed",
            "a 100 A house panel: use load-sharing",
            "chargers or size PH at 200 A.",
        ]),
        ("Lighting", [
            "LED strips on occupancy sensors in",
            "the garage and storage room.",
            "Exterior lights are full-cutoff and",
            "aimed down: no glare onto neighbours",
            "or the street (1337.07(F)).",
            "Stair lights on the house panel with",
            "emergency battery backup.",
        ]),
        ("Code basis", [
            "2020 NEC as adopted by West Virginia.",
            "Preliminary layout for the electrician",
            "or engineer to finalize.",
        ]),
    ]
    fig, bg = new_sheet("E-101", "Electrical: garage level", "3/16\" = 1'-0\"", notes)
    ax = plan_frame(fig, "Garage level power and lighting plan", "Power purple · lighting amber · alarms red · preliminary")
    garage_bg(ax)
    for x, y in ((15, 13.5), (15, 23), (24, 13.5), (24, 23), (33, 13.5), (33, 23), (15, 31), (23, 31)):
        light(ax, x, y, "S")
    for x, y in ((40.8, 25.6), (40.8, 10.6), (40.8, 20.2), (42.4, 7.2), (10.9, 7.3), (28.2, 7.3), (37.2, 7.3)):
        light(ax, x, y)
    for x, y, k in ((10.9, 14, "G"), (10.9, 24, "G"), (36.9, 16, "G"), (28.1, 9.2, "G"), (19.4, 18.4, "G"), (32.9, 18.4, "G"),
                    (12, 33.7, "R"), (20, 33.7, "R"), (26.6, 28.7, "R"), (43.7, 28.6, "G"), (38.0, 26.4, "2"), (41.4, 29.0, "2"),
                    (39.0, 29.0, "2"), (27.2, 31.6, "2"), (36.6, 7.3, "W"), (15, 27.7, "2"), (24, 27.7, "2"), (36.9, 20.4, "2")):
        recept(ax, x, y, k)
    tag(ax, 19.4, 19.8, "GDO", PWR, size=4.0)
    tag(ax, 32.9, 19.8, "GDO", PWR, size=4.0)
    for x, y in ((15, 26.3), (24, 26.3), (34.4, 20.4)):
        tag(ax, x, y, "EV-READY 40A", PWR, size=3.8)
    tag(ax, 24.4, 32.0, "HP-S head\n+ dehumid.", PWR, size=3.8)
    tag(ax, 40.2, 30.6, "WH-A  WH-B  30A each, from unit panels", PWR, size=3.8)
    panel(ax, 37.5, 23.0, 37.9, 25.4, "PH", 36.0, 24.2)
    tag(ax, 33.6, 25.8, "HOUSE PANEL\n100 A (200 A if EV)", PWR, size=4.0, weight="normal")
    rect(ax, 45.0, 10.5, 45.7, 15.5, fc=PWR, ec=PWR, z=11)
    tag(ax, 49.0, 13.0, "METER STACK\n3 METERS\n(A, B, HOUSE)", PWR, size=4.2)
    line(ax, [(45.35, 15.5), (45.35, 17.0), (44.6, 17.0), (44.6, 22.4), (38.0, 22.4)], color=PWR, lw=1.2, ls=(0, (4, 2)), z=10)
    tag(ax, 48.8, 19.0, "FEEDERS TO\nPH, PA, PB\n(PA, PB up in\nshaft wall)", PWR, size=4.0, weight="normal")
    line(ax, [(45.35, 10.5), (45.35, 2.5)], color=PWR, lw=1.4, z=10)
    tag(ax, 49.2, 4.6, "SERVICE LATERAL\nfrom Mon Power:\noverhead or\nunderground TBC", PWR, size=4.0, weight="normal")
    alarm(ax, 42.8, 12.4, "SD")
    alarm(ax, 23.8, 17.0, "HD")
    tag(ax, 23.8, 15.6, "heat detector (recommended)", ACCENT, size=3.8, weight="normal")
    e_legend(ax, -3.6, 31.5)
    save(fig, "E-101", pdf)


def unit_power(ax, unit):
    R = [(19.5, 8.8), (31.0, 8.8), (35.5, 8.8), (24.5, 18.2), (29.5, 18.2), (36.7, 16.6), (20.5, 18.2),
         (10.3, 26.6), (10.3, 32.6), (19.7, 28.0), (19.7, 33.2), (17.6, 34.2),
         (20.7, 28.0), (20.7, 33.2), (27.7, 27.2), (27.7, 32.6),
         (44.2, 23.2), (44.2, 28.8), (35.6, 29.2), (36.6, 22.6), (10.3, 17.2), (30.7, 20.3)]
    for x, y in R:
        recept(ax, x, y, "R")
    for x, y in ((10.3, 10.0), (10.3, 12.9), (15.8, 10.5), (13.7, 23.2), (24.3, 20.9), (28.7, 25.9)):
        recept(ax, x, y, "G")
    for x, y in ((10.3, 14.6), (33.0, 20.3)):
        recept(ax, x, y, "2")
    for x, y in ((20, 7.7), (32, 7.7)):
        recept(ax, x, y, "W")
    tag(ax, 13.4, 14.6, "RANGE 50A", PWR, size=3.6)
    tag(ax, 35.4, 20.3, "DRYER 30A", PWR, size=3.6)
    for x, y in ((22, 13.5), (31, 13.5), (12.9, 13.0), (15.85, 12.0), (15.85, 14.5), (15, 30.2), (24.2, 30.2), (38.2, 26.4),
                 (18.45, 21.2), (22.05, 21.2), (35.3, 20.5), (14.6, 21.0), (25.9, 21.4), (30.9, 26.2), (31.8, 19.8), (16, 6), (28, 6)):
        light(ax, x, y)
    alarm(ax, 17.6, 31.6, "SD")
    alarm(ax, 25.6, 31.6, "SD")
    alarm(ax, 36.4, 24.6, "SD")
    alarm(ax, 28.0, 16.6, "SC")
    panel(ax, 36.6, 13.2, 37.0, 15.0, f"P{unit}", 34.6, 14.1)
    for x, y in ((36.3, 12.4), (18.4, 19.4), (22.0, 19.4), (35.2, 19.4), (17.4, 24.4), (21.0, 24.4), (34.2, 22.8)):
        txt(ax, x, y, "S", size=4.2, color=LIT, weight="bold", z=12)
    for x, y, s in ((27.0, 17.0, "AH-1"), (18.2, 31.0, "AH-2"), (22.2, 31.0, "AH-3"), (39.5, 23.9, "AH-4")):
        tag(ax, x, y, s, PWR, size=3.6)
    e_legend(ax, -3.6, 31.5)


def unit_power_sheet(pdf, number, unit):
    name, lev, el = LVL[unit]
    notes = [
        (f"{name} power ({lev})", [
            f"Panel P{unit}: 125 A, 30 spaces, surface-",
            "mounted on the living-room side of the",
            "stair wall with 30 x 36 in. clear in front.",
            "It is in the shared room, not inside a",
            "bedroom suite, so every occupant can",
            "reach it.",
            "Receptacles so no wall point is more",
            "than 6 ft from one (NEC 210.52).",
        ]),
        ("Kitchen, baths, laundry", [
            "Kitchen: two 20 A small-appliance",
            "circuits, GFCI; island receptacle;",
            "dedicated range, dishwasher,",
            "microwave/hood, refrigerator.",
            "Each bath: its own 20 A GFCI circuit.",
            "Laundry: 20 A washer + 30 A dryer.",
            "AFCI on all 120 V living-area circuits.",
        ]),
        ("Alarms (IRC R314, R315)", [
            "Smoke alarm in each bedroom and one",
            "smoke + CO alarm in the living room",
            "outside the suites. Hard-wired, battery",
            "backup, interconnected.",
        ]),
        ("Fire-stopping", [
            "No back-to-back boxes in rated walls.",
            "Listed putty pads on boxes in the stair",
            "and unit-separation assemblies.",
        ]),
    ]
    fig, bg = new_sheet(number, f"Electrical: {name}", "3/16\" = 1'-0\"", notes)
    ax = plan_frame(fig, f"{name} power and lighting plan", f"{lev.capitalize()} · EL {el:.1f} · power purple · lighting amber · alarms red · preliminary", street=False)
    porch(ax, bg=True)
    unit_plan(ax, "bg", unit)
    unit_power(ax, unit)
    save(fig, number, pdf)


def sheet_e201(pdf):
    fig, bg = new_sheet("E-201", "One-line diagram and loads", "No scale", [
        ("Service", [
            "120/240 V, single-phase, 3-wire.",
            "Calculated demand is about 263 A, so",
            "plan a 320 A class (400 A) service with",
            "a 3-gang meter stack. Confirm with",
            "Mon Power before ordering gear.",
        ]),
        ("Grounding", [
            "Concrete-encased electrode: 20 ft of",
            "#4 bar in the footing, stubbed up at",
            "the service (tell the concrete crew).",
            "Bond the metal water service, the",
            "steel frame and the gas pipe if any.",
        ]),
        ("To finalize", [
            "Overhead vs underground lateral.",
            "Meter location: Mon Power may want",
            "it at the front. The east side yard is",
            "5 ft wide with 3 ft clear required.",
            "EV charging strategy (see E-101).",
        ]),
    ])
    ax = fig.add_axes([0.55 / SHEET_W, 5.0 / SHEET_H, 12.6 / SHEET_W, 5.3 / SHEET_H])
    ax.set_xlim(0, 126)
    ax.set_ylim(0, 53)
    ax.axis("off")
    txt(ax, 0, 50.5, "ELECTRICAL ONE-LINE DIAGRAM", size=10, weight="bold", ha="left")

    def box(x, y, w, h, s, sub=None):
        rect(ax, x, y, x + w, y + h, fc=PAPER, ec=PWR, lw=1.2, z=5)
        txt(ax, x + w / 2, y + h / 2 + (1.0 if sub else 0), s, size=6.0, weight="bold", z=6)
        if sub:
            txt(ax, x + w / 2, y + h / 2 - 1.5, sub, size=4.8, z=6, color=GREY)

    box(2, 36, 18, 8, "UTILITY", "Mon Power · 120/240 V 1Ø")
    line(ax, [(20, 40), (30, 40)], color=PWR, lw=2.0)
    txt(ax, 25, 41.6, "400 A lateral", size=4.8)
    box(30, 30, 22, 20, "METER STACK", "400 A bus · 3 meters\noutdoor, NEMA 3R")
    ys = [45, 40, 35]
    feeds = [("125 A", "PA · UNIT A", "125 A MLO, 30 sp\n#1 AL feeder", ["Range 50A", "Dryer 30A", "WH-A 30A", "Heat pump 35A", "DW, micro, ref.", "2 kitchen SA", "3 bath circuits", "Laundry, lights, recept."]),
             ("125 A", "PB · UNIT B", "125 A MLO, 30 sp\n#1 AL feeder", ["Same as PA", "WH-B 30A"]),
             ("100 A", "PH · HOUSE", "100 A (200 A if EV)\n#2 AL feeder", ["Garage + stair lights", "Door operators", "HP-S + dehumid.", "Sump pump", "Stair + mech heaters", "Exterior", "EV-ready x3"])]
    for y, (brk, name, sub, loads) in zip(ys, feeds):
        line(ax, [(52, y), (62, y)], color=PWR, lw=1.6)
        rect(ax, 55, y - 1.3, 59, y + 1.3, fc=PAPER, ec=PWR, lw=1.0, z=6)
        txt(ax, 57, y + 2.6, brk, size=4.8, weight="bold")
    for x, y, (brk, name, sub, loads) in zip([64, 86, 106], ys, feeds):
        line(ax, [(62, y), (x + 9, y), (x + 9, 27)], color=PWR, lw=1.6)
        box(x, 17, 18, 10, name, sub)
        for j, s in enumerate(loads):
            txt(ax, x + 1, 14.6 - j * 1.75, "· " + s, size=4.8, ha="left")
    line(ax, [(41, 30), (41, 22), (36, 22)], color="#2e7d32", lw=1.2)
    txt(ax, 21, 22, "GROUNDING ELECTRODE\n(footing rebar) + bonds", size=4.8, color="#2e7d32")
    L = MARGIN + 0.45
    cols = [
        (L, 4.0, [("Load summary, each unit (NEC 220.82 optional method)", [
            ("General lighting", "780 sf x 3 VA = 2,340 VA"),
            ("Small appliance + laundry", "3 x 1,500 = 4,500 VA"),
            ("Range", "12,000 VA nameplate"),
            ("Dryer", "5,000 VA"),
            ("Water heater (80 gal)", "4,500 VA"),
            ("Dishwasher, micro, disposal", "3,600 VA"),
            ("Subtotal", "31,940 VA"),
            ("First 10 kVA at 100 %", "10,000 VA"),
            ("Remainder at 40 %", "8,780 VA"),
            ("Heat pump (4 heads) at 100 %", "6,000 VA"),
            ("Demand", "24,780 VA = 103 A  →  125 A panel"),
        ])]),
        (L + 4.42, 4.0, [("House panel PH", [
            ("Lighting, garage + stair", "600 VA"),
            ("Door operators (2)", "1,500 VA"),
            ("HP-S + dehumidifier", "1,800 VA"),
            ("Sump pump", "1,000 VA"),
            ("Stair + mech heaters", "2,500 VA"),
            ("Receptacles", "1,800 VA"),
            ("Subtotal without EV", "9,200 VA = 38 A"),
            ("EV-ready, 3 x 40 A", "up to 23,000 VA if\nall charge at once"),
            ("Result", "100 A without EV, or with\nload-sharing chargers;\n200 A for three full circuits"),
        ])]),
        (L + 8.84, 4.0, [("Service size", [
            ("Unit A", "103 A"),
            ("Unit B", "103 A"),
            ("House (managed EV)", "±57 A"),
            ("Total", "±263 A"),
            ("Select", "400 A (320 A continuous)\nmeter stack"),
        ]), ("Notes", [
            "Preliminary and unsealed. Each unit is calculated\nseparately. The electrician or engineer of record\nconfirms conductor sizes, fault current and\nvoltage drop.",
        ])]),
    ]
    text_columns(bg, cols, top=4.55, fs=6.2, lh=0.158)
    save(fig, "E-201", pdf)
