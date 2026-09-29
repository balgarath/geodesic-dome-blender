# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Ralph Edge / Geovisual Creations
"""Generate docs/logo/logo.svg from the extension's own geometry.

A 3V 5/9 Kruschke dome (the default), seen from slightly above, with struts
colored in the shop palette. Run from the repo root:
    python docs/logo/make_logo.py
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "geovisual_dome_tools"))

from core.build import build_dome  # noqa: E402

PALETTE = ["#ff2a2a", "#2f6bff", "#18d04a", "#ffd21a", "#9b3dff", "#e6e8ef"]
BG = "#11131a"
SIZE = 512
TILT = math.radians(18)   # look down onto the dome
SPIN = math.radians(9)    # turn so no strut sits dead-on to the viewer


def project(v, z0):
    x, y, z = v
    z -= z0
    x, y = (x * math.cos(SPIN) - y * math.sin(SPIN),
            x * math.sin(SPIN) + y * math.cos(SPIN))
    # rotate about X so the camera looks slightly down
    y2 = y * math.cos(TILT) - z * math.sin(TILT)
    z2 = y * math.sin(TILT) + z * math.cos(TILT)
    return x, z2, y2      # screen x, screen up, depth (negative = toward viewer)


def main():
    geo = build_dome("KRUSCHKE", 3, 5)
    z0 = min(v[2] for v in geo.verts)
    pts = [project(v, z0) for v in geo.verts]

    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    scale = (SIZE * 0.66) / max(w, h)
    cx = SIZE / 2 - (min(xs) + w / 2) * scale
    cy = SIZE / 2 + (min(ys) + h / 2) * scale + SIZE * 0.02

    def sx(p):
        return cx + p[0] * scale, cy - p[1] * scale

    back, front = [], []
    for (a, b), t in zip(geo.edges, geo.edge_type):
        depth = (pts[a][2] + pts[b][2]) / 2
        (x1, y1), (x2, y2) = sx(pts[a]), sx(pts[b])
        line = (x1, y1, x2, y2, PALETTE[t % len(PALETTE)])
        (front if depth <= 0.02 else back).append(line)

    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" '
        'width="%d" height="%d">' % (SIZE, SIZE, SIZE, SIZE),
        '<title>Geovisual Dome Tools</title>',
        '<defs><filter id="glow" x="-20%" y="-20%" width="140%" height="140%">'
        '<feGaussianBlur stdDeviation="4" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>'
        '</filter></defs>',
        '<circle cx="%g" cy="%g" r="%g" fill="%s"/>' % (SIZE / 2, SIZE / 2, SIZE / 2, BG),
    ]
    base_y = max(sx(p)[1] for p in pts)
    out.append('<line x1="%g" y1="%.1f" x2="%g" y2="%.1f" stroke="#4fd1c5" '
               'stroke-opacity="0.35" stroke-width="3" stroke-linecap="round"/>'
               % (SIZE * 0.14, base_y + 14, SIZE * 0.86, base_y + 14))
    out.append('<g stroke-linecap="round" stroke-width="3" opacity="0.22">')
    for x1, y1, x2, y2, c in back:
        out.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s"/>'
                   % (x1, y1, x2, y2, c))
    out.append('</g><g stroke-linecap="round" stroke-width="6" filter="url(#glow)">')
    for x1, y1, x2, y2, c in front:
        out.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s"/>'
                   % (x1, y1, x2, y2, c))
    out.append('</g></svg>')

    path = os.path.join(HERE, "logo.svg")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print("wrote", path, "front", len(front), "back", len(back))


if __name__ == "__main__":
    main()
