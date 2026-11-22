"""Plumbing, mechanical and electrical sheets. PRELIMINARY layouts on the architectural background."""
import math

import numpy as np

from common import *  # noqa: F401,F403
from levels import *  # noqa: F401,F403
from struct_sheets import text_columns

CW, HW, SAN, VENT, STORM = "#1f5fa8", "#c0392b", "#2e7d32", "#2e7d32", "#0e8f9c"
PWR = "#6a1b9a"
STACK = (31.8, 25.6)          # main soil stack in the bath wet wall (both units)
MECH_DROP = (38.3, 23.4)      # where the stack comes down in the mech room


def tag(ax, x, y, s, color=INK, size=4.6, r=None, box=True, weight="bold", **kw):
    txt(ax, x, y, s, size=size, color=color, weight=weight, box=box, z=12, **kw)


def pipe(ax, pts, color, lw=1.4, ls="-"):
    line(ax, pts, color=color, lw=lw, ls=ls, z=10)


def dot(ax, x, y, color, r=0.28, fill=True):
    ax.add_patch(plt.Circle((x, y), r, fc=color if fill else PAPER, ec=color, lw=1.0, zorder=11))


# ----------------------------------------------------------------------------
def sheet_p101(pdf):
    notes = [
        ("Garage level plumbing", [
            "Water: 1 in. service to the mech room,",
            "then a sub-meter and shutoff per unit",
            "plus a house line (hose bibbs).",
            "WH-A and WH-B: 50 gal electric water",
            "heaters, one per unit, each on its own",
            "unit's panel. Pan, drain and expansion",
            "tank at each.",
        ]),
        ("Sanitary", [
            "One 3 in. soil stack serves both units.",
            "It offsets in the garage ceiling truss",
            "space to the mech room, drops, and",
            "leaves under the slab as a 4 in. building",
            "drain at 1/4 in. per ft. Two-way cleanout",
            "on the lot before the lot line.",
            "Sewer depth in Baird St is unknown:",
            "if the main is shallow, an ejector is",
            "needed. Ask MUB for the tap card.",
        ]),
        ("Storm and groundwater", [
            "Trench drain and sump discharge are",
            "storm water: they may not go to the",
            "sanitary sewer. Outlet location is a",
            "City Engineer decision.",
            "Floor drain in the mech room.",
        ]),
        ("Code basis", [
            "2018 IPC / IRC Part VII as adopted by",
            "West Virginia. Preliminary sizes.",
        ]),
    ]
    fig, bg = new_sheet("P-101", "Plumbing: garage level", "3/16\" = 1'-0\"", notes)
    ax = plan_frame(fig, "Garage level plumbing plan", "Water blue · hot water red dashed · sanitary green · storm teal · preliminary")
    poly(ax, APRON, fc="#f1f3f5", ec=BG_EDGE, lw=0.5, z=2)
    rect(ax, 37.5, 3, 45, BY0, fc="#f6f7f8", ec=BG_EDGE, lw=0.4, z=2)
    lower_plan(ax, "bg", cars=False)
    # water service
    pipe(ax, [(42.9, PAVE_N - 2.5), (42.9, 23.6)], CW, 1.6)
    tag(ax, 47.6, -4.6, "1\" WATER SERVICE\nfrom MUB main\n(location TBC)", CW)
    line(ax, [(45.2, -4.6), (43.1, -4.6)], lw=0.3, color=CW)
    for i, (y, s) in enumerate(((23.9, "WM-A"), (24.9, "WM-B"), (25.9, "WM-H"))):
        rect(ax, 43.0, y - 0.3, 43.8, y + 0.3, fc=PAPER, ec=CW, lw=0.9, z=11)
    tag(ax, 48.4, 25.0, "SUB-METERS A, B,\nHOUSE + PRV +\nBACKFLOW", CW)
    line(ax, [(45.8, 25.0), (43.9, 25.0)], lw=0.3, color=CW)
    pipe(ax, [(43.0, 24.9), (41.4, 24.9), (41.4, 26.6)], CW, 1.0)
    pipe(ax, [(43.0, 23.9), (39.0, 23.9), (39.0, 26.6)], CW, 1.0)
    pipe(ax, [(39.6, 27.0), (40.2, 27.0), (40.2, 28.6), (38.6, 28.6)], HW, 1.0, (0, (4, 2)))
    tag(ax, 40.2, 31.4, "CW + HW RISERS UP IN WET-WALL CHASE TO UNITS A AND B", HW, size=4.4)
    line(ax, [(38.6, 28.6), (38.6, 30.6)], lw=0.3, color=HW)
    # hose bibbs
    for x, y in ((37.3, 7.7), (27.2, 28.2)):
        dot(ax, x, y, CW, 0.3, fill=False)
    tag(ax, 36.0, 6.2, "HB frost-free\n(house)", CW, size=4.2)
    tag(ax, 30.0, 26.9, "HB", CW, size=4.2)
    pipe(ax, [(43.0, 25.9), (37.6, 25.9), (37.6, 8.2), (37.3, 7.9)], CW, 0.8)
    # sanitary
    pipe(ax, [STACK, (STACK[0], 23.4), MECH_DROP], SAN, 1.6, (0, (5, 2)))
    dot(ax, *STACK, SAN, 0.38, fill=False)
    tag(ax, 30.6, 27.6, "3\" SOIL STACK\nFROM UNITS ABOVE", SAN, size=4.4)
    tag(ax, 33.6, 22.0, "3\" OFFSET IN CEILING TRUSS SPACE\n(boxed in 5/8\" Type X)", SAN, size=4.2)
    dot(ax, *MECH_DROP, SAN, 0.38)
    pipe(ax, [MECH_DROP, (38.3, 9.0), (39.6, 7.0), (39.6, PAVE_N - 2.5)], SAN, 2.2)
    tag(ax, 34.2, 13.5, "4\" BUILDING DRAIN\nUNDER SLAB, 1/4\"/FT", SAN, size=4.4)
    line(ax, [(36.6, 13.5), (38.2, 13.5)], lw=0.3, color=SAN)
    dot(ax, 39.6, 1.2, SAN, 0.34, fill=False)
    tag(ax, 43.4, 1.0, "CO two-way cleanout\non lot", SAN, size=4.2)
    line(ax, [(41.2, 1.1), (40.0, 1.2)], lw=0.3, color=SAN)
    tag(ax, 35.2, -5.6, "4\" SEWER TO\nMUB MAIN", SAN, size=4.4)
    line(ax, [(37.2, -5.6), (39.5, -5.6)], lw=0.3, color=SAN)
    rect(ax, 40.2, 23.2, 40.9, 23.9, fc=PAPER, ec=SAN, lw=0.9, z=11)
    tag(ax, 40.55, 22.0, "FD", SAN, size=4.2)
    pipe(ax, [(40.55, 23.2), (38.5, 23.2)], SAN, 1.0)
    # storm
    pipe(ax, [(DOOR_A[0], 7.55), (DOOR_B[1], 7.55)], STORM, 2.0)
    tag(ax, 20, 5.8, "TRENCH DRAIN, TRAFFIC-RATED GRATE, 4\" OUTLET", STORM, size=4.4)
    pipe(ax, [(DOOR_B[1], 7.55), (37.4, 6.6), (37.4, 1.0)], STORM, 1.2, (0, (3, 2)))
    ax.add_patch(plt.Circle((43.0, 27.8), 0.8, fc=PAPER, ec=STORM, lw=1.0, zorder=11))
    tag(ax, 43.0, 27.8, "SP", STORM, size=4.0, box=False)
    pipe(ax, [(43.0, 27.0), (44.4, 27.0)], STORM, 1.0, (0, (3, 2)))
    tag(ax, 31.6, 2.4, "STORM OUTLET (TD + SUMP):\nlocation by City Engineer", STORM, size=4.2)
    line(ax, [(35.0, 2.0), (37.3, 1.4)], lw=0.3, color=STORM)
    tag(ax, 48.6, 29.2, "SUMP PIT +\nPUMP, footing\ndrain", STORM, size=4.2)
    line(ax, [(46.4, 28.6), (43.9, 28.0)], lw=0.3, color=STORM)
    tag(ax, 19, 30.8, "NO PLUMBING IN STORAGE ROOM · dehumidifier condensate pumped to mech-room floor drain", GREY, size=4.2, weight="normal")
    save(fig, "P-101", pdf)


