"""Plumbing, mechanical and electrical sheets, one per floor. PRELIMINARY layouts on the architectural background."""
import math

import numpy as np

from common import *  # noqa: F401,F403
from levels import *  # noqa: F401,F403
from struct_sheets import text_columns

CW, HW, SAN, VENT, STORM = "#1f5fa8", "#c0392b", "#2e7d32", "#2e7d32", "#0e8f9c"
PWR, LIT, OR, EX = "#6a1b9a", "#b9770e", "#d35400", "#6a1b9a"
S1 = (13.3, 18.2)             # stack 1: kitchen + bath 1, in the living / bath wet wall
S2 = (29.6, 23.7)             # stack 2: bath 2, bath 3, laundry
S1_DROP = (10.9, 18.2)        # where stack 1 comes down on the garage west wall
S2_DROP = (38.3, 23.0)        # where stack 2 comes down in the utility closet
WR = (19.7, 31.0)             # water risers, inside the rear-wing partition (heated space)
PADS = [(34.6, "HP-A"), (37.2, "HP-B")]
LVL = {"A": ("Unit A", "main level", EL_MAIN), "B": ("Unit B", "upper level", EL_UP)}


def tag(ax, x, y, s, color=INK, size=4.4, box=True, weight="bold", **kw):
    txt(ax, x, y, s, size=size, color=color, weight=weight, box=box, z=12, **kw)


def pipe(ax, pts, color, lw=1.2, ls="-"):
    line(ax, pts, color=color, lw=lw, ls=ls, z=10)


def dot(ax, x, y, color, r=0.28, fill=True):
    ax.add_patch(plt.Circle((x, y), r, fc=color if fill else PAPER, ec=color, lw=1.0, zorder=11))


def cleanout(ax, x, y, color=SAN, lab=True, dx=0.0, dy=-1.1):
    rect(ax, x - 0.42, y - 0.42, x + 0.42, y + 0.42, fc=PAPER, ec=color, lw=1.1, z=12)
    txt(ax, x, y, "CO", size=3.2, color=color, weight="bold", z=13)


def keynote(ax, x, y, n, color=PWR):
    pts = [(x + 0.62 * math.cos(math.radians(a)), y + 0.62 * math.sin(math.radians(a))) for a in range(0, 360, 60)]
    poly(ax, pts, fc=PAPER, ec=color, lw=1.0, z=13)
    txt(ax, x, y, str(n), size=4.4, color=color, weight="bold", z=14)


def garage_bg(ax):
    poly(ax, APRON, fc="#f1f3f5", ec=BG_EDGE, lw=0.5, z=2)
    rect(ax, 37.5, 3, 45, BY0, fc="#f6f7f8", ec=BG_EDGE, lw=0.4, z=2)
    rect(ax, *TRASH[:2], *TRASH[2:], fc="#f3f4f6", ec=BG_EDGE, lw=0.4, z=2)
    rect(ax, BX0, BY1, WX1, WY1, fc="#f7f3ec", ec=BG_EDGE, lw=0.4, z=1, ls="--")
    lower_plan(ax, "bg", cars=False)


