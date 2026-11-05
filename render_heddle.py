#!/usr/bin/env python3
"""Renders an exploded 3D view of the heddle to heddle_exploded.png (pure Python, z-buffer).

The layers (front heddle frame, Lojan segments, middle layer, back heddle frame) are pulled apart
with the M3 bolts between them. Dimensions come from generate_laser.py. Requires ImageMagick
('convert') for the PNG and labels.
    python3 render_heddle.py
"""
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import generate_laser as g  # noqa: E402

W, H, SS = 1600, 1000, 2
VIEW = (1.0, 0.55, -0.42)          # from front right, above
LIGHT = (-0.6, -0.5, 1.0)
APART = 55.0                       # distance between the layers in the exploded view

WOOD = (226, 190, 140)
ACRYLIC = (196, 222, 236)
SEGMENT = (58, 60, 66)
SEGMENT_LIGHT = (125, 128, 136)
METAL = (150, 150, 158)


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

faces = []   # (list of 3D contours, colour, draw edges)


def circle(cy, cz, r, n=14):
    return [(cy + r * math.cos(2 * math.pi * i / n), cz + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def rectangle(y0, y1, z0, z1):
    return [(y0, z0), (y1, z0), (y1, z1), (y0, z1)]


def prism_x(contours, x0, x1, colour, walls=True):
    """Plate perpendicular to x: the first contour is the outer edge, the rest are holes (even-odd)."""
    for x in (x0, x1):
        faces.append(([[(x, y, z) for y, z in c] for c in contours], colour, True))
    if not walls:
        return
    for c in contours:
        for i in range(len(c)):
            (ya, za), (yb, zb) = c[i], c[(i + 1) % len(c)]
            faces.append(([[(x0, ya, za), (x0, yb, zb), (x1, yb, zb), (x1, ya, za)]], colour, False))


# ---------------------------------------------------------------- heddle
mid_u = g.HEDDLE_L / 2


def local(c):
    """Heddle coordinates (u from 0..HEDDLE_L, v from 0..HEDDLE_H) to world (y, z)."""
    return [(u - mid_u, v) for u, v in c]


outer = local(g.heddle_outline())
window = rectangle(-g.WINDOW_L / 2, g.WINDOW_L / 2, g.HEDDLE_H / 2 - g.WINDOW_H / 2, g.HEDDLE_H / 2 + g.WINDOW_H / 2)
groove = rectangle(-g.GROOVE_L / 2, g.GROOVE_L / 2, g.HEDDLE_H / 2 - g.GROOVE_H / 2, g.HEDDLE_H / 2 + g.GROOVE_H / 2)
bolt_yz = [(x, g.HEDDLE_H / 2 + y) for x, y in g.heddle_bolt_holes()]
holes = [circle(y, z, g.M3_HOLE / 2) for y, z in bolt_yz]

X_FRONT, X_SEG, X_MID, X_BACK = 0.0, APART, 2 * APART, 3 * APART
prism_x([outer, window] + holes, X_FRONT, X_FRONT + g.T, WOOD)
prism_x([outer, groove] + holes, X_MID, X_MID + g.T_ACRYLIC, ACRYLIC)
prism_x([outer, window] + holes, X_BACK, X_BACK + g.T, WOOD)

# Lojan segments: rails (3 mm) over the full height, reed (5 mm) between them, slots and holes as lines
zc, rz = g.HEDDLE_H / 2, g.SEG_H / 2 - g.SEG_RAIL_H
xr = X_SEG + (g.SEG_REED_T - g.SEG_RAIL_T) / 2
pitch = 100.0 / g.DENTS_PER_10CM
for i in range(g.SEG_N):
    ya = -g.WEAVING_WIDTH / 2 + i * g.SEG_W
    yb = ya + g.SEG_W - 0.2
    for z0, z1 in ((zc - g.SEG_H / 2, zc - rz), (zc + rz, zc + g.SEG_H / 2)):
        prism_x([rectangle(ya, yb, z0, z1)], xr, xr + g.SEG_RAIL_T, SEGMENT)
    prism_x([rectangle(ya, yb, zc - rz, zc + rz)], X_SEG, X_SEG + g.SEG_REED_T, SEGMENT)
    for k in range(round(g.SEG_W / pitch)):
        y = ya + (k + .5) * pitch
        faces.append(([[(X_SEG - .05, y - .35, zc - rz + 3), (X_SEG - .05, y + .35, zc - rz + 3),
                        (X_SEG - .05, y + .35, zc + rz - 3), (X_SEG - .05, y - .35, zc + rz - 3)]],
                      SEGMENT_LIGHT, False))

# M3 bolts: head at the front, shank through all layers, washer and nut at the back
for y, z in bolt_yz:
    prism_x([circle(y, z, 2.8, 12)], X_FRONT - 3, X_FRONT, METAL)
    prism_x([circle(y, z, 1.5, 8)], X_FRONT, X_BACK + g.T + 6, METAL)
    prism_x([circle(y, z, 3.2, 6)], X_BACK + g.T + 1, X_BACK + g.T + 3.5, METAL)

# ---------------------------------------------------------------- rasterise
def proj(p):
    return dot(p, R), -dot(p, U), dot(p, D)


everything = [proj(p) for c, _, _ in faces for cc in c for p in cc]
minx, maxx = min(p[0] for p in everything), max(p[0] for p in everything)
miny, maxy = min(p[1] for p in everything), max(p[1] for p in everything)
scale = min(W * 0.84 / (maxx - minx), H * 0.62 / (maxy - miny)) * SS
BW, BH = W * SS, H * SS
offx = BW * 0.5 - scale * (minx + maxx) / 2
offy = BH * 0.56 - scale * (miny + maxy) / 2


def screen(p):
    x, y, z = proj(p)
    return x * scale + offx, y * scale + offy, z


zbuf = [math.inf] * (BW * BH)
pixels = bytearray(b"\xf8\xf6\xf1" * (BW * BH))


def normal(pts):
    nx = ny = nz = 0.0
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        nx += (a[1] - b[1]) * (a[2] + b[2])
        ny += (a[2] - b[2]) * (a[0] + b[0])
        nz += (a[0] - b[0]) * (a[1] + b[1])
    l = math.sqrt(nx * nx + ny * ny + nz * nz) or 1
    return nx / l, ny / l, nz / l


def fill(contours, rgb):
    """Fill a face with holes (even-odd scanline) with a depth test via the plane equation."""
    sc = [[screen(p) for p in c] for c in contours]
    p0 = sc[0][0]
    best, p1, p2 = 0, None, None
    pts = sc[0]
    for i in range(1, len(pts)):
        for j in range(i + 1, len(pts), max(1, len(pts) // 12)):
            a = abs((pts[i][0] - p0[0]) * (pts[j][1] - p0[1]) - (pts[i][1] - p0[1]) * (pts[j][0] - p0[0]))
            if a > best:
                best, p1, p2 = a, pts[i], pts[j]
    if best < 1e-6:
        return
    # z = a*x + b*y + c
    (x0, y0_, z0), (x1, y1, z1), (x2, y2, z2) = p0, p1, p2
    det = (x1 - x0) * (y2 - y0_) - (x2 - x0) * (y1 - y0_)
    a = ((z1 - z0) * (y2 - y0_) - (z2 - z0) * (y1 - y0_)) / det
    b = ((x1 - x0) * (z2 - z0) - (x2 - x0) * (z1 - z0)) / det
    c = z0 - a * x0 - b * y0_
    edges = [(q[i], q[(i + 1) % len(q)]) for q in sc for i in range(len(q))]
    ys = [p[1] for q in sc for p in q]
    for py in range(max(0, int(min(ys))), min(BH - 1, int(max(ys)) + 1) + 1):
        yc = py + .5
        xs = sorted(xa + (yc - ya) * (xb - xa) / (yb - ya)
                    for (xa, ya, _), (xb, yb, _) in edges if (ya <= yc < yb) or (yb <= yc < ya))
        row = py * BW
        for k in range(0, len(xs) - 1, 2):
            for px in range(max(0, int(xs[k] + .5)), min(BW, int(xs[k + 1] + .5))):
                z = a * (px + .5) + b * yc + c
                i = row + px
                if z < zbuf[i]:
                    zbuf[i] = z
                    pixels[i * 3:i * 3 + 3] = rgb


def line(p, q, rgb, tol=1.0):
    a, b = screen(p), screen(q)
    steps = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]))) + 1
    for s in range(steps + 1):
        t = s / steps
        x, y, z = a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]), a[2] + t * (b[2] - a[2])
        px, py = int(x), int(y)
        if 0 <= px < BW and 0 <= py < BH:
            i = py * BW + px
            if z <= zbuf[i] + tol:
                pixels[i * 3:i * 3 + 3] = rgb