def sheet_p102(pdf):
    notes = [
        ("Typical unit plumbing", [
            "Units A and B are identical and stack,",
            "so one wet wall serves both.",
            "Fixtures per unit: water closet,",
            "lavatory, tub/shower, kitchen sink,",
            "dishwasher, clothes washer, ice-maker.",
        ]),
        ("Water", [
            "3/4 in. cold and 3/4 in. hot risers in the",
            "wet-wall chase; 1/2 in. branches.",
            "Shutoff for each unit inside the unit.",
            "Insulate hot water to R-3 (IECC).",
            "Scald protection at tub/shower valve.",
        ]),
        ("Drain, waste, vent", [
            "3 in. stack at the water closet.",
            "Tub and lavatory: 2 in. wet-vented.",
            "Kitchen sink + dishwasher: 2 in. branch",
            "in the floor trusses to the stack,",
            "individually vented.",
            "Washer: 2 in. standpipe, 2 in. trap and",
            "branch, vented.",
            "3 in. vent through roof, 10 ft from any",
            "window and the lot line as required.",
        ]),
        ("Fire-stopping", [
            "Every pipe through the 1-hour floor",
            "between units gets a listed firestop",
            "system. No plastic pipe through the",
            "stair enclosure.",
        ]),
    ]
    fig, bg = new_sheet("P-102", "Plumbing: typical unit", "3/16\" = 1'-0\"", notes)
    ax = plan_frame(fig, "Typical unit plumbing plan (Units A and B)", "Cold blue · hot red dashed · waste green · vent green dashed · preliminary", street=False)
    unit_plan(ax, "bg", "A")
    sx, sy = STACK
    # waste
    dot(ax, sx, sy, SAN, 0.42, fill=False)
    tag(ax, 35.4, 27.4, "3\" STACK S-1\n+ 3\" VTR", SAN, size=4.4)
    line(ax, [(33.7, 27.0), (32.2, 25.9)], lw=0.3, color=SAN)
    pipe(ax, [(29.0, 28.2), (31.2, 28.2), (31.2, 25.9), (sx, sy)], SAN, 1.4)          # tub
    pipe(ax, [(30.4, 21.5), (31.2, 21.5), (31.2, 25.3)], SAN, 1.2)                    # lav
    pipe(ax, [(29.6, 19.0), (29.6, 20.2), (31.2, 20.2), (31.2, 21.5)], SAN, 1.4)      # kitchen sink
    pipe(ax, [(27.1, 19.0), (29.6, 19.0)], SAN, 0.9)                                  # dishwasher
    pipe(ax, [(24.2, 29.2), (25.6, 29.2), (25.6, 30.4), (31.2, 30.4)], SAN, 0.0001)
    pipe(ax, [(24.2, 29.2), (26.2, 29.2), (26.2, 26.4), (31.2, 26.4)], SAN, 1.4)      # washer
    tag(ax, 24.2, 30.6, "WASHER BOX\n2\" STANDPIPE", SAN, size=4.0)
    tag(ax, 29.4, 16.9, "KS + DW  2\"", SAN, size=4.2)
    tag(ax, 28.6, 23.6, "2\" WET VENT\n(TUB + LAV)", SAN, size=4.0)
    # vents
    pipe(ax, [(29.6, 20.2), (29.6, 20.9), (31.6, 20.9)], VENT, 0.9, (0, (3, 2)))
    pipe(ax, [(26.2, 29.2), (26.2, 29.6)], VENT, 0.9, (0, (3, 2)))
    # water
    rx, ry = 32.3, 24.4
    dot(ax, rx, ry, CW, 0.26)
    dot(ax, rx, ry - 0.8, HW, 0.26)
    tag(ax, 36.0, 24.2, "3/4\" CW + HW\nRISERS", CW, size=4.2)
    line(ax, [(34.3, 24.2), (32.7, 24.2)], lw=0.3, color=CW)
    cw = [[(rx, ry), (31.0, ry), (31.0, 28.9), (29.6, 28.9)], [(31.0, ry), (31.0, 22.2), (30.4, 22.2)],
          [(31.0, 22.2), (31.0, 20.0), (29.9, 20.0), (29.9, 19.3)], [(31.0, 20.0), (35.4, 20.0), (35.4, 19.6)],
          [(31.0, 26.9), (25.9, 26.9), (25.9, 28.9), (24.6, 28.9)], [(rx, ry), (rx - 0.4, 25.0)]]
    for p in cw:
        pipe(ax, p, CW, 0.9)
    hw = [[(rx, ry - 0.8), (30.6, ry - 0.8), (30.6, 28.5), (29.6, 28.5)], [(30.6, ry - 0.8), (30.6, 22.6), (30.0, 22.6)],
          [(30.6, 22.6), (30.6, 20.4), (29.3, 20.4), (29.3, 19.3)], [(29.3, 19.3), (27.4, 19.3)],
          [(30.6, 26.5), (25.5, 26.5), (25.5, 28.5), (24.6, 28.5)]]
    for p in hw:
        pipe(ax, p, HW, 0.9, (0, (4, 2)))
    tag(ax, 35.6, 21.4, "ICE-MAKER\nBOX", CW, size=4.0)
    line(ax, [(35.4, 20.6), (35.4, 20.0)], lw=0.3, color=CW)
    rect(ax, 21.0, 36.0, 49.5, 38.2, fc=PAPER, ec="none", z=11)
    tag(ax, 35, 37.1, "Pipes are drawn beside each other for clarity. They run in the 2x6 wet wall and the floor-truss space.", GREY, size=4.6, weight="normal", box=False)
    save(fig, "P-102", pdf)


