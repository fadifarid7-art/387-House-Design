"""Rev E building model: every wall, door, fixture and piece of furniture as a real dimension.

All values are FEET in the site system of common.py (origin = SW front lot corner, +X east along
the Baird St front lot line, +Y north). Nothing on a sheet is "drawn in": the sheets read their
geometry from this file, and `check()` fails the build when something does not fit.
"""
import math

from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

from common import (LOT, LOT_NE, LOT_NW, LOT_SE, LOT_SW, REAR_SLOPE, WEST_LEAN, elev, poly_area, rear_y, west_x)

IN = 1 / 12.0

# ----------------------------------------------------------------------------
# 1. Setbacks and building lines
# ----------------------------------------------------------------------------
SB_FRONT, SB_SIDE, SB_REAR_CODE = 10.0, 5.0, 20.0
SB_REAR = 5.0                      # the one variance requested (20 ft -> 5 ft)
MARGIN_IN = 2.0                    # every wall face is held 2 in. inside its setback line
M = MARGIN_IN * IN
_cw = math.cos(WEST_LEAN)
_tw = math.tan(WEST_LEAN)
_cr = math.cos(math.atan(abs(REAR_SLOPE)))
REAR_ANGLE = math.degrees(math.atan(REAR_SLOPE))        # plan angle of the rear line (negative)

EXT = 6.5 * IN       # exterior frame wall: 1/2 gyp + 2x6 + 7/16 OSB (cladding is outside this)
PART = 4.5 * IN      # partition: 2x4 + 1/2 gyp each side
WET = 6.5 * IN       # plumbing wall: 2x6 + 1/2 gyp each side
RATED = 4.75 * IN    # stair enclosure: 2x4 + 5/8 Type X each side (1 hour)
CONC = 1.0           # garage retaining walls, 12 in. concrete
CMU = 8 * IN         # garage-level interior walls, 8 in. concrete or grouted block

YF = SB_FRONT + M                      # outside face, front
XE = 50.0 - SB_SIDE - M                # outside face, east


def xw_o(y):
    """Outside face of the west wall (parallel to the west lot line)."""
    return west_x(y) + (SB_SIDE + M) / _cw


def xw_i(y):
    return xw_o(y) + EXT / _cw


def yr_o(x):
    """Outside face of the rear wall (parallel to the rear lot line)."""
    return rear_y(x) - (SB_REAR + M) / _cr


def yr_i(x):
    return yr_o(x) - EXT / _cr


def _west_rear_corner(xw, yr):
    y = 30.0
    for _ in range(60):
        y = yr(xw(y))
    return (xw(y), y)


YFI = YF + EXT                         # inside face, front (upper floors)
XEI = XE - EXT                         # inside face, east (upper floors)
OUT_U = [(xw_o(YF), YF), (XE, YF), (XE, yr_o(XE)), _west_rear_corner(xw_o, yr_o)]
IN_U = [(xw_i(YFI), YFI), (XEI, YFI), (XEI, yr_i(XEI)), _west_rear_corner(xw_i, yr_i)]
FOOTPRINT = poly_area(OUT_U)
FACADE_W = XE - xw_o(YF)
REAR_WALL_LEN = math.dist(OUT_U[2], OUT_U[3])
WEST_WALL_LEN = math.dist(OUT_U[0], OUT_U[3])

# ----------------------------------------------------------------------------
# 2. Levels (ft, NAVD88 from LiDAR)
# ----------------------------------------------------------------------------
EL_GAR, EL_A, EL_B = 914.5, 925.5, 935.5        # 11'-0" and 10'-0" floor to floor
TRUSS_A, TRUSS_B = 20 * IN, 24 * IN             # open-web floor trusses
CLG_GAR = 11.0 - TRUSS_A - (0.75 + 0.625) * IN  # clear height, garage
CLG_A = 10.0 - TRUSS_B - (0.75 + 1.25) * IN     # ceiling, Unit A
CLG_B = 8.0 + 1.125 * IN                        # ceiling, Unit B (precut studs + plates)
CLG_SOFFIT = 7.0                                # dropped duct soffit, both flats
EL_PLATE = EL_B + CLG_B + 0.625 * IN
ROOF_PITCH = 4 / 12.0
HEEL = 1.0                                      # raised (energy) heel


def ridge_y(x):
    """Roof trusses run N-S; each is a common truss, so the ridge sits at mid-span."""
    return (YF + yr_o(x)) / 2


def ridge_el(x):
    return EL_PLATE + HEEL + (yr_o(x) - YF) / 2 * ROOF_PITCH


EL_RIDGE_HI = ridge_el(OUT_U[3][0] + 0.5)
EL_RIDGE_LO = ridge_el(XE)

# stair: IRC R311.7 (riser <= 7 3/4 in., tread >= 10 in., width >= 36 in.)
STAIR_LO = dict(rise_total=11.0, risers=18, riser_in=132 / 18, treads_per_flight=8, tread_in=10)
STAIR_UP = dict(rise_total=10.0, risers=16, riser_in=120 / 16, treads_per_flight=7, tread_in=10)

# ----------------------------------------------------------------------------
# 3. Garage level (concrete)
# ----------------------------------------------------------------------------
Y_GR_O = yr_o(XE)                     # outside face of the garage rear wall (square to the street)
Y_GR_I = Y_GR_O - CONC
XE_GI = XE - CONC                     # inside face, east retaining wall


def xw_gi(y):
    return xw_o(y) + CONC / _cw


