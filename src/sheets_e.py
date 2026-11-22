"""Electrical sheets E-101 to E-201 (Rev E), drawn over the grey background plans.

PRELIMINARY: device positions come from model.py; loads, breaker and wire sizes are assumptions for
the electrician / engineer of record to confirm. 2020 NEC, all electric, two meters only.
The circuit numbers on the plan sheets and the panel schedules on E-201 come from one list (`circuits`).
"""
import math
import os
import textwrap

from shapely.geometry import Point

from common import *  # noqa: F401,F403
import model as m
from plans import *  # noqa: F401,F403

PWR, LIT, ALM, DAT, GRN = "#6a1b9a", "#b9770e", ACCENT, "#0e7c86", "#2e7d32"
UTILITY = "Mon Power"
SCALE = "3/16\" = 1'-0\""

E1, XH0, XH1, XC0, XC1, XB3, XST, SX0, XEI = m.E1, m.X_H0, m.X_H1, m.X_C0, m.X_C1, m.X_B3, m.X_ST, m.SHAFT_X0, m.XEI
YF, YFI, Y1, Y2, Y3, Y4 = m.YF, m.YFI, m.Y1, m.Y2, m.Y3, m.Y4
W, R = m.xw_i, m.yr_i                       # west and rear wall inside faces
_T = math.atan(abs(REAR_SLOPE))
DIRS = {"n": (0, 1), "s": (0, -1), "e": (1, 0), "w": (-1, 0),
        "r": (-math.sin(_T), -math.cos(_T)),                    # off the angled rear wall, into the room
        "o": (math.cos(WEST_LEAN), -math.sin(WEST_LEAN))}       # off the leaning west wall, into the room
PANEL_C = ((m.PANEL[0] + m.PANEL[2]) / 2, (m.PANEL[1] + m.PANEL[3]) / 2)


def off(p, d, k=0.42):
    if not d:
        return p
    dx, dy = DIRS[d]
    return (p[0] + dx * k, p[1] + dy * k)


# ----------------------------------------------------------------------------
# Circuits: one list drives the plan tags and the panel schedules
# ----------------------------------------------------------------------------
def circuits(unit):
    """(key, spaces, load, amps, poles, wire, protection). A = AFCI, G = GFCI, AG = both."""
    c = [
        ("range", (1, 3), "Range, 240 V", 40, 2, "#8", ""),
        ("dryer", (5, 7), "Dryer, 240 V", 30, 2, "#10", "G"),
        ("wh", (9, 11), f"Water heater WH-{unit} (mech. closet)", 30, 2, "#10", ""),
        ("ahu", (13, 15), "Air handler with 5 kW strip heat", 30, 2, "#10", ""),
        ("hp", (17, 19), f"Heat pump HP-{unit} (west side yard)", 20, 2, "#12", "G*"),
        ("sa1", (21,), "Kitchen counter receptacles (SA-1)", 20, 1, "#12", "AG"),
        ("sa2", (23,), "Island + kitchen wall recept. (SA-2)", 20, 1, "#12", "AG"),
        ("ref", (25,), "Refrigerator", 20, 1, "#12", "AG"),
        ("dw", (2,), "Dishwasher", 20, 1, "#12", "AG"),
        ("mw", (4,), "Microwave / range hood", 20, 1, "#12", "AG"),
        ("washer", (6,), "Washer", 20, 1, "#12", "AG"),
        ("b1", (8,), "Bath 1 receptacle", 20, 1, "#12", "G"),
        ("b2", (10,), "Bath 2 receptacle", 20, 1, "#12", "G"),
        ("b3", (12,), "Bath 3 receptacle", 20, 1, "#12", "G"),
        ("br1", (14,), "Bedroom 1 receptacles", 15, 1, "#14", "A"),
        ("br2", (16,), "Bedroom 2 receptacles", 15, 1, "#14", "A"),
        ("br3", (18,), "Bedroom 3 receptacles", 15, 1, "#14", "A"),
        ("liv", (20,), "Living room + porch receptacles", 20, 1, "#12", "A"),
        ("lt1", (22,), "Lights: bedrooms 1, 2, closets 1, 2", 15, 1, "#14", "A"),
        ("lt2", (24,), "Lights: living, kitchen, bed 3, porch", 15, 1, "#14", "A"),
        ("bath", (26,), "Bath fan/lights and vanity lights", 15, 1, "#14", "A"),
        ("hall", (28,), "Hall: light, alarms, recept., media", 15, 1, "#14", "A"),
        ("spd", (36, 38), "Surge protector (NEC 230.67)", 30, 2, "-", ""),
        ("ev", (37, 39), "SPACE ONLY: future car charger", 0, 2, "-", ""),
    ]
    if unit == "A":
        c += [
            ("cl1", (27,), "CL-1 common lights (automatic)", 15, 1, "#14", "G"),
            ("cl2r", (29,), "CL-2R garage + outdoor receptacles", 20, 1, "#12", "G"),
            ("cl2h", (31, 33), "CL-2H stair + utility heaters, 240 V", 20, 2, "#12", ""),
        ]
    return sorted(c, key=lambda r: r[1][0])


def nums(unit):
    return {k: ",".join(str(s) for s in sp) for k, sp, *_ in circuits(unit)}


NUM = nums("A")                               # the flats use the same numbers; PB simply has no CL circuits

# ---- NEC 2020 Table 310.12 (dwelling feeders) and 250.122 ----
FEEDER = {150: ("3 #1 Cu + #6 Cu ground", "3 #2/0 Al + #4 Al ground"),
          125: ("3 #2 Cu + #6 Cu ground", "3 #1/0 Al + #4 Al ground")}

# ----------------------------------------------------------------------------
# Garage level (common) devices: positions from the model
# ----------------------------------------------------------------------------
YL = m.Y_GR_I - 10.0                                            # garage strips: 10'-0" off the rear wall
G_STRIPS = [(m.xw_gi(YL) + 2.0, YL, "v"), (m.STALL_LINES[0], YL, "v"), (m.STALL_LINES[1], YL, "v"),
            (m.GAR_X1 - 3.5, m.Y_GR_I - 3.5, "h")]
G_REC = [m.GAR_X1 - d for d in (24.0, 13.0, 2.0)]               # one receptacle per stall, on the rear wall
EV_STUB = {"A": m.GAR_X1 - 19.0, "B": m.GAR_X1 - 6.5}           # empty conduit stubs: stall 1 (PA), stall 3 (PB)
EXT_AL = [(41.0, 8.9), (41.4, 6.75)]                            # under the porch soffit: street door; landing + trash bay
STAIR_AL = [(40.64, 12.6), (40.64, 22.4)]                       # this level: lobby and first mid landing
N_STAIR_AL = 5                                                  # lobby, mid landing, Unit A, mid landing, Unit B
UTIL_AL = (40.3, 26.9)
W_G1, W_G2, W_G3, W_G4 = 40, 15, 20, 20                         # watts per automatic fixture
N_CL2R = len(G_REC) + 2                                         # + street-door and heat-pump service receptacles
HTR_STAIR, HTR_UTIL = 1500, 500
CL1_W = len(G_STRIPS) * W_G1 + len(EXT_AL) * W_G2 + N_STAIR_AL * W_G3 + W_G4
METER = m.E_METER
FEED_PATH = [(m.XE, METER[1]), (m.XE - 0.3, METER[1]), (m.XE - 0.3, m.SHAFT_U[3] + 0.35),
             (PANEL_C[0] - 0.35, m.SHAFT_U[3] + 0.35), (PANEL_C[0] - 0.35, PANEL_C[1])]
FEED_LEN = sum(math.dist(a, b) for a, b in zip(FEED_PATH[:-1], FEED_PATH[1:]))
FEED_A = FEED_LEN + 2.0 + 6.5                                   # + rise at the meter + up the wall to the panel
FEED_B = FEED_A + (m.EL_B - m.EL_A)

# ----------------------------------------------------------------------------
# Unit devices (Units A and B are identical)
# ----------------------------------------------------------------------------
# key: [(x, y, wall side, kind, label, tag position)]   kind: R duplex, G GFCI, W weatherproof GFCI, 2 = 240 V, C = hard-wired
REC = {
    "br1": [(15.9, Y1, "s", "R"), (W(18.9), 18.9, "o", "R"), (W(12.6), 12.6, "o", "R"), (15.0, YFI, "n", "R"), (E1, 12.9, "w", "R")],
    "br2": [(14.5, Y4, "n", "R"), (W(29.0), 29.0, "o", "R"), (W(34.75), 34.75, "o", "R"), (12.4, R(12.4), "r", "R"),
            (17.5, R(17.5), "r", "R"), (E1, 31.2, "w", "R")],
    "br3": [(XB3, 27.6, "e", "R"), (29.85, Y2, "n", "R"), (35.95, Y2, "n", "R"), (XST, 29.2, "w", "R"), (31.3, R(31.3), "r", "R")],
    "liv": [(26.1, Y1, "s", "R"), (30.3, Y1, "s", "R"), (XST, 16.5, "w", "R"), (32.1, YFI, "n", "R"), (31.0, YF, "s", "W")],
    "sa1": [(21.3, YFI, "n", "G", None, (22.0, YFI + 0.42, "left")), (XH0, 12.2, "e", "G", None, (XH0 + 0.95, 12.2, "left"))],
    "sa2": [(26.5, m.ISLAND[3], "n", "G", None, (27.25, m.ISLAND[3] + 0.42, "left")),
            (26.5, m.ISLAND[1], "s", "G", None, (27.25, m.ISLAND[1] - 0.42, "left")), (24.2, YFI, "n", "G")],
    "range": [(XH0, 13.5, "e", "2", "RANGE", (XH0 + 0.95, 13.5, "left"))],
    "mw": [(XH0, 14.6, "e", "R", "MW/HOOD", (XH0 + 0.95, 14.6, "left"))],
    "ref": [(XH0, 16.7, "e", "R", "REF", (XH0 + 0.95, 16.7, "left"))],
    "dw": [(26.95, 16.4, None, "R", "DW", (26.4, 16.4, "right"))],
    "washer": [(XC1, 22.3, "w", "G", "W", (XC1 - 0.95, 22.3, "right"))],
    "dryer": [(XC1, 23.6, "w", "2", "D", (XC1 - 0.95, 23.6, "right"))],
    "ahu": [(XC1, 26.2, "w", "C", "AHU", (XC1 - 0.95, 26.2, "right"))],
    "wh": [(25.6, m.HALL_Y1, "s", "C", "WH", (25.1, m.HALL_Y1 - 0.42, "right"))],          # in the flat's mechanical closet
    "b1": [(14.85, Y3, "s", "G")],
    "b2": [(23.15, m.B2_Y0, "n", "G")],
    "b3": [(39.55, m.B3_Y1, "s", "G")],
    "hall": [(XH0, 26.3, "e", "R"), (23.95, m.WD_Y1, "s", "R", "MEDIA", (22.8, 25.0, "right"))],
}
ROOM_C = {"br1": (13.5, 16.0), "br2": (14.3, 32.5), "br3": (32.0, 26.5), "liv": (31.0, 15.5), "sa1": (22.5, 13.0), "sa2": (24.6, 16.0)}
HOME = {"br1": (0.9, -0.45), "br2": (0.9, 0.45), "br3": (0.35, -0.94), "liv": (-0.25, -0.97), "sa1": (0.8, 0.6), "sa2": (-0.9, 0.42)}
FANS = [(15.9, 23.9), (21.9, 33.5), (40.3, 26.3)]                              # bath fan/lights
ALARMS = [("SD", 16.8, 18.2), ("SD", 14.3, 29.6), ("SD", 33.6, 29.0), ("SD", 29.5, 19.6), ("SC", 21.4, 27.5)]
RANGE_C = ((m.RANGE[0] + m.RANGE[2]) / 2, (m.RANGE[1] + m.RANGE[3]) / 2)

