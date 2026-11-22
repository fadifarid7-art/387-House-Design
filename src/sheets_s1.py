"""Structural sheets S-001 and S-101..S-104 (Rev E): notes, foundations, retaining walls, slabs, steel.

Every size here is a PRELIMINARY assumption for pricing and coordination, to be designed and sealed by a
WV structural engineer. The geometry (where each wall, footing, slab edge and post is) comes from model.py.
Assumptions that the model does not hold are collected under "local preliminary assumptions" below.
"""
import math
import textwrap

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from common import *  # noqa: F401,F403
import model as m
from plans import *  # noqa: F401,F403
from index import TITLE

IN = m.IN
STEEL = BLUE
SOIL = "#efe9e1"
FILL = "#e6dccb"
STONE = "#dcdfe3"
TINT = "#eef2f6"
FTGC = "#f3ecdd"
WOODC = "#ead9b8"
RED = ACCENT

# ----------------------------------------------------------------------------
# local preliminary assumptions (not in model.py; reported to the design lead)
# ----------------------------------------------------------------------------
TOE = 1.0                                   # F1 toe, toward the garage
HEEL = m.FTG_W - m.CONC - TOE               # F1 heel, toward the retained soil (2'-0")
EL_F1_BOT = m.EL_FTG_TOP - m.FTG_T          # bottom of the retaining-wall footing
STEM_T, STEM_FW, STEM_FT = 8 * IN, 20 * IN, 10 * IN      # stem wall and its footing F4
INT_FW, INT_FT = 16 * IN, 8 * IN            # footing F3 under the 8 in. garage-level walls
PAD, PAD_T = 4.0, 14 * IN                   # pad footing F2 under the steel post
BRG_PAD, BRG_PAD_T = 3.0, 12 * IN           # local pad under the east bearing of B1
SILL = 1.5 * IN                             # treated sill plate / nailer
EL_BRG = m.EL_B1_TOP                        # floor-truss bearing level (underside of the 20 in. trusses)
EL_TOC = EL_BRG - SILL                      # top of concrete under the sill plate
FROST = 3.0
BACKFILL = 4.0                              # assumed width of the backfilled over-dig behind the garage walls
SLAB_G, STONE_G = 6 * IN, 6 * IN            # garage slab
SLAB_A, STONE_A, INSUL_A = 5 * IN, 4 * IN, 2 * IN        # Unit A slab on grade
EL_UPSTAND = m.EL_A - SLAB_A                # top of the 6 in. upstand on the garage rear wall
DRAIN_OFF = HEEL + 0.75                     # French-drain centre line, ft outside the wall face
Y_TD = m.YF - 0.6                           # trench drain centre line (brief)
Y_SLAB_S = Y_TD - 0.5                       # south edge of the garage slab = joint to the apron
THICK_W, THICK_D = 2.0, 12 * IN             # thickened slab edge at the opening
EL_TD = m.EL_GAR - (m.Y_GR_I - Y_TD) / 8 / 12            # slab at the trench drain (1/8 in. per ft from the rear wall)
BEAM_X0, BEAM_X1 = m.OPEN[0] - 0.5, m.OPEN[1] + m.CMU    # ends of B1: 6 in. on the pier, 8 in. on the lobby wall
W14 = dict(d=13.98 * IN, bf=6.745 * IN, tf=0.455 * IN, tw=0.285 * IN, plf=34.0)
HSS_PLF = 27.48
EL_SOFFIT = m.EL_B1_TOP - m.B1_DEPTH
GROUT, PLATE = 1.0 * IN, 0.75 * IN
POST_LEN = (EL_SOFFIT - PLATE) - (m.EL_FTG_TOP + GROUT + PLATE)

_cw, _sw = math.cos(WEST_LEAN), math.sin(WEST_LEAN)
_th = math.atan(abs(REAR_SLOPE))
_cr, _sr = math.cos(_th), math.sin(_th)
SW, SE, NE, NWG = m.OUT_L
NWU = m.OUT_U[3]
LW, LN, LE = math.dist(SW, NWG), math.dist(NWG, NE), math.dist(NE, SE)
L_STEM_W, L_STEM_R = math.dist(NWG, NWU), math.dist(NWU, NE)
DASH = (0, (5, 3))


def wx(y, off=0.0):
    """x of a line parallel to the west wall face, `off` ft outside it (negative = inside)."""
    return m.xw_o(y) - off / _cw


def strip(p0, p1, a, b, ext=0.0):
    """Quad along p0->p1 between offsets a and b, measured to the LEFT of the direction."""
    L = math.dist(p0, p1)
    ux, uy = (p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L
    nx, ny = -uy, ux
    q0 = (p0[0] - ux * ext, p0[1] - uy * ext)
    q1 = (p1[0] + ux * ext, p1[1] + uy * ext)
    return Polygon([(q0[0] + nx * a, q0[1] + ny * a), (q1[0] + nx * a, q1[1] + ny * a),
                    (q1[0] + nx * b, q1[1] + ny * b), (q0[0] + nx * b, q0[1] + ny * b)])


def _geometry():
    g = {}
    yb, yt = m.YF - 1.5, m.Y_GR_O + HEEL
    outer = Polygon([(wx(yb, HEEL), yb), (m.XE + HEEL, yb), (m.XE + HEEL, yt), (wx(yt, HEEL), yt)])
    yi = m.Y_GR_I - TOE
    inner = Polygon([(wx(yb - 1, -(m.CONC + TOE)), yb - 1), (m.XE_GI - TOE, yb - 1), (m.XE_GI - TOE, yi),
                     (wx(yi, -(m.CONC + TOE)), yi)])
    pier_f = box(-5, yb, m.OPEN[0] + 1.0, m.YF + m.CONC + 1.5).intersection(outer)
    g["F1"] = outer.difference(inner).union(pier_f)
    p = (INT_FW - m.CMU) / 2
    g["F3"] = unary_union([box(m.GAR_X1 - p, m.YF - p, m.XE, m.YF + m.CMU + p),
                           box(m.GAR_X1 - p, m.YF - p, m.SHAFT_X0 + p, m.Y_GR_I),
                           box(m.SHAFT_X0, m.SHAFT_U[3] - p, m.XE_GI, m.UTIL[2] + p)]).difference(g["F1"])
    g["F2"] = box(m.COL_X[1] - PAD / 2, m.B1_Y - PAD / 2, m.COL_X[1] + PAD / 2, m.B1_Y + PAD / 2)
    g["F2E"] = box(m.COL_X[2] - BRG_PAD / 2, m.B1_Y - BRG_PAD / 2, m.COL_X[2] + BRG_PAD / 2, m.B1_Y + BRG_PAD / 2)
    inside = Polygon([(m.xw_gi(m.YF - 1), m.YF - 1), (m.XE_GI, m.YF - 1), (m.XE_GI, m.Y_GR_I), (m.xw_gi(m.Y_GR_I), m.Y_GR_I)])
    pier = Polygon([(m.xw_o(m.YF), m.YF), (m.OPEN[0], m.YF), (m.OPEN[0], m.YF + m.CONC), (m.xw_gi(m.YF + m.CONC), m.YF + m.CONC)])
    g["PIER"] = pier
    g["RW"] = Polygon(m.OUT_L).difference(inside).union(pier)
    doors = unary_union([box(m.ENTRY[0], m.YF - 0.1, m.ENTRY[1], m.YF + m.CMU + 0.1),
                         box(m.GAR_X1 - 0.1, m.UTIL_DOOR[0], m.SHAFT_X0 + 0.1, m.UTIL_DOOR[1])])
    g["IW"] = unary_union([box(m.GAR_X1, m.YF, m.XE_GI, m.YF + m.CMU), box(m.GAR_X1, m.YF, m.SHAFT_X0, m.Y_GR_I),
                           box(m.SHAFT_X0, m.SHAFT_U[3], m.XE_GI, m.UTIL[2])]).difference(doors).difference(g["RW"])
    sog = Polygon(m.SOG)
    walls = unary_union([strip(NWG, NWU, -STEM_T, 0, 3), strip(NWU, NE, -STEM_T, 0, 3)])
    g["STEM"] = walls.intersection(sog)
    pf = (STEM_FW - STEM_T) / 2
    g["F4"] = unary_union([strip(NWG, NWU, -(STEM_T + pf), pf, 3), strip(NWU, NE, -(STEM_T + pf), pf, 3)]) \
        .intersection(sog.buffer(pf, join_style=2)).intersection(box(-50, m.Y_GR_O, m.XE + pf, 100))
    g["SOG_NET"] = sog.difference(walls)
    gar = Polygon([(m.xw_gi(m.YF), m.YF), (m.GAR_X1, m.YF), (m.GAR_X1, m.Y_GR_I), (m.xw_gi(m.Y_GR_I), m.Y_GR_I)]).difference(pier)
    g["GAR"] = gar.union(box(m.OPEN[0], Y_SLAB_S, m.OPEN[1], m.YF))
    g["LOBBY"] = box(m.SHAFT_L[0], m.SHAFT_L[2], m.SHAFT_L[1], m.SHAFT_L[3])
    g["UTIL"] = box(m.UTIL[0], m.UTIL[2], m.UTIL[1], m.UTIL[3])
    return g


G = _geometry()

# French drain: beside the footing heel, west -> north -> east, then solid pipe to the outlet
DR = [(wx(m.YF, DRAIN_OFF), m.YF), (wx(m.Y_GR_O + DRAIN_OFF, DRAIN_OFF), m.Y_GR_O + DRAIN_OFF),
      (m.XE + DRAIN_OFF, m.Y_GR_O + DRAIN_OFF), (m.XE + DRAIN_OFF, m.YF), m.DRAIN_OUT]
DR_SEG = [math.dist(a, b) for a, b in zip(DR[:-1], DR[1:])]
DR_STA = [sum(DR_SEG[:i]) for i in range(5)]
DR_LEN = DR_STA[-1]
DR_FALL = m.EL_DRAIN_HI - m.EL_DRAIN_OUT
DR_SLOPE = DR_FALL / DR_LEN
DR_INV = [m.EL_DRAIN_HI - DR_SLOPE * s for s in DR_STA]
DR_NAMES = ["CO-1", "CO-2", "CO-3", "CO-4", "OUTLET"]


def ground_w(s):
    t = s / LW
    return elev(SW[0] + (NWG[0] - SW[0]) * t - 0.5 * _cw, SW[1] + (NWG[1] - SW[1]) * t + 0.5 * _sw)


def ground_n(s):
    return elev(NWG[0] + s, m.Y_GR_O + 0.5)


def ground_e(s):
    return elev(m.XE + 0.5, m.Y_GR_O - s)


def stem_top(x, y):
    return max(m.EL_A, elev(x, y) + 8 * IN)


def stem_bot(x, y):
    return min(elev(x, y) - FROST, m.EL_A - 2.0)


# ----------------------------------------------------------------------------
# drafting helpers
# ----------------------------------------------------------------------------
def two_line(title, n=27):
    if len(title) <= n:
        return title
    words, best = title.split(" "), None
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        if best is None or max(len(a), len(b)) < max(len(best[0]), len(best[1])):
            best = (a, b)
    return best[0] + "\n" + best[1]


def tbn(*blocks, n=45):
    """Title-block notes: wrap each paragraph and warn when the column would run into the stamp."""
    out = []
    for head, *paras in blocks:
        lines = []
        for p in paras:
            lines += textwrap.wrap(p, n)
        out.append((head, lines))
    used = sum(0.31 + 0.183 * len(ls) for _, ls in out)
    if used > 5.82:
        print(f"WARNING: title-block notes too long ({used:.2f} in. of 5.82)")
    return out


def spoly(ax, g, **kw):
    for p in getattr(g, "geoms", [g]):
        if p.geom_type == "Polygon" and not p.is_empty:
            poly(ax, list(p.exterior.coords)[:-1], **kw)


def lead(ax, p, q, s, size=4.8, ha="left", va="center", color=INK, weight="normal", dot=True, box=True):
    line(ax, [p, q], lw=0.3, color=color, z=10)
    if dot:
        ax.plot([p[0]], [p[1]], marker="o", ms=1.4, color=color, zorder=10)
    g = 0.03 * ax.fpi * (1 if ha == "left" else -1 if ha == "right" else 0)
    txt(ax, q[0] + g, q[1], s, size=size, ha=ha, va=va, color=color, weight=weight, box=box, z=11)


def knote(ax, p, q, n):
    line(ax, [p, q], lw=0.3, z=10)
    ax.plot([p[0]], [p[1]], marker="o", ms=1.4, color=INK, zorder=10)
    ax.add_patch(plt.Circle(q, 0.085 * ax.fpi, fc=PAPER, ec=INK, lw=0.6, zorder=11))
    txt(ax, q[0], q[1], str(n), size=5.0, weight="bold", z=12)


def vtitle(bg, x, y, tag, title, sub):
    bg.text(x, y, f"{tag}   {title.upper()}", fontsize=8.0, fontweight="bold", color=INK, va="center")
    bg.text(x, y - 0.17, sub, fontsize=5.6, color=GREY, va="center")


def eltag(ax, x, y, s, ha="left", size=4.8, color=INK, w=None):
    w = 0.12 * ax.fpi if w is None else w
    d = 1 if ha == "left" else -1
    line(ax, [(x, y), (x + d * w, y)], lw=0.5, color=color, z=10)
    txt(ax, x + d * w * 1.25, y, s, size=size, ha=ha, color=color, z=11, box=True)


def frame(fig, view, left, bottom, fpi=FPI, lot=True):
    ax = plan_axes(fig, left, bottom, view[0], view[1], fpi)
    if lot:
        line(ax, [LOT_NW, LOT_SW, LOT_SE, LOT_NE, LOT_NW], color=ACCENT, lw=1.0, ls=(0, (9, 2.5, 1.5, 2.5)), z=5.25)
    return ax


def arrow(ax, p, q, color=INK, lw=0.6, style="-|>"):
    ax.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle=style, lw=lw, color=color, shrinkA=0, shrinkB=0), zorder=10)


def cut_mark(ax, p, q, tag, flip=1):
    """Section cut line p->q with a tag bubble at each end."""
    line(ax, [p, q], lw=0.9, ls=(0, (8, 2, 2, 2)), z=11)
    for e in (p, q):
        ax.add_patch(plt.Circle(e, 0.1 * ax.fpi, fc=PAPER, ec=INK, lw=0.7, zorder=12))
        txt(ax, e[0], e[1], tag, size=4.6, weight="bold", z=13)


def rebar_dots(ax, pts, r):
    for (x, y) in pts:
        ax.add_patch(plt.Circle((x, y), r, fc=RED, ec=RED, lw=0.2, zorder=8))


def break_line(ax, p, q, color=GREY):
    line(ax, [p, q], lw=0.5, color=color, ls=(0, (6, 2, 1, 2)), z=9)


# ----------------------------------------------------------------------------
# S-001
# ----------------------------------------------------------------------------
def _para(s, n=74):
    return textwrap.fill(s, n)


def _item(s, n=74):
    return textwrap.fill(s, n, initial_indent="· ", subsequent_indent="  ")


