"""390 Forest Ave mechanical: room-by-room heating and cooling loads (Manual J method, simplified and written out), equipment sizing,
ventilation and room airflow. Every number on sheets M-002 / M-003 comes from here; change an input and rebuild.

Geometry comes from the plan model (build390.LV): room rectangles, ceiling heights, windows (scan + additions), exterior doors.
Exterior walls are found by probing past each room edge: if the point beyond the wall is outside the level's outline, that edge is
exterior. Orientation from the building frame's north (draw_existing.FX)."""
import math
from functools import lru_cache
import os
import sys

import numpy as np
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build390 as b  # noqa: E402
import draw_existing as de  # noqa: E402
import b390_eq as q  # noqa: E402

# ---------------------------------------------------------------------------------------------- design conditions (confirm with Manual J Table 1A)
DES = dict(t_out_h=9, t_in_h=70, t_out_c=87, t_in_c=75, gr=30, zone="5A", place="Morgantown WV (Hart Field)")
DTH = DES["t_in_h"] - DES["t_out_h"]; DTC = DES["t_out_c"] - DES["t_in_c"]
# The owner's reported extremes last year. Manual J sizes to the 1 % / 99 % design values above (sizing to records oversizes); the equipment is
# then checked against these: furnaces must carry the heat loss at -15 F, and the variable-speed condensers at full speed must give at least
# 90 % of the 105 F load (indoor drifts a degree or two at the peak, no more).
EXTREME = dict(t_out_h=-15, t_out_c=105, gr=40)
CAP_105 = 0.92            # condenser output at 105 F outdoor as a share of its rating at 95 F (typical; check the unit's extended performance table)
MAX_CFM = 700             # 14 x 8 in. trunk at 900 fpm, the most the duct takes
# ---------------------------------------------------------------------------------------------- envelope after the gut (assumed: insulated while the walls are open)
U = dict(wall=0.070,       # 2x4 wall, R-15 high-density batts or dense-pack cellulose, siding and sheathing: effective about R-14
         stone=0.065,      # lower flat stone foundation wall with a new 2x4 wall inside it, R-15
         window=0.50,      # existing double-pane vinyl windows (kept); SHGC below
         door=0.35, ceil=0.026,   # attic flat ceiling and the eave floors over the upper flat's main floor: R-49 blown
         roof=0.026,       # attic sloped ceilings: R-38 closed-cell foam under the roof deck (fur the rafters if under 6 in. deep)
         knee=0.033)       # attic knee walls to the eave spaces: R-30 (2x6 knee walls, or 2x4 + 1-1/2 in. foam board)
SHGC = 0.55
F_SLAB = 0.55             # lower flat floor on earth: heat loss per ft of exterior wall per F
ACH_H, ACH_C = 0.35, 0.20 # natural air changes after air sealing during the gut (about 5 ACH50)
CLTD = dict(wall=20, stone=12, ceil=45, roof=50, knee=35, door=20)      # cooling temperature differences, F (medium wall, 87 F design, medium daily range)
SOLAR = {"N": 30, "NE": 45, "E": 70, "SE": 70, "S": 70, "SW": 120, "W": 150, "NW": 100}     # peak solar gain x CLF, Btu/h per sf of glass per unit SHGC
WIN_H = {3: 4.0, 4: 5.0, 5: 5.0, 6: 4.0}                                                 # window heights (scan gives widths only)
WIN_H_OVR = {(3, 27.4, 26.3): 1.5}                                                     # lower flat bedroom 2: small high basement window
WIN_EXTRA = {4: [(31.23, 18.45, 4.4, 4.0)]}                                             # middle flat kitchen: window over the counter (photo; scan shows an opening)
PEOPLE_S, PEOPLE_L, APPL_KIT, APPL_BED, LIGHT_W = 230, 200, 1200, 150, 0.3
NORTH = np.array(de.FX["north_in_building_frame"]); EAST = np.array([NORTH[1], -NORTH[0]])
SYSTEMS = {"A": dict(levels={3: None}, name="Lower flat"), "B": dict(levels={4: None}, name="Middle flat"),
           "C": dict(levels={5: None, 6: None}, name="Upper flat (main floor + attic)")}
