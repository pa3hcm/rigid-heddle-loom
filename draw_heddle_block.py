#!/usr/bin/env python3
"""Draws the heddle block with all heddle positions to heddle_block_positions.png (requires inkscape)."""
import os
import subprocess

import generate_laser as g

HERE = os.path.dirname(os.path.abspath(__file__))
S = 4.0                                        # pixels per mm
X0, Y0 = g.BLOCK_X - 25, g.EAR_UP + 45         # top left of the view in panel coordinates
W, H = int((g.BLOCK_X1 - X0 + 100) * S), int((Y0 - g.BLOCK_Y + 30) * S)
EAR_T = g.HEDDLE_T                              # thickness of the ear
HEDDLE1, HEDDLE2 = "#c96a3a", "#2f7f86"        # ear colour of heddle 1 and heddle 2


def p(x, y):
    return (x - X0) * S, (Y0 - y) * S


def poly(pts, fill, stroke="#5b4630", extra=""):
    d = " ".join(f"{a:.1f},{b:.1f}" for a, b in (p(*q) for q in pts))
    return f'<polygon points="{d}" fill="{fill}" stroke="{stroke}" stroke-width="2" {extra}/>'


def text(x, y, s, size=17, colour="#2d2a26", anchor="start"):
    a, b = p(x, y)
    return (f'<text x="{a:.1f}" y="{b:.1f}" font-family="DejaVu Sans, sans-serif" font-size="{size}" '
            f'fill="{colour}" text-anchor="{anchor}">{s}</text>')


def ear(x_mid, bottom, fill, extra=""):
    return poly([(x_mid - EAR_T / 2, bottom), (x_mid + EAR_T / 2, bottom), (x_mid + EAR_T / 2, bottom + g.EAR_H),
                 (x_mid - EAR_T / 2, bottom + g.EAR_H)], fill, "#7a3d1c", extra)


out = [f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
       '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
       'orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#c0392b"/></marker>'
       '<marker id="arrowb" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
       'orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#2d6a8a"/></marker></defs>']
# side panel (behind the block) and heddle block
out.append(poly([(X0, g.BLOCK_Y), (g.BLOCK_X1 + 40, g.BLOCK_Y), (g.BLOCK_X1 + 40, g.PANEL_TOP), (X0, g.PANEL_TOP)],
                "#e9dcc6", "#b59b74"))
out.append(text(X0 + 4, g.PANEL_TOP - 14, "side panel", 16, "#8a7556"))
out.append(poly(g.heddle_block_outline(), "#d8b47e"))
for x, y in g.BLOCK_HOLES:
    a, b = p(x, y)
    out.append(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="{2.75 * S:.1f}" fill="#fff" stroke="#5b4630" stroke-width="2"/>')

# down positions: entry (dashed) and locked under the lip, for heddle 1 and heddle 2
for nr, x_down, colour in ((1, g.X_DOWN1, HEDDLE1), (2, g.X_DOWN2, HEDDLE2)):
    xl, bl = g.POSITIONS[f"down {nr}"]
    x_entry = x_down + g.NOTCH_W / 2
    out.append(ear(x_entry, bl + 40, "none", 'stroke-dasharray="6,4"'))
    out.append(ear(x_entry, bl, "none", 'stroke-dasharray="6,4"'))
    a0, b0 = p(x_entry, bl + 38)
    a1, b1 = p(x_entry, bl + g.EAR_H + 3)
    out.append(f'<line x1="{a0:.1f}" y1="{b0:.1f}" x2="{a1:.1f}" y2="{b1:.1f}" stroke="#c0392b" stroke-width="2.5" marker-end="url(#arrow)"/>')
    a0, b0 = p(x_entry + 3, bl - 5)
    a1, b1 = p(xl + 2, bl - 5)
    out.append(f'<line x1="{a0:.1f}" y1="{b0:.1f}" x2="{a1:.1f}" y2="{b1:.1f}" stroke="#c0392b" stroke-width="2.5" marker-end="url(#arrow)"/>')
    out.append(ear(xl, bl, colour))
    out.append(text(x_down - 2, bl - 16, "1. in  2. slide out", 14, "#c0392b"))
    # pull of the warp in the down position
    a0, b0 = p(xl, bl + g.EAR_H - 4)
    a1, b1 = p(xl, bl + g.EAR_H + 22)
    out.append(f'<line x1="{a0:.1f}" y1="{b0:.1f}" x2="{a1:.1f}" y2="{b1:.1f}" stroke="#2d6a8a" stroke-width="2.5" '
               f'marker-end="url(#arrowb)" opacity="0.8"/>')
    x, b = g.POSITIONS[f"neutral {nr}"]
    out.append(ear(x, b, colour, 'opacity="0.35"'))
    x, b = g.POSITIONS[f"up {nr}"]
    out.append(ear(x, b, colour, 'opacity="0.35"'))
    out.append(text(x_down + 8, g.BLOCK_Y + 6, f"heddle {nr}", 18, colour, "middle"))

# labels on the right
lx = g.BLOCK_X1 + 12
out.append(text(lx, g.EAR_UP + 4, "up: wide notch for one", 16))
out.append(text(lx, g.EAR_UP - 2.5, "or both heddles", 16))
out.append(text(lx, g.EAR_NEUTRAL + 4, "neutral: a notch of", 16))
out.append(text(lx, g.EAR_NEUTRAL - 2.5, "its own per heddle", 16))
out.append(text(lx, g.EAR_DOWN + 4, "down: ear under the lip,", 16, "#c0392b"))
out.append(text(lx, g.EAR_DOWN - 2.5, "the lip holds the heddle down", 16, "#c0392b"))
out.append(text(lx, g.EAR_DOWN - 9, "(blue arrow = pull of the warp)", 14, "#2d6a8a"))
out.append(text(lx, g.BLOCK_Y + 30, "orange = heddle 1 (front)", 16, HEDDLE1))
out.append(text(lx, g.BLOCK_Y + 23.5, "teal = heddle 2 (back)", 16, HEDDLE2))
out.append(text(lx, g.BLOCK_Y + 17, "with one heddle: heddle 1 only", 16))
out.append(text(X0 + 4, Y0 - 8, "Symmetric heddle block (side view, front on the left) with the ears of two heddles in all positions",
                18, "#2d2a26"))

svg = os.path.join(HERE, "heddle_block_positions.svg")
with open(svg, "w") as f:
    f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            + "\n".join(out) + "</svg>")
png = os.path.join(HERE, "heddle_block_positions.png")
subprocess.run(["inkscape", svg, "--export-type=png", f"--export-filename={png}"], check=True,
               stderr=subprocess.DEVNULL)
os.remove(svg)
print("written:", png)
