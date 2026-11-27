"""390 Forest Ave builder set: plan model (walls, doors, rooms, fixtures, furniture) and the drawing framework.
Coordinates: building frame, feet. x runs north, y runs west. Scale on the sheets: 1/4 in. = 1 ft (4 ft per inch)."""
import math
import os

import numpy as np
from matplotlib.patches import Arc, Ellipse, Rectangle, Polygon as MPoly
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

import draw_existing as de
import sheetx as sx
from sheetx import HERE, W, H, MG, TB, sheet, save
from common import INK, GREY, LIGHT, PAPER, ftin, table, plt

FPI = 4.0                      # 1/4 in. = 1 ft
EXW = "#9aa0a8"; NEWW = "#b3261e"; FIXE = "#b9770e"; FXN = "#1f5fa8"; FXE = "#6b7480"; MECHC = "#6a2c91"; FURN = "#7a5a2a"
T4, T6 = 1 / 3, 0.5             # drawn thickness of a 2x4 and a 2x6 wall (ft); matches the scanned walls so lines meet cleanly
RANGE_FUEL = {3: "electric", 4: "electric", 5: "gas"}     # from the owner's photos and the inspection report
EXISTING = dict(  # home inspection report, Oasis Home Inspections, 9 Oct 2026, and owner's photos
    built=1911, type="triplex, 7 bedrooms, 3 baths", foundation="stone; finished lower level plus a crawl space (access door stuck)",
    heat="three gas forced-air furnaces with ductwork and ceiling registers (made 1996, 1997, 2019); no central cooling; window units",
    water="three 40 gal gas water heaters (made 2017, 2022, 2022): no pans, no expansion tanks, relief pipes short",
    power="overhead service; 100 A 120/240 V panels (General Electric, Murray); some ungrounded receptacles, open splices",
    kitchens="dishwasher in every kitchen; electric ranges in the lower and middle flats, gas range in the upper flat; no range hoods",
    upper="the upper flat's furnace and water heater stand in the west end of Room B (new bedroom 4): they move to closet 307",
    equipment="owner's videos: lower flat furnace closet with louvered doors beside the kitchen (room 109); middle flat furnace and water heater in the closet off bedroom 1 (room 208); a fireplace mantel on the chimney wall of old Room A",
    attic="rafters cut or separated in places; roof flashing lifted", lower="bedroom 2's only window is a small high basement window")
STACK = (17.3, 8.9)            # new 3 in. drain stack in the old chimney shaft, same spot on every level
CHIMNEY = (15.8, 6.2, 18.3, 9.3)


def V(x, y0, y1, t=T4): return (x - t / 2, min(y0, y1), x + t / 2, max(y0, y1))
def Hh(y, x0, x1, t=T4): return (min(x0, x1), y - t / 2, max(x0, x1), y + t / 2)


def room(no, name, kind, rects, size, ceil, lab=None, new=False, disp=None, compact=False):
    """disp: shorter name to print on the plan; compact: two-line label for a tight room."""
    r0 = rects[0]
    return dict(no=no, name=name, kind=kind, rects=rects, size=size, ceil=ceil, lab=lab or ((r0[0] + r0[2]) / 2, (r0[1] + r0[3]) / 2), new=new, disp=disp, compact=compact)