OUT_L = [(xw_o(YF), YF), (XE, YF), (XE, Y_GR_O), (xw_o(Y_GR_O), Y_GR_O)]
SHAFT_X0 = XEI - (6 + 10 * IN)        # stair shaft, 6'-10" clear on the unit floors (two 3'-3" flights)
SHAFT_U = (SHAFT_X0, XEI, YFI, YFI + 13 + 3 * IN)                   # x0, x1, y0, y1 (unit floors)
SHAFT_L = (SHAFT_X0, XE_GI, YF + CMU, SHAFT_U[3])                   # garage level
GAR_X1 = SHAFT_X0 - CMU               # inside face of the garage east (lobby) wall
OPEN_W = 25.0                         # garage opening; 65 % of the facade is the limit
OPEN = (GAR_X1 - OPEN_W, GAR_X1)
GARAGE_PCT = 100 * OPEN_W / FACADE_W
IN_L = [(xw_gi(YF), YF), (GAR_X1, YF), (GAR_X1, Y_GR_I), (xw_gi(Y_GR_I), Y_GR_I)]
UTIL = (SHAFT_X0, XE_GI, SHAFT_U[3] + CMU, Y_GR_I)                  # heated utility room: water service entry, shutoffs
CAR_W, CAR_L = 6.17, 16.0                                           # design car, 6'-2" x 16'-0"
_c0, _c2 = OPEN[0] + 0.5, OPEN[1] - 1.25 - CAR_W
CARS = [_c0, (_c0 + _c2) / 2, _c2]                                 # west side of each car
COL_X = [OPEN[0] - 0.25, (CARS[1] + CAR_W + CARS[2]) / 2, OPEN[1] + CMU / 2]   # beam B1 supports along the open front
CAR_Y0 = YF + 2.0
STALL_LINES = [(CARS[0] + CAR_W + CARS[1]) / 2, (CARS[1] + CAR_W + CARS[2]) / 2]
ENTRY = (39.5, 42.5)                  # 3'-0" street door into the stair
UTIL_DOOR = (UTIL[3] - 0.25 - 2.667, UTIL[3] - 0.25)                # 2'-8" door, west wall, swings INTO the room
WH = []                               # (Rev E.1) no water heaters at garage level: each is in its own flat, see WH_UNIT
WH_R = 1.0                            # 80 gal electric heater, 24 in. diameter
WH_PAN_R = 13 * IN                    # 26 in. drain pan under each heater
SOG = [(xw_o(Y_GR_O), Y_GR_O), (XE, Y_GR_O), OUT_U[3]]              # Unit A floor that is a slab on grade

# porches (Unit A and Unit B), cantilevered 4'-0"; allowed 5'-0" into the front setback
PORCH = (OPEN[0], YF - 4.0, XE, YF)

# ---- site work (all on the lot unless noted) ----
APRON = [(OPEN[0], YF), (OPEN[1], YF), (OPEN[1] - 1.5, 0.0), (OPEN[1] + 0.5, -7.0), (OPEN[0] - 0.5, -7.0), (OPEN[0] + 1.5, 0.0)]
APRON_W_ROW = (OPEN[1] - 1.5) - (OPEN[0] + 1.5)                     # 22'-0" at the right-of-way line


def apron_x(y, side):
    """Apron edge at depth y (0 <= y <= YF); side = 0 west, 1 east."""
    t = max(0.0, min(1.0, y / YF))
    return (OPEN[0] + 1.5 * (1 - t)) if side == 0 else (OPEN[1] - 1.5 * (1 - t))


LAND_Y0 = 3.3                                                       # entry landing, level with the garage floor
WALK = [(apron_x(LAND_Y0, 1), LAND_Y0), (XE, LAND_Y0), (XE, YF), (OPEN[1], YF)]
TRASH = (38.0, 0.5, XE, LAND_Y0)                                    # screened bay for 4 carts, opens onto the landing
WING_W = [(OPEN[0], YF), (apron_x(0.5, 0), 0.5)]                    # west wing wall beside the apron (retains the front yard)
WING_E = [(apron_x(0.5, 1) + 0.2, 0.5), (XE + 0.35, 0.5), (XE + 0.35, YF)]   # low wall around the trash bay and landing
HP = [(xw_o(20.5) - 1.1, 20.5), (xw_o(24.6) - 1.1, 24.6)]           # heat-pump pads A, B: side-discharge units 38 x 15 in.
HP_SIZE = (38 * IN, 15 * IN)

# ---- coordination points shared by every trade ----
EL_FTG_TOP = EL_GAR - (36 - 14) * IN  # top of the retaining-wall footing: its bottom is 36 in. (frost) below the open garage slab
FTG_W, FTG_T = 4.0, 14 * IN           # preliminary retaining-wall footing, 4'-0" x 14 in.
EL_SLAB_A = EL_A                      # Unit A slab on grade (rear), same level as the framed floor
B1_Y = YF + 0.5                       # centre line of steel beam B1 over the garage opening (dropped below the trusses)
EL_B1_TOP = EL_A - 0.75 * IN - TRUSS_A - 1.5 * IN        # 1 1/2 in. wood nailer between steel and trusses
B1_PAD = 5.0                          # preliminary pad footing under the B1 post, 5'-0" square
B1_DEPTH = 14 * IN                    # W14 preliminary
OPEN_CLEAR_H = EL_B1_TOP - B1_DEPTH - EL_GAR
SEWER_OUT_X = 33.5                                      # building drain leaves under the garage opening here
SEWER_CO = (SEWER_OUT_X, 3.0)                           # two-way cleanout on the lot
WATER_ENTRY = (XE, UTIL[2] + 2.2)                       # two 1 in. services enter the utility room through the east wall
EL_WATER_ENTRY = EL_GAR + 2.5
WATER_METERS = [(46.6, -1.6), (48.0, -1.6)]             # MUB meter pits (utility-owned, in the right-of-way)
WATER_DEPTH = 3.5                                       # 42 in. cover, below frost
E_METER = (XE, YF + 2.6)                                # 2-position meter stack on the east wall
DRAIN_OUT = (46.8, -6.2)                                # gravity outlet of the French drain and trench drain (street edge)
EL_DRAIN_HI, EL_DRAIN_OUT = 913.1, 912.2                # French-drain inverts: high point (west) and outlet
PANEL_A_AMPS, PANEL_B_AMPS = 150, 125


