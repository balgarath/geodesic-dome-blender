# Geodesic Dome Builder, Blender extension. Design and math spec

Status: verified design. Every number in this spec was checked numerically by
`reference\verify_geometry.py` (run it: `python reference\verify_geometry.py`,
exit 0 = all 130 checks pass, full log in `reference\verify_output.txt`).
Implementation plan: `docs\plan.md`.

Target: Blender 4.2+ extension (blender_manifest.toml format, no bl_info).
Geometry core is pure Python (no bpy), unit-testable with plain pytest.

---

## 1. What it does

Add > Mesh > Geodesic Dome. Generates an icosahedron-based geodesic dome
frame (verts, edges, faces) with a selectable calculation method, frequency,
truncation fraction and radius. Tags every edge with its strut type (A, B,
C...), reports chord factors, strut lengths, counts and hub valences in an
N-panel with CSV export, and optionally builds a colored strut-prism object
so strut types are visually distinct.

## 2. Methods (the core decision)

Three methods in the enum. Rationale and provenance below.

| id | UI name | Frequencies | What it is |
|---|---|---|---|
| `CLASS_I` | Icosa Class I Method 1 | 1V to 8V | Standard equal-chord subdivision, projected to the sphere. Matches domerama.com chord charts. |
| `KRUSCHKE` | Kruschke | 3V, 4V; UI offers level-base fractions only | The 1972 Kruschke flat-base construction (exact algorithm below). The report shows domerama.com's published chord factor next to ours whenever the built dome matches one of the four domes domerama publishes (3V 4/9, 3V 5/9, 4V 5/12, 4V 7/12); the column is blank otherwise. |
| `CUSTOM` | Custom chord table | 1V to 8V | User supplies one chord factor per strut class of the chosen Class I topology; geometry is produced by an edge-length relaxation solve (see 7). |

**Revision (2026-09-28):** the original design shipped two Kruschke enum
entries, `KRUSCHKE` and `KRUSCHKE_DOMERAMA`, on the theory that Ralph wanted
one category that reproduces domerama's published numbers verbatim and a
separate category that is the method itself at any supported frequency.
Ralph corrected this mid-build: the geometry is identical at 3V/4V, so two
menu entries is redundant. There is now a single `KRUSCHKE` method; the
domerama cross-check lives in the strut report as a "domerama" column that
is populated whenever the generated dome matches a published domerama
variant (by chord factor, within the 2e-4 match threshold in 4.4) and blank
otherwise. The UI's fraction dropdown for Kruschke is filtered to
level-base fractions only, since a flat-base method with a non-level base
is not useful to build from; this still includes domerama's 4/9, 5/9, 5/12
and 7/12 alongside the other level fractions (e.g. 3V 1/9, 8/9) the
construction supports. Verified result behind the cross-check: the exact
construction reproduces every domerama Kruschke chord factor to within
2.7e-6 (their own rounding), every count, every height factor.

### Rejected alternatives

- Deriving Kruschke from chain/lesser-circle planarity constraints: the
  closed strut loops are not planar circles in the real 3V/4V Kruschke
  geometry (verified numerically while reverse-engineering); the folklore
  "disk" description is a visualization, not the generative rule.
- Equal-arc division of icosa edges, meridian-slide leveling, "keep interior
  points and slide edge points" and several other candidate rules: each was
  tested against the measured chord factors and failed by 0.5 to 3 percent.
  The hub-slide construction (5.3) matches to full precision.
- Building the domerama-documented variants directly from the published
  rounded lengths: rejected; rounded lengths are not mutually consistent to
  better than 1e-6 and do not define vertex positions. Report shows them
  instead, next to our full-precision values.
- A separate "Leveled Class I" method (slide only the base row): dropped
  from v1 scope; noted in docs/todos.md as a future idea.
- Two separate Kruschke enum entries (`KRUSCHKE` / `KRUSCHKE_DOMERAMA`):
  shipped initially, then merged into one per Ralph's correction above.

## 3. Provenance of the Kruschke algorithm