LV = {
    3: dict(name="Lower flat", view=((-3.5, 36.1), (-3, 30)), stairs=[],
            cut=[(30.25, 4.23, 30.58, 6.89), (16.09, 13.5, 16.42, 15.6)],     # walled-up openings: old laundry outside door (scan), furnace closet door (owner's video; position to verify)
            # hall south wall rebuilt with its hall face at y = 9.72 (the existing jamb of the bedroom 1 door): hall 3'-0" clear
            ap=[(11.95, 1.6, 11.95, 2.8, -1), (24.24, 2.8, 24.24, 4.0, -1)],
            demo=[(12.85, 0.95, 13.35, 9.56), (13.1, 6.1, 16.5, 6.6), (16.0, 6.3, 16.5, 9.3), (15.9, 3.2, 17.45, 6.65), (17.4, 0.95, 18.4, 9.5), (12.6, 9.2, 24.2, 9.95),
                  (7.3, 26.0, 8.3, 26.75), (20.74, 13.45, 21.14, 15.75), (27.2, 12.75, 29.7, 13.15), (24.63, 4.08, 30.6, 4.56),
                  (26.0, 13.13, 26.45, 16.75), (23.9, 15.8, 30.25, 16.75)],
            new=[V(12.2, 0.61, 9.72), Hh(0.78, 12.03, 13.3), V(17.7, 0.61, 9.72, T6), Hh(9.55, 12.03, 21.07), Hh(9.55, 24.07, 24.5), Hh(10.43, 1.62, 2.3), Hh(10.43, 6.9, 7.94), V(7.77, 10.43, 12.78),
                 (24.63, 1.97, 25.25, 4.8), (30.25, 2.14, 30.79, 4.48), (30.25, 4.23, 30.58, 6.89), (16.09, 13.5, 16.42, 15.6), V(24.46, 9.55, 12.95)],
            fix=[Hh(26.94, 19.0, 21.1), V(20.94, 26.2, 26.94), Hh(12.95, 20.94, 21.6), Hh(12.95, 24.1, 27.2)],
            doors=[("100", "v", 0.93, 18.54, 21.4, "lo", 1, "3'-0\" x 6'-8\"", "Flat entrance (existing: verify)"),
                   ("107", "v", 13.1, 9.72, 12.26, "hi", -1, "2'-6\" x 6'-8\"", "Bedroom 1 (existing opening)"),
                   ("101", "v", 12.2, 6.5, 9.0, "hi", 1, "2'-6\" x 6'-8\"", "Bath 1, from bedroom 1"),
                   ("102", "h", 12.95, 21.6, 24.1, "hi", 1, "2'-6\" x 6'-8\"", "Bedroom 2, from the hall"),
                   ("103", "h", 9.55, 21.07, 24.07, "hi", -1, "3'-0\" x 6'-8\"", "Laundry / mech., solid core"),
                   ("106", "h", 12.95, 27.2, 29.7, "hi", -1, "2'-6\" x 6'-8\"", "Bath 2, from bedroom 2")],
            bifolds=[("104", "h", 10.43, 2.3, 6.9, -1, "4'-7\" bifold", "Closet, bedroom 1"), ("105", "v", 20.94, 13.45, 15.75, 1, "2'-4\" bifold", "Closet, bedroom 2")],
            tagpos={"105": (20.15, 15.2)},
            rooms=[room("101", "Living room", "living", [(1.1, 13.12, 12.93, 26.77)], "11'-10\" x 13'-8\"", "7'-6\"", (7.0, 18.6)),
                   room("102", "Kitchen", "kitchen", [(13.27, 16.31, 20.77, 26.77)], "7'-6\" x 10'-5\"", "6'-10\"", (15.6, 21.5)),
                   room("103", "Bedroom 1", "bed", [(1.62, 0.95, 12.03, 10.26), (7.94, 10.26, 12.93, 12.78), (12.03, 9.72, 12.93, 10.26)], "10'-5\" x 9'-4\" + entry", "6'-10\"", (8.58, 6.3), True),
                   room("104", "Bedroom 2", "bed", [(21.11, 13.12, 30.25, 26.07)], "9'-2\" x 12'-11\"", "7'-1\"", (24.6, 17.6), True),
                   room("105", "Laundry / mechanical", "mech", [(17.95, 2.4, 24.29, 9.38)], "6'-4\" x 7'-0\"", "7'-0\"", (22.5, 5.9), True, disp="LAUNDRY / MECH.", compact=True),
                   room("106", "Bath 1 (bedroom 1)", "bath", [(12.37, 0.95, 17.45, 9.38)], "5'-1\" x 8'-5\"", "7'-0\"", (13.65, 5.3), True, disp="BATH 1"),
                   room("107", "Hall", "hall", [(13.27, 9.72, 24.29, 12.78), (13.27, 12.78, 16.08, 16.14)], "3'-0\" wide", "7'-0\"", (18.2, 11.4)),
                   room("108", "Bath 2 (bedroom 2)", "bath", [(24.63, 4.64, 30.25, 12.78), (25.25, 2.14, 30.25, 4.64)], "5'-7\" x 8'-2\" + alcove", "6'-10\"", (28.65, 8.6), True, disp="BATH 2"),
                   room("109", "Closet (BR 2)", "closet", [(16.42, 13.12, 20.77, 15.97)], "", "", (18.75, 14.55), True),
                   room("112", "Closet (BR 1)", "closet", [(1.62, 10.6, 7.6, 12.78)], "", "", (4.6, 11.9), True)],
            fx=[("tub", 12.41, 0.95, 17.41, 3.45, True), ("wc", 17.45, 5.0, "x-", True), ("van", 15.7, 6.4, 17.45, 8.4, True),
                ("tub", 25.25, 2.14, 30.25, 4.64, True), ("wc", 24.63, 6.4, "x+", True), ("van", 24.63, 8.3, 26.38, 11.3, True),
                ("fridge", 18.27, 16.4, 20.77, 19.15), ("range", 18.6, 19.15, 20.77, 21.65), ("dw", 18.69, 21.65, 20.77, 23.65), ("sinkbase", 18.69, 23.65, 20.77, 26.65),
                # mechanical: all three units along the west (wet) wall, fronts to a 3'-9" aisle; panel on the outside (south) wall
                ("furnace", 18.05, 2.6, 20.47, 4.06), ("wh", 18.97, 5.2), ("wdstack", 17.95, 6.4, 20.53, 8.8), ("panel", 21.6, 2.4, 22.85, 2.4, 1)],
            furn=[("bed", 4.6, 0.95, "y+"), ("night", 7.2, 0.95, 8.7, 2.45), ("desk", 10.03, 2.95, 12.03, 6.45), ("dresser", 8.0, 11.28, 10.4, 12.78),
                  ("bed", 25.4, 26.07, "y-"), ("desk", 28.25, 16.0, 30.25, 20.0), ("dresser", 21.11, 16.5, 22.61, 19.5),
                  ("couch", 9.4, 19.5, 12.4, 26.5, "x+"), ("tv", 1.1, 21.8, 2.5, 26.3), ("ctable", 5.0, 22.3, 7.0, 25.7), ("table", 4.0, 13.6, 9.0, 16.6)],
            lead={3: (17.7, 2.2), 8: (30.42, 5.8), 15: (30.6, 2.4), 17: (16.25, 14.55)},
            notes=[(1, (13.7, 2.2), "Bath 1, private to bedroom 1: 60 in. tub, toilet, 24 in. vanity. Built where two closets and the chimney base were. Door opens back against the hall wall."),
                   (2, (11.2, 7.75), "New wall 11 in. inside the old one; old wall out. Tub valve at this end; access panel AP on the bedroom side, kept clear of furniture."),
                   (3, (16.3, 2.2), "2x6 wet wall with drain stack S (circle). Chimney base removed; patch the floor."),
                   (4, (2.5, 11.7), "New closet for bedroom 1, 4'-7\" bifold."),
                   (5, (22.2, 4.7), "Laundry / mechanical (the old bath): furnace, water heater and stacked washer-dryer along the west wall, each with 30 in. clear in front on a 3'-9\" aisle. New electrical panel on the outside wall, 30 x 36 in. kept clear. 5/8 in. type X board. No sink."),
                   (6, (22.3, 10.45), "New 3'-0\" solid door (34 in. clear): a 27 in. washer, the furnace and the water heater fit through. It opens back against the east wall. Hall wall rebuilt in one straight line; hall 3'-0\" clear."),
                   (7, (28.75, 6.3), "Bath 2, private to bedroom 2 (the old laundry): toilet, 36 in. vanity; the old storage closet becomes the 60 in. tub alcove, 2x6 wet wall, access panel AP on the laundry side. Door opens back against the outside wall. The old electrical panel here is removed."),
                   (8, (31.6, 5.8), "Old laundry outside door closed up and insulated (patch outside)."),
                   (9, (23.6, 11.9), "Old laundry doorway walled up."),
                   (10, (17.15, 14.85), "Old furnace closet becomes bedroom 2's closet: 2'-4\" bifold cut in from the bedroom (panels stack at the north side). The fridge stands against the other side of its north wall; that wall stays."),
                   (11, (25.0, 14.2), "Bedroom 2 entrance: new 2'-6\" door from the hall; it can fold back flat against the wall. Wall each side not in the scan: verify."),
                   (12, (27.3, 17.4), "Old closet walls removed: bedroom 2 is one room, and bath 2 opens straight off it."),
                   (13, (29.1, 25.0), "Small high basement window only (photo): not an escape window. Bedroom 2 needs a larger window or an outside door."),
                   (14, (29.1, 22.6), "Door on this wall: closet or outside door? Verify."),
                   (15, (31.6, 1.2), "Meter socket outside this corner (owner). New feeders run from it to the new panel in each flat."),
                   (16, (2.6, 17.6), "Flat entrance. Every door is new and drawn with its swing; check each on site."),
                   (17, (14.7, 14.55), "Furnace closet door walled up (position from the video: verify).")],
            dims=[(12.37, 3.85, 17.45, 3.85, 0.72), (15.0, 0.95, 15.0, 9.38, 0.8), (1.62, 8.6, 12.03, 8.6, 0.45), (24.63, 5.2, 30.25, 5.2, 0.62), (27.0, 4.64, 27.0, 12.78, 0.5),
                  (17.95, 9.09, 24.29, 9.09, 0.2), (20.8, 2.4, 20.8, 9.38, 0.72), (16.42, 13.6, 20.77, 13.6), (21.11, 15.7, 30.25, 15.7, 0.5), (30.0, 13.12, 30.0, 26.07, 0.62)]),
    4: dict(name="Middle flat", view=((-2.5, 37.1), (-3, 30)), cut=[(31.0, 22.6, 31.45, 25.6)],
            ap=[(16.9, 9.25, 18.1, 9.25), (10.4, 18.9, 11.6, 18.9)],
            stairs=[(20.6, 24.75, 24.6, 27.3, "x-", "UP"), (17.2, 21.5, 19.6, 24.5, "y-", "UP")],
            demo=[(10.75, 6.2, 15.7, 6.75), (15.1, 6.2, 15.75, 9.9), (15.2, 9.3, 17.3, 9.9), (31.7, 0.56, 33.6, 3.8), (6.2, 25.3, 8.3, 25.8), (10.35, 7.75, 10.85, 12.8), (16.2, 17.33, 18.87, 17.73), (15.95, 0.56, 16.35, 3.25), (10.39, 5.9, 10.79, 8.4), (5.77, 16.2, 6.17, 18.4)],
            new=[Hh(8.88, 10.4, 18.73, T6), V(10.59, 8.4, 9.3), V(10.59, 11.8, 12.8), Hh(15.64, 0.05, 0.75), Hh(15.64, 5.1, 5.97), Hh(3.44, 16.0, 18.9), V(12.45, 13.64, 16.6)],
            fix=[V(34.76, 0.2, 5.6), Hh(0.37, 32.2, 34.93), Hh(26.0, 6.2, 15.45), V(15.28, 21.3, 26.17), V(31.23, 16.1, 17.9), Hh(0.37, 16.2, 18.95)],
            doors=[("201", "v", 10.59, 9.3, 11.8, "lo", -1, "2'-6\" x 6'-8\"", "Bedroom 2"), ("202", "v", 10.59, 5.9, 8.4, "hi", 1, "2'-6\" x 6'-8\"", "Bath 2, from bedroom 2"),
                   ("205", "v", 5.97, 16.2, 18.4, "hi", -1, "2'-2\" x 6'-8\"", "Bath 1, from bedroom 1"),
                   ("203", "h", 17.53, 16.2, 18.87, "lo", -1, "2'-8\" x 6'-8\"", "Mechanical, solid core")],
            bifolds=[("204", "h", 15.64, 0.75, 5.1, 1, "4'-4\" bifold", "Closet, bedroom 1")],
            rooms=[room("201", "Living room", "living", [(19.07, 0.54, 34.59, 11.4), (22.17, 11.4, 31.06, 13.64)], "15'-6\" x 10'-10\" + dining", "8'-8\"", (29.0, 8.6)),
                   room("202", "Kitchen", "kitchen", [(19.86, 13.64, 31.06, 20.72)], "11'-2\" x 7'-1\"", "7'-4\"", (25.5, 16.6)),
                   room("203", "Bedroom 1", "bed", [(0.05, 18.85, 15.11, 25.83), (0.05, 15.81, 5.8, 18.85), (12.62, 17.7, 15.11, 18.85)], "15'-0\" x 7'-0\" + 5'-9\" x 3'-0\"", "7'-8\"", (10.6, 23.6)),
                   room("204", "Bedroom 2", "bed", [(0.05, 0.54, 10.42, 13.3)], "10'-4\" x 12'-9\"", "8'-8\"", (6.8, 2.2)),
                   room("205", "Bath 1 (bedroom 1)", "bath", [(6.14, 13.64, 12.28, 18.51)], "6'-2\" x 5'-0\"", "7'-4\"", (8.3, 17.4), True),
                   room("206", "Bath 2 (bedroom 2)", "bath", [(10.76, 3.61, 18.73, 8.61)], "8'-0\" x 5'-0\"", "8'-0\"", (13.6, 7.3), True),
                   room("207", "Hall", "hall", [(10.76, 9.15, 16.83, 13.3), (16.83, 9.15, 18.7, 11.4)], "6'-1\" x 4'-2\"", "7'-0\"", (13.8, 11.9), True),
                   room("208", "Mechanical", "mech", [(15.45, 17.7, 19.52, 21.29)], "4'-1\" x 3'-7\"", "", (17.5, 20.8), True),
                   room("209", "Laundry", "laundry", [(17.17, 11.77, 22.0, 13.47)], "", "", (19.6, 14.9)),
                   room("210", "Passage", "hall", [(12.62, 13.64, 19.5, 17.36)], "", "7'-4\"", (15.6, 15.6)),
                   room("211", "Clo.", "closet", [(10.76, 0.54, 18.73, 3.27)], "", "", (14.7, 1.9), True),
                   room("212", "Clo.", "closet", [(0.05, 13.64, 5.8, 15.47)], "", "", (2.9, 14.5), True),
                   room("213", "Stair hall (upper flat)", "stair", [(19.86, 21.06, 31.06, 27.38)], "", "8'-9\"", (26.5, 23.2))],
            fx=[("tub", 16.23, 3.61, 18.73, 8.61, True), ("wc", 14.6, 3.61, "y+", True), ("van", 11.2, 3.61, 13.2, 5.36, True),
                ("tub", 9.78, 13.58, 12.28, 18.58, True), ("wc", 8.53, 13.64, "y+", True), ("van", 6.14, 13.64, 7.3, 15.97, True),
                ("fridge", 19.9, 18.22, 22.9, 20.72), ("dw", 22.9, 18.64, 24.9, 20.72), ("base", 24.9, 18.64, 25.9, 20.72), ("sinkbase", 25.9, 18.64, 28.9, 20.72), ("base", 28.9, 18.64, 31.06, 20.72),
                ("base", 28.98, 17.7, 31.06, 18.64), ("range", 28.9, 15.2, 31.06, 17.7),
                ("washer", 17.2, 11.8, 19.5, 14.2), ("dryer", 19.6, 11.8, 21.9, 14.2), ("furnace", 15.6, 18.0, 17.06, 20.33), ("wh", 18.5, 19.3)],
            furn=[("bed", 0.05, 6.9, "x+"), ("night", 0.05, 9.5, 1.55, 11.0), ("desk", 1.0, 11.3, 5.0, 13.3), ("dresser", 0.05, 0.54, 1.55, 3.54),
                  ("bed", 3.0, 25.83, "y-"), ("desk", 6.5, 23.83, 10.5, 25.83), ("dresser", 11.5, 24.33, 14.5, 25.83),
                  ("couch", 19.2, 2.0, 22.2, 9.0, "x-"), ("tv", 33.2, 1.0, 34.59, 5.5), ("ctable", 24.5, 3.5, 26.5, 7.5), ("table", 23.0, 11.6, 28.0, 14.6)],
            notes=[(1, (14.6, 8.88), "New 2x6 wall: bath 2, private to bedroom 2 (door from the bedroom only). Tub valve in this wall; access panel AP on the hall side."), (2, (17.0, 6.5), "Chimney and the old inner hall walls removed. Patch floor and ceiling."),
                   (3, (10.59, 10.5), "4'-11\" opening re-framed for a 2'-6\" door."), (4, (2.9, 15.64), "New closet front, 4'-4\" bifold."),
                   (12, (11.2, 15.0), "Bath 1 becomes private to bedroom 1: the old door to the passage is walled up and a new 2'-2\" door opens from the bedroom. To make that work in a 6'-2\" x 5'-0\" room the 60 in. tub moves to the old door wall, the toilet to the bedroom 2 wall, with a 14 in. deep wall-hung sink beside the door."),
                   (5, (17.5, 18.6), "Today this closet holds the furnace and water heater behind louvered doors that open into bedroom 1 (owner's video). Wall up the bedroom side; new solid door from the passage; 5/8 in. type X board."),
                   (6, (33.6, 0.37), "Walls not in the scan: verify."), (7, (11.0, 26.0), "Wall not in the scan: verify."),
                   (8, (31.9, 19.2), "Window over the counter (photo). The scan shows a 4'-4\" opening; the amber piece beside it is wall behind the range: verify."),
                   (9, (31.9, 24.1), "Upper flat's entry door from the porch: position not in the scan, verify."),
                   (10, (15.28, 24.0), "Wall between bedroom 1 and the stair: not in the scan, verify."),
                   (11, (17.4, 2.0), "Bedroom 2's closet is lengthened into the closed-in pocket beside the chimney: its end wall comes out and a new wall closes the tub end of bath 2.")],
            dims=[(10.76, 5.9, 16.23, 5.9), (15.6, 3.61, 15.6, 8.61), (10.76, 10.2, 16.83, 10.2), (0.05, 13.64, 0.05, 15.47), (9.3, 13.64, 9.3, 18.51), (6.14, 16.6, 9.78, 16.6)]),
    5: dict(name="Upper flat, main floor", view=((-3.5, 36.1), (-3, 30)), cut=[],
            ap=[(9.95, 25.3, 9.95, 26.5)],
            stairs=[(16.95, 19.6, 19.8, 24.6, "y+", "DN"), (20.3, 20.7, 23.45, 23.2, "y+", "UP to attic")],
            demo=[(17.9, 5.0, 18.4, 9.4), (17.9, 9.4, 18.4, 13.1), (16.0, 13.05, 20.0, 13.5), (25.6, 13.05, 30.6, 13.5), (23.5, 15.2, 23.9, 17.87)],
            new=[Hh(3.9, 15.62, 17.97), Hh(9.93, 15.62, 20.57), V(20.4, 9.76, 13.1), V(18.14, 9.4, 9.76), Hh(10.94, 23.53, 31.35), V(23.7, 10.77, 13.1)],
            fix=[],
            doors=[("301", "v", 23.7, 15.2, 17.87, "lo", 1, "2'-8\" x 6'-8\"", "Bedroom 4"), ("302", "h", 13.27, 16.0, 18.0, "lo", 1, "pair 2'-0\" x 6'-8\"", "Mechanical, solid core"),
                   ("302", "h", 13.27, 18.0, 20.0, "hi", 1, "", "")],
            bifolds=[("303", "v", 18.14, 5.0, 9.4, 1, "4'-5\" bifold", "Closet, bedroom 3"), ("304", "h", 13.27, 25.6, 30.6, 1, "5'-0\" bifold", "Closet, bedroom 4")],
            rooms=[room("301", "Living room", "living", [(0.33, 0.33, 15.28, 13.1)], "15'-0\" x 12'-9\"", "8'-2\"", (9.5, 1.9)),
                   room("302", "Kitchen", "kitchen", [(0.33, 13.44, 7.46, 26.86)], "7'-2\" x 13'-5\"", "7'-2\"", (5.0, 18.6)),
                   room("303", "Bedroom 3", "bed", [(18.31, 0.33, 31.35, 10.77), (20.57, 10.77, 23.53, 13.1)], "13'-0\" x 10'-5\" + entry", "8'-1\"", (22.6, 9.3), True),
                   room("304", "Bedroom 4", "bed", [(23.87, 13.44, 31.35, 26.86)], "7'-6\" x 13'-5\"", "7'-2\"", (26.0, 19.4), True),
                   room("305", "Bath 1", "bath", [(10.18, 17.49, 16.57, 27.17)], "6'-5\" x 9'-8\"", "8'-3\"", (13.6, 19.6)),
                   room("306", "Hall", "hall", [(10.18, 13.44, 23.53, 17.15)], "", "7'-5\"", (19.0, 15.3)),
                   room("312", "Stair", "stair", [(16.91, 17.32, 23.53, 24.56)], "", "", (21.9, 18.5)),
                   room("307", "Mechanical", "mech", [(15.62, 10.1, 20.23, 13.1)], "4'-7\" x 3'-0\"", "", (18.0, 14.2), True),
                   room("308", "Laundry", "laundry", [(7.8, 13.44, 9.84, 23.09)], "", "", (8.8, 16.0)),
                   room("309", "Clo.", "closet", [(15.62, 4.07, 17.97, 9.76)], "", "", (16.8, 5.6), True),
                   room("310", "Clo.", "closet", [(23.87, 11.11, 31.35, 13.1)], "", "", (27.6, 12.1), True),
                   room("311", "Coat clo.", "closet", [(15.62, 0.33, 17.97, 3.73)], "", "", (16.8, 2.0))],
            fx=[("tub", 10.18, 24.67, 15.18, 27.17, True), ("van", 10.18, 20.9, 11.93, 22.9, True), ("wc", 16.57, 22.5, "x-", True),
                ("base", 0.33, 24.78, 2.41, 26.86), ("dw", 2.41, 24.78, 4.41, 26.86), ("sinkbase", 4.41, 24.78, 7.41, 26.86), ("base", 0.33, 22.9, 2.41, 24.78),
                ("range", 0.33, 20.4, 2.5, 22.9), ("base", 0.33, 16.1, 2.41, 20.4), ("fridge", 0.33, 13.6, 2.83, 16.1),
                ("washer", 7.2, 18.2, 9.84, 20.7), ("dryer", 7.2, 20.8, 9.84, 23.3), ("furnace", 15.8, 10.3, 17.26, 12.7), ("wh", 19.0, 11.55),
                ("xequip", 24.0, 24.2, 27.6, 26.7)],
            furn=[("couch", 0.5, 1.5, 3.5, 8.5, "x-"), ("tv", 13.9, 4.2, 15.28, 9.2), ("ctable", 6.0, 3.3, 8.0, 6.7), ("table", 6.0, 9.4, 11.0, 12.4),
                  ("bed", 31.35, 5.4, "x-"), ("night", 29.85, 8.0, 31.35, 9.5), ("desk", 18.6, 0.33, 22.6, 2.33), ("dresser", 25.5, 0.33, 28.5, 1.83),
                  ("bed", 28.85, 26.86, "y-"), ("desk", 29.35, 15.4, 31.35, 19.4)],
            notes=[(1, (17.0, 7.6), "Chimney removed roof to lower flat, with the fireplace mantel on this wall of old Room A (owner's video). Patch floor, ceiling and roof. Stack S boxed in the closet corner."),
                   (2, (18.14, 7.3), "Wall opened 4'-7\" for closet doors; header over."), (3, (18.0, 10.2), "New mechanical closet: 2x4 walls, 5/8 in. type X board, pair of solid doors to the hall."),
                   (4, (27.6, 10.94), "New 2x4 wall: closet for bedroom 4."), (5, (28.1, 13.27), "Wall opened 5'-0\" for closet doors; header over (wall may be bearing)."),
                   (6, (23.7, 16.5), "Opening widened from 2'-4\" to 2'-8\"; new door."), (7, (16.8, 3.9), "Closet end wall: build if not there."),
                   (8, (25.8, 23.6), "This room is the flat's furnace and water heater room today (photo). Move both to closet 307; cap and re-run gas, flue, ducts and water. Patch the dropped ceiling.")],
            dims=[(15.62, 10.6, 20.23, 10.6), (19.95, 10.1, 19.95, 13.1), (23.87, 11.11, 23.87, 13.1), (18.31, 3.2, 31.35, 3.2), (24.4, 13.44, 24.4, 26.86)]),
    6: dict(name="Attic (upper flat)", view=((-3.5, 36.1), (-3, 30)), cut=[(16.55, 13.45, 17.2, 15.45)],
            ap=[(14.7, 15.4, 15.9, 15.4), (22.5, 6.5, 22.5, 7.7)],
            stairs=[(17.2, 17.0, 20.0, 24.5, "y+", "DN")],
            demo=[(15.5, 5.95, 18.6, 8.85), (16.9, 12.95, 19.75, 13.45), (20.0, 13.7, 20.4, 16.2)],
            new=[V(9.43, 15.56, 21.0), Hh(15.73, 9.43, 16.7, T6), V(16.7, 5.53, 8.85), Hh(6.2, 15.53, 16.87), Hh(5.7, 16.53, 18.5), Hh(5.7, 19.8, 22.33), V(22.16, 5.53, 13.37, T6),
                 Hh(13.2, 16.87, 19.8), Hh(13.2, 20.03, 22.33), V(14.2, 8.43, 9.27), V(14.2, 12.4, 13.24), Hh(8.6, 14.03, 16.7), Hh(13.07, 14.03, 16.53)],
            fix=[V(24.0, 23.0, 27.4)],
            doors=[("401", "h", 15.73, 9.9, 12.2, "hi", 1, "2'-4\" x 6'-8\"", "Bath A"), ("402", "v", 22.16, 8.9, 11.2, "hi", -1, "2'-4\" x 6'-8\"", "Bath B"),
                   ("403", "v", 20.2, 13.7, 16.2, "lo", 1, "2'-6\" x 6'-8\"", "Bedroom 2")],
            bifolds=[("404", "v", 14.2, 9.27, 12.4, -1, "3'-2\" bifold", "Closet, bedroom 1"), ("405", "h", 20.68, 20.6, 23.6, -1, "3'-0\" bifold", "Closet, bedroom 2")],
            rooms=[room("401", "Bedroom 1", "bed", [(0.59, 8.2, 14.0, 15.56), (0.59, 15.56, 9.26, 21.0), (5.57, 2.42, 10.93, 8.2), (11.27, 6.37, 15.53, 8.2)], "13'-5\" x 7'-4\" + 8'-8\" x 5'-5\" + bay", "7'-9\"", (9.8, 10.2), True),
                   room("402", "Bedroom 2", "bed", [(22.43, 7.2, 31.6, 20.4), (20.37, 13.47, 22.43, 20.4), (20.07, 2.17, 25.43, 5.43), (22.43, 5.43, 25.43, 7.2)], "9'-4\" x 13'-2\" + bay", "7'-10\"", (26.9, 18.6), True),
                   room("403", "Bath A", "bath", [(9.6, 16.0, 16.6, 21.0)], "7'-0\" x 5'-0\"", "7'-8\"", (12.2, 17.2), True),
                   room("404", "Bath B", "bath", [(16.89, 5.87, 21.89, 13.03)], "5'-0\" x 7'-2\"", "7'-8\"", (20.4, 9.9), True),
                   room("405", "Stair hall", "stair", [(17.17, 13.37, 20.03, 17.0)], "", "7'-9\"", (18.6, 18.6)),
                   room("406", "Clo.", "closet", [(14.37, 8.77, 16.53, 12.9)], "", "", (15.45, 10.8), True),
                   room("407", "Clo.", "closet", [(20.37, 20.77, 23.83, 22.98)], "", "", (22.1, 21.9), True)],
            fx=[("tub", 14.1, 16.0, 16.6, 21.0, True), ("wc", 12.85, 21.0, "y-", True), ("van", 9.6, 18.4, 11.35, 20.4, True),
                ("tub", 16.89, 5.87, 21.89, 8.37, True), ("wc", 16.89, 10.0, "x+", True), ("van", 19.2, 11.28, 21.2, 13.03, True)],
            furn=[("bed", 0.59, 14.5, "x+"), ("night", 0.59, 17.2, 2.09, 18.7), ("desk", 6.3, 2.42, 10.3, 4.42), ("dresser", 11.0, 8.2, 14.0, 9.7),
                  ("bed", 31.6, 13.2, "x-"), ("night", 30.1, 15.9, 31.6, 17.4), ("desk", 22.4, 2.3, 25.4, 4.3), ("dresser", 26.5, 18.9, 29.5, 20.4)],
            notes=[(1, (17.1, 7.2), "Chimney removed through the roof; frame and sheath the hole, re-shingle. Vent stack leaves through the same spot."),
                   (2, (12.5, 15.73), "New 2x6 wall: bath A. Tub valve in this wall; access panel AP on the bedroom side."), (3, (22.16, 9.6), "New 2x6 wall: bath B. Tub valve in this wall; access panel AP on the bedroom side."),
                   (4, (18.3, 13.2), "Old bedroom 2 doorway walled up."), (5, (20.2, 15.0), "New 2'-6\" door cut in for bedroom 2."),
                   (6, (14.2, 10.8), "New closet, 3'-2\" bifold."), (7, (22.1, 20.68), "Recess gets a closet front, 3'-0\" bifold."), (8, (24.0, 25.2), "Wall not in the scan: verify."),
                   (9, (16.0, 14.4), "Existing doorway to bedroom 1, about 2'-0\" wide: keep. It cannot be widened without shortening bath A.")],
            dims=[(9.6, 17.6, 14.1, 17.6), (13.4, 16.0, 13.4, 21.0), (16.89, 9.2, 21.89, 9.2), (21.3, 5.87, 21.3, 13.03)]),
}

