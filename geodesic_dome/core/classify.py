"""Strut grouping, labeling, hub census, and report dataclasses.

Design.md 4.4, 4.5, 9.
"""
import json
import math
import os
from dataclasses import dataclass, field

from .icosa import dist

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")

_FINE_GAP = 1e-7
_MATCH_THRESHOLD = 2e-4


@dataclass(frozen=True)
class StrutType:
    label: str            # "A".."Z","AA"..
    chord_factor: float   # mean of members, unit radius
    count: int
    bend_angle_deg: float
    domerama_label: "str | None" = None
    domerama_cf: "float | None" = None      # published value when known
    sub_spread: float = 0.0                 # 0.0 unless merge_tolerance merged types


@dataclass
class DomeReport:
    method: str
    frequency: int
    k: int
    denom: int   # fraction = k/denom
    fraction_label: str
    alias: "str | None"
    strut_types: list
    hub_valences: dict
    height_factor: float
    base_is_level: bool
    base_z_spread: float          # 0 when level
    base_radius_factor: "float | None"
    total_struts: int
    total_faces: int
    total_verts: int
    notes: list = field(default_factory=list)   # honesty strings, site-bug notes, residual
    custom_residual: "float | None" = None


@dataclass
class DomeGeometry:
    verts: list            # unit radius, apex +Z
    edges: list
    faces: list
    edge_type: list        # index into report.strut_types
    face_type: list        # congruence class by sorted edge-type triple
    vert_row: list
    report: DomeReport


def label(i):
    """A..Z, AA, AB, ... for i = 0, 1, 2, ..."""
    s = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def group_edges(edges, positions, merge_tolerance):
    """Two-stage grouping: chain-merge < 1e-7, then merge adjacent groups
    with mean gap < merge_tolerance (for labeling/reporting).

    Returns (edge_type, groups) where edge_type[i] is an index into groups
    (aligned with the input edges list) and each group is a dict with keys
    chord_factor, count, sub_spread.
    """
    lengths = [dist(positions[u], positions[v]) for (u, v) in edges]
    order = sorted(range(len(edges)), key=lambda i: lengths[i])

    fine_groups = []
    for i in order:
        l = lengths[i]
        if fine_groups and l - fine_groups[-1]["max"] < _FINE_GAP:
            g = fine_groups[-1]
            g["idxs"].append(i)
            g["max"] = l
        else:
            fine_groups.append({"idxs": [i], "max": l})
    for g in fine_groups:
        g["mean"] = sum(lengths[i] for i in g["idxs"]) / len(g["idxs"])

    final_groups = []
    for g in fine_groups:
        if final_groups and g["mean"] - final_groups[-1]["fine"][-1]["mean"] < merge_tolerance:
            final_groups[-1]["fine"].append(g)
        else:
            final_groups.append({"fine": [g]})

    groups = []
    edge_type = [0] * len(edges)
    for gi, fg in enumerate(final_groups):
        idxs = [i for g in fg["fine"] for i in g["idxs"]]
        cf = sum(lengths[i] for i in idxs) / len(idxs)
        means = [g["mean"] for g in fg["fine"]]
        sub_spread = (max(means) - min(means)) if len(fg["fine"]) > 1 else 0.0
        groups.append({"chord_factor": cf, "count": len(idxs), "sub_spread": sub_spread})
        for i in idxs:
            edge_type[i] = gi
    return edge_type, groups


def hub_valences(edges):
    """{valence: count} across all vertices touched by the given edges."""
    val = {}
    for (u, v) in edges:
        val[u] = val.get(u, 0) + 1
        val[v] = val.get(v, 0) + 1
    out = {}
    for d in val.values():
        out[d] = out.get(d, 0) + 1
    return out


def face_types(faces, edges, edge_type):
    """Congruence class id per face, by sorted edge-type triple."""
    edge_index = {}
    for i, (u, v) in enumerate(edges):
        edge_index[(min(u, v), max(u, v))] = i
    sig_map = {}
    out = []
    for (a, b, c) in faces:
        sig = tuple(sorted(
            edge_type[edge_index[(min(x, y), max(x, y))]]
            for x, y in ((a, b), (b, c), (c, a))
        ))
        if sig not in sig_map:
            sig_map[sig] = len(sig_map)
        out.append(sig_map[sig])
    return out


_CLASS_I_TRUNC = {
    (1, "2/3"): 2, (2, "1/2"): 3,
    (3, "3/8"): 4, (3, "5/8"): 5,
    (4, "1/2"): 6,
    (5, "7/15"): 7, (5, "8/15"): 8,
    (6, "1/2"): 9, (7, "10/21"): 10, (8, None): 12,
}
_KRU_TRUNC = {
    (3, "4/9"): 4, (3, "5/9"): 5, (4, "5/12"): 5, (4, "7/12"): 7,
}


def _load_json(name):
    with open(os.path.join(DATA_DIR, name), encoding="utf8") as f:
        return json.load(f)


def domerama_columns(method, frequency, k, ascending_cfs):
    """For known variants, map our ascending strut types to domerama's
    letter labels and published chord factors by nearest CF.

    Returns a list of (label, cf) tuples aligned with ascending_cfs, using
    (None, None) when there is no known variant or no match within the
    2e-4 threshold.
    """
    ref_struts = None
    if method == "CLASS_I":
        data = _load_json("domerama_chord_factors.json")
        for dome in data["domes"]:
            if dome.get("method") != "Class I Method 1":
                continue
            n = int(dome["frequency"][0])
            key = (n, dome["fraction"])
            if key == (frequency, _class1_fraction_for_k(frequency, k)) and _CLASS_I_TRUNC.get(key) == k:
                if all(s.get("chord_factor") is not None for s in dome["struts"]):
                    ref_struts = dome["struts"]
                    break
    elif method == "KRUSCHKE":
        data = _load_json("domerama_kruschke_chord_factors.json")
        for dome in data["domes"]:
            n = dome["frequency"]
            key = (n, dome["fraction"])
            if _KRU_TRUNC.get(key) == k and n == frequency:
                ref_struts = dome["struts"]
                break

    out = [(None, None)] * len(ascending_cfs)
    if not ref_struts:
        return out
    used = set()
    for i, cf in enumerate(ascending_cfs):
        best_j, best_d = None, None
        for j, srow in enumerate(ref_struts):
            if j in used or srow.get("chord_factor") is None:
                continue
            d = abs(srow["chord_factor"] - cf)
            if d <= _MATCH_THRESHOLD and (best_d is None or d < best_d):
                best_j, best_d = j, d
        if best_j is not None:
            out[i] = (ref_struts[best_j]["label"], ref_struts[best_j]["chord_factor"])
            # allow reuse only for legitimate site-merged rows; mark used so
            # a single site row is not claimed by many of our types unless
            # nothing else matches it.
            used.add(best_j)
    return out


def _class1_fraction_for_k(frequency, k):
    for (n, frac), kk in _CLASS_I_TRUNC.items():
        if n == frequency and kk == k:
            return frac
    return None
