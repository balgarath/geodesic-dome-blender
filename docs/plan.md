# Geodesic Dome Builder, implementation plan

Executor notes, read first:

- Project root: `E:\claude\geodesic-dome-blender`. All paths below are
  relative to it unless absolute.
- The full spec is `E:\claude\geodesic-dome-blender\docs\design.md`. Each
  task below names the spec sections it implements. Read those sections
  before coding the task.
- `E:\claude\geodesic-dome-blender\reference\verify_geometry.py` is the
  verified oracle: it already implements the icosahedron, Class I
  subdivision, Kruschke construction and extended leveling, and passes 130
  checks against the domerama reference JSONs (run
  `python reference\verify_geometry.py`; exit code 0). When a task says
  "port function X", copy it with minimal renames. Do not "improve" the
  math. Never edit files in `reference\`.
- Pure-core rule: nothing under `geodesic_dome\core\` may import bpy.
- No em-dashes or double hyphens in any user-facing string.
- Run `python -m pytest tests -q` after every task that touches core or
  tests; it must pass before moving on.
- Commit after each task: conventional commits (`feat: ...`, `test: ...`),
  concise, no Co-Authored-By trailer.

Task order: T1 -> T2 -> T3 -> T4 -> T5 -> T6, then T7, T8 in any order;
T9 -> T10 -> T11 after T8; T12 last. (T7 is independent of T8-T11.)

---

## T1. Repo init and scaffold

Sections: design.md 8, 10.1.

1. In `E:\claude\geodesic-dome-blender`: `git init -b main`.
2. Create `.gitignore`:
   ```
   __pycache__/
   *.pyc
   dist/
   .pytest_cache/
   ```
3. Create directories: `geodesic_dome\core\data`, `tests`, `dist` (empty,
   ignored).
4. Create `geodesic_dome\blender_manifest.toml` exactly as in design.md
   10.1.
5. Copy these three files byte-identical from `reference\` into
   `geodesic_dome\core\data\`:
   `domerama_chord_factors.json`, `domerama_kruschke_chord_factors.json`,
   `kruschke_extended_reference.json`.
6. Create empty-but-importable modules: `geodesic_dome\__init__.py` (stub
   `register()`/`unregister()` doing nothing yet), `geodesic_dome\core\__init__.py`,
   and `tests\conftest.py`:
   ```python
   import sys, os
   sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "geodesic_dome"))
   ```
7. Create `tests\test_data_sync.py`: for each of the three JSON filenames,
   assert the bytes of `reference\<name>` equal
   `geodesic_dome\core\data\<name>`.
8. Create `tests\test_no_bpy.py`: walk `geodesic_dome\core\` recursively,
   read every `.py`, assert the substring `import bpy` appears in none.
9. First commit: all of the above plus the existing `reference\` and
   `docs\` contents. `chore: scaffold extension, reference data, docs`.

Accept: `python -m pytest tests -q` passes (2 test files), `git log` shows
one commit, `git status` clean.

## T2. core/icosa.py: icosahedron + Class I subdivision

Sections: design.md 4.1, 4.2. Port from
`reference\verify_geometry.py`: functions `norm`, `dist`, `lerp`,
`icosahedron_vertex_up`, class `Mesh`, `subdivide_class1`. Keep the row
formula, welding (round to 9 decimals), `on_edge`, `is_ppt`, `ppt_id`
bookkeeping exactly.

Also add `hub_neighbors(mesh)` (port as-is) returning
`{vertex_id: icosa_hub_vertex_id}` and asserting uniqueness.

Create `tests\test_icosa.py`:
- for n in 1..8: full sphere has `10*n*n+2` verts, `30*n*n` edges,
  `20*n*n` faces; every vertex unit length within 1e-12; rows range 0..3n;
  row 0 and 3n have exactly 1 vertex each.
- n=3: `hub_neighbors` has 60 entries, 5 per hub.

Accept: pytest passes. Commit `feat: icosahedron and class I subdivision core`.

## T3. core/truncate.py: fractions, aliases, dome extraction

Sections: design.md 4.3.

API:
```python
def dome_edges(mesh, k) -> list[tuple[int,int]]      # port from verify script
def dome_faces(mesh, k) -> list[tuple[int,int,int]]  # faces with max row <= k
def base_ring(mesh, k, edges) -> list[int]           # row-k verts used by kept edges
def fraction_alias(k, denom) -> str | None
def base_level_info(mesh_positions, base_verts) -> tuple[bool, float]  # (level, z_spread), level = spread < 1e-9
```
`fraction_alias`: return the reduced fraction as a string when k/denom
reduces (gcd > 1), e.g. (9,18) -> "1/2", (6,24) -> "1/4", (18,24) -> "3/4";
additionally the legacy names: (4,9) -> "3/8", (5,9) -> "5/8",
(7,15) -> "3/8", (8,15) -> "5/8". Legacy name wins when both exist.
Return None when k == denom (full sphere) or no alias.

Create `tests\test_truncate.py`:
- 3V k=4: 120 edges; 3V k=5: 165; 4V k=6: 250; 5V k=7: 350; 5V k=8: 425;
  6V k=9: 555; 7V k=10: 700; 8V k=12: 980 (all from domerama, already
  verified).
- aliases: the six examples above plus (3,6) -> "1/2", (12,24) -> "1/2".
- Class I base level: (2V, k=3) level True; (3V, k=4) level False.

Accept: pytest passes. Commit `feat: truncation, fractions, aliases`.

## T4. core/kruschke.py: Kruschke and extended constructions

Sections: design.md 5.2, 5.4. Port from `reference\verify_geometry.py`:
`interior_orbit_zs`, `apply_hub_slide`, `solve_kruschke_m` (closed-form
quadratic; keep the assertion structure), `slide_on_arc_to_z`,
`kruschke_positions(mesh, n, extended=False)` including the
`r == 2*n - 1 -> zr = -z_target` branch.

API: `kruschke_positions` returns `(positions, m)`. Frequencies: n=3,4 use
`extended=False`; n=5,6 `extended=True`. Raise `ValueError("Kruschke needs frequency 3 to 6")`
otherwise.

Create `tests\test_kruschke.py` (constants are authoritative, from the
verified run):
- m(3V) == 0.9442890009767209 within 1e-12; m(4V) == 0.8761509568376010
  within 1e-12.
- Against `core/data/domerama_kruschke_chord_factors.json`: for each of the
  4 domes (3V k=4, 3V k=5, 4V k=5, 4V k=7), group dome edge lengths
  (chain-merge gap < 1e-7), then assert: number of types equals the JSON
  strut rows; per row ascending, |cf_generated - cf_published| < 6e-6 and
  count equal; height factor `1 - base_z` within 1e-5 of `height_factor`.
- Base ring z spread < 1e-12 for all four.
- Hub census: 3V k=4 {6:25, 5:6, 4:15}; 4V k=7 {6:85, 5:6, 4:20};
  4V k=5 {6:45, 5:6, 4:20} with a comment that domerama's published 85 for
  5/12 is a known site copy-paste bug.

Create `tests\test_extended.py`:
- For n=5 and n=6: all verts unit within 1e-12; 60 hub spokes equal within
  1e-12; every band row n<r<2n level within 1e-12.
- Against `core/data/kruschke_extended_reference.json`: for every dome
  entry, per-type chord factors within 1e-9 and counts exact; `m` within
  1e-9.

Accept: pytest passes. Commit `feat: kruschke construction, exact and extended`.

## T5. core/classify.py + core/build.py: grouping, labels, report, facade

Sections: design.md 4.4, 4.5, 9 (copy the dataclass definitions from 9
verbatim), 5.1 (authoritative 4V table), 5.3 (domerama columns).

classify.py:
- `group_edges(edges, positions, merge_tolerance)` -> `(edge_type list,
  groups)` where grouping is two-stage: chain-merge < 1e-7, then merge
  adjacent groups with mean gap < merge_tolerance recording `sub_spread`.
- `label(i)`: A..Z, AA, AB, ...
- `hub_valences(edges)` (port), `face_types(faces, edge_type)` by sorted
  edge-type triple.
- `domerama_columns(method, frequency, k)`: for known variants, map our
  ascending types to domerama letters and published CFs by nearest CF from
  the bundled JSONs (match threshold 2e-4; the 7V/8V merged rows map two of
  our types to one site letter). Returns per-type `(label|None, cf|None)`.

build.py:
- `build_dome(...)` per the design.md 9 signature: subdivide, method
  positions (Class I: standard; Kruschke/domerama: kruschke_positions;
  Custom: task T7 hook, until then raise ValueError), truncate, classify,
  assemble `DomeGeometry` + `DomeReport` including notes:
  - not-level note with mm mismatch (design.md 4.3 exact strings),
  - Class I odd-frequency note,
  - even-frequency 1/2 Kruschke note (design.md 5.4),
  - extended-method note for 5V/6V:
    `"5V and 6V Kruschke are an extension of the 1972 method. See the manual."`
- `valid_frequencies`, `valid_fractions` (level flags computed by actually
  building or via cached geometry; keep it simple: build the positions once
  per (method, n) and evaluate each k), `expected_custom_count`,
  `class1_defaults`.
- `KRUSCHKE_DOMERAMA`: restrict to (3, k=4), (3, k=5), (4, k=5), (4, k=7),
  else ValueError with message
  `"Domerama publishes Kruschke tables for 3V 4/9, 3V 5/9, 4V 5/12 and 4V 7/12 only. Use Kruschke (traditional) for other sizes."`

Create `tests\test_classify.py` and `tests\test_class1.py`:
- test_class1: replicate the Class I comparison of the verify script
  against `core/data/domerama_chord_factors.json` for the truncation map
  {1V:2/3->k2, 2V:k3, 3V:k4 and k5, 4V:k6, 5V:k7 and k8, 6V:k9, 7V:k10,
  8V:k12}; tolerance per value = 10^(-displayed decimals) + 5e-6; counts
  exact except 7V J = our 0.17585131 x60 + 0.17589689 x10 and 8V N = our
  0.15636158 x60 + 0.15638647 x30 (assert the split values explicitly);
  hub censuses where published; assert the authoritative 4V table constants
  from design.md 5.1.
- test_classify: labels ascending; 8V full-precision grouping has 20 types,
  with merge_tolerance=1e-4 the reported table has 19 and the merged row
  has sub_spread > 0; build_dome('KRUSCHKE', 5, 7) returns 22 types at
  merge_tolerance=1e-7 as in the extended JSON.

Accept: pytest passes. Commit `feat: classification, report, build facade`.

## T6. Wire the oracle into CI habit

Add `tests\test_oracle_script.py`: run
`[sys.executable, "reference/verify_geometry.py"]` with cwd = project root
via subprocess, assert returncode 0 (skip with reason if it takes > 120 s;
it takes about 15 s). This keeps the independent implementation honest
against the same data the core is tested on.

Accept: pytest passes. Commit `test: run reference oracle in pytest`.

## T7. core/custom.py: custom chord table

Sections: design.md 7.

```python
def parse_table(text: str) -> list[float]        # commas, spaces, newlines; ValueError on junk
def solve_custom(mesh, base_positions, k, targets: list[float],
                 merge_tolerance=1e-7, iters=400, tol=1e-9
                 ) -> tuple[list[pos], float]    # (positions, residual)
