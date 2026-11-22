"""Structural sheets S-001, S-101..S-103, S-301. PRELIMINARY member sizes for the engineer of record to verify."""
import math

import numpy as np
from shapely.geometry import Polygon

from common import *  # noqa: F401,F403
from levels import *  # noqa: F401,F403

STEEL = "#1f5fa8"
FRAME_Y = 8.33
COLS = [10.9, 28.15, 37.3, 44.5]


def text_columns(bg, cols, top=None, fs=6.5, lh=0.165):
    """cols: list of (x_in, width_in, [(heading, [lines...]), ...])."""
    top = (SHEET_H - MARGIN - 0.55) if top is None else top
    for x, w, blocks in cols:
        y = top
        for head, lines in blocks:
            bg.text(x, y, head.upper(), fontsize=8.0, fontweight="bold", va="top", color=INK)
            bg.plot([x, x + w], [y - 0.19, y - 0.19], color=INK, lw=0.6)
            y -= 0.31
            for ln in lines:
                if isinstance(ln, tuple):
                    bg.text(x, y, ln[0], fontsize=fs, va="top", color=GREY)
                    bg.text(x + w * 0.42, y, ln[1], fontsize=fs, va="top", color=INK, linespacing=1.25)
                    y -= lh * (ln[1].count("\n") + 1) + 0.03
                else:
                    bg.text(x, y, ln, fontsize=fs, va="top", color=INK, linespacing=1.25)
                    y -= lh * (ln.count("\n") + 1) + 0.035
            y -= 0.2


def sheet_s001(pdf):
    fig, bg = new_sheet("S-001", "Structural notes and criteria", "No scale", [
        ("Read this first", [
            "Every size on the S sheets is a",
            "PRELIMINARY assumption so the",
            "engineer has a model to react to.",
            "Nothing here has been calculated to",
            "code by a licensed engineer.",
        ]),
        ("Engineer needs first", [
            "1. Boundary + topographic survey.",
            "2. Geotechnical report: bearing,",
            "    lateral pressures, groundwater,",
            "    rock depth, mine-map check.",
            "3. Survey of 441 and 442 Baird and",
            "    386 Forest foundations for the",
            "    shoring design.",
        ]),
    ])
    L = MARGIN + 0.45
    cols = [
        (L, 4.0, [
            ("Governing codes (confirm edition)", [
                ("Building", "WV State Building Code,\n87 CSR 4: 2018 IRC for the\ntwo-family dwelling"),
                ("Beyond IRC", "Retaining walls over the IRC\ntables, steel frame: 2018 IBC,\nASCE 7-16, ACI 318-14,\nAISC 360-16, NDS 2018"),
                ("Local", "City of Morgantown Code\nEnforcement issues the permit\nand sets local design criteria"),
            ]),
            ("Design loads (assumed)", [
                ("Floors, units", "40 psf live, 15 psf dead\n(30 psf live in bedrooms)"),
                ("Porches", "60 psf live (1.5 x floor)"),
                ("Garage slab", "40 psf or 3,000 lb wheel load"),
                ("Roof", "Ground snow 30 psf (verify),\n15 psf dead"),
                ("Wind", "115 mph ultimate, Exposure B\n(verify; hillside may govern)"),
                ("Seismic", "Design Category A/B (verify)"),
                ("Soil bearing", "1,500 psf presumptive until\nthe geotech report"),
                ("Lateral soil", "60 pcf at-rest on restrained\nwalls + 2 ft surcharge; add\nneighbour-footing surcharge"),
                ("Frost depth", "36 in. (verify with the city)"),
            ]),
        ]),
        (L + 4.42, 4.0, [
            ("Structural system", [
                "Garage level: 12 in. reinforced concrete walls on the west,\nnorth and east, retaining 8 to 13 ft of soil. They are\nrestrained at the top by the Unit A floor diaphragm, so\nthat floor must be built and anchored before backfill.",
                "Front line: the garage doors leave almost no wall, so a\nsteel frame (beam B1 on four HSS columns) carries the\nfront of both floors and the roof and resists sideways\nload. This is the critical engineered element.",
                "Floors: 20 in. open-web wood trusses at 16 in. o.c.\nspanning front to back with no interior supports, which\nkeeps the garage column-free. Porches are 4 ft\ncantilevers of the same trusses.",
                "Walls above: 2x6 studs at 16 in. o.c. with wood\nstructural panel sheathing as shear walls.",
                "Roof: pre-engineered wood trusses at 24 in. o.c.",
            ]),
            ("Materials (assumed)", [
                ("Concrete", "Footings 3,000 psi. Walls and\ngarage slab 4,000 psi,\nair-entrained"),
                ("Reinforcing", "ASTM A615 Grade 60"),
                ("Steel", "W shapes A992; HSS A500\nGr. C; hot-dip galvanized\nwhere exposed"),
                ("Framing", "SPF No. 2 studs and plates;\nLVL 2.0E headers; treated\nsill plates"),
                ("Sheathing", "7/16 in. OSB walls, 23/32 in.\nT&G subfloor glued + screwed,\n5/8 in. roof"),
            ]),
        ]),
        (L + 8.84, 4.0, [
            ("Excavation and neighbours", [
                "Cut is 8 to 13 ft deep and within 5 to 9 ft of three\nneighbouring lots. Assume engineered shoring\n(soldier piles and lagging or equivalent) on the\nwest, north and east. No sloped open cut fits.",
                "Pre-construction survey and vibration monitoring of\n441 and 442 Baird and 386 Forest.",
                "Underpinning if any neighbouring footing falls inside\na 1:1 line from the bottom of this excavation.",
            ]),
            ("Drainage and waterproofing", [
                "Membrane waterproofing and drainage board on all\nretaining walls. 4 in. perforated footing drain in\nstone, to a sump in the mech room.",
                "Slab on 4 in. stone with a 15-mil vapour barrier,\nsloped 1/8 in. per ft to the trench drain.",
            ]),
            ("Special inspections to expect", [
                "Soil bearing, rebar placement, concrete strength,\nsteel frame bolting and welding, shear-wall nailing.",
            ]),
            ("Preliminary member schedule", [
                ("B1", "W12 steel beam, front line"),
                ("C1-C4", "HSS 6x6x3/8 columns"),
                ("W1", "12 in. concrete wall"),
                ("F1", "Footing 3'-0\" x 12 in.\n(4'-6\" at the wing rear)"),
                ("F2", "Pad 4'-0\" x 4'-0\" x 16 in."),
                ("FT1", "20 in. floor truss @ 16 in."),
                ("RT1 / RT2", "Roof truss @ 24 in."),
            ]),
        ]),
    ]
    text_columns(bg, cols)
    bg.text(L, SHEET_H - MARGIN - 0.3, "STRUCTURAL NOTES AND DESIGN CRITERIA", fontsize=12, fontweight="bold", va="center")
    save(fig, "S-001", pdf)