# lighting: (type, x, y, circuit key)
FIX = [("A", 13.4, 15.2, "lt1"), ("A", 14.3, 31.4, "lt1"), ("A", 31.9, 24.9, "lt2"), ("A", 32.6, 15.0, "lt2"),
       ("D", 35.3, 12.7, "lt2"), ("D", 23.7, 13.0, "lt2"), ("D", 23.7, 16.9, "lt2"), ("P", 27.0, 15.0, "lt2"),
       ("P", 27.0, 17.5, "lt2"), ("D", 21.4, 24.5, "hall"), ("U", 20.9, 11.25, "lt2"),
       ("F", *FANS[0], "bath"), ("V", 13.5, Y3 - 0.3, "bath"), ("F", *FANS[1], "bath"), ("V", 21.5, m.B2_Y0 + 0.3, "bath"),
       ("F", *FANS[2], "bath"), ("V", 38.4, m.B3_Y1 - 0.3, "bath"),
       ("C", 10.4, 22.7, "lt1"), ("C", 10.5, 25.3, "lt1"), ("C", 28.0, 32.2, "lt2"),
       ("E", 24.75, 23.1, "hall"), ("E", 23.75, 27.45, "hall"), ("X", 30.55, YF - 0.45, "lt2")]
# switches: (x, y, wall side, symbol, fixtures controlled in chain order)
SWITCHES = [(E1, 18.0, "w", "S", [0]), (E1, 30.15, "w", "S", [1]), (29.85, Y2, "n", "S", [2]),
            (XST, 14.35, "w", "S", [3]), (XST, 14.95, "w", "S", [4]),
            (23.45, Y1, "s", "S", [6, 5]), (24.1, Y1, "s", "S", [8, 7]), (24.8, Y1, "s", "S3", [9]), (20.6, m.HALL_Y1, "s", "S3", [9]),
            (15.4, Y2, "n", "S", [11]), (16.0, Y2, "n", "S", [12]), (XH0, 34.7, "e", "S", [13]), (XH0, 35.3, "e", "S", [14]),
            (SX0, 27.05, "e", "S", [15]), (SX0, 27.6, "e", "S", [16]),
            (W(19.5), 19.5, "o", "S", [17]), (W(28.85), 28.85, "o", "S", [18]), (m.C3_X + m.PART, 30.75, "e", "S", [19]),
            (30.3, YFI, "n", "S", [22])]
MEDIA = (23.85, m.WD_Y1 - 0.45)                                                # media box, W/D closet side wall
DATA = [("TV", 32.75, YFI, "n", "C6+RG6"), ("BR1", E1, 13.7, "w", "C6"), ("BR2", 13.6, R(13.6), "r", "C6"), ("BR3", 32.5, R(32.5), "r", "C6")]
TSTAT = (XH0, 25.0)
CHIME = (22.3, m.HALL_Y1)                                                      # hall end wall

# no receptacle may sit inside a door swing
for _k, _devs in REC.items():
    for _dv in _devs:
        _p = off((_dv[0], _dv[1]), _dv[2], 0.42)
        for _d in m.DOORS:
            assert not m.door_sector(_d).contains(Point(*_p)), f"receptacle {_k} at {_p} is inside the swing of {_d['tag']}"
# smoke alarms: 3 ft from a bath door, 10 ft from the range (IRC R314.3)
for _i, (_s, _x, _y) in enumerate(ALARMS):
    if _i >= 3:                                # living room and hall share the kitchen's air; bedrooms are behind doors
        assert math.dist((_x, _y), RANGE_C) >= 10.0, "alarm under 10 ft from the range"
    for _d in m.DOORS:
        if "Bath" in _d["note"]:
            _c = m.door_cut(_d)
            assert Point(_x, _y).distance(Point((_c[0] + _c[2]) / 2, (_c[1] + _c[3]) / 2)) >= 3.0 + _d["w"] / 2, "alarm near a bath door"


# ----------------------------------------------------------------------------
# NEC 220.82 optional calculation, computed from the model
# ----------------------------------------------------------------------------
def load_calc():
    area = m.net_area()
    gen = [(f"General lighting + receptacles, {area:.0f} sf x 3 VA", 3 * area),
           ("Two small-appliance circuits", 3000), ("Laundry circuit", 1500), ("Range (8 kW unit assumed)", 8000),
           ("Dryer", 5000), ("Water heater, 4.5 kW (in the flat)", 4500), ("Dishwasher", 1200), ("Microwave / hood", 1500),
           ("Bath fans, air-handler blower, misc.", 600)]
    tot = sum(v for _, v in gen)
    rem = 0.4 * (tot - 10000)
    heat = [("Heat pump compressor at 100 %", 2200), ("5 kW strip heat at 65 %", 0.65 * 5000)]
    own = 10000 + rem + sum(v for _, v in heat)
    common = [(f"CL-1 automatic lights ({len(G_STRIPS) + len(EXT_AL) + N_STAIR_AL + 1}) + utility recept.", CL1_W + 180),
              (f"CL-2H heaters {HTR_STAIR:,} W + {HTR_UTIL} W", HTR_STAIR + HTR_UTIL),
              (f"CL-2R receptacles, {N_CL2R} x 180 VA", N_CL2R * 180)]
    a = own + sum(v for _, v in common)
    return dict(gen=gen, tot=tot, rem=rem, heat=heat, own=own, common=common, A=a, B=own, ampsA=a / 240, ampsB=own / 240)


LC = load_calc()


# ----------------------------------------------------------------------------
# Sheet helpers
# ----------------------------------------------------------------------------
def wrap(s, width=44):
    return "\n".join(textwrap.wrap(s, width))


def kn(n, s, width=44):
    return "\n".join(textwrap.wrap(s, width, initial_indent=f"{n}  ", subsequent_indent="     " if n < 10 else "       "))


def fit_notes(notes, name):
    """The title-block column is a fixed height: stop the build if the notes run into the PRELIMINARY box."""
    y = SHEET_H - MARGIN - 1.95
    bottom = y
    for head, lines in notes:
        y -= 0.19
        for ln in lines:
            n = ln.count("\n") + 1
            bottom = y - 0.1146 * n
            y -= 0.148 * n + 0.035
        y -= 0.12
    assert bottom > MARGIN + 2.62, f"{name}: notes column is {MARGIN + 2.62 - bottom:.2f} in. too long"
    return notes


def frame(fig, view, title, sub, left=None, bottom=0.72, street=False, north=None, lot_label=None, bar=True, lot=True):
    (vx, vy) = view
    w = (vx[1] - vx[0]) / FPI
    if left is None:
        left = MARGIN + (SHEET_W - 2 * MARGIN - TB_W - w) / 2
    ax = plan_axes(fig, left, bottom, vx, vy, FPI)
    ax.left, ax.bottom, ax.view = left, bottom, view
    if lot:
        line(ax, [LOT_NW, LOT_SW, LOT_SE, LOT_NE, LOT_NW], color=ACCENT, lw=1.0, ls=(0, (9, 2.5, 1.5, 2.5)), z=5.25)
    if lot_label:
        txt(ax, lot_label[0], lot_label[1], "LOT LINE", size=5.0, color=ACCENT, rot=90, box=True)
    if street:
        rect(ax, vx[0], vy[0], vx[1], PAVE_N, fc="#e6e8eb", ec="none", z=1)
        line(ax, [(vx[0], PAVE_N), (vx[1], PAVE_N)], color=GREY, lw=0.6, z=2)
    if north:
        north_arrow(ax, north[0], north[1], 1.8, 6.5)
    if bar:
        scale_bar(ax, vx[0] + 1.5, vy[0] + 1.0, 16, 4, 0.42, size=5.2)
    view_title(ax, vx[0] + 0.6, vy[1] - 1.6, "1", title, sub, 9)
    return ax


def inch(ax, x, y):
    return (ax.left + (x - ax.view[0][0]) / FPI, ax.bottom + (y - ax.view[1][0]) / FPI)


def block(ax, x, y, head, lines, fs=4.8, lh=0.78, color=INK, head_color=None):
    """Small text block in plan units (ft)."""
    if head:
        txt(ax, x, y, head, size=fs + 0.8, weight="bold", ha="left", color=head_color or color)
        y -= lh * 1.25
    for ln in lines:
        n = ln.count("\n") + 1
        txt(ax, x, y, ln, size=fs, ha="left", va="top", color=color)
        y -= lh * n + 0.12
    return y


def audit(fig, name):
    """Development aid (E_AUDIT=1): report text that leaves the sheet or sits on other text."""
    if not os.environ.get("E_AUDIT"):
        return
    r = fig.canvas.get_renderer()
    x_tb = (SHEET_W - MARGIN - TB_W) * fig.dpi
    items = []
    for ax in fig.axes:
        for t in ax.texts:
            s = t.get_text().strip()
            if not s:
                continue
            b = t.get_window_extent(r)
            items.append((s.replace("\n", " / ")[:38], b, t.get_color(), t.get_fontsize()))
    lo, hi_x, hi_y = MARGIN * fig.dpi, (SHEET_W - MARGIN) * fig.dpi, (SHEET_H - MARGIN) * fig.dpi
    for s, b, c, fs in items:
        if b.x0 < lo or b.y0 < lo or b.x1 > hi_x or b.y1 > hi_y:
            print(f"  {name} OFF SHEET: {s}")
        elif b.x0 < x_tb - 2 < b.x1:
            print(f"  {name} CROSSES TITLE BLOCK: {s}")
        if fs < 4.2:
            print(f"  {name} SMALL TEXT {fs}: {s}")
    grey = {"#8a9199"}
    for i, (s, b, c, fs) in enumerate(items):
        for s2, b2, c2, fs2 in items[i + 1:]:
            if c in grey or c2 in grey:
                continue
            w = min(b.x1, b2.x1) - max(b.x0, b2.x0)
            h = min(b.y1, b2.y1) - max(b.y0, b2.y0)
            if w > 2 and h > 2:
                print(f"  {name} OVERLAP: [{s}] x [{s2}]")


# ----------------------------------------------------------------------------
# Symbols
# ----------------------------------------------------------------------------
def tag(ax, x, y, s, color=PWR, size=4.2, box=True, weight="bold", **kw):
    txt(ax, x, y, s, size=size, color=color, weight=weight, box=box, z=12, **kw)


def recept(ax, p, kind="R"):
    x, y = p
    ax.add_patch(plt.Circle((x, y), 0.36, fc=PWR if kind == "2" else PAPER, ec=PWR, lw=0.8, zorder=11))
    if kind in ("G", "W"):
        txt(ax, x, y - 0.02, kind, size=4.2, color=PWR, weight="bold", z=12)


def conn(ax, p, color=PWR):
    """Disconnect switch or hard-wired equipment connection."""
    x, y = p
    rect(ax, x - 0.34, y - 0.34, x + 0.34, y + 0.34, fc=PAPER, ec=color, lw=0.9, z=11)
    line(ax, [(x - 0.34, y - 0.34), (x + 0.34, y + 0.34)], color=color, lw=0.8, z=12)


