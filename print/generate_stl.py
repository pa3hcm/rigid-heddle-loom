#!/usr/bin/env python3
"""Generates STL files for the 3D-printed parts (without OpenSCAD, pure Python).

    python3 generate_stl.py

Creates in this folder:
    ratchet_front.stl,    - ratchet wheels for the cloth roller and the warp roller: mirror images,
    ratchet_back.stl        because the tension pulls the rollers back in opposite directions
    ratchet_*, knob.stl   - double-D bore (fits the filed shaft) + hole for a locking screw
    collar.stl            - round bore + hole for a locking screw
    pawl.stl
    filing_jig.stl        - jig to file the two flats on the shaft straight and equally deep
Print 1 of each ratchet wheel, 2 each of knob, collar and pawl, and 1 filing jig.
All parts stand upright/flat on the bed and need no supports.
The dimensions match loom_print.scad.
"""
import math
import os
import struct

# ---------------------------------------------------------------- dimensions
DOWEL_D = 21.7         # measured diameter of the dowel (nominal 22 mm)
CLEARANCE = 0.4
BORE_R = (DOWEL_D + CLEARANCE) / 2
FLAT_DISTANCE = 18.5   # distance between the two filed flats on the shaft
FLAT_LENGTH = 60.0     # length of the flats from the end of the shaft
BORE_F = (FLAT_DISTANCE + CLEARANCE) / 2
SCREW_HOLE = 3.8       # through hole for a 3.5 x 25 wood screw
TEETH = 16
R_TIP, R_ROOT = 35.0, 29.0
WHEEL_T = 10.0
HUB_R, HUB_L = 21.0, 14.0
PAWL_LENGTH = 41.0
PAWL_HOLE_R = 5.4 / 2
KNOB_D, KNOB_T = 90.0, 18.0
JIG_R = 18.0
SAMPLES = 360

HERE = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------- 2D shapes (polar around the origin)
def circle(cx, cy, r, n=64):
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def convex_hull(pts):
    pts = sorted(set(pts))

    def half(seq):
        h = []
        for p in seq:
            while len(h) >= 2 and ((h[-1][0] - h[-2][0]) * (p[1] - h[-2][1])
                                   - (h[-1][1] - h[-2][1]) * (p[0] - h[-2][0])) <= 0:
                h.pop()
            h.append(p)
        return h[:-1]

    return half(pts) + half(reversed(pts))


def ray(poly, theta):
    """Largest distance at which a ray from the origin crosses the edge of poly (or None)."""
    dx, dy = math.cos(theta), math.sin(theta)
    best = None
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        ex, ey = x2 - x1, y2 - y1
        den = dx * ey - dy * ex
        if abs(den) < 1e-12:
            continue
        t = (x1 * ey - y1 * ex) / den
        u = (x1 * dy - y1 * dx) / den
        if t > 0 and -1e-9 <= u <= 1 + 1e-9:
            best = t if best is None else max(best, t)
    return best


class Shape:
    """Star-shaped outline around the origin: union of polygons (convex, or star-shaped)."""

    def __init__(self, *polys):
        self.polys = polys

    def r(self, theta):
        return max(r for r in (ray(p, theta) for p in self.polys) if r is not None)

    def angles(self):
        return [math.atan2(y, x) % (2 * math.pi) for p in self.polys for x, y in p]


class Round(Shape):
    """Circle with radius r (exact, without corner points)."""

    def __init__(self, r):
        self.radius = r

    def r(self, theta):
        return self.radius

    def angles(self):
        return []


class DoubleD(Shape):
    """Circle with radius R, flattened on two sides at distance F from the centre (flats perpendicular to x)."""

    def __init__(self, R, F):
        self.R, self.F = R, F

    def r(self, theta):
        c = abs(math.cos(theta))
        return self.R if c < 1e-12 else min(self.R, self.F / c)

    def angles(self):
        a = math.acos(self.F / self.R)
        return [a, math.pi - a, math.pi + a, 2 * math.pi - a]


# ---------------------------------------------------------------- 3D: stacked layers
class Layer:
    """Layer between z0 and z1 with an inner and an outer outline.

    hole: half angle (rad) of a radial hole around angle 0 (direction +x), or 0 for no hole.
    """

    def __init__(self, z0, z1, inner, outer, hole=0.0):
        self.z0, self.z1, self.inner, self.outer, self.hole = z0, z1, inner, outer, hole


