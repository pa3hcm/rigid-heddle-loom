#!/usr/bin/env python3
"""Draws how the aprons are attached with Texsolv cord to aprons_texsolv.png (requires inkscape)."""
import math
import os
import subprocess

import generate_laser as g

W, H = 1600, 1000
WOOD, WOOD_D, BAR, BAR_D = "#b98352", "#8a5a30", "#e3c48f", "#a9864f"
CORD, CORD_D, EYE = "#fbf7ec", "#6f6551", "#cdbf9f"
TEXT, ACCENT = "#2d2a26", "#c0392b"
out = []


def path(*segs):
    """Build a fine polyline from ('l', p, q) and ('a', c, r, a0, a1) segments (degrees, y down)."""
    pts = []
    for s in segs:
        if s[0] == "l":
            (x0, y0), (x1, y1) = s[1], s[2]
            n = max(2, int(math.hypot(x1 - x0, y1 - y0)))
            pts += [(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n) for i in range(n + 1)]
        else:
            (cx, cy), r, a0, a1 = s[1], s[2], s[3], s[4]
            n = max(2, int(abs(a1 - a0) / 180 * math.pi * r))
            pts += [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
                     cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    return pts


def cord(pts, pitch=11.0, rx=6.0, ry=3.4):
    """Texsolv: a chain of eyes along the polyline."""
    travelled, nxt = 0.0, 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        d = math.hypot(x1 - x0, y1 - y0)
        while d > 0 and nxt <= travelled + d:
            t = (nxt - travelled) / d
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            a = math.degrees(math.atan2(y1 - y0, x1 - x0))
            out.append(f'<g transform="translate({x:.1f},{y:.1f}) rotate({a:.1f})">'
                       f'<ellipse rx="{rx}" ry="{ry}" fill="{CORD}" stroke="{CORD_D}" stroke-width="1.5"/>'
                       f'<ellipse rx="{rx * 0.5:.1f}" ry="{ry * 0.35:.1f}" fill="{EYE}"/></g>')
            nxt += pitch
        travelled += d


def text(x, y, s, size=22, anchor="start", colour=TEXT, weight="normal", backed=False):
    if backed:   # white background so the text stays readable over the cords
        b = len(s) * size * 0.58
        x0 = {"start": x, "middle": x - b / 2, "end": x - b}[anchor]
        out.append(f'<rect x="{x0 - 6:.0f}" y="{y - size:.0f}" width="{b + 12:.0f}" height="{size * 1.35:.0f}" '
                   f'rx="5" fill="#ffffff" opacity="0.92"/>')
    out.append(f'<text x="{x}" y="{y}" font-family="DejaVu Sans, sans-serif" font-size="{size}" '
               f'text-anchor="{anchor}" fill="{colour}" font-weight="{weight}">{s}</text>')


def line(x0, y0, x1, y1, colour=TEXT, width=1.5, arrow=False):
    extra = ' marker-end="url(#arrow)"' if arrow else ""
    out.append(f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y1}" stroke="{colour}" stroke-width="{width}"{extra}/>')


def ring(x, y, r=13):
    out.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="{ACCENT}" stroke-width="2.5"/>')


# ---------------------------------------------------------------- background and panels
out.append(f'<rect width="{W}" height="{H}" fill="#f7f5f0"/>')
out.append('<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
           f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{TEXT}"/></marker></defs>')
for x, w in ((30, 840), (900, 670)):
    out.append(f'<rect x="{x}" y="30" width="{w}" height="870" rx="14" fill="#ffffff" stroke="#ddd6c8"/>')
text(60, 75, "Overview (front view of one roller)", 26, weight="bold")
text(930, 75, "Detail (side view)", 26, weight="bold")

# ---------------------------------------------------------------- overview
RY, RH = 170, 38           # roller: top and height
SY, SH = 520, 26           # apron bar
out.append(f'<rect x="70" y="{RY}" width="760" height="{RH}" rx="19" fill="{WOOD}" stroke="{WOOD_D}" stroke-width="2"/>')
out.append(f'<rect x="70" y="{RY + 6}" width="760" height="8" rx="4" fill="#d29e6c" opacity="0.6"/>')
out.append(f'<rect x="115" y="{SY}" width="670" height="{SH}" rx="5" fill="{BAR}" stroke="{BAR_D}" stroke-width="2"/>')
xs = [150 + i * 100 for i in range(7)]
for x in xs:
    cord(path(("l", (x, RY + RH + 2), (x, SY - 2))))                 # standing part
    cord(path(("l", (x, RY - 4), (x, RY + RH + 2))))                 # around the roller
    cord(path(("l", (x + 11, RY + RH + 2), (x + 11, RY + RH + 34))))  # end hanging down
    cord(path(("l", (x, SY - 2), (x, SY + SH + 4))))                 # around the bar
    cord(path(("l", (x + 11, SY - 2), (x + 11, SY - 34))))           # end pointing up
ring(xs[-1] + 6, RY + RH + 34, 15)
ring(xs[-1] + 6, SY - 34, 15)
text(70, RY - 30, f"cloth roller / warp roller (dowel Ø {round(g.DOWEL_D)} mm)", 22)
text(115, SY + SH + 45, "apron bar (laser cut, 6 mm)", 22)
text(185, 345, "Texsolv cord", 22, weight="bold", backed=True)
text(185, 375, "7 cords of about 70 cm per roller", 20, backed=True)
text(xs[-1] - 16, RY + RH + 72, "end through a loop", 20, "end", ACCENT, backed=True)
text(xs[-1] - 16, SY - 52, "end through a loop", 20, "end", ACCENT, backed=True)
# length dimension line
line(810, RY + RH, 810, SY, width=1.2)
line(800, RY + RH, 820, RY + RH, width=1.2)
line(800, SY, 820, SY, width=1.2)
text(825, (RY + RH + SY) / 2 - 10, "length", 18)
text(825, (RY + RH + SY) / 2 + 14, "adjustable", 18)
text(60, 690, "• Spread the 7 cords evenly across the width (about 10 cm apart).", 20)
text(60, 722, "• Same attachment on the cloth roller (front) and the warp roller (back).", 20)
text(60, 754, "• No knots: choose the length by passing the end through a different loop.", 20)
text(60, 786, "• Keep the apron bar straight: all cords the same length.", 20)

# ---------------------------------------------------------------- roller detail
cx, cy, r = 1110, 240, 62
out.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{WOOD}" stroke="{WOOD_D}" stroke-width="2.5"/>')
for rr in (44, 28, 12):
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{rr}" fill="none" stroke="#9c6a3c" stroke-width="1.2" opacity="0.6"/>')
R = r + 6
# end first, so the standing part lies on top where it passes through the loop
cord(path(("l", (cx - R, cy), (cx - R, cy + 40)), ("l", (cx - R, cy + 40), (cx + R, cy + 112)),
          ("l", (cx + R, cy + 112), (cx + R + 48, cy + 146))))
cord(path(("l", (cx + R, cy + 250), (cx + R, cy)), ("a", (cx, cy), R, 0, -180)))
ring(cx + R, cy + 112, 16)
text(cx + R + 30, cy + 98, "end through a", 20, colour=ACCENT)
text(cx + R + 30, cy + 122, "loop of the cord", 20, colour=ACCENT)
text(cx, cy - r - 30, "roller", 22, "middle")
line(cx + R, cy + 268, cx + R, cy + 350, width=1.5, arrow=True)
text(cx + R + 18, cy + 305, "the same cord, continuing", 18)
text(cx + R + 18, cy + 327, "to the apron bar", 18)

# ---------------------------------------------------------------- apron bar detail
sx, sy, sw, sh = 1050, 770, 110, 30
out.append(f'<rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" rx="4" fill="{BAR}" stroke="{BAR_D}" stroke-width="2.5"/>')
x_r, x_l = sx + sw + 6, sx - 6
cord(path(("l", (x_l, sy + sh / 2), (x_l, sy - 30)), ("l", (x_l, sy - 30), (x_r, sy - 100)),
          ("l", (x_r, sy - 100), (x_r + 46, sy - 134))))
cord(path(("l", (x_r, sy - 150), (x_r, sy + sh + 6)), ("a", (sx + sw / 2, sy + sh + 6), (sw + 12) / 2, 0, 180),
          ("l", (x_l, sy + sh + 6), (x_l, sy + sh / 2))))
ring(x_r, sy - 100, 16)
text(x_r + 58, sy - 112, "end through a", 20, colour=ACCENT)
text(x_r + 58, sy - 88, "loop of the cord", 20, colour=ACCENT)
text(sx - 30, sy + 24, "apron bar", 22, "end")
text(x_r + 30, sy - 40, "other loop =", 18)
text(x_r + 30, sy - 18, "cord shorter or longer", 18)

# ---------------------------------------------------------------- caption
text(W / 2, 950, "Attaching the aprons with Texsolv cord: wrap around the roller or bar and pass the end "
     "through one of the loops.", 22, "middle")

HERE = os.path.dirname(os.path.abspath(__file__))
svg = os.path.join(HERE, "aprons_texsolv.svg")
png = os.path.join(HERE, "aprons_texsolv.png")
with open(svg, "w") as f:
    f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">\n'
            + "\n".join(out) + "\n</svg>\n")
subprocess.run(["inkscape", svg, "--export-type=png", f"--export-filename={png}"], check=True,
               stderr=subprocess.DEVNULL)
os.remove(svg)
print("written:", png)