# ---------------------------------------------------------------------------- plumbing
def sheet_p101(pdf):
    notes = [
        ("Garage level plumbing", [
            "The garage is open and unheated, so",
            "no water pipe runs through it.",
            "Water: two meters in the utility's pits",
            "at the street. Two 1 in. lines run",
            "buried 42 in. deep along the west side",
            "yard and come up through the rear",
            "wing slab, straight into heated space.",
        ]),
        ("Sanitary", [
            "Stacks S-1 and S-2 come down from",
            "the flats. Each offsets inside the",
            "insulated, fire-rated ceiling, drops on",
            "a wall and joins a 4 in. building drain",
            "under the slab at 1/4 in. per ft.",
            "Drains hold no standing water here",
            "(no traps at this level).",
        ]),
        ("Cleanouts (CO)", [
            "At the base of each stack, at each",
            "turn under the slab (flush floor",
            "cleanouts), and a two-way cleanout on",
            "the lot before the lot line. Every part",
            "of the main drain can be rodded.",
        ]),
        ("Storm: gravity, no pump", [
            "Trench drain across the open front,",
            "the French drain (S-101) and the roof",
            "leaders run by gravity to one outlet at",
            "the street edge. City Engineer approval.",
            "Sewer depth in Baird St is unknown:",
            "ask MUB for the tap card.",
        ]),
    ]
    fig, bg = new_sheet("P-101", "Plumbing: garage level", "3/16\" = 1'-0\"", notes)
    ax = plan_frame(fig, "Garage level plumbing plan", "Water blue · sanitary green · storm teal · CO = cleanout · preliminary")
    garage_bg(ax)
    # water: meter pits at the street, buried along the west side yard, up through the wing
    for x in (3.4, 5.2):
        rect(ax, x - 0.6, -3.6, x + 0.6, -2.4, fc=PAPER, ec=CW, lw=1.0, z=11)
    tag(ax, -1.4, -5.2, "2 WATER METER PITS\n(MUB), A + B", CW)
    pipe(ax, [(4.3, PAVE_N - 2.5), (4.3, -3.6)], CW, 1.6)
    pipe(ax, [(3.4, -2.4), (5.6, 2.0), (6.6, 31.4), (10.0, 31.4), (WR[0], WR[1])], CW, 1.4, (0, (6, 2)))
    pipe(ax, [(5.2, -2.4), (6.2, 1.6), (7.2, 31.0)], CW, 1.4, (0, (6, 2)))
    tag(ax, 2.2, 20.0, "TWO 1\" LINES\nBURIED 42\" MIN.\n(below frost)", CW, size=4.2)
    dot(ax, WR[0], WR[1], CW, 0.4)
    tag(ax, 19.7, 33.6, "RISERS W-A + W-B UP INTO UNIT A (heated space)", CW, size=4.2)
    tag(ax, 19, 14.0, "NO WATER PIPING IN THE OPEN GARAGE", CW, size=5.0, weight="normal")
    # stack 2 -> utility closet
    pipe(ax, [S2, (S2[0], 23.0), S2_DROP], SAN, 1.6, (0, (5, 2)))
    dot(ax, *S2, SAN, 0.38, fill=False)
    tag(ax, 28.4, 25.4, "S-2  3\" FROM\nFLATS ABOVE", SAN, size=4.2)
    tag(ax, 33.6, 21.2, "3\" OFFSET INSIDE THE\nINSULATED RATED CEILING", SAN, size=4.0)
    dot(ax, *S2_DROP, SAN, 0.38)
    cleanout(ax, 39.6, 23.0)
    # stack 1 -> west wall
    pipe(ax, [S1, S1_DROP], SAN, 1.6, (0, (5, 2)))
    dot(ax, *S1, SAN, 0.38, fill=False)
    dot(ax, *S1_DROP, SAN, 0.38)
    cleanout(ax, 12.0, 19.6)
    tag(ax, 16.6, 20.0, "S-1  3\" FROM FLATS ABOVE,\ndrops on west wall (boxed)", SAN, size=4.2)
    pipe(ax, [S1_DROP, (10.9, 11.4), (12.0, 10.4), (38.3, 10.4)], SAN, 2.0)
    cleanout(ax, 12.0, 10.4)
    cleanout(ax, 38.3, 10.4)
    tag(ax, 24, 11.9, "4\" BRANCH UNDER SLAB, 1/4\"/FT", SAN, size=4.2)
    pipe(ax, [S2_DROP, (38.3, 9.0), (39.6, 7.0), (39.6, PAVE_N - 2.5)], SAN, 2.2)
    tag(ax, 34.4, 16.0, "4\" BUILDING DRAIN\nUNDER SLAB", SAN, size=4.2)
    line(ax, [(36.6, 16.0), (38.2, 16.0)], lw=0.3, color=SAN)
    cleanout(ax, 39.6, 4.4)
    tag(ax, 33.6, 4.4, "TWO-WAY CO\non lot", SAN, size=4.0)
    line(ax, [(35.6, 4.4), (39.1, 4.4)], lw=0.3, color=SAN)
    tag(ax, 35.2, -5.6, "4\" SEWER TO\nMUB MAIN", SAN, size=4.2)
    line(ax, [(37.2, -5.6), (39.5, -5.6)], lw=0.3, color=SAN)
    # storm
    pipe(ax, [(DOOR_A[0], 7.55), (DOOR_B[1], 7.55)], STORM, 2.0)
    tag(ax, 20, 5.9, "TRENCH DRAIN, TRAFFIC-RATED GRATE", STORM, size=4.2)
    pipe(ax, [(DOOR_B[1], 7.55), (40.2, 4.4)], STORM, 1.2)
    fd = [(BX0 - 1.6, 9.0), (BX0 - 1.6, BY1 + 1.6), (BX1 + 1.6, BY1 + 1.6), (BX1 + 1.6, 3.4), (43.6, 0.2), (43.6, PAVE_N)]
    pipe(ax, fd, STORM, 1.3, (0, (6, 2, 1, 2)))
    pipe(ax, [(40.2, 4.4), (43.6, 1.2)], STORM, 1.2)
    poly(ax, [(43.0, PAVE_N), (44.2, PAVE_N), (43.6, PAVE_N - 1.2)], fc=STORM, ec=STORM, z=11)
    tag(ax, 49.2, -5.0, "ONE GRAVITY\nOUTLET AT THE\nSTREET EDGE", STORM, size=4.2)
    tag(ax, 50.0, 22.0, "FRENCH\nDRAIN\n(S-101)", STORM, size=4.0)
    for (x, y) in ((BX0 - 1.6, 9.0), (BX0 - 1.6, BY1 + 1.6), (BX1 + 1.6, BY1 + 1.6), (BX1 + 1.6, 9.0)):
        cleanout(ax, x, y, STORM)
    for (x, y) in ((9.0, 7.4), (45.5, 30.5), (9.0, 35.5), (29.0, 35.5)):
        ax.add_patch(plt.Circle((x, y), 0.36, fc=STORM, ec=STORM, zorder=12))
    tag(ax, 36.5, 36.6, "● ROOF LEADERS, PIPED TO THE DRAIN (not onto neighbours)", STORM, size=4.0)
    tag(ax, 19, 26.2, "NO SUMP PUMP · NO FLOOR FIXTURES AT THIS LEVEL", GREY, size=4.4, weight="normal")
    save(fig, "P-101", pdf)