def sheet_s001(pdf):
    notes = tbn(
        ("Read this first",
         "Every size on the S sheets is a PRELIMINARY assumption for pricing and coordination. Nothing here has been "
         "calculated by an engineer."),
        ("Before the engineer can design",
         "1. Boundary and topographic survey.",
         "2. Soil report: bearing, lateral earth pressure, groundwater, rock depth, old mine workings.",
         "3. Foundations of 441 and 442 Baird and 386 Forest located (for shoring, C-104).",
         "4. Truss supplier's reactions on B1 and on the walls."),
        ("What is real",
         "Positions and lengths of walls, footings, slab edges and the post come from the dimensioned model and "
         "agree with the A sheets."),
        ("Sheets",
         "S-101 foundations. S-102 retaining walls and drains. S-103 slabs. S-104 steel. S-201 to S-301 framing."),
    )
    fig, bg = new_sheet("S-001", two_line(TITLE["S-001"]), "No scale", notes)
    hw = m.OPEN[0] - m.xw_o(m.YF)
    lobby = m.XE - m.OPEN[1]
    rg = [ground_w(0) - m.EL_GAR, ground_w(LW) - m.EL_GAR, ground_n(LN) - m.EL_GAR, ground_e(LE) - m.EL_GAR]
    c1 = [
        ("Status of these sheets", [
            _para("These five sheets are a preliminary structural layout for pricing and for coordinating the trades. "
                  "Every member size, bar size and spacing is an assumption, not a design. A structural engineer "
                  "licensed in West Virginia designs and seals the structure before permit and before anything is "
                  "ordered or built. Where a sheet says PRELIM., expect the engineer to change it."),
            _para("The geometry is real: where each wall, footing, slab edge and post sits, and how long it is, is "
                  "read from the dimensioned building model and is the same on every sheet of the set. Dimensions "
                  "are rounded to the nearest inch, so a string can differ from its overall by 1 in."),
        ]),
        ("Codes", [
            _para("WV State Building Code: 2018 IRC (two-family dwelling). Work outside the IRC tables is engineered "
                  "to 2018 IBC / ASCE 7-16, ACI 318-14, AISC 360-16 and NDS 2018: the retaining walls, beam B1 and "
                  "its post, the open garage front, the cantilevered porches. Confirm editions and local design "
                  "criteria with City of Morgantown Code Enforcement."),
        ]),
        ("Design loads (engineer to confirm)", [
            _item("Roof: ground snow 30 psf; roof dead load 15 psf."),
            _item("Floors, Units A and B: 40 psf live + 15 psf dead. The truss supplier adds tub, tile and "
                  "partition allowances."),
            _item("Porches: 60 psf live."),
            _item("Garage slab: passenger vehicles only (40 psf or a 3,000 lb wheel load)."),
            _item("Wind: 115 mph. Exposure to confirm (hillside site)."),
            _item("Seismic: design category B."),
            _item("Frost depth: 36 in."),
            _item("Soil bearing: 2,000 psf ASSUMED until the soil report."),
            _item("Lateral earth pressure: PENDING the soil report. The garage walls are held at the top, so they "
                  "see at-rest pressure; for pricing only assume 60 pcf equivalent fluid, plus surcharge from the "
                  "Unit A slab on grade behind the rear wall and from the neighbours' houses (about 1 ft beyond "
                  "the side lot lines, so about 6 ft from the walls)."),
            _item("Water: the walls are drained by the gravity French drain (S-102), so no water pressure is "
                  "assumed. There is no sump pump and none may be added."),
        ]),
        ("Materials (preliminary)", [
            _item("Concrete, walls and footings: 4,000 psi at 28 days."),
            _item("Concrete, exterior flatwork and the open garage slab (weather and road salt): 4,500 psi, "
                  "air-entrained 5 to 7 %, water/cement ratio 0.45 max."),
            _item("Concrete, Unit A slab on grade (indoors): 4,000 psi, no air entrainment under a trowel finish."),
            _item("Reinforcing: ASTM A615 Grade 60. Cover: 3 in. cast against earth, 2 in. formed faces against "
                  "earth or weather, 1 1/2 in. indoors."),
            _item("Steel: W shapes ASTM A992; HSS ASTM A500 Gr. C; plates A36; anchor rods F1554 Gr. 36; "
                  "bolts A325; E70 welds; non-shrink grout under plates."),
            _item("Framing: SPF or SYP No. 2 studs and plates; preservative-treated sill plates on concrete, "
                  "hot-dip galvanised fasteners in treated wood."),
            _item("Floor trusses: engineered open-web trusses, 20 in. deep under Unit A and 24 in. under Unit B. "
                  "Roof trusses: 4:12 common trusses at 24 in. All by a truss supplier, with SEALED truss "
                  "drawings and a layout."),
        ]),
    ]
    c2 = [
        ("Load path in plain words", [
            _item("Roof trusses and both floors span front to back (north-south). No partition inside the flats "
                  "carries load."),
            _item("FRONT LINE. The roof and the Unit B floor come down the 2x6 front walls. With the front end of "
                  "the Unit A floor they all land on steel beam B1 over the garage opening. B1 sits on the west "
                  "concrete return pier, one HSS post and the lobby wall corner (S-104)."),
            _item("REAR LINE. The roof and the Unit B floor come down the skewed rear wall of Unit A onto the "
                  "8 in. concrete stem wall and its footing (S-101)."),
            _item("Unit A's floor over the garage spans from B1 to the garage rear retaining wall, which carries "
                  "it down to its footing. North of that wall Unit A's floor is a slab on grade (S-103)."),
            _item("The east and west walls carry their own weight and the roof gable ends, down onto the east "
                  "and west retaining walls and the west stem wall."),
            _item("Sideways load (wind, earthquake): roof and floor sheathing carry it to the sheathed shear "
                  "walls of the flats (S-204) and, at garage level, into the concrete walls."),
            _item("Earth pressure: each garage wall spans from its footing up to the Unit A floor, which props "
                  "its top. The east and west walls push against each other through the floor. The rear wall "
                  "has no wall opposite it (the front is open), so the floor must carry its push sideways into "
                  "the east and west walls."),
        ]),
        ("Critical engineered items", [
            _item(f"RETAINING WALLS. Retained height from the garage slab: west {ftin(rg[0])} to {ftin(rg[1])}, "
                  f"rear {ftin(rg[1])} to {ftin(rg[2])}, east {ftin(rg[2])} down to {ftin(rg[3])}. They are propped "
                  "by the Unit A floor diaphragm and must be braced until that floor is framed, sheathed and "
                  "anchored. No backfill above half height before then, unless the engineer designs them as "
                  "cantilevers (bigger footings). The rear wall's unbalanced push is the hard part."),
            _item(f"BEAM B1, ITS POST AND BEARINGS. About 2.5 kips per ft from three levels (S-104). The post "
                  "load is about 32 to 43 kips; the 4'-0\" pad carries 32 kips at 2,000 psf, so expect it to grow."),
            _item(f"OPEN GARAGE FRONT. Only the {ftin(hw)} concrete return pier (west) and the 8 in. lobby front "
                  f"wall (east, {ftin(lobby)} long with a 3'-0\" door in it) stand in that wall line to resist "
                  "sideways load. The engineer checks them as shear piers or calls for a steel moment frame "
                  "(B1 plus posts) instead."),
            _item("CANTILEVERED PORCHES. Units A and B, 4'-0\" past the front wall, 60 psf: back-span, uplift at "
                  "the rear bearing, guard-post loads."),
            _item("LONG FLOOR TRUSSES. Unit B: 24 in. deep, clear span 20'-0\" to 30'-9\". Stiffness (L/480 live "
                  "or better), vibration and bearing govern. They must not lean on Unit A's partitions."),
            _item(f"FROST IN AN OPEN GARAGE. As modelled, the bottom of the wall footings is EL {EL_F1_BOT:.2f}, "
                  f"only {ftin(m.EL_GAR - EL_F1_BOT)} below the slab. The garage is open and unheated and the "
                  "frost depth is 36 in. The engineer confirms frost protection, above all along the open "
                  "front (pier, lobby front wall, post pad, slab edge). Going deeper is limited by the gravity "
                  f"drain outlet at EL {m.EL_DRAIN_OUT:.1f}."),
            _item("EXCAVATION beside three neighbours: shoring by a specialist engineer (C-104)."),
        ]),
    ]
    c3 = [
        ("Bearing level: decide before forming", [
            _para(f"The model puts the top of beam B1 at EL {m.EL_B1_TOP:.2f}, which is the underside of the 20 in. "
                  "floor trusses. The 1 1/2 in. treated sill plate on the concrete walls and the nailer on B1 need "
                  f"that 1 1/2 in. These sheets set the top of concrete at EL {EL_TOC:.2f} so the trusses bear at "
                  f"EL {EL_BRG:.2f}. B1 must drop the same 1 1/2 in. (clear height under it becomes "
                  f"{ftin(m.OPEN_CLEAR_H - SILL)}) or the nailer must go. Engineer, architect and truss supplier "
                  "settle this before shop drawings."),
        ]),
        ("Sequence that matters", [
            _item("1. Shoring and excavation (C-104)."),
            _item("2. Footings on subgrade approved by the soil engineer."),
            _item("3. Garage walls; waterproofing, drainage board and French drain inspected and photographed "
                  "before any backfill."),
            _item("4. Garage slab, steel beam B1 and post."),
            _item("5. Unit A floor over the garage framed, sheathed and anchored to the walls."),
            _item("6. Backfill in lifts. Not above half height before step 5."),
            _item("7. Stem walls and the Unit A slab on grade, on compacted backfill and undisturbed ground."),
            _item("8. Wall framing, Unit B floor, roof."),
        ]),
        ("Special inspections and tests to expect", [
            _item("Footing subgrade (soil engineer) before each footing pour."),
            _item("Reinforcing, embeds and anchor rods before each pour."),
            _item("Concrete: cylinders, slump and air content."),
            _item("Waterproofing and drains before backfill; backfill compaction by lift."),
            _item("Steel: mill certificates, bolting, any field welds, grout under plates."),
            _item("Truss bracing and bearing per the sealed truss drawings; shear-wall nailing and hold-downs."),
        ]),
        ("Submittals before ordering", [
            _item("Survey and soil report (owner)."),
            _item("Sealed shoring design."),
            _item("Concrete mix designs; reinforcing shop drawings."),
            _item("Waterproofing, drainage board, drain pipe and fabric product data."),
            _item("Structural steel shop drawings (S-104)."),
            _item("Sealed floor and roof truss drawings with layout and reactions."),
        ]),
        ("Preliminary member list", [
            _item(f"F1 retaining-wall footing {ftin(m.FTG_W)} x 14 in.; F2 post pad {ftin(PAD)} square x 14 in.; "
                  "F3 16 x 8 in.; F4 stem-wall footing 20 x 10 in."),
            _item("Garage walls 12 in. concrete; lobby, stair and utility walls 8 in.; stem walls 8 in."),
            _item("B1 W14x34; post HSS 6x6x3/8."),
            _item("Garage slab 6 in.; Unit A slab on grade 5 in."),
        ]),
    ]
    cols = [c1, c2, c3]
    fs, lh = 6.2, 0.152
    for i, c in enumerate(cols):
        h = sum(lh * 1.5 + sum(lh * (ln.count("\n") + 1) + 0.04 for ln in lines) + lh * 0.9 for _, lines in c)
        if h > 9.3:
            print(f"WARNING: S-001 column {i + 1} is {h:.2f} in. tall (9.3 available)")
    bg.text(MARGIN + 0.3, SHEET_H - MARGIN - 0.33, "STRUCTURAL NOTES AND DESIGN CRITERIA", fontsize=12, fontweight="bold", va="center")
    bg.text(MARGIN + 0.3, SHEET_H - MARGIN - 0.56, "Preliminary sizes for pricing and coordination. To be designed and sealed by a structural engineer licensed in West Virginia.",
            fontsize=6.6, color=ACCENT, va="center")
    w = text_columns(bg, cols, top=SHEET_H - MARGIN - 0.82, fs=fs, lh=lh)
    for i in (1, 2):
        x = MARGIN + 0.3 + i * w - 0.13
        bg.plot([x, x], [MARGIN + 0.25, SHEET_H - MARGIN - 0.8], color=LIGHT, lw=0.5)
    save(fig, "S-001", pdf)


# ----------------------------------------------------------------------------
# S-101
# ----------------------------------------------------------------------------
def draw_foundation(ax, footings=True, dims=False):
    """Concrete walls (cut) and footing outlines, used on S-101 and as the base of other plans."""
    if footings:
        for k in ("F1", "F3", "F4", "F2", "F2E"):
            spoly(ax, G[k], fc=FTGC, ec="none", z=2.4, alpha=0.9)
            spoly(ax, G[k], fc="none", ec=INK, lw=0.6, z=6.6, ls=DASH)
    spoly(ax, G["RW"], fc=CONC, ec=INK, lw=0.9, z=6)
    spoly(ax, G["IW"], fc="#c3c7cc", ec=INK, lw=0.7, z=6)
    spoly(ax, G["STEM"], fc=CONC, ec=INK, lw=0.8, z=6)
    cx = m.COL_X[1]
    rect(ax, cx - 0.25, m.B1_Y - 0.25, cx + 0.25, m.B1_Y + 0.25, fc=STEEL, ec=INK, lw=0.5, z=8)


def drain_plan(ax, lw=0.8, labels=False, size=4.4):
    line(ax, DR[:4], color=BLUE, lw=lw, ls=(0, (4, 2)), z=7)
    line(ax, DR[3:], color=BLUE, lw=lw, z=7)
    r = 0.07 * ax.fpi
    for i, (x, y) in enumerate(DR[:4]):
        ax.add_patch(plt.Circle((x, y), r, fc=PAPER, ec=BLUE, lw=0.8, zorder=9))
    ox, oy = DR[4]
    poly(ax, [(ox - r, oy + r * 0.6), (ox + r, oy + r * 0.6), (ox, oy - r * 1.2)], fc=BLUE, ec=BLUE, z=9)


