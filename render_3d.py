#!/usr/bin/env python3
"""Renders a 3D impression of the loom to loom_3d.png (pure Python, z-buffer).

Uses the dimensions from generate_laser.py. Requires ImageMagick ('convert') for the PNG.
    python3 render_3d.py          (angled front view)
    python3 render_3d.py side     (side view with table notch)
    python3 render_3d.py left     (angled front view from the left)
    python3 render_3d.py bottom   (bottom view, without table and clamps)
    python3 render_3d.py warping  (flat on the table, clamped at the front clamp beam)
"""
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import generate_laser as g  # noqa: E402

# Loom: X = front (weaver) -> back, Y = width (+Y = left seen from the weaver), Z = up
W, H, SS = 1600, 1100, 2          # final resolution and supersampling
VIEW = (1.0, 0.85, -0.62)         # viewing direction: from front right, above
SIDE = "side" in sys.argv         # side view from the right
LEFT = "left" in sys.argv         # from front left, above
if SIDE:
    VIEW = (0.001, 1.0, -0.08)
LIGHT = (-0.35, -0.55, 1.0)
if LEFT:
    VIEW = (1.0, -0.85, -0.62)
    LIGHT = (-0.35, 0.55, 1.0)
WARPING = "warping" in sys.argv
BOTTOM = "bottom" in sys.argv     # from below, slightly from the right
if BOTTOM:
    VIEW = (0.001, 0.45, 1.0)
    LIGHT = (-0.3, -0.5, -1.0)

WOOD = (226, 190, 140)
WOOD_DARK = (190, 145, 95)
SEGMENT = (58, 60, 66)
SEGMENT_LIGHT = (120, 124, 132)
PRINT = (232, 112, 38)
METAL = (150, 150, 155)
CLAMP = (200, 45, 40)
BLACK = (45, 45, 45)
WARP = (248, 244, 230)
TABLE = (125, 98, 78)
CLOTH = [(40, 120, 130), (248, 244, 230), (190, 80, 50), (248, 244, 230)]


def norm(v):
    l = math.sqrt(sum(c * c for c in v))
    return tuple(c / l for c in v)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


D = norm(VIEW)
R = norm(cross(D, (0, 0, 1)))
U = cross(R, D)
L = norm(LIGHT)

faces = []   # (3D points, colour, draw edges)
lines = []   # (3D points, colour, width)


def face(pts, colour, edge=True):
    faces.append((pts, colour, edge))


def prism_y(outline, y0, y1, colour, side_edges=True):
    """Extrudes an outline in the XZ plane along Y."""
    face([(x, y0, z) for x, z in outline], colour)
    face([(x, y1, z) for x, z in outline], colour)
    n = len(outline)
    for i in range(n):
        (xa, za), (xb, zb) = outline[i], outline[(i + 1) % n]
        face([(xa, y0, za), (xb, y0, zb), (xb, y1, zb), (xa, y1, za)], colour, side_edges)


def box(x0, x1, y0, y1, z0, z1, colour):
    prism_y([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], y0, y1, colour)