# ---------------------------------------------------------------------------------------------- geometry
_G = {}


def geom(fl):
    """Existing walls (after removals), openings and windows of one level, as shapely / point lists in feet."""
    if fl in _G:
        return _G[fl]
    G, _ = sx.regularize(de.P390[str(fl)], de.T390(fl))
    L = LV[fl]
    demo = unary_union([box(*r) for r in L["demo"]]) if L["demo"] else None
    walls = unary_union([Polygon(w["pts"]).buffer(0) for w in G["walls"] if len(w["pts"]) >= 4])
    removed = walls.intersection(demo) if demo is not None else None
    if demo is not None:
        walls = walls.difference(demo)
    if L["cut"]:
        walls = walls.difference(unary_union([box(*r) for r in L["cut"]]))
    cut = unary_union([box(*r) for r in L["demo"] + L["new"]]) if (L["demo"] or L["new"]) else None
    def keep(o):
        if len(o["pts"]) < 2: return False
        q = np.array(o["pts"])
        if len(q) >= 4 and max(np.ptp(q[:, 0]), np.ptp(q[:, 1])) < 1.0: return False      # scan artefact, not a door
        c = np.mean(np.array(o["pts"]), 0)
        return cut is None or not cut.buffer(0.3).contains(Polygon([(c[0] - .01, c[1] - .01), (c[0] + .01, c[1] - .01), (c[0] + .01, c[1] + .01)]).centroid)
    fixu = unary_union([box(*r) for r in L["fix"]]).buffer(0.02) if L["fix"] else None
    def trim(o):
        """Cut a scanned opening back where a wall is now drawn across part of it."""
        if fixu is None or len(o["pts"]) < 4: return o
        d_ = Polygon(o["pts"]).buffer(0).difference(fixu)
        if d_.is_empty: return None
        if d_.geom_type != "Polygon": d_ = max(d_.geoms, key=lambda q: q.area)
        return dict(o, pts=[list(c) for c in d_.exterior.coords[:-1]])
    G["doors"] = [t_ for t_ in (trim(o) for o in G["doors"]) if t_]; G["openings"] = [t_ for t_ in (trim(o) for o in G["openings"]) if t_]
    out = dict(removed=removed, walls=walls, doors=[o for o in G["doors"] + G["openings"] if keep(o)], windows=[o for o in G["windows"] if len(o["pts"]) >= 4],
               rooms=G["rooms"],
               arcs=[a for a in G.get("arc_pts", []) if cut is None or not any(cut.buffer(0.6).contains(Polygon([(q[0] - .01, q[1] - .01), (q[0] + .01, q[1] - .01), (q[0], q[1] + .01)]).centroid) for q in a)])
    _G[fl] = out
    return out