def sheet_s101(pdf):
    pts = dict(nw=NWU, mid=((NWU[0] + NE[0]) / 2, (NWU[1] + NE[1]) / 2), ne=NE, nwg=NWG)
    gnd = {k: elev(*p) for k, p in pts.items()}
    top = {k: stem_top(*p) for k, p in pts.items()}
    bot = {k: stem_bot(*p) for k, p in pts.items()}
    vol = lambda a, t: a * t / 27.0
    q_f1, q_f3, q_f4 = vol(G["F1"].area, m.FTG_T), vol(G["F3"].area, INT_FT), vol(G["F4"].area, STEM_FT)
    q_rw = vol(G["RW"].area, EL_TOC - m.EL_FTG_TOP)
    notes = tbn(
        ("Preliminary",
         "Sizes are assumptions for pricing and coordination; a WV structural engineer designs and seals them. "
         "Positions and lengths are from the model."),
        ("Footing schedule (prelim.)",
         f"F1 garage retaining walls and west pier: {ftin(m.FTG_W)} x 14 in., toe {ftin(TOE)} inside, heel {ftin(HEEL)} "
         f"toward the soil. Top EL {m.EL_FTG_TOP:.2f}.",
         f"F2 pad under the steel post: {ftin(PAD)} x {ftin(PAD)} x 14 in. Top EL {m.EL_FTG_TOP:.2f}. "
         f"Similar {ftin(BRG_PAD)} pad under the east bearing of B1.",
         f"F3 under 8 in. lobby, stair and utility walls: 16 x 8 in. Top EL {m.EL_FTG_TOP:.2f}.",
         "F4 under 8 in. stem walls: 20 x 10 in., bottom 36 in. min. below finish grade and at least 2'-0\" below "
         "the Unit A slab."),
        ("Stem walls",
         "Top of wall is 8 in. above finish grade and never below the Unit A floor. Elevations shown use existing "
         "ground (LiDAR); adjust to the C-105 finish grades.",
         "Near the garage walls the stem footing must not sit on backfill: step it down or span it (engineer)."),
        ("Concrete, approx.",
         f"F1 {q_f1:.0f} cy, F3 {q_f3:.1f} cy, F4 {q_f4:.1f} cy, garage walls to EL {EL_TOC:.2f} {q_rw:.0f} cy. "
         "Stem walls vary with grade."),
    )
    fig, bg = new_sheet("S-101", two_line(TITLE["S-101"]), "3/16\" = 1'-0\"", notes)
    view = ((-7.0, 56.0), (-7.5, 44.0))
    left = MARGIN + (SHEET_W - 2 * MARGIN - TB_W - (view[0][1] - view[0][0]) / FPI) / 2
    ax = frame(fig, view, left, 0.55)
    site_work(ax, bg=True)
    lower_plan(ax, "bg", cars=False)
    poly(ax, m.SOG, fc="#faf7f0", ec="none", z=2)
    draw_foundation(ax)
    # backfill zone behind the garage walls, where stem footings may not bear
    zone = Polygon(m.OUT_L).buffer(BACKFILL, join_style=2).intersection(box(-50, m.YF, 100, 100))
    spoly(ax, zone, fc="none", ec=EARTH, lw=0.5, z=5.4, ls=(0, (2, 2)))
    # stepped footing marks along the stem walls inside the backfill zone
    xs = NE[0] - BACKFILL / abs(REAR_SLOPE)
    for i in range(1, 4):
        x = NE[0] - (NE[0] - xs) * i / 3.5
        y = m.yr_o(x)
        a = (x - _sr * 0.75, y - _cr * 0.75 - 0.35)
        b = (x + _sr * 0.75, y + _cr * 0.75 - 0.35)
        line(ax, [a, b], lw=1.3, color=RED, z=9)
    yz = m.Y_GR_O + 2.2
    line(ax, [(wx(yz, 0.6), yz + 0.07), (wx(yz, -1.4), yz - 0.16)], lw=1.3, color=RED, z=9)
    drain_plan(ax, lw=0.7)

    # ---- dimensions: west side
    dim(ax, SW, NWG, 7.4, f"{ftin(LW)}  GARAGE WEST WALL", size=5.2)
    dim(ax, NWG, NWU, 7.4, f"{ftin(L_STEM_W)}  STEM WALL", size=5.2)
    f = (SW[0] - (m.SB_SIDE + m.M) * _cw, SW[1] + (m.SB_SIDE + m.M) * _sw)
    dim(ax, f, SW, 0, ftin(m.SB_SIDE + m.M), ext=False, size=4.8, color=RED, side=-1)
    f = (NWU[0] - (m.SB_SIDE + m.M) * _cw, NWU[1] + (m.SB_SIDE + m.M) * _sw)
    dim(ax, f, NWU, 0, ftin(m.SB_SIDE + m.M), ext=False, size=4.8, color=RED)
    # rear
    dim(ax, NWU, NE, 2.5, f"{ftin(L_STEM_R)}  REAR STEM WALL, 8 in., ALONG THE SKEW", size=5.2)
    for c in (NWU, NE):
        f = (c[0] + (m.SB_REAR + m.M) * _sr, c[1] + (m.SB_REAR + m.M) * _cr)
        dim(ax, c, f, 0, ftin(m.SB_REAR + m.M), ext=False, size=4.8, color=RED, side=-1 if c is NE else 1)
    # east
    xe1, xe2 = 51.9 - m.XE, 54.3 - m.XE
    for a, b in ((m.YF, m.SHAFT_U[3]), (m.SHAFT_U[3], m.UTIL[2]), (m.UTIL[2], m.Y_GR_I), (m.Y_GR_I, m.Y_GR_O)):
        dim(ax, (m.XE, b), (m.XE, a), xe1, size=4.8)
    dim(ax, NE, SE, xe2, f"{ftin(LE)}  GARAGE EAST WALL", size=5.2)
    dim(ax, (m.XE, m.Y_GR_O), (50.0, m.Y_GR_O), 0, ftin(m.SB_SIDE + m.M), ext=False, size=4.8, color=RED)
    dim(ax, (m.XE, m.YF - 0.75), (50.0, m.YF - 0.75), 0, ftin(m.SB_SIDE + m.M), ext=False, size=4.8, color=RED, side=-1)
    # front
    y1, y2 = -(m.YF - 6.6), -(m.YF - 4.7)
    for a, b, lab in ((m.xw_o(m.YF), m.OPEN[0], None), (m.OPEN[0], m.OPEN[1], f"{ftin(m.OPEN_W)}  GARAGE OPENING"),
                      (m.OPEN[1], m.XE, None)):
        dim(ax, (a, m.YF), (b, m.YF), y1, lab, size=5.0)
    dim(ax, (m.xw_o(m.YF), m.YF), (m.COL_X[1], m.YF), y2, f"{ftin(m.COL_X[1] - m.xw_o(m.YF))}  TO CENTRE OF POST", size=5.0)
    dim(ax, (m.COL_X[1], m.YF), (m.XE, m.YF), y2, size=5.0)
    dim(ax, (m.xw_o(m.YF) - 1.1, 0.0), (m.xw_o(m.YF) - 1.1, m.YF), 0, ftin(m.YF), ext=False, size=4.8, color=RED)
    dim(ax, (m.XE + 1.3, 0.0), (m.XE + 1.3, m.YF), 0, ftin(m.YF), ext=False, size=4.8, color=RED, side=-1)
    # inside the garage
    yn = m.Y_GR_I - 3.4
    dim(ax, (NWG[0], m.Y_GR_O), (NE[0], m.Y_GR_O), -(m.Y_GR_O - yn), f"{ftin(LN)}  GARAGE REAR WALL, OUTSIDE FACE", size=5.2, side=-1)
    xg = m.GAR_X1 - 2.2
    dim(ax, (m.GAR_X1, m.YF), (m.GAR_X1, m.Y_GR_I), m.GAR_X1 - xg, f"{ftin(m.Y_GR_I - m.YF)}  8 in. WALL", size=4.8)
    dim(ax, (m.SHAFT_X0, m.SHAFT_U[3] - 1.3), (m.XE_GI, m.SHAFT_U[3] - 1.3), 0, ftin(m.XE_GI - m.SHAFT_X0), ext=False, size=4.6)
    # thicknesses and footing widths
    yw = 15.0
    a = (wx(yw, HEEL), yw)
    b = (a[0] + m.FTG_W * _cw, a[1] - m.FTG_W * _sw)
    dim(ax, a, b, 0, ftin(m.FTG_W), ext=False, size=4.6)
    a = (m.xw_o(19.5), 19.5)
    dim(ax, a, (a[0] + _cw, a[1] - _sw), 0, "12\"", ext=False, size=4.6)
    dim(ax, (14.0, m.Y_GR_I - TOE), (14.0, m.Y_GR_O + HEEL), 0, ftin(m.FTG_W), ext=False, size=4.6)
    dim(ax, (17.0, m.Y_GR_I), (17.0, m.Y_GR_O), 0, "12\"", ext=False, size=4.6)
    dim(ax, (m.XE_GI - TOE, 21.0), (m.XE + HEEL, 21.0), 0, ftin(m.FTG_W), ext=False, size=4.6)
    dim(ax, (m.XE_GI, 19.2), (m.XE, 19.2), 0, "12\"", ext=False, size=4.6)
    dim(ax, (m.COL_X[1] - PAD / 2, m.B1_Y + PAD / 2 + 0.7), (m.COL_X[1] + PAD / 2, m.B1_Y + PAD / 2 + 0.7), 0, ftin(PAD), ext=False, size=4.6)
    # stem-wall elevations
    lead(ax, NWU, (-6.6, 42.6), f"NW CORNER: TOP OF STEM WALL EL {top['nw']:.1f}\nexisting ground EL {gnd['nw']:.1f} · bottom of F4 EL {bot['nw']:.1f} or lower",
         size=4.6, va="center")
    lead(ax, pts["mid"], (33.5, 40.4), f"MID REAR: TOP OF STEM WALL EL {top['mid']:.1f}\nexisting ground EL {gnd['mid']:.1f} · bottom of F4 EL {bot['mid']:.1f} or lower", size=4.6)
    lead(ax, NE, (46.6, 38.2), f"NE CORNER: TOP OF STEM WALL EL {top['ne']:.1f}\n(Unit A floor level; ground EL {gnd['ne']:.1f})\njoins the garage wall here", size=4.6)
    lead(ax, NWG, (-6.6, 33.2), f"GARAGE NW CORNER\nexisting ground EL {gnd['nwg']:.1f}\ntop of stem wall EL {top['nwg']:.1f}", size=4.6)
    # call-outs
    lead(ax, (m.xw_o(m.YF) + 2.6, m.YF + 0.5), (12.6, 14.4), f"CONCRETE RETURN PIER 12 in. x {ftin(m.OPEN[0] - m.xw_o(m.YF))}\nwest bearing of beam B1 (S-104)", size=4.6)
    lead(ax, (m.COL_X[1] + 1.2, m.B1_Y + 1.2), (30.2, 15.3), f"F2  PAD {ftin(PAD)} x {ftin(PAD)} x 14 in.\nunder HSS 6x6 post", size=4.6)
    lead(ax, (m.COL_X[2], m.B1_Y + 1.0), (30.2, 13.0), f"{ftin(BRG_PAD)} PAD, east bearing of B1", size=4.6)
    lead(ax, (20.0, m.Y_GR_I - 0.6), (18.5, 22.3), f"F1  {ftin(m.FTG_W)} x 14 in. UNDER 12 in. WALLS\ntoe {ftin(TOE)} · wall 12 in. · heel {ftin(HEEL)}\nTOP OF FOOTING EL {m.EL_FTG_TOP:.2f}", size=4.8, ha="center", va="top", dot=True)
    lead(ax, (m.GAR_X1 + 0.33, 17.5), (30.6, 19.4), "F3  16 x 8 in. UNDER 8 in. WALLS\n(concrete or grouted block)", size=4.6, ha="right")
    lead(ax, (16.0, m.yr_o(16.0) - 0.8), (13.6, 34.6), "F4  20 x 10 in.\nUNDER 8 in.\nSTEM WALLS", size=4.6, ha="center", va="top")
    txt(ax, 27.5, 31.9, f"UNIT A SLAB ON GRADE EL {m.EL_A:.2f}  (S-103)", size=4.6, color=GREY, z=9)
    txt(ax, 24.0, 17.2, f"GARAGE SLAB EL {m.EL_GAR:.2f}  (S-103)", size=4.6, color=GREY, z=9)
    lead(ax, (xs + 3.0, m.yr_o(xs + 3.0) - 0.4), (33.0, 37.0), "STEP THE STEM FOOTING DOWN to F1, or span the\nbackfill as a grade beam (engineer): red marks", size=4.6, color=RED, va="bottom")
    lead(ax, (10.0, m.Y_GR_O + BACKFILL), (-6.6, 37.6), f"BROWN DOTS: {ftin(BACKFILL)} BACKFILL ZONE\nbehind the garage walls (assumed;\nsee C-104). No footing on backfill.", size=4.6, color=EARTH, dot=False)
    lead(ax, DR[1], (-6.6, 28.6), "FRENCH DRAIN AND\nCLEANOUT RISERS\n(blue): see S-102", size=4.6, color=BLUE)
    lead(ax, DR[4], (48.4, -4.6), f"GRAVITY OUTLET\nINV. EL {m.EL_DRAIN_OUT:.1f}", size=4.6, color=BLUE, va="bottom")
    cut_mark(ax, (m.XE - 4.2, 14.2), (m.XE + 4.0, 14.2), "C")
    txt(ax, m.XE - 4.2, 13.2, "S-102", size=4.2, z=12)
    txt(ax, 46.3, -0.9, "FRONT LOT LINE = R.O.W. LINE", size=4.8, color=ACCENT)
    txt(ax, 50.9, 4.5, "LOT LINE", size=4.8, color=ACCENT, rot=90)
    txt(ax, 26.5, 43.0, "REAR LOT LINE", size=4.8, color=ACCENT, rot=-math.degrees(_th))
    txt(ax, 1.7, 5.0, "LOT LINE", size=4.8, color=ACCENT, rot=90 - math.degrees(WEST_LEAN))
    # title, north, scale, legend
    view_title(ax, 31.5, 42.6, "1", "Foundation and footing plan", "3/16\" = 1'-0\" · footings dashed · concrete walls grey · red dimensions tie the corners to the lot lines", 9)
    north_arrow(ax, 53.2, 34.6, 1.7, 6.5)
    scale_bar(ax, -5.5, -6.2, 16, 4, 0.42, size=5.2)
    txt(ax, -6.6, -2.0, "Wall lengths are along the outside face.\nAll footing tops EL 913.50 except F4.\nRounded to 1 in.", size=4.6, ha="left", color=GREY)
    save(fig, "S-101", pdf)


# ----------------------------------------------------------------------------
# S-102
# ----------------------------------------------------------------------------
def wall_elevations(fig, left, bottom):
    tot = LW + LN + LE
    ax = plan_axes(fig, left, bottom, (-8.0, tot + 8.0), (910.2, 929.6), 8.0)
    X0, X1, X2, X3 = 0.0, LW, LW + LN, tot
    S = np.concatenate([np.linspace(0, LW, 21), LW + np.linspace(0, LN, 37), LW + LN + np.linspace(0, LE, 21)])
    Gd = np.array([ground_w(s) for s in np.linspace(0, LW, 21)] + [ground_n(s) for s in np.linspace(0, LN, 37)]
                  + [ground_e(s) for s in np.linspace(0, LE, 21)])
    # footing, wall face, retained zone
    rect(ax, X0 - 1.0, EL_F1_BOT, X3 + 1.0, m.EL_FTG_TOP, fc=CONC, ec=INK, lw=0.6, z=3)
    rect(ax, X0, m.EL_FTG_TOP, X3, EL_TOC, fc="#eceef0", ec=INK, lw=0.9, z=3)
    ret = [(s, min(g, EL_UPSTAND if X1 <= s <= X2 else 1e9)) for s, g in zip(S, Gd)]
    poly(ax, [(X0, m.EL_GAR)] + [(s, max(g, m.EL_GAR)) for s, g in ret] + [(X3, m.EL_GAR)], fc=SOIL, ec="none", z=3.2)
    # upstands above the bearing level
    up_w = [(s, max(EL_TOC, ground_w(s) + 8 * IN)) for s in np.linspace(0, LW, 21)]
    poly(ax, [(X0, EL_TOC)] + up_w + [(X1, EL_TOC)], fc="#d9dce0", ec=INK, lw=0.6, z=3.4, hatch="////")
    rect(ax, X1, EL_TOC, X2, EL_UPSTAND, fc="#d9dce0", ec=INK, lw=0.6, z=3.4, hatch="////")
    line(ax, list(zip(S, Gd)), color=EARTH, lw=1.1, ls=(0, (5, 2)), z=6)
    line(ax, [(X0, m.EL_GAR), (X3, m.EL_GAR)], lw=0.6, color=GREY, z=5)
    line(ax, [(X0 - 1.5, EL_TOC), (X3 + 1.5, EL_TOC)], lw=0.4, color=GREY, ls=(0, (1, 2)), z=5)
    # fold lines, cross walls
    for x, lab in ((X1, "NW CORNER"), (X2, "NE CORNER")):
        line(ax, [(x, EL_F1_BOT - 0.8), (x, 928.2)], lw=0.6, ls=(0, (8, 2, 2, 2)), z=7)
        txt(ax, x, 928.7, lab, size=4.8, weight="bold")
    for a, b in ((X0, X0 + m.CONC), (X1 + m.GAR_X1 - NWG[0], X1 + m.SHAFT_X0 - NWG[0]),
                 (X2 + m.Y_GR_O - m.UTIL[2], X2 + m.Y_GR_O - m.SHAFT_U[3]), (X3 - m.CMU, X3)):
        rect(ax, a, m.EL_FTG_TOP, b, EL_TOC, fc="#c3c7cc", ec=GREY, lw=0.4, z=4)
    # drain profile and cleanouts
    xs = [X0, X1, X2, X3]
    line(ax, list(zip(xs, DR_INV[:4])), color=BLUE, lw=1.0, ls=(0, (4, 2)), z=8)
    for i, x in enumerate(xs):
        gx = Gd[[0, 20, 57, 78][i]]
        xo = x + (0.5 if i in (0, 1) else -0.5) * (1 if i in (0, 3) else 1)
        xo = x + (0.6 if i == 0 else -0.6 if i == 3 else 0.6)
        line(ax, [(xo, DR_INV[i]), (xo, gx + 0.3)], color=BLUE, lw=0.7, z=8)
        rect(ax, xo - 0.25, gx + 0.3, xo + 0.25, gx + 0.55, fc=BLUE, ec=BLUE, z=8)
        txt(ax, xo + (1.0 if i != 3 else -1.0), DR_INV[i] - 1.75, f"{DR_NAMES[i]}\nINV {DR_INV[i]:.2f}", size=4.6, color=BLUE, weight="bold",
            ha="left" if i != 3 else "right")
    # sleeves
    sx = X2 + m.Y_GR_O - m.WATER_ENTRY[1]
    for d in (-0.35, 0.35):
        ax.add_patch(plt.Circle((sx + d, m.EL_WATER_ENTRY), 0.22, fc=PAPER, ec=INK, lw=0.6, zorder=8))
    lead(ax, (sx, m.EL_WATER_ENTRY - 0.3), (sx + 2.6, 916.0), f"2 SLEEVES, 1 in. WATER\nSERVICES, EL {m.EL_WATER_ENTRY:.1f} (P-101)", size=4.4, dot=False)
    bx = X1 + m.CHASE_2[0] - NWG[0]
    rect(ax, bx - 0.4, EL_TOC + 0.25, bx + 0.4, EL_UPSTAND - 0.25, fc=PAPER, ec=INK, lw=0.6, z=8)
    lead(ax, (bx, EL_UPSTAND - 0.25), (bx + 1.6, 927.4), f"SLEEVE THROUGH THE UPSTAND FOR BATH 2 DRAINS AT CHASE 2,\n{ftin(m.CHASE_2[0] - NWG[0])} from the NW corner; size and level by P-101", size=4.4, dot=False)
    # names and lengths
    for a, b, lab, L in ((X0, X1, "WEST WALL", LW), (X1, X2, "NORTH (REAR) WALL", LN), (X2, X3, "EAST WALL", LE)):
        dim(ax, (a, EL_F1_BOT), (b, EL_F1_BOT), -1.0, f"{lab}  {ftin(L)}", size=5.4, side=-1)
    # retained heights
    for x, g, sd in ((X0, Gd[0], 1), (X1, Gd[20], 1), (X2, Gd[57], 1), (X3, Gd[78], -1)):
        xo = x + (2.6 if x == X0 else -2.6 if x == X3 else 2.2)
        dim(ax, (xo, m.EL_GAR), (xo, g), 0, f"{ftin(g - m.EL_GAR)} RETAINED", ext=False, size=4.6, side=sd)
        txt(ax, xo + (0.3 if x != X3 else -0.3), g + 0.55, f"GROUND EL {g:.1f}", size=4.4, color=EARTH, ha="left" if x != X3 else "right", weight="bold")
    # levels
    eltag(ax, X3 + 1.5, EL_TOC, f"TOP OF CONCRETE EL {EL_TOC:.2f}", size=4.6, w=0.8)
    eltag(ax, X3 + 1.5, m.EL_GAR, f"SLAB EL {m.EL_GAR:.2f}", size=4.6, w=0.8)
    eltag(ax, X3 + 1.5, m.EL_FTG_TOP - 0.25, f"FTG TOP EL {m.EL_FTG_TOP:.2f}", size=4.6, w=0.8)
    eltag(ax, X3 + 1.5, EL_F1_BOT - 0.75, f"FTG BOTTOM {EL_F1_BOT:.2f}", size=4.6, w=0.8)
    dim(ax, (X0 - 1.6, m.EL_FTG_TOP), (X0 - 1.6, EL_TOC), 0, ftin(EL_TOC - m.EL_FTG_TOP), ext=False, size=4.8)
    txt(ax, X0 - 2.6, 926.3, "WALL\nHEIGHT", size=4.4, ha="right")
    # labels
    xm = (X1 + X2) / 2
    txt(ax, xm + 8, (EL_TOC + EL_UPSTAND) / 2, f"6 in. UPSTAND TO EL {EL_UPSTAND:.2f}, UNDER THE UNIT A SLAB ON GRADE", size=4.4, box=True, z=9)
    txt(ax, xm - 1, EL_TOC - 0.75, f"TRUSS BEARING LEDGE: TOP OF CONCRETE EL {EL_TOC:.2f}, SILL PLATE, TRUSSES BEAR AT EL {EL_BRG:.2f}", size=4.4, z=9)
    txt(ax, xm, 920.0, "RETAINED TO THE UNDERSIDE OF THE UNIT A SLAB (backfill)", size=4.4, color=EARTH, z=9)
    lead(ax, (X0 + 13.5, max(EL_TOC, ground_w(13.5) + 8 * IN) - 0.3), (X0 + 3.0, 927.9), "UPSTAND AT THE OUTSIDE FACE, STEPPED TO STAY\n8 in. ABOVE FINISH GRADE (C-105)", size=4.4, dot=False)
    txt(ax, X0 + LW / 2, 918.6, "EXISTING GROUND\nAT THE OUTSIDE FACE\n(LiDAR, dashed)", size=4.4, color=EARTH, z=9)
    txt(ax, X2 + LE / 2 + 1.5, 925.6, "wall is exposed above\nthe ground line", size=4.4, color=GREY, z=9)
    txt(ax, xm, m.EL_GAR - 0.5, "FRENCH DRAIN INVERT (blue), beside the footing heel", size=4.4, color=BLUE, z=9, box=True)
    txt(ax, X0 - 0.2, 911.0, "SW (front)", size=4.4, ha="right", color=GREY)
    txt(ax, X3 + 0.2, 911.0, "SE (front)", size=4.4, ha="left", color=GREY)
    return ax


