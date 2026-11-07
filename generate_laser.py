#!/usr/bin/env python3
"""Generates the laser-cutting SVGs for a rigid heddle loom (40 cm weaving width).

All dimensions in mm. Adjust the parameters below and run again:
    python3 generate_laser.py
Red (#ff0000) = cut, blue (#0000ff) = engrave (labels, optional).
"""
import math
import os

# ---------------------------------------------------------------- parameters
T = 6.0             # measured plywood thickness (measure your sheet!)
T_ACRYLIC = 3.0     # thickness of the heddle middle layer (3 mm acrylic); = width of the groove
KERF = 0.15         # laser beam width in 6 mm plywood; holes and slots are compensated for it
KERF_ACRYLIC = 0.30 # laser beam width in 3 mm acrylic (measured on a test strip)
DENTS_PER_10CM = 30
# Lojan heddle segments: top rail + reed + bottom rail; the rails sit in a groove of the heddle
SEG_W = 20.0        # width of one segment
SEG_N = 20          # number of segments side by side
SEG_H = 100.0       # total height of a segment
SEG_RAIL_H = 5.0    # height of top and bottom rail (= depth in the groove)
SEG_RAIL_T = 3.0    # thickness of top and bottom rail
SEG_REED_T = 5.0    # thickness of the reed between the rails
SEG_CLEARANCE = 0.5 # extra room in length and height for the row of segments
WEAVING_WIDTH = SEG_N * SEG_W
DOWEL_D = 21.7      # diameter of the dowel for the rollers (nominal 22 mm)
ROLLER_HOLE = DOWEL_D + 1.0
BEAM = 30.0         # outer size of the clamp beams: box of 4 finger-jointed slats
BEAM_CLEARANCE = 0.2
BOX_FINGERS = 15    # number of finger sections along a slat (odd)
ROD_HOLE = 5.5      # M5 threaded rod through the clamp beams
BEAM_DOWEL_HOLE = DOWEL_D + 0.5   # breast and back beam: dowel, 6 mm deep in the inner layer
SCREW_HOLE = 4.5    # wood screw 5 x 50 into the end grain of breast and back beam (pre-drill 3 mm)
M5_HOLE = 5.5       # M5 bolts: pawl pivot and heddle blocks
ALIGN_HOLE = 3.3    # M3 bolts to align the layers while gluing
M3_HOLE = 3.3

BED_W, BED_H = 600.0, 400.0
MARGIN = 10.0

# derived dimensions
SIDE_L = 580.0                 # length of a side panel
INNER_W = WEAVING_WIDTH + 40   # inside width between the side panels
SIDE_T = 2 * T                 # side panel = 2 layers
BEAM_L = INNER_W + 2 * T       # clamp beams and breast/back beam sit one layer (T) deep in the inner panel
BLOCK_T = 2 * T                # heddle block = 2 layers, on the outside of the side panel
HEDDLE_W = INNER_W - 2         # width of the heddle body: fits between the side panels
EAR_H = 16.0                   # height of the ears at the top of the heddle
HEDDLE_L = 2 * (INNER_W / 2 + SIDE_T + BLOCK_T + 6)   # incl. ears, 6 mm beyond the heddle blocks
HEDDLE_H = 150.0
# middle layer: opening the segments fit in exactly; the heddle frames in front and behind have a
# smaller window and so hold the rails (the groove = middle layer between two frames)
GROOVE_L = WEAVING_WIDTH + SEG_CLEARANCE
GROOVE_H = SEG_H + SEG_CLEARANCE
WINDOW_L = GROOVE_L + 2.0          # generous, so the segment ends only touch the middle layer
WINDOW_H = SEG_H - 2 * SEG_RAIL_H + 1.0
WARP_H = 155.0                 # height of the warp (top of breast and back beam)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "laser")


