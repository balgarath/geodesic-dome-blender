import json
import os

from core.icosa import subdivide_class1, hub_neighbors
from core.kruschke import kruschke_positions
from core.truncate import dome_edges

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "geovisual_dome_tools", "core", "data")

with open(os.path.join(DATA, "kruschke_extended_reference.json"), encoding="utf8") as f:
    EXT_REF = json.load(f)


def _dist(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5


def _group_lengths(edges, pos):
    groups = []
    lens = sorted(_dist(pos[u], pos[v]) for (u, v) in edges)
    for l in lens:
        if groups and l - groups[-1][3] < 1e-7:
            g = groups[-1]
            g[0] += l
            g[1] += 1
            g[3] = l
        else:
            groups.append([l, 1, l, l])
    return [(g[0] / g[1], g[1]) for g in groups]


def test_extended_properties():
    for n in (5, 6):
        mesh = subdivide_class1(n)
        pos, m = kruschke_positions(mesh, n, extended=True)
        for p in pos:
            r = (p[0] ** 2 + p[1] ** 2 + p[2] ** 2) ** 0.5
            assert abs(r - 1.0) < 1e-12
        hn = hub_neighbors(mesh)
        spokes = [_dist(pos[v], pos[h]) for v, h in hn.items()]
        assert max(spokes) - min(spokes) < 1e-12
        for r in range(n + 1, 2 * n):
            zs = [pos[i][2] for i in range(len(pos)) if mesh.row[i] == r]
            assert max(zs) - min(zs) < 1e-12


def test_extended_against_golden():
    meshes = {}
    positions = {}
    for dome in EXT_REF["domes"]:
        n = dome["frequency"]
        k, denom = (int(x) for x in dome["fraction"].split("/"))
        if n not in meshes:
            meshes[n] = subdivide_class1(n)
        if n not in positions:
            positions[n] = kruschke_positions(meshes[n], n, extended=True)
        pos, m = positions[n]
        assert abs(m - dome["m"]) < 1e-9
        edges = dome_edges(meshes[n], k)
        groups = _group_lengths(edges, pos)
        assert len(groups) == len(dome["struts"])
        for row, (l, c) in zip(dome["struts"], groups):
            assert abs(l - row["chord_factor"]) < 1e-9
            assert c == row["count"]