def _fill(ax, g, **kw):
    """Fill a shapely polygon or multipolygon, holes left open."""
    from matplotlib.path import Path
    from matplotlib.patches import PathPatch
    for p in (g.geoms if hasattr(g, "geoms") else [g]):
        if p.is_empty or p.geom_type != "Polygon": continue
        verts, codes = [], []
        for ring in [p.exterior] + list(p.interiors):
            c = np.array(ring.coords)
            verts += c.tolist(); codes += [Path.MOVETO] + [Path.LINETO] * (len(c) - 2) + [Path.CLOSEPOLY]
        ax.add_patch(PathPatch(Path(verts, codes), **kw))


# ---------------------------------------------------------------------------------------------- symbols
def s_door(ax, axis, w0, a0, a1, hinge, swing, col=NEWW, z=8):
    wd = a1 - a0; hp = a0 if hinge == "lo" else a1; d = 1 if hinge == "lo" else -1
    if axis == "h":
        ax.add_patch(Rectangle((a0, w0 - 0.3), wd, 0.6, fc=PAPER, ec="none", zorder=z - 0.5))
        ax.plot([hp, hp], [w0, w0 + swing * wd], color=col, lw=0.9, zorder=z)
        t0 = 90 if swing > 0 else 270; th = (t0 - 90, t0) if (d * swing) > 0 else (t0, t0 + 90)
        ax.add_patch(Arc((hp, w0), 2 * wd, 2 * wd, theta1=th[0], theta2=th[1], color=col, lw=0.45, zorder=z))
    else:
        ax.add_patch(Rectangle((w0 - 0.3, a0), 0.6, wd, fc=PAPER, ec="none", zorder=z - 0.5))
        ax.plot([w0, w0 + swing * wd], [hp, hp], color=col, lw=0.9, zorder=z)
        t0 = 0 if swing > 0 else 180; th = (t0, t0 + 90) if (d * swing) > 0 else (t0 - 90, t0)
        ax.add_patch(Arc((w0, hp), 2 * wd, 2 * wd, theta1=th[0], theta2=th[1], color=col, lw=0.45, zorder=z))