def sheet_p201(pdf):
    fig, bg = new_sheet("P-201", "Plumbing riser and schedules", "No scale", [
        ("Reading the riser", [
            "Schematic, not to scale. Unit B is",
            "above Unit A; both drain to one stack",
            "that offsets at the garage ceiling.",
        ]),
        ("Open items for the plumber", [
            "MUB sewer and water main locations,",
            "depths and tap fees.",
            "Whether the city wants two sewer",
            "laterals for a two-family dwelling.",
            "Static water pressure (PRV setting).",
            "Gas: none shown. All-electric",
            "appliances. Hope Gas is in the area if",
            "gas ranges or heat are wanted.",
            "Sprinklers: confirm whether the state",
            "amendments require them for a",
            "two-family dwelling.",
        ]),
    ])
    ax = fig.add_axes([0.55 / SHEET_W, 0.6 / SHEET_H, 7.4 / SHEET_W, 9.6 / SHEET_H])
    ax.set_xlim(0, 74)
    ax.set_ylim(0, 96)
    ax.axis("off")
    txt(ax, 0, 93.5, "SANITARY AND VENT RISER DIAGRAM", size=10, weight="bold", ha="left")
    lv = {"ROOF": 84, "UNIT B": 62, "UNIT A": 40, "GARAGE": 16}
    for name, y in lv.items():
        line(ax, [(2, y), (72, y)], lw=0.5, color=GREY, ls=(0, (8, 3)))
        txt(ax, 2, y + 1.4, name + (" FLOOR" if "UNIT" in name else (" SLAB" if name == "GARAGE" else "")), size=6.2, weight="bold", ha="left")
    X = 44
    line(ax, [(X, 88), (X, 26)], color=SAN, lw=2.6)
    line(ax, [(X, 88), (X, 84)], color=VENT, lw=2.6)
    txt(ax, X + 1.5, 87.5, "3\" VTR", size=5.6, color=SAN, ha="left", weight="bold")
    for name in ("UNIT B", "UNIT A"):
        y = lv[name]
        fx = [(36, "WC", 3), (29, "TUB", 2), (22, "LAV", 2), (14, "KS+DW", 2), (6, "CW", 2)]
        line(ax, [(6, y - 3), (X, y - 3)], color=SAN, lw=2.0)
        for x, n, sz in fx:
            line(ax, [(x, y - 3), (x, y + 3)], color=SAN, lw=1.4)
            rect(ax, x - 2.6, y + 3, x + 2.6, y + 6.4, fc=PAPER, ec=SAN, lw=0.9, z=6)
            txt(ax, x, y + 4.7, n, size=5.4, weight="bold", z=7)
            txt(ax, x + 0.6, y + 0.4, f"{sz}\"", size=4.8, color=SAN, ha="left")
        line(ax, [(6, y + 6.4), (6, y + 12), (X, y + 12)], color=VENT, lw=1.0, ls=(0, (4, 2)))
        line(ax, [(14, y + 6.4), (14, y + 12)], color=VENT, lw=1.0, ls=(0, (4, 2)))
        line(ax, [(22, y + 6.4), (22, y + 12)], color=VENT, lw=1.0, ls=(0, (4, 2)))
        txt(ax, 25, y + 13.2, "2\" VENT HEADER, 42\" MIN. ABOVE FLOOR", size=4.8, color=VENT)
        txt(ax, 40, y - 4.6, "3\"", size=4.8, color=SAN)
        txt(ax, 50, y + 3, "11 DFU", size=5.4, color=SAN, ha="left", weight="bold")
    line(ax, [(X, 26), (58, 26), (58, 16)], color=SAN, lw=2.6)
    txt(ax, 51, 27.6, "3\" OFFSET IN GARAGE\nCEILING TRUSS SPACE", size=5.0, color=SAN)
    line(ax, [(58, 16), (58, 9), (70, 6)], color=SAN, lw=3.2)
    txt(ax, 63.5, 11.2, "4\" BUILDING DRAIN\n1/4\"/FT · 22 DFU", size=5.0, color=SAN)
    ax.add_patch(plt.Circle((66, 7), 1.0, fc=PAPER, ec=SAN, lw=1.2, zorder=6))
    txt(ax, 66, 3.6, "CO", size=5.0, color=SAN, weight="bold")
    txt(ax, 71.5, 3.2, "TO SEWER", size=5.0, color=SAN, ha="right")
    rect(ax, 49.5, 16, 53.5, 19, fc=PAPER, ec=SAN, lw=0.9)
    txt(ax, 51.5, 17.5, "FD", size=5.2, weight="bold")
    line(ax, [(51.5, 16), (51.5, 12), (58, 12)], color=SAN, lw=1.4)
    txt(ax, 42, 20.5, "CO AT BASE OF STACK", size=4.8, color=SAN, ha="right")
    line(ax, [(42.5, 20.5), (57.5, 20.5)], lw=0.3, color=SAN)
    # schedules (right side)
    L = 8.35
    cols = [(L, 5.0, [
        ("Fixture schedule (per unit)", [
            ("Water closet", "1.28 gpf, 3 in. waste, 1/2 in. cold · 3 DFU"),
            ("Lavatory", "1-1/4 in. trap, 1/2 in. hot + cold · 1 DFU"),
            ("Tub / shower", "2 in. waste, pressure-balance valve · 2 DFU"),
            ("Kitchen sink", "2 in. waste, with dishwasher · 2 + 2 DFU"),
            ("Clothes washer", "2 in. standpipe 18 to 42 in. high · 2 DFU"),
            ("Total per unit", "±11 DFU waste, ±17 WSFU water"),
        ]),
        ("Water heaters", [
            ("WH-A, WH-B", "50 gal electric, 4.5 kW, 240 V, 30 A, in\nthe mech room with pan and drain"),
            ("Option", "Heat-pump water heaters cut energy use\nbut need 700 cu ft of air or ducting"),
        ]),
        ("Pipe sizes (preliminary)", [
            ("Water service", "1 in. type K copper or CTS PE"),
            ("To each unit", "3/4 in. cold, 3/4 in. hot (PEX or copper)"),
            ("Soil stack", "3 in. (two water closets, 22 DFU)"),
            ("Building drain", "4 in. at 1/4 in. per ft"),
            ("Vent through roof", "3 in."),
            ("Trench drain outlet", "4 in. to storm, not sanitary"),
        ]),
        ("Materials", [
            ("DWV", "PVC schedule 40; cast iron for the stack\nbetween units is quieter (recommended)"),
            ("Water", "PEX-A with copper stub-outs, or type L\ncopper"),
        ]),
    ])]
    text_columns(bg, cols, top=SHEET_H - MARGIN - 0.75, fs=6.4)
    save(fig, "P-201", pdf)


