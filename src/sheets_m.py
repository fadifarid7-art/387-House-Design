"""Mechanical sheets M-101 to M-201 (Rev E): central air with ductwork, one ducted split heat pump per flat.

Every duct, register, fan and pad on these sheets is placed from model.py. Room air quantities are the
room's share of the supplied floor area, so the plans and the air-balance table read the same numbers.
"""
import math
import textwrap

from shapely.geometry import LineString

from common import *  # noqa: F401,F403
import model as m
from plans import *  # noqa: F401,F403
from index import TITLE

IN = m.IN
SUP, RET, EXH, REF, CND, HEAT = "#1f5fa8", "#2e7d32", "#6a1b9a", "#d35400", "#0e8f9c", "#c0392b"
SUP_F, RET_F, EXH_F = "#d3e4f6", "#d5ecd7", "#e8daf2"
ZONE_F, ZONE_E = "#f4e3b1", "#9a761a"
TIMBER = "#f3efe6"

# ----------------------------------------------------------------------------
# 1. The system, in numbers (identical in both flats)
# ----------------------------------------------------------------------------
TOTAL_CFM = 800                      # 2 tons x 400 cfm per ton
BTUH = 24000
STRIP_KW = 5
BR1, BR2, BR3, LIV = "BEDROOM 1", "BEDROOM 2", "BEDROOM 3", "LIVING / KITCHEN"
BA1, BA2, BA3 = "BATH 1", "BATH 2", "BATH 3"
SUPPLIED = [BR1, BR2, BR3, LIV, BA1, BA2, BA3]
AREA = {k: m.area(k) for k in SUPPLIED}
A_SUP = sum(AREA.values())
CFM = {k: 5 * round(TOTAL_CFM * AREA[k] / A_SUP / 5) for k in SUPPLIED}
CFM[LIV] += TOTAL_CFM - sum(CFM.values())          # rounding remainder goes to the largest room
LIV_A = 5 * math.ceil(CFM[LIV] / 10)               # living room register over the hall opening
LIV_B = CFM[LIV] - LIV_A                           # living room register over the W/D closet
ROUND_CAP = {5: 60, 6: 100, 7: 140, 8: 180}        # round branch rule, cfm at about 0.08 in. w.g. per 100 ft
RECT_FPM = 750                                     # rectangular duct rule


def rd(cfm):
    """Smallest round branch (in.) that carries cfm under the stated rule."""
    return min(d for d, c in ROUND_CAP.items() if c >= cfm)


def fpm(cfm, w, h):
    return cfm / (w * h / 144.0)


Q_N = CFM[BR2] + CFM[BA2]                          # north trunk leg
Q_S = TOTAL_CFM - Q_N                              # south trunk leg
Q_SOF = CFM[BR3] + CFM[BA3]                        # duct in the bedroom 3 soffit
Q_E = LIV_B + Q_SOF                                # branch over the W/D closet
RECTS = {"con": (20, 8, TOTAL_CFM), "south": (16, 8, Q_S), "north": (10, 8, Q_N), "east": (12, 8, Q_E), "sof": (12, 6, Q_SOF)}
for _k, (_w, _h, _q) in RECTS.items():
    assert fpm(_q, _w, _h) <= RECT_FPM, _k
assert sum(CFM.values()) == TOTAL_CFM

# id, room, cfm, register, type, branch
OUTLETS = [
    ("S-1", BR1, CFM[BR1], "12 x 6", "high sidewall", f'{rd(CFM[BR1])}" round'),
    ("S-2", BR2, CFM[BR2], "12 x 6", "high sidewall", f'{rd(CFM[BR2])}" round'),
    ("S-3", BR3, CFM[BR3], "12 x 6", "soffit face", "12 x 6"),
    ("S-4", LIV, LIV_A, "14 x 6", "high sidewall", "trunk end"),
    ("S-5", LIV, LIV_B, "14 x 6", "high sidewall", "12 x 8"),
    ("S-6", BA1, CFM[BA1], "8 x 4", "ceiling", f'{rd(CFM[BA1])}" round'),
    ("S-7", BA2, CFM[BA2], "8 x 4", "ceiling", f'{rd(CFM[BA2])}" round'),
    ("S-8", BA3, CFM[BA3], "8 x 4", "high sidewall", f'{rd(CFM[BA3])}" round'),
]
OUT = {o[0]: o for o in OUTLETS}
BEDROOMS = 3
VENT_FORMULA = 0.01 * m.net_area() + 7.5 * (BEDROOMS + 1)     # IRC M1505.4.3 equation
VENT_CFM = 45                                                  # IRC Table M1505.4.3(1): under 1,500 sf, 2-3 bedrooms
FAN_CFM = 80
CLG = {"A": m.CLG_A, "B": m.CLG_B}
EL = {"A": m.EL_A, "B": m.EL_B}
TRUSS = {"A": m.TRUSS_A, "B": m.TRUSS_B}
CAP_H = m.CLG_SOFFIT + 4 * IN                      # centre of every wall cap above the flat's floor
STAND_H, AHU_H = 2.0, 4.0                          # return stand and air-handler cabinet (catalogue: about 48 in.)
DRY_RISER = 3.5                                    # dryer outlet (stacked) to the dropped ceiling, ft
HP_H = 28 * IN                                     # outdoor unit height (catalogue: about 28 in.)
PAD_T = 4 * IN                                     # pad top above existing grade at the pad
PAD_GROW = 3 * IN

# ----------------------------------------------------------------------------
# 2. Geometry of the runs (all from the model)
# ----------------------------------------------------------------------------
D = {d["tag"]: d for d in m.DOORS}
_cL, _sL = math.cos(WEST_LEAN), math.sin(WEST_LEAN)
_tR = math.atan(abs(REAR_SLOPE))
_cR = math.cos(_tR)
TR_W, TRN_W, CON_W, SOF_W = 16 * IN, 10 * IN, 20 * IN, 16 * IN
TR_CX = m.X_H1 - 6.5 * IN - TR_W / 2                         # trunk centre line in the hall soffit
AH_CX, AH_CY = (m.AHU[0] + m.AHU[2]) / 2, (m.AHU[1] + m.AHU[3]) / 2
Y_TEE = AH_CY + CON_W / 2
Y_TRN = m.HALL_Y1 - 5 * IN                                   # north end of the trunk
Y_BR1 = m.Y2 + 5.5 * IN                                      # 8 in. branch to bedroom 1, above the tub
S1_X = (D["D5"]["s0"] + D["D5"]["s1"]) / 2
Y_B1 = m.PANEL[3] + 5.5 * IN                                 # bath 1 branch, clear of the panel's wall space
CR1 = (m.B1_X0 + 1.9, Y_B1)
EF1 = (m.TUBS[0][0] - 0.5, m.Y3 - 1.25)
Y_E = m.Y2 + SOF_W / 2                                       # branch over the W/D closet = soffit centre line
X_E1 = m.X_C1 - 0.5
S5_X = (m.X_C0 + m.X_C1) / 2
S3_X = (m.X_B3 + m.X_ST) / 2
SOF_CX = m.X_ST - SOF_W / 2
S8_Y = (D["D7"]["s0"] + D["D7"]["s1"]) / 2
SOF_Y1 = D["D7"]["s1"] + 3 * IN
S2_Y = D["D3"]["s0"] + 0.6
T2_Y = D["D3"]["s1"] - 0.6
T1_Y = (D["D2"]["s0"] + D["D2"]["s1"]) / 2
T3_X = m.X_ST - SOF_W - 0.6
CR2 = (TR_CX, m.B2_Y0 + 2.1)
EF2 = (m.TUBS[1][0] - 0.85, m.B2_Y0 + 3.3)
EF3 = ((m.TUBS[2][0] + m.TUBS[2][2]) / 2, (m.TUBS[2][1] + m.TUBS[2][3]) / 2)
DV_X, DV_Y0 = m.X_C1 - 3.5 * IN, m.WD_Y1 - 3.5 * IN
RH_X, RH_Y0 = m.X_H0 + 4.5 * IN, (m.RANGE[1] + m.RANGE[3]) / 2
KSOF = (m.X_H0, m.YFI, m.X_H0 + 13 * IN, m.RANGE[3])         # soffit above the kitchen wall cabinets
LS_DROP = (m.X_C0 + 3.5 * IN, m.AH_Y0 + 2.5 * IN)
TSTAT = (m.X_H0, m.Y3 - 1.2)
SOF_L = [(m.X_B3, m.Y2), (m.X_ST, m.Y2), (m.X_ST, SOF_Y1), (m.X_ST - SOF_W, SOF_Y1), (m.X_ST - SOF_W, m.Y2 + SOF_W),
         (m.X_B3, m.Y2 + SOF_W)]
HP_U = (_sL, _cL)                                            # unit vector north along the west wall
HP_N = (-_cL, _sL)                                           # unit vector out of the west wall (west)
_hw, _hd = m.HP_SIZE
LS_Y = {"A": m.HP[0][1] - (_hw / 2 + 4 * IN) * _cL, "B": (m.HP[0][1] + m.HP[1][1]) / 2}
DS_Y = {"A": LS_Y["A"] - 0.85, "B": m.HP[1][1] + (_hw / 2 + 0.8) * _cL}
HP_BACK = (m.xw_o(m.HP[0][1]) - m.HP[0][0]) * _cL - _hd / 2         # wall to the back of the unit
HP_FRONT = (m.HP[0][0] - west_x(m.HP[0][1])) * _cL - _hd / 2        # front of the unit to the west lot line
HP_GAP = math.dist(m.HP[0], m.HP[1]) - _hw
W4 = [w for w in m.WINDOWS if w[0] == "W4"][0]
HP_WIN = (m.HP[0][1] - W4[3]) / _cL - _hw / 2                        # bedroom 1 window jamb to unit A
PAD_EL = [elev(*p) + PAD_T for p in m.HP]
LS_EL = {u: EL[u] - 0.5 for u in "AB"}                               # line set sleeve through the rim
DV_RUN = m.yr_o(DV_X) - DV_Y0
DV_EQ = DV_RUN + DRY_RISER + 2 * 5.0
EF_RUN = {"EF-1": EF1[0] - m.xw_o(EF1[1]), "EF-2": m.yr_o(EF2[0]) - EF2[1], "EF-3": m.yr_o(EF3[0]) - EF3[1]}
RH_RUN = RH_Y0 - m.YF
W2 = [w for w in m.WINDOWS if w[0] == "W2"][0]
RH_CLEAR = (W2[2] + W2[3]) / 2 - RH_X                                # hood cap to the operable (east) sash of W2
RA_TO_RANGE = math.dist((m.X_H1, AH_CY), ((m.RANGE[0] + m.RANGE[2]) / 2, RH_Y0))


def ls_len(u):
    i = "AB".index(u)
    inside = abs(LS_DROP[1] - LS_Y[u]) + (LS_DROP[0] - m.xw_o(LS_Y[u])) + 4.0
    outside = max(LS_EL[u] - (PAD_EL[i] + 0.75), 0) + 2.5
    return 5 * round((inside + outside) / 5)


def hp_poly(i, grow=0.0):
    hx, hy = m.HP[i]
    pts = [(-_hd / 2 - grow, -_hw / 2 - grow), (_hd / 2 + grow, -_hw / 2 - grow), (_hd / 2 + grow, _hw / 2 + grow), (-_hd / 2 - grow, _hw / 2 + grow)]
    return [(hx + px * _cL + py * _sL, hy - px * _sL + py * _cL) for px, py in pts]


def inch(v):
    h = round(v * 24) / 2
    return f'{int(h)}"' if h == int(h) else f'{int(h)} 1/2"'


def west_gap(y):
    """Distance along the west wall from station y to the nearest window."""
    return min(min(abs(y - w[2]), abs(y - w[3])) for w in m.WINDOWS if w[1] == "W") / _cL


def rear_gap(x):
    return min(min(abs(x - w[2]), abs(x - w[3])) for w in m.WINDOWS if w[1] == "N") / _cR