def avg_grade():
    """Average existing grade at the four building corners (zoning height reference)."""
    return sum(elev(x, y) for x, y in OUT_U) / 4


def zoning_height():
    """Mean roof height (midway between the eave and the highest ridge) above average grade."""
    return ((EL_PLATE + HEEL) + EL_RIDGE_HI) / 2 - avg_grade()


# ----------------------------------------------------------------------------
# 4. Unit plan (Units A and B are identical): partitions as rectangles
# ----------------------------------------------------------------------------
Y1 = YFI + 10.5                       # bedroom 1 / living north face
Y2 = Y1 + PART                        # bath strip south face
Y3 = Y2 + 5.0                         # bath strip north face (60 in. tub alcove)
Y4 = Y3 + WET                         # bedroom 2 south face
E1 = 19.5                             # bedroom 1 / bedroom 2 / bath 1 east face
X_H0 = E1 + PART                      # hall and living west face
X_H1 = X_H0 + 3 + 1 * IN              # hall east face (3'-1")
X_C0 = X_H1 + PART                    # closet strip west face
X_C1 = X_C0 + 2 + 10 * IN             # closet strip east face (2'-10")
X_B3 = X_C1 + PART                    # bedroom 3 west face
X_ST = SHAFT_X0 - RATED               # west face of the stair wall = east face of living / bedroom 3
Y_ST = SHAFT_U[3] + RATED             # north face of the stair wall = south face of bath 3
B2_Y0 = round(yr_i(X_C1) - 5.0 - 0.02, 3)      # bath 2 south face (tub alcove ends at the rear wall)
B2_Y1 = B2_Y0 + 5.0
HALL_Y1 = B2_Y0 - PART
B3_Y1 = Y_ST + 5.0                    # bath 3 north face
CL_X0, CL_X1 = 8.875, 12.125          # closets at the west end of the strip (3'-3")
B1_X0 = CL_X1 + PART                  # bath 1 west face (7'-0" to E1)
CL_Y = Y2 + 2.25                      # bedroom 1 closet depth 2'-3"
WD_Y1 = Y2 + 3.0                      # washer/dryer closet 3'-0"
AH_Y0, AH_Y1 = WD_Y1 + PART, WD_Y1 + PART + 2.5                    # mechanical closet, air-handler half 2'-6"
LIN_Y0 = AH_Y1                        # water-heater half starts here (no wall between the two halves)
C3_Y = Y2 + 6.667 + 2.0               # bedroom 3 closet: south face of its front wall (24 in. past the bed)
C3_X = X_B3 + 3.0                     # bedroom 3 closet: east inside face (3'-0" wide)
B2_FUR = round(yr_i(X_C1 - 2.5) - 0.02 - B2_Y1, 3)   # furred wall behind the bath 2 toilet

# (x0, y0, x1, y1, kind)   kind: p = 2x4, w = 2x6 plumbing, r = 1-hour, f = furring
PARTITIONS = [
    (xw_i(Y1) - 0.2, Y1, X_H0, Y2, "p"),             # bedroom 1 north wall
    (X_H1, Y1, X_ST, Y2, "p"),                       # living north wall (hall opening is the gap)
    (xw_i(Y3) - 0.2, Y3, E1, Y4, "w"),               # strip north wall (plumbing) = bedroom 2 south wall
    (E1, YFI, X_H0, Y1, "p"),                        # bedroom 1 / living
    (E1, Y2, X_H0, yr_i(E1) + 0.1, "p"),                       # bath 1 + bedroom 2 east wall (hall, bath 2 west)
    (CL_X1, Y2, B1_X0, Y3, "p"),                     # closets / bath 1
    (CL_X0 - 0.4, CL_Y, CL_X1, CL_Y + PART, "p"),    # between the two closets
    (X_H1, Y2, X_C0, HALL_Y1, "p"),                  # hall east wall (closet fronts)
    (X_H0, HALL_Y1, X_C1, B2_Y0, "p"),               # hall end / bath 2 south wall
    (X_C0, WD_Y1, X_C1, AH_Y0, "p"),                 # W/D | air handler
    (X_C1, Y2, X_B3, yr_i(X_C1) + 0.1, "p"),                     # closet strip + bath 2 / bedroom 3
    (X_B3, C3_Y, C3_X + PART, C3_Y + PART, "p"),     # bedroom 3 closet front
    (C3_X, C3_Y, C3_X + PART, yr_i(C3_X) + 0.1, "p"),   # bedroom 3 closet end
    (X_ST, YFI, SHAFT_X0, yr_i(X_ST) + 0.1, "r"),                # stair west wall, continued as bedroom 3 / bath 3
    (SHAFT_X0, SHAFT_U[3], XEI, Y_ST, "r"),          # stair north wall
    (SHAFT_X0, B3_Y1, XEI, B3_Y1 + PART, "p"),       # bath 3 north wall (pipe chase behind it)
    (X_H0, B2_Y1 + B2_FUR, X_C1 - 2.5, B2_Y1 + B2_FUR + PART, "f"),   # furred square wall behind the bath 2 toilet
]
HALL_OPENING = (X_H0, X_H1)                          # cased opening, hall <-> living, in the Y1..Y2 wall