NOT_SERVED = {"closet", "mech", "laundry"}
# Upper flat: two zones on one furnace and one condenser. Zone 1 main floor, zone 2 attic, each with its own thermostat; motorized dampers;
# modulating furnace and variable-speed condenser with the maker's communicating zoning, so no bypass damper. min_cfm: the least the
# equipment moves (about 40 % of 700 CFM), which zone 2's ducts must carry on their own.
ZONES = {"C": dict(levels=(6,), min_cfm=300)}
MERGE = {(5, "312"): (5, "306"),               # open stair: its load is supplied by the register in the hall it opens from
         (6, "403"): (6, "401"), (6, "404"): (6, "402")}   # attic baths: every wall is under the slope, the tub, the vanity or the door;
                                                 # their small load comes from the bedroom through a 3/4 in. door undercut, pulled by the bath fan
STAIR_HEATER = (4, "213")                       # the upper flat's entrance stair hall: electric wall heater (no duct can reach it without crossing the middle flat)


def bearing(n):
    v = np.array(n, float); ang = math.degrees(math.atan2(v @ EAST, v @ NORTH)) % 360
    return ["N", "NE", "E", "SE", "S", "SW", "W", "NW"][int(((ang + 22.5) % 360) // 45)]


def ceil_ft(fl, r):
    return q.ceil_ft(fl, r)


def flat_of(fl, r):
    return "C" if (fl == 4 and r["no"] == "213") else {3: "A", 4: "B", 5: "C", 6: "C"}[fl]


def ext_edges(fl, r):
    """Exterior wall runs of a room: [(length ft, outward normal, bearing, kind)]. kind: wall / stone / knee."""
    P = q.outline(fl); probe = 2.3 if fl == 3 else 1.4; out = []
    for (x0, y0, x1, y1) in r["rects"]:
        for (a, c0, c1, n) in ((y0, x0, x1, (0, -1)), (y1, x0, x1, (0, 1)), (x0, y0, y1, (-1, 0)), (x1, y0, y1, (1, 0))):
            L = 0.0
            for t in np.arange(c0 + .125, c1, .25):
                p = (t, a) if n[0] == 0 else (a, t)
                if not P.contains(Point(p[0] + n[0] * probe, p[1] + n[1] * probe)) and not any(
                        box(*qq).buffer(.05).contains(Point(p[0] + n[0] * .3, p[1] + n[1] * .3)) for qq in r["rects"]):
                    L += .25
            if L >= .5:
                kind = "stone" if fl == 3 else ("knee" if (fl == 6 and n[0] == 0) else "wall")
                out.append((L, n, bearing(n), kind))
    return out


def windows(fl):
    """All windows of a level: [(centre x, y, width ft, height ft)]."""
    g = b.geom(fl); out = []
    for o in g["windows"]:
        pts = np.array(o["pts"]); c = pts.mean(0); w = max(np.ptp(pts[:, 0]), np.ptp(pts[:, 1]))
        if w < .8: continue
        out.append((c[0], c[1], w, WIN_H_OVR.get((fl, round(c[0], 1), round(c[1], 1)), WIN_H[fl])))
    for w_ in b.LV[fl].get("win", []):
        poly = b.wshape(w_); pts = np.array(poly.exterior.coords[:-1]); c = pts.mean(0)
        w = max(math.dist(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts)))
        out.append((c[0], c[1], w, WIN_H[fl]))
    return out + WIN_EXTRA.get(fl, [])


def room_windows(fl, r):
    """Windows belonging to a room, with the bearing of the wall they sit in."""
    out = []
    for cx, cy, w, h in windows(fl):
        d = min(box(*qq).distance(Point(cx, cy)) for qq in r["rects"])
        if d > 1.6: continue
        best = min((rr for rr in b.LV[fl]["rooms"]), key=lambda rr: min(box(*qq).distance(Point(cx, cy)) for qq in rr["rects"]))
        if best is not r: continue
        # bearing: the room edge nearest the window
        cand = []
        for (x0, y0, x1, y1) in r["rects"]:
            cand += [(abs(cy - y0), (0, -1)), (abs(cy - y1), (0, 1)), (abs(cx - x0), (-1, 0)), (abs(cx - x1), (1, 0))]
        n = min(cand)[1]; out.append((cx, cy, w, h, n, bearing(n)))
    return out


def ext_doors(fl, r):
    out = []
    for d in b.LV[fl]["doors"]:
        if not d[8] or "entrance" not in d[8].lower(): continue
        w, a0, a1 = d[2], d[3], d[4]; p = ((a0 + a1) / 2, w) if d[1] == "h" else (w, (a0 + a1) / 2)
        if min(box(*qq).distance(Point(p)) for qq in r["rects"]) < .8:
            out.append((a1 - a0) * 6.67)
    return out


def rooms(fl):
    return [r for r in b.LV[fl]["rooms"] if not q.skip(r)]


def room_load(fl, r, flat_ach_cfm_share=None):
    """Heating and cooling (sensible) for one room, every component listed: dict with rows [(item, area or length, U or F, dT/CLTD, Btu/h heat, Btu/h cool)]."""
    A = sum((x1 - x0) * (y1 - y0) for x0, y0, x1, y1 in r["rects"]); hgt = ceil_ft(fl, r); vol = A * hgt
    rows = []; wins = room_windows(fl, r); drs = ext_doors(fl, r); edges = ext_edges(fl, r)
    for L, n, br, kind in edges:
        h_ = hgt if kind != "knee" else 5.7
        gross = L * h_
        wa = sum(w * h for cx, cy, w, h, nn, bb in wins if nn == n); da = sum(drs) if drs and kind != "knee" else 0
        net = max(0.0, gross - wa - da); u = U[kind]
        rows.append((f"{'Knee wall' if kind == 'knee' else 'Wall'} {br}", f"{net:.0f} sf", u, net * u * DTH, net * u * CLTD[kind]))
        drs = [] if da else drs
    for cx, cy, w, h, n, br in wins:
        a = w * h; rows.append((f"Window {br} {w:.1f} x {h:.1f}", f"{a:.0f} sf", U["window"], a * U["window"] * DTH, a * (U["window"] * DTC + SHGC * SOLAR[br])))
    for a in drs:
        rows.append(("Door", f"{a:.0f} sf", U["door"], a * U["door"] * DTH, a * U["door"] * CLTD["door"]))
    if fl == 6:
        rows.append(("Ceiling / roof", f"{A:.0f} sf", U["roof"], A * U["roof"] * DTH, A * U["roof"] * CLTD["roof"]))
    if fl == 5:                                  # ceiling under the attic's eave spaces (outside the attic rooms' footprint)
        expo = unary_union([box(*qq) for qq in r["rects"]]).difference(q.outline(6)).area
        if expo > 2: rows.append(("Ceiling under eave", f"{expo:.0f} sf", U["ceil"], expo * U["ceil"] * DTH, expo * U["ceil"] * CLTD["ceil"]))
    if fl == 3:
        per = sum(L for L, n, br, kind in edges)
        if per > 0: rows.append(("Floor on earth (perimeter)", f"{per:.0f} ft", F_SLAB, per * F_SLAB * DTH, 0.0))
    return dict(r=r, fl=fl, A=A, hgt=hgt, vol=vol, rows=rows, wins=wins, edges=edges,
                exp=sum(float(x[1].split()[0]) for x in rows if x[0].startswith(("Wall", "Window", "Knee", "Door"))))


def people(fl, r, f):
    k = r["kind"]
    if k == "bed": return 1
    if k == "living": return 1
    return 0


def internal(fl, r):
    k = r["kind"]; A = sum((x1 - x0) * (y1 - y0) for x0, y0, x1, y1 in r["rects"])
    s = LIGHT_W * A * 3.412 + (APPL_KIT if k == "kitchen" else 0) + (APPL_BED if k == "bed" else 0)
    return s


def _loads(k):
    """Room and system loads of one flat at the current design conditions."""
    S = SYSTEMS[k]; rl = []
    for fl, only in S["levels"].items():
        for r in rooms(fl):
            if fl == 4 and r["no"] == "213": continue             # the upper flat's stair hall: counted with system C
            rl.append(room_load(fl, r))
    if k == "C": rl.append(room_load(4, next(r for r in b.LV[4]["rooms"] if r["no"] == "213")))
    vol = sum(x["vol"] for x in rl); exp_tot = sum(x["exp"] for x in rl) or 1
    inf_h = ACH_H * vol / 60; inf_c = ACH_C * vol / 60
    f = q.FLATS[k]; beds = f["beds"]; Afl = q.AREA[k]
    vent = 0.03 * Afl + 7.5 * (beds + 1)                        # ASHRAE 62.2 / IRC M1505.4.3 continuous whole-house ventilation, CFM
    for x in rl:
        sh = x["exp"] / exp_tot
        x["inf_h"] = 1.08 * inf_h * sh * DTH; x["inf_c"] = 1.08 * inf_c * sh * DTC
        x["vent_h"] = 1.08 * vent * sh * DTH; x["vent_c"] = 1.08 * vent * sh * DTC
        x["int"] = internal(x["fl"], x["r"]) + PEOPLE_S * people(x["fl"], x["r"], k)
        x["H"] = sum(row[3] for row in x["rows"]) + x["inf_h"] + x["vent_h"]
        x["C"] = sum(row[4] for row in x["rows"]) + x["inf_c"] + x["vent_c"] + x["int"]
    npeople = beds + 1
    lat = 0.68 * (inf_c + vent) * DES["gr"] + PEOPLE_L * npeople
    H = sum(x["H"] for x in rl); Cs = sum(x["C"] for x in rl); Ct = Cs + lat
    return dict(rl=rl, vol=vol, inf_h=inf_h, inf_c=inf_c, vent=vent, lat=lat, H=H, Cs=Cs, Ct=Ct, npeople=npeople)


def extreme(k):
    """Loads of one flat at the reported extremes (-15 F, 105 F): same model, outdoor temperatures and wall/roof CLTDs moved up."""
    global DTH, DTC
    save = (dict(DES), DTH, DTC, dict(CLTD))
    try:
        DES.update(EXTREME); DTH = DES["t_in_h"] - DES["t_out_h"]; DTC = DES["t_out_c"] - DES["t_in_c"]
        for kk in CLTD: CLTD[kk] += EXTREME["t_out_c"] - save[0]["t_out_c"]
        return _loads(k)
    finally:
        DES.clear(); DES.update(save[0]); DTH, DTC = save[1], save[2]; CLTD.clear(); CLTD.update(save[3])


@lru_cache(None)
def system(k):
    """All loads of one flat (system): rooms, infiltration, ventilation, totals, equipment, room airflow."""
    D = _loads(k); X = extreme(k)
    rl, vol, inf_h, inf_c, vent, lat, H, Cs, Ct, npeople = (D[x] for x in ("rl", "vol", "inf_h", "inf_c", "vent", "lat", "H", "Cs", "Ct", "npeople"))
    # equipment (Manual S: cooling 90 to 115 % of the total load; furnace output at least the heat loss)
    tons_calc = next(t for t in (1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0) if t * 12000 >= Ct * 0.95)
    tons_min = max(1.5, tons_calc)                                # 1.5 ton is the smallest ducted split commonly made: variable speed so it turns down
    tons = tons_min
    while CAP_105 * tons * 12000 < 0.9 * X["Ct"]: tons += 0.5     # the reported 105 F: variable speed covers it at full speed, turns down on normal days
    furn = next(fz for fz in (40000, 60000, 80000) if fz * .96 >= max(H, X["H"]))
    cfm = int(round(min(400 * tons, MAX_CFM) / 25) * 25)
    for (fs, ns), (fh, nh) in MERGE.items():
        xs = next((x for x in rl if x["fl"] == fs and x["r"]["no"] == ns), None); xh = next((x for x in rl if x["fl"] == fh and x["r"]["no"] == nh), None)
        if xs and xh: xs["via"] = nh; xh["plus"] = xs
    eff = lambda x, key: x[key] + (x["plus"][key] if "plus" in x else 0.0)
    served = [x for x in rl if x["r"]["kind"] not in NOT_SERVED and (x["fl"], x["r"]["no"]) != STAIR_HEATER and "via" not in x and
              (eff(x, "H") > 300 or x["r"]["kind"] in ("bath",))]
    sH = sum(eff(x, "H") for x in served) or 1; sC = sum(eff(x, "C") for x in served) or 1
    for x in served:
        x["cfm_raw"] = max(eff(x, "H") / sH, eff(x, "C") / sC)
    tot = sum(x["cfm_raw"] for x in served)
    for x in served:
        x["cfm"] = max(30, int(round(cfm * x["cfm_raw"] / tot / 5) * 5))
    out = dict(k=k, rooms=rl, served=served, vol=vol, inf_h=inf_h, inf_c=inf_c, vent=vent, lat=lat, H=H, Cs=Cs, Ct=Ct, tons=tons, tons_calc=tons_calc, tons_min=tons_min,
               furn=furn, cfm=cfm, shr=Cs / Ct, npeople=npeople, ext=X, summer=None)
    for x in served: x["cfm_size"] = x["cfm"]
    if k in ZONES:                                                 # zone 2 alone must carry the equipment's lowest airflow
        z2 = [x for x in served if x["fl"] in ZONES[k]["levels"]]
        for x in z2: x["cfm_size"] = max(x["cfm"], int(math.ceil(ZONES[k]["min_cfm"] / len(z2) / 5) * 5))
    return out


_system_cache = {}


# ---------------------------------------------------------------------------------------------- top floor vs the floor with the thermostat
def _gain_at(x, T, dout):
    """Sensible gain of a room held at T (F) with the outdoor temperature dout above design: conduction falls as the room warms."""
    ua = c = 0.0; fixed = x["int"]
    for name, area, u, h, cl in x["rows"]:
        if name.startswith("Floor"): continue
        a = float(area.split()[0]); ua += a * u
        if name.startswith("Window"):
            c += a * u * (DTC + dout); fixed += a * SHGC * SOLAR[name.split()[1]]
        else:
            kind = "roof" if name.startswith("Ceiling / roof") else "knee" if name.startswith("Knee") else "ceil" if name.startswith("Ceiling under") else "door" if name.startswith("Door") else "wall"
            c += a * u * (CLTD[kind] + dout)
    air = (x["inf_c"] + x["vent_c"]) / (1.08 * DTC)
    return c - ua * (T - 75) + fixed + 1.08 * air * (DTC + dout - (T - 75))


def top_floor(k="C", share=None, dout=0.0, Ts=55.0):
    """Temperature the attic settles at when the thermostat holds the main floor at 75 F, the attic getting 'share' of the airflow."""
    S = _system_cache.get(k) or system(k); att = [x for x in S["rooms"] if x["fl"] == 6]; main = [x for x in S["rooms"] if x["fl"] == 5]
    if share is None: share = sum(x["cfm"] for x in S["served"] if x["fl"] == 6) / S["cfm"]
    Dm = sum(_gain_at(x, 75, dout) for x in main); lo, hi = 55.0, 100.0
    for _ in range(60):
        T = (lo + hi) / 2
        if sum(_gain_at(x, T, dout) for x in att) > Dm * share / (1 - share) * (T - Ts) / (75 - Ts): lo = T
        else: hi = T
    return T


def summer_share(k="C"):
    """Attic share of the airflow that keeps it level with the main floor in summer (rounded up to the next 1 %)."""
    S = _system_cache.get(k) or system(k); att = [x for x in S["rooms"] if x["fl"] == 6]; main = [x for x in S["rooms"] if x["fl"] == 5]
    r = sum(_gain_at(x, 75, 0) for x in att) / sum(_gain_at(x, 75, 0) for x in main)
    return math.ceil(r / (1 + r) * 100) / 100


# ---------------------------------------------------------------------------------------------- sizing helpers
def round_duct(cfm):
    """Round branch duct (flex or rigid), about 0.08 in. w.c. per 100 ft: smallest size that carries the airflow."""
    for d, cap in ((5, 50), (6, 80), (7, 120), (8, 170), (9, 230), (10, 300), (12, 480), (14, 720), (16, 1050)):
        if cfm <= cap: return d
    return 18


def register(cfm):
    for s, cap in (("4x10", 70), ("4x12", 100), ("6x10", 130), ("6x12", 170), ("8x12", 230)):
        if cfm <= cap: return s
    return "8x14"


def n_registers(r, cfm):
    return 1 if cfm <= 150 else 2 if cfm <= 300 else 3


def return_grille(cfm):
    """Filter return grille at no more than about 300 fpm through the filter face."""
    for s, area in (("14x20", 1.94), ("16x20", 2.22), ("20x20", 2.78), ("20x25", 3.47), ("20x30", 4.17), ("24x30", 5.0)):
        if cfm / area <= 300: return s
    return "2 x 20x25"


def sidewall(cfm):
    """High sidewall supply register, W x H in. (W along the wall), and the wall stack or boot that feeds it."""
    for sz, cap, st in (("10x4", 70, "3-1/4 x 10"), ("12x4", 90, "3-1/4 x 10"), ("10x6", 130, "3-1/4 x 10"), ("12x6", 170, "3-1/4 x 14"),
                        ("14x6", 210, "3-1/4 x 14"), ("14x8", 280, "two 3-1/4 x 14")):
        if cfm <= cap: return sz, st
    return "14x8", "two 3-1/4 x 14"


def wall_return(cfm):
    """Filter return grille in a wall, W x H in.: 14 in. wide fits one stud bay; about 300 fpm or less through the filter."""
    for sz, area in (("14x20", 1.94), ("14x25", 2.43), ("14x30", 2.92)):
        if cfm / area <= 310: return sz
    return "2 x 14x30"


def jump(cfm):
    for d, cap in ((6, 80), (8, 140), (10, 220), (12, 310)):
        if cfm <= cap: return d
    return 14


AC_ELEC = {1.5: (10.0, 15), 2.0: (12.0, 20), 2.5: (15.0, 25), 3.0: (18.0, 30), 3.5: (21.0, 35)}       # typical MCA / MOCP: verify with the unit bought
LINESET = {1.5: ('3/8"', '3/4"'), 2.0: ('3/8"', '3/4"'), 2.5: ('3/8"', '7/8"'), 3.0: ('3/8"', '7/8"'), 3.5: ('3/8"', '7/8"')}


if __name__ == "__main__":
    for k in SYSTEMS:
        s = system(k)
        print(f"{k}: heat {s['H']:,.0f}  cool S {s['Cs']:,.0f} L {s['lat']:,.0f} T {s['Ct']:,.0f} (SHR {s['shr']:.2f})  -> {s['tons']} ton, furnace {s['furn']:,} in, "
              f"{s['cfm']} CFM, vent {s['vent']:.0f} CFM, vol {s['vol']:.0f}")
        for x in s["rooms"]:
            r = x["r"]
            print(f"    L{x['fl']} {r['no']} {r['name'][:20]:20s} A {x['A']:5.0f} H {x['H']:6.0f} C {x['C']:6.0f} wins {len(x['wins'])} edges {[(round(L,1), br, kd) for L, n, br, kd in x['edges']]} cfm {x.get('cfm', '-')}")