def offset_poly(pts, d):
    return list(Polygon(pts).buffer(d, join_style=2).exterior.coords)


def sheet_s101(pdf):
    notes = [
        ("Foundation plan", [
            "F1: continuous footing 3'-0\" x 12 in.",
            "under all 12 in. walls, widened to 4'-6\"",
            "at the wing rear wall (tallest fill).",
            "F2: 4'-0\" square pads under the four",
            "front frame columns, tied by a grade",
            "beam below the door sills.",
            "Bottom of footing EL 912.0 or lower,",
            "36 in. minimum below finished grade",
            "at the front where it is exposed.",
        ]),
        ("Slab", [
            "5 in. slab, #4 at 18 in. each way, on a",
            "15-mil vapour barrier and 4 in. stone.",
            "Slope 1/8 in./ft to the trench drain.",
            "Saw-cut joints as shown. Thicken to",
            "10 in. under the storage partition.",
            "2 in. rigid insulation under the storage",
            "room and mech room slabs.",
        ]),
        ("Drainage", [
            "Footing drain (dashed blue) around the",
            "three buried sides to a sump in the",
            "mech room. Discharge location is a",
            "civil/City Engineer item: it must not",
            "create a structure in the right-of-way.",
        ]),
        ("Preliminary", [
            "Sizes are assumptions for the engineer",
            "to check against the soil report.",
        ]),
    ]
    fig, bg = new_sheet("S-101", "Foundation plan", "3/16\" = 1'-0\"", notes)
    ax = plan_frame(fig, "Foundation and slab plan", f"Top of slab EL {EL_GAR:.1f} · footings dashed · preliminary sizes", street=False)
    lower_plan(ax, "bg", cars=False)
    # footings
    outer = offset_poly(OUT, 1.0)
    inner = offset_poly(IN_L, -1.0)
    line(ax, outer, color=INK, lw=0.7, ls=(0, (5, 3)), z=7)
    line(ax, inner, color=INK, lw=0.7, ls=(0, (5, 3)), z=7)
    rect(ax, BX0 - 2.5, 31.0, WX1 + 1.0, WY1 + 2.5, fc="none", ec=INK, lw=0.7, z=7, ls=(0, (5, 3)))
    txt(ax, 19, 36.4, "F1 WIDENED TO 4'-6\" AT WING REAR WALL", size=4.8, box=True)
    for cx in COLS:
        rect(ax, cx - 2, FRAME_Y - 2, cx + 2, FRAME_Y + 2, fc="none", ec=STEEL, lw=0.9, z=8, ls=(0, (5, 3)))
        rect(ax, cx - 0.3, FRAME_Y - 0.3, cx + 0.3, FRAME_Y + 0.3, fc=STEEL, ec=STEEL, z=9)
    for i, cx in enumerate(COLS):
        txt(ax, cx, 5.3, f"C{i + 1} / F2", size=4.8, color=STEEL, weight="bold", box=True)
    line(ax, [(COLS[0], FRAME_Y), (COLS[-1], FRAME_Y)], color=STEEL, lw=0.6, ls=(0, (2, 2)), z=8)
    txt(ax, 19.4, 7.0, "GRADE BEAM 16\" x 24\" BELOW DOOR SILLS, TIES F2 PADS", size=4.6, color=STEEL, box=True)
    # footing drain + sump
    fd = offset_poly(OUT, 1.6)
    seg = [p for p in fd if p[1] > 8.5]
    line(ax, [(BX0 - 1.6, 9.0), (BX0 - 1.6, WY1 + 1.6), (WX1 + 1.6, WY1 + 1.6), (WX1 + 1.6, BY1 + 1.6), (BX1 + 1.6, BY1 + 1.6), (BX1 + 1.6, 9.0)],
         color=BLUE, lw=0.9, ls=(0, (6, 2, 1, 2)), z=8)
    line(ax, [(BX1 + 1.6, 26.0), (43.2, 26.0)], color=BLUE, lw=0.9, ls=(0, (6, 2, 1, 2)), z=8)
    ax.add_patch(plt.Circle((43.0, 24.4), 0.9, fc=PAPER, ec=BLUE, lw=1.0, zorder=9))
    txt(ax, 43.0, 24.4, "SUMP", size=3.8, color=BLUE)
    txt(ax, 48.6, 22.0, "4\" FOOTING\nDRAIN", size=4.6, color=BLUE)
    # slab joints and slopes
    for x in (19.39, 28.28):
        line(ax, [(x, 8.8), (x, 27.9)], lw=0.4, color=GREY, ls=(0, (8, 3)), z=6)
    line(ax, [(10.6, 18.5), (37.1, 18.5)], lw=0.4, color=GREY, ls=(0, (8, 3)), z=6)
    for x in (15, 24, 33):
        ax.annotate("", xy=(x, 10.0), xytext=(x, 15.5), arrowprops=dict(arrowstyle="-|>", lw=0.5, color=GREY), zorder=7)
    txt(ax, 24, 16.6, "SLOPE 1/8\"/FT TO TRENCH DRAIN", size=4.6, color=GREY, box=True)
    line(ax, [(DOOR_A[0], 7.55), (DOOR_B[1], 7.55)], lw=1.4, color=BLUE, z=6)
    txt(ax, 24, 22.8, "5\" SLAB · #4 @ 18\" E.W. · 15-MIL VAPOUR BARRIER · 4\" STONE", size=4.8, box=True)
    txt(ax, 24, 21.6, f"T.O. SLAB EL {EL_GAR:.1f}", size=5.2, weight="bold", box=True)
    txt(ax, 19, 30.4, "INSULATED SLAB · THICKENED EDGE UNDER PARTITION", size=4.4, box=True)
    # wall tags
    for (x, y, t) in ((6.4, 22, "W1"), (27, 37.8, "W1"), (47.5, 14, "W1"), (39, 31.6, "W1")):
        ax.add_patch(plt.Circle((x, y), 1.0, fc=PAPER, ec=INK, lw=0.6, zorder=9))
        txt(ax, x, y, t, size=4.8, weight="bold", z=10)
    line(ax, [(7.4, 22), (9.6, 22)], lw=0.3)
    line(ax, [(27, 36.8), (27, 35.2)], lw=0.3)
    line(ax, [(46.5, 14), (45.1, 14)], lw=0.3)
    line(ax, [(39, 30.6), (39, 30.1)], lw=0.3)
    txt(ax, 2.2, 28.5, "W1 = 12\" CONC.\nWALL, #5 @ 12\"\nVERT. INSIDE\nFACE, #4 @ 12\"\nHORIZ. (PRELIM.)", size=4.4, color=GREY)
    dim(ax, (BX0, WY1), (WX1, WY1), 4.6, "19'-0\"", size=5.2)
    dim(ax, (BX1, BY0), (BX1, BY1), -8.2, "22'-0\"", side=-1, size=5.2)
    dim(ax, (BX0, -1.2), (BX1, -1.2), 0, "35'-6\"", ext=False, size=5.2)
    for a, b in zip(COLS[:-1], COLS[1:]):
        dim(ax, (a, 2.6), (b, 2.6), 0, ftin(b - a), ext=False, size=4.8, color=STEEL)
    save(fig, "S-101", pdf)


