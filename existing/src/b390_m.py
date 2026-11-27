"""390 Forest Ave builder set: mechanical (HVAC). Sheets M-001 (notes, equipment and fan schedules), M-002 (heating and cooling loads),
M-003 (air distribution schedule, outdoor units, venting) and M-101 to M-104 (duct plans). Gut renovation: all HVAC is new.

One direct-vent gas furnace with a cased cooling coil and an outdoor condenser per flat. Supply trunk in the ceiling framing, round
branches to a register per room, one central filter return per flat (plus an attic return for the upper flat), jump ducts from the
bedrooms, bath fans for exhaust and continuous ventilation, dryer and range-hood exhaust, PVC venting up the old chimney chase.
Loads and airflows: b390_mq.py. Line sets to the condensers are NOT final: the condensers' place under the rear deck is pending."""
import math
import os
import sys
from functools import lru_cache

import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch, Polygon as MPoly, Rectangle
from matplotlib.patheffects import withStroke
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import nearest_points, unary_union

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build390 as b  # noqa: E402
import b390_eq as q  # noqa: E402
import b390_mq as mq  # noqa: E402
import b390_e as e  # noqa: E402
import b390_mr as mr  # noqa: E402
from common import INK, GREY, table  # noqa: E402

SUP, SUPF, RET, EXH, PVC, LS = "#6a2c91", "#eadcf3", "#2f6fa8", "#c2570c", "#0b7a75", "#b3261e"
HALO = [withStroke(linewidth=1.4, foreground="white")]
FLAT_LEV = {3: "A", 4: "B", 5: "C", 6: "C"}
SYS = {k: mq.system(k) for k in mq.SYSTEMS}
LINESETS_FINAL = False
TBD = "LINE SETS NOT FINALIZED: condensers go under the rear deck (size of the walled area under it pending). Route and lengths to be set then."

TBD_SHORT = "Line sets NOT FINALIZED"


def room_rec(fl, no):
    for k in SYS:
        for x in SYS[k]["rooms"]:
            if x["fl"] == fl and x["r"]["no"] == no: return x, k
    return None, None


# ---------------------------------------------------------------------------------------------- drawing
def poly(ax, pts, **kw):
    ax.plot([p[0] for p in pts], [p[1] for p in pts], **kw)


def patch(ax, shp, **kw):
    for P in (shp.geoms if hasattr(shp, "geoms") else [shp]):
        if P.is_empty: continue
        ax.add_patch(MPoly(np.array(P.exterior.coords), closed=True, **kw))


class Placer:
    """Puts labels and keynote diamonds where they touch nothing: walls, fixtures, door swings, windows, stairs, any duct or
    symbol, other text. Measures the real text with the renderer."""
    def __init__(self, fig, ax, fl, block):
        self.fig, self.ax, self.fl = fig, ax, fl
        fig.canvas.draw(); self.r = fig.canvas.get_renderer(); self.inv = ax.transData.inverted()
        obs = [o[0] for o in b.obstacles(fl) if o[2] != "tub" or True]
        self.hard = unary_union(obs + block)
        self.soft = []                                            # labels and diamonds placed so far
        for t in ax.texts:
            if t.get_text().strip(): self.soft.append(self.bbox(t))
        self.leaders = []

    def bbox(self, t, pad=1.2):
        bb = t.get_window_extent(self.r); (u0, v0), (u1, v1) = self.inv.transform((bb.x0 - pad, bb.y0 - pad)), self.inv.transform((bb.x1 + pad, bb.y1 + pad))
        return box(min(u0, u1), min(v0, v1), max(u0, u1), max(v0, v1))

    def ok(self, shp):
        return not shp.intersects(self.hard) and not any(shp.intersects(o) for o in self.soft) and not any(shp.intersects(l_) for l_ in self.leaders)

    def label(self, p, txt, col, r0=.6, fs=3.5, rmax=4.0, z=14):
        x, y = p; t = self.ax.text(x, y, txt, fontsize=fs, color=col, ha="center", va="center", fontweight="bold", zorder=z, path_effects=HALO)
        for r_ in np.arange(r0, rmax, .2):
            for ang in range(0, 360, 15):
                cx, cy = x + r_ * math.cos(math.radians(ang)), y + r_ * math.sin(math.radians(ang))
                t.set_position((cx, cy)); bb = self.bbox(t)
                if self.ok(bb):
                    self.soft.append(bb); return (cx, cy)
        t.set_position((x, y + r0)); self.soft.append(self.bbox(t)); return None

    def room_label(self, r, txt):
        x0, y0, x1, y1 = max(r["rects"], key=lambda qq: (qq[2] - qq[0]) * (qq[3] - qq[1])); R = mr.room_shape(r)
        t = self.ax.text(0, 0, txt, fontsize=3.6, color="#7a818a", ha="center", va="center", zorder=11, fontweight="bold")
        lab = r.get("lab") or ((x0 + x1) / 2, (y0 + y1) / 2); best = None
        for qq in r["rects"]:
            for cx in np.arange(qq[0] + .3, qq[2] - .3, .25):
                for cy in np.arange(qq[1] + .3, qq[3] - .3, .25):
                    d = math.dist((cx, cy), lab)
                    if best is not None and d >= best[0]: continue
                    t.set_position((cx, cy)); bb = self.bbox(t)
                    if R.contains(bb) and self.ok(bb): best = (d, (cx, cy), bb)
        if best is None:
            t.remove(); return False
        t.set_position(best[1]); self.soft.append(best[2]); return True

    def keynote(self, n, anchor, pref=None, col=None, reach=7.0, need_leader=True):
        """Diamond at the clear spot nearest pref (or the anchor); leader to the anchor."""
        shape = anchor if hasattr(anchor, "geom_type") else None
        if shape is not None: anchor = (shape.centroid.x, shape.centroid.y)
        px, py = pref or anchor; best = None
        for r_ in np.arange(0.0 if pref else 0.9, reach, .2):
            for ang in range(0, 360, 12 if r_ else 360):
                cx, cy = px + r_ * math.cos(math.radians(ang)), py + r_ * math.sin(math.radians(ang))
                D = Polygon([(cx - .62, cy), (cx, cy + .62), (cx + .62, cy), (cx, cy - .62)])
                if not self.ok(D): continue
                if shape is not None:                            # leader to the edge of the thing, clear of its own lettering
                    bp = nearest_points(shape.exterior, Point(cx, cy))[0]; anchor = (bp.x, bp.y)
                if anchor is not None and math.dist((cx, cy), anchor) > .8:
                    dd = math.dist((cx, cy), anchor); f_ = max(0.0, (dd - .5) / dd)
                    ld = LineString([(cx, cy), (cx + (anchor[0] - cx) * f_, cy + (anchor[1] - cy) * f_)]); ldb = ld.buffer(.05)
                    if any(ldb.intersects(o) for o in self.soft): continue
                best = (cx, cy, D); break
            if best: break
        if best is None: return None
        cx, cy, D = best
        to = anchor if anchor is not None and math.dist((cx, cy), anchor) > .8 else None
        b.keynote(self.ax, n, cx, cy, col=col or SUP, to=to)
        self.soft.append(D.buffer(.05))
        if to: self.leaders.append(LineString([(cx, cy), to]).buffer(.04)); self.ax._leaders = getattr(self.ax, "_leaders", []) + [(n, (cx, cy), to)]
        return (cx, cy)


