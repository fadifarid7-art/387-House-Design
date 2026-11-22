"""Sheets A-101..A-103 (plans), A-201 (street elevation), A-301 (section). Rev B: duplex over 3-car garage."""
import math

import numpy as np

from common import *  # noqa: F401,F403
from levels import *  # noqa: F401,F403


def site_work(ax, bg=False):
    c = BG_EDGE if bg else INK
    poly(ax, APRON, fc="#d5dbe2" if not bg else "#eceef1", ec=c, lw=0.6, z=2)
    rect(ax, 37.5, 3, 45, BY0, fc="#e7eaee" if not bg else "#f3f4f6", ec=c, lw=0.5, z=2)       # entry landing, on lot
    rect(ax, *TRASH[:2], *TRASH[2:], fc="#dfe3d6" if not bg else "#f3f4f6", ec=c, lw=0.6, z=3)  # screened cart bay, on lot
    if not bg:
        for i in range(4):
            rect(ax, 38.6 + i * 1.6, 0.9, 39.9 + i * 1.6, 2.5, fc=PAPER, ec=GREY, lw=0.4, z=4)
    line(ax, [(11.0, 7.9), (10.75, 0.5)], lw=2.2, color=CONC, z=3)                             # west apron wall (on lot)
    line(ax, [(37.9, 2.9), (37.9, 0.5), (45.2, 0.5), (45.2, 7.9)], lw=1.8, color=CONC, z=3)    # low wall around bay + landing
    line(ax, [(DOOR_A[0], 7.55), (DOOR_B[1], 7.55)], lw=1.4, color=BLUE, z=6)                  # trench drain


def setback_dims(ax):
    dim(ax, (46.6, 0), (46.6, BY0), 0, "8'-0\"", ext=False, size=5.2, color=ACCENT)
    dim(ax, (BX1, 18.5), (50, 18.5), 0, "5'-0\"", ext=False, size=5.2, color=ACCENT)
    dim(ax, (west_x(22), 22), (BX0, 22), 0, ftin(perp_to_west(BX0, 22)), ext=False, size=5.2, color=ACCENT)
    s = math.atan(REAR_SLOPE)
    for (x, y, dx) in ((BX1, BY1, 2.8), (WX1, WY1, 3.0)):
        d = perp_to_rear(x, y)
        line(ax, [(x, y), (x - d * math.sin(s), y + d * math.cos(s))], color=ACCENT, lw=0.6, z=9)
        txt(ax, x + dx, y + 2.2, ftin(d), size=5.0, color=ACCENT)
    txt(ax, 39.5, 38.0, "REAR LOT LINE", size=5.0, color=ACCENT, rot=math.degrees(math.atan(REAR_SLOPE)))


