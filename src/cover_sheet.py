"""Sheets G-001 (cover and summary) and G-002 (code analysis and general notes)."""
from common import *  # noqa: F401,F403
from struct_sheets import text_columns

INDEX = [("G-001", "Cover and summary"), ("G-002", "Code analysis and general notes"),
         ("C-101", "Existing site conditions"), ("C-102", "Site plan and zoning"), ("C-103", "Vehicle access and towing"),
         ("A-101", "Garage level plan"), ("A-102", "Unit A plan"), ("A-103", "Unit B plan"),
         ("A-201", "Street elevation"), ("A-301", "Building section"),
         ("S-001", "Structural notes and criteria"), ("S-101", "Foundation plan"), ("S-102", "Unit A floor framing"),
         ("S-103", "Unit B floor framing"), ("S-104", "Roof framing and shear walls"), ("S-301", "Structural sections"),
         ("P-101", "Plumbing: garage level"), ("P-102", "Plumbing: Unit A"), ("P-103", "Plumbing: Unit B"),
         ("P-201", "Plumbing riser and schedules"),
         ("M-101", "Mechanical: garage level"), ("M-102", "Mechanical: Unit A"), ("M-103", "Mechanical: Unit B"),
         ("E-101", "Electrical: garage level"), ("E-102", "Electrical: Unit A"), ("E-103", "Electrical: Unit B"),
         ("E-201", "One-line diagram and loads")]


