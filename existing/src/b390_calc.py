"""390 Forest Ave builder set: electrical load calculation (E-002) and lighting calculation (E-003)."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build390 as b  # noqa: E402
from common import INK, GREY, table  # noqa: E402

FLATS = [("Lower flat", 800, 2900, "1.5 ton"), ("Middle flat", 890, 3400, "2 ton"), ("Upper flat + attic", 1450, 4400, "3 ton")]
FIXED = [("Dishwasher", 1200), ("Range hood / microwave", 1500), ("Furnace blower", 800), ("Water heater power vent", 200), ("Bath fans", 100)]
SCEN = [("A", "As drawn: electric ranges in the lower and middle flats, electric dryers, cooling", (12000, 12000, 0), 5000),
        ("B", "Gas ranges in all three flats, electric dryers, cooling", (0, 0, 0), 5000),
        ("C", "Gas ranges and gas dryers in all three flats, cooling", (0, 0, 0), 0)]


def std(area, rng, dry, ac):
    gen = 3 * area + 3000 + 1500
    g = 3000 + 0.35 * (gen - 3000)
    fx = 0.75 * sum(v for _n, v in FIXED)
    r = 8000 if rng else 0
    return g + fx + dry + r + ac + 0.25 * ac, dict(gen=gen, g=g, fx=fx, r=r)


def opt(area, rng, dry, ac):
    tot = 3 * area + 4500 + sum(v for _n, v in FIXED) + rng + dry
    return 10000 + 0.4 * max(0, tot - 10000) + ac, tot


def panel(a):
    for p in (100, 125, 150, 200):
        if a <= p: return p
    return 400


def service(sc):
    _k, _t, rngs, dry = sc
    gen = sum(3 * f[1] + 4500 for f in FLATS); g = 3000 + 0.35 * (gen - 3000)
    fx = 0.75 * 3 * sum(v for _n, v in FIXED)
    nr = sum(1 for r in rngs if r); r = {0: 0, 1: 8000, 2: 11000, 3: 14000}[nr]
    ac = sum(f[2] for f in FLATS) + 0.25 * max(f[2] for f in FLATS)
    return g + fx + 3 * dry + r + ac


def load_sheet(pdf):
    fig, bg, _ = b.bsheet("E-002", "Electrical load calculation: do the flats need more than 100 A?", 0, [
        ("Answer", ["100 A per flat is enough by the NEC optional", "method in every case studied.", "200 A panels are not needed for these loads.", "The limit is the building service, not the", "panels: see the last table."]),
        ("Method", ["NEC 2020 Article 220, 120/240 V single phase.", "Standard: 220.42 lighting demand, 220.53", "appliances at 75 %, 220.54 dryer 5 kW,", "220.55 range 8 kW, cooling + 25 %.",
                    "Optional (220.82): first 10 kVA at 100 %,", "the rest at 40 %, plus cooling at 100 %.", "Heating is gas; only the blower counts."]),
        ("Not known", ["The size of the existing service cable and", "meter sockets. The photo shows one service", "cable feeding a 3-meter socket: typical of a", "200 A service, but the electrician must", "read the cable and socket ratings."])],
        sub="Rear building · all flats")
    bg.text(0.6, 10.2, "ELECTRICAL LOAD CALCULATION", fontsize=11, fontweight="bold", color=INK, va="center")
    bg.text(0.6, 9.95, "Areas: lower flat 800 sf, middle flat 890 sf, upper flat with attic 1,450 sf. Fixed appliances per flat: " + ", ".join(f"{n} {v:,} VA" for n, v in FIXED) + ".", fontsize=6.2, color=GREY, va="center")
    y = 9.6
    for k, title, rngs, dry in SCEN:
        bg.text(0.6, y, f"CASE {k}: {title}", fontsize=7.2, fontweight="bold", color=INK, va="center")
        rows = [["Flat", "Lighting + small appl. + laundry", "after demand", "Fixed appl. 75 %", "Dryer", "Range", "Cooling + 25 %", "Standard method", "Optional method", "Smallest panel"]]
        for (name, area, ac, ton), rg in zip(FLATS, rngs):
            sv, d = std(area, rg, dry, ac); ov, _t = opt(area, rg, dry, ac)
            rows.append([name, f"{d['gen']:,} VA", f"{d['g']:,.0f} VA", f"{d['fx']:,.0f} VA", f"{dry:,} VA" if dry else "gas", "8,000 VA" if rg else "gas", f"{1.25 * ac:,.0f} VA ({ton})",
                         f"{sv:,.0f} VA = {sv / 240:.0f} A", f"{ov:,.0f} VA = {ov / 240:.0f} A", f"{panel(ov / 240)} A  (standard: {panel(sv / 240)} A)"])
        y = table(bg, 0.6, y - 0.15, [1.25, 1.75, 0.95, 1.0, 0.7, 0.75, 1.3, 1.55, 1.55, 1.75], rows, fs=5.5, rh=0.19) - 0.3
    bg.text(0.6, y, "WHOLE BUILDING: what the service outside has to carry (standard method, three flats together)", fontsize=7.2, fontweight="bold", color=INK, va="center")
    rows = [["Case", "Loads", "Service load", "On a 200 A service", "Service needed"]]
    for sc in SCEN:
        v = service(sc); a = v / 240
        rows.append([sc[0], sc[1], f"{v:,.0f} VA = {a:.0f} A", "over by %d A" % (a - 200) if a > 200 else "fits, %d %% used" % (100 * a / 200), "320 A class (400 A meter stack)" if a > 200 else "200 A"])
    y = table(bg, 0.6, y - 0.15, [0.5, 5.3, 1.9, 1.9, 2.95], rows, fs=5.7, rh=0.2) - 0.3
    b.text_block(bg, 0.6, y, "What this means", [
        "1  Panels: a new 100 A panel per flat carries the load in every case by the optional method (the method the code allows for a single dwelling unit).",
        "   By the stricter standard method, case A puts the lower and middle flats at or just over 100 A, so 125 A panels are the safe choice if the electric ranges stay.",
        "2  200 A panels: not needed. A 200 A panel only helps if the service and meter socket feeding it are also 200 A per flat, which means a new 600 A service.",
        "   If you want room to grow, fit 125 A, 30-space panels with 100 A main breakers: the spaces are what you run out of, not the amps.",
        "3  The service: with electric ranges, electric dryers and new cooling the building needs about 234 A, more than a 200 A service. Gas ranges bring it to 188 A;",
        "   gas ranges and gas dryers bring it to 125 A. So the cheapest way to keep the existing service size is gas cooking (and gas drying) in all three flats.",
        "4  Before deciding: have the electrician read the service cable size and the meter socket rating, and ask Mon Power what the drop can supply.",
        "5  Not included: electric car charging, electric water heating or electric heat. Any of those changes the answer."], fs=6.3, lh=0.165)
    b.save(fig, "E-002", pdf)


TARGET = {"bed": (15, "bedroom, general"), "living": (15, "living room, general"), "kitchen": (35, "kitchen, general"), "bath": (30, "bath, general"),
          "hall": (8, "hall"), "stair": (8, "stair"), "laundry": (30, "laundry"), "mech": (25, "mechanical / laundry"), "closet": (8, "closet")}
LM, CU, LLF = 900, 0.60, 0.85


def light_sheet(pdf):
    fig, bg, _ = b.bsheet("E-003", "Lighting calculation: how many lights each room needs", 0, [
        ("Answer", ["One ceiling light per bedroom is not enough:", "it gives about 9 foot-candles where 15 is", "the target. Bedrooms need 3 to 5 recessed", "lights each, living rooms 6 to 8, kitchens",
                    "6 to 8 plus under-cabinet strips, baths 2 to", "3 plus the vanity light."]),
        ("Method", ["Lumen method: lights = target x area /", "(lumens x CU x LLF).", "Light: 6 in. LED recessed, 900 lumens, 12 W,", "3000 K, dimmable.",
                    "CU 0.60 (room shape, 7 to 8 ft ceilings,", "light walls), LLF 0.85 (dirt and ageing).", "Targets follow IES residential practice."]),
        ("Use", ["Counts are the general lighting. Task lights", "are extra: vanity light in each bath,", "under-cabinet strip in each kitchen.", "Put bedrooms and living rooms on dimmers."])],
        sub="Rear building · all levels")
    bg.text(0.6, 10.2, "LIGHTING CALCULATION", fontsize=11, fontweight="bold", color=INK, va="center")
    rows = [["No.", "Room", "Area", "Target", "Lumens needed", "Recessed lights", "Result", "Extra"]]
    for fl in (3, 4, 5, 6):
        for r in b.LV[fl]["rooms"]:
            if r["kind"] == "closet":
                continue
            area = sum((x1 - x0) * (y1 - y0) for (x0, y0, x1, y1) in r["rects"])
            fc, _d = TARGET[r["kind"]]
            need = fc * area / (CU * LLF); n = max(1, math.ceil(need / LM)); got = n * LM * CU * LLF / area
            extra = {"bath": "vanity + fan light", "kitchen": "under-cab. strip", "bed": "closet light", "mech": "", "living": ""}.get(r["kind"], "")
            rows.append([r["no"], r["name"], f"{area:.0f} sf", f"{fc} fc", f"{need:,.0f}", str(n), f"{got:.0f} fc", extra])
    half = (len(rows) + 1) // 2
    w = [0.4, 1.75, 0.5, 0.5, 0.85, 0.75, 0.55, 1.0]
    table(bg, 0.6, 9.9, w, rows[:half], fs=5.4, rh=0.185); table(bg, 7.0, 9.9, w, [rows[0]] + rows[half:], fs=5.4, rh=0.185)
    y = 9.9 - 0.185 * (half + 1) - 0.4
    b.text_block(bg, 0.6, y, "Notes", [
        "Check: one 1,800 lumen ceiling fixture in a 100 sf bedroom gives 1,800 x 0.60 x 0.85 / 100 = 9 foot-candles. That is why one light per room reads dim.",
        "Closets: one enclosed LED surface light each (about 800 lumens). Stairs: one light at each landing, switched top and bottom.",
        "Lower flat ceilings are 6'-10\" to 7'-6\": use shallow wafer-type recessed lights that fit under ducts and joists, 1/2 in. deep housings.",
        "Spacing rule: about 4 to 5 ft apart and 2 to 3 ft off the walls; keep them off the ceiling fans' blades and 3 ft from smoke alarms' test reach.",
        "The electrical plans E-101 to E-104 will be redrawn to these counts once the floor plans are approved."], fs=6.3, lh=0.165)
    b.save(fig, "E-003", pdf)


SHEETS = [("E-002", "Load calculation", load_sheet), ("E-003", "Lighting calculation", light_sheet)]