def plan_sheet(pdf, number, fl):
    L = b.LV[fl]; D = mr.level(fl); k = FLAT_LEV[fl]; s = SYS[k]; g = mr.grid(mr.SPACE[fl])
    title = {3: "Lower flat: HVAC plan", 4: "Middle flat: HVAC plan", 5: "Upper flat main floor: HVAC plan", 6: "Attic: HVAC plan"}[fl]
    where = {3: ["Ducts in the lower flat's ceiling framing", "(the middle flat's floor)."], 4: ["Ducts in the middle flat's ceiling framing", "(the upper flat's floor)."],
             5: ["Ducts in the attic floor framing, above", "this ceiling. The same framing feeds the", "attic floor registers (M-104)."],
             6: ["Floor registers fed by branches in the", "attic floor framing off the main-floor", "trunk (dashed; drawn on M-103)."]}[fl]
    notes = [("This sheet", [f"System {k}: {q.FLATS[k]['name'].split(' (')[0].lower()}, furnace F-{k},", f"{s['tons']:g} ton cooling, {s['cfm']} CFM blower.", *where,
                             "At each register: CFM and round duct", "size. Schedules M-003, loads M-002,", "equipment and caps M-001."]),
             ("Rules", ["Joist direction is not known: ducts are", "drawn square; run each in its joist bay", "or shift it a bay, keeping the sizes.",
                        "No duct crosses another flat, the chase,", "a stair opening or a panel's space.", "Outside caps: see M-001 note 6."])]
    fig, bg, ax = b.bsheet(number, title, fl, notes, sub=f"Rear building · {L['name'].lower()}", view=e.VIEW[fl])
    b.draw_base(ax, fl, "trade", labels=False)
    dims, L["dims"] = L["dims"], []                               # not drawn on trade sheets: nothing to keep clear of
    ch = mr.CHASE[fl]; ax.add_patch(Rectangle((ch[0], ch[1]), ch[2] - ch[0], ch[3] - ch[1], fill=False, ec=PVC, lw=.6, ls=(0, (1.5, 1.5)), zorder=9))
    block = [box(*ch).exterior.buffer(.05)]
    # trunk, to scale (14 x 8 in.)
    if fl != 6:
        patch(ax, g.trunk_shape, fc=SUPF, ec=SUP, lw=.5, zorder=8.5, alpha=.6); block.append(g.trunk_shape)
    else:
        patch(ax, g.trunk_shape, fc="none", ec=SUP, lw=.5, ls=(0, (3, 2)), zorder=8.5, alpha=.7); block.append(g.trunk_shape.exterior.buffer(.05))
    for rg in D["regs"]:
        if len(rg.get("path", [])) > 1:
            poly(ax, rg["path"], color=SUP, lw=.9, zorder=8.7); block.append(LineString(rg["path"]).buffer(.07))
    for rg in D["regs"]:
        x0, y0, x1, y1 = rg["shape"].bounds
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc="white", ec=SUP, lw=.8, zorder=9.5))
        ax.plot([x0, x1], [y0, y1], color=SUP, lw=.5, zorder=9.6); ax.plot([x0, x1], [y1, y0], color=SUP, lw=.5, zorder=9.6); block.append(rg["shape"])
    for rt in D["rets"]:
        if len(rt["path"]) > 1 and LineString(rt["path"]).length > .1:
            poly(ax, rt["path"], color=RET, lw=1.4, ls=(0, (4, 1.5)), zorder=8.8); block.append(LineString(rt["path"]).buffer(.1))
            ax.add_patch(Circle(rt["path"][-1], .14, fc=RET, ec=RET, zorder=9.0))
        x0, y0, x1, y1 = rt["shape"].bounds
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc="white", ec=RET, lw=.9, zorder=9.5))
        n_ = 5
        for i in range(n_):
            u = x0 + (x1 - x0) * (i + .5) / n_
            ax.plot([u - .1, u + .1], [y0 + .1, y1 - .1], color=RET, lw=.4, zorder=9.6)
        block.append(rt["shape"])
    if fl == 6:                                                   # the R-C1 box below, for reference
        r1 = next(rt for rt in mr.layout(5)["rets"] if rt["name"] == "R-C1"); x0, y0, x1, y1 = r1["shape"].bounds
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, ec=RET, lw=.5, ls=(0, (2, 1.5)), zorder=9.4)); block.append(r1["shape"].buffer(.05))
    for j in D["jumps"]:
        if j["kind"] == "ceiling":
            for p in (j["a"], j["b"]):
                ax.add_patch(Rectangle((p[0] - .35, p[1] - .35), .7, .7, fc="white", ec=RET, lw=.7, zorder=9.5)); block.append(Point(p).buffer(.4, cap_style="square"))
            poly(ax, [j["a"], j["b"]], color=RET, lw=.8, ls=(0, (2, 1.2)), zorder=9.4); block.append(LineString([j["a"], j["b"]]).buffer(.06))
        else:
            for p in (j["a"], j["b"]):
                w_, h_ = (.12, .9) if j["axis"] == "v" else (.9, .12)
                ax.add_patch(Rectangle((p[0] - w_ / 2, p[1] - h_ / 2), w_, h_, fc="white", ec=RET, lw=.7, zorder=9.5)); block.append(box(p[0] - w_ / 2, p[1] - h_ / 2, p[0] + w_ / 2, p[1] + h_ / 2).buffer(.05))
    for x_ in D["exh"]:
        if x_["to"] == "wall":
            poly(ax, x_["path"], color=EXH, lw=.9, ls=(0, (3, 1.5)), zorder=9.2); block.append(LineString(x_["path"]).buffer(.08))
            ax.add_patch(Circle(x_["cap"], .16, fc=EXH, ec=EXH, lw=.8, zorder=9.3)); block.append(Point(x_["cap"]).buffer(.2))
        else:                                                     # straight up to a roof cap: fan symbol only
            x_["cap"] = x_["a"]; ax.add_patch(Circle(x_["a"], .2, fc="white", ec=EXH, lw=.9, zorder=9.3))
            ax.plot([x_["a"][0] - .14, x_["a"][0] + .14], [x_["a"][1] - .14, x_["a"][1] + .14], color=EXH, lw=.6, zorder=9.31)
            ax.plot([x_["a"][0] - .14, x_["a"][0] + .14], [x_["a"][1] + .14, x_["a"][1] - .14], color=EXH, lw=.6, zorder=9.31); block.append(Point(x_["a"]).buffer(.25))
    for x_ in D["dry"]:
        if x_.get("ventless"):
            continue
        poly(ax, x_["path"], color=EXH, lw=1.2, zorder=9.2); ax.add_patch(Circle(x_["cap"], .16, fc=EXH, ec=EXH, zorder=9.3))
        block += [LineString(x_["path"]).buffer(.08), Point(x_["cap"]).buffer(.2)]
    for x_ in D["hood"]:
        if x_["ducted"]:
            poly(ax, x_["path"], color=EXH, lw=1.2, zorder=9.2); ax.add_patch(Circle(x_["cap"], .16, fc=EXH, ec=EXH, zorder=9.3)); block.append(Point(x_["cap"]).buffer(.2))
    for x_ in D["vent"]:
        poly(ax, x_["path"], color=PVC, lw=1.1, ls=(0, (5, 1.2, 1, 1.2)), zorder=9.1); block.append(LineString(x_["path"]).buffer(.08))
    for x_ in D["ls"]:                                            # drawn beside the vents it runs with
        ln = LineString(x_["path"]); off = ln.offset_curve(.22) if ln.length > 0 else ln
        x_["drawn"] = list(off.coords) if off.geom_type == "LineString" and not off.is_empty else x_["path"]
        poly(ax, x_["drawn"], color=LS, lw=1.0, ls=(0, (1, 1.5)), zorder=9.0); block.append(LineString(x_["drawn"]).buffer(.08))
    if fl in mr.TSTAT:
        x, y, n = mr.TSTAT[fl]; cx, cy = x + n[0] * .35, y + n[1] * .35
        ax.add_patch(Circle((cx, cy), .28, fc="white", ec=INK, lw=.7, zorder=9.6)); ax.text(cx, cy, "T", fontsize=3.6, ha="center", va="center", color=INK, fontweight="bold", zorder=9.7, gid="own")
        block.append(Point(cx, cy).buffer(.3))
    for h in D["heater"]:
        (x, y), n = h["p"], h["n"]; r_ = box(x - .6 + n[0] * .1, y - .15 + n[1] * .15, x + .6 + n[0] * .1, y + .15 + n[1] * .15) if n[0] == 0 else box(x - .15 + n[0] * .15, y - .6, x + .15 + n[0] * .15, y + .6)
        patch(ax, r_, fc="#fde3c4", ec=EXH, lw=.7, zorder=9.5); block.append(r_)
    # labels
    P = Placer(fig, ax, fl, block)
    for rg in D["regs"]: P.label(rg["p"], f"{rg['cfm']:.0f} · {rg['d']}\"", SUP, r0=.55)
    for rt in D["rets"]: P.label(rt["p"], f"{rt['name']} {rt['size']}", RET, r0=.9)
    for j in D["jumps"]: P.label(j["b"], f"J {j['d']}\"" if j["kind"] == "ceiling" else f"TG {j['size']}", RET, r0=.6)
    for x_ in D["exh"]:
        P.label(x_["cap"], {"wall": "EF 4\" wall cap", "eave": "EF 4\" up to roof cap", "roof": "EF 4\" roof cap"}[x_["to"]], EXH, r0=.45)
    for x_ in D["dry"]:
        if not x_.get("ventless"): P.label(x_["cap"], f"DV 4\" rigid, {x_['eq']:.0f} ft eq.", EXH, r0=.45)
    for x_ in D["hood"]: P.label(x_["cap"] if x_["ducted"] else x_["a"], "RH 6\" wall cap" if x_["ducted"] else "RH recirculating", EXH, r0=.45)
    for f in L["fx"]:
        if f[0] == "furnace": P.label(((f[1] + f[3]) / 2, (f[2] + f[4]) / 2), f"F-{k} + coil", SUP, r0=.3)
    for x_ in D["ls"]: P.label(x_.get("drawn", x_["path"])[-1], f"LS-{k}: TBD", LS, r0=.5)
    for h in D["heater"]: P.label(h["p"], "EWH 1,000 W", EXH, r0=.5)
    if fl != 6:
        t0 = mr.TRUNK[mr.SPACE[fl]][0]; seg = max(zip(t0[:-1], t0[1:]), key=lambda sg: math.dist(*sg))
        P.label(((seg[0][0] + seg[1][0]) / 2, (seg[0][1] + seg[1][1]) / 2), f"Trunk {mr.TRUNK_SIZE}", SUP, r0=.9)
    else:
        P.label((7.0, 17.0), "Main-floor trunk below (M-103)", SUP, r0=.9)
    for r in L["rooms"]:
        if r["kind"] == "closet" or q.skip(r): continue
        if not P.room_label(r, f"{r['name'].split(' (')[0]}  {r['no']}"): print(f"   {number}: no room for the label of {r['no']}")
    # keynotes
    KN = keynotes(fl, D); placed = []
    for i, (txt, anchor, pref) in enumerate(KN):
        c = P.keynote(i + 1, anchor, pref) or P.keynote(i + 1, anchor, pref, reach=14.0)
        if c is None: print(f"   {number}: keynote {i + 1} found no clear spot")
    y = legend(bg, 10.6, 9.95) - .1
    bg.text(10.6, y, "KEYNOTES", fontsize=6.6, fontweight="bold", color=INK, va="center"); y -= .2
    for i, kn in enumerate(KN):
        bg.text(10.68, y, str(i + 1), fontsize=5.4, color=SUP, fontweight="bold", va="center", ha="center")
        for j_, ln in enumerate(b.wrap(kn[0], 56)): bg.text(10.85, y - j_ * .12, ln, fontsize=5.2, color=INK, va="center")
        y -= .12 * len(b.wrap(kn[0], 56)) + .07
    bad = b.clarity(fig, ax, fl, bg); print(number, "text clashes:", len(bad)); [print("   ", m) for m in bad[:12]]
    L["dims"] = dims
    for pr in mr.layout(mr.SPACE[fl])["problems"]:
        if fl != 6: print("   layout:", pr)
    b.save(fig, number, pdf)