# ----------------------------------------------------------------------------
# 5. Doors
#    wall: "h" = in a wall that runs E-W (cut spans x0..x1), "v" = N-S wall (cut spans y0..y1)
#    at  : wall rectangle (a0, a1) across its thickness
#    hinge: which end of the cut; swing: +1 = toward +Y (h walls) or +X (v walls)
# ----------------------------------------------------------------------------
def _d(tag, wall, s0, w, at, hinge, swing, kind="swing", note=""):
    return dict(tag=tag, wall=wall, s0=s0, s1=s0 + w, w=w, at=at, hinge=hinge, swing=swing, kind=kind, note=note)


DOORS = [
    _d("D1", "v", YFI + 0.25, 3.0, (X_ST, SHAFT_X0), "lo", -1, note="Unit entry, 3'-0\" x 6'-8\", 20-min, self-closing"),
    _d("D2", "v", Y1 - 0.125 - 2.667, 2.667, (E1, X_H0), "hi", -1, note="Bedroom 1, 2'-8\""),
    _d("D3", "v", Y4 + 0.125, 2.5, (E1, X_H0), "lo", -1, note="Bedroom 2, 2'-6\""),
    _d("D4", "h", X_B3 + 0.25, 2.667, (Y1, Y2), "lo", +1, note="Bedroom 3, 2'-8\""),
    _d("D5", "h", B1_X0 + 0.167, 2.333, (Y1, Y2), "lo", +1, note="Bath 1, 2'-4\""),
    _d("D6", "v", B2_Y0 + 1.70, 2.333, (E1, X_H0), "lo", +1, note="Bath 2, 2'-4\""),
    _d("D7", "v", Y_ST + 0.125, 2.333, (X_ST, SHAFT_X0), "lo", +1, note="Bath 3, 2'-4\""),
    _d("D8", "h", CL_X0 + 0.29, 2.667, (Y1, Y2), "lo", -1, "bifold", "Bedroom 1 closet, 2'-8\" bifold"),
    _d("D9", "h", CL_X0 + 0.29, 2.667, (Y3, Y4), "lo", +1, "bifold", "Bedroom 2 closet, 2'-8\" bifold"),
    _d("D10", "h", X_B3 + 0.25, 2.5, (C3_Y, C3_Y + PART), "lo", -1, "bifold", "Bedroom 3 closet, 2'-6\" bifold"),
    _d("D11", "v", Y2 + 0.167, 2.667, (X_H1, X_C0), "lo", -1, "bifold", "Washer/dryer, 2'-8\" bifold"),
    _d("D12", "v", (AH_Y0 + HALL_Y1) / 2 - 2.0, 2.0, (X_H1, X_C0), "lo", -1, note="Mechanical closet, pair leaf 2'-0\" with return grille (air handler)"),
    _d("D13", "v", (AH_Y0 + HALL_Y1) / 2, 2.0, (X_H1, X_C0), "hi", -1, note="Mechanical closet, pair leaf 2'-0\" (water heater)"),
    _d("D14", "h", 26.9, 3.0, (YF, YFI), "lo", +1, note="Porch, 3'-0\" full-glass"),
]

# windows on the exterior walls: (tag, wall, s0, s1, note). Stations: x for S/N walls, y for E/W walls.
WINDOWS = [
    ("W1", "S", 10.2, 10.2 + 2.333, "Bedroom 1 escape window"),
    ("W2", "S", 21.5, 26.5, "Living room"),
    ("W3", "S", 39.6, 42.6, "Stair"),
    ("W4", "W", 14.5, 17.0, "Bedroom 1"),
    ("W1", "W", 34.25, 34.25 + 2.333, "Bedroom 2 escape window"),
    ("W5", "N", 13.0, 16.0, "Bedroom 2, high sill"),
    ("W1", "N", 34.55, 34.55 + 2.333, "Bedroom 3 escape window"),
]
WINDOW_TYPES = {
    "W1": "2'-4\" x 5'-0\" vinyl casement, escape: clear opening 5.7 sf min., sill 30 in.",
    "W2": "5'-0\" x 5'-0\" vinyl slider, sill 30 in.",
    "W3": "3'-0\" x 4'-0\" vinyl fixed, tempered",
    "W4": "2'-6\" x 4'-0\" vinyl single-hung, sill 42 in.",
    "W5": "3'-0\" x 2'-6\" vinyl awning, sill 54 in.",
}