def sheet_a101(pdf):
    notes = [
        ("Open garage", [
            f"Slab EL {EL_GAR:.1f}. 9'-2\" clear. No doors.",
            "One clear room, 26'-8\" x 20'-4\", with no",
            "walls or columns between cars. Stalls",
            "are painted lines only.",
            "Stall 1 is 9'-8\" (its driver's door faces",
            "the wall); stalls 2 and 3 are 8'-6\".",
            "Each driver's door has ±2'-3\" to 2'-5\".",
            "Duplex parking: 3 required, 3 provided.",
        ]),
        ("Because it is open", [
            "The garage is at outdoor temperature.",
            "No water pipes run through it. Drain",
            "pipes cross it inside the insulated,",
            "fire-rated ceiling.",
            "Lobby door is on the tenants' key.",
            "Lights are automatic (E-101). A conduit",
            "is left for a future grille.",
        ]),
        ("Trash", [
            "Screened, lockable bay for 4 carts (trash",
            "+ recycling for each flat) beside the",
            "entry landing, on the lot. Carts roll",
            "down the apron on collection day.",
        ]),
        ("Floor and relief", [
            "Broom-finished concrete, sealed,",
            "painted lines and numbers.",
            "Garage is 78 % of the front (65 % max);",
            "apron 26 ft at the R.O.W. (22 ft).",
        ]),
    ]
    fig, bg = new_sheet("A-101", "Garage level plan", "3/16\" = 1'-0\"", notes)
    ax = plan_frame(fig, "Garage level plan", f"Open 3-car garage · slab EL {EL_GAR:.1f} · concrete walls grey · rear wing not excavated at this level")
    site_work(ax)
    rect(ax, BX0, BY1, WX1, WY1, fc="#efe9e1", ec=EARTH, lw=0.5, z=1, ls="--", hatch="////", alpha=0.6)
    txt(ax, 19, 32.5, "UNEXCAVATED · rear wing of the flats above sits on fill here", size=4.8, color=EARTH, box=True)
    txt(ax, 24, 1.8, "CONCRETE APRON", size=6.0, weight="bold")
    txt(ax, 24, 0.6, "15 ft to pavement · slopes −7 % (west) to +12 % (east)", size=4.9)
    txt(ax, 24, -3.6, "CITY RIGHT-OF-WAY: APRON ONLY, NO WALLS / STEPS / POSTS\nbanks beside the apron graded back at 2:1", size=4.9, color=ACCENT)
    txt(ax, 41.5, 5.6, "ENTRY LANDING\nlevel, on lot", size=4.8)
    txt(ax, 48.6, 1.7, "TRASH BAY\n4 carts,\nscreened", size=4.4)
    line(ax, [(46.6, 1.7), (45.3, 1.7)], lw=0.3)
    txt(ax, 6.6, 5.0, "TRENCH DRAIN", size=4.4, color=BLUE)
    line(ax, [(8.6, 5.4), (11.4, 7.4)], lw=0.3, color=BLUE)
    txt(ax, 4.2, 1.4, "RETAINING WALL\nON LOT, ENDS AT\nLOT LINE", size=4.4, color=GREY)
    line(ax, [(7.0, 1.8), (10.7, 3.0)], lw=0.3, color=GREY)
    rect(ax, 9.5, 4, 35.5, BY0, fc="none", ec=GREY, lw=0.5, z=6, ls="--")
    txt(ax, 22.5, 5.6, "CANTILEVERED PORCHES ABOVE (NO POSTS IN THE APRON)", size=4.6, color=GREY, box=True)
    lower_plan(ax, "arch")
    txt(ax, 19.6, 9.6, "OPEN, NO DOOR", size=5.0, color=GREY)
    txt(ax, 33.0, 9.6, "OPEN", size=5.0, color=GREY)
    txt(ax, 42.4, 7.0, "ENTRY", size=4.6)
    txt(ax, 27.6, 6.9, "POST", size=4.0, color=BLUE)
    dim(ax, (BX0, BY1), (BX1, BY1), 6.6, "35'-6\"", size=5.4)
    dim(ax, (BX1, BY0), (BX1, BY1), -8.0, "22'-0\"", side=-1)
    for (a, b), lab in zip(STALLS, ("9'-8\"", "8'-6\"", "8'-6\"")):
        dim(ax, (a, 24.6), (b, 24.6), 0, lab, ext=False, size=4.8)
    dim(ax, (11.6, 8.67), (11.6, 29.0), 0, "20'-4\"", ext=False, size=4.8)
    dim(ax, (10.5, 15.4), (CARS[0], 15.4), 0, "2'-5\"", ext=False, size=4.4, color=BLUE)
    dim(ax, (CARS[0] + 6.2, 15.4), (CARS[1], 15.4), 0, "2'-3\"", ext=False, size=4.4, color=BLUE)
    dim(ax, (CARS[1] + 6.2, 15.4), (CARS[2], 15.4), 0, "2'-4\"", ext=False, size=4.4, color=BLUE)
    setback_dims(ax)
    save(fig, "A-101", pdf)


def unit_sheet(pdf, number, unit, el, notes):
    fig, bg = new_sheet(number, f"Unit {unit} plan", "3/16\" = 1'-0\"", notes)
    ax = plan_frame(fig, f"Unit {unit} floor plan", f"{'Main' if unit == 'A' else 'Upper'} level · finished floor EL {el:.1f} · 3 bedrooms, 3 baths · ±780 sf net")
    if unit == "A":
        rect(ax, BX0, BY1, WX1, WY1, fc="none", ec="none", z=1)
        poly(ax, APRON, fc="none", ec=GREY, lw=0.4, z=2, ls="--")
        txt(ax, 24, 0.8, "driveway apron below", size=4.8, color=GREY)
        rect(ax, 29.2, BY1, 44, 34.2, fc="#f3f4f5", ec=GREY, lw=0.5, z=2, ls="--")
        txt(ax, 37.0, 32.2, "REAR YARD AT GRADE\nheat-pump pads", size=4.8, color=GREY)
    else:
        rect(ax, BX0 - 1, BY0 - 1, BX1 + 1, BY1 + 1, fc="none", ec=GREY, lw=0.4, z=2, ls=(0, (6, 3)))
        txt(ax, 47.2, 12, "ROOF EAVE ABOVE", size=4.4, color=GREY, rot=90)
    porch(ax)
    txt(ax, 22.5, 6.1, "COVERED PORCH  26'-0\" x 4'-0\"  (cantilevered)", size=5.4, weight="bold", box=True)
    unit_plan(ax, "arch", unit)
    txt(ax, 26, 8.95, "8' SLIDING DOOR", size=4.2, color=GREY)
    txt(ax, 39.2, 10.6, "UNIT\nENTRY", size=4.4, color=RATED)
    txt(ax, 35.6, 16.1, "water heater", size=3.8, color=GREY)
    dim(ax, (BX0, WY1), (WX1, WY1), 1.6, "19'-0\"", size=5.4)
    dim(ax, (WX1, BY1), (BX1, BY1), 1.6 if unit == "B" else 5.6, "16'-6\"", size=5.4)
    dim(ax, (BX1, BY0), (BX1, BY1), -8.0, "22'-0\"", side=-1)
    dim(ax, (BX0, BY0), (BX0, WY1), 5.2, "27'-0\"")
    dim(ax, (37.6, 4), (37.6, BY0), 0, "4'-0\"", ext=False, size=5.0)
    setback_dims(ax)
    save(fig, number, pdf)