# ----------------------------------------------------------------------------
def sheet_m101(pdf):
    notes = [
        ("Heating and cooling", [
            "Each unit: one cold-climate ductless",
            "heat pump, about 24,000 Btu/h, with",
            "three wall heads (living 12k, bedrooms",
            "6k each). No gas, no flues, no ducts",
            "through the rated floor.",
            "HP-A, HP-B and HP-S outdoor units sit",
            "on pads in the rear yard: at least 2 ft",
            "from a side lot line and not in the front",
            "yard (1337.05(D)).",
            "Manual J/S by the HVAC designer.",
        ]),
        ("Ventilation (IRC M1505)", [
            "Bath fan EF-1: 80 cfm, runs continuous",
            "at 30 cfm for whole-unit ventilation.",
            "Range hood RH-1: 150 cfm min., 6 in.",
            "duct to the rear wall.",
            "Dryer DV-1: 4 in. rigid duct, under 35 ft",
            "equivalent, to the wing rear wall.",
            "Terminations 3 ft from lot lines and",
            "from openings.",
        ]),
        ("Garage level", [
            "Storage room: HP-S 9,000 Btu/h mini-",
            "split + dehumidifier (50 % RH), house",
            "meter. Mech room: inside the insulated",
            "envelope. Stair: 1.5 kW wall heater.",
            "Garage: unheated; 3-car private garage",
            "needs no mechanical exhaust.",
        ]),
    ]
    fig, bg = new_sheet("M-101", "Mechanical: typical unit", "3/16\" = 1'-0\"", notes)
    ax = plan_frame(fig, "Typical unit HVAC and ventilation plan (Units A and B)", "Heat-pump heads orange · exhaust purple · preliminary", street=False)
    rect(ax, 30, BY1, 44, 34.2, fc="#f6f7f8", ec=BG_EDGE, lw=0.5, z=2, ls="--")
    unit_plan(ax, "bg", "A")
    OR, EX = "#d35400", "#6a1b9a"
    heads = [((10.1, 16.8, 10.9, 19.8), "AH-1\n12k", (13.6, 18.3)), ((18.0, 33.7, 21.0, 34.5), "AH-2\n6k", (19.5, 32.0)),
             ((43.7, 22.9, 44.5, 24.4), "AH-3\n6k", (41.6, 23.6))]
    for (x0, y0, x1, y1), lab, (tx, ty) in heads:
        rect(ax, x0, y0, x1, y1, fc=OR, ec=OR, z=11)
        tag(ax, tx, ty, lab, OR, size=4.4)
    for x, lab in ((32.0, "HP-A"), (36.0, "HP-B"), (40.0, "HP-S")):
        rect(ax, x - 1.5, 31.2, x + 1.5, 33.4, fc=PAPER, ec=OR, lw=1.2, z=11)
        tag(ax, x, 32.3, lab, OR, size=4.4, box=False)
    tag(ax, 37, 35.2, "OUTDOOR UNITS ON PADS, REAR YARD (grade ±EL 923 to 925)", OR, size=4.4)
    line(ax, [(10.5, 19.8), (10.5, 20.2), (21.6, 20.2), (21.6, 29.7), (31.8, 29.7), (31.8, 31.2)], color=OR, lw=0.8, ls=(0, (2, 2)), z=10)
    line(ax, [(19.5, 33.7), (19.5, 29.7)], color=OR, lw=0.8, ls=(0, (2, 2)), z=10)
    line(ax, [(44.1, 24.4), (44.1, 29.7), (33.0, 29.7), (33.0, 31.2)], color=OR, lw=0.8, ls=(0, (2, 2)), z=10)
    tag(ax, 16.0, 21.5, "refrigerant line sets in truss space / wall", OR, size=4.0, weight="normal")
    # exhaust
    rect(ax, 28.3, 24.3, 29.5, 25.5, fc=PAPER, ec=EX, lw=1.2, z=11)
    line(ax, [(28.3, 24.3), (29.5, 25.5)], color=EX, lw=0.8, z=12)
    tag(ax, 28.9, 23.2, "EF-1", EX, size=4.4)
    line(ax, [(28.9, 25.5), (28.9, 26.6), (30.0, 26.6), (30.0, 30.2)], color=EX, lw=1.4, z=10)
    rect(ax, 31.5, 18.4, 33.6, 19.6, fc="none", ec=EX, lw=1.2, z=11)
    tag(ax, 32.5, 17.2, "RH-1", EX, size=4.4)
    line(ax, [(33.2, 19.6), (33.2, 30.2)], color=EX, lw=1.4, z=10)
    line(ax, [(24.2, 29.0), (24.2, 35.2)], color=EX, lw=1.4, z=10)
    tag(ax, 24.2, 36.4, "DV-1 4\" DRYER VENT", EX, size=4.2)
    tag(ax, 30.4, 37.6, "", EX)
    for x, y in ((30.0, 30.3), (33.2, 30.3), (24.2, 35.3)):
        poly(ax, [(x - 0.5, y), (x + 0.5, y), (x, y + 0.8)], fc=EX, ec=EX, z=12)
    tag(ax, 27.2, 31.3, "EF-1 4\"", EX, size=4.0)
    tag(ax, 35.0, 28.6, "RH-1 6\"", EX, size=4.0)
    tag(ax, 16, 14.6, "T", OR, size=5.0)
    tag(ax, 26.4, 10.4, "Transfer: 3/4\" door undercuts\nfor return air to living", GREY, size=4.2, weight="normal")
    save(fig, "M-101", pdf)


