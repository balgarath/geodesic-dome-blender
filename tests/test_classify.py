from core.icosa import subdivide_class1, dist
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


def test_merge_tolerance_cannot_chain_past_the_limit():
    # A chain of small gaps (each under merge_tolerance) that would sum to
    # more than merge_tolerance across the whole chain. Comparing each
    # candidate to the *last* group mean (the old, buggy behavior) would
    # merge the whole chain into one group whose spread exceeds tolerance;
    # comparing to the group's min (the fix) must not let that happen.
    merge_tolerance = 1e-4
    base_lengths = [1.0, 1.00003, 1.00006, 1.00009, 1.00012, 1.00015]
    positions = []
    edges = []
    for i, length in enumerate(base_lengths):
        positions.append((i * 10.0, 0.0, 0.0))
        positions.append((i * 10.0 + length, 0.0, 0.0))
        edges.append((2 * i, 2 * i + 1))

    edge_type, groups = group_edges(edges, positions, merge_tolerance)

    # Recompute each group's true min/max length from its member edges to
    # verify the spread invariant directly, independent of classify.py's
    # own internal bookkeeping.
    lengths = [dist(positions[u], positions[v]) for (u, v) in edges]
    per_group_lengths = {}
    for i, t in enumerate(edge_type):
        per_group_lengths.setdefault(t, []).append(lengths[i])
    for t, ls in per_group_lengths.items():
        spread = max(ls) - min(ls)
        assert spread < merge_tolerance, "group %d spread %.2e exceeds tolerance %.2e" % (
            t, spread, merge_tolerance)

    # With the fix, this chain must not collapse into a single group: the
    # total span (1.00015 - 1.0 = 1.5e-4) exceeds merge_tolerance (1e-4).
    assert len(groups) == 2