def sheet_a102(pdf):
    unit_sheet(pdf, "A-102", "A", EL_MAIN, [
        ("Unit A (main level)", [
            f"Finished floor EL {EL_MAIN:.1f}, 11'-0\" above the",
            "garage slab. 3 bedrooms, 3 baths with",
            "tubs, shared living room / kitchen.",
            "About 780 sf inside the unit.",
        ]),
        ("Bedrooms and baths", [
            "Bedroom 1: 94 sf. Bedroom 2: 79 sf.",
            "Bedroom 3: 77 sf. Code minimum is",
            "70 sf and 7 ft across.",
            "Each bath has a 5 ft tub/shower, toilet",
            "and sink, and opens only off its own",
            "bedroom. Bedrooms 1 and 2 share a",
            "short hall from the living room.",
            "Each bedroom has an escape window",
            "on an outside wall (IRC R310).",
        ]),
        ("This flat's own equipment", [
            "Water heater (80 gal) in the closet by",
            "the entry. Stacked washer and dryer.",
            "Range, refrigerator, dishwasher.",
            "Its own electric meter and panel, heat",
            "pump and water meter.",
        ]),
        ("Access", [
            "Unit door opens off the common stair",
            "landing. The stair is a 1-hour enclosure",
            "with its own street door.",
        ]),
        ("Finishes (rental grade)", [
            "Vinyl plank floors, one-piece fiberglass",
            "tub surrounds, laminate counters,",
            "solid-core doors.",
        ]),
    ])


def sheet_a103(pdf):
    unit_sheet(pdf, "A-103", "B", EL_UP, [
        ("Unit B (upper level)", [
            f"Finished floor EL {EL_UP:.1f}, 10'-0\" above",
            "Unit A. Same plan as Unit A so the",
            "kitchens, baths and laundry stack.",
            "3 bedrooms, 3 baths with tubs.",
            "8'-1\" ceilings, sloping to 6'-10\" at the",
            "rear of the wing.",
        ]),
        ("Building totals", [
            "6 bedrooms, 6 baths, 2 kitchens",
            "Garage level (open)             781 sf",
            f"Unit A level                          {FOOTPRINT:,.0f} sf",
            f"Unit B level                          {FOOTPRINT:,.0f} sf",
            "Each unit, net of stair          ±780 sf",
            f"Lot coverage  {FOOTPRINT / LOT_AREA_DEED * 100:.0f} % (50 % maximum)",
        ]),
        ("Separation between units", [
            "IRC R302.3: 1-hour floor/ceiling",
            "between units and 1-hour walls around",
            "the common stair, carried to the roof",
            "deck. Garage ceiling: 5/8 in. Type X",
            "(R302.6). Stair-to-garage door: 20-min.",
            "Sound insulation in the floor and the",
            "bedroom walls is recommended.",
        ]),
        ("Storey count", [
            "R-2 allows 2.5 storeys / 35 ft. The",
            "garage level is over half below the",
            "average adjoining grade, so it should",
            "rate as a basement: two storeys over a",
            "basement. Confirm with Planning.",
            f"Height to mean roof: {EL_MEAN_ROOF - EL_REF:.1f} ft.",
        ]),
    ])


def level_marks(ax, x, levels, x_line=None):
    for el, name in levels:
        if x_line is not None:
            line(ax, [(x_line, el), (x, el)], lw=0.35, color=GREY, ls=(0, (8, 3, 2, 3)), z=2)
        poly(ax, [(x, el), (x + 0.7, el + 0.7), (x + 1.4, el)], fc=INK, lw=0.3, z=8)
        txt(ax, x + 1.9, el + 0.55, f"{name}", size=5.4, ha="left", weight="bold")
        txt(ax, x + 1.9, el - 0.45, f"EL {el:.1f}", size=5.0, ha="left", color=GREY)


