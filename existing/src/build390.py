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


def room(no, name, kind, rects, size, ceil, lab=None, new=False):
    r0 = rects[0]
    return dict(no=no, name=name, kind=kind, rects=rects, size=size, ceil=ceil, lab=lab or ((r0[0] + r0[2]) / 2, (r0[1] + r0[3]) / 2), new=new)


LV = {
    3: dict(name="Lower flat", view=((-3.5, 36.1), (-3, 30)), stairs=[], cut=[],
            ap=[(11.95, 1.6, 11.95, 2.8), (24.24, 2.7, 24.24, 3.9)],
            demo=[(12.85, 0.95, 13.35, 9.56), (13.1, 6.1, 16.5, 6.6), (16.0, 6.3, 16.5, 9.3), (15.9, 3.2, 17.45, 6.65), (17.4, 0.95, 18.4, 9.5), (12.6, 9.2, 24.2, 9.95),
                  (7.3, 26.0, 8.3, 26.75), (20.74, 13.45, 21.14, 15.75), (27.2, 12.75, 29.7, 13.15), (24.63, 4.08, 30.6, 4.56)],
            new=[V(12.2, 0.61, 9.9), Hh(0.78, 12.03, 13.3), V(17.7, 0.61, 9.9, T6), Hh(9.73, 12.03, 21.4), Hh(9.73, 24.07, 24.5), Hh(10.43, 1.62, 2.3), Hh(10.43, 6.9, 7.94), V(7.77, 10.43, 12.78),
                 (24.63, 1.97, 25.25, 4.8), (30.25, 2.14, 30.79, 4.48), V(30.42, 4.4, 7.26), V(24.46, 9.73, 12.95)],
            fix=[Hh(26.94, 19.0, 21.1), V(20.94, 26.2, 26.94), Hh(12.95, 20.94, 21.6), Hh(12.95, 24.1, 26.22)],
            doors=[("101", "v", 12.2, 6.5, 9.0, "lo", 1, "2'-6\" x 6'-8\"", "Bath 1, from bedroom 1"), ("102", "h", 12.95, 21.6, 24.1, "hi", 1, "2'-6\" x 6'-8\"", "Bedroom 2, from the hall"),
                   ("103", "h", 9.73, 21.4, 24.07, "hi", -1, "2'-8\" x 6'-8\"", "Laundry / mechanical, solid core"), ("106", "h", 12.95, 27.2, 29.7, "lo", -1, "2'-6\" x 6'-8\"", "Bath 2, from bedroom 2")],
            bifolds=[("104", "h", 10.43, 2.3, 6.9, -1, "4'-7\" bifold", "Closet, bedroom 1"), ("105", "v", 20.94, 13.45, 15.75, 1, "2'-4\" bifold", "Closet, bedroom 2")],
            rooms=[room("101", "Living room", "living", [(1.1, 13.12, 12.93, 26.77)], "11'-10\" x 13'-8\"", "7'-6\"", (7.0, 18.6)),
                   room("102", "Kitchen", "kitchen", [(13.27, 16.31, 20.77, 26.77)], "7'-6\" x 10'-5\"", "6'-10\"", (15.6, 21.5)),
                   room("103", "Bedroom 1", "bed", [(1.62, 0.95, 12.03, 10.26), (7.94, 10.26, 12.93, 12.78), (12.03, 9.9, 12.93, 10.26)], "10'-5\" x 9'-4\" + entry", "6'-10\"", (7.6, 8.8), True),
                   room("104", "Bedroom 2", "bed", [(21.11, 16.31, 30.25, 26.07), (21.11, 13.12, 26.05, 16.31)], "9'-2\" x 9'-9\" + entry 4'-11\" x 3'-2\"", "7'-1\"", (26.4, 18.4), True),
                   room("105", "Laundry / mechanical", "mech", [(17.95, 2.4, 24.29, 9.56)], "6'-4\" x 7'-2\"", "7'-0\"", (20.3, 6.3), True),
                   room("106", "Bath 1 (bedroom 1)", "bath", [(12.37, 0.95, 17.45, 9.56)], "5'-1\" x 8'-7\"", "7'-0\"", (14.0, 4.7), True),
                   room("107", "Hall", "hall", [(13.27, 9.9, 24.29, 12.78), (13.27, 12.78, 16.08, 16.14)], "2'-10\" wide", "7'-0\"", (18.2, 11.35)),
                   room("108", "Bath 2 (bedroom 2)", "bath", [(24.63, 4.64, 30.25, 12.78), (25.25, 2.14, 30.25, 4.64)], "5'-7\" x 8'-2\" + tub alcove", "6'-10\"", (28.3, 10.2), True),
                   room("109", "Closet (BR 2)", "closet", [(16.42, 13.12, 20.77, 15.97)], "", "", (18.6, 14.55), True),
                   room("111", "Dressing", "closet", [(26.39, 13.12, 30.25, 15.97)], "", "", (28.3, 15.2), True),
                   room("112", "Closet (BR 1)", "closet", [(1.62, 10.6, 7.6, 12.78)], "", "", (4.6, 11.9), True)],
            fx=[("tub", 12.41, 0.95, 17.41, 3.45, True), ("wc", 17.45, 5.0, "x-", True), ("van", 15.7, 6.4, 17.45, 8.4, True),
                ("tub", 25.25, 2.14, 30.25, 4.64, True), ("wc", 24.63, 6.4, "x+", True), ("van", 24.63, 8.3, 26.38, 11.3, True),
                ("fridge", 18.27, 16.4, 20.77, 19.15), ("range", 18.6, 19.15, 20.77, 21.65), ("dw", 18.69, 21.65, 20.77, 23.65), ("sinkbase", 18.69, 23.65, 20.77, 26.65),
                ("wdstack", 17.95, 7.3, 20.45, 9.56), ("furnace", 18.1, 2.5, 19.56, 4.9), ("wh", 20.6, 3.42), ("panel", 24.29, 4.8, 24.29, 6.8)],
            furn=[("bed", 4.6, 0.95, "y+"), ("night", 7.2, 0.95, 8.7, 2.45), ("desk", 10.03, 1.3, 12.03, 5.3), ("dresser", 8.0, 11.28, 10.4, 12.78),
                  ("bed", 21.11, 23.5, "x+"), ("desk", 21.11, 16.6, 23.11, 20.6), ("dresser", 28.75, 24.0, 30.25, 26.0),
                  ("couch", 9.4, 19.5, 12.4, 26.5, "x+"), ("tv", 1.1, 21.8, 2.5, 26.3), ("ctable", 5.0, 22.3, 7.0, 25.7), ("table", 4.0, 13.6, 9.0, 16.6)],
            notes=[(1, (14.9, 7.6), "Bath 1, private to bedroom 1: 60 in. tub, toilet, 24 in. vanity. Door from the bedroom only. Built where two closets and the chimney base were."),
                   (2, (11.2, 6.0), "New wall 11 in. inside the old one; the old wall comes out. Tub valve at this end, access panel AP on the bedroom side."),
                   (3, (16.9, 8.0), "2x6 wet wall with drain stack S. Chimney base removed; patch the floor."),
                   (4, (4.6, 9.6), "New closet for bedroom 1, 4'-7\" bifold."),
                   (5, (22.6, 3.3), "Laundry / mechanical room (the old bath): furnace and water heater on the south wall, stacked washer and dryer in the corner, new electrical panel on the east wall with 30 x 36 in. kept clear in front. 5/8 in. type X board. No sink."),
                   (6, (22.7, 8.3), "New 2'-8\" solid door, swings in against the east wall. The hall wall is rebuilt in one straight line."),
                   (7, (28.4, 7.2), "Bath 2, private to bedroom 2 (the old laundry): toilet, 36 in. vanity; the old storage closet becomes the 60 in. tub alcove with a 2x6 wet wall and access panel AP on the laundry side. The existing electrical panel here is removed."),
                   (8, (31.3, 5.8), "Old laundry outside door closed up and insulated (patch outside)."),
                   (9, (25.4, 11.3), "Old laundry doorway walled up."),
                   (10, (17.5, 15.2), "The old furnace closet becomes bedroom 2's closet: hall side closed, 2'-4\" bifold from the bedroom entry."),
                   (11, (22.8, 14.5), "Bedroom 2 entrance: new 2'-6\" door from the hall. Wall on each side not in the scan: verify."),
                   (12, (28.3, 13.6), "Old closet becomes the dressing area and the way into bath 2."),
                   (13, (27.6, 25.2), "Small high basement window only (photo): not an escape window. Bedroom 2 needs a larger window or an outside door."),
                   (14, (29.6, 22.7), "Door on this wall: closet or outside door? Verify.")],
            dims=[(12.37, 4.3, 17.45, 4.3), (15.2, 0.95, 15.2, 9.56), (1.62, 6.0, 12.03, 6.0), (24.63, 5.3, 30.25, 5.3), (27.6, 4.64, 27.6, 12.78), (17.95, 6.4, 24.29, 6.4), (23.0, 2.4, 23.0, 9.56),
                  (16.42, 13.6, 20.77, 13.6)]),
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
        ax.text((x0 + x1) / 2, (y0 + y1) / 2, name, fontsize=fs, color=col, ha="center", va="center", zorder=z + 0.2, rotation=90 if (y1 - y0) > 1.6 * (x1 - x0) else 0, linespacing=1.1)


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
    ax.text(x0 + w / 2 + dx * 0.7, y0 + h / 2 + dy * 0.7, "QUEEN\n5'-0\" x 6'-8\"", fontsize=3.3, color=col, ha="center", va="center", zorder=5.2, linespacing=1.15)
    return (x0, y0, x0 + w, y0 + h)


def s_couch(ax, x0, y0, x1, y1, back, col="#5b6470"):
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc="#eef0f2", ec=col, lw=0.6, zorder=5)); b = 0.7
    r = {"x-": (x0, y0, b, y1 - y0), "x+": (x1 - b, y0, b, y1 - y0), "y-": (x0, y0, x1 - x0, b), "y+": (x0, y1 - b, x1 - x0, b)}[back]
    ax.add_patch(Rectangle(r[:2], r[2], r[3], fc="#d5d9de", ec=col, lw=0.4, zorder=5.1))
    ax.text((x0 + x1) / 2, (y0 + y1) / 2, "COUCH 7'-0\"", fontsize=3.2, color=col, ha="center", va="center", zorder=5.2, rotation=90 if (y1 - y0) > (x1 - x0) else 0)