# tag, wall, plan point on the outside face, outward unit vector, what, clearance text
TERMS = [
    ("RH-1", "front", (RH_X, m.YF), (0, -1), "Range hood, 6 in.", f"{ftin(RH_CLEAR)} to the east (operable) sash of W2"),
    ("EF-1", "west", (m.xw_o(EF1[1]), EF1[1]), HP_N, "Bath 1 fan, 4 in.", f"{ftin(west_gap(EF1[1]))} to the nearest window"),
    ("EF-2", "rear", (EF2[0], m.yr_o(EF2[0])), (math.sin(_tR), _cR), "Bath 2 fan, 4 in.", f"{ftin(rear_gap(EF2[0]))} to the nearest window"),
    ("DV-1", "rear", (DV_X, m.yr_o(DV_X)), (math.sin(_tR), _cR), "Dryer, 4 in.", f"{ftin(rear_gap(DV_X))} to the nearest window"),
    ("EF-3", "rear", (EF3[0], m.yr_o(EF3[0])), (math.sin(_tR), _cR), "Bath 3 fan, 4 in.", f"{ftin(rear_gap(EF3[0]))} to the nearest window"),
]
assert RH_CLEAR >= 3.0 and min(west_gap(EF1[1]), rear_gap(EF2[0]), rear_gap(DV_X), rear_gap(EF3[0])) >= 3.0
assert HP_FRONT >= 2.0 and DV_EQ <= 35.0


# ----------------------------------------------------------------------------
# 3. Drafting helpers
# ----------------------------------------------------------------------------
def tag(ax, x, y, s, color=INK, size=4.4, box=True, weight="bold", **kw):
    return txt(ax, x, y, s, size=size, color=color, weight=weight, box=box, z=14, **kw)


def lead(ax, p, q, s=None, color=INK, size=4.6, ha=None, weight="normal", va="center", flip=False):
    """Leader from the thing at p to a note at q."""
    line(ax, [p, q], color=color, lw=0.35, z=13)
    if s is None:
        return
    right = (q[0] >= p[0]) != flip
    ha = ha or ("left" if right else "right")
    off = 0.03 * getattr(ax, "fpi", FPI) * (1 if ha == "left" else -1 if ha == "right" else 0) * (-1 if flip else 1)
    txt(ax, q[0] + off, q[1], s, size=size, color=color, ha=ha, va=va, weight=weight, z=14, box=True)


def keynote(ax, x, y, n, color=INK, r=0.62):
    pts = [(x + r * math.cos(math.radians(a)), y + r * math.sin(math.radians(a))) for a in range(0, 360, 60)]
    poly(ax, pts, fc=PAPER, ec=color, lw=0.9, z=15)
    txt(ax, x, y, str(n), size=4.4, color=color, weight="bold", z=16)


def duct(ax, pts, w, color=SUP, fc=SUP_F, z=10.0, lw=0.7):
    g = LineString(pts).buffer(w / 2, cap_style=2, join_style=2)
    poly(ax, list(g.exterior.coords), fc=fc, ec=color, lw=lw, z=z)


def throw(ax, x, y, d, color=SUP, L=0.85):
    ax.annotate("", xy=(x + d[0] * L, y + d[1] * L), xytext=(x + d[0] * 0.1, y + d[1] * 0.1),
                arrowprops=dict(arrowstyle="-|>", lw=0.6, color=color, mutation_scale=5, shrinkA=0, shrinkB=0), zorder=12)


def sidewall(ax, x, y, w, d, color=SUP):
    """High sidewall register on a wall face at (x, y), w ft long, blowing in direction d."""
    tx, ty = -d[1], d[0]
    line(ax, [(x - tx * w / 2, y - ty * w / 2), (x + tx * w / 2, y + ty * w / 2)], color=color, lw=2.6, z=12)
    for k in (-0.3, 0.3):
        throw(ax, x + tx * w * k, y + ty * w * k, d, color)


def ceil_reg(ax, x, y, s=0.4, color=SUP):
    rect(ax, x - s, y - s, x + s, y + s, fc=PAPER, ec=color, lw=0.9, z=12)
    line(ax, [(x - s, y - s), (x + s, y + s)], color=color, lw=0.5, z=12.5)
    line(ax, [(x - s, y + s), (x + s, y - s)], color=color, lw=0.5, z=12.5)


def fan(ax, x, y, s=0.42):
    rect(ax, x - s, y - s, x + s, y + s, fc=PAPER, ec=EXH, lw=1.0, z=12)
    line(ax, [(x - s, y - s), (x + s, y + s)], color=EXH, lw=0.7, z=12.5)


def cap(ax, p, n, color=EXH, s=0.55):
    tx, ty = -n[1], n[0]
    poly(ax, [(p[0] - tx * s, p[1] - ty * s), (p[0] + tx * s, p[1] + ty * s), (p[0] + n[0] * s * 1.5, p[1] + n[1] * s * 1.5)], fc=color, ec=color, lw=0.5, z=12)


def transfer(ax, x0, y0, x1, y1):
    """Transfer grille through a wall: the rectangle is the wall thickness by the grille length."""
    rect(ax, x0, y0, x1, y1, fc=RET_F, ec=RET, lw=0.9, z=12)
    if (x1 - x0) < (y1 - y0):
        a, b = (x0 - 0.55, (y0 + y1) / 2), (x1 + 0.55, (y0 + y1) / 2)
    else:
        a, b = ((x0 + x1) / 2, y0 - 0.55), ((x0 + x1) / 2, y1 + 0.55)
    ax.annotate("", xy=b, xytext=a, arrowprops=dict(arrowstyle="<|-|>", lw=0.6, color=RET, mutation_scale=4.5, shrinkA=0, shrinkB=0), zorder=12.5)


def vt(bg, x, y, title, sub, size=8.5):
    bg.text(x, y, title.upper(), fontsize=size, fontweight="bold", color=INK, va="bottom")
    bg.text(x, y - 0.05, sub, fontsize=5.6, color=GREY, va="top")


def sheet(number, scale, notes):
    """new_sheet with the index title; a long title is set smaller so it stays inside the title block."""
    fig, bg = new_sheet(number, TITLE[number], scale, notes)
    for t in bg.texts:
        if t.get_text() == TITLE[number].upper() and len(t.get_text()) > 30:
            t.set_fontsize(9.6 * 30 / len(t.get_text()))
    return fig, bg


def wrap_list(items, width):
    out = []
    for n, s in items:
        lines = textwrap.wrap(s, width)
        out.append((n, lines))
    return out


# ----------------------------------------------------------------------------
# 4. The system drawn in plan (used on M-102, M-103, the key plan and the closet detail)
# ----------------------------------------------------------------------------
def zone_polys():
    R = m.ROOMS
    return [R["HALL"], R["BATH 1"], R["BATH 2"], R["CLOSET 2"], R["W/D"], R["AIR HANDLER"], R["LINEN"], SOF_L,
            [(m.TUBS[2][0], m.TUBS[2][1]), (m.TUBS[2][2], m.TUBS[2][1]), (m.TUBS[2][2], m.TUBS[2][3]), (m.TUBS[2][0], m.TUBS[2][3])],
            [(KSOF[0], KSOF[1]), (KSOF[2], KSOF[1]), (KSOF[2], KSOF[3]), (KSOF[0], KSOF[3])]]


def draw_zones(ax):
    for p in zone_polys():
        poly(ax, p, fc=ZONE_F, ec=ZONE_E, lw=0.45, z=7.6, alpha=0.55, ls=(0, (3, 2)))


def draw_supply(ax):
    xs0, xs1, xn0, xn1 = TR_CX - TR_W / 2, TR_CX + TR_W / 2, TR_CX - TRN_W / 2, TR_CX + TRN_W / 2
    # branches first, the trunk over them
    duct(ax, [(xs0, Y_BR1), (S1_X, Y_BR1), (S1_X, m.Y1 + 0.05)], rd(CFM[BR1]) * IN)                # to S-1
    duct(ax, [(xs0, Y_B1), (CR1[0], Y_B1)], rd(CFM[BA1]) * IN)                                    # to S-6
    duct(ax, [(xs1, Y_E), (X_E1, Y_E)], 12 * IN)                                                  # 12 x 8 over the W/D closet
    poly(ax, [(X_E1, Y_E - 6 * IN), (m.X_C1, Y_E - 6 * IN), (m.X_C1, Y_E + 6 * IN), (X_E1, Y_E + 6 * IN)], fc=SUP_F, ec=SUP, lw=0.7, z=10)
    duct(ax, [(m.X_C1, Y_E), (S3_X + 0.5, Y_E)], 12 * IN)                                         # 12 x 6 in the soffit
    duct(ax, [(S3_X + 0.5, Y_E), (SOF_CX, Y_E), (SOF_CX, S8_Y), (m.SHAFT_X0 - 0.05, S8_Y)], rd(CFM[BA3]) * IN)   # to S-8
    rect(ax, S5_X - 7 * IN, m.Y1 + 0.05, S5_X + 7 * IN, Y_E - 6 * IN, fc=SUP_F, ec=SUP, lw=0.7, z=10)            # boot to S-5
    rect(ax, S3_X - 6 * IN, Y_E + 6 * IN, S3_X + 6 * IN, m.Y2 + SOF_W, fc=SUP_F, ec=SUP, lw=0.7, z=10)           # boot to S-3
    duct(ax, [(xn0, S2_Y), (m.E1 + 0.05, S2_Y)], rd(CFM[BR2]) * IN)                               # to S-2
    duct(ax, [(TR_CX, Y_TRN), CR2], rd(CFM[BA2]) * IN)                                            # to S-7
    rect(ax, TR_CX, AH_CY - CON_W / 2, m.AHU[0], AH_CY + CON_W / 2, fc=SUP_F, ec=SUP, lw=0.7, z=10.2)            # 20 x 8 connection
    poly(ax, [(xs0, m.Y1 + 0.05), (xs1, m.Y1 + 0.05), (xs1, Y_TEE), (xn1, Y_TEE + 0.35), (xn1, Y_TRN), (xn0, Y_TRN), (xn0, Y_TEE + 0.35), (xs0, Y_TEE)],
         fc=SUP_F, ec=SUP, lw=0.8, z=10.4)
    line(ax, [(xs1, AH_CY - CON_W / 2), (xs1, AH_CY + CON_W / 2)], color=SUP_F, lw=1.2, z=10.5)
    # air handler with the plenum on top
    rect(ax, *m.AHU[:2], *m.AHU[2:], fc=SUP_F, ec=SUP, lw=1.3, z=10.6)
    line(ax, [m.AHU[:2], m.AHU[2:]], color=SUP, lw=0.4, z=10.7)
    line(ax, [(m.AHU[0], m.AHU[3]), (m.AHU[2], m.AHU[1])], color=SUP, lw=0.4, z=10.7)
    # registers
    sidewall(ax, S1_X, m.Y1, 1.0, (0, -1))
    sidewall(ax, m.E1, S2_Y, 1.0, (-1, 0))
    sidewall(ax, S3_X, m.Y2 + SOF_W, 1.0, (0, 1))
    sidewall(ax, TR_CX, m.Y1, 14 * IN, (0, -1))
    sidewall(ax, S5_X, m.Y1, 14 * IN, (0, -1))
    sidewall(ax, m.SHAFT_X0, S8_Y, 8 * IN, (1, 0))
    ceil_reg(ax, *CR1)
    ceil_reg(ax, *CR2)


