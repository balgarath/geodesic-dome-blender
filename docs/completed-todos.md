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

## Post-0.2.0 (2026-09-29 to 2026-09-30)
- [x] v0.1.3: shop strut palette (red, blue, green, yellow, purple, black, shortest to longest); manifest website fixed to geovisual.net.
- [x] Public GitHub repo under GPL-3.0-or-later with LICENSE, CREDITS.md, SPDX headers; reference notes rewritten with no copied site prose.
- [x] Ralph's logo in README (light/dark picture), 1280x640 social preview images (og-dark.png, og-light.png).
- [x] v0.2.1: custom menu icon from Ralph's logo, loaded via bpy.utils.previews; confirmed in Ralph's Blender 5.2 menu.
- [x] README intro reworded; upgrade-from-0.1.x note removed.

## Fixed in v0.1.2 (reviewer follow-up on v0.1.1)
- [x] N1: the custom-table "N strut lengths instead of M" warning false-
      positived on genuinely consistent tables (domerama's own rounded
      Kruschke CFs at residual 5e-6 reported 23 instead of 6; a
      self-consistent default table at a coarse merge_tolerance reported
      14 instead of 16). Now counts at max(merge_tolerance, 3x residual)
      and only warns when that count still exceeds M and residual exceeds
      the 1e-4 gate. Note: on small, closely-spaced topologies (e.g. Class
      I 3V, only 3 classes within ~0.06 of each other), a single-class
      perturbation large enough to be genuinely inconsistent also makes
      3x residual comparable to the inter-class gaps, so this specific
      count warning does not fire for that shape of bad table; the general
      "not self-consistent" residual warning still does. Documented in the
      test (test_inconsistent_table_still_warns).
- [x] N2: the base-level tolerance was a fixed 0.1 mm regardless of
      radius, letting tiny Class I odd-frequency domes (5V under 1.45 cm)
      report "level". Now relative: max(1e-9 x radius, min(0.1 mm,
      1e-5 x radius)).
- [x] N3: suppressed the "Base spread: 0.0000 mm... within tolerance" note
      when it rounds to zero at display precision or the base is a single
      vertex (full sphere).
- [x] N4: test_class1_against_domerama silently skipped any out-of-
      tolerance nearest match; now asserts the skip is limited to the two
      documented site-merged rows (7V J, 8V N). Added a test verifying the
      _KNOWN_SPLITS pair counts actually sum to domerama's published
      merged counts (70, 90) instead of assuming it.

## Fixed in v0.1.1 (two-review fix round)
- [x] N-panel was missing the domerama column; now shown per strut row.
- [x] Edge/face mesh attributes (strut_type, strut_color, panel_type) were
      assigned by list position, which Blender can reorder inside
      from_pydata (measured: only 1/310 edges kept their input index for
      Kruschke 4V 7/12 in Blender 4.0.1). Fixed by mapping attributes by
      sorted vertex-index pair (edges) / vertex-index set (faces) instead
      of position. Verified correct in headless Blender 4.0.1 AND 5.2.0;
      Blender 4.2-5.1 is covered by the same vertex-index mapping (it does
      not depend on which specific version reorders edges), so this is no
      longer a version-specific risk.
- [x] Merge tolerance could chain past its own limit (compared each
      candidate to the previous group's mean instead of the group's min);
      fixed, with a regression test. Default lowered to 1e-6, UI max
      lowered to 1e-3, and merged sub-types now report their spread in mm
      at the actual radius with a warning above 0.5 mm.
- [x] Custom solver messages hard-coded "at radius 1.000 m"; now scaled to
      the actual radius. Added a warning when the custom table is not
      geometrically consistent (actual strut-type count vs table row
      count).
- [x] Base-level check used an absolute 1e-9 tolerance regardless of
      radius, so a Custom dome fed domerama's own rounded Kruschke factors
      was reported "not level". Now uses a tolerance in real length (0.1 mm)
      at the chosen radius.
- [x] API bug: build_dome with custom_table=None combined class1_defaults
      (Class I only, one tolerance) with solve_custom (any base, a
      different tolerance), raising ValueError for some base/frequency
      combinations. Fixed with core/custom.py:base_defaults, which uses
      the correct base topology and the same tolerance solve_custom uses.
- [x] Added tests comparing the shipped build_dome() at its PRODUCTION
      default tolerance against the reference JSONs for every Class I
      1V-8V variant and all 4 Kruschke variants, using nearest-match
      pairing; fixed the older sequential first-within-tolerance test the
      same way; added a synthetic regression test for the chaining fix.

## Design decisions recorded this session (see docs/design.md for detail)
- 5V/6V extended Kruschke: stays in the pure core with tests, hidden from
  every Blender UI path (design.md 14, item 1).
- Kruschke (Domerama) and Kruschke (Traditional) merged into one `KRUSCHKE`
  method; domerama's published values now show as a report column instead
  of a second menu entry (design.md 2 and 5.3).
- Defaults confirmed: method Kruschke, frequency 3V, fraction 5/9, radius
  3 m (design.md 14, item 2).