# ---------------------------------------------------------------- rounding
def rounded(pts, convex=0.0, concave=0.0):
    """Rounds the corners of a closed contour.

    Each point is (x, y) or (x, y, r). Without r a convex (outward) corner gets radius `convex` and
    a concave (inward) corner radius `concave`. The radius is reduced when the adjacent edges are
    too short. Arcs are returned as short line segments.
    """
    p = [(q[0], q[1]) for q in pts]
    n = len(p)
    area = sum(p[i][0] * p[(i + 1) % n][1] - p[(i + 1) % n][0] * p[i][1] for i in range(n))
    out = []
    for i, q in enumerate(pts):
        a, c, b = p[i - 1], p[i], p[(i + 1) % n]
        ux, uy = a[0] - c[0], a[1] - c[1]
        vx, vy = b[0] - c[0], b[1] - c[1]
        lu, lv = math.hypot(ux, uy), math.hypot(vx, vy)
        if lu < 1e-9 or lv < 1e-9:
            continue
        ux, uy, vx, vy = ux / lu, uy / lu, vx / lv, vy / lv
        cross = (c[0] - a[0]) * (b[1] - c[1]) - (c[1] - a[1]) * (b[0] - c[0])
        r = q[2] if len(q) > 2 else (convex if cross * area > 0 else concave)
        angle = math.acos(max(-1.0, min(1.0, ux * vx + uy * vy)))
        if r <= 0 or angle > math.pi - 1e-3:
            out.append(c)
            continue
        t = min(r / math.tan(angle / 2), 0.45 * lu, 0.45 * lv)
        r = t * math.tan(angle / 2)
        bx, by = ux + vx, uy + vy
        lb = math.hypot(bx, by)
        mx, my = c[0] + bx / lb * r / math.sin(angle / 2), c[1] + by / lb * r / math.sin(angle / 2)
        t1, t2 = (c[0] + ux * t, c[1] + uy * t), (c[0] + vx * t, c[1] + vy * t)
        a1, a2 = math.atan2(t1[1] - my, t1[0] - mx), math.atan2(t2[1] - my, t2[0] - mx)
        d = (a2 - a1 + math.pi) % (2 * math.pi) - math.pi
        steps = max(2, int(abs(d) / math.radians(10)))
        out += [(mx + r * math.cos(a1 + d * k / steps), my + r * math.sin(a1 + d * k / steps))
                for k in range(steps + 1)]
    return out


# ---------------------------------------------------------------- svg helpers
class Svg:
    def __init__(self, name, w=BED_W, h=BED_H):
        self.name, self.w, self.h, self.items = name, w, h, []

    def path(self, d, colour="#ff0000"):
        self.items.append(f'<path d="{d}" fill="none" stroke="{colour}" stroke-width="0.1"/>')

    def text(self, x, y, s, size=6):
        self.items.append(
            f'<text x="{x:.2f}" y="{y:.2f}" font-family="sans-serif" font-size="{size}" '
            f'fill="none" stroke="#0000ff" stroke-width="0.1">{s}</text>')

    def save(self):
        os.makedirs(OUT, exist_ok=True)
        body = "\n".join(self.items)
        with open(os.path.join(OUT, self.name), "w") as f:
            f.write(f'<?xml version="1.0" encoding="UTF-8"?>\n'
                    f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}mm" height="{self.h}mm" '
                    f'viewBox="0 0 {self.w} {self.h}">\n{body}\n</svg>\n')


class Part:
    """Draws in a local coordinate system (y up) with an offset onto the sheet."""

    def __init__(self, svg, ox, oy, h, mirror=None, kerf=KERF, rotate=False):
        # oy is the top on the sheet, h the height of the part
        # mirror: width of the part, to draw it mirrored left to right
        # kerf: laser beam width in the material of this part
        # rotate: quarter turn; local x then runs down and y to the right (ox, oy = local 0, 0)
        self.svg, self.ox, self.oy, self.h, self.mirror, self.kerf = svg, ox, oy, h, mirror, kerf
        self.rotate = rotate

    def xy(self, x, y):
        if self.mirror:
            x = self.mirror - x
        if self.rotate:
            return self.ox + y, self.oy + x
        return self.ox + x, self.oy + self.h - y

    def p(self, x, y):
        return "%.3f,%.3f" % self.xy(x, y)

    def poly(self, pts):
        self.svg.path("M" + " L".join(self.p(x, y) for x, y in pts) + " Z")

    def rect(self, x0, y0, x1, y1, hole=True):
        k = self.kerf / 2 if hole else -self.kerf / 2
        self.poly([(x0 + k, y0 + k), (x1 - k, y0 + k), (x1 - k, y1 - k), (x0 + k, y1 - k)])

    def circle(self, cx, cy, d):
        r = d / 2 - self.kerf / 2
        a, b = self.p(cx - r, cy), self.p(cx + r, cy)
        self.svg.path(f"M{a} A{r:.3f},{r:.3f} 0 1 0 {b} A{r:.3f},{r:.3f} 0 1 0 {a} Z")

    def label(self, x, y, s, size=6):
        lx, ly = self.xy(x, y)
        self.svg.text(lx - (len(s) * size * 0.5 if self.mirror else 0), ly, s, size)