# ----------------------------------------------------------------------------
def recept(ax, x, y, kind="R"):
    c = PWR
    ax.add_patch(plt.Circle((x, y), 0.3, fc=PAPER, ec=c, lw=0.9, zorder=11))
    if kind == "G":
        txt(ax, x, y, "G", size=3.4, color=c, weight="bold", z=12)
    elif kind == "W":
        txt(ax, x, y, "W", size=3.4, color=c, weight="bold", z=12)
    elif kind == "2":
        ax.add_patch(plt.Circle((x, y), 0.3, fc=c, ec=c, lw=0.9, zorder=11))


def light(ax, x, y, kind="C"):
    c = "#b9770e"
    if kind == "S":
        rect(ax, x - 2, y - 0.25, x + 2, y + 0.25, fc=PAPER, ec=c, lw=0.9, z=11)
    else:
        ax.add_patch(plt.Circle((x, y), 0.42, fc=PAPER, ec=c, lw=0.9, zorder=11))
        line(ax, [(x - 0.3, y - 0.3), (x + 0.3, y + 0.3)], color=c, lw=0.6, z=12)
        line(ax, [(x - 0.3, y + 0.3), (x + 0.3, y - 0.3)], color=c, lw=0.6, z=12)


def alarm(ax, x, y, s="SD"):
    rect(ax, x - 0.5, y - 0.4, x + 0.5, y + 0.4, fc=PAPER, ec=ACCENT, lw=0.9, z=11)
    txt(ax, x, y, s, size=3.4, color=ACCENT, weight="bold", z=12)