- David Kruschke, "Dome Cookbook of Geodesic Geometry" (1972/1975) derives
  flat-base chord factors for 2v, 3v, 4v icosa via spherical trig (per Gerry
  Toomey, geodesichelp Google Group, thread "Fuller-Kruschke method:
  description, equations & calcs for 3v icosa"). Toomey's independent
  derivation "results in the same chord factors".
- domerama.com publishes the resulting chord factors (extracted from their
  calculator JavaScript: `reference\domerama_kruschke_chord_factors.json`).
- acidome.ru/lab/calc (bundle inspected 2026-09-28) implements Kruschke as:
  standard Class I subdivision, then every vertex S adjacent to an
  icosahedron vertex E is replaced by `normalize((1-m)*E + m*S)` with one
  constant m per frequency; their 3V constant 0.9442890204731844 was found
  by bisecting against a 7-digit spoke target. Our construction derives m
  exactly from the leveling condition and agrees with their constant to
  2e-8 and with all domerama values to their rounding.
- Toomey (geodesichelp, "Lesser Circle Domes?"): at 6V "the 7/18th and
  11/18ths cut-off points refuse to cooperate" - consistent with our finding
  that the one-parameter construction levels the base rows only for 3V/4V
  (see 5.4), which is why domerama and acidome offer Kruschke for 3V/4V only.

## 4. Shared geometry foundation (pure core)

All math on the unit sphere (radius 1). Chord factor = strut length at
radius 1. Bend angle (domerama's "angle") = asin(chord_factor / 2), degrees.
Final mesh is scaled by the user radius.

### 4.1 Icosahedron, vertex-up

Unit circumradius, apex at +Z ("vertex-zenith"):

- apex `(0, 0, 1)`
- upper ring, k = 0..4: `(r*cos(72k deg), r*sin(72k deg), z)` with
  `z = 1/sqrt(5)`, `r = 2/sqrt(5)`
- lower ring, k = 0..4: longitude `72k + 36` deg, z = `-1/sqrt(5)`
- nadir `(0, 0, -1)`

20 faces as in `reference\verify_geometry.py::icosahedron_vertex_up` (copy
it verbatim; it carries a per-vertex `tier` 0/1/2/3 used for row indexing).

### 4.2 Class I Method 1 subdivision

For frequency n, each icosa face (A,B,C) gets barycentric points
`(i*A + j*B + k*C)/n`, i+j+k = n, normalized to the sphere (equal chords on
the planar face, then projected). Points are welded across faces by rounding
coordinates to 9 decimals.

Vertex row index (0 at apex to 3n at nadir), computed per face from corner
tiers: `row = (i*tier(A) + j*tier(B) + k*tier(C)) * n / n` (always an exact
integer; assert it). Each vertex also records:

- `is_ppt` : it is one of the 12 icosahedron vertices ("hub")
- `on_edge`: the icosa vertex pair whose edge chord it subdivides, or None
  (interior of a face)

Faces: the standard n^2 triangulation per icosa face. Edges derived from
faces. Full sphere invariants: 10n^2+2 verts, 30n^2 edges, 20n^2 faces.

Reference implementation: `reference\verify_geometry.py::subdivide_class1`.
Port it as-is into the core.

### 4.3 Truncation semantics

A fraction is `k / 3n`: keep triangle rows 1..k from the apex (a face is
kept iff max vertex row of its 3 corners <= k). The base ring is vertex row
k. `k = 3n` is the full sphere. This exactly reproduces domerama's naming:

| Frequency | domerama name | k/3n | level base? |
|---|---|---|---|
| 1V | "2/3" | 2/3 | yes (icosa lower ring) |
| 2V | 1/2 | 3/6 | yes |
| 3V | "3/8" | 4/9 | Class I: no. Kruschke: yes |
| 3V | "5/8" | 5/9 | Class I: no. Kruschke: yes |
| 4V | 1/2 | 6/12 | yes |
| 4V | Kruschke 5/12, 7/12 | 5/12, 7/12 | Kruschke: yes; Class I: no |
| 5V | "3/8" = 7/15, "5/8" = 8/15 | 7/15, 8/15 | Class I: no; Kruschke ext: yes |
| 6V | 1/2 | 9/18 | yes |
| 7V | 10/21 | 10/21 | no |
| 8V | 1/2 | 12/24 | yes |

The UI fraction dropdown lists every k = 1..3n plus Full sphere, labelled
`"k/3n"` with alias suffixes where they exist (`"4/9 (a.k.a. 3/8)"`,
`"12/24 (1/2)"`, `"18/24 (3/4)"`, `"6/24 (1/4)"`, etc. - alias shown
whenever k/3n reduces to quarters or eighths, or is a domerama legacy name),
and a level-base marker. Level-base rules:

- `CLASS_I`: level iff every base-row vertex has the same z. True for
  k = 3n/2 (even n) and for k = n*tier boundaries k = n, 2n only when that
  row is a hub ring... implementation: compute it (z spread < 1e-9), do not
  hard-code. Rows n and 2n (hub rings) are NOT level for n >= 2 (edge points
  of the U-U arcs sit higher than the hubs); the computed check handles this.
- `KRUSCHKE`: level for n < row < 2n... likewise computed, not hard-coded.
- UI honesty (exact strings, no em-dashes): when the chosen combo is not
  level, the redo panel and report show:
  `"Base is not level for this method and fraction. Max height mismatch: X mm at radius R."`
  For Class I odd frequency add:
  `"Class I odd frequencies never give a level base. The Kruschke method does."`

### 4.4 Strut classification and labels

Group edge lengths at full precision: sort, then chain-merge lengths whose
gap < 1e-7 (exact symmetry orbits collapse; verified min genuine gap across
all shipped variants is 1.34e-5). Then apply the user-facing merge tolerance
`merge_tolerance` (default 1e-4, operator prop, range 0..1e-2): adjacent
groups with mean gap < merge_tolerance merge for LABELING and REPORTING
(the underlying mesh attribute keeps the fine groups; report shows merged
rows with a "contains N sub-types, spread X" note when merging occurred).
Rationale: domerama's own 7V/8V tables merge types 2.4e-5 apart (verified),
and 0.02 mm at 6 m radius is not buildable anyway.

Labels: A, B, C, ..., Z, AA, AB, ... in ascending chord-factor order.
Note: this matches domerama's Kruschke labels exactly, and domerama's Class
I labels for 1V-3V; domerama's Class I 5V-8V letters are NOT sorted by
length. The report adds a "domerama" column with their letter for the known
variants (mapping data bundled from the reference JSONs).

### 4.5 Hub census and report data

Hub valences: count incident kept edges per vertex; report
`{6-way: x, 5-way: y, 4-way: z}` style. Verified against domerama for every
published variant (one site bug: domerama lists 85 six-ways for 4V 5/12
Kruschke; correct value is 45 - their 85 belongs to 7/12; the bundled data
notes this and the report shows the correct number).

Also computed: height factor (1 - base z), base radius factor
(sqrt(1 - base_z^2) when level), strut totals, face count, per-type total
length. Verified: 3V Kruschke heights 0.812408 / 1.187592 vs site 0.81241 /
1.187592; 4V 0.723607 / 1.276393 vs 0.72361 / 1.27639.

## 5. Method math

### 5.1 CLASS_I

Exactly 4.2 + 4.3. Verified vs domerama chord charts (1V-8V): every chord
factor matches to the digits the site displays (max diff 8.5e-6 on their
5-decimal values, 6.6e-9 on their 8-decimal values), every strut count and
hub census matches, with these two site quirks (encode in tests):

- 7V "J" (0.17585 x70) is really two types: 0.17585131 x60 + 0.17589689 x10.
- 8V "N" (0.15636 x90) is really two types: 0.15636158 x60 + 0.15638647 x30.
  (Note 8V "O"/"P" differ by only 2.8e-5 yet the site kept them separate.)

Authoritative 4V 1/2 table (derived here; domerama's two 4V pages
contradict each other and cannot be paired - documented in the scrape notes):

| label | chord factor | count | bend angle |
|---|---|---|---|
| A | 0.25318460 | 30 | 7.27 |
| B | 0.29453083 | 60 | 8.47 |
| C | 0.29524181 | 30 | 8.49 |
| D | 0.29858813 | 30 | 8.59 |
| E | 0.31286893 | 70 | 9.00 |
| F | 0.32491970 | 30 | 9.35 |

(The chord-charts page's CF values are all correct but three of its angle
entries are permuted, and its letters differ; the calculator page's counts
are correct. The table above reconciles both and is the plugin's truth.)

### 5.2 Kruschke, the construction (3V and 4V, exact)

1. Build Class I Method 1 at frequency n (4.2), vertex-up.
2. Hub-adjacency: every subdivision vertex S that shares an edge with one of
   the 12 icosahedron vertices E (for n >= 3 that E is unique; assert).
   These are exactly the first subdivision points of the 30 icosa edges,
   5 around each hub.
3. One ratio m per frequency. Replace each such S by
   `T = normalize((1-m)*E + m*S)`. Geometric meaning: T slides along the
   great circle through E and S; all 60 hub spokes end up the same length,
   every hub pentagon stays regular.
4. m is fixed by the leveling condition: the moved point in vertex row n+1
   (first subdivision point of an upper-to-lower icosa edge) must land on
   the z of that row's unmoved interior points, `z_target`:
   - n=3: z_target = z of normalized (U0+U72+L36)/3 = 0.1875924741
   - n=4: z_target = z of normalized (2*U0+U72+L36)/4 = 0.2763932023
   Closed form (quadratic in m; derivation: `T_z = z_target` with
   `zw(m) = Ez + m(Sz-Ez)` and `|W(m)|^2 = 1 + 2m(d-1) + 2m^2(1-d)`,
   `d = dot(E,S)`; solve `zw^2 - z_target^2*|W|^2 = 0`, take the root in
   (0,2) nearest 1 whose T_z has the right sign). Copy
   `reference\verify_geometry.py::solve_kruschke_m` verbatim.
5. By mirror symmetry row 2n-1 lands level at -z_target. For n=4 the
   equator row 6 is already level (z=0). Valid level truncations:
   n=3: k in {4, 5}; n=4: k in {5, 6, 7}; plus full sphere for both.

Solved constants (regression-test these to 1e-12):

- n=3: m = 0.9442890009767209
- n=4: m = 0.8761509568376010

Verified output (full precision; site values in parentheses):

3V Kruschke: A 0.32970646 (0.329706), B 0.38229019 (0.382290),
C 0.42148879 (0.421489), D 0.44105636 (0.441056).
Counts 4/9: 30/30/50/10; 5/9: 30/35/80/20. Hubs 4/9: 25x6 6x5 15x4.

4V Kruschke: A 0.22218795 (0.22219), B 0.25958076 (0.25958),
C 0.30906270 (0.30906), D 0.31286893 (0.31287), E 0.32491970 (0.32492),
F 0.32941885 (0.32942). Counts 5/12: 30/30/50/40/20/20;
7/12: 30/35/80/80/45/40. (D and E are shared with plain Class I 4V, as
expected: those struts touch no moved vertex.)

### 5.3 Domerama cross-check (report feature, not a separate method)

For the single `KRUSCHKE` method, the report table adds domerama columns
(domerama chord factor, published, from bundled JSON) whenever the built
dome matches one of the four domes domerama publishes: (3V, 4/9), (3V,
5/9), (4V, 5/12), (4V, 7/12). Matching is by nearest chord factor within
the 2e-4 threshold from 4.4 (`domerama_columns` in `core/classify.py`);
labels agree with ascending order for these four domes. For every other
Kruschke fraction the column is blank. Max deviation observed: 2.7e-6
(domerama's own rounding).

### 5.4 KRUSCHKE extended (5V and 6V) - our documented extension

Fact (verified, and consistent with Toomey's 6V remark): for n >= 5 the
one-parameter construction cannot level the candidate base rows, because
those rows contain points that are not hub-adjacent, and even row n+1
contains interior orbits at different standard latitudes. There is no
published 5V/6V Kruschke math to follow. We therefore define and clearly
document this extension (UI name "Kruschke 5V extended" etc.):

1. Steps 1-3 of 5.2 (hub slide), with z_target for the m equation replaced
   by the multiplicity-weighted mean z of row n+1's interior points (for
   n=3,4 this equals the single interior z, so the extension reduces exactly
   to the classic construction).
2. Then level every band vertex row r, n < r < 2n:
   - target z_r: row n+1 -> z_target; row 2n-1 -> -z_target; other rows ->
     multiplicity-weighted mean of the row's standard z values (equator of
     even n comes out exactly 0).
   - hub-adjacent points are already placed by step 1; skip them.
   - points on icosa edges slide along their edge great circle to z_r
     (function `slide_on_arc_to_z` in the reference script; picks the
     intersection nearest the current position).
   - face-interior points slide along their meridian to z_r (longitude
     kept, `(r_xy*cos(lam), r_xy*sin(lam), z_r)` with
     `r_xy = sqrt(1 - z_r^2)`).

Verified properties: all vertices on the sphere (1e-16), all 60 spokes
equal, all band rows level to 1e-16. Solved m: 5V 0.8034029131,
6V 0.7284893921. Valid level truncations: 5V k in {6,7,8,9}; 6V k in
{7,8,9,10,11}; plus full sphere.

Cost, stated honestly in UI and report: strut-type count grows. 5V 7/15: 22
types (min gap 1.3e-5); 5V 8/15: 25; 6V 7/18: 16; 6V 9/18: 30 (for 6V 1/2
plain Class I is level with only 9 types; the UI says
`"For 1/2 domes at even frequency, Class I already gives a level base with fewer strut types."`).
With the default merge tolerance 1e-4 the reported table shrinks
substantially (near-degenerate types merge). Full golden tables:
`reference\kruschke_extended_reference.json` (generated by the verify
script; these are the regression targets).

## 6. Match table (verification summary)

All from `reference\verify_output.txt` (130 checks, all PASS):

| Variant | CFs | Counts | Hubs | Height | Notes |
|---|---|---|---|---|---|
| Class I 1V 2/3, 2V 1/2, 3V 4/9 and 5/9, 4V 1/2, 5V 7/15 and 8/15, 6V 1/2, 7V 10/21, 8V 1/2 | PASS | PASS | PASS (where published) | n/a | 7V J and 8V N are site-merged double types; 4V pairing re-derived |
| Kruschke 3V 4/9, 5/9 | PASS (<= 5e-7) | PASS | PASS | PASS | m matches acidome constant to 2e-8 |
| Kruschke 4V 5/12, 7/12 | PASS (<= 2.7e-6) | PASS | PASS (site's 5/12 hub count is a copy-paste bug; correct 45x6-way asserted) | PASS | |
| Extended 5V, 6V | golden (no external ref) | golden | golden | golden | level rows and equal spokes proven |

## 7. CUSTOM chord table

Semantics: the table applies to a chosen base layout (`custom_base` operator
enum: "Class I" for 1V-8V, or "Kruschke" for 3V-6V) at the chosen frequency
and fraction. The user pastes N chord factors (comma, space or newline
separated) where N = number of strut classes of that base layout at merge
tolerance 1e-7 (the operator shows the expected N and the base defaults as
placeholder; e.g. Class I 3V expects 3 values, Kruschke 3V expects 4).
Mapping: ascending order against the base layout's ascending classes (table
row i replaces class i). This lets Ralph paste a published flat-base
4-length 3V table onto the Kruschke topology directly.

Geometry from the table: constrained relaxation starting from the Class I
positions. Iterate (default 400 rounds or until max length error < 1e-9):
for each edge, move both endpoints along the edge direction by half the
length error each (weighted equally), then re-normalize both to the unit
sphere; apex pinned at (0,0,1); no symmetry enforcement. This converges for
any table that describes a sphere-like icosahedral design (e.g. feeding the
Kruschke 3V factors reproduces the Kruschke dome). After solving, report
`max residual` (worst |edge length - target|); if residual > 1e-4 the panel
warns: `"Chord table is not self-consistent on a sphere. Worst strut error: X mm at radius R."`
The mesh is still produced (best fit).

Validation: N values, all > 0, all < 2.0; wrong count is a hard error
listing expected N. Values deviating > 25 percent from the Class I default
produce a warning (probable class-order mismatch), not an error.

Rejected alternative: interpreting the custom table only as report override
without geometry change (does not meet the requirement); asking the user for
per-row vertex coordinates (nobody has those).

## 8. Package layout

```
E:\claude\geodesic-dome-blender\
  geodesic_dome\                  <- the extension (zip root)
    blender_manifest.toml
    __init__.py                   register/unregister only
    operators.py                  mesh.geodesic_dome_add
    panel.py                      N-panel + CSV export operator
    core\                         PURE PYTHON, never imports bpy
      __init__.py                 re-exports build_dome, valid_fractions
      icosa.py                    icosahedron + Class I subdivision + Mesh
      kruschke.py                 hub slide, m solve, extended leveling
      truncate.py                 fractions, aliases, dome_edges/faces
      classify.py                 grouping, labels, hubs, report dataclasses
      custom.py                   relaxation solver
      build.py                    build_dome() facade
      data\
        domerama_chord_factors.json
        domerama_kruschke_chord_factors.json
        kruschke_extended_reference.json
  tests\                          pytest, no bpy, runs anywhere
    conftest.py test_icosa.py test_class1.py test_kruschke.py
    test_extended.py test_truncate.py test_classify.py test_custom.py
    test_no_bpy.py test_data_sync.py
  reference\                      scrape data + verify_geometry.py (not shipped)
  docs\ design.md plan.md todos.md completed-todos.md
  build.py                        builds dist\geodesic_dome_builder-<ver>.zip
  README.md
  .gitignore
```

Canonical JSONs live in `reference\`; `geodesic_dome\core\data\` holds
byte-identical copies (test_data_sync.py asserts equality).

## 9. Core API

```python
# core/classify.py
@dataclass(frozen=True)
class StrutType:
    label: str            # "A".."Z","AA"..
    chord_factor: float   # mean of members, unit radius
    count: int
    bend_angle_deg: float
    domerama_label: str | None
    domerama_cf: float | None      # published value when known
    sub_spread: float              # 0.0 unless merge_tolerance merged types

@dataclass
class DomeReport:
    method: str; frequency: int; k: int; denom: int   # fraction = k/denom
    fraction_label: str; alias: str | None
    strut_types: list[StrutType]
    hub_valences: dict[int, int]
    height_factor: float
    base_is_level: bool
    base_z_spread: float          # 0 when level
    base_radius_factor: float | None
    total_struts: int; total_faces: int; total_verts: int
    notes: list[str]              # honesty strings, site-bug notes, residual
    custom_residual: float | None

@dataclass
class DomeGeometry:
    verts: list[tuple[float, float, float]]   # unit radius, apex +Z
    edges: list[tuple[int, int]]
    faces: list[tuple[int, int, int]]
    edge_type: list[int]          # index into report.strut_types
    face_type: list[int]          # congruence class by sorted edge-type triple
    vert_row: list[int]
    report: DomeReport

# core/build.py
def build_dome(method: str,            # 'CLASS_I'|'KRUSCHKE'|'CUSTOM'
               frequency: int,
               k: int,                 # triangle rows kept, 1..3n (3n = sphere)
               merge_tolerance: float = 1e-4,
               custom_table: list[float] | None = None) -> DomeGeometry

def valid_frequencies(method: str) -> list[int]
def valid_fractions(method: str, frequency: int) -> list[FractionInfo]
# FractionInfo: k, denom, label, alias|None, base_is_level, note|None
def expected_custom_count(frequency: int, k: int) -> int
def class1_defaults(frequency: int, k: int) -> list[float]
```

`build_dome` raises `ValueError` with a user-readable message for invalid
combos. All floats double precision; no numpy (stdlib only, keeps the
extension dependency-free and the wheels list empty).

## 10. Blender layer

### 10.1 blender_manifest.toml

```toml
schema_version = "1.0.0"
id = "geodesic_dome_builder"
version = "0.1.0"
name = "Geodesic Dome Builder"
tagline = "Geodesic dome frames with Class I and Kruschke chord factors"
maintainer = "Ralph Ledge <rledge21@gmail.com>"
type = "add-on"
website = "https://geovisualcreations.com"
tags = ["Add Mesh"]
blender_version_min = "4.2.0"
license = ["SPDX:GPL-3.0-or-later"]
```

### 10.2 Operator `mesh.geodesic_dome_add`

`bl_options = {'REGISTER', 'UNDO'}`; appended to `VIEW3D_MT_mesh_add` with
icon 'MESH_ICOSPHERE'. Redo-panel properties (order as listed):

- `method`: EnumProperty, default `'KRUSCHKE'`.
- `frequency`: EnumProperty built per method (Class I/Custom: 1-8;
  Kruschke UI: 3-4 only; the pure core also supports Kruschke 5-6, extended,
  but no operator path reaches them, per 14). Enum, not Int, so invalid
  values cannot be set. Default 3.
- `fraction`: EnumProperty, items callback from `valid_fractions(method,
  frequency)`; for Kruschke the callback filters to level-base fractions
  only (a flat-base method with a non-level base is not buildable); item
  name e.g. `"5/9 (a.k.a. 5/8), level base"` or `"7/15 (a.k.a. 3/8), base
  not level"` plus `"Full sphere"`. Default: 5/9 for Kruschke 3V, 7/12 for
  Kruschke 4V (Ralph's usual builds), else the first level item.
- `radius`: FloatProperty, default 3.0, unit LENGTH, min 0.01.
- `orientation`: Enum: `BASE_ORIGIN` (base plane sits at Z=0; for non-level
  bases the lowest base vertex sits at Z=0) default, `CENTER_ORIGIN`
  (sphere center at origin).
- `merge_tolerance`: FloatProperty default 1e-4, precision 6.
- `add_base_face`: Bool, default False; adds an n-gon face across a level
  base ring (disabled with a note when the base is not level).
- `create_strut_object`: Bool, default True.
- `strut_thickness`: Float, default 0.025 m (only when strut object on).
- `custom_table`: StringProperty (only for CUSTOM), free text of N numbers;
  parse on execute, `self.report({'ERROR'}, ...)` on validation failure.

Execute: call `build_dome`, scale verts by radius, apply orientation offset,
create mesh via `from_pydata`, set attributes (10.3), stash report JSON,
optionally build the strut object (10.4), select+activate. Dynamic enum item
strings must be kept referenced (Blender enum-callback gotcha): cache item
tuples in a module-level dict.

### 10.3 Mesh attributes and object properties

On the frame mesh object:

- Edge attribute `strut_type` (INT, EDGE domain) = index into strut table.
- Edge attribute `strut_color` (FLOAT_COLOR, EDGE domain) = the type color.
- Face attribute `panel_type` (INT, FACE domain).
- Vertex attribute `row` (INT, POINT domain).
- Object custom property `geodome_report` = JSON dump of DomeReport
  (via dataclasses.asdict), plus `radius`, plugin version. The N-panel and
  CSV exporter read only this property, so reports survive file reload and
  work on linked/duplicated objects.

Colors: HSV wheel, `hue = (0.48 + 0.618033988749895 * i) % 1.0`, s = 0.75,
v = 0.9 (starts teal, then cycles distinct hues; golden-ratio step keeps
neighbors distinct for 30+ types).

### 10.4 Strut visualization object

Optional child object `<name> Struts`: for every edge, a 3-sided prism
(triangular cross-section, 6 verts, inscribed radius = strut_thickness)
oriented along the edge, welded nothing, one material slot per strut type,
face material_index = strut type. Materials named `Strut A` etc., diffuse +
emission 0.05 of the type color, viewport display color set (so Solid mode
shows it without rendering). Parent: the frame object. 8V sphere = 1920
edges = ~23k tris; fine.

### 10.5 N-panel

3D Viewport sidebar, category "Geodome" (panel `VIEW3D_PT_geodome_report`),
visible when the active object has `geodome_report`:

- Summary box: method, frequency, fraction (+alias), radius, height,
  base diameter, level-base status (with mismatch in mm when not level).
- Strut table: label, chord factor (6 dp), length at radius (mm, 1 dp),
  count, bend angle (2 dp); domerama columns when present; merged-type note.
- Hub box: `6-way: x  5-way: y  4-way: z`.
- Notes box: honesty strings.
- Buttons: `Export CSV` (`geodome.export_csv`, invoke file browser, default
  name `dome_<method>_<freq>V_<k>-<denom>.csv`) and `Copy table` (clipboard,
  tab-separated).

### 10.6 CSV format

```
# Geodesic Dome Builder 0.1.0
# method,Kruschke (traditional)
# frequency,3V
# fraction,5/9,alias,5/8
# radius_m,3.0
# height_m,3.562776
# base_diameter_m,5.893482
# base_level,yes
strut,chord_factor,bend_angle_deg,length_m,count,total_length_m,domerama_label,domerama_cf
A,0.32970646,9.4877,0.989119,30,29.673574,A,0.329706
...
hub_valence,count
6,40
5,6
4,15
```

Numbers: chord factors 8 dp, lengths 6 dp. Comma separated, `#` metadata
lines, UTF-8 no BOM, CRLF acceptable.

## 11. Tests (pytest, no Blender)

`tests\conftest.py` inserts `geodesic_dome` dir into sys.path; every test
imports `core.*` only. `test_no_bpy.py` walks core modules and asserts
`"import bpy"` never appears (guards the purity requirement).

Tolerances and cases (mirror of the verify script, which stays as an
independent oracle):

- Class I vs `core/data/domerama_chord_factors.json`: per published CF,
  tolerance = 1 ulp of displayed digits + 5e-6; counts exact; the 7V/8V
  merged-type quirks asserted explicitly (both sub-types present with the
  documented values); hub censuses exact; authoritative 4V table asserted
  as constants.
- Kruschke vs `core/data/domerama_kruschke_chord_factors.json`: CF within
  6e-6, counts exact, height factors within 1e-5, hubs exact (4V 5/12
  asserts 45x6-way, documented site bug), m constants to 1e-12
  (3V 0.9442890009767209, 4V 0.8761509568376010).
- Extended 5V/6V vs `core/data/kruschke_extended_reference.json`: CFs to
  1e-9, counts exact, every band row level (z spread < 1e-12), all verts on
  sphere (< 1e-12), 60 equal spokes.
- Truncation: full-sphere invariants (10n^2+2 / 30n^2 / 20n^2) for n 1..8;
  fraction list contents and level flags for 3V-6V.
- Classification: ascending labels; merge_tolerance=1e-4 merges the 8V pair
  (2.49e-5) and reports sub_spread; merge_tolerance=1e-6 keeps them apart.
- Custom: Class I 3V defaults reproduce Class I (residual < 1e-9); Kruschke
  3V factors fed into 3V topology converge (residual < 1e-6) and produce a
  level base; garbage count raises ValueError.

## 12. Build and install

- `python build.py` -> `dist\geodesic_dome_builder-0.1.0.zip` containing the
  CONTENTS of `geodesic_dome\` at the zip root (manifest at top level).
  Version read from the manifest. Excludes `__pycache__`.
- Install: Blender > Edit > Preferences > Get Extensions > top-right arrow
  menu > Install from Disk > pick the zip. (Or drag the zip into Blender.)
- Result appears under Add > Mesh > Geodesic Dome.
- Optional check if Blender is on PATH:
  `blender --command extension validate geodesic_dome`.

## 13. Copy rules for all UI strings

No em-dashes or double hyphens anywhere in UI text, tooltips, reports, CSV.
Grounded and direct tone; no filler intensifiers. Icon: the stock Blender
'MESH_ICOSPHERE' (triangles; no custom icon in v1).

## 14. Open questions for Ralph (defaults chosen, all changeable)

1. 5V/6V Kruschke is our extension (5.4): level base and regular hubs, but
   22-30 strut types before merging. OK as shipped, or should 5V/6V be
   hidden until you have build-table confidence?
   **Decided (2026-09-28): hidden from the UI entirely.** The Kruschke
   frequency dropdown offers only 3V and 4V; there is no Blender operator
   path that can reach `build_dome('KRUSCHKE', 5, ...)` or `(..., 6, ...)`.
   The extended construction stays in the pure core (`core/kruschke.py`,
   `extended=True`) with its own tests (`tests/test_extended.py`) because
   it is a documented, numerically verified result (see 5.4 and 6); it is
   simply not exposed to Ralph until there is build-table confidence in it.
   **Follow-up decided the same day:** the two Kruschke UI entries were
   further merged into one `KRUSCHKE` method (see section 2's revision
   note); the domerama cross-check is now a report column, not a second
   menu entry.
2. Default radius 3.0 m and default method Kruschke 3V 5/9: match your
   usual builds?
   **Decided (2026-09-28): confirmed.** Default method is Kruschke,
   frequency 3V, fraction 5/9, radius 3 m.
3. Strut prisms are triangular cross-section. Want a hub-sphere/connector
   visualization too? (Not in v1.)
4. CSV: single file per dome as specced, or also a cut-list variant (one row
   per physical strut)? (v1: per-type table only.)