def unit_plumbing(ax, unit):
    for (sx, sy), lab, lx, ly in ((S1, "S-1 3\"", 13.3, 16.9), (S2, "S-2 3\"", 31.2, 24.6)):
        dot(ax, sx, sy, SAN, 0.42, fill=False)
        tag(ax, lx, ly, lab, SAN, size=4.4)
    for p in ([(11.0, 11.65), (10.4, 11.65), (10.4, 18.2), S1], [(11.0, 9.7), (10.4, 9.7), (10.4, 11.65)],      # kitchen
              [(11.35, 19.2), (11.35, 18.2)], [(14.1, 19.6), (14.1, 18.2)], [(16.5, 19.2), (16.5, 18.2), S1],   # bath 1
              [(28.05, 22.9), (28.05, 23.7), S2], [(25.3, 22.4), (25.3, 23.7), (28.05, 23.7)],                   # bath 2
              [(23.0, 19.3), (24.3, 19.9), (24.3, 23.7), (25.3, 23.7)],
              [(31.65, 21.2), (31.65, 21.7), (29.6, 21.7), S2],                                                   # washer
              [(28.95, 28.2), (28.95, 24.2), S2], [(29.3, 25.3), (28.95, 25.3)], [(31.6, 22.7), (31.6, 21.7)]):  # bath 3
        pipe(ax, p, SAN, 1.3)
    for p in ([(10.4, 11.65), (10.15, 12.6)], [(16.5, 18.2), (17.2, 18.2)], [(24.3, 19.9), (24.9, 19.5)], [(31.65, 21.7), (32.6, 21.7)]):
        pipe(ax, p, VENT, 0.9, (0, (3, 2)))
    cleanout(ax, 10.4, 17.2)
    cleanout(ax, 28.6, 22.0)
    # water: risers in the wing partition, mains in heated space, water heater by the entry
    dot(ax, WR[0], WR[1], CW, 0.32)
    tag(ax, 16.6, 32.6, "COLD WATER\nRISER + SHUTOFF", CW, size=4.0)
    cold = [[WR, (19.7, 23.7)], [(19.7, 23.7), (19.7, 18.2), (13.9, 18.2)], [(13.9, 18.2), (13.9, 19.0)], [(11.9, 18.2), (11.9, 19.0)], [(16.0, 18.2), (16.0, 19.0)],
            [(13.9, 18.2), (12.4, 18.2), (12.4, 11.9), (11.7, 11.9)], [(12.4, 16.6), (11.9, 16.6)],
            [(19.7, 23.7), (33.7, 23.7), (33.7, 17.4), (35.7, 17.4), (35.7, 15.0)],
            [(25.9, 23.7), (25.9, 23.0)], [(28.5, 23.7), (28.5, 23.0)], [(23.4, 23.7), (23.4, 19.9)],
            [(31.0, 23.7), (31.0, 21.3)], [(29.0, 23.7), (29.0, 24.8)], [(30.4, 23.7), (30.4, 27.2)], [(32.2, 23.7), (32.2, 23.3)]]
    for p in cold:
        pipe(ax, p, CW, 0.8)
    hot = [[(36.2, 15.0), (36.2, 17.0), (34.1, 17.0), (34.1, 23.4), (20.1, 23.4), (20.1, 18.5), (12.2, 18.5)],
           [(16.3, 18.5), (16.3, 19.0)], [(12.2, 18.5), (12.2, 19.0)], [(12.7, 18.5), (12.7, 12.2), (11.7, 12.2)], [(12.7, 10.0), (12.7, 12.2)], [(12.7, 10.0), (11.9, 10.0)],
            [(28.8, 23.4), (28.8, 23.0)], [(23.7, 23.4), (23.7, 19.9)], [(31.3, 23.4), (31.3, 21.3)], [(30.7, 23.4), (30.7, 27.2)], [(32.5, 23.4), (32.5, 23.3)]]
    for p in hot:
        pipe(ax, p, HW, 0.8, (0, (4, 2)))
    tag(ax, 35.7, 11.2, "WH 80 gal electric\npan drain to laundry", HW, size=3.8)
    for x, y, s in ((16.6, 12.2, "KS + DW 2\""), (22.2, 16.6, "BATH 1 GROUP\non the wet wall"), (25.6, 17.0, "BATH 2"), (36.4, 21.6, "WASHER BOX\n2\" STANDPIPE"),
                    (36.4, 27.6, "BATH 3")):
        tag(ax, x, y, s, SAN, size=3.9)
    line(ax, [(14.6, 12.2), (11.4, 11.9)], lw=0.3, color=SAN)
    line(ax, [(34.6, 21.6), (32.2, 21.5)], lw=0.3, color=SAN)
    tag(ax, 16.2, 15.6, "ICE-MAKER", CW, size=3.8)
    line(ax, [(14.6, 15.9), (12.0, 16.5)], lw=0.3, color=CW)
    if unit == "A":
        ax.add_patch(plt.Circle((33.0, 30.3), 0.34, fc=PAPER, ec=CW, lw=1.0, zorder=12))
        pipe(ax, [(32.2, 23.7), (33.0, 24.2), (33.0, 30.0)], CW, 0.7)
        tag(ax, 36.2, 31.6, "frost-free hose bibb", CW, size=3.8)
        tag(ax, 24, 36.9, "S-1, S-2 AND UNIT B'S WATER RISER PASS THROUGH: FIRESTOP AT THE FLOOR ABOVE", SAN, size=4.2)
    else:
        tag(ax, 24, 36.9, "S-1 AND S-2 CONTINUE UP AS 3\" VENTS THROUGH THE REAR ROOF SLOPE · NO PIPES IN THE ATTIC", VENT, size=4.2)


def unit_plumbing_sheet(pdf, number, unit):
    name, lev, el = LVL[unit]
    notes = [
        (f"{name} plumbing ({lev})", [
            "Three baths with tubs, kitchen and",
            "laundry on two stacks.",
            "S-1: kitchen sink, dishwasher, bath 1.",
            "S-2: baths 2 and 3, clothes washer.",
            "Units A and B stack exactly.",
        ]),
        ("Water, kept from freezing", [
            "This flat's own meter and 1 in. line.",
            "The riser comes up inside the rear",
            "wing partition, never through the open",
            "garage. Mains run in the heated ceiling",
            ("space between the flats." if unit == "A" else "space and interior walls, not the attic."),
            "Shutoff at the riser.",
            "Own 80 gal electric water heater in",
            "the closet by the entry, with a pan",
            "drained to the laundry standpipe.",
        ]),
        ("Drain, waste, vent", [
            "3 in. stack at each group. Tubs and",
            "lavatories 2 in. Kitchen sink and",
            "washer individually vented.",
            ("3 in. vents through the rear roof slope,\n10 ft from any window." if unit == "B" else
             "Stacks continue down to the garage\nceiling offset (see P-101)."),
            "CO = cleanout, reachable from the",
            "kitchen base cabinet and bath 2.",
        ]),
        ("Fire-stopping and noise", [
            "Listed firestop at every pipe through",
            "the 1-hour floor between the flats.",
            "Cast-iron stacks between flats.",
        ]),
    ]
    fig, bg = new_sheet(number, f"Plumbing: {name}", "3/16\" = 1'-0\"", notes)
    ax = plan_frame(fig, f"{name} plumbing plan", f"{lev.capitalize()} · EL {el:.1f} · cold blue · hot red dashed · waste green · CO = cleanout · preliminary", street=False)
    unit_plan(ax, "bg", unit)
    unit_plumbing(ax, unit)
    save(fig, number, pdf)