def panel(ax, x0, y0, x1, y1, lab, tx, ty):
    rect(ax, x0, y0, x1, y1, fc=PWR, ec=PWR, z=11)
    tag(ax, tx, ty, lab, PWR, size=4.4)


def e_legend(ax, x, y):
    items = [("R", "Duplex receptacle, 20 A, tamper-resistant"), ("G", "GFCI-protected receptacle"), ("W", "Weatherproof GFCI receptacle"),
             ("2", "240 V outlet or equipment connection"), ("L", "Ceiling or wall light"), ("A", "Smoke (SD) / smoke + CO (SC) alarm, interconnected")]
    for i, (k, s) in enumerate(items):
        yy = y - i * 1.15
        if k == "L":
            light(ax, x, yy)
        elif k == "A":
            alarm(ax, x, yy)
        else:
            recept(ax, x, yy, k)
        txt(ax, x + 1.1, yy, s, size=4.4, ha="left")


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
    poly(ax, APRON, fc="#f1f3f5", ec=BG_EDGE, lw=0.5, z=2)
    rect(ax, 37.5, 3, 45, BY0, fc="#f6f7f8", ec=BG_EDGE, lw=0.4, z=2)
    lower_plan(ax, "bg", cars=False)
    for x, y in ((15, 13.5), (15, 23), (24, 13.5), (24, 23), (33, 13.5), (33, 23), (15, 31), (23, 31)):
        light(ax, x, y, "S")
    for x, y in ((40.8, 25.0), (40.8, 10.6), (40.8, 20.6), (42.4, 7.2), (10.9, 7.3), (28.2, 7.3), (37.2, 7.3)):
        light(ax, x, y)
    for x, y, k in ((10.9, 14, "G"), (10.9, 24, "G"), (36.9, 16, "G"), (28.1, 9.2, "G"), (19.4, 18.4, "G"), (32.9, 18.4, "G"),
                    (12, 33.7, "R"), (20, 33.7, "R"), (26.6, 28.7, "R"), (43.7, 28.6, "G"), (38.0, 26.4, "2"), (41.4, 29.0, "2"),
                    (39.0, 29.0, "2"), (27.2, 31.6, "2"), (36.6, 7.3, "W"), (15, 27.7, "2"), (24, 27.7, "2"), (36.9, 21, "2")):
        recept(ax, x, y, k)
    tag(ax, 19.4, 19.8, "GDO", PWR, size=4.0)
    tag(ax, 32.9, 19.8, "GDO", PWR, size=4.0)
    for x, y in ((15, 26.3), (24, 26.3), (34.6, 21)):
        tag(ax, x, y, "EV-READY 40A", PWR, size=3.8)
    tag(ax, 24.4, 32.0, "HP-S head\n+ dehumid.", PWR, size=3.8)
    tag(ax, 40.2, 30.6, "WH-A  WH-B  30A each, from unit panels", PWR, size=3.8)
    panel(ax, 37.5, 23.0, 37.9, 25.4, "PH", 36.0, 24.2)
    tag(ax, 33.6, 25.6, "HOUSE PANEL\n100 A (200 A if EV)", PWR, size=4.0, weight="normal")
    rect(ax, 45.0, 10.5, 45.7, 15.5, fc=PWR, ec=PWR, z=11)
    tag(ax, 49.0, 13.0, "METER STACK\n3 METERS\n(A, B, HOUSE)", PWR, size=4.2)
    line(ax, [(45.35, 15.5), (45.35, 17.0), (44.6, 17.0), (44.6, 22.6), (38.0, 22.6)], color=PWR, lw=1.2, ls=(0, (4, 2)), z=10)
    tag(ax, 48.8, 19.0, "FEEDERS TO\nPH, PA, PB\n(PA, PB up in\nshaft wall)", PWR, size=4.0, weight="normal")
    line(ax, [(45.35, 10.5), (45.35, 2.5)], color=PWR, lw=1.4, z=10)
    tag(ax, 49.2, 4.6, "SERVICE LATERAL\nfrom Mon Power:\noverhead or\nunderground TBC", PWR, size=4.0, weight="normal")
    alarm(ax, 42.8, 12.4, "SD")
    alarm(ax, 23.8, 17.0, "HD")
    tag(ax, 23.8, 15.6, "heat detector (recommended)", ACCENT, size=3.8, weight="normal")
    tag(ax, 43.2, 26.0, "sump", PWR, size=3.6, weight="normal")
    e_legend(ax, -3.6, 31.5)
    save(fig, "E-101", pdf)