```
`base_positions` come from the chosen `custom_base` ("CLASS_I" for 1V-8V or
"KRUSCHKE" for 3V-6V; an operator enum, design.md 7). Classify the base
dome edges at those positions (chain-merge 1e-7) to get class count N and
per-edge target = `targets[class_index]`; validate `len(targets) == N`
(ValueError listing expected N), all in (0, 2). Relaxation starts from
`base_positions`.
Relaxation loop over dome edges (edges with row <= k only): move endpoints
half the error each along the edge direction, re-normalize to unit sphere,
apex (0,0,1) pinned. Stop at `iters` or max error < `tol`. Return final
positions and worst residual.

Hook into `build_dome(method='CUSTOM', ...)`: report.custom_residual set;
warning note added when residual > 1e-4 (design.md 7 exact string with X
computed at radius 1 in the note template; the Blender layer re-renders mm
at chosen radius).

`tests\test_custom.py`:
- Feeding `class1_defaults(3, 4)` reproduces Class I: residual < 1e-9 and
  chord factors match Class I within 1e-9.
- Feeding the four Kruschke 3V factors [0.32970646, 0.38229019,
  0.42148879, 0.44105636] with custom_base="CLASS_I" (3 classes) raises
  ValueError on count mismatch; with custom_base="KRUSCHKE" it converges
  with residual < 1e-9 and the base ring stays level within 1e-9.
- Feeding perturbed Class I 3V values (A*1.05) converges with residual
  < 1e-3 and produces 3 types.

Accept: pytest passes. Commit `feat: custom chord table solver`.

## T8. Blender operator

Sections: design.md 10.2, plus 10.3 attribute names. Files:
`geodesic_dome\operators.py`, update `geodesic_dome\__init__.py` to
register the operator and the Add > Mesh menu entry (icon 'MESH_ICOSPHERE',
menu text "Geodesic Dome").

Implementation notes:
- Import core lazily inside functions is not needed; `from . import core`
  is fine (core never imports bpy).
- Dynamic EnumProperty items callbacks must return tuples cached in a
  module-level dict keyed by (method, frequency) to avoid the Blender
  string-lifetime bug.
- On method/frequency change the fraction enum repopulates; if the previous
  selection is invalid, default to the first level-base item, else first.
- execute(): try/except ValueError -> `self.report({'ERROR'}, str(e))`,
  return {'CANCELLED'}. Success: build mesh `Geodesic Dome` via
  `mesh.from_pydata(verts, edges, faces)`, `mesh.validate()`; scale by
  radius; orientation offset per design.md 10.2; set attributes:
  `strut_type` INT/EDGE, `strut_color` FLOAT_COLOR/EDGE, `panel_type`
  INT/FACE, `row` INT/POINT; object custom property `geodome_report` =
  JSON string (dataclasses.asdict + radius + version). Color formula:
  design.md 10.3.
- `add_base_face`: when base level and not full sphere, append the base
  ring n-gon (ordered by angle around Z).

Manual accept (needs Blender 4.2+, no automated test): described in T11
smoke checklist. Automated accept: `python -m pytest tests -q` still passes
and `python -c "import ast,sys; ast.parse(open('geodesic_dome/operators.py').read())"`
succeeds. Commit `feat: add mesh operator`.

## T9. Strut visualization object

Sections: design.md 10.4. In `operators.py` (helper module ok):
`create_strut_object(context, frame_obj, geometry, radius, thickness)`:
triangular prism per edge (6 verts, 8 tris including caps... caps optional,
skip caps: 6 verts, 6 side tris per edge is enough visually; choose skip),
material slot per strut type, `material_index` per face, materials with
`diffuse_color` and node-based base color + emission 0.05, viewport
display color set. Parent to frame object, name `<frame> Struts`.

Accept: syntax-clean, pytest passes, verified in T11 smoke test.
Commit `feat: strut prism visualization with per-type materials`.

## T10. N-panel and CSV export

Sections: design.md 10.5, 10.6. File `geodesic_dome\panel.py`; register in
`__init__.py`.

- `VIEW3D_PT_geodome_report`, sidebar category "Geodome"; `poll`: active
  object has `geodome_report`.
- Render summary, strut table (use `layout.box()` + aligned columns via
  `split(factor=...)`; Blender UI tables are rough, keep it readable, one
  row per type), hubs, notes.
- `geodome.export_csv` operator: `bpy.props.StringProperty(subtype='FILE_PATH')`,
  `invoke` opens file browser with default filename
  `dome_<method>_<freq>V_<k>-<denom>.csv`; write the format from design.md
  10.6 exactly (metadata `#` lines, strut rows, hub rows). Lengths =
  chord_factor * radius.