def draw_return(ax):
    d = D["D12"]
    rect(ax, m.X_H1 - 0.16, AH_CY - 10 * IN, m.X_H1 + 0.02, AH_CY + 10 * IN, fc=RET, ec=RET, lw=0.6, z=12.6)     # 20 x 20 filter grille
    for dy in (-0.5, 0.5):
        ax.annotate("", xy=(m.X_H1 - 0.2, AH_CY + dy), xytext=(m.X_H1 - 1.0, AH_CY + dy),
                    arrowprops=dict(arrowstyle="-|>", lw=0.7, color=RET, mutation_scale=5, shrinkA=0, shrinkB=0), zorder=12.6)
    transfer(ax, m.E1, T1_Y - 0.5, m.X_H0, T1_Y + 0.5)                                            # T-1 over the bedroom 1 door
    transfer(ax, m.E1, T2_Y - 0.5, m.X_H0, T2_Y + 0.5)                                            # T-2 over the bedroom 2 door
    rect(ax, m.X_H0 + 0.06, T2_Y - 0.5, m.X_H0 + 0.06 + 8 * IN, T2_Y + 0.5, fc=RET_F, ec=RET, lw=0.7, z=11.5)   # its grille in the hall soffit
    transfer(ax, T3_X - 0.5, m.Y1, T3_X + 0.5, m.Y2)                                              # T-3 below the soffit
    # service clearance in front of the closet door
    rect(ax, m.X_H1 - 2.5, AH_CY - 1.25, m.X_H1, AH_CY + 1.25, fc="none", ec=INK, lw=0.5, z=11.2, ls=(0, (2, 2)))
    del d


def draw_exhaust(ax, hood=True):
    for (fx, fy), pts in ((EF1, [EF1, (m.xw_o(EF1[1]), EF1[1])]), (EF2, [EF2, (EF2[0], m.yr_o(EF2[0]))]), (EF3, [EF3, (EF3[0], m.yr_o(EF3[0]))])):
        duct(ax, pts, 4 * IN, color=EXH, fc=EXH_F, z=9.6)
        fan(ax, fx, fy)
    duct(ax, [(DV_X, DV_Y0), (DV_X, m.yr_o(DV_X))], 4 * IN, color=EXH, fc=EXH_F, z=9.6)
    ax.add_patch(plt.Circle((DV_X, DV_Y0), 0.24, fc=EXH, ec=EXH, zorder=12))
    if hood:
        rect(ax, *m.RANGE[:2], *m.RANGE[2:], fc="none", ec=EXH, lw=1.0, z=11)
    duct(ax, [(RH_X, RH_Y0), (RH_X, m.YF)], 6 * IN, color=EXH, fc=EXH_F, z=9.6)
    for t in TERMS:
        cap(ax, t[2], t[3])


def draw_hp(ax, unit=None, both_bold=False):
    for i, u in enumerate("AB"):
        on = both_bold or u == unit
        poly(ax, hp_poly(i, PAD_GROW), fc="#eceef1", ec=BG_EDGE, lw=0.4, z=7.9)
        poly(ax, hp_poly(i), fc=PAPER, ec=REF if on else BG_EDGE, lw=1.1 if on else 0.6, z=8)


def draw_lineset(ax, unit, path=True):
    y = LS_Y[unit]
    xo = m.xw_o(y)
    if path:
        line(ax, [LS_DROP, (LS_DROP[0], y), (xo, y)], color=REF, lw=1.1, ls=(0, (3, 1.6)), z=11.4)
        ax.add_patch(plt.Circle(LS_DROP, 0.2, fc=PAPER, ec=REF, lw=1.0, zorder=12))
    rect(ax, xo - 0.42, y - 0.17, xo, y + 0.17, fc=REF, ec=REF, lw=0.5, z=12)                      # cover on the wall
    yd = DS_Y[unit]
    xd = m.xw_o(yd)
    rect(ax, xd - 0.3, yd - 0.33, xd, yd + 0.33, fc=PAPER, ec=INK, lw=0.9, z=12)                   # disconnect


def draw_condensate(ax):
    x = m.AHU[2] - 0.3
    line(ax, [(x, m.AHU[1]), (x, m.WD_Y1 - 0.25)], color=CND, lw=1.0, ls=(0, (2, 1.4)), z=11.6)
    ax.add_patch(plt.Circle((x, m.WD_Y1 - 0.25), 0.14, fc=CND, ec=CND, zorder=12))


def draw_tstat(ax, r=0.36):
    ax.add_patch(plt.Circle((TSTAT[0] + r, TSTAT[1]), r, fc=PAPER, ec=HEAT, lw=0.9, zorder=13))
    txt(ax, TSTAT[0] + r, TSTAT[1], "T", size=4.2, color=HEAT, weight="bold", z=14)


# ----------------------------------------------------------------------------
# 5. M-102 / M-103: unit ductwork plans
# ----------------------------------------------------------------------------
VIEW_M = ((-5.0, 65.0), (2.5, 53.0))


def unit_tags(ax, u):
    b = dict(color=SUP)
    for t, (x, y) in (("S-1", (S1_X + 0.2, m.Y1 - 1.75)), ("S-2", (m.E1 - 3.55, S2_Y - 0.1)), ("S-3", (S3_X, m.Y2 + SOF_W + 1.75)),
                      ("S-4", (TR_CX - 0.15, m.Y1 - 1.75)), ("S-5", (S5_X + 0.75, m.Y1 - 1.75)), ("S-6", (CR1[0] - 0.95, CR1[1] - 1.0)),
                      ("S-7", (CR2[0] - 0.85, CR2[1] + 1.2)), ("S-8", (m.SHAFT_X0 + 2.5, S8_Y))):
        o = OUT[t]
        tag(ax, x, y, f"{t}  {o[3]}\n{o[2]} cfm", **b)
    # duct sizes
    tag(ax, TR_CX, 23.6, "16 x 8", SUP, size=4.2, box=False, rot=90)
    tag(ax, TR_CX, 28.75, "10 x 8", SUP, size=4.2, box=False, rot=90)
    tag(ax, (TR_CX + TR_W / 2 + m.AHU[0]) / 2, AH_CY, "20 x 8", SUP, size=4.2, box=False, rot=90)
    tag(ax, 17.9, Y_BR1, f'{rd(CFM[BR1])}" RD', SUP, size=4.2, box=False)
    tag(ax, 18.3, Y_B1 + 0.48, f'{rd(CFM[BA1])}" RD', SUP, size=4.0, box=False)
    tag(ax, 23.55, Y_E, "12x8", SUP, size=4.0, box=False)
    tag(ax, 28.9, Y_E, "12 x 6", SUP, size=4.2, box=False)
    tag(ax, 34.3, Y_E + 0.42, f'{rd(CFM[BA3])}" RD', SUP, size=4.0, box=False)
    tag(ax, TR_CX + 1.05, 31.0, f'{rd(CFM[BA2])}" RD', SUP, size=4.0, box=True)
    # return
    tag(ax, m.E1 - 2.15, T1_Y, "T-1 12x8", RET)
    tag(ax, m.E1 - 1.3, T2_Y + 1.05, "T-2", RET)
    tag(ax, T3_X, m.Y1 - 1.25, "T-3 12x8", RET)
    lead(ax, (m.X_H1 - 0.08, AH_CY - 0.75), (27.5, 24.7), "R-1 20x20", RET, size=4.2, weight="bold")
    for dn in ("D5", "D6", "D7"):
        x0, y0, x1, y1 = m.door_cut(D[dn])
        (hx, hy), a_, s_ = m.door_hinge(D[dn])
        tag(ax, (x0 + x1) / 2 - s_[0] * 0.75, (y0 + y1) / 2 - s_[1] * 0.75, "UC", RET, size=4.0, box=False)
    # exhaust
    tag(ax, EF1[0] + 0.2, EF1[1] + 0.85, "EF-1", EXH, size=4.2)
    tag(ax, EF2[0] + 0.15, EF2[1] + 0.85, "EF-2", EXH, size=4.2)
    tag(ax, EF3[0], EF3[1] - 0.95, "EF-3", EXH, size=4.2)
    tag(ax, m.RANGE[2] + 1.15, RH_Y0 + 0.3, 'RH-1\n6" RD', EXH, size=4.2)
    lead(ax, (DV_X, 32.0), (28.0, 31.6), 'DV-1 4" RD', EXH, size=4.2, weight="bold")
    tag(ax, 11.4, EF1[1] + 0.55, '4" RD', EXH, size=4.0, box=False)
    lead(ax, TERMS[0][2], (17.2, 8.4), "RH-1 CAP", EXH, size=4.2, weight="bold", ha="right")
    lead(ax, (TERMS[1][2][0] - 0.6, TERMS[1][2][1]), (4.6, 28.6), "EF-1 CAP", EXH, size=4.2, weight="bold", ha="right")
    lead(ax, (TERMS[2][2][0], TERMS[2][2][1] + 0.7), (19.6, 39.6), "EF-2 CAP", EXH, size=4.2, weight="bold", ha="right")
    lead(ax, (TERMS[3][2][0] + 0.2, TERMS[3][2][1] + 0.7), (27.4, 38.6), "DV-1 CAP", EXH, size=4.2, weight="bold")
    lead(ax, (TERMS[4][2][0] + 0.25, TERMS[4][2][1] + 0.7), (45.2, 32.9), "EF-3 CAP", EXH, size=4.2, weight="bold")
    # equipment
    lead(ax, (m.AHU[2], AH_CY + 0.5), (27.5, 26.75), f"AHU-{u}\nplenum on top", SUP, size=4.4, weight="bold")
    i = "AB".index(u)
    hx, hy = m.HP[i]
    lead(ax, (hx - 0.7, hy), (1.6, hy - 0.2 if u == "A" else hy + 0.6), f"HP-{u}", REF, size=5.0, weight="bold", ha="right")
    o = "BA"[i]
    ox, oy = m.HP[1 - i]
    lead(ax, (ox - 0.7, oy), (1.6, oy + 1.6 if u == "A" else oy - 1.4), f"HP-{o} (Unit {o})", GREY, size=4.2, ha="right")
    lead(ax, (m.xw_o(DS_Y[u]) - 0.3, DS_Y[u]), (4.3, DS_Y[u] - 2.4 if u == "A" else DS_Y[u] + 3.6), "DISCONNECT", INK, size=4.2, ha="right")
    # ceiling heights of the shaded zones
    z = dict(color=ZONE_E, size=4.0, box=False)
    tag(ax, m.B1_X0 + 1.0, m.Y3 - 0.45, "CLG 7'-0\"", **z)
    tag(ax, m.X_H0 + 1.6, m.B2_Y1 - 0.2, "CLG 7'-0\"", **z)
    tag(ax, EF3[0], m.B3_Y1 - 0.6, "CLG 7'-0\"", **z)
    lead(ax, (m.X_ST - SOF_W + 0.3, SOF_Y1 - 0.5), (33.3, 28.2), "SOFFIT, UNDERSIDE 7'-0\"", ZONE_E, size=4.0, weight="bold", ha="center")
    lead(ax, (KSOF[2] - 0.2, KSOF[1] + 0.9), (23.9, 11.6), "SOFFIT OVER WALL\nCABINETS, 7'-0\"", ZONE_E, size=4.0, weight="bold")
    # dimensions
    dim(ax, (m.X_ST - SOF_W, m.Y2), (m.X_ST - SOF_W, SOF_Y1), 0.75, size=4.6)
    dim(ax, (DV_X, DV_Y0), (DV_X, m.yr_o(DV_X)), -1.3, size=4.6)
    # keynotes on the plan
    for n, (x, y) in {1: (27.4, 28.1), 2: (24.3, 28.85), 3: (20.5, 26.65), 4: (15.6, 23.25), 5: (24.6, 23.55), 6: (29.6, 23.75),
                      7: (17.9, T1_Y - 1.2), 8: (25.0, 33.4), 9: (23.0, 15.9), 10: (28.0, 33.2), 12: (27.4, 22.95), 13: (18.2, 25.95)}.items():
        keynote(ax, x, y, n)
    keynote(ax, 3.9, LS_Y[u] - 0.9 if u == "A" else LS_Y[u] - 5.9, 11)
    if u == "B":
        line(ax, [(4.4, LS_Y[u] - 5.5), (m.xw_o(LS_Y[u]) - 0.45, LS_Y[u] - 0.1)], color=REF, lw=0.35, z=13)
    line(ax, [(26.8, 28.0), (m.AHU[2], AH_CY + 0.75)], lw=0.35, z=13)
    line(ax, [(23.9, 28.4), (23.2, AH_CY + 0.6)], lw=0.35, z=13)
    line(ax, [(26.8, 22.95), (m.AHU[2] - 0.3, m.WD_Y1 - 0.1)], color=CND, lw=0.35, z=13)
    line(ax, [(18.8, 25.9), (TSTAT[0] + 0.1, TSTAT[1] + 0.2)], color=HEAT, lw=0.35, z=13)


