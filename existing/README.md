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
- `drawings/390-Forest_A-101_Lower-flat_Rev6.pdf`, `drawings/390-Forest_A-102_Middle-flat_Rev7.pdf`,
  `drawings/390-Forest_A-103_Upper-flat_Rev5.pdf`, `drawings/390-Forest_A-104_Attic_Rev6.pdf`: the four floor plans as they stand in the
  floor-by-floor review (newer than the A-101 to A-104 inside the builder set; the trade sheets are redrawn once the four floor plans are
  agreed). Every floor-plan sheet is checked when it is built (`clarity()` in `src/build390.py`): no label may sit on
  another label, a fixture, furniture, a door swing, a wall, the dashed outline of a removed wall or a dimension line, and nothing may run
  outside the border. The count is printed; all four sheets are at zero.
  Middle flat as found (owner's video): the furnace and water heater are in the louvered closet at the south end of the hall and the panel
  is on the hall wall; the small room beside bedroom 1's door is that bedroom's closet. Its bedroom side is drawn from wall faces measured in
  the 3D scan (`src/scan_survey.py`), because the phone-scan floor plan had that side about 1'-6" too narrow (it assumes 4 in. walls; several
  are 7 to 12 in. thick). Inside width is 26'-10" on both sides of the flat and the outside walls are straight, as the aerial photo shows.
  Lower flat checked the same way: its phone-scan plan agrees with the 3D scan to about 4 in. in every room checked, so A-101 was left as
  drawn.
  Upper flat main floor: the whole floor is drawn from the 3D scan (rev 3). Rev 4 (owner's request): the centre wall between the kitchen and
  the living room comes out for an open plan (new beam and posts, to be engineered), the panel moves to the living room wall, and the coat
  closet joins bedroom 3's closet. Found: hall 3'-4" wide, bath 5'-7" x 9'-4", Room B (bedroom 4)
  7'-1" x 13'-4", a thick wall between the bath and the stairs, a closed box in the kitchen corner that sits over the boxed-out section in
  the middle flat's bedroom 1 (most likely a drain stack or old flue), and the real stairs: the stair from the entrance arrives heading
  south, and the attic stair is 5 risers, a landing 3'-7" up, then 8 risers passing back over the stair down.
  Attic (rev 4): drawn from the 3D scan read ABOVE furniture height (5 ft and up). Below that the scan mesh smooths over whatever stood in
  front of a wall; rev 3 had drawn one such surface as an angled wall and had read furniture as a foot of extra wall thickness. Neither
  exists: every corner is square and the wall between the bedrooms is an ordinary 7 in. wall. The roof is a gable of about 11 in 12; the
  ceiling is flat at 7'-9" and slopes over the last 2 ft on the east side and 1'-6" on the west. The two private baths are mirror images,
  back to back on the wall between the bedrooms, each with a new knee wall where the ceiling is 6'-9"; the old chimney shaft
  between the two alcoves stays as the chase. Rev 5 (owner's review): vanity and mirror on the wall facing the door, under the full-height
  ceiling; toilet in the alcove under the slope, out of the sight line. Rev 6: the new knee wall moved 4 in. toward the eave (ceiling
  6'-5" at its face) so the toilet front stops 1 in. short of the vanity end; round-front toilet, 12 in. rough-in. A cross-section through the bath (the view as you walk in) is on
  the sheet. No dormer is added.
  The chimney shaft is at the same coordinates on the middle flat, the upper flat and the attic (frames agree to about 1 in.): `CHIMNEY`
  and `STACK` in `src/build390.py` hold that position, and the upper flat's chase (rev 5) was moved onto it.
  Lesson for `scan_survey.py`: take wall faces from slices at 5 ft and higher; lower slices pick up furniture and mesh fill.
- `drawings/390-Forest_Electrical_Rev1.pdf`: the electrical set for the agreed floor plans (`src/b390_e.py`, `src/b390_eq.py`): E-001 notes and
  legend, E-002 load calculations (NEC 220 standard and 220.82 optional per flat, 220.84 for the building; every value with its arithmetic),
  E-003 lighting calculations (lumen method, every room; the fixtures counted are the ones drawn), E-004 service entrance elevation, riser,
  feeder route, grounding and a check of the old service cable, E-005 panel schedules, E-101 to E-104 power and lighting plans.
  Design basis: electric ranges and dryers, gas furnaces and water heaters, central air (1.5 / 2 / 3 ton). Result: a 125 A panel and feeder
  per flat; building service 200 A calculated, so the old cable (typically 4/0 Al, 180 A) is replaced; 3-position meter stack with 125 A
  meter-mains at the existing place (east wall, north end). Receptacles are placed by the NEC spacing rules from the plan model; kitchen
  counter receptacles alternate over 3 or 4 circuits. The plumbing sheets in the builder set predate the floor-plan review.
- `drawings/390-Forest_Mechanical_Rev2.pdf`: the HVAC set for the agreed floor plans. `src/b390_mq.py` loads (Manual J method written out room
  by room: U x A x dT per surface, glass solar gain, people, lights, infiltration and the ASHRAE 62.2 ventilation rate), equipment (Manual S) and
  room airflows, checked again at the owner's reported -15 F and 105 F. `src/b390_mr.py` finds the walls around every room from the wall geometry and
  puts each supply register HIGH ON AN INSIDE WALL (top 6 in. below the ceiling, throwing across the room toward the outside wall), each return
  filter grille in a wall with a box behind it, transfer grilles beside or over bedroom doors, and wall caps 3 ft from windows, doors and property
  lines; then routes every branch, return, exhaust duct and vent on a 3 in. grid through its joist space, square to the walls, without crossing the
  trunk, another duct, the chase, a stair opening, another flat or a panel's space. `src/b390_m.py` draws M-001 notes, equipment and per-fan exhaust
  schedules, M-002 loads (with the extremes check), M-003 the register-by-register schedule, condenser airflow under the rear deck and the chase,
  M-501 construction details and 3D views of each flat's ducts, M-101 to M-104 plans with every duct drawn to scale and sized.
  Result: variable-speed air conditioners, 1.5 ton lower and middle, 2 ton upper; 40,000 Btu/h two-stage furnaces; 14 x 8 in. trunks; the attic
  is fed from the upper flat's main-floor trunk in the attic floor; middle flat dryer is a ventless heat-pump type (no wall within 35 ft
  equivalent, even west). Line sets are NOT final: they wait for the size of the walled area under the rear deck.
- `data/evidence/`: pictures used on PR-105 (aerial photo supplied by the owner, views from the scan).
- `data/*_polycam_plan.json`: rooms, walls, doors and windows read from the Polycam floor-plan DXF.
- `data/390_registration.json`, `data/390_fixed.json`: how each level of 390 Forest lines up with the
  3D scan, and the ceiling heights and attic headroom measured from it.
- `src/`: `extract_plans.py` (DXF to JSON), `register.py` and `analyze_390.py` (need the 3D scan
  `.laz`, which is too large to keep in the repository), `draw_existing.py` (draws the scan-fix sheets from `data/`), `draw_proposed.py` (draws the proposed layouts).
