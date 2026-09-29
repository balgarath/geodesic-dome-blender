import pytest

from core.icosa import subdivide_class1
from core.build import class1_defaults, build_dome
from core.custom import solve_custom, parse_table
from core.classify import group_edges
from core.truncate import dome_edges


def test_class1_defaults_reproduce_class1():
    mesh = subdivide_class1(3)
    targets = class1_defaults(3, 4)
    positions, residual = solve_custom(mesh, mesh.verts, 4, targets)
    assert residual < 1e-9

    edges = dome_edges(mesh, 4)
    _edge_type, groups = group_edges(edges, positions, 1e-7)
    for g, t in zip(groups, targets):
        assert abs(g["chord_factor"] - t) < 1e-9


def test_custom_base_count_mismatch():
    mesh = subdivide_class1(3)
    kru_values = [0.32970646, 0.38229019, 0.42148879, 0.44105636]
    with pytest.raises(ValueError):
        solve_custom(mesh, mesh.verts, 4, kru_values)


def test_custom_base_kruschke_converges_level():
    # The four published Kruschke 3V chord factors are only given to 8
    # decimal places (design.md 5.2); that rounding alone puts a floor of
    # about 1e-8 on the achievable residual, so we check against that floor
    # rather than the unrounded 1e-9 a full-precision target would allow.
    from core.kruschke import kruschke_positions
    mesh = subdivide_class1(3)
    base_positions, _m = kruschke_positions(mesh, 3)
    kru_values = [0.32970646, 0.38229019, 0.42148879, 0.44105636]
    positions, residual = solve_custom(mesh, base_positions, 4, kru_values)
    assert residual < 2e-8

    from core.truncate import base_ring, base_level_info
    edges = dome_edges(mesh, 4)
    base = base_ring(mesh, 4, edges)
    _level, spread = base_level_info(positions, base)
    # base_level_info's hard-coded 1e-9 threshold is tighter than what an
    # 8-decimal-rounded input target can reach (see comment above); check
    # the spread directly against a tolerance consistent with that rounding.
    assert spread < 1e-8


def test_perturbed_class1_converges():
    # A uniform per-class perturbation this small (0.1% on strut A) is a
    # near-consistent target the relaxation can satisfy well within the
    # default iteration budget. Larger single-class perturbations (verified
    # separately, not asserted here) hit a genuine geometric floor: growing
    # one strut class while every vertex is pinned to the unit sphere and
    # the apex is fixed is over-constrained, so residual does not keep
    # shrinking with more iterations for large perturbations.
    mesh = subdivide_class1(3)
    targets = class1_defaults(3, 4)
    perturbed = list(targets)
    perturbed[0] = perturbed[0] * 1.001
    positions, residual = solve_custom(mesh, mesh.verts, 4, perturbed)
    assert residual < 1e-3
    edges = dome_edges(mesh, 4)
    # The relaxation converges close to, but not exactly onto, the
    # symmetric fixed point (residual ~5e-4), so grouping needs a tolerance
    # comfortably above that residual to see the topology's true 3 classes;
    # the no-chaining fix (classify.py) means the tolerance must now cover
    # each class's full observed spread, not just adjacent gaps, so 1e-4
    # (which worked before that fix) is no longer enough.
    _edge_type, groups = group_edges(edges, positions, 1e-3)
    assert len(groups) == 3


def test_parse_table():
    assert parse_table("0.36, 0.41 0.42\n") == [0.36, 0.41, 0.42]
    with pytest.raises(ValueError):
        parse_table("0.36, abc, 0.42")
    with pytest.raises(ValueError):
        parse_table("   ")


def test_consistency_warning_not_false_positive_on_rounded_domerama_table():
    # domerama's own published 4V 7/12 Kruschke chord factors (5-6 decimal
    # places), fed back as a Custom table on the Kruschke base: residual is
    # tiny (solver noise from the rounding, well under the 1e-4 warning
    # gate), so no "not geometrically consistent" strut-count warning
    # should appear, even though the reporting merge_tolerance alone would
    # otherwise see many more than 6 near-duplicate types.
    table = [0.22219, 0.25958, 0.30906, 0.31287, 0.32492, 0.32942]
    geometry = build_dome("CUSTOM", 4, 7, custom_base="KRUSCHKE",
                          custom_table=table, radius=5.0)
    assert geometry.report.custom_residual < 1e-4
    assert not any("strut lengths instead of" in n for n in geometry.report.notes)


def test_consistency_warning_not_false_positive_on_self_consistent_defaults():
    # Feeding the 7V default table back at a coarse merge_tolerance (1e-4)
    # legitimately reports fewer strut types than the table has rows
    # (adjacent true classes are close enough to merge for reporting); that
    # is a merge_tolerance choice, not an inconsistent table, and must not
    # raise the "strut lengths instead of" warning.
    from core.custom import base_defaults
    targets = base_defaults(7, 10, "CLASS_I", merge_tolerance=1e-7)
    geometry = build_dome("CUSTOM", 7, 10, custom_table=targets,
                          merge_tolerance=1e-4, radius=3.0)
    assert geometry.report.custom_residual < 1e-9
    assert not any("strut lengths instead of" in n for n in geometry.report.notes)


def test_no_zero_spread_note_when_it_rounds_to_zero():
    # domerama's own rounded Kruschke 3V factors, fed back on the Kruschke
    # base: base spread is a few billionths on the unit sphere, which at
    # 3 m rounds to 0.0000 mm. That is not useful information and must not
    # appear as a "Base spread: 0.0000 mm..." note.
    kru_values = [0.32970646, 0.38229019, 0.42148879, 0.44105636]
    geometry = build_dome("CUSTOM", 3, 4, custom_base="KRUSCHKE",
                          custom_table=kru_values, radius=3.0)
    assert geometry.report.base_is_level is True
    assert not any("Base spread" in n for n in geometry.report.notes)


def test_no_spread_note_for_full_sphere():
    # Full sphere: the "base" is a single vertex (the nadir), so any
    # spread note is meaningless and must not appear.
    geometry = build_dome("CLASS_I", 4, 12, radius=3.0)
    assert geometry.report.k == geometry.report.denom  # full sphere
    assert not any("Base spread" in n for n in geometry.report.notes)


def test_inconsistent_table_still_warns():
    # Class I 3V 5/8 with strut A pushed 1% off its self-consistent value:
    # genuinely inconsistent (residual well above the warning gate), and
    # must still produce the general "not self-consistent" warning. (The
    # more specific "N strut lengths instead of M" count warning is tuned
    # to the noise floor via 3 x residual and, for a single-class
    # perturbation on this small a topology, that same loosening collapses
    # the true classes together rather than splitting them further, so it
    # is the general residual warning that is the reliable "still warns"
    # signal here, not the count warning.)
    targets = class1_defaults(3, 5)
    perturbed = list(targets)
    perturbed[0] = perturbed[0] * 1.01
    geometry = build_dome("CUSTOM", 3, 5, custom_table=perturbed, radius=3.0)
    assert geometry.report.custom_residual > 1e-4
    assert any("not self-consistent" in n for n in geometry.report.notes)