def circle(cx, cz, r, n=40):
    return [(cx + r * math.cos(2 * math.pi * i / n), cz + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def cylinder_y(cx, cz, r, y0, y1, colour, n=40):
    prism_y(circle(cx, cz, r, n), y0, y1, colour, side_edges=False)


# ---------------------------------------------------------------- model
YI = g.INNER_W / 2         # inside of the side panel
YO = YI + g.SIDE_T         # outside of the side panel
def clean(pts):
    return [p for i, p in enumerate(pts) if p != pts[i - 1]]


for s in (1, -1):
    prism_y(clean(g.side_panel_outline(True)), s * YI, s * (YI + g.T), WOOD)
    prism_y(clean(g.side_panel_outline(False)), s * (YI + g.T), s * YO, WOOD)

for cx_, cz_ in (g.BREAST_BEAM, g.BACK_BEAM):        # breast and back beam: dowel
    cylinder_y(cx_, cz_, g.DOWEL_D / 2, -YI - g.T, YI + g.T, WOOD_DARK)
for cx_, cz_ in g.clamp_beam_centers():               # threaded rod with dome nuts through the boxes
    for sgn in (1, -1):
        cylinder_y(cx_, cz_, 7.5, sgn * YO, sgn * (YO + 1.2), METAL, 16)
        cylinder_y(cx_, cz_, 4.6, sgn * (YO + 1.2), sgn * (YO + 9), METAL, 6)
prism_y(g.clamp_beam_corners(), -YI - g.T, YI + g.T, WOOD)
box(g.FRONT_CLAMP_X, g.FRONT_CLAMP_X + g.BEAM, -YI - g.T, YI + g.T, 0, g.BEAM, WOOD)   # front clamp beam

# rollers, right (-Y) ratchet wheel + knob, left collar
for (cx, cz), wound, colour, tip in ((g.CLOTH_ROLLER, 17, CLOTH[0], .08), (g.WARP_ROLLER, 22, WARP, .92)):
    cylinder_y(cx, cz, g.DOWEL_D / 2, -YO - 47, YO + 16, WOOD_DARK)
    cylinder_y(cx, cz, wound, -200, 200, colour)
    teeth, step = 16, 2 * math.pi / 16
    wheel = []
    for i in range(teeth):
        wheel.append((cx + 29 * math.cos(i * step), cz + 29 * math.sin(i * step)))
        wheel.append((cx + 35 * math.cos((i + tip) * step), cz + 35 * math.sin((i + tip) * step)))
    prism_y(wheel, -YO - 1, -YO - 11, PRINT)
    cylinder_y(cx, cz, 21, -YO - 11, -YO - 25, PRINT)
    knob = [(cx + (30 + 15 * (0.5 + 0.5 * math.cos(5 * t)) ** 2) * math.cos(t),
             cz + (30 + 15 * (0.5 + 0.5 * math.cos(5 * t)) ** 2) * math.sin(t))
            for t in (2 * math.pi * i / 80 for i in range(80))]
    prism_y(knob, -YO - 25, -YO - 43, PRINT)
    cylinder_y(cx, cz, 21, YO, YO + 14, PRINT)

# pawls: tip at radius 32 of the ratchet wheel, 41 mm from the pivot
for (px, pz), (cx, cz) in ((g.PAWL_FRONT, g.CLOTH_ROLLER), (g.PAWL_BACK, g.WARP_ROLLER)):
    dx, dz = cx - px, cz - pz
    d = math.hypot(dx, dz)
    a = (41 ** 2 - 32 ** 2 + d ** 2) / (2 * d)
    h = math.sqrt(41 ** 2 - a ** 2)
    candidates = [(px + a * dx / d + s * h * dz / d, pz + a * dz / d - s * h * dx / d) for s in (1, -1)]
    tx, tz = max(candidates, key=lambda p: p[1])
    ux, uz = (tx - px) / 41, (tz - pz) / 41
    nx, nz = -uz, ux
    arm = [(px - 7 * ux + 7 * nx, pz - 7 * uz + 7 * nz), (tx + 4 * nx, tz + 4 * nz),
           (tx - 3 * nx, tz - 3 * nz), (px - 7 * ux - 7 * nx, pz - 7 * uz - 7 * nz)]
    prism_y(arm, -YO - 1, -YO - 11, PRINT)
    cylinder_y(px, pz, 5, -YO - 11, -YO - 15, METAL, 16)

# heddle blocks on the outside of both side panels
for sgn in (1, -1):
    prism_y(g.heddle_block_outline(), sgn * YO, sgn * (YO + g.T), WOOD)
    prism_y(g.heddle_block_outline(), sgn * (YO + g.T), sgn * (YO + g.BLOCK_T), WOOD)

# heddle in the down position, ears slid back under the lip
x_mid, ear_b = g.POSITIONS["down 1"]
kz0 = ear_b + g.EAR_H - g.HEDDLE_H
top = kz0 + g.HEDDLE_H
kzc = kz0 + g.HEDDLE_H / 2
kx = x_mid - (2 * g.T + g.T_ACRYLIC) / 2
hb, hl = g.HEDDLE_W / 2, g.HEDDLE_L / 2
vy, vz = g.WINDOW_L / 2, g.WINDOW_H / 2


def heddle_layer(x0, x1, colour):
    box(x0, x1, -hb, hb, kz0, kzc - vz, colour)
    box(x0, x1, -hb, hb, kzc + vz, top - g.EAR_H, colour)
    box(x0, x1, -hl, hl, top - g.EAR_H, top, colour)          # top rail with ears
    for sgn in (1, -1):
        box(x0, x1, min(sgn * vy, sgn * hb), max(sgn * vy, sgn * hb), kzc - vz, kzc + vz, colour)


for x0 in (kx, kx + g.T + g.T_ACRYLIC):
    heddle_layer(x0, x0 + g.T, WOOD)
# Lojan segments: the reed (5 mm thick) passes through the windows of both frames
ax0 = kx + (g.HEDDLE_T - g.SEG_REED_T) / 2
ax1 = ax0 + g.SEG_REED_T
pitch = 100.0 / g.DENTS_PER_10CM
n = round(g.WEAVING_WIDTH / pitch)
rz = g.SEG_H / 2 - g.SEG_RAIL_H
for i in range(g.SEG_N):
    ya = -g.WEAVING_WIDTH / 2 + i * g.SEG_W
    box(ax0, ax1, ya + .15, ya + g.SEG_W - .15, kzc - rz, kzc + rz, SEGMENT)
for i in range(n + 1):
    y = -g.WEAVING_WIDTH / 2 + i * pitch
    faces.append(([(ax0 - .05, y - .4, kzc - rz), (ax0 - .05, y + .4, kzc - rz), (ax0 - .05, y + .4, kzc + rz),
                   (ax0 - .05, y - .4, kzc + rz)], SEGMENT_LIGHT, False))

# warp: threads in the slots stay straight, threads in the holes move with the heddle
FELL = 120.0
heddle_x = x_mid
zb = g.WARP_H
for i in range(2 * n + 1):
    y = -g.WEAVING_WIDTH / 2 + i * pitch / 2
    z_heddle = zb - (g.HEDDLE_STROKE if i % 2 else 0)   # down position: threads in the holes go down
    lines.append(([(g.WARP_ROLLER[0] + 20, y, g.WARP_ROLLER[1] + 10), (g.BACK_BEAM[0] + g.DOWEL_D / 2, y, zb - 4),
                   (g.BACK_BEAM[0] + 8, y, zb + .5), (heddle_x, y, z_heddle), (FELL, y, zb + .5)], WARP, 1.4))

# woven cloth with stripes, over the breast beam to the cloth roller
steps = 9
front_edge = g.BREAST_BEAM[0] - g.DOWEL_D / 2
for i in range(steps):
    xa = FELL - i * (FELL - front_edge) / steps
    xb = FELL - (i + 1) * (FELL - front_edge) / steps
    face([(xa, -200, zb + .6), (xb, -200, zb + .6), (xb, 200, zb + .6), (xa, 200, zb + .6)],
         CLOTH[i % len(CLOTH)], False)
face([(front_edge, -200, zb + .6), (front_edge - 1, -200, zb - 10), (front_edge - 1, 200, zb - 10),
      (front_edge, 200, zb + .6)], CLOTH[0], False)
face([(front_edge - 1, -200, zb - 10), (g.CLOTH_ROLLER[0] - 14, -200, g.CLOTH_ROLLER[1] + 10),
      (g.CLOTH_ROLLER[0] - 14, 200, g.CLOTH_ROLLER[1] + 10), (front_edge - 1, 200, zb - 10)], CLOTH[0], False)

# shuttle halfway through the open (lower) shed, with weft wound on it; sticks out in front of the block
box(185, 225, -380, 70, zb - 10, zb - 4, WOOD)
box(193, 217, -300, 20, zb - 4, zb - 2, CLOTH[2])
n_loom = len(faces)

# table: the table edge drops into the notch, the table top lies against the slanted face
# (when warping: loom flat on the table, table edge just in front of the front clamp beam)
cl = (g.BEAM_CLEARANCE + g.KERF) / 2
th = 0.0 if WARPING else math.radians(g.TABLE_ANGLE)
table_w = 200 if SIDE else 520            # narrow in side view, so the notch stays visible
cx, cz = (g.FRONT_CLAMP_X - cl, 0.0) if WARPING else (g.TABLE_X, g.TABLE_DEPTH)
bx, bz = math.cos(th), -math.sin(th)       # table top towards the back
dx, dz = -math.sin(th), -math.cos(th)      # downwards
prism_y([(cx, cz), (cx + 700 * bx, cz + 700 * bz), (cx + 700 * bx + 30 * dx, cz + 700 * bz + 30 * dz),
         (cx + 30 * dx, cz + 30 * dz)], -table_w, table_w, TABLE)


# F-clamps on both sides over the clamp beam; u along the table top, v perpendicular to it
def table_box(u0, u1, v0, v1, y0, y1, colour):
    def p(u, v):
        return (cx + u * bx - v * dx, cz + u * bz - v * dz)
    prism_y([p(u0, v0), p(u1, v0), p(u1, v1), p(u0, v1)], y0, y1, colour)


km = (cl if WARPING else g.CLAMP_OFFSET) + g.BEAM / 2    # middle of the clamp beam
for yc in (YI - 30, -YI + 30):
    table_box(-22, -12, -75, g.BEAM + 20, yc - 5, yc + 5, METAL)           # bar
    table_box(-22, km + 12, g.BEAM + 8, g.BEAM + 20, yc - 7, yc + 7, CLAMP)  # upper jaw
    table_box(km - 11, km + 11, g.BEAM, g.BEAM + 8, yc - 11, yc + 11, BLACK)
    table_box(-22, km + 12, -62, -50, yc - 7, yc + 7, CLAMP)               # lower jaw
    table_box(km - 2, km + 2, -50, -34, yc - 2, yc + 2, METAL)             # spindle
    table_box(km - 11, km + 11, -34, -30, yc - 11, yc + 11, BLACK)
    table_box(km - 7, km + 7, -100, -62, yc - 7, yc + 7, WOOD_DARK)        # handle


# ---------------------------------------------------------------- rasterise
if BOTTOM:
    del faces[n_loom:]                 # leave out table and clamps, they would hide the bottom
TILT = 0.0 if BOTTOM or WARPING else math.radians(g.TABLE_ANGLE)   # tilt so the table is horizontal


def proj(p):
    x, y, z = p
    p = (x * math.cos(TILT) - z * math.sin(TILT), y, x * math.sin(TILT) + z * math.cos(TILT))
    return dot(p, R), -dot(p, U), dot(p, D)


everything = [proj(p) for f in faces[:n_loom] for p in f[0]]
minx, maxx = min(p[0] for p in everything), max(p[0] for p in everything)
miny, maxy = min(p[1] for p in everything), max(p[1] for p in everything)
scale = min((W * 0.92) / (maxx - minx), (H * 0.92) / (maxy - miny)) * SS
BW, BH = W * SS, H * SS
offx = BW / 2 - scale * (minx + maxx) / 2
offy = BH / 2 - scale * (miny + maxy) / 2


def screen(p):
    x, y, z = proj(p)
    return x * scale + offx, y * scale + offy, z


zbuf = [math.inf] * (BW * BH)
pixels = bytearray(BW * BH * 3)
for y in range(BH):                       # background: soft gradient
    t = y / BH
    c = bytes((int(250 - 18 * t), int(248 - 18 * t), int(244 - 20 * t)))
    pixels[y * BW * 3:(y + 1) * BW * 3] = c * BW


def ear_clip(pts2):
    """Ear clipping for (possibly concave) simple polygons."""
    idx = list(range(len(pts2)))
    area = sum(pts2[i][0] * pts2[(i + 1) % len(pts2)][1] - pts2[(i + 1) % len(pts2)][0] * pts2[i][1]
               for i in range(len(pts2)))
    if area < 0:
        idx.reverse()
    tris = []

    def inside(p, a, b, c):
        def k(o, q, r):
            return (q[0] - o[0]) * (r[1] - o[1]) - (q[1] - o[1]) * (r[0] - o[0])
        return k(a, b, p) >= 0 and k(b, c, p) >= 0 and k(c, a, p) >= 0

    while len(idx) > 3:
        for j in range(len(idx)):
            i0, i1, i2 = idx[j - 1], idx[j], idx[(j + 1) % len(idx)]
            a, b, c = pts2[i0], pts2[i1], pts2[i2]
            if (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]) <= 1e-9:
                continue
            if any(inside(pts2[k], a, b, c) for k in idx if k not in (i0, i1, i2)):
                continue
            tris.append((i0, i1, i2))
            idx.pop(j)
            break
        else:
            break
    if len(idx) == 3:
        tris.append(tuple(idx))
    return tris


def triangle(a, b, c, rgb):
    x0, x1 = max(int(min(a[0], b[0], c[0])), 0), min(int(max(a[0], b[0], c[0])) + 1, BW - 1)
    y0, y1 = max(int(min(a[1], b[1], c[1])), 0), min(int(max(a[1], b[1], c[1])) + 1, BH - 1)
    den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(den) < 1e-12:
        return
    for py in range(y0, y1 + 1):
        fy = py + .5
        row = py * BW
        for px in range(x0, x1 + 1):
            fx = px + .5
            w0 = ((b[1] - c[1]) * (fx - c[0]) + (c[0] - b[0]) * (fy - c[1])) / den
            if w0 < 0:
                continue
            w1 = ((c[1] - a[1]) * (fx - c[0]) + (a[0] - c[0]) * (fy - c[1])) / den
            if w1 < 0 or w0 + w1 > 1:
                continue
            z = w0 * a[2] + w1 * b[2] + (1 - w0 - w1) * c[2]
            k = row + px
            if z < zbuf[k]:
                zbuf[k] = z
                pixels[k * 3:k * 3 + 3] = rgb


def line(p, q, rgb, width, tol=1.5):
    a, b = screen(p), screen(q)
    steps = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]))) + 1
    r = width * SS / 2
    for s in range(steps + 1):
        t = s / steps
        x, y, z = a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]), a[2] + t * (b[2] - a[2])
        for py in range(int(y - r + .5), int(y + r + .5)):
            for px in range(int(x - r + .5), int(x + r + .5)):
                if 0 <= px < BW and 0 <= py < BH:
                    k = py * BW + px
                    if z <= zbuf[k] + tol:
                        pixels[k * 3:k * 3 + 3] = rgb
                        zbuf[k] = min(zbuf[k], z)