def sheet_a201(pdf):
    notes = [
        ("Street (south) elevation", [
            "From Baird Street looking north. Uphill",
            "(442 Baird) is on the left. The pavement",
            "falls ±4 ft across the building.",
        ]),
        ("What you see", [
            "Garage level: an open front with one",
            "steel post, and the common entry",
            "door, all at slab level, no steps.",
            "Units A and B: stacked covered porches",
            "cantilevered 4 ft, sliding doors behind.",
            "Bedrooms are at the rear and sides.",
            "Gable roof, ridge parallel to the street.",
        ]),
        ("Materials (1337.07)", [
            "Fibre-cement or vinyl lap siding over a",
            "masonry-faced concrete base. Roof pitch",
            "to match neighbouring houses.",
        ]),
        ("Height", [
            f"Garage slab                 EL {EL_GAR:.1f}",
            f"Unit A floor                  EL {EL_MAIN:.1f}",
            f"Unit B floor                  EL {EL_UP:.1f}",
            f"Top plate                     EL {EL_PLATE:.1f}",
            f"Ridge                           EL {EL_RIDGE:.1f}",
            f"Zoning height {EL_MEAN_ROOF - EL_REF:.1f} ft to mean roof",
            "level (35 ft maximum).",
        ]),
        ("Not drawn", [
            "East, west and north elevations are",
            "left for the architect.",
        ]),
    ]
    fig, bg = new_sheet("A-201", "Street elevation", "3/16\" = 1'-0\"", notes)
    xl, yl = (-6, 58), (903.5, 957.5)
    left = MARGIN + (SHEET_W - 2 * MARGIN - TB_W - (xl[1] - xl[0]) / FPI) / 2
    ax = plan_axes(fig, left, 0.5, xl, yl, FPI)
    g = [(-6, elev(-6, BY0)), (2, elev(2, BY0)), (9.5, 921.2), (11.1, 920.2), (11.1, EL_GAR), (45.1, EL_GAR),
         (45.1, 917.3), (50, elev(50, BY0)), (58, elev(58, BY0))]
    poly(ax, g + [(58, 903.5), (-6, 903.5)], fc="#efe9e1", ec="none", z=6)
    line(ax, g, lw=1.4, color=INK, z=7)
    ax.fill_between([p[0] for p in g], [p[1] - 1.0 for p in g], [p[1] for p in g], hatch="////", fc="none", ec=EARTH, lw=0, zorder=6, alpha=0.6)
    sx = np.linspace(-6, 58, 30)
    line(ax, [(x, street_el(x)) for x in sx], lw=0.8, color=BLUE, ls=(0, (6, 3)), z=8)
    txt(ax, 49.5, street_el(49.5) - 1.3, "BAIRD ST PAVEMENT (IN FRONT) · FALLS ±11 % EASTWARD", size=5.0, color=BLUE, rot=-6.5)
    rect(ax, BX0, EL_GAR - 1.5, BX1, EL_MAIN, fc="#d9dcdf", ec=INK, lw=1.0, z=3)
    for y in np.arange(EL_GAR - 1.0, EL_MAIN, 0.667):
        line(ax, [(BX0, y), (BX1, y)], lw=0.15, color=GREY, z=3)
    for (a, b) in (DOOR_A, DOOR_B):
        rect(ax, a, EL_GAR, b, EL_GAR + 8.6, fc="#5c6269", ec=INK, lw=0.9, z=4)
    rect(ax, DOOR_A[1], EL_GAR, DOOR_B[0], EL_GAR + 8.6, fc="#1f5fa8", ec=INK, lw=0.6, z=5)
    txt(ax, 19.8, EL_GAR + 4.6, "OPEN GARAGE (NO DOORS)", size=5.4, color=PAPER, z=9)
    txt(ax, 33.0, EL_GAR + 4.6, "OPEN", size=5.0, color=PAPER, z=9)
    rect(ax, ENTRY[0], EL_GAR, ENTRY[1], EL_GAR + 6.67, fc="#dfe7ee", ec=INK, lw=0.9, z=4)
    rect(ax, ENTRY[0], EL_GAR + 6.9, ENTRY[1], EL_GAR + 8.0, fc="#dfe7ee", ec=INK, lw=0.6, z=4)
    txt(ax, 42.4, EL_GAR + 3.3, "ENTRY", size=4.6, z=9, rot=90)
    rect(ax, BX0, EL_MAIN, BX1, EL_PLATE, fc="#fbfaf7", ec=INK, lw=1.0, z=3)
    for y in np.arange(EL_MAIN + 0.5, EL_PLATE, 0.5):
        line(ax, [(BX0, y), (BX1, y)], lw=0.12, color=LIGHT, z=3)
    line(ax, [(BX0, EL_UP), (BX1, EL_UP)], lw=0.5, z=4)
    for el in (EL_MAIN, EL_UP):
        rect(ax, 22, el, 30, el + 6.8, fc="#dfe7ee", ec=INK, lw=0.7, z=4)
        line(ax, [(26, el), (26, el + 6.8)], lw=0.5, z=4)
        rect(ax, 12, el + 2.6, 17, el + 6.8, fc="#dfe7ee", ec=INK, lw=0.7, z=4)
        line(ax, [(14.5, el + 2.6), (14.5, el + 6.8)], lw=0.5, z=4)
        rect(ax, 39.5, el + 3.4, 43, el + 7.2, fc="#dfe7ee", ec=INK, lw=0.7, z=4)
        # cantilevered porch
        rect(ax, 9.5, el - 0.9, 35.5, el, fc="#e9e4d9", ec=INK, lw=0.8, z=10)
        line(ax, [(9.5, el + 3), (35.5, el + 3)], lw=0.8, z=10)
        for x in np.arange(9.9, 35.5, 0.42):
            line(ax, [(x, el + 0.3), (x, el + 3)], lw=0.15, color=GREY, z=9)
        line(ax, [(9.5, el + 0.3), (35.5, el + 0.3)], lw=0.4, z=10)
    rect(ax, BX0 - 1, EL_PLATE - 0.4, BX1 + 1, EL_RIDGE, fc="#c9cdd2", ec=INK, lw=1.0, z=4)
    for y in np.arange(EL_PLATE, EL_RIDGE, 0.55):
        line(ax, [(BX0 - 1, y), (BX1 + 1, y)], lw=0.15, color=GREY, z=4)
    poly(ax, [(9.0, EL_PLATE - 1.0), (36.0, EL_PLATE - 1.0), (36.0, EL_PLATE - 0.2), (9.0, EL_PLATE - 0.2)], fc="#c9cdd2", ec=INK, lw=0.8, z=10)
    txt(ax, 22.5, EL_PLATE - 0.6, "PORCH ROOF", size=4.4, z=11)
    txt(ax, 22.5, EL_MAIN - 0.45, "UNIT A PORCH", size=4.2, z=11)
    txt(ax, 22.5, EL_UP - 0.45, "UNIT B PORCH", size=4.2, z=11)
    for x in (0, 50):
        line(ax, [(x, 906), (x, 950.6)], color=ACCENT, lw=0.8, ls=(0, (9, 2.5, 1.5, 2.5)), z=12)
    txt(ax, 0.5, 949.6, "LOT LINE\n(SW CORNER)", size=4.8, color=ACCENT, ha="left")
    txt(ax, 49.5, 951.6, "LOT LINE (EAST)", size=4.8, color=ACCENT, ha="right")
    txt(ax, -3.2, 934, "442\nBAIRD ST", size=5.2, color=GREY)
    txt(ax, 54.8, 928, "441\nBAIRD ST", size=5.2, color=GREY)
    txt(ax, 5.2, 923.4, "RETAINED BANK\n(WALL ON LOT)", size=4.6, color=GREY)
    level_marks(ax, 51.6, [(EL_MAIN, "UNIT A FLOOR"), (EL_UP, "UNIT B FLOOR"), (EL_PLATE, "TOP PLATE"), (EL_RIDGE, "RIDGE")], x_line=BX1)
    txt(ax, 24, EL_GAR - 1.3, f"GARAGE SLAB  EL {EL_GAR:.1f}", size=5.2, weight="bold", box=True, z=12)
    line(ax, [(20, EL_REF + 35), (BX1 + 3, EL_REF + 35)], color=ACCENT, lw=0.6, ls=(0, (4, 3)), z=12)
    txt(ax, 34, EL_REF + 35.8, f"35' ZONING HEIGHT LIMIT  (EL {EL_REF + 35:.1f}, from reference grade EL {EL_REF:.1f})", size=5.0, color=ACCENT)
    dim(ax, (BX0, EL_RIDGE), (BX1, EL_RIDGE), 1.6, "35'-6\"", size=5.4)
    dim(ax, (47.4, EL_GAR), (47.4, EL_MAIN), 0, "11'-0\"", ext=False, size=5.0)
    dim(ax, (47.4, EL_MAIN), (47.4, EL_UP), 0, "10'-0\"", ext=False, size=5.0)
    dim(ax, (47.4, EL_UP), (47.4, EL_PLATE), 0, "8'-1\"", ext=False, size=5.0)
    scale_bar(ax, -4.5, 905.6, 16, 4, 0.42, size=5.2)
    view_title(ax, -5.4, 954.6, "1", "South (Baird Street) elevation", "Looking north · elevations NAVD88 ft from state LiDAR", 9)
    save(fig, "A-201", pdf)