def sheet_g001(pdf, m):
    fig, bg = new_sheet("G-001", "Cover and summary", "As noted", None)
    x0 = SHEET_W - MARGIN - TB_W
    tx = x0 + 0.16
    top = SHEET_H - MARGIN
    bg.text(tx, top - 1.95, "DRAWING INDEX", fontsize=7.2, fontweight="bold", va="top")
    for i, (n, t) in enumerate(INDEX):
        bg.text(tx, top - 2.2 - i * 0.158, n, fontsize=5.9, fontweight="bold", va="top")
        bg.text(tx + 0.6, top - 2.2 - i * 0.158, t, fontsize=5.9, va="top")
    bg.text(tx, top - 6.62, "SOURCES", fontsize=7.2, fontweight="bold", va="top")
    src = ["County assessment record, parcel", "31-13-0029-0084-0000 · tax map 09-0029", "City of Morgantown zoning layer + code",
           "WV State Building Code, 87 CSR 4", "WV 1 m LiDAR · public GIS, 21 Nov 2026"]
    for i, s in enumerate(src):
        bg.text(tx, top - 6.86 - i * 0.155, s, fontsize=5.6, va="top", color=INK)
    L = MARGIN + 0.45
    bg.text(L, top - 0.62, "387 BAIRD STREET", fontsize=30, fontweight="bold", va="center")
    bg.text(L, top - 1.08, "Two-family dwelling, six bedrooms and six baths, over a 3-car garage · head-start permit set, Rev C",
            fontsize=12, va="center", color=INK)
    bg.text(L, top - 1.40, "Morgantown, Monongalia County, West Virginia 26505 · Tax District 13 (5th Ward), Map 29, Parcel 84 · Zoned R-2",
            fontsize=8, va="center", color=GREY)
    bg.plot([L, x0 - 0.45], [top - 1.62, top - 1.62], color=INK, lw=1.0)
    c1, c2, c3 = L, L + 4.42, L + 8.84
    cols = [
        (c1, 4.0, [
            ("What this set is", [
                "A coordinated first draft of every discipline, so the\nlicensed architect and engineers start from a\nworked-out scheme instead of a blank page.",
                "It is not engineered and cannot be stamped as-is.\nEach professional must review, recalculate and take\nresponsibility for their own sheets.",
            ]),
            ("The building", [
                ("Garage level", "3 cars side by side + 96 sf\nconditioned owner storage,\nlobby, mech room"),
                ("Unit A", "Main level, 3 bedrooms each\nwith a private bath, ±780 sf"),
                ("Unit B", "Upper level, same plan"),
                ("Total", "6 bedrooms, 6 baths"),
                ("Footprint", f"{FOOTPRINT:,.0f} sf, {m['cov']:.0f} % of the lot"),
                ("Height", f"{EL_MEAN_ROOF - EL_REF:.1f} ft, 2 storeys over a\nbasement garage"),
                ("Structure", "Concrete retaining walls,\nsteel frame at the doors,\nwood trusses and walls"),
                ("Services", "All-electric: heat pumps, 80 gal\nwater heaters, 400 A service"),
            ]),
            ("The property", [
                ("Owner of record", "R & L RENTALS LLC"),
                ("Deed", "Book 1246, Page 78"),
                ("Lot", f"50 ft x 34 to 48 ft, {LOT_AREA_DEED:,.0f} sf"),
                ("Existing", "1929 house, 768 sf"),
            ]),
        ]),
        (c2, 4.0, [
            ("How your requests were handled", [
                ("Most cars", "Three. The lot is 50 ft wide and\nside setbacks leave 35'-6\". Three\n8'-11\" stalls and the stair fill it.\nA duplex also requires three."),
                ("Six bedrooms", "Three per flat, each with its own\nbath and entry hall. Rooms are\n80 to 106 sf (70 sf minimum)."),
                ("Every floor drawn", "Each trade has a separate sheet\nfor the garage, Unit A and Unit B."),
                ("Storage", "One 96 sf conditioned room on\nthe garage level, 16 ft rack."),
                ("Tow trucks", "Each car has its own straight run\nto a door; no posts in the apron;\nflush floor. See C-103."),
                ("Entrance", "One street-level door to a common\nstair, reached by a landing on the\nlot. No steps."),
                ("City property", "Only the driveway apron is in the\nright-of-way. No walls, steps, posts\nor porches cross the lot line."),
            ]),
            ("Follows the code", [
                "Side setbacks, lot coverage, height, parking count,\nporch standard, unit separation, egress, stairs,\nsmoke/CO alarms, energy code targets.",
            ]),
        ]),
        (c3, 4.0, [
            ("Cannot follow the code: approvals needed", [
                f"1.  Rear setback. {m['r_ne']:.1f} ft at the tightest corner against\n     20 ft required. The R-2 setbacks leave ±{m['env_area']:,.0f} sf of\n     buildable area on this lot, so nothing fits without it.",
                "2.  Front setback. 8 ft against 10 ft, unless the block-\n     averaging rule sets it by the neighbours.",
                "3.  Garage width. 78 % of the front against 65 %. Two\n     cars would comply, but then the duplex is one\n     parking space short. One or the other needs relief.",
                "4.  Driveway width at the street (26 ft against 22 ft)\n     and a sidewalk waiver: City Engineer.",
            ]),
            ("Order of work", [
                "1.  Boundary and topographic survey.",
                "2.  Pre-application meeting, Planning Division,\n     389 Spruce St, 304-284-7431.",
                "3.  Purchase contingent on Board of Zoning Appeals\n     approval. Do not demolish before it.",
                "4.  Geotechnical borings and shoring concept.",
                "5.  Architect and engineers take over this set.",
                "6.  Utilities: MUB sewer/water taps, Mon Power service.",
            ]),
        ]),
    ]
    text_columns(bg, cols, top=top - 1.92, fs=6.6, lh=0.168)
    kx = plan_axes(fig, c2 + 0.55, MARGIN + 0.3, (-22, 74), (-25, 52), 34)
    rect(kx, -22, PAVE_S, 74, PAVE_N, fc="#e3e5e8", ec="none", z=1)
    rect(kx, -22, PAVE_N, 74, 0, fc="#fbe9e7", ec="none", z=1)
    txt(kx, 26, -14, "BAIRD STREET", size=5.4, color=GREY, weight="bold")
    poly(kx, LOT, fc="none", ec=ACCENT, lw=1.2, z=4, ls=(0, (9, 2.5, 1.5, 2.5)))
    poly(kx, OUT, fc="#d9dcdf", ec=INK, lw=1.2, z=5)
    poly(kx, APRON, fc="#cfd6de", ec=INK, lw=0.4, z=3)
    txt(kx, 27, 20, "PROPOSED", size=5.2, weight="bold", z=9)
    txt(kx, -11, 22, "442\nBAIRD", size=4.8, color=GREY)
    txt(kx, 62, 18, "441\nBAIRD", size=4.8, color=GREY)
    txt(kx, 34, 45, "386 FOREST", size=4.8, color=GREY)
    north_arrow(kx, 66, 42, 4.2, 6)
    txt(kx, -21, 49.5, "KEY PLAN", size=6.0, weight="bold", ha="left")
    save(fig, "G-001", pdf)