def normal(pts):
    n = [0.0, 0.0, 0.0]
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        n[0] += (a[1] - b[1]) * (a[2] + b[2])
        n[1] += (a[2] - b[2]) * (a[0] + b[0])
        n[2] += (a[0] - b[0]) * (a[1] + b[1])
    l = math.sqrt(sum(c * c for c in n)) or 1
    return tuple(c / l for c in n)


for pts, rgb, _ in faces:
    nrm = normal(pts)
    if dot(nrm, D) > 0:
        nrm = tuple(-c for c in nrm)
    f = 0.55 + 0.5 * max(0.0, dot(nrm, L))
    shaded = bytes(min(255, int(c * f)) for c in rgb)
    sp = [screen(p) for p in pts]
    if len(sp) == 3:
        triangle(*sp, shaded)
        continue
    # 2D projection onto the plane for triangulation
    axis = max(range(3), key=lambda i: abs(nrm[i]))
    p2 = [tuple(c for i, c in enumerate(p) if i != axis) for p in pts]
    for i0, i1, i2 in ear_clip(p2):
        triangle(sp[i0], sp[i1], sp[i2], shaded)

for pts, rgb, edge in faces:
    if edge:
        dark = tuple(int(c * 0.45) for c in rgb)
        for i in range(len(pts)):
            line(pts[i], pts[(i + 1) % len(pts)], dark, 0.9)
for pts, rgb, width in lines:
    for a, b in zip(pts, pts[1:]):
        line(a, b, rgb, width)

png = os.path.join(HERE, "loom_side.png" if SIDE else "loom_left.png" if LEFT
                   else "loom_bottom.png" if BOTTOM else "loom_warping.png" if WARPING
                   else "loom_3d.png")
ppm = png[:-4] + ".ppm"
with open(ppm, "wb") as f:
    f.write(f"P6 {BW} {BH} 255\n".encode())
    f.write(pixels)
subprocess.run(["convert", ppm, "-resize", f"{100 // SS}%", png], check=True)
os.remove(ppm)
print("written:", png)