def light(ax, p, r=0.4):
    x, y = p
    ax.add_patch(plt.Circle((x, y), r, fc=PAPER, ec=LIT, lw=0.9, zorder=11))
    k = r * 0.7
    line(ax, [(x - k, y - k), (x + k, y + k)], color=LIT, lw=0.6, z=12)
    line(ax, [(x - k, y + k), (x + k, y - k)], color=LIT, lw=0.6, z=12)


def pendant(ax, p):
    x, y = p
    ax.add_patch(plt.Circle((x, y), 0.4, fc=PAPER, ec=LIT, lw=0.9, zorder=11))
    ax.add_patch(plt.Circle((x, y), 0.14, fc=LIT, ec=LIT, lw=0.5, zorder=12))


def bar(ax, p, length=2.0, orient="h", color=LIT):
    x, y = p
    a, b = (length / 2, 0.17) if orient == "h" else (0.17, length / 2)
    rect(ax, x - a, y - b, x + a, y + b, fc=PAPER, ec=color, lw=0.9, z=11)


def fanlight(ax, p, color=LIT):
    x, y = p
    rect(ax, x - 0.48, y - 0.48, x + 0.48, y + 0.48, fc=PAPER, ec=color, lw=0.9, z=11)
    ax.add_patch(plt.Circle((x, y), 0.3, fc=PAPER, ec=color, lw=0.7, zorder=12))
    line(ax, [(x - 0.2, y - 0.2), (x + 0.2, y + 0.2)], color=color, lw=0.5, z=13)
    line(ax, [(x - 0.2, y + 0.2), (x + 0.2, y - 0.2)], color=color, lw=0.5, z=13)


def auto_light(ax, p):
    """AUTOMATIC light: fixture plus a solid sensor triangle."""
    x, y = p
    light(ax, p)
    poly(ax, [(x + 0.5, y - 0.42), (x + 1.24, y - 0.42), (x + 0.87, y + 0.42)], fc=LIT, ec=LIT, lw=0.4, z=12)


def auto_strip(ax, p, orient="v", length=4.0):
    x, y = p
    h = length / 2
    if orient == "v":
        rect(ax, x - 0.24, y - h, x + 0.24, y + h, fc=PAPER, ec=LIT, lw=0.9, z=11)
        poly(ax, [(x - 0.4, y + h + 0.12), (x + 0.4, y + h + 0.12), (x, y + h + 0.86)], fc=LIT, ec=LIT, lw=0.4, z=12)
    else:
        rect(ax, x - h, y - 0.24, x + h, y + 0.24, fc=PAPER, ec=LIT, lw=0.9, z=11)
        poly(ax, [(x + h + 0.12, y - 0.4), (x + h + 0.12, y + 0.4), (x + h + 0.86, y)], fc=LIT, ec=LIT, lw=0.4, z=12)


def heater(ax, p, orient="v", length=1.2):
    x, y = p
    a, b = (0.2, length / 2) if orient == "v" else (length / 2, 0.2)
    rect(ax, x - a, y - b, x + a, y + b, fc=PWR, ec=PWR, lw=0.6, z=11, hatch="////", alpha=0.85)


def switch(ax, p, s="S"):
    txt(ax, p[0], p[1], s, size=4.6, color=LIT, weight="bold", z=13)


def alarm(ax, p, s="SD"):
    x, y = p
    rect(ax, x - 0.52, y - 0.4, x + 0.52, y + 0.4, fc=PAPER, ec=ALM, lw=0.9, z=11)
    txt(ax, x, y - 0.02, s, size=4.2, color=ALM, weight="bold", z=12)


def lowv(ax, p, s, color=DAT):
    """Low-voltage device: triangle outlet (data) or lettered box."""
    x, y = p
    if s == "D":
        poly(ax, [(x - 0.4, y - 0.32), (x + 0.4, y - 0.32), (x, y + 0.42)], fc=color, ec=color, lw=0.6, z=11)
    else:
        rect(ax, x - 0.46, y - 0.38, x + 0.46, y + 0.38, fc=PAPER, ec=color, lw=0.9, z=11)
        txt(ax, x, y - 0.02, s, size=4.2, color=color, weight="bold", z=12)


def keynote(ax, x, y, n, color=PWR, r=0.62):
    pts = [(x + r * math.cos(math.radians(a)), y + r * math.sin(math.radians(a))) for a in range(0, 360, 60)]
    poly(ax, pts, fc=PAPER, ec=color, lw=1.0, z=13)
    txt(ax, x, y - 0.02, str(n), size=4.4, color=color, weight="bold", z=14)


def wire(ax, p, q, toward=None, k=0.14, color=PWR, lw=0.4, ls="-", z=10):
    """Curved run between two devices (diagrammatic), bowed toward `toward`."""
    (x0, y0), (x1, y1) = p, q
    length = math.hypot(x1 - x0, y1 - y0) or 1.0
    nx, ny = -(y1 - y0) / length, (x1 - x0) / length
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    if toward is not None and (toward[0] - mx) * nx + (toward[1] - my) * ny < 0:
        nx, ny = -nx, -ny
    cx, cy = mx + nx * 2 * k * length, my + ny * 2 * k * length
    t = np.linspace(0, 1, 24)
    ax.plot((1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t ** 2 * x1, (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t ** 2 * y1,
            color=color, lw=lw, ls=ls, zorder=z)


def arrow(ax, p, q, color=PWR, lw=0.6, z=11, scale=5):
    ax.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle="-|>", lw=lw, color=color, mutation_scale=scale,
                                                    shrinkA=0, shrinkB=0), zorder=z)


def homerun(ax, p, vec, length=1.9, color=PWR):
    n = math.hypot(*vec)
    ux, uy = vec[0] / n, vec[1] / n
    arrow(ax, (p[0] + ux * 0.42, p[1] + uy * 0.42), (p[0] + ux * length, p[1] + uy * length), color=color)


def leader(ax, pts, color=GREY, lw=0.35, dot=True):
    line(ax, pts, color=color, lw=lw, z=10.5)
    if dot:
        ax.add_patch(plt.Circle(pts[-1], 0.1, fc=color, ec=color, zorder=10.5))


def legend(ax, x, y, items, dy=1.3, size=4.6, title="LEGEND"):
    txt(ax, x - 0.6, y + 1.5, title, size=5.8, weight="bold", ha="left")
    for fn, s in items:
        fn(ax, (x + 0.35, y))
        txt(ax, x + 1.9, y, s, size=size, ha="left")
        y -= dy * (1 + 0.42 * s.count("\n"))
    return y


def _l_wire(color, ls, lw=0.8):
    return lambda ax, p: line(ax, [(p[0] - 0.85, p[1]), (p[0] + 0.95, p[1])], color=color, lw=lw, ls=ls, z=11)


def _l_txt(s, color, size=4.6):
    return lambda ax, p: txt(ax, p[0], p[1], s, size=size, color=color, weight="bold")