def keynotes(fl, D):
    """[(text, anchor point or None, preferred diamond spot or None)] for one level."""
    L = b.LV[fl]; k = FLAT_LEV[fl]
    fur = next((box(*f[1:5]) for f in L["fx"] if f[0] == "furnace"), None)
    ch = mr.CHASE[fl]; chc = ((ch[0] + ch[2]) / 2, (ch[1] + ch[3]) / 2)
    lsend = D["ls"][0].get("drawn", D["ls"][0]["path"])[-1] if D["ls"] else chc
    caps = [x_ for x_ in D["exh"] + D["dry"] if x_.get("to") == "wall"]
    if fl == 3:
        return [("Furnace F-A with its cooling coil on top, in laundry / mechanical 105. The 14 x 8 trunk rises into the ceiling and runs along the hall.", fur, None),
                ("Furnace and water heater: 2 in. PVC exhaust and intake each, in the ceiling to the pipe wall between bath 1 and the laundry (2x6, the chase on this level), then up the chase to the roof.", chc, None),
                (TBD, lsend, None),
                ("Ceilings here are low (6'-10\" to 7'-6\"): every duct goes in the joist space while the ceilings are open; no soffits. Check the joist direction first.", None, (7.0, 20.5)),
                ("Wall caps on the east wall (north end is below grade, south has the deck, west the neighbour): verify each is 12 in. above grade, 3 ft from windows, doors and the property line, and not blowing onto the stair.", caps[0]["cap"] if caps else None, None)]
    if fl == 4:
        dry = next((box(*f[1:5]) for f in L["fx"] if f[0] in ("dryer", "wdstack")), None); rng = next((box(*f[1:5]) for f in L["fx"] if f[0] == "range"), None)
        return [("Furnace F-B with its coil, in the mechanical closet. Two trunks: west up the hall, east along the bath 2 wall into the living room.", fur, None),
                ("Stair hall 213 is the upper flat's: no duct can reach it without crossing this flat, so it gets a 1,000 W electric wall heater EWH on panel C.", D["heater"][0]["p"] if D["heater"] else None, None),
                (TBD, lsend, None),
                ("Dryer: heat-pump type, no vent. No outside wall it may vent through is within the 35 ft limit (north windows, west neighbour, east stair, the trunk).", dry, None),
                ("Range hood recirculating: the only outside wall beside the range has the kitchen window within 3 ft.", rng, None),
                ("Pipes and vents from below rise at the back of this closet, where the chimney was, behind the water heater.", chc, None)]
    if fl == 5:
        r1 = next(rt for rt in D["rets"] if rt["name"] == "R-C1")
        fan = next((x_ for x_ in D["exh"] if x_["to"] == "eave"), None)
        return [("Furnace F-C with its coil. The 14 x 8 trunk rises into the attic floor framing; the same trunk feeds the attic floor registers (M-104).", fur, None),
                ("Return box in the floor framing: R-C1 grille in this ceiling, R-C2 grille in the attic stair-hall floor above, one duct down to F-C.", r1["p"], None),
                (TBD, lsend, None),
                ("Bath fan: 4 in. insulated duct up into the eave space to a roof cap. No caps on the west wall: the neighbour is too close.", fan["a"] if fan else None, None),
                ("Supply ducts stay under the attic rooms (inside the insulation); none in the eave floors, which get R-49.", None, (8.0, 10.0))]
    tg = next((j for j in D["jumps"] if j["kind"] == "wall"), None); r2 = next((rt for rt in D["rets"] if rt["name"] == "R-C2"), None)
    fan = next((x_ for x_ in D["exh"]), None)
    return [("Floor registers: branches in the attic floor framing off the main-floor trunk (dashed; see M-103). Stay inside the insulation.", (12.0, 17.0), None),
            ("R-C2 floor return grille at the top of the stair, on the return box over R-C1 (dashed, M-103).", r2["p"] if r2 else None, None),
            ("Bath fans (circle): 4 in. insulated duct straight up through the roof slope to a roof cap with a damper.", fan["a"] if fan else None, None),
            ("TG: transfer grilles beside each bedroom door, high on the bedroom side, low on the hall side, in a lined stud bay (return path).", tg["a"] if tg else None, None)]


