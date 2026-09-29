import json
import os

from core.icosa import subdivide_class1
from core.truncate import dome_edges
from core.classify import group_edges

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "geodesic_dome", "core", "data")

with open(os.path.join(DATA, "domerama_chord_factors.json"), encoding="utf8") as f:
    CLASSI_REF = json.load(f)

TRUNC = {
    ("1V", "2/3"): 2, ("2V", "1/2"): 3,
    ("3V", "3/8"): 4, ("3V", "5/8"): 5,
    ("4V", "1/2"): 6,
    ("5V", "7/15"): 7, ("5V", "8/15"): 8,
    ("6V", "1/2"): 9, ("7V", "10/21"): 10, ("8V", None): 12,
}


def _tol_for(cf):
    s = "%r" % cf
    dec = len(s.split(".")[1]) if "." in s else 0
    return 1.0 * 10 ** (-dec) + 5e-6


def test_class1_against_domerama():
    meshes = {}
    for dome in CLASSI_REF["domes"]:
        if dome["method"] != "Class I Method 1":
            continue
        n = int(dome["frequency"][0])
        key = (dome["frequency"], dome["fraction"])
        if key not in TRUNC:
            continue
        k = TRUNC[key]
        if n not in meshes:
            meshes[n] = subdivide_class1(n)
        mesh = meshes[n]
        edges = dome_edges(mesh, k)
        # fine grouping (1e-7) matches the oracle's group_lengths
        edge_type, groups = group_edges(edges, mesh.verts, 1e-7)
        counts_ok = all(s.get("count") for s in dome["struts"] if s.get("chord_factor"))
        used = set()
        for srow in dome["struts"]:
            cf = srow.get("chord_factor")
            if cf is None:
                continue
            tol = _tol_for(cf)
            hit = None
            for gi, g in enumerate(groups):
                if gi not in used and abs(g["chord_factor"] - cf) <= tol:
                    hit = gi
                    break
            assert hit is not None, "%s %s: no match for CF %.8f" % (
                dome["frequency"], srow["label"], cf)
            used.add(hit)
            if counts_ok and srow.get("count") is not None:
                c = groups[hit]["count"]
                if c != srow["count"]:
                    # site sometimes merges two true strut types (7V J, 8V N)
                    merged = False
                    for gj, g2 in enumerate(groups):
                        if gj not in used and abs(g2["chord_factor"] - cf) < 2e-4 \
                                and c + g2["count"] == srow["count"]:
                            used.add(gj)
                            merged = True
                            break
                    assert merged, "%s %s: count %d vs ref %d" % (
                        dome["frequency"], srow["label"], c, srow["count"])


def test_7v_j_split():
    mesh = subdivide_class1(7)
    edges = dome_edges(mesh, 10)
    edge_type, groups = group_edges(edges, mesh.verts, 1e-7)
    cfs = sorted((g["chord_factor"], g["count"]) for g in groups)
    matches = [(l, c) for (l, c) in cfs if abs(l - 0.17585131) < 1e-6 or abs(l - 0.17589689) < 1e-6]
    assert any(abs(l - 0.17585131) < 1e-6 and c == 60 for l, c in matches)
    assert any(abs(l - 0.17589689) < 1e-6 and c == 10 for l, c in matches)


def test_8v_n_split():
    mesh = subdivide_class1(8)
    edges = dome_edges(mesh, 12)
    edge_type, groups = group_edges(edges, mesh.verts, 1e-7)
    cfs = [(g["chord_factor"], g["count"]) for g in groups]
    assert any(abs(l - 0.15636158) < 1e-6 and c == 60 for l, c in cfs)
    assert any(abs(l - 0.15638647) < 1e-6 and c == 30 for l, c in cfs)


def test_authoritative_4v_table():
    mesh = subdivide_class1(4)
    edges = dome_edges(mesh, 6)
    edge_type, groups = group_edges(edges, mesh.verts, 1e-7)
    cfs = [(round(g["chord_factor"], 8), g["count"]) for g in groups]
    expected = [
        (0.25318460, 30), (0.29453083, 60), (0.29524181, 30),
        (0.29858813, 30), (0.31286893, 70), (0.32491970, 30),
    ]
    assert len(cfs) == len(expected)
    for (got_cf, got_c), (exp_cf, exp_c) in zip(cfs, expected):
        assert abs(got_cf - exp_cf) < 1e-6
        assert got_c == exp_c
