# Existing houses: scan clean-up (390 Forest Ave and 441 Baird St)

Before / after sheets for the two existing buildings on county parcel 31-13-0029-0083, made from
Polycam phone scans dated 5 Oct 2026. Nothing new is designed here yet.

- `drawings/390-Forest_441-Baird_Scan-Fixes.pdf`: 11 sheets. EX-001 is the fix log; red tags (F) are
  fixes made, amber tags (U) are items that still need a look on site.
- `drawings/390-Forest_8-Bed-7-Bath_Proposed.pdf`: 6 sheets (PR-001, PR-101 to PR-105). Each level of 390 Forest as
  checked against the 3D scan (walls, stairs, chimney, doors, windows) beside the proposed layout: 8 bedrooms and 7 baths (issue 3: tubs in every bath, king beds, closets, mechanical rooms drawn): the lower and
  middle flats gain a second bath; the upper flat gains a fourth bedroom and a private bath for each attic bedroom. Layout only; structure and
  plumbing design come later.
- `drawings/390-Forest_Builder-Set.pdf`: 21 sheets at 1/4 in. = 1 ft for a full gut of 390 Forest (8 bedrooms, 7 baths): cover and
  scope (G-001), floor plans (A-101 to A-104), schedules (A-601), electrical (E), HVAC (M), plumbing and gas (P). Built by
  `src/make_build390.py` from the plan model in `src/build390.py` and the trade modules `src/b390_*.py`. It supersedes the
  earlier before/after and proposed sets.
- `drawings/390-Forest_A-101_Lower-flat_Rev5.pdf`, `drawings/390-Forest_A-102_Middle-flat_Rev4.pdf`: the lower and middle flat floor plans
  as they stand in the floor-by-floor review (newer than the A-101 and A-102 inside the builder set; the upper flat and attic follow, and the
  trade sheets are redrawn once the four floor plans are agreed). Every floor-plan sheet is checked when it is built (`clarity()` in
  `src/build390.py`): no label may sit on another label, a fixture, furniture, a door swing, a wall or a dimension line, and nothing may run
  outside the border. The count is printed; A-101 and A-102 are at zero.
  Middle flat as found (owner's video): the furnace and water heater are in the louvered closet at the south end of the hall and the panel
  is on the hall wall; the small room beside bedroom 1's door is that bedroom's closet. Rev 3 was planned around that. Rev 4 is checked
  against the 3D scan as well: angled bay at the front (both corners), straight walls where the Polycam plan drew two diagonals, bedroom 1's
  stepped north wall, and the real stair to the upper flat (7 risers, landing, 9 risers) with its outside door.
- `data/evidence/`: pictures used on PR-105 (aerial photo supplied by the owner, views from the scan).
- `data/*_polycam_plan.json`: rooms, walls, doors and windows read from the Polycam floor-plan DXF.
- `data/390_registration.json`, `data/390_fixed.json`: how each level of 390 Forest lines up with the
  3D scan, and the ceiling heights and attic headroom measured from it.
- `src/`: `extract_plans.py` (DXF to JSON), `register.py` and `analyze_390.py` (need the 3D scan
  `.laz`, which is too large to keep in the repository), `draw_existing.py` (draws the scan-fix sheets from `data/`), `draw_proposed.py` (draws the proposed layouts).