LEG = [("trunk", SUPF, "Supply trunk, 8 in. deep, in the ceiling framing"), ("br", SUP, "Supply branch, round; number = CFM · size"),
       ("reg", SUP, "Supply register (ceiling; floor in the attic)"), ("ret", RET, "Return grille with filter; return duct dashed"),
       ("jump", RET, "Jump duct: bedroom to hall, return path"), ("exh", EXH, "Exhaust: bath fan EF, dryer DV, range hood RH"),
       ("vent", PVC, "PVC vent and intake, furnace and water heater"), ("ls", LS, "Refrigerant line set: NOT FINALIZED"), ("T", INK, "Thermostat, 5 ft, inside wall")]


def legend(bg, x, y, fs=5.4, rh=.21):
    bg.text(x, y, "LEGEND", fontsize=6.6, fontweight="bold", color=INK, va="center"); y -= .22
    for k, col, t in LEG:
        if k == "trunk": bg.plot([x, x + .34], [y, y], color=SUPF, lw=4.5, solid_capstyle="butt"); bg.plot([x, x + .34], [y, y], color=SUP, lw=.4)
        elif k == "br": bg.plot([x, x + .34], [y, y], color=SUP, lw=.9)
        elif k == "reg":
            bg.add_patch(Rectangle((x + .07, y - .05), .2, .1, fc="white", ec=SUP, lw=.6)); bg.plot([x + .07, x + .27], [y - .05, y + .05], color=SUP, lw=.4)
        elif k == "ret": bg.add_patch(Rectangle((x + .06, y - .07), .22, .14, fc="white", ec=RET, lw=.7)); bg.plot([x + .3, x + .5], [y, y], color=RET, lw=1, ls=(0, (3, 1)))
        elif k == "jump": bg.add_patch(Rectangle((x, y - .04), .08, .08, fc="white", ec=RET, lw=.6)); bg.add_patch(Rectangle((x + .26, y - .04), .08, .08, fc="white", ec=RET, lw=.6)); bg.plot([x + .08, x + .26], [y, y], color=RET, lw=.6, ls=(0, (2, 1)))
        elif k == "exh": bg.plot([x, x + .34], [y, y], color=EXH, lw=.9, ls=(0, (3, 1.5))); bg.add_patch(Circle((x + .34, y), .03, fc=EXH, ec=EXH))
        elif k == "vent": bg.plot([x, x + .34], [y, y], color=PVC, lw=1.1, ls=(0, (5, 1.2, 1, 1.2)))
        elif k == "ls": bg.plot([x, x + .34], [y, y], color=LS, lw=1.0, ls=(0, (1, 1.5)))
        elif k == "T": bg.add_patch(Circle((x + .17, y), .06, fc="white", ec=INK, lw=.6)); bg.text(x + .17, y, "T", fontsize=3.2, ha="center", va="center")
        bg.text(x + .55, y, t, fontsize=fs, color=INK, va="center"); y -= rh
    return y


