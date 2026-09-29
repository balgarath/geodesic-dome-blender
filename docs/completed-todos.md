# Completed TODOs

## v0.1.0 build (2026-09-28)
- [x] Execute docs/plan.md T1 through T12: pure Python geometry core
      (icosahedron, Class I subdivision, Kruschke construction and its 5V/6V
      extension, truncation/fractions, classification/report, custom chord
      table relaxation solver), Blender operator, strut prism visualization,
      N-panel report and CSV export, build script, README, and a manual
      Blender headless smoke test.
- [x] Ralph's open questions in docs/design.md section 14: 5V/6V hidden
      from the UI, default radius/method confirmed (Kruschke 3V 5/9, 3 m).
- [x] Ralph's mid-build correction: merged the Kruschke (Domerama) and
      Kruschke (Traditional) UI entries into one `KRUSCHKE` method with the
      domerama cross-check as a report column.

## v0.1.1 fix round (2026-09-28): two independent reviews
- [x] N-panel domerama column, edge/face attribute vertex-pair mapping
      (fixes a real Blender edge-reorder bug), merge-tolerance chaining
      fix, radius-aware residual/spread messages, custom solver
      type-count-mismatch warning, radius-aware base-level tolerance, a
      real build_dome API bug for custom_table=None, and new tests
      comparing production defaults against the reference JSONs with
      nearest-match pairing. Full list in docs/todos.md's "Fixed in v0.1.1"
      section.

## v0.2.0 rename (2026-09-29)
- [x] Renamed Geodesic Dome Builder to Geovisual Dome Tools (new extension ID, menu label, icon, N-panel tab) so it no longer looks identical to Blender's bundled Geodesic Domes add-on.