def wall_section(fig, left, bottom):
    g0 = 922.0
    ylo, yhi = 911.3, 927.2
    ax = plan_axes(fig, left, bottom, (-5.6, 8.6), (ylo, yhi), 8 / 3.0)
    lot = m.CONC + m.SB_SIDE + m.M
    grade = [(1.0, g0), (2.0, g0 - 0.2), (4.0, g0 - 0.55), (lot, g0 - 0.1), (8.6, g0 + 0.25)]
    poly(ax, [(-5.6, ylo), (8.6, ylo)] + grade[::-1] + [(1.0, m.EL_FTG_TOP), (-5.6, m.EL_FTG_TOP)], fc=SOIL, ec="none", z=1)
    line(ax, grade, lw=1.0, color=EARTH, z=6)
    inv = (m.EL_DRAIN_HI + DR_INV[3]) / 2
    px = m.CONC + DRAIN_OFF
    # drain stone, backfill, cap
    poly(ax, [(1.0, m.EL_FTG_TOP), (1.0 + HEEL, m.EL_FTG_TOP), (1.0 + HEEL, inv - 0.35), (px + 0.9, inv - 0.35), (px + 0.9, m.EL_GAR + 0.3),
              (1.0, m.EL_GAR + 0.3)], fc=STONE, ec="none", z=2, hatch="ooo")
    line(ax, [(1.0 + HEEL, inv - 0.35), (px + 0.9, inv - 0.35), (px + 0.9, m.EL_GAR + 0.3), (1.0 + HEEL, m.EL_GAR + 0.3), (1.0 + HEEL, g0 - 1.35)],
         lw=0.7, color=BLUE, ls=(0, (3, 1.5)), z=5)
    poly(ax, [(1.0, m.EL_GAR + 0.3), (1.0 + HEEL, m.EL_GAR + 0.3), (1.0 + HEEL, g0 - 1.35), (1.0, g0 - 1.0)], fc="#f5f1e4", ec="none", z=2, hatch="...")
    poly(ax, [(1.0, g0 - 1.0), (1.0 + HEEL, g0 - 1.35), (1.0 + HEEL, g0 - 0.38), (2.0, g0 - 0.2), (1.0, g0)], fc="#cdbfa8", ec="none", z=2)
    ax.add_patch(plt.Circle((px, inv + 2 * IN), 2.2 * IN, fc=PAPER, ec=BLUE, lw=1.2, zorder=6))
    # concrete
    rect(ax, -TOE, EL_F1_BOT, m.CONC + HEEL, m.EL_FTG_TOP, fc=CONC, ec=INK, lw=0.9, z=4)
    rect(ax, 0, m.EL_FTG_TOP, m.CONC, EL_TOC, fc=CONC, ec=INK, lw=0.9, z=4)
    rect(ax, 0.33, m.EL_FTG_TOP - 0.125, 0.67, m.EL_FTG_TOP, fc=CONC, ec=INK, lw=0.5, z=4.5)
    rect(ax, -5.6, m.EL_GAR - SLAB_G - STONE_G, 0, m.EL_GAR - SLAB_G, fc=STONE, ec="none", z=2, hatch="ooo")
    rect(ax, -5.6, m.EL_GAR - SLAB_G, -0.04, m.EL_GAR, fc=CONC, ec=INK, lw=0.7, z=4)
    # waterproofing and drainage board
    line(ax, [(1.5, m.EL_FTG_TOP + 0.03), (1.03, m.EL_FTG_TOP + 0.03), (1.03, g0 + 0.5)], lw=1.8, color=INK, z=7)
    line(ax, [(1.13, m.EL_FTG_TOP + 0.3), (1.13, g0 - 0.2)], lw=1.3, color=BLUE, ls=(0, (1, 1)), z=7)
    # reinforcing (preliminary)
    for x, hk in ((0.19, -0.75), (0.81, 2.7)):
        line(ax, [(x, EL_TOC - 0.2), (x, EL_F1_BOT + 0.32), (hk, EL_F1_BOT + 0.32)], lw=0.8, color=RED, z=8)
    rebar_dots(ax, [(x, y) for x in (0.29, 0.71) for y in np.arange(m.EL_FTG_TOP + 0.5, EL_TOC - 0.1, 1.0)], 0.045)
    rebar_dots(ax, [(x, EL_F1_BOT + 0.42) for x in (-0.5, 1.2, 2.5)], 0.045)
    # sill, floor, wall above
    rect(ax, m.CONC - 5.5 * IN, EL_TOC, m.CONC, EL_BRG, fc=WOODC, ec=INK, lw=0.5, z=5)
    line(ax, [(0.72, EL_TOC - 0.6), (0.72, EL_BRG + 0.12)], lw=0.8, color=INK, z=6)
    rect(ax, -5.6, EL_BRG, m.CONC - 3.5 * IN, m.EL_A - 0.75 * IN, fc="#faf7ef", ec=GREY, lw=0.4, z=3)
    rect(ax, m.CONC - 3.5 * IN, EL_BRG, m.CONC, m.EL_A - 0.75 * IN, fc=WOODC, ec=INK, lw=0.6, z=5)
    for xa in (-1.7, -3.7):
        rect(ax, xa, EL_BRG, xa + 3.5 * IN, m.EL_A - 0.75 * IN, fc=WOODC, ec=INK, lw=0.5, z=5)
    for xa, xb in ((-1.7 + 3.5 * IN, m.CONC - 3.5 * IN), (-3.7 + 3.5 * IN, -1.7)):
        line(ax, [(xa, EL_BRG + 0.1), (xb, m.EL_A - 0.2), (xb, EL_BRG + 0.1), (xa, m.EL_A - 0.2)], lw=0.4, color=GREY, z=4)
    rect(ax, -5.6, m.EL_A - 0.75 * IN, m.CONC, m.EL_A, fc=WOODC, ec=INK, lw=0.5, z=5)
    line(ax, [(-5.6, EL_BRG - 0.052), (0, EL_BRG - 0.052)], lw=1.0, color=GREY, z=5)
    rect(ax, m.CONC - m.EXT, m.EL_A, m.CONC, yhi, fc="#4a5058", ec=INK, lw=0.5, z=5)
    # lot line
    line(ax, [(lot, ylo + 0.3), (lot, g0 + 3.3)], color=ACCENT, lw=1.0, ls=(0, (9, 2.5, 1.5, 2.5)), z=6)
    txt(ax, lot + 0.25, g0 + 2.9, "LOT LINE", size=4.8, color=ACCENT, ha="left")
    dim(ax, (m.CONC, g0 + 2.3), (lot, g0 + 2.3), 0, ftin(m.SB_SIDE + m.M), ext=False, size=5.0, color=ACCENT)
    txt(ax, 3.9, g0 - 0.1, "SWALE", size=4.6, color=EARTH, va="bottom")
    txt(ax, 7.5, g0 - 3.0, "NATIVE SOIL\n(shored cut,\nC-104)", size=4.6, color=EARTH)
    # dimensions and levels
    yb = EL_F1_BOT - 0.42
    dim(ax, (-TOE, yb), (0, yb), 0, ftin(TOE), ext=False, size=4.6, side=-1)
    dim(ax, (0, yb), (m.CONC, yb), 0, "12\"", ext=False, size=4.6, side=-1)
    dim(ax, (m.CONC, yb), (m.CONC + HEEL, yb), 0, ftin(HEEL), ext=False, size=4.6, side=-1)
    dim(ax, (-1.7, EL_F1_BOT), (-1.7, m.EL_FTG_TOP), 0, "14\"", ext=False, size=4.6)
    dim(ax, (-3.9, m.EL_GAR), (-3.9, EL_TOC), 0, ftin(EL_TOC - m.EL_GAR), ext=False, size=5.0)
    dim(ax, (8.0, m.EL_GAR), (8.0, g0 + 0.15), 0, "RETAINED HEIGHT VARIES: SEE ELEVATIONS", ext=False, size=4.6, side=-1)
    line(ax, [(1.0, m.EL_GAR), (8.3, m.EL_GAR)], lw=0.3, color=GREY, ls=(0, (2, 2)), z=3)
    eltag(ax, -5.5, m.EL_A + 0.22, f"UNIT A FLOOR EL {m.EL_A:.2f}", size=5.0, w=0.0)
    eltag(ax, -5.5, EL_TOC - 0.5, f"TOP OF CONCRETE EL {EL_TOC:.2f}\nTRUSS BEARING EL {EL_BRG:.2f}", size=4.8, w=0.0)
    eltag(ax, -5.5, m.EL_GAR + 0.25, f"GARAGE SLAB EL {m.EL_GAR:.2f}", size=5.0, w=0.0)
    eltag(ax, -5.5, m.EL_FTG_TOP - 0.55, f"TOP OF FOOTING EL {m.EL_FTG_TOP:.2f}", size=4.8, w=0.0)
    txt(ax, -2.9, 919.0, "OPEN GARAGE", size=5.4, color=GREY, weight="bold")
    txt(ax, -3.4, 924.65, "UNIT A FLOOR TRUSSES RUN\nPARALLEL TO THIS WALL", size=4.4, color=GREY)
    # keynote bubbles
    ks = [((0.5, 918.2), (-1.3, 917.3), 1), ((-0.6, EL_F1_BOT + 0.75), (-2.9, 912.25), 2), ((-2.6, m.EL_GAR - 0.2), (-2.6, 915.6), 3),
          ((0.72, EL_TOC + 0.06), (-1.1, 922.7), 4), ((-0.5, 924.7), (-1.6, 926.4), 5), ((1.03, 920.3), (2.3, 921.25), 6),
          ((1.13, 917.4), (3.9, 918.6), 7), ((px, inv + 0.17), (6.3, 913.3), 8), ((2.2, 918.0), (4.6, 916.4), 9),
          ((1.6, g0 - 0.6), (3.0, g0 + 1.2), 10), ((lot, 914.2), (7.5, 915.2), 11), ((0.75, 926.5), (2.6, 926.5), 12),
          ((-4.6, EL_BRG - 0.052), (-4.6, 922.6), 13)]
    for p, q, n in ks:
        knote(ax, p, q, n)
    return ax


def key_plan(fig, left, bottom):
    fpi = 16.0
    ax = plan_axes(fig, left, bottom, (-3.0, 56.0), (-9.5, 43.0), fpi)
    line(ax, [LOT_NW, LOT_SW, LOT_SE, LOT_NE, LOT_NW], color=ACCENT, lw=0.7, ls=(0, (9, 2.5, 1.5, 2.5)), z=3)
    line(ax, [(-3, PAVE_N), (56, PAVE_N)], lw=0.5, color=GREY, z=2)
    txt(ax, 14, PAVE_N - 1.2, "BAIRD STREET (edge of pavement)", size=4.4, color=GREY)
    poly(ax, m.APRON, fc="#f1f3f5", ec=BG_EDGE, lw=0.4, z=2)
    poly(ax, m.OUT_U, fc="none", ec=BG_EDGE, lw=0.5, z=3)
    spoly(ax, G["RW"], fc=CONC, ec=INK, lw=0.6, z=5)
    spoly(ax, G["IW"], fc="#d3d7dc", ec=GREY, lw=0.4, z=5)
    spoly(ax, G["STEM"], fc="#d3d7dc", ec=GREY, lw=0.4, z=5)
    line(ax, [(m.OPEN[0], Y_TD), (m.OPEN[1], Y_TD), (41.0, 2.0), DR[4]], lw=0.7, color="#0e8f9c", z=6)
    drain_plan(ax, lw=1.3)
    for i, (x, y) in enumerate(DR[:4]):
        dx, ha = ((-1.2, "right") if i in (0, 1) else (1.2, "left"))
        txt(ax, x + dx, y + (1.6 if i in (1, 2) else -1.4), f"{DR_NAMES[i]}\n{DR_INV[i]:.2f}", size=4.4, color=BLUE, weight="bold", ha=ha)
    txt(ax, DR[4][0] + 1.6, DR[4][1] - 0.6, f"OUTLET\n{m.EL_DRAIN_OUT:.2f}", size=4.4, color=BLUE, weight="bold", ha="left")
    for (a, b) in zip(DR[:3], DR[1:4]):
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        L = math.dist(a, b)
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        arrow(ax, (mx - ux * 2, my - uy * 2), (mx + ux * 2, my + uy * 2), color=BLUE, lw=1.0)
    txt(ax, 24.0, 20.5, "OPEN GARAGE\nSLAB EL 914.50", size=4.6, color=GREY)
    txt(ax, 22.0, 34.2, "UNIT A SLAB ON GRADE", size=4.2, color=GREY)
    txt(ax, 3.8, 19.0, "WEST WALL", size=4.6, rot=90 - math.degrees(WEST_LEAN), weight="bold")
    txt(ax, 27.0, 28.2, "NORTH (REAR) WALL", size=4.6, weight="bold")
    txt(ax, 42.6, 20.0, "EAST WALL", size=4.6, rot=90, weight="bold")
    txt(ax, 24.0, 6.6, "trench drain", size=4.2, color="#0e8f9c")
    cut_mark(ax, (m.XE - 5.5, 16.0), (m.XE + 4.4, 16.0), "C")
    north_arrow(ax, 4.5, 38.5, 2.6, 6)
    return ax


