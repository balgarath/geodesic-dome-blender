import json
import os

from core.icosa import subdivide_class1
from core.kruschke import kruschke_positions
from core.truncate import dome_edges, base_ring, base_level_info

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "geovisual_dome_tools", "core", "data")

with open(os.path.join(DATA, "domerama_kruschke_chord_factors.json"), encoding="utf8") as f:
    KRU_REF = json.load(f)


def _group_lengths(edges, pos):
    def dist(a, b):
        return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5

    groups = []
    lens = sorted(dist(pos[u], pos[v]) for (u, v) in edges)
    for l in lens:
        if groups and l - groups[-1][3] < 1e-7:
            g = groups[-1]
            g[0] += l
            g[1] += 1
            g[3] = l
        else:
            groups.append([l, 1, l, l])
    return [(g[0] / g[1], g[1]) for g in groups]


def test_m_constants():
    mesh3 = subdivide_class1(3)
    _, m3 = kruschke_positions(mesh3, 3)
    assert abs(m3 - 0.9442890009767209) < 1e-12

    mesh4 = subdivide_class1(4)
    _, m4 = kruschke_positions(mesh4, 4)
    assert abs(m4 - 0.8761509568376010) < 1e-12


KRU_TRUNC = {(3, "4/9"): 4, (3, "5/9"): 5, (4, "5/12"): 5, (4, "7/12"): 7}


def test_against_domerama_kruschke():
    meshes = {}
    positions = {}
    for dome in KRU_REF["domes"]:
        n = dome["frequency"]
        k = KRU_TRUNC[(n, dome["fraction"])]
        if n not in meshes:
            meshes[n] = subdivide_class1(n)
        if n not in positions:
            positions[n], _ = kruschke_positions(meshes[n], n)
        mesh = meshes[n]
        pos = positions[n]
        edges = dome_edges(mesh, k)
        groups = _group_lengths(edges, pos)
        assert len(groups) == len(dome["struts"])
        for row, (l, c) in zip(dome["struts"], groups):
            assert abs(l - row["chord_factor"]) < 6e-6
            assert c == row["count"]

        base = base_ring(mesh, k, edges)
        level, spread = base_level_info(pos, base)
        assert level is True
        assert spread < 1e-12
        height = 1.0 - pos[base[0]][2]
        assert abs(height - dome["height_factor"]) < 1e-5


def test_hub_census():
    mesh3 = subdivide_class1(3)
    pos3, _ = kruschke_positions(mesh3, 3)
    edges3 = dome_edges(mesh3, 4)
    val = {}
    for (u, v) in edges3:
        val[u] = val.get(u, 0) + 1
        val[v] = val.get(v, 0) + 1
    census = {}
    for d in val.values():
        census[d] = census.get(d, 0) + 1
    assert census == {6: 25, 5: 6, 4: 15}

    mesh4 = subdivide_class1(4)
    pos4, _ = kruschke_positions(mesh4, 4)
    edges4_7 = dome_edges(mesh4, 7)
    val = {}
    for (u, v) in edges4_7:
        val[u] = val.get(u, 0) + 1
        val[v] = val.get(v, 0) + 1
    census = {}
    for d in val.values():
        census[d] = census.get(d, 0) + 1
    assert census == {6: 85, 5: 6, 4: 20}

    # 4V 5/12: domerama publishes 85x6-way, but that value belongs to 7/12.
    # The correct 5/12 hub census (documented site copy-paste bug) is 45x6-way.
    edges4_5 = dome_edges(mesh4, 5)
    val = {}
    for (u, v) in edges4_5:
        val[u] = val.get(u, 0) + 1
        val[v] = val.get(v, 0) + 1
    census = {}
    for d in val.values():
        census[d] = census.get(d, 0) + 1
    assert census == {6: 45, 5: 6, 4: 20}
