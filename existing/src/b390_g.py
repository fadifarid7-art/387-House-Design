"""390 Forest Ave builder set: cover sheet (G-001) and schedules (A-601)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build390 as b  # noqa: E402
from common import INK, GREY, table  # noqa: E402

INDEX = [("G-001", "Cover: scope, basis of design, sheet index"),
         ("A-101", "Lower flat: floor plan"), ("A-102", "Middle flat: floor plan"), ("A-103", "Upper flat main floor: floor plan"), ("A-104", "Attic: floor plan"),
         ("A-601", "Room, door, cabinet and appliance schedules"),
         ("E-001", "Electrical general notes and legend"), ("E-002", "Electrical load calculations"), ("E-003", "Lighting calculations"),
         ("E-004", "Service, meters, feeders and grounding"), ("E-005", "Panel schedules"),
         ("E-101", "Lower flat: power and lighting"), ("E-102", "Middle flat: power and lighting"),
         ("E-103", "Upper flat main floor: power and lighting"), ("E-104", "Attic: power and lighting"),
         ("M-001", "Mechanical notes, equipment and exhaust schedules"), ("M-002", "Heating and cooling loads"),
         ("M-003", "Air distribution, outdoor units, venting"), ("M-501", "Mechanical details and 3D views"), ("M-101", "Lower flat: HVAC"), ("M-102", "Middle flat: HVAC"), ("M-103", "Upper flat main floor: HVAC"), ("M-104", "Attic: HVAC"),
         ("P-001", "Plumbing and gas notes, fixture schedule, risers"), ("P-101", "Lower flat: plumbing and gas"), ("P-102", "Middle flat: plumbing and gas"),
         ("P-103", "Upper flat main floor: plumbing and gas"), ("P-104", "Attic: plumbing and gas")]


def cover(pdf):
    fig, bg, _ = b.bsheet("G-001", "390 Forest Ave: builder set, 8 bedrooms and 7 baths in three flats", 0, [
        ("Read this first", ["These are layout drawings to price and build", "from, made from a phone 3D scan. They are", "not stamped. Each licensed trade confirms", "sizes and code items for its own work."]),
        ("Flats", ["Lower flat    2 bed  2 bath   rooms 101-112", "Middle flat   2 bed  2 bath   rooms 201-213", "Upper flat    4 bed  3 bath   rooms 301-311", "              and attic rooms 401-407"]),
        ("Colours on the plans", ["Grey   existing, stays", "Red    new walls and doors", "Dashed remove", "Amber  wall the scan missed: verify", "Blue   new plumbing fixtures", "Purple furnace and water heater"])],
        sub="Rear building · all levels")
    bg.text(0.6, 10.2, "390 FOREST AVE, MORGANTOWN WV: BUILDER SET", fontsize=13, fontweight="bold", color=INK, va="center")
    bg.text(0.6, 9.9, "Interior renovation of an existing three-flat house: 8 bedrooms, 7 baths. No exterior work except roof and wall patches where the chimney and vents pass.", fontsize=7, color=GREY, va="center")
    y = b.text_block(bg, 0.6, 9.45, "Scope of work: full gut, everything new", [
        "1  Strip all three flats to the studs and joists: plaster and board, dropped ceilings, flooring, doors, trim, cabinets, all wiring, piping, ducts,",
        "   furnaces, water heaters and fixtures. The outside walls, floor framing, stairs, windows and the grey walls on the plans keep their framing.",
        "2  Remove the chimney from the roof down to the lower flat (confirmed by the owner's photo). Patch roof, floors and ceilings.",
        "3  Lower flat: build bath 2 (room 106); move bedroom 1's wall 9 in.; new closet; mechanical closet 109.",
        "4  Middle flat: build bath 2 (room 206) in the south half of the hall and the chimney space; re-frame bedroom 2's door; new closet; mechanical closet 208.",
        "5  Upper flat main floor: bedroom 3 with a new closet; bedroom 4 (the present furnace room) with a door and a new closet; mechanical closet 307.",
        "6  Attic: private bath A for bedroom 1 and private bath B for bedroom 2; move bedroom 2's door; two closets.",
        "7  All new in every flat: electrical service, panel and wiring; gas furnace with cooling and ducts to every room; gas water heater; water, drain, vent",
        "   and gas piping; 7 baths; 3 kitchens with cabinets and appliances in their present positions; insulation, board, doors, trim and finishes."], fs=6.4, lh=0.165)
    y = b.text_block(bg, 0.6, y - 0.05, "Basis of design: assumptions the builder must confirm", [
        "A  Natural gas is on site. Each flat is taken to have its own gas and electric meter. Meter and service locations are not on the scan.",
        "B  What is there now, all to be removed (inspection report, 9 Oct 2026): three gas forced-air furnaces with ducts (1996, 1997, 2019), three 40 gal gas",
        "   water heaters (2017, 2022, 2022), 100 A panels on an overhead service, no central cooling. Furnace and heater positions today (owner's videos): lower",
        "   flat in the louvered closet by the kitchen (109), middle flat in the closet off bedroom 1 (208), upper flat standing in Room B (new bedroom 4).",
        "   Built 1911: assume lead paint, and test plaster, flooring and pipe wrap for asbestos before demolition.",
        "C  Foundation is stone with a crawl space under part of the house (its access door was stuck). Joist direction and bearing walls are not known. Any wall to be cut is treated as",
        "   bearing until shown otherwise: shore it and size the header.",
        "D  The lower flat's position under the other floors is good to about 12 in. Set out the drain stack on site from the floors above.",
        "E  Walls with an amber edge were missed by the scan and are drawn in to close the outline.",
        "F  The lower flat's living room and kitchen floor is 1'-5\" lower than the rest of that flat. Ceilings there are 6'-10\" to 7'-6\".",
        "G  Lower flat: bedroom 2 has only a small high basement window and bedroom 1 shows none in the scan. Bedrooms need an escape window or door: resolve first.",
        "H  Bedroom windows must open at least 5.7 sf clear, 24 in. high and 20 in. wide, sill no more than 44 in. up. Sizes were not readable in the scan.",
        "I  Fire separation between the flats (walls, floors, and around the new stack and ducts) is to be kept or restored: 5/8 in. type X board, firestop every penetration."], fs=6.4, lh=0.165)
    b.text_block(bg, 0.6, y - 0.05, "General notes", [
        "Dimensions are clear, finish face to finish face, in feet and inches. New partitions: 2x4 at 16 in. o.c.; 2x6 where a tub valve, toilet or a stack is in the wall.",
        "With the walls open: insulate outside walls and the attic slopes, air-seal, and fire-block balloon-framed stud bays at each floor.",
        "Between flats: 5/8 in. type X board on ceilings and on walls shared with the stair, sound batts in the floor, firestop every pipe, duct and cable hole.",
        "Board: 1/2 in. on walls, 5/8 in. type X on ceilings and mechanical closets; cement board at tubs, moisture-resistant board in the rest of each bath.",
        "Closets: one shelf and rod. Doors 6'-8\" high as scheduled. Have the cut and separating attic rafters (inspection report) repaired while the attic is open.",
        "Furniture (queen beds 5'-0\" x 6'-8\", desks, couches) is drawn to show that it fits; it is not part of the work."], fs=6.4, lh=0.165)
    bg.text(8.9, 9.45, "SHEET INDEX", fontsize=6.6, fontweight="bold", color=INK, va="center")
    ye = table(bg, 8.9, 9.3, [0.7, 3.5], [["Sheet", "Title"]] + [[a, t] for a, t in INDEX], fs=5.4, rh=0.14)
    b.text_block(bg, 8.9, ye - 0.3, "Open items the trade checks raised", [
        "1  Lower flat bedrooms need an escape window or outside door (A-101).",
        "2  Panels: 125 A is recommended in all three flats (E-001).",
        "3  Panel A: the lower hall is about 2'-10\" deep; 36 in. clear is needed.",
        "   Measure it or use the deeper west end of the hall (E-101).",
        "4  Lower flat ceilings are too low for a soffit: ducts in joist space (M-101).",
        "5  Exhaust caps on the east wall: verify grade and the stair. Line",
        "   sets wait for the deck area's size (M-001, M-003).",
        "6  Middle flat dryer: heat-pump, no vent; hood recirculating (M-102).",
        "7  Middle bath 2 toilet drain crosses joists on its way to stack S1: fur",
        "   the lower flat ceiling there or shift the toilet (P-102).",
        "8  Upper kitchen drain runs 14 ft to stack S2: 3 1/2 in. of fall (P-103).",
        "9  Stacks S2 to S4 offset 2 to 6 in. between floors: set out on site (P-001).",
        "10 Lower bath 2 tub valve has no access from behind: use a valve",
        "   serviced from the front (P-101)."], fs=5.9, lh=0.15)
    b.save(fig, "G-001", pdf)


def schedules(pdf):
    fig, bg, _ = b.bsheet("A-601", "Schedules: rooms, new doors, cabinets and appliances", 0, [
        ("Notes", ["Room sizes are clear sizes from the scan,", "good to about 2 in.", "new room = built or re-shaped in this work.", "Every room is gutted and refinished.", "Appliance openings: confirm against the", "units bought before cabinets are ordered."])],
        sub="Rear building · all levels")
    bg.text(0.6, 10.2, "ROOM SCHEDULE", fontsize=9, fontweight="bold", color=INK, va="center")
    rows = [["No.", "Room", "Level", "Clear size", "Ceiling", "Work"]]
    for fl in (3, 4, 5, 6):
        for r in b.LV[fl]["rooms"]:
            if r["kind"] == "closet" and not r["new"]: continue
            rows.append([r["no"], r["name"] if r["kind"] != "closet" else "Closet", b.LV[fl]["name"].split(",")[0].split(" (")[0], r["size"] or "-", r["ceil"] or "-", "new room" if r["new"] else "same room, gutted"])
    half = (len(rows) + 1) // 2
    table(bg, 0.6, 9.95, [0.45, 1.5, 0.95, 2.1, 0.6, 0.6], rows[:half], fs=5.6, rh=0.17)
    table(bg, 7.0, 9.95, [0.45, 1.5, 0.95, 2.1, 0.6, 0.6], [rows[0]] + rows[half:], fs=5.6, rh=0.17)
    y = 9.95 - 0.17 * (half + 1) - 0.35
    bg.text(0.6, y, "NEW DOOR SCHEDULE", fontsize=9, fontweight="bold", color=INK, va="center")
    d = [["No.", "Location", "Size / type", "Notes"]]
    for fl in (3, 4, 5, 6):
        seen = set()
        for x in b.LV[fl]["doors"]:
            if x[0] in seen or not x[7]: continue
            seen.add(x[0]); d.append([x[0], x[8], x[7], "solid core, self-closing, weather-stripped" if "Mechanical" in x[8] else "hollow core, passage or privacy set"])
        for x in b.LV[fl]["bifolds"]:
            d.append([x[0], x[7], x[6], "bifold pair, full height 6'-8\""])
    yd = table(bg, 0.6, y - 0.25, [0.45, 2.1, 1.5, 2.3], d, fs=5.6, rh=0.17)
    bg.text(7.0, y, "KITCHENS: NEW CABINETS AND APPLIANCES (present positions kept)", fontsize=9, fontweight="bold", color=INK, va="center")
    k = [["Flat", "Item", "Size allowed on plan", "Notes"],
         ["Lower", "Refrigerator", "33 in. wide x 30 in. deep space", "ceiling here is 6'-10\": check the unit's height"],
         ["Lower", "Electric range", "30 in.", "new recirculating hood; range is on an inside wall"],
         ["Lower", "Sink base + dishwasher", "36 in. sink base, 24 in. dishwasher, 25 in. top", "one straight run 10'-5\": sink, DW, range, refrigerator"],
         ["Middle", "Refrigerator", "36 in. wide x 30 in. deep space", "end of the long run"],
         ["Middle", "Electric range", "30 in.", "on the outside wall: new hood ducted out"],
         ["Middle", "Base cabinets, sink, dishwasher", "L-shape: 4'-0\" base, 24 in. DW, 36 in. sink base in the corner", "sink is under the window on the outside wall"],
         ["Upper", "Refrigerator", "30 in. wide x 30 in. deep space (36 in. does not fit)", "beside the window"],
         ["Upper", "Gas range", "30 in.", "on the outside wall: hood ducted out"],
         ["Upper", "Base cabinets, sink, dishwasher", "L-shape: 36 in. sink base, 24 in. DW, 6 ft of base", "kitchen is 7'-2\" wide: 5 ft clear in front"],
         ["All", "Washer and dryer", "27 in. wide each, side by side", "present positions; dryers electric"],
         ["All", "Wall cabinets", "12 in. deep, 30 in. high over the base runs", "18 in. above the counter; hood over range"]]
    table(bg, 7.0, y - 0.25, [0.6, 1.3, 2.5, 1.9], k, fs=5.4, rh=0.17)
    b.text_block(bg, 0.6, yd - 0.3, "Bedrooms: what fits", [
        "Every bedroom is drawn with a queen bed (5'-0\" x 6'-8\"), a desk (2'-0\" x 4'-0\", or 2'-0\" x 3'-0\" where noted) and a closet.",
        "Bedroom 4 (upper flat, 7'-6\" wide) and lower flat bedroom 2 are the tightest: the bed goes against a wall with one side clear.",
        "Bedroom 1 in the attic keeps its existing 2'-0\" doorway: check that the bed and mattress can be carried in, or use a split box spring."], fs=6.2, lh=0.16)
    b.save(fig, "A-601", pdf)


SHEETS = [("G-001", "Cover", cover), ("A-601", "Schedules", schedules)]