def dim(ax, x0, y0, x1, y1, off=0.0, fs=3.8):
    L = abs(x1 - x0) + abs(y1 - y0); t = ftin(round(L * 12) / 12)
    ax.plot([x0, x1], [y0, y1], color="#333", lw=0.35, zorder=11)
    for (a, b) in ((x0, y0), (x1, y1)):
        ax.plot([a - 0.16, a + 0.16], [b - 0.16, b + 0.16], color="#333", lw=0.55, zorder=11)
    hz = abs(x1 - x0) > abs(y1 - y0)
    ax.text((x0 + x1) / 2 + (0 if hz else off), (y0 + y1) / 2 + (off if hz else 0), t, fontsize=fs, color="#111", ha="center", va="center", rotation=0 if hz else 90, zorder=11.1,
            bbox=dict(fc="white", ec="none", pad=0.25, alpha=0.92))


def keynote(ax, n, x, y, col=NEWW):
    ax.add_patch(MPoly([(x - 0.55, y), (x, y + 0.55), (x + 0.55, y), (x, y - 0.55)], closed=True, fc="white", ec=col, lw=0.8, zorder=20))
    ax.text(x, y, str(n), fontsize=4.4, color=col, ha="center", va="center", fontweight="bold", zorder=21)


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
        rem = g["removed"] if newu is None else g["removed"].difference(newu.buffer(0.02))
        _fill(ax, rem, fc="none", ec=NEWW, lw=0.45, ls=(0, (2, 1.6)), zorder=3.8)
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
            ax.text((f[1] + f[3]) / 2, (f[2] + f[4]) / 2, "furnace + water heater\nhere today: remove", fontsize=3.2, color=NEWW if arch else "#8a9099", ha="center", va="center", zorder=6.1, linespacing=1.1)
        elif k == "sinkbase":
            s_box(ax, *f[1:5], "", FXE, "#f1f2f4"); x0, y0, x1, y1 = f[1:5]
            ax.add_patch(Rectangle((x0 + 0.25 * (x1 - x0), y0 + 0.2 * (y1 - y0)), 0.5 * (x1 - x0), 0.6 * (y1 - y0), fc="#eef4fb", ec=FXE, lw=0.5, zorder=6.2))
        elif k == "wdstack": s_box(ax, *f[1:5], "W/D\nstacked", FXE, "white", 3.2)
        elif k == "panel":
            x0, y0, x1, y1 = f[1:5]
            ax.plot([x0, x1], [y0, y1], color="#123a6b", lw=3.2, solid_capstyle="butt", zorder=9.4)
            if arch:
                dx = -3.0 if x0 == x1 else 0; dy = -3.0 if y0 == y1 else 0
                ax.add_patch(Rectangle((min(x0, x0 + dx), min(y0, y0 + dy) - (0.25 if x0 == x1 else 0)), abs(dx) or (x1 - x0), (abs(dy) or (y1 - y0)) + (0.5 if x0 == x1 else 0), fill=False, ec="#123a6b", lw=0.5, ls=(0, (3, 2)), zorder=9.3))
                ax.text(x0 + (dx / 2 if dx else (x1 - x0) / 2), y0 + (dy / 2 if dy else (y1 - y0) / 2), "PANEL\n30 x 36\nclear", fontsize=3.2, color="#123a6b", ha="center", va="center", zorder=9.5, linespacing=1.1)
        elif k == "washer": s_box(ax, *f[1:5], "W")
        elif k == "dryer": s_box(ax, *f[1:5], "D")
        elif k == "lsink": s_van(ax, *f[1:5], FXE)
        elif k == "furnace": s_box(ax, *f[1:5], "F", MECHC, "#f3e9f7", 4.0)
        elif k == "wh":
            ax.add_patch(plt.Circle((f[1], f[2]), 0.92, fc="#f3e9f7", ec=MECHC, lw=0.7, zorder=6)); ax.text(f[1], f[2], "WH", fontsize=3.6, color=MECHC, ha="center", va="center", zorder=6.2, fontweight="bold")
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
        for (x0, y0, x1, y1) in L.get("ap", []):
            ax.plot([x0, x1], [y0, y1], color="#c79a00", lw=2.6, solid_capstyle="butt", zorder=9.5)
            ax.text((x0 + x1) / 2 + (0.45 if x0 == x1 else 0), (y0 + y1) / 2 + (0.45 if y0 == y1 else 0), "AP", fontsize=3.4, color="#8a6a00", ha="center", va="center", fontweight="bold", zorder=9.6)
    ax.add_patch(plt.Circle(STACK if fl != 3 else (17.68, 8.9), 0.28, fc="white", ec=FXN if arch else "#8a9099", lw=0.9, zorder=9))
    for r in L["rooms"]:
        x, y = r["lab"]
        if arch:
            big = r["kind"] not in ("closet",)
            col = NEWW if r["new"] else INK
            ax.text(x, y + (0.5 if big else 0), (r["name"] if not big else f"{r['name'].upper()}"), fontsize=4.6 if big else 3.6, fontweight="bold", color=col, ha="center", va="center", zorder=12,
                    bbox=dict(fc="white", ec="none", pad=0.4, alpha=0.85))
            if big:
                ax.text(x, y - 0.25, r["no"] + ((" · " + r["size"]) if r["size"] else ""), fontsize=3.7, color=col, ha="center", va="center", zorder=12, bbox=dict(fc="white", ec="none", pad=0.3, alpha=0.85))
                if r["ceil"]:
                    ax.text(x, y - 0.9, "clg " + r["ceil"], fontsize=3.4, color=GREY, ha="center", va="center", zorder=12, bbox=dict(fc="white", ec="none", pad=0.25, alpha=0.85))
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
        y = 9.9
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