# ---------------------------------------------------------------------------------------------- M-001: notes and schedules
GEN = ["Scope: full gut; all heating, cooling, ductwork, exhaust and venting are new. Design intent to the IRC 2018 / IMC as adopted in West Virginia "
       "(confirm the edition Morgantown enforces), ACCA Manual J / S / D methods (simplified, written out on M-002 and M-003) and the equipment instructions.",
       "One system per flat: direct-vent (sealed combustion) condensing gas furnace, cased cooling coil on top, outdoor condenser. Two-stage or modulating "
       "furnaces and variable-speed condensers: the loads are small, so the equipment must turn down to run long, quiet cycles and dry the air.",
       "Ducts: galvanised steel trunk 14 x 8 in. (one joist bay at 16 in. o.c.), rigid round branches (flex only for the last 5 ft, stretched tight), "
       "every joint sealed with mastic, balancing damper at every take-off. All ducts inside the heated space of the flat they serve; none cross another "
       "flat, the chase, a stair opening or a panel's dedicated space. The upper flat's attic registers are fed from its main-floor trunk in the attic floor.",
       "Returns: one filter return per flat (MERV 8). Upper flat: R-C1 in the main-floor hall ceiling and R-C2 in the attic stair-hall floor share one return "
       "box in the floor framing. Every bedroom has a jump duct to the hall (attic: transfer grilles beside the door) so it is not pressurised with the door "
       "shut. No returns from baths, kitchens, laundry or the mechanical closets.",
       "Ventilation (IRC M1505.4 / ASHRAE 62.2): the bath fans run continuously at low speed to meet the whole-house rate on M-003, boosting to 80 CFM "
       "on the humidity sensor or timer. Each fan ducted in 4 in. smooth duct to its own cap with a back-draft damper; insulated where it passes cold space.",
       "Outside caps (IRC M1504.3, M1502.3): 3 ft or more from property lines and from windows and doors; 10 ft from the furnace and water heater intakes "
       "unless 3 ft above them; 12 in. above grade; not blowing onto the east stair or a walkway. None on the west wall (the neighbour is too close); the lower "
       "flat's north end is below grade. Caps are drawn where these rules allow: verify on site before cutting, and move along the same wall if needed.",
       "Dryers A and C: 4 in. rigid smooth metal duct, no screws through it, to a wall cap with a damper, 35 ft equivalent length maximum (5 ft per 90 "
       "degree elbow); lengths in the schedule below. Dryer B: heat-pump (ventless) type, because no wall it may vent through is within 35 ft. Range hoods: "
       "ducted in 6 in. metal in the upper flat; recirculating in the lower (inside wall) and middle (window within 3 ft) flats; 300 CFM or less, so no make-up air.",
       "Venting: each furnace and water heater has 2 in. or 3 in. PVC exhaust and intake (sizes per the instructions) up the old chimney chase to a roof "
       "termination (lower level: the 2x6 pipe wall between bath 1 and the laundry); condensate to an indirect drain with a neutraliser, or a pump (plumbing).",
       "Refrigerant line sets: insulated copper, sizes on M-003, down the chase. " + TBD,
       "Thermostats: one per flat, programmable, 5 ft up on an inside wall as drawn, away from supplies, sun, the kitchen and every door swing.",
       "Start-up: set airflow to the CFM on M-003 at each register (balancing report), check the refrigerant charge, gas pressure and temperature rise."]


def exhaust_rows():
    """One row per fan, dryer and hood, from the plan layout."""
    rows = []; vent = {k: SYS[k]["vent"] / q.FLATS[k]["baths"] for k in SYS}
    side = lambda fl, p: mr.side(np.array(p) - np.array(nearest_points(q.outline(fl).buffer(-1.0).exterior, Point(p))[0].coords[0]))
    for sp in (3, 4, 5):
        D = mr.layout(sp)
        for i, x_ in enumerate(sorted(D["exh"], key=lambda x_: (x_["fl"], x_["room"]))):
            k = FLAT_LEV[x_["fl"]]; Ld = sum(math.dist(a, c) for a, c in zip(x_["path"][:-1], x_["path"][1:]))
            cap = {"wall": f"{ {'N': 'north', 'S': 'south', 'E': 'east'}.get(side(x_['fl'], x_['cap']), '?') } wall cap", "eave": "roof cap via the eave space", "roof": "roof cap above"}[x_["to"]]
            rows.append([f"EF-{k}{i + 1}", f"{k}: bath {x_['room']}", "Ceiling fan, 0.3 sone, DC motor", f"80 boost / {vent[k]:.0f} continuous",
                         f"4 in. smooth, about {Ld:.0f} ft" if x_["to"] == "wall" else "4 in. insulated, straight up", cap, "humidity sensor + timer"])
        for x_ in D["dry"]:
            k = FLAT_LEV[x_["fl"]]
            if x_.get("ventless"):
                rows.append([f"DRY-{k}", f"{k}: laundry", "Heat-pump dryer, ventless (condensate to the drain)", "-", "none", "-", "-"])
            else:
                rows.append([f"DV-{k}", f"{k}: laundry", "Dryer exhaust (dryer per owner)", "per dryer", f"4 in. rigid, {x_['len']:.0f} ft run, {x_['eq']:.0f} ft eq.",
                             f"{ {'N': 'north', 'S': 'south', 'E': 'east'}.get(side(x_['fl'], x_['cap']), '?') } wall cap", "-"])
        for x_ in D["hood"]:
            k = FLAT_LEV[x_["fl"]]
            rows.append([f"RH-{k}", f"{k}: kitchen", "Microwave-hood, 300 CFM max (E: circuit MW)", "300 max", "6 in. metal, short" if x_["ducted"] else "recirculating, charcoal filter",
                         (f"{ {'N': 'north', 'S': 'south', 'E': 'east'}.get(side(x_['fl'], x_['cap']), '?') } wall cap") if x_["ducted"] else "-", "on the unit"])
    return rows


def notes_sheet(pdf):
    notes = [("Read with", ["M-002 heating and cooling loads, M-003 air", "distribution and outdoor units, M-101 to", "M-104 plans. Electrical: E sheets;", "gas and condensate: P sheets."]),
             ("Pending", ["Condenser place under the rear deck and", "the line sets (M-003). The equipment", "sizes here are final unless the windows or", "insulation assumptions change (M-002)."])]
    fig, bg, _ = b.bsheet("M-001", "Mechanical notes and schedules", 0, notes, sub="Rear building · all flats")
    bg.text(.5, 10.25, "MECHANICAL GENERAL NOTES, EQUIPMENT AND FAN SCHEDULES", fontsize=9.5, fontweight="bold", color=INK, va="center")
    y = 9.95
    for i, t in enumerate(GEN):
        bg.text(.55, y, f"{i + 1}.", fontsize=5.8, color=INK, va="center", fontweight="bold")
        for j, ln in enumerate(b.wrap(t, 190)): bg.text(.8, y - j * .14, ln, fontsize=5.8, color=INK, va="center")
        y -= .14 * len(b.wrap(t, 190)) + .07
    y -= .1
    bg.text(.5, y, "EQUIPMENT SCHEDULE", fontsize=7, fontweight="bold", color=INK, va="center"); y -= .2
    rows = [["Tag", "Serves", "Equipment", "Capacity", "Airflow", "Electrical (verify nameplate)", "Location"]]
    for k, s in SYS.items():
        mca, mocp = mq.AC_ELEC[s["tons"]]; liq, suc = mq.LINESET[s["tons"]]; loc = {"A": "laundry / mech. 105", "B": "mech. closet 208", "C": "mech. closet 307"}[k]
        rows += [[f"F-{k}", q.FLATS[k]["name"].split(" (")[0], "Gas furnace, condensing 96 % AFUE, direct vent, 2-stage or modulating, upflow",
                  f"{s['furn'] / 1000:.0f}k Btu/h in, {s['furn'] * .96 / 1000:.1f}k out", f"{s['cfm']} CFM cool", "120 V, 15 A circuit, about 7 A", loc],
                 [f"CC-{k}", "", "Cased cooling coil on top of F-" + k + ", R-454B or R-32 per the condenser", f"{s['tons']:g} ton", "", "", "on F-" + k],
                 [f"AC-{k}", "", "Air conditioner, variable speed (inverter), 15.2 SEER2 or better", f"{s['tons']:g} ton", "", f"240 V, MCA {mca:g} A, MOCP {mocp} A", "under rear deck: TBD"]]
    rows += [["EWH-1", "Upper flat stair hall 213", "Electric wall heater with built-in thermostat", "1,000 W", "", "240 V, 4.2 A, panel C", "stair hall 213 wall"]]
    y = table(bg, .5, y, [.45, 1.25, 3.6, 1.35, .85, 1.75, 1.25], rows, fs=5.0, rh=.16) - .2
    bg.text(.5, y, "FAN, DRYER AND HOOD SCHEDULE (from the plans)", fontsize=7, fontweight="bold", color=INK, va="center"); y -= .2
    rows = [["Tag", "Flat: room", "Type", "Airflow CFM", "Duct", "Outside", "Control"]] + exhaust_rows()
    table(bg, .5, y, [.6, 1.25, 2.85, 1.25, 2.1, 1.65, 1.3], rows, fs=4.9, rh=.148)
    bad = b.clarity(fig, None, None, bg); print("M-001 text clashes:", len(bad)); [print("   ", m) for m in bad[:8]]
    b.save(fig, "M-001", pdf)


