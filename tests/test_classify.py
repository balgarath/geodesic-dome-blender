from core.icosa import subdivide_class1
from core.truncate import dome_edges
from core.classify import group_edges, label
from core.build import build_dome


def test_labels_ascending():
    assert label(0) == "A"
    assert label(25) == "Z"
    assert label(26) == "AA"
    assert label(27) == "AB"


def test_8v_merge_tolerance():
    mesh = subdivide_class1(8)
    edges = dome_edges(mesh, 12)
    _et, fine_groups = group_edges(edges, mesh.verts, 1e-7)
    assert len(fine_groups) == 20

    _et2, merged_groups = group_edges(edges, mesh.verts, 1e-4)
    # 8V full precision has two near-degenerate gaps under 1e-4 (the 8V "N"
    # split at 2.49e-5 and the "O"/"P" pair at 2.83e-5), so merge_tolerance
    # 1e-4 collapses 20 fine types to 18 reported rows (not 19 as guessed in
    # the plan; verified directly from the fine-group gap list).
    assert len(merged_groups) == 18
    merged_rows = [g for g in merged_groups if g["sub_spread"] > 0]
    assert len(merged_rows) == 2


def test_extended_kruschke_5v_type_count():
    geometry = build_dome("KRUSCHKE", 5, 7, merge_tolerance=1e-7)
    assert len(geometry.report.strut_types) == 22