# ----------------------------------------------------------------------------
# E-101  Garage level and service
# ----------------------------------------------------------------------------
def sheet_e101(pdf):
    g_meter = elev(m.XE + 1.5, METER[1])
    g_hp = sum(elev(*h) for h in m.HP) / len(m.HP)
    notes = fit_notes([
        ("Keynotes", [
            kn(1, "AUTOMATIC GARAGE LIGHT: 4 ft LED strip, wet-rated, 40 W. Its own occupancy sensor and photocell "
                  "turn it on only when someone is there and it is dark. NO wall switch. CL-1."),
            kn(2, "AUTOMATIC OUTSIDE LIGHT under the porch soffit, full cut-off, same control: street door, landing, trash bay."),
            kn(3, "AUTOMATIC STAIR LIGHT with battery pack at every landing (E-104), and the utility room light. CL-1."),
            kn(4, "GARAGE RECEPTACLE, one per stall: 20 A GFCI, weather-resistant, lockable in-use cover, 48 in. up. CL-2R."),
            kn(5, "WALL HEATER with thermostat, 240 V: stair 1,500 W, utility room 500 W. CL-2H."),
            kn(6, "FUTURE CAR CHARGER: empty 1 in. conduit, pull string, blank cover. Stall 1 to PA, stall 3 to PB."),
            kn(7, "METER STACK: 2 meters, 2 main breakers. Keep 3 ft clear in front."),
            kn(8, f"SERVICE LATERAL underground in conduit. Pole location unknown: set the route with {UTILITY}."),
            kn(9, "GROUNDING ELECTRODE in the footing: place it BEFORE the footing pour."),
            kn(10, "FEEDERS to panels PA and PB. Sizes: E-201."),
            kn(11, "HEAT PUMP DISCONNECTS, 30 A, and a GFCI service receptacle at the pads."),
            kn(12, "LEASE: CL-1, CL-2R and CL-2H run on Unit A's meter. Unit A's lease must disclose the common load and credit it."),
        ]),
    ], "E-101")
    fig, bg = new_sheet("E-101", "Electrical: garage level and service", SCALE, notes)
    view = ((-12.0, 58.0), (-8.5, 41.0))
    ax = frame(fig, view, "Garage level power and service plan",
               f"Garage floor EL {m.EL_GAR:.1f} · common loads on Unit A's panel PA (CL)",
               street=True, north=(55.3, 37.6), lot_label=(50.0, 29.3))
    site_work(ax, bg=True)
    lower_plan(ax, "bg")
    txt(ax, 24.0, -7.75, "BAIRD STREET", size=5.6, color=GREY, weight="bold")
    txt(ax, 5.2, -0.7, "FRONT LOT LINE = R.O.W. LINE", size=4.6, color=ACCENT)
    px0, py0, px1, py1 = m.PORCH
    line(ax, [(px0, py1), (px0, py0), (px1, py0), (px1, py1)], color=BG_EDGE, lw=0.5, ls=(0, (4, 2)), z=6)
    txt(ax, 24.0, py0 + 0.55, "PORCH ABOVE (soffit about 9 ft over the apron)", size=4.4, color="#8a9199")

    # ---- CL-1: automatic lights ----
    for (x, y, o) in G_STRIPS:
        auto_strip(ax, (x, y), o)
    (ax_, ay_, _), (bx_, by_, _), (cx_, cy_, _), (dx_, dy_, _) = G_STRIPS
    run = dict(color=LIT, lw=0.5, ls=(0, (1.2, 1.6)))
    wire(ax, (ax_ + 0.24, ay_), (bx_ - 0.24, by_), k=0, **run)
    wire(ax, (bx_ + 0.24, by_), (cx_ - 0.24, cy_), k=0, **run)
    wire(ax, (cx_ + 0.24, cy_ + 1.0), (dx_ - 2.0, dy_), k=0, **run)
    wire(ax, (dx_ + 2.9, dy_), (UTIL_AL[0] - 0.4, UTIL_AL[1]), k=0, **run)
    wire(ax, (UTIL_AL[0], UTIL_AL[1] - 0.4), (STAIR_AL[1][0], STAIR_AL[1][1] + 0.4), k=0, **run)
    wire(ax, (STAIR_AL[1][0], STAIR_AL[1][1] - 0.4), (STAIR_AL[0][0], STAIR_AL[0][1] + 0.4), k=0, **run)
    wire(ax, (STAIR_AL[0][0], STAIR_AL[0][1] - 0.4), (EXT_AL[0][0], EXT_AL[0][1] + 0.4), k=0, **run)
    wire(ax, (EXT_AL[0][0], EXT_AL[0][1] - 0.4), (EXT_AL[1][0], EXT_AL[1][1] + 0.4), k=0, **run)
    for p in STAIR_AL + EXT_AL + [UTIL_AL]:
        auto_light(ax, p)
    keynote(ax, ax_ + 1.25, ay_ - 1.0, 1)
    keynote(ax, bx_ + 1.25, by_ - 1.0, 1)
    keynote(ax, cx_ + 1.25, cy_ - 1.0, 1)
    keynote(ax, dx_ - 0.8, dy_ + 1.05, 1)
    keynote(ax, 42.9, 7.8, 2)
    keynote(ax, 42.6, 22.4, 3)
    keynote(ax, 38.75, 12.6, 3)
    dim(ax, (m.xw_gi(YL), YL - 2.0), (ax_, YL - 2.0), -0.7, size=5.2)
    dim(ax, (ax_ + 0.24, YL), (ax_ + 0.24, m.Y_GR_I), -0.75, size=5.2)
    txt(ax, bx_ - 2.9, YL - 2.75, "ON THE STALL LINE", size=4.4, color=LIT, weight="bold", box=True)
    txt(ax, cx_ - 2.9, YL - 2.75, "ON THE STALL LINE", size=4.4, color=LIT, weight="bold", box=True)
    txt(ax, bx_ + 4.3, YL + 0.75, f"STRIP CENTRES {ftin(m.Y_GR_I - YL)} OFF THE REAR WALL", size=4.4, color=LIT, weight="bold", box=True)
    txt(ax, dx_, dy_ - 0.72, f"{ftin(m.Y_GR_I - dy_)} OFF THE REAR WALL", size=4.2, color=LIT, weight="bold", box=True)
    # home run of CL-1 to the panel above
    rect(ax, PANEL_C[0] - 0.55, m.PANEL[1], PANEL_C[0] + 0.25, m.PANEL[3], fc=PAPER, ec=PWR, lw=0.9, z=11, ls=(0, (2, 1.2)))
    arrow(ax, (bx_, by_ + 2.95), (PANEL_C[0] - 0.15, m.PANEL[1] - 0.05), color=LIT)
    tag(ax, bx_ + 1.35, by_ + 2.75, "CL-1", LIT)
    tag(ax, 14.4, 21.7, "PANEL PA ABOVE\n(Unit A hall; PB is over it)", PWR, size=4.4)
    leader(ax, [(16.6, 22.3), (PANEL_C[0] - 0.6, 23.2)], color=PWR, dot=False)

    # ---- CL-2R: receptacles; empty conduit stubs ----
    yrw = m.Y_GR_I
    for x in G_REC:
        recept(ax, (x, yrw - 0.45), "W")
        keynote(ax, x, yrw - 1.75, 4)
        tag(ax, x + 1.2, yrw - 0.45, "CL-2R")
    for u, x in EV_STUB.items():
        rect(ax, x - 0.36, yrw - 0.8, x + 0.36, yrw - 0.08, fc=PAPER, ec=PWR, lw=0.9, z=11, ls=(0, (2, 1.2)))
        keynote(ax, x, yrw - 1.75, 6)
    xs = [m.xw_gi(yrw)] + sorted(G_REC + list(EV_STUB.values())) + [m.GAR_X1]
    for a, b in zip(xs[:-1], xs[1:]):
        dim(ax, (a, m.Y_GR_O), (b, m.Y_GR_O), 1.1, size=5.2)
    txt(ax, 23.0, m.Y_GR_O + 2.25, "RECEPTACLES AND CONDUIT STUBS ON THE REAR WALL, 48 in. ABOVE THE FLOOR (clear of the pipe chases, P-101)",
        size=4.4, color=PWR)
    ec = dict(color=PWR, lw=0.7, ls=(0, (5, 1.5, 1, 1.5)))
    line(ax, [(PANEL_C[0] - 0.55, 23.75), (EV_STUB["A"], 23.75), (EV_STUB["A"], yrw - 0.8)], z=9.5, **ec)
    line(ax, [(PANEL_C[0] + 0.25, 23.0), (EV_STUB["B"], 23.0), (EV_STUB["B"], yrw - 0.8)], z=9.5, **ec)
    tag(ax, 25.7, 22.4, "EMPTY CONDUIT, PB TO STALL 3", PWR, size=4.2, weight="normal")
    tag(ax, 14.9, 25.3, "EMPTY CONDUIT,\nPA TO STALL 1", PWR, size=4.2, weight="normal")
    # street-door receptacle
    recept(ax, (43.75, YF - 0.45), "W")
    tag(ax, 46.6, YF - 0.45 - 0.9, "CL-2R", PWR)
    leader(ax, [(45.9, YF - 1.25), (44.1, YF - 0.6)], color=PWR, dot=False)

    # ---- CL-2H: heaters; utility room ----
    heater(ax, (m.XE_GI - 0.2, 12.25), "v")
    keynote(ax, 42.55, 11.75, 5)
    heater(ax, (SX0 + 0.2, 25.4), "v", 1.1)
    recept(ax, (38.6, m.UTIL[2] + 0.42), "G")
    ux = 38.2
    txt(ax, ux - 0.5, 34.15, "UTILITY ROOM (heated, locked)", size=5.0, weight="bold", ha="left", color=PWR)
    for j, (n, s) in enumerate([(5, "500 W wall heater, CL-2H: keeps the room above freezing"),
                                (3, "Automatic light and GFCI receptacle, CL-1")]):
        keynote(ax, ux, 33.05 - j * 1.1, n, r=0.5)
        txt(ax, ux + 0.85, 33.05 - j * 1.1, s, size=4.4, ha="left")
    leader(ax, [(40.6, 31.3), (40.6, 29.9), (39.6, 25.9)], color=PWR)

    # ---- service: meter stack, lateral, grounding, feeders ----
    rect(ax, m.XE, METER[1] - 1.15, m.XE + 0.6, METER[1] + 1.15, fc=PWR, ec=PWR, z=11)
    dim(ax, (m.XE, YF), (m.XE, METER[1]), -1.75, size=5.0)
    xl = 49.0
    line(ax, [(m.XE + 0.6, METER[1]), (xl, METER[1]), (xl, -5.2)], color=PWR, lw=1.5, ls=(0, (6, 2)), z=10)
    arrow(ax, (xl, -5.0), (xl, -6.6), color=PWR, lw=1.2, scale=8)
    line(ax, [(m.XE - 0.75, YF + 0.1), (m.XE - 0.75, m.Y_GR_O - 0.1)], color=GRN, lw=1.1, ls=(0, (3, 1.5)), z=10)
    line(ax, [(m.XE - 0.75, METER[1] + 0.75), (m.XE + 0.1, METER[1] + 0.75)], color=GRN, lw=1.1, z=10)
    line(ax, [(m.XE - 0.75, m.WATER_ENTRY[1] - 0.2), (m.XE_GI - 0.25, m.WATER_ENTRY[1] - 0.2)], color=GRN, lw=1.1, z=10)
    ax.add_patch(plt.Circle((m.XE_GI - 0.25, m.WATER_ENTRY[1] - 0.2), 0.16, fc=GRN, ec=GRN, zorder=11))
    line(ax, FEED_PATH, color=PWR, lw=1.3, ls=(0, (3, 1.6)), z=10)
    keynote(ax, 28.4, FEED_PATH[2][1], 10)
    tag(ax, 23.4, FEED_PATH[2][1] + 0.72, "FEEDERS PA + PB, in the floor trusses above", PWR, size=4.2, weight="normal")
    tx = 52.4
    for (n, y, target, lines) in [
        (7, 17.6, (m.XE + 0.6, METER[1] + 0.7),
         ["METER STACK", "2 meters + 2 main breakers", f"A {m.PANEL_A_AMPS} A · B {m.PANEL_B_AMPS} A, NEMA 3R",
          f"{ftin(METER[1] - YF)} from the corner,", "centre 4 to 6 ft above grade", f"(grade about EL {g_meter:.1f})"]),
        (9, 25.4, (m.XE - 0.75, 24.6),
         ["GROUNDING", "20 ft of bare #4 Cu in the", "east-wall footing, stubbed", "up at the meter. #4 Cu bond",
          "to the metal water piping", "in the utility room."]),
        (8, 6.6, (xl, 5.6),
         ["SERVICE LATERAL", "underground in conduit,", "24 in. min. cover. Shown", "1'-0\" inside the lot line:",
          "pole, route and depth to be", f"set with {UTILITY}.", "Keep 12 in. off the water", "services (C-106)."]),
    ]:
        keynote(ax, tx - 0.95, y, n)
        leader(ax, [(tx - 1.55, y), target], color=PWR)
        txt(ax, tx, y + 0.3, lines[0], size=4.8, weight="bold", ha="left", color=PWR, va="center")
        txt(ax, tx, y - 0.25, "\n".join(lines[1:]), size=4.3, ha="left", va="top")

    # ---- west side yard: heat pumps ----
    for i, (y, u) in enumerate(((18.2, "A"), (22.55, "B"))):
        p = (m.xw_o(y) - 0.4, y)
        conn(ax, p)
        tag(ax, p[0] - 0.65, y, f"HP-{u} DISC. · P{u} cct {NUM['hp']}", PWR, ha="right")
    pr = (m.xw_o(27.0) - 0.42, 27.0)
    recept(ax, pr, "W")
    tag(ax, pr[0] - 0.65, 27.0, "SERVICE RECEPT. · CL-2R", PWR, ha="right")
    keynote(ax, 3.9, 24.7, 11)
    for i, (hx, hy) in enumerate(m.HP):
        txt(ax, hx, hy, f"HP\n{'AB'[i]}", size=4.2, color=GREY, z=8)
    txt(ax, 4.45, 14.6, f"WEST SIDE YARD\ngrade EL {g_hp:.1f}:\n{g_hp - m.EL_GAR:.0f} ft above the\ngarage floor", size=4.3, color=PWR)

    # ---- legend, common-circuit table, general notes ----
    legend(ax, -11.2, 33.0, [
        (lambda a, p: auto_strip(a, (p[0], p[1] - 0.3), "v", 1.5), "AUTOMATIC LIGHT, 4 ft LED strip: built-in\noccupancy sensor + photocell, no switch"),
        (auto_light, "AUTOMATIC LIGHT, ceiling, wall or soffit"),
        (lambda a, p: recept(a, p, "W"), "GFCI receptacle, weather-resistant,\nlockable in-use cover"),
        (lambda a, p: recept(a, p, "G"), "GFCI receptacle"),
        (conn, "Disconnect switch, 30 A, non-fused"),
        (lambda a, p: heater(a, p, "h"), "Electric wall heater with thermostat"),
        (lambda a, p: rect(a, p[0] - 0.36, p[1] - 0.36, p[0] + 0.36, p[1] + 0.36, fc=PAPER, ec=PWR, lw=0.9, z=11, ls=(0, (2, 1.2))),
         "Empty conduit stub, blank cover"),
        (_l_wire(PWR, (0, (5, 1.5, 1, 1.5)), 0.7), "Empty 1 in. conduit in the truss space"),
        (_l_wire(PWR, (0, (3, 1.6)), 1.3), "Feeder, in the floor trusses above"),
        (_l_wire(PWR, (0, (6, 2)), 1.5), "Underground service lateral"),
        (_l_wire(GRN, (0, (3, 1.5)), 1.1), "Grounding electrode and bonds"),
        (_l_wire(LIT, (0, (1.2, 1.6)), 0.6), "Circuit CL-1 run (in the truss space)"),
        (lambda a, p: keynote(a, p[0], p[1], 1, r=0.5), "Keynote: see the list at right"),
    ], dy=1.3)
    block(ax, -11.8, 12.4, "GENERAL", [
        "All of this level is fed from Unit A's panel PA, except heat pump HP-B (panel PB).",
        "Water heaters are in the flats (E-102, E-103): nothing for them at this level.",
        "Feeders: through the wall at the meter, up in the stair east wall, north to the end",
        f"of the stair shaft, then west in each flat's own floor trusses (about {FEED_A:.0f} and {FEED_B:.0f} ft).",
        "Open garage = damp / wet location: wet-rated fixtures, in-use covers.",
        "On the concrete walls: surface EMT or schedule 80 PVC with cast boxes.",
        "Above the ceiling: in the floor trusses, over the R-30. The ceiling is the rated",
        "garage ceiling (5/8 in. Type X): listed boxes, seal every hole.",
        "Not included, not wired: cameras, door operators, heat cable, sump pump.",
        "Confirm with the inspector: GFCI on the outdoor heat-pump circuits (NEC 210.8(F))",
        "and outdoor receptacles for the flats (210.52(E)).",
    ], fs=4.5, lh=0.7)
    x_in, y_in = inch(ax, 4.9, 37.2)
    bg.text(x_in, y_in + 0.05, "COMMON CIRCUITS, ALL ON UNIT A'S PANEL PA (no house meter)", fontsize=6.2, fontweight="bold", color=INK, va="bottom")
    table(bg, x_in, y_in, [0.5, 1.2, 3.4, 0.8], [
        ["Circuit", "Breaker, wire", "Serves", "Load"],
        ["CL-1", "15 A 1-pole, #14 Cu", f"Automatic lights: garage {len(G_STRIPS)}, stair {N_STAIR_AL}, outside {len(EXT_AL)}, utility room 1; utility receptacle",
         f"{CL1_W} W + 180 VA"],
        ["CL-2R", "20 A 1-pole GFCI, #12", f"{len(G_REC)} garage receptacles (own circuit, NEC 210.11(C)(4)), street-door + heat-pump receptacles",
         f"{N_CL2R} x 180 VA"],
        ["CL-2H", "20 A 2-pole, #12 Cu", f"Stair heater {HTR_STAIR:,} W and utility-room heater {HTR_UTIL} W, 240 V", f"{HTR_STAIR + HTR_UTIL:,} W"],
    ], fs=5.2, rh=0.175)
    audit(fig, "E-101")
    save(fig, "E-101", pdf)