def unit_keynotes(u):
    dep = inch(CLG[u] - m.CLG_SOFFIT)
    p = "P-102" if u == "A" else "P-103"
    return [
        (1, f"AIR HANDLER AHU-{u}: vertical, 21 x 21 in., on a 24 in. open return stand, supply plenum on top, {STRIP_KW} kW strip "
            "heat. Keep 30 x 30 in. clear in the hall in front of the 2'-0\" closet door (dashed) for service."),
        (2, f"20 x 8 from the plenum through a framed opening above the closet door into the hall soffit: {TOTAL_CFM} cfm, "
            f"{fpm(TOTAL_CFM, 20, 8):.0f} fpm."),
        (3, f"MAIN TRUNK in the hall soffit: 16 x 8 south ({Q_S} cfm, {fpm(Q_S, 16, 8):.0f} fpm), 10 x 8 north ({Q_N} cfm). "
            "Galvanized steel, every joint sealed with mastic."),
        (4, f"{rd(CFM[BR1])} in. round to S-1 and {rd(CFM[BA1])} in. round to S-6 cross bath 1's dropped ceiling above the tub. No duct through the "
            "wall space above the electrical panel."),
        (5, f"12 x 8 ({Q_E} cfm) over the W/D closet with a boot to S-5, then 12 x 6 ({Q_SOF} cfm) through the wall into the bedroom 3 soffit."),
        (6, f"BEDROOM 3 SOFFIT: L-shaped, 1'-4\" wide, underside 7'-0\" ({dep} deep), full length of the south wall and {ftin(SOF_Y1 - m.Y2)} up "
            f"the east wall. 12 x 6 to S-3 in the soffit face, then {rd(CFM[BA3])} in. round to S-8 above the bath 3 door. The stair wall's Type X "
            "board runs up behind the soffit; no opening in the stair wall."),
        (7, "RETURN AIR: R-1 filter grille low in the air-handler closet door. T-1 and T-2: 12 x 8 transfer grilles above the bedroom "
            "doors (T-2 turns down to a grille in the hall soffit). T-3: 12 x 8 through the wall below the soffit, top at 6'-10\". "
            "UC = bath door undercut 1 in."),
        (8, f"BATH FANS EF-1, EF-2, EF-3: {FAN_CFM} cfm each, 4 in. rigid duct to a wall cap with damper. EF-2 runs all the time at "
            f"{VENT_CFM} cfm for whole-flat ventilation. EF-3 sits in a dropped ceiling over the tub."),
        (9, f"RANGE HOOD RH-1: 6 in. round up into the 13 in. soffit above the wall cabinets, {ftin(RH_RUN)} south to a cap on the front "
            f"wall under the porch roof. The WEST sash of window W2 must be the fixed one: the cap is {ftin(RH_CLEAR)} from the east sash."),
        (10, f"DRYER DV-1: 4 in. rigid metal. Riser at the back of the W/D closet, then north in the dropped ceiling past the air "
             f"handler and over the bath 2 tub to a damper cap (no screen) on the rear wall. {ftin(DV_RUN)} run + {ftin(DRY_RISER)} riser + "
             f"2 elbows = {DV_EQ:.0f} equivalent ft; 35 max."),
        (11, f"LINE SET (3/8 + 3/4 in., insulated) drops in the closet corner into THIS flat's floor trusses, runs to the west wall, "
             f"leaves through the rim at about EL {LS_EL[u]:.1f} and runs in a cover to HP-{u}. About {ls_len(u)} ft."),
        (12, f"CONDENSATE: 3/4 in. PVC, trapped, with an overflow shut-off switch, sloped 1/8 in. per ft through the closet wall to "
             f"the washer standpipe box ({p}). No pump."),
        (13, "THERMOSTAT at 5'-0\" on the hall west wall, away from the registers. One per flat."),
    ]


def legend(ax, x, y, pitch=1.22, size=4.6):
    txt(ax, x - 0.6, y + 1.3, "LEGEND", size=6.2, weight="bold", ha="left")
    items = [("duct", "Supply duct, drawn to scale.\nSizes are width x depth, inches"), ("sw", "High sidewall supply register,\narrows show the throw"),
             ("cr", "Ceiling supply register"), ("fg", "Return-air filter grille (low)"), ("tg", "Transfer grille, high on the wall"),
             ("ef", "Bath fan and 4 in. exhaust duct"), ("cap", "Wall cap with damper"), ("ls", "Refrigerant line set, in the\nfloor trusses below"),
             ("cd", "Condensate drain, 3/4 in."), ("zone", "Dropped ceiling or soffit,\nunderside 7'-0\" above the floor"), ("t", "Thermostat"),
             ("key", "Keynote, see the list above"), ("txt", "RD = round duct · UC = door\nundercut 1 in. · cfm = air quantity")]
    yy = y
    for k, s in items:
        if k == "duct":
            rect(ax, x - 0.6, yy - 0.3, x + 0.6, yy + 0.3, fc=SUP_F, ec=SUP, lw=0.7, z=10)
        elif k == "sw":
            sidewall(ax, x, yy + 0.35, 1.0, (0, -1))
        elif k == "cr":
            ceil_reg(ax, x, yy)
        elif k == "fg":
            rect(ax, x - 0.5, yy - 0.1, x + 0.5, yy + 0.1, fc=RET, ec=RET, z=10)
        elif k == "tg":
            transfer(ax, x - 0.19, yy - 0.4, x + 0.19, yy + 0.4)
        elif k == "ef":
            rect(ax, x - 0.6, yy - 0.16, x + 0.2, yy + 0.16, fc=EXH_F, ec=EXH, lw=0.7, z=10)
            fan(ax, x + 0.3, yy, 0.34)
        elif k == "cap":
            cap(ax, (x - 0.3, yy), (1, 0))
        elif k == "ls":
            line(ax, [(x - 0.6, yy), (x + 0.6, yy)], color=REF, lw=1.1, ls=(0, (3, 1.6)), z=10)
        elif k == "cd":
            line(ax, [(x - 0.6, yy), (x + 0.6, yy)], color=CND, lw=1.0, ls=(0, (2, 1.4)), z=10)
        elif k == "zone":
            rect(ax, x - 0.6, yy - 0.35, x + 0.6, yy + 0.35, fc=ZONE_F, ec=ZONE_E, lw=0.45, z=7.6, alpha=0.55, ls=(0, (3, 2)))
        elif k == "t":
            ax.add_patch(plt.Circle((x, yy), 0.36, fc=PAPER, ec=HEAT, lw=0.9, zorder=13))
            txt(ax, x, yy, "T", size=4.2, color=HEAT, weight="bold", z=14)
        elif k == "key":
            keynote(ax, x, yy, 1, r=0.5)
        txt(ax, x + 1.1 if k != "txt" else x - 0.6, yy, s, size=size, ha="left")
        yy -= pitch * (1.45 if "\n" in s else 1.0)


def unit_notes(u):
    dep = inch(CLG[u] - m.CLG_SOFFIT)
    if u == "A":
        where = ["No floor ducts: the rear rooms are on a",
                 "slab. Ducts stay BELOW the 1-hour ceiling",
                 f"(2 layers 5/8 Type X): {dep} of space, so no",
                 "duct is deeper than 8 in. Nothing cuts",
                 "the rated ceiling: no duct, no register."]
    else:
        where = ["Same soffits and duct sizes as Unit A.",
                 "NOTHING in the attic: no duct, no fan, no",
                 "vent through the roof. Ducts stay below",
                 f"the ceiling board (R-49 above it); {dep} of",
                 "space above the 7'-0\" line."]
    return [
        (f"Unit {u} heating and cooling", [
            "One 2-ton ducted split heat pump on this",
            f"flat's meter: outdoor unit HP-{u} on the west",
            f"side yard, air handler AHU-{u} with {STRIP_KW} kW strip",
            "in the hall closet. All electric, no flue.",
        ]),
        ("Where the ducts run", [
            "All overhead, inside the flat, in dropped",
            "ceilings and soffits with the underside",
            "at 7'-0\" (shaded): trunk over the hall,",
            "branches over the baths and closets.",
        ] + where),
        ("Air quantities", [
            f"Room cfm = {TOTAL_CFM} x room area / {A_SUP:.0f} sf of",
            "supplied rooms (table on M-201). Round",
            "ducts: 5 in. = 60 cfm, 6 in. = 100, 7 in. = 140,",
            f"8 in. = 180. Rectangular: {RECT_FPM} fpm max. The",
            "contractor confirms with Manual J, S, D.",
        ]),
        ("Ventilation and exhaust", [
            "IRC M1505: 0.01 x 784 sf + 7.5 x (3 + 1) =",
            f"{VENT_FORMULA:.0f} cfm; the code table makes it {VENT_CFM} cfm.",
            "EF-2 runs at that rate all the time.",
            "Hood under 400 cfm: no make-up air unit.",
            "Wall caps 3 ft min. from windows, doors",
            "and lot lines; none on the stair side.",
        ]),
    ]


def unit_mech_sheet(pdf, number, u):
    fig, bg = sheet(number, "3/16\" = 1'-0\"", unit_notes(u))
    ax = plan_frame(fig, f"Unit {u} ductwork plan",
                    f"EL {EL[u]:.1f} · ceiling {ftin(CLG[u])}, soffits 7'-0\" · supply blue, return green, exhaust purple · preliminary",
                    view=VIEW_M, north=False, lot=False)
    line(ax, [(west_x(7.0), 7.0), (west_x(46.5), 46.5)], color=ACCENT, lw=1.0, ls=(0, (9, 2.5, 1.5, 2.5)), z=5.25)
    txt(ax, west_x(40.0) - 0.6, 40.0, "WEST LOT LINE", size=5.0, color=ACCENT, rot=90 - math.degrees(WEST_LEAN))
    north_arrow(ax, 61.6, 9.0, 1.8, 6.5)
    unit_plan(ax, "bg", u, furniture=False)
    draw_zones(ax)
    draw_hp(ax, u)
    draw_exhaust(ax)
    draw_supply(ax)
    draw_return(ax)
    draw_lineset(ax, u)
    draw_condensate(ax)
    draw_tstat(ax)
    unit_tags(ax, u)
    # keynote list, two columns above the rear wall
    items = wrap_list(unit_keynotes(u), 78)
    cols = [(17.6, 52.35, items[:7]), (41.6, 52.35, items[7:])]
    for x, y, part in cols:
        for n, lines in part:
            keynote(ax, x, y - 0.02, n, r=0.44)
            for ln in lines:
                txt(ax, x + 0.85, y, ln, size=4.7, ha="left")
                y -= 0.62
            y -= 0.14
    legend(ax, 53.6, 31.2)
    if u == "A":
        tag(ax, 30.0, 5.2, "UNIT A: NO FLOOR DUCTS (REAR ROOMS ARE ON A SLAB) · EVERYTHING IS OVERHEAD, BELOW THE RATED CEILING", SUP, size=5.0, box=False)
    else:
        tag(ax, 30.0, 5.2, "UNIT B: SAME SOFFITS AS UNIT A · NOTHING IN THE ATTIC · FANS, HOOD AND DRYER LEAVE THROUGH THE WALLS, NOT THE ROOF", SUP, size=5.0, box=False)
    save(fig, number, pdf)


def sheet_m102(pdf):
    unit_mech_sheet(pdf, "M-102", "A")


def sheet_m103(pdf):
    unit_mech_sheet(pdf, "M-103", "B")