# ---------------------------------------------------------------- side panel
# Coordinates: x = 0 front (weaver), x = 580 back; y = 0 bottom.
BREAST_BEAM = (30.0, WARP_H - DOWEL_D / 2)    # centre; top of the dowel at warp height
BACK_BEAM = (SIDE_L - 30.0, WARP_H - DOWEL_D / 2)
CLOTH_ROLLER = (75.0, 55.0)
WARP_ROLLER = (505.0, 55.0)
PAWL_FRONT = (115.0, 97.0)
PAWL_BACK = (465.0, 97.0)
ALIGN_HOLES = [(185.0, 40.0), (300.0, 30.0), (540.0, 100.0)]

# Table notch in the bottom edge: the front rests on your lap, the table edge drops into the notch.
# The slanted face then lies flat on the table top, the short wall hooks behind the table edge.
TABLE_X = 430.0       # inside corner of the notch (where the table edge goes)
TABLE_DEPTH = 20.0    # depth of the notch
TABLE_ANGLE = 15.0    # tilt of the loom in degrees (lap lower than the table)

# Back clamp beam: sits just behind the table edge with its bottom flush with the slanted face, so
# flat on the table top. Clamp it to the table with an F-clamp on each side.
CLAMP_OFFSET = (BEAM_CLEARANCE + KERF) / 2   # front of the cut-out coincides with the table edge

# Front clamp beam: for warping with the loom flat on the table. Bottom flush with the bottom edge
# of the side panels; an F-clamp over this beam holds the loom to the table. It sits behind the
# cloth roller, so the clamp bar in front of the table edge clears the roller.
FRONT_CLAMP_X = 130.0   # front of the front clamp beam (= position of the table edge when warping)


def clamp_beam_corners(clearance=0.0):
    """Corner points (front-bottom, front-top, back-top, back-bottom) in panel coordinates."""
    a = math.radians(TABLE_ANGLE)
    tx, ty = math.cos(a), -math.sin(a)     # along the table top, towards the back
    nx, ny = math.sin(a), math.cos(a)      # perpendicular to the table top, up
    s0, s1, h = CLAMP_OFFSET - clearance / 2, CLAMP_OFFSET + BEAM + clearance / 2, BEAM + clearance / 2

    def p(s, v):
        return (TABLE_X + s * tx + v * nx, TABLE_DEPTH + s * ty + v * ny)

    return [p(s0, 0), p(s0, h), p(s1, h), p(s1, 0)]

# Heddle blocks: separate blocks on the outside of the side panels. The ears at the top of the
# heddle rest in them. Two heddles fit (heddle 1 front, heddle 2 back); with one heddle use heddle 1.
# The block is symmetric. Front to back: down 1, neutral 1, up 1, up 2, neutral 2, down 2.
# Down: the threads in the holes pull the heddle up; so after setting the ear down in the entry you
# slide it outwards (heddle 1 forward, heddle 2 back) under the lip at the end of the block.
# Up: the warp pushes the heddle down into the notch. Heddle 1 is always in front of heddle 2.
HEDDLE_T = 2 * T + T_ACRYLIC    # thickness of the heddle (and so of the ears)
NOTCH_W = HEDDLE_T + 1.0        # notch width = heddle thickness + 1 mm
UP_W = 2 * HEDDLE_T + 1.0       # up notch in the middle: up 1 and up 2 side by side
HEDDLE_STROKE = 28.0            # heddle moves 28 mm up / down from neutral
BLOCK_X = 230.0                 # front of the heddle block
BLOCK_Y = 40.0                  # bottom of the heddle block (overlaps the side panel to bolt it on)
PANEL_TOP = 110.0               # top of the side panel between breast beam and warp roller
POST_W = 10.0                   # width of the post at each end that carries the lip
WALL_W = 6.0                    # width of the walls between the notches
LIP_T = 10.0                    # thickness of the lip


