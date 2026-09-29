from core.icosa import subdivide_class1
from core.truncate import dome_edges, fraction_alias, base_level_info


def test_dome_edge_counts():
    cases = [
        (3, 4, 120),
        (3, 5, 165),
        (4, 6, 250),
        (5, 7, 350),
        (5, 8, 425),
        (6, 9, 555),
        (7, 10, 700),
        (8, 12, 980),
    ]
    meshes = {}
    for n, k, expected in cases:
        if n not in meshes:
            meshes[n] = subdivide_class1(n)
        edges = dome_edges(meshes[n], k)
        assert len(edges) == expected, "n=%d k=%d got %d expected %d" % (n, k, len(edges), expected)


def test_fraction_aliases():
    assert fraction_alias(4, 9) == "3/8"
    assert fraction_alias(5, 9) == "5/8"
    assert fraction_alias(7, 15) == "3/8"
    assert fraction_alias(8, 15) == "5/8"
    assert fraction_alias(3, 6) == "1/2"
    assert fraction_alias(12, 24) == "1/2"
    assert fraction_alias(6, 24) == "1/4"
    assert fraction_alias(18, 24) == "3/4"
    assert fraction_alias(9, 18) == "1/2"
    assert fraction_alias(3, 3) is None  # full sphere


def test_class1_base_level():
    mesh2 = subdivide_class1(2)
    edges2 = dome_edges(mesh2, 3)
    base2 = sorted({v for e in edges2 for v in e if mesh2.row[v] == 3})
    level, spread = base_level_info(mesh2.verts, base2)
    assert level is True

    mesh3 = subdivide_class1(3)
    edges3 = dome_edges(mesh3, 4)
    base3 = sorted({v for e in edges3 for v in e if mesh3.row[v] == 4})
    level, spread = base_level_info(mesh3.verts, base3)
    assert level is False