def sheet_p201(pdf):
    fig, bg = new_sheet("P-201", "Plumbing riser and schedules", "No scale", [
        ("Reading the riser", [
            "Schematic, not to scale. Unit B is",
            "above Unit A. Two stacks serve both",
            "flats and meet under the garage slab.",
            "CO = cleanout.",
        ]),
        ("Open items for the plumber", [
            "MUB sewer and water main locations,",
            "depths and tap fees.",
            "Whether MUB sets two meters or one",
            "with private sub-meters.",
            "Whether the city wants two sewer",
            "laterals for a two-family dwelling.",
            "Static water pressure (PRV setting).",
            "City Engineer approval of the storm",
            "outlet at the street edge.",
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
        g1 = [(4, "KS+DW"), (10, "TUB 1"), (16, "LAV 1"), (28, "WC 1")]
        g2 = [(36, "LAV 2"), (42, "TUB 2"), (48, "WC 2"), (54, "CW"), (66, "WC 3"), (71.5, "TUB/LAV 3")]
        line(ax, [(4, y - 3), (28, y - 3)], color=SAN, lw=1.8)
        line(ax, [(36, y - 3), (71.5, y - 3)], color=SAN, lw=1.8)
        for x, n in g1 + g2:
            line(ax, [(x, y - 3), (x, y + 3)], color=SAN, lw=1.2)
            rect(ax, x - 2.7, y + 3, x + 2.7, y + 6.2, fc=PAPER, ec=SAN, lw=0.8, z=6)
            txt(ax, x, y + 4.6, n, size=4.4, weight="bold", z=7)
        for xs, X in (((4, 16), X1), ((36, 54, 71.5), X2)):
            for x in xs:
                line(ax, [(x, y + 6.2), (x, y + 11)], color=VENT, lw=0.9, ls=(0, (4, 2)))
            line(ax, [(min(xs), y + 11), (X, y + 11)] if max(xs) < X else [(min(xs), y + 11), (max(xs), y + 11)], color=VENT, lw=0.9, ls=(0, (4, 2)))
        txt(ax, 11, y + 12.3, "10 DFU", size=5.0, color=SAN, weight="bold")
        txt(ax, 45, y + 12.3, "14 DFU", size=5.0, color=SAN, weight="bold")
    line(ax, [(X1, 26), (X1, 9), (48, 9)], color=SAN, lw=2.6)
    line(ax, [(X2, 26), (48, 26), (48, 9)], color=SAN, lw=2.6)
    for x, y in ((X1, 20), (48, 20), (30, 9), (48, 9)):
        rect(ax, x - 1.3, y - 1.3, x + 1.3, y + 1.3, fc=PAPER, ec=SAN, lw=1.1, z=6)
        txt(ax, x, y, "CO", size=4.4, color=SAN, weight="bold", z=7)
    txt(ax, 54, 27.6, "S-2 OFFSET IN GARAGE CEILING", size=4.8, color=SAN)
    txt(ax, 12, 23.5, "S-1 DROPS ON\nWEST WALL", size=4.8, color=SAN)
    txt(ax, 38, 6.6, "4\" UNDER SLAB", size=4.8, color=SAN)
    line(ax, [(48, 9), (70, 5)], color=SAN, lw=3.2)
    txt(ax, 60, 10.6, "4\" BUILDING DRAIN\n1/4\"/FT · 48 DFU", size=4.8, color=SAN)
    rect(ax, 64.7, 4.4, 67.3, 7.0, fc=PAPER, ec=SAN, lw=1.1, z=6)
    txt(ax, 66, 5.7, "CO", size=4.4, color=SAN, weight="bold", z=7)
    txt(ax, 66, 2.6, "two-way, on lot", size=4.6, color=SAN)
    txt(ax, 75, 2.6, "TO SEWER", size=5.0, color=SAN, ha="right")
    L = 8.55
    cols = [(L, 4.8, [
        ("Fixture schedule (per flat)", [
            ("Water closets (3)", "1.28 gpf, 3 in. waste · 3 DFU each"),
            ("Lavatories (3)", "1-1/4 in. trap · 1 DFU each"),
            ("Tub / showers (3)", "5 ft fiberglass, 2 in. waste,\npressure-balance valve · 2 DFU each"),
            ("Kitchen sink + DW", "2 in. waste · 2 + 2 DFU"),
            ("Clothes washer", "2 in. standpipe 18 to 42 in. · 2 DFU"),
            ("Total per flat", "±24 DFU waste, ±17 WSFU water"),
        ]),
        ("Water heaters", [
            ("One per flat", "80 gal electric, 4.5 kW, 240 V, 30 A, in\nthe closet by that flat's entry"),
            ("Why 80 gal", "Three tubs per flat; 50 gal runs short"),
        ]),
        ("Pipe sizes (preliminary)", [
            ("Water, each flat", "1 in. from its meter; 3/4 in. cold and\nhot mains; 1/2 in. branches"),
            ("Soil stacks", "3 in. each (S-1 20 DFU, S-2 28 DFU)"),
            ("Building drain", "4 in. at 1/4 in. per ft"),
            ("Vents through roof", "3 in. at each stack, rear slope"),
            ("Storm outlet", "4 in., gravity, to the street edge"),
        ]),
        ("Freeze protection", [
            "Meters in pits at the street. Lines buried 42 in. or\ndeeper. Risers come up inside the rear wing. Nothing\nwet in the open garage or the attic.",
        ]),
        ("Materials", [
            ("DWV", "PVC schedule 40; cast-iron stacks\nbetween flats for noise"),
            ("Water", "PEX-A with copper stub-outs"),
        ]),
    ])]
    text_columns(bg, cols, top=SHEET_H - MARGIN - 0.75, fs=6.3)
    save(fig, "P-201", pdf)


# ---------------------------------------------------------------------------- mechanical
def sheet_m101(pdf):
    notes = [
        ("Garage level", [
            "Open to the street on one side: it",
            "ventilates naturally and is unheated.",
            "No mechanical equipment, no heaters,",
            "no exhaust fan, no sump.",
        ]),
        ("What keeps it simple", [
            "Water heaters, washers and dryers are",
            "inside the flats. There is no storage",
            "room to condition and no mechanical",
            "room to heat.",
            "The bike / utility closet is unheated",
            "and holds only the S-2 drain drop and",
            "its cleanout.",
        ]),
        ("Envelope above", [
            "The Unit A floor is the thermal line:",
            "R-30 in the trusses with an air barrier,",
            "5/8 in. Type X below. Drain pipes that",
            "cross the garage run above that",
            "insulation.",
        ]),
        ("Outdoor units", [
            "HP-A and HP-B sit on raised pads in",
            "the rear yard at Unit A floor level,",
            "shown dashed: 2 ft+ from a side lot",
            "line, not in the front yard (1337.05(D)).",
            "Quiet-rated models, kept clear of the",
            "bedroom 3 windows.",
        ]),
    ]
    fig, bg = new_sheet("M-101", "Mechanical: garage level", "3/16\" = 1'-0\"", notes)
    ax = plan_frame(fig, "Garage level mechanical plan", "Naturally ventilated open garage · no equipment at this level · preliminary")
    garage_bg(ax)
    for x, lab in PADS:
        rect(ax, x - 1.2, 31.2, x + 1.2, 33.4, fc=PAPER, ec=OR, lw=1.0, z=11, ls="--")
        tag(ax, x, 32.3, lab, OR, size=4.0, box=False)
    tag(ax, 36, 35.2, "HEAT-PUMP OUTDOOR UNITS ON PADS ABOVE (rear yard, ±EL 923 to 925)", OR, size=4.2)
    for x in (15, 24, 33):
        ax.annotate("", xy=(x, 5.2), xytext=(x, 12.0), arrowprops=dict(arrowstyle="<|-|>", lw=0.9, color=EX), zorder=11)
    tag(ax, 24, 14.2, "NATURAL VENTILATION THROUGH THE OPEN FRONT", EX, size=5.0)
    tag(ax, 24, 21.0, "UNHEATED · NO EQUIPMENT · NO WATER PIPING", GREY, size=5.0, weight="normal")
    tag(ax, 19, 32.5, "UNEXCAVATED", GREY, size=4.4, weight="normal")
    save(fig, "M-101", pdf)


def term(ax, x, y, d):
    pts = [(x, y - 0.5), (x, y + 0.5), (x - 0.8, y)] if d == "W" else [(x - 0.5, y), (x + 0.5, y), (x, y + 0.8)]
    poly(ax, pts, fc=EX, ec=EX, z=12)


def unit_hvac(ax, unit):
    heads = [((25.5, 17.2, 28.5, 18.0), "AH-1\n12k", (27.0, 15.6)), ((18.7, 29.5, 19.5, 32.5), "AH-2\n6k", (16.6, 31.0)),
             ((19.9, 29.5, 20.7, 32.5), "AH-3\n6k", (22.8, 31.0)), ((38.0, 22.2, 41.0, 23.0), "AH-4\n6k", (39.5, 24.7))]
    for (x0, y0, x1, y1), lab, (tx, ty) in heads:
        rect(ax, x0, y0, x1, y1, fc=OR, ec=OR, z=11)
        tag(ax, tx, ty, lab, OR, size=4.2)
    for x, lab in PADS:
        rect(ax, x - 1.2, 31.2, x + 1.2, 33.4, fc=PAPER, ec=OR, lw=1.2 if lab.endswith(unit) else 0.6, z=11, ls="-" if lab.endswith(unit) else "--")
        tag(ax, x, 32.3, lab, OR, size=4.0, box=False)
    hp = PADS[0][0] if unit == "A" else PADS[1][0]
    tag(ax, 39.6, 35.2, f"HP-{unit} OUTDOOR UNIT ON A RAISED PAD, REAR YARD" + (" (lines rise up the rear wall)" if unit == "B" else ""), OR, size=4.2)
    for p in ([(27.0, 18.0), (27.0, 18.2), (33.7, 18.2), (33.7, 29.8), (hp, 29.8), (hp, 31.2)],
              [(19.1, 32.5), (19.1, 34.2), (28.2, 34.2), (28.2, 29.8), (33.7, 29.8)], [(20.3, 32.5), (20.3, 34.2)], [(39.5, 23.0), (39.5, 29.8), (hp, 29.8)]):
        line(ax, p, color=OR, lw=0.8, ls=(0, (2, 2)), z=10)
    tag(ax, 24.2, 35.6, "refrigerant line sets in wall / ceiling space", OR, size=3.8, weight="normal")
    fans = [((14.6, 21.6), [(14.0, 21.6), (9.4, 21.6)], (9.2, 21.6, "W")), ((24.6, 21.4), [(25.2, 22.0), (25.2, 22.9), (29.0, 22.9), (29.0, 30.2)], (29.0, 30.3, "N")),
            ((31.2, 26.0), [(31.2, 26.6), (31.2, 30.2)], (31.2, 30.3, "N"))]
    for (x, y), duct, (tx, ty, d) in fans:
        rect(ax, x - 0.6, y - 0.6, x + 0.6, y + 0.6, fc=PAPER, ec=EX, lw=1.1, z=11)
        line(ax, [(x - 0.6, y - 0.6), (x + 0.6, y + 0.6)], color=EX, lw=0.7, z=12)
        line(ax, duct, color=EX, lw=1.3, z=10)
        term(ax, tx, ty, d)
    tag(ax, 16.2, 20.4, "EF-1", EX, size=3.8)
    tag(ax, 24.6, 20.2, "EF-2", EX, size=3.8)
    tag(ax, 32.6, 25.0, "EF-3", EX, size=3.8)
    rect(ax, 10.05, 12.9, 12.2, 15.3, fc="none", ec=EX, lw=1.2, z=11)
    line(ax, [(10.05, 14.1), (9.4, 14.1)], color=EX, lw=1.3, z=10)
    term(ax, 9.2, 14.1, "W")
    tag(ax, 6.0, 14.1, "RH-1 6\"", EX, size=3.8)
    tag(ax, 6.0, 21.6, "EF-1 4\"", EX, size=3.8)
    line(ax, [(32.6, 21.3), (32.6, 30.2)], color=EX, lw=1.3, z=10)
    term(ax, 32.6, 30.3, "N")
    tag(ax, 30.8, 37.0, "EF-2, EF-3 AND DV-1 (dryer 4\") TERMINATE AT THE REAR WALL, 3 FT+ FROM OPENINGS", EX, size=3.8)
    tag(ax, 22, 12.2, "T", OR, size=5.0)
    tag(ax, 28, 9.4, "3/4\" door undercuts return air from each bedroom", GREY, size=4.0, weight="normal")


def unit_hvac_sheet(pdf, number, unit):
    name, lev, el = LVL[unit]
    notes = [
        (f"{name} heating and cooling", [
            "One cold-climate ductless heat pump",
            f"(HP-{unit}), about 30,000 Btu/h, on this",
            "flat's own meter, with four wall heads:",
            "living 12k and one 6k head in each",
            "bedroom, each with its own control.",
            "The outdoor unit has to be outdoors",
            "and is weatherproof. Everything else",
            "is inside the flat.",
            "All-electric: no gas, no flues.",
        ]),
        ("Ventilation (IRC M1505)", [
            "A bath fan in each of the three baths,",
            "50 cfm each. EF-2 runs continuously at",
            "30 cfm for whole-flat ventilation.",
            "Range hood RH-1: 150 cfm min., straight",
            "out the west wall.",
            "Dryer DV-1: 4 in. rigid duct, about 9 ft,",
            "to the rear wall.",
            "Terminations 3 ft from lot lines and",
            "from windows and doors.",
        ]),
        ("Coordination", [
            "EF-2 and the dryer duct cross above",
            "bath 3 in the ceiling space.",
            ("Unit B line sets rise up the rear wall\nfrom the pad in a covered chase." if unit == "B" else
             "Unit A line sets enter through the\nrear wall just above floor level."),
            "Condensate from each head to the",
            "nearest bath or laundry drain.",
            "Water heater is electric: no vent.",
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


def e_legend(ax, x, y, auto=False):
    items = [("R", "Duplex receptacle, 20 A, tamper-resistant"), ("G", "GFCI-protected receptacle"), ("W", "Weatherproof GFCI receptacle"),
             ("2", "240 V outlet or equipment connection"), ("L", "Ceiling or wall light"), ("A", "Smoke (SD) / smoke + CO (SC) alarm")]
    if auto:
        items = [("G", "GFCI-protected receptacle"), ("L", "Light"), ("AL", "Automatic light: motion sensor + photocell"), ("K", "Keynote, see list at right"),
                 ("A", "Smoke alarm")]
    for i, (k, s) in enumerate(items):
        yy = y - i * 1.25
        if k == "L":
            light(ax, x, yy)
        elif k == "AL":
            auto_light(ax, x, yy)
        elif k == "K":
            keynote(ax, x, yy, 1)
        elif k == "A":
            alarm(ax, x, yy)
        else:
            recept(ax, x, yy, k)
        txt(ax, x + 1.2, yy, s, size=4.2, ha="left", box=True)


def auto_light(ax, x, y, strip=False):
    """Automatic light: fixture with a filled motion-sensor triangle."""
    if strip:
        rect(ax, x - 2, y - 0.25, x + 2, y + 0.25, fc=PAPER, ec=LIT, lw=0.9, z=11)
        poly(ax, [(x + 2.1, y - 0.45), (x + 2.9, y - 0.45), (x + 2.5, y + 0.45)], fc=LIT, ec=LIT, z=12)
    else:
        light(ax, x, y)
        poly(ax, [(x + 0.5, y - 0.45), (x + 1.3, y - 0.45), (x + 0.9, y + 0.45)], fc=LIT, ec=LIT, z=12)


def sheet_e101(pdf):
    notes = [
        ("Two meters only", [
            "One meter and panel per flat (PA, PB).",
            "No house meter or house panel. This",
            "level runs on one circuit, CL-1, from",
            "Unit A's panel.",
        ]),
        ("Keynotes", [
            "1  AUTOMATIC GARAGE LIGHT. LED strip,",
            "    on by motion sensor and only after",
            "    dark (photocell), off after 10 min.",
            "    Circuit CL-1 from panel PA.",
            "2  AUTOMATIC EXTERIOR LIGHT at the",
            "    opening and entry. Full cutoff, aimed",
            "    down (1337.07(F)). Circuit CL-1.",
            "3  LOBBY AND STAIR LIGHTS. On CL-1,",
            "    motion sensor, with a battery unit so",
            "    the stair stays lit in an outage.",
            "4  GARAGE RECEPTACLE, one per stall",
            "    (NEC 210.52(G)), GFCI, on CL-1.",
            "5  EMPTY 1 in. CONDUIT for a future car",
            "    charger: stall 1 to PA, stall 2 to PB.",
            "6  EMPTY CONDUIT + BACKING at the",
            "    opening for a future grille operator.",
        ]),
        ("Lease note", [
            "CL-1 is common lighting on Unit A's",
            "meter (about 250 W when on). Disclose",
            "it in Unit A's lease or credit the rent.",
            "No cameras, sump pump, door",
            "operators or heat cable are included.",
        ]),
    ]
    fig, bg = new_sheet("E-101", "Electrical: garage level", "3/16\" = 1'-0\"", notes)
    ax = plan_frame(fig, "Garage level power and lighting plan", "All fed from Unit A panel PA, circuit CL-1 · numbers are keynotes · preliminary")
    garage_bg(ax)
    for x, y in ((15, 13.5), (15, 23.5), (24, 13.5), (24, 23.5), (32.5, 13.5), (32.5, 23.5)):
        auto_light(ax, x, y, strip=True)
    keynote(ax, 19.6, 13.5, 1)
    keynote(ax, 19.6, 23.5, 1)
    for x, y in ((11.0, 7.3), (28.7, 7.3), (37.0, 7.3), (42.4, 7.2)):
        auto_light(ax, x, y)
    keynote(ax, 31.4, 6.2, 2)
    for x, y in ((40.8, 10.6), (40.8, 20.0), (40.8, 25.6)):
        auto_light(ax, x, y)
    keynote(ax, 43.2, 16.4, 3)
    for x, y in ((10.9, 20.0), (24.0, 28.7), (36.9, 16.0)):
        recept(ax, x, y, "G")
    keynote(ax, 12.6, 20.0, 4)
    keynote(ax, 25.8, 27.6, 4)
    for x, y in ((10.9, 26.0), (22.0, 28.7)):
        rect(ax, x - 0.4, y - 0.4, x + 0.4, y + 0.4, fc=PAPER, ec=PWR, lw=0.9, z=11, ls="--")
    keynote(ax, 12.6, 26.0, 5)
    keynote(ax, 20.4, 27.6, 5)
    rect(ax, 27.0, 8.9, 30.3, 9.5, fc=PAPER, ec=PWR, lw=0.9, z=11, ls="--")
    keynote(ax, 31.4, 9.8, 6)
    rect(ax, 45.0, 10.5, 45.7, 14.5, fc=PWR, ec=PWR, z=11)
    tag(ax, 49.0, 12.5, "METER STACK\n2 METERS\n(A, B)", PWR, size=4.2)
    line(ax, [(45.35, 14.5), (45.35, 16.0), (44.4, 16.0)], color=PWR, lw=1.2, ls=(0, (4, 2)), z=10)
    tag(ax, 49.0, 18.0, "FEEDERS UP IN\nTHE SHAFT WALL\nTO PA AND PB", PWR, size=4.0, weight="normal")
    line(ax, [(45.35, 10.5), (45.35, 2.5)], color=PWR, lw=1.4, z=10)
    tag(ax, 49.4, 5.6, "SERVICE from\nMon Power:\noverhead or\nunderground\nTBC", PWR, size=4.0, weight="normal")
    line(ax, [(44.4, 16.0), (41.6, 16.0), (41.6, 11.2), (37.2, 11.2), (37.2, 9.2), (11.4, 9.2)], color=PWR, lw=0.8, ls=(0, (2, 2)), z=9)
    tag(ax, 20, 10.6, "CIRCUIT CL-1 FROM PANEL PA (Unit A, above)", PWR, size=4.2)
    alarm(ax, 42.8, 12.6, "SD")
    e_legend(ax, -3.6, 31.5, auto=True)
    save(fig, "E-101", pdf)


def unit_power(ax, unit):
    R = [(19.5, 8.8), (31.0, 8.8), (35.5, 8.8), (27.0, 17.8), (30.0, 17.8), (36.7, 16.6), (33.8, 13.9), (10.3, 16.8),
         (10.3, 26.8), (10.3, 33.2), (19.2, 28.6), (19.2, 33.6), (17.4, 34.2),
         (20.2, 28.6), (20.2, 33.6), (27.7, 27.4), (27.7, 32.8),
         (44.2, 23.2), (44.2, 28.9), (35.6, 29.2), (36.6, 22.6), (30.3, 20.0)]
    for x, y in R:
        recept(ax, x, y, "R")
    for x, y in ((10.3, 10.0), (10.3, 12.4), (15.8, 10.2), (17.3, 20.6), (22.1, 20.6), (33.2, 22.8)):
        recept(ax, x, y, "G")
    for x, y in ((10.3, 14.1), (33.0, 20.0), (35.7, 15.0)):
        recept(ax, x, y, "2")
    for x, y in ((20, 7.7), (32, 7.7)):
        recept(ax, x, y, "W")
    tag(ax, 13.6, 14.1, "RANGE 50A", PWR, size=3.6)
    tag(ax, 31.6, 16.8, "DRYER 30A", PWR, size=3.6)
    tag(ax, 35.7, 16.4, "WH 30A", PWR, size=3.6)
    for x, y in ((22, 13.4), (31, 13.4), (12.9, 12.4), (15.85, 11.4), (15.85, 14.0), (14.4, 30.4), (24.0, 30.6), (38.2, 26.4),
                 (19.7, 21.0), (19.7, 25.4), (35.4, 20.4), (14.6, 21.4), (25.0, 21.4), (31.0, 25.6), (16, 6), (28, 6)):
        light(ax, x, y)
    alarm(ax, 16.8, 31.8, "SD")
    alarm(ax, 25.6, 32.2, "SD")
    alarm(ax, 36.4, 24.6, "SD")
    alarm(ax, 28.0, 15.6, "SC")
    panel(ax, 22.0, 17.6, 23.8, 18.0, f"P{unit}", 22.9, 16.4)
    for x, y in ((36.3, 12.0), (18.6, 19.2), (34.4, 19.2), (18.4, 25.4), (21.0, 25.4), (35.0, 22.8)):
        txt(ax, x, y, "S", size=4.2, color=LIT, weight="bold", z=12)
    for x, y, s in ((27.0, 16.6, "AH-1"), (17.9, 31.0, "AH-2"), (21.6, 31.0, "AH-3"), (39.5, 23.9, "AH-4")):
        tag(ax, x, y, s, PWR, size=3.6)
    if unit == "A":
        keynote(ax, 25.6, 17.0, 1)
    e_legend(ax, -3.6, 31.5)


def unit_power_sheet(pdf, number, unit):
    name, lev, el = LVL[unit]
    notes = [
        (f"{name} power ({lev})", [
            f"Its own meter. Panel P{unit}: 125 A, 30",
            "spaces, on the living-room wall with",
            "30 x 36 in. clear in front, in the shared",
            "room so every occupant can reach it.",
            "It feeds this flat's heat pump, 80 gal",
            "water heater, range, dryer and washer.",
        ]),
        ("Rooms", [
            "Receptacles so no wall point is more",
            "than 6 ft from one (NEC 210.52).",
            "Kitchen: two 20 A small-appliance",
            "circuits, GFCI; island receptacle;",
            "dedicated range, dishwasher,",
            "microwave/hood, refrigerator.",
            "Each bath: its own 20 A GFCI circuit.",
            "AFCI on all 120 V living-area circuits.",
        ]),
        ("Alarms (IRC R314, R315)", [
            "Smoke alarm in each bedroom and one",
            "smoke + CO alarm in the living room.",
            "Hard-wired, battery backup,",
            "interconnected.",
        ]),
    ] + ([("Keynote", [
        "1  Circuit CL-1 leaves this panel for the",
        "    garage, stair and exterior lights and",
        "    the garage receptacles (see E-101).",
        "    They are automatic: motion sensor",
        "    plus photocell.",
    ])] if unit == "A" else [("Common lighting", [
        "Garage, stair and exterior lights are on",
        "Unit A's panel, not this one (E-101).",
    ])])
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
            "Two meters, one per flat. No house",
            "meter. Calculated demand is about",
            "208 A for the two flats together.",
            "Confirm the meter equipment and",
            "service size with Mon Power.",
        ]),
        ("Grounding", [
            "Concrete-encased electrode: 20 ft of",
            "#4 bar in the footing, stubbed up at",
            "the service (tell the concrete crew).",
            "Bond the metal water lines and the",
            "steel frame.",
        ]),
        ("To finalize", [
            "Overhead vs underground lateral.",
            "Meter location: Mon Power may want",
            "it at the front. The east side yard is",
            "5 ft wide with 3 ft clear required.",
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
    txt(ax, 25, 41.6, "service lateral", size=4.8)
    box(30, 32, 22, 16, "METER STACK", "2 meters, 125 A main each\noutdoor, NEMA 3R")
    feeds = [(44, 66, "PA · UNIT A", ["Range 50A", "Dryer 30A", "Water heater 30A", "Heat pump 35A", "DW, micro, ref.", "2 kitchen SA", "3 bath circuits", "Laundry, lights, recept.", "CL-1 common lighting"]),
             (36, 94, "PB · UNIT B", ["Range 50A", "Dryer 30A", "Water heater 30A", "Heat pump 35A", "DW, micro, ref.", "2 kitchen SA", "3 bath circuits", "Laundry, lights, recept."])]
    for y, x, name, loads in feeds:
        line(ax, [(52, y), (62, y)], color=PWR, lw=1.6)
        rect(ax, 55, y - 1.3, 59, y + 1.3, fc=PAPER, ec=PWR, lw=1.0, z=6)
        txt(ax, 57, y + 2.6, "125 A", size=4.8, weight="bold")
        line(ax, [(62, y), (x + 10, y), (x + 10, 28)], color=PWR, lw=1.6)
        box(x, 18, 20, 10, name, "125 A MLO, 30 sp\n#1 AL feeder")
        for j, s in enumerate(loads):
            txt(ax, x + 1, 15.6 - j * 1.7, "· " + s, size=4.8, ha="left")
    line(ax, [(41, 32), (41, 24), (36, 24)], color="#2e7d32", lw=1.2)
    txt(ax, 21, 24, "GROUNDING ELECTRODE\n(footing rebar) + bonds", size=4.8, color="#2e7d32")
    L = MARGIN + 0.45
    cols = [
        (L, 4.0, [("Load summary, each flat (NEC 220.82 optional method)", [
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
        (L + 4.42, 4.0, [("Common lighting on Unit A (circuit CL-1)", [
            ("Garage LED strips (6)", "240 VA"),
            ("Stair, lobby, exterior", "120 VA"),
            ("Garage receptacles", "540 VA allowance"),
            ("Added to Unit A", "±900 VA, about 2 A of demand"),
            ("Unit A demand", "±105 A  →  125 A panel"),
            ("Typical use", "Lights run only on motion after\ndark: a few dollars a month"),
        ])]),
        (L + 8.84, 4.0, [("Service size", [
            ("Unit A", "±105 A"),
            ("Unit B", "103 A"),
            ("Total", "±208 A"),
            ("Select", "Two-gang meter-main, 125 A\neach; lateral sized by utility"),
        ]), ("Notes", [
            "Preliminary and unsealed. Each flat is calculated\nseparately. The electrician or engineer of record\nconfirms conductor sizes, fault current and\nvoltage drop.",
        ])]),
    ]
    text_columns(bg, cols, top=4.55, fs=6.2, lh=0.158)
    save(fig, "E-201", pdf)
