# Reusable prompt: rigid heddle loom

Copy everything below the line into a new session with an AI assistant (preferably Claude Code in
a clone of this repository) and put your change request at the bottom under **My change**.

## Models and tools used

| What | Specification |
|---|---|
| AI model | Claude Opus 5.5 (model ID `claude-opus-5-5`, Anthropic), knowledge cutoff June 2026 |
| Environment | Claude Code in the Claude desktop app (Code tab), Linux, Python 3 |
| Period | October–November 2026 |
| Laser cutter | bed 600 × 400 mm; red (#ff0000) = cut, blue (#0000ff) = engrave |
| 3D printer | FDM, PETG or PLA, 0.2 mm layers, 4 walls, 40 % infill; STLs need no supports |
| Local software | Python 3 (standard library only, **no** numpy/matplotlib), Inkscape (CLI), ImageMagick (`convert`), pdftotext/pdftoppm; **no OpenSCAD** |
| Storage | this git repository (`rigid-heddle-loom`) |

---

## Prompt

You are helping me with the design of a home-built **rigid heddle loom** (table/lap model). All
files are in this repository (`rigid-heddle-loom`). The design is fully parametric in Python; the
`README.md` in that folder is the build manual (English), `README_dutch.md` is the same manual in
Dutch. Read `README.md`, `generate_laser.py` and `print/generate_stl.py` before you change
anything.

### Way of working and preferences

- **Everything is in English**: code, identifiers, comments, file names, engraved labels, image
  labels, `README.md` and this prompt. The only exception is `README_dutch.md`, which must stay a
  complete Dutch translation of `README.md` (with the same English file and parameter names).
  Answer in the language I write in.
- Change **only what I ask for**. Much of the loom has already been built: side panels, clamp
  beams, rollers, ratchet wheels, knobs, shuttles and aprons exist. Don't change dimensions of
  built parts unless I ask, and keep holes that have already been drilled where they are (e.g.
  `BLOCK_HOLES` = (240, 55), (330, 55), (285, 95) in side-panel coordinates).
- After every change: make all outputs again (SVGs, STLs, images), check the images (actually look
  at them), and update both READMEs (file table, shopping list, cost estimate, construction, build
  steps, tips, design decisions) and, if needed, this prompt.
- Be honest about what has not been tested. Propose design choices with a recommendation.
- Code: same style as the existing scripts. No external Python packages.

### Starting points

- Weaving width 40 cm; inside width between the side panels `INNER_W` = 440 mm.
- Material: birch plywood 6 mm (`T` = 6.0, `KERF` = 0.15, measured), acrylic 3 mm
  (`T_ACRYLIC` = 3.0, `KERF_ACRYLIC` = 0.30, measured). All parts fit on 600 × 400 mm.
- Only **M3** and **M5** bolt sizes.
- Rounded outer corners (`rounded(pts, convex, concave)`); inside corners that must fit stay sharp.
- Use: on the lap, with the back resting on a table (slanted table notch, 15°); or clamped to the
  table with F-clamps (back clamp beam for lap use, front clamp beam to put it flat on the table
  while warping).

### Construction (current state)

Side-panel coordinates: x from front (0) to back (580), y up from the bottom edge.

- **Side panels**: 2 layers of 6 mm glued, length `SIDE_L` = 580. Inner layer with cut-outs for
  the clamp beams and (6 mm deep) for breast and back beam. Aligned with M3 bolts while gluing
  (`ALIGN_HOLES`). Low between breast beam and warp roller (`PANEL_TOP` = 110) so you can beat
  freely. Table notch at `TABLE_X` = 430, depth 20, angle 15°.
- **Warp** at height `WARP_H` = 155.
- **Breast and back beam**: beech dowel Ø 22 (measured **21.7** mm, `DOWEL_D` = 21.7), 452 mm,
  centres (30, 144.15) and (550, 144.15); 5 × 50 wood screw into the end grain.
- **Cloth and warp roller**: the same dowel, 540 mm, through Ø 22.7 holes at (75, 55) and
  (505, 55). Ratchet wheel + knob on the right, collar on the left. Shaft end filed double-D
  (18.5 mm between the flats, 60 mm long) with a printed filing jig; 3.5 × 25 locking screw in
  each hub.
- **Ratchet wheels**: front and back are mirror images (the teeth of the front one point the
  other way). Pawls with an M5 pivot at (115, 97) and (465, 97).
- **Clamp beams**: 30 × 30 mm boxes of 4 laser-cut finger-jointed slats (2 × A, 2 × B), with an M5
  threaded rod (2 × 480 mm) through box and side panels, penny washer + dome nut. Back beam
  slanted along the table notch, front beam at `FRONT_CLAMP_X` = 130 with its bottom flush with
  the panel.
- **Aprons**: laser-cut apron bars, attached with **Texsolv cord** (7 cords per roller).
- **Heddle blocks** (2 layers of 6 mm, on the outside of each side panel, 3 × M5 × 35), from x 230
  to 415, suitable for **two heddles**. Front to back: down 1 (entry + lip that holds the heddle
  down, slide the ear back), neutral 1, up (one wide notch for one or both heddles), down 2 (with
  lip), neutral 2. Heddle 1 is always in front of heddle 2. Stroke `HEDDLE_STROKE` = 28 mm up/down
  from neutral. On sheet 5 the blocks are rotated a quarter turn.
- **Heddle**: 500 × 150 mm (`HEDDLE_L`, `HEDDLE_H`), body 438 wide between the side panels, with
  an ear (`EAR_H` = 16) at the top on each side that rests in the heddle blocks. Build-up (15 mm
  thick): front heddle frame (6 mm plywood, window 402.5 × 91) + middle layer (3 mm acrylic,
  opening 400.5 × 100.5 = the groove) + back heddle frame (6 mm), bolted with 20 × M3 × 20.
  The reed consists of **20 Lojan heddle segments 30/10** (€ 0.90 each incl. VAT; Lojan sells them
  separately in 10/10 to 60/10). One segment: 20 mm wide, 100 mm high; top and bottom rail
  5 mm high × 3 mm thick; reed 90 mm high × 5 mm thick. The rails are clamped between the frames in
  the opening of the middle layer; the reed passes through the windows. There is a test piece for
  3 segments. (Earlier the reed was laser-cut acrylic; that warped during cutting and was dropped.)
- **Printed**: 2 ratchet wheels (front/back), 2 pawls, 2 knobs, 2 collars, 1 filing jig.
- **Other**: 2 shuttles (38 cm), pick-up stick.
- **Material cost**: about € 90–140 (without F-clamps); a second heddle about € 32–47 extra.

### Files

| File | Role |
|---|---|
| `generate_laser.py` | all parameters + SVGs in `laser/` (sheets 1–6 and test piece) |
| `print/generate_stl.py` | STLs in `print/` (own mesher, checks watertightness) |
| `print/loom_print.scad` | the same printed parts for OpenSCAD (untested) |
| `render_3d.py` | own z-buffer renderer: `loom_3d.png`, and with argument `left`, `side`, `bottom`, `warping` |
| `render_heddle.py` | exploded heddle with labels → `heddle_exploded.png` |
| `draw_heddle_block.py` | heddle block with all positions → `heddle_block_positions.png` |
| `draw_aprons.py` | apron attachment with Texsolv → `aprons_texsolv.png` |
| `README.md`, `README_dutch.md` | build manual in English and Dutch, shopping list, cost estimate, design decisions |

Make everything again:

```bash
python3 generate_laser.py && (cd print && python3 generate_stl.py) && for v in "" left side bottom warping; do python3 render_3d.py $v; done && python3 render_heddle.py && python3 draw_heddle_block.py && python3 draw_aprons.py
```

### Open points

- Test the fit of the Lojan segments with the test piece (`SEG_CLEARANCE`).
- Measure the length of the slots in the segments: with a 28 mm stroke they must be about 60 mm or
  longer, otherwise reduce `HEDDLE_STROKE` (and so the heddle blocks).

### My change

<!-- describe what you want to change here -->