# ----------------------------------------------------------------------------
# 6. M-101: garage level and outdoor units
# ----------------------------------------------------------------------------
def heater(ax, x, y, s=0.6):
    rect(ax, x - s, y - s, x + s, y + s, fc=PAPER, ec=HEAT, lw=1.1, z=12)
    txt(ax, x, y, "H", size=4.6, color=HEAT, weight="bold", z=13)


def garage_view(fig, bg):
    L, B, fpi = 0.62, 5.98, 8.0
    ax = plan_axes(fig, L, B, (-1.5, 50.5), (6.5, 37.0), fpi)
    vt(bg, L + 0.05, 10.2, "Garage level mechanical plan", "1/8\" = 1'-0\" · EL %.1f · open, unheated garage · two small heaters on Unit A's common circuit" % m.EL_GAR)
    line(ax, [LOT_NW, LOT_SW, LOT_SE, LOT_NE, LOT_NW], color=ACCENT, lw=0.9, ls=(0, (9, 2.5, 1.5, 2.5)), z=5.25)
    site_work(ax, bg=True)
    lower_plan(ax, "bg", cars=False, labels=False)
    poly(ax, m.IN_L, fc="#e4eef9", ec=SUP, lw=0.4, z=4.2, alpha=0.55, ls=(0, (3, 2)))
    draw_hp(ax, both_bold=True)
    # heaters
    h1 = (m.UTIL[0] + 1.3, m.UTIL[2] + 0.62)
    h2 = (m.XE_GI - 0.62, m.SHAFT_L[2] + 1.8)
    heater(ax, *h1)
    heater(ax, *h2)
    lead(ax, (h1[0], h1[1] + 0.6), (38.0, 33.3), "UH-1  500 W WALL HEATER, UTILITY ROOM\nown thermostat set to 45 °F", HEAT, size=4.6, weight="bold", ha="center")
    lead(ax, (h2[0] - 0.6, h2[1]), (34.6, 12.4), "UH-2  1,500 W WALL HEATER, STAIR\nown thermostat set to 50 °F", HEAT, size=4.6, weight="bold", ha="right")
    # Unit A line set in the truss space
    y = LS_Y["A"]
    line(ax, [LS_DROP, (LS_DROP[0], y), (m.xw_o(y), y)], color=REF, lw=1.1, ls=(0, (3, 1.6)), z=11)
    ax.add_patch(plt.Circle(LS_DROP, 0.3, fc=PAPER, ec=REF, lw=1.0, zorder=12))
    lead(ax, LS_DROP, (25.2, 26.2), "FROM AHU-A ABOVE", REF, size=4.4, weight="bold")
    tag(ax, 16.6, y + 1.35, "HP-A LINE SET IN THE UNIT A FLOOR TRUSSES,\nabove the R-30 (warm side), out through the rim", REF, size=4.4)
    tag(ax, 23.6, 23.4, "OPEN GARAGE: UNHEATED · NO FAN · NO DUCTS · NO EQUIPMENT", INK, size=5.2)
    tag(ax, 23.6, 21.9, "ventilated by the open front (25'-0\" wide, no doors)", GREY, size=4.6, weight="normal")
    tag(ax, 23.2, 16.3, "CEILING OVER THE WHOLE GARAGE (shaded): 5/8 in. TYPE X BOARD + R-30 IN THE BOTTOM OF\n"
        "THE 20 in. TRUSSES. THE TRUSS SPACE ABOVE THE INSULATION IS RESERVED FOR UNIT A'S\n"
        "PIPES AND THE HP-A LINE SET. THIS TRADE CUTS NO HOLE IN THE GARAGE CEILING BOARD.", SUP, size=4.4)
    for x in (16.0, 24.0, 32.0):
        ax.annotate("", xy=(x, 8.0), xytext=(x, 12.0), arrowprops=dict(arrowstyle="<|-|>", lw=0.8, color=GREY, mutation_scale=7), zorder=11)
    tag(ax, 3.2, 28.3, "HP-B", REF, size=4.8, ha="right")
    line(ax, [(3.4, 28.1), (m.HP[1][0] - 0.5, m.HP[1][1] + 0.9)], color=REF, lw=0.35, z=13)
    tag(ax, 2.2, 16.6, "HP-A", REF, size=4.8, ha="right")
    line(ax, [(2.4, 16.9), (m.HP[0][0] - 0.5, m.HP[0][1] - 0.9)], color=REF, lw=0.35, z=13)
    tag(ax, 22.5, 31.6, "NORTH OF THE GARAGE WALL: UNIT A SLAB ON GRADE (no ducts in or under it)", GREY, size=4.4, weight="normal")
    txt(ax, 47.2, 8.0, "LOT LINE", size=4.4, color=ACCENT)
    north_arrow(ax, 8.6, 33.6, 1.4, 6.0)
    return ax


def pads_view(fig, bg):
    L, B, fpi = 7.75, 5.6, 32 / 12.0
    ax = plan_axes(fig, L, B, (0.4, 11.3), (16.0, 27.6), fpi)
    vt(bg, L + 0.02, 10.2, "Heat-pump pads, west side yard", "3/8\" = 1'-0\" · side-discharge units 38 x 15 in. · pads 44 x 21 in.")
    unit_plan(ax, "bg", "A", furniture=False, labels=False, with_porch=False)
    line(ax, [(west_x(15.0), 15.0), (west_x(29.0), 29.0)], color=ACCENT, lw=1.0, ls=(0, (9, 2.5, 1.5, 2.5)), z=5.25)
    txt(ax, west_x(26.6) - 0.35, 26.6, "WEST LOT LINE", size=4.6, color=ACCENT, rot=90 - math.degrees(WEST_LEAN))
    draw_hp(ax, both_bold=True)
    for u in "AB":
        draw_lineset(ax, u, path=False)
    cap(ax, TERMS[1][2], HP_N, s=0.3)
    for i, u in enumerate("AB"):
        hx, hy = m.HP[i]
        txt(ax, hx, hy, f"HP-{u}", size=5.2, color=REF, weight="bold", rot=90 - math.degrees(WEST_LEAN), z=13)
        # chain across the side yard, perpendicular to the wall
        if u == "B":
            continue                                   # same clearances at HP-B
        s = -1                                         # dimension line beyond the south end of A
        e = (_cL, -_sL)                                # toward the wall
        c = (hx + HP_U[0] * s * _hw / 2, hy + HP_U[1] * s * _hw / 2)
        pts = [(c[0] - e[0] * (_hd / 2 + HP_FRONT), c[1] - e[1] * (_hd / 2 + HP_FRONT)), (c[0] - e[0] * _hd / 2, c[1] - e[1] * _hd / 2),
               (c[0] + e[0] * _hd / 2, c[1] + e[1] * _hd / 2), (c[0] + e[0] * (_hd / 2 + HP_BACK), c[1] + e[1] * (_hd / 2 + HP_BACK))]
        off = 0.95 * s
        dim(ax, pts[0], pts[1], off, f"{ftin(HP_FRONT)}", size=5.0)
        dim(ax, pts[1], pts[2], off, f"{ftin(_hd)}", size=5.0)
        dim(ax, pts[2], pts[3], off, "", size=5.0)
    # along the wall: window jamb, unit A, gap, unit B
    e = (_cL, -_sL)
    base = lambda t: (m.HP[0][0] - e[0] * (_hd / 2 + 1.0) + HP_U[0] * t, m.HP[0][1] - e[1] * (_hd / 2 + 1.0) + HP_U[1] * t)   # noqa: E731
    t0 = -_hw / 2
    stations = [t0, t0 + _hw, t0 + _hw + HP_GAP, t0 + 2 * _hw + HP_GAP]
    for a, b_, lab in ((stations[0], stations[1], ftin(_hw)), (stations[1], stations[2], inch(HP_GAP)), (stations[2], stations[3], ftin(_hw))):
        dim(ax, base(a), base(b_), 0.0, lab, size=5.0, ext=False)
    # bedroom window to unit A along the wall face
    wj = (m.xw_o(W4[3]), W4[3])
    pa = (wj[0] + HP_U[0] * HP_WIN, wj[1] + HP_U[1] * HP_WIN)
    dim(ax, wj, pa, 1.0, ftin(HP_WIN), size=4.8)
    lead(ax, (m.xw_i(16.5) + 0.1, 16.5), (9.0, 16.9), "BEDROOM 1 WINDOW W4\n(Unit A sill at EL %.1f)" % (m.EL_A + 3.5), GREY, size=4.4, ha="center")
    lead(ax, (m.xw_o(DS_Y["A"]) - 0.3, DS_Y["A"] - 0.2), (5.6, 16.45), "DS-A", INK, size=4.8, weight="bold", ha="right")
    lead(ax, (m.xw_o(LS_Y["A"] - 0.95) - HP_BACK / 2, LS_Y["A"] - 1.05), (8.9, 18.25), f"{inch(HP_BACK)} UNIT TO WALL", INK, size=4.4, ha="left")
    tag(ax, 4.0, 27.05, f"UNIT TO THE WEST LOT LINE: {ftin(HP_FRONT)}\n(ZONING MINIMUM 2'-0\") · SAME AT HP-B", ACCENT, size=4.4)
    lead(ax, (m.xw_o(DS_Y["B"]) - 0.15, DS_Y["B"]), (9.6, 27.1), "DS-B", INK, size=4.8, weight="bold", ha="left")
    lead(ax, (m.xw_o(LS_Y["A"]) - 0.2, LS_Y["A"] - 0.1), (2.7, 18.0), "LINE-SET COVER A\ninto the rim at EL %.1f" % LS_EL["A"], REF, size=4.4, weight="bold", ha="right")
    lead(ax, (m.xw_o(LS_Y["B"]), LS_Y["B"]), (9.3, 22.3), "LINE-SET COVER B\nup the wall to EL %.1f" % LS_EL["B"], REF, size=4.4, weight="bold", ha="left")
    lead(ax, (TERMS[1][2][0], TERMS[1][2][1]), (9.6, 25.5), "EF-1 CAPS ABOVE\n(EL %.1f and %.1f)" % (EL["A"] + CAP_H, EL["B"] + CAP_H), EXH, size=4.4, weight="bold", ha="left")
    tag(ax, 10.2, 19.9, "BEDROOM 1", GREY, size=4.4, weight="normal")
    tag(ax, 10.3, 23.6, "CLOSETS", GREY, size=4.4, weight="normal")
    return ax