# ----------------------------------------------------------------------------
# 6. Rooms (clear, inside finished faces)
# ----------------------------------------------------------------------------
ROOMS = {
    "BEDROOM 1": [(xw_i(YFI), YFI), (E1, YFI), (E1, Y1), (xw_i(Y1), Y1)],
    "BEDROOM 2": [(xw_i(Y4), Y4), (E1, Y4), (E1, yr_i(E1)), IN_U[3]],
    "BEDROOM 3": [(X_B3, Y2), (X_ST, Y2), (X_ST, yr_i(X_ST)), (C3_X + PART, yr_i(C3_X + PART)), (C3_X + PART, C3_Y), (X_B3, C3_Y)],
    "LIVING / KITCHEN": [(X_H0, YFI), (X_ST, YFI), (X_ST, Y1), (X_H0, Y1)],
    "HALL": [(X_H0, Y1), (X_H1, Y1), (X_H1, HALL_Y1), (X_H0, HALL_Y1)],
    "BATH 1": [(B1_X0, Y2), (E1, Y2), (E1, Y3), (B1_X0, Y3)],
    "BATH 2": [(X_H0, B2_Y0), (X_C1, B2_Y0), (X_C1, B2_Y1), (X_C1 - 2.5, B2_Y1), (X_C1 - 2.5, B2_Y1 + B2_FUR), (X_H0, B2_Y1 + B2_FUR)],
    "BATH 3": [(SHAFT_X0, Y_ST), (XEI, Y_ST), (XEI, B3_Y1), (SHAFT_X0, B3_Y1)],
    "CLOSET 1": [(CL_X0 - 0.375, Y2), (CL_X1, Y2), (CL_X1, CL_Y), (CL_X0 - 0.375, CL_Y)],
    "CLOSET 2": [(CL_X0, CL_Y + PART), (CL_X1, CL_Y + PART), (CL_X1, Y3), (CL_X0, Y3)],
    "CLOSET 3": [(X_B3, C3_Y + PART), (C3_X, C3_Y + PART), (C3_X, yr_i(C3_X)), (X_B3, yr_i(X_B3))],
    "W/D": [(X_C0, Y2), (X_C1, Y2), (X_C1, WD_Y1), (X_C0, WD_Y1)],
    "AIR HANDLER": [(X_C0, AH_Y0), (X_C1, AH_Y0), (X_C1, AH_Y1), (X_C0, AH_Y1)],
    "WATER HEATER": [(X_C0, LIN_Y0), (X_C1, LIN_Y0), (X_C1, HALL_Y1), (X_C0, HALL_Y1)],
}
STAIR_AREA = (SHAFT_U[1] - SHAFT_U[0]) * (SHAFT_U[3] - SHAFT_U[2])


def clear_rect(name):
    """Largest plain rectangle used for the furniture check: (x0, y0, x1, y1)."""
    if name == "BEDROOM 1":
        return (xw_i(Y1), YFI, E1, Y1)
    if name == "BEDROOM 2":
        return (xw_i(yr_i(E1)), Y4, E1, yr_i(E1))
    if name == "BEDROOM 3":
        return (X_B3, Y2, X_ST, C3_Y)
    if name == "LIVING / KITCHEN":
        return (X_H0, YFI, X_ST, Y1)
    raise KeyError(name)


# ----------------------------------------------------------------------------
# 7. Fixtures and equipment (real catalogue sizes)
# ----------------------------------------------------------------------------
SIZES = {
    "Bathtub": "60 x 30 in. alcove tub, 60 in. between finished walls",
    "Toilet": "30 in. wide space (15 in. each side of centre), 28 in. deep, 21 in. clear in front",
    "Vanity": "24 x 21 in. (bath 1); 30 x 18 in. (bath 2); 20 x 18 in. wall-hung lavatory (bath 3)",
    "Washer/dryer": "stacked 27 x 31 in. in a 36 x 34 in. closet",
    "Air handler": "vertical, 21 x 21 in., in the 5'-0\" x 2'-10\" mechanical closet off the hall",
    "Water heater": "80 gal electric, 24 in. dia. x 60 in., on a 26 in. drain pan, in the mechanical closet of its own flat",
    "Range": "30 in.",
    "Refrigerator": "36 in. wide space x 30 in. deep",
    "Dishwasher": "24 in.",
    "Sink base": "33 in.",
    "Base cabinets": "24 in. deep, counter 25 in.",
    "Island": "5'-0\" x 2'-1\" with a 12 in. seating overhang, sink and dishwasher",
    "Queen bed": "60 x 80 in.",
    "Desk": "48 x 24 in. with chair space",
    "Dresser": "36 x 18 in.",
    "Sofa": "84 x 36 in.",
    "Design car": "6'-2\" x 16'-0\"",
}
TUBS = [(E1 - 2.5, Y2, E1, Y3), (X_C1 - 2.5, B2_Y0, X_C1, B2_Y1), (XEI - 2.5, Y_ST, XEI, B3_Y1)]
# toilets: (centre x, centre y of the wall side, facing)
WCS = [(E1 - 2.5 - 1.25, Y3, "S"), (X_C1 - 2.5 - 1.25, B2_Y1 + B2_FUR, "S"), (XEI - 2.5 - 1.25, B3_Y1, "S")]
WC_D, WC_W = 28 * IN, 30 * IN
LAVS = [(B1_X0, Y3 - 1.75, B1_X0 + 2.0, Y3), (X_H0 + 0.35, B2_Y0, X_H0 + 2.85, B2_Y0 + 1.5), (SHAFT_X0 + 0.08, B3_Y1 - 1.5, SHAFT_X0 + 0.08 + 1.667, B3_Y1)]
WD = (X_C0 + 0.29, Y2 + 0.2, X_C0 + 0.29 + 2.25, Y2 + 0.2 + 2.583)        # 27 x 31 in.
AHU = (X_C0 + 0.5, AH_Y0 + 0.375, X_C0 + 2.25, AH_Y0 + 2.125)             # 21 x 21 in.
PANEL = (X_H0, Y2 + 1.2, X_H0 + 0.33, Y2 + 2.4)                           # load centre, hall west wall
WH_UNIT = (X_C0 + 1.45, HALL_Y1 - 1.2)                                    # water heater centre, in each flat's mechanical closet
KIT_BASE = (X_H0, YFI, X_H0 + 2.083, YFI + 2.0)
RANGE = (X_H0, YFI + 2.0, X_H0 + 2.083, YFI + 4.5)
FRIDGE = (X_H0, YFI + 4.5, X_H0 + 2.5, YFI + 7.5)
ISLAND = (X_H0 + 2.083 + 3.5, YFI + 3.0, X_H0 + 2.083 + 3.5 + 2.083, YFI + 8.0)
ISLAND_TOP = (ISLAND[0], ISLAND[1], ISLAND[2] + 1.0, ISLAND[3])
ISL_SINK = (ISLAND[0] + 0.15, ISLAND[1] + 2.25, ISLAND[2] - 0.15, ISLAND[1] + 5.0)
ISL_DW = (ISLAND[0], ISLAND[1] + 0.25, ISLAND[2], ISLAND[1] + 2.25)
STOOLS = [(ISLAND_TOP[2] + 0.75, ISLAND[1] + 0.85 + i * 1.65) for i in range(3)]