# ---------------------------------------------------------------------------------------------- M-002: loads
def loads_sheet(pdf):
    notes = [("Method", ["ACCA Manual J method, simplified and", "written out room by room:", "Heat loss = U x A x (70 - 9 F) per surface", "  + infiltration + ventilation.",
                         "Heat gain = U x A x CLTD per surface", "  + glass A x SHGC x solar factor", "  + people, lights, appliances", "  + infiltration + ventilation.",
                         "Infiltration and ventilation shared by", "the rooms' outside wall area."]),
             ("Confirm", ["Design temperatures from NOAA data for", "Morgantown: check Manual J Table 1A.", "Window count from the scan; heights", "assumed. Insulation: as assumed below.",
                          "If the windows are replaced or the", "insulation differs, rebuild: the sheets", "follow automatically."])]
    fig, bg, _ = b.bsheet("M-002", "Heating and cooling loads", 0, notes, sub="Rear building · all flats")
    bg.text(.5, 10.25, "HEATING AND COOLING LOADS · room by room · Manual J method", fontsize=9.5, fontweight="bold", color=INK, va="center")
    y = 9.98
    cond = [["Design conditions", "Value"], ["Location, climate zone", f"{mq.DES['place']}, zone {mq.DES['zone']}"], ["Winter: outdoor / indoor", f"{mq.DES['t_out_h']} F / {mq.DES['t_in_h']} F (dT {mq.DTH} F)"],
            ["Summer: outdoor / indoor", f"{mq.DES['t_out_c']} F / {mq.DES['t_in_c']} F at 50 % RH (dT {mq.DTC} F)"], ["Moisture difference", f"{mq.DES['gr']} grains per lb"],
            ["Infiltration (after air sealing)", f"{mq.ACH_H} ACH winter, {mq.ACH_C} ACH summer"], ["People", "1 per bedroom + 1; 230 Btu/h sensible, 200 latent"]]
    table(bg, .5, y, [1.6, 2.4], cond, fs=5.0, rh=.15)
    env = [["Assumed after the gut", "U", "CLTD"], ["2x4 walls, R-15 insulation", f"{mq.U['wall']}", f"{mq.CLTD['wall']}"], ["Lower flat stone walls + 2x4 R-15", f"{mq.U['stone']}", f"{mq.CLTD['stone']}"],
           [f"Windows kept, double pane (SHGC {mq.SHGC})", f"{mq.U['window']}", "dT + sun"], ["Attic sloped ceilings, R-30 foam", f"{mq.U['roof']}", f"{mq.CLTD['roof']}"],
           ["Attic knee walls, R-20", f"{mq.U['knee']}", f"{mq.CLTD['knee']}"], ["Ceilings under eaves, R-49", f"{mq.U['ceil']}", f"{mq.CLTD['ceil']}"], ["Lower flat floor on earth, per ft", f"F {mq.F_SLAB}", "-"]]
    table(bg, 4.7, y, [1.9, .45, .55], env, fs=5.0, rh=.15)
    sol = [["Sun", "N", "NE", "E", "SE", "S", "SW", "W", "NW"], ["Btu/h sf"] + [f"{mq.SOLAR[k_]}" for k_ in ("N", "NE", "E", "SE", "S", "SW", "W", "NW")]]
    table(bg, 7.85, y, [.55] + [.32] * 8, sol, fs=5.0, rh=.15)
    y = 8.7
    hdr = ["Room", "Area", "Walls sf", "Glass sf", "Roof/ceil sf", "Heat: surfaces", "+ air", "= Heat Btu/h", "Cool: surfaces", "+ inside", "+ air", "= Cool Btu/h", "CFM"]
    wid = [1.75, .38, .5, .5, .58, .72, .5, .72, .72, .55, .45, .72, .4]
    for k, s in SYS.items():
        rows = [hdr]
        for x in s["rooms"]:
            r = x["r"]; wa = sum(float(rw[1].split()[0]) for rw in x["rows"] if rw[0].startswith(("Wall", "Knee"))); ga = sum(float(rw[1].split()[0]) for rw in x["rows"] if rw[0].startswith("Window"))
            ca = sum(float(rw[1].split()[0]) for rw in x["rows"] if rw[0].startswith(("Ceiling",)))
            hs = sum(rw[3] for rw in x["rows"]); cs = sum(rw[4] for rw in x["rows"])
            if x["H"] < 1 and x["C"] < 60: continue
            rows.append([f"{r['no']} {r['name'].split(' (')[0]}", f"{x['A']:.0f}", f"{wa:.0f}", f"{ga:.0f}", f"{ca:.0f}", f"{hs:,.0f}", f"{x['inf_h'] + x['vent_h']:,.0f}", f"{x['H']:,.0f}",
                         f"{cs:,.0f}", f"{x['int']:,.0f}", f"{x['inf_c'] + x['vent_c']:,.0f}", f"{x['C']:,.0f}",
                         "heater" if (x['fl'], r['no']) == mq.STAIR_HEATER else (f"via {x['via']}" if "via" in x else f"{x.get('cfm', '-')}")])
        rows.append(["Latent (moisture)", "", "", "", "", "", "", "", "", f"{mq.PEOPLE_L * s['npeople']:,}", f"{s['lat'] - mq.PEOPLE_L * s['npeople']:,.0f}", f"{s['lat']:,.0f}", ""])
        rows.append([f"TOTAL SYSTEM {k}", "", "", "", "", "", "", f"{s['H']:,.0f}", "", "", "", f"{s['Ct']:,.0f}", f"{s['cfm']}"])
        bg.text(.5, y, f"SYSTEM {k} · {q.FLATS[k]['name'].upper()} · infiltration {s['inf_h']:.0f} / {s['inf_c']:.0f} CFM, ventilation {s['vent']:.0f} CFM", fontsize=6.0, fontweight="bold", color=INK, va="center")
        y = table(bg, .5, y - .1, wid, rows, fs=4.7, rh=.132) - .22
    # sizing results, right column
    x0 = 9.1; yy = 8.7
    bg.text(x0, yy, "EQUIPMENT SIZING (Manual S)", fontsize=6.4, fontweight="bold", color=INK, va="center"); yy -= .2
    for k, s in SYS.items():
        lines = [f"System {k}: heat loss {s['H']:,.0f} Btu/h; furnace {s['furn'] / 1000:.0f}k in x 96 % = {s['furn'] * .96 / 1000:.1f}k out.",
                 f"  {s['furn'] * .96 / s['H']:.1f} x the load: smallest furnace made; 2-stage or modulating.",
                 f"Cooling {s['Cs']:,.0f} sensible + {s['lat']:,.0f} latent = {s['Ct']:,.0f} Btu/h ({s['Ct'] / 12000:.2f} ton).",
                 (f"  {s['tons']:g} ton variable speed: the design load is {s['Ct'] / (s['tons'] * 12000) * 100:.0f} % of it; sized up for 105 F (below)." if s['tons'] > s['tons_min'] else
                  f"  {s['tons']:g} ton {'(smallest ducted size; variable speed turns down)' if s['tons'] > s['tons_calc'] else ''}".rstrip()),
                 f"Blower {s['cfm']} CFM = {s['cfm'] / s['tons']:.0f} CFM per ton{' (the most the 14 x 8 trunk takes)' if s['cfm'] < 400 * s['tons'] else ''}; rooms get it",
                 "  in proportion to the larger of their heat and cool shares (Manual D)."]
        for ln in lines: bg.text(x0, yy, ln, fontsize=5.0, color=INK, va="center"); yy -= .13
        yy -= .1
    yy -= .05
    bg.text(x0, yy, "WORKED EXAMPLE", fontsize=6.4, fontweight="bold", color=INK, va="center"); yy -= .2
    x, _k = room_rec(5, "303")
    bg.text(x0, yy, f"303 Bedroom 3 (upper flat), {x['A']:.0f} sf, ceiling {x['hgt']:.1f} ft", fontsize=5.0, color=INK, va="center"); yy -= .14
    for rw in x["rows"]:
        bg.text(x0, yy, f"{rw[0]}: {rw[1]} x U {rw[2]} -> heat {rw[3]:,.0f}, cool {rw[4]:,.0f}", fontsize=4.9, color=INK, va="center"); yy -= .125
    bg.text(x0, yy, f"Air (infiltration + ventilation share): heat {x['inf_h'] + x['vent_h']:,.0f}, cool {x['inf_c'] + x['vent_c']:,.0f}", fontsize=4.9, color=INK, va="center"); yy -= .125
    bg.text(x0, yy, f"Inside: person 230 + lights + computer = {x['int']:,.0f}", fontsize=4.9, color=INK, va="center"); yy -= .125
    bg.text(x0, yy, f"Totals: heat {x['H']:,.0f} Btu/h, cool {x['C']:,.0f} Btu/h -> {x['cfm']} CFM", fontsize=5.0, color=INK, va="center", fontweight="bold"); yy -= .3
    E = mq.EXTREME
    bg.text(x0, yy, f"CHECK AT LAST YEAR'S EXTREMES ({E['t_out_h']} F AND {E['t_out_c']} F)", fontsize=6.4, fontweight="bold", color=INK, va="center"); yy -= .13
    rows = [["System", f"Heat loss at {E['t_out_h']} F", "Furnace out", f"Cool load at {E['t_out_c']} F", f"AC at {E['t_out_c']} F (est.)", "Result"]]
    for k, s in SYS.items():
        X = s["ext"]; cap = mq.CAP_105 * s["tons"] * 12000
        rows.append([k, f"{X['H']:,.0f}", f"{s['furn'] * .96:,.0f}", f"{X['Ct']:,.0f}", f"{cap:,.0f}", "holds 75 F" if cap >= X["Ct"] else f"{cap / X['Ct'] * 100:.0f} %: +2 F at peak"])
    yy = table(bg, x0, yy, [.4, .78, .6, .78, .72, .86], rows, fs=4.8, rh=.14) - .1
    for t in ["Same model with the outdoor temperatures moved: walls and roof +18 F, moisture 40 grains. Manual J sizes to the 1 % values",
              "(9 F / 87 F, exceeded a few days a year); sizing to the record would make units that short-cycle and leave the air damp.",
              f"So: variable-speed condensers, checked to give at least 90 % at {E['t_out_c']} F at full speed ({mq.CAP_105:.0%} of rating assumed)."]:
        bg.text(x0, yy, t, fontsize=4.9, color=INK, va="center"); yy -= .125
    bad = b.clarity(fig, None, None, bg); print("M-002 text clashes:", len(bad)); [print("   ", m) for m in bad[:8]]
    b.save(fig, "M-002", pdf)