TR = "#7a5c2e"


def floor_framing(ax, over_garage):
    """Floor trusses at 16 in. o.c. spanning front to back; common to both unit floors."""
    shaft = SHAFT_L if over_garage else SHAFT_U
    y_front = FRAME_Y if over_garage else BY0 + 0.25
    for x in np.arange(10.17, 28.4, 16 / 12):
        line(ax, [(x, y_front), (x, 34.5)], lw=0.35, color=TR, z=7)
        line(ax, [(x, 4.0), (x, y_front)], lw=0.35, color=TR, z=7, ls=(0, (3, 2)))
    for x in np.arange(28.83, 37.1, 16 / 12):
        line(ax, [(x, y_front), (x, 29.5)], lw=0.35, color=TR, z=7)
        if x < 35.5:
            line(ax, [(x, 4.0), (x, y_front)], lw=0.35, color=TR, z=7, ls=(0, (3, 2)))
    for x in np.arange(38.2, 44.4, 16 / 12):
        line(ax, [(x, shaft[3] + 0.3), (x, 29.5)], lw=0.35, color=TR, z=7)
    rect(ax, 9.5, 4.0, 35.5, BY0, fc="none", ec=TR, lw=0.7, z=7, ls=(0, (3, 2)))
    for x in (28.5, 37.3):
        line(ax, [(x, y_front), (x, 29.5 if x > 30 else 34.5)], lw=1.3, color=TR, z=8)
    txt(ax, 29.7, 26.6, "GT1", size=4.8, color=TR, weight="bold", rot=90, box=True)
    txt(ax, 36.2, 26.6, "GT1", size=4.8, color=TR, weight="bold", rot=90, box=True)
    rect(ax, shaft[0], shaft[2], shaft[1], shaft[3], fc="none", ec=INK, lw=0.6, z=8, hatch="xx")
    txt(ax, 40.75, 15.2, "STAIR\nOPENING", size=5.0, weight="bold", box=True, z=10)
    txt(ax, 19.2, 27.6, "FT1 · 20\" OPEN-WEB FLOOR TRUSSES @ 16\" O.C.", size=5.2, weight="bold", box=True, z=10)
    txt(ax, 19.2, 26.4, "span 26'-4\" · front bearing to wing rear wall", size=4.8, box=True, z=10)
    txt(ax, 33.0, 14.5, "FT1 @ 16\"\nspan 21'-4\"", size=4.8, box=True, z=10)
    txt(ax, 41.2, 26.0, "FT1 @ 16\"\nspan 7'", size=4.4, box=True, z=10)
    txt(ax, 22.5, 2.9, "4'-0\" PORCH CANTILEVER (TRUSS TOP CHORD EXTENDS) · 60 PSF LIVE", size=4.6, color=TR)
    ax.annotate("", xy=(14, 33.6), xytext=(14, 9.4), arrowprops=dict(arrowstyle="<|-|>", lw=0.6, color=INK), zorder=10)