def _along_rear(x_start, length, depth, gap=0.05):
    """Rectangle with its back against the (angled) rear wall, starting at plan station x_start."""
    t = math.atan(abs(REAR_SLOPE))
    u = (math.cos(t), -math.sin(t))
    n = (-math.sin(t), -math.cos(t))
    a = (x_start + n[0] * gap, yr_i(x_start) + n[1] * gap)
    b_ = (a[0] + u[0] * length, a[1] + u[1] * length)
    return [a, b_, (b_[0] + n[0] * depth, b_[1] + n[1] * depth), (a[0] + n[0] * depth, a[1] + n[1] * depth)]


def _r(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


_B3X = X_ST - 2.0 - 5.0               # bedroom 3 bed: 24 in. to the stair wall
# furniture: (room, kind, polygon)
FURN = [
    ("BEDROOM 1", "bed", _r(8.25, 13.25, 8.25 + 6.667, 18.25)),
    ("BEDROOM 1", "desk", _r(E1 - 2.0, YFI + 0.3, E1, YFI + 4.3)),
    ("BEDROOM 1", "dresser", _r(E1 - 1.5, YFI + 4.45, E1, YFI + 7.45)),
    ("BEDROOM 2", "bed", _r(9.9, 29.2, 9.9 + 6.667, 34.2)),
    ("BEDROOM 2", "desk", _r(11.0, 36.6, 15.0, 38.6)),
    ("BEDROOM 2", "dresser", _r(E1 - 1.5, 34.38, E1, 37.38)),
    ("BEDROOM 3", "bed", _r(_B3X, Y2, _B3X + 5.0, Y2 + 6.667)),
    ("BEDROOM 3", "desk", _along_rear(C3_X + PART + 0.75, 4.0, 2.0)),
    ("BEDROOM 3", "dresser", _r(X_B3, 24.4, X_B3 + 1.5, 27.4)),
    ("LIVING / KITCHEN", "sofa", _r(X_ST - 7.05, Y1 - 3.0, X_ST - 0.05, Y1)),
    ("LIVING / KITCHEN", "tv", _r(30.6, YFI, 33.6, YFI + 1.4)),
]
BED_HEAD = {"BEDROOM 1": "W", "BEDROOM 2": "W", "BEDROOM 3": "S"}
CHAIRS = {"BEDROOM 1": _r(E1 - 4.5, YFI + 1.05, E1 - 2.0, YFI + 3.55),
          "BEDROOM 2": _r(11.75, 34.4, 14.25, 36.6),
          "BEDROOM 3": _r(32.6, 28.5, 35.1, 30.4)}


# stacks and chases (coordination points for plumbing, framing and fire-stopping)
STACK_1 = (E1 - 3.75, Y3 + WET / 2)                     # bath 1 stack (in the 2x6 wall behind the toilet)
STACK_2 = (X_H0 + 0.55, B2_Y1 + B2_FUR + PART + 0.3)    # bath 2 stack (pipe space behind the furred wall, west of the toilet)
STACK_3 = (XEI - 3.75, B3_Y1 + PART + 0.45)             # bath 3 stack (pipe space behind bath 3)
CHASE_1 = (STACK_1[0], Y_GR_I - 0.67)                   # insulated 1-hour chase on the garage rear wall
CHASE_2 = (STACK_2[0], Y_GR_I - 0.67)
CHASE_3 = (STACK_3[0], Y_GR_I - 0.5)                    # in the heated utility room (no chase needed)


# ----------------------------------------------------------------------------
# 8. Geometry helpers used by the sheets
# ----------------------------------------------------------------------------
def door_cut(d):
    a0, a1 = d["at"]
    return (d["s0"], a0, d["s1"], a1) if d["wall"] == "h" else (a0, d["s0"], a1, d["s1"])


def door_hinge(d):
    """Hinge point and the two unit vectors: along the closed leaf and toward the swing side."""
    a0, a1 = d["at"]
    face = a1 if d["swing"] > 0 else a0
    s = d["s0"] if d["hinge"] == "lo" else d["s1"]
    k = 1 if d["hinge"] == "lo" else -1
    if d["wall"] == "h":
        return (s, face), (k, 0), (0, d["swing"])
    return (face, s), (0, k), (d["swing"], 0)


def door_sector(d, n=10):
    """Floor swept by a swing door (bifolds sweep half their width)."""
    (hx, hy), (ax_, ay_), (sx, sy) = door_hinge(d)
    r = d["w"] if d["kind"] == "swing" else d["w"] / 2
    pts = [(hx, hy)]
    for i in range(n + 1):
        t = math.pi / 2 * i / n
        pts.append((hx + r * (ax_ * math.cos(t) + sx * math.sin(t)), hy + r * (ay_ * math.cos(t) + sy * math.sin(t))))
    if d["kind"] != "swing":
        return box(*_norm(hx, hy, hx + ax_ * d["w"] + sx * r, hy + ay_ * d["w"] + sy * r))
    return Polygon(pts)


def _norm(x0, y0, x1, y1):
    return (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))


