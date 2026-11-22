"""Sheet G-001: cover, property data, findings and drawing index."""
from common import *  # noqa: F401,F403


def sheet_g001(pdf, m):
    fig, bg = new_sheet("G-001", "Cover and summary", "As noted", None)
    x0 = SHEET_W - MARGIN - TB_W
    tx = x0 + 0.16
    top = SHEET_H - MARGIN
    idx = [("G-001", "Cover and summary"), ("C-101", "Existing site conditions"), ("C-102", "Zoning envelope and site plan"),
           ("A-101", "Lower level: garage + storage"), ("A-102", "Main level: living"), ("A-103", "Upper level: bedrooms"),
           ("A-201", "Street elevation"), ("A-301", "Building section"), ("A-401", "Parking and storage options")]
    bg.text(tx, top - 1.95, "DRAWING INDEX", fontsize=7.2, fontweight="bold", va="top")
    for i, (n, t) in enumerate(idx):
        bg.text(tx, top - 2.2 - i * 0.2, n, fontsize=6.8, fontweight="bold", va="top")
        bg.text(tx + 0.62, top - 2.2 - i * 0.2, t, fontsize=6.8, va="top")
    bg.text(tx, top - 4.25, "SOURCES", fontsize=7.2, fontweight="bold", va="top")
    src = ["WV Real Estate Assessment record,", "parcel 31-13-0029-0084-0000 (mapwv.gov)", "WV statewide parcel GIS (WVGISTC)",
           "Monongalia Co. tax map 09-0029", "City of Morgantown zoning GIS layer", "Morgantown Planning & Zoning Code,",
           "Arts. 1329, 1331, 1337, 1363, 1365, 1373", "WV 1 m LiDAR DEM (elevations, NAVD88)", "2026 county orthophoto (viewed only)",
           "Retrieved 21 Nov 2026."]
    for i, s in enumerate(src):
        bg.text(tx, top - 4.5 - i * 0.165, s, fontsize=6.0, va="top", color=INK)

    L = MARGIN + 0.45
    bg.text(L, top - 0.62, "387 BAIRD STREET", fontsize=30, fontweight="bold", va="center")
    bg.text(L, top - 1.08, "Replacement dwelling with drive-under garage and storage · feasibility concept",
            fontsize=12, va="center", color=INK)
    bg.text(L, top - 1.40, "Morgantown, Monongalia County, West Virginia 26505 · Tax District 13 (5th Ward), Map 29, Parcel 84 · Zoned R-2",
            fontsize=8, va="center", color=GREY)
    bg.plot([L, x0 - 0.45], [top - 1.62, top - 1.62], color=INK, lw=1.0)

    def block(x, y, head, rows, w=4.0, lh=0.178, fs=7.0, kw=1.42):
        bg.text(x, y, head.upper(), fontsize=8.2, fontweight="bold", va="top", color=INK)
        bg.plot([x, x + w], [y - 0.2, y - 0.2], color=INK, lw=0.6)
        yy = y - 0.32
        for r in rows:
            if isinstance(r, tuple):
                bg.text(x, yy, r[0], fontsize=fs, va="top", color=GREY)
                bg.text(x + kw, yy, r[1], fontsize=fs, va="top", color=INK, linespacing=1.25)
                yy -= lh * (r[1].count("\n") + 1) + 0.035
            else:
                bg.text(x, yy, r, fontsize=fs, va="top", color=INK, linespacing=1.25)
                yy -= lh * (r.count("\n") + 1) + 0.045
        return yy

    c1, c2, c3 = L, L + 4.42, L + 8.84
    ytop = top - 1.92
    y = block(c1, ytop, "Ownership and sale history", [
        ("Owner of record", "R & L RENTALS LLC"),
        ("Mailing address", "3025 Greystone Dr,\nMorgantown, WV 26508"),
        ("Deed reference", "Book 1246, Page 78"),
        ("Last recorded sales", "1 Jun 2001 · \\$160,000 · code 4\n(related parties / corporations)\n1 Oct 2000 · \\$160,000 · code 1\n(sale of more than one parcel)"),
        ("Held since", "Same owner on every tax roll\nfrom 2005 to 2026"),
        ("2026 appraisal", "\\$28,000 (land \\$15,400,\nbuilding \\$12,600)"),
        ("Note", "\\$160,000 bought several parcels\ntogether; it is not this lot's price.\nConfirm with a title search."),
    ])
    y = block(c1, y - 0.22, "The parcel", [
        ("Frontage", "50.0 ft on Baird St (tax map)"),
        ("Depth", "34.0 ft east side, 48.0 ft west side"),
        ("Area", f"0.0471 ac deeded = {LOT_AREA_DEED:,.0f} sf\n(dimensions compute to ±{LOT_AREA_CALC:,.0f} sf)"),
        ("Legal", "Block I, part of Lot 2"),
        ("Existing house", "1929, 2-storey stucco, 768 sf,\n24' x 16', no basement"),
        ("Slope", "Up ±8 to 12 ft from street to rear;\nstreet itself climbs ±11 %"),
        ("Flood", "Low risk, no mapped flood zone"),
    ])
    y2 = block(c2, ytop, "Zoning: R-2 single and two-family", [
        ("Minimum lot", "5,000 sf and 40 ft frontage.\nThis lot: ±2,050 sf, so it is a legal\nnonconforming lot (1373.04)"),
        ("Setbacks", "Front 10 ft min / 20 ft max,\nside 5 ft, rear 20 ft"),
        ("Coverage", "50 % maximum"),
        ("Height", "2.5 storeys or 35 ft"),
        ("Parking", "2 spaces per single-family dwelling"),
        ("Overlay", "None mapped at this parcel"),
    ])
    y2 = block(c2, y2 - 0.22, "What is possible", [
        f"1.  By right, almost nothing. The setbacks leave a wedge\n     of ±{m['env_area']:,.0f} sf, 4.6 to 16 ft deep.",
        "2.  With a rear-setback variance, a 36' x 22' house fits:\n     792 sf per floor, 39 % coverage, 5 ft side yards.",
        "3.  The slope suits a drive-under garage. Cutting in at\n     street level puts the main floor at rear-yard grade.",
        "4.  Tearing the house down ends its grandfathered\n     setbacks (1373.06). Get the variance first.",
        "5.  Every car must be inside the building. There is no\n     room for surface parking and none on the street.",
    ], fs=6.9)
    y3 = block(c3, ytop, "The concept in this set", [
        ("Lower level", "2-car garage (427 sf) + storage room\n(177 sf) with a truck-height loading door"),
        ("Main level", "Living, dining, kitchen, powder,\nlaundry; walk-out to rear patio"),
        ("Upper level", "2 bedrooms + study, 2 baths"),
        ("Living area", "1,584 sf gross on two floors"),
        ("Height", f"{EL_MEAN_ROOF - EL_REF:.1f} ft to mean roof level"),
        ("Cars", "2 as drawn · 1 to 3 by option (A-401)"),
    ], kw=1.0)
    y3 = block(c3, y3 - 0.22, "Relief likely needed", [
        f"·  Rear setback: {m['r_ne']:.1f} to {m['r_nw']:.1f} ft proposed, 20 ft required",
        "·  Front setback: 8 ft proposed, 10 ft required unless the\n    developed-block averaging rule applies (1363.02(C))",
        "·  Storey count: ruling that the garage level is a basement",
        "·  Use: written confirmation that indoor storage of\n    materials for other properties is an accessory use",
    ], fs=6.9)
    y3 = block(c3, y3 - 0.22, "Before you buy", [
        "·  Boundary and topographic survey (GIS is ±3 to 5 ft)",
        "·  Title search of Deed Book 1246 / 78 and easements",
        "·  Pre-application meeting, Morgantown Planning Division,\n    389 Spruce St, 304-284-7431",
        "·  Geotechnical borings; retaining-wall and shoring budget",
        "·  City Engineer: driveway on an ±11 % one-lane street",
        "·  Make the offer contingent on Board of Zoning Appeals\n    approval",
    ], fs=6.9)
    # key plan
    kx = plan_axes(fig, c2 + 0.35, MARGIN + 0.42, (-22, 74), (-25, 52), 30)
    rect(kx, -22, PAVE_S, 74, PAVE_N, fc="#e3e5e8", ec="none", z=1)
    txt(kx, 26, -14, "BAIRD STREET", size=5.6, color=GREY, weight="bold")
    poly(kx, LOT, fc="none", ec=ACCENT, lw=1.2, z=4, ls=(0, (9, 2.5, 1.5, 2.5)))
    rect(kx, BX0, BY0, BX1, BY1, fc="#d9dcdf", ec=INK, lw=1.2, z=5)
    poly(kx, [(12.5, BY0), (28.5, BY0), (30.2, PAVE_N), (10.3, PAVE_N)], fc="#cfd6de", ec=INK, lw=0.4, z=3)
    txt(kx, 27, 19, "PROPOSED\n36' x 22'", size=5.4, weight="bold", z=9)
    txt(kx, -11, 22, "442\nBAIRD", size=5.0, color=GREY)
    txt(kx, 62, 18, "441\nBAIRD", size=5.0, color=GREY)
    txt(kx, 30, 46, "386 FOREST AVE", size=5.0, color=GREY)
    txt(kx, 25, -2.6, "50'", size=5.0, color=ACCENT)
    txt(kx, 52.6, 17, "34'", size=5.0, color=ACCENT, rot=90)
    txt(kx, -0.6, 26, "48'", size=5.0, color=ACCENT, rot=83)
    north_arrow(kx, 66, 42, 4.2, 6)
    txt(kx, -21, 49.5, "KEY PLAN  ·  1\" = 30'", size=6.2, weight="bold", ha="left")
    save(fig, "G-001", pdf)
