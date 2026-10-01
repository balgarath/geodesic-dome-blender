# Geovisual Dome Tools

Blender 4.2+ extension (manifest format) that generates geodesic dome meshes:
Kruschke (3V, 4V), Icosa Class I Method 1 (1V to 8V), and custom chord tables.
Public repo: https://github.com/balgarath/geovisual-dome-tools (GPL-3.0-or-later).
Renamed from "Geodesic Dome Builder" at v0.2.0 to avoid looking identical to
Blender's bundled "Geodesic Domes" add-on.

## Layout
- `geovisual_dome_tools/core/` is pure Python (no bpy, no numpy). All geometry
  lives here and is tested with pytest outside Blender.
- `geovisual_dome_tools/operators.py`, `panel.py` are the thin Blender layer.
  Mesh attributes are mapped by vertex pair/set, never by list index (Blender
  can reorder edges in from_pydata).
- `reference/` holds domerama.com chord factors (incl. the Kruschke values
  extracted from each calculator page's `circle(form)` JS) and
  `verify_geometry.py`, the math oracle.
- Design and rationale: `docs/design.md`. Backlog: `docs/todos.md`.

## Commands
- Tests: `python -m pytest tests -q`
- Math oracle: `python reference/verify_geometry.py` (must end ALL CHECKS PASSED)
- Build zip: `python build.py` -> `dist/geovisual_dome_tools-<version>.zip`
- Headless Blender: `"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --factory-startup --python <script>`;
  install the zip with `bpy.ops.extensions.package_install_files(filepath=..., repo='user_default')`
  and uninstall it afterwards (it uses Ralph's real user config).

## Release checklist
1. Bump version in `geovisual_dome_tools/blender_manifest.toml`, `PLUGIN_VERSION`
   in `operators.py`, and the version + zip name in README.
2. Tests + oracle green, `python build.py`, check the manifest inside the zip.
3. Commit (conventional, no Co-Authored-By), annotated tag `vX.Y.Z`, push with tags.
4. `gh release create vX.Y.Z dist/<zip> --title ... --notes ...`

## Rules
- Domerama numbers are the pass/fail truth. Never edit reference data to make
  a test pass; known site errors are documented in `reference/domerama_chord_factors.md`.
- 5V/6V "extended" Kruschke stays in the core but hidden from every UI path
  until Ralph validates it against a real build.
- No em-dashes or double-dashes in any user-facing string (UI, report, CSV, README).
- Strut colors, shortest to longest: red, blue, green, yellow, purple, black
  (Ralph's shop paint order); generated hues past six types.
- Copyright line: `Ralph Edge / Geovisual Creations`. Maintainer email rledge21@gmail.com is intentionally public.
