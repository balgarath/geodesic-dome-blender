"""Custom chord table: parsing and constrained relaxation solve.

Design.md 7.
"""
import re

from .icosa import subdivide_class1, norm, dist
from .kruschke import kruschke_positions
from .truncate import dome_edges
from .classify import group_edges

_TOKEN_RE = re.compile(r"[,\s]+")


def parse_table(text):
    """Parse comma, space or newline separated chord factor values."""
    tokens = [t for t in _TOKEN_RE.split(text.strip()) if t]
    if not tokens:
        raise ValueError("No chord factor values found in table.")
    values = []
    for t in tokens:
        try:
            values.append(float(t))
        except ValueError:
            raise ValueError("Could not parse chord factor value: '%s'" % t)
    return values


def _base_positions(mesh, frequency, custom_base):
    if custom_base == "CLASS_I":
        return mesh.verts
    if custom_base == "KRUSCHKE":
        extended = frequency in (5, 6)
        pos, _m = kruschke_positions(mesh, frequency, extended=extended)
        return pos
    raise ValueError("Unknown custom_base: %s" % custom_base)


def expected_class_count(frequency, k, custom_base="CLASS_I"):
    mesh = subdivide_class1(frequency)
    base_positions = _base_positions(mesh, frequency, custom_base)
    edges = dome_edges(mesh, k)
    _edge_type, groups = group_edges(edges, base_positions, 1e-7)
    return len(groups)


def base_defaults(frequency, k, custom_base="CLASS_I", merge_tolerance=1e-7):
    """Ascending chord factors of the chosen base layout, classified at the
    same tolerance solve_custom uses internally (1e-7 by default). This is
    the correct source for a table the user hasn't supplied yet: it always
    matches the base topology (Class I or Kruschke) and the class count
    solve_custom will actually require, unlike a Class-I-only, differently
    -tolerant helper such as build.class1_defaults.
    """
    mesh = subdivide_class1(frequency)
    base_positions = _base_positions(mesh, frequency, custom_base)
    edges = dome_edges(mesh, k)
    _edge_type, groups = group_edges(edges, base_positions, merge_tolerance)
    return [g["chord_factor"] for g in groups]


def solve_custom(mesh, base_positions, k, targets, merge_tolerance=1e-7,
                 iters=400, tol=1e-9):
    """Constrained relaxation solve for a custom chord table.

    Returns (positions, residual) where residual is the worst
    |edge length - target| at the final positions.
    """
    edges = dome_edges(mesh, k)
    edge_type, groups = group_edges(edges, base_positions, merge_tolerance)
    n_classes = len(groups)
    if len(targets) != n_classes:
        raise ValueError(
            "Expected %d chord factor values for this base layout, got %d."
            % (n_classes, len(targets)))
    for t in targets:
        if not (0.0 < t < 2.0):
            raise ValueError("Chord factor values must be between 0 and 2 (got %r)." % t)

    apex_id = mesh.row.index(0)
    positions = [list(p) for p in base_positions]

    for _ in range(iters):
        max_err = 0.0
        for i, (u, v) in enumerate(edges):
            target = targets[edge_type[i]]
            pu, pv = positions[u], positions[v]
            cur = dist(pu, pv)
            err = target - cur
            if abs(err) > max_err:
                max_err = abs(err)
            if cur < 1e-12:
                continue
            d = ((pv[0] - pu[0]) / cur, (pv[1] - pu[1]) / cur, (pv[2] - pu[2]) / cur)
            half = err / 2.0
            if u != apex_id:
                pu[0] -= d[0] * half
                pu[1] -= d[1] * half
                pu[2] -= d[2] * half
            if v != apex_id:
                pv[0] += d[0] * half
                pv[1] += d[1] * half
                pv[2] += d[2] * half
        for i in range(len(positions)):
            if i == apex_id:
                positions[i] = [0.0, 0.0, 1.0]
            else:
                positions[i] = list(norm(tuple(positions[i])))
        if max_err < tol:
            break

    positions = [tuple(p) for p in positions]
    residual = 0.0
    for i, (u, v) in enumerate(edges):
        target = targets[edge_type[i]]
        cur = dist(positions[u], positions[v])
        if abs(cur - target) > residual:
            residual = abs(cur - target)
    return positions, residual