# ----------------------------------------------------------------------------
# E-102 / E-103  Unit power
# ----------------------------------------------------------------------------
def power_plan(ax, unit):
    num = nums(unit)
    # panel and working space
    px0, py0, px1, py1 = m.PANEL
    rect(ax, px0, PANEL_C[1] - 1.25, px0 + 3.0, PANEL_C[1] + 1.25, fc="none", ec=PWR, lw=0.7, z=10, ls=(0, (3, 1.5)))
    rect(ax, px0, py0, px1, py1, fc=PWR, ec=PWR, z=11)
    tag(ax, px0 + 1.75, PANEL_C[1] + 0.45, f"P{unit}", PWR, size=5.4, box=False)
    tag(ax, px0 + 1.75, PANEL_C[1] - 0.45, "30 x 36 in.\nCLEAR", PWR, size=4.2, weight="normal", box=False)
    # runs and home runs
    for key, devs in REC.items():
        pts = [off((d[0], d[1]), d[2], 0.42) for d in devs]
        if key in ROOM_C:
            for a, b in zip(pts[:-1], pts[1:]):
                wire(ax, a, b, toward=ROOM_C[key], k=0.1)
            homerun(ax, pts[0], HOME[key])
    for key, devs in REC.items():
        for d in devs:
            x, y, side, kind = d[:4]
            label = d[4] if len(d) > 4 else None
            tpos = d[5] if len(d) > 5 else None
            p = off((x, y), side, 0.42)
            conn(ax, p) if kind == "C" else recept(ax, p, kind)
            s = num[key] + (f" {label}" if label else "")
            if tpos:
                tag(ax, tpos[0], tpos[1], s, ha=tpos[2])
            else:
                t = off((x, y), side, 1.22)
                tag(ax, t[0], t[1], s)
    for (x, y) in FANS:
        fanlight(ax, (x, y), PWR)
        tag(ax, x + 1.05, y, num["bath"])
    for i, (s, x, y) in enumerate(ALARMS):
        alarm(ax, (x, y), s)
        tag(ax, x + (-1.1 if i == 3 else 1.1), y, num["hall"])
    # circuits that leave the floor: keynotes at the panel
    ky = 19.45
    leader(ax, [(21.2, ky + 0.62), (px0 + 0.6, py0 - 0.25)], color=PWR, dot=False)
    n_k = 4 if unit == "A" else 3
    for i in range(n_k):
        keynote(ax, 20.6 + i * 1.3, ky, i + 1)


def unit_power_sheet(pdf, number, unit):
    el = m.EL_A if unit == "A" else m.EL_B
    amps = m.PANEL_A_AMPS if unit == "A" else m.PANEL_B_AMPS
    num = nums(unit)
    keys = [
        kn(1, f"HEAT PUMP, cct {num['hp']}: leaves this floor at the panel, west in this flat's floor trusses to the disconnect "
              f"at pad HP-{unit} (E-101)."),
        kn(2, f"FEEDER from Unit {unit}'s main breaker at the meter stack arrives in this flat's floor trusses (E-101, E-201). 4-wire: "
              "neutral bar NOT bonded to the can."),
        kn(3, f"EMPTY 1 in. CONDUIT down to garage stall {'1' if unit == 'A' else '3'} for a future car charger (E-101)."),
    ]
    if unit == "A":
        keys.append(kn(4, f"COMMON CIRCUITS CL-1, CL-2R, CL-2H (cct {num['cl1']}, {num['cl2r']}, {num['cl2h']}) leave here for the garage, "
                          "stair, outside lights and heaters (E-101). Unit A's lease must disclose and credit them."))
    notes = [
        (f"Unit {unit} power", [
            wrap(f"Panel P{unit}: {amps} A, 40 spaces, in the hall, fed from Unit {unit}'s own meter. Keep 30 in. wide x 36 in. deep x "
                 "6'-6\" high clear in front. Circuit numbers: see the panel schedule, E-201."),
        ]),
        ("Rules (2020 NEC)", [
            wrap("Receptacles: no point along a wall more than 6 ft from one (210.52), none behind a door. Tamper-resistant. "
                 "Kitchen: two 20 A small-appliance circuits; two receptacles on the island ends (210.52(C))."),
            wrap("AFCI: every 120 V circuit except the bath receptacles. GFCI: kitchen, baths, laundry, dryer, dishwasher, porch."),
            wrap(f"Mechanical closet: water heater (cct {num['wh']}) and air handler (cct {num['ahu']}), each with a 30 A "
                 "disconnect in the closet."),
        ]),
        ("Keynotes", keys),
    ]
    if unit == "B":
        notes.append(("Common loads", [wrap("None on this panel. Garage, stair and outside lights and heaters are on Unit A's panel (E-101).")]))
    fit_notes(notes, number)
    fig, bg = new_sheet(number, f"Electrical: Unit {unit} power", SCALE, notes)
    ax = frame(fig, ((-14.0, 53.0), (3.0, 47.0)), f"Unit {unit} power plan",
               f"Floor EL {el:.1f} · numbers = circuits in panel P{unit} (E-201) · arrows = home runs",
               bottom=0.8, north=(50.0, 43.0), lot_label=(50.0, 22.0))
    unit_plan(ax, "bg", unit)
    power_plan(ax, unit)
    y = legend(ax, -13.0, 41.6, [
        (lambda a, p: recept(a, p, "R"), "Duplex receptacle, tamper-resistant"),
        (lambda a, p: recept(a, p, "G"), "GFCI-protected receptacle"),
        (lambda a, p: recept(a, p, "W"), "Weather-resistant GFCI, in-use cover"),
        (lambda a, p: recept(a, p, "2"), "240 V receptacle"),
        (conn, "Hard-wired equipment + disconnect"),
        (lambda a, p: fanlight(a, p, PWR), "Bath exhaust fan / light (E-104, M-201)"),
        (alarm, "Smoke (SD), smoke + CO (SC) alarm, E-105"),
        (lambda a, p: rect(a, p[0] - 0.2, p[1] - 0.45, p[0] + 0.2, p[1] + 0.45, fc=PWR, ec=PWR, z=11), f"Panel P{unit}, recessed in the hall wall"),
        (lambda a, p: rect(a, p[0] - 0.5, p[1] - 0.4, p[0] + 0.5, p[1] + 0.4, fc="none", ec=PWR, lw=0.7, z=11, ls=(0, (3, 1.5))),
         "Working space kept clear"),
        (lambda a, p: (wire(a, (p[0] - 0.9, p[1] - 0.2), (p[0] + 0.1, p[1] - 0.2), k=0.25, toward=(p[0], p[1] + 5)),
                       arrow(a, (p[0] + 0.1, p[1] - 0.2), (p[0] + 1.0, p[1] + 0.3))), "Circuit run and home run to the panel"),
        (_l_txt("14", PWR), "Circuit number (list below, E-201)"),
        (lambda a, p: keynote(a, p[0], p[1], 1, r=0.5), "Keynote: see the list at right"),
    ], dy=1.22)
    y -= 0.5
    txt(ax, -13.6, y, f"CIRCUITS, PANEL P{unit}", size=5.8, weight="bold", ha="left")
    y -= 1.0
    for key, sp, name, a, poles, wire_, prot in circuits(unit):
        if key in ("spd", "ev", "lt1", "lt2"):
            continue
        txt(ax, -11.3, y, ",".join(str(s) for s in sp), size=4.4, color=PWR, weight="bold", ha="right")
        txt(ax, -10.8, y, f"{name.replace(' (mech. closet)', '').replace(' (west side yard)', '')} · {a} A", size=4.4, ha="left")
        y -= 0.83
    txt(ax, -10.8, y, f"Lights: circuits {num['lt1']}, {num['lt2']} (E-104). Spaces 36-40: E-201.", size=4.4, ha="left", color=GREY)
    txt(ax, 26.0, 5.05, "MOUNTING HEIGHTS, to the centre above the floor: receptacles 16 in. · kitchen counter, island and bath receptacles 44 in.\n"
        "washer and dryer 42 in. · switches 48 in. · panel: highest breaker handle 6'-7\" max. · porch receptacle 18 in.",
        size=4.5, color=INK)
    audit(fig, number)
    save(fig, number, pdf)


def sheet_e102(pdf):
    unit_power_sheet(pdf, "E-102", "A")


def sheet_e103(pdf):
    unit_power_sheet(pdf, "E-103", "B")


# ----------------------------------------------------------------------------
# E-104  Lighting
# ----------------------------------------------------------------------------
FIX_TAG = {10: (0, 0.75, 0, -0.75), 12: (-1.6, 0, 1.6, 0), 14: (-1.6, 0, 1.6, 0), 16: (-1.6, 0, 1.6, 0),
           22: (1.3, -0.1, 2.3, -0.1), 20: (-0.85, 0.35, 0.9, 0.35), 21: (0.8, 0, 1.6, 0)}


def draw_fixture(ax, t, p):
    if t in ("A", "D", "C", "E", "X"):
        light(ax, p, 0.4 if t == "A" else 0.32)
    elif t == "P":
        pendant(ax, p)
    elif t == "F":
        fanlight(ax, p)
    elif t == "V":
        bar(ax, p, 2.0)
    elif t == "U":
        bar(ax, p, 1.5)