def sheet_s102(pdf):
    notes = [
        ("Unit A floor framing", [
            "FT1: 20 in. open-web floor trusses at",
            "16 in. o.c., spanning front to back:",
            "26'-4\" in the wing bay, 21'-4\" in the",
            "east bay. No interior bearing, so the",
            "garage stays column-free.",
            "Top-chord cantilever 4'-0\" for the porch.",
            "Truss maker designs to L/480 live load",
            "with the loads on S-001.",
        ]),
        ("Front frame (critical)", [
            "B1: W12 steel beam on C1-C4. It",
            "carries Units A and B and the roof over",
            "the garage doors and, with the columns,",
            "forms the lateral frame for the open",
            "front. Engineer to size as a moment",
            "frame or braced portal.",
        ]),
        ("Stair opening", [
            "Shaft walls run full height in concrete",
            "or CMU to this floor, wood above.",
            "Girder truss GT1 each side.",
        ]),
        ("Diaphragm", [
            "23/32 in. T&G subfloor, glued and",
            "screwed. Blocked at walls. Anchor the",
            "floor to the concrete walls before",
            "backfilling: it props the walls.",
        ]),
        ("Loads from above", [
            "Six bathrooms and two kitchens sit on",
            "these floors: allow for tile and",
            "fixture dead load in the truss design.",
        ]),
    ]
    fig, bg = new_sheet("S-102", "Unit A floor framing", "3/16\" = 1'-0\"", notes)
    ax = plan_frame(fig, "Unit A floor framing plan", f"Framing at EL {EL_MAIN:.1f} over the garage · garage walls below shown grey · preliminary", street=False)
    lower_plan(ax, "bg", cars=False)
    floor_framing(ax, True)
    line(ax, [(BX0, FRAME_Y), (BX1, FRAME_Y)], lw=3.0, color=STEEL, z=9)
    for i, cx in enumerate(COLS):
        rect(ax, cx - 0.35, FRAME_Y - 0.35, cx + 0.35, FRAME_Y + 0.35, fc=PAPER, ec=STEEL, lw=1.4, z=10)
        txt(ax, cx, 10.2, f"C{i + 1}", size=4.8, color=STEEL, weight="bold", box=True, z=11)
    txt(ax, 19.4, 6.4, "B1  W12 STEEL BEAM, CONTINUOUS OVER C2 AND C3 (PRELIM.) · FRAME RESISTS LATERAL LOAD AT THE OPEN FRONT", size=4.6, color=STEEL, box=True, z=11)
    txt(ax, 5.0, 30.5, "ANCHOR FLOOR TO\nCONCRETE WALLS\nBEFORE BACKFILL", size=4.4, color=ACCENT)
    line(ax, [(8.2, 30.5), (9.6, 30.5)], lw=0.3, color=ACCENT)
    save(fig, "S-102", pdf)