# ---------------------------------------------------------------------------------------------- M-003: air distribution, outdoor units, venting
def dist_sheet(pdf):
    notes = [("Air distribution", ["Room CFM from M-002. Registers sized", "for about 500 fpm; branches at about", "0.08 in. per 100 ft. Jump ducts at", "400 fpm or less. Filter returns at",
                                   "300 fpm or less through the filter."]),
             ("Outdoor units", ["Five condensers in the walled area under", "the rear deck (3 for 390, 2 for 441).", "The airflow check below shows the deck", "must have an open grate over them.",
                                "Line sets and final layout pending the", "area's size: NOT FINALIZED."])]
    fig, bg, _ = b.bsheet("M-003", "Air distribution, outdoor units and venting", 0, notes, sub="Rear building · all flats")
    bg.text(.5, 10.25, "AIR DISTRIBUTION SCHEDULE, OUTDOOR UNITS AND VENTING", fontsize=9.5, fontweight="bold", color=INK, va="center")
    y = 9.98; wid = [.35, 1.55, .5, .45, .9, .55, .9]
    xx = .5
    for k, s in SYS.items():
        rows = [["Sys", "Room", "CFM", "Regs", "Register", "Branch", "Return path"]]
        for x in s["served"]:
            r = x["r"]; n = mq.n_registers(r, x["cfm"]); c = x["cfm"] / n
            ret = (("transfer grille " if x["fl"] == 6 else "jump duct ") + (f"{mq.jump(x['cfm'])} in." if x["fl"] != 6 else ("14x6" if x["cfm"] > 80 else "12x6"))) if r["kind"] == "bed" else ("none (exhaust)" if r["kind"] == "bath" else "open to return")
            nm = f"{r['no']} {r['name'].split(' (')[0]}" + (f" + stair {x['plus']['r']['no']}" if "plus" in x else "")
            rows.append([k, nm, f"{x['cfm']}", f"{n}", f"{mq.register(c)}{' floor' if x['fl'] == 6 else ' ceiling'}", f"{mq.round_duct(c)} in.", ret])
        for rt in mr.layout(mr.SPACE[{"A": 3, "B": 4, "C": 5}[k]])["rets"]:
            rows.append([k, f"Return {rt['name']}" + (" hall ceiling" if rt["kind"] == "ceiling" else " attic stair-hall floor"), f"{rt['cfm']}", "1", f"{rt['size']} filter",
                         "", "duct to the furnace" if rt["kind"] == "ceiling" else "on the R-C1 box"])
        vel = s["cfm"] / (14 * 8 / 144)
        bg.text(xx, y, f"SYSTEM {k} · {s['cfm']} CFM · trunk {mr.TRUNK_SIZE} in. ({vel:.0f} fpm)", fontsize=6.0, fontweight="bold", color=INK, va="center")
        y = table(bg, xx, y - .1, wid, rows, fs=4.8, rh=.138) - .22
    # ventilation
    bg.text(.5, y, "WHOLE-HOUSE VENTILATION (IRC M1505.4.3: 0.03 x floor area + 7.5 x (bedrooms + 1))", fontsize=6.0, fontweight="bold", color=INK, va="center"); y -= .12
    rows = [["Flat", "Floor sf", "Bedrooms", "Required CFM", "Provided by"]] + [[k, f"{q.AREA[k]:,}", f"{q.FLATS[k]['beds']}", f"{0.03 * q.AREA[k]:.0f} + {7.5 * (q.FLATS[k]['beds'] + 1):.1f} = {SYS[k]['vent']:.0f}",
                                                                              f"{q.FLATS[k]['baths']} bath fans on continuous low, {SYS[k]['vent'] / q.FLATS[k]['baths']:.0f} CFM each"] for k in SYS]
    table(bg, .5, y, [.35, .55, .55, 1.3, 2.4], rows, fs=4.8, rh=.14)
    # outdoor units: airflow check
    x0 = 6.0; yy = 9.98
    bg.text(x0, yy, "OUTDOOR UNITS UNDER THE REAR DECK: AIRFLOW CHECK", fontsize=6.2, fontweight="bold", color=INK, va="center"); yy -= .14
    units = [(f"390 AC-{k}", SYS[k]["tons"]) for k in SYS] + [("441 A (not designed yet)", 2.0), ("441 B (not designed yet)", 2.0)]
    rows = [["Unit", "Ton", "Fan CFM (900/ton)", "Heat out Btu/h (15k/ton)", "Air leaves at"]]
    for n, t in units: rows.append([n, f"{t:g}", f"{900 * t:,.0f}", f"{15000 * t:,.0f}", f"+{15000 / (1.08 * 900):.0f} F"])
    tc = sum(900 * t for _n, t in units); th = sum(15000 * t for _n, t in units)
    rows.append(["Total", f"{sum(t for _n, t in units):g}", f"{tc:,.0f}", f"{th:,.0f}", ""])
    yy = table(bg, x0, yy, [1.35, .35, .9, 1.2, .65], rows, fs=4.8, rh=.14) - .12
    chk = [f"Fresh-air opening needed: {tc:,.0f} / 300 fpm = {tc / 300:.0f} sf free (lattice is about half open).",
           f"Closed U with a solid deck: staying within 3 F of outdoor air needs {th:,.0f} / (1.08 x 3) = {th / 3.24:,.0f} CFM",
           f"of exchange through one opening: about 5 x the fans. Not possible: the units would overheat.",
           f"With an open grate over the units: hot air leaves straight up. Grate free area >= {tc:,.0f} / 500 fpm = {tc / 500:.0f} sf",
           f"(about {tc / 500 / .7:.0f} sf of 70 % open grating, about 4 x 4 ft over each unit). Open end stays open.",
           "Units: 12 in. from walls, 12-24 in. apart, 3 ft service aisle, 3 ft from dryer and furnace vents."]
    for t in chk: bg.text(x0, yy, t, fontsize=5.0, color=INK, va="center"); yy -= .13
    yy -= .08
    bg.text(x0, yy, TBD, fontsize=5.0, color=LS, va="center", fontweight="bold"); yy -= .22
    rows = [["Line set", "Liquid", "Suction (insulated)", "Route", "Length"]] + [[f"LS-{k}", mq.LINESET[SYS[k]['tons']][0], mq.LINESET[SYS[k]['tons']][1], "coil, chase, lower flat ceiling, out to the deck", "TBD"] for k in SYS]
    yy = table(bg, x0, yy, [.6, .45, .9, 2.4, .5], rows, fs=4.8, rh=.14) - .25
    # venting riser in the chase
    bg.text(x0, yy, "OLD CHIMNEY CHASE: WHAT RUNS IN IT (schematic)", fontsize=6.2, fontweight="bold", color=INK, va="center"); yy -= .2
    items = [("Drain and vent stack S, 3 in. (plumbing)", PVC), ("F-A, F-B, F-C: 2 in. PVC exhaust + 2 in. intake each, to the roof", PVC),
             ("Water heaters A, B, C: PVC vents to the roof (size per the units)", PVC),
             ("Feeders B and C (electrical, E-004)", INK), ("Line sets LS-A, B, C: pending", LS)]
    for t, col in items:
        bg.add_patch(Rectangle((x0, yy - .05), .14, .1, fc=col, ec=col)); bg.text(x0 + .22, yy, t, fontsize=5.0, color=INK, va="center"); yy -= .14
    bg.text(x0, yy - .05, "Chase inside about 2'-0\" x 2'-4\": check the fit when the brick is out; firestop at every floor. Lower level: the", fontsize=5.0, color=GREY, va="center")
    bg.text(x0, yy - .19, "2x6 pipe wall between bath 1 and the laundry. The attic is fed in its floor framing: no ducts in the chase.", fontsize=5.0, color=GREY, va="center")
    bad = b.clarity(fig, None, None, bg); print("M-003 text clashes:", len(bad)); [print("   ", m) for m in bad[:8]]
    b.save(fig, "M-003", pdf)


SHEETS = [("M-001", "Mechanical notes and schedules", notes_sheet), ("M-002", "Heating and cooling loads", loads_sheet),
          ("M-003", "Air distribution, outdoor units and venting", dist_sheet)] + [
          (n, t, (lambda fl_, n_: (lambda pdf: plan_sheet(pdf, n_, fl_)))(fl, n)) for n, t, fl in
          (("M-101", "Lower flat: HVAC plan", 3), ("M-102", "Middle flat: HVAC plan", 4), ("M-103", "Upper flat main floor: HVAC plan", 5), ("M-104", "Attic: HVAC plan", 6))]

if __name__ == "__main__":
    from matplotlib.backends.backend_pdf import PdfPages
    only = sys.argv[1:]
    out = os.path.join(b.HERE, "drawings", "390-Forest_Mechanical_Rev1.pdf" if not only else "_test_m.pdf")
    with PdfPages(out) as pdf:
        for n, _t, fn in SHEETS:
            if not only or n in only: fn(pdf)
    print("wrote", out)