def sheet_e104(pdf):
    notes = fit_notes([
        ("Lighting, both flats", [
            wrap("Units A and B are wired alike: one plan. All fixtures LED. Unit A's ceiling is the rated two-layer ceiling: "
                 "surface fixtures on listed boxes only, or fixtures in the 7'-0\" soffits. Nothing recessed through it. "
                 "Unit B: surface fixtures under the insulated attic floor."),
            wrap("Switches 48 in. up, on the latch side of each door, inside the room. Bedrooms 1 and 3 and the kitchen are entered "
                 "from the living room; bedroom 2 from the hall."),
            wrap(f"Ceilings: Unit A {ftin(m.CLG_A)}, Unit B {ftin(m.CLG_B)}, duct soffits {ftin(m.CLG_SOFFIT)} (M-102). Keep fixtures off the soffit registers."),
        ]),
        ("Keynotes", [
            kn(1, "COMMON STAIR LIGHTS (type G3), AUTOMATIC: occupancy sensor, battery pack, no switch. On CL-1 from Unit A's panel "
                  "in BOTH flats' stair landings, never on PB."),
            kn(2, "HALL LIGHT on two 3-way switches: at the living room end and at the bedroom 2 door."),
            kn(3, "PORCH LIGHT on this flat's own panel, switched inside at the porch door. Full cut-off, aimed down."),
            kn(4, "CLOSET LIGHTS: enclosed LED, 6 in. min. (recessed) or 12 in. (surface) clear of the shelf space, NEC 410.16."),
            kn(5, "BATH: fan/light on one switch, vanity light on the other. Fan runs on a timer or humidity control (M-201)."),
        ]),
    ], "E-104")
    fig, bg = new_sheet("E-104", "Electrical: lighting, Units A and B", SCALE, notes)
    ax = frame(fig, ((-13.5, 53.0), (5.0, 44.0)), "Lighting plan, typical for Unit A and Unit B",
               "Letter = fixture type · number = circuit · dashed arc = switch leg",
               bottom=2.95, north=(50.0, 40.0), lot_label=(50.0, 22.0))
    unit_plan(ax, "bg", "A")
    leg = dict(color=LIT, lw=0.5, ls=(0, (2.2, 1.6)))
    for (x, y, side, s, ctl) in SWITCHES:
        p = off((x, y), side, 0.42)
        prev = p
        for i in ctl:
            q = (FIX[i][1], FIX[i][2])
            wire(ax, prev, q, toward=(q[0], q[1] + 3) if FIX[i][0] in ("A",) else None, k=0.14, **leg)
            prev = q
        switch(ax, p, s)
    for i, (t, x, y, key) in enumerate(FIX):
        draw_fixture(ax, t, (x, y))
        dx0, dy0, dx1, dy1 = FIX_TAG.get(i, (-0.85, 0, 0.9, 0))
        tag(ax, x + dx0, y + dy0, t, LIT, size=4.4)
        tag(ax, x + dx1, y + dy1, NUM[key], PWR, size=4.2)
    for p in ((40.9, 12.5), (40.9, 22.3)):
        auto_light(ax, p)
        tag(ax, p[0] - 1.05, p[1], "G3", LIT, size=4.4)
        tag(ax, p[0] + 2.2, p[1], "CL-1", LIT)
    keynote(ax, 40.9, 13.9, 1)
    keynote(ax, 21.45, 22.2, 2)
    keynote(ax, 34.2, 9.6, 3)
    keynote(ax, 28.2, 33.6, 4)
    keynote(ax, 38.9, 25.0, 5)
    txt(ax, 21.3, 5.55, "UNDER-CABINET LIGHT (U) has its own switch. The hood light is part of the microwave/hood. "
        "W/D and mechanical closet lights (E): pull chain.", size=4.4)
    y = legend(ax, -12.6, 39.0, [
        (light, "Ceiling light (types A, D, C, E), wall light (X)"),
        (pendant, "Pendant over the island (P)"),
        (fanlight, "Bath exhaust fan with light (F)"),
        (lambda a, p: bar(a, p, 1.6), "Vanity light (V), under-cabinet strip (U)"),
        (auto_light, "AUTOMATIC common light: sensor, no switch"),
        (_l_txt("S", LIT), "Wall switch, 48 in., latch side of the door"),
        (_l_txt("S3", LIT), "3-way switch"),
        (_l_wire(LIT, (0, (2.2, 1.6)), 0.6), "Switch leg: switch to its fixtures"),
        (_l_txt("A", LIT), "Fixture type, see the schedule"),
        (_l_txt("22", PWR), "Circuit number in the flat's panel (E-201)"),
        (lambda a, p: keynote(a, p[0], p[1], 1, r=0.5), "Keynote: see the list at right"),
    ], dy=1.3)
    block(ax, -13.2, y - 0.6, "UNIT A / UNIT B DIFFERENCES", [
        "Porch light X: Unit A's is on the wall under Unit B's",
        "porch; Unit B's is under the roof overhang.",
        "Unit A ceiling boxes sit in the rated two-layer ceiling:",
        "listed fire-rated boxes only. Unit B ceiling boxes are",
        "under R-49: airtight, insulation-contact rated.",
        "Stair lights G3: common, on PA at every landing.",
        "Everything else is identical, circuit for circuit.",
    ], fs=4.4, lh=0.74)
    cnt = {t: sum(1 for f in FIX if f[0] == t) for t in "ADPUFVCEX"}
    rows = [
        ["Type", "Fixture (all LED, 2700-3000 K)", "Where", "Size", "Mounting", "Control", "Qty", "Circuit"],
        ["A", "Flush ceiling light, 14 in., enclosed", "Bedrooms 1, 2, 3 and living room", "20 W, 1,600 lm", "Ceiling", "Wall switch at the door", f"{cnt['A']} / flat", f"{NUM['lt1']}, {NUM['lt2']}"],
        ["D", "Surface disc light, 6 in.", "Kitchen (2), unit entry, hall", "12 W, 900 lm", "Ceiling; hall: under the 7'-0\" soffit", "Wall switch; hall on two 3-ways", f"{cnt['D']} / flat", f"{NUM['lt2']}, {NUM['hall']}"],
        ["P", "Pendant", "Over the island", "9 W each", "Ceiling, bottom 30-36 in. over the top", "Wall switch", f"{cnt['P']} / flat", NUM["lt2"]],
        ["U", "Under-cabinet strip, 18 in.", "Under the wall cabinet at the counter", "8 W", "Under the cabinet", "Switch on the fixture", f"{cnt['U']} / flat", NUM["lt2"]],
        ["F", "Bath exhaust fan with light, 80 cfm", "Baths 1, 2, 3 (duct: M-102, M-103)", "15 W light", "Ceiling or soffit, listed for a rated ceiling", "Wall switch; fan on a timer", f"{cnt['F']} / flat", NUM["bath"]],
        ["V", "Vanity light bar, 24 in., damp-rated", "Over the mirror in each bath", "20 W", "Wall, 78 in. to centre", "Wall switch", f"{cnt['V']} / flat", NUM["bath"]],
        ["C", "Closet light, enclosed, low profile", "Bedroom closets 1, 2, 3", "10 W", "Ceiling, clearances per NEC 410.16", "Wall switch beside the closet door", f"{cnt['C']} / flat", f"{NUM['lt1']}, {NUM['lt2']}"],
        ["E", "Utility light with pull chain", "Washer/dryer and mechanical closets", "10 W", "Ceiling", "Pull chain", f"{cnt['E']} / flat", NUM["hall"]],
        ["X", "Porch wall light, wet-rated, full cut-off", "Beside each flat's porch door", "12 W", "Wall, 6'-8\" to centre", "Switch inside at the porch door", f"{cnt['X']} / flat", NUM["lt2"]],
        ["G1", "AUTOMATIC strip, 4 ft, wet-rated", "Garage ceiling (E-101)", f"{W_G1} W, 4,000 lm", "Surface, on the 5/8 in. Type X ceiling", "Built-in occupancy sensor + photocell", f"{len(G_STRIPS)} total", "CL-1 (PA)"],
        ["G2", "AUTOMATIC downlight, full cut-off", "Porch soffit: street door, landing / trash bay", f"{W_G2} W", "Soffit over the landing", "Built-in occupancy sensor + photocell", f"{len(EXT_AL)} total", "CL-1 (PA)"],
        ["G3", "AUTOMATIC stair light, battery pack", "Every stair landing, garage to Unit B", f"{W_G3} W", "Wall or ceiling", "Built-in occupancy sensor, no switch", f"{N_STAIR_AL} total", "CL-1 (PA)"],
        ["G4", "AUTOMATIC utility light", "Utility room (E-101)", f"{W_G4} W", "Ceiling", "Built-in occupancy sensor", "1 total", "CL-1 (PA)"],
    ]
    bg.text(0.62, 2.82, "LIGHTING SCHEDULE (preliminary: equal fixtures accepted)", fontsize=6.4, fontweight="bold", color=INK, va="bottom")
    table(bg, 0.62, 2.78, [0.42, 2.45, 2.75, 1.05, 2.35, 2.4, 0.62, 0.78], rows, fs=5.3, rh=0.153)
    audit(fig, "E-104")
    save(fig, "E-104", pdf)