def sheet_s103(pdf):
    notes = [
        ("Unit B floor framing", [
            "Same FT1 trusses and layout as the",
            "Unit A floor, so bearing lines stack.",
            "Here the trusses bear on the 2x6 stud",
            "walls of Unit A instead of steel and",
            "concrete.",
        ]),
        ("Headers in the front wall", [
            "H1 over the 8 ft sliding door:",
            "(3) 1-3/4 x 11-7/8 LVL on (3) 2x6",
            "trimmers each end.",
            "H2 over the 5 ft kitchen window:",
            "(2) 1-3/4 x 9-1/4 LVL on (2) trimmers.",
            "Both carry this floor, the porch and",
            "the roof. Preliminary.",
        ]),
        ("Walls below (Unit A)", [
            "Interior partitions in Unit A are not",
            "bearing walls. Do not rely on them.",
            "The stair enclosure walls are 1-hour",
            "rated and continuous through this floor.",
        ]),
        ("Rated floor", [
            "This is the 1-hour separation between",
            "the two units (IRC R302.3). Build it to a",
            "tested floor/ceiling design; firestop",
            "every pipe, duct and wire through it.",
        ]),
        ("Sound", [
            "Not required by the IRC, but strongly",
            "recommended between rental units:",
            "resilient channel, insulation and a",
            "gypsum-concrete or mat underlayment.",
        ]),
    ]
    fig, bg = new_sheet("S-103", "Unit B floor framing", "3/16\" = 1'-0\"", notes)
    ax = plan_frame(fig, "Unit B floor framing plan", f"Framing at EL {EL_UP:.1f} over Unit A · Unit A walls below shown grey · preliminary", street=False)
    unit_plan(ax, "bg", "A")
    floor_framing(ax, False)
    for (a, b, lab) in ((22, 30, "H1"), (12, 17, "H2"), (39.5, 43, "H2")):
        line(ax, [(a - 0.4, BY0 + 0.25), (b + 0.4, BY0 + 0.25)], lw=3.0, color=STEEL, z=9)
        txt(ax, (a + b) / 2, 6.6, lab, size=5.0, color=STEEL, weight="bold", box=True, z=11)
    txt(ax, 22.5, 5.2, "BEARING ON UNIT A FRONT WALL (2x6 @ 16\") · LVL HEADERS OVER OPENINGS", size=4.6, color=STEEL, box=True, z=11)
    save(fig, "S-103", pdf)


def sheet_s104(pdf):
    notes = [
        ("Roof framing", [
            "RT1: common trusses at 24 in. o.c. over",
            "the east bay, 22'-0\" span, 6:12.",
            "RT2: broken-pitch trusses over the wing",
            "bay, 27'-0\" span, 6:12 front and 3:12",
            "beyond the 22 ft line.",
            "12 in. overhangs. Hurricane ties at",
            "every truss. 5/8 in. sheathing with clips.",
            "Porch roof: 4 ft outlookers at plate level.",
        ]),
        ("Shear walls (red)", [
            "SW: 7/16 in. OSB, 8d at 4 in. edges,",
            "hold-downs at ends (preliminary).",
            "Side and rear walls have long solid",
            "runs. The front wall is mostly glass:",
            "its narrow piers need engineered",
            "hold-downs or a second steel frame",
            "at Unit A level.",
        ]),
        ("Roof penetrations", [
            "Two 3 in. plumbing vents, bath and",
            "dryer exhausts leave through walls,",
            "not the roof. Keep vents 10 ft from",
            "any opening and off the front slope.",
        ]),
        ("Fire separation", [
            "Stair walls run tight to the roof deck.",
            "Attic draft-stopping over the stair",
            "wall line.",
        ]),
    ]
    fig, bg = new_sheet("S-104", "Roof framing and shear walls", "3/16\" = 1'-0\"", notes)
    ax = plan_frame(fig, "Roof framing plan and shear-wall key", "Trusses at 24 in. o.c. · walls of Unit B shown grey · preliminary", street=False)
    unit_plan(ax, "bg", "B")
    c = TR
    poly(ax, [(BX0 - 1, BY0 - 1), (BX1 + 1, BY0 - 1), (BX1 + 1, BY1 + 1), (WX1 + 1, BY1 + 1), (WX1 + 1, WY1 + 1), (BX0 - 1, WY1 + 1)],
         fc="none", ec=c, lw=0.7, z=7, ls=(0, (6, 3)))
    for x in np.arange(10.5, 28.4, 2.0):
        line(ax, [(x, BY0 - 1), (x, WY1 + 1)], lw=0.4, color=c, z=7)
    for x in np.arange(30.5, 45.5, 2.0):
        line(ax, [(x, BY0 - 1), (x, BY1 + 1)], lw=0.4, color=c, z=7)
    line(ax, [(BX0 - 1, 19), (BX1 + 1, 19)], lw=1.4, color=c, z=8)
    line(ax, [(BX0 - 1, 30), (WX1, 30)], lw=0.8, color=c, z=8, ls=(0, (2, 2)))
    line(ax, [(28.5, BY0 - 1), (28.5, WY1 + 1)], lw=1.2, color=c, z=8)
    txt(ax, 36.5, 19.9, "RIDGE", size=4.8, color=c, weight="bold", box=True, z=10)
    txt(ax, 19, 30.9, "PITCH BREAK 6:12 TO 3:12", size=4.4, color=c, box=True, z=10)
    txt(ax, 19, 14.2, "RT2 · BROKEN-PITCH TRUSSES @ 24\" · 27'-0\"", size=5.0, weight="bold", box=True, z=10)
    txt(ax, 36.8, 14.2, "RT1 · COMMON TRUSSES\n@ 24\" · 22'-0\"", size=4.8, weight="bold", box=True, z=10)
    for x, y, a in ((19, 11.5, 270), (19, 25.5, 90), (36.8, 11.2, 270), (36.8, 25.5, 90)):
        dy = -2.2 if a == 270 else 2.2
        ax.annotate("", xy=(x, y + dy), xytext=(x, y), arrowprops=dict(arrowstyle="-|>", lw=0.6, color=c), zorder=10)
    txt(ax, 22.5, 5.2, "PORCH ROOF: 4' OUTLOOKERS AT PLATE", size=4.4, color=c)
    rect(ax, 9.0, 3.5, 36.0, BY0 - 1, fc="none", ec=c, lw=0.6, z=7, ls=(0, (3, 2)))
    sw = [((BX0 + 0.25, 14.2), (BX0 + 0.25, 26.4)), ((BX0 + 0.25, 30.6), (BX0 + 0.25, 34.5)), ((16.6, WY1 - 0.25), (21.4, WY1 - 0.25)),
          ((26.6, WY1 - 0.25), (28, WY1 - 0.25)), ((WX1 - 0.25, 30), (WX1 - 0.25, 34.5)), ((28.5, BY1 - 0.25), (38.4, BY1 - 0.25)),
          ((BX1 - 0.25, 8.5), (BX1 - 0.25, 23.4)), ((BX1 - 0.25, 27.6), (BX1 - 0.25, 29.5)),
          ((17.6, BY0 + 0.25), (21.4, BY0 + 0.25)), ((30.6, BY0 + 0.25), (38.9, BY0 + 0.25)), ((37.25, 8.5), (37.25, 21.7))]
    for a, b in sw:
        line(ax, [a, b], lw=2.6, color=ACCENT, z=9)
    txt(ax, 48.2, 16, "SW", size=5.0, color=ACCENT, weight="bold")
    txt(ax, 6.6, 20, "SW", size=5.0, color=ACCENT, weight="bold")
    txt(ax, 19, 36.8, "SW", size=5.0, color=ACCENT, weight="bold")
    txt(ax, 34.8, 9.6, "SW", size=4.6, color=ACCENT, weight="bold", box=True, z=10)
    txt(ax, 19.5, 9.6, "SW (short pier)", size=4.4, color=ACCENT, weight="bold", box=True, z=10)
    save(fig, "S-104", pdf)


