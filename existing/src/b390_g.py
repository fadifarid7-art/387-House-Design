"""390 Forest Ave builder set: cover sheet (G-001) and schedules (A-601)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build390 as b  # noqa: E402
from common import INK, GREY, table  # noqa: E402

INDEX = [("G-001", "Cover: scope, basis of design, sheet index"),
         ("A-101", "Lower flat: floor plan"), ("A-102", "Middle flat: floor plan"), ("A-103", "Upper flat main floor: floor plan"), ("A-104", "Attic: floor plan"),
         ("A-601", "Room, door, cabinet and appliance schedules"),
         ("E-001", "Electrical notes, legend, panel schedules"), ("E-101", "Lower flat: power and lighting"), ("E-102", "Middle flat: power and lighting"),
         ("E-103", "Upper flat main floor: power and lighting"), ("E-104", "Attic: power and lighting"),
         ("M-001", "HVAC notes, equipment schedule, air balance"), ("M-101", "Lower flat: HVAC"), ("M-102", "Middle flat: HVAC"), ("M-103", "Upper flat main floor: HVAC"), ("M-104", "Attic: HVAC"),
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
    y = b.text_block(bg, 0.6, 9.45, "Scope of work", [
        "1  Remove the chimney from the roof down to the lower flat (confirmed as a chimney by the owner's photo). Patch roof, floors and ceilings.",
        "   Before removal, find what vents into it now and take those appliances out of service.",
        "2  Lower flat: build bath 2 (room 106) in place of two closets; move bedroom 1's wall 9 in.; new closet; mechanical closet 109.",
        "3  Middle flat: build bath 2 (room 206) in the south half of the hall and the chimney space; re-frame bedroom 2's door; new closet; mechanical closet 208.",
        "4  Upper flat main floor: bedroom 3 (old Room A) with a new closet; bedroom 4 (old Room B) with a door and a new closet; mechanical closet 307.",
        "5  Attic: private bath A for bedroom 1 and private bath B for bedroom 2; move bedroom 2's door; two closets.",
        "6  New in every flat: gas furnace with cooling and ducts to every room, gas water heater, electrical panel and wiring to current rules,",
        "   water, drain and gas piping for the new baths and equipment. Existing kitchens and the three existing baths stay where they are."], fs=6.4, lh=0.165)
    y = b.text_block(bg, 0.6, y - 0.05, "Basis of design: assumptions the builder must confirm", [
        "A  Natural gas is available and each flat has, or will have, its own gas meter and its own electric meter. Meter and service locations are not known.",
        "B  Heating and cooling: one ducted gas furnace with cooling coil per flat, in that flat's mechanical closet. What heats the house today is not known.",
        "C  Joist direction, bearing walls and what is below the lower flat (basement, cellar or crawl space) are not known. Any wall to be cut is treated as",
        "   bearing until shown otherwise: shore it and size the header.",
        "D  The lower flat's position under the other floors is good to about 12 in. Set out the drain stack on site from the floors above.",
        "E  Walls with an amber edge were missed by the scan and are drawn in to close the outline.",
        "F  The lower flat's living room and kitchen floor is 1'-5\" lower than the rest of that flat. Ceilings there are 6'-10\" to 7'-6\".",
        "G  Lower flat bedroom 1 shows no window in the scan. A bedroom needs an escape window: check before work starts.",
        "H  Bedroom windows must open at least 5.7 sf clear, 24 in. high and 20 in. wide, sill no more than 44 in. up. Sizes were not readable in the scan.",
        "I  Fire separation between the flats (walls, floors, and around the new stack and ducts) is to be kept or restored: 5/8 in. type X board, firestop every penetration."], fs=6.4, lh=0.165)
    b.text_block(bg, 0.6, y - 0.05, "General notes", [
        "Dimensions are clear, finish face to finish face, in feet and inches. New partitions: 2x4 at 16 in. o.c. with 1/2 in. board; 2x6 where a tub valve, toilet or the stack is in the wall.",
        "Baths: cement board behind tub surrounds, moisture-resistant board elsewhere, slip-resistant floor, 60 in. alcove tub, exhaust fan to outside.",
        "Closets: one shelf and rod. Doors 6'-8\" high; bedroom and bath doors as scheduled. Smoke and CO alarms as shown on the electrical sheets.",
        "Furniture (queen beds 5'-0\" x 6'-8\", desks 2'-0\" x 4'-0\", couches 7'-0\") is drawn to show that it fits; it is not part of the work."], fs=6.4, lh=0.165)
    bg.text(8.9, 9.45, "SHEET INDEX", fontsize=6.6, fontweight="bold", color=INK, va="center")
    table(bg, 8.9, 9.3, [0.7, 3.5], [["Sheet", "Title"]] + [[a, t] for a, t in INDEX], fs=5.9, rh=0.185)
    b.save(fig, "G-001", pdf)


def schedules(pdf):
    fig, bg, _ = b.bsheet("A-601", "Schedules: rooms, new doors, cabinets and appliances", 0, [
        ("Notes", ["Room sizes are clear sizes from the scan,", "good to about 2 in.", "NEW = built or changed in this work.", "Appliance openings: confirm against the", "units bought before cabinets are ordered."])],
        sub="Rear building · all levels")
    bg.text(0.6, 10.2, "ROOM SCHEDULE", fontsize=9, fontweight="bold", color=INK, va="center")
    rows = [["No.", "Room", "Level", "Clear size", "Ceiling", "Work"]]
    for fl in (3, 4, 5, 6):
        for r in b.LV[fl]["rooms"]:
            if r["kind"] == "closet" and not r["new"]: continue
            rows.append([r["no"], r["name"] if r["kind"] != "closet" else "Closet", b.LV[fl]["name"].split(",")[0].split(" (")[0], r["size"] or "-", r["ceil"] or "-", "NEW" if r["new"] else "existing"])
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
    bg.text(7.0, y, "KITCHENS: CABINETS AND APPLIANCES (existing positions kept)", fontsize=9, fontweight="bold", color=INK, va="center")
    k = [["Flat", "Item", "Size allowed on plan", "Notes"],
         ["Lower", "Refrigerator", "36 in. wide x 30 in. deep space", "ceiling here is 6'-10\": check the unit's height"],
         ["Lower", "Gas range", "30 in.", "recirculating hood; range is on an inside wall"],
         ["Lower", "Base cabinets + sink", "18 in. base + 36 in. sink base, 25 in. top", "one straight run 10'-5\" long"],
         ["Middle", "Refrigerator", "36 in. wide x 30 in. deep space", "end of the long run"],
         ["Middle", "Gas range", "30 in.", "on the outside wall: hood ducted out"],
         ["Middle", "Base cabinets + sink", "L-shape: 8'-2\" + 3'-6\" of base, 36 in. sink base", "opening behind the counter treated as a window"],
         ["Upper", "Refrigerator", "30 in. wide x 30 in. deep space (36 in. does not fit)", "beside the window"],
         ["Upper", "Gas range", "30 in.", "on the outside wall: hood ducted out"],
         ["Upper", "Base cabinets + sink", "L-shape: 7'-2\" + 5'-8\" of base, 36 in. sink base", "kitchen is 7'-2\" wide: 5 ft clear in front"],
         ["All", "Washer and dryer", "27 in. wide each, side by side", "existing positions; dryers electric"],
         ["All", "Wall cabinets", "12 in. deep, 30 in. high over the base runs", "18 in. above the counter; hood over range"]]
    table(bg, 7.0, y - 0.25, [0.6, 1.3, 2.5, 1.9], k, fs=5.4, rh=0.17)
    b.text_block(bg, 0.6, yd - 0.3, "Bedrooms: what fits", [
        "Every bedroom is drawn with a queen bed (5'-0\" x 6'-8\"), a desk (2'-0\" x 4'-0\", or 2'-0\" x 3'-0\" where noted) and a closet.",
        "Bedroom 4 (upper flat, 7'-6\" wide) and lower flat bedroom 2 are the tightest: the bed goes against a wall with one side clear.",
        "Bedroom 1 in the attic keeps its existing 2'-0\" doorway: check that the bed and mattress can be carried in, or use a split box spring."], fs=6.2, lh=0.16)
    b.save(fig, "A-601", pdf)


SHEETS = [("G-001", "Cover", cover), ("A-601", "Schedules", schedules)]