def sheet_s102(pdf):
    perf = sum(DR_SEG[:3])
    notes = tbn(
        ("Preliminary",
         "Wall thickness, bars and footing are assumptions for pricing. A WV structural engineer designs and seals "
         "the walls. Lengths and levels are from the model and the LiDAR ground."),
        ("Bracing: read before backfilling",
         "These walls are NOT cantilevers. The Unit A floor props their tops. Do not backfill above half height "
         "until the Unit A floor is framed and sheathed, unless the engineer designs the walls as cantilevers. "
         "Brace or shore until then."),
        ("Waterproofing trade",
         "Membrane and drainage board on the west, rear and east walls from footing to grade. Seal every sleeve. "
         "Flood-test or photograph before backfill; inspection by the owner.",
         "The east side yard also carries the two water services (42 in. cover) and the solid pipe from the rear "
         "yard drain (C-105). Lay the French drain first: it is the deepest."),
        ("Cleanouts",
         "4 in. solid riser with a threaded cap in a flush box at each corner (CO-1 to CO-4), so every run can be "
         "flushed and cameraed."),
    )
    fig, bg = new_sheet("S-102", two_line(TITLE["S-102"]), "As noted", notes)
    L = MARGIN + 0.3
    # B: unfolded elevations
    wall_elevations(fig, L + 0.75, 8.05)
    vtitle(bg, L, 10.42, "B", "Garage retaining walls unfolded, seen from inside the garage", "1/8\" = 1'-0\" · lengths along the outside face · ground from LiDAR at the outside face · preliminary")
    # banner
    bx0, bx1 = L, SHEET_W - MARGIN - TB_W - 0.3
    bg.add_patch(Rectangle((bx0, 7.3), bx1 - bx0, 0.52, fc="#fbeeee", ec=ACCENT, lw=1.0))
    bg.text(bx0 + 0.12, 7.66, "GRAVITY ONLY: NO SUMP PUMP.", fontsize=9.0, fontweight="bold", color=ACCENT, va="center")
    out_g = elev(*m.DRAIN_OUT)
    bg.text(bx0 + 2.62, 7.66, f"Foundation water leaves through the French drain to the street edge. On paper the pipe falls {DR_FALL * 12:.0f} in. in {DR_LEN:.0f} ft, "
            f"but the outlet invert (EL {m.EL_DRAIN_OUT:.1f}) is at the LiDAR ground level there (EL {out_g:.1f}) and",
            fontsize=6.0, color=INK, va="center")
    bg.text(bx0 + 0.12, 7.44, f"about {(m.EL_DRAIN_OUT - street_el(m.DRAIN_OUT[0])) * 12:.0f} in. above the pavement. Count on only about 6 in. of fall until the SURVEY confirms these levels. "
            "If the fall cannot be confirmed, the garage floor (and the whole building with it) is RAISED. A pump is never added.",
            fontsize=6.0, color=INK, va="center")
    # C: typical section
    wall_section(fig, L + 0.05, 0.92)
    vtitle(bg, L, 7.02, "C", "Typical wall section: west and east walls", "3/8\" = 1'-0\" · east wall shown looking north, west wall opposite hand · rear wall top: S-103 detail D")
    keys = [
        "12 in. concrete wall, 4,000 psi. PRELIM. bars: #5 at 12 in. vertical each face, #4 at 12 in. horizontal each face. Engineer to design.",
        f"Footing F1 {ftin(m.FTG_W)} x 14 in.: toe {ftin(TOE)}, heel {ftin(HEEL)} toward the soil. PRELIM. #5 at 12 in. across the bottom, 3 #5 lengthwise. "
        "Keyed joint (2x4 keyway) and #5 dowels at 12 in. into the wall. On undisturbed soil passed by the soil engineer.",
        "Wall to slab: 6 in. garage slab on 6 in. compacted stone (S-103), 1/2 in. isolation joint, sealed. The footing, not the slab, holds the wall base against sliding (engineer to confirm).",
        "Treated 2x6 sill plate on sill sealer, 5/8 in. anchor bolts at 32 in. (prelim.).",
        "Wall to floor: THE UNIT A FLOOR PROPS THE TOP OF THE WALL. Blocking panels between the end truss and the next two trusses at 4 ft, subfloor nailed to them, straps as engineered. Rear wall: trusses bear on it (S-103).",
        "Sheet membrane waterproofing (60-mil self-adhered, or equal) from the footing to finish grade, lapped 6 in. onto the footing, termination bar at the top.",
        "Dimpled drainage board with filter fabric over the membrane, full height, open at the bottom into the drain stone.",
        f"FRENCH DRAIN: 4 in. perforated PVC, holes down, in 12 in. of washed stone wrapped in filter fabric, beside the footing heel. "
        f"Invert EL {m.EL_DRAIN_HI:.2f} (CO-1) falling to {DR_INV[3]:.2f} (CO-4). Never dig below the footing bottom, EL {EL_F1_BOT:.2f}.",
        "Free-draining backfill (washed gravel or clean crushed stone), 2 ft wide min., in 8 in. lifts. Hand-operated compactors only within 4 ft of the wall.",
        "Top 12 in.: compacted clay cap and topsoil, graded away from the wall to a surface swale that runs to the street (C-105).",
        f"Lot line {ftin(m.SB_SIDE + m.M)} from the wall face. The cut cannot be sloped back: shoring by C-104.",
        "2x6 wall of Unit A above (A-501). Keep concrete 8 in. above finish grade: where grade is higher, a concrete upstand rises with it (see elevations).",
        "Garage ceiling: R-30 in the trusses and 5/8 in. Type X gypsum board (A-501).",
    ]
    kx, ky = L + 5.62, 6.62
    bg.text(kx, ky + 0.2, "KEYNOTES, SECTION C", fontsize=6.6, fontweight="bold")
    for i, k in enumerate(keys):
        lines = textwrap.wrap(k, 63)
        bg.add_patch(plt.Circle((kx + 0.08, ky - 0.045), 0.078, fc=PAPER, ec=INK, lw=0.5))
        bg.text(kx + 0.08, ky - 0.05, str(i + 1), fontsize=4.8, fontweight="bold", ha="center", va="center")
        bg.text(kx + 0.22, ky, "\n".join(lines), fontsize=5.3, va="top", linespacing=1.22)
        ky -= 0.106 * len(lines) + 0.075
    if ky < 0.5:
        print("WARNING: S-102 keynotes run off the sheet", ky)
    # A: key plan and D: drain data
    px = L + 9.35
    key_plan(fig, px - 0.05, 3.62)
    vtitle(bg, px, 7.02, "A", "Key plan and French drain", "1/16\" = 1'-0\" · inverts at cleanouts")
    bg.text(px, 3.42, "D   FRENCH DRAIN DATA", fontsize=8.0, fontweight="bold", va="center")
    rows = [("Point", "Station", "Invert EL")]
    names = ["CO-1 SW corner, high point", "CO-2 NW corner", "CO-3 NE corner", "CO-4 SE corner", "Outlet at the street edge"]
    for n_, s, v in zip(names, DR_STA, DR_INV):
        rows.append((n_, f"{s:.1f} ft", f"{v:.2f}"))
    yb = table(bg, px, 3.27, [1.95, 0.72, 0.72], rows, fs=5.6, rh=0.175)
    info = [
        f"Perforated pipe CO-1 to CO-4: {perf:.0f} ft (west {DR_SEG[0]:.0f}, rear {DR_SEG[1]:.0f}, east {DR_SEG[2]:.0f}).",
        f"Solid pipe CO-4 to the outlet: {DR_SEG[3]:.0f} ft, no holes, glued joints.",
        f"Fall {DR_FALL:.1f} ft in {DR_LEN:.0f} ft = {DR_SLOPE * 100:.2f} % (about 1/{round(1 / (DR_SLOPE * 12))} in. per ft).",
        "Lay it at one even slope. 0.5 % is the least acceptable.",
        f"Pipe centre line {ftin(DRAIN_OFF)} outside the wall face.",
        "Outlet: rodent screen and stone splash pad at the street",
        "edge; it is in the right-of-way, so the City Engineer approves.",
        "The trench drain at the opening joins the same outlet pipe",
        "downstream of CO-4 (C-105).",
    ]
    for i, s in enumerate(info):
        bg.text(px, yb - 0.17 - i * 0.135, s, fontsize=5.4, va="center")
    save(fig, "S-102", pdf)


# ----------------------------------------------------------------------------
# S-103
# ----------------------------------------------------------------------------
def trench_detail(fig, left, bottom):
    """Section through the slab edge at the garage opening, looking west. x = distance north of the building face."""
    ax = plan_axes(fig, left, bottom, (-2.4, 2.7), (-1.75, 0.95), 4 / 3.0)
    xs = Y_SLAB_S - m.YF
    xt = Y_TD - m.YF
    xn = xs + THICK_W
    poly(ax, [(-2.4, -1.75), (2.7, -1.75), (2.7, -1.0), (xn + 0.5, -1.0), (xn, -1.5), (xs, -1.5), (xs, -0.83), (-2.4, -0.83)], fc=SOIL, ec="none", z=1)
    poly(ax, [(2.7, -1.0), (xn + 0.5, -1.0), (xn, -1.5), (xs, -1.5), (xs, -THICK_D), (xn, -THICK_D), (xn + 0.5, -SLAB_G), (2.7, -SLAB_G)], fc=STONE, ec="none", z=2, hatch="ooo")
    poly(ax, [(xs, 0), (2.7, 0.045), (2.7, 0.045 - SLAB_G), (xn + 0.5, -SLAB_G + 0.03), (xn, -THICK_D), (xs, -THICK_D)], fc=CONC, ec=INK, lw=0.8, z=4)
    rect(ax, xt - 0.29, -0.54, xt + 0.29, 0.0, fc=PAPER, ec=INK, lw=0.8, z=5)
    rect(ax, xt - 0.17, -0.46, xt + 0.17, -0.06, fc="#dfe9f5", ec=BLUE, lw=0.6, z=6)
    rect(ax, xt - 0.21, -0.06, xt + 0.21, 0.0, fc=INK, ec=INK, z=7)
    rect(ax, -2.4, -0.5, xs - 0.04, -0.02, fc="#d9dde2", ec=GREY, lw=0.6, z=4)
    rect(ax, -2.4, -0.83, xs, -0.5, fc=STONE, ec="none", z=2, hatch="ooo")
    line(ax, [(xn + 0.2, -0.22), (2.6, -0.2)], lw=0.8, color=RED, z=8)
    rebar_dots(ax, [(xs + 0.3, -0.75), (xn - 0.3, -0.75), (xs + 0.3, -0.25)], 0.035)
    line(ax, [(0, 0.1), (0, 0.9)], lw=0.5, color=GREY, ls=(0, (4, 2)), z=6)
    txt(ax, 0.06, 0.82, "FACE OF BUILDING ABOVE", size=4.4, color=GREY, ha="left")
    txt(ax, -1.75, -0.26, "APRON\n(C-107)", size=4.4, color=GREY, z=9)
    txt(ax, 2.05, -0.12, "GARAGE SLAB", size=4.4, z=9)
    dim(ax, (xs, -1.5), (xn, -1.5), -0.14, ftin(THICK_W), ext=False, size=4.6, side=-1)
    dim(ax, (xn + 0.95, -SLAB_G + 0.03), (xn + 0.95, 0.03), 0, "6\"", ext=False, size=4.6)
    dim(ax, (xs - 0.55, -THICK_D), (xs - 0.55, 0), 0, "12\"", ext=False, size=4.6)
    dim(ax, (xt, 0.3), (0, 0.3), 0, "7\"", ext=False, size=4.6)
    lead(ax, (xt, -0.3), (-2.3, 0.62), "TRENCH DRAIN: 4 in. presloped channel,\nvehicle-rated grate, outlet to the\ngravity outlet (C-105)", size=4.4)
    lead(ax, (xs, -0.3), (-2.3, -1.2), "ISOLATION JOINT\nTO THE APRON", size=4.4, ha="left")
    lead(ax, (xn - 0.3, -0.75), (1.0, -1.45), "THICKENED EDGE, 2 #4\ncontinuous (prelim.)", size=4.4)
    lead(ax, (2.2, -0.75), (1.0, 0.5), "6 in. COMPACTED STONE", size=4.4, va="bottom")
    eltag(ax, xt + 0.35, 0.02, f"EL {EL_TD:.2f}", size=4.4, w=0.0)
    return ax


def sog_section(fig, left, bottom, X0=22.0):
    """North-south section through the Unit A slab on grade at site station x = X0, looking west."""
    yo = m.yr_o(X0)
    t = STEM_T / _cr
    pf = (STEM_FW - STEM_T) / 2 / _cr
    gnd = elev(X0, yo + 0.5)
    top = stem_top(X0, yo + 0.5)
    fb = stem_bot(X0, yo + 0.5)
    ylo, yhi = 922.3, 928.9
    x0v, x1v = 28.3, yo + 2.3
    ax = plan_axes(fig, left, bottom, (x0v, x1v), (ylo, yhi), 8 / 3.0)
    yg, yb = m.Y_GR_I, m.Y_GR_O
    yl = yg + 0.5                                      # garage-side face of the upstand
    sub = m.EL_A - SLAB_A - INSUL_A - STONE_A
    # soils
    poly(ax, [(yb, ylo), (yb + BACKFILL, ylo), (yb + BACKFILL + 0.6, sub), (yb, sub)], fc=FILL, ec="none", z=1, hatch="...")
    poly(ax, [(yb + BACKFILL, ylo), (x1v, ylo), (x1v, gnd + 0.25), (yo, gnd), (yo, sub), (yb + BACKFILL + 0.6, sub)], fc=SOIL, ec="none", z=1)
    line(ax, [(yo, gnd), (x1v, gnd + 0.25)], lw=1.0, color=EARTH, z=6)
    # garage wall with ledge and upstand
    poly(ax, [(yg, ylo), (yb, ylo), (yb, EL_UPSTAND), (yl, EL_UPSTAND), (yl, EL_TOC), (yg, EL_TOC)], fc=CONC, ec=INK, lw=0.9, z=4)
    # slab build-up
    xi = yo - t                                         # inside face of the stem wall
    rect(ax, yb, sub, xi, sub + STONE_A, fc=STONE, ec="none", z=2, hatch="ooo")
    rect(ax, yb, sub + STONE_A, xi, sub + STONE_A + INSUL_A, fc="#f7d9de", ec=GREY, lw=0.3, z=3)
    rect(ax, xi - INSUL_A, sub + STONE_A, xi, m.EL_A, fc="#f7d9de", ec=GREY, lw=0.3, z=3)
    poly(ax, [(yl, EL_UPSTAND), (xi - INSUL_A, EL_UPSTAND), (xi - INSUL_A, m.EL_A), (yl, m.EL_A)], fc="#b9bec4", ec=INK, lw=0.8, z=5)
    line(ax, [(yb, EL_UPSTAND - 0.01), (xi - INSUL_A, EL_UPSTAND - 0.01)], lw=1.0, color=BLUE, ls=(0, (3, 1.5)), z=6)
    line(ax, [(yl + 0.25, EL_UPSTAND - 0.9), (yl + 0.25, EL_UPSTAND + 0.14), (yb + BACKFILL + 1.2, EL_UPSTAND + 0.14)], lw=0.8, color=RED, z=8)
    # stem wall and footing
    rect(ax, xi - pf, fb, yo + pf, fb + STEM_FT, fc=CONC, ec=INK, lw=0.8, z=4)
    rect(ax, xi, fb + STEM_FT, yo, top, fc=CONC, ec=INK, lw=0.9, z=4)
    rect(ax, yo - m.EXT / _cr, top, yo, yhi, fc="#4a5058", ec=INK, lw=0.5, z=5)
    # truss on the ledge
    rect(ax, yg + 0.02, EL_TOC, yl - 0.04, EL_BRG, fc=WOODC, ec=INK, lw=0.5, z=5)
    rect(ax, x0v, EL_BRG, yl - 0.04, m.EL_A - 0.75 * IN, fc="#faf7ef", ec=INK, lw=0.5, z=3)
    for a, b in ((EL_BRG, EL_BRG + 0.125), (m.EL_A - 0.75 * IN - 0.125, m.EL_A - 0.75 * IN)):
        rect(ax, x0v, a, yl - 0.04, b, fc=WOODC, ec=INK, lw=0.4, z=5)
    rect(ax, yl - 0.04 - 0.125, EL_BRG, yl - 0.04, m.EL_A - 0.75 * IN, fc=WOODC, ec=INK, lw=0.4, z=5)
    line(ax, [(x0v, m.EL_A - 0.3), (x0v + 0.45, EL_BRG + 0.2), (yl - 0.2, m.EL_A - 0.3)], lw=0.4, color=GREY, z=4)
    rect(ax, x0v, m.EL_A - 0.75 * IN, yl, m.EL_A, fc=WOODC, ec=INK, lw=0.4, z=5)
    line(ax, [(yg + 0.25, EL_TOC - 0.5), (yg + 0.25, EL_BRG + 0.1)], lw=0.8, z=6)
    # bath 2 drain through the upstand
    line(ax, [(yb + 4.6, sub + 0.1), (yl + 0.02, EL_TOC + 0.55), (yl - 0.5, EL_TOC + 0.52)], lw=1.4, color="#2e7d32", ls=(0, (4, 1.5)), z=7)
    # labels
    eltag(ax, yb + 1.7, m.EL_A + 0.02, f"UNIT A SLAB EL {m.EL_A:.2f}", size=4.6, w=0.0)
    dim(ax, (yb, ylo + 0.45), (yb + BACKFILL, ylo + 0.45), 0, f"{ftin(BACKFILL)} ON WALL BACKFILL", ext=False, size=4.6)
    dim(ax, (yo + 1.15, gnd), (yo + 1.15, top), 0, "8\" MIN.", ext=False, size=4.4, side=-1)
    dim(ax, (yo + 1.6, fb), (yo + 1.6, gnd), 0, f"{ftin(gnd - fb)}", ext=False, size=4.4, side=-1)
    txt(ax, yo + 0.25, top + 0.35, f"EL {top:.1f}", size=4.4, ha="left")
    txt(ax, yo + 0.9, gnd + 0.45, f"GROUND EL {gnd:.1f}", size=4.4, color=EARTH, ha="left")
    txt(ax, xi - pf - 0.1, fb + 0.2, f"F4 20 x 10 in.\nbottom EL {fb:.1f}", size=4.4, ha="right")
    txt(ax, yb + 5.4, ylo + 1.0, "UNDISTURBED\nGROUND", size=4.2, color=EARTH)
    txt(ax, yg + 0.5, 922.9, "12 in. GARAGE\nREAR WALL", size=4.2, z=9)
    txt(ax, x0v + 0.1, 923.2, "GARAGE", size=4.4, color=GREY, ha="left")
    for p, q, n in (((yl + 0.25, EL_UPSTAND - 0.5), (yb + 1.3, 923.5), 1), ((yb + 2.6, m.EL_A - 0.2), (yb + 2.6, 926.9), 2), ((yb + 3.4, sub + 0.45), (yb + 3.9, 927.6), 3),
                    ((yg + 0.25, EL_BRG), (x0v + 0.5, 927.2), 4), ((yb + 2.4, sub + 1.02), (yb + 1.3, 927.9), 5), ((xi + 0.3, 925.0), (xi - 1.5, 928.3), 6),
                    ((yl - 0.25, EL_TOC + 0.53), (x0v + 0.55, 922.75), 7)):
        knote(ax, p, q, n)
    return ax