def sheet_s301(pdf):
    notes = [
        ("1 · Retaining wall", [
            "Typical at the wing rear wall, the tallest",
            "condition (±12.5 ft of soil). The wall is",
            "propped by the slab at the bottom and",
            "by the Unit A floor at EL 925.5; above",
            "that it cantilevers 3 ft as a stem wall.",
            "Rebar shown is a placeholder.",
        ]),
        ("2 · Front frame", [
            "Looking north at the garage doors.",
            "B1 spans 17'-3\", 9'-2\" and 7'-2\" over",
            "C1-C4. Rough check for the 17 ft bay:",
            "about 2.4 kips/ft from two floors, porch",
            "and roof gives ±85 kip-ft. A W12x30",
            "works for gravity; lateral design will",
            "likely increase it.",
            "Columns bear on F2 pads tied by a",
            "grade beam under the door sills.",
        ]),
        ("Sequence that matters", [
            "1. Shore. 2. Excavate. 3. Footings and",
            "walls. 4. Slab. 5. Steel frame. 6. Unit A",
            "floor, anchored to walls. 7. Only then",
            "backfill, in lifts, with light compaction",
            "near the walls.",
        ]),
        ("Preliminary", [
            "For the engineer of record to redesign.",
        ]),
    ]
    fig, bg = new_sheet("S-301", "Structural sections", "As noted", notes)
    # --- detail 1: wall section at 3/8" = 1' (2.667 ft/in)
    f1 = 8 / 3.0
    ax = plan_axes(fig, 0.75, 0.9, (-9, 11), (-4.5, 19.5), f1)
    z0 = 0.0                                # top of slab
    poly(ax, [(1, -1.5), (11, -1.5), (11, 12.5), (1, 12.5)], fc="#efe9e1", ec="none", z=1)
    ax.fill_between([1, 11], [12.5, 12.9], [12.5 - 0.8, 12.9 - 0.8], hatch="////", fc="none", ec=EARTH, lw=0, zorder=2, alpha=0.6)
    line(ax, [(1, 12.5), (11, 12.9)], lw=1.2, z=6)
    rect(ax, -4.5, -2.75, 3.0, -1.5, fc=CONC, ec=INK, lw=0.9, z=4)                     # footing 7'-6"? shown 4'-6" + toe
    rect(ax, 0, -1.5, 1, 14.0, fc=CONC, ec=INK, lw=0.9, z=5)                           # wall
    rect(ax, -9, -0.42, 0, 0, fc=CONC, ec=INK, lw=0.7, z=4)                            # slab
    rect(ax, -9, -0.9, 0, -0.42, fc="#e1ddd4", ec="none", z=3)
    rect(ax, 1, -1.5, 1.9, 12.0, fc="#dcdfe3", ec="none", z=3, hatch="....")           # drainage stone/board
    ax.add_patch(plt.Circle((1.6, -1.1), 0.3, fc=PAPER, ec=BLUE, lw=1.0, zorder=6))
    line(ax, [(0.75, -1.3), (0.75, 13.7)], lw=0.9, color=ACCENT, z=7)                  # inside-face vertical bars
    for y in np.arange(-1.0, 13.8, 1.0):
        ax.add_patch(plt.Circle((0.6, y), 0.06, fc=ACCENT, ec=ACCENT, zorder=7))
    line(ax, [(0.75, -1.3), (0.75, -2.45), (-3.8, -2.45)], lw=0.9, color=ACCENT, z=7)
    line(ax, [(-4.2, -1.8), (2.7, -1.8)], lw=0.9, color=ACCENT, z=7)
    # floor at EL 925.5 (11 ft above slab)
    rect(ax, -9, 11 - 1.73, 0, 11, fc="#e9e4d9", ec=INK, lw=0.8, z=4)
    for x in np.arange(-8, 0, 2.0):
        line(ax, [(x - 0.8, 11 - 1.73), (x, 10.9), (x + 0.8, 11 - 1.73)], lw=0.25, color=GREY, z=5)
    rect(ax, -0.9, 11 - 1.73, 0, 11 - 1.48, fc=POCHE, z=6)                              # ledger / bearing
    rect(ax, 0, 14.0, 0.5, 19.5, fc=POCHE, z=5)                                         # stud wall above
    rect(ax, 0, 14.0, 1, 14.15, fc=POCHE, z=6)
    lab = [(-8.6, 12.0, "UNIT A FLOOR  EL 925.5"), (-8.6, 0.6, f"GARAGE SLAB  EL {EL_GAR:.1f}")]
    for x, y, s in lab:
        txt(ax, x, y, s, size=5.6, weight="bold", ha="left")
    call = [((0.5, 7.0), (4.2, 7.6), "12\" CONCRETE WALL, 4,000 PSI\n#5 @ 12\" VERT. INSIDE FACE\n#4 @ 12\" HORIZ. (PLACEHOLDER)"),
            ((1.45, 4.0), (4.2, 4.6), "WATERPROOFING MEMBRANE +\nDRAINAGE BOARD, FREE-DRAINING\nBACKFILL 12\" MIN."),
            ((1.6, -1.1), (4.4, 0.6), "4\" PERFORATED FOOTING DRAIN\nIN STONE, FILTER FABRIC, TO SUMP"),
            ((-2.0, -2.1), (-8.6, -3.4), "F1 FOOTING 4'-6\" x 15\" HERE (3'-0\" x 12\" ELSEWHERE), BEARING ON UNDISTURBED SOIL OR ROCK"),
            ((-0.45, 9.4), (-8.6, 8.0), "FLOOR TRUSSES BEAR ON A LEDGE OR\nSTEEL ANGLE; ANCHOR BOLTS TIE THE\nDIAPHRAGM TO THE WALL (PROP)"),
            ((0.5, 13.0), (4.2, 15.2), "WALL CONTINUES 3'-0\" ABOVE THE\nFLOOR AS A CANTILEVER STEM\nWHERE GRADE IS ABOVE THE FLOOR"),
            ((0.25, 17.0), (4.2, 18.0), "2x6 STUD WALL, TREATED SILL,\nANCHOR BOLTS @ 32\""),
            ((6.0, 12.7), (4.4, 10.6), "FINISHED GRADE ±EL 927\nSLOPE AWAY 5 % MIN.")]
    for (px, py), (tx, ty), s in call:
        line(ax, [(px, py), (tx - 0.15 if tx > px else tx + 0.2, ty)], lw=0.3, z=8)
        txt(ax, tx, ty, s, size=4.9, ha="left", va="center", box=True)
    dim(ax, (-6.6, 0), (-6.6, 11), 0, "11'-0\"", ext=False, size=5.2)
    dim(ax, (9.6, 0), (9.6, 12.8), 0, "±12'-6\" RETAINED", ext=False, size=5.0, side=-1)
    dim(ax, (0, -3.5), (1, -3.5), 0, "12\"", ext=False, size=4.8)
    txt(ax, -9, -4.2, "1   RETAINING WALL AT WING REAR (TALLEST CONDITION)      3/8\" = 1'-0\"", size=7.4, weight="bold", ha="left")
    # --- detail 2: front frame elevation at 3/16"
    f2 = 8.0
    ax2 = plan_axes(fig, 8.45, 6.55, (7, 47.5), (EL_GAR - 5, EL_GAR + 19), f2)
    g = EL_GAR
    rect(ax2, 7, g - 5, 47.5, g, fc="#efe9e1", ec="none", z=1)
    line(ax2, [(7, g), (47.5, g)], lw=1.0, z=3)
    rect(ax2, 9.5, g - 2.2, 45, g - 0.2, fc=CONC, ec=INK, lw=0.6, z=2)                  # grade beam
    for cx in COLS:
        rect(ax2, cx - 2, g - 3.5, cx + 2, g - 2.2, fc=CONC, ec=INK, lw=0.6, z=2)
        rect(ax2, cx - 0.25, g - 0.2, cx + 0.25, g + 8.3, fc=STEEL, ec=STEEL, z=5)
    rect(ax2, 9.5, g + 8.3, 45, g + 9.3, fc=STEEL, ec=STEEL, z=5)                        # B1
    rect(ax2, 9.5, g + 9.3, 45, g + 11.0, fc="#e9e4d9", ec=INK, lw=0.6, z=4)             # floor trusses (end view band)
    for x in np.arange(10.17, 45, 16 / 12):
        line(ax2, [(x, g + 9.3), (x, g + 11.0)], lw=0.2, color=GREY, z=5)
    rect(ax2, 9.5, g + 11.0, 45, g + 19, fc="#fbfaf7", ec=INK, lw=0.6, z=3)
    for (a, b), lab in ((DOOR_A, "16' x 8' DOOR"), (DOOR_B, "8' x 8' DOOR"), (ENTRY, "ENTRY")):
        rect(ax2, a, g, b, g + (8 if b - a > 4 else 6.67), fc=PAPER, ec=GREY, lw=0.5, z=4, ls="--")
        txt(ax2, (a + b) / 2, g + 3.6, lab, size=4.6, color=GREY, rot=90 if b - a < 4 else 0)
    for i, cx in enumerate(COLS):
        txt(ax2, cx, g - 4.3, f"C{i + 1} / F2", size=4.8, color=STEEL, weight="bold")
    txt(ax2, 27, g + 12.6, "B1  W12 STEEL BEAM", size=4.8, color=STEEL, weight="bold", z=9)
    line(ax2, [(27, g + 12.0), (27, g + 9.4)], lw=0.3, color=STEEL, z=9)
    txt(ax2, 27, g + 16.2, "UNIT A WALL ABOVE (2x6 STUDS, SLIDING DOORS)", size=4.6, color=GREY)
    txt(ax2, 27, g - 1.2, "GRADE BEAM TIES THE PADS", size=4.4)
    for a, b in zip(COLS[:-1], COLS[1:]):
        dim(ax2, (a, g + 6.2), (b, g + 6.2), 0, ftin(b - a), ext=False, size=4.8, color=STEEL)
    for cx in COLS[1:3]:
        ax2.add_patch(plt.Circle((cx, g + 8.3), 0.55, fc="none", ec=ACCENT, lw=1.0, zorder=8))
    for cx in (COLS[0], COLS[3]):
        ax2.add_patch(plt.Circle((cx, g + 8.3), 0.55, fc="none", ec=ACCENT, lw=1.0, zorder=8))
    txt(ax2, 33.2, g + 6.9, "", size=4)
    bg.text(8.45, 9.9, "2   FRONT STEEL FRAME, LOOKING NORTH      1/8\" = 1'-0\"", fontsize=7.4, fontweight="bold")
    bg.text(8.45, 6.3, "Red circles: beam-to-column joints the engineer must detail as moment connections\nor replace with a braced/portal system. This frame is what keeps the open garage\nfront from racking under wind and seismic load.", fontsize=6.2, color=ACCENT, va="top", linespacing=1.3)
    bg.text(8.45, 5.35, "ROUGH GRAVITY CHECK FOR THE ENGINEER (17'-3\" BAY)", fontsize=7.0, fontweight="bold", va="top")
    rows = [("Two unit floors", "2 x 55 psf x 13.2 ft tributary", "1,450 plf"), ("Two porches", "2 x 75 psf x 2 ft", "300 plf"),
            ("Roof", "45 psf x 12 ft", "540 plf"), ("Walls", "two storeys of 2x6 wall", "180 plf"), ("Total", "", "±2,470 plf"),
            ("Moment", "w L² / 8, L = 16.5 ft clear", "±84 kip-ft"), ("Trial size", "W12x30, A992 (Zx 43 in³)", "gravity only")]
    for i, (a, b, c) in enumerate(rows):
        y = 5.07 - i * 0.2
        bg.text(8.45, y, a, fontsize=6.3, va="top", fontweight="bold" if a in ("Total", "Trial size") else "normal")
        bg.text(9.75, y, b, fontsize=6.3, va="top", color=GREY)
        bg.text(12.55, y, c, fontsize=6.3, va="top", fontweight="bold" if a in ("Total", "Trial size") else "normal")
    bg.text(8.45, 3.57, "Unfactored service loads, simple span. Deflection, lateral load, continuity and\nbearing still to be checked. Not a design.", fontsize=5.8, color=GREY, va="top", linespacing=1.3)
    save(fig, "S-301", pdf)
