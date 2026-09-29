from core.icosa import subdivide_class1, hub_neighbors


def test_full_sphere_invariants():
    for n in range(1, 9):
        mesh = subdivide_class1(n)
        edges = mesh.edges()
        assert len(mesh.verts) == 10 * n * n + 2
        assert len(edges) == 30 * n * n
        assert len(mesh.faces) == 20 * n * n
        for p in mesh.verts:
            length = (p[0] ** 2 + p[1] ** 2 + p[2] ** 2) ** 0.5
            assert abs(length - 1.0) < 1e-12
        rows = mesh.row
        assert min(rows) == 0
        assert max(rows) == 3 * n
        assert rows.count(0) == 1
        assert rows.count(3 * n) == 1


def test_hub_neighbors_3v():
    mesh = subdivide_class1(3)
    hn = hub_neighbors(mesh)
    assert len(hn) == 60
    counts = {}
    for v, h in hn.items():
        counts[h] = counts.get(h, 0) + 1
    assert len(counts) == 12
    for h, c in counts.items():
        assert c == 5