def stacked(layers):
    """Builds a watertight mesh from adjoining layers (bottom to top).

    Per angle step ('strip') each layer either has material between its inner and outer outline
    or not. Walls, horizontal faces between layers and radial side walls (at holes and windows)
    are built so that every edge is shared by exactly two triangles.
    """
    angles = set(2 * math.pi * i / SAMPLES for i in range(SAMPLES))
    for l in layers:
        for v in (l.inner, l.outer):
            for h in v.angles():
                angles.update((h - 1e-4, h, h + 1e-4))
        if l.hole:
            angles.update((l.hole, 2 * math.pi - l.hole))
    angles = sorted(h % (2 * math.pi) for h in angles)
    unique = [angles[0]]
    for h in angles[1:]:                  # near-duplicate angles give degenerate triangles
        if h - unique[-1] > 5e-5:
            unique.append(h)
    if 2 * math.pi - unique[-1] + unique[0] <= 5e-5:
        unique.pop()
    # add the exact angles where inner and outer outline touch (edge of a window)
    extra = []
    for l in layers:
        def f(a):
            return l.outer.r(a) - l.inner.r(a)
        for a0, a1 in zip(unique, unique[1:] + [unique[0] + 2 * math.pi]):
            if f(a0) * f(a1) < 0:
                for _ in range(60):
                    m = (a0 + a1) / 2
                    a0, a1 = (a0, m) if f(a0) * f(m) <= 0 else (m, a1)
                extra.append(((a0 + a1) / 2) % (2 * math.pi))
    angles = sorted(unique + [a for a in extra if min(abs(a - u) for u in unique) > 5e-5])
    n = len(angles)

    ri = [[l.inner.r(a) for a in angles] for l in layers]
    ro = [[l.outer.r(a) for a in angles] for l in layers]

    def present(k, i):
        a0, a1 = angles[i], angles[(i + 1) % n]
        if a1 < a0:
            a1 += 2 * math.pi
        mid = (a0 + a1) / 2 % (2 * math.pi)
        l = layers[k]
        if l.hole and min(mid, 2 * math.pi - mid) < l.hole:
            return False
        return l.outer.r(mid) > l.inner.r(mid) + 1e-6

    on = [[present(k, i) for i in range(n)] for k in range(len(layers))]
    tris = []

    def p(r, a, z):
        return (r * math.cos(a), r * math.sin(a), z)

    def face(r_in, r_out, i, z, up):
        """Horizontal ring strip between two radius profiles (per corner point) at height z."""
        j = (i + 1) % n
        (q0, q1), (r0, r1) = r_in, r_out
        if r0 - q0 <= 1e-9 and r1 - q1 <= 1e-9:
            return
        a0, a1 = angles[i], angles[j]
        t = [(p(q0, a0, z), p(r0, a0, z), p(r1, a1, z)), (p(q0, a0, z), p(r1, a1, z), p(q1, a1, z))]
        tris.extend(t if up else [(a, c, b) for a, b, c in t])

    for i in range(n):
        j = (i + 1) % n
        a0, a1 = angles[i], angles[j]
        for k, l in enumerate(layers):
            if not on[k][i]:
                continue
            z0, z1 = l.z0, l.z1
            o0, o1, b0, b1 = ro[k][i], ro[k][j], ri[k][i], ri[k][j]
            tris += [(p(o0, a0, z0), p(o1, a1, z0), p(o1, a1, z1)),
                     (p(o0, a0, z0), p(o1, a1, z1), p(o0, a0, z1))]
            tris += [(p(b0, a0, z0), p(b1, a1, z1), p(b1, a1, z0)),
                     (p(b0, a0, z0), p(b0, a0, z1), p(b1, a1, z1))]
        # horizontal faces at every layer boundary: material below and not above faces up
        for k in range(len(layers) + 1):
            below = k - 1 if k > 0 and on[k - 1][i] else None
            above = k if k < len(layers) and on[k][i] else None
            z = layers[k].z0 if k < len(layers) else layers[-1].z1

            def prof(m):
                return (ri[m][i], ri[m][j]), (ro[m][i], ro[m][j])

            for src, other, neighbour, up in ((below, above, k, True), (above, below, k - 1, False)):
                if src is None:
                    continue
                vb, vo = prof(src)
                if other is None:
                    if 0 <= neighbour < len(layers):
                        # split at the inner edge of the neighbouring layer, so the edges match
                        m = tuple(min(vo[e], max(vb[e], ri[neighbour][(i, j)[e]])) for e in (0, 1))
                        face(vb, m, i, z, up)
                        face(m, vo, i, z, up)
                    else:
                        face(vb, vo, i, z, up)
                    continue
                ab, ao = prof(other)
                # part inside the inner edge of the other layer
                face(vb, tuple(min(vo[e], max(vb[e], ab[e])) for e in (0, 1)), i, z, up)
                # part outside the outer edge of the other layer
                face(tuple(max(vb[e], min(vo[e], ao[e])) for e in (0, 1)), vo, i, z, up)
    # radial side walls where a strip with material borders a strip without
    for i in range(n):
        h = (i - 1) % n
        a = angles[i]
        for k, l in enumerate(layers):
            if on[k][i] == on[k][h] or ro[k][i] - ri[k][i] <= 1e-9:
                continue
            q = [p(ri[k][i], a, l.z0), p(ro[k][i], a, l.z0), p(ro[k][i], a, l.z1), p(ri[k][i], a, l.z1)]
            t = [(q[0], q[1], q[2]), (q[0], q[2], q[3])]
            tris.extend(t if on[k][i] else [(x, z, y) for x, y, z in t])
    return tris