def s_bifold(ax, axis, w0, a0, a1, side, col=NEWW, z=8):
    n = 4; t = np.linspace(a0, a1, n + 1); off = [w0 + (0.5 * side if i % 2 else 0) for i in range(n + 1)]
    if axis == "h":
        ax.add_patch(Rectangle((a0, w0 - 0.3), a1 - a0, 0.6, fc=PAPER, ec="none", zorder=z - 0.5)); ax.plot(t, off, color=col, lw=0.8, zorder=z)
    else:
        ax.add_patch(Rectangle((w0 - 0.3, a0), 0.6, a1 - a0, fc=PAPER, ec="none", zorder=z - 0.5)); ax.plot(off, t, color=col, lw=0.8, zorder=z)


def s_tub(ax, x0, y0, x1, y1, col):
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc="white", ec=col, lw=0.8, zorder=6))
    ax.add_patch(Rectangle((x0 + 0.22, y0 + 0.22), x1 - x0 - 0.44, y1 - y0 - 0.44, fc="#eef4fb", ec=col, lw=0.4, zorder=6.1, joinstyle="round"))


def s_wc(ax, x, y, face, col):
    dx, dy = {"x+": (1, 0), "x-": (-1, 0), "y+": (0, 1), "y-": (0, -1)}[face]
    tx, ty = (0.67, 1.6) if dx else (1.6, 0.67)
    ax.add_patch(Rectangle((x - (0 if dx > 0 else tx if dx < 0 else tx / 2), y - (0 if dy > 0 else ty if dy < 0 else ty / 2)), tx, ty, fc="white", ec=col, lw=0.7, zorder=6))
    ax.add_patch(Ellipse((x + dx * 1.45, y + dy * 1.45), 1.5 if dx else 1.2, 1.2 if dx else 1.5, fc="white", ec=col, lw=0.7, zorder=6))


def s_van(ax, x0, y0, x1, y1, col):
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc="white", ec=col, lw=0.7, zorder=6))
    ax.add_patch(Ellipse(((x0 + x1) / 2, (y0 + y1) / 2), (x1 - x0) * 0.55, (y1 - y0) * 0.55, fc="#eef4fb", ec=col, lw=0.4, zorder=6.1))


def s_box(ax, x0, y0, x1, y1, name, col=FXE, fc="white", fs=3.4, z=6):
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc=fc, ec=col, lw=0.6, zorder=z))
    if name:
        ax.text((x0 + x1) / 2, (y0 + y1) / 2, name, fontsize=fs, color=col, ha="center", va="center", zorder=z + 0.2, rotation=90 if (y1 - y0) > 1.6 * (x1 - x0) else 0, linespacing=1.1, gid="own")


def s_range(ax, x0, y0, x1, y1, col=FXE):
    s_box(ax, x0, y0, x1, y1, "", col)
    for i in (0.28, 0.72):
        for j in (0.28, 0.72):
            ax.add_patch(plt.Circle((x0 + i * (x1 - x0), y0 + j * (y1 - y0)), 0.3, fill=False, ec=col, lw=0.5, zorder=6.2))


def s_bed(ax, hx, hy, face, col=FURN):
    Wd, L = 5.0, 6.67
    dx, dy = {"x+": (1, 0), "x-": (-1, 0), "y+": (0, 1), "y-": (0, -1)}[face]
    if dx: x0, y0, w, h = (hx if dx > 0 else hx - L), hy - Wd / 2, L, Wd
    else: x0, y0, w, h = hx - Wd / 2, (hy if dy > 0 else hy - L), Wd, L
    ax.add_patch(Rectangle((x0, y0), w, h, fc="#fbf5ea", ec=col, lw=0.6, zorder=5))
    for s in (-1, 1):
        if dx: ax.add_patch(Rectangle((hx + dx * 0.2 - (0 if dx > 0 else 1.3), hy + s * 1.25 - 1.0), 1.3, 2.0, fc="white", ec=col, lw=0.35, zorder=5.1))
        else: ax.add_patch(Rectangle((hx + s * 1.25 - 1.0, hy + dy * 0.2 - (0 if dy > 0 else 1.3)), 2.0, 1.3, fc="white", ec=col, lw=0.35, zorder=5.1))
    ax.text(x0 + w / 2 + dx * 0.7, y0 + h / 2 + dy * 0.7, "QUEEN\n5'-0\" x 6'-8\"", fontsize=3.3, color=col, ha="center", va="center", zorder=5.2, linespacing=1.15, gid="own")
    return (x0, y0, x0 + w, y0 + h)


def s_couch(ax, x0, y0, x1, y1, back, col="#5b6470"):
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc="#eef0f2", ec=col, lw=0.6, zorder=5)); b = 0.7
    r = {"x-": (x0, y0, b, y1 - y0), "x+": (x1 - b, y0, b, y1 - y0), "y-": (x0, y0, x1 - x0, b), "y+": (x0, y1 - b, x1 - x0, b)}[back]
    ax.add_patch(Rectangle(r[:2], r[2], r[3], fc="#d5d9de", ec=col, lw=0.4, zorder=5.1))
    ax.text((x0 + x1) / 2, (y0 + y1) / 2, "COUCH 7'-0\"", fontsize=3.2, color=col, ha="center", va="center", zorder=5.2, rotation=90 if (y1 - y0) > (x1 - x0) else 0, gid="own")


def dim(ax, x0, y0, x1, y1, at=0.5, fs=3.8, gid="dim"):
    """Dimension string. at = where the figure sits along the line (0 to 1)."""
    L = abs(x1 - x0) + abs(y1 - y0); t = ftin(round(L * 12) / 12)
    ax.plot([x0, x1], [y0, y1], color="#333", lw=0.35, zorder=11)
    for (a, b) in ((x0, y0), (x1, y1)):
        ax.plot([a - 0.16, a + 0.16], [b - 0.16, b + 0.16], color="#333", lw=0.55, zorder=11)
    hz = abs(x1 - x0) > abs(y1 - y0)
    ax.text(x0 + (x1 - x0) * at, y0 + (y1 - y0) * at, t, fontsize=fs, color="#111", ha="center", va="center", rotation=0 if hz else 90, zorder=11.1, gid=gid,
            bbox=dict(fc="white", ec="none", pad=0.25))


def keynote(ax, n, x, y, col=NEWW, to=None):
    """Numbered diamond. to = (x, y): thin leader from the diamond to the thing it is about."""
    if to is not None:
        ax.plot([x, to[0]], [y, to[1]], color=col, lw=0.45, zorder=19.5)
        ax.add_patch(plt.Circle(to, 0.09, fc=col, ec="none", zorder=19.6))
    ax.add_patch(MPoly([(x - 0.55, y), (x, y + 0.55), (x + 0.55, y), (x, y - 0.55)], closed=True, fc="white", ec=col, lw=0.8, zorder=20))
    ax.text(x, y, str(n), fontsize=4.4, color=col, ha="center", va="center", fontweight="bold", zorder=21, gid=f"keynote:{n}")


def panel_box(f):
    """Working space in front of a panel: 30 in. wide (centred on the panel), 36 in. deep, on side f[5] (-1 by default)."""
    x0, y0, x1, y1 = f[1:5]; sd = f[5] if len(f) > 5 else -1
    if x0 == x1:
        c = (y0 + y1) / 2; hw = max(1.25, (y1 - y0) / 2); return (min(x0, x0 + sd * 3.0), c - hw, max(x0, x0 + sd * 3.0), c + hw)
    c = (x0 + x1) / 2; hw = max(1.25, (x1 - x0) / 2); return (c - hw, min(y0, y0 + sd * 3.0), c + hw, max(y0, y0 + sd * 3.0))