- `geodome.copy_table` operator: same rows tab-separated to
  `context.window_manager.clipboard`.
- CSV row assembly must live in a pure helper `core\report_csv.py`
  (`def csv_lines(report_dict: dict, radius: float, version: str) -> list[str]`)
  so it is pytest-testable. Add `tests\test_csv.py`: build 3V Kruschke k=5
  report, render lines, assert header fields, row count = types + hubs +
  metadata, and the A-row contains `0.32970646` and count 30.

Accept: pytest passes. Commit `feat: report panel and csv export`.

## T11. Build script, README, smoke test

Sections: design.md 12.

- `build.py` at repo root: reads version from
  `geodesic_dome\blender_manifest.toml` (simple regex is fine), zips the
  CONTENTS of `geodesic_dome\` (manifest at zip root) to
  `dist\geodesic_dome_builder-<version>.zip`, excluding `__pycache__`.
  Print the output path.
- `README.md`: what it is, install steps (Preferences > Get Extensions >
  Install from Disk), method summary table, how to run tests, how to
  rebuild the zip, pointer to docs\design.md. Follow the copy rules (no
  em-dashes, grounded tone).
- Manual smoke checklist, append to README under "Smoke test" and execute
  it if Blender is available (else leave for Ralph):
  1. Install zip in Blender 4.2+.
  2. Add > Mesh > Geodesic Dome. Default creates Kruschke 3V 5/9, radius
     3 m, with colored strut prisms.
  3. Redo panel: switch method to Class I, frequency 5V, fraction 7/15:
     warning text about non-level base appears; mesh rebuilds.
  4. N-panel Geodome tab shows 9 strut rows for Class I 5V 7/15; Export
     CSV writes a file that opens in a spreadsheet.
  5. Kruschke (Domerama tables) 4V 5/12 shows domerama column values.
  6. Custom: 3V k=4 with table "0.36 0.41 0.42" builds and reports
     residual; with two values errors cleanly.

Accept: `python build.py` produces the zip; README present.
Commit `feat: build script and readme`.

## T12. Wrap up

1. `python -m pytest tests -q` green; `python reference\verify_geometry.py`
   exit 0.
2. `python build.py` fresh zip.
3. Update `docs\todos.md`: mark done items, carry over: hub connector
   visualization, cut-list CSV, possible "Leveled Class I" method, Blender
   automated tests via `blender --background --python`.
4. Final commit `chore: v0.1.0` and tag `v0.1.0`.

Accept: clean `git status`, tagged release, zip in `dist\`.