def win_quad(wall, s0, s1):
    """Four corners of a window opening through an exterior wall (outer s0, outer s1, inner s1, inner s0)."""
    if wall == "S":
        return [(s0, YF), (s1, YF), (s1, YFI), (s0, YFI)]
    if wall == "E":
        return [(XE, s0), (XE, s1), (XEI, s1), (XEI, s0)]
    if wall == "W":
        return [(xw_o(s0), s0), (xw_o(s1), s1), (xw_i(s1), s1), (xw_i(s0), s0)]
    if wall == "N":
        dx = EXT * math.sin(math.atan(abs(REAR_SLOPE)))
        return [(s0, yr_o(s0)), (s1, yr_o(s1)), (s1 - dx, yr_i(s1 - dx)), (s0 - dx, yr_i(s0 - dx))]
    raise KeyError(wall)


def area(name):
    return poly_area(ROOMS[name])


def room_dims(name):
    x0, y0, x1, y1 = clear_rect(name)
    return (x1 - x0, y1 - y0)


def net_area():
    return poly_area(IN_U) - STAIR_AREA


# ----------------------------------------------------------------------------
# 9. Checks: the build stops if any of these fail
# ----------------------------------------------------------------------------
def check(verbose=False):
    msgs = []

    def ok(cond, text):
        if not cond:
            msgs.append(text)

    lot = Polygon(LOT)
    out = Polygon(OUT_U)
    front, east = 0.0, 50.0
    ok(min(y for _, y in OUT_U) >= SB_FRONT - 1e-6, "front setback")
    ok(max(x for x, _ in OUT_U) <= east - SB_SIDE + 1e-6, "east setback")
    from shapely.geometry import LineString
    ok(out.distance(LineString([LOT_NE, LOT_NW])) >= SB_REAR - 1e-6, "rear setback (variance line)")
    ok(out.distance(LineString([LOT_SW, LOT_NW])) >= SB_SIDE - 1e-6, "west setback")
    ok(FOOTPRINT / poly_area(LOT) <= 0.50, "lot coverage over 50 %")
    ok(GARAGE_PCT <= 65.0 + 1e-6, "garage over 65 % of the facade")
    ok(APRON_W_ROW <= 22.0 + 1e-6, "driveway over 22 ft at the right-of-way")
    ok(PORCH[3] - PORCH[1] <= SB_FRONT / 2, "porch more than half-way into the front setback")
    ok((PORCH[2] - PORCH[0]) >= 0.5 * FACADE_W, "porch under 50 % of the facade")
    ok(yr_i(X_C1) >= B2_Y1, "bath 2 tub alcove crosses the rear wall")
    ok(yr_i(XEI) >= B3_Y1 + PART, "bath 3 crosses the rear wall")
    ok(STAIR_LO["riser_in"] <= 7.75 and STAIR_UP["riser_in"] <= 7.75, "stair riser")
    # tub alcoves exactly 60 in.
    for i, (x0, y0, x1, y1) in enumerate(TUBS):
        ok(abs((y1 - y0) - 5.0) < 1e-6 and abs((x1 - x0) - 2.5) < 1e-6, f"tub {i + 1} is not 60 x 30")
    rooms = {k: Polygon(v) for k, v in ROOMS.items()}
    for k, p in rooms.items():
        ok(p.is_valid and Polygon(IN_U).buffer(0.02).contains(p), f"{k} leaves the building")
    names = list(rooms)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            ok(rooms[a].intersection(rooms[b]).area < 0.02, f"{a} overlaps {b}")
    # IRC R304: habitable rooms >= 70 sf and >= 7 ft
    for k in ("BEDROOM 1", "BEDROOM 2", "BEDROOM 3"):
        w, d = room_dims(k)
        ok(max(w, d) >= 10.0 - 1e-6, f"{k} clear rectangle under 10 ft")
        ok(min(w, d) >= 8.5, f"{k} clear rectangle under 8'-6\"")
        ok(area(k) >= 100, f"{k} under 100 sf")
    sectors = [(d["tag"], door_sector(d)) for d in DOORS]
    solid = []
    _wh = (WH_UNIT[0] - WH_R, WH_UNIT[1] - WH_R, WH_UNIT[0] + WH_R, WH_UNIT[1] + WH_R)
    ok(Polygon(ROOMS["WATER HEATER"]).buffer(0.01).contains(Point(*WH_UNIT).buffer(WH_PAN_R)), "water heater pan does not fit its closet")
    ok(box(*AHU).intersection(Point(*WH_UNIT).buffer(WH_PAN_R)).area < 0.01, "air handler and water heater overlap")
    for (x0, y0, x1, y1) in TUBS + LAVS + [WD, AHU, _wh, KIT_BASE, RANGE, FRIDGE, ISLAND_TOP]:
        solid.append(box(x0, y0, x1, y1))
    for (cx, cy, f) in WCS:
        solid.append(box(cx - 0.8, cy - WC_D, cx + 0.8, cy))
    furn = []
    for (room, kind, pts) in FURN:
        b = Polygon(pts)
        ok(rooms[room].buffer(0.02).contains(b), f"{room} {kind} is outside the room")
        furn.append((room, kind, b))
    for room, c in CHAIRS.items():
        furn.append((room, "chair space", Polygon(c)))
        ok(rooms[room].buffer(0.02).contains(Polygon(c)), f"{room} chair space is outside the room")
    for i, (ra, ka, a) in enumerate(furn):
        for (rb, kb, b) in furn[i + 1:]:
            if "chair space" in (ka, kb) and "desk" in (ka, kb):
                continue
            ok(a.intersection(b).area < 0.02, f"{ra} {ka} overlaps {rb} {kb}")
        for tag, s in sectors:
            ok(a.intersection(s).area < 0.02, f"{ra} {ka} blocks door {tag}")
    for tag, s in sectors:
        for b in solid:
            ok(s.intersection(b).area < 0.02, f"door {tag} hits a fixture")
    # beds: 24 in. clear on both sides and at the foot
    for (room, kind, pts) in FURN:
        if kind != "bed":
            continue
        x0, y0, x1, y1 = Polygon(pts).bounds
        others = unary_union([b for (r, k, b) in furn if r == room and k not in ("bed", "chair space")])
        rp = rooms[room]
        if BED_HEAD[room] == "W":
            zones = [box(x0, y0 - 2.0, x1, y0), box(x0, y1, x1, y1 + 2.0), box(x1, y0, x1 + 2.0, y1)]
        else:
            zones = [box(x0 - 2.0, y0, x0, y1), box(x1, y0, x1 + 2.0, y1), box(x0, y1, x1, y1 + 2.0)]
        for z in zones:
            ok(rp.buffer(0.02).contains(z), f"{room}: under 24 in. beside the bed")
            ok(z.intersection(others).area < 0.02, f"{room}: furniture inside the 24 in. bed clearance")
    # toilets: 15 in. to each side, 21 in. in front
    walls = [box(*p[:4]) for p in PARTITIONS]
    for i, (cx, cy, f) in enumerate(WCS):
        zone = box(cx - 1.25, cy - WC_D - 1.75, cx + 1.25, cy)
        for j, b in enumerate(solid):
            if b.intersection(box(cx - 0.8, cy - WC_D, cx + 0.8, cy)).area > 0.5:
                continue
            ok(zone.intersection(b).area < 0.02, f"toilet {i + 1} clearance blocked")
    # kitchen aisle
    ok(ISLAND[0] - (X_H0 + 2.083) >= 3.5 - 1e-6, "kitchen aisle under 42 in.")
    ok(Y1 - ISLAND_TOP[3] >= 2.5, "path north of the island under 30 in.")
    # garage
    ok(CARS[0] >= OPEN[0] + 0.5 - 1e-6 and CARS[2] + CAR_W <= OPEN[1] - 1.0, "car does not clear the opening")
    ok(CARS[1] - (CARS[0] + CAR_W) >= 2.25 and CARS[2] - (CARS[1] + CAR_W) >= 2.25, "under 2'-3\" between cars")
    ok(Y_GR_I - CAR_Y0 - CAR_L >= 0.75, "garage too shallow")
    ok(UTIL[1] - UTIL[0] >= 6.0 and UTIL[3] - UTIL[2] >= 4.3, "utility room too small")
    ok(all(y >= 0.5 - 1e-6 for _, y in WALK + WING_E + WING_W) and TRASH[1] >= 0.5 - 1e-6, "site wall or bay in the right-of-way")
    ok(OPEN_CLEAR_H >= 7.0, "garage opening under 7 ft clear")
    for st_ in (STACK_1, STACK_2, STACK_3):
        ok(Polygon(IN_U).contains(Point(*st_).buffer(0.17)), "a plumbing stack is outside the building")
    for (hx, hy) in HP:
        ok((hx - HP_SIZE[1] / 2 - west_x(hy)) * _cw >= 2.0, "heat pump under 2 ft from the side lot line")
    if verbose or msgs:
        for m_ in msgs:
            print("CHECK FAILED:", m_)
    if msgs:
        raise SystemExit(f"{len(msgs)} model check(s) failed")
    return True