def with_hub(inner, outer, thickness, hole_inner_r):
    """Layers for a disc (thickness may be 0) with a hub on top that has a radial locking-screw hole."""
    alpha = math.atan(SCREW_HOLE / 2 / hole_inner_r)
    zm, h = thickness + HUB_L / 2, SCREW_HOLE / 2
    layers = [Layer(0, thickness, inner, outer)] if thickness else []
    return layers + [Layer(thickness, zm - h, inner, Round(HUB_R)),
                     Layer(zm - h, zm + h, inner, Round(HUB_R), alpha),
                     Layer(zm + h, thickness + HUB_L, inner, Round(HUB_R))]


# ---------------------------------------------------------------- parts
def ratchet(front=False):
    """Ratchet wheel with the hub facing out (+z), seen from the hub side.

    back (warp roller): steep tooth flank faces anticlockwise, the pawl blocks anticlockwise turning.
    front (cloth roller): mirrored, the pawl blocks clockwise turning.
    """
    step = 2 * math.pi / TEETH
    tip = 0.08 if front else 0.92        # position of the tooth tip within one tooth pitch
    teeth = []
    for i in range(TEETH):
        teeth.append((R_ROOT * math.cos(i * step), R_ROOT * math.sin(i * step)))
        teeth.append((R_TIP * math.cos((i + tip) * step), R_TIP * math.sin((i + tip) * step)))
    return stacked(with_hub(DoubleD(BORE_R, BORE_F), Shape(teeth), WHEEL_T, BORE_F))


def knob():
    star = []
    for i in range(SAMPLES):
        t = 2 * math.pi * i / SAMPLES
        r = KNOB_D / 3 + KNOB_D / 6 * (0.5 + 0.5 * math.cos(5 * t)) ** 2
        star.append((r * math.cos(t), r * math.sin(t)))
    return stacked(with_hub(DoubleD(BORE_R, BORE_F), Shape(star), KNOB_T, BORE_F))


def collar():
    return stacked(with_hub(Round(BORE_R), None, 0, BORE_R))


def pawl():
    # pivot at the origin, tip at (-PAWL_LENGTH, 0), release tab towards the top right
    arm = convex_hull(circle(0, 0, 8) + circle(-PAWL_LENGTH + 6, 0, 5))
    tip = [(-PAWL_LENGTH + 6, -5), (-PAWL_LENGTH, -1), (-PAWL_LENGTH, 1.5), (-PAWL_LENGTH + 6, 5)]
    tab = convex_hull(circle(0, 0, 6) + circle(22, 6, 5))
    return stacked([Layer(0, WHEEL_T, Round(PAWL_HOLE_R), Shape(arm, tip, tab))])


def filing_jig():
    """Sleeve over the shaft with a stop at the bottom and two windows.

    The edges of the windows are exactly FLAT_DISTANCE / 2 from the centre: file until the shaft
    is level with the edges. The stop sets the length of the flats.
    """
    base = 3.0
    return stacked([
        Layer(0, base, Round(3.0), Round(JIG_R)),
        Layer(base, base + FLAT_LENGTH, Round(BORE_R), DoubleD(JIG_R, FLAT_DISTANCE / 2)),
        Layer(base + FLAT_LENGTH, base + FLAT_LENGTH + 15, Round(BORE_R), Round(JIG_R)),
    ])


# ---------------------------------------------------------------- check & export
def check(tris):
    """Watertight: every edge occurs exactly once in each direction. Returns the volume."""
    def k(p):
        return tuple(round(c, 5) for c in p)
    edges = {}
    vol = 0.0
    for a, b, c in tris:
        for u, v in ((a, b), (b, c), (c, a)):
            edges[(k(u), k(v))] = edges.get((k(u), k(v)), 0) + 1
        vol += (a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0])
                + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6
    errors = sum(1 for (u, v), n in edges.items() if u != v and (n != 1 or edges.get((v, u)) != 1))
    return vol, errors


def write_stl(name, tris):
    tris = [t for t in tris if len({tuple(round(c, 5) for c in p) for p in t}) == 3]
    with open(os.path.join(HERE, name), "wb") as f:
        f.write(name.encode().ljust(80, b" ")[:80])
        f.write(struct.pack("<I", len(tris)))
        for a, b, c in tris:
            u = [b[i] - a[i] for i in range(3)]
            v = [c[i] - a[i] for i in range(3)]
            n = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
            l = math.sqrt(sum(x * x for x in n)) or 1
            f.write(struct.pack("<12fH", *(x / l for x in n), *a, *b, *c, 0))
    return tris


if __name__ == "__main__":
    for name, make in (("ratchet_front.stl", lambda: ratchet(front=True)), ("ratchet_back.stl", ratchet),
                       ("pawl.stl", pawl), ("knob.stl", knob),
                       ("collar.stl", collar), ("filing_jig.stl", filing_jig)):
        tris = write_stl(name, make())
        vol, errors = check(tris)
        status = "watertight" if errors == 0 else f"{errors} open edges!"
        print(f"{name:18s} {len(tris):6d} triangles  {vol / 1000:6.1f} cm3  {status}")