def section_base(ax, XS, xl, bottom, labels=True):
    """N-S section at plan station XS (through the wing), looking west. Returns rear lot line station."""
    ry = rear_y(XS)
    ys = np.arange(xl[0], xl[1] + 0.5, 1.0)
    eg = [(y, elev(XS, y)) for y in ys]
    st = street_el(XS)
    fg = [(xl[0], elev(XS, xl[0])), (PAVE_S, elev(XS, PAVE_S)), (PAVE_S, st), (PAVE_N, st), (BY0, EL_GAR), (BY0, EL_GAR - 1.5),
          (BY1, EL_GAR - 1.5), (BY1, EL_MAIN - 0.42), (WY1, EL_MAIN - 0.42), (WY1, 927.0)]
    fg += [(y, max(elev(XS, y), 927.0)) for y in np.arange(WY1 + 2, xl[1] + 1, 2)]
    poly(ax, fg + [(xl[1], bottom), (xl[0], bottom)], fc="#efe9e1", ec="none", z=2)
    line(ax, [(xl[0], elev(XS, xl[0])), (PAVE_S, elev(XS, PAVE_S))], lw=1.2, z=7)
    line(ax, [(PAVE_S, st), (PAVE_N, st)], lw=2.6, color="#3a3f45", z=7)
    line(ax, [(PAVE_N, st), (BY0, EL_GAR)], lw=1.4, z=7)
    line(ax, [(WY1, 927.0)] + fg[10:], lw=1.4, z=7)
    line(ax, eg, lw=0.9, color=EARTH, ls=(0, (5, 3)), z=8)
    # garage slab, footings, walls
    rect(ax, BY0, EL_GAR - 0.42, BY1 - 1, EL_GAR, fc=CONC, ec=INK, lw=0.6, z=5)
    rect(ax, BY0, EL_GAR - 0.9, BY1 - 1, EL_GAR - 0.42, fc="#e1ddd4", ec="none", z=4)
    rect(ax, BY0 - 0.9, EL_GAR - 2.5, BY0 + 1.6, EL_GAR - 1.5, fc=CONC, ec=INK, lw=0.6, z=5)       # grade beam at the open front
    rect(ax, BY1 - 1, EL_GAR - 1.5, BY1, EL_MAIN - 1.73, fc=CONC, ec=INK, lw=0.8, z=5)             # rear retaining wall
    rect(ax, BY1 - 5.0, EL_GAR - 2.75, BY1 + 2.0, EL_GAR - 1.5, fc=CONC, ec=INK, lw=0.8, z=5)
    ax.add_patch(plt.Circle((BY1 + 0.6, EL_GAR - 1.1), 0.33, fc=PAPER, ec=BLUE, lw=0.8, zorder=6))
    rect(ax, BY1, EL_GAR - 1.5, BY1 + 1.2, EL_MAIN - 1.2, fc="#dcdfe3", ec="none", z=4, hatch="....")
    rect(ax, BY0, EL_GAR + 8.6, BY0 + 0.67, EL_MAIN - 1.73, fc="#1f5fa8", ec=INK, lw=0.6, z=5)    # steel beam over the open front
    # rear wing: slab on fill, shallow frost wall
    rect(ax, BY1, EL_MAIN - 0.42, WY1 - 1, EL_MAIN, fc=CONC, ec=INK, lw=0.6, z=5)
    rect(ax, WY1 - 1, EL_MAIN - 3.6, WY1, EL_MAIN + 3.0, fc=CONC, ec=INK, lw=0.8, z=5)
    rect(ax, WY1 - 1.6, EL_MAIN - 4.6, WY1 + 0.9, EL_MAIN - 3.6, fc=CONC, ec=INK, lw=0.8, z=5)
    for el in (EL_MAIN, EL_UP):                                                                  # 20 in. floor trusses
        yend = BY1 if el == EL_MAIN else WY1
        rect(ax, BY0, el - 1.73, yend, el, fc="#e9e4d9", ec=INK, lw=0.7, z=5)
        for y in np.arange(BY0 + 1, yend - 1, 2.0):
            line(ax, [(y - 0.8, el - 1.73), (y, el - 0.1), (y + 0.8, el - 1.73)], lw=0.2, color=GREY, z=6)
        rect(ax, 4, el - 1.0, BY0, el, fc="#e9e4d9", ec=INK, lw=0.7, z=6)                         # cantilevered porch
        line(ax, [(4.1, el), (4.1, el + 3), (BY0, el + 3)], lw=0.6, z=6)
    rect(ax, BY0, EL_MAIN, BY0 + 0.5, EL_UP - 1.73, fc=POCHE, z=6)
    rect(ax, BY0, EL_UP, BY0 + 0.5, EL_PLATE, fc=POCHE, z=6)
    rect(ax, WY1 - 0.5, EL_MAIN + 3.0, WY1, EL_UP - 1.73, fc=POCHE, z=6)
    rect(ax, WY1 - 0.5, EL_UP, WY1, EL_PLATE - 1.25, fc=POCHE, z=6)
    rect(ax, BY0 - 0.02, EL_MAIN + 2.7, BY0 + 0.52, EL_MAIN + 6.8, fc=PAPER, ec=INK, lw=0.4, z=7)
    rect(ax, BY0 - 0.02, EL_UP + 2.7, BY0 + 0.52, EL_UP + 6.8, fc=PAPER, ec=INK, lw=0.4, z=7)
    rect(ax, WY1 - 0.52, EL_MAIN + 3.4, WY1 + 0.02, EL_MAIN + 7.0, fc=PAPER, ec=INK, lw=0.4, z=7)
    rect(ax, WY1 - 0.52, EL_UP + 2.4, WY1 + 0.02, EL_UP + 6.0, fc=PAPER, ec=INK, lw=0.4, z=7)
    for el in (EL_MAIN, EL_UP):                                                                  # partitions cut at this station
        top_el = (EL_UP - 1.73) if el == EL_MAIN else EL_PLATE
        rect(ax, 18.0, el, 18.4, top_el, fc=POCHE, z=6)
        rect(ax, 23.5, el, 23.9, top_el, fc=POCHE, z=6)
    ym = (BY0 + BY1) / 2
    top = [(BY0 - 1.2, EL_PLATE - 0.6), (ym, EL_RIDGE), (BY1, EL_PLATE), (WY1 + 1.2, EL_PLATE - 1.55)]
    roof = top + [(WY1 + 1.2, EL_PLATE - 1.05), (BY1, EL_PLATE + 0.55), (ym, EL_RIDGE + 0.6), (BY0 - 1.2, EL_PLATE - 0.1)]
    poly(ax, roof, fc="#c9cdd2", ec=INK, lw=0.8, z=6)
    line(ax, [(BY0, EL_PLATE), (BY1, EL_PLATE), (WY1 - 0.5, EL_PLATE - 1.25)], lw=0.7, z=6)
    poly(ax, [(3.4, EL_PLATE - 0.9), (BY0, EL_PLATE - 0.5), (BY0, EL_PLATE - 0.2), (3.4, EL_PLATE - 0.6)], fc="#c9cdd2", ec=INK, lw=0.6, z=6)
    return ry, st