def ear_bottom(stroke):
    """Height of the bottom of the ear when the centre of the heddle is at WARP_H + stroke."""
    return WARP_H + stroke + HEDDLE_H / 2 - EAR_H


EAR_DOWN, EAR_NEUTRAL, EAR_UP = ear_bottom(-HEDDLE_STROKE), ear_bottom(0), ear_bottom(HEDDLE_STROKE)
LIP_BOTTOM = EAR_DOWN + EAR_H + 1      # underside of the lip
LIP_TOP = LIP_BOTTOM + LIP_T           # top of the lip (and of the posts)
WALL_TOP = EAR_NEUTRAL + 10            # top of the wall between down entry and neutral
UP_TOP = EAR_UP + 10                   # top of the walls around the up notch

# front half; the back half is its mirror image
X_LIP_END = BLOCK_X + POST_W + NOTCH_W + 1   # end of the lip = start of the entry of down 1
X_DOWN1 = X_LIP_END                          # entry down 1
X_NEUTRAL1 = X_DOWN1 + NOTCH_W + WALL_W      # neutral 1 notch
X_UP = X_NEUTRAL1 + NOTCH_W + WALL_W         # up notch (both heddles)
BLOCK_X1 = X_UP + UP_W + (X_UP - BLOCK_X)    # back of the heddle block


def mirror_x(x):
    return BLOCK_X + BLOCK_X1 - x


X_DOWN2 = mirror_x(X_DOWN1 + NOTCH_W)        # entry down 2
X_NEUTRAL2 = mirror_x(X_NEUTRAL1 + NOTCH_W)  # neutral 2 notch
# centre (x) and bottom of the ear per position, for the renders
POSITIONS = {
    "down 1": (BLOCK_X + POST_W + (NOTCH_W + 1) / 2, EAR_DOWN),
    "neutral 1": (X_NEUTRAL1 + NOTCH_W / 2, EAR_NEUTRAL),
    "up 1": (X_UP + HEDDLE_T / 2, EAR_UP),
    "up 2": (X_UP + UP_W - HEDDLE_T / 2, EAR_UP),
    "neutral 2": (X_NEUTRAL2 + NOTCH_W / 2, EAR_NEUTRAL),
    "down 2": (mirror_x(BLOCK_X + POST_W + (NOTCH_W + 1) / 2), EAR_DOWN),
}
# fixed positions: these holes have already been drilled in the side panels
BLOCK_HOLES = [(240.0, 55.0), (330.0, 55.0), (285.0, 95.0)]


def heddle_block_outline():
    """Symmetric heddle block with rounded outer corners; the inside corners of the notches stay sharp."""
    front = [(BLOCK_X, LIP_TOP), (X_LIP_END, LIP_TOP), (X_LIP_END, LIP_BOTTOM),        # post + lip
             (BLOCK_X + POST_W, LIP_BOTTOM), (BLOCK_X + POST_W, EAR_DOWN),               # down 1
             (X_DOWN1 + NOTCH_W, EAR_DOWN), (X_DOWN1 + NOTCH_W, WALL_TOP),               # entry down 1
             (X_NEUTRAL1, WALL_TOP), (X_NEUTRAL1, EAR_NEUTRAL),
             (X_NEUTRAL1 + NOTCH_W, EAR_NEUTRAL), (X_NEUTRAL1 + NOTCH_W, UP_TOP),        # neutral 1
             (X_UP, UP_TOP), (X_UP, EAR_UP)]                                             # up
    back = [(mirror_x(x), y) for x, y in reversed(front)]
    top = front + back                       # from front to back
    return rounded([(BLOCK_X, BLOCK_Y), (BLOCK_X1, BLOCK_Y), *reversed(top)], convex=3)


def clamp_beam_centers():
    k = clamp_beam_corners()
    return [(sum(p[0] for p in k) / 4, sum(p[1] for p in k) / 4), (FRONT_CLAMP_X + BEAM / 2, BEAM / 2)]