# ----------------------------------------------------------------------------
# E-105  Alarms, data and doorbell
# ----------------------------------------------------------------------------
def sheet_e105(pdf):
    d_range = math.dist((ALARMS[3][1], ALARMS[3][2]), RANGE_C)
    notes = fit_notes([
        ("Smoke and CO alarms", [
            wrap("IRC R314: one smoke alarm in each bedroom, one in the hall outside bedroom 2 and one in the living room outside "
                 "bedrooms 1 and 3. 120 V hard-wired with battery backup, interconnected so all sound together, photoelectric."),
            wrap(f"Keep 3 ft from bath doors and supply registers and 10 ft from the range (living room alarm is {ftin(d_range)} away)."),
            wrap("CO alarm: NOT required by IRC R315 (no fuel-burning appliance, the garage is open and not attached as an enclosed "
                 "garage). One combination smoke + CO unit is placed in the hall anyway as good practice."),
            wrap("Each flat's alarms are on its own circuit 28 with the hall light, so a tripped breaker is noticed. The flats are not "
                 "interconnected with each other. None in the open garage or common stair."),
        ]),
        ("Data, doorbell, thermostat", [
            wrap("Media box recessed in the W/D closet side wall of each flat: 1 Cat6 + 1 RG6 coax to the TV wall, 1 Cat6 to each "
                 "bedroom desk, all home runs."),
            wrap("Doorbell: one lit button per flat at the street door, chime in the hall. Plain push buttons. NO cameras, "
                 "no video doorbell, no intercom."),
            wrap("Thermostat in the hall, 60 in. up: 18/8 cable to the air handler (M-102)."),
        ]),
    ], "E-105")
    fig, bg = new_sheet("E-105", "Alarms, data and doorbell", SCALE, notes)
    bot = 2.75
    ax = frame(fig, ((3.0, 47.5), (5.0, 44.5)), "Units A and B: alarms, data, doorbell chime, thermostat",
               "Typical for both flats · cables run in the flat's own ceiling and walls · preliminary", left=0.55, bottom=bot, bar=True, lot=False)
    unit_plan(ax, "bg", "A")
    # alarms and interconnect
    pos = {i: (x, y) for i, (s, x, y) in enumerate(ALARMS)}
    ic = dict(color=ALM, lw=0.5, ls=(0, (3, 1.5)))
    wire(ax, pos[1], pos[4], k=0.08, **ic)
    wire(ax, pos[4], pos[3], k=-0.12, toward=(30, 30), **ic)
    wire(ax, pos[3], pos[2], k=0.1, **ic)
    wire(ax, pos[3], pos[0], k=0.1, toward=(22, 14), **ic)
    for s, x, y in ALARMS:
        alarm(ax, (x, y), s)
    tag(ax, 24.9, 20.2, f"{ftin(d_range)} TO THE RANGE\n(10 ft min.)", ALM, size=4.2, weight="normal")
    leader(ax, [(ALARMS[3][1] - 0.6, ALARMS[3][2] - 0.3), (RANGE_C[0] + 0.6, RANGE_C[1] + 0.4)], color=ALM, lw=0.3)
    # media box and cables
    for name, x, y, side, cab in DATA:
        p = off((x, y), side, 0.45)
        wire(ax, MEDIA, p, k=0.07, color=DAT, lw=0.6, toward=(26, 24))
        lowv(ax, p, "D")
        t = off((x, y), side, 1.35)
        tag(ax, t[0], t[1], cab, DAT)
    lowv(ax, MEDIA, "MB")
    # service from the utility room, thermostat, chime
    svc = (41.0, m.B3_Y1 + 0.75)
    wire(ax, svc, (MEDIA[0] + 0.46, MEDIA[1]), k=0.03, color=DAT, lw=0.9, ls=(0, (4, 1.5)))
    ax.add_patch(plt.Circle(svc, 0.26, fc=DAT, ec=DAT, zorder=11))
    tag(ax, 44.0, 32.6, "SERVICE CABLES UP FROM THE\nTELECOM BOARD (utility room),\nIN THE PIPE SPACE", DAT, size=4.2, weight="normal")
    leader(ax, [(43.2, 31.7), (svc[0] + 0.3, svc[1] + 0.15)], color=DAT, dot=False)
    pt = off(TSTAT, "e", 0.46)
    pc = off(CHIME, "s", 0.46)
    wire(ax, pt, (m.AHU[0], (m.AHU[1] + m.AHU[3]) / 2), k=0.2, color=DAT, lw=0.6)
    lowv(ax, pt, "T")
    lowv(ax, pc, "CH")
    wire(ax, (pc[0], pc[1] - 0.38), (MEDIA[0] - 0.46, MEDIA[1]), k=0.12, color=DAT, lw=0.5, ls=(0, (1.2, 1.4)), toward=(21.5, 24.0))
    bw = (XST - 0.3, 15.6)
    lowv(ax, bw, "DB")
    arrow(ax, (bw[0] + 0.5, bw[1]), (bw[0] + 1.9, bw[1]), color=DAT)
    tag(ax, 33.9, 17.6, "BELL WIRE 18/2 DOWN THE\nSTAIR WALL TO THIS FLAT'S\nBUTTON AT THE STREET DOOR", DAT, size=4.2, weight="normal")

    # garage-level strip
    gl = 0.55 + (47.5 - 3.0) / FPI + 0.25
    gv = ((33.5, 56.5), (-5.5, 35.5))
    gx = frame(fig, gv, "Garage level: entry and telecom", "East end of the garage level", left=gl, bottom=bot,
               bar=False, lot_label=(50.0, 31.6))
    site_work(gx, bg=True)
    lower_plan(gx, "bg")
    for t in list(gx.texts):                    # background labels that fall outside this strip
        tx_, ty_ = t.get_position()
        if not (gv[0][0] + 1 < tx_ < gv[0][1] and gv[1][0] < ty_ < gv[1][1] - 3):
            t.remove()
    view_title(gx, gv[0][0] + 0.6, gv[1][1] - 1.6, "1", "Garage level: entry and telecom", "East end of the garage level", 9)
    txt(gx, 40.0, -0.75, "R.O.W. LINE", size=4.4, color=ACCENT)
    txt(gx, 52.6, -4.6, "to Baird Street", size=4.4, color=DAT)
    for i, x in enumerate((43.05, 43.65)):
        gx.add_patch(plt.Circle((x, YF - 0.4), 0.22, fc=DAT, ec=DAT, zorder=11))
    tag(gx, 48.6, 8.6, "DOORBELL BUTTONS\nA and B, lit, 48 in. up,\nlatch side of the door.\nNo camera.", DAT, size=4.2, weight="normal")
    leader(gx, [(46.4, 9.3), (43.95, YF - 0.45)], color=DAT, dot=False)
    arrow(gx, (43.35, YF + 0.75), (43.35, YF + 2.6), color=DAT)
    tag(gx, 41.0, 14.9, "BELL WIRES UP\nIN THE STAIR WALL", DAT, size=4.2, weight="normal")
    # telecom conduit: street -> joint trench -> pull box at the meter -> truss space -> utility room board
    xt = 49.55
    tc = dict(color=DAT, lw=1.2, ls=(0, (5, 1.6)))
    line(gx, [(xt, -3.6), (xt, METER[1] - 1.9), (m.XE + 0.35, METER[1] - 1.9)], z=10, **tc)
    arrow(gx, (xt, -3.4), (xt, -5.0), color=DAT, lw=1.0, scale=7)
    rect(gx, m.XE, METER[1] - 2.3, m.XE + 0.7, METER[1] - 1.5, fc=PAPER, ec=DAT, lw=1.0, z=11)
    rect(gx, m.XE, METER[1] - 1.15, m.XE + 0.6, METER[1] + 1.15, fc=PWR, ec=PWR, z=10, alpha=0.45)
    board = (38.4, m.UTIL[2] + 0.2)
    line(gx, [(m.XE, METER[1] - 1.9), (m.XE - 0.55, METER[1] - 1.9), (m.XE - 0.55, m.SHAFT_U[3] + 0.35), (board[0], m.SHAFT_U[3] + 0.35)],
         color=DAT, lw=0.9, ls=(0, (2, 1.4)), z=10)
    rect(gx, board[0] - 1.0, board[1] - 0.2, board[0] + 1.0, board[1] + 0.2, fc=DAT, ec=DAT, z=11)
    riser = (41.15, m.UTIL[3] - 0.4)
    wire(gx, (board[0] + 1.0, board[1]), riser, k=0.2, color=DAT, lw=0.9, ls=(0, (4, 1.5)), toward=(39.5, 27.5))
    gx.add_patch(plt.Circle(riser, 0.26, fc=DAT, ec=DAT, zorder=11))
    for (y, target, s) in [
        (27.8, (riser[0] + 0.3, riser[1]), "RISERS UP: 2 Cat6 + 2 RG6\n(or 1 in. conduit) per flat,\nin the pipe space behind\nbath 3, to each media box"),
        (22.4, (board[0] + 0.6, board[1] + 0.1), "TELECOM BOARD, 2 x 2 ft\nplywood, top 6 ft, on the\nutility room south wall"),
        (16.6, (m.XE - 0.55, 17.5), "2 in. CONDUIT in the floor\ntrusses above, with the\nfeeders' route (E-101)"),
        (12.2, (m.XE + 0.7, METER[1] - 1.9), "PULL BOX, 12 x 12 in.,\nweatherproof, beside the\nmeter stack: carrier's\nhand-off, bonded to the\nintersystem bonding bar"),
        (3.6, (xt, 2.6), "2 in. CONDUIT + PULL\nSTRING from the street,\nin the service-lateral\ntrench, 12 in. apart.\nCarrier and its pole or\npedestal: not known,\nfind on site."),
    ]:
        tag(gx, 51.0, y, s, DAT, size=4.2, weight="normal", ha="left", va="top")
        leader(gx, [(50.8, y - 0.5), target], color=DAT, lw=0.3)
    txt(gx, 46.9, METER[1] + 2.2, "METER\nSTACK", size=4.2, color=PWR, weight="bold")

    # legend and schedule in the bottom band
    lx = 0.75
    bg.text(lx - 0.1, 2.48, "LEGEND", fontsize=6.4, fontweight="bold", color=INK, va="center")
    lax = plan_axes(fig, 0.55, 0.5, (0, 24.5), (0, 9.8), FPI)
    items = [(lambda a, p: alarm(a, p, "SD"), "Smoke alarm, hard-wired, battery backup"),
             (lambda a, p: alarm(a, p, "SC"), "Combination smoke + CO alarm"),
             (_l_wire(ALM, (0, (3, 1.5)), 0.6), "Alarm interconnect (14/3, same circuit)"),
             (lambda a, p: lowv(a, p, "MB"), "Media box, 14 in. plastic, W/D closet wall"),
             (lambda a, p: lowv(a, p, "D"), "Data outlet: Cat6 (C6), coax (RG6)"),
             (lambda a, p: lowv(a, p, "T"), "Thermostat"),
             (lambda a, p: lowv(a, p, "CH"), "Doorbell chime"),
             (lambda a, p: lowv(a, p, "DB"), "Bell wire drop to the street-door button"),
             (_l_wire(DAT, (0, (5, 1.6)), 1.2), "Telecom conduit or service cable"),
             ]
    for i, (fn, s) in enumerate(items):
        col, row = divmod(i, 5)
        x, y = 1.3 + col * 12.6, 7.4 - row * 1.5
        fn(lax, (x, y))
        txt(lax, x + 1.5, y, s, size=4.6, ha="left")
    tx = 5.55
    bg.text(tx, 2.48, "LOW-VOLTAGE AND ALARM SCHEDULE (each flat)", fontsize=6.4, fontweight="bold", color=INK, va="center")
    table(bg, tx, 2.36, [1.45, 0.4, 2.35, 3.85], [
        ["Item", "Qty", "Where", "Wiring and notes"],
        ["Smoke alarm (SD)", "4", "Each bedroom; living room", f"120 V + battery, photoelectric, interconnected, circuit {NUM['hall']}"],
        ["Smoke + CO alarm (SC)", "1", "Hall outside bedroom 2", "As above. CO not required here: placed as good practice"],
        ["Doorbell button", "1", "Street door, garage level", "Lit push button marked A or B, 18/2 bell wire. No camera"],
        ["Chime + transformer", "1", "Hall end wall; transformer at the media box", "16 V, 10 VA transformer on the media-box receptacle"],
        ["Media box (MB)", "1", "W/D closet side wall, top at 66 in.", f"Duplex receptacle inside, circuit {NUM['hall']}; carrier's modem goes here"],
        ["Cat6 data outlet", "4", "TV wall and each bedroom desk", "Home run to the media box, RJ45 jack, 16 in. up"],
        ["RG6 coax outlet", "1", "TV wall", "Home run to the media box"],
        ["Thermostat", "1", "Hall west wall, 60 in. up", "18/8 to the air handler; outdoor-unit control cable by HVAC"],
    ], fs=5.2, rh=0.172)
    audit(fig, "E-105")
    save(fig, "E-105", pdf)


# ----------------------------------------------------------------------------
# E-201  One-line diagram, panel schedules and loads
# ----------------------------------------------------------------------------
def panel_rows(unit):
    by_space = {}
    for key, sp, name, a, poles, wire_, prot in circuits(unit):
        for s in sp:
            by_space[s] = (name, f"{a}/{poles}" if a else "space", wire_, prot)
    rows = [["No.", "Load", "A / P", "Wire", "Prot.", "No.", "Load", "A / P", "Wire", "Prot."]]
    for i in range(20):
        r = []
        for s in (2 * i + 1, 2 * i + 2):
            name, ap, wire_, prot = by_space.get(s, ("Spare space", "-", "-", ""))
            r += [str(s), name, ap, wire_, prot]
        rows.append(r)
    return rows


