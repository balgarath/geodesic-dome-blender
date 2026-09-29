import json
import os

from core.icosa import subdivide_class1
from core.truncate import dome_edges
from core.classify import group_edges
from _helpers import nearest_match_pairs

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

# domerama displays these as one row; the true, physically distinct split
# is documented and verified separately (test_7v_j_split, test_8v_n_split).
# A nearest match landing outside tolerance is only acceptable for these.
_KNOWN_SPLIT_LABELS = {("7V", "J"), ("8V", "N")}


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

        ref_rows = [s for s in dome["struts"] if s.get("chord_factor") is not None]
        ref_cfs = [s["chord_factor"] for s in ref_rows]
        computed_cfs = [g["chord_factor"] for g in groups]
        pairs = nearest_match_pairs(computed_cfs, ref_cfs)
        matched_ref = {ri for ri, ci, d in pairs}
        for ri in range(len(ref_rows)):
            assert ri in matched_ref, "%s %s: CF %.8f has no nearest match at all" % (
                dome["frequency"], ref_rows[ri]["label"], ref_cfs[ri])

        used_computed = set()
        for ri, ci, d in pairs:
            srow = ref_rows[ri]
            cf = ref_cfs[ri]
            tol = _tol_for(cf)
            if d > tol:
                # Not a direct match. This is only acceptable for the two
                # documented site-merged rows (7V J, 8V N), where the
                # nearest match is one half of the true split and can sit
                # up to ~2e-4 away from the merged reference value; any
                # other row failing to match within tolerance is a real
                # regression, so assert rather than silently skip it.
                assert (dome["frequency"], srow["label"]) in _KNOWN_SPLIT_LABELS, (
                    "%s %s: nearest match distance %.2e exceeds tolerance %.2e "
                    "(ref CF %.8f, nearest computed %.8f) and is not a known "
                    "site-merged row" % (
                        dome["frequency"], srow["label"], d, tol, cf, computed_cfs[ci]))
                continue
            used_computed.add(ci)
            if counts_ok and srow.get("count") is not None:
                c = groups[ci]["count"]
                if c != srow["count"]:
                    # site sometimes merges two true strut types (7V J, 8V N)
                    merged = False
                    for gj, g2 in enumerate(groups):
                        if gj not in used_computed and abs(g2["chord_factor"] - cf) < 2e-4 \
                                and c + g2["count"] == srow["count"]:
                            used_computed.add(gj)
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