def side_panel_outline(inner=False):
    t = math.tan(math.radians(TABLE_ANGLE))
    # the inner layer gets a cut-out for the clamp beam, open towards the table top
    clamp = clamp_beam_corners(BEAM_CLEARANCE + KERF) if inner else []
    cl = (BEAM_CLEARANCE + KERF) / 2
    front = ([(FRONT_CLAMP_X - cl, 0), (FRONT_CLAMP_X - cl, BEAM + cl),
              (FRONT_CLAMP_X + BEAM + cl, BEAM + cl), (FRONT_CLAMP_X + BEAM + cl, 0)] if inner else [])
    # (x, y, radius): generously rounded outer corners; cut-outs and table corner stay sharp
    pts = [(0, 0, 12), *front,
           (TABLE_X - TABLE_DEPTH * t, 0, 3),     # wall perpendicular to the slanted face
           (TABLE_X, TABLE_DEPTH, 0),
           *clamp,
           (TABLE_X + TABLE_DEPTH / t, 0, 10),    # slanted face = table top
           (SIDE_L, 0, 12), (SIDE_L, 170, 12), (470, 170, 25),
           # low between breast beam and warp roller: ears and shuttle pass freely over it
           (420, PANEL_TOP, 25), (85, PANEL_TOP, 25), (55, 170, 20), (0, 170, 12)]
    return rounded(pts)


def side_panel(svg, ox, oy, inner, name, mirrored=False):
    o = Part(svg, ox, oy, 170, SIDE_L if mirrored else None)
    o.poly(side_panel_outline(inner))
    for c in (CLOTH_ROLLER, WARP_ROLLER):
        o.circle(*c, ROLLER_HOLE)
    for c in (PAWL_FRONT, PAWL_BACK):
        o.circle(*c, M5_HOLE)
    for c in ALIGN_HOLES:
        o.circle(*c, ALIGN_HOLE)
    for c in BLOCK_HOLES:
        o.circle(*c, M5_HOLE)
    for c in (BREAST_BEAM, BACK_BEAM):
        o.circle(*c, BEAM_DOWEL_HOLE if inner else SCREW_HOLE)
    if not inner:                            # threaded rod through the middle of both boxes
        for c in clamp_beam_centers():
            o.circle(*c, ROD_HOLE)
    if inner:
        o.label(250, 20, name)
    else:
        o.label(240, 75, name, 3)          # hidden behind the heddle block


def heddle_block(svg, ox, oy, name):
    """Rotated a quarter turn on the sheet: (ox, oy) is top left, the front of the block is at the top."""
    o = Part(svg, ox - BLOCK_Y, oy - BLOCK_X, 0, rotate=True)
    o.poly(heddle_block_outline())
    for c in BLOCK_HOLES:
        o.circle(*c, M5_HOLE)
    for n in ("down 1", "neutral 1", "down 2", "neutral 2"):
        x, b = POSITIONS[n]
        o.label(x + 2, b - 30, n, 4)
    o.label(X_UP + UP_W / 2 + 2, EAR_UP - 30, "up", 4)
    o.label(BLOCK_X + 30, BLOCK_Y + 8, name, 4)