def elevation_view(fig, bg):
    L, B, fpi = 0.62, 0.62, 16 / 3.0
    y0, y1 = 13.0, 31.5
    ax = plan_axes(fig, L, B, (y0, y1), (921.0, 944.6), fpi)
    ax.set_xlim(y1, y0)                                               # looking east: north is to the left
    vt(bg, L + 0.03, 5.52, "West wall at the heat pumps", "3/16\" = 1'-0\" · looking east · existing grade from LiDAR")
    ys = [y0 + i * 0.25 for i in range(int((y1 - y0) / 0.25) + 1)]
    g = [elev(m.xw_o(y) - 0.6, y) for y in ys]
    rect(ax, y0, 921.0, y1, 943.65, fc="#f1f2f4", ec=BG_EDGE, lw=0.5, z=2)
    for u in "AB":
        rect(ax, y0, EL[u] - 0.0625 - TRUSS[u], y1, EL[u], fc=TIMBER, ec=BG_EDGE, lw=0.4, z=3)
        line(ax, [(y0, EL[u]), (y1, EL[u])], color=INK, lw=0.7, z=4)
        txt(ax, y1 - 0.25, EL[u] + 0.42, f"UNIT {u} FLOOR  EL {EL[u]:.1f}", size=4.6, weight="bold", ha="left", z=9)
        txt(ax, y1 - 0.25, EL[u] - 0.95, f"{inch(TRUSS[u])} floor trusses", size=4.2, color=GREY, ha="left", z=9)
        rect(ax, W4[2], EL[u] + 3.5, W4[3], EL[u] + 7.5, fc=PAPER, ec=BG_EDGE, lw=0.6, z=4)
        txt(ax, (W4[2] + W4[3]) / 2, EL[u] + 5.5, "W4", size=4.2, color=GREY, z=5)
    poly(ax, [(y0, 921.0)] + list(zip(ys, g)) + [(y1, 921.0)], fc="#e6dccb", ec=EARTH, lw=0.8, z=6)
    txt(ax, 29.6, 923.3, "EXISTING GRADE", size=4.2, color=EARTH, z=9)
    for i, u in enumerate("AB"):
        hy, pe = m.HP[i][1], PAD_EL[i]
        a, b_ = hy - _hw / 2 * _cL, hy + _hw / 2 * _cL
        rect(ax, a - 0.25, pe - PAD_T, b_ + 0.25, pe, fc="#cfd3d8", ec=BG_EDGE, lw=0.4, z=7)
        rect(ax, a, pe, b_, pe + HP_H, fc=PAPER, ec=REF, lw=1.1, z=8)
        txt(ax, hy, pe + HP_H / 2, f"HP-{u}", size=4.6, color=REF, weight="bold", z=9)
        yl = LS_Y[u]
        rect(ax, yl - 0.17, pe + 0.75, yl + 0.17, LS_EL[u], fc=REF, ec=REF, lw=0.4, z=8.5)
        ax.add_patch(plt.Circle((yl, LS_EL[u]), 0.26, fc=PAPER, ec=REF, lw=1.0, zorder=9))
        yd = DS_Y[u]
        rect(ax, yd - 0.33, pe + 3.6, yd + 0.33, pe + 4.6, fc=PAPER, ec=INK, lw=0.9, z=8.5)
        ye = EF1[1]
        poly(ax, [(ye - 0.3, EL[u] + CAP_H - 0.25), (ye + 0.3, EL[u] + CAP_H - 0.25), (ye + 0.3, EL[u] + CAP_H + 0.25), (ye - 0.3, EL[u] + CAP_H + 0.25)],
             fc=EXH, ec=EXH, z=8.5)
    lead(ax, (LS_Y["B"], 930.6), (20.9, 931.6), f"LINE-SET COVER B\npad to EL {LS_EL['B']:.1f}", REF, size=4.4, weight="bold", ha="left")
    lead(ax, (LS_Y["A"] - 0.2, LS_EL["A"]), (17.6, 927.4), f"SLEEVE A\nEL {LS_EL['A']:.1f}", REF, size=4.4, weight="bold", ha="left")
    lead(ax, (LS_Y["B"] + 0.2, LS_EL["B"]), (26.2, 937.6), f"SLEEVE B  EL {LS_EL['B']:.1f}", REF, size=4.4, weight="bold", ha="right")
    lead(ax, (DS_Y["A"], PAD_EL[0] + 4.6), (16.6, 930.6), "DS-A", INK, size=4.4, weight="bold", ha="center")
    lead(ax, (DS_Y["B"], PAD_EL[1] + 4.6), (28.6, 931.2), "DS-B", INK, size=4.4, weight="bold", ha="center")
    lead(ax, (EF1[1] + 0.3, EL["A"] + CAP_H), (29.3, 933.6), f"EF-1 (A)\nEL {EL['A'] + CAP_H:.1f}", EXH, size=4.4, weight="bold", ha="center")
    lead(ax, (EF1[1] + 0.3, EL["B"] + CAP_H), (29.3, 941.6), f"EF-1 (B)\nEL {EL['B'] + CAP_H:.1f}", EXH, size=4.4, weight="bold", ha="center")
    txt(ax, m.HP[0][1], PAD_EL[0] - 1.25, f"PAD A\nEL {PAD_EL[0]:.1f}", size=4.2, z=9)
    txt(ax, m.HP[1][1], PAD_EL[1] - 1.25, f"PAD B\nEL {PAD_EL[1]:.1f}", size=4.2, z=9)
    txt(ax, y1 - 0.4, 921.5, "N", size=5.5, weight="bold", z=9)
    txt(ax, y0 + 0.4, 921.5, "S", size=5.5, weight="bold", z=9)
    return ax


def key_view(fig, bg):
    L, B, fpi = 4.75, 0.5, 8.0
    ax = plan_axes(fig, L, B, (2.5, 47.5), (6.0, 44.4), fpi)
    vt(bg, L + 0.25, 5.52, "Wall terminations, Units A and B", "1/8\" = 1'-0\" · same plan position on both floors · dashed circles = 3 ft clear of openings")
    unit_plan(ax, "bg", "A", furniture=False, labels=False)
    draw_exhaust(ax, hood=False)
    for t in TERMS:
        ax.add_patch(plt.Circle(t[2], 3.0, fc="none", ec=EXH, lw=0.5, ls=(0, (3, 2)), zorder=11))
    nw, ne, sw = m.OUT_U[3], m.OUT_U[2], m.OUT_U[0]
    pr = [nw, TERMS[2][2], TERMS[3][2], TERMS[4][2], ne]
    for a, b_ in zip(pr[:-1], pr[1:]):
        dim(ax, b_, a, -3.4, size=4.8)
    dim(ax, sw, TERMS[0][2], -2.6, size=4.8)
    dim(ax, sw, TERMS[1][2], 2.3, size=4.8)
    tag(ax, TERMS[0][2][0] - 1.7, m.YF - 1.3, "RH-1", EXH, size=4.6, box=True)
    tag(ax, TERMS[1][2][0] - 1.5, TERMS[1][2][1] + 0.9, "EF-1", EXH, size=4.6)
    for k, dx in ((2, -0.2), (3, 0.3), (4, 0.2)):
        p = TERMS[k][2]
        tag(ax, p[0] + dx + 1.25, p[1] + 1.1, TERMS[k][0], EXH, size=4.6)
    mid = (W2[2] + W2[3]) / 2
    dim(ax, (RH_X, m.YF), (mid, m.YF), -0.9, ftin(RH_CLEAR), size=4.6, color=EXH)
    lead(ax, ((W2[2] + mid) / 2, m.YF - 0.1), (30.5, 7.6), "W2: WEST SASH FIXED,\nEAST SASH SLIDES", EXH, size=4.4, weight="bold")
    draw_hp(ax, both_bold=True)
    tag(ax, 38.0, 17.0, "STAIR:\nNO CAPS", GREY, size=4.4, weight="normal", box=False)
    tag(ax, 28.0, 26.5, "ALL CAPS AT 7'-4\" ABOVE THE FLOOR\nUNIT A: EL %.1f · UNIT B: EL %.1f" % (EL["A"] + CAP_H, EL["B"] + CAP_H), EXH, size=4.6)
    return ax


def sheet_m101(pdf):
    notes = [
        ("Garage level", [
            "Open to the street: not heated, no fan,",
            "no ducts, no equipment, no water piping.",
            "UH-1 keeps the utility room (water heaters",
            "and water entries) above freezing. UH-2",
            "keeps the stair at 50 °F. Both have their",
            "own thermostat; circuit CL, Unit A panel.",
        ]),
        ("Outdoor units HP-A and HP-B", [
            "One per flat, each on a level pad 3 in.",
            f"above grade. Unit to the west lot line: {ftin(HP_FRONT)}",
            f"(zoning min. 2'-0\"). Unit to the wall: {inch(HP_BACK)}.",
            f"Between units: {inch(HP_GAP)}. Check all three",
            "against the model bought; if it needs",
            "more at the valve end, slide pad B north.",
            "Pad levels are from LiDAR grade: set",
            "them from the grading plan (C-105).",
        ]),
        ("Line sets and power", [
            "Each line set runs in its own flat's floor",
            "trusses, leaves through the rim 6 in.",
            "below the floor and drops to the unit in",
            "a cover. Sleeve and seal the rim hole,",
            "8 in. min. above finished grade. DS = 30 A",
            "disconnect in sight, 3 ft clear in front.",
        ]),
        ("Wall terminations", [
            "Every cap is 3 ft or more from a window,",
            "door or lot line (IRC M1504.3). None on",
            "the stair or the east wall. W2's west",
            "sash must be fixed (tell A-601).",
        ]),
    ]
    fig, bg = sheet("M-101", "AS NOTED", notes)
    garage_view(fig, bg)
    pads_view(fig, bg)
    elevation_view(fig, bg)
    key_view(fig, bg)
    rows = [["TAG", "WHAT", "WALL", "NEAREST OPENING"]]
    for t in TERMS:
        rows.append([t[0], t[4], t[1], t[5].replace(" to the nearest window", " to a window").replace(" to the east (operable) sash of W2", " to W2 east sash")])
    bg.text(10.55, 4.72, "TERMINATION SCHEDULE (each flat)", fontsize=7.0, fontweight="bold", color=INK)
    yb = table(bg, 10.55, 4.6, [0.45, 1.05, 0.45, 1.2], rows, fs=5.0, rh=0.2)
    for i, ln in enumerate(["All caps: hooded, with back-draft damper.",
                            "Dryer cap: no screen. Rear and west walls are",
                            "5'-2\" from the lot line (3 ft min.).",
                            "Unit A rear caps: existing grade is up to 2 ft",
                            "above the floor there; caps are 5 ft above it."]):
        bg.text(10.55, yb - 0.17 - i * 0.15, ln, fontsize=5.2, color=INK, va="center")
    save(fig, "M-101", pdf)


# ----------------------------------------------------------------------------
# 7. M-201: schedules and details
# ----------------------------------------------------------------------------
def sec_shell(ax, u, x0, x1, walls, soffits, zlo=-1.25, zhi=9.4):
    cl = CLG[u]
    gt = 1.25 * IN if u == "A" else 0.625 * IN
    rect(ax, x0, zlo, x1, -0.0625, fc=TIMBER, ec="none", z=2)
    rect(ax, x0, -0.0625, x1, 0, fc="#cdb98a", ec=INK, lw=0.4, z=3)
    rect(ax, x0, cl + gt, x1, zhi, fc=TIMBER, ec="none", z=2)
    rect(ax, x0, cl, x1, cl + gt, fc=ACCENT if u == "A" else GREY, ec="none", z=6)
    for a, b_ in walls:
        rect(ax, a, 0, b_, cl, fc=BG_WALL, ec=BG_EDGE, lw=0.4, z=4)
    for a, b_ in soffits:
        rect(ax, a, 7.0 + 0.5 * IN, b_, 7.0 + 2 * IN, fc="#e9dcbb", ec=ZONE_E, lw=0.3, z=5)
        rect(ax, a, 7.0, b_, 7.0 + 0.5 * IN, fc=INK, ec="none", z=5)
    return cl, gt