# ---------------------------------------------------------------------------------------------- architectural sheets
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
                                       "Doors 6'-8\" high. Bedroom doors 2'-6\" min."])], ALEG)
    draw_base(ax, fl, "arch")
    for d in L["doors"]:
        if d[7]:
            x, y = ((d[3] + d[4]) / 2, d[2] + d[6] * 0.9) if d[1] == "h" else (d[2] + d[6] * 0.9, (d[3] + d[4]) / 2)
            ax.text(x, y, d[0], fontsize=3.6, color=NEWW, ha="center", va="center", zorder=13, bbox=dict(boxstyle="round,pad=0.15", fc="white", ec=NEWW, lw=0.5))
    for b in L["bifolds"]:
        x, y = ((b[3] + b[4]) / 2, b[2] + b[5] * 1.0) if b[1] == "h" else (b[2] + b[5] * 1.0, (b[3] + b[4]) / 2)
        ax.text(x, y, b[0], fontsize=3.6, color=NEWW, ha="center", va="center", zorder=13, bbox=dict(boxstyle="round,pad=0.15", fc="white", ec=NEWW, lw=0.5))
    for (x0, y0, x1, y1) in L["dims"]:
        dim(ax, x0, y0, x1, y1)
    for n, (x, y), _t in L["notes"]:
        keynote(ax, n, x, y)
    y = getattr(fig, "_legend_end", 8.0) - 0.15
    bg.text(10.6, y, "KEYNOTES", fontsize=7, fontweight="bold", color=INK, va="center"); y -= 0.24
    for n, _p, t in L["notes"]:
        bg.text(10.68, y, str(n), fontsize=5.6, color=NEWW, fontweight="bold", va="center", ha="center")
        for i, ln in enumerate(wrap(t, 44)):
            bg.text(10.85, y - i * 0.13, ln, fontsize=5.5, color=INK, va="center")
        y -= 0.13 * len(wrap(t, 44)) + 0.08
    y -= 0.1
    bg.text(10.6, y, "NEW DOORS", fontsize=7, fontweight="bold", color=INK, va="center"); y -= 0.22
    seen = set()
    for d in L["doors"] + [(b[0], 0, 0, 0, 0, 0, 0, b[6], b[7]) for b in L["bifolds"]]:
        if d[0] in seen or not d[7]: continue
        seen.add(d[0])
        bg.text(10.6, y, d[0], fontsize=5.5, color=NEWW, fontweight="bold", va="center"); bg.text(10.95, y, f"{d[7]}  {d[8]}", fontsize=5.4, color=INK, va="center"); y -= 0.14
    save(fig, number, pdf)


SHEETS_A = [("A-101", "Lower flat: floor plan", lambda pdf: arch_sheet(pdf, "A-101", 3)), ("A-102", "Middle flat: floor plan", lambda pdf: arch_sheet(pdf, "A-102", 4)),
            ("A-103", "Upper flat main floor: floor plan", lambda pdf: arch_sheet(pdf, "A-103", 5)), ("A-104", "Attic: floor plan", lambda pdf: arch_sheet(pdf, "A-104", 6))]

if __name__ == "__main__":
    from matplotlib.backends.backend_pdf import PdfPages
    with PdfPages(os.path.join(HERE, "drawings", "_a_test.pdf")) as pdf:
        for n, t, fn in SHEETS_A:
            fn(pdf)
    print("ok")