# ---------------------------------------------------------------------------------------------- base plan
def draw_base(ax, fl, mode="arch"):
    """mode 'arch': full construction plan (new walls red, removals dashed, furniture, sizes). mode 'trade': quiet grey background for a trade overlay."""
    L = LV[fl]; g = geom(fl); arch = mode == "arch"
    for r in g["rooms"]:
        ax.fill([p[0] for p in r["pts"]], [p[1] for p in r["pts"]], fc="#fafafa", ec="none", zorder=1)
    wc_ = EXW if arch else "#b8bdc4"
    newu = unary_union([box(*r) for r in L["new"]]) if L["new"] else None
    fixu = unary_union([box(*r) for r in L["fix"]]) if L["fix"] else None
    if newu is not None:
        _fill(ax, newu.difference(g["walls"]), fc=NEWW if arch else "#8d939b", ec="#7d1a14" if arch else "#8a9099", lw=0.35, zorder=3.9)
    if fixu is not None:
        _fill(ax, fixu.difference(g["walls"]), fc=wc_, ec=FIXE if arch else "#8a9099", lw=0.9 if arch else 0.35, zorder=3.95)
    _fill(ax, g["walls"], fc=wc_, ec="#4a4f57" if arch else "#8a9099", lw=0.35, zorder=4)
    if arch and g["removed"] is not None and not g["removed"].is_empty:
        dr = [box(d[3], d[2] - 0.45, d[4], d[2] + 0.45) if d[1] == "h" else box(d[2] - 0.45, d[3], d[2] + 0.45, d[4]) for d in L["doors"]]      # a new door in a rebuilt wall
        rem = g["removed"] if newu is None else g["removed"].difference(unary_union([newu.buffer(0.3)] + dr))
        rem = unary_union([q for q in (rem.geoms if hasattr(rem, "geoms") else [rem]) if q.geom_type == "Polygon" and q.area > 0.12 and q.buffer(-0.08).area > 0])
        if not rem.is_empty: _fill(ax, rem, fc="none", ec=NEWW, lw=0.45, ls=(0, (2, 1.6)), zorder=3.8)
        c = CHIMNEY if fl != 3 else (16.4, 6.4, 18.3, 9.4)
        ax.add_patch(Rectangle((c[0], c[1]), c[2] - c[0], c[3] - c[1], fill=False, ec=NEWW, lw=0.6, ls=(0, (2, 1.6)), hatch="//", alpha=0.35, zorder=3.5))
    for o in g["doors"]:
        if len(o["pts"]) >= 4:
            ax.add_patch(MPoly(np.array(o["pts"]), closed=True, fc=PAPER, ec="#8d949c", lw=0.35, zorder=4.5))
    for pts in g["arcs"]:
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color="#8d949c", lw=0.4, zorder=4.6)
    for o in g["windows"]:
        ax.add_patch(MPoly(np.array(o["pts"]), closed=True, fc="#cfe3f7", ec="#1f5fa8", lw=0.5, zorder=4.7))
    for (x0, y0, x1, y1, way, lab_) in L["stairs"]:
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc="none", ec="#6b7480", lw=0.5, zorder=4.4))
        if way[0] == "x":
            for t in np.arange(x0 + 0.9, x1 - 0.2, 0.9): ax.plot([t, t], [y0, y1], color="#6b7480", lw=0.3, zorder=4.4)
            a, b = ((x0 + 0.4, (y0 + y1) / 2), (x1 - 0.4, (y0 + y1) / 2)); a, b = (b, a) if way == "x-" else (a, b)
        else:
            for t in np.arange(y0 + 0.9, y1 - 0.2, 0.9): ax.plot([x0, x1], [t, t], color="#6b7480", lw=0.3, zorder=4.4)
            a, b = (((x0 + x1) / 2, y0 + 0.4), ((x0 + x1) / 2, y1 - 0.4)); a, b = (b, a) if way == "y-" else (a, b)
        ax.annotate("", xy=b, xytext=a, arrowprops=dict(arrowstyle="->", color="#4a4f57", lw=0.6), zorder=4.5)
        ax.text(a[0], a[1], lab_, fontsize=3.4, color="#4a4f57", ha="center", va="center", zorder=4.6, bbox=dict(fc="white", ec="none", pad=0.2))
    dc = NEWW if arch else "#8a9099"
    for d in L["doors"]:
        s_door(ax, d[1], d[2], d[3], d[4], d[5], d[6], col=dc)
    for b in L["bifolds"]:
        s_bifold(ax, b[1], b[2], b[3], b[4], b[5], col=dc)
    # fixtures, cabinets, appliances
    for f in L["fx"]:
        k = f[0]
        if k == "tub": s_tub(ax, *f[1:5], FXN if (f[5] and arch) else FXE)
        elif k == "wc": s_wc(ax, f[1], f[2], f[3], FXN if (f[4] and arch) else FXE)
        elif k == "van": s_van(ax, *f[1:5], FXN if (f[5] and arch) else FXE)
        elif k == "range": s_range(ax, *f[1:5])
        elif k == "fridge": s_box(ax, *f[1:5], "REF")
        elif k == "base": s_box(ax, *f[1:5], "", FXE, "#f1f2f4")
        elif k == "dw": s_box(ax, *f[1:5], "DW", FXE, "#f1f2f4")
        elif k == "xequip":
            ax.add_patch(Rectangle((f[1], f[2]), f[3] - f[1], f[4] - f[2], fill=False, ec=NEWW if arch else "#8a9099", lw=0.6, ls=(0, (2, 1.6)), zorder=6))
            ax.text((f[1] + f[3]) / 2, (f[2] + f[4]) / 2, "furnace + water heater\nhere today: remove", fontsize=3.2, color=NEWW if arch else "#8a9099", ha="center", va="center", zorder=6.1, linespacing=1.1, gid="own")
        elif k == "sinkbase":
            s_box(ax, *f[1:5], "", FXE, "#f1f2f4"); x0, y0, x1, y1 = f[1:5]
            ax.add_patch(Rectangle((x0 + 0.25 * (x1 - x0), y0 + 0.2 * (y1 - y0)), 0.5 * (x1 - x0), 0.6 * (y1 - y0), fc="#eef4fb", ec=FXE, lw=0.5, zorder=6.2))
        elif k == "wdstack": s_box(ax, *f[1:5], "W/D\nstacked", FXE, "white", 3.2)
        elif k == "panel":
            x0, y0, x1, y1 = f[1:5]
            ax.plot([x0, x1], [y0, y1], color="#123a6b", lw=3.2, solid_capstyle="butt", zorder=9.4)
            if arch:
                bx = panel_box(f)
                ax.add_patch(Rectangle((bx[0], bx[1]), bx[2] - bx[0], bx[3] - bx[1], fill=False, ec="#123a6b", lw=0.5, ls=(0, (3, 2)), zorder=9.3))
                sd = f[5] if len(f) > 5 else -1
                tx, ty = ((x0 + sd * 1.0, (y0 + y1) / 2) if x0 == x1 else ((x0 + x1) / 2, y0 + sd * 1.0))
                ax.text(tx, ty, "PANEL\n30 x 36\nclear", fontsize=3.2, color="#123a6b", ha="center", va="center", zorder=9.5, linespacing=1.1, gid="own")
        elif k == "washer": s_box(ax, *f[1:5], "W")
        elif k == "dryer": s_box(ax, *f[1:5], "D")
        elif k == "lsink": s_van(ax, *f[1:5], FXE)
        elif k == "furnace": s_box(ax, *f[1:5], "F", MECHC, "#f3e9f7", 4.0)
        elif k == "wh":
            ax.add_patch(plt.Circle((f[1], f[2]), 0.92, fc="#f3e9f7", ec=MECHC, lw=0.7, zorder=6)); ax.text(f[1], f[2], "WH", fontsize=3.6, color=MECHC, ha="center", va="center", zorder=6.2, fontweight="bold", gid="own")
    if arch:
        for f in L["furn"]:
            k = f[0]
            if k == "bed": s_bed(ax, f[1], f[2], f[3])
            elif k == "couch": s_couch(ax, *f[1:6])
            elif k == "desk":
                s_box(ax, *f[1:5], "DESK", FURN, "#fbf5ea", 3.2, 5)
            elif k == "tv": s_box(ax, *f[1:5], "TV", "#5b6470", "#e3e6ea", 3.2, 5)
            elif k == "table": s_box(ax, *f[1:5], "TABLE", FURN, "#fbf5ea", 3.2, 5)
            elif k == "ctable": s_box(ax, *f[1:5], "", "#5b6470", "#f4f5f6", 3.2, 5)
            elif k in ("dresser", "night"): s_box(ax, *f[1:5], "DR" if k == "dresser" else "", FURN, "#fbf5ea", 3.0, 5)
    if arch:
        for a_ in L.get("ap", []):
            x0, y0, x1, y1 = a_[:4]; sd = a_[4] if len(a_) > 4 else 1
            ax.plot([x0, x1], [y0, y1], color="#c79a00", lw=2.6, solid_capstyle="butt", zorder=9.5)
            ax.text((x0 + x1) / 2 + (sd * 0.42 if x0 == x1 else 0), (y0 + y1) / 2 + (sd * 0.42 if y0 == y1 else 0), "AP", fontsize=3.4, color="#8a6a00", ha="center", va="center", fontweight="bold", zorder=9.6, gid="ap")
    ax.add_patch(plt.Circle(STACK if fl != 3 else (17.68, 8.9), 0.28, fc="white", ec=FXN if arch else "#8a9099", lw=0.9, zorder=9))
    for r in L["rooms"]:
        x, y = r["lab"]
        if arch:
            big = r["kind"] not in ("closet",)
            col = NEWW if r["new"] else INK
            nm = r.get("disp") or (r["name"] if not big else r["name"].upper())
            if r.get("compact"):
                ax.text(x, y + 0.22, nm, fontsize=4.6, fontweight="bold", color=col, ha="center", va="center", zorder=12, gid="room", bbox=dict(fc="white", ec="none", pad=0.3))
                ax.text(x, y - 0.24, r["no"] + ((" · " + r["size"]) if r["size"] else "") + ((" · clg " + r["ceil"]) if r["ceil"] else ""), fontsize=3.6, color=col, ha="center", va="center", zorder=12, gid="room",
                        bbox=dict(fc="white", ec="none", pad=0.25))
                continue
            ax.text(x, y + (0.5 if big else 0), nm, fontsize=4.6 if big else 3.6, fontweight="bold", color=col, ha="center", va="center", zorder=12, gid="room",
                    bbox=dict(fc="white", ec="none", pad=0.4))
            if big:
                ax.text(x, y - 0.25, r["no"] + ((" · " + r["size"]) if r["size"] else ""), fontsize=3.7, color=col, ha="center", va="center", zorder=12, gid="room", bbox=dict(fc="white", ec="none", pad=0.3))
                if r["ceil"]:
                    ax.text(x, y - 0.9, "clg " + r["ceil"], fontsize=3.4, color=GREY, ha="center", va="center", zorder=12, gid="room", bbox=dict(fc="white", ec="none", pad=0.25))
        elif r["kind"] != "closet":
            ax.text(x, y, f"{r['name']}\n{r['no']}", fontsize=3.4, color="#9097a0", ha="center", va="center", zorder=2, linespacing=1.15)