def summary():
    lotA = poly_area(LOT)
    rows = dict(
        footprint=FOOTPRINT, coverage=100 * FOOTPRINT / lotA, facade=FACADE_W, garage_pct=GARAGE_PCT,
        net=net_area(), rear_wall=REAR_WALL_LEN, west_wall=WEST_WALL_LEN,
        ridge_hi=EL_RIDGE_HI, ridge_lo=EL_RIDGE_LO, plate=EL_PLATE,
    )
    for k in ROOMS:
        rows[k] = area(k)
    return rows


if __name__ == "__main__":
    from common import ftin
    check(verbose=True)
    for k, v in summary().items():
        print(f"{k:18s} {v:8.2f}")
    for k in ("BEDROOM 1", "BEDROOM 2", "BEDROOM 3", "LIVING / KITCHEN"):
        w, d = room_dims(k)
        print(k, ftin(w), "x", ftin(d), f"= {w * d:.0f} sf clear rectangle; {area(k):.0f} sf total")
    print("OUT_U", [(round(x, 2), round(y, 2)) for x, y in OUT_U])
    print("IN_U", [(round(x, 2), round(y, 2)) for x, y in IN_U])
    print("garage inside", [(round(x, 2), round(y, 2)) for x, y in IN_L], "open", OPEN, "util", [round(v, 2) for v in UTIL])
    print("key y:", [round(v, 3) for v in (YFI, Y1, Y2, Y3, Y4, B2_Y0, B2_Y1, HALL_Y1, Y_ST, B3_Y1)])
    print("key x:", [round(v, 3) for v in (E1, X_H0, X_H1, X_C0, X_C1, X_B3, X_ST, SHAFT_X0, XEI)])
