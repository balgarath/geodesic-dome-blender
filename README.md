# Geodesic Dome Builder

A Blender 4.2+ extension that adds geodesic dome mesh frames: Add > Mesh >
Geodesic Dome. Supports Class I Method 1 subdivision (1V to 8V), the 1972
Kruschke flat base construction (3V and 4V), a Kruschke variant restricted
to the four domes domerama.com publishes, and a custom chord factor table
solved by relaxation. Every strut is tagged with its type, and an N-panel
reports chord factors, lengths, counts, hub valences, and can export a CSV.

The math is pure Python (no bpy, no numpy) and is checked against
domerama.com's published chord charts. See `docs/design.md` for the full
spec and provenance, and `reference/verify_geometry.py` for the independent
numerical oracle every value is checked against.

## Install

1. Build the zip (see below), or use a prebuilt one from `dist/`.
2. In Blender: Edit > Preferences > Get Extensions > the arrow menu in the
   top right corner > Install from Disk. Pick the zip.
3. The operator appears under Add > Mesh > Geodesic Dome.

## Methods

| Name in the UI | Frequencies | What it is |
|---|---|---|
| Kruschke | 3V, 4V, level-base fractions only | The 1972 Kruschke flat base construction. The report shows domerama.com's published chord factor next to ours for the four fractions domerama documents (3V 4/9, 3V 5/9, 4V 5/12, 4V 7/12); blank for the rest |
| Icosa Class I Method 1 | 1V to 8V | Standard equal chord subdivision projected to the sphere |
| Custom chord table | 1V to 8V (or 3V to 6V on the Kruschke base) | Builds a dome from chord factors you supply |

The 5V and 6V extension of the Kruschke construction exists in the pure
Python core (with its own tests) but is not reachable from the Blender UI.
There is no published 5V/6V Kruschke reference to check it against; see
`docs/design.md` section 5.4 and 14 for the reasoning.

Defaults: Kruschke, 3V, fraction 5/9, radius 3 m.

## Running the tests

Pure Python, no Blender required:

```
python -m pip install pytest
python -m pytest tests -q
```

`tests/test_no_bpy.py` guards the purity rule: nothing under
`geodesic_dome/core/` may import bpy. `tests/test_oracle_script.py` runs
the independent reference oracle (`reference/verify_geometry.py`) as part
of the suite.

## Building the zip

```
python build.py
```

Writes `dist/geodesic_dome_builder-<version>.zip`, contents of
`geodesic_dome/` at the zip root, `__pycache__` excluded.

## Smoke test

Manual checklist (needs Blender 4.2+; see docs/todos.md for automating
this):

1. Install the zip in Blender 4.2+.
2. Add > Mesh > Geodesic Dome. Default creates Kruschke 3V 5/9, radius 3 m,
   with colored strut prisms.
3. In the redo panel, switch method to Icosa Class I Method 1, frequency
   5V, fraction 7/15: a not-level-base warning note appears and the mesh
   rebuilds.
4. The N-panel Geodome tab shows 9 strut rows for Class I 5V 7/15. Export
   CSV writes a file that opens cleanly in a spreadsheet.
5. Kruschke, 4V, fraction 5/12 shows domerama's published column values
   next to ours in the report.
6. Custom chord table: 3V k=4 with table "0.36 0.41 0.42" builds and
   reports a residual; feeding two values instead of three errors cleanly.

More detail: `docs/design.md`, `docs/plan.md`.