def section_hall(fig, bg, L, B):
    """Section through the hall soffit at the branch take-offs, looking north (Unit A)."""
    x0, x1, fpi = 15.6, 28.0, 32 / 12.0
    ax = plan_axes(fig, L, B, (x0, x1), (-1.25, 9.4), fpi)
    vt(bg, L, B + 4.2, "1  Hall soffit and trunk duct", "3/8\" = 1'-0\" · Unit A, looking north at the branch take-offs")
    cl, gt = sec_shell(ax, "A", x0, x1, [(m.E1, m.X_H0), (m.X_H1, m.X_C0), (m.X_C1, m.X_B3)],
                       [(x0, m.E1), (m.X_H0, m.X_H1), (m.X_C0, m.X_C1), (m.X_B3, x1)])
    rect(ax, m.X_H1 - 0.01, 0, m.X_C0 + 0.01, 6.667, fc=PAPER, ec=BG_EDGE, lw=0.4, z=4.5)          # W/D door opening
    zb, zt = 7.0 + 2 * IN, 7.0 + 10 * IN
    xs0, xs1 = TR_CX - TR_W / 2, TR_CX + TR_W / 2
    rect(ax, x0, zb, xs0, zt, fc=SUP_F, ec=SUP, lw=0.7, z=7)                                       # 8 in. round to S-1
    rect(ax, xs1, zb, X_E1, zt, fc=SUP_F, ec=SUP, lw=0.7, z=7)                                     # 12 x 8
    poly(ax, [(X_E1, zb), (m.X_C1, zb + 1 * IN), (m.X_C1, zt - 1 * IN), (X_E1, zt)], fc=SUP_F, ec=SUP, lw=0.7, z=7)
    rect(ax, m.X_C1, zb + 1 * IN, x1, zt - 1 * IN, fc=SUP_F, ec=SUP, lw=0.7, z=7)                  # 12 x 6
    rect(ax, xs0, zb, xs1, zt, fc="#a9c9ec", ec=SUP, lw=1.2, z=8)                                  # trunk, cut
    line(ax, [(xs0, zb), (xs1, zt)], color=SUP, lw=0.4, z=8.5)
    line(ax, [(xs0, zt), (xs1, zb)], color=SUP, lw=0.4, z=8.5)
    rect(ax, m.TUBS[0][0], 0, m.E1, 1.5, fc=PAPER, ec=BG_EDGE, lw=0.6, z=4)                        # tub
    rect(ax, m.WD[0], 0, m.WD[2], 6.25, fc=PAPER, ec=BG_EDGE, lw=0.6, z=4)
    txt(ax, (m.WD[0] + m.WD[2]) / 2, 3.2, "W/D", size=4.6, color=GREY)
    txt(ax, 18.3, 0.75, "TUB", size=4.4, color=GREY)
    txt(ax, 16.9, 3.3, "BATH 1", size=4.8, color=GREY)
    txt(ax, (m.X_H0 + m.X_H1) / 2, 1.0, "HALL", size=4.8, color=GREY)
    txt(ax, 27.3, 3.0, "BED-\nROOM 3", size=4.6, color=GREY)
    dim(ax, (m.X_H0 + 0.55, 0), (m.X_H0 + 0.55, 7.0), 0.0, "7'-0\" CLEAR", size=4.8, ext=False)
    dim(ax, (m.X_H1 - 0.3, 7.0), (m.X_H1 - 0.3, cl), 0.0, inch(cl - 7.0), size=4.4, ext=False, side=-1.3)
    dim(ax, (16.2, 0), (16.2, cl), 0.0, ftin(cl) + " CEILING", size=4.8, ext=False)
    dim(ax, (m.X_H0, 5.6), (m.X_H1, 5.6), 0.0, ftin(m.X_H1 - m.X_H0), size=4.6, ext=False)
    txt(ax, TR_CX, 6.45, "TRUNK 16 x 8", size=4.6, color=SUP, weight="bold")
    line(ax, [(TR_CX, 6.62), (TR_CX, zb + 0.05)], color=SUP, lw=0.35, z=13)
    txt(ax, 17.6, 6.55, f'{rd(CFM[BR1])}" ROUND TO S-1', size=4.4, color=SUP, weight="bold")
    line(ax, [(17.6, 6.72), (17.6, zb + 0.1)], color=SUP, lw=0.35, z=13)
    txt(ax, 24.7, 6.62, "12 x 8", size=4.4, color=SUP, weight="bold")
    line(ax, [(24.7, 6.8), (24.7, zb + 0.1)], color=SUP, lw=0.35, z=13)
    txt(ax, 27.2, 6.45, "12 x 6", size=4.4, color=SUP, weight="bold")
    line(ax, [(27.2, 6.62), (27.2, zb + 0.2)], color=SUP, lw=0.35, z=13)
    txt(ax, (x0 + x1) / 2, 8.85, "UNIT B FLOOR TRUSSES (24 in.) = 1-HOUR FLOOR/CEILING ASSEMBLY", size=4.6, color=GREY, weight="bold")
    lead(ax, (19.0, cl + gt / 2), (17.0, 8.35), "RATED CEILING: 2 LAYERS 5/8 TYPE X, UNBROKEN ABOVE EVERY SOFFIT", ACCENT, size=4.4, weight="bold", ha="left")
    txt(ax, (x0 + x1) / 2, -0.65, "UNIT A FLOOR TRUSSES (20 in.): line set and pipes, no ducts", size=4.4, color=GREY)
    lead(ax, (23.0, 7.0 + 1.2 * IN), (22.7, 4.6), "SOFFIT: 1/2 in. board on\n1 1/2 in. framing hung\nbelow the rated ceiling", ZONE_E, size=4.2, weight="bold", ha="left")
    return ax


def section_closet(fig, bg, L, B):
    """Section through the air-handler closet and the hall, looking north (Unit A)."""
    x0, x1, fpi = 19.2, 29.6, 32 / 12.0
    ax = plan_axes(fig, L, B, (x0, x1), (-1.25, 9.4), fpi)
    vt(bg, L, B + 4.2, "2  Air-handler closet", "3/8\" = 1'-0\" · Unit A, looking north through the closet door")
    cl, gt = sec_shell(ax, "A", x0, x1, [(x0, m.X_H0), (m.X_H1, m.X_C0), (m.X_C1, m.X_B3)], [(m.X_H0, m.X_H1), (m.X_C0, m.X_C1)])
    rect(ax, m.X_H1 - 0.01, 0, m.X_C0 + 0.01, 6.667, fc=PAPER, ec=BG_EDGE, lw=0.4, z=4.5)          # door opening
    rect(ax, m.X_H1 + 0.1, 0.04, m.X_H1 + 0.24, 6.6, fc=PAPER, ec=INK, lw=0.5, z=5)                # door leaf
    rect(ax, m.X_H1 + 0.06, 0.33, m.X_H1 + 0.28, 2.0, fc=RET, ec=RET, z=6)                         # 20 x 20 filter grille
    for z in (0.75, 1.5):
        ax.annotate("", xy=(m.X_C0 + 0.45, z), xytext=(m.X_H1 - 0.95, z), arrowprops=dict(arrowstyle="-|>", lw=0.7, color=RET, mutation_scale=5), zorder=9)
    zb, zt = 7.0 + 2 * IN, 7.0 + 10 * IN
    xs0, xs1 = TR_CX - TR_W / 2, TR_CX + TR_W / 2
    a0, a1 = m.AHU[0], m.AHU[2]
    rect(ax, xs1, zb, a0 + 0.1, zt, fc=SUP_F, ec=SUP, lw=0.7, z=7)                                 # 20 x 8 connection
    rect(ax, a0, STAND_H + AHU_H, a1, zt, fc=SUP_F, ec=SUP, lw=0.9, z=7.2)                         # plenum
    rect(ax, xs0, zb, xs1, zt, fc="#a9c9ec", ec=SUP, lw=1.2, z=8)
    line(ax, [(xs0, zb), (xs1, zt)], color=SUP, lw=0.4, z=8.5)
    line(ax, [(xs0, zt), (xs1, zb)], color=SUP, lw=0.4, z=8.5)
    rect(ax, a0, STAND_H, a1, STAND_H + AHU_H, fc=PAPER, ec=INK, lw=1.1, z=7)                      # air handler
    line(ax, [(a0, STAND_H + 1.5), (a1, STAND_H + 1.5)], lw=0.4, z=7.5)
    txt(ax, AH_CX, STAND_H + 2.9, "AHU-A\nblower", size=4.4, weight="bold")
    txt(ax, AH_CX, STAND_H + 0.75, "coil +\n5 kW strip", size=4.2)
    txt(ax, AH_CX, STAND_H + AHU_H + 0.75, "PLENUM", size=4.4, color=SUP, weight="bold")
    for x in (a0, a1 - 0.12):
        rect(ax, x, 0, x + 0.12, STAND_H, fc=BG_WALL, ec=INK, lw=0.4, z=7)                         # stand legs
    rect(ax, a0, STAND_H - 0.12, a1, STAND_H, fc=BG_WALL, ec=INK, lw=0.4, z=7)
    txt(ax, AH_CX, 0.95, "open\nreturn\nstand", size=4.2, color=RET)
    ax.add_patch(plt.Circle((DV_X, 7.0 + 6 * IN), 2 * IN, fc=EXH_F, ec=EXH, lw=0.9, zorder=8))      # dryer duct passing
    # line set and condensate
    xl = m.X_C0 + 0.22
    line(ax, [(a0, STAND_H + 0.9), (xl, STAND_H + 0.9), (xl, -0.7), (x0, -0.7)], color=REF, lw=1.1, ls=(0, (3, 1.6)), z=9)
    xc = a1 + 0.3
    line(ax, [(a1, STAND_H + 0.5), (xc, STAND_H + 0.5), (xc, STAND_H + 0.15), (xc + 0.2, STAND_H + 0.15), (xc + 0.2, STAND_H + 0.35)], color=CND, lw=1.0, z=9)
    ax.add_patch(plt.Circle((TSTAT[0] + 0.12, 5.0), 0.2, fc=PAPER, ec=HEAT, lw=0.9, zorder=9))
    # notes
    R = 26.95
    lead(ax, (DV_X, 7.0 + 6 * IN), (R, 7.5), "DRYER DUCT 4 in. passing in\nthe 7 in. space beside the plenum", EXH, size=4.2, weight="bold", ha="left")
    lead(ax, (a1, STAND_H + 3.3), (R, 5.9), "30 A, 240 V feed. The breaker in\nthe heater kit is the disconnect\n(if none: switch at the door)", INK, size=4.2, ha="left")
    lead(ax, (xc + 0.2, STAND_H + 0.3), (R, 3.9), "CONDENSATE 3/4 in.: trap,\noverflow shut-off switch, then\nthrough the wall to the washer\nbox. Outlet must be higher\nthan the box: no pump", CND, size=4.2, weight="bold", ha="left")
    lead(ax, (m.X_H1 + 0.28, 1.9), (R, 1.3), "R-1 FILTER GRILLE 20 x 20 in\nthe door, bottom 4 in. above\nthe floor. Gasket the door;\nseal the closet airtight", RET, size=4.2, weight="bold", ha="left")
    lead(ax, (xl, -0.7), (R, -0.75), "LINE SET to HP-A in the floor trusses", REF, size=4.2, weight="bold", ha="left")
    txt(ax, 21.4, 4.2, "30 in. CLEAR\nIN THE HALL\nFOR SERVICE", size=4.2)
    lead(ax, (TSTAT[0] + 0.3, 5.0), (20.6, 5.55), "T-STAT 5'-0\"", HEAT, size=4.2, weight="bold", ha="left")
    lead(ax, (22.75, (zb + zt) / 2), (21.9, 6.3), "20 x 8 ABOVE\nTHE DOOR", SUP, size=4.2, weight="bold", ha="center")
    dim(ax, (a0 - 0.28, 0), (a0 - 0.28, STAND_H), 0.0, "2'-0\"", size=4.2, ext=False)
    dim(ax, (m.X_C1 - 0.2, STAND_H), (m.X_C1 - 0.2, STAND_H + AHU_H), 0.0, "ABOUT 4'-0\"", size=4.2, ext=False, side=-1)
    dim(ax, (m.X_H0 + 0.4, 0), (m.X_H0 + 0.4, 7.0), 0.0, "7'-0\"", size=4.6, ext=False)
    txt(ax, 24.4, 8.85, "1-HOUR FLOOR/CEILING ASSEMBLY", size=4.6, color=GREY, weight="bold")
    return ax