def sheet_e102(pdf):
    notes = [
        ("Typical unit power", [
            "Panel PA / PB: 125 A, 30 spaces, in the",
            "hall with 30 x 36 in. clear in front.",
            "Receptacles so no wall point is more",
            "than 6 ft from one (NEC 210.52).",
            "Kitchen: two 20 A small-appliance",
            "circuits, GFCI; island receptacle;",
            "dedicated range, dishwasher,",
            "microwave/hood, refrigerator.",
            "Bath: 20 A GFCI. Laundry: 20 A washer",
            "+ 30 A, 240 V dryer.",
            "AFCI on all 120 V living-area circuits.",
        ]),
        ("Alarms (IRC R314, R315)", [
            "Smoke alarm in each bedroom and",
            "outside the bedrooms; hard-wired,",
            "battery backup, interconnected.",
            "CO alarm outside bedrooms because of",
            "the attached garage.",
        ]),
        ("Lighting", [
            "LED throughout; 90 % high-efficacy.",
            "Switched light at each room entry,",
            "porch light, 3-way at hall.",
        ]),
        ("Fire-stopping", [
            "No back-to-back boxes in the rated",
            "walls. Listed putty pads on boxes in",
            "the stair and unit-separation walls.",
        ]),
    ]
    fig, bg = new_sheet("E-102", "Electrical: typical unit", "3/16\" = 1'-0\"", notes)
    ax = plan_frame(fig, "Typical unit power and lighting plan (Units A and B)", "Power purple · lighting amber · alarms red · preliminary", street=False)
    porch(ax, bg=True)
    unit_plan(ax, "bg", "A")
    R = [(10.3, 10.3), (10.3, 17.6), (14.5, 19.7), (21.0, 19.7), (22.5, 8.8), (11.0, 8.8), (31.5, 8.8), (36.7, 14.5), (36.7, 17.0),
         (10.3, 22.0), (10.3, 30.5), (19.5, 34.2), (21.7, 27.5), (15.0, 20.7), (11.5, 34.2),
         (44.2, 23.2), (44.2, 28.9), (34.5, 29.2), (33.0, 20.7), (38.5, 23.0), (24.2, 20.7), (27.0, 34.2)]
    for x, y in R:
        recept(ax, x, y, "R")
    for x, y in ((27.0, 19.8), (30.6, 19.8), (34.1, 19.75), (30.0, 13.4), (29.2, 20.7), (23.1, 29.2)):
        recept(ax, x, y, "G")
    for x, y in ((32.5, 19.8), (25.3, 29.2)):
        recept(ax, x, y, "2")
    for x, y in ((22.0, 7.7), (33.0, 7.7)):
        recept(ax, x, y, "W")
    tag(ax, 32.5, 21.0, "RANGE 50A", PWR, size=3.6)
    tag(ax, 27.4, 28.0, "DRYER 30A", PWR, size=3.6)
    for x, y in ((16, 14), (25, 12.5), (28.5, 14.5), (31.5, 14.5), (31, 17), (24.2, 23.2), (16, 27.5), (38.5, 26), (29, 25.4),
                 (30.4, 21.8), (25.2, 32.2), (16, 6), (28, 6)):
        light(ax, x, y)
    alarm(ax, 20.2, 22.8, "SD")
    alarm(ax, 34.3, 24.0, "SD")
    alarm(ax, 24.2, 18.6, "SC")
    panel(ax, 25.6, 24.4, 26.0, 26.2, "PA / PB", 24.2, 25.3)
    for x, y in ((36.2, 12.6), (23.0, 22.3), (25.4, 22.3), (34.6, 20.8), (22.6, 19.5)):
        txt(ax, x, y, "S", size=4.4, color="#b9770e", weight="bold", z=12)
    tag(ax, 13.6, 18.3, "AH-1", PWR, size=3.8)
    tag(ax, 19.5, 32.6, "AH-2", PWR, size=3.8)
    tag(ax, 42.0, 23.8, "AH-3", PWR, size=3.8)
    tag(ax, 28.9, 23.4, "EF-1", PWR, size=3.8)
    e_legend(ax, -3.6, 31.5)
    save(fig, "E-102", pdf)


