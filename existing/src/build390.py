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
    equipment="owner's videos: lower flat furnace closet with louvered doors beside the kitchen (room 109); middle flat furnace and water heater in the louvered closet at the south end of the hall, with the electrical panel on the hall wall beside it; a fireplace mantel on the chimney wall of old Room A",
    attic="rafters cut or separated in places; roof flashing lifted", lower="bedroom 2's only window is a small high basement window")
STACK = (17.3, 8.9)            # new 3 in. drain stack in the old chimney shaft, same spot on every level
CHIMNEY = (15.8, 6.2, 18.3, 9.3)


def V(x, y0, y1, t=T4): return (x - t / 2, min(y0, y1), x + t / 2, max(y0, y1))
def Hh(y, x0, x1, t=T4): return (min(x0, x1), y - t / 2, max(x0, x1), y + t / 2)


def Dg(x0, y0, x1, y1, t=T4):
    """A wall running at an angle from (x0, y0) to (x1, y1), t thick: its four corners."""
    dx, dy = x1 - x0, y1 - y0; n = math.hypot(dx, dy); ox, oy = -dy / n * t / 2, dx / n * t / 2
    return [(x0 + ox, y0 + oy), (x1 + ox, y1 + oy), (x1 - ox, y1 - oy), (x0 - ox, y0 - oy)]


def wshape(r):
    """Shapely shape of one wall entry: (x0, y0, x1, y1) rectangle, or a list of corner points for an angled wall."""
    return Polygon(r) if isinstance(r[0], (tuple, list)) else box(*r)


def room(no, name, kind, rects, size, ceil, lab=None, new=False, disp=None, compact=False, plansize=True):
    """disp: shorter name to print on the plan; compact: two-line label for a tight room; plansize=False: leave the size off the plan label
    (dimension strings or a keynote give it instead)."""
    r0 = rects[0]
    return dict(no=no, name=name, kind=kind, rects=rects, size=size, ceil=ceil, lab=lab or ((r0[0] + r0[2]) / 2, (r0[1] + r0[3]) / 2), new=new, disp=disp, compact=compact, plansize=plansize)