def bsheet(number, title, fl, notes, legend=None, sub=None):
    """One level at 1/4 in. = 1 ft. Returns fig, bg (inch coordinates), ax (feet). A strip 2.6 in. wide is free at x 10.55 to 13.15 in. for legends and schedules."""
    sx.KIND[:] = ["BUILDER SET", "8 BEDROOMS · 7 BATHS · 3 FLATS"]
    sx.LEGEND[:] = ["Scale 1/4 in. = 1 ft on 11 x 17 · north as shown"]
    sx.ISSUE2[:] = ["BUILDER SET · ISSUE 1 · 27 NOV 2026"]
    sx.WARN[:] = ["PRELIMINARY · VERIFY ON SITE", "Layout from a phone scan. Not stamped. Structure, loads and\nfinal sizes to be confirmed by licensed trades before work."]
    fig, bg = sheet(number, title, "390 Forest Ave", sub or f"Rear building · {LV[fl]['name'].lower()}" if fl else (sub or "Rear building"), notes)
    if not fl:
        return fig, bg, None
    vx, vy = LV[fl]["view"]
    ax = sx.axes(fig, 0.45, 1.25, vx, vy, FPI)
    sx.north(ax, vx[0] + 2.0, vy[1] - 1.9, de.FX["north_in_building_frame"], 1.1)
    bg.text(0.5, 10.25, title.upper(), fontsize=10, fontweight="bold", color=INK, va="center")
    bg.text(0.5, 1.0, "SCALE 1/4 in. = 1 ft", fontsize=6.5, fontweight="bold", color=INK, va="center")
    for i in range(5):
        bg.add_patch(Rectangle((2.2 + i * 0.5, 0.95), 0.5, 0.08, fc=INK if i % 2 == 0 else "white", ec=INK, lw=0.4))
        bg.text(2.2 + i * 0.5, 0.82, f"{i * 2}", fontsize=5, ha="center", color=INK)
    bg.text(4.7, 0.82, "10 ft", fontsize=5, ha="center", color=INK)
    if legend:
        y = 10.3
        bg.text(10.6, y, "LEGEND", fontsize=7, fontweight="bold", color=INK, va="center"); y -= 0.24
        for kind, col, txt in legend:
            if kind == "fill": bg.add_patch(Rectangle((10.6, y - 0.05), 0.34, 0.1, fc=col, ec="#4a4f57", lw=0.4))
            elif kind == "dash": bg.plot([10.6, 10.94], [y, y], color=col, lw=0.9, ls=(0, (2, 1.6)))
            elif kind == "line": bg.plot([10.6, 10.94], [y, y], color=col, lw=1.2)
            elif kind == "dot": bg.add_patch(plt.Circle((10.77, y), 0.06, fc="white", ec=col, lw=1.0))
            else: bg.text(10.77, y, kind, fontsize=6, color=col, ha="center", va="center", fontweight="bold")
            for i, ln in enumerate(txt.split("\n")):
                bg.text(11.05, y - i * 0.13, ln, fontsize=5.6, color=INK, va="center")
            y -= 0.2 + 0.13 * txt.count("\n")
        fig._legend_end = y
    return fig, bg, ax


def text_block(bg, x, y, title, lines, fs=5.6, col=INK, lh=0.135):
    bg.text(x, y, title.upper(), fontsize=6.6, fontweight="bold", color=col, va="center"); y -= 0.22
    for ln in lines:
        bg.text(x, y, ln, fontsize=fs, color=INK, va="center"); y -= lh
    return y - 0.1


def wrap(s, n=46):
    import textwrap
    return textwrap.wrap(s, n)


def _fx_geom(f):
    from shapely.geometry import Point
    k = f[0]
    if k == "wc":
        x, y, face = f[1], f[2], f[3]; dx, dy = {"x+": (1, 0), "x-": (-1, 0), "y+": (0, 1), "y-": (0, -1)}[face]
        tx, ty = (0.67, 1.6) if dx else (1.6, 0.67)
        tx0 = x - (0 if dx > 0 else tx if dx < 0 else tx / 2); ty0 = y - (0 if dy > 0 else ty if dy < 0 else ty / 2)
        cx, cy = x + dx * 1.45, y + dy * 1.45; w, h = (1.5, 1.2) if dx else (1.2, 1.5)
        return box(tx0, ty0, tx0 + tx, ty0 + ty).union(box(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2))
    if k == "wh": return Point(f[1], f[2]).buffer(0.92)
    if k == "panel":
        from shapely.geometry import LineString
        return LineString([(f[1], f[2]), (f[3], f[4])]).buffer(0.1)
    return box(*f[1:5])


def _furn_geom(f):
    if f[0] == "bed":
        Wd, Ln = 5.0, 6.67; hx, hy = f[1], f[2]; dx, dy = {"x+": (1, 0), "x-": (-1, 0), "y+": (0, 1), "y-": (0, -1)}[f[3]]
        if dx: return box((hx if dx > 0 else hx - Ln), hy - Wd / 2, (hx if dx > 0 else hx - Ln) + Ln, hy + Wd / 2)
        return box(hx - Wd / 2, (hy if dy > 0 else hy - Ln), hx + Wd / 2, (hy if dy > 0 else hy - Ln) + Ln)
    return box(*f[1:5])


def _swing_geom(d):
    """Door leaf (open 90 degrees) and its arc, as a thin shape."""
    from shapely.geometry import LineString
    axis, w0, a0, a1, hinge, swing = d[1:7]; wd = a1 - a0; hp = a0 if hinge == "lo" else a1; far = a1 if hinge == "lo" else a0
    pts = []
    for t in np.linspace(0, math.pi / 2, 16):
        u = hp + (far - hp) * math.cos(t); v = w0 + swing * wd * math.sin(t)
        pts.append((u, v) if axis == "h" else (v, u))
    c = (hp, w0) if axis == "h" else (w0, hp)
    return LineString(pts + [c]).buffer(0.05)


def obstacles(fl, leaders=None):
    """Linework a loose label must not sit on: [(shape, name, kind)]."""
    from shapely.geometry import LineString, Point
    L = LV[fl]; g = geom(fl); out = []
    for f in L["fx"]:
        out.append((_fx_geom(f), f"fixture {f[0]}", "tub" if f[0] == "tub" else "fx"))
        if f[0] == "panel":
            out.append((box(*panel_box(f)).exterior.buffer(0.03), "panel working space outline", "fx"))
    for f in L["furn"]:
        out.append((_furn_geom(f), f"furniture {f[0]}", "furn"))
    for d in L["doors"]:
        out.append((_swing_geom(d), f"door {d[0]} swing", "swing"))
    for b in L["bifolds"]:
        r = (b[3], min(b[2], b[2] + 0.5 * b[5]), b[4], max(b[2], b[2] + 0.5 * b[5])) if b[1] == "h" else (min(b[2], b[2] + 0.5 * b[5]), b[3], max(b[2], b[2] + 0.5 * b[5]), b[4])
        out.append((box(*r), f"bifold {b[0]}", "swing"))
    w = g["walls"]
    for k in ("new", "fix"):
        if L[k]: w = w.union(unary_union([box(*r) for r in L[k]]))
    out.append((w.buffer(-0.03), "a wall", "wall"))
    for o in g["windows"]:
        out.append((Polygon(o["pts"]).buffer(0), "a window", "wall"))
    for a in g["arcs"]:
        if len(a) >= 2: out.append((LineString(a).buffer(0.04), "an existing door swing", "swing"))
    for (x0, y0, x1, y1, *_r) in L["stairs"]:
        out.append((box(x0, y0, x1, y1), "the stair", "fx"))
    out.append((Point(STACK if fl != 3 else (17.68, 8.9)).buffer(0.3), "the drain stack", "fx"))
    for i, d in enumerate(L["dims"]):
        out.append((LineString([(d[0], d[1]), (d[2], d[3])]).buffer(0.03), f"dimension line {i}", f"dim:{i}"))
    for a_ in L.get("ap", []):
        out.append((LineString([(a_[0], a_[1]), (a_[2], a_[3])]).buffer(0.08), "an access panel", "fx"))
    for n, (p, q) in (leaders or {}).items():
        out.append((LineString([p, q]).buffer(0.03), f"leader of keynote {n}", f"lead:{n}"))
    return out