def sheet_e201(pdf):
    fig, bg = new_sheet("E-201", "One-line diagram and loads", "No scale", [
        ("Service", [
            "120/240 V, single-phase, 3-wire.",
            "Calculated demand is about 255 A, so",
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

    def box(x, y, w, h, s, sub=None, fc=PAPER):
        rect(ax, x, y, x + w, y + h, fc=fc, ec=PWR, lw=1.2, z=5)
        txt(ax, x + w / 2, y + h / 2 + (1.0 if sub else 0), s, size=6.0, weight="bold", z=6)
        if sub:
            txt(ax, x + w / 2, y + h / 2 - 1.5, sub, size=4.8, z=6, color=GREY)

    box(2, 36, 18, 8, "UTILITY", "Mon Power · 120/240 V 1Ø")
    line(ax, [(20, 40), (30, 40)], color=PWR, lw=2.0)
    txt(ax, 25, 41.6, "400 A lateral", size=4.8)
    box(30, 30, 22, 20, "METER STACK", "400 A bus · 3 meters\noutdoor, NEMA 3R")
    ys = [45, 40, 35]
    feeds = [("125 A", "PA · UNIT A", "125 A MLO, 30 sp\n#1 AL feeder", ["Range 50A", "Dryer 30A", "WH-A 30A", "Heat pump 30A", "DW, micro, ref.", "2 kitchen SA", "Bath, laundry", "Lighting / recept."]),
             ("125 A", "PB · UNIT B", "125 A MLO, 30 sp\n#1 AL feeder", ["Same as PA", "WH-B 30A"]),
             ("100 A", "PH · HOUSE", "100 A (200 A if EV)\n#2 AL feeder", ["Garage + stair lights", "Door operators", "HP-S + dehumid.", "Sump pump", "Stair heater", "Exterior", "EV-ready x3"])]
    for y, (brk, name, sub, loads) in zip(ys, feeds):
        line(ax, [(52, y), (62, y)], color=PWR, lw=1.6)
        rect(ax, 55, y - 1.3, 59, y + 1.3, fc=PAPER, ec=PWR, lw=1.0, z=6)
        txt(ax, 57, y + 2.6, brk, size=4.8, weight="bold")
    px = [64, 86, 108]
    for i, (x, (brk, name, sub, loads)) in enumerate(zip(px, feeds)):
        y = ys[i]
        line(ax, [(62, y), (62 + 0.1, y)], color=PWR, lw=1.6)
        line(ax, [(62, y), (x + 9, y), (x + 9, 27)], color=PWR, lw=1.6) if i else line(ax, [(62, y), (x + 9, y), (x + 9, 27)], color=PWR, lw=1.6)
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
            ("Water heater", "4,500 VA"),
            ("Dishwasher, micro, disposal", "3,600 VA"),
            ("Subtotal", "31,940 VA"),
            ("First 10 kVA at 100 %", "10,000 VA"),
            ("Remainder at 40 %", "8,780 VA"),
            ("Heat pump + aux at 100 %", "5,000 VA"),
            ("Demand", "23,780 VA = 99 A  →  125 A panel"),
        ])]),
        (L + 4.42, 4.0, [("House panel PH", [
            ("Lighting, garage + stair", "600 VA"),
            ("Door operators (2)", "1,500 VA"),
            ("HP-S + dehumidifier", "1,800 VA"),
            ("Sump pump", "1,000 VA"),
            ("Stair heater", "1,500 VA"),
            ("Receptacles", "1,800 VA"),
            ("Subtotal without EV", "8,200 VA = 34 A"),
            ("EV-ready, 3 x 40 A", "up to 23,000 VA if\nall charge at once"),
            ("Result", "100 A without EV, or with\nload-sharing chargers;\n200 A for three full circuits"),
        ])]),
        (L + 8.84, 4.0, [("Service size", [
            ("Unit A", "99 A"),
            ("Unit B", "99 A"),
            ("House (managed EV)", "±57 A"),
            ("Total", "±255 A"),
            ("Select", "400 A (320 A continuous)\nmeter stack"),
        ]), ("Notes", [
            "Preliminary and unsealed. NEC 220.84 (multifamily)\ndoes not apply to two units; each is calculated\nseparately. The electrician or engineer of record\nconfirms conductor sizes, fault current and\nvoltage drop.",
        ])]),
    ]
    text_columns(bg, cols, top=4.55, fs=6.2, lh=0.158)
    save(fig, "E-201", pdf)