def sheet_g002(pdf, m):
    fig, bg = new_sheet("G-002", "Code analysis and general notes", "No scale", [
        ("Who stamps what", [
            "Whether an architect's seal is required",
            "for a two-family dwelling depends on",
            "state law and on what the city will",
            "accept. Expect at minimum:",
            "· Structural engineer (PE): all S sheets,",
            "  retaining walls, steel frame, shoring.",
            "· Geotechnical engineer: soil report.",
            "· Surveyor: boundary, topo, stake-out.",
            "· Civil engineer: grading, driveway,",
            "  drainage, utility taps.",
            "· Architect: recommended for the code",
            "  package and the zoning hearing.",
            "· Licensed plumber, electrician and",
            "  HVAC contractor under the trade",
            "  permits.",
            "Confirm with Morgantown Code",
            "Enforcement before hiring.",
        ]),
    ])
    L = MARGIN + 0.45
    bg.text(L, SHEET_H - MARGIN - 0.3, "CODE ANALYSIS AND GENERAL NOTES", fontsize=12, fontweight="bold", va="center")
    cols = [
        (L, 4.0, [
            ("Zoning (Morgantown P&Z Code)", [
                ("District", "R-2; two-family is permitted"),
                ("Lot", "2,052 sf deeded; 5,000 min.\nNonconforming, buildable\nunder 1373.04"),
                ("Frontage", "50 ft (40 min.) ✓"),
                ("Front setback", "8 ft (10 min.) ✗ or 1363.02(C)"),
                ("Side setbacks", f"5.0 and {m['w_n']:.1f} to {m['w_s']:.1f} ft (5 min.) ✓"),
                ("Rear setback", f"{m['r_ne']:.1f} to {m['r_nw']:.1f} ft (20 min.) ✗"),
                ("Coverage", f"{m['cov']:.0f} % (50 max) ✓"),
                ("Height", f"{EL_MEAN_ROOF - EL_REF:.1f} ft (35 max) ✓"),
                ("Storeys", "2 over basement (2.5 max) ✓\nsubject to basement ruling"),
                ("Min. height", "Two-family: 2 storeys ✓"),
                ("Parking", "3 provided (1.5 x 2 = 3) ✓"),
                ("Garage width", "78 % of front (65 max) ✗"),
                ("Front porch", "73 % of front (50 min.) ✓"),
                ("HVAC units", "Rear yard, 2 ft+ off side line ✓"),
                ("Lighting", "Full cutoff, no glare ✓"),
                ("Sidewalk", "5 ft required; request waiver"),
            ]),
            ("Right-of-way rule for this design", [
                "Nothing permanent is built on city property except\nthe driveway apron, which is permitted work under a\ndriveway permit. Retaining walls, the entry landing,\ndrains, lights, meters, mailboxes and porches all stay\non the lot. Banks beside the apron are regraded,\nnot walled. This avoids an encroachment agreement.",
            ]),
        ]),
        (L + 4.42, 4.0, [
            ("Building code (2018 IRC, two-family)", [
                ("Classification", "Two-family dwelling, IRC scope:\nseparate units, 3 storeys or\nfewer above grade"),
                ("Unit separation", "R302.3: 1-hour floor/ceiling and\nwalls, tight to the roof deck"),
                ("Garage", "R302.6: 5/8 in. Type X ceiling\nunder habitable rooms; R302.5:\n20-minute door to the stair"),
                ("Lot-line walls", "R302.1: under 5 ft needs a 1-hour\nwall. All walls here are 5 ft or\nmore; eaves kept 4 ft+ away"),
                ("Egress", "R311: each unit has a door to\nthe enclosed stair leading\noutside, not through the garage"),
                ("Stairs", "R311.7: 36 in. wide, 7-3/4 in. max\nriser, 10 in. min. tread, 6'-8\"\nheadroom, handrail 34 to 38 in."),
                ("Escape windows", "R310: all six bedrooms"),
                ("Room sizes", "R304: 70 sf and 7 ft minimum;\nsmallest bedroom is 80 sf"),
                ("Alarms", "R314 smoke, R315 CO"),
                ("Guards", "R312: 36 in. at porches, 4 in.\nsphere rule"),
                ("Ceilings", "R305: 7 ft minimum"),
                ("Sprinklers", "Confirm state amendment for\ntwo-family dwellings"),
                ("Accessibility", "Not required for two units"),
            ]),
        ]),
        (L + 8.84, 4.0, [
            ("Energy (2015 IECC, climate zone 5A)", [
                ("Ceiling", "R-49"),
                ("Wood walls", "R-20, or R-13 + R-5 continuous"),
                ("Basement walls", "R-15 continuous or R-19 cavity"),
                ("Floor over garage", "R-30"),
                ("Slab edge", "R-10, 2 ft, at heated rooms"),
                ("Windows", "U-0.32 or better"),
                ("Air leakage", "Blower-door test, 5 ACH50 max"),
            ]),
            ("Trades (as adopted by West Virginia)", [
                ("Plumbing", "2018 IPC / IRC Part VII"),
                ("Mechanical", "2018 IMC / IRC Part V"),
                ("Electrical", "2020 NEC"),
                ("Fuel gas", "None: all-electric building"),
            ]),
            ("Permits to expect", [
                "Zoning variance (BZA) · demolition permit and\nutility disconnects · asbestos survey of the 1929\nhouse before demolition · building permit ·\ndriveway and right-of-way work permit · trade\npermits · MUB water and sewer taps · Mon Power\nservice · erosion and sediment controls.",
            ]),
            ("Edition check", [
                "Editions are from the state rule in force when this\nwas prepared. Confirm the editions and any local\namendments with Code Enforcement before design.",
            ]),
        ]),
    ]
    text_columns(bg, cols, fs=6.3, lh=0.162)
    save(fig, "G-002", pdf)