def sheet_s103(pdf):
    a_g, a_l, a_u, a_s = G["GAR"].area, G["LOBBY"].area, G["UTIL"].area, G["SOG_NET"].area
    extra = (THICK_D - SLAB_G) * THICK_W * m.OPEN_W / 27
    cy = lambda a, t: a * t / 27
    notes = tbn(
        ("Preliminary",
         "Thickness, bars and joints are assumptions for pricing; engineer to confirm. Edges and joint lines are "
         "from the model."),
        ("Garage slab",
         "6 in., 4,500 psi air-entrained, #4 at 16 in. each way at mid-depth (prelim.), on 6 in. compacted stone. "
         "15-mil vapour barrier under the utility room only.",
         f"Slope 1/8 in. per ft from the rear wall (EL {m.EL_GAR:.2f}) to the trench drain (EL {EL_TD:.2f}). Lobby "
         f"and utility room level at EL {m.EL_GAR:.2f}.",
         "Saw-cut control joints (CJ) 1 1/2 in. deep within 12 hours. Isolation joints (IJ) at every wall, the "
         "pier and the post. Broom finish; penetrating sealer after 28 days."),
        ("Unit A slab on grade",
         "5 in., 4,000 psi, 6x6 W2.9 mesh or #3 at 18 in., on 15-mil vapour barrier, R-10 rigid foam under and "
         "at the edge, 4 in. stone.",
         "UNDER-SLAB PLUMBING FOR BATH 2 GOES IN FIRST: coordinate with P-101 and P-102 before stone."),
        ("Before pouring",
         "Building drain, floor drain and sleeves in and tested. Subgrade compacted and passed."),
    )
    fig, bg = new_sheet("S-103", two_line(TITLE["S-103"]), "3/16\" = 1'-0\" U.N.O.", notes)
    L = MARGIN + 0.3
    # ---- A: garage slab plan
    ax = frame(fig, ((2.0, 50.0), (3.2, 33.6)), L, 0.55, lot=False)
    lower_plan(ax, "bg", cars=False)
    line(ax, [(m.OPEN[0], m.YF), (m.OPEN[0] + 1.5 * (m.YF - 3.2) / m.YF, 3.2)], lw=0.5, color=BG_EDGE, z=2)
    line(ax, [(m.OPEN[1], m.YF), (m.OPEN[1] - 1.5 * (m.YF - 3.2) / m.YF, 3.2)], lw=0.5, color=BG_EDGE, z=2)
    for k in ("GAR", "LOBBY", "UTIL"):
        spoly(ax, G[k], fc=TINT, ec="none", z=4.1)
    spoly(ax, G["RW"], fc=CONC, ec=INK, lw=0.8, z=6)
    spoly(ax, G["IW"], fc="#c3c7cc", ec=INK, lw=0.6, z=6)
    spoly(ax, G["UTIL"], fc="none", ec=BLUE, lw=0.0, z=4.3, hatch="////")
    ym = (m.YF + m.Y_GR_I) / 2
    cj = (0, (7, 2, 1.5, 2))
    for sx in m.STALL_LINES:
        line(ax, [(sx, Y_SLAB_S + THICK_W), (sx, m.Y_GR_I)], lw=0.9, color=RED, ls=cj, z=7)
    line(ax, [(m.xw_gi(ym), ym), (m.GAR_X1, ym)], lw=0.9, color=RED, ls=cj, z=7)
    cx = m.COL_X[1]
    poly(ax, [(cx - 1.0, m.B1_Y), (cx, m.B1_Y + 1.0), (cx + 1.0, m.B1_Y), (cx, m.B1_Y - 1.0)], fc=PAPER, ec=RED, lw=0.7, z=7.5)
    rect(ax, cx - 0.25, m.B1_Y - 0.25, cx + 0.25, m.B1_Y + 0.25, fc=STEEL, ec=INK, lw=0.5, z=8)
    # thickened edge and trench drain
    rect(ax, m.OPEN[0], Y_SLAB_S, m.OPEN[1], Y_SLAB_S + THICK_W, fc="none", ec=GREY, lw=0.5, z=6.5, hatch="\\\\\\\\", ls=(0, (3, 2)))
    line(ax, [(m.OPEN[0], Y_TD), (m.OPEN[1], Y_TD)], lw=2.2, color=BLUE, z=7)
    # slope arrows
    for x in (14.5, 24.0, 32.6):
        arrow(ax, (x, 26.6), (x, 21.6), color=GREY, lw=0.8)
    txt(ax, 24.0, 27.3, "SLOPE 1/8 in. PER FT TO THE TRENCH DRAIN", size=4.8, color=GREY, weight="bold", box=True)
    eltag(ax, 11.0, m.Y_GR_I - 0.7, f"EL {m.EL_GAR:.2f} AT THE REAR WALL (high side)", size=4.8, w=0.0)
    lead(ax, (17.0, Y_TD), (14.6, 5.9), f"TRENCH DRAIN, top EL {EL_TD:.2f}\ncentre line 7 in. outside the building face: detail C", size=4.6, color=BLUE, ha="left", va="top")
    lead(ax, (22.5, Y_SLAB_S + THICK_W - 0.3), (22.6, 13.6), f"THICKENED EDGE 12 in. x {ftin(THICK_W)} (hatched)", size=4.6, va="bottom")
    lead(ax, (m.STALL_LINES[0], 23.6), (15.0, 24.4), "CJ on the stall line", size=4.6, color=RED, ha="right")
    lead(ax, (16.0, ym), (15.0, 18.2), "CJ at mid-depth", size=4.6, color=RED, ha="center", va="top")
    lead(ax, (cx + 0.7, m.B1_Y + 0.3), (30.0, 14.6), "IJ: diamond block-out at the post,\nfilled after the base is grouted", size=4.6, color=RED)
    lead(ax, (m.xw_gi(22.0) + 0.05, 22.0), (11.2, 20.9), "IJ at all walls\nand the pier", size=4.6, color=RED)
    lead(ax, (m.UTIL[0] + 1.0, m.UTIL[2] + 1.0), (33.4, 23.3), "15-mil VAPOUR BARRIER\nunder the utility room slab\nonly; floor drain by P-101", size=4.6, ha="right")
    # sewer exit
    line(ax, [(m.SEWER_OUT_X, m.YF + 2.6), (m.SEWER_OUT_X, 3.8)], lw=1.0, color="#2e7d32", ls=(0, (4, 1.5)), z=7)
    lead(ax, (m.SEWER_OUT_X, 5.0), (38.6, 4.2), "4 in. BUILDING DRAIN leaves under the\nthickened edge here (P-101): sleeve it", size=4.6, color="#2e7d32")
    # areas
    txt(ax, 24.0, 16.2, f"GARAGE SLAB  {a_g:.0f} sf", size=5.4, weight="bold", box=True, z=9)
    txt(ax, (m.SHAFT_L[0] + m.SHAFT_L[1]) / 2, 21.6, f"LOBBY + STAIR\n{a_l:.0f} sf", size=4.6, weight="bold", box=True, z=9)
    txt(ax, (m.UTIL[0] + m.UTIL[1]) / 2 + 0.2, m.UTIL[2] + 3.4, f"UTILITY {a_u:.0f} sf", size=4.4, weight="bold", box=True, z=9)
    # dimensions
    y1 = -(m.YF - 7.3)
    segs = [m.OPEN[0]] + list(m.STALL_LINES) + [m.OPEN[1]]
    for a, b in zip(segs[:-1], segs[1:]):
        dim(ax, (a, m.YF), (b, m.YF), y1, size=5.0)
    dim(ax, (m.OPEN[1] - (m.OPEN[1] - m.SEWER_OUT_X), 5.6), (m.OPEN[1], 5.6), 0, ftin(m.OPEN[1] - m.SEWER_OUT_X), ext=False, size=4.6, side=-1)
    xe = 47.0 - m.XE
    dim(ax, (m.XE, ym), (m.XE, m.YF), xe, size=5.0)
    dim(ax, (m.XE, m.Y_GR_I), (m.XE, ym), xe, size=5.0)
    dim(ax, (m.XE, m.SHAFT_L[3]), (m.XE, m.SHAFT_L[2]), xe + 1.9, size=4.8)
    dim(ax, (m.XE, m.UTIL[3]), (m.XE, m.UTIL[2]), xe + 1.9, size=4.8)
    yt = 31.6 - m.Y_GR_O
    dim(ax, (m.xw_gi(m.Y_GR_I), m.Y_GR_O), (m.GAR_X1, m.Y_GR_O), yt, f"{ftin(m.GAR_X1 - m.xw_gi(m.Y_GR_I))}  INSIDE, AT THE REAR WALL", size=5.0)
    dim(ax, (m.SHAFT_X0, m.Y_GR_O), (m.XE_GI, m.Y_GR_O), yt, size=5.0)
    dim(ax, (m.xw_gi(m.YF + 1.0), m.YF + 2.6), (m.GAR_X1, m.YF + 2.6), 0, f"{ftin(m.GAR_X1 - m.xw_gi(m.YF + 1.0))}  INSIDE, AT THE FRONT", ext=False, size=4.8)
    dim(ax, (9.4, Y_SLAB_S), (9.4, Y_SLAB_S + THICK_W), 0, ftin(THICK_W), ext=False, size=4.6)
    line(ax, [(9.2, Y_SLAB_S), (m.OPEN[0], Y_SLAB_S)], lw=0.3, z=8)
    line(ax, [(9.2, Y_SLAB_S + THICK_W), (m.OPEN[0], Y_SLAB_S + THICK_W)], lw=0.3, z=8)
    view_title(ax, 2.4, 32.2, "A", f"A   Garage slab plan, EL {m.EL_GAR:.2f}", "3/16\" = 1'-0\" · red = joints · blue = trench drain · preliminary", 8.5)
    scale_bar(ax, 3.0, 4.6, 8, 4, 0.36, size=5.0)
    # ---- B: Unit A slab on grade plan
    ax2 = frame(fig, ((2.0, 50.0), (27.4, 44.2)), L, 6.75, lot=True)
    rect(ax2, 2.0, 27.4, 50.0, m.Y_GR_I, fc="#f6f7f8", ec="none", z=1)
    spoly(ax2, G["RW"].intersection(box(0, m.Y_GR_I - 0.01, 60, 60)), fc="#d3d7dc", ec=BG_EDGE, lw=0.6, z=3)
    spoly(ax2, G["SOG_NET"], fc=TINT, ec="none", z=3)
    spoly(ax2, G["SOG_NET"].intersection(box(0, m.Y_GR_O, 60, m.Y_GR_O + BACKFILL)), fc="none", ec=EARTH, lw=0.0, z=3.2, hatch="....")
    line(ax2, [(wx(m.Y_GR_O + BACKFILL, -STEM_T), m.Y_GR_O + BACKFILL), (NE[0] - BACKFILL / abs(REAR_SLOPE) - 2.3, m.Y_GR_O + BACKFILL)], lw=0.6, color=EARTH, ls=(0, (4, 2)), z=5)
    spoly(ax2, G["STEM"], fc=CONC, ec=INK, lw=0.8, z=6)
    line(ax2, [NWG, NE], lw=0.9, z=6)
    # bath 2 and its stack
    st_ = Style("bg")
    poly(ax2, m.ROOMS["BATH 2"], fc="none", ec=BG_EDGE, lw=0.6, z=4, ls=(0, (3, 2)))
    tub(ax2, *m.TUBS[1], st_)
    wc(ax2, *m.WCS[1][:2], st_, facing=m.WCS[1][2])
    lav(ax2, *m.LAVS[1], st_)
    ax2.add_patch(plt.Circle(m.STACK_2, 0.22, fc=PAPER, ec="#2e7d32", lw=0.9, zorder=8))
    line(ax2, [m.STACK_2, (m.CHASE_2[0], m.Y_GR_I + 0.5)], lw=1.0, color="#2e7d32", ls=(0, (4, 1.5)), z=7)
    rect(ax2, m.CHASE_2[0] - 0.5, m.CHASE_2[1] - 0.5, m.CHASE_2[0] + 0.5, m.Y_GR_I, fc=PAPER, ec="#2e7d32", lw=0.7, z=7)
    lead(ax2, (m.CHASE_2[0] + 0.3, 32.6), (27.6, 36.2), "BATH 2: drains under the slab, then through the 6 in. upstand\nof the garage rear wall into chase 2 (P-101, P-102). In first.", size=4.6, color="#2e7d32", ha="left")
    txt(ax2, 23.0, 33.0, "BATH 2", size=4.4, color=GREY, z=5)
    txt(ax2, 15.0, 35.6, f"5 in. SLAB ON GRADE\nEL {m.EL_A:.2f}, level\n{a_s:.0f} sf", size=5.2, weight="bold", z=9)
    lead(ax2, (33.0, m.Y_GR_O + 1.6), (36.5, 39.4), f"DOTTED STRIP: {ftin(BACKFILL)} beside the garage rear wall sits on wall\nbackfill. Slab spans it: #4 at 12 in. bottom, hooked #4 dowels\nat 16 in. into the wall upstand (prelim.). Detail D.", size=4.6, color=EARTH, ha="left")
    lead(ax2, (12.6, m.yr_o(12.6) - 0.3), (4.0, 43.3), "8 in. STEM WALL, R-10 at the slab edge (S-101)", size=4.6, ha="left")
    # dimensions
    dim(ax2, NWG, NE, -1.5, f"{ftin(LN)}  ALONG THE GARAGE REAR WALL", size=5.0, side=-1)
    dim(ax2, NWG, NWU, 1.6, ftin(L_STEM_W), size=5.0)
    dim(ax2, NWU, NE, 1.3, f"{ftin(L_STEM_R)}  ALONG THE REAR WALL (outside faces)", size=5.0)
    dim(ax2, (11.6, m.Y_GR_O), (11.6, m.Y_GR_O + BACKFILL), 0, ftin(BACKFILL), ext=False, size=4.6)
    cut_mark(ax2, (22.0, m.Y_GR_I - 1.0), (22.0, m.yr_o(22.0) + 1.4), "D")
    view_title(ax2, 27.5, 43.1, "B", "B   Unit A slab on grade plan", "3/16\" = 1'-0\" · garage rear wall below shown grey · preliminary", 8.5)
    north_arrow(ax2, 47.4, 41.6, 1.5, 6)
    # ---- right column: quantities, details
    rx = L + 9.3
    bg.text(rx, 10.38, "QUANTITIES (computed from the model)", fontsize=7.4, fontweight="bold", va="center")
    rows = [("Slab", "Area", "Thick", "Concrete", "Stone")]
    rows.append(("Garage, incl. thick edge", f"{a_g:.0f} sf", "6 in.", f"{cy(a_g, SLAB_G) + extra:.1f} cy", f"{cy(a_g, STONE_G):.1f} cy"))
    rows.append(("Lobby and stair", f"{a_l:.0f} sf", "6 in.", f"{cy(a_l, SLAB_G):.1f} cy", f"{cy(a_l, STONE_G):.1f} cy"))
    rows.append(("Utility room", f"{a_u:.0f} sf", "6 in.", f"{cy(a_u, SLAB_G):.1f} cy", f"{cy(a_u, STONE_G):.1f} cy"))
    tg = a_g + a_l + a_u
    rows.append(("Garage level total", f"{tg:.0f} sf", "", f"{cy(tg, SLAB_G) + extra:.1f} cy", f"{cy(tg, STONE_G):.1f} cy"))
    rows.append(("Unit A slab on grade", f"{a_s:.0f} sf", "5 in.", f"{cy(a_s, SLAB_A):.1f} cy", f"{cy(a_s, STONE_A):.1f} cy"))
    yb = table(bg, rx, 10.22, [1.42, 0.56, 0.48, 0.62, 0.56], rows, fs=5.5, rh=0.18)
    bg.text(rx, yb - 0.13, f"Net of walls. Add waste. R-10 foam and vapour barrier under Unit A slab: {a_s:.0f} sf.", fontsize=5.2, color=GREY, va="center")
    bg.text(rx, yb - 0.27, f"Unit A slab outline to the outside of the walls: {poly_area(m.SOG):.0f} sf.", fontsize=5.2, color=GREY, va="center")
    vtitle(bg, rx, 8.42, "C", "Slab edge and trench drain at the opening", "3/4\" = 1'-0\" · looking west · preliminary")
    trench_detail(fig, rx - 0.02, 6.2)
    vtitle(bg, rx, 5.82, "D", "Section through the Unit A slab on grade", "3/8\" = 1'-0\" · cut at bath 2, looking west · preliminary")
    sog_section(fig, rx - 0.02, 3.1)
    keys = [
        "Garage rear wall: 6 in. truss ledge on the garage side, 6 in. upstand on the soil side to the underside of the slab.",
        "5 in. slab bears on the upstand and spans the backfill strip: #4 at 12 in. bottom, hooked #4 dowels at 16 in. (prelim.). Mesh or #3 at 18 in. elsewhere.",
        "Under the slab: 15-mil vapour barrier, R-10 rigid foam (2 in.), 4 in. stone. R-10 also at the slab edge against the stem wall.",
        "Floor trusses bear on a treated 2x6 sill, 5/8 in. anchor bolts at 32 in. This connection props the top of the wall (S-102).",
        "Wall backfill compacted in 8 in. lifts to 95 % before the slab.",
        "8 in. stem wall, 8 in. min. above finish grade, damp-proofed where it holds soil; R-15 inside above the floor (A-501).",
        "Bath 2 drains pass through a sleeve in the upstand, between trusses, to chase 2 (P-101).",
    ]
    ky = 2.86
    for i, k in enumerate(keys):
        lines = textwrap.wrap(k, 72)
        bg.add_patch(plt.Circle((rx + 0.08, ky - 0.045), 0.078, fc=PAPER, ec=INK, lw=0.5))
        bg.text(rx + 0.08, ky - 0.05, str(i + 1), fontsize=4.8, fontweight="bold", ha="center", va="center")
        bg.text(rx + 0.22, ky, "\n".join(lines), fontsize=5.2, va="top", linespacing=1.22)
        ky -= 0.104 * len(lines) + 0.07
    if ky < 0.45:
        print("WARNING: S-103 keynotes run off the sheet", ky)
    save(fig, "S-103", pdf)


