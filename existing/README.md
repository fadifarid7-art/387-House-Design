# Existing houses: scan clean-up (390 Forest Ave and 441 Baird St)

Before / after sheets for the two existing buildings on county parcel 31-13-0029-0083, made from
Polycam phone scans dated 5 Oct 2026. Nothing new is designed here yet.

- `drawings/390-Forest_441-Baird_Scan-Fixes.pdf`: 11 sheets. EX-001 is the fix log; red tags (F) are
  fixes made, amber tags (U) are items that still need a look on site.
- `drawings/390-Forest_8-Bed-7-Bath_Proposed.pdf`: 6 sheets (PR-001, PR-101 to PR-105). Each level of 390 Forest as
  checked against the 3D scan (walls, stairs, chimney, doors, windows) beside the proposed layout: 8 bedrooms and 7 baths: the lower and
  middle flats gain a second bath; the upper flat gains a fourth bedroom and a private bath for each attic bedroom. Layout only; structure and
  plumbing design come later.
- `data/evidence/`: pictures used on PR-105 (aerial photo supplied by the owner, views from the scan).
- `data/*_polycam_plan.json`: rooms, walls, doors and windows read from the Polycam floor-plan DXF.
- `data/390_registration.json`, `data/390_fixed.json`: how each level of 390 Forest lines up with the
  3D scan, and the ceiling heights and attic headroom measured from it.
- `src/`: `extract_plans.py` (DXF to JSON), `register.py` and `analyze_390.py` (need the 3D scan
  `.laz`, which is too large to keep in the repository), `draw_existing.py` (draws the scan-fix sheets from `data/`), `draw_proposed.py` (draws the proposed layouts).