def sheet_e201(pdf):
    notes = fit_notes([
        ("Service", [
            wrap(f"120/240 V, single-phase, 3-wire from {UTILITY}. TWO meters only, one per flat, no house meter. "
                 "The two main breakers at the meter stack are the service disconnects."),
            wrap(f"Calculated demand: Unit A {LC['ampsA']:.0f} A, Unit B {LC['ampsB']:.0f} A, about {LC['ampsA'] + LC['ampsB']:.0f} A "
                 "together. Meter-stack bus, lateral and available fault current: per the utility."),
        ]),
        ("Feeders and grounding", [
            wrap("Feeders are 4-wire (2 hots, neutral, ground): type SER cable or conductors in 2 in. conduit. In PA and PB the "
                 "neutral bar is isolated; grounds go to a separate bar."),
            wrap("Concrete-encased electrode in the east footing: tell the concrete crew before the pour. Bond metal water piping "
                 "and the steel beam and post (S-104)."),
            wrap("Each water heater is in its own flat's mechanical closet, on its own flat's panel."),
        ]),
        ("To confirm", [
            wrap("Sizes here are preliminary and unsealed. The electrician or engineer of record confirms conductor sizes, "
                 "voltage drop, breaker ratings and equipment nameplates."),
            wrap("NEC 210.8(F) (GFCI on outdoor heat pumps, marked G*): check the current WV rule."),
            wrap("Range: keep its receptacle 6 ft or more from the island sink, or use a GFCI breaker."),
        ]),
    ], "E-201")
    fig, bg = new_sheet("E-201", "One-line diagram, panel schedules and loads", "No scale", notes)
    T = dict(fontsize=5.4, color=INK, va="center", linespacing=1.2)

    # ---------------- one-line diagram ----------------
    bg.text(0.62, 10.33, "ONE-LINE DIAGRAM", fontsize=9, fontweight="bold", color=INK, va="center")
    bg.text(2.35, 10.32, "preliminary · conductor sizes per NEC 310.12 (dwelling feeders) and 250.122", fontsize=5.6, color=GREY, va="center")

    def box(x0, y0, x1, y1, head, lines, ec=PWR):
        rect(bg, x0, y0, x1, y1, fc=PAPER, ec=ec, lw=1.1, z=5)
        bg.text((x0 + x1) / 2, y1 - 0.13, head, fontsize=6.0, fontweight="bold", color=INK, ha="center", va="center", zorder=6)
        bg.text((x0 + x1) / 2, y1 - 0.25, "\n".join(lines), fontsize=5.0, color=INK, ha="center", va="top", zorder=6, linespacing=1.25)

    yA, yB = 9.45, 8.25
    box(0.62, 8.35, 1.95, 9.35, "UTILITY", [UTILITY, "120/240 V, 1-phase,", "3-wire", "pole / transformer", "location: find on site"], ec=INK)
    line(bg, [(1.95, 8.85), (3.35, 8.85)], color=PWR, lw=1.8, ls=(0, (6, 2)))
    bg.text(2.65, 9.0, "SERVICE LATERAL", fontsize=5.4, fontweight="bold", color=PWR, ha="center", va="center")
    bg.text(2.65, 8.72, "underground in conduit;\nconduit, depth and who\npulls the wire: per utility", fontsize=4.8, color=INK, ha="center", va="top", linespacing=1.25)
    rect(bg, 3.35, 7.72, 5.25, 9.98, fc="#faf7fc", ec=PWR, lw=1.2, z=4)
    bg.text(4.3, 10.07, "METER STACK · east wall, outdoors, NEMA 3R", fontsize=5.4, fontweight="bold", color=PWR, ha="center", va="center")
    line(bg, [(3.35, 8.85), (3.6, 8.85)], color=PWR, lw=1.8)
    line(bg, [(3.6, yB), (3.6, yA)], color=PWR, lw=2.4)
    for y, u, amps, row in ((yA, "A", m.PANEL_A_AMPS, 0), (yB, "B", m.PANEL_B_AMPS, 1)):
        line(bg, [(3.6, y), (7.05, y)], color=PWR, lw=1.5, z=5)
        bg.add_patch(plt.Circle((4.05, y), 0.17, fc=PAPER, ec=PWR, lw=1.1, zorder=6))
        bg.text(4.05, y, "M", fontsize=6, fontweight="bold", color=PWR, ha="center", va="center", zorder=7)
        bg.text(4.05, y + 0.28, f"METER {u}", fontsize=5.0, color=INK, ha="center", va="center")
        rect(bg, 4.62, y - 0.1, 4.98, y + 0.1, fc=PAPER, ec=PWR, lw=1.1, z=6)
        line(bg, [(4.66, y - 0.04), (4.94, y + 0.06)], color=PWR, lw=1.0, z=7)
        bg.text(4.8, y + 0.28, f"MAIN {u}: {amps} A, 2-pole", fontsize=5.0, fontweight="bold", color=INK, ha="center", va="center")
        bg.text(4.8, y - 0.24, "service disconnect", fontsize=4.6, color=GREY, ha="center", va="center")
        cu, al = FEEDER[amps]
        ln = FEED_A if u == "A" else FEED_B
        bg.text(6.15, y + 0.14, f"FEEDER {u} · 4-wire · about {ln:.0f} ft", fontsize=5.2, fontweight="bold", color=PWR, ha="center", va="center")
        bg.text(6.15, y - 0.1, f"{cu}\nor {al}", fontsize=4.9, color=INK, ha="center", va="top", linespacing=1.25)
        extra = ["WH-A, HP-A, Unit A circuits", "CL-1, CL-2R, CL-2H common loads"] if u == "A" else ["WH-B, HP-B, Unit B circuits", "no common loads"]
        box(7.05, y - 0.5, 8.85, y + 0.45, f"PANEL P{u} · UNIT {u} HALL", [f"{amps} A bus, 40 spaces, main lugs", "neutral bar isolated"] + extra)
    # grounding
    gy = 7.25
    line(bg, [(3.9, 7.72), (3.9, gy), (2.2, gy)], color=GRN, lw=1.2)
    line(bg, [(3.9, gy), (5.6, gy)], color=GRN, lw=1.2)
    for k, wdt in enumerate((0.3, 0.2, 0.1)):
        line(bg, [(2.2 - 0.06 * k - 0.02, gy - wdt / 2), (2.2 - 0.06 * k - 0.02, gy + wdt / 2)], color=GRN, lw=1.2)
    bg.add_patch(plt.Circle((3.9, gy), 0.04, fc=GRN, ec=GRN, zorder=6))
    bg.add_patch(plt.Circle((5.6, gy), 0.04, fc=GRN, ec=GRN, zorder=6))
    bg.text(3.98, 7.55, "main bonding jumper in the stack · #4 Cu electrode conductor", fontsize=4.8, color=GRN, va="center")
    bg.text(0.62, gy + 0.02, "CONCRETE-ENCASED ELECTRODE\n20 ft of bare #4 Cu (or 1/2 in. bar)\nin the east-wall footing", fontsize=4.8, color=GRN, va="center", linespacing=1.25)
    bg.text(5.7, gy + 0.02, "#4 Cu BOND to metal water piping (utility room) and building steel\n"
            "Intersystem bonding bar at the meter stack for telecom (E-105)\nSurge protector in PA and PB (NEC 230.67)",
            fontsize=4.8, color=GRN, va="center", linespacing=1.25)

    # ---------------- load calculation ----------------
    lx, ly = 9.15, 10.33
    bg.text(lx, ly, "LOAD CALCULATION, NEC 220.82 (optional method)", fontsize=7.2, fontweight="bold", color=INK, va="center")

    def va(v):
        return f"{v:,.0f}"

    rows = [["Load, VA", "Unit A", "Unit B"]]
    rows += [[n, va(v), va(v)] for n, v in LC["gen"]]
    rows += [["General load, total", va(LC["tot"]), va(LC["tot"])],
             ["First 10,000 VA at 100 %", "10,000", "10,000"],
             [f"Remainder {va(LC['tot'] - 10000)} VA at 40 %", va(LC["rem"]), va(LC["rem"])]]
    rows += [[n, va(v), va(v)] for n, v in LC["heat"]]
    rows += [["Flat's own demand", va(LC["own"]), va(LC["own"])]]
    rows += [[n + ", 100 %", va(v), "-"] for n, v in LC["common"]]
    rows += [["TOTAL DEMAND, VA", va(LC["A"]), va(LC["B"])],
             ["AMPS at 240 V", f"{LC['ampsA']:.0f} A", f"{LC['ampsB']:.0f} A"],
             ["Main breaker and panel", f"{m.PANEL_A_AMPS} A", f"{m.PANEL_B_AMPS} A"],
             ["Spare capacity", f"{m.PANEL_A_AMPS - LC['ampsA']:.0f} A", f"{m.PANEL_B_AMPS - LC['ampsB']:.0f} A"]]
    yb = table(bg, lx, ly - 0.14, [2.75, 0.85, 0.85], rows, fs=5.4, rh=0.148)
    ev = 32 * 240
    bg.text(0.62, 6.93, "\n".join([
        "LOAD NOTES. Floor area is the net area from the model. Each water heater is in its own flat, on its own flat's panel. If the range nameplate is 12 kW, add 1,600 VA (7 A) to each flat.",
        f"A future 32 A car charger (7,680 VA at 100 %) brings Unit A to {(LC['A'] + ev) / 240:.0f} A of {m.PANEL_A_AMPS} A and Unit B to {(LC['B'] + ev) / 240:.0f} A of {m.PANEL_B_AMPS} A: Unit B's charger must be 24 A or load-managed (NEC 625.42). Recalculate then.",
    ]), fontsize=5.0, color=INK, va="top", linespacing=1.3)

    # ---------------- panel schedules ----------------
    wd = [0.27, 1.73, 0.42, 0.33, 0.36]
    pw = 2 * sum(wd)
    for i, unit in enumerate("AB"):
        x = 0.62 + i * (pw + 0.33)
        amps = m.PANEL_A_AMPS if unit == "A" else m.PANEL_B_AMPS
        bg.text(x, 6.30, f"PANEL P{unit} · UNIT {unit}", fontsize=7.6, fontweight="bold", color=INK, va="center")
        bg.text(x + 1.75, 6.29, f"{amps} A, 120/240 V, 40 spaces, main lugs, recessed in the hall west wall · fed from MAIN {unit}",
                fontsize=5.2, color=GREY, va="center")
        yb = table(bg, x, 6.16, wd + wd, panel_rows(unit), fs=5.1, rh=0.176)
        bg.plot([x + sum(wd), x + sum(wd)], [6.16, yb], color=INK, lw=0.6)
    bg.text(0.62, yb - 0.1, "\n".join([
        "A / P = breaker amps / poles. Wire = copper NM-B branch wiring, minimum size shown: #14 for 15 A, #12 for 20 A, #10 for 30 A, #8 for 40 A. "
        "Prot.: A = AFCI, G = GFCI, AG = dual-function breaker, G* = confirm (see To confirm).",
        "Circuit numbers are the numbers beside the devices on E-102, E-103 and E-104. CL-1, CL-2R and CL-2H (E-101) exist in PA only: the same spaces are spare in PB. "
        "Spaces 37-39 are kept empty at the end of the future car-charger conduit.",
    ]), fontsize=5.0, color=INK, va="top", linespacing=1.3)
    audit(fig, "E-201")
    save(fig, "E-201", pdf)


SHEETS = [("E-101", sheet_e101), ("E-102", sheet_e102), ("E-103", sheet_e103), ("E-104", sheet_e104),
          ("E-105", sheet_e105), ("E-201", sheet_e201)]