def closet_plan(fig, bg, L, B):
    x0, x1, y0, y1, fpi = 19.55, 26.75, 24.25, 28.25, 2.0
    ax = plan_axes(fig, L, B, (x0, x1), (y0, y1), fpi)
    vt(bg, L, B + 2.2, "3  Air-handler closet plan", "1/2\" = 1'-0\" · both flats")
    unit_plan(ax, "bg", "A", furniture=False, labels=False, with_porch=False)
    for p in zone_polys():
        poly(ax, p, fc=ZONE_F, ec="none", z=7.6, alpha=0.4)
    draw_exhaust(ax)
    draw_supply(ax)
    draw_return(ax)
    draw_condensate(ax)
    ax.add_patch(plt.Circle(LS_DROP, 0.13, fc=PAPER, ec=REF, lw=1.0, zorder=12))
    draw_tstat(ax, r=0.16)
    for a in ax.patches + ax.lines:
        a.set_clip_on(True)
    txt(ax, AH_CX, AH_CY + 0.35, "AHU\n21 x 21", size=5.0, color=SUP, weight="bold", z=14, box=True)
    txt(ax, TR_CX, 25.0, "16 x 8", size=4.8, color=SUP, weight="bold", rot=90, z=14)
    txt(ax, TR_CX, 27.9, "10 x 8", size=4.6, color=SUP, weight="bold", rot=90, z=14)
    txt(ax, 23.15, AH_CY - 0.35, "20 x 8\nover door", size=4.4, color=SUP, weight="bold", z=14, rot=90)
    txt(ax, 20.72, AH_CY + 0.45, "30 x 30 in.\nservice\nspace", size=4.6, z=14)
    dim(ax, (m.X_C0, m.AH_Y1 + 0.02), (m.X_C1, m.AH_Y1 + 0.02), 0.42, size=4.8)
    dim(ax, (m.X_C1 + 0.4, m.AH_Y0), (m.X_C1 + 0.4, m.AH_Y1), 0.0, size=4.8, ext=False, side=-1)
    dim(ax, (m.X_C0, m.AHU[1] - 0.12), (m.AHU[0], m.AHU[1] - 0.12), 0.0, inch(m.AHU[0] - m.X_C0), size=4.2, ext=False, side=-1)
    dim(ax, (m.AHU[2], m.AHU[3] + 0.1), (m.X_C1, m.AHU[3] + 0.1), 0.0, inch(m.X_C1 - m.AHU[2]), size=4.2, ext=False)
    lead(ax, (DV_X, 24.75), (26.3, 24.45), "DRYER\n4 in.", EXH, size=4.2, weight="bold", ha="center")
    lead(ax, LS_DROP, (24.35, 24.5), "LINE SET\nDOWN", REF, size=4.2, weight="bold", ha="center")
    lead(ax, (m.AHU[2] - 0.3, 24.75), (25.35, 24.5), "COND.", CND, size=4.2, weight="bold", ha="center")
    lead(ax, (m.X_H1 - 0.1, AH_CY + 0.75), (22.2, 27.9), "R-1", RET, size=4.6, weight="bold", ha="center")
    return ax


def sheet_m201(pdf):
    lo, hi = 25 * m.net_area(), 30 * m.net_area()
    notes = [
        ("Duct sizing rule (preliminary)", [
            f"{TOTAL_CFM} cfm per flat = 2 tons x 400 cfm per ton.",
            "Each room gets its share by floor area.",
            "Round branches at about 0.08 in. w.g. per",
            "100 ft: 5 in. = 60 cfm, 6 in. = 100 cfm,",
            "7 in. = 140 cfm, 8 in. = 180 cfm.",
            f"Rectangular ducts: {RECT_FPM} fpm maximum.",
            "Confirm with ACCA Manual J, S and D.",
        ]),
        ("Ducts", [
            "Galvanized sheet metal, all inside the",
            "heated flat: no duct insulation needed",
            "(IECC R403.3.1). Mastic on every joint.",
            "Balancing damper at each take-off.",
            "Unit A: 8 in. deep ducts exactly fill the",
            "space under the rated ceiling. If hangers",
            "or wrap need room, use a 22 x 6 trunk",
            "and 6 in. deep flat-oval branches.",
        ]),
        ("Controls and sequence", [
            "One programmable heat-pump thermostat",
            "per flat, in the hall. Each tenant runs",
            "and pays for their own system.",
            "Heating: the heat pump runs first. The",
            f"{STRIP_KW} kW strip comes on only when the heat",
            "pump cannot hold the setting, or during",
            "defrost; locked out above 35 °F outdoors.",
            "Cooling: fan and compressor together.",
            "Overflow switch on the condensate line",
            "stops the unit before the pan spills.",
            "EF-2 runs all the time; other fans, the",
            "hood and the heaters are local.",
        ]),
    ]
    fig, bg = sheet("M-201", "AS NOTED", notes)
    section_hall(fig, bg, 0.6, 5.5)
    section_closet(fig, bg, 5.5, 5.5)
    closet_plan(fig, bg, 9.75, 7.35)
    bx, by = 9.75, 6.95
    bg.text(bx, by, "CLOSET NOTES", fontsize=6.6, fontweight="bold", color=INK, va="top")
    for i, ln in enumerate([
        "Closet 2'-10\" x 2'-6\" inside, door 2'-0\": buy a unit no more",
        "than 21 in. wide so it can be carried through the door.",
        "Supply plenum the size of the unit, from the unit to the",
        "ceiling; 20 x 8 take-off on the hall side, above the door.",
        "Return: R-1 in the door feeds the open stand. If the",
        "inspector does not accept the closet as the return path,",
        "box the stand in sheet metal out to the grille.",
        f"R-1 is {RA_TO_RANGE:.0f} ft from the range (10 ft min., IRC M1602.2).",
        "Line set and condensate: sleeve and seal the floor and",
        "wall holes. Low-voltage cable follows the line set.",
        "Unit B: same closet; ceiling 8'-1\", so 13 in. over the soffit line.",
        "TO CONFIRM: equipment model and its clearances; closet as",
        "the return path (above); Manual J for each flat.",
    ]):
        bg.text(bx, by - 0.2 - i * 0.142, ln, fontsize=5.3, color=INK, va="top")

    # ---- schedules ----
    X1, YT = 0.6, 4.75
    bg.text(X1, YT + 0.06, "EQUIPMENT SCHEDULE", fontsize=7.0, fontweight="bold", color=INK)
    eq = [["TAG", "SERVES", "EQUIPMENT", "CAPACITY", "ELECTRICAL (for E-201)"],
          ["HP-A", "Unit A", "Outdoor heat pump, side-discharge, inverter, 38 x 15 in.", f"{BTUH:,} Btu/h nominal (2 tons)", "about 20 A, 240 V, 1-phase"],
          ["HP-B", "Unit B", "Same as HP-A", "Same", "about 20 A, 240 V, 1-phase"],
          ["AHU-A", "Unit A", f"Vertical air handler 21 x 21 in., {STRIP_KW} kW strip heat", f"{TOTAL_CFM} cfm at 0.5 in. w.g.", "30 A, 240 V (with the strip)"],
          ["AHU-B", "Unit B", "Same as AHU-A", "Same", "30 A, 240 V (with the strip)"]]
    y = table(bg, X1, YT, [0.5, 0.5, 2.75, 1.5, 1.45], eq, fs=5.0, rh=0.19)
    bg.text(X1, y - 0.11, "Efficiency: not less than the current federal minimum for split heat pumps (14.3 SEER2, 7.5 HSPF2). A cold-climate rated model is",
            fontsize=5.0, color=INK, va="center")
    bg.text(X1, y - 0.25, "preferred. Breaker and wire sizes follow the nameplate of the model bought. Each unit is on its own flat's panel and meter.",
            fontsize=5.0, color=INK, va="center")
    y2 = y - 0.62
    bg.text(X1, y2 + 0.06, "FAN AND HEATER SCHEDULE (EF, RH and DV: one set per flat)", fontsize=7.0, fontweight="bold", color=INK)
    fans = [["TAG", "LOCATION", "DUTY", "DUCT AND RUN", "NOTES"],
            ["EF-1", "Bath 1 ceiling", f"{FAN_CFM} cfm", f"4 in., {ftin(EF_RUN['EF-1'])} to the west wall", "1.0 sone max., own switch"],
            ["EF-2", "Bath 2 ceiling", f"{VENT_CFM} cfm always, {FAN_CFM} boost", f"4 in., {ftin(EF_RUN['EF-2'])} to the rear wall", "0.3 sone, rated for continuous use"],
            ["EF-3", "Bath 3, over the tub", f"{FAN_CFM} cfm", f"4 in., {ftin(EF_RUN['EF-3'])} to the rear wall", "Listed for use over a tub, GFCI"],
            ["RH-1", "Over the range", "250 cfm max., 30 in. hood", f"6 in., {ftin(RH_RUN)} to the front wall", "Smooth metal duct, damper"],
            ["DV-1", "W/D closet", "Dryer exhaust", f"4 in. rigid, {DV_EQ:.0f} equivalent ft", "35 ft max. (IRC M1502.4.5)"],
            ["UH-1", "Utility room", "500 W wall heater", "none", "Set 45 °F; circuit CL, Unit A"],
            ["UH-2", "Stair, garage level", "1,500 W wall heater", "none", "Set 50 °F; circuit CL, Unit A"]]
    table(bg, X1, y2, [0.45, 1.15, 1.5, 1.9, 1.7], fans, fs=5.0, rh=0.19)

    X2 = 7.55
    bg.text(X2, YT + 0.06, f"AIR BALANCE, EACH FLAT ({TOTAL_CFM} cfm)", fontsize=7.0, fontweight="bold", color=INK)
    ret = {BR1: "T-1 12 x 8 over the door", BR2: "T-2 12 x 8 to the hall soffit", BR3: "T-3 12 x 8 through the wall", LIV: "open to the hall",
           BA1: "door undercut 1 in.", BA2: "door undercut 1 in.", BA3: "door undercut 1 in."}
    rows = [["ROOM", "AREA", "CFM", "REGISTER", "BRANCH DUCT", "RETURN PATH"]]
    for k in SUPPLIED:
        outs = [o for o in OUTLETS if o[1] == k]
        nm = k.title().replace(" / Kitchen", " + kitchen")
        if len(outs) == 1:
            o = outs[0]
            rows.append([nm, f"{AREA[k]:.0f} sf", str(CFM[k]), f"{o[0]}  {o[3]} {o[4]}", o[5], ret[k]])
        else:
            rows.append([nm, f"{AREA[k]:.0f} sf", str(CFM[k]), f"S-4 + S-5  14 x 6, {LIV_A} + {LIV_B}", "trunk end; 12 x 8", ret[k]])
    rows.append(["Hall, closets, walls", f"{m.net_area() - A_SUP:.0f} sf", "0", "none: return path", "", "R-1 20 x 20 filter grille"])
    rows.append(["TOTAL", f"{m.net_area():.0f} sf", str(sum(CFM.values())), "8 supply registers", "20 x 8 at the plenum", f"R-1: {TOTAL_CFM} cfm, 2 cfm per sq in."])
    yb = table(bg, X2, YT, [1.05, 0.45, 0.35, 1.6, 1.0, 1.6], rows, fs=5.0, rh=0.19)
    bg.text(X2, yb - 0.22, "ROUGH LOAD CHECK (rule of thumb only, not a load calculation)", fontsize=7.0, fontweight="bold", color=INK)
    for i, ln in enumerate([
        f"25 to 30 Btu/h per sf x {m.net_area():.0f} sf flat = about {round(lo, -3):,.0f} to {round(hi, -3):,.0f} Btu/h, so a 2-ton ({BTUH:,} Btu/h) unit is the",
        f"expected size for each flat. The {STRIP_KW} kW strip adds {STRIP_KW * 3412:,} Btu/h for the coldest hours and for defrost.",
        "ACCA Manual J is REQUIRED before equipment is ordered (IRC M1401.3). Unit A (over the garage and on",
        "a slab) and Unit B (under the roof) will not have the same load; do one calculation for each.",
        "Trunk check: 16 x 8 at %d cfm = %d fpm; 20 x 8 at %d cfm = %d fpm; 10 x 8 at %d cfm = %d fpm (%d max.)."
        % (Q_S, fpm(Q_S, 16, 8), TOTAL_CFM, fpm(TOTAL_CFM, 20, 8), Q_N, fpm(Q_N, 10, 8), RECT_FPM),
    ]):
        bg.text(X2, yb - 0.42 - i * 0.15, ln, fontsize=5.2, color=INK, va="center")
    save(fig, "M-201", pdf)


SHEETS = [("M-101", sheet_m101), ("M-102", sheet_m102), ("M-103", sheet_m103), ("M-201", sheet_m201)]