def sheet_heddle_blocks():
    s = Svg(f"sheet5_heddle_blocks_shuttles_{T:g}mm.svg")
    height = EAR_UP + 10 - BLOCK_Y        # on the sheet: the width of a block
    length = BLOCK_X1 - BLOCK_X           # on the sheet: the height of a block
    gap = 6.0
    for i in range(4):
        heddle_block(s, MARGIN + (i % 2) * (height + gap), MARGIN + (i // 2) * (length + gap),
                     f"heddle block {i + 1}/4")
    # shuttles upright to the right of the heddle blocks; therefore 380 mm long
    x = MARGIN + 2 * height + gap + 10
    for i in range(2):
        o = Part(s, x + i * 46, MARGIN, 0, rotate=True)
        shuttle_shape(o, name=f"shuttle {i + 1}", l=BED_H - 2 * MARGIN)
    assert 2 * length + gap <= BED_H - 2 * MARGIN, "sheet 5 does not fit (height)"
    assert x + 46 + 40 <= BED_W - MARGIN, "sheet 5 does not fit (width)"
    s.save()


def sheet_side_panels(inner):
    s = Svg(f"sheet{1 if inner else 2}_side_panels_{'inner' if inner else 'outer'}_{T:g}mm.svg")
    if inner:
        for i in range(2):
            side_panel(s, MARGIN, MARGIN + i * 185, True, f"side panel inner {i + 1}/2 - front = left")
    else:
        # the left outer panel is mirrored, so both panels have the same outside face
        side_panel(s, MARGIN, MARGIN, False, "outer RIGHT - front left")
        side_panel(s, MARGIN, MARGIN + 185, False, "outer LEFT - front right", mirrored=True)
    s.save()


# ---------------------------------------------------------------- heddle
# Heddle coordinates: x = 0 centre, y = 0 centre; shifted locally to (HEDDLE_L/2, HEDDLE_H/2).
def heddle_bolt_holes():
    holes = []
    post_x = (WINDOW_L / 2 + HEDDLE_W / 2) / 2
    rail_y = (GROOVE_H / 2 + HEDDLE_H / 2) / 2
    for sx in (-1, 1):
        for y in (-rail_y, 0, rail_y):
            holes.append((sx * post_x, y))
    for x in range(-180, 181, 60):
        for sy in (-1, 1):
            holes.append((x, sy * rail_y))
    return holes


def heddle_outline():
    """Heddle body between the side panels with an ear on both sides at the top."""
    a, b, h = (HEDDLE_L - HEDDLE_W) / 2, (HEDDLE_L + HEDDLE_W) / 2, HEDDLE_H - EAR_H
    return rounded([(a, 0), (b, 0), (b, h), (HEDDLE_L, h), (HEDDLE_L, HEDDLE_H), (0, HEDDLE_H), (0, h), (a, h)],
                   convex=4, concave=2)


def heddle_layer(svg, ox, oy, name, middle=False, count=SEG_N):
    """Heddle frame (6 mm, window) or middle layer (3 mm, opening = groove). count < SEG_N: test piece."""
    if count == SEG_N:
        width, height, holes = HEDDLE_L, HEDDLE_H, heddle_bolt_holes()
    else:
        width, height = count * SEG_W + 50, GROOVE_H + 40
        holes = [(sx * (count * SEG_W / 2 + 12), sy * (GROOVE_H / 2 + 10)) for sx in (-1, 1) for sy in (-1, 1)]
    o = Part(svg, ox, oy, height, kerf=KERF_ACRYLIC if middle else KERF)
    cx, cy = width / 2, height / 2
    o.poly(heddle_outline() if count == SEG_N else rounded(
        [(0, 0), (width, 0), (width, height), (0, height)], convex=4))
    extra = SEG_CLEARANCE + (2.0 if not middle else 0)    # window of the frames slightly larger
    w = count * SEG_W + extra
    h = GROOVE_H if middle else WINDOW_H
    o.rect(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
    for x, y in holes:
        o.circle(cx + x, cy + y, M3_HOLE)
    o.label(cx - 20, cy + h / 2 + 3, name, 4)
    return width, height


def sheet_heddle_frames():
    s = Svg(f"sheet3_heddle_frames_{T:g}mm.svg")
    heddle_layer(s, MARGIN, MARGIN, "heddle frame front")
    heddle_layer(s, MARGIN, MARGIN + HEDDLE_H + 10, "heddle frame back")
    s.save()


def sheet_heddle_middle():
    s = Svg(f"sheet6_heddle_middle_layer_{T_ACRYLIC:g}mm.svg")
    heddle_layer(s, MARGIN, MARGIN, "heddle middle layer", middle=True)
    s.save()
    # test piece for 3 segments: two frames (6 mm) and a middle layer (3 mm), each as a separate file
    for middle, name, t in ((False, "frame", T), (True, "middle_layer", T_ACRYLIC)):
        f = Svg(f"test_piece_heddle_{name}_{t:g}mm.svg", 3 * SEG_W + 70,
                GROOVE_H + 60 if middle else 2 * GROOVE_H + 110)
        label = f"test {name.replace('_', ' ')}"
        heddle_layer(f, 10, 10, label, middle, count=3)
        if not middle:
            heddle_layer(f, 10, GROOVE_H + 60, label, middle, count=3)
        f.save()


# ---------------------------------------------------------------- strips & accessories
def strip(svg, ox, oy, l, h, name, holes=()):
    o = Part(svg, ox, oy, h)
    o.poly(rounded([(0, 0), (l, 0), (l, h), (0, h)], convex=3))
    for x in holes:
        o.circle(x, h / 2, 4.0)
    o.label(l / 2 - 30, h / 2 - 2, name, 4)


def shuttle(svg, ox, oy, l=450.0, h=40.0, name="shuttle"):
    """Flat stick shuttle with V-shaped notches at both ends."""
    shuttle_shape(Part(svg, ox, oy, h), l, h, name)


def shuttle_shape(o, l=450.0, h=40.0, name="shuttle"):
    d, w = 30.0, 10.0   # depth and half width of the notch
    o.poly(rounded([(0, 0), (l, 0), (l, h / 2 - w), (l - d, h / 2 - 2), (l - d, h / 2 + 2), (l, h / 2 + w),
                    (l, h), (0, h), (0, h / 2 + w), (d, h / 2 + 2), (d, h / 2 - 2), (0, h / 2 - w)], convex=3))
    o.label(l / 2 - 15, h / 2 - 2, name, 4)


def pickup_stick(svg, ox, oy, l=470.0, h=30.0):
    o = Part(svg, ox, oy, h)
    o.poly(rounded([(0, h / 2), (40, 0), (l - 40, 0), (l, h / 2), (l - 40, h), (40, h)], convex=4))
    o.label(l / 2 - 20, h / 2 - 2, "pick-up stick", 4)


def box_slat(svg, ox, oy, phase, name):
    """Slat for a 30 x 30 mm box: fingers along both long edges.

    phase 0: fingers on the even sections (top and bottom of the box), phase 1: on the odd
    sections (sides). Two slats of each phase per box. Fingers are drawn KERF longer and the
    gaps KERF shorter, so they fit exactly after cutting.
    """
    o = Part(svg, ox, oy, BEAM)
    section = BEAM_L / BOX_FINGERS

    def finger(i):
        return i % 2 == phase

    def bounds():
        xs = [0.0]
        for j in range(1, BOX_FINGERS):
            xs.append(j * section + (KERF / 2 if finger(j - 1) else -KERF / 2))
        return xs + [BEAM_L]

    xs = bounds()
    bottom, top = [], []
    for i in range(BOX_FINGERS):
        d = 0.0 if finger(i) else T
        bottom += [(xs[i], d), (xs[i + 1], d)]
        top += [(xs[i], BEAM - d), (xs[i + 1], BEAM - d)]
    o.poly(bottom + top[::-1])
    o.label(BEAM_L / 2 - 30, BEAM / 2 - 2, name, 4)


def sheet_box_slats_accessories():
    s = Svg(f"sheet4_box_slats_accessories_{T:g}mm.svg")
    y = MARGIN
    for beam in ("front clamp beam", "back clamp beam"):
        for i, phase in enumerate((0, 0, 1, 1)):
            box_slat(s, MARGIN, y, phase, f"{beam} - slat {'AABB'[i]}{i % 2 + 1}")
            y += BEAM + 2
    holes = [15 + i * 50 for i in range(9)]
    for i in range(2):
        strip(s, MARGIN, y, INNER_W - 10, 20, f"apron bar {i + 1}", holes)
        y += 24
    pickup_stick(s, MARGIN, y)
    y += 34
    assert y - 4 <= BED_H - MARGIN, "sheet 4 does not fit"
    s.save()


if __name__ == "__main__":
    assert SIDE_L + 2 * MARGIN <= BED_W and HEDDLE_L + 2 * MARGIN <= BED_W
    sheet_side_panels(True)
    sheet_side_panels(False)
    sheet_heddle_frames()
    sheet_box_slats_accessories()
    sheet_heddle_middle()
    sheet_heddle_blocks()
    print(f"inside width {INNER_W} mm, clamp beam/breast/back beam {BEAM_L:.0f} mm, "
          f"heddle {HEDDLE_L:.0f} x {HEDDLE_H:.0f} mm")
    print(f"dowel Ø{DOWEL_D:g}: 2 x {INNER_W + 2 * SIDE_T + 76:.0f} mm (rollers) and "
          f"2 x {BEAM_L:.0f} mm (breast/back beam)")
    print(f"M5 threaded rod: 2 x {BEAM_L + 2 * T + 2 * 8:.0f} mm")
    print("SVGs written to", OUT)