def clarity(fig, ax, fl=None, bg=None, pad=1.0):
    """Check that nothing written on the sheet sits on anything else. Returns a list of plain sentences, one per clash:
    label on label anywhere on the sheet; text outside the border or across a title-block line;
    on the plan also label on fixture, furniture, door swing, wall, window, dimension line or leader."""
    fig.canvas.draw(); r = fig.canvas.get_renderer(); inv = ax.transData.inverted() if ax is not None else None; items = []
    for A in (ax, bg):
        if A is None: continue
        for t in A.texts:
            if not t.get_text().strip(): continue
            bb = t.get_window_extent(r); gid = t.get_gid() or ""; x, y = t.get_position()
            if gid.startswith("keynote"):
                c = A.transData.transform((x, y)); h = abs(A.transData.transform((0.57, 0))[0] - A.transData.transform((0, 0))[0])
                px = Polygon([(c[0] - h, c[1]), (c[0], c[1] + h), (c[0] + h, c[1]), (c[0], c[1] - h)])
            else:
                px = box(bb.x0 - pad, bb.y0 - pad, bb.x1 + pad, bb.y1 + pad)
            items.append((px, gid, f"{t.get_text().splitlines()[0][:26]!r} at ({x:.1f}, {y:.1f})", A is ax, (x, y)))
    out = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if items[i][0].intersects(items[j][0]):
                out.append(f"{items[i][2]} is on {items[j][2]}")
    if bg is not None:                                     # border and title-block rules
        T = bg.transData.transform; x0 = W - MG - TB
        frame = box(*T((MG + 0.04, MG + 0.04)), *T((W - MG - 0.04, H - MG - 0.04)))
        rules = [((x0, MG), (x0, H - MG)), ((x0, MG + 2.35), (W - MG, MG + 2.35)), ((x0, MG + 1.40), (W - MG, MG + 1.40)), ((x0, H - MG - 1.08), (W - MG, H - MG - 1.08)), ((x0, H - MG - 1.68), (W - MG, H - MG - 1.68))]
        from shapely.geometry import LineString
        for px, gid, nm, _onplan, _p in items:
            if not frame.contains(px): out.append(f"{nm} runs outside the sheet border")
            for p, q in rules:
                if LineString([T(p), T(q)]).intersects(px): out.append(f"{nm} crosses a title-block line")
    if fl and ax is not None:
        obs = obstacles(fl, getattr(ax, "_leaders", None)); D = ax.transData.transform
        from shapely.ops import transform as _tf
        for px, gid, nm, onplan, _p in items:
            if gid == "own" or not onplan: continue
            (u0, v0), (u1, v1) = inv.transform(px.bounds[:2]), inv.transform(px.bounds[2:])
            shp = box(min(u0, u1), min(v0, v1), max(u0, u1), max(v0, v1)) if not gid.startswith("keynote") else Polygon([inv.transform(c) for c in px.exterior.coords[:-1]])
            for og, on, ok in obs:
                if gid.startswith("keynote") and (ok == "tub" or ok == "lead:" + gid[8:]): continue
                if gid.startswith("dim:") and ok == gid: continue
                if og.intersects(shp):
                    out.append(f"{nm} is on {on}")
    return out


def free_spot(ax, fig, fl, x, y, reach=3.0):
    """Nearest place to (x, y) where a keynote diamond touches nothing. For laying out a sheet."""
    fig.canvas.draw(); r = fig.canvas.get_renderer(); inv = ax.transData.inverted(); boxes = []
    for t in ax.texts:
        if not t.get_text().strip() or (t.get_gid() or "").startswith("keynote") and t.get_position() == (x, y): continue
        bb = t.get_window_extent(r); (u0, v0), (u1, v1) = inv.transform((bb.x0 - 2, bb.y0 - 2)), inv.transform((bb.x1 + 2, bb.y1 + 2))
        boxes.append(box(min(u0, u1), min(v0, v1), max(u0, u1), max(v0, v1)))
    blk = unary_union(boxes + [o[0] for o in obstacles(fl, getattr(ax, "_leaders", None)) if o[2] != "tub"]); best = None
    for dx in np.arange(-reach, reach + 0.01, 0.1):
        for dy in np.arange(-reach, reach + 0.01, 0.1):
            d = math.hypot(dx, dy)
            if best and d >= best[0]: continue
            c = (x + dx, y + dy)
            if not Polygon([(c[0] - 0.6, c[1]), (c[0], c[1] + 0.6), (c[0] + 0.6, c[1]), (c[0], c[1] - 0.6)]).intersects(blk): best = (d, round(c[0], 1), round(c[1], 1))
    return best and best[1:]


# ---------------------------------------------------------------------------------------------- architectural sheets
CHECK_HINTS = bool(os.environ.get("B390_HINTS"))          # True: print the nearest clear spot for each keynote that clashes (slow; for laying out a sheet)
ALEG = [("fill", EXW, "Existing wall: framing stays, stripped\nto the studs and re-boarded"), ("fill", NEWW, "New wall: 2x4 at 16 in. o.c.,\n1/2 in. board each side (2x6 where noted)"), ("dash", NEWW, "Existing wall or chimney removed\n(dashed outline)"),
        ("fill", FIXE, "Amber edge: wall the scan missed.\nVerify before building to it"), ("dot", FXN, "S  New 3 in. drain stack"), ("AP", "#8a6a00", "Access panel 12 x 12 in. behind the\ntub valve, on the side shown"), ("3", NEWW, "Keynote (list below)")]


def arch_sheet(pdf, number, fl):
    L = LV[fl]
    beds = sum(1 for r in L["rooms"] if r["kind"] == "bed"); baths = sum(1 for r in L["rooms"] if r["kind"] == "bath")
    fig, bg, ax = bsheet(number, f"{L['name']}: floor plan, walls and doors", fl,
                         [("This level", [f"{beds} bedrooms, {baths} baths." if fl != 5 else "2 bedrooms, 1 bath here; 2 bedrooms and", "Red = build. Dashed = remove." if fl != 5 else "2 baths in the attic. Red = build.",
                                          "Full gut: all finishes, wiring, pipes, ducts,", "fixtures, cabinets and doors are new.", "Grey walls keep their framing only.", "Furniture is for scale only."]),
                          ("General", ["Dimensions are clear, finish face to finish", "face. Hold the sizes marked; verify the", "rest on site before framing.",
                                       "New walls 2x4 at 16 in. o.c.; 2x6 where a", "tub valve, toilet or the stack is in the wall.", "Bath walls: cement board at tubs, moisture-",
                                       "resistant board elsewhere.", "Headers over every new opening; any wall", "that may be bearing is flagged: shore and", "size the header before cutting.",
                                       "Bedroom doors 2'-6\" min."]),
                          ("New doors (all 6'-8\" high)", [f"{d[0]}   {d[7].replace(' x 6' + chr(39) + '-8' + chr(34), '')}   {d[8]}"[:46] for d in sorted(L["doors"] + [(b[0], 0, 0, 0, 0, 0, 0, b[6], b[7]) for b in L["bifolds"]]) if d[7]])], ALEG)
    draw_base(ax, fl, "arch")
    tp = L.get("tagpos", {})
    for d in L["doors"]:
        if d[7]:
            x, y = tp.get(d[0]) or (((d[3] + d[4]) / 2, d[2] + d[6] * 0.9) if d[1] == "h" else (d[2] + d[6] * 0.9, (d[3] + d[4]) / 2))
            ax.text(x, y, d[0], fontsize=3.6, color=NEWW, ha="center", va="center", zorder=13, gid="tag", bbox=dict(boxstyle="round,pad=0.15", fc="white", ec=NEWW, lw=0.5))
    for b in L["bifolds"]:
        x, y = tp.get(b[0]) or (((b[3] + b[4]) / 2, b[2] + b[5] * 1.0) if b[1] == "h" else (b[2] + b[5] * 1.0, (b[3] + b[4]) / 2))
        ax.text(x, y, b[0], fontsize=3.6, color=NEWW, ha="center", va="center", zorder=13, gid="tag", bbox=dict(boxstyle="round,pad=0.15", fc="white", ec=NEWW, lw=0.5))
    for i, d in enumerate(L["dims"]):
        dim(ax, *d[:4], at=d[4] if len(d) > 4 else 0.5, gid=f"dim:{i}")
    lead = L.get("lead", {}); ax._leaders = {n: (p, lead[n]) for n, p, _t in L["notes"] if n in lead}
    for n, (x, y), _t in L["notes"]:
        keynote(ax, n, x, y, to=lead.get(n))
    y = getattr(fig, "_legend_end", 8.0) - 0.15
    bg.text(10.6, y, "KEYNOTES", fontsize=7, fontweight="bold", color=INK, va="center"); y -= 0.24
    for n, _p, t in L["notes"]:
        bg.text(10.68, y, str(n), fontsize=5.6, color=NEWW, fontweight="bold", va="center", ha="center")
        for i, ln in enumerate(wrap(t, 56)):
            bg.text(10.85, y - i * 0.13, ln, fontsize=5.5, color=INK, va="center")
        y -= 0.13 * len(wrap(t, 56)) + 0.08
    bad = clarity(fig, ax, fl, bg)
    print(number, "label clashes:", len(bad))
    for m in bad:
        print("   ", m)
        if "' at (" in m and m.split("'")[1].isdigit() and CHECK_HINTS:
            xy = m.split(" at (")[1].split(")")[0].split(","); print("        nearest clear spot:", free_spot(ax, fig, fl, float(xy[0]), float(xy[1])))
    fig._clashes = bad
    save(fig, number, pdf)


SHEETS_A = [("A-101", "Lower flat: floor plan", lambda pdf: arch_sheet(pdf, "A-101", 3)), ("A-102", "Middle flat: floor plan", lambda pdf: arch_sheet(pdf, "A-102", 4)),
            ("A-103", "Upper flat main floor: floor plan", lambda pdf: arch_sheet(pdf, "A-103", 5)), ("A-104", "Attic: floor plan", lambda pdf: arch_sheet(pdf, "A-104", 6))]

if __name__ == "__main__":
    from matplotlib.backends.backend_pdf import PdfPages
    with PdfPages(os.path.join(HERE, "drawings", "_a_test.pdf")) as pdf:
        for n, t, fn in SHEETS_A:
            fn(pdf)
    print("ok")