for contours, rgb, _ in faces:
    nrm = normal(contours[0])
    if dot(nrm, D) > 0:
        nrm = tuple(-c for c in nrm)
    f = 0.6 + 0.45 * max(0.0, dot(nrm, L))
    fill(contours, bytes(min(255, int(c * f)) for c in rgb))
for contours, rgb, edge in faces:
    if edge:
        dark = tuple(int(c * 0.45) for c in rgb)
        for c in contours:
            for i in range(len(c)):
                line(c[i], c[(i + 1) % len(c)], dark)

ppm = os.path.join(HERE, "heddle_exploded.ppm")
png = os.path.join(HERE, "heddle_exploded.png")
with open(ppm, "wb") as f:
    f.write(f"P6 {BW} {BH} 255\n".encode())
    f.write(pixels)

# ---------------------------------------------------------------- labels
def pix(p):
    x, y, _ = screen(p)
    return x / SS, y / SS


bolt_bl = max(bolt_yz, key=lambda p: (p[0], -p[1]))        # bolt at the bottom left of the image
labels = [
    ((X_FRONT, g.HEDDLE_L / 2 - 90, g.HEDDLE_H - 10), (40, 150), "Front heddle frame - 6 mm plywood"),
    ((X_SEG, 60, g.HEDDLE_H / 2 + 10), (360, 100),
     f"{g.SEG_N} Lojan segments {g.DENTS_PER_10CM}/10, {g.SEG_W:g} mm wide"),
    ((X_MID, -40, g.HEDDLE_H - 6), (760, 150), "Middle layer 3 mm: the opening forms the groove"),
    ((X_BACK, -g.HEDDLE_L / 2 + 6, g.HEDDLE_H - 8), (1260, 400), "Back heddle frame + ear"),
    ((X_FRONT - 3, bolt_bl[0], bolt_bl[1]), (40, 900), "20 x M3 x 20 with washer and nut"),
    ((X_FRONT, -120, g.HEDDLE_H / 2 - g.WINDOW_H / 2 + 1), (760, 960),
     "Window: the reed passes through, the rails do not"),
]
cmd = ["convert", ppm, "-resize", f"{100 // SS}%", "-font", "DejaVu-Sans", "-pointsize", "24",
       "-fill", "#2d2a26", "-stroke", "#2d2a26", "-strokewidth", "1.5"]
for anchor, (tx, ty), text in labels:
    ax, ay = pix(anchor)
    ly = ty + 8 if ay > ty else ty - 28          # start the leader line below or above the text
    cmd += ["-draw", f"line {tx + 4:.0f},{ly:.0f} {ax:.0f},{ay:.0f}",
            "-draw", f"circle {ax:.0f},{ay:.0f} {ax + 4:.0f},{ay:.0f}"]
cmd += ["-stroke", "none"]
for anchor, (tx, ty), text in labels:
    cmd += ["-annotate", f"+{tx}+{ty}", text]
cmd += ["-pointsize", "30", "-annotate", "+40+45", "The heddle, exploded (layers pulled apart)", png]
subprocess.run(cmd, check=True)
os.remove(ppm)
print("written:", png)