# ----------------------------------------------------------------------------
# S-104
# ----------------------------------------------------------------------------
def b1_loads():
    """Plain tributary numbers for the longer (west) span of B1. Returns rows and totals in plf."""
    xm = (m.COL_X[0] + m.COL_X[1]) / 2
    span_a = (m.Y_GR_I + 0.25) - m.B1_Y
    a_c = m.B1_Y - m.PORCH[1]
    span_b = m.yr_o(xm) - m.EXT / _cr / 2 - (m.YF + m.EXT / 2)
    b_c = (m.YF + m.EXT / 2) - m.PORCH[1]
    oh = 4.0
    kc_a = a_c * (1 + a_c / (2 * span_a))
    kc_b = b_c * (1 + b_c / (2 * span_b))
    kr = span_b / 2 + oh * (1 + oh / (2 * span_b))
    rows = [
        (f"Unit A floor, half of {ftin(span_a)}", f"{span_a / 2:.1f} ft", 15 * span_a / 2, 40 * span_a / 2, 0),
        (f"Unit A porch, {ftin(a_c)} cantilever", f"{kc_a:.1f} ft", 15 * kc_a, 60 * kc_a, 0),
        (f"Unit B floor, half of {ftin(span_b)}", f"{span_b / 2:.1f} ft", 15 * span_b / 2, 40 * span_b / 2, 0),
        (f"Unit B porch, {ftin(b_c)} cantilever", f"{kc_b:.1f} ft", 15 * kc_b, 60 * kc_b, 0),
        ("Roof, half span + 4 ft overhang", f"{kr:.1f} ft", 15 * kr, 0, 30 * kr),
        ("Front walls, two storeys", "18 ft x 10 psf", 180, 0, 0),
        ("Beam and nailer", "", 40, 0, 0),
    ]
    D, Lv, S = (sum(r[i] for r in rows) for i in (2, 3, 4))
    return rows, D, Lv, S


def detail_bearing(fig, left, bottom):
    ax = plan_axes(fig, left, bottom, (-2.05, 1.75), (-1.25, 2.05), 1.0)
    d, tf = W14["d"], W14["tf"]
    seat = -(PLATE + 0.75 * IN)
    poly(ax, [(-2.05, -1.25), (0, -1.25), (0, seat), (-0.5, seat), (-0.5, d), (-2.05, d)], fc=CONC, ec=INK, lw=0.9, z=3)
    rect(ax, -0.5, seat, 0, -PLATE, fc="#7d848c", ec=INK, lw=0.4, z=4)
    rect(ax, -0.5, -PLATE, 0, 0, fc=STEEL, ec=INK, lw=0.5, z=5)
    rect(ax, -0.46, 0, 1.75, d, fc="#dbe6f3", ec=STEEL, lw=1.0, z=4)
    for y in (tf, d - tf):
        line(ax, [(-0.46, y), (1.75, y)], lw=0.6, color=STEEL, z=5)
    line(ax, [(-0.25, -0.85), (-0.25, tf + 0.1)], lw=1.1, color=INK, z=6)
    line(ax, [(-0.25, -0.85), (-0.45, -0.85)], lw=1.1, color=INK, z=6)
    rect(ax, -0.31, tf, -0.19, tf + 0.06, fc=INK, ec=INK, z=7)
    rect(ax, -2.05, d, -0.5, d + SILL, fc=WOODC, ec=INK, lw=0.5, z=5)
    rect(ax, -0.46, d, 1.75, d + SILL, fc=WOODC, ec=INK, lw=0.5, z=5)
    rect(ax, -2.05, d + SILL, 1.75, 2.05, fc="#faf7ef", ec="none", z=2)
    line(ax, [(-2.05, d + SILL), (1.75, d + SILL)], lw=0.5, z=5)
    for x in (-1.5, 0.5):
        rect(ax, x, d + SILL, x + 3.5 * IN, 2.05, fc=WOODC, ec=INK, lw=0.4, z=4)
    txt(ax, -0.45, 1.78, "FLOOR TRUSSES OVER (S-201)", size=4.6, color=GREY)
    dim(ax, (-0.5, -0.42), (0, -0.42), 0, "6\"", ext=False, size=4.8, side=-1)
    lead(ax, (0.9, d * 0.5), (0.55, -0.55), "B1  W14x34", size=5.2, color=STEEL, weight="bold", va="top", ha="left")
    lead(ax, (-0.1, -PLATE / 2), (0.3, -0.95), "3/4 in. BEARING PLATE 7 x 6 in.\non 3/4 in. non-shrink grout", size=4.6, va="center")
    lead(ax, (-0.25, 0.25), (-1.95, 0.55), "2 ANCHOR RODS\n3/4 in., 9 in. embed,\nslotted holes", size=4.6, ha="left")
    lead(ax, (-0.48, 0.9), (-1.95, 1.0), "1/2 in. GAP at the\nbeam end", size=4.6, ha="left")
    lead(ax, (1.2, d + SILL / 2), (0.75, 1.52), "2x8 NAILER on the steel", size=4.6, va="bottom", ha="left")
    lead(ax, (-1.2, d + SILL / 2), (-1.95, 1.52), "SILL PLATE", size=4.6, va="bottom", ha="left")
    txt(ax, -1.25, -0.4, "CONCRETE RETURN\nPIER, 12 in. thick\n(extra ties under\nthe seat: engineer)", size=4.6, z=9)
    return ax


def detail_cap(fig, left, bottom):
    """Section across B1 at the post, looking west: south (porch) to the left."""
    ax = plan_axes(fig, left, bottom, (-1.75, 1.55), (-1.25, 2.05), 1.0)
    d, bf, tf, tw = W14["d"], W14["bf"], W14["tf"], W14["tw"]
    I = [(-bf / 2, 0), (bf / 2, 0), (bf / 2, tf), (tw / 2, tf), (tw / 2, d - tf), (bf / 2, d - tf), (bf / 2, d), (-bf / 2, d),
         (-bf / 2, d - tf), (-tw / 2, d - tf), (-tw / 2, tf), (-bf / 2, tf)]
    poly(ax, I, fc=STEEL, ec=INK, lw=0.6, z=5)
    rect(ax, -bf / 2, tf, bf / 2, d - tf, fc="none", ec=STEEL, lw=0.5, z=4, ls=(0, (3, 2)))
    rect(ax, -3.5 * IN, -PLATE, 3.5 * IN, 0, fc="#7d848c", ec=INK, lw=0.5, z=5)
    rect(ax, -0.25, -1.25, 0.25, -PLATE, fc="#dbe6f3", ec=STEEL, lw=1.0, z=4)
    for x in (-0.25 + 0.375 * IN, 0.25 - 0.375 * IN):
        line(ax, [(x, -1.25), (x, -PLATE)], lw=0.4, color=STEEL, z=5)
    for x in (-1.75 * IN, 1.75 * IN):
        line(ax, [(x, -PLATE - 0.07), (x, tf + 0.07)], lw=0.9, color=INK, z=6)
    rect(ax, -3.625 * IN, d, 3.625 * IN, d + SILL, fc=WOODC, ec=INK, lw=0.5, z=5)
    line(ax, [(1.2 * IN, d - tf - 0.05), (1.2 * IN, d + SILL + 0.04)], lw=0.9, z=6)
    # truss over (side view), cut by a break line
    y0 = d + SILL
    rect(ax, -1.75, y0, 1.55, y0 + 0.125, fc=WOODC, ec=INK, lw=0.5, z=4)
    rect(ax, -0.0625, y0 + 0.125, 0.0625, 2.05, fc=WOODC, ec=INK, lw=0.4, z=4)
    for a, b in ((-1.6, -0.1), (0.1, 1.45)):
        line(ax, [(a, y0 + 0.125), ((a + b) / 2, 2.05)], lw=0.5, color=GREY, z=3)
        line(ax, [(b, y0 + 0.125), ((a + b) / 2, 2.05)], lw=0.5, color=GREY, z=3)
    break_line(ax, (-1.75, 1.98), (1.55, 1.98))
    txt(ax, -1.72, 1.02, "PORCH SIDE\n(south)", size=4.6, color=GREY, ha="left")
    txt(ax, 1.5, 1.02, "GARAGE SIDE\n(north)", size=4.6, color=GREY, ha="right")
    arrow(ax, (-0.6, 1.72), (-1.6, 1.72), color=GREY, lw=0.6)
    txt(ax, -1.1, 1.82, "cantilever 4'-0\"", size=4.4, color=GREY)
    lead(ax, (bf / 2 - 0.05, 0.45), (0.62, 0.5), "B1  W14x34\nstiffeners over the\npost if required", size=4.6, ha="left")
    lead(ax, (3.5 * IN, -PLATE / 2), (0.62, -0.28), "3/4 in. CAP PLATE 7 x 14 in.\n4 bolts 3/4 in. A325,\nbeyond the HSS faces", size=4.6, ha="left")
    lead(ax, (0.25, -0.95), (0.62, -0.95), "HSS 6x6x3/8 POST", size=4.6, ha="left", weight="bold", color=STEEL)
    lead(ax, (-3.625 * IN, d + SILL / 2), (-1.7, 0.45), "2x8 TREATED NAILER,\n1/2 in. bolts at 24 in.,\nstaggered, through the\ntop flange", size=4.6, ha="left", va="top")
    lead(ax, (0.9, y0 + 0.06), (0.62, 1.55), "20 in. FLOOR TRUSS, bears on\nthe nailer; clip each truss", size=4.6, ha="left", va="bottom")
    dim(ax, (-bf / 2, -0.55), (bf / 2, -0.55), 0, "6 3/4\" FLANGE", ext=False, size=4.4, side=-1)
    return ax


def detail_base(fig, left, bottom):
    ax = plan_axes(fig, left, bottom, (-2.45, 2.45), (-2.55, 0.75), 1.0)
    ft_top = -(SLAB_G + STONE_G)
    rect(ax, -2.45, -2.55, 2.45, ft_top, fc=SOIL, ec="none", z=1)
    rect(ax, -2.45, ft_top, 2.45, -SLAB_G, fc=STONE, ec="none", z=2, hatch="ooo")
    rect(ax, -2.45, -SLAB_G, -0.83, 0, fc=CONC, ec=INK, lw=0.7, z=4)
    rect(ax, 0.83, -SLAB_G, 2.45, 0, fc=CONC, ec=INK, lw=0.7, z=4)
    rect(ax, -0.83, ft_top, 0.83, 0, fc="#d5d8dc", ec=RED, lw=0.7, z=3.5)
    rect(ax, -PAD / 2, ft_top - PAD_T, PAD / 2, ft_top, fc=CONC, ec=INK, lw=0.9, z=4)
    rect(ax, -7 * IN, ft_top, 7 * IN, ft_top + GROUT, fc="#7d848c", ec=INK, lw=0.4, z=5)
    rect(ax, -7 * IN, ft_top + GROUT, 7 * IN, ft_top + GROUT + PLATE, fc=STEEL, ec=INK, lw=0.5, z=6)
    rect(ax, -0.25, ft_top + GROUT + PLATE, 0.25, 0.75, fc="#dbe6f3", ec=STEEL, lw=1.0, z=6)
    for x in (-0.25 + 0.375 * IN, 0.25 - 0.375 * IN):
        line(ax, [(x, ft_top + GROUT + PLATE), (x, 0.75)], lw=0.4, color=STEEL, z=7)
    for x in (-5 * IN, 5 * IN):
        line(ax, [(x, ft_top - 0.95), (x, ft_top + GROUT + PLATE + 0.1)], lw=1.1, z=7)
        line(ax, [(x, ft_top - 0.95), (x + (0.18 if x < 0 else -0.18), ft_top - 0.95)], lw=1.1, z=7)
    line(ax, [(-1.75, ft_top - PAD_T + 0.29), (1.75, ft_top - PAD_T + 0.29)], lw=0.9, color=RED, z=8)
    rebar_dots(ax, [(x, ft_top - PAD_T + 0.34) for x in np.arange(-1.5, 1.6, 1.0)], 0.03)
    dim(ax, (-PAD / 2, ft_top - PAD_T), (PAD / 2, ft_top - PAD_T), -0.16, f"{ftin(PAD)} SQUARE PAD F2", ext=False, size=4.8, side=-1)
    dim(ax, (-2.2, ft_top - PAD_T), (-2.2, ft_top), 0, "14\"", ext=False, size=4.6)
    eltag(ax, -2.4, 0.07, f"SLAB EL {EL_TD + (m.B1_Y - Y_TD) / 96:.2f} HERE", size=4.6, w=0.0)
    eltag(ax, 1.05, ft_top - 0.12, f"TOP OF PAD EL {m.EL_FTG_TOP:.2f}", size=4.6, w=0.0)
    lead(ax, (0.25, 0.45), (0.62, 0.52), "HSS 6x6x3/8 POST", size=4.6, weight="bold", color=STEEL)
    lead(ax, (7 * IN, ft_top + GROUT + PLATE / 2), (1.0, -0.72), "3/4 in. BASE PLATE 14 x 14 in.\non 1 in. non-shrink grout", size=4.6)
    lead(ax, (-5 * IN, ft_top - 0.6), (-2.4, -1.72), "4 ANCHOR RODS 3/4 in.,\n12 in. embed, at 10 in.", size=4.6, ha="left")
    lead(ax, (-0.6, -0.3), (-2.4, 0.45), "BLOCK-OUT filled with concrete after grouting:\nthe base is encased. Isolation joint all round.", size=4.6, ha="left")
    lead(ax, (1.2, ft_top - PAD_T + 0.29), (0.95, -1.62), "#5 at 12 in. each way,\nbottom (prelim.)", size=4.6, va="center")
    lead(ax, (1.8, -0.75), (1.0, -0.2), "6 in. slab on\n6 in. stone", size=4.6, va="bottom")
    return ax


