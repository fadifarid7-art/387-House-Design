# Existing houses: scan clean-up (390 Forest Ave and 441 Baird St)

Before / after sheets for the two existing buildings on county parcel 31-13-0029-0083, made from
Polycam phone scans dated 5 Oct 2026. Nothing new is designed here yet.

- `drawings/390-Forest_441-Baird_Scan-Fixes.pdf`: 11 sheets. EX-001 is the fix log; red tags (F) are
  fixes made, amber tags (U) are items that still need a look on site.
- `data/*_polycam_plan.json`: rooms, walls, doors and windows read from the Polycam floor-plan DXF.
- `data/390_registration.json`, `data/390_fixed.json`: how each level of 390 Forest lines up with the
  3D scan, and the ceiling heights and attic headroom measured from it.
- `src/`: `extract_plans.py` (DXF to JSON), `register.py` and `analyze_390.py` (need the 3D scan
  `.laz`, which is too large to keep in the repository), `draw_existing.py` (draws the sheets from `data/`).