def sheet_a301(pdf):
    XS = 14.0
    notes = [
        ("Section A-A", [
            "Cut north-south at plan station X = 14 ft,",
            "through stall 1, bath 1 and bedroom 1,",
            "looking west. Dashed brown = existing",
            "ground from the 1 m LiDAR.",
        ]),
        ("What it shows", [
            f"The slab sits at EL {EL_GAR:.1f}, within a foot",
            "of the pavement. The garage front is",
            "open under a steel beam.",
            "The rear wing is not dug out: its floor",
            "is a slab on fill at Unit A level, behind",
            "the garage's rear wall.",
        ]),
        ("Cost drivers visible here", [
            "±8 ft average cut over the garage.",
            "Rear wall retains ±10.5 ft, 14 ft from",
            "386 Forest Ave's lot line at this cut.",
            "Shoring and neighbour monitoring.",
            "Rock depth unknown: borings needed.",
            "Ask the geotech to check state mine",
            "maps for old workings.",
        ]),
        ("Garage clearances", [
            "20'-4\" clear depth, 9'-2\" clear height,",
            "8'-7\" clear under the front beam.",
            "Full-size crew-cab pickups will not fit;",
            "sedans, SUVs and vans will.",
        ]),
        ("Wing foundation", [
            "The wing's footing sits near the garage",
            "wall's backfill. Engineer to place it on",
            "engineered fill or step it down.",
        ]),
    ]
    fig, bg = new_sheet("A-301", "Building section", "3/16\" = 1'-0\"", notes)
    xl, yl = (-24, 47), (904.5, 958)
    left = MARGIN + (SHEET_W - 2 * MARGIN - TB_W - (xl[1] - xl[0]) / FPI) / 2
    ax = plan_axes(fig, left, 0.42, xl, yl, FPI)
    ry, st = section_base(ax, XS, xl, 904.5)
    txt(ax, 42.2, elev(XS, 42.2) + 1.6, "EXISTING GRADE", size=5.0, color=EARTH, rot=14)
    txt(ax, 2.6, elev(XS, 3.2) + 1.6, "EXISTING BANK +\nHOUSE TERRACE\n(REMOVED)", size=4.8, color=EARTH)
    txt(ax, -14, st - 1.2, "BAIRD STREET  ±14' PAVEMENT", size=5.4, weight="bold")
    txt(ax, -14, st - 2.4, f"±EL {st:.1f} at this section", size=4.8, color=GREY)
    txt(ax, 0.4, EL_GAR - 2.2, "APRON", size=4.8, color=GREY)
    txt(ax, BY0 - 2.6, EL_GAR + 4.2, "OPEN FRONT", size=4.6, color=GREY, rot=90)
    cx = 10.4
    carp = [(cx, EL_GAR + 1.0), (cx + 0.3, EL_GAR + 2.6), (cx + 3.2, EL_GAR + 3.0), (cx + 5.0, EL_GAR + 4.8), (cx + 10.4, EL_GAR + 4.9),
            (cx + 12.6, EL_GAR + 3.3), (cx + 15.6, EL_GAR + 2.9), (cx + 16.2, EL_GAR + 1.0)]
    poly(ax, carp, fc="#f2f3f5", ec=FURN, lw=0.6, z=5)
    for wx in (cx + 3.1, cx + 12.8):
        ax.add_patch(plt.Circle((wx, EL_GAR + 1.05), 1.05, fc=PAPER, ec=FURN, lw=0.6, zorder=6))
    txt(ax, 18.5, EL_GAR + 7.0, "OPEN GARAGE", size=6.2, weight="bold")
    txt(ax, 32.5, EL_GAR + 5.0, "UNEXCAVATED", size=5.0, color=EARTH, weight="bold")
    for el, u in ((EL_MAIN, "A"), (EL_UP, "B")):
        txt(ax, 13.2, el + 4.4, f"UNIT {u} · LIVING", size=5.6, weight="bold")
        txt(ax, 20.95, el + 4.4, "BATH 1", size=4.4, color=GREY)
        txt(ax, 29.3, el + 4.4, "BEDROOM 1", size=5.4, weight="bold")
        txt(ax, 1.4, el + 5.2, "PORCH", size=4.6)
    txt(ax, 19, EL_PLATE + 2.0, "ATTIC / TRUSSES · 6:12", size=4.8, color=GREY)
    txt(ax, 38.0, 917.4, "12\" CONC. WALL\n±10.5' retained\nengineered · drained", size=4.8, ha="left")
    line(ax, [(31.4, 918.0), (37.8, 917.8)], lw=0.3)
    txt(ax, 39.6, EL_MAIN - 4.0, "FROST WALL +\nSLAB ON FILL", size=4.6, ha="left")
    line(ax, [(35.6, EL_MAIN - 2.4), (39.4, EL_MAIN - 3.6)], lw=0.3)
    txt(ax, 19, EL_MAIN - 0.85, "1-HR FLOOR/CEILING · 20\" TRUSSES · R-30 · 5/8\" TYPE X BELOW", size=4.2, z=9)
    txt(ax, 19, EL_UP - 0.85, "1-HR FLOOR/CEILING BETWEEN UNITS (IRC R302.3)", size=4.2, z=9)
    for y, lab in ((0, "FRONT LOT LINE"), (ry, "REAR LOT LINE")):
        line(ax, [(y, 906), (y, 952.6)], color=ACCENT, lw=0.8, ls=(0, (9, 2.5, 1.5, 2.5)), z=12)
        txt(ax, y, 953.5, lab, size=4.8, color=ACCENT)
    dim(ax, (0, 908.6), (BY0, 908.6), 0, "8'-0\"", ext=False, size=5.0, color=ACCENT)
    dim(ax, (BY0, 908.6), (BY1, 908.6), 0, "22'-0\"", ext=False, size=5.0)
    dim(ax, (BY1, 908.6), (WY1, 908.6), 0, "5'-0\"", ext=False, size=5.0)
    dim(ax, (WY1, 908.6), (ry, 908.6), 0, f"{ftin(ry - WY1)}", ext=False, size=5.0, color=ACCENT)
    dim(ax, (PAVE_N, 908.6), (0, 908.6), 0, "±7' R.O.W.", ext=False, size=4.8, color=GREY)
    level_marks(ax, -23.4, [(EL_GAR, "GARAGE SLAB"), (EL_MAIN, "UNIT A FLOOR"), (EL_UP, "UNIT B FLOOR"), (EL_PLATE, "TOP PLATE")])
    for el in (EL_GAR, EL_MAIN, EL_UP, EL_PLATE):
        line(ax, [(-22, el), (2.5 if el > EL_GAR else PAVE_N - 0.5, el)], lw=0.3, color=GREY, ls=(0, (8, 3, 2, 3)), z=3)
    line(ax, [(BY0 - 2, EL_REF + 35), (WY1 + 10, EL_REF + 35)], color=ACCENT, lw=0.6, ls=(0, (4, 3)), z=12)
    txt(ax, 22, EL_REF + 35.9, f"35' ZONING HEIGHT LIMIT (EL {EL_REF + 35:.1f})", size=4.8, color=ACCENT)
    dim(ax, (WY1 + 3.0, EL_MAIN), (WY1 + 3.0, EL_UP), 0, "10'-0\"", ext=False, size=4.8, side=-1)
    scale_bar(ax, -22.5, 906.3, 16, 4, 0.42, size=5.2)
    view_title(ax, -23.4, 955.6, "A", "Section A-A", "North-south through the garage and rear wing, looking west", 9)
    save(fig, "A-301", pdf)