def sheet_s104(pdf):
    rows, D, Lv, S = b1_loads()
    w_all = (D + Lv + S) / 1000
    w_asd = max(D + Lv, D + 0.75 * Lv + 0.75 * S) / 1000
    L1, L2 = m.COL_X[1] - m.COL_X[0], m.COL_X[2] - m.COL_X[1]
    blen = BEAM_X1 - BEAM_X0
    r_post_s = w_asd * (L1 + L2) / 2
    mint = w_asd * (L1 ** 3 + L2 ** 3) / (8 * (L1 + L2))
    r_post_c = r_post_s + mint * (1 / L1 + 1 / L2)
    r_w, r_e = w_asd * L1 / 2, w_asd * L2 / 2
    m_ss = w_asd * L1 ** 2 / 8
    cap = PAD * PAD * 2.0
    need = math.sqrt(r_post_c / 2.0)
    notes = tbn(
        ("Preliminary",
         "W14x34 and HSS 6x6x3/8 are assumptions for pricing. A WV structural engineer sizes the beam, post, plates, "
         "anchors and footings and seals them. Spans and levels are from the model."),
        ("Nailer and bearing level",
         f"The model sets top of steel at EL {m.EL_B1_TOP:.2f}, the underside of the trusses, with no room for the "
         f"1 1/2 in. nailer. Fix before shop drawings: drop B1 to top of steel EL {EL_TOC:.2f} (clear height "
         f"{ftin(m.OPEN_CLEAR_H - SILL)}), or omit the nailer."),
        ("Fire and corrosion",
         "B1 and the post hold up the dwelling above an open garage: engineer and architect to specify intumescent "
         "paint or a gypsum wrap as the code requires.",
         "Exterior exposure and road salt: hot-dip galvanise, or shop prime and finish paint. Touch up after "
         "erection."),
        ("Steel fabricator",
         "Shop drawings required, reviewed by the engineer before fabrication. Field-verify the concrete seats and "
         "anchor rods first. Erect, plumb and grout before the floor trusses are loaded."),
    )
    fig, bg = new_sheet("S-104", two_line(TITLE["S-104"]), "As noted", notes)
    L = MARGIN + 0.3
    vx = (3.0, 50.0)
    # ---- A: plan
    ax = frame(fig, (vx, (3.6, 15.4)), L, 8.02, lot=False)
    lower_plan(ax, "bg", cars=False)
    for k in ("F1", "F2", "F2E"):
        spoly(ax, G[k].intersection(box(0, 0, 60, 15.4)), fc="none", ec=GREY, lw=0.5, z=6.5, ls=DASH)
    spoly(ax, G["RW"].intersection(box(0, 0, 60, 15.4)), fc=CONC, ec=INK, lw=0.8, z=6)
    spoly(ax, G["IW"].intersection(box(0, 0, 60, 15.4)), fc="#c3c7cc", ec=INK, lw=0.6, z=6)
    rect(ax, *m.PORCH[:2], *m.PORCH[2:], fc="none", ec=GREY, lw=0.6, z=5, ls=(0, (6, 3)))
    rect(ax, BEAM_X0, m.B1_Y - W14["bf"] / 2, BEAM_X1, m.B1_Y + W14["bf"] / 2, fc=STEEL, ec=INK, lw=0.5, z=8)
    cx = m.COL_X[1]
    rect(ax, cx - 0.25, m.B1_Y - 0.25, cx + 0.25, m.B1_Y + 0.25, fc=PAPER, ec=INK, lw=1.2, z=9)
    for x in m.COL_X:
        line(ax, [(x, m.B1_Y - 1.0), (x, m.B1_Y + 1.0)], lw=0.4, ls=(0, (6, 2, 1, 2)), z=10)
    y1 = -(m.YF - 5.6)
    dim(ax, (m.COL_X[0], m.YF), (m.COL_X[1], m.YF), y1, f"{ftin(L1)}  CENTRE OF BEARING TO CENTRE OF POST", size=5.0)
    dim(ax, (m.COL_X[1], m.YF), (m.COL_X[2], m.YF), y1, ftin(L2), size=5.0)
    dim(ax, (BEAM_X0, m.YF), (BEAM_X1, m.YF), -(m.YF - 4.3), f"{ftin(blen)}  B1 OVERALL", size=5.0)
    dim(ax, (m.PORCH[0] + 2.5, m.PORCH[1]), (m.PORCH[0] + 2.5, m.YF), 0, ftin(m.YF - m.PORCH[1]), ext=False, size=4.6)
    txt(ax, 21.5, 8.2, "PORCH ABOVE: floor trusses cantilever over B1", size=4.6, color=GREY)
    lead(ax, (17.0, m.B1_Y + 0.25), (13.0, 13.4), f"B1  W14x34 (prelim.), centre line {ftin(m.B1_Y - m.YF)} north of the building face, TOP OF STEEL EL {m.EL_B1_TOP:.2f}", size=4.8, color=STEEL, weight="bold")
    lead(ax, (cx + 0.3, m.B1_Y + 0.3), (30.0, 12.2), "HSS 6x6x3/8 POST on pad F2", size=4.6)
    for x, tag in ((m.COL_X[0], "1"), (cx, "2"), (cx, "3")):
        pass
    cut_mark(ax, (m.COL_X[0] - 1.6, 11.9), (m.COL_X[0] - 1.6, 11.9), "1")
    cut_mark(ax, (cx - 1.4, 12.6), (cx - 1.4, 12.6), "2")
    cut_mark(ax, (cx - 2.6, 12.6), (cx - 2.6, 12.6), "3")
    txt(ax, 4.6, 12.2, "details", size=4.2, color=GREY)
    vtitle(bg, L, 10.42, "A", "Plan of beam B1 over the garage opening", "3/16\" = 1'-0\" · steel blue · footings dashed · preliminary")
    # ---- B: elevation looking north
    yv = (910.9, 927.4)
    ax2 = plan_axes(fig, L, 4.48, vx, yv, FPI)
    xs_ = np.linspace(vx[0], vx[1], 60)
    gl = [(x, elev(x, m.YF - 0.5)) for x in xs_]
    poly(ax2, [(vx[0], yv[0])] + gl + [(vx[1], yv[0])], fc="#f7f3ec", ec="none", z=0.5)
    rect(ax2, m.xw_gi(m.YF), yv[0], m.XE_GI, 927.4, fc=PAPER, ec="none", z=0.8)
    rect(ax2, vx[0], yv[0], vx[1], EL_F1_BOT, fc="#f7f3ec", ec="none", z=0.9)
    line(ax2, gl, color=EARTH, lw=0.8, ls=(0, (5, 2)), z=6)
    # footings
    rect(ax2, wx(m.YF, HEEL), EL_F1_BOT, m.OPEN[0] + 1.0, m.EL_FTG_TOP, fc=CONC, ec=INK, lw=0.6, z=3)
    rect(ax2, cx - PAD / 2, m.EL_FTG_TOP - PAD_T, cx + PAD / 2, m.EL_FTG_TOP, fc=CONC, ec=INK, lw=0.6, z=3)
    rect(ax2, m.COL_X[2] - BRG_PAD / 2, m.EL_FTG_TOP - BRG_PAD_T, m.XE_GI - TOE, m.EL_FTG_TOP, fc=CONC, ec=INK, lw=0.6, z=3)
    rect(ax2, m.XE_GI - TOE, EL_F1_BOT, m.XE + HEEL, m.EL_FTG_TOP, fc=CONC, ec=INK, lw=0.6, z=3)
    # slab and stone
    rect(ax2, m.OPEN[0], m.EL_GAR - SLAB_G, m.XE_GI, m.EL_GAR, fc="#d5d8dc", ec=INK, lw=0.5, z=2.5)
    # concrete pier (west) and lobby walls (east)
    seat = EL_SOFFIT - PLATE - 0.75 * IN
    poly(ax2, [(m.xw_o(m.YF), m.EL_FTG_TOP), (m.OPEN[0], m.EL_FTG_TOP), (m.OPEN[0], seat), (BEAM_X0, seat), (BEAM_X0, EL_TOC), (m.xw_o(m.YF), EL_TOC)],
         fc=CONC, ec=INK, lw=0.9, z=4)
    rect(ax2, m.GAR_X1, m.EL_FTG_TOP, m.SHAFT_X0, seat, fc=CONC, ec=INK, lw=0.9, z=4)
    rect(ax2, m.SHAFT_X0, m.EL_FTG_TOP, m.XE_GI, EL_TOC, fc="#c3c7cc", ec=INK, lw=0.7, z=4)
    rect(ax2, m.XE_GI, m.EL_FTG_TOP, m.XE, EL_TOC, fc=CONC, ec=INK, lw=0.9, z=4)
    rect(ax2, m.ENTRY[0], m.EL_GAR, m.ENTRY[1], m.EL_GAR + 6.667, fc=PAPER, ec=INK, lw=0.5, z=5)
    txt(ax2, (m.ENTRY[0] + m.ENTRY[1]) / 2, m.EL_GAR + 3.3, "ENTRY\nDOOR", size=4.4, color=GREY, z=6)
    # steel
    rect(ax2, BEAM_X0, EL_SOFFIT, BEAM_X1, m.EL_B1_TOP, fc=STEEL, ec=INK, lw=0.5, z=6)
    rect(ax2, cx - 0.25, m.EL_FTG_TOP + GROUT + PLATE, cx + 0.25, EL_SOFFIT - PLATE, fc=STEEL, ec=INK, lw=0.5, z=6)
    rect(ax2, cx - 7 * IN, m.EL_FTG_TOP, cx + 7 * IN, m.EL_FTG_TOP + GROUT + PLATE, fc=INK, ec=INK, z=6)
    rect(ax2, cx - 7 * IN, EL_SOFFIT - PLATE, cx + 7 * IN, EL_SOFFIT, fc=INK, ec=INK, z=7)
    # floor and wall above
    rect(ax2, m.xw_o(m.YF), m.EL_B1_TOP, m.XE, m.EL_A, fc="#f3ead6", ec=INK, lw=0.6, z=5)
    rect(ax2, m.xw_o(m.YF), m.EL_A, m.XE, yv[1], fc="#fbfaf7", ec=GREY, lw=0.5, z=3)
    txt(ax2, 22.0, (m.EL_B1_TOP + m.EL_A) / 2, "UNIT A FLOOR: 20 in. TRUSSES SIT ON TOP OF B1 (ON A NAILER) AND CANTILEVER 4'-0\" TOWARD YOU FOR THE PORCH", size=4.6, z=8)
    txt(ax2, 22.0, 926.5, "UNIT A FRONT WALL (2x6), UNIT B AND ROOF ABOVE", size=4.6, color=GREY, z=8)
    # dimensions
    yd = 921.3
    dim(ax2, (m.COL_X[0], yd), (m.COL_X[1], yd), 0, f"{ftin(L1)} SPAN", ext=False, size=5.0, color=STEEL)
    dim(ax2, (m.COL_X[1], yd), (m.COL_X[2], yd), 0, f"{ftin(L2)} SPAN", ext=False, size=5.0, color=STEEL)
    for x in (m.COL_X[0], m.COL_X[2]):
        line(ax2, [(x, yd - 0.4), (x, EL_SOFFIT)], lw=0.4, color=STEEL, ls=(0, (6, 2, 1, 2)), z=9)
    dim(ax2, (m.OPEN[0], 916.3), (m.OPEN[1], 916.3), 0, f"{ftin(m.OPEN_W)} CLEAR OPENING, NO DOORS", ext=False, size=5.0)
    dim(ax2, (18.5, m.EL_GAR), (18.5, EL_SOFFIT), 0, f"{ftin(m.OPEN_CLEAR_H)} CLEAR", ext=False, size=5.0)
    dim(ax2, (cx + 1.3, m.EL_FTG_TOP + GROUT + PLATE), (cx + 1.3, EL_SOFFIT - PLATE), 0, f"POST {ftin(POST_LEN)}", ext=False, size=4.8, side=-1)
    xr = m.XE + 0.5
    eltag(ax2, xr, m.EL_A, f"UNIT A FLOOR EL {m.EL_A:.2f}", size=4.6, w=0.6)
    eltag(ax2, xr, m.EL_B1_TOP - 0.1, f"TOP OF STEEL EL {m.EL_B1_TOP:.2f}", size=4.6, w=0.6, color=STEEL)
    eltag(ax2, xr, EL_SOFFIT - 0.2, f"UNDERSIDE EL {EL_SOFFIT:.2f}", size=4.6, w=0.6, color=STEEL)
    eltag(ax2, xr + 2.1, m.EL_GAR + 0.1, f"SLAB {m.EL_GAR:.2f}", size=4.4, w=0.3)
    eltag(ax2, xr + 2.1, m.EL_FTG_TOP - 0.55, f"FTG {m.EL_FTG_TOP:.2f}", size=4.4, w=0.3)
    lead(ax2, (9.0, 918.5), (4.2, 915.2), f"CONCRETE\nRETURN PIER\n{ftin(m.OPEN[0] - m.xw_o(m.YF))} x 12 in.", size=4.4, ha="center", va="top", box=True)
    txt(ax2, 5.0, 924.2, "existing ground at\nthe front wall (LiDAR)", size=4.2, color=EARTH)
    lead(ax2, (m.COL_X[2], 919.0), (34.6, 918.4), "8 in. LOBBY\nWALL CORNER", size=4.4, ha="right")
    txt(ax2, cx, m.EL_FTG_TOP - PAD_T - 0.5, f"F2 PAD {ftin(PAD)} SQ.", size=4.4, z=8)
    for x, tag in ((BEAM_X0 + 0.2, "1"), (cx, "2")):
        ax2.add_patch(plt.Circle((x, EL_SOFFIT - 0.1), 0.95, fc="none", ec=RED, lw=0.8, zorder=9))
    txt(ax2, BEAM_X0 - 1.6, EL_SOFFIT - 1.3, "1", size=5.4, weight="bold", color=RED)
    txt(ax2, cx - 1.5, EL_SOFFIT - 1.3, "2", size=5.4, weight="bold", color=RED)
    ax2.add_patch(plt.Circle((cx, m.EL_FTG_TOP + 0.1), 0.95, fc="none", ec=RED, lw=0.8, zorder=9))
    txt(ax2, cx - 1.5, m.EL_FTG_TOP + 1.2, "3", size=5.4, weight="bold", color=RED)
    vtitle(bg, L, 7.78, "B", "Elevation of B1, looking north from the street", "3/16\" = 1'-0\" · red circles = details 1 to 3 · preliminary")
    # ---- right column: loads and steel list
    rx = L + 9.12
    bg.text(rx, 10.42, "WHAT B1 CARRIES (west span, plain numbers)", fontsize=7.4, fontweight="bold", va="center")
    trows = [("Load", "Tributary", "Dead", "Live", "Snow")]
    for r in rows:
        trows.append((r[0], r[1], f"{r[2]:.0f}", f"{r[3]:.0f}" if r[3] else "", f"{r[4]:.0f}" if r[4] else ""))
    trows.append(("Total, lb per ft of beam", "", f"{D:.0f}", f"{Lv:.0f}", f"{S:.0f}"))
    yb = table(bg, rx, 10.26, [1.62, 0.78, 0.42, 0.42, 0.42], trows, fs=5.3, rh=0.165)
    info = [
        f"Floors 15 dead + 40 live psf; porches 60 live; roof 15 dead + 30 snow.",
        f"Everything at once: {w_all:.1f} kips per ft. Code combination (dead + 0.75 live",
        f"+ 0.75 snow): about {w_asd:.1f} kips per ft. ENGINEER TO CALCULATE.",
        f"Rough reactions at {w_asd:.1f} k/ft: west pier {r_w:.0f} k, post {r_post_s:.0f} k (two simple",
        f"spans) to {r_post_c:.0f} k (one continuous beam), lobby wall {r_e:.0f} k.",
        f"Moment on the {ftin(L1)} span about {m_ss:.0f} kip-ft; a braced W14x34 allows",
        "about 136 kip-ft, so it works for gravity on paper.",
        f"PAD F2: {ftin(PAD)} square carries {cap:.0f} k at 2,000 psf. A continuous beam",
        f"needs about {ftin(need)} square. Expect the pad to grow (engineer).",
    ]
    for i, s in enumerate(info):
        bg.text(rx, yb - 0.15 - i * 0.132, s, fontsize=5.3, va="center", color=RED if s.startswith("PAD") or s.startswith("needs") else INK)
    ys = yb - 0.15 - len(info) * 0.132 - 0.2
    bg.text(rx, ys, "STEEL LIST (preliminary, for pricing)", fontsize=7.4, fontweight="bold", va="center")
    plate_lb = lambda a, b, t=0.75: a * b * t * 0.2836
    w_b1, w_p = blen * W14["plf"], POST_LEN * HSS_PLF
    w_pl = plate_lb(7, 14) + plate_lb(14, 14) + plate_lb(7, 6) + plate_lb(7, 8)
    w_ar = 8 * 1.25 * 1.5
    srows = [("Mark", "Item", "Length", "Weight"),
             ("B1", "W14x34, A992", ftin(blen), f"{w_b1:.0f} lb"),
             ("P1", "HSS 6x6x3/8, A500 Gr. C", ftin(POST_LEN), f"{w_p:.0f} lb"),
             ("PL1", "Cap plate 3/4 x 7 x 14 in.", "1", f"{plate_lb(7, 14):.0f} lb"),
             ("PL2", "Base plate 3/4 x 14 x 14 in.", "1", f"{plate_lb(14, 14):.0f} lb"),
             ("PL3", "Bearing plates 3/4 x 7 x 6 and 7 x 8 in.", "2", f"{plate_lb(7, 6) + plate_lb(7, 8):.0f} lb"),
             ("AR", "Anchor rods 3/4 in. F1554 Gr. 36", "8", f"{w_ar:.0f} lb"),
             ("N1", "Nailer 2x8 treated, 1/2 in. bolts at 24 in.", ftin(blen), "wood"),
             ("", "Steel total, plus about 10 % for connections", "", f"{(w_b1 + w_p + w_pl + w_ar) * 1.1:.0f} lb")]
    yb2 = table(bg, rx, ys - 0.14, [0.36, 2.2, 0.55, 0.55], srows, fs=5.3, rh=0.165)
    bg.text(rx, yb2 - 0.13, "W14x34 = 34 lb/ft; HSS 6x6x3/8 = 27.5 lb/ft; plate 0.284 lb per cu. in.", fontsize=5.0, color=GREY, va="center")
    # ---- details
    yd0 = 0.62
    vtitle(bg, L, 4.2, "1", "Beam bearing on concrete", "1\" = 1'-0\" · west pier shown; east bearing on the 8 in. lobby wall corner similar, 8 in. long")
    detail_bearing(fig, L + 0.05, yd0)
    vtitle(bg, L + 4.2, 4.2, "2", "Post cap and nailer", "1\" = 1'-0\" · section across B1, looking west")
    detail_cap(fig, L + 4.2, yd0)
    vtitle(bg, L + 7.95, 4.2, "3", "Post base on pad footing F2", "1\" = 1'-0\"")
    detail_base(fig, L + 7.85, yd0)
    save(fig, "S-104", pdf)


SHEETS = [("S-001", sheet_s001), ("S-101", sheet_s101), ("S-102", sheet_s102), ("S-103", sheet_s103), ("S-104", sheet_s104)]