LV = {
    3: dict(name="Lower flat", view=((-3.5, 36.1), (-3, 30)), stairs=[],
            cut=[(30.25, 4.23, 30.58, 6.89), (16.09, 13.5, 16.42, 15.6),      # walled-up openings: old laundry outside door (scan), furnace closet door (owner's video; position to verify)
                 (7.3, 26.0, 8.3, 26.75)],                                    # stub the phone scan drew beside tall shelving on the living room wall: not a wall
            # hall south wall rebuilt with its hall face at y = 9.72 (the existing jamb of the bedroom 1 door): hall 3'-0" clear
            ap=[(11.95, 1.6, 11.95, 2.8, -1), (24.24, 2.8, 24.24, 4.0, -1)],
            demo=[(12.85, 0.95, 13.35, 9.56), (13.1, 6.1, 16.5, 6.6), (16.0, 6.3, 16.5, 9.3), (15.9, 3.2, 17.45, 6.65), (17.4, 0.95, 18.4, 9.5), (12.6, 9.2, 24.2, 9.95),
                  (20.74, 13.45, 21.14, 15.75), (27.2, 12.75, 29.7, 13.15), (24.63, 4.08, 30.6, 4.56),
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
            tagpos={"105": (20.15, 15.2), "101": (13.9, 8.2)},
            rooms=[room("101", "Living room", "living", [(1.1, 13.12, 12.93, 26.77)], "11'-10\" x 13'-8\"", "7'-6\"", (7.0, 18.6)),
                   room("102", "Kitchen", "kitchen", [(13.27, 16.31, 20.77, 26.77)], "7'-6\" x 10'-5\"", "6'-10\"", (15.6, 21.5)),
                   room("103", "Bedroom 1", "bed", [(1.62, 0.95, 12.03, 10.26), (7.94, 10.26, 12.93, 12.78), (12.03, 9.72, 12.93, 10.26)], "10'-5\" x 9'-4\" + entry", "6'-10\"", (8.58, 6.3), True),
                   room("104", "Bedroom 2", "bed", [(21.11, 13.12, 30.25, 26.07)], "9'-2\" x 12'-11\"", "7'-1\"", (24.6, 17.6), True),
                   room("105", "Laundry / mechanical", "mech", [(17.95, 2.4, 24.29, 9.38)], "6'-4\" x 7'-0\"", "7'-0\"", (22.5, 5.9), True, disp="LAUNDRY / MECH.", compact=True),
                   room("106", "Bath 1 (bedroom 1)", "bath", [(12.37, 0.95, 17.45, 9.38)], "5'-1\" x 8'-5\"", "7'-0\"", (14.2, 5.2), True, disp="BATH 1", plansize=False),
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
            notes=[(1, (14.1, 2.2), "Bath 1, private to bedroom 1: 60 in. tub, toilet, 24 in. vanity. Built where two closets and the chimney base were. Door opens back against the hall wall."),
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
                   (17, (14.7, 14.55), "Furnace closet door walled up (position from the video: verify)."),
                   (18, (8.3, 25.6), "Tall shelving hides this wall in the scans. The boxed-out section in the two flats above is right over it: check here for a pipe chase or old flue, and whether the window is real.")],
            dims=[(12.37, 3.85, 17.45, 3.85, 0.72), (15.0, 0.95, 15.0, 9.38, 0.8), (1.62, 8.6, 12.03, 8.6, 0.45), (24.63, 5.2, 30.25, 5.2, 0.62), (27.0, 4.64, 27.0, 12.78, 0.5),
                  (17.95, 9.09, 24.29, 9.09, 0.2), (20.8, 2.4, 20.8, 9.38, 0.72), (16.42, 13.6, 20.77, 13.6), (21.11, 15.7, 30.25, 15.7, 0.5), (30.0, 13.12, 30.0, 26.07, 0.62)]),
    4: dict(name="Middle flat", view=((-2.5, 37.1), (-3, 30)),
            # As found (3D scan + owner's video): furnace and water heater stand in the louvered closet at the south end of the hall, the panel is on
            # the hall wall, the small room beside bedroom 1's door is bedroom 1's closet, and bedroom 2's closet is on the outside wall.
            # The bedroom side (x < 17) is drawn from wall faces measured in the straightened 3D scan, not from the phone-scan floor plan: that plan
            # assumed 4 in. walls everywhere, but several walls here are 7 to 12 in. thick, and it drew the bedroom side about 1'-6" too narrow.
            # House inside width 26'-10" on both sides; the outside walls are straight (aerial photo); the front is an angled bay with a window each side.
            rescan=dict(clear=[(-0.6, -0.2, 17.19, 28.0), (17.19, 17.3, 19.51, 17.75), (17.19, 21.25, 19.51, 21.7)],
                        walls=[(-0.29, 0.20, 0.05, 27.72), (-0.29, 0.20, 15.35, 0.54), (-0.29, 27.39, 17.19, 27.72),                      # outside walls
                               (7.40, 26.04, 10.45, 26.37), (7.40, 26.04, 7.73, 27.39), (10.12, 26.04, 10.45, 27.39),                      # boxed projection in bedroom 1
                               (9.65, 0.54, 10.25, 13.81), (0.05, 13.81, 10.25, 14.36), (10.25, 13.55, 12.95, 14.36),                      # bedroom 2 right wall; its top wall; hall north wall
                               (5.90, 14.36, 6.22, 19.63), (5.90, 19.11, 13.0, 19.63), (12.27, 13.55, 13.0, 19.63),                        # bath 1: west, north, east (thick) walls
                               (10.25, 4.14, 15.35, 4.50), (15.0, 0.54, 15.35, 4.50), (10.25, 7.80, 14.45, 8.10),                          # bedroom 2's old closet; louvered closet front
                               (14.45, 8.10, 14.78, 9.85), (14.45, 9.52, 16.0, 9.85), (16.0, 9.52, 17.19, 14.30), (15.5, 13.55, 16.0, 14.36),   # chimney enclosure; thick wall hall / laundry
                               (13.0, 17.68, 19.52, 18.01), (15.5, 18.01, 15.9, 21.63), (15.5, 21.30, 19.52, 21.63), (18.8, 18.01, 19.52, 21.30),   # passage north wall; bedroom 1's closet
                               (15.9, 21.63, 16.85, 27.39)]),                                                                              # thick wall between bedroom 1 and the stair
            floor=[(0.05, 0.54, 9.65, 13.81), (0.05, 14.36, 5.9, 19.63), (0.05, 19.63, 15.9, 27.39), (6.22, 14.36, 12.27, 19.11), (10.25, 0.54, 18.74, 9.52), (10.25, 9.85, 16.0, 13.55),
                   (13.0, 14.36, 17.2, 17.68), (13.0, 18.01, 15.5, 19.63), (15.9, 18.01, 18.8, 21.3)],
            cut=[(12.27, 14.6, 13.0, 17.2), (9.65, 8.05, 10.25, 10.4),                                    # old bath door; old bedroom 2 door (walled up: drawn as new wall)
                 (16.86, 10.4, 18.3, 11.4), (18.72, 9.71, 19.9, 11.4), (29.0, 13.42, 31.05, 14.84),          # diagonals drawn by the phone-scan plan that the 3D scan does not show
                 (31.41, 0.1, 33.7, 3.9)],                                                                   # its attempt at the south-east corner (replaced by the bay wall below)
            ap=[(16.9, 6.09, 18.1, 6.09, 1), (5.9, 19.68, 7.1, 19.68, 1)],
            # stair to the upper flat, from the 3D scan: 7 risers west along the north wall, landing, 9 risers south; the top of it passes over the closet
            stairs=[(19.9, 24.7, 24.5, 27.39, "x-", "UP", 0.767), (16.85, 24.7, 19.9, 27.39, "x-", "", 0), (16.85, 21.63, 19.52, 24.7, "y-", "UP", 0.64)],
            above=[(16.85, 19.6, 19.52, 21.3, "stair\nabove")],
            win=[Dg(32.2, 3.13, 33.8, 4.67, 0.3), (-0.29, 8.5, 0.05, 11.2), (5.83, 0.20, 7.91, 0.54), (4.0, 27.39, 6.4, 27.72)],
            mask=[[(31.4, -0.2), (35.6, -0.2), (35.6, 5.7), (34.9, 5.7), (31.35, 2.2)]],          # outside the bay: not floor
            demo=[(10.27, 4.12, 15.37, 4.52), (14.98, 0.56, 15.37, 4.52), (10.27, 7.78, 14.47, 8.12), (14.43, 8.12, 14.8, 9.5), (14.43, 9.5, 16.0, 9.87),
                  (5.88, 14.38, 6.24, 19.09)],
            new=[Hh(5.79, 10.25, 18.74, T6), V(12.67, 6.04, 9.52), Hh(9.685, 10.25, 12.95), Hh(9.685, 17.19, 18.74),
                 (9.65, 9.3, 10.25, 10.3), (12.27, 14.6, 13.0, 17.2), V(5.105, 14.36, 19.63), Hh(19.37, 4.94, 5.92, 0.52)],
            fix=[V(31.23, 0.2, 2.35), Dg(31.2, 2.17, 34.79, 5.63), Hh(0.37, 15.3, 18.95), V(31.23, 16.1, 17.9), Hh(15.0, 29.4, 31.23), V(18.91, 9.7, 11.41)],
            doors=[("200", "v", 34.76, 6.49, 9.17, "lo", -1, "2'-8\" x 6'-8\"", "Flat entrance (existing: verify)"),
                   ("201", "v", 9.95, 10.3, 12.8, "hi", -1, "2'-6\" x 6'-8\"", "Bedroom 2, from the hall"),
                   ("202", "v", 9.95, 0.9, 3.4, "lo", 1, "2'-6\" x 6'-8\"", "Bath 2, from bedroom 2"),
                   ("203", "h", 9.685, 12.95, 14.45, "lo", 1, "3'-0\" pair x 6'-8\"", "Mechanical, solid core"), ("203", "h", 9.685, 14.45, 15.95, "hi", 1, "", ""),
                   ("205", "h", 19.37, 9.7, 12.2, "hi", -1, "2'-6\" x 6'-8\"", "Bath 1, from bedroom 1"),
                   ("206", "h", 17.845, 13.08, 15.42, "lo", 1, "2'-4\" x 6'-8\"", "Bedroom 1 (existing opening)"),
                   ("208", "v", 31.23, 22.1, 24.77, "lo", -1, "2'-8\" x 6'-8\"", "Upper flat entrance (existing)")],
            bifolds=[("204", "v", 9.95, 6.3, 9.3, -1, "3'-0\" bifold", "Closet, bedroom 2"), ("207", "v", 15.7, 18.6, 21.1, -1, "2'-6\" bifold", "Closet, bedroom 1")],
            rooms=[room("201", "Living room", "living", [(19.07, 0.54, 34.59, 11.4), (22.17, 11.4, 31.06, 13.64)], "15'-6\" x 10'-10\" + bay", "8'-8\"", (26.5, 9.6)),
                   room("202", "Kitchen", "kitchen", [(19.86, 13.64, 31.06, 20.72)], "11'-2\" x 7'-1\"", "7'-4\"", (25.5, 16.6)),
                   room("203", "Bedroom 1", "bed", [(0.05, 19.63, 15.9, 27.39), (0.05, 14.36, 4.94, 19.63), (13.0, 18.01, 15.5, 19.63)], "15'-10\" x 7'-9\" + alcove", "7'-9\"", (10.4, 22.3)),
                   room("204", "Bedroom 2", "bed", [(0.05, 0.54, 9.65, 13.81)], "9'-7\" x 13'-3\"", "8'-10\"", (5.0, 2.2)),
                   room("205", "Bath 1 (bedroom 1)", "bath", [(5.27, 14.36, 12.27, 19.11)], "7'-0\" x 4'-9\"", "7'-4\"", (9.1, 17.75), True, disp="BATH 1"),
                   room("206", "Bath 2 (bedroom 2)", "bath", [(10.25, 0.54, 18.74, 5.54)], "8'-6\" x 5'-0\"", "8'-0\"", (13.7, 2.0), True, disp="BATH 2"),
                   room("207", "Hall", "hall", [(10.25, 9.85, 16.0, 13.55)], "5'-9\" x 3'-8\"", "7'-0\"", (11.75, 12.35)),
                   room("208", "Mechanical", "mech", [(12.83, 6.04, 18.74, 9.52)], "5'-11\" x 3'-6\"", "", (15.9, 8.75), True, disp="MECH.", compact=True, plansize=False),
                   room("209", "Laundry", "laundry", [(17.17, 11.74, 21.7, 13.64)], "", "", (19.45, 15.2)),
                   room("210", "Passage", "hall", [(13.0, 14.36, 19.5, 17.68)], "3'-4\" wide", "7'-4\"", (14.9, 16.0)),
                   room("211", "Closet (BR 2)", "closet", [(10.25, 6.04, 12.5, 9.52)], "", "", (11.37, 8.3), True),
                   room("212", "Closet (BR 1)", "closet", [(15.9, 18.01, 18.8, 21.3)], "", "", (17.6, 18.45)),
                   room("213", "Stair hall (upper flat)", "stair", [(19.86, 21.06, 31.06, 27.38)], "", "8'-9\"", (25.6, 22.9))],
            fx=[("tub", 16.24, 0.54, 18.74, 5.54, True), ("wc", 14.95, 5.54, "y-", True), ("van", 10.6, 3.79, 13.6, 5.54, True),
                ("tub", 5.27, 14.36, 7.77, 19.11, True), ("wc", 9.02, 14.36, "y+", True), ("van", 10.27, 14.36, 12.27, 16.11, True),
                ("fridge", 19.9, 18.22, 22.9, 20.72), ("dw", 22.9, 18.64, 24.9, 20.72), ("base", 24.9, 18.64, 25.9, 20.72), ("sinkbase", 25.9, 18.64, 28.9, 20.72), ("base", 28.9, 18.64, 31.06, 20.72),
                ("base", 28.98, 17.7, 31.06, 18.64), ("range", 28.9, 15.2, 31.06, 17.7),
                ("washer", 17.2, 11.76, 19.45, 14.3), ("dryer", 19.45, 11.76, 21.7, 14.3),
                ("furnace", 13.0, 6.14, 14.46, 8.56), ("wh", 15.45, 7.05), ("panel", 16.0, 11.8, 16.0, 13.05, -1, -0.3)],
            furn=[("bed", 0.05, 7.2, "x+"), ("night", 0.05, 9.8, 1.55, 11.3), ("desk", 1.0, 11.81, 5.0, 13.81), ("dresser", 0.05, 0.54, 1.55, 3.54),
                  ("bed", 0.05, 24.89, "x+"), ("night", 0.05, 20.85, 1.55, 22.35), ("desk", 11.0, 25.39, 15.0, 27.39), ("dresser", 0.05, 14.6, 1.55, 17.6),      # bedroom 1: bed along the outside wall, before the projection
                  ("couch", 19.2, 2.0, 22.2, 9.0, "x-"), ("tv", 28.2, 13.35, 30.9, 14.75), ("ctable", 24.5, 3.5, 26.5, 7.5), ("table", 28.2, 0.9, 30.9, 3.6)],     # TV and table where the video shows them
            tagpos={"207": (16.6, 20.75), "204": (10.75, 7.55), "201": (9.25, 11.0)},
            lead={16: (33.0, 3.9)},
            notes=[(1, (17.5, 3.0), "Bath 2, private to bedroom 2, where its old closet and the old furnace closet were: 60 in. tub, toilet, 36 in. vanity. Door is the old closet doorway widened to 2'-6\"."),
                   (2, (17.95, 7.35), "New 2x6 wet wall. Tub valve at this end; access panel AP in the mechanical closet."),
                   (3, (17.5, 1.35), "Not seen by the scan. Bath 2 is drawn 8'-6\" long and needs at least 7'-6\": open up and measure before ordering the tub."),
                   (4, (14.2, 11.6), "Mechanical closet, 5'-11\" x 3'-6\". Furnace and water heater stay at this end of the hall, as today (video). Sealed-combustion units vented through the south wall. Pair of solid doors; 5/8 in. type X board."),
                   (5, (18.1, 8.6), "Chimney removed, roof to lower flat. Its place is the pipe chase: drain stack S and risers."),
                   (6, (7.7, 7.3), "New closet for bedroom 2, 3'-0\" bifold, in the old south end of the hall."),
                   (7, (6.3, 11.0), "Bedroom 2's door moves 2 ft north in the same wall; the old opening becomes closet front."),
                   (8, (13.75, 12.75), "Electrical panel stays on this wall (video; verify). 30 x 36 in. kept clear."),
                   (9, (6.95, 15.7), "Bath 1 becomes private to bedroom 1: door to the passage walled up, new 2'-6\" door from the bedroom. Tub stays (60 in. between studs). Toilet and 24 in. vanity."),
                   (10, (3.9, 17.7), "Wall moves 11 in. west so tub, toilet and vanity each get full clearance. It may carry load: check before moving."),
                   (11, (8.0, 20.4), "Access panel AP for the tub valve: keep clear of furniture."),
                   (12, (11.6, 20.6), "Bedroom 1 door: existing opening, 2'-4\" door (the most that fits)."),
                   (13, (16.6, 19.3), "Bedroom 1's closet, as today: about 2'-11\" x 3'-3\", under the top of the upper flat's stair (8 ft and up over it). Scan sees in through the doorway only: verify. New 2'-6\" bifold."),
                   (14, (19.45, 16.6), "Washer and dryer stay in the open recess. Doors do not fit: the 3'-4\" passage would drop under 36 in."),
                   (15, (31.4, 7.8), "Flat entrance (existing: verify size and swing)."),
                   (16, (31.3, 5.7), "Shape from the 3D scan (the phone-scan plan missed it or drew it at an angle): verify. Angled bay, a window each side of the door."),
                   (16, (30.3, 12.6), ""), (16, (20.2, 10.4), ""),
                   (17, (32.2, 19.2), "Window over the counter (photo); the amber piece is wall behind the range: verify."),
                   (18, (29.4, 25.5), "Upper flat's entrance from the porch: 2'-8\" door, seen in the 3D scan."),
                   (19, (22.2, 23.2), "Stair to the upper flat (existing, for reference): 7 risers, landing, then 9 risers passing over bedroom 1's closet."),
                   (20, (17.95, 10.65), "Closed-in space the scan could not see into: check when the walls are open."),
                   (21, (8.9, 25.2), "Boxed-out section, 3'-1\" x 1'-4\". A closed box sits over it by the upper flat's kitchen and bath: most likely their drain stack or an old flue. Keep it."),
                   (22, (7.9, 2.6), "Bedroom-side sizes are from the 3D scan (phone-scan plan was 6 to 11 in. off; walls up to 12 in. thick). Good to about 2 in.: tape-check."),
                   (22, (5.0, 21.3), "")],
            dims=[(10.25, 3.2, 16.24, 3.2, 0.3), (16.02, 0.54, 16.02, 5.54, 0.2), (10.7, 9.85, 10.7, 13.55, 0.25),
                  (5.27, 18.75, 12.27, 18.75, 0.5), (0.05, 19.2, 4.94, 19.2, 0.6), (10.25, 6.9, 12.5, 6.9, 0.5),
                  (0.05, 4.1, 9.65, 4.1, 0.4), (8.6, 0.54, 8.6, 13.81, 0.4), (0.05, 23.4, 15.9, 23.4, 0.55), (15.2, 19.63, 15.2, 27.39, 0.55)]),
    5: dict(name="Upper flat, main floor", view=((-3.5, 36.1), (-3, 30)), cut=[],
            # Drawn from wall faces measured in the 3D scan (27 Nov), checked against the owner's video. The phone-scan plan had the hall 5 in. too wide,
            # the bath 10 in. too wide and Room B 5 in. too wide, and showed neither stair correctly.
            # Stairs (3D scan): the stair from the entrance arrives heading south at y = 19.7; the attic stair starts beside Room B's door, 5 risers north to
            # a landing 3'-7" up across the outside wall, then 8 risers south over the stair down. The windows the phone scan put on this wall are the
            # landing window of the stair below.
            rescan=dict(clear=[(-1.0, -1.0, 33.0, 29.0)],
                        walls=[(-0.28, -0.13, 0.05, 27.43), (-0.28, -0.13, 31.53, 0.2), (31.2, -0.13, 31.53, 27.43), (-0.28, 27.1, 31.53, 27.43),                # outside walls
                               (0.05, 13.3, 12.4, 13.75), (15.0, 13.3, 20.75, 13.75), (23.25, 13.3, 31.2, 13.75),                                              # centre wall of the house
                               (15.35, 0.2, 15.65, 1.35), (15.35, 3.35, 15.65, 5.3), (15.35, 8.9, 15.65, 13.3), (15.65, 3.5, 17.85, 3.8),                      # living room east wall; coat closet back wall
                               (17.85, 0.2, 18.15, 6.0), (17.85, 9.6, 18.15, 13.3),                                                                            # old Room A west wall
                               (9.94, 17.1, 10.4, 27.1), (7.7, 23.3, 7.95, 27.1), (7.7, 23.3, 9.94, 23.55), (7.95, 25.45, 9.94, 25.7),                         # kitchen / bath wall; pantry and the closed box
                               (10.4, 17.1, 13.33, 17.8), (10.4, 19.3, 12.25, 19.6), (16.0, 17.1, 16.7, 27.1), (15.4, 24.6, 16.0, 27.1), (16.7, 22.5, 17.35, 27.1),   # bath walls; thick wall to the stair (furred out beside the attic flight)
                               (20.6, 20.2, 21.0, 24.0), (20.0, 20.2, 20.6, 22.5), (23.75, 13.75, 24.1, 15.05), (23.75, 17.55, 24.1, 27.1)]),                                            # wall between the stair flights; Room B wall
            floor=[(0.05, 0.2, 31.2, 27.1)],
            win=[(5.5, -0.13, 8.05, 0.2), (21.95, -0.13, 24.95, 0.2), (-0.28, 8.5, 0.05, 10.7), (-0.28, 16.15, 0.05, 18.65), (31.2, 5.0, 31.53, 7.6), (31.2, 19.4, 31.53, 21.6)],
            ap=[(9.4, 24.55, 9.4, 25.45, -1)],
            stairs=[(21.0, 21.0, 23.75, 24.0, "y+", "UP", 0.75), (17.35, 24.0, 23.75, 27.1, "x-", "", 0), (17.35, 22.5, 20.6, 24.0, "y-", "UP", 0.75), (16.7, 19.7, 20.0, 22.5, "y+", "DN", 0.64)],
            above=[(17.35, 18.8, 20.6, 22.5, "attic stair\nabove")],
            demo=[(17.83, 1.3, 18.17, 6.0), (17.83, 9.6, 18.17, 13.3), (16.3, 13.28, 19.97, 13.77), (25.15, 13.28, 30.15, 13.77),
                  (2.9, 13.28, 12.4, 13.77), (15.63, 3.48, 17.87, 3.82)],          # centre wall between kitchen and living room; coat closet back wall
            beams=[(2.9, 13.525, 15.0, 13.525, "NEW BEAM OVER")], posts=[(2.7, 13.525), (15.2, 13.525)],
            new=[Hh(9.535, 15.65, 20.57), V(20.4, 9.37, 13.3), Hh(11.135, 23.43, 31.2), V(23.6, 10.97, 13.3), Hh(7.635, 15.65, 17.85),
                 V(18.0, 6.0, 9.6, 0.3), V(15.5, 5.3, 8.9, 0.3), (15.35, 1.35, 15.65, 3.35)],
            fix=[],
            doors=[("301", "v", 23.925, 15.05, 17.55, "lo", 1, "2'-6\" x 6'-8\"", "Bedroom 4 (existing opening)"),
                   ("302", "h", 13.525, 16.3, 18.135, "lo", 1, "3'-8\" pair x 6'-8\"", "Mechanical, solid core"), ("302", "h", 13.525, 18.135, 19.97, "hi", 1, "", ""),
                   ("305", "h", 13.525, 20.75, 23.25, "hi", -1, "2'-6\" x 6'-8\"", "Bedroom 3 (existing opening)"),
                   ("306", "h", 17.45, 13.33, 16.0, "hi", 1, "2'-8\" x 6'-8\"", "Bath 1 (existing opening)")],
            bifolds=[("303", "v", 18.0, 1.3, 6.3, 1, "5'-0\" bifold", "Closet, bedroom 3"), ("304", "h", 13.525, 25.15, 30.15, 1, "5'-0\" bifold", "Closet, bedroom 4")],
            rooms=[room("301", "Living room", "living", [(0.05, 0.2, 15.35, 13.3)], "15'-4\" x 13'-1\", open to kitchen", "8'-2\"", (8.6, 1.9)),
                   room("302", "Kitchen", "kitchen", [(0.05, 13.75, 9.94, 27.1)], "9'-11\" x 13'-4\" with laundry", "7'-2\"", (4.9, 21.4)),
                   room("303", "Bedroom 3", "bed", [(18.15, 0.2, 31.2, 10.97), (20.57, 10.97, 23.43, 13.3)], "13'-1\" x 10'-9\" + entry", "8'-1\"", (22.0, 9.0), True),
                   room("304", "Bedroom 4", "bed", [(24.1, 13.75, 31.2, 27.1)], "7'-1\" x 13'-4\"", "7'-2\"", (27.3, 19.0), True),
                   room("305", "Bath 1", "bath", [(10.4, 17.8, 16.0, 27.1)], "5'-7\" x 9'-4\"", "8'-3\"", (12.05, 23.45)),
                   room("306", "Hall", "hall", [(15.0, 13.75, 23.75, 17.1), (16.7, 17.1, 23.75, 19.7), (20.0, 19.7, 23.75, 21.0)], "3'-4\" wide", "7'-5\"", (18.2, 16.2)),
                   room("312", "Stair", "stair", [(16.7, 19.7, 23.75, 27.1)], "", "", (20.5, 18.4)),
                   room("307", "Mechanical", "mech", [(15.65, 9.7, 20.23, 13.3)], "4'-7\" x 3'-7\"", "", (19.2, 12.75), True, disp="MECH.", compact=True, plansize=False),
                   room("308", "Laundry", "laundry", [(7.2, 18.4, 9.94, 23.0)], "", "", (6.0, 19.5)),
                   room("309", "Closet (BR 3)", "closet", [(15.65, 0.2, 17.85, 7.47)], "", "", (16.75, 4.4), True),
                   room("310", "Closet (BR 4)", "closet", [(23.77, 11.3, 31.2, 13.3)], "", "", (25.6, 12.3), True),
                   room("313", "Pantry", "closet", [(7.95, 23.55, 9.94, 25.45)], "", "", (8.75, 24.1))],
            fx=[("tub", 10.4, 24.6, 15.4, 27.1, True), ("van", 10.4, 20.3, 12.15, 22.3, True), ("wc", 16.0, 23.25, "x-", True),
                ("base", 0.05, 25.02, 2.13, 27.1), ("dw", 2.13, 25.02, 4.13, 27.1), ("sinkbase", 4.13, 25.02, 7.13, 27.1), ("base", 7.13, 25.02, 7.7, 27.1),
                ("base", 0.05, 23.02, 2.13, 25.02), ("range", 0.05, 20.52, 2.22, 23.02), ("base", 0.05, 16.3, 2.13, 20.52), ("fridge", 0.05, 13.8, 2.88, 16.3),
                ("washer", 7.2, 18.4, 9.9, 20.7), ("dryer", 7.2, 20.7, 9.9, 23.0), ("furnace", 16.4, 9.8, 17.86, 12.22), ("wh", 19.0, 10.75),
                ("panel", 15.35, 1.75, 15.35, 2.95, -1), ("xequip", 24.9, 24.9, 31.0, 26.9, "")],
            furn=[("couch", 0.25, 1.4, 3.25, 8.4, "x-"), ("tv", 13.95, 5.6, 15.35, 9.8), ("ctable", 6.0, 3.3, 8.0, 6.7), ("table", 5.5, 9.6, 10.5, 12.6),
                  ("bed", 31.2, 5.6, "x-"), ("night", 29.7, 8.3, 31.2, 9.8), ("desk", 19.9, 0.2, 23.9, 2.2), ("dresser", 25.5, 0.2, 28.5, 1.7),
                  ("bed", 28.7, 27.1, "y-"), ("desk", 29.2, 16.2, 31.2, 20.2)],
            tagpos={"301": (25.2, 15.9)}, lead={3: (16.0, 11.5), 15: (19.5, 25.6), 16: (16.35, 21.4), (7, 1): (25.5, 25.9), 19: (5.0, 13.9)},
            notes=[(1, (16.75, 6.3), "Chimney removed, roof to lower flat, with the mantels on both sides of it (video). Walls rebuilt flush (red). Patch floor, ceiling and roof."),
                   (2, (16.25, 8.6), "Old chimney shaft becomes the pipe and duct chase: drain stack S, ducts and wiring to the attic, furnace and water heater vents to the roof."),
                   (3, (14.6, 11.5), "Mechanical closet, 4'-7\" x 3'-7\": furnace and water heater move here from Room B. 5/8 in. type X board; pair of solid doors (1'-10\" leaves)."),
                   (4, (21.9, 14.8), "Centre wall of the house: it almost certainly carries the attic floor. The beam (19), the mechanical doors and bedroom 4's closet opening need one engineer's design before any of it is cut."),
                   (4, (29.6, 14.85), ""),
                   (5, (27.6, 12.3), "New closet for bedroom 4, 2'-0\" deep, taken from old Room A; 5'-0\" bifold through the centre wall."),
                   (6, (20.0, 5.6), "Bedroom 3's closet: the old coat closet plus the chimney's place, 7'-3\" long, 5'-0\" bifold."),
                   (7, (25.25, 18.2), "Bedroom 4 (old Room B) is 7'-1\" wide: a queen fits with a 2'-1\" aisle. The furnace and water heater here today (dashed) go. Existing door opening."),
                   (7, (25.5, 23.4), ""),
                   (8, (12.2, 18.55), "Bath 1 stays, all new: 60 in. tub, toilet and 21 in. vanity in today's positions. 2'-8\" door opens back against the wall."),
                   (9, (11.3, 26.0), "Tub valve at this end; access panel AP in the pantry. The wall between is about 11 in. thick: open it from the pantry side first."),
                   (10, (8.9, 26.4), "Closed-in box, not opened, over the boxed-out section in the middle flat's bedroom 1: likely a drain and vent stack or an old flue. Keep it."),
                   (11, (6.2, 24.1), "Pantry closet (existing): door and shelves to verify."),
                   (12, (6.2, 21.9), "Washer and dryer stay side by side here, as today."),
                   (13, (13.1, 2.35), "New panel on the living room wall; 30 x 36 in. kept clear, no furniture here. The meter corner is outside bedroom 3, about 16 ft along this side. Old panel not found in the video."),
                   (14, (22.4, 19.6), "Stairs, existing. Down to the entrance: 16 risers. Up to the attic: 5 risers, a landing 3'-7\" up, then 8 risers over the stair down; about 8 1/2 in. each."),
                   (15, (19.5, 28.35), "Attic stair landing. The window on this wall is at the landing below, under this floor."),
                   (16, (15.2, 21.4), "Thick wall between bath and stairs, with a closed-in strip beside the landing (grille in the video): likely the duct to the attic. Verify."),
                   (17, (16.75, 1.6), "Coat closet removed: door walled up (red); its space joins bedroom 3's closet."),
                   (18, (3.6, 11.4), "Room sizes are from the 3D scan; good to about 2 in.: tape-check."),
                   (19, (5.0, 15.1), "Wall between kitchen and living room removed (dashed): 9'-6\" of it, a 12'-1\" clear span with the old opening. New beam overhead on a post at each end, carried down through both flats below to footings: engineer to design. 2'-10\" of wall stays beside the fridge. Ceilings today: kitchen 7'-2\", living room 8'-2\".")],
            dims=[(10.4, 20.05, 16.0, 20.05, 0.2), (24.1, 20.31, 31.2, 20.31, 0.155), (24.55, 13.75, 24.55, 27.1, 0.42), (18.15, 2.75, 31.2, 2.75, 0.35), (24.22, 0.2, 24.22, 10.97, 0.85),
                  (24.1, 11.3, 24.1, 13.3, 0.5)]),
    6: dict(name="Attic (upper flat)", view=((-3.5, 36.1), (-3, 30)),
            # Drawn from the 3D scan (27 Nov), checked against the owner's video. The roof is a 10 in 12 gable with its eaves on the long sides: the
            # ceiling is flat at 7'-9" over almost all of both rooms and slopes only in the last 1'-6" along the west wall (5'-10" at the wall) and in
            # the recesses on the east side. The two bays are dormers with flat ceilings. Beyond the long walls are unfinished eave spaces.
            # The wall between bedroom 1 and the hall / bedroom 2 is about a foot thick (duct chase from below). Bedroom 1's door is in it at the hall;
            # bedroom 2's door closes the south end of the hall. Both baths back onto that thick wall, over the mechanical closet and chase below.
            rescan=dict(clear=[(-1.0, -1.0, 33.0, 29.0)],     # the whole floor
                        walls=[(-0.08, 4.97, 0.25, 21.28), (0.25, 7.52, 1.35, 7.85), (3.68, 7.52, 5.38, 7.85), (0.25, 4.97, 5.38, 5.3), (5.05, 2.02, 5.38, 7.85),          # bedroom 1: gable wall, east wall, closet
                               (5.05, 2.02, 11.45, 2.35), (11.12, 2.02, 11.45, 5.96), (11.12, 5.63, 15.45, 5.96), (0.25, 20.95, 17.2, 21.28),                          # its bay, recess wall and west wall
                               (16.35, 8.65, 17.45, 14.05), (16.35, 14.05, 17.2, 15.0), (16.6, 17.5, 17.2, 20.95), (16.87, 20.95, 17.2, 27.78),                        # thick wall; hall west wall
                               (16.87, 27.45, 23.98, 27.78), (23.65, 23.3, 23.98, 27.78), (20.45, 14.05, 20.87, 23.3), (20.45, 23.3, 23.98, 23.63), (23.65, 20.85, 23.98, 23.63),   # hall, stair well, alcove
                               (23.65, 20.85, 31.48, 21.18), (31.15, 4.57, 31.48, 21.18), (25.7, 7.0, 27.7, 7.33), (30.2, 7.0, 31.48, 7.33),                           # bedroom 2: west, gable and east walls
                               (26.67, 4.57, 27.0, 7.0), (26.67, 4.57, 31.48, 4.9), (19.57, 1.57, 19.9, 5.7), (19.57, 1.57, 26.03, 1.9), (25.7, 1.57, 26.03, 7.33),     # its closet and bay
                               Dg(19.9, 5.55, 18.3, 8.5, 0.33)]),                                                                                                      # angled wall beside the chimney
            floor=[(0.25, 7.85, 16.35, 20.95), (5.38, 2.35, 11.12, 7.85), (11.12, 5.96, 15.45, 8.65), (0.25, 5.3, 5.05, 7.52), (17.2, 14.2, 20.45, 27.45), (20.45, 23.63, 23.65, 27.45),
                   (17.45, 6.9, 31.15, 20.85), (19.9, 1.9, 25.7, 7.33), (20.87, 20.85, 23.65, 23.3), (27.0, 4.9, 31.15, 7.0)],
            win=[(-0.08, 12.68, 0.25, 15.03), (7.41, 2.02, 10.37, 2.35), (20.64, 1.57, 25.34, 1.9), (31.15, 10.5, 31.48, 15.87), (19.17, 27.45, 21.77, 27.78)],
            cut=[(20.43, 14.6, 20.89, 17.1)], demo=[(20.43, 14.6, 20.89, 17.1)],                               # new doorway for bedroom 2 in the hall wall
            ap=[(10.85, 12.1, 10.85, 13.3, -1), (22.95, 12.0, 22.95, 13.2, 1)],
            stairs=[(17.2, 18.8, 20.45, 24.0, "y+", "DN", 0.743), (17.2, 24.0, 23.65, 27.45, "x-", "", 0)],
            above=[(17.45, 24.25, 23.4, 27.2, "open to the stair below"), (21.05, 21.0, 23.65, 23.3, "shelves over\nstair bulkhead")],
            slopes=[(0.25, 20.2, 16.6, 20.2, "ceiling 6'-8\" on this line, 5'-10\" at the wall", (5.6, 20.57)), (23.98, 19.85, 31.15, 19.85, "", (0, 0)),
                    (11.35, 7.04, 13.2, 7.04, "", (0, 0))],
            new=[V(11.185, 5.96, 11.45), V(11.1, 11.45, 14.28, T6), Hh(14.115, 10.85, 16.35),                                              # bath A
                 V(15.615, 5.63, 8.65), Hh(8.485, 15.45, 19.9), Hh(5.795, 15.45, 18.3), V(18.135, 5.63, 8.65),                             # chase in the chimney's place
                 (17.45, 13.85, 20.45, 14.2), Hh(14.025, 20.45, 22.95), V(22.615, 6.57, 11.35), V(22.7, 11.35, 14.2, T6), Hh(6.735, 19.57, 22.78), V(19.735, 6.57, 8.65)],   # bath B
            fix=[],
            doors=[("401", "v", 11.185, 8.45, 10.95, "lo", 1, "2'-6\" x 6'-8\"", "Bath A, from bedroom 1"), ("402", "v", 22.615, 8.8, 11.3, "lo", -1, "2'-6\" x 6'-8\"", "Bath B, from bedroom 2"),
                   ("403", "v", 20.66, 14.6, 17.1, "lo", 1, "2'-6\" x 6'-8\"", "Bedroom 2 (new opening)"), ("404", "v", 16.9, 15.0, 17.5, "lo", -1, "2'-6\" x 6'-8\"", "Bedroom 1 (existing opening)"),
                   ("405", "h", 7.685, 1.35, 3.68, "lo", 1, "2'-4\" x 6'-8\"", "Closet, bedroom 1 (existing)"), ("406", "h", 7.165, 27.7, 30.2, "lo", 1, "2'-6\" x 6'-8\"", "Closet, bedroom 2 (existing)")],
            bifolds=[],
            rooms=[room("401", "Bedroom 1", "bed", [(0.25, 7.85, 10.85, 20.95), (10.85, 14.28, 16.35, 20.95), (5.38, 2.35, 11.12, 7.85)], "10'-7\" x 13'-1\" + 5'-6\" x 6'-8\" + bay", "7'-9\"", (6.2, 9.8), True),
                   room("402", "Bedroom 2", "bed", [(20.87, 14.2, 31.15, 20.85), (22.95, 7.33, 31.15, 14.2), (19.9, 1.9, 25.7, 7.33)], "10'-3\" x 6'-8\" + 8'-2\" x 6'-10\" + bay", "7'-9\"", (27.0, 11.6), True),
                   room("403", "Bath A (bedroom 1)", "bath", [(11.35, 8.65, 16.35, 13.95), (11.35, 5.96, 15.45, 8.65)], "5'-0\" x 8'-0\"", "7'-9\"", (14.35, 7.35), True, disp="BATH A"),
                   room("404", "Bath B (bedroom 2)", "bath", [(17.45, 8.65, 22.45, 13.85), (19.9, 6.9, 22.45, 8.65)], "5'-0\" x 5'-2\" + alcove", "7'-9\"", (21.5, 9.9), True, disp="BATH B", plansize=False),
                   room("405", "Stair hall", "stair", [(17.2, 14.2, 20.45, 18.8)], "", "7'-6\"", (18.8, 17.3)),
                   room("406", "Closet (BR 1)", "closet", [(0.25, 5.3, 5.05, 7.52)], "", "", (1.9, 6.4)),
                   room("407", "Closet (BR 2)", "closet", [(27.0, 4.9, 31.15, 7.0)], "", "", (28.4, 5.95))],
            fx=[("tub", 11.35, 11.45, 16.35, 13.95, True), ("wc", 16.35, 10.0, "x-", True), ("van", 11.35, 6.2, 13.1, 8.2, True),
                ("tub", 17.45, 11.35, 22.45, 13.85, True), ("wc", 17.45, 10.0, "x+", True), ("van", 19.95, 6.9, 21.95, 8.65, True)],
            furn=[("bed", 0.25, 13.85, "x+"), ("night", 0.25, 16.5, 1.75, 18.0), ("desk", 6.3, 2.4, 10.3, 4.4), ("dresser", 11.3, 14.28, 14.3, 15.78),
                  ("bed", 28.1, 20.85, "y-"), ("night", 24.0, 19.35, 25.5, 20.85), ("desk", 21.0, 1.95, 25.0, 3.95), ("dresser", 29.6, 9.1, 31.1, 12.1)],
            tagpos={"402": (23.45, 10.05)}, lead={4: (16.9, 12.6), 11: (18.0, 22.3)},
            notes=[(1, (16.9, 7.2), "Chimney removed through the roof; frame and sheath the hole, re-shingle. Its place is boxed in as the chase to the roof for the stack vent and the furnace and water heater vents."),
                   (2, (14.3, 12.7), "Bath A, private to bedroom 1: 60 in. tub, toilet and 21 in. vanity. Tub, toilet and door are under the flat ceiling; the vanity end is under the slope (6'-8\" at the dash-dot line)."),
                   (3, (21.3, 12.6), "Bath B, private to bedroom 2, 5'-0\" x 5'-2\" plus the vanity alcove: 60 in. tub, toilet, 24 in. vanity. Built where bedroom 2's entry was."),
                   (4, (18.5, 12.6), "Both baths back onto this thick wall, which stands over the mechanical closet and chase below: both toilets are on it and stack S is inside it."),
                   (5, (8.7, 12.7), "Tub valve at this end; access panel AP on the bedroom side: keep clear of furniture."), (5, (24.45, 12.4), ""),
                   (6, (18.8, 15.0), "Old bedroom 2 doorway walled up (red)."),
                   (7, (22.3, 15.5), "New 2'-6\" door for bedroom 2, cut into the hall wall; it opens back against the bath wall. Move the handrail end if it is in the way."),
                   (8, (13.3, 16.7), "Bedroom 1 door: existing opening, new 2'-6\" door hung to open back against the bath wall."),
                   (9, (4.0, 6.4), "Existing closet under the eave, sloping ceiling; new door. Its depth is not fully seen in the scan: verify."), (9, (30.3, 5.95), ""),
                   (10, (22.6, 20.0), "Built-in shelves over the stair bulkhead (video): keep."),
                   (11, (15.7, 23.2), "Stair down, existing: 8 risers to the landing, then 5 more. Open well beside it: check the guard is 36 in. high. Floor grille at the stair head today: keep a return-air path."),
                   (12, (4.0, 19.3), "Ceiling is flat at 7'-9\". Along this wall it slopes down in the last 1'-6\" (dash-dot line = 6'-8\")."), (12, (24.75, 18.4), ""),
                   (13, (6.5, 17.6), "Sizes are from the 3D scan; good to about 2 in.: tape-check. The spaces beyond the long walls are unfinished eaves, not drawn.")],
            dims=[(11.35, 11.2, 16.35, 11.2, 0.5), (17.45, 11.08, 22.45, 11.08, 0.3), (0.25, 11.0, 10.85, 11.0, 0.75), (9.6, 7.85, 9.6, 20.95, 0.7),
                  (22.95, 13.45, 31.15, 13.45, 0.5), (23.32, 14.2, 23.32, 20.85, 0.72)]),
}

# ---------------------------------------------------------------------------------------------- geometry
_G = {}


def geom(fl):
    """Existing walls (after removals), openings and windows of one level, as shapely / point lists in feet."""
    if fl in _G:
        return _G[fl]
    G, _ = sx.regularize(de.P390[str(fl)], de.T390(fl))
    L = LV[fl]
    demo = unary_union([wshape(r) for r in L["demo"]]) if L["demo"] else None
    walls = unary_union([Polygon(w["pts"]).buffer(0) for w in G["walls"] if len(w["pts"]) >= 4])
    rs = L.get("rescan")                                    # {"clear": [areas], "walls": [walls measured from the 3D scan]}
    if rs:
        clr = unary_union([box(*r) for r in rs["clear"]])
        walls = walls.difference(clr).union(unary_union([wshape(r) for r in rs["walls"]]))
        inside = lambda o: len(o["pts"]) >= 1 and clr.contains(Polygon([(q[0], q[1]) for q in o["pts"]]).centroid if len(o["pts"]) >= 3 else box(o["pts"][0][0] - .01, o["pts"][0][1] - .01, o["pts"][0][0] + .01, o["pts"][0][1] + .01).centroid)
        for k_ in ("doors", "openings", "windows"):
            G[k_] = [o for o in G[k_] if not inside(o)]
        G["arc_pts"] = [a for a in G.get("arc_pts", []) if not any(clr.contains(box(q[0] - .01, q[1] - .01, q[0] + .01, q[1] + .01).centroid) for q in a)]
    removed = walls.intersection(demo) if demo is not None else None
    if demo is not None:
        walls = walls.difference(demo)
    if L["cut"]:
        walls = walls.difference(unary_union([wshape(r) for r in L["cut"]]))
    cut = unary_union([wshape(r) for r in L["demo"] + L["new"]]) if (L["demo"] or L["new"]) else None
    def keep(o):
        if len(o["pts"]) < 2: return False
        q = np.array(o["pts"])
        if len(q) >= 4 and max(np.ptp(q[:, 0]), np.ptp(q[:, 1])) < 1.0: return False      # scan artefact, not a door
        c = np.mean(np.array(o["pts"]), 0)
        return cut is None or not cut.buffer(0.3).contains(Polygon([(c[0] - .01, c[1] - .01), (c[0] + .01, c[1] - .01), (c[0] + .01, c[1] + .01)]).centroid)
    fixu = unary_union([wshape(r) for r in L["fix"]]).buffer(0.02) if L["fix"] else None
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


def dim(ax, x0, y0, x1, y1, at=0.5, fs=3.8, gid="dim", text=None):
    """Dimension string. at = where the figure sits along the line (0 to 1). text = wording to print instead of the measured length."""
    L = abs(x1 - x0) + abs(y1 - y0); t = text or ftin(round(L * 12) / 12)
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


def removed_shape(fl):
    """Walls being removed, as drawn (dashed outline): not where a new wall or a new door takes their place, and no slivers."""
    L = LV[fl]; g = geom(fl)
    if g["removed"] is None or g["removed"].is_empty: return Polygon()
    newu = unary_union([wshape(r) for r in L["new"]]) if L["new"] else None
    dr = [box(d[3], d[2] - 0.45, d[4], d[2] + 0.45) if d[1] == "h" else box(d[2] - 0.45, d[3], d[2] + 0.45, d[4]) for d in L["doors"]]      # a new door in a rebuilt wall
    rem = g["removed"] if newu is None else g["removed"].difference(unary_union([newu.buffer(0.3)] + dr))
    return unary_union([q for q in (rem.geoms if hasattr(rem, "geoms") else [rem]) if q.geom_type == "Polygon" and q.area > 0.12 and q.buffer(-0.08).area > 0])


def panel_box(f):
    """Working space in front of a panel: 30 in. wide, 36 in. deep, on side f[5] (-1 by default). It is centred on the panel unless f[6] slides it
    along the wall (the code lets the 30 in. sit to one side as long as it covers the panel)."""
    x0, y0, x1, y1 = f[1:5]; sd = f[5] if len(f) > 5 else -1; sh = f[6] if len(f) > 6 else 0.0
    if x0 == x1:
        c = (y0 + y1) / 2 + sh; hw = max(1.25, (y1 - y0) / 2); return (min(x0, x0 + sd * 3.0), c - hw, max(x0, x0 + sd * 3.0), c + hw)
    c = (x0 + x1) / 2 + sh; hw = max(1.25, (x1 - x0) / 2); return (c - hw, min(y0, y0 + sd * 3.0), c + hw, max(y0, y0 + sd * 3.0))


# ---------------------------------------------------------------------------------------------- base plan
def draw_base(ax, fl, mode="arch"):
    """mode 'arch': full construction plan (new walls red, removals dashed, furniture, sizes). mode 'trade': quiet grey background for a trade overlay."""
    L = LV[fl]; g = geom(fl); arch = mode == "arch"
    for r in g["rooms"]:
        ax.fill([p[0] for p in r["pts"]], [p[1] for p in r["pts"]], fc="#fafafa", ec="none", zorder=1)
    for f_ in L.get("floor", []):                            # rooms re-measured from the 3D scan
        ax.add_patch(Rectangle((f_[0], f_[1]), f_[2] - f_[0], f_[3] - f_[1], fc="#fafafa", ec="none", zorder=1.2))
    for m_ in L.get("mask", []):                             # outdoors that the scan's room outline wrongly covers
        ax.add_patch(MPoly(np.array(m_), closed=True, fc=PAPER, ec="none", zorder=1.5))
    wc_ = EXW if arch else "#b8bdc4"
    newu = unary_union([wshape(r) for r in L["new"]]) if L["new"] else None
    fixu = unary_union([wshape(r) for r in L["fix"]]) if L["fix"] else None
    if newu is not None:
        _fill(ax, newu.difference(g["walls"]), fc=NEWW if arch else "#8d939b", ec="#7d1a14" if arch else "#8a9099", lw=0.35, zorder=3.9)
    if fixu is not None:
        _fill(ax, fixu.difference(g["walls"]), fc=wc_, ec=FIXE if arch else "#8a9099", lw=0.9 if arch else 0.35, zorder=3.95)
    _fill(ax, g["walls"], fc=wc_, ec="#4a4f57" if arch else "#8a9099", lw=0.35, zorder=4)
    if arch and g["removed"] is not None and not g["removed"].is_empty:
        rem = removed_shape(fl)
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
    for st in L["stairs"]:                                  # (x0, y0, x1, y1, way up, label[, tread depth]); tread depth 0 = a landing
        x0, y0, x1, y1, way, lab_ = st[:6]; step = st[6] if len(st) > 6 else 0.9
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc="white" if step == 0 else "none", ec="#6b7480", lw=0.5, zorder=4.4))
        if way[0] == "x":
            for t in (np.arange(x0 + step, x1 - 0.2, step) if step else []): ax.plot([t, t], [y0, y1], color="#6b7480", lw=0.3, zorder=4.4)
            a, b = ((x0 + 0.4, (y0 + y1) / 2), (x1 - 0.4, (y0 + y1) / 2)); a, b = (b, a) if way == "x-" else (a, b)
        else:
            for t in (np.arange(y1 - step, y0 + 0.2, -step) if step else []): ax.plot([x0, x1], [t, t], color="#6b7480", lw=0.3, zorder=4.4)
            a, b = (((x0 + x1) / 2, y0 + 0.4), ((x0 + x1) / 2, y1 - 0.4)); a, b = (b, a) if way == "y-" else (a, b)
        if lab_:
            ax.annotate("", xy=b, xytext=a, arrowprops=dict(arrowstyle="->", color="#4a4f57", lw=0.6), zorder=4.5)
            ax.text(a[0], a[1], lab_, fontsize=3.4, color="#4a4f57", ha="center", va="center", zorder=4.6, gid="own", bbox=dict(fc="white", ec="none", pad=0.2))
    for (x0, y0, x1, y1, lab_) in L.get("above", []):        # a flight passing over this level: dashed outline
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc="none", ec="#6b7480", lw=0.5, ls=(0, (3, 2)), zorder=9.2))
        ax.text((x0 + x1) / 2, (y0 + y1) / 2, lab_, fontsize=3.2, color="#4a4f57", ha="center", va="center", zorder=9.3, gid="own", linespacing=1.1)
    for w_ in L.get("win", []):                              # a window the Polycam plan missed (from the 3D scan)
        ax.add_patch(MPoly(np.array(wshape(w_).exterior.coords[:-1]), closed=True, fc="#cfe3f7", ec="#1f5fa8", lw=0.5, zorder=4.7))
    for (x0, y0, x1, y1, lab_, tp) in L.get("slopes", []):    # line where a sloping ceiling passes a given height
        ax.plot([x0, x1], [y0, y1], color="#6b7480", lw=0.55, ls=(0, (5, 2, 1, 2)), zorder=5.6)
        if arch and lab_:
            ax.text(tp[0], tp[1], lab_, fontsize=3.2, color="#4a4f57", ha="center", va="center", zorder=9.6, gid="own", bbox=dict(fc="white", ec="none", pad=0.2))
    for (x0, y0, x1, y1, lab_) in L.get("beams", []):         # new beam overhead: pair of dash-dot lines; posts: solid squares
        hz = abs(x1 - x0) >= abs(y1 - y0)
        for o_ in (-0.14, 0.14):
            ax.plot([x0, x1] if hz else [x0 + o_, x1 + o_], [y0 + o_, y1 + o_] if hz else [y0, y1], color=NEWW if arch else "#8a9099", lw=0.75, ls=(0, (7, 2, 1.5, 2)), zorder=9.25)
        if arch and lab_:
            ax.text((x0 + x1) / 2, (y0 + y1) / 2, lab_, fontsize=3.4, color=NEWW, ha="center", va="center", fontweight="bold", zorder=9.6, gid="own", rotation=0 if hz else 90,
                    bbox=dict(fc="white", ec="none", pad=0.25))
    for (px_, py_) in L.get("posts", []):
        ax.add_patch(Rectangle((px_ - 0.2, py_ - 0.2), 0.4, 0.4, fc=NEWW if arch else "#8a9099", ec="#7d1a14" if arch else "#8a9099", lw=0.4, zorder=9.3))
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
            lab_ = f[5] if len(f) > 5 else "furnace + water heater\nhere today: remove"
            if lab_: ax.text((f[1] + f[3]) / 2, (f[2] + f[4]) / 2, lab_, fontsize=3.2, color=NEWW if arch else "#8a9099", ha="center", va="center", zorder=6.1, linespacing=1.1, gid="own")
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
                ax.text(x, y - 0.24, r["no"] + ((" · " + r["size"]) if (r["size"] and r.get("plansize", True)) else "") + ((" · clg " + r["ceil"]) if r["ceil"] else ""), fontsize=3.6, color=col, ha="center", va="center", zorder=12, gid="room",
                        bbox=dict(fc="white", ec="none", pad=0.25))
                continue
            ax.text(x, y + (0.5 if big else 0), nm, fontsize=4.6 if big else 3.6, fontweight="bold", color=col, ha="center", va="center", zorder=12, gid="room",
                    bbox=dict(fc="white", ec="none", pad=0.4))
            if big:
                ax.text(x, y - 0.25, r["no"] + ((" · " + r["size"]) if (r["size"] and r.get("plansize", True)) else ""), fontsize=3.7, color=col, ha="center", va="center", zorder=12, gid="room", bbox=dict(fc="white", ec="none", pad=0.3))
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
    if k == "xequip":                                       # dashed outline of something being removed: only its edge matters
        return box(*f[1:5]).exterior.buffer(0.03)
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
        if L[k]: w = w.union(unary_union([wshape(r) for r in L[k]]))
    out.append((w.buffer(-0.03), "a wall", "wall"))
    rem = removed_shape(fl)
    if not rem.is_empty: out.append((rem.boundary.buffer(0.03), "the dashed outline of a removed wall", "wall"))
    for (x0, y0, x1, y1, _l) in L.get("beams", []):
        out.append((LineString([(x0, y0), (x1, y1)]).buffer(0.2), "the new beam", "wall"))
    for (px_, py_) in L.get("posts", []):
        out.append((box(px_ - 0.22, py_ - 0.22, px_ + 0.22, py_ + 0.22), "a post", "wall"))
    for o in g["windows"]:
        out.append((Polygon(o["pts"]).buffer(0), "a window", "wall"))
    for w_ in L.get("win", []):
        out.append((wshape(w_).buffer(0), "a window", "wall"))
    for a in g["arcs"]:
        if len(a) >= 2: out.append((LineString(a).buffer(0.04), "an existing door swing", "swing"))
    for (x0, y0, x1, y1, *_r) in L["stairs"]:
        out.append((box(x0, y0, x1, y1), "the stair", "fx"))
    out.append((Point(STACK if fl != 3 else (17.68, 8.9)).buffer(0.3), "the drain stack", "fx"))
    for i, d in enumerate(L["dims"]):
        out.append((LineString([(d[0], d[1]), (d[2], d[3])]).buffer(0.03), f"dimension line {i}", f"dim:{i}"))
    for a_ in L.get("ap", []):
        out.append((LineString([(a_[0], a_[1]), (a_[2], a_[3])]).buffer(0.08), "an access panel", "fx"))
    for n, p, q in (leaders or []):
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
            if not onplan: continue
            if gid == "own":
                (u0, v0), (u1, v1) = inv.transform(px.bounds[:2]), inv.transform(px.bounds[2:]); shp = box(min(u0, u1), min(v0, v1), max(u0, u1), max(v0, v1))
                out += [f"{nm} is on {on}" for og, on, ok in obs if ok[:4] in ("dim:", "lead") and og.intersects(shp)]
                continue
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
                                       "Door sizes are in the list below."]),
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
        dim(ax, *d[:4], at=d[4] if len(d) > 4 else 0.5, gid=f"dim:{i}", text=d[5] if len(d) > 5 else None)
    lead = L.get("lead", {}); ax._leaders = []; cnt = {}
    for n, (x, y), t in L["notes"]:
        k = cnt.get(n, 0); cnt[n] = k + 1
        to = lead.get((n, k)) or (lead.get(n) if k == 0 else None)       # lead[n] = first placing, lead[(n, k)] = k-th placing
        if to: ax._leaders.append((n, (x, y), to))
        keynote(ax, n, x, y, to=to)
    y = getattr(fig, "_legend_end", 8.0) - 0.15
    bg.text(10.6, y, "KEYNOTES", fontsize=7, fontweight="bold", color=INK, va="center"); y -= 0.24
    kn = [(n, wrap(t, 56)) for n, _p, t in L["notes"] if t]          # an empty text = the same keynote shown at a second place
    need = sum(0.13 * len(w) + 0.08 for _n, w in kn); k = max(0.82, min(1.0, (y - MG - 0.12) / need))
    for n, w in kn:
        bg.text(10.68, y, str(n), fontsize=5.6, color=NEWW, fontweight="bold", va="center", ha="center")
        for i, ln in enumerate(w):
            bg.text(10.85, y - i * 0.13 * k, ln, fontsize=5.5, color=INK, va="center")
        y -= (0.13 * len(w) + 0.08) * k
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
